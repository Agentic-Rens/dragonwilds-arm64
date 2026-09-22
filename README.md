# Dragonwilds on ARM64

Run a RuneScape: Dragonwilds dedicated server on a 64-bit Raspberry Pi using
Docker and Box64. This project adapts [Jagex's official server image](https://github.com/runescape/rsdw-dedicated)
with an ARM64 runtime, x86 translation, and a native game downloader.

You can also try hosting directly on an **Apple Silicon Mac** through Docker
Desktop—no Raspberry Pi required. The Pi 4 is the tested platform; Mac hosting
is experimental.

- [Run on a Raspberry Pi](#quick-start)
- [Run on a Mac instead of a Pi](#run-on-a-mac-instead-of-a-pi)
- [Use a Mac to manage a Pi over SSH](#use-a-mac-to-set-up-a-raspberry-pi)

**Experimental, but it boots:** a Pi 4 has created a world, registered a session,
and loaded the saved world after a restart. That is not yet a promise of smooth
multiplayer. Client compatibility and performance with players need more testing.
See [the test notes](VALIDATION.md) for what has actually been checked.

This is an unofficial community project, not an ARM port of the game or a
Jagex-supported configuration.

## Tested devices

Devices this server has been run on:

| Device | RAM | Status |
| --- | --- | --- |
| Raspberry Pi 4 (Model B) | 8 GB | Tested — world creation, restart, and reload confirmed |
| Mac Studio (M4 Max) | 36 GB | Experimental — Docker Desktop hosting |

## What you need

- Either a Raspberry Pi 4 with **8 GB RAM recommended** and a 64-bit Linux OS,
  or an **Apple Silicon Mac** with enough memory for Docker and macOS.
  Debian 13 on the Pi 4 has been tested. Mac hosting and other boards, including
  the Pi 5, are untested. Local Intel Mac hosting is not supported by this project.
- Docker Engine and the Docker Compose plugin (`docker compose`) on Linux, or
  Docker Desktop on Mac, which includes Compose.
- Python 3 for the configuration helpers.
- Plenty of free disk space: **30 GB or more recommended**. The image, game
  downloads, and saves all use space, and building the image yourself needs
  extra room for build layers. An SSD is
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
machine that will host the server. Mac users should first follow
[Run on a Mac instead of a Pi](#run-on-a-mac-instead-of-a-pi).

```sh
git clone https://github.com/Agentic-Rens/dragonwilds-arm64.git
cd dragonwilds-arm64
```

Then run:

```sh
sh scripts/setup.sh
```

Paste your EOS player ID when prompted. The script creates `.env` with generated
passwords, pulls the prebuilt image from GHCR, runs preflight, and starts the
container. It checks
for Docker, Compose, Python, and an ARM64 Linux Docker engine first. It does not
install system packages. If the pull fails, it falls back to building the image
locally, which can take around an hour on a Pi 4.

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

## Run on a Mac instead of a Pi

In this setup, **the Mac hosts the server**. All commands below run in macOS
Terminal, and no Pi or SSH connection is needed. Docker Desktop provides an
ARM64 Linux VM; Box64 inside the container translates the x86 game server.

Use an **Apple Silicon Mac (M-series)**. Check **Apple menu → About This Mac**
for its chip, or run `uname -m` in a native Terminal session: it should report
`arm64`. Local Intel Mac hosting is not supported by the setup script.

**Mac hosting has not been runtime-tested here.** It uses the same Box64 build
and workarounds as the Pi. Passing setup or preflight is not proof of a playable
Mac-hosted session.

### 1. Install Docker Desktop and Python

If you already use [Homebrew](https://brew.sh/):

```sh
brew install --cask docker
brew install python git
open -a Docker
```

Alternatively, install [Docker Desktop for Apple Silicon](https://docs.docker.com/desktop/setup/install/mac-install/)
and [Python 3 for macOS](https://www.python.org/downloads/macos/) using their
installers. Install Apple's Command Line Tools with `xcode-select --install`
if Git is missing, or download the repository ZIP instead of cloning it.

Complete Docker Desktop's first-run setup and wait for its engine to start.
In Docker Desktop's resource settings, allow at least **4 GB of VM memory**,
preferably **6–8 GB** if your Mac has room, and at least **30 GB of free
Docker disk-image capacity**. Leave memory and disk space for macOS and other
apps; a 16 GB or larger Mac gives more breathing room.

Verify your tools and Docker target:

```sh
python3 --version
docker compose version
docker context ls
docker info --format '{{.OSType}}/{{.Architecture}}'
```

The final command should report `linux/aarch64` or `linux/arm64`. If you use
remote Docker contexts, select your local Docker Desktop context before setup
(normally `docker context use desktop-linux`). **Do not use `sudo`** for the
following commands on Mac.

### 2. Download the project and run setup

```sh
git clone https://github.com/Agentic-Rens/dragonwilds-arm64.git
cd dragonwilds-arm64
sh scripts/setup.sh
```

Paste your EOS player ID from the game's Settings menu when prompted. Setup
creates `.env` with fixed join/admin passwords, pulls the prebuilt image, runs
preflight, and starts the server. The first game download can take
a while. View the passwords privately with `open -e .env`.

Follow startup:

```sh
docker compose logs -f server
```

Wait for the world-settings beacon on UDP `8888` and `ReadyToJoin` with
`value[1]`. Pressing Control-C exits the log viewer; the server keeps running.

### 3. Connect to the Mac-hosted server

- From a game client on another device on your LAN, Direct Connect to
  **`<mac-lan-address>:7777`** and enter the join password from `.env`.
- Find the Mac's LAN address in **System Settings → Network → your active
  connection → Details → TCP/IP**. Use the Mac's address, not the container's
  internal address.
- If a compatible game client is running on the same Mac, use
  **`localhost:7777`**. This project hosts the Linux server only; it does not
  install or provide a native macOS game client.
- Allow Docker Desktop's incoming traffic through the macOS firewall if
  prompted. Both **UDP 7777 and UDP 8888** must be reachable.
- For internet players, forward both UDP ports on your router to the Mac.
  A DHCP reservation helps keep the Mac's LAN address stable.

### 4. Keep it running and manage saves

Docker Desktop must stay running, and the Mac must stay awake while people
play. Keep a MacBook connected to power with its lid open. To prevent idle
system sleep during a session, run this in a separate Terminal tab and leave it
running:

```sh
caffeinate -i
```

Press Control-C in that tab when you no longer need to keep the Mac awake.
The command does not keep a closed-lid MacBook awake. For regular hosting,
configure the Mac's power settings and Docker Desktop's startup-at-login option.
The container's restart policy takes effect once Docker Desktop is running;
it does not start Docker Desktop itself.

From the repository directory:

```sh
docker compose ps
docker compose stop     # Stop the game server cleanly
docker compose start    # Start it again
```

World data lives in the named volume `dragonwilds-pi_server-data` inside Docker
Desktop's Linux VM, not alongside the repository. Follow [Saves and backups](#saves-and-backups)
before resetting or uninstalling Docker Desktop. Keep `.env` as a separate
private backup. The volume retains its name on Mac so the same backup and
restore instructions work on both platforms.

## Use a Mac to set up a Raspberry Pi

This separate option works from either an Intel or Apple Silicon Mac. The game
server runs on the Pi; your Mac is just the terminal.

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

### 2. Get the image

Pull the prebuilt ARM64 image published from this repository:

```sh
docker compose pull server
sh scripts/preflight.sh
```

Preflight checks the translator and downloader; it does not start the game.

To build the image yourself instead (for example after changing the
`Dockerfile`):

```sh
docker compose build server
```

A local build compiles Box64 and can take around an hour on a Pi 4. Later
builds reuse Docker's cache.

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
`BOX64_DYNACACHE=0`. The default arguments also pass `-useperfthreads`: the
Unreal Engine 5.6.1 dedicated server otherwise disables its performance
worker threads (`FApp::ShouldUseThreadingForPerformance` returns false for
dedicated servers without the flag; the shipping binary contains the
`useperfthreads` switch). This enables UE's performance task threads; it
does **not** parallelize the main game simulation, so runtime validation
under real player load is still needed. To experiment with launch
arguments, edit the environment
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

To update to the latest published image:

```sh
docker compose pull server
docker compose up -d --no-build
```

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
  ghcr.io/agentic-rens/dragonwilds-arm64:latest \
  -czf /backup/server-data.tar.gz -C /data .
docker compose start
```

This backs up the entire volume and overwrites that archive if it already
exists. Keep dated copies elsewhere, and back up `.env` privately as well.
**Do not run `docker compose down -v` unless you intend to delete the world.**

To restore an archive to a new installation, place it at
`backups/server-data.tar.gz`, restore your `.env`, pull the image, and run:

```sh
docker compose stop
docker volume create dragonwilds-pi_server-data
docker run --rm --user 0:0 --entrypoint tar \
  -v dragonwilds-pi_server-data:/data \
  -v "$PWD/backups:/backup:ro" \
  ghcr.io/agentic-rens/dragonwilds-arm64:latest \
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
