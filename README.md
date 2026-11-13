# Nebula Music Center 1.28

## What's new in 1.28

- **Equalizer.** A 25-band graphical EQ (20 Hz – 20 kHz, 0.1 dB steps) and a
  parametric EQ (peak, low-shelf and high-shelf bands with frequency, gain and Q).
  Each tab keeps its own curve, so switching between them changes nothing.
- **Presets and profiles.** Save named curves for each tab, and import or export
  Equalizer APO profiles (`.txt`) or Nebula JSON profiles.
- **Per-band readouts.** Every graphic band shows its gain above the slider.
- **Bit-perfect switch.** Bypasses the equalizer and disables its controls. The
  exclusive output path itself is not part of this release.
- **Equalizer needs ffmpeg.** The equalised audio is rendered with the system
  `ffmpeg` when a track starts, and the package recommends it. Without ffmpeg the
  window still opens for editing, but nothing is applied.

## What's new in 1.27.1

- **Real links in About.** The inspiration entries now open the Mp3Tag, Strawberry
  Music Player and FreeFileSync donation pages; the coffee line still says the
  support page is temporarily unavailable.

## What's new in 1.27
- Updated icon
- changed descriptions

## What's new in 1.26

**1.26 is the first official release of Nebula Music Center.**

- **GPLv3.** Nebula Music Center is now released under **GPL-3.0-only**. The
  copyright holder is Roger Barthares; the full license is in `LICENSE`.
- **The source offer is documented.** `SOURCE_OFFER.md` identifies the
  Corresponding Source and the exact upstream source for the bundled libraries.
- **Only the Qt modules the app uses are bundled.** Qt VirtualKeyboard and Qt PDF,
  including their plugins and libraries, are not included.
- **The new branding is in place.** The app icon is the purple circular mark from
  the full logo; the full logo is preserved under `branding/`.
- **The sync-log icon is Lucide file-clock.** The Lucide notice is included under
  `LICENSES/Lucide.txt`.

## License

Copyright (C) 2026 Roger Barthares.

Nebula Music Center is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free Software
Foundation, version 3 only.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

The full license is in [LICENSE](LICENSE). The Nebula name and logo are covered by
the separate [TRADEMARK.md](TRADEMARK.md) policy; the GPL does not grant trademark
rights. Corresponding Source for this release is available from
[SOURCE_OFFER.md](SOURCE_OFFER.md) and:

```text
https://github.com/blaz101/Nebula-Music-Center
```

## Run it from the source archive

Extract the release archive and start the app:

```bash
tar -xf nebula-music-center_1.28.orig.tar.xz
cd nebula-music-center-1.28
./run.sh
```

`assets/` contains PySide6 6.12 (including the QtMultimedia/FFmpeg backend),
mutagen, and the X11/font/audio helper libraries that some distributions leave
out. `run.sh` puts the bundled Qt and codec libraries first on the loader path
(GPU and audio drivers still come from your system), then starts the app.
Nothing is installed system-wide and nothing is written outside your home.

```bash
./run.sh --check      # Python, PySide6, Qt and mutagen versions, and asset check
```

## Install it (.deb, Debian and Ubuntu)

```bash
sudo apt install ./nebula-music-center_1.28_amd64.deb
nebula-music-center              # or pick it from the menu
```

It installs to `/opt/nebula-music-center` with its own Qt, adds
`/usr/bin/nebula-music-center` and a menu entry, and reads the same
`~/Nebula` and `~/.cache/Nebula` folders as the source archive — so both ways of
running it share one library. `apt remove nebula-music-center` takes the
program away and leaves your music and settings alone (add `--purge` plus a delete of
`~/Nebula` and `~/.cache/Nebula` if you want those gone too).

## Where everything is kept

```
~/Nebula/                                    settings and data
  settings/   config.json, profiles.json, smart_playlists.json, queue-meta.json
  library/    library.db, collections/, playlists/
  sync/       hashdb/, manifests/

~/.cache/Nebula/                             rebuildable
  covers/     artwork cache
  tmp/        cd-buffer/, device-buffer/, cd/, devplay/, rip and burn staging
```

