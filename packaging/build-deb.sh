#!/bin/bash
# Copyright (C) 2026 Roger Barthares
# SPDX-License-Identifier: GPL-3.0-only
# Build nebula-music-center_1.27.1_amd64.deb from the source tree.
# The bundle is the same one the zip and the AppImage ship: PySide6, mutagen and
# the X11/font/audio helper libraries, so the package needs no distro Qt.
set -euo pipefail

V=1.27.1
PKG=nebula-music-center
ARCH=amd64
SRC=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
RELEASE_DIR=$SRC/release-$V
OUT=$RELEASE_DIR
DOWNLOADS_DIR=${NMC_DOWNLOADS_DIR:-$HOME/Downloads/NMC}
STAGE=$(mktemp -d /tmp/deb$V-XXXXXX)
trap 'rm -rf "$STAGE"' EXIT
APPDIR=$STAGE/opt/$PKG

test -f "$SRC/nebula.py"
test -d "$SRC/assets/PySide6"

mkdir -p "$APPDIR" "$STAGE/DEBIAN" \
         "$STAGE/usr/bin" \
         "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/icons/hicolor/256x256/apps" \
         "$STAGE/usr/share/doc/$PKG"

# only what the app runs on: the script, the launcher, the icon, the docs and
# the bundled runtime.  The test suite and the screenshot folder stay in the
# source tree; they are development material, not part of an installed app.
cp -a "$SRC/run.sh" "$SRC/nebula.py" "$SRC/nebula.png" "$SRC/sync-log.png" \
      "$SRC/README.md" "$SRC/SYNC_PART1.md" "$SRC/SYNC_PART2.md" \
      "$SRC/THIRD_PARTY_LICENSES.md" "$SRC/requirements.txt" "$SRC/assets" "$APPDIR/"
find "$APPDIR" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "$APPDIR" -name '*.pyc' -delete
# marks an installed bundle: run.sh copies it into ~/.cache/Nebula and runs it there
printf '%s\n' "$V" > "$APPDIR/BUNDLE_VERSION"

# launcher on $PATH: hands off to the bundle's own run.sh
# Prefers the package copy in /opt, which refreshes ~/.cache/Nebula/app on upgrade.
# If /opt has been removed, runs the copy already in ~/.cache/Nebula/app.
cat > "$STAGE/usr/bin/$PKG" <<'LAUNCH'
#!/bin/sh
if [ -f /opt/nebula-music-center/run.sh ]; then
    exec /opt/nebula-music-center/run.sh "$@"
fi
exec "${NEBULA_CACHE:-$HOME/.cache/Nebula}/app/run.sh" "$@"
LAUNCH
chmod 0755 "$STAGE/usr/bin/$PKG" "$APPDIR/run.sh"

cat > "$STAGE/usr/share/applications/$PKG.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Nebula Music Center
GenericName=Music Player
Comment=Music library, player and tagger
Exec=/usr/bin/$PKG %U
TryExec=/usr/bin/$PKG
Icon=$PKG
Terminal=false
Categories=AudioVideo;Audio;Player;Qt;
Keywords=music;audio;player;library;cd;sync;mp3;flac;
StartupNotify=true
DESKTOP

install -m 0644 "$SRC/nebula.png" "$STAGE/usr/share/icons/hicolor/256x256/apps/$PKG.png"
install -m 0644 "$SRC/README.md" "$STAGE/usr/share/doc/$PKG/README.md"
install -m 0644 "$SRC/SYNC_PART1.md" "$STAGE/usr/share/doc/$PKG/SYNC_PART1.md"
install -m 0644 "$SRC/SYNC_PART2.md" "$STAGE/usr/share/doc/$PKG/SYNC_PART2.md"
install -m 0644 "$SRC/THIRD_PARTY_LICENSES.md" "$STAGE/usr/share/doc/$PKG/THIRD_PARTY_LICENSES.md"
install -m 0644 "$SRC/LICENSE" "$STAGE/usr/share/doc/$PKG/LICENSE"
install -m 0644 "$SRC/SOURCE_OFFER.md" "$STAGE/usr/share/doc/$PKG/SOURCE_OFFER.md"
install -m 0644 "$SRC/TRADEMARK.md" "$STAGE/usr/share/doc/$PKG/TRADEMARK.md"
install -m 0644 "$SRC/PROVENANCE.md" "$STAGE/usr/share/doc/$PKG/PROVENANCE.md"
mkdir -p "$STAGE/usr/share/doc/$PKG/LICENSES"
cp -a "$SRC/LICENSES/." "$STAGE/usr/share/doc/$PKG/LICENSES/"

cat > "$STAGE/usr/share/doc/$PKG/copyright" <<'COPY'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: nebula-music-center
Source: https://github.com/blaz101/Nebula-Music-Center

Files: *
Copyright: 2026 Roger Barthares
License: GPL-3.0-only
 This program is free software: you can redistribute it and/or modify it
 under the terms of the GNU General Public License as published by the Free
 Software Foundation, version 3 only.
 .
 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
 .
 On Debian systems the complete GPLv3 text is in
 /usr/share/common-licenses/GPL-3. The complete text is also installed as
 /usr/share/doc/nebula-music-center/LICENSE.

