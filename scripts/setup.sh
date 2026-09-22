#!/bin/sh
# Run from any directory. Docker and Python must already be installed.
set -eu

usage() {
  cat <<'EOF'
Usage: sh scripts/setup.sh [EOS_PLAYER_ID [--server-name NAME] [--world-name NAME]]

With no .env, prompts for an EOS player ID or uses the supplied arguments.
With an existing .env, run without arguments to reuse its settings.
Pulls the prebuilt image (or builds it locally), runs preflight, and
starts the server. An already-running server is left alone.
EOF
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
esac

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"

for program in docker python3; do
  if ! command -v "$program" >/dev/null 2>&1; then
    printf 'Missing %s. See the prerequisites in README.md.\n' "$program" >&2
    exit 1
  fi
done
if ! docker compose version >/dev/null 2>&1; then
  printf '%s\n' 'Install the Docker Compose plugin (docker compose), then run setup again.' >&2
  exit 1
fi
if ! platform=$(docker info --format '{{.OSType}}/{{.Architecture}}'); then
  printf '%s\n' 'Cannot reach Docker. Start Docker Engine or Docker Desktop and check your Docker permissions/context.' >&2
  exit 1
fi
case "$platform" in
  linux/aarch64|linux/arm64) ;;
  *) printf 'Expected an ARM64 Linux Docker engine; found %s. Use a 64-bit Pi or Apple Silicon Docker Desktop.\n' "$platform" >&2; exit 1 ;;
esac

if [ -f .env ]; then
  if [ "$#" -ne 0 ]; then
    printf '%s\n' '.env already exists. Edit it directly, or run setup without arguments to reuse it.' >&2
    exit 1
  fi
  printf '%s\n' 'Using existing .env.'
else
  if [ "$#" -eq 0 ]; then
    printf '%s' 'EOS player ID (from the game Settings menu): '
    if ! IFS= read -r owner_id; then
      printf '\n%s\n' 'No ID received. Pass your EOS player ID as an argument for noninteractive setup.' >&2
      exit 1
    fi
    set -- "$owner_id"
  fi
  python3 scripts/configure.py "$@"
fi

docker compose config --quiet
running=$(docker compose ps --status running -q server)
if [ -n "$running" ]; then
  printf '%s\n' 'The server is already running. Setup has not rebuilt or restarted it.'
  exit 0
fi

printf '%s\n' 'Pulling the prebuilt image from GHCR.'
if ! docker compose pull server; then
  printf '%s\n' 'Pull failed; building locally. The first build can take around an hour on a Pi 4.'
  docker compose build server
fi
sh scripts/preflight.sh
docker compose up -d --no-build server
printf '\n%s\n' \
  'The container has started. The first game download and world startup take more time.' \
  'Follow startup with: docker compose logs -f server' \
  'Wait for ReadyToJoin with value[1] before connecting to <server-address>:7777.' \
  'Your join/admin passwords are stored in .env; keep that file private.'
