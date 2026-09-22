from pathlib import Path

# Preserve Jagex's configuration template handling; use a native downloader
# and invoke the game explicitly through Box64 instead of host binfmt.
entry = Path('/entry.sh')
text = entry.read_text()
old = 'bash "${RSDW_LAUNCH}"'
assert text.count(old) == 1, 'Upstream launcher changed; review integration'
text = text.replace(old, '/usr/local/bin/box64 "${STEAMAPPDIR}/RSDragonwilds/Binaries/Linux/RSDragonwildsServer-Linux-Shipping" RSDragonwilds')
# No updater loop: give the server PID 1's child slot so SIGTERM reaches it.
old = '  else\n    "${server_cmd[@]}"\n  fi'
assert text.count(old) == 1, 'Upstream start function changed'
text = text.replace(old, '  else\n    exec "${server_cmd[@]}"\n  fi')
start = text.index('function download() {')
end = text.index('function start() {', start)
text = text[:start] + '''function download() {
  AUTO_UPDATE="false"
  if [[ "${RSDW_SKIP_UPDATE:-false}" != "true" ]]; then
    /opt/depotdownloader/DepotDownloader -app 4019830 -os linux -osarch 64 -dir "${STEAMAPPDIR}"
  fi
  test -s "${STEAMAPPDIR}/RSDragonwilds/Binaries/Linux/RSDragonwildsServer-Linux-Shipping"
  chmod +x "${STEAMAPPDIR}/RSDragonwilds/Binaries/Linux/RSDragonwildsServer-Linux-Shipping" "${STEAMAPPDIR}/RSDragonwildsServer.sh"
}

''' + text[end:]
entry.write_text(text)

steamcmd = Path('/home/steam/steamcmd/steamcmd.sh')
steamcmd.write_text('''#!/bin/sh
set -eu
cd /home/steam/steamcmd
exec /usr/local/bin/box64 ./linux32/steamcmd "$@"
''')
steamcmd.chmod(0o755)
