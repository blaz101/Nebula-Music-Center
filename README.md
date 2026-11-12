# Nebula Music Center 1.26

## What's new in 1.26

- **GPLv3.** Nebula Music Center is now released under **GPL-3.0-only**. The
  copyright holder is Roger Barthares; the full license is in `LICENSE`.
- **The source offer is documented.** `SOURCE_OFFER.md` identifies the
  Corresponding Source and the exact upstream source for the bundled libraries.
- **Unused Qt components are gone.** Qt VirtualKeyboard and Qt PDF, including
  their plugins and libraries, were removed from the bundle. The remaining Qt
  modules are the ones the app actually uses.
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

## What's new in 1.25

- **The Audible `.aax` importer is gone.** The Audiobooks tab no longer has an
  Import .aax button, and Preferences no longer has activation-byte or
  rainbow-table settings. Ordinary Import and Import folder are unchanged.
- **The bundled `rcrack` tool is gone with it.** The package no longer carries the
  RainbowCrack binary or its README. That removes the licensing blocker identified
  in the 1.20 audit. The remaining GPLv3 work was completed in 1.26: the
  application licence, notices and source offer are now in the tree.
- **The third-party audit is refreshed for 1.25.** See `THIRD_PARTY_LICENSES.md`.

## What's new in 1.24

- **A device keeps its preset.** The preset chosen for a sync profile is saved with
  that profile and restored after the app restarts. Deleting a preset clears the
  association.
- **The tagger right-click menu is consistent.** It no longer repeats the filename/tag
  conversion commands; those remain on the toolbar and in the Convert menu.
- **Devices no longer offers a Podcasts tab.** The device browser now has Music and
  Audiobooks only.

## What's new in 1.23

- **Select Items is a folder tree.** Music now opens by artist, then album, then
  the tracks on that album, instead of showing every song as one flat list.
  Select All and Unselect All still work at every level.

## What's new in 1.22

- **Sync can include LRC files.** The sync profile now has a third option,
  **Include LRC files**, between **Only audio files** and **Autosync when
  connected**. It copies the matching `.lrc` sidecar next to selected audio, even
  though **Choose items** lists audio only; it also works with audio-only folder
  sync.
- **Version 1.22.** LRC sidecar support for sync.

## What's new in 1.21

- **The tagger saves composer on M4A.** Composer is written as the native `©wrt`
  atom, so it survives Ctrl+S and appears in Strawberry and other players; the
  tagger reads it back when the file is reopened.
- **MP3 comments use COMM.** Comment writes were silently dropped by the easy
  layer and now use the standard ID3 COMM frame.
- **Unsupported fields are no longer reported as saved.** If a format cannot
  store a tag, the row stays marked as changed and the tagger names the field
  instead of clearing the dirty state.
- **Every core tag has a round-trip test.** Title, artist, album, album artist,
  track, disc, date, genre, composer and comment are written, read and cleared
  across FLAC, M4A, MP3, WAV, OGG, OPUS and AIFF.
- **Version 1.21.** Tagger save fixes and per-version release artifacts.

## What's new in 1.20

- **Imports no longer freeze the window.** Audible `.aax`, file and folder imports
  run in background workers with progress; the Audiobooks grid refreshes after the
  worker finishes instead of blocking the event loop. The three import buttons are
  disabled while one import is running, and each failure is reported independently.
- **Tag conversion reads left to right.** The Convert menu, toolbar and dialogs now
  say **Filename → Tag**, **Tag → Filename** and **Tag → Tag**.
- **Extended tags understands a multiple selection.** Selecting several files shows
  the union of their keys. Values that agree are shown once; values that differ or
  are missing from some files show `< keep >`, so accepting the window preserves
  each file's own value. A shared edit is applied to every selected file.
- **GPLv3 audit is in the tree.** `THIRD_PARTY_LICENSES.md` inventories every bundled
  library, records the notices/source duties and flags the one remaining blocker:
  the bundled RainbowCrack `rcrack` binary is not GPL-compatible. That binary was
  removed in 1.25.
- **Version 1.20.** Background imports, left-to-right conversion labels, multi-file
  extended tags and the licence audit.

## What's new in 1.19

- **Hash sync keeps exactly one device path per selected file.** The manifest is
  keyed by the target-relative path, and the path is part of the file's identity:
  identical bytes at another path are a duplicate, not equality. Mirror removes old
  paths recorded for a still-selected file, and Verify content restores only the
  canonical path.
- **A corrected target or media folder cleans up after itself.** After fixing a
  target such as `Music/Artists` → `Music`, or a doubled `Artists/Artists` folder,
  stale copies inside the current target are removed by Mirror instead of being
  restored forever. Copies outside the current target stay untouched.
- **Verify content is exact on both sides.** It re-hashes the PC copy as well as the
  device copy, so a same-size edit with its timestamp put back cannot hide behind the
  hash cache.
- **Fast hash stays fast.** A trusted manifest compare still reads no device bytes;
  files are opened only when the manifest is missing or its evidence moved, or when
  Verify content was requested.
- **The hash pipeline is documented and tested.** `SYNC_PART1.md` and
  `SYNC_PART2.md` hold the decision trees; `tests/sync_hash_check.py` and
  `tests/sync_hash_matrix.py` run 763 independent scenarios (263 focused plus a
  500-case seeded matrix) across routing, names, manifest states, duplicates,
  restores, verification and the reported album case.
- **Version 1.19.** Fixes duplicate copies after tag edits and target-folder fixes.

## What's new in 1.18

- **Mirror removes items you unselect.** A selected-item profile now deletes the files
  it synced before that are no longer ticked in **Choose items**, so a device does not
  keep an old book or track after it leaves the selection. Only copies this profile
  wrote are candidates: files it never synced, and files another profile put on the
  device, are left alone. **Update** still never deletes.
- **Version 1.18.** Adds cleanup of unselected items to selected-item Mirror syncs.

## What's new in 1.17

- **The file chooser is the desktop's own.** The launcher no longer redirects the
  desktop's config or data home, so the native dialog sees the system's Documents,
  Downloads, Music and other places, its recent files and bookmarks, and follows the
  desktop's light or dark setting.
- **Audiobooks show covers, sort and search.** The grid begins with a cover column,
  followed by Title, Author, Chapters and Length. Clicking a heading sorts ascending,
  then descending; columns can be dragged into a new order and resized. The search box
  filters titles, authors and chapters as you type.
- **Devices → Audiobooks uses the Audiobooks table.** The device category now shows
  one row per book with cover, Title, Author, Chapters and Length, instead of the
  music-style cover grid; Music and Podcasts keep their own views.
- **Preferences → Backup exports and imports settings.** Pick preferences and app
  settings, sync profiles, device presets or smart playlists, then export them to one
  JSON file or import them back. Account tokens and Audible activation bytes are never
  included in an export.
- **Podcast sync is paused.** Sync selections and target folders now cover
  music and audiobooks only. Existing Podcasts folders on a device are left alone.
- **Version 1.17.** Includes the system chooser fix, the audiobook grid changes,
  settings backup and the temporary podcast-sync pause.

## Planned next

- **Podcast sync.** Return the Podcasts selection group and the Podcasts target
  folder to sync profiles.
- **Mirror cleanup after a codec swap.** A replaced audiobook can leave the old
  codec's files on the device because they now sit in a media folder this run is not
  sending, and Mirror protects that folder before it considers stale files. Make
  Mirror remove stale profile-owned copies even when a codec change moves them to a
  different media tree. Review rehashing PC files on every sync (about 10 seconds for
  20 GB) as part of that work; note that rehashing alone does not bypass the media-
  folder protection.


## What's new in 1.16

- **The native file chooser follows dark mode.** The system chooser now receives
  the desktop's current GTK theme, so a dark desktop no longer gets a light file
  picker from a stale light system GTK setting. Light desktops keep the light
  chooser.
- **Version 1.16.** Fixes the native chooser theme, with no other changes.

## What's new in 1.15

- **File choosers use the system dialog.** Browse, Open, Save and folder pickers now
  open the desktop's own file chooser instead of a Qt-drawn window. It follows the
  system light or dark setting, so it matches the file manager and the rest of the
  desktop.
- **Version 1.15.** Uses the system file chooser for every file and folder picker.

## What's new in 1.14

- **Each device has Music, Audiobooks and Podcasts tabs.** The Devices tab now
  separates the three media trees instead of mixing every audio file in one list. The
  tabs use the profile's target folder names, and remember the last tab for each device.
- **Audiobook covers load on a device.** Artwork now comes from the device's own book
  files or their folder image when the book is not in the music library index.
- **Cover captions have room to breathe.** The device cover grid uses taller tiles, so
  long album names and artists wrap instead of being cut off.
- **The Audiobooks tab opens quickly again.** Opening it no longer re-reads tags and
  chapter metadata for every unchanged book; a cheap signature check skips that work.
- **Version 1.14.** Adds the per-device media tabs, device audiobook artwork and the
  audiobook loading cache.

## What's new in 1.13

- **Target folders belong to the sync profile.** Syncing → Profile now has one
  **Choose Target Folders** button. Pick the selected folder on the device, then the
  Music, Audiobooks and Podcasts folders below it. The three paths are stored with that
  profile and used by Compare, Sync, Verify content and mirror.
- **The folders are actually used.** Music goes to `<selected>/Artists`, audiobooks to
  `<selected>/Audiobooks` and podcasts to `<selected>/Podcasts` by default. The folder
  names remain editable, and an existing library or audiobook folder name is kept below
  the chosen media folder instead of being repeated.
- **Mirror is media-aware.** A music-only profile no longer deletes the Audiobooks or
  Podcasts tree it is not sending.
- **Version 1.13.** Moves target folders into the sync profile and routes music,
  audiobooks and podcasts to their selected destinations.

## What's new in 1.12

- **Audible imports run in the background.** The Audiobooks tab shows “Importing
  audiobook 44%” while a book decrypts, so the window keeps responding and can still
  play music. Failures leave the earlier files alone and the remaining books continue.
- **Choose one .m4b or real chapter files.** The new Preferences → Audiobooks page
  selects one .m4b per book, or chapter files laid out as
  `ARTIST/ALBUM/001 - Chapter 1.m4a` with the .aax title, artist, album, cover art,
  `Chapter 1` titles and `1/137` track numbers. Names are sanitized, chapter padding
  follows the chapter count, and temporary decrypted files are removed.
- **Device folders have sensible defaults.** New sync profiles and Copy to device use
  `Music/Artists` for music, `Audiobooks` for audiobooks and `Music/Podcasts` for
  podcasts. Preferences → Syncing lets each default be changed, and an individual
  profile can still choose its own folder on the device.
- **Version 1.12.** Adds the background .aax importer and media-aware device defaults.

## What's new in 1.11.1

- **The audible table search uses the real tables again.** It no longer walks up to
  `/` and can no longer choose a stray test table over the standard set in
  `~/Music/A`. Empty or fake `.rt` files are ignored, so offline `.aax` import finds
  the account key again.
- **Version 1.11.1.** Fixes the table-selection bug found after 1.11.

## What's new in 1.11

