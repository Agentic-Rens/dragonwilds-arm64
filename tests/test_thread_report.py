import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("thread_report", ROOT / "scripts" / "thread-report.py")
THREAD_REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(THREAD_REPORT)


class ThreadReportTests(unittest.TestCase):
    def test_compact_cpus(self):
        self.assertEqual(THREAD_REPORT.compact_cpus(set()), "none")
        self.assertEqual(THREAD_REPORT.compact_cpus({0, 1, 2, 3}), "0-3")
        self.assertEqual(THREAD_REPORT.compact_cpus({0, 2, 3, 7}), "0,2-3,7")

    def test_wrapper_runs_the_container_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docker = root / "docker"
            docker.write_text(
                '#!/bin/sh\n'
                'printf "%s\\n" "$*" >> "$CALL_LOG"\n'
                'if [ "$1 $2 $3" = "compose ps -q" ]; then printf "container-id\\n"; fi\n'
            )
            docker.chmod(0o700)
            log = root / "calls"
            environment = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}", CALL_LOG=str(log))
            result = subprocess.run(
                ["sh", str(ROOT / "scripts/thread-report.sh"), "5"],
                env=environment, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                log.read_text().splitlines(),
                [
                    "compose ps -q server",
                    "exec container-id python3 /usr/local/bin/thread-report.py --seconds 5",
                ],
            )

    def test_wrapper_rejects_invalid_interval_before_docker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docker = root / "docker"
            docker.write_text('#!/bin/sh\nexit 99\n')
            docker.chmod(0o700)
            environment = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}")
            for seconds in ("0", "five"):
                with self.subTest(seconds=seconds):
                    result = subprocess.run(
                        ["sh", str(ROOT / "scripts/thread-report.sh"), seconds],
                        env=environment, capture_output=True, text=True, check=False,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("positive-seconds", result.stderr)


if __name__ == "__main__":
    unittest.main()
