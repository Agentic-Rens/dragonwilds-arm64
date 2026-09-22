#!/bin/sh
set -eu
platform=$(docker info --format '{{.OSType}}/{{.Architecture}}')
case "$platform" in
  linux/aarch64|linux/arm64) ;;
  *) echo 'Expected an ARM64 Linux Docker engine.' >&2; exit 1 ;;
esac
docker run --rm --platform linux/arm64 \
  --entrypoint /bin/bash dragonwilds-pi:experimental \
  -lc 'box64 --version && /opt/depotdownloader/DepotDownloader -V'
