# Third-party licence audit for Nebula Music Center

Audited: 2026-11-12  
Target: Nebula Music Center 1.26, released under **GPL-3.0-only**.

This is a distribution audit, not legal advice. It covers the files actually shipped
in the source tree and in the `.deb`, plus the external programs the app invokes.

## Verdict

- **No known bundled licensing blocker remains.** The RainbowCrack `rcrack` binary
  and its `README-rcrack.txt` were removed in 1.25 along with the Audible `.aax`
  import feature. There is no bundled `rcrack`, rainbow-table payload, activation
  byte setting or `.aax` importer in this version.
- **The application itself is now licensed under GPL-3.0-only.** `LICENSE`, source
  headers, `SOURCE_OFFER.md`, `PROVENANCE.md` and `TRADEMARK.md` are present in the
  release tree.
- **The old conditional Qt components are gone.** Qt VirtualKeyboard and Qt PDF,
  including their libraries and plugins, were removed in 1.26 because the app does
  not use them.
- Everything else found is compatible with GPLv3, subject to the notices and
  source-offer obligations below.

## Bundled components

| Component | Where | Licence | GPLv3 status |
|---|---|---|---|
| PySide6 6.12.0 / shiboken6 | `assets/PySide6`, `assets/shiboken6` | LGPL-3.0-only, GPL-2.0-only, GPL-3.0-only, or commercial | **Compatible** under LGPLv3. Keep dynamic linking, notices and relink/source rights. |
| Qt 6.12 libraries | `assets/PySide6/Qt/lib` | LGPL-3.0 (most modules) | **Compatible** under LGPLv3. The unused GPLv3-only modules were removed in 1.26. |
| FFmpeg 9.0.1 libraries | `assets/PySide6/Qt/lib/libavcodec.so.63`, `libavformat.so.63`, `libavutil.so.61`, `libswresample.so.7`, `libswscale.so.10` | LGPL-2.1-or-later (verified in the binaries) | **Compatible.** Ship the LGPL text and corresponding source/offer. No `--enable-nonfree` string was found. |
| mutagen 1.48.1 | `assets/mutagen` | GPL-2.0-or-later | **Compatible** with GPLv3; the "or later" permission is present in the source headers. |
| DejaVu Sans fonts | `assets/fonts/*.ttf` | Bitstream Vera / Arev font licence (permissive) | **Compatible.** Keep the copyright and licence notice with the fonts. |
| libmp3lame | `assets/lib/libmp3lame.so.0` | LGPL-2.0 | **Compatible**, but LGPL-2.0 still requires notices and source/relink compliance. Confirm the exact build. |
| libsndfile, libmpg123, libpulse, libpulse-simple, libasyncns | `assets/lib` | LGPL-2.1-or-later | **Compatible.** Notices and source/relink compliance. |
| libfreetype | `assets/lib/libfreetype.so.6` | FreeType Licence (FTL) or GPL-2.0-or-later | **Compatible** under the FTL. Keep the FTL notice. |
| libfontconfig, libharfbuzz, libxkbcommon, libX11/XCB/Xrender/Xrandr, libEGL, libbrotli, libpng, libFLAC, libogg, libvorbis, libopus | `assets/lib` | MIT / BSD / libpng / zlib-style permissive licences | **Compatible.** Preserve notices. |
| libgraphite2 | `assets/lib/libgraphite2.so.3` | LGPL-2.1-or-later, MPL-2.0, or GPL-2.0-or-later | **Compatible** under LGPLv2.1+ (which permits GPLv2-or-later relicensing). |
| ICU | `assets/PySide6/Qt/lib/libicu*.so.73` | Unicode-3.0 | **Compatible.** Preserve the Unicode notice. |
| Qt image/FFmpeg plugins | `assets/PySide6/Qt/plugins` | Qt module licences plus IJG/BSD/Zlib/Apache-2.0/MPL-2.0 components | **Compatible.** Ship Qt's third-party notices; the common texts are in `LICENSES/`. |
| Nebula code, UI text, `nebula.png`, docs | project root | Copyright (C) 2026 Roger Barthares; GPL-3.0-only | **Licensed.** `LICENSE`, source headers and source offer are present. |
| Lucide icons: repeat, repeat-one, shuffle and file-clock | vector paths in `nebula.py`; `sync-log.png` | ISC, with Feather-derived portions under MIT | **Compatible.** Ship the full `LICENSES/Lucide.txt` and keep the icon notice. |

