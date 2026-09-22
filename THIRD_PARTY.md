# Third-party software

The MIT license in this repository covers its original scripts and documentation.
It does not replace the licenses or terms of the software used by the image.

## Jagex dedicated-server image

[runescape/rsdw-dedicated](https://github.com/runescape/rsdw-dedicated) provides
the official launcher, configuration templates, and x86 runtime. The image is
pinned by digest in `Dockerfile`. Its launcher is BSD-3-Clause licensed;
the launcher license and SteamCMD terms are included in the built image under
`/usr/share/doc/dragonwilds/`.

`patch-upstream.py` modifies the launcher during the build to use native
downloads and explicit Box64 execution. It does not modify or relicense the
proprietary game. Game files are downloaded from Steam at runtime and are not
included in this source repository. Use of the game and Steam services remains
subject to their respective terms.

## Box64 and Box32

[ptitSeb/box64](https://github.com/ptitSeb/box64) is MIT licensed. Its source
commit is pinned in `Dockerfile`, and its license is installed at
`/usr/local/share/doc/box64/LICENSE` in the image.

## DepotDownloader

[SteamRE/DepotDownloader](https://github.com/SteamRE/DepotDownloader) is GPL-2.0
licensed. The build downloads the self-contained ARM64 release **3.4.0**, pinned
by SHA-256. The archive includes its license at `/opt/depotdownloader/LICENSE`.
Source for that release is available at the
[`DepotDownloader_3.4.0` tag](https://github.com/SteamRE/DepotDownloader/tree/DepotDownloader_3.4.0).

## System libraries

Debian packages, the .NET runtime bundled with DepotDownloader, SteamCMD, and
libraries copied from the upstream image retain their respective licenses and
notices. The Dockerfile preserves the upstream system documentation alongside
the copied libraries.

## Source publication versus image distribution

This repository provides build instructions, not a redistribution of the game.
If you publish a built container image, review the obligations for all included
components, including required notices and corresponding source for GPL
components. Linking to this repository alone does not satisfy every component's
redistribution requirements.
