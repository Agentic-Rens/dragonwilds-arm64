"""Exercise setup orchestration with a fake Docker CLI and isolated settings."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
OWNER_ID = "0123456789abcdef0123456789abcdef"


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "docker-calls"
        docker = self.bin / "docker"
        docker.write_text(
            '#!/bin/sh\n'
            'printf "%s\\n" "$*" >> "$CALL_LOG"\n'
            'case "$*" in\n'
            '  "info --format "*) printf "%s\\n" "$TEST_PLATFORM" ;;\n'
            '  "compose ps --status running -q server")\n'
            '    [ "$TEST_RUNNING" != yes ] || printf "container-id\\n" ;;\n'
            '  "compose pull server") exit "$TEST_PULL_EXIT" ;;\n'
            '  "compose build server") exit "$TEST_BUILD_EXIT" ;;\n'
            '  "compose version") exit "$TEST_COMPOSE_EXIT" ;;\n'
            'esac\n'
        )
        docker.chmod(0o700)
        self.environment = dict(
            os.environ, PATH=f"{self.bin}:{os.environ['PATH']}",
            CALL_LOG=str(self.log), TEST_PLATFORM="linux/aarch64",
            TEST_RUNNING="no", TEST_PULL_EXIT="0", TEST_BUILD_EXIT="0", TEST_COMPOSE_EXIT="0",
        )

    def setup(self, *arguments, input=""):
        return subprocess.run(
            ["sh", str(self.root / "scripts/setup.sh"), *arguments],
            cwd=self.bin, env=self.environment, input=input,
            capture_output=True, text=True, check=False,
        )

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_fresh_setup_from_another_directory(self):
        result = self.setup(OWNER_ID, "--server-name", "Example Server")
        self.assertEqual(result.returncode, 0, result.stderr)
        settings = (self.root / ".env").read_text()
        self.assertIn("RSDW_SERVER_NAME=Example Server", settings)
        calls = self.calls()
        self.assertLess(calls.index("compose pull server"), calls.index("compose up -d --no-build server"))
        self.assertNotIn("compose build server", calls)
        self.assertTrue(any(call.startswith("run --rm --platform linux/arm64") for call in calls))
        for line in settings.splitlines():
            if "PASSWORD=" in line:
                self.assertNotIn(line.split("=", 1)[1], result.stdout + result.stderr)

    def test_interactive_id_with_apple_silicon_engine_architecture(self):
        self.environment["TEST_PLATFORM"] = "linux/arm64"
        result = self.setup(input=OWNER_ID + "\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("RSDW_OWNER_ID=" + OWNER_ID, (self.root / ".env").read_text())

    def test_running_server_and_configuration_are_untouched(self):
        existing = "RSDW_OWNER_ID=" + OWNER_ID + "\nRSDW_PASSWORD=KeepThis42\n"
        (self.root / ".env").write_text(existing)
        self.environment["TEST_RUNNING"] = "yes"
        result = self.setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / ".env").read_text(), existing)
        self.assertFalse(any(call.startswith(("compose pull", "compose build", "compose up", "run ")) for call in self.calls()))

    def test_existing_settings_reject_new_arguments(self):
        (self.root / ".env").write_text("existing settings\n")
        result = self.setup(OWNER_ID)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.root / ".env").read_text(), "existing settings\n")
        self.assertNotIn("compose pull server", self.calls())

    def test_unsupported_engine_fails_before_configuration(self):
        self.environment["TEST_PLATFORM"] = "linux/x86_64"
        result = self.setup(OWNER_ID)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / ".env").exists())

    def test_missing_compose_fails_before_configuration(self):
        self.environment["TEST_COMPOSE_EXIT"] = "1"
        result = self.setup(OWNER_ID)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / ".env").exists())

    def test_pull_failure_falls_back_to_local_build(self):
        self.environment["TEST_PULL_EXIT"] = "1"
        result = self.setup(OWNER_ID)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertLess(calls.index("compose build server"), calls.index("compose up -d --no-build server"))

    def test_pull_and_build_failure_does_not_start_server(self):
        self.environment["TEST_PULL_EXIT"] = "1"
        self.environment["TEST_BUILD_EXIT"] = "1"
        result = self.setup(OWNER_ID)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("compose up -d --no-build server", self.calls())

    def test_help_needs_no_docker_connection(self):
        result = self.setup("--help")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
