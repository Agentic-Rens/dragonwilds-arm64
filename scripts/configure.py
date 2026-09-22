"""Create private configuration once; never print generated credentials."""
import argparse
import os
from pathlib import Path
import re
import secrets

parser = argparse.ArgumentParser(description="Create private Dragonwilds server settings.")
parser.add_argument("owner_id", help="32-character EOS player ID from the game settings")
parser.add_argument("--server-name", default="Dragonwilds Pi")
parser.add_argument("--world-name", default="MyWorld")
args = parser.parse_args()
if not re.fullmatch(r"[0-9a-fA-F]{32}", args.owner_id):
    parser.error("Expected a 32-character hexadecimal EOS player ID")
for name in (args.server_name, args.world_name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _-]{0,63}", name):
        parser.error(
            "Names must be 1–64 characters: letters, digits, spaces, _ or -; "
            "start with a letter or digit"
        )

destination = Path(__file__).resolve().parent.parent / ".env"
content = (
    f"RSDW_OWNER_ID={args.owner_id}\n"
    f"RSDW_SERVER_NAME={args.server_name}\n"
    f"RSDW_WORLD_NAME={args.world_name}\n"
    f"RSDW_PASSWORD={secrets.token_hex(8)}\n"
    f"RSDW_ADMIN_PASSWORD={secrets.token_hex(16)}\n"
)
try:
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    parser.exit(1, "Configuration already exists; edit .env to change it.\n")
with os.fdopen(fd, "w") as stream:
    stream.write(content)
print(f"Created private server configuration at {destination}")
