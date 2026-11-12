# Asset provenance

This file records the origin of the artwork shipped with Nebula Music Center. It is
not a substitute for a legal review, but it is the project's written record of where
each asset came from.

## Nebula logo and app icon

- **Full logo source:** `branding/nebula-logo.png`
- **App icon:** `nebula.png`, cropped from the purple circle in the full logo,
  including the circle and everything inside it, with transparent corners.
- **Copyright:** Copyright (C) 2026 Roger Barthares.
- **License:** distributed under GPL-3.0-only with the application.
- **Evidence:** original source image supplied by the copyright holder.

## Sync log icon

- **File:** `sync-log.png`
- **Icon:** Lucide `file-clock`.
- **Source:** <https://lucide.dev/icons/file-clock>
- **License:** ISC, with Feather-derived portions under MIT. See
  `LICENSES/Lucide.txt`.

## Repeat and shuffle icons

- **Location:** vector paths drawn in `nebula.py` (`player_icon` / `mode_icon`).
- **Icons:** `repeat`, `repeat-one`, `repeat-off`, `shuffle`, `shuffle-off`.
- **Source:** derived from Lucide's icon set.
- **License:** ISC, with Feather-derived portions under MIT. See
  `LICENSES/Lucide.txt`.

## Other UI icons

- The remaining interface glyphs are drawn in `nebula.py`, use Qt standard icons,
  or are emoji rendered by the user's system font. They are not separate bundled
  image files.

## Third-party fonts and libraries

See `THIRD_PARTY_LICENSES.md` for the bundled fonts, Qt/PySide6, FFmpeg, mutagen and
the native libraries. Those components keep their own copyrights and licenses.