The whole of `~/.cache/Nebula` carries a `CACHEDIR.TAG`, so a backup pointed at
`~/Nebula` is all you need and never walks a buffer. Your music folders stay where
they are; the app only reads them, and only the files above are ever written.
`NEBULA_DATA=/some/folder` and `NEBULA_CACHE=/some/cache` move the two roots (a
portable install on a stick, or a Flatpak's own directories). Anything in `tmp/`
untouched for a day is deleted at start-up.

Requirements: 64-bit Linux, glibc 2.34+ (Ubuntu 22.04, Debian 12, Fedora 36 or
newer), Python 3.10+ (`python3` on PATH). The bundled wheels are manylinux_2_34,
so they run on any distribution from that baseline onwards.

Without the bundle (system PySide6, Qt 6.5+):

```bash
pip install -r requirements.txt
python3 nebula.py
```

Phones (MTP) need `gvfs-backends` (Debian/Ubuntu) or `gvfs-mtp` (Fedora/Arch).
Online lookups (CDDB, MusicBrainz, Discogs, Cover Art Archive) and `ffmpeg` for
ReplayGain measurement are optional; everything else works offline.

## The library tab

**Search box.** One rounded field: `✕` clears the query on the left, the wrench
with its drop-down arrow opens the library options on the right. The field
understands Strawberry's filter language:

```
artist:aphex                    album:"Selected Ambient Works"
year:>=1990 year:<=1999         bitrate:>320k
rating:>=4                      length:<3:30
electronic -genre:pop           artist:boards OR artist:aphex
(title:alpha OR title:beta) year:1992
```

Fields: `title artist albumartist album composer performer grouping genre comment
filename path track disc year samplerate bitdepth bitrate playcount skipcount length
rating loved format added lastplayed`. Operators: `: = != < > <= >=`, `-term`
excludes, `AND`/`OR`/parentheses combine, `"quotes"` keep spaces. A bare word
searches every text field. Numeric fields accept `k`/`M` suffixes and `m:ss`
durations.

**A–Z hierarchy.** The library shows exactly three levels — artist, album,
track — inside letter sections:

```
A
  Air
    [cover] Moon Safari
      ♥ 01. La Femme d'Argent
        02. Sexy Boy
B
  Bonobo
    [cover] Black Sands
      01. Prelude
```

Artist and album rows use the full tag values, and tracks are labelled
`01. Full title`; there is no separate Track/Artist/Album column taking space
away from the names. Each expandable row has a small solid triangle at its left edge
(white on selection, accent on hover), so collapsed artists and albums are
obvious. Letters, artists and albums are all collapsible; search results expand
everything automatically. The detail table is still available — tick **Details
columns** in the wrench menu (it is off by default).

**Grouping.** Presets: Artist / Album, Album artist / Album, Album, Genre, Year,
Folder, Album artist / Album / Disc, Year / Album, Genre / Artist / Album,
Composer, File type, Sample rate, Bit depth, Bitrate, flat list. The **…**
button opens the three-level group-by dialog over 16 fields, with saved
groupings that persist in the config.

**Folder grouping** now nests as deep as the filesystem goes, then continues
with the remaining grouping levels underneath. A folder that also contains files
directly keeps them.

**Details list** (optional, off by default). Columns: Track, Title, Artist,
Album, Length, Year, Genre, Rating, Play count, Type. Turn them on from the
options menu or by right-clicking the header; drag a header section to reorder
the columns (the order and widths are remembered). Click to sort, again for
descending, a third time for the album order. Album rows show year and total
length.

**Per-track state.** 0–5 stars, a loved flag (♥ prefix), play counts, last played
and a skip counter, stored in SQLite and preserved across rescans.

**Multiple collections.** The selector to the left of "Group" switches between
independent libraries, each with its own folder list and database. Create,
rename and remove them from the wrench menu → *Collections*. Removing keeps the
database file on disk.

**Right-click menu.** Play now, Append to queue, Queue to play next, Replace
current playlist, Open in new playlist, Add to playlist, Rating, Love/Unlove,
Search for this, Edit tags, Organize files…, Rescan, Copy path / "Artist —
Title", Show in file browser, Copy to device, **Look up metadata & cover…**,
**Analyse ReplayGain**, and **Delete** →
*Remove from library (keep file)*, *Move file to Trash* or
*Delete file permanently…*. Trash moves files to `~/Nebula/trash`.

**Options menu** (the wrench): music folders, rescan, reset play counts,
collections, details on/off, column chooser, group by…, saved groupings, locate
playing track, Find duplicates… (three match fields, keep-first selection),
collection statistics. Covers, A–Z dividers, auto-open and the double-click
action now live in **Tools > Preferences** (Ctrl+P).

**Mouse**: single click selects, double-click queues (or plays, configurable),
middle-click enqueues a track or a whole group.

## The Tags tab (mp3tag-style menus)

Switching to **Tags** swaps the whole menu bar for mp3tag's: **File**, **Edit**,
**View**, **Convert**, **Actions**, **Tag Sources** and **Help**. Every entry is
live, and shortcuts follow the visible set (`Ctrl+S` saves tags here and the
queue on the library tab).

The tag panel on the left edits all selected files at once (mixed fields show
`< keep >`). Labels sit above the fields, in two columns, with the cover art and
the file count on top — the layout of current mp3tag rather than the old form.

The file list on the right uses mp3tag's columns: **Filename, Title, Track,
Artist, Album artist, Album, Disc, Tag, Year, Genre, Comment**. *Tag* names the
container and the tag family it carries, and for MP4/M4A it is measured from the
stream, so an AAC file reads `MP4 (AAC)` and only a real ALAC file reads
`MP4 (ALAC)`. Click a header to sort; edited cells turn amber until saved.
Under the list, the **Filter** row accepts words and hides rows that do not match
(`Ctrl+F` jumps to it), and the file / selection / size counts sit on its right.

The tag panel's **Extended** section is a free-form key/value list, like mp3tag's
full version: **Add** a key, edit a value, or **Remove** a key. Extended keys are
stored as `TXXX` frames (MP3, WAV/AIFF), `----:com.apple.iTunes:` atoms (M4A/MP4)
and Vorbis comments (FLAC/Ogg/Opus). An empty value deletes the key. With several
files selected, keys are the union across them and differing values show `< keep >`.
The cover in the panel follows the selected file (the first file when nothing is selected).

Right-click a file for **Extended tags…**, the whole-tag window: every tag the
file carries — the core fields and its own keys in one list — with **＋** to add a
tag, **✎** to edit the selected value and **✕** to remove it, and the cover with
its format, dimensions and size on the right. **‹‹ ››** move between the selected
files and keep what you typed. OK hands the values back to the file list unsaved,
so `Ctrl+S` still decides when the disk is written.

- **File**: open a folder (`Ctrl+O`), add files (`Ctrl+Shift+O`), remove rows (`Del`), save tag (`Ctrl+S`), revert (`Ctrl+R`), close list (`Ctrl+W`).
- **Edit**: 80-step undo/redo (`Ctrl+Z` / `Ctrl+Y`), cut/copy/paste (`Ctrl+X/C/V`) of tag cells as TSV, select all/deselect/invert, filter, find and replace (`Ctrl+H`).
- **View**: toggle the toolbar, tag panel, file list and filter row, pick **Columns**, refresh from disk (`F5`).
- **Convert**: filename → tag (`Alt+1`), tag → filename (`Alt+2`), tag → tag, auto-numbering.
- **Actions**: replace (regex allowed), case conversion (title / lower / UPPER), save.
- **Tag Sources**: MusicBrainz search with Cover Art Archive covers (`Ctrl+M`).
- **Remove selected files** (`Del`) only drops rows from the list; files on disk stay untouched until you save.

Removing a music folder (**Music → Remove music folder…**) drops every track it
contributed from the library at once, including when it was the last folder.

## Online metadata and covers

*Look up metadata & cover…* searches MusicBrainz for the selected album and shows
matching releases (artist, year, country, track count, label) with the Cover Art
Archive front cover preview. From there:

- **Save front cover** writes `cover.jpg`/`cover.png` next to the album's files.
- **Apply album tags** fetches the release's track list and writes album, album
  artist, year, genre, and — when the file count matches the release — track
  titles, numbers and disc numbers. The library index is refreshed immediately.

No API key is needed. The user agent identifies Nebula Music Center, covers are cached in
`~/.cache/Nebula/covers`, and network errors are reported in the dialog rather
than breaking the library. Requests are paced to MusicBrainz's one-per-second
policy and 429/5xx answers are retried with a short backoff, so a burst of
searches no longer dies with "HTTP 503 Service Temporarily Unavailable". If the
artist+album phrase finds nothing, the search retries with the album title
before its bracket (e.g. `SERENS (A Selection…)` → `SERENS`).

**Audio CDs** are named from their table of contents. CDDB and MusicBrainz are both
matched by disc ID — each computes its own ID from the TOC — while Discogs is
searched by artist/album text after sign-in. Tools > Preferences > Identification
sets which sources are used and in what order (default: CDDB, Discogs,
MusicBrainz); inserting a disc tries them in that order and stops at the first one
that knows it, reporting a source that is down in the CD tab's status line instead
of failing the lookup. CDDB itself is asked of GNUdb first, then the dBpoweramp
freedb server and the RetroBridge gateway, so an outage or a blocked host doesn't
leave the disc unnamed. CDDB's protocol has no text search, so *Find release*
searches MusicBrainz and Discogs only.

## ReplayGain

The small **RG** button in the player bar offers *Off*, *Track gain* and *Album
gain*, a pre-amp, and a clipping guard that caps boosts at the track peak. Gains
are read from `REPLAYGAIN_*` tags (ID3 `TXXX`, Vorbis comments, MP4 freeform) and
applied to the output volume, so it works for every format the player supports.

*Analyse ReplayGain* (right-click menu, or the RG menu for the current track)
measures loudness with `ffmpeg`'s EBU R128 filter, converts it to a −18 LUFS
target and writes the tags back. It runs in the background with a progress
dialog; **Cancel** stops after the track being measured. It writes the **track**
gain and peak for every measured file, and when the selection holds two or more
tracks from the same album it measures that album again as one programme with
the same filter and writes the **album** gain and peak (`REPLAYGAIN_ALBUM_GAIN`
/ `_PEAK`) to those tracks too. Tracks are grouped by albumartist and album, or
by folder when there is no albumartist; a single track gets track tags only. If
`ffmpeg` is not installed the command says so; existing tags still work.

## Player and the other tabs

- Player bar: cover viewer, format pills (`[FLAC] [24-bit / 96.0 kHz] [984 kbps]`),
  shuffle, repeat off/all/one, stop after track, volume, seek, spectrum.
- **Spectrum**: on Qt 6.8+ it uses the player's real audio buffers. On older Qt
  it decodes the playing file with `QAudioDecoder` in the background and keeps
  one spectral frame per 80 ms (cached in `~/.cache/Nebula/tmp/spectrum`). Only if
  the Qt build has neither does it show an animated placeholder, labelled as
  such in the tooltip. **Stop** clears the analyser and stops its timer instead
  of leaving the last bars frozen.
- Queue: Strawberry columns, zebra rows, blue now-playing row, drag reorder,
  header sort, undo/redo, `.m3u8` save/load, file drops.
- **Devices** shows the music on each connected device, with the devices in a bar
  across the top or a list down the side (Preferences > Library). **Select device
  folder…** picks the folder to show, remembered per device; **List** groups it as
  artist > album > numbered track and **Covers** as one cover per album. The search box
  filters either view with the library's `field:value` terms. **Play** plays what is
  shown; a click on a cover opens the album, a double-click queues it, and the context
  menu covers play, add to queue, the folder picker and refresh. Queued device music is
  the file on the device, named *MTP device*, *iPod* or *USB device* in the queue's Source
  column; Preferences > Playback can copy the upcoming device tracks into a local buffer
  first. Disconnecting the device removes its queued tracks and buffered copies. Sending
  files and folders to the device still works. Right-click a device to rename it or
  **Remove from the Devices tab…**; removed devices wait under **Preferences > Devices**
  and **Restore selected** brings them back, connected or not. MTP requires gvfs and an
  unlocked phone in File Transfer mode.
- **Syncing** stores profiles for one or more library folders and a device/folder
  destination. **Folder(s) to sync** takes as many folders as you add, or switch **What
  to sync** to **Selected items** and tick individual music and audiobooks in the
  selection window (**Select All** and **Unselect All** are there too). Selected-item
  **Mirror** sync copies those files and removes copies it wrote for items that are no
  longer ticked; **Update** never deletes, and files the profile never wrote are left
  alone.
  The tab has three buttons. **Compare** only builds the plan and lists it.
  **Sync** runs the plan you reviewed last (it asks you to press Compare first if
  there is none). **Compare+Sync** compares fresh and then runs the result in one
  step. The **Compare by** option picks how files are compared; neither mode is
  hidden for a phone or a folder, only the cost differs. The **Device filesystem**
  option says what the destination can store in a file name, because that decides
  whether a name may change on the way over: *exFAT* and *MTP (mtpfs)* carry UTF-16
  names, so a file keeps its PC name to the character, while *FAT32* drops
  `* ? : " < > | \`, control characters and a trailing space or dot — the log's `NAME`
  line names any file whose name changed. FAT32 is the default, matching earlier
  builds. Two library files that would land on the same device name — including two
  that differ only by case, which these devices treat as one name — still get a
  ` (2)` suffix; that is the only editing any filesystem does to a name it can store.

  - *Bit-by-bit (exact)* (default) streams both copies byte-for-byte in bounded
    chunks, so any changed byte is caught, including a same-size edit. This mode
    reads the device copy in full every time; on MTP that can take a while, and the
    log says so when a phone is the destination. Missing device files are found by
    comparing the device listing with the source tree.
  - *Fast hash (SHA-256, cached)* uses a content digest per PC file plus a per-device
    manifest of what was actually written to that device. Each PC file's digest is
    cached in `~/Nebula/sync/hashdb/` and reused while its size and mtime are
    unchanged (so a same-size tag edit is noticed when the timestamp moves); the
    manifest in `~/Nebula/sync/manifests/` is keyed by the device's identity and
    the device path, and records the size, digest and device timestamp of each
    successful transfer. Later compares read no device file when the manifest record
    matches the PC digest and a fresh directory listing still shows the same size and
    timestamp. A file whose device timestamp moved is checked and copied again if it
    differs; a file missing from the device is planned as *restore* and copied back
    from the PC (the PC original is never deleted because the device lacks it). This
    mode is fast, not proof: an edit made outside the app that keeps both size and
    timestamp can go unnoticed, and MTP can't supply a trustworthy content hash.
    **Verify content** — a button that appears beside Compare/Sync only while this mode
    is chosen, never in Bit-by-bit where it would be redundant — reads every device file
    and compares it byte for byte when
    certainty is required, and rewrites each verified file's manifest record (digest, size
    and the listed timestamp) from that read, dropping the record of a file whose device
    copy turned out different. The plan's Equal count and the status line say *cached,
    unverified* or *byte-verified*, so the mode never claims more than it did. A
    reviewed plan keeps the verification level it was compared with when Sync runs it.
    The same listing also covers the device's own files: one the library does not claim
    is checked before anything happens to it. A size no library file shares cannot be
    library content, so it is settled without a read; otherwise the device file is hashed
    and the library searched for that content (a PC file is hashed once and cached).
    Content the library is about to send is kept where it is and adopted as that file's
    copy, so a file copied to the device by hand is neither deleted nor written again; a
    second copy of content the device already holds is a duplicate and goes; content the
    library does not have at all is removed in Mirror and only reported in Update. The
    log names every decision (`SCAN`, `KEEP`, `EXTRA`, `READ`).

  All device reads, writes and deletes go through one worker, because MTP is serial;
  a manifest record is written only after the device write succeeds, so a refused or
  interrupted transfer is never treated as verified.

  Update never deletes destination-only files; Mirror does, after a
  confirmation that says files whose content matches the library are kept where they
  are. Folder and USB destinations use the same engine. MTP copies are
  written through the gvfs mount (so artist/album names with spaces arrive
  unchanged), fall back to `gio copy` when the mount refuses a write, and each
  file is size-checked afterwards; failures are named in the log. Autosync waits
  until the phone actually answers (file transfer enabled) instead of firing the
  moment the mount appears, retries while it stays locked, and gives up if the
  device is unplugged. The status dot beside the device turns green as soon as the
  device answers (after File transfer is enabled) and gray when it is unplugged or
  unreadable. The same line shows **last sync** with the time the profile's last
  finished sync ran (`last sync 2026-10-20 14:03`), or *never synced*. Compare
  does not change it. The time is saved with the profile. A Fast hash profile also
  shows *last verified 2026-10-27 09:05* — when the device contents were last read in
  full — or *not verified in full* if that has never happened; a bit-by-bit sync needs
  no such note, since reading both copies is what it does.
  While a task runs, its button turns blue, the other stays
  grey, and the tab bar shows the profile and percentage next to a sync glyph.

- Playlists are `.m3u8` with portable relative paths; six built-in smart
  playlists plus the rule builder; Tags tab (WAV/AIFF included).

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| Space | play / pause |
| Ctrl+← / Ctrl+→ | previous / next track |
| Ctrl+O | add a music folder / open a folder in the tag editor |
| Ctrl+F | search the library / filter the tag list |
| Ctrl+S | save the queue as a playlist / save tags |
| Ctrl+Z / Ctrl+Shift+Z | undo / redo queue edits or tag edits |
| Del (Tags tab) | remove selected files from the list |
| Ctrl+X / Ctrl+C / Ctrl+V (Tags tab) | cut / copy / paste tag cells |
| Ctrl+P | Tools > Preferences (library) |
| Ctrl+Q | quit |

## Where your data lives

- Config: `~/Nebula/settings/config.json` (queue, volume, view, grouping, columns,
  collections, ReplayGain mode, window state)
- Smart playlists: `~/Nebula/settings/smart_playlists.json`
- Sync profiles: `~/Nebula/settings/profiles.json`; PC hash cache:
  `~/Nebula/sync/hashdb/`; per-device sync manifests:
  `~/Nebula/sync/manifests/` (both are only hints — see *Syncing*)
- Library index: `~/Nebula/library/library.db` (SQLite; v2 databases are migrated
  in place). Extra collections: `~/Nebula/library/collections/*.db`
- Playlists: `~/Nebula/library/playlists/*.m3u8`
- Online covers: `~/.cache/Nebula/covers`; decoded spectra:
  `~/.cache/Nebula/tmp/spectrum`; device track buffer:
  `~/.cache/Nebula/tmp/device-buffer` (cleared on start, on disconnect and on quit);
  buffered CD tracks: `~/.cache/Nebula/tmp/cd-buffer` (cleared on start)

## Verification

The 1.26 source and package were checked with:

- the deep suite: **214/214 checks passed**;
- the headless suite: **1057/1057 checks passed**;
- `run.sh --check` from the extracted `.deb`, using a fresh cache;
- a package audit confirming no VirtualKeyboard, PDF, `qpdf`, `rcrack` or `.aax`
  files are bundled.

The automated suites use temporary HOME, library and cache folders, so they do
not touch a real library. Audio output, real MTP hardware and a physical optical
drive are still the parts that need a real desktop check.

## Honest limitations

- Fast hash trusts what this app last wrote. A device file edited outside the app
  while keeping both its size and timestamp is reported equal until the **Verify
  content** button (or *Bit-by-bit*) reads it. The manifest is a record of past
  transfers, not a hash of what is on the device now, and *last verified* dates
  the last time the device was actually read.
- The quick scan reads a device file only when a library file of the same size exists;
  when one does, checking a stray costs a full read of it on the device, which on MTP is
  the cost the fast path otherwise avoids. A file it cannot read is left in place rather
  than removed on the strength of a guess.
- A library file the scan adopts stays where the scan found it, so the device layout then
  differs from the library for that one file. The alternative is deleting it and writing
  the same bytes again, which is what that check exists to avoid. Content the library does
  not have at all is still removed in Mirror.

- ReplayGain is applied by scaling the output volume; playback is capped at the
  player's maximum, so large positive gains (or a high pre-amp) are limited by
  the peak guard instead of being amplified beyond full scale. Measurement needs
  `ffmpeg`; without it only existing tags are used.
- Online lookup depends on CDDB/GNUdb, MusicBrainz, Discogs and the Cover Art
  Archive being reachable. MusicBrainz and the album lookup match releases by
  artist/album text, not by audio fingerprint, and track titles are only applied
  when the file count equals the release track count.
- The decoded-spectrum fallback costs CPU on the first play of a track (it
  decodes the file ahead of playback, then caches the frames). Seeking to a part
  that has not been decoded yet briefly shows the placeholder.
- The drives are checked every two seconds. A disc swapped for another one in the
  same drive between two checks is only noticed once the drive reports no disc at
  all, so a new CD can take one more moment than a disc going into an empty drive.
- Disc identification uses the table of contents only, not an audio fingerprint.
  Two pressings with the same TOC can pick the same entry, and CDDB's inexact
  ("close") matches are taken best-first. CDDB is matched by disc ID alone and has
  no text search, so a disc no service knows needs *Find release* on MusicBrainz or
  Discogs. When GNUdb is down the freedb mirror or RetroBridge answers instead, and
  the three servers do not always hold the same entry (or the same spelling) for a
  disc.
- Tag writing covers MP3/FLAC/OGG/Opus/MP4 and WAV/AIFF; exotic formats are
  read-only.
- Collections are switched one at a time; there is no combined view.
- MTP support depends on gvfs; on some phones folder creation only works after
  unlocking the device.
