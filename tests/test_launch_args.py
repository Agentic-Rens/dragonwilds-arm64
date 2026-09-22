"""Launch arguments must enable Unreal performance threading.

The dedicated server binary (Unreal Engine 5.6.1) ships FApp::
ShouldUseThreadingForPerformance returning false for dedicated servers
unless `-useperfthreads` is passed. The flag strings are present in the
shipping binary. Both the Compose defaults and the boot test must pass it
so the server uses UE performance worker threads.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
FLAG = "-useperfthreads"


def compose_additional_args():
    text = (ROOT / "compose.yaml").read_text()
    match = re.search(r'RSDW_ADDITIONAL_ARGS:\s*"([^"]*)"', text)
    if match is None:
        raise AssertionError("compose.yaml has no RSDW_ADDITIONAL_ARGS default")
    return match.group(1).split()


def boot_test_args():
    text = (ROOT / "scripts" / "boot-test.sh").read_text()
    match = re.search(r"RSDragonwildsServer-Linux-Shipping\s+RSDragonwilds\s+([^']*)'", text)
    if match is None:
        raise AssertionError("boot-test.sh launch command not found")
    return match.group(1).split()


class LaunchArgsTests(unittest.TestCase):
    def test_compose_default_args_enable_performance_threading(self):
        self.assertIn(FLAG, compose_additional_args())

    def test_boot_test_command_enables_performance_threading(self):
        self.assertIn(FLAG, boot_test_args())

    def test_compose_and_boot_test_keep_tested_flags(self):
        for args in (compose_additional_args(), boot_test_args()):
            for flag in ("-log", "-unattended", "-nullrhi", "-nosound", "-ansimalloc"):
                self.assertIn(flag, args)


if __name__ == "__main__":
    unittest.main()
