# syntax=docker/dockerfile:1
# ARM64 userspace with Box64/Box32 translating the proprietary x86 server.
ARG UPSTREAM_IMAGE=ghcr.io/runescape/rsdw-dedicated@sha256:c35701edb05619fd28bfb37856b6a323c10bc8aa6466fb57b3e1b232936294dc
FROM --platform=linux/amd64 ${UPSTREAM_IMAGE} AS upstream

FROM debian:trixie-slim AS box64-build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake python3 ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*
ARG BOX64_COMMIT=fbbb0544f770de73d04598079dec43644df3d462
RUN curl -fsSL "https://codeload.github.com/ptitSeb/box64/tar.gz/${BOX64_COMMIT}" | tar xz -C /tmp \
    && cmake -S "/tmp/box64-${BOX64_COMMIT}" -B /tmp/build \
       -DRPI4ARM64=1 -DBOX32=ON -DCMAKE_BUILD_TYPE=Release -DNOGIT=1 \
    && cmake --build /tmp/build -j4 \
    && cmake --install /tmp/build --prefix /opt/box64 \
    && install -Dm644 "/tmp/box64-${BOX64_COMMIT}/LICENSE" /opt/box64/share/doc/box64/LICENSE

FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl jq pwgen gettext-base unzip libstdc++6 libgcc-s1 \
    libatomic1 libtinfo6 libncurses6 libcurl4t64 libssl3t64 python3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 steam
COPY --from=box64-build /opt/box64/ /usr/local/
COPY --from=box64-build /etc/box64.box64rc /etc/box64.box64rc
COPY --from=box64-build /usr/lib/box64-x86_64-linux-gnu/ /usr/lib/box64-x86_64-linux-gnu/
COPY --from=box64-build /usr/lib/box64-i386-linux-gnu/ /usr/lib/box64-i386-linux-gnu/
COPY --from=upstream --chown=1000:1000 /home/steam/ /home/steam/
COPY --from=upstream /etc/default/ /etc/default/
COPY --from=upstream /usr/lib/x86_64-linux-gnu/ /opt/x86/lib64/
COPY --from=upstream /usr/lib/i386-linux-gnu/ /opt/x86/lib32/
COPY --from=upstream /usr/share/doc/ /usr/share/doc/upstream/
COPY --from=upstream /bin/bash /opt/x86/bash
COPY --from=upstream /entry.sh /entry.sh
ADD https://raw.githubusercontent.com/runescape/rsdw-dedicated/56f379b58ab3369894a91ad473e247942dfea87f/LICENSE /usr/share/doc/dragonwilds/LICENSE.upstream
ADD https://raw.githubusercontent.com/runescape/rsdw-dedicated/56f379b58ab3369894a91ad473e247942dfea87f/LICENSE.steamcmd /usr/share/doc/dragonwilds/LICENSE.steamcmd
ADD --checksum=sha256:d9fb612ccebc1db8eeea3b4045d2221ec70431381393ce908fb72f01d4f9c812 https://github.com/SteamRE/DepotDownloader/releases/download/DepotDownloader_3.4.0/DepotDownloader-linux-arm64.zip /tmp/depot.zip
RUN unzip /tmp/depot.zip -d /opt/depotdownloader && rm /tmp/depot.zip
COPY patch-upstream.py /tmp/patch-upstream.py
RUN python3 /tmp/patch-upstream.py && rm /tmp/patch-upstream.py
ENV HOME=/home/steam STEAMAPPID=4019830 STEAMAPP=rsdw \
    STEAMCMDDIR=/home/steam/steamcmd STEAMAPPDIR=/home/steam/rsdw-dedicated \
    STEAMAPPVALIDATE=0 GAMELIFT=false DEVBUILD_PRESIGNED_URL="" \
    RSDW_SERVER_NAME="Dragonwilds Pi" RSDW_PORT=7777 RSDW_ADMINS="" \
    RSDW_ADDITIONAL_ARGS="" BOX64_LD_LIBRARY_PATH=/opt/x86/lib64 \
    BOX86_LD_LIBRARY_PATH=/opt/x86/lib32 BOX64_BASH=/opt/x86/bash \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 \
    BOX64_DYNAREC_STRONGMEM=1 OPENSSL_ia32cap=0 \
    BOX64_LD_PRELOAD=/opt/x86/lib64/libstdc++.so.6 \
    BOX64_EMULATED_LIBS=libssl.so.3:libcrypto.so.3:libzstd.so.1:libgcrypt.so.20:libgpg-error.so.0
COPY --chmod=755 entrypoint.sh /pi-entrypoint.sh
COPY LICENSE /usr/share/doc/dragonwilds/LICENSE
USER 1000:1000
WORKDIR /home/steam
EXPOSE 7777/udp 8888/udp
ENTRYPOINT ["/bin/bash", "/pi-entrypoint.sh"]
