"""Exercise configuration helpers in an isolated directory, never a real .env."""
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
OWNER_ID = "0123456789abcdef0123456789abcdef"


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(SCRIPTS, self.root / "scripts")
        self.env = self.root / ".env"

    def run_script(self, script, *arguments, input=None):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / script), *arguments],
            input=input, capture_output=True, text=True, check=False,
        )

    def configure(self, *arguments):
        result = self.run_script("configure.py", OWNER_ID, *arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_configuration_is_private_and_does_not_print_passwords(self):
        result = self.configure("--server-name", "Weekend Server", "--world-name", "World-1")
        settings = dict(line.split("=", 1) for line in self.env.read_text().splitlines())
        self.assertEqual(settings["RSDW_SERVER_NAME"], "Weekend Server")
        self.assertEqual(settings["RSDW_WORLD_NAME"], "World-1")
        self.assertEqual(settings["RSDW_OWNER_ID"], OWNER_ID)
        self.assertEqual(stat.S_IMODE(self.env.stat().st_mode), 0o600)
        self.assertNotEqual(settings["RSDW_PASSWORD"], settings["RSDW_ADMIN_PASSWORD"])
        for key in ("RSDW_PASSWORD", "RSDW_ADMIN_PASSWORD"):
            self.assertTrue(settings[key])
            self.assertNotIn(settings[key], result.stdout + result.stderr)

    def test_existing_configuration_is_never_overwritten(self):
        self.configure()
        original = self.env.read_bytes()
        result = self.run_script("configure.py", OWNER_ID)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.env.read_bytes(), original)

    def test_invalid_owner_and_names_do_not_create_configuration(self):
        for arguments in (
            ("not-an-eos-id",),
            (OWNER_ID, "--world-name", "../world"),
            (OWNER_ID, "--server-name", "Server\nRSDW_PASSWORD=injected"),
            (OWNER_ID, "--server-name", "$VARIABLE"),
        ):
            with self.subTest(arguments=arguments):
                result = self.run_script("configure.py", *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.env.exists())

    def test_password_update_preserves_other_settings(self):
        self.configure()
        before = self.env.read_text().splitlines()
        password = "ExampleJoin42"
        result = self.run_script("set-join-password.py", input=password + "\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        after = self.env.read_text().splitlines()
        self.assertIn("RSDW_PASSWORD=" + password, after)
        self.assertEqual(
            [line for line in before if not line.startswith("RSDW_PASSWORD=")],
            [line for line in after if not line.startswith("RSDW_PASSWORD=")],
        )
        self.assertNotIn(password, result.stdout + result.stderr)
        self.assertEqual(stat.S_IMODE(self.env.stat().st_mode), 0o600)

    def test_invalid_password_does_not_modify_file(self):
        self.configure()
        original = self.env.read_bytes()
        for password in ("", "random", "two words", "$VARIABLE", "a\nSETTING=value", "é"):
            with self.subTest(password=password):
                result = self.run_script("set-join-password.py", input=password)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.env.read_bytes(), original)

    def test_ambiguous_password_settings_are_rejected(self):
        self.configure()
        self.env.write_text(self.env.read_text() + "RSDW_PASSWORD=Duplicate42\n")
        original = self.env.read_bytes()
        result = self.run_script("set-join-password.py", input="NewPassword42")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.env.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