- **File choosers are dark with the app.** Browse, Open and Save dialogs now use the
  app's Qt chooser and its palette instead of the desktop's light native chooser, so
  they are dark in Dark and Black AMOLED and light in Light. Folder pickers still show
  folders only.
- **The Audiobooks header is simpler.** The folder path picker is gone; Import uses the
  configured/default audiobook folder, and its button now uses the same style as
  Import folder and Import .aax. Right-click a title to add the whole book to the
  queue, or a chapter to add that chapter; Play is on the same menu.
- **The sync sheet only shows what it needs.** Folder(s) to sync disappears when What
  to sync is Selected items. The Choose items tree opens collapsed, the buttons are
  **Select All** and **Unselect All**, and a book that was unchecked stays unchecked
  when reopened — its tick follows its chapters. An empty selected-item set is kept as
  empty instead of reverting to everything.
- **Version 1.11.** Includes the 1.10 path-confinement and packaging changes.

## What's new in 1.10

- **App-owned files stay in the two Nebula folders.** Settings and data remain under
  `~/Nebula`; covers, the installed program copy and every buffer remain under
  `~/.cache/Nebula`. Transcode, concat, CD, burn and ISO staging temporary files now
  use `~/.cache/Nebula/tmp` instead of `/tmp`, and the launcher redirects Qt,
  fontconfig and Mesa caches there too. Python bytecode is not written into the app
  folder, so a portable unpacked copy leaves no `__pycache__` behind.
- **The `.deb` installs only its program and desktop integration outside your home.**
  The package payload is `/opt/nebula-music-center`, `/usr/bin/nebula-music-center`,
  the menu entry, the icon and `/usr/share/doc/nebula-music-center`; there is no
  installer action in any other location. A system package cannot put its launcher
  or menu entry inside a home folder, so those system paths are unavoidable.
- **Version 1.10.** This is the 1.1 feature set, packaged as 1.10.

## What's new in 1.1

- **Settings have a safety net.** Before every write the previous `config.json` is kept
  as `config.json.bak`, and a missing, empty or truncated config is read from that copy
  instead of starting over with defaults. Your library folders, remembered devices and
  preferences therefore survive a bad or interrupted save.
- **Activation bytes can be found offline.** The package carries `rcrack`, so **Find
  activation bytes** no longer needs anything downloaded or installed. It uses the
  audible rainbow tables it finds on the PC (the zip in `~/Music/A` is unpacked once)
  and ffmpeg decrypts with the recovered key. One key covers every `.aax` on the account.
  This feature and the bundled `rcrack` were removed in 1.25.
- **Import whole folders.** The Audiobooks tab has **Import folder…** beside Import. A
  book folder becomes one title; a shelf of book folders has each book moved in.
- **The Audiobooks grid sorts.** Click Title, Artist, Chapters or Length to sort, and
  click the same heading again to reverse it. Chapters stay in their natural order.
- **Bitrate only appears when it matters.** With **Force transcode** off, the Bitrate
  row is hidden instead of showing a blank control.
- **Presets are shared by every device.** The Syncing tab lists all presets whatever
  device the profile targets; Save stores the current settings for every device.
- **Sync several folders, or pick exactly what to sync.** **Folder(s) to sync** takes as
  many library folders as you add. Switch **What to sync** to **Selected items** for a
  window of every music track and audiobook with checkboxes, **Select All**
  and **Unselect All**; selected-item sync copies only those files and never deletes
  anything else.
- **Tested end to end.** The 187-check `tests/deep_check.py` runs against a throw-away
  home directory (never your real settings) and covers the config and its backup,
  scanning, playlists, the grids, audiobooks and `.aax` helpers (including a real offline
  key lookup), shared presets, multi-folder and selected-item sync, menus and session
  restore.

## What's new in 1.09

- **Audiobooks is one clean list.** The folder panel is gone: the tab is the grid, and
  the menu keeps Select folder and Remove folder.
- **Import moves audiobooks in.** Import takes .m4b, .m4a, .mp3 and the other audio
  formats you pick and moves them into the chosen folder, by default
  `~/Music/Nebula - Audiobooks`, which is created on first use. A file dropped straight
  into an audiobook folder is a title of its own.
- **Import .aax decrypts Audible files.** It uses this account's 8-character activation
  bytes, remembered once found; if there are none saved it offers Find activation bytes,
  which reads the file's checksum and looks the key up in the audible rainbow tables
  with rcrack. Wrong bytes are reported and cleared.
- **Grids remember their columns.** Columns can be dragged into a new order in the Music
  and Audiobooks grids, and that order and width are kept for next time.

## What's new in 1.08

- **The Audiobooks list shows more at a glance.** Each title has its artist, chapter
  count and total length, and the chapters below it show their own length.
- **Chapters are counted properly for `.m4b`.** A single `.m4b` reports the chapters in
  its own chapter table instead of counting as one file; other books count one chapter
  per audio file.
- **The menu bar follows the Audiobooks tab.** While it is open the Music menu becomes
  an Audiobooks menu with Select folder and Refresh, sitting next to Playlist.
- **`.m4b` is an audiobook format only**, so the music library never picks one up.

## What's new in 1.07

- **Library is now Music.** The tab that held your music library is renamed to Music.
- **New Audiobooks tab.** It sits between Music and Tags. Each folder that holds audio
  is one title, with its chapters in natural order. Double-click a title to play it
  from the start, or a chapter to play from there on.
- **Audiobooks stay out of the music library.** Audiobook folders are kept in their own
  list, so they are never scanned into Music, and removing one from the Audiobooks tab
  leaves its files on disk.

## What's new in 1.06

- **Force transcode now has a bitrate choice in sync profiles.** Choose MP3 (LAME) or AAC
  (`.m4a`) at 128, 192, 256 or 320 kbps, or Opus at 64, 96, 128, 160, 192, 224 or 256
  kbps. The codec's old fixed setting is still the starting point. Presets remember the
  codec and bitrate too, and Copy to device uses the same choices.
- **A changed bitrate is a real change.** The sync manifest records the encode setting
  with every transcode, so Fast hash does not call an old 128 kbps copy equal to a new
  320 kbps choice. The device copy is re-encoded once on the next Compare or Sync.
- **Verify content steps aside for forced transcodes.** A lossy device file cannot be
  compared with the source bytes, so Compare and Sync use the manifest's source hash and
  encode setting instead; the Verify button is disabled while Force transcode is on.

## What's new in 1.05

- **Verify content now reads the device, not the PC's cache.** It evicts the cached copy of
  each file before hashing it, so a 3 GB player takes as long as its USB connection really
  needs instead of finishing in seconds from RAM. That is the honest cost of proving what
  the device holds.
- **A verification that read nothing no longer says the matches are exact.** An empty device
  folder now says so plainly and does not update the profile's *last verified* time. The
  result reports how many files were read and matched, and names any file that could not be
  read instead of treating silence as success.
- **A moved device timestamp is checked, not called a difference.** Fast hash now reads both
  copies when a device file's time changes after reconnecting; identical bytes stay equal,
  and only a real content change is planned for a copy.
- **Copies are flushed to the device before they are reported done.** Each finished file and
  its directory entry are synced, so a reconnect does not lose writes that were still only
  in the PC's cache.

## What's new in 1.04

- **Click anywhere on the time bar to jump to that point.** The old click paged the
  position; now the bar follows the click and keeps up while you drag, from the groove or
  the handle. **Preferences > Playback > Click the time bar to jump** turns the jump off
  and restores click-to-page, while dragging the handle always works.

## What's new in 1.03

- **Double-clicking a group no longer opens or closes it.** In the library tree, a
  double-click still queues the group's tracks (or plays them, per Preferences >
  Library); only the disclosure arrow expands or collapses a group now. The tree stays
  still while several artists or albums are queued.
- **Stop returns the player bar to Nothing playing.** The title, artist, cover, format
  pills and time read as they do before anything has played, and the queue's playing
  highlight clears. The queue itself is kept, so Play starts the stopped track again.

## What's new in 1.02

- **ReplayGain no longer raises a notification for every track.** The progress dialog and
  the status bar still follow the run track by track, but the notification appears once,
  when the whole analysis has finished — or when it stops or fails. Analysing one track
  from the player bar works the same way: only the result is announced.

## What's new in 1.01

- **ReplayGain can write album gain.** Selecting two or more tracks from one album and
  choosing *Analyse ReplayGain* now measures the album as a whole with `ffmpeg`'s EBU
  R128 filter, in one extra pass, and writes `REPLAYGAIN_ALBUM_GAIN` and
  `REPLAYGAIN_ALBUM_PEAK` to each selected track as well as the usual track tags. Tracks
  are grouped by albumartist and album, or by folder when there is no albumartist, so a
  multi-disc album stays one album. A single track still gets track tags only.
- **Measuring loudness no longer freezes the window.** The work runs on a worker thread;
  a progress dialog and the status bar name the track or album being measured, **Cancel**
  stops after the one in progress, and tag writes happen off the interface thread.
- **A device can be removed from the Devices tab.** Right-click it — plugged in or
  remembered — and choose **Remove from the Devices tab…**. Its music, sync profiles and
  presets stay untouched; it waits in **Preferences > Devices**, where **Restore
  selected** brings the same name and entry back, connected or not. A removed device
  stays out of the tab after a restart or a re-plug until it is restored.
- **The tray menu no longer carries the presets.** **Device presets** has been removed
  from the tray; presets still live in the Syncing tab's **Preset** row, where they are
  saved, applied and deleted, so the tray stays the short transport menu it is next to the
  other players.

## What's new in 1.0

- **Nebula has a tray icon, with the controls where the other players keep theirs.**
  The icon in the status area opens a menu with Previous track, Play/Pause, Stop, Stop
  after this track, Next track, Mute and Quit, plus *Show Nebula* and the device presets.
  The Play entry becomes Pause while music is playing, and the two check marks follow the
  player, so the menu never disagrees with the window. Clicking the icon brings the window
  back. Closing the window still quits the app.
- **Device presets.** A preset belongs to one device, so each phone or player can keep its
  own saved setup: the folder on it, the variant, the compare method, the device
  filesystem and any forced transcode, with the library folder it syncs from. The
  **Syncing** tab's new **Preset** row lists that device's presets; **Save…** stores the
  profile as it is now (a second save with the same name replaces it), **Delete** removes
  it. The tray menu has **Device presets** with one submenu per device, including devices
  that are not plugged in right now. Choosing a preset loads it into the profile for that
  device, opens the Syncing tab and says to press Sync — it never starts a sync by itself,
  so a Mirror preset cannot remove anything until you ask it to.
- **Every profile keeps a log of what it did.** The clock-and-page button beside the change
  list opens the profile's last compares, syncs and verifications, newest first, with a
  separator between runs. Each entry says when it ran, which task it was, the counts
  (new, restored, changed, delete, equal), whether the contents were read in full, any
  errors, and up to 200 file lines in the same colours as the list. **Clear log** empties
  it, and deleting a profile deletes its log with it.
- **The log keeps the last 10 runs by default, and that is a preference.** Preferences >
  Syncing sets how many runs each profile keeps, from 1 to 100; a smaller limit also trims
  logs that already hold more.
