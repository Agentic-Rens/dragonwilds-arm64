"""Check shared-volume protection without contacting a Docker daemon."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


class VolumeHelperTests(unittest.TestCase):
    def test_helpers_only_run_after_a_successful_idle_volume_check(self):
        for script in ("download.sh", "boot-test.sh"):
            for state in ("busy", "unavailable", "idle"):
                with self.subTest(script=script, state=state), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    docker = root / "docker"
                    docker.write_text(
                        '#!/bin/sh\n'
                        'printf "%s\\n" "$*" >> "$CALL_LOG"\n'
                        'if [ "$1" = ps ]; then\n'
                        '  case "$DOCKER_STATE" in\n'
                        '    busy) printf "active-container\\n" ;;\n'
                        '    unavailable) exit 42 ;;\n'
                        '  esac\n'
                        'fi\n'
                    )
                    docker.chmod(0o700)
                    log = root / "calls"
                    environment = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}",
                                       CALL_LOG=str(log), DOCKER_STATE=state)
                    result = subprocess.run(
                        ["sh", str(SCRIPTS / script)], env=environment,
                        capture_output=True, text=True, check=False,
                    )
                    calls = log.read_text().splitlines()
                    self.assertEqual(calls[0], "ps -q --filter volume=dragonwilds-pi_server-data")
                    if state == "idle":
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(len(calls), 2)
                        self.assertTrue(calls[1].startswith("run "))
                        if script == "boot-test.sh":
                            self.assertIn("-ansimalloc", calls[1])
                            self.assertIn("BOX64_DYNACACHE=0", calls[1])
                    else:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertEqual(len(calls), 1)

    def test_boot_test_allocator_override_and_validation(self):
        for allocator in ("mimalloc", "jemalloc", "binnedmalloc"):
            with self.subTest(allocator=allocator), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                docker = root / "docker"
                docker.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALL_LOG"\n')
                docker.chmod(0o700)
                log = root / "calls"
                environment = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}",
                                   CALL_LOG=str(log), DOCKER_STATE="idle",
                                   RSDW_ALLOCATOR=allocator)
                result = subprocess.run(
                    ["sh", str(SCRIPTS / "boot-test.sh")], env=environment,
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("-" + allocator, log.read_text())

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docker = root / "docker"
            docker.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALL_LOG"\n')
            docker.chmod(0o700)
            environment = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}",
                               CALL_LOG=str(root / "calls"), DOCKER_STATE="idle",
                               RSDW_ALLOCATOR="malloc")
            result = subprocess.run(
                ["sh", str(SCRIPTS / "boot-test.sh")], env=environment,
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported RSDW_ALLOCATOR", result.stderr)
            self.assertNotIn("run ", (root / "calls").read_text())


if __name__ == "__main__":
    unittest.main()
