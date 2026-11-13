# Roadmap

## 1.27.1

- [x] **Real donation links in About.** Mp3Tag, Strawberry Music Player and
  FreeFileSync now open their donation pages; the coffee line still reads
  *Temporarily unavailable*.
- [ ] **Release 1.27.1** — tag, push, and publish the `.deb`, source archive and
  `SHA256SUMS`.

## 1.27

- [x] **Replace the app icon.** Swapped the 1.26 crop for the cleaner source at
  `/home/rba/Pictures/Nebula Icon.png` (221 × 221 RGBA, transparent corners).
  - Source copied to `branding/nebula-icon.png`.
  - `nebula.png` regenerated from it at 512 × 512.
  - `PROVENANCE.md` and `branding/README.md` record the new source.
  - The package is rebuilt for 1.27, not the 1.26 assets.
- [x] **Apply the updated copy deck** (attached 2026-11-13): About, Library,
  Devices, Sync, Preferences and Audio CD strings. Applied entries: A05, C102,
  C163, C166, C176, C180, C181, C188, C194, C203, C206, C227, C239, C240, C241,
  C249, plus the About "Buy me a coffee" line set to *Temporarily unavailable*.
  - Held back: C100 — the new text asks a folder-removal confirmation, but the
    string is shown when the only collection is removed.
  - Held back: C178 — the draft text is `Include LRC files (X amount of LRC files
    found)`, which needs a real count before it can ship.
- [x] **README entry for 1.27** — release notes are in `README.md`.
- [x] **Stage and push the release** — v1.27 tagged and published with the
  `.deb`, source archive and `SHA256SUMS` attached.
  - Do not rebuild or replace the 1.26 release assets.