## Removed in 1.25

The following are no longer shipped:

- `assets/bin/rcrack`
- `assets/bin/README-rcrack.txt`
- the Audiobooks **Import .aax** button and worker
- activation-byte storage and lookup
- rcrack path and rainbow-table settings
- the `.aax` preferences (one .m4b vs chapter files, artist/album organisation,
  cover retention)

The regular audiobook **Import** and **Import folder** actions remain. They move
ordinary audio files and folders and do not decrypt anything.

The non-code Audible service/DRM question is therefore no longer part of the
application's bundled feature set. MusicBrainz/Cover Art Archive metadata and
artwork still keep their own attribution and service terms.

## Removed in 1.26

- Qt VirtualKeyboard libraries and plugin
- Qt PDF library and `libqpdf.so` image plugin

Neither was imported by the application. Removing them eliminates the old
GPLv3-only Qt VirtualKeyboard condition and the Qt PDF licensing choice.

## External programs (not bundled in the `.deb`)

The app invokes these as separate processes. They are **not linked** into Nebula, but
they are still part of the user's installed system and may be listed as Recommends:

| Program | Typical licence | Note |
|---|---|---|
| `ffmpeg` / `ffprobe` | LGPL-2.1+ or GPL-2.0+ depending on the distro build | Ubuntu's build uses `--enable-gpl`; this is GPL-2.0-or-later and is compatible with a GPLv3 app as a separate program. Never use a `--enable-nonfree` build. |
| `cdparanoia` | GPL-2.0-or-later | Separate executable. |
| `eject` | GPL-2.0-or-later | Separate executable. |
| `genisoimage` / `wodim` (cdrkit) | GPL-2.0 | Separate executable; do not link or bundle it into the app. |
| `cdrdao` | GPL-2.0-or-later | Separate executable. |
| `gio` / gvfs | LGPL-2.0-or-later | Separate executable/library already on the system. |
| `gsettings` / GLib | LGPL-2.1-or-later | Separate executable. |

The system `ffmpeg` on this machine reports:

```text
ffmpeg version 6.1.1-3ubuntu5
configuration: ... --enable-gpl ... --enable-libx264 --enable-libx265 ...
```

That is acceptable for a separate-process dependency. It is not acceptable to copy
those GPL libraries into a differently licensed bundle.

## Release requirements met in 1.26

1. The full **GPL-3.0** licence text is in `LICENSE`, with copyright and SPDX headers
   in the application, launcher, build script and tests.
2. The licence texts and notices for Qt/PySide6, FFmpeg, mutagen, DejaVu,
   libmp3lame, libsndfile, libpulse, fontconfig/freetype/harfbuzz, graphite2, ICU,
   Lucide and the other bundled libraries are in `LICENSES/` and this audit. Qt's own
   third-party notice file is the authoritative list for the Qt plugins.
3. `SOURCE_OFFER.md` provides the exact source for the main libraries, the source
   archive, and a written offer for the remaining LGPL components. The libraries stay
   dynamically linked so users can replace them.
4. The GPLv3-only Qt VirtualKeyboard and the Qt PDF/PDFium modules were removed. The
   app no longer carries a conditional Qt module.
5. The external CD/FFmpeg tools remain separate executables. Their libraries are not
   copied into the Nebula package.
6. MusicBrainz/Cover Art Archive attribution and service terms remain separate from
   the GPL; the app does not relicense their data or artwork.
7. The Debian `Maintainer` and `Homepage` are filled in, and the release folder
   contains the package plus its corresponding-source archive.

## Checks used

- `find assets -maxdepth 3 -type f` and the `.deb` file list for the shipped set.
- `strings` on the bundled FFmpeg libraries: all five report
  `LGPL version 2.1 or later` / `FFmpeg version 9.0.1`; no `--enable-nonfree` found.
- The Qt 6 licensing pages and module licence tables for PySide6; VirtualKeyboard and
  PDF were removed in 1.26.
- The GPL FAQ / licence-compatibility guidance for LGPL-2.1+ and GPLv2+ combinations.
- A source-tree search confirming no `rcrack`, `.aax`, activation-byte or
  rainbow-table code or settings remain in 1.26.
- A package audit confirming no VirtualKeyboard/PDF files are present in 1.26.
