#!/bin/sh
set -eu
# Uses the downloaded files and existing saved configuration. Stop the main
# server first; they share a volume. No ports published; not a gameplay test.
running=$(docker ps -q --filter volume=dragonwilds-pi_server-data)
if [ -n "$running" ]; then
  echo 'Stop containers using server-data before running the boot test.' >&2
  exit 1
fi
docker run --rm --name dragonwilds-boot-test --platform linux/arm64 \
  -v dragonwilds-pi_server-data:/home/steam/rsdw-dedicated \
  -w /home/steam/rsdw-dedicated/RSDragonwilds/Binaries/Linux \
  --entrypoint /bin/bash dragonwilds-pi:experimental \
  -lc 'set -e; chmod +x ./RSDragonwildsServer-Linux-Shipping ../../Plugins/Developer/Sentry/Binaries/Linux/crashpad_handler; export BOX64_DYNACACHE=0; exec timeout --signal=TERM --kill-after=30 180 box64 ./RSDragonwildsServer-Linux-Shipping RSDragonwilds -log -unattended -nullrhi -nosound -ansimalloc'
