#!/bin/sh
set -eu
seconds=${1:-10}
case "$seconds" in
  ''|*[!0-9]*)
    echo 'Usage: sh scripts/thread-report.sh [positive-seconds]' >&2
    exit 1
    ;;
esac
if [ "$seconds" -eq 0 ]; then
  echo 'Usage: sh scripts/thread-report.sh [positive-seconds]' >&2
  exit 1
fi
container=$(docker compose ps -q server)
if [ -z "$container" ] || [ "$(printf '%s\n' "$container" | wc -l)" -ne 1 ]; then
  echo 'Expected exactly one configured server container; start it first.' >&2
  exit 1
fi
docker exec "$container" python3 /usr/local/bin/thread-report.py --seconds "$seconds"