Files: assets/PySide6/* assets/shiboken6/*
Copyright: Qt Company and contributors
License: LGPL-3.0-only
 The bundled PySide6, shiboken6 and Qt libraries keep their own copyright
 and license. See LICENSES/LGPL-3.0.txt and THIRD_PARTY_LICENSES.md.

Files: assets/PySide6/Qt/lib/libav*
Copyright: FFmpeg contributors
License: LGPL-2.1-or-later
 See LICENSES/LGPL-2.1.txt and THIRD_PARTY_LICENSES.md.

Files: assets/mutagen/*
Copyright: Mutagen contributors
License: GPL-2.0-or-later
 See LICENSES/GPL-2.0.txt and THIRD_PARTY_LICENSES.md.

Files: assets/fonts/*
Copyright: Bitstream, Inc. and DejaVu contributors
License: Bitstream-Vera
 See LICENSES/DejaVu.txt.

Files: assets/lib/*
Copyright: respective upstream authors
License: LGPL-2.1-or-later or permissive
 See THIRD_PARTY_LICENSES.md and LICENSES/ for the component notices.

Files: sync-log.png
Copyright: Lucide Icons and contributors
License: ISC
 See LICENSES/Lucide.txt.

Files: nebula.png branding/nebula-logo.png
Copyright: 2026 Roger Barthares
License: GPL-3.0-only
 The name and logo are subject to the trademark policy in TRADEMARK.md.
COPY

SIZE=$(du -sk "$STAGE" | cut -f1)
cat > "$STAGE/DEBIAN/control" <<CONTROL
Package: $PKG
Version: $V
Architecture: $ARCH
Maintainer: Roger Barthares <roger.barthares@gmail.com>
Installed-Size: $SIZE
Section: sound
Priority: optional
Homepage: https://github.com/blaz101/Nebula-Music-Center
Description: Music library, player, tagger and device sync
 Nebula Music Center plays and tags a local music library, rips and burns
 audio CDs with buffering so the drive is not read during playback, and
 syncs to USB players, iPods and MTP phones.
 .
 It keeps your settings and library in ~/Nebula and its caches in
 ~/.cache/Nebula. It brings its own Qt, so no distribution Qt is needed.
Recommends: gvfs-backends, ffmpeg, cdparanoia, eject, genisoimage, wodim | cdrdao, libssl3 | libssl3t64
CONTROL

# system libraries the bundle does not carry (taken from ldd against assets/)
DEPS="python3 (>= 3.9), libc6 (>= 2.34), libstdc++6, libgcc-s1"
DEPS="$DEPS, libx11-6, libx11-xcb1, libxcb1, libxcb-glx0, libxcb-randr0"
DEPS="$DEPS, libxcb-render0, libxcb-shm0, libxcb-sync1, libxcb-xfixes0"
DEPS="$DEPS, libxcomposite1, libxcursor1, libxdamage1, libxfixes3, libxi6"
DEPS="$DEPS, libxinerama1, libxext6, libxrender1"
DEPS="$DEPS, libgl1, libegl1, libglvnd0, libglx0, libdrm2, libepoxy0"
DEPS="$DEPS, libdbus-1-3, libglib2.0-0, libfontconfig1, libfreetype6, libexpat1"
DEPS="$DEPS, zlib1g, libzstd1, libbz2-1.0, liblzma5, libpcre2-8-0, libsystemd0"
DEPS="$DEPS, libcap2, libgcrypt20, libgpg-error0, liblz4-1, libmd0, libbsd0"
DEPS="$DEPS, libgssapi-krb5-2, libkrb5-3, libk5crypto3, libkrb5support0"
DEPS="$DEPS, libkeyutils1, libcom-err2, libwayland-client0, libpulse0"
printf 'Depends: %s\n' "$DEPS" >> "$STAGE/DEBIAN/control"

# keep the package tidy: drop anything the build left behind
rm -rf "$STAGE/usr/share/doc/$PKG/.git"

mkdir -p "$OUT" "$DOWNLOADS_DIR"
find "$STAGE" -type d -exec chmod 0755 {} +
find "$STAGE" -type f -exec chmod 0644 {} +
chmod 0755 "$STAGE/usr/bin/$PKG" "$APPDIR/run.sh"
find "$STAGE" -type f -name '*.so*' -exec chmod 0644 {} +

dpkg-deb --root-owner-group -Zzstd -z19 --build "$STAGE" "$OUT/${PKG}_${V}_${ARCH}.deb"
# one copy per version in the release folder, and a flat copy for distribution
cp -f "$OUT/${PKG}_${V}_${ARCH}.deb" "$DOWNLOADS_DIR/"
ls -lh "$OUT/${PKG}_${V}_${ARCH}.deb" "$DOWNLOADS_DIR/${PKG}_${V}_${ARCH}.deb"
