# Dragonwilds on Raspberry Pi

Run a RuneScape: Dragonwilds dedicated server on a 64-bit Raspberry Pi using
Docker and Box64. This project adapts [Jagex's official server image](https://github.com/runescape/rsdw-dedicated)
with an ARM64 runtime, x86 translation, and a native game downloader.

**Experimental, but it boots:** a Pi 4 has created a world, registered a session,
and loaded the saved world after a restart. That is not yet a promise of smooth
multiplayer. Client compatibility and performance with players need more testing.
See [the test notes](VALIDATION.md) for what has actually been checked.

This is an unofficial community project, not an ARM port of the game or a
Jagex-supported configuration.

## What you need

- A Raspberry Pi 4 with **8 GB RAM recommended**, running a 64-bit Linux OS.
  Debian 13 has been tested. Other boards, including the Pi 5, are untested.
- Docker Engine and the Docker Compose plugin (`docker compose`).
- Python 3 for the configuration helpers.
- Plenty of free disk space: **30 GB or more recommended before building**.
  Build layers, the image, game downloads, and saves all use space. An SSD is
  preferable to a microSD card for a long-running server.
- A suitable power supply and cooling for sustained CPU load.
- Your **EOS player ID**, shown at the bottom of the game's Settings menu.
  This is a 32-character hexadecimal ID, not your Steam ID.

A 4 GB Pi reached server readiness in early tests, but leaves less room for
players and translation overhead. The container has no CPU or memory limits;
it is best suited to a machine with resources to spare.

For a Pi, install [Docker Engine using the Debian instructions](https://docs.docker.com/engine/install/debian/)
on your 64-bit OS, including the Compose plugin. Install Python 3 if needed:
`sudo apt update && sudo apt install -y python3`.
Check that `docker info`, `docker compose version`, and `python3 --version` work.
If Docker needs elevated permissions, follow its
[Linux post-install instructions](https://docs.docker.com/engine/install/linux-postinstall/)
or use `sudo` for the Docker commands.

## Quick start

Download or clone this repository and open a terminal in its directory on the
machine that will host the server. For Mac options, see [Setup from a Mac](#setup-from-a-mac).

```sh
git clone https://github.com/Agentic-Rens/dragonwilds-arm64.git
cd dragonwilds-arm64
```

Then run:

```sh
sh scripts/setup.sh
```

Paste your EOS player ID when prompted. The script creates `.env` with generated
passwords, builds the image, runs preflight, and starts the container. It checks
for Docker, Compose, Python, and an ARM64 Linux Docker engine first. It does not
install system packages.

You can also supply the settings up front:

```sh
sh scripts/setup.sh YOUR_EOS_PLAYER_ID \
  --server-name "Weekend Dragonwilds" --world-name "MyWorld"
```

Run the script without arguments to reuse an existing `.env`. If the server is
already running, setup exits without rebuilding or restarting it. Use the
[day-to-day commands](#day-to-day-use) for intentional updates or restarts.
For Docker permission errors on Linux, configure Docker access as described
above or run `sudo sh scripts/setup.sh`; the latter creates a root-owned `.env`,
so use `sudo` to view or edit it. Do not use `sudo` with Docker Desktop on Mac.

Watch startup with `docker compose logs -f server`, then follow [Join](#4-join).
The script finishing means the container has started, not that the game is ready.

## Setup from a Mac

### Use your Mac to set up a Raspberry Pi

This works from either an Intel or Apple Silicon Mac. The game server runs on
the Pi; your Mac is just the terminal.

1. Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to install a
   64-bit OS. Set your Pi's username, network settings, and enable SSH in Imager.
2. In macOS Terminal, connect with your chosen username and the Pi's hostname:

   ```sh
   ssh <pi-user>@<pi-hostname>.local
   ```

3. Install Docker, Compose, and Python **on the Pi** using the prerequisites
   above. Download or clone this repository there, open its directory, and run
   `sh scripts/setup.sh`.
4. Keep the SSH session open through the build, or run it inside `tmux` on the
   Pi so a dropped connection does not interrupt setup. Once started, the
   detached server keeps running after you close Terminal.
5. Players connect to `<pi-address>:7777`. You do not need Docker Desktop on
   your Mac for this route.

### Host on an Apple Silicon Mac (experimental)

You can also try the ARM64 Linux container in Docker Desktop on an M-series
Mac. **This has not been runtime-tested here.** It uses the same Box64 build and
workarounds as the Pi; preflight success alone does not establish compatibility.
Local Intel Mac hosting is not supported by this setup script.

1. Install and start [Docker Desktop for Apple Silicon](https://docs.docker.com/desktop/setup/install/mac-install/).
   Allow at least **4 GB of Docker VM memory**, preferably **6–8 GB** if your Mac
   has room, and at least **30 GB of free Docker disk-image capacity** for the
   build and game. Leave memory for macOS and other apps.
2. Install Python 3. With [Homebrew](https://brew.sh/), run `brew install python`;
   alternatively use the [python.org macOS installer](https://www.python.org/downloads/macos/).
3. Download or clone this repository and open Terminal in its directory. Check
   `docker info`, `docker compose version`, and `python3 --version`, then run:

   ```sh
   sh scripts/setup.sh
   docker compose logs -f server
   ```

4. Wait for `ReadyToJoin` with `value[1]`. A client on the same Mac uses
   `localhost:7777`; clients elsewhere on your LAN use `<mac-lan-address>:7777`.
   Allow Docker's incoming traffic through the macOS firewall if prompted.

Docker Desktop must remain running, and the Mac must stay awake while people
play. Its startup-at-login setting is separate from the container's restart
policy. Saves are in Docker Desktop's named volume; back them up before
resetting or uninstalling Docker Desktop. Hosting this Linux server does not
install or provide a native macOS game client.

## Manual setup

Prefer to run each step yourself? These commands are the same flow as the
setup script. Use `sudo` for Docker commands and shell helpers on Linux if
your account cannot access Docker.

### 1. Create your configuration

```sh
python3 scripts/configure.py YOUR_EOS_PLAYER_ID
```

The helper creates a private `.env` file with generated, fixed join and admin
passwords. It refuses to overwrite an existing file. To choose names:

```sh
python3 scripts/configure.py YOUR_EOS_PLAYER_ID \
  --server-name "Weekend Dragonwilds" --world-name "MyWorld"
```

Names entered through the helper may contain letters, digits, spaces, `_`, and
`-` (up to 64 characters, starting with a letter or digit).

Open `.env` locally to view the passwords or change your settings. Keep it out
of version control. You can also copy `.env.example` to `.env`, fill it in, and
run `chmod 600 .env`.

### 2. Build the image

```sh
docker build --platform linux/arm64 -t dragonwilds-pi:experimental .
sh scripts/preflight.sh
```

The first build compiles Box64 and can take around an hour on a Pi 4. Later
builds reuse Docker's cache. Preflight checks the translator and downloader;
it does not start the game.

### 3. Start the server

```sh
docker compose up -d --no-build
docker compose logs -f server
```

The first start downloads the official Linux server anonymously from Steam.
Allow time for the download and world creation. Look for the world-settings
beacon on port `8888` and a `ReadyToJoin` setting with `value[1]`.

Compose restarts the server after an unexpected exit or a host reboot, unless
you explicitly stop it. Docker itself must also be enabled at boot.

### 4. Join

Use Direct Connect in the game with **`<server-address>:7777`** and the join
password from `.env`. The server uses these ports:

| Port | Protocol | Purpose |
| --- | --- | --- |
| 7777 | UDP | Game traffic |
| 8888 | UDP | World-settings beacon |

For internet access, forward **both UDP ports** to the server host and allow them through
your firewall, preserving the port numbers. Ordinary HTTP reverse proxies do
not carry this traffic. This project does not configure your router or firewall.

## Configuration

| Variable | Purpose |
| --- | --- |
| `RSDW_OWNER_ID` | The world owner's EOS player ID; required. |
| `RSDW_SERVER_NAME` | Name shown to players. |
| `RSDW_WORLD_NAME` | Persistent world/save-slot name; keep it unchanged to reuse a world. |
| `RSDW_PASSWORD` | Join password. An explicitly empty value allows public joining. |
| `RSDW_ADMIN_PASSWORD` | Fixed, nonempty admin password; required. |
| `RSDW_SKIP_UPDATE` | Set to `true` to start already-downloaded game files without checking Steam. |

Avoid the literal password `random`: the launcher rejects it so passwords stay
consistent between starts. The game itself can include join passwords and
session details in logs; redact logs before sharing them.

Compose supplies the tested runtime flags, including `-ansimalloc` and
`BOX64_DYNACACHE=0`. To experiment with launch arguments, edit the environment
section in `compose.yaml`; it takes precedence over values in `.env`.

### Change the join password

```sh
python3 scripts/set-join-password.py
docker compose up -d --no-build
```

The helper prompts without echoing the password. The Compose command recreates
the server to apply the change, disconnecting any players. The helper also
accepts a password on standard input for automation.
The helper accepts ASCII letters and digits; edit `.env` directly if you intend
to use an empty join password for public access.

## Day-to-day use

```sh
docker compose ps                 # Container status
docker compose logs --tail 100 server
docker compose stop               # Graceful stop; saves are retained
docker compose start              # Start the existing container
```

Game files are checked for updates at each start unless `RSDW_SKIP_UPDATE=true`.
The base image digest and translator source are pinned, but the Steam game
download is **not** version-pinned. There is no background update polling or
automatic shutdown when a new game release appears.

To rebuild after changing this repository:

```sh
docker compose build
docker compose up -d --no-build
```

### Saves and backups

Installation files, configuration, and saves live in the Docker volume
`dragonwilds-pi_server-data`. Stop the server before backing it up:

```sh
docker compose stop
mkdir -p backups
docker run --rm --user 0:0 --entrypoint tar \
  -v dragonwilds-pi_server-data:/data:ro \
  -v "$PWD/backups:/backup" \
  dragonwilds-pi:experimental \
  -czf /backup/server-data.tar.gz -C /data .
docker compose start
```

This backs up the entire volume and overwrites that archive if it already
exists. Keep dated copies elsewhere, and back up `.env` privately as well.
**Do not run `docker compose down -v` unless you intend to delete the world.**

To restore an archive to a new installation, place it at
`backups/server-data.tar.gz`, restore your `.env`, build the image, and run:

```sh
docker compose stop
docker volume create dragonwilds-pi_server-data
docker run --rm --user 0:0 --entrypoint tar \
  -v dragonwilds-pi_server-data:/data \
  -v "$PWD/backups:/backup:ro" \
  dragonwilds-pi:experimental \
  -xzf /backup/server-data.tar.gz -C /data
docker compose up -d --no-build
```

Restore into an empty volume to avoid mixing old and restored files. These
commands assume the default Compose project name; changing it also changes
the volume name.

## How it works

- **Box64/Box32** translates the official x86 game runtime inside native ARM64
  Debian. No privileged container or host-wide binfmt registration is needed.
- **DepotDownloader** downloads the game natively on ARM64. SteamCMD's network
  login was unreliable under translation.
- The official launcher still generates configuration, with a small patch to
  use the native downloader and launch the game through Box64.
- Runtime workarounds cover the observed allocator, TLS, and x86 library issues.
  TLS certificate verification remains enabled.

## Troubleshooting

- **Container is running, but you cannot join:** check for `ReadyToJoin=1`, the
  correct join password, and both UDP ports. Container startup alone is not
  proof the world is ready.
- **Owner ID error:** use the EOS ID from the game, not a Steam ID or username.
- **Crash during world loading:** keep the tested `-ansimalloc` and Box64 settings.
  Capture a redacted log and note the game version when reporting a problem.
- **Slow play or instability:** check memory pressure, disk space, CPU temperature,
  and power-related throttling. More RAM cannot remove CPU translation overhead.
- **Misleading `docker stats` memory figures:** some Pi kernels lack container
  memory accounting. Cross-check with `free -h` and host process memory usage.

Overclocking is optional and is **not configured by this repository**. One Pi 4
passed a short check at 2.0 GHz, but that is not a recommendation for every board.
Start at stock clocks; see the [test notes](VALIDATION.md) for context.

## Contributing and license

Bug reports, compatibility results, and focused fixes are welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md) for useful test information and local checks.

The original code and documentation in this repository are licensed under
[MIT](LICENSE). The game remains proprietary, and the components used to build
the image have their own terms. See [THIRD_PARTY.md](THIRD_PARTY.md).
