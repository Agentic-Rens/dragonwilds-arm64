"""Update the join password using a hidden prompt or standard input."""
import getpass
import os
from pathlib import Path
import sys

password = (
    getpass.getpass("New join password: ")
    if sys.stdin.isatty()
    else sys.stdin.read().rstrip("\n")
)
if not password or not password.isascii() or not password.isalnum():
    raise SystemExit("Expected a nonempty ASCII alphanumeric password")
if password == "random":
    raise SystemExit("Choose a fixed password; 'random' is reserved by the upstream launcher")
path = Path(__file__).resolve().parent.parent / ".env"
lines = path.read_text().splitlines()
matches = [i for i, line in enumerate(lines) if line.startswith("RSDW_PASSWORD=")]
if len(matches) != 1:
    raise SystemExit("Expected exactly one RSDW_PASSWORD setting")
lines[matches[0]] = f"RSDW_PASSWORD={password}"
os.chmod(path, 0o600)
path.write_text("\n".join(lines) + "\n")
print("Join password updated. Run 'docker compose up -d --no-build' to apply it (restarts the server).")
