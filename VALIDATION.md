# Test notes

These are development observations, not a hardware support matrix. They separate
what the server has demonstrated from what still needs a real multiplayer test.

## Tested setup

September 2026:

| Component | Tested configuration |
| --- | --- |
| Board | Raspberry Pi 4 Model B Rev 1.5, 8 GB RAM |
| OS | Debian 13, ARM64 |
| Storage | 128 GB microSD |
| Cooling | Passive heatsink |
| Runtime | Box64 0.4.5 with Box32, built from the commit in `Dockerfile` |
| Downloader | DepotDownloader 3.4.0, native ARM64 |
| Game | Linux dedicated server, Steam app `4019830` |
| Observed engine build | `5.6.1-243922+++dominion+live` |

A Pi 4 with 4 GB RAM also completed the startup and saved-world reload checks.
Its 32 GB microSD had little space left after development builds. Other Pi
models and operating systems have not been validated.

The setup script also accepts Apple Silicon Docker Desktop's ARM64 Linux engine.
Its orchestration is covered by local tests with a fake Docker CLI; the image,
game startup, UDP connectivity, and performance on macOS remain untested.

## Confirmed

- The image builds on the Pi, and preflight runs both Box64 and DepotDownloader.
- The native downloader anonymously obtains the official Linux server.
- The game creates a world and completes its initial save.
- EOS session creation and startup succeed, followed by `ReadyToJoin=1`.
- The game binds UDP 7777 and the world-settings beacon binds UDP 8888.
- A clean container stop reaches launcher cleanup and exits with 143 (SIGTERM),
  rather than being forcibly killed.
- Restarting loads the same saved world and publishes readiness again.

After startup on the 8 GB board, the game process used about **1.96 GiB RSS**.
Host memory usage was about 2.1 GiB, with around 5.6 GiB available and no swap
usage. These are near-idle observations, not populated-world capacity estimates.

### Clock experiment

At stock 1.8 GHz, a 15-minute four-worker CPU verification passed without errors
or throttling. Image compilation overlapped most of that test. Observed
temperatures reached about 63°C.

A CPU-only 2.0 GHz setting, with firmware automatic voltage scaling, booted and
passed a brief four-worker verification lasting about three minutes. Game
download/startup overlapped the check. The temperature afterwards was 60.3°C
and the firmware reported no throttling. The saved world also loaded at this
clock speed.

This establishes neither a maximum overclock nor long-term stability. An 11%
clock increase is not a measured 11% improvement in gameplay. Cooling, power,
ambient temperature, and individual boards differ. No overclock settings are
applied by the installation instructions or scripts.

## Why the runtime has workarounds

### Native downloads instead of SteamCMD

An earlier QEMU experiment crashed in SteamCMD. With Box64/Box32, SteamCMD could
start but anonymous network login failed with `Missing configuration` and
`No Connection`. Native ARM64 DepotDownloader succeeded, so it handles downloads.
The SteamCMD polling mechanism is disabled because DepotDownloader does not
maintain the SteamCMD appmanifest expected by the official launcher.

### Allocator and translation cache

Unreal's default Binned2 allocator booted once but crashed on a later startup
with SIGSEGV. Disabling the persistent translation cache alone did not fix it.
Using `-ansimalloc` allowed repeated saved-world loads. Compose keeps that flag
and `BOX64_DYNACACHE=0` as the tested combination.

### Performance threading

The server reports Unreal Engine 5.6.1. In that version,
`FApp::ShouldUseThreadingForPerformance` returns false for dedicated servers
unless `-useperfthreads` is passed on the command line; the shipping binary
contains the `useperfthreads`/`noperfthreads` switches. Compose and
`scripts/boot-test.sh` now pass `-useperfthreads` so UE performance worker
threads run. This does not parallelize the main game simulation thread;
whether it measurably helps under translated (Box64) execution still needs
runtime validation with real players.

### TLS and libraries

The runtime preloads x86 libstdc++, enables Box64 strong memory ordering, and
sets `OPENSSL_ia32cap=0` after an observed translated crypto failure. It also
emulates the OpenSSL 3, zstd, and gcrypt dependency chain used by Crashpad.
TLS certificate verification remains enabled.

Some upstream warnings about online subsystems, localization, navigation, or
the world ban list appeared even on successful starts. Judge readiness by the
completed save/load and session events, not the absence of every warning.

## Still to verify

- Repeatable client joins and reconnects across client/game updates.
- Player movement, combat, and acceptable latency under sustained load.
- Player-progress persistence across clean shutdowns and host reboots.
- Memory growth, performance, and stability with several players.
- A full backup/restore drill and long-running unattended operation.

Please include the board, OS, game build, runtime changes, player count, and
test duration when contributing results. Redact owner IDs, passwords, addresses,
and session identifiers from logs.