- **The change list is bigger and says what changed first.** The old text log no longer
  takes the bottom of the tab, so the list fills the window. Files are grouped under **New
  files**, **Missing on the device — copied back**, **Changed — updated on the device** and
  **Only on the device — removed by Mirror**, each heading carrying its own file count and
  size in the group's colour. An empty plan says *Nothing to change* instead of showing
  bare columns.
- **The long explanation under Compare by is gone.** The picker's own labels say what each
  mode does, and its tooltip keeps the short version; the space goes to the list.

## What's new in 0.99

- **The taskbar shows the Nebula icon and name.** The running app is now linked to its
  installed launcher, so the taskbar shows the Nebula Music Center icon and name instead
  of a generic one.

## What's new in 0.98

- **No more "not connected" flash when selecting File transfer.** A phone that drops out
  of the device list for a moment while it switches to File transfer now stays listed
  through that gap, so the sync tab goes from *waiting for File transfer* straight to
  *connected*.

## What's new in 0.97

- **Devices are noticed faster.** A phone plugged in, or switched to File transfer, now
  shows up in the app within about a second instead of up to three.
- **No more brief "not connected" when a phone changes mode.** A phone that drops out of
  the device list for a moment, as it does while switching to File transfer, stays
  listed until it has been missing for two checks in a row, so the sync tab goes from
  *waiting for File transfer* straight to *connected* instead of flashing *not connected*.

## What's new in 0.96

- **The sync tab's device status shows the three states a phone actually goes through.**
  Nothing plugged in reads *not connected*. A phone that is plugged in but has not
  switched to File transfer reads *waiting for File transfer*, and it keeps that wording
  while it sits on its charging prompt, even while the Devices tab is reading its
  library. Once its storage answers, the dot reads *connected*.
- **No more flicker through "reading" or "checking".** The status used to show *reading*
  while the Devices tab walked the phone, and *checking* until the first answer, so a
  phone waiting for File transfer appeared to move between states for a few seconds.
  The sync tab now goes straight to the answer it has.

## What's new in 0.95

- **The device status dot follows File transfer mode.** The dot used to keep its first
  answer, so a phone switched in or out of File transfer while plugged in was never
  re-checked. An answer older than six seconds is now asked again, and the dot reads
  `checking` until the first answer arrives instead of showing `connected` by default.

## What's new in 0.94

- **Copy to device and autosync wait for MTP file transfer.** A phone that is plugged
  in but still charging leaves a mount whose storage refuses to be read, and a copy
  started then failed at once with a permission error. The copy now waits, says
  `Waiting for <device> — switch the phone to 'File transfer'…` in the busy page, the
  status bar and the top-right badge, and continues by itself when the storage answers.
  It gives up after three minutes with the same advice.
- **Readiness is asked inside a storage, not at the mount root.** gvfs can list a
  phone's storages while every read inside them fails, so the Devices tab's read and
  autosync now require a storage that answers. A re-plugged phone also starts unasked:
  a `ready` answer from its previous connection can no longer start a sync early.

## What's new in 0.93

- **Copy to device is one window.** The device, whether folders are kept, the folder on
  the device and any forced transcode are asked together; the separate device picker and
  options dialog are gone.
- **Keep folder organization.** A copy keeps each file's path inside its library folder
  (`Artist/Album/33 - Track.m4a`) or puts only the file itself in the target folder. The
  window previews where the first file lands.
- **The folder on the device is remembered, and can be picked.** *Select folder…* browses
  the device: one copied to before opens where it was left, a new one opens at its root
  with the storages listed. The chosen folder is remembered per device, and the Devices
  tab shows it too.
- **Force transcode asks for codec and bitrate separately**, with the VBR or CBR choices
  each codec supports; the codec's old fixed setting is still the starting choice.
- **A copy says how far it is.** The badge at the top right, beside the tabs, reads
  `Copying files to <device> 42%`, measured by bytes so a single large track moves.

## What's new in 0.92

- **Sending to a phone uses the storage that holds the music.** When the target folder (such as
  `Music`) is given without a storage, the upload now goes to the storage that already contains
  it, typically the SD card. Previously it tried to create the folder on the phone's internal
  storage, which the MTP mount refused.

## What's new in 0.91

- **Force transcode for sync and copy to device.** A sync profile has a "Force transcode"
  setting: Off, MP3 (LAME V2), AAC `.m4a` 256 kbps, or Opus 128 kbps. Every file is
  re-encoded on its way to the device and named with the new extension. Copy to device has
  the same option. Off is the default and copies files unchanged.

## What's new in 0.90

- **The device has one reader, everywhere.** A compare, sync, verification or copy now
  claims the device by its path until it is done. The Devices tab shows that task instead of
  the music, and every read it could start — Refresh, search, List/Covers, the folder picker,
  Play, Copy to library, uploads and mounting — is refused while the claim holds. Because the
  claim is a path, a profile pointed at a folder inside the mount is the same device as the
  row that shows the mount.
- **The message says which process has the device**: `Comparing …`, `Syncing …`,
  `Verifying content on …`, `Autosyncing …`, `Copying files to …`, `Copying files from …`,
  or `Autosync is starting on …` while an automatic run is queued. The rows are gone, not
  greyed.
- **With Autosync on, the device library is never loaded first.** The sync tab is offered the
  device before the Devices tab sees it, so an automatic run claims the device before any
  walk begins; the library is read once, after the sync, when the device is free.
