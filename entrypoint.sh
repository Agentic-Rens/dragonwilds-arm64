#!/bin/bash
set -euo pipefail

: "${RSDW_OWNER_ID:?Set the owner EOS Online ID from the game client}"
: "${RSDW_WORLD_NAME:?Set a persistent world name}"
: "${RSDW_ADMIN_PASSWORD:?Set a persistent admin password}"
if [[ ! ${RSDW_PASSWORD+x} ]]; then
    printf '%s\n' 'Set RSDW_PASSWORD (an explicitly empty value allows public joining).' >&2
    exit 1
fi
if [[ ${RSDW_ADMIN_PASSWORD} == random || ${RSDW_PASSWORD} == random ]]; then
    printf '%s\n' 'Choose fixed passwords; the upstream random setting changes them between starts.' >&2
    exit 1
fi
printf '%s\n' 'Dragonwilds Pi: experimental ARM64 runtime with Box64/Box32 translation.'
exec /bin/bash /entry.sh "$@"
