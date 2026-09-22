#!/bin/sh
set -eu
# This writes the same game files used by the main server.
running=$(docker ps -q --filter volume=dragonwilds-pi_server-data)
if [ -n "$running" ]; then
  echo 'Stop containers using server-data before downloading game files.' >&2
  exit 1
fi
docker run --rm --name dragonwilds-download --platform linux/arm64 \
  -v dragonwilds-pi_server-data:/home/steam/rsdw-dedicated \
  --entrypoint /opt/depotdownloader/DepotDownloader ghcr.io/agentic-rens/dragonwilds-arm64:latest \
  -app 4019830 -os linux -osarch 64 -dir /home/steam/rsdw-dedicated