- **No device request runs on the GUI thread any more.** That was the freeze the note could
  not cover: the status dot listed the MTP mount to decide whether to say "connected", and it
  did so right as a task handed the device back. The dot now follows the last answer (from the
  Devices tab's own read or a probe on a worker), the sync tab's readiness checks for autosync
  run on workers, and a cancelled library walk is waited for before a sync starts — one reader
  at the mount, never two.
- **The sync progress bar ends on `Done`, `Stopped` or `Failed`** even when every file was
  already equal, and a finished worker's last progress tick can no longer put it back to 0%.
- **Copy to library and Copy to device own the device too**, and show their own note while
  they run; the music returns when they finish.

## What's new in 0.89

- **The Devices tab cannot fight a sync for the device any more.** While a compare, sync or
  verification is running, that device's music is replaced by a note naming the profile that
  is using it, and Refresh, search, the folder picker, Play and Copy to library are out of
  reach until it finishes; the library is read again automatically afterwards. This covers a
  task started while the device library is still loading, an autosync, and a manual run on a
  device that was already loaded — the cases where two readers on one MTP mount used to stop
  the window answering. Other connected devices stay browsable.
- **Switching Autosync on while the player is already plugged in now starts a sync**, just
  as plugging it in does. Pointing an autosync profile at the device that is already
  connected does the same; switching Autosync off drops a queued or waiting run.
- **The sync progress bar ends on `Done`** (or `Stopped` when cancelled) instead of showing
  0% after a run in which every file was already equal.
- **The device status dot says `syncing`** while its device is in use and `reading` while
  its library is being loaded, and no longer probes an MTP mount mid-sync or mid-load — those
  probes could queue behind the transfer and freeze the window.

## What's new in 0.88

- **Opening a folder in Tags no longer freezes the window.** A progress window reports
  `Reading files 12/342` while the tags are read, with a Cancel button that stops the read
  and keeps the files already loaded.
- **The cover has a right-click menu on the tag panel**, the same one the Extended Tags
  window shows: Add, Remove, Replace, Extract, Adjust cover, Manage covers, Set cover type,
  Set cover description, Cut/Copy/Paste cover and Correct aspect ratio.
- **Covers keep their picture type and description.** Set cover type offers the ID3/FLAC
  types (Front Cover, Back Cover, Media, Leaflet and the rest) and both are written with the
  image on Save. MP4 files store the image only, as the format has no place for them.
- **Adjust cover** re-encodes or resizes a picture: Format (Original, JPEG, PNG), Quality for
  JPEG, Size with `max. size` / `min. size`, and Scale proportionally, Scale to square or
  Crop to square. The result is held until Save, like every other cover edit.
- **Manage covers** lists what the file carries and offers the same actions in one place.

## What's new in 0.87

- **Cover art can be changed in Extended Tags.** Right-click the cover in the Extended Tags
  dialog to add, replace, remove or extract it. Changes are written to the file on Save,
  like the other tags.
- **Renamed from Spectra to Nebula.** The source folder is now `nebula/` and the program is
  `nebula.py`. Update any launcher or shortcut that pointed at `spectra.py`.

## What's new in 0.86

- **Nothing is removed from `/opt` by the app.** The app and the package never delete the
  `/opt/nebula-music-center` copy. If `/opt` is gone, the `nebula-music-center` launcher runs
  the copy already in `~/.cache/Nebula/app`, so the app still starts.

## What's new in 0.85

- **Everything the app needs lives in two folders.** The program, Qt, FFmpeg and the other
  bundled libraries are copied from `/opt/nebula-music-center` into
  `~/.cache/Nebula/app` the first time the app starts after an install or upgrade. Deleted
  files now move to `~/Nebula/trash` instead of the desktop Trash, so nothing is written
  outside the two folders. Deleting the cache folder removes the program copy too; the next
  start rebuilds it from `/opt`.

  ```
  ~/Nebula/        settings, library, sync and trash: the one to back up
  ~/.cache/Nebula/ app copy, covers and buffers: safe to delete
  ```

## What's new in 0.84

- **Two folders instead of one: settings and data, and a cache you can delete.** The
  single folder from 0.82 was handy to explain but wrong to back up — one `rsync` of it
  walked a 2 GB buffer along with your library. Now:

  ```
  ~/Nebula/                    settings and data — this is the one to back up
    settings/   config.json, profiles.json, smart_playlists.json, queue-meta.json
    library/    library.db, collections/, playlists/
    sync/       hashdb/, manifests/

  ~/.cache/Nebula/             rebuildable, safe to delete at any time
    covers/     artwork cache
    tmp/        cd-buffer/, device-buffer/, cd/, devplay/, rip and burn staging
  ```

  `~/.cache/Nebula` carries a `CACHEDIR.TAG` (as do `covers/` and `tmp/`), so rsync,
  restic and Déjà Dup skip the whole tree without being configured. The split is also
  what a sandboxed install needs: a Flatpak maps the two roots onto its own private
  directories, `$XDG_DATA_HOME/Nebula` and `$XDG_CACHE_HOME/Nebula`, with no code
  change at all.
- **The `~/.NebulaMusicCenter` move is gone.** The start-up check that split the 0.82 and
  0.83 single folder into `~/Nebula` and `~/.cache/Nebula` has been removed, since it only
  applied to the developer's own machine. Upgrading from 0.82 or 0.83 means moving the
  folder's contents by hand: `settings/`, `library/` and `sync/` go to `~/Nebula`, and
  `covers/` and `tmp/` go to `~/.cache/Nebula`.
- **The one-off move from the pre-0.82 `spectra` folders is gone.** That migration only
  ever applied to installs from before 0.82 and cost a start-up check on every launch
  since. Upgrading from 0.81 or older straight to 0.84 no longer carries that data
  across; it can be moved by hand.
- **The `.deb` no longer ships the test suite or the screenshots.** They are
  development material and have no place in an installed app; the package is about
  2 MB smaller.
- **`NEBULA_DATA` and `NEBULA_CACHE` move the two roots.** Set one or both to keep the
  app on a USB stick, or in a folder of your choosing; `NEBULA_HOME` is gone. The test
  suite sets both so it can never touch a real library.

## What's new in 0.83

- **The Devices action buttons stay compact when no device is connected.** Play, Refresh
  and Select device folder… use their natural button widths instead of stretching across
  the empty view.
- **The Nebula logo is tab-height.** Its image and corner widget now match the height of
  the tab buttons.
- **The .deb upgrades in place.** It keeps the same Debian package name, so installing
  `nebula-music-center_0.83_amd64.deb` upgrades 0.82 in place, keeping your data.

## What's new in 0.82

- **Everything the app writes now lives in one folder: `~/.NebulaMusicCenter`.** It used
  to be spread over `~/.config/spectra`, `~/.local/share/spectra` and `~/.cache/spectra`,
  which made "where is my stuff?" hard to answer and made a backup pick up a 2 GB
  buffer. The folder is self-describing:

  ```
  ~/.NebulaMusicCenter/
    settings/   config, profiles, smart playlists, queue rows for device tracks
    library/    library.db, collections/, playlists/
    sync/       hashdb/ and manifests/ — what each profile knows a device holds
    covers/     artwork cache
    tmp/        CD, device, rip and burn buffers
  ```

  Music folders are still read where they are; nothing is copied into the app folder.
  `covers/` and `tmp/` carry a `CACHEDIR.TAG`, so rsync, restic and Déjà Dup skip them
  without being told which folder is which.
- **An existing library moves itself.** On the first start of 0.82, the three old folders
  are moved into the new one, each file to its proper place, and the collection
  databases listed in `config.json` are repointed at their new paths. Nothing is
  overwritten: a file that already exists in the new place is left alone, so an
  interrupted move can just be run again. The old folders are removed only once they are
  empty — a move that fails (a read-only home, say) leaves the data where it was.
- **Old buffers are cleaned up at start-up.** Anything in `tmp/` untouched for a day is
  deleted, so a crash or a session closed by force no longer leaves a device or CD
  buffer on the disk for good. A second copy of the app that is playing right now keeps
  its buffers, because nothing younger than a day is touched.
- **`NEBULA_HOME` moves the whole folder.** Set it to keep the app on a USB stick, or in
  a folder of your choosing; with it unset the default above is used. The test suite uses
  it to stay away from real data, and now deletes its throw-away home when it finishes
  instead of leaving roughly 20 MB behind on every run.
- **A `.deb` for Debian and Ubuntu.** `nebula-music-center_0.82_amd64.deb` installs to
  `/opt/nebula-music-center`, adds `nebula-music-center` to the menu and to `$PATH`, and
  brings its own Qt, so no distro Qt is needed. It declares the system libraries it uses
  and recommends the optional command-line tools (ffmpeg, cdparanoia, gvfs for MTP).

## What's new in 0.81

- **The Devices list is the title tree and its sizes, nothing else.** The *Artist,*
  *Album* and *Size* columns are now *Title* and *Size*: artists stay bold at the top,
  their albums open under them, and each track keeps its numbered name — one text
  column, one size column. The old second column repeated the album (and put the artist
  under an *Album* heading) and no longer matched what the rows were showing.
- **A device is remembered after it is unplugged.** Both the top bar and the sidebar
  keep its row, by its stable id, and the dot below the name says *connected* (green)
  or *not connected* (grey). Picking an unplugged row shows its name and *not
  connected*, with nothing to play; plugging it back in reads it as before. The rows
  come back on the next launch, in the order they were first seen.
- **Right-click a device to give it a nickname.** Works in the top bar and the sidebar;
  the name is saved in the config and used in both views and in the device header.
  *Use the device's own name* puts the original back. The kind and mount path stay in
  the tooltip.
- **No false "disconnected" line.** A read that loses its mount no longer paints *The
  device was disconnected* while the device is still listed: the row's dot is the one
  place that says whether it is here. The empty tab still shows a single line when no
  device has ever been seen.

## What's new in 0.80

- **Music queued from a device stays the device's file.** The queue no longer swaps in the
  PC copy for a track this app synced: the entry is the mounted file itself, so it plays
  from the phone or player it came from. The Source column names it *MTP device*, *iPod*
  or *USB device*, and the title tooltip adds the device's name. The origin is kept in
  `queue-meta.json`, so a queue restored at the next launch still shows where it came from.
- **A buffer for device tracks.** Preferences > Playback has *Buffer device tracks ahead*
  (Off, or 64 MB to 2 GB; 128 MB by default). The current track is copied to a local cache
  first, then the tracks after it while the size lasts; playback uses a finished copy and
  reads the device directly until then. The size is a budget for whole tracks, so one
  track can be larger than the number you pick, and nothing is claimed to be buffered
  before its copy is complete. The copies live only for the session and are deleted when
  the device goes away or the app closes.
- **A disconnected device takes its queue with it.** Pulling a device out removes every
  queued track that came from it (stopping if the track playing now was one) and deletes
  what was buffered from it. PC files and CD tracks in the queue are left alone. This also
  applies when the mount disappears between device polls.
- **The List / Covers switch has its own line under the search box.** It is there while a
  device is being read and while none is connected, so either view is always one click
  away; the folder, Play, Refresh and folder picker stay on the line below.
- **No misleading hint on an empty cover grid.** The album instructions live on the covers
  themselves, so hovering an empty or still-loading grid no longer shows an *open / queue*
  hint for albums that are not there.
- **One "No devices connected" message.** The empty device bar no longer repeats the line
  the music pane already shows.

## What's new in 0.79

- **A connected device is read as soon as it is loaded.** The Devices tab scans the folder
  it shows and then displays the music, with the window still usable while it reads. On a
  phone it waits for MTP file transfer before listing anything; a phone that is still in
  charging mode shows *Loading device library — waiting for file transfer…* and starts on
  its own once the storage answers.
- **The scan reports in the status bar, not in a bar across the bottom.** *Loading device
  library…* replaces the old scan progress bar, and it goes away when the music is in. The
  folder name and capacity appear once the device has answered, so a phone that is not
  ready yet is not described as empty or as having an unknown amount of space.
- **A running sync always goes first.** Starting a sync stops the device read; the scan
  waits, says it is waiting, and runs again by itself when the sync finishes. The device tab
  is no longer competing with the sync for an MTP mount.
- **Covers load after the scan.** The list of albums is drawn at once and the artwork is
  read on a worker in the background, first from the PC file the sync manifest points at,
  then from any library track with the same album and artist, and each tile is replaced as
  its cover arrives. A scan that has just finished therefore does not leave every tile on
  the drawn placeholder.
- **The library's fold menu is in the Devices tab, beside the search box.** *Open all*,
  *Open letter markers only* and *Close all* act on the artist tree and the position is
  remembered in the config, so it is the same after the next scan or the next launch.
  (The device tree has no A-Z rows of its own, so *Open letter markers only* means its first
  level: artists open with their albums showing, tracks still closed.)
- **Disconnecting leaves nothing behind.** Pulling the device out clears its music, covers,
  tree and summary at once, and hides the capacity bar and folder line instead of showing a
  capacity for a device that is not there. The old covers cannot be clicked any more.
- **The side layout has a divider** between the device list and the music, so the two are
  separated in Preferences > Library's sidebar shape.
- Rebuilding the list and cover grid no longer emits click signals, so a scan finishing
  cannot queue or start an album by itself.

## What's new in 0.78

- **Copy to library, in the Devices tab's right-click menu.** *Copy 6 tracks to library* on
  a selection (and *Copy album to library* on a cover, *Play 6 tracks* stays first) copies
  the music off the device into your own library, so it can be played and queued from the
  Library tab like anything else. The copy keeps the names and the artist/album folders
  exactly as the device has them; only the folder the device is showing is dropped, so
  `Music/Aphex Twin/…/01 - Xtal.flac` lands as `Aphex Twin/…/01 - Xtal.flac`.
- **Where copies land.** The music folder of the sync profile for that device when there is
  one (that is where the music came from), otherwise the library's first music folder. A
  library with no music folder says so instead of guessing.
- **Nothing is overwritten.** A track the sync manifest says the library already holds, or
  the same file sitting at the same place with the same size, is left alone and counted as
  *already in the library*. A different file already using the name is kept and the copy is
  numbered — `02 - Tha (2).wav`. The new files are added to the library at once, without a
  full rescan, and the result is reported in the status bar (*Copied 6 tracks into the
  library · 2 already in the library*).
- The Devices tab keeps its own queue exactly as it was — this only adds the menu entry.

## What's new in 0.77

- **The bulk Queue button is gone from the Devices tab.** One press filled the queue with
  the whole folder, which is rarely what you want from a device. Queueing is still there
  where it belongs: double-click a track, album or artist, or use *Add to queue* in the
  context menu.
- **Device music queues as the library's copy.** When this app synced the file from the
  library, the queue now gets the PC file, not the device one: the row has the real
  title, artist, album, length and format, and playback reads the computer instead of the
  device. A file only the device holds is still queued from the device, with its tags read
  so the row is not blank; those tags are kept in
  `~/Nebula/settings/queue-meta.json`, so a
  queue restored at the next launch comes back with its columns filled in.
- **Fixed: playing or queueing from a device folder used the wrong path.** A row kept the
  name with the folder stripped off (`Artist/Album/01 - track.flac`), so playback asked
  the device for `/Artist/Album/01 - track.flac` while the music was under `/Music/...`:
  the file was not found, which is why music queued off a device came back as 0:00 rows
  with no tags. Rows now carry the full device path, which is also what the sync manifest
  is keyed by.

## What's new in 0.76

- **The device's music can be searched.** The Devices tab now has the library's search
  box above the list, and it answers the same `field:value` language — `artist:aphex`,
  `album:"Selected Ambient Works"`, `track:>=5`, `size:>10m`, `-artist:boards`, `OR`,
  parentheses. It filters what was already read, so typing never goes back to the device,
  and List and Covers narrow together; the line under the box counts the matches and the
  summary keeps the device total beside it (*2 tracks · 1 album · 3 on the device*). A
  query that will not parse says so and falls back to a plain text search, as in the
  library.
- **Covers open albums.** A click on a cover opens that album in the list — its artist,
  the album and its numbered tracks — with a *‹ Albums* bar to go back; a double-click on
  the cover adds the album to the queue instead. Those are the library's gestures, so the
  two tabs finally behave the same.
- **Play and Queue act on what is shown.** The new **Queue** button beside **Play** adds
  the view to the queue (search results, or the open album) instead of always the whole
  device folder, and the context menu acts on a whole multi-selection and names how many
  tracks it is about to play or add. Double-click on a track, album or artist follows the
  library's *double-click action* preference (Preferences > Library) — by default it adds
  to the queue, and set to *play* it plays.

## What's new in 0.75

- **The Devices tab shows the music on the device, not the PC's folders.** The device
  tabs across the top (or the list down the side — Preferences > Library, unchanged) pick
  the device; under them is what that device holds, drawn the way the library draws music.
  **List** gives artists, each opening to its albums and then to numbered tracks; **Covers**
  gives one cover per album with its name, artist and track count. Which one is showing is
  remembered.
- **Each device has its own folder.** *Select device folder…* walks the device's folders
  (folders only — the file-manager view is gone) and remembers the choice per device; a
  device that has a `Music` folder opens on it the first time, and one that does not opens
  on the whole device. The line above the list names the folder in use.
- **The PC music-folder table is gone from this tab.** Adding, removing and rescanning
  folders stays in the Library tab, where the folders are; the Devices tab no longer
  duplicates it, and the *Music* / *Files* switch that sat above it is gone with it.
- **Tags come from the library where they can.** A device file this app wrote is matched
  through the sync manifest to the PC file it came from, so the list shows that file's real
  title, track number and album art. Anything the library does not know falls back to the
  folder layout (`Artist/Album/01 - Title.ext`), and those rows are drawn muted so it is
  obvious which are guesses.
- **Playing fetches the device copies first.** Double-click a track to play its album from
  that track on, an artist or album row to play all of it, or **Play** for everything in the
  folder; **Add to queue** is on the context menu. On MTP the files are copied locally
  before they play, with progress in the bar — the same path the old browser used.
- **Copying files still works**: *Copy to device* and drag-and-drop put files in the folder
  the device is showing, and the view refreshes afterwards.

## What's new in 0.74

- **Verify content now indexes the whole device folder.** It reads and SHA-256s every
  file in the folder the profile syncs to — only audio files when *Only audio files* is
  ticked, everything when it is not — and writes those digests into the sync manifest:
  the files this profile syncs under their source path, and files it does not claim under
  their device path with no source. A record whose device copy turns out to differ is
  dropped instead of being left claiming the PC content. The manifest after a
  verification is therefore an exact list of what the device holds, not a guess about it.
- **A verified record holds content and no timestamp.** Timestamps were the part of Fast
  hash that could be wrong: a phone that rewrites its file times on every mount forced
  every file to be re-read, and an equal-size edit with its time put back was invisible.
  A record written by Verify content stores the SHA-256 of the device's own bytes and
  `0` for the timestamp, so equality is the digests — exact, like bit-by-bit — and a
  device clock nobody trusts cannot change the answer or cost a re-read. A file that
  cannot be read is never recorded.
- **The honest cost is unchanged.** Verification reads every byte of every file in that
  folder once, which on MTP is the slow part; that is why it is a button and not the
  default. A fast compare still trusts the manifest until Verify content is pressed.
- **The transport row is laid out like a handheld player:** shuffle, previous, play,
  stop, next, repeat, with the sizes unchanged (play is the big circle, previous, stop
  and next the smaller ones).
- **Shuffle and repeat are drawn as the supplied icons.** Shuffle is two paths that cross
  and end in arrows; repeat is a loop whose top-right and bottom-left corners are the
  arrowheads, with a `1` in it for repeat one. While a mode is off its glyph is the same
  drawing struck through, in the muted grey; while it is on it is the plain drawing in the
  theme's text colour — white on Black AMOLED, dark on Light. The tooltips name the state
  (*Shuffle: on*, *Repeat one*), and repeat one still takes shuffle out of play.

## What's new in 0.73

- **Shuffle and repeat show what they are set to again.** Both toggles painted white
  whatever state they were in. The colour was not the problem: the button was being
  handed the wrong picture. A button with keyboard focus — or the pointer resting on it —
  asks Qt for `QIcon.Active` rather than `QIcon.Normal`, and only the *on* pixmap existed
  for that role, so an off button fell back to it and drew itself in the text colour. Every
  role now has an off pixmap in the muted colour and an on pixmap in the text colour, so
  off is dark grey and on is white on Black AMOLED — focused or not, hovered or not.
- **Repeat one takes shuffle out, and gives it back.** Repeat one plays the same track, so
  there is nothing to shuffle: choosing it turns shuffle off and greys the shuffle button
  out, its tooltip saying why. The setting is not thrown away — leave repeat one and
  shuffle comes back on if it was on before, unchanged from what it was. Repeat all and
  repeat off leave shuffle exactly as it is.
- **Shuffle is a real order now, not a random jump per track.** Turning shuffle on draws
  one order for the queue, opening with the track that is playing, and next and previous
  walk that order — so previous undoes next, and a queue of N tracks plays all N before it
  ends instead of replaying some and never reaching others. A row picked by hand joins the
  order at that point.
- **Repeat all restarts a shuffled queue reshuffled.** When the drawn order runs out and
  repeat is set to repeat all, a new order is drawn first, so the next pass does not open
  with the track that has just finished.

## What's new in 0.72

- **The transport buttons are drawn circles now, like a portable player.** Previous, next
  and stop are outlined circles with a glyph inside, and play/pause is a bigger circle in
  the middle that shows a triangle or the two pause bars. The glyphs are drawn in code
  (`player_icon`), not taken from the desktop's icon theme or a font, so they look the
  same on every desktop and stay crisp at any size — the old ones were the platform's
  media icons, which is why they looked nothing like this.
- **They follow the theme's text colour.** On Black AMOLED the rings and glyphs are white
  on black; on Light they are dark on the light bar; any theme edit recolours them with
  everything else. The ring is the button's own border, so it scales with the button and
  takes the same colour as the glyph.
- **The stop button got the same treatment** rather than being left as the odd one out:
  the same circle, with a square inside.
- **Shuffle and repeat say their state with colour, not a ring.** They sit outside the
  circles with no border: muted grey while off, the text colour while on — so on Black
  AMOLED an off shuffle and repeat are dark grey and a running one is white. Repeat all
  is a loop with an arrow; **repeat one** is the same loop with a small **1** inside it.
- **Hover and press still show**: the circles take a faint fill under the pointer and a
  stronger one while pressed, and the mode glyphs brighten on hover even when off.

## What's new in 0.71

- **Verify content looks and behaves like the other three buttons.** It no longer wears the
  outline-only *Ghost* style — it is an ordinary button beside Compare, Sync and
  Compare+Sync, as the rest of that row is.
- **The button that is highlighted while a job runs is the job you started.** Pressing
  Verify content used to light **Compare** up in the running colour, because a verification
  is internally a compare. Now the running colour (the theme's accent) follows the button
  you pressed: Verify content turns blue while it verifies, Compare goes and stays grey, and
  everything returns to grey when the pass ends.
- **Verify content now rewrites the sync manifest from what it read.** It reads every device
  copy this profile syncs, compares each one byte for byte with the PC file, and records
  each verified file again from that read — the content's SHA-256, the size and the
  timestamp the device listing actually showed. Before, a file that already had a record
  kept it untouched, so the manifest could hold a stale timestamp (or none) for a file that
  had just been read in full. A file whose device copy turns out to be different has its
  record dropped, so nothing in the manifest claims content the device does not hold; the
  next Sync puts the record back with the bytes it writes. Records for files that are
  *gone* from the device are kept on purpose, because that is how the next compare knows to
  call them a **restore** rather than a new file.
- **What it does not do, so nobody has to guess.** It does not hash unrelated files in the
  device folder: those have no PC counterpart to record against, and the quick scan already
  lists them and adopts or removes them by content. The manifest is per device, so a
  verification of one profile rewrites the records of the files that profile syncs, not
  another profile's.

## What's new in 0.70

- **The library comes back the way you left it.** The fold button's three positions —
  *Open all*, *Open letter markers only* and *Close all* — are saved with the collection, so
  the folders are in the same position next time the app starts instead of collapsing to
  whatever the auto-open setting says. The menu ticks the position the folders are in, and
  a rescan, a grouping change or a new search keeps it. Searches still open every result,
  since a filtered tree with closed folders would hide what was found.
- **A click on a cover opens that album.** Single click shows the album's tracks in the
  list with an *‹ Albums* bar above them naming the album, and one click on that bar goes
  back to the grid. Double-click still adds the album to the queue, nothing else: the open
  waits for the double-click interval and is cancelled when a second click arrives, so the
  two gestures never fight. Choosing List or Covers leaves the opened album behind.
- **The Devices tab has two layouts** (Preferences > Library): *Device list across the top*
  (the default) or *Device list down the side*. Both list the same devices — ``MTP · `` for a
  phone, ``USB · `` for a stick — and swapping between them keeps the open device open. The
  browser follows the list into either frame, rows and alternating colours follow the
  library's list, and a device that goes away takes its buttons and its row with it.
- **The Devices tab's two views are now called *Music* and *Files***, instead of *Music
  folders* and *Phone & USB*: one is the folders this collection scans, the other is what is
  on a plugged-in phone or stick.
- **New theme setting: the line around buttons.** Preferences > Theme has *Button outline* —
  a width from 0 to 6 px and a colour, with a sample button on the page showing both. 0
  draws no line at all, and an outline colour you have not chosen follows the template, so
  switching from Dark to Black AMOLED keeps your width but takes that template's line. It
  applies to the app's ordinary buttons and tool buttons; the round player buttons keep
  their own ring, and the buttons that draw no frame at all (the icon strip, the search
  box's own controls) stay frameless.

## What's new in 0.69

- **A disc's buffer is deleted when that disc leaves its drive — whatever took it out.**
  Each drive now has its own buffer directory, and that directory goes on every way a disc
  can leave: the app's eject, the tray's own button, the disc being pulled out by hand, the
  drive being unplugged, and another disc taking its place. Only a drive that says it is
  empty — no disc in it, or its tray open — counts as proof, so a disc sitting in a slow
  drive cannot lose its buffer during the seconds that drive spends spinning up, and a disc
  that is simply *gone* is not mistaken for one that is still there. A drive that cannot be
  asked at all for 30 seconds is the exception: nothing about its disc can be confirmed any
  more, so what was read from it goes too. The decision is made per drive, so a drive that
  says it is empty loses its buffer even while another drive still holds a disc.
- **A read can never put a deleted buffer back.** The check that names a finished read
  happens under the same lock that removes the directory, and the file that read writes to
  is created under that lock as well: a read that is no longer wanted writes nothing at
  all, and one that was already open is unlinked along with the directory. The app also
  deletes every buffer when it closes, and removes anything left behind by a crash at the
  next start, so a buffer outlives neither its disc nor the app.
- **A disc swapped in while the app was not looking is noticed.** When a drive stops
  answering and then reports a disc again, the table of contents is read once more. A
  different disc means the one that was there has gone: its buffer is deleted, its queued
  tracks leave the queue, and the CD tab shows the new disc. Reading the same disc again
  changes nothing — its tab and buffer stay as they are rather than being rebuilt and
  looked up afresh.
- **What the app cannot see.** A drive that never goes quiet — one whose disc is swapped
  for another entirely between two checks, without ever reporting its tray or a spin-up —
  leaves its buffer until the next disc change, the next eject, or the next start of the
  app. Every other way a disc can leave, including pulling it out mid-read with nothing
  queued, is caught and its buffer deleted.
- **A stalled read no longer holds up the next disc.** A buffer record was kept against the
  queue entry, which is only *this drive and this track number*: a read of one disc that
  never finished blocked the same track number of the disc that replaced it for 30 seconds.
  Records are now kept against the file they fill — that is, against that disc and track —
  and a disc leaving takes its own records with it.
- **New option: start buffering as soon as a disc is identified** (Preferences > Audio CD,
  off by default). With it on, the tracks the buffer depth covers are read as soon as the
  disc's table of contents has been read, before anything is queued — so the first track
  you press play on already comes from the buffer instead of waiting for the drive. What is
  queued still comes first: the track playing now, then the ones after it, then the disc's
  own tracks. With it off, buffering starts when a CD track is queued or played, as before.
  The depth applies either way, and Off reads nothing at all.

## What's new in 0.68

- **Playing a CD now buffers the tracks instead of reading the disc for each one.** The
  buffer read the track ahead only while nothing was playing: with a CD track streaming off
  the disc it waited, so a queued disc played live from start to finish and the drive span
  up again for every track. The track playing now goes first in the buffer's list, and
  playback is served from that read as it arrives, so the disc is read **once, in one
  pass** — and the drive stops when the queued tracks have been read.
- **Starting a track no longer waits for the drive, or for the whole track.** A track the
  buffer is reading starts playing from the bytes written so far; the now-playing pills say
  **from buffer** for it rather than **from disc**.
- **A seek past what has been read still reads the drive**, so it never waits for the
  buffer to catch up. While playback reads the disc itself, the read ahead stands back at
  its next chunk and carries on from where it stopped afterwards — one reader at a time, so
  nothing skips.
- The drive is never read in two places at once, including between playback and the buffer:
  the read ahead hands the drive over when playback asks for it, and takes it back when
  playback is done.

## What's new in 0.67

- **The CD buffer's *All queued CD tracks* option did nothing.** The wanted list was only
  built for a positive depth, so the All setting fell through to an empty list and no track
  was ever read ahead — every track streamed live off the disc, which is exactly the drive
  noise that made it look like playback was reading the disc and not the buffer. All now
  keeps every CD entry queued after the one playing, and the same line no longer drops the
  last queued track. Off, 1–4 tracks and All behave as the picker says; the default stays
  3 tracks ahead.
- **A track played straight off the disc now fills the buffer as it plays.** The bytes the
  stream server is already reading are written into that track's half-written cache file,
  and the file is named once the whole track has gone past. No extra drive work and no
  second reader, so nothing can skip; replaying that track, or looping the queue, then
  needs no drive at all. This is part of the buffer: with the depth at Off nothing is
  written at all.
- **An interrupted read carries on where it stopped.** A read that is cut short (the queue
  changes, or the drive is needed for the track that is playing) keeps its half-written
  file and resumes from that exact sector instead of reading the same audio a second time.
- **You can see what the buffer is doing.** The status bar says
  `Buffering CD: <title> (N track(s) left to read)` while the drive is being read, and the
  now-playing pills say **from disc** or **from buffer** for a CD track, so where the audio
  is coming from is never a guess.
- **New: an MB buffer for tracks playing from the PC.** Preferences > Playback has
  *Buffer playing tracks ahead* — Off, 30, 64, 128, 256, 512, 1024 or 2048 MB, on at 30 MB.
  The tracks coming up are read into memory ahead of the player: first the **next 30 seconds
  of every track coming up**, in play order, and only then deeper into them with what is
  left of the budget. So with a one-minute track 50 seconds in, the next track's first
  30 seconds are already read, whatever the size — and a bigger size fills whole tracks
  ahead. Nothing is decoded and nothing is copied: the player opens the same file it always
  did, by which time the bytes are in memory rather than waiting for a slow disk or a share.
  Off reads nothing at all.

## What's new in 0.66

- **Each profile now says what filesystem its device has, so file names survive the trip.**
  A new **Device filesystem** picker on the sync profile decides how a name is written to
  the device. **exFAT** and **MTP (mtpfs)** store names as UTF-16, so a name arrives exactly
  as it is on the PC — not one character is changed. **FAT32** cannot store `* ? : " < > | \`,
  a control character, or a name that ends in a space or a dot, so those are left out on the
  device; spaces and every other character are kept. FAT32 is the default, which is what
  every profile did before the setting existed, so an existing setup changes nothing until
  you pick otherwise.
- **Nothing is renamed in silence.** When a name does change on the way over, the sync log
  says so: `NAME  Artist - Album/01 - DECO*27.wav: stored on the device as
  Artist - Album/01 - DECO27.wav`.
- **Switching the setting leaves what is already on the device alone.** The manifest
  remembers the path each file was actually written to, so a card synced under FAT32 names is
  adopted where it stands when the profile moves to exFAT — no delete, no rewrite and no
  device read. Only files not yet on the device are affected by the new naming rule.

## What's new in 0.65

- **Fast hash now checks the device folder itself, and hashes a stray before removing it.**
  Every compare already listed the device folder to find files the PC has and the device
  lacks (planned as *restore* or *new*). The other half was missing: a file on the device
  that the library does not claim was removed in Mirror only when this app's own state
  database remembered writing it, so Bit-by-bit mirror cleared extras that Fast hash
  mirror left behind. One listing now decides both, and **nothing is removed before it has
  been checked**: a file whose size no library file shares cannot be library content and
  is settled without reading it; otherwise the device file is hashed and the library is
  searched for that content (only library files of that size are hashed, so it is a
  handful of files rather than the whole library). When the library is about to send
  exactly that content, the copy already on the device is **kept and adopted** as that
  file's copy — so a file you put on the device by hand is neither deleted nor written
  again — and a second copy of content the device already holds is a duplicate and goes.
  Update mode reports extras and reads nothing, because it never deletes.
- **The scan says what it did, and what it cost.** The log carries one line per compare —
  `SCAN Music: listed 1248 file(s) · 1242 matched · 3 missing · 2 extra (1 kept, 1
  removed)` — plus `KEEP`, `EXTRA` and `READ` lines naming the files involved; the plan
  summary counts *Extra N* separately from *Equal*, which no longer counts an adopted
  file as an ordinary equal one.
- **A hash sync no longer nested the target folder inside itself.** `_verify_device_names`
  prepended the target folder (`Music/`) to a manifest device path that already contained
  it, so after a Fast hash sync it copied every file a second time to `Music/Music/…` and
  recorded that as the file's location. A sync now leaves exactly one copy under the
  target, and the duplicates an earlier build left on a device are seen by the scan as
  second copies and removed in Mirror.

## What's new in 0.64

- **Verification is a button again, and it lives where it belongs.** The *Verify contents*
  check box is gone. In **Fast hash** a **Verify content** button sits beside
  Compare/Sync and does one thing: read every device file and compare it byte for byte.
  In *Bit-by-bit* there is no button, because that mode already reads both copies.
- **The status line says when the device was last verified.** For a Fast hash profile the
  line beside the device now reads *last sync … · last verified 2026-10-27 09:05*, or
  *not verified in full* while the manifest has never been checked by reading the device.
  A bit-by-bit sync leaves the note out: that compare was exact by itself, and the
  tooltip still explains what the manifest is and is not.
- **Check boxes are visible in every theme, including Black AMOLED.** The box next to
  Only audio files, Autosync, the tag list and the disc track list is now drawn by the
  app's own style from the active palette — a visible outline when empty, the accent
  colour with a tick in the on-accent colour when ticked — instead of relying on
  Fusion's dark-on-dark box, which left the outlines invisible on the AMOLED palette.
  Radio buttons get a centred dot in the same colours.

## What's new in 0.63

- **The CD tab now shows the release, not just track numbers.** Album, artist, year,
  genre, track count and total playing time sit above the track list, and the heading is
  the album. They come from whichever source named the disc (CDDB, MusicBrainz or
  Discogs) and are updated by *Find release*, so the tab says what the queue entries say.
- **Adding tracks from a CD no longer starts the queue.** With the queue stopped, *Add
  ticked to queue* (and its right-click entry) leaves it stopped; playback starts when
  you press play. The CD tab also has **Add CD to queue** and **Shuffle CD into queue**
  (both in the track menu), which add the whole disc in running or random order.
- **Sync comparison has two honest modes instead of a 128-bit shortcut.** *Bit-by-bit
  (exact)* reads both copies in full. *Fast hash* uses SHA-256 digests cached for the PC
  files and a per-device manifest of what was actually written to that device, checked
  against a fresh directory listing; a device file whose timestamp moved is checked again,
  and one that is missing is restored from the PC copy (the PC original is never deleted
  because the device lacks it).  **Verify content** forces a full read of every device
  file when certainty is needed, and rewrites those files' manifest records from the read
  (0.71); it is a button shown only in Fast hash mode, and the status line adds
  *last verified* for hash profiles. The plan, status line and
  summary always say whether the equal files were byte-verified or only matched the cache. Both modes stay available for
  every device, including MTP; bit-by-bit logs that reading a phone in full can be slow.

## What's new in 0.62

- **CDDB keeps working when one server doesn't.** GNUdb is the freedb successor, but it
  goes down (and some networks can't reach it — the CD tab showed *CDDB is unreachable*
  and left the disc unnamed). A CDDB lookup now tries GNUdb, then the dBpoweramp freedb
  server — which still holds the old freedb catalogue — and then the RetroBridge CDDB
  gateway, stopping at the first that answers. Each attempt has a 6-second limit, the
  server that answered is used first from then on, and one that didn't answer is skipped
  for five minutes, so a dead host costs a single short wait instead of one on every
  insert. The CDDB disc ID, query and entry parsing are unchanged, so any of the three
  servers names the disc the same way.
- **The CD tab no longer cries "lookup failed" when a source was simply down.** A disc
  that MusicBrainz doesn't know while CDDB can't be reached now reads *not found on CDDB
  or MusicBrainz · CDDB: no server answered*, and the full error is in the label's
  tooltip. "Lookup failed" is kept for the case where nothing answered at all, and when
  another source does name the disc its status stays clean.

## What's new in 0.61

- **CDDB as a third identification source.** Audio CDs are now also looked up on
  CDDB, through GNUdb — the database that took over when freedb.org shut down.
  CDDB is matched by disc ID, computed from the table of contents (a different ID
  from MusicBrainz's), and it knows a lot of discs the other two services have
  never catalogued. Preferences > Identification lists it with the others, and
  the default order is CDDB, Discogs, MusicBrainz. A source that is unreachable
  or doesn't know the disc is skipped and the next one tried, so one bad service
  no longer costs the disc its names. CDDB has no text search, so *Find release*
  still searches MusicBrainz and Discogs.
- **A removed disc takes its tracks with it.** Pulling the disc out of the drive —
  or ejecting it from the app — closes the CD tab and drops that disc's queued
  tracks, because a `cd://` entry can't play without the disc that holds it.
  Playback stops if one of them was playing, the entries and their buffered copies
  are forgotten, and the queue keeps playing the files around them. When the
  watcher sees a different disc in the same drive, the previous disc's tracks go
  too; putting the same disc back keeps them.
- **The title bar says Nebula.** *Nebula* is the short name, used in the title
  bar, menus and dialogs; *Nebula Music Center* is the full name in the About box,
  the desktop entry and the release files. Config and library folders live in
  `~/Nebula` since 0.84 (0.82 moved them out of the older `spectra` paths), and
  existing libraries, playlists and settings are carried over by that move.

## What's new in 0.60

- **A whole-tag window in the Tags tab.** Right-click a file and choose
  **Extended tags…** to see every tag it carries in one list — the nine core
  fields and the format's own keys together. Double-click a value to edit it,
  **＋** adds a tag (pick a core name or type any name), **✎** edits the selected
  value, **✕** removes it, and the cover sits on the right with its format, size
  and dimensions. **‹‹ ››** page through the selected files without losing what
  you typed. OK returns the values to the file list, where they stay amber until
  **Save tag** (`Ctrl+S`) writes them, exactly like every other edit there.
- **The Devices tab is now a music-folder view.** It opens on the folders that
  feed the current collection, as a library-style table: folder, location, track
  count, album count and total playing time. **Add folder…** (or dropping folders
  onto the table) scans a new location, **Remove** stops scanning the selected
  folder and drops its tracks, and **Rescan** looks for changes. Double-click
  plays a folder. **Files** switches to the device browser (see 0.70: the two views
  are called *Music* and *Files*, and the device list has a bar and a side layout).

## What's new in 0.59

- **Inserting or ejecting a disc no longer freezes the window.** 0.58 moved the
  table of contents and the tray off the GUI thread, but the drives were still
  asked for their status in the GUI thread every few seconds — and opening a
  drive node while a disc spins up, or while the tray is moving, blocks for
  seconds. That was the freeze the desktop offered to force-quit. The drives are
  now watched on a thread of their own: the status check, the table of contents
  and the tray all happen there, and the window only receives the results. A CD
  is picked up within about two seconds of going in, and the status bar says
  *Reading the disc…* while a slow drive is read.
- **The tray and the watcher don't fight.** While the app opens the tray the
  watcher stops touching the drive, and a read that was in flight when the tray
  moved is dropped instead of bringing a stale CD tab back after an eject. A
  disc whose table of contents can't be read (a data disc, or one still spinning
  up) is reported once and retried after ten seconds.

## What's new in 0.58

- **The window no longer freezes when a disc goes in or comes out.** Reading a
  new disc's table of contents happens on a worker, so a drive that is still
  spinning up can't stop the window responding. Eject opens the tray on a worker
  too, with *Ejecting the disc…* in the status bar until the tray is open.
- **CD tracks are buffered ahead of playback.** Preferences > Audio CD has a
  *Buffer CD tracks ahead* setting: Off, 1 to 4 tracks, or all queued CD tracks.
  The tracks coming up are read into `~/.cache/Nebula/tmp/cd-buffer` in the
  background, so when a played file ends and the next queued track is on the disc
  it starts at once instead of waiting for the drive to spin up and seek.
  Playback is served from the buffer, and nothing new is read while the track
  that is playing is itself being streamed from the disc — that track fills its own
  buffer copy as it plays, so it is on disk afterwards. A read that is interrupted
  resumes where it stopped instead of reading that audio again, the status bar says
  what is being read, and the player bar says *from disc* or *from buffer*. Buffered
  tracks are deleted as the queue moves past them, and the cache is cleared on start.

## What's new in 0.57

- **CD tracks play straight off the disc.** *Add to queue* on the Audio CD tab
  now queues the disc tracks themselves instead of ripping them first. Playback
  streams the PCM off the drive through a local server, so seeking works and no
  cache file is written. Tracks are shown with their disc, artist and album in
  the queue. Ripping to files is still there under *Rip…*.
- **Themes.** Tools > Preferences > Theme has three templates — *Light*, *Dark*
  and *Black AMOLED* — plus colour swatches for the background, panels, text,
  muted text and accent colour. Any change switches the template to *Custom*,
  with *Reset to template* to go back. The theme is saved and applied to the
  whole window as soon as you click OK or Apply, with no restart. Check boxes
  and radio buttons are drawn from the active palette (see 0.64), so they stay
  visible on all three templates.

## What's new in 0.55

- **Rip progress window.** Ripping and queueing an audio CD open a small window
  that shows each track as it is read and encoded. Any failure is shown in it.
  Ripping needs the `cdparanoia` and `ffmpeg` packages; the app says so when one
  is missing.
- **Eject.** Eject unlocks the tray, opens it, and waits to confirm the disc has
  left the drive. If the drive ignores that, the `eject` program is tried.
- **Bitrate mode.** Lossy rips show a *Bitrate mode* list with VBR and CBR, so
  both can be chosen. Lossless codecs hide the row, since they have no bitrate mode.
- **More sources for disc identification.** A CD is looked up on Discogs and
  MusicBrainz. Preferences has the priority order (Discogs first by default) and
  lets you turn each source on or off. Discogs needs a free account: sign in from
  Preferences. Find release on the CD tab searches the enabled sources by text.

## What's new in 0.54

- **Audio CD.** Insert an audio CD and an *Audio CD* tab opens with the track
  list. Tick tracks, then queue them or rip them. The disc is identified by its
  table of contents and looked up on MusicBrainz for the album, artist and track
  titles. Data tracks on mixed-mode discs are left out.
- **Rip CD.** Rip the checked tracks to FLAC, ALAC, MP3 (LAME), AAC (.m4a) or
  Opus, using cdparanoia for the reads and ffmpeg for the encodes. The lossless
  codecs round-trip bit-exact. Ripped files are tagged and can be added to the
  library.
- **Burn to disc.** Right-click tracks, albums or a playlist and choose *Burn to
  Disc…*. Pick the disc kind, drive and write speed (1x up to the drive's maximum).
  Audio CDs are converted to CD audio and written with cdrdao; playlists longer than
  the disc are split across discs at album breaks. CD-TEXT (album and track names)
  is optional. Data discs hold the files as they are, or converted to MP3 or Opus,
  and are written with wodim after an ISO 9660 image is built. Burning needs the
  `cdrdao`, `wodim`, `genisoimage` and `ffmpeg` packages.

## What's new in 0.53

- **Device filename check.** After a hash-mode sync, the app lists the phone or
  USB device and confirms every synced file is there under its expected name.
  Any file that is missing is copied again and logged as `MISSING`.
- **Edit tags.** Right-click an artist, album or song and choose *Edit tags…* to
  open a track-by-track editor (track list, tag fields, Previous/Next, Save/Close).
  Tags are written only on Save, and only for fields you changed.
- **Organize files.** The existing right-click action renames and moves files on
  disk by pattern, for artists, albums and songs.

## What's new in 0.52

- **Advanced shuffle.** Ten modes (Play in order, Shuffle all tracks, Shuffle
  albums, Shuffle artists, Shuffle inside albums, Loved first then shuffle,
  Spread artists, Least played first, Most played first, Top rated first). Pick
  the default in Tools > Preferences > Playback, or play the current selection
  once in any mode from Music > Play selection as.
- **Album play order.** When a queue plays in order and spans several albums,
  albums can play one after another (default) or in shuffled album order, with
  each album's tracks kept in disc and track order. Right-click an album and
  choose *Play album in order* to play it that way regardless of the shuffle mode.
- **Tools > Preferences (Ctrl+P).** One dialog for the library's double-click
  action, album covers, A–Z dividers and auto-open, plus the playback settings.
  These used to be in the library's wrench menu.

A single-file Linux music app: collection browser, player, batch tag editor,
music-folder manager, phone/USB device browser (MTP), audio CD ripping and
burning, and folder sync. **Nebula** is the short name; **Nebula Music Center**
the full one. PySide6 + mutagen, no build step.

![Library](artifacts/library.png)

![Online lookup](artifacts/online.png)

## Run it (bundled zip)

Unzip `nebula-music-center-0.65-linux-x86_64.zip`, then:

```bash
cd nebula-music-center-0.65-linux-x86_64
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

## Run it (AppImage)

```bash
chmod +x nebula-music-center-0.65-linux-x86_64.AppImage   # if the download dropped the bit
./nebula-music-center-0.65-linux-x86_64.AppImage
```

The AppImage contains the same files as the zip. It mounts itself through FUSE;
where FUSE is unavailable, `./nebula-music-center-0.65-linux-x86_64.AppImage
--appimage-extract` unpacks the same tree as `squashfs-root/`, and
`APPIMAGE_EXTRACT_AND_RUN=1 ./nebula-music-center-0.65-linux-x86_64.AppImage` starts the
app without a mount.

## Install it (.deb, Debian and Ubuntu)

```bash
sudo apt install ./nebula-music-center_1.26_amd64.deb
nebula-music-center              # or pick it from the menu
```

It installs to `/opt/nebula-music-center` with its own Qt, adds
`/usr/bin/nebula-music-center` and a menu entry, and reads the same
`~/Nebula` and `~/.cache/Nebula` folders as the zip and the AppImage — so the three
ways of running it share one library. `apt remove nebula-music-center` takes the
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

![Filter](artifacts/filter.png)

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
*Delete file permanently…*. Trash moves files to `~/Nebula/trash` (since 0.85).

**Options menu** (the wrench): music folders, rescan, reset play counts,
collections, details on/off, column chooser, group by…, saved groupings, locate
playing track, Find duplicates… (three match fields, keep-first selection),
collection statistics. Covers, A–Z dividers, auto-open and the double-click
action now live in **Tools > Preferences** (Ctrl+P).

**Mouse**: single click selects, double-click queues (or plays, configurable),
middle-click enqueues a track or a whole group.

## The Tags tab (mp3tag-style menus)

![Tags](artifacts/tags.png)

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

  ![Sync progress beside the tabs](artifacts/sync-activity.png)
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

```bash
pip install -r requirements-dev.txt
QT_QPA_PLATFORM=offscreen python3 tests/headless_check.py
```

**959 headless checks** (exit 0): real WAV/FLAC/MP3 files are generated, then
tags, stream specs, scanning, v2 database migration, the filter language,
ratings/loved/skips across rescans, every grouping preset, three-level nesting,
the A–Z hierarchy, full artist/album names and `01. Title` labels, visible
expander triangles, the spectrum reset on Stop, MusicBrainz 503 retries and query
fallback, nested folder grouping, saved
groupings, columns and header sorting, column reordering, the cover grid,
middle-click enqueue, queue-next, locate-playing, search-for-this,
organize-files, duplicate finder, delete-to-Trash (file, row and `.trashinfo`),
ReplayGain tag round-trips and volume maths, MusicBrainz/Cover Art parsing, the
lookup dialog and its tag application, multiple collections (separate DBs and
counts), `.m3u8` round-trips, real mouse double-click behaviour, queue
drag/sort/undo, format pills, the cover viewer, the spectrum (including the
decoded fallback), tag writing/renaming, the Tags-tab cover following the selection, free-form extended tags (MP3/FLAC/M4A/WAV round trips, multi-selection and key removal), the mp3tag menu swap, tag-list filter, tag undo/redo and clipboard edits, sync compare/execute including a one-bit same-size difference, SHA-256 digests and PC-hash reuse, a trusted manifest compare that opens no device file, a same-size device edit with its timestamp restored staying invisible until Verify content catches it, a moved device timestamp forcing a re-check, a missing device file planned as a restore without touching the PC copy, a refused transfer staying out of the manifest and new on the next compare, fast hash on an MTP device, both comparison modes staying selectable for MTP, a reviewed plan keeping its verification level, the cached/byte-verified wording in the plan and status line, the per-profile device filesystem (FAT32 dropping the reserved characters, a control character and a trailing space or dot while keeping accents and a space before the extension, exFAT and MTP keeping every character, a case-insensitive collision still getting a ` (2)` suffix, the field saving and a `profiles.json` written before it existed loading as FAT32, the `NAME` log line naming a file whose name changed, and a card synced under FAT32 names staying adopted — nothing copied and nothing removed — when the profile moves to exFAT), device queue entries keeping the device file with an MTP/iPod/USB source and a byte-identical device-buffer copy, queued device tracks and their buffer being removed when the device disconnects, the fold switch under the search box, an empty cover grid carrying no hint, a single no-device message, device path safety,
MTP URI escaping, MTP copies keeping folder names with spaces, the AAC/ALAC
sample-entry reader and the database re-read of stale MP4 codecs, autosync waiting
for a locked phone, the running-task button states and the sync activity text,
device copy operations and session restore, the quick scan of the device folder (a
file copied on by hand being adopted instead of deleted or written again, a copy under
another name staying adopted across compares with no device read, a duplicate of
content the device already holds being removed once, a size no library file shares being
settled without a read, update reporting an extra without removing or reading it, a file
dropped from the library being removed exactly once, and a device folder that lists
nothing planning no removals), a sync leaving one copy under the target with the target
folder not nested inside itself, queueing CD tracks straight off the
disc without ripping, the streaming server's WAV output and its Range seeks,
buffering the tracks ahead to disk and serving them from the cache without
reading the drive, the buffer depth setting and its pruning, the All option keeping every
queued CD track (it used to keep none, and used to drop the last one), a track streamed
live being kept as it plays and served from the file afterwards, an interrupted read
resuming from the sector it stopped at, a track the buffer is still reading playing as it
is read (one read of the drive, the stream server taking none of its own), the read ahead
giving the drive up when playback wants it and carrying on from where it stopped, a seek
past what has been buffered reading the drive instead of waiting, the buffer's status line
and the disc/buffer pills (including a track being read right now, which says **from
buffer**), a disc's buffer being deleted when the disc is pulled out of its drive while
nothing is queued (the drive directory and its half-read files included, with the status
bar saying so), when the app ejects it, and when another disc takes its place in the same
drive (while the disc that is in the drive keeps its own buffer, and a disc found again
later keeps it too); a drive that is only spinning up, or that cannot be asked at all, not
being taken as its disc having gone (and losing its buffer once it has gone unanswered for
half a minute); a drive that says it is empty losing its buffer even while another drive
holds a disc, and not being reported over and over; the same disc read again keeping the tab
it already has, while a disc swapped in between two checks - with the drive never going
quiet - is noticed and takes the old disc's buffer and queued tracks with it; a read that
was in flight not putting its file back after the buffer is deleted, and a read that starts
after that writing nothing at all; a failed read of a disc that has gone not holding up the
same track number of the disc that replaced it; the *start buffering as soon as a disc is
identified* option (offered in
Preferences and saved, the disc's own tracks kept and read with nothing queued, the queued
track and the ones after it coming first when something is queued, the depth still capping
what is read, and an unqueued disc's buffer going when the disc does),
and the PC read-ahead (the sizes offered and the 30 MB default, the next track's first
30 seconds read before anything deeper, the size capping the plan, a file shorter than
30 seconds capped by its own length, the track playing now left to the player, and Off
reading nothing), the CDDB disc ID
against a published freedb example, the CDDB query (disc ID, frame offsets,
lead-out) and its 200/210/202 answers, joined multi-line titles and escaped
characters, an empty CDDB entry counting as no match, a dead CDDB server being
skipped for the next one (and remembered, then retried after its cooldown), the
"not found" wording when a source was down but another answered, CDDB naming a
disc before MusicBrainz is asked, a source that is down falling through to the
next, the priority list gaining CDDB in an older
config, a removed disc's tracks leaving the queue (with the buffer released and
the tab closed), a swapped disc dropping the previous one's tracks while the same
disc keeps them, the drive watcher that probes the drives and reads the table of
contents on its own thread (checked by the thread the probe runs on, not just by
timing), the window staying answerable while a slow drive is read, the tray
opening off the GUI thread, a stale disc read not bringing the tab back after an
eject, the short name in the title bar, the whole-tag window
(its tag list, adding a tag through the ＋ prompts, removing one with ✕, edits
reaching the file list and the disk, paging between files), the Devices tab playing no
part in choosing the PC's folders any more (no folder table, no Music/Files switch), a
stick whose `Music` folder opens by itself and is remembered per device, its artist and
album folders read as tags, choosing the whole device re-listing it, the list showing
artists that open to albums that open to numbered tracks, the covers grid carrying one
cover per album with its name, artist and count, the List/Covers switch being remembered,
a synced device file taking its real tags from the library through the sync manifest and
a hand-copied one falling back to its folder layout, double-clicking a track playing its
album from that track, a phone labelled `MTP ·` and a
stick `USB ·`, the device bar listing every device and a click in it selecting one (with
the sidebar list agreeing), the list's *Title* and *Size* columns holding the tree and
its sizes and no repeated album, a device remembered across an unplug and a launch with
its nickname and a green or grey dot drawn in the row (counted by colour), selecting an
unplugged device showing no music and no false *disconnected* claim, the bar and the side layouts swapping with the browser
following the device list into either frame, Preferences offering both layouts and
applying one as soon as it is saved, the fold position being remembered (each of *Open
all*, *Close all* and *Open letter markers only* written to the config, ticked in the
menu as the only one, and a collapsed tree coming back the same way after a refresh —
which is what a launch does), a click on a cover opening that album's tracks behind an
*‹ Albums* bar that names it, the way back to the grid, choosing List leaving an opened
album behind, and a real double-click queueing the album without opening it; and
the theme templates, swatches and live palette,
the Verify content button appearing only in Fast hash (rendering the check boxes of
all three palettes and counting the pixels that stand out from the background, which
plain Fusion left at zero on the AMOLED palette), the last-verified
line and the *not verified in full* wording, which runs record a verification, and the
bit-by-bit sync that records none because it needs none.

The player's new buttons are checked by rendering their icons and reading the pixels: on the
Black AMOLED palette the previous, stop and next glyphs are drawn in that theme's text
colour (counted, not assumed), the big circle is 44 px against 34 for the others, and
playing swaps the triangle for pause bars and back. Shuffle and repeat are checked the way
they failed: the **buttons themselves** are grabbed and their pixels counted, with the
shuffle button given keyboard focus first, so an off toggle that paints in the text colour
— which is exactly what one focus-driven fallback used to do — fails the check; the icon is
also asked for its `QIcon.Active` off pixmap directly. Repeat one is checked to switch
shuffle off and disable its button while keeping `config["shuffle"]`, and to bring it back
when repeat moves on. Shuffle and repeat are `PlayerToggle`
buttons with no ring, their off pixmap drawn in the muted colour and their on pixmap in the
text colour, repeat one differing from repeat all by a visible number of pixels (the 1),
and a light theme redrawing the same glyphs in its dark text colour. The rings themselves
are asserted in the stylesheet, in the active theme's text colour.

Verify content is checked by what it leaves behind as well as by what it plans: a record's
timestamp is set to a nonsense value, a verification is run, and the record comes back
carrying the read digest and **no** timestamp; a device file is given a one-bit edit with
its timestamp put back, and the verification plans it *changed* **and** drops its manifest
record (the prior fast compare still calls it equal), then a sync puts the record back with
the copied bytes. A file written to the device by hand gets a record of its own content with
no source and no timestamp, beside the library's files in the same manifest, and Mirror
still plans it for removal; the device's timestamps are then scrambled and the next fast
compare reads nothing and calls both files equal; an audio-only profile verifies audio only
while the same profile with the box cleared records a `.txt` as well. The two button checks are plain state:
the Verify content button has the same object name as Compare, Sync and Compare+Sync, no
`Ghost` style, and it — not Compare — is the one given the running colour while it runs,
both when set directly and when the real click is captured with a stand-in worker.

The button outline is checked by rendering, not by reading the stylesheet: a real button
is drawn with 3 px, 1 px and 0 px outlines in a colour no palette uses, and the pixels of
that colour are counted — 3 px paints more than 1 px, and 0 px paints none. The width is
clamped (99 becomes 8, a negative becomes 0), an outline colour nobody picked follows the
template's own line, and Preferences saves the pair with the theme. `tests/make_screenshots.py`
renders the images in `artifacts/`.

The 0.75 ZIP is tested after extracting it to a clean directory: `./run.sh
--check` reports PySide6 6.12 loaded from `assets/`, its `spectra.py`, test file and
README hash byte-identical to the tree, and the offscreen launch stayed up until the
timeout with no traceback. The headless suite then passed **865/865** against that
extracted copy — it uses a virtualenv only because its WAV/FLAC/M4A fixtures need
numpy, soundfile and ffmpeg. The 0.75 AppImage passes `--check` from the tree
`--appimage-extract` writes, and the FUSE mount itself worked:
`./nebula-music-center-0.75-linux-x86_64.AppImage --check` reports PySide6 6.12 from
`/tmp/.mount_nebula…/usr/share/spectra/assets/PySide6` with exit 0, its payload hashes
match the tree, and the mounted image launched offscreen without a traceback. The CD buffer was also run against
a real audio CD in a real drive, which is where the 0.67 behaviour showed up: a track
started cold was read by the buffer and served to the player from the growing file with
**no** second reader on the drive, the queued tracks after it were read in the same pass
and the drive stopped when they were done, a seek to a part that had not been read yet
read the drive (with at most **one** `cdparanoia` process at any moment, sampled every
50 ms) and the read ahead carried on from where it had stopped. The profile form was rendered
and looked at as well: the Device filesystem picker sits under *Folder on device*
with a one-line note under it, because a wrapped note there is squeezed by the form at
ordinary window heights and paints over the rows below it. The check box fix was measured
rather than eyeballed: rendering an empty box on the palette that has been in use so
far leaves **0** pixels distinguishable from the background on both the dark and the
AMOLED palette, while the style's own drawing leaves 280 and 66 — which is the
outline the screenshots were missing.

The CDDB client was also run against the live servers from this machine, with the
freedb test TOC that the suite uses: GNUdb refused the connection, the lookup fell
through to the dBpoweramp freedb server and named the disc *Portishead — Dummy*
(1994) with all eleven track titles parsed out of the entry. The suite itself stays
offline and uses recorded answers. Reading the
extended tags adds about 17% to the per-file tag read on a 200-file mixed folder
(0.207 s → 0.243 s, best of three), which is not visible in the window.

Not verifiable in this sandbox (report these if they misbehave): actual audio
output (no sound device), real MTP hardware, and the X11 platform plugin on a
real display (the bundle was exercised with Qt's offscreen platform). There is no
disc in the drive, so insert, eject and removal run against faked drive ioctls.
GNUdb itself was refusing connections while this was built (every port, IPv4 and
IPv6), which is exactly the case the fallback servers exist for; the dBpoweramp
and RetroBridge endpoints did answer live, so the fallback path and the entry
parser were verified for real, but GNUdb's own responses are still untested.

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
