# Corresponding Source for Nebula Music Center 1.27

Nebula Music Center is licensed under **GPL-3.0-only**. The complete source code for
version 1.27 is distributed with the release as:

```text
nebula-music-center_1.27.orig.tar.xz
```

It is also available from:

```text
https://github.com/blaz101/Nebula-Music-Center
```

If the repository is not public when a binary is distributed, the source archive
above is the Corresponding Source. The archive contains the application source,
build and packaging scripts, the artwork and the license/notice files.

## Written offer

For at least three years from the date Nebula Music Center 1.27 is distributed,
Roger Barthares will provide the Corresponding Source for the application and the
bundled LGPL components to any third party, at no charge beyond the cost of
physically performing the source distribution.

Contact:

```text
Roger Barthares
roger.barthares@gmail.com
```

## Exact third-party source

The versions bundled in 1.27 include the following. These are the upstream source
archives used for the corresponding libraries:

```text
PySide6 6.12.0
https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.12.0-src/pyside-setup-everywhere-src-6.12.0.tar.xz

Qt 6.12.0
https://download.qt.io/archive/qt/6.12/6.12.0/single/qt-everywhere-src-6.12.0.tar.xz

FFmpeg 9.0.1
https://ffmpeg.org/releases/ffmpeg-9.0.1.tar.xz

mutagen 1.48.1
https://pypi.org/project/mutagen/1.48.1/#files
```

The exact source for the remaining bundled LGPL libraries (libmp3lame, libsndfile,
libmpg123, libpulse, libasyncns, freetype, fontconfig, harfbuzz, xkbcommon, the X11
helper libraries, graphite2 and the other LGPL components) is available under the
same written offer. Their names and licenses are listed in
`THIRD_PARTY_LICENSES.md`; the bundled binaries are unmodified.

The full license texts are in `LICENSES/`:

```text
LICENSES/GPL-3.0.txt
LICENSES/LGPL-3.0.txt
LICENSES/LGPL-2.1.txt
LICENSES/LGPL-2.0.txt
LICENSES/GPL-2.0.txt
LICENSES/DejaVu.txt
LICENSES/Lucide.txt
LICENSES/Apache-2.0.txt
LICENSES/BSD-3-Clause.txt
LICENSES/MPL-2.0.txt
```

This source offer does not change the license of any third-party component. Each
component remains under its own license, reproduced or referenced in
`THIRD_PARTY_LICENSES.md` and `LICENSES/`.

## Building the release

The Debian package is built with:

```bash
bash packaging/build-deb.sh
```

The build script uses the source tree in this archive and writes the package to
`release-1.27/`. It does not fetch or relicense any third-party component.
