# Nebula Music Center — App Copy Deck (1.26)

This is a working copy deck generated from the text currently shown by the app. It covers descriptions, explanatory notes, tooltips, placeholders, dialog messages, notifications, headings, and the descriptive buttons. Standard `OK` / `Cancel` / `Apply` buttons, most menu commands, combo-box options and table headers are left out so the deck stays readable.

## How to edit this file

- Rewrite the text after **New:**. Leave **Current:** alone so the change can be compared.
- Keep placeholders such as `{name}`, `{path}` and `{count}` unless you want to rename them; tell me if a placeholder should change.
- Write `DELETE` after **New:** if a line should be removed, or add a new entry under the section if something is missing.
- Do not edit the source references or the line numbers. They are a snapshot for applying your copy back to the code.
- Technical method names are included only to identify where the text lives.

---

## App identity and About

- **A01 · Full app name** (`nebula.py:147`, `APP_NAME`)
  Current: `Nebula Music Center`  
  New:
- **A02 · Short name used in the title bar and menus** (`nebula.py:148`, `APP_SHORT`)
  Current: `Nebula`  
  New:
- **A03 · Version shown in About** (`nebula.py:149`, `VERSION`)
  Current: `1.26`  
  New:
- **A04 · About window title** (`nebula.py:22451`, `QMessageBox.about`)
  Current: `About Nebula`  
  New:
- **A05 · About description** (`nebula.py:22452–22461`, `_about`)
  Current:

  > Nebula Music Center  
  > Library, player, batch tagger, device browser (MTP/USB) and sync for Linux, in a single Python file.  
  > Music: collection tree with grouping, playlists and smart playlists, queue with drag reorder. Tags: batch tag editor with a whole-tag window for every tag on a file. Devices: the collection's music folders, plus phones and USB storage. Syncing: compare by content and mirror or update.  
  > Copyright (C) 2026 Roger Barthares.  
  > Licensed under the GNU General Public License, version 3 only. This program comes with ABSOLUTELY NO WARRANTY. See LICENSE for the full text.  
  > Source: https://github.com/blaz101/Nebula-Music-Center  
  > Contact: roger.barthares@gmail.com  
  New:

---

## Main window, menus and About
*Internal component: `MainWindow`*

- **C001 · window title · `MainWindow.__init__`** (`nebula.py:22144`)
  Current:  
  > Nebula 1.26
  New:
- **C002 · tab · `MainWindow.__init__`** (`nebula.py:22180`)
  Current:  
  > Music
  New:
- **C003 · tab · `MainWindow.__init__`** (`nebula.py:22181`)
  Current:  
  > Audiobooks
  New:
- **C004 · tab · `MainWindow.__init__`** (`nebula.py:22182`)
  Current:  
  > Tags
  New:
- **C005 · tab · `MainWindow.__init__`** (`nebula.py:22183`)
  Current:  
  > Devices
  New:
- **C006 · tab · `MainWindow.__init__`** (`nebula.py:22184`)
  Current:  
  > Syncing
  New:
- **C007 · tooltip · `MainWindow.__init__`** (`nebula.py:22195`)
  Current:  
  > Nebula — Nebula Music Center
  New:
- **C008 · status message · `MainWindow.__init__`** (`nebula.py:22212`)
  Current:  
  > Ready
  New:
- **C009 · menu · `MainWindow._build_menus`** (`nebula.py:22246`)
  Current:  
  > &Music
  New:
- **C010 · menu · `MainWindow._build_menus`** (`nebula.py:22262`)
  Current:  
  > &Audiobooks
  New:
- **C011 · menu · `MainWindow._build_menus`** (`nebula.py:22267`)
  Current:  
  > &Playlist
  New:
- **C012 · menu · `MainWindow._build_menus`** (`nebula.py:22279`)
  Current:  
  > &Tools
  New:
- **C013 · menu · `MainWindow._build_menus`** (`nebula.py:22292`)
  Current:  
  > &Help
  New:
- **C014 · menu · `MainWindow._build_menus`** (`nebula.py:22301`)
  Current:  
  > &File
  New:
- **C015 · menu · `MainWindow._build_menus`** (`nebula.py:22313`)
  Current:  
  > &Edit
  New:
- **C016 · menu · `MainWindow._build_menus`** (`nebula.py:22329`)
  Current:  
  > &View
  New:
- **C017 · menu · `MainWindow._build_menus`** (`nebula.py:22351`)
  Current:  
  > &Convert
  New:
- **C018 · menu · `MainWindow._build_menus`** (`nebula.py:22359`)
  Current:  
  > &Actions
  New:
- **C019 · menu · `MainWindow._build_menus`** (`nebula.py:22369`)
  Current:  
  > Tag &Sources
  New:
- **C020 · menu · `MainWindow._build_menus`** (`nebula.py:22374`)
  Current:  
  > &Help
  New:
- **C021 · message · `MainWindow._show_shortcuts`** (`nebula.py:22437`)
  Current:  
  > Space — play / pause
  > Ctrl+← / Ctrl+→ — previous / next track
  > Ctrl+O — add a music folder / open a folder in the tag editor
  > Ctrl+F — search the library / filter the tag list
  > Ctrl+S — save the queue as a playlist / save tags
  > Ctrl+Z / Ctrl+Y — undo / redo
  > Ctrl+Q — quit
  > 
  > Tags tab: Del removes files from the list, Ctrl+C / Ctrl+V copy and paste tags between files, Alt+1 / Alt+2 convert between filename and tags, Ctrl+M looks up MusicBrainz, Ctrl+R reverts, F5 reloads them from disk.
  > 
  > Double-click a track in the library to add it to the queue; drag rows in the queue to reorder; drop files on the queue to add them.
  New:
- **C022 · question · `MainWindow._first_run`** (`nebula.py:22469`)
  Current:  
  > Choose your music folder now?
  New:
- **C023 · question · `MainWindow._first_run`** (`nebula.py:22469`)
  Current:  
  > Welcome to Nebula
  New:
- **C024 · tooltip · `MainWindow._build_tray`** (`nebula.py:22518`)
  Current:  
  > Nebula Music Center 1.26
  New:
- **C025 · notification · `MainWindow._disc_lost`** (`nebula.py:22654`)
  Current:  
  > Disc removed: its buffer was deleted
  New:
- **C026 · tab · `MainWindow._show_disc_tab`** (`nebula.py:22661`)
  Current:  
  > CD
  New:
- **C027 · notification · `MainWindow._show_disc_tab`** (`nebula.py:22663`)
  Current:  
  > Audio CD inserted: {count} tracks
  New:
- **C028 · text · `MainWindow._show_disc_tab`** (`nebula.py:22674`)
  Current:  
  > {count} tracks · looking up on {' or '.join(sources)}…
  New:
- **C029 · notification · `MainWindow.show_disc_tab`** (`nebula.py:22688`)
  Current:  
  > No audio CD in a drive
  New:
- **C030 · notification · `MainWindow.eject_disc`** (`nebula.py:22695`)
  Current:  
  > No audio CD in a drive
  New:
- **C031 · notification · `MainWindow.burn_paths`** (`nebula.py:22726`)
  Current:  
  > A disc is already burning
  New:
- **C032 · notification · `MainWindow.burn_paths`** (`nebula.py:22764`)
  Current:  
  > Nothing to burn: the tracks have no length
  New:
- **C033 · question · `MainWindow.burn_paths`** (`nebula.py:22771`)
  Current:  
  > Burn {len(items)} file(s) to {len(discs)} disc(s) at {settings['speed']}x in {settings['device']}?
  > 
  > You will be asked to insert each further blank disc.
  New:
- **C034 · notification · `MainWindow._burn_start`** (`nebula.py:22796`)
  Current:  
  > Burning disc {index + 1} of {len(job['discs'])}
  New:
- **C035 · question · `MainWindow._burn_disc_finished`** (`nebula.py:22808`)
  Current:  
  > Disc {index + 1} of {total} is done and has been ejected. Insert a blank disc for disc {index + 2}, then click OK.
  New:

## Library
*Internal component: `LibraryTab`*

- **C036 · placeholder · `LibraryTab._build_collection_page`** (`nebula.py:12726`)
  Current:  
  > Enter search terms here…
  New:
- **C037 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12731`)
  Current:  
  > Clear search
  New:
- **C038 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12738`)
  Current:  
  > Library options
  New:
- **C039 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12747`)
  Current:  
  > Open or close folders
  New:
- **C040 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12778`)
  Current:  
  > Collection
  New:
- **C041 · label · `LibraryTab._build_collection_page`** (`nebula.py:12783`)
  Current:  
  > Group
  New:
- **C042 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12791`)
  Current:  
  > Grouping presets — the … button opens the three-level dialog
  New:
- **C043 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12796`)
  Current:  
  > Group by… (three levels and saved groupings)
  New:
- **C044 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12803`)
  Current:  
  > Details list
  New:
- **C045 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12809`)
  Current:  
  > Album cover grid
  New:
- **C046 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12828`)
  Current:  
  > Double-click to add to the queue; use the arrow to open a group
  New:
- **C047 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12852`)
  Current:  
  > Click an album to open it, double-click to queue it
  New:
- **C048 · tooltip · `LibraryTab._build_collection_page`** (`nebula.py:12871`)
  Current:  
  > Back to the album covers
  New:
- **C049 · label · `LibraryTab._build_playlists_page`** (`nebula.py:12899`)
  Current:  
  > Playlists
  New:
- **C050 · label · `LibraryTab._build_playlists_page`** (`nebula.py:12902`)
  Current:  
  > Double-click to add a playlist to the queue
  New:
- **C051 · button · `LibraryTab._build_playlists_page`** (`nebula.py:12917`)
  Current:  
  > Add selected playlist to queue
  New:
- **C052 · label · `LibraryTab._build_smart_page`** (`nebula.py:12928`)
  Current:  
  > Smart playlists
  New:
- **C053 · label · `LibraryTab._build_smart_page`** (`nebula.py:12931`)
  Current:  
  > Live queries that update with your library
  New:
- **C054 · button · `LibraryTab._build_smart_page`** (`nebula.py:12946`)
  Current:  
  > Add selected smart playlist to queue
  New:
- **C055 · label · `LibraryTab._build_queue_page`** (`nebula.py:12958`)
  Current:  
  > Queue
  New:
- **C056 · tooltip · `LibraryTab._build_queue_page`** (`nebula.py:12962`)
  Current:  
  > Undo queue change
  New:
- **C057 · tooltip · `LibraryTab._build_queue_page`** (`nebula.py:12967`)
  Current:  
  > Redo queue change
  New:
- **C058 · tooltip · `LibraryTab._build_queue_page`** (`nebula.py:13005`)
  Current:  
  > Click a column to sort the queue — drag rows to reorder
  New:
- **C059 · label · `LibraryTab._build_queue_page`** (`nebula.py:13021`)
  Current:  
  > 0 tracks · 0:00
  New:
- **C060 · text · `LibraryTab.refresh`** (`nebula.py:13184`)
  Current:  
  > Filter error: {error} — showing a plain text search
  New:
- **C061 · text · `LibraryTab.refresh`** (`nebula.py:13186`)
  Current:  
  > {shown} match{('es' if shown != 1 else '')} · field:value filters — artist:… · year:1990-1999 · bitrate:>320
  New:
- **C062 · text · `LibraryTab.refresh`** (`nebula.py:13189`)
  Current:  
  > field:value filters — artist:aphex · album:"…" · bitrate:>320 · rating:>=4
  New:
- **C063 · tooltip · `LibraryTab._build_level`** (`nebula.py:13305`)
  Current:  
  > {label} — {len(info['rows'])} track(s)
  New:
- **C064 · notification · `LibraryTab._enqueue_paths`** (`nebula.py:13685`)
  Current:  
  > Playing {label or str(len(paths)) + ' track(s)'}
  New:
- **C065 · notification · `LibraryTab._enqueue_paths`** (`nebula.py:13689`)
  Current:  
  > Added {label or str(len(paths)) + ' track(s)'} to the queue
  New:
- **C066 · notification · `LibraryTab.queue_next`** (`nebula.py:13842`)
  Current:  
  > Queued {len(paths)} track(s) to play next
  New:
- **C067 · notification · `LibraryTab.rate_paths`** (`nebula.py:13851`)
  Current:  
  > Rating {arrow} for {len(paths)} track(s)
  New:
- **C068 · notification · `LibraryTab.toggle_loved`** (`nebula.py:13862`)
  Current:  
  > {('♥ Loved' if loved else 'Unloved')} {len(paths)} track(s)
  New:
- **C069 · notification · `LibraryTab.locate_playing`** (`nebula.py:13880`)
  Current:  
  > The playing track is not in the current filter
  New:
- **C070 · message · `LibraryTab.show_in_browser`** (`nebula.py:13910`)
  Current:  
  > Show in file browser
  New:
- **C071 · notification · `LibraryTab.remove_from_library`** (`nebula.py:13923`)
  Current:  
  > Removed {len(paths)} track(s) from the library
  New:
- **C072 · notification · `LibraryTab.lookup_online`** (`nebula.py:13951`)
  Current:  
  > Select one or more tracks to look up
  New:
- **C073 · message · `LibraryTab.lookup_online`** (`nebula.py:13954`)
  Current:  
  > Online lookup is disabled in the config.
  New:
- **C074 · notification · `LibraryTab.analyse_replaygain`** (`nebula.py:13995`)
  Current:  
  > ReplayGain analysis is already running
  New:
- **C075 · window title · `LibraryTab.analyse_replaygain`** (`nebula.py:14001`)
  Current:  
  > ReplayGain
  New:
- **C076 · status message · `LibraryTab.analyse_replaygain`** (`nebula.py:14030`)
  Current:  
  > Measuring loudness for {total} track(s)…
  New:
- **C077 · status message · `LibraryTab._rg_progress`** (`nebula.py:14041`)
  Current:  
  > Measuring loudness: {done} of {total}…
  New:
- **C078 · notification · `LibraryTab._rg_done`** (`nebula.py:14056`)
  Current:  
  > ReplayGain stopped: {len(written)} track(s) written
  New:
- **C079 · message · `LibraryTab._rg_done`** (`nebula.py:14059`)
  Current:  
  > ffmpeg was not found (or could not decode these files).
  > 
  > Tracks that already carry REPLAYGAIN_* tags still work — set the RG button in the player bar to Track or Album gain.
  New:
- **C080 · notification · `LibraryTab._rg_done`** (`nebula.py:14067`)
  Current:  
  > ReplayGain written for {len(written)} track(s){suffix}
  New:
- **C081 · notification · `LibraryTab.edit_tags`** (`nebula.py:14092`)
  Current:  
  > Select some tracks to edit
  New:
- **C082 · notification · `LibraryTab.edit_tags`** (`nebula.py:14100`)
  Current:  
  > Saved tags for {len(dialog.saved)} file(s)
  New:
- **C083 · notification · `LibraryTab.organize_selected`** (`nebula.py:14105`)
  Current:  
  > Select some tracks to organize
  New:
- **C084 · notification · `LibraryTab.organize_selected`** (`nebula.py:14114`)
  Current:  
  > Organized {len(dialog.organized)} file(s)
  New:
- **C085 · notification · `LibraryTab.find_duplicates`** (`nebula.py:14122`)
  Current:  
  > Removed {len(dialog.removed)} duplicate(s) from the library
  New:
- **C086 · message · `LibraryTab.show_statistics`** (`nebula.py:14126`)
  Current:  
  > Artists: {stats['artists']}
  > Albums: {stats['albums']}
  > Tracks: {stats['tracks']}
  > Total length: {fmt_time(stats['length'])}
  > Total plays: {stats['plays']}
  > On disk: {fmt_human_size(stats['size'])}
  New:
- **C087 · text · `LibraryTab.rebuild_queue`** (`nebula.py:14335`)
  Current:  
  > {len(paths)} tracks · {fmt_time(total)}
  New:
- **C088 · notification · `LibraryTab._sort_queue`** (`nebula.py:14420`)
  Current:  
  > Queue sorted by {QUEUE_COLS[col]} ({('descending' if self._sort_desc else 'ascending')})
  New:
- **C089 · notification · `LibraryTab._add_dropped`** (`nebula.py:14440`)
  Current:  
  > Added {len(audio)} file(s) to the queue
  New:
- **C090 · notification · `LibraryTab.open_playlist`** (`nebula.py:14537`)
  Current:  
  > Playlist '{name}' is empty or its files are gone
  New:
- **C091 · notification · `LibraryTab._append_to_playlist`** (`nebula.py:14568`)
  Current:  
  > Added {len(paths)} track(s) to '{name}'
  New:
- **C092 · notification · `LibraryTab.save_playlist`** (`nebula.py:14582`)
  Current:  
  > Saved {len(self.player.queue)} tracks to '{name}'
  New:
- **C093 · warning · `LibraryTab.import_playlist`** (`nebula.py:14621`)
  Current:  
  > That playlist has no readable entries.
  New:
- **C094 · notification · `LibraryTab.export_m3u`** (`nebula.py:14633`)
  Current:  
  > Exported {len(self.player.queue)} track(s)
  New:
- **C095 · notification · `LibraryTab._smart_double`** (`nebula.py:14687`)
  Current:  
  > Added {len(paths)} tracks from “{item.text()}”
  New:
- **C096 · message · `LibraryTab.new_smart`** (`nebula.py:14699`)
  Current:  
  > Add at least one rule.
  New:
- **C097 · message · `LibraryTab.edit_smart`** (`nebula.py:14708`)
  Current:  
  > Only custom smart playlists can be edited.
  New:
- **C098 · message · `LibraryTab.delete_smart`** (`nebula.py:14725`)
  Current:  
  > Built-in smart playlists cannot be deleted.
  New:
- **C099 · message · `LibraryTab.new_collection`** (`nebula.py:14796`)
  Current:  
  > A collection with that name already exists.
  New:
- **C100 · message · `LibraryTab.remove_collection`** (`nebula.py:14830`)
  Current:  
  > Keep at least one collection.
  New:
- **C101 · question · `LibraryTab.reset_play_counts`** (`nebula.py:14899`)
  Current:  
  > Reset play counts for every track?
  New:
- **C102 · notification · `LibraryTab.rescan`** (`nebula.py:14919`)
  Current:  
  > Library is empty — add a music folder
  New:

## Tags
*Internal component: `TaggerTab`*

- **C103 · label · `TaggerTab.__init__`** (`nebula.py:15149`)
  Current:  
  > Tag
  New:
- **C104 · label · `TaggerTab.__init__`** (`nebula.py:15151`)
  Current:  
  > No files loaded
  New:
- **C105 · tooltip · `TaggerTab.__init__`** (`nebula.py:15167`)
  Current:  
  > Right-click for cover actions
  New:
- **C106 · label · `TaggerTab.__init__`** (`nebula.py:15189`)
  Current:  
  > Extended tags
  New:
- **C107 · button · `TaggerTab.__init__`** (`nebula.py:15191`)
  Current:  
  > Add…
  New:
- **C108 · placeholder · `TaggerTab.__init__`** (`nebula.py:15252`)
  Current:  
  > Filter files…
  New:
- **C109 · label · `TaggerTab.__init__`** (`nebula.py:15261`)
  Current:  
  > Filter:
  New:
- **C110 · question · `TaggerTab.revert`** (`nebula.py:15429`)
  Current:  
  > Discard unsaved changes and reload from disk?
  New:
- **C111 · notification · `TaggerTab.copy_selection`** (`nebula.py:15485`)
  Current:  
  > Copied {len(cells)} cell(s)
  New:
- **C112 · notification · `TaggerTab.paste_selection`** (`nebula.py:15518`)
  Current:  
  > Pasted into {len(touched)} file(s)
  New:
- **C113 · window title · `TaggerTab.load_paths`** (`nebula.py:15548`)
  Current:  
  > Reading files
  New:
- **C114 · notification · `TaggerTab.load_paths`** (`nebula.py:15571`)
  Current:  
  > Stopped after {added} of {total} files
  New:
- **C115 · tooltip · `TaggerTab._fill_cover`** (`nebula.py:15671`)
  Current:  
  > {_image_mime(data)} · {pm.width()}×{pm.height()}
  > {fmt_human_size(len(data))} · {role}
  > Right-click for cover actions
  New:
- **C116 · notification · `TaggerTab.extended_tags`** (`nebula.py:15822`)
  Current:  
  > Updated tags for {len(rows)} file(s) — save to write them
  New:
- **C117 · message · `TaggerTab._ext_add`** (`nebula.py:15933`)
  Current:  
  > '{key}' is a core field; edit it above.
  New:
- **C118 · prompt · `TaggerTab.tag_from_name`** (`nebula.py:15986`)
  Current:  
  > %tracknumber% - %artist% - %title%
  New:
- **C119 · message · `TaggerTab.tag_from_name`** (`nebula.py:16000`)
  Current:  
  > {miss} file(s) did not match the pattern.
  New:
- **C120 · notification · `TaggerTab.save`** (`nebula.py:16141`)
  Current:  
  > Saved {max(0, len(self.files) - len(errors))} file(s)
  New:

## Player and queue
*Internal component: `PlayerBar`*

- **C121 · tooltip · `PlayerBar.__init__`** (`nebula.py:9045`)
  Current:  
  > Click to enlarge the cover
  New:
- **C122 · tooltip · `PlayerBar.__init__`** (`nebula.py:9083`)
  Current:  
  > Shuffle
  New:
- **C123 · label · `PlayerBar.__init__`** (`nebula.py:9087`)
  Current:  
  > Nothing playing
  New:
- **C124 · tooltip · `PlayerBar.__init__`** (`nebula.py:9120`)
  Current:  
  > ReplayGain: off
  New:
- **C125 · tooltip · `PlayerBar.__init__`** (`nebula.py:9127`)
  Current:  
  > Stop playback when the current track ends
  New:
- **C126 · tooltip · `PlayerBar.__init__`** (`nebula.py:9132`)
  Current:  
  > Click to jump; drag the handle to seek
  New:
- **C127 · tooltip · `PlayerBar.__init__`** (`nebula.py:9143`)
  Current:  
  > Volume
  New:
- **C128 · notification · `PlayerBar.analyse_current`** (`nebula.py:9279`)
  Current:  
  > ReplayGain analysis is already running
  New:
- **C129 · status message · `PlayerBar.analyse_current`** (`nebula.py:9293`)
  Current:  
  > Measuring loudness with ffmpeg…
  New:
- **C130 · message · `PlayerBar._rg_current_done`** (`nebula.py:9299`)
  Current:  
  > ffmpeg was not found (or could not decode this file).
  > 
  > Install ffmpeg to measure loudness; tracks that already carry REPLAYGAIN_* tags work without it.
  New:
- **C131 · text · `PlayerBar._on_pos`** (`nebula.py:9935`)
  Current:  
  > {fmt_time(p / 1000)} / {fmt_time(self.player.duration() / 1000)}
  New:

## Spectrum
*Internal component: `SpectrumWidget`*

- **C132 · tooltip · `SpectrumWidget._set_tooltip`** (`nebula.py:8878`)
  Current:  
  > Live spectrum of the playing audio
  New:
- **C133 · tooltip · `SpectrumWidget._set_tooltip`** (`nebula.py:8882`)
  Current:  
  > Animated spectrum placeholder — no audio decoder is available in this Qt build; bars are not derived from the audio
  New:

## Devices
*Internal component: `DevicesTab`*

- **C134 · button · `DevicesTab.__init__`** (`nebula.py:16852`)
  Current:  
  > Mount phone (MTP)…
  New:
- **C135 · button · `DevicesTab.__init__`** (`nebula.py:16865`)
  Current:  
  > Mount phone (MTP)…
  New:
- **C136 · label · `DevicesTab.__init__`** (`nebula.py:16876`)
  Current:  
  > Plug in a device (phones: choose 'File transfer / MTP').
  New:
- **C137 · placeholder · `DevicesTab.__init__`** (`nebula.py:16896`)
  Current:  
  > Search the device's music…
  New:
- **C138 · tooltip · `DevicesTab.__init__`** (`nebula.py:16901`)
  Current:  
  > Clear search
  New:
- **C139 · tooltip · `DevicesTab.__init__`** (`nebula.py:16915`)
  Current:  
  > Open or close the artists' folders
  New:
- **C140 · button · `DevicesTab.__init__`** (`nebula.py:16939`)
  Current:  
  > Select device folder…
  New:
- **C141 · tooltip · `DevicesTab.__init__`** (`nebula.py:16941`)
  Current:  
  > Choose the folder on this device to show music from
  New:
- **C142 · tooltip · `DevicesTab.__init__`** (`nebula.py:16949`)
  Current:  
  > Artists, albums and tracks as a list
  New:
- **C143 · tooltip · `DevicesTab.__init__`** (`nebula.py:16954`)
  Current:  
  > Albums as covers
  New:
- **C144 · tooltip · `DevicesTab.__init__`** (`nebula.py:16958`)
  Current:  
  > Play everything shown here from the device
  New:
- **C145 · tooltip · `DevicesTab.__init__`** (`nebula.py:16962`)
  Current:  
  > Read the device folder again
  New:
- **C146 · tooltip · `DevicesTab.__init__`** (`nebula.py:16980`)
  Current:  
  > Double-click an artist, album or track to play it (or add it to the queue — Preferences > Library chooses which)
  New:
- **C147 · tooltip · `DevicesTab.__init__`** (`nebula.py:17026`)
  Current:  
  > Titles on the device; double-click a title or chapter to play it (or add it to the queue)
  New:
- **C148 · tooltip · `DevicesTab.__init__`** (`nebula.py:17039`)
  Current:  
  > Back to the album covers
  New:
- **C149 · text · `DevicesTab._show_not_connected`** (`nebula.py:17322`)
  Current:  
  > Plug it back in to browse its music.
  New:
- **C150 · text · `DevicesTab._show_not_connected`** (`nebula.py:17333`)
  Current:  
  > <b>{entry['name']}</b> — {DEVICE_STATUS_OFF}
  New:
- **C151 · prompt · `DevicesTab._rename_device`** (`nebula.py:17373`)
  Current:  
  > Name shown for {entry['raw']}:
  New:
- **C152 · message · `DevicesTab._remove_device`** (`nebula.py:17392`)
  Current:  
  > A sync is using this device. Wait for it to finish first.
  New:
- **C153 · question · `DevicesTab._remove_device`** (`nebula.py:17395`)
  Current:  
  > Remove "{entry['name']}" from the Devices tab?
  > 
  > Its music, sync profiles and presets stay where they are, and it can be added back from Preferences > Devices.
  New:
- **C154 · text · `DevicesTab._refresh_current_label`** (`nebula.py:17430`)
  Current:  
  > <b>{entry['name']}</b> — {kind} — {d.root}
  New:
- **C155 · text · `DevicesTab._refresh_current_label`** (`nebula.py:17432`)
  Current:  
  > <b>{entry['name']}</b> — {DEVICE_STATUS_OFF}
  New:
- **C156 · placeholder · `DevicesTab._restore_category`** (`nebula.py:17497`)
  Current:  
  > Search the device's {label.lower()}…
  New:
- **C157 · placeholder · `DevicesTab._category_changed`** (`nebula.py:17510`)
  Current:  
  > Search the device's {label.lower()}…
  New:
- **C158 · message · `DevicesTab._mount_mtp`** (`nebula.py:17539`)
  Current:  
  > A task is using this device. Wait for it to finish before mounting again.
  New:
- **C159 · message · `DevicesTab._mount_mtp`** (`nebula.py:17544`)
  Current:  
  > No unmounted MTP device found.
  > Unlock the phone and pick 'File transfer' in the USB notification. Requires gvfs-mtp / gvfs-backends.
  New:
- **C160 · text · `DevicesTab._update_hint`** (`nebula.py:17696`)
  Current:  
  > Filter error: {self._query_error} — showing a plain text search
  New:
- **C161 · text · `DevicesTab.reload`** (`nebula.py:17823`)
  Current:  
  > <b>{shown}</b> — {('MTP' if d.kind == 'mtp' else 'USB storage')} — {d.root}
  New:
- **C162 · text · `DevicesTab._scan_failed`** (`nebula.py:18128`)
  Current:  
  > Could not read the device: {last}
  New:
- **C163 · text · `DevicesTab._show_busy_page`** (`nebula.py:18232`)
  Current:  
  > The device is being read or written, so its music cannot be browsed, played or copied until that finishes.
  > 
  > A phone answers one request at a time: a second reader waits in line and the window stops answering, so this tab is out of the way while the task runs.
  > 
  > The device library is read again automatically afterwards.
  New:
- **C164 · text · `DevicesTab._fill_views`** (`nebula.py:18632`)
  Current:  
  > No tracks left in this album
  New:
- **C165 · message · `DevicesTab.copy_to_library`** (`nebula.py:18968`)
  Current:  
  > The library has no music folder yet.
  > 
  > Add one in the Library tab (Music > Add music folder…) and copy again.
  New:
- **C166 · message · `DevicesTab._run`** (`nebula.py:19201`)
  Current:  
  > A sync is using this device. Wait for it to finish before reading or writing the device from here.
  New:

## Sync
*Internal component: `SyncTab`*

- **C167 · label · `SyncTab.__init__`** (`nebula.py:19937`)
  Current:  
  > Profiles
  New:
- **C168 · tooltip · `SyncTab.__init__`** (`nebula.py:19955`)
  Current:  
  > Every folder this profile copies from, merged into one library on the device.
  New:
- **C169 · button · `SyncTab.__init__`** (`nebula.py:19957`)
  Current:  
  > Add…
  New:
- **C170 · tooltip · `SyncTab.__init__`** (`nebula.py:19975`)
  Current:  
  > Sync every file below the folders, or only the music and audiobooks you tick. Mirror deletes the copies it wrote for items you untick; Update never deletes.
  New:
- **C171 · button · `SyncTab.__init__`** (`nebula.py:19979`)
  Current:  
  > Choose items…
  New:
- **C172 · label · `SyncTab.__init__`** (`nebula.py:19983`)
  Current:  
  > Folder(s) to sync
  New:
- **C173 · tooltip · `SyncTab.__init__`** (`nebula.py:19992`)
  Current:  
  > The actual device paths for music and audiobooks, below the folder selected on the device.
  New:
- **C174 · tooltip · `SyncTab.__init__`** (`nebula.py:20000`)
  Current:  
  > Bit-by-bit reads every file on the device. Fast hash trusts the sync manifest; Verify content reads and hashes the device folder in full.
  New:
- **C175 · tooltip · `SyncTab.__init__`** (`nebula.py:20014`)
  Current:  
  > Re-encode every file on its way to this device. Off copies each file as it is.
  New:
- **C176 · tooltip · `SyncTab.__init__`** (`nebula.py:20019`)
  Current:  
  > The codec's bitrate, or its VBR quality where it has one. Changing this re-encodes a device copy on the next compare or sync.
  New:
- **C177 · checkbox · `SyncTab.__init__`** (`nebula.py:20022`)
  Current:  
  > Only audio files
  New:
- **C178 · checkbox · `SyncTab.__init__`** (`nebula.py:20023`)
  Current:  
  > Include LRC files
  New:
- **C179 · tooltip · `SyncTab.__init__`** (`nebula.py:20024`)
  Current:  
  > Also copy the matching .lrc lyric file beside a selected audio file.
  New:
- **C180 · checkbox · `SyncTab.__init__`** (`nebula.py:20026`)
  Current:  
  > Autosync when connected
  New:
- **C181 · tooltip · `SyncTab.__init__`** (`nebula.py:20036`)
  Current:  
  > Saved settings shared by every device: the folder on it, the variant, the compare method, the filesystem and any transcode codec and bitrate.
  New:
- **C182 · button · `SyncTab.__init__`** (`nebula.py:20040`)
  Current:  
  > Save…
  New:
- **C183 · tooltip · `SyncTab.__init__`** (`nebula.py:20041`)
  Current:  
  > Save this profile's settings as a preset shared by every device
  New:
- **C184 · tooltip · `SyncTab.__init__`** (`nebula.py:20045`)
  Current:  
  > Delete the chosen preset
  New:
- **C185 · label · `SyncTab.__init__`** (`nebula.py:20060`)
  Current:  
  > Bitrate
  New:
- **C186 · section heading · `SyncTab.__init__`** (`nebula.py:20067`)
  Current:  
  > Profile
  New:
- **C187 · tooltip · `SyncTab.__init__`** (`nebula.py:20086`)
  Current:  
  > Read and hash every file in the device folder (only audio files when this profile is audio only) and rebuild the sync manifest from those hashes, so it lists exactly what the device holds. Timestamps are ignored, so a device that rewrites them changes nothing. Exact, but slow on a phone.
  New:
- **C188 · tooltip · `SyncTab.__init__`** (`nebula.py:20132`)
  Current:  
  > Sync log — every compare, sync and verification this profile ran, newest first
  New:
- **C189 · prompt · `SyncTab.save_preset_dialog`** (`nebula.py:20283`)
  Current:  
  > Save these settings as a preset shared by every device:
  New:
- **C190 · question · `SyncTab._delete_preset`** (`nebula.py:20307`)
  Current:  
  > Delete the preset '{preset.name}'?
  New:
- **C191 · message · `SyncTab.show_log`** (`nebula.py:20352`)
  Current:  
  > Choose a profile first.
  New:
- **C192 · text · `SyncTab._refresh_device_status`** (`nebula.py:20455`)
  Current:  
  > <span style="color:{color}">●</span> {text} · <span style="color:{MUTED}">{last}</span>{tail}
  New:
- **C193 · tooltip · `SyncTab._method_changed`** (`nebula.py:20471`)
  Current:  
  > Not used with Force transcode: the device copy is a lossy encode, so it cannot be compared with the source bytes. Compare checks the source and encode setting recorded in the sync manifest.
  New:
- **C194 · tooltip · `SyncTab._method_changed`** (`nebula.py:20476`)
  Current:  
  > Read and hash every file in the device folder (only audio files when this profile is audio only) and rebuild the sync manifest from those hashes, so it lists exactly what the device holds. Timestamps are ignored, so a device that rewrites them changes nothing. Exact, but slow on a phone.
  New:
- **C195 · question · `SyncTab.delete_profile`** (`nebula.py:20682`)
  Current:  
  > Delete profile '{p.name}'?
  New:
- **C196 · message · `SyncTab._choose_target_folders`** (`nebula.py:20760`)
  Current:  
  > A task is using this device. Choose the folders when it finishes.
  New:
- **C197 · message · `SyncTab.run`** (`nebula.py:20941`)
  Current:  
  > The device is busy reading or copying files. Wait for that to finish, then start again.
  New:
- **C198 · message · `SyncTab.run`** (`nebula.py:20947`)
  Current:  
  > Press Compare first, review the list, then press Sync. Compare+Sync does both in one step.
  New:
- **C199 · message · `SyncTab.run`** (`nebula.py:20959`)
  Current:  
  > The device for this profile is not connected.
  New:
- **C200 · warning · `SyncTab.run`** (`nebula.py:20963`)
  Current:  
  > No items are selected to sync. Choose items, or switch back to Folder(s).
  New:
- **C201 · warning · `SyncTab.run`** (`nebula.py:20969`)
  Current:  
  > Add at least one folder to sync.
  New:
- **C202 · text · `SyncTab._done`** (`nebula.py:21085`)
  Current:  
  > Bit-by-bit: every matched file was compared byte for byte.
  New:
- **C203 · text · `SyncTab._done`** (`nebula.py:21088`)
  Current:  
  > Verify content: the device folder is empty — no file was read or hashed, so nothing was verified and the manifest was not rebuilt.
  New:
- **C204 · text · `SyncTab._done`** (`nebula.py:21092`)
  Current:  
  > Verify content: read and hashed {read} of {files} file(s) from the device; {unreadable} could not be read. The manifest records only what was read.
  New:
- **C205 · text · `SyncTab._done`** (`nebula.py:21097`)
  Current:  
  > Verify content: read and hashed {files} file(s) from the device; {matches} match the library exactly. The manifest now records those hashes.
  New:
- **C206 · text · `SyncTab._done`** (`nebula.py:21102`)
  Current:  
  > Fast hash: equal files matched the cached manifest — not verified byte for byte.
  New:

## Audiobooks
*Internal component: `AudiobooksTab`*

- **C207 · label · `AudiobooksTab.__init__`** (`nebula.py:21611`)
  Current:  
  > Audiobooks
  New:
- **C208 · button · `AudiobooksTab.__init__`** (`nebula.py:21615`)
  Current:  
  > Import…
  New:
- **C209 · tooltip · `AudiobooksTab.__init__`** (`nebula.py:21616`)
  Current:  
  > Move audiobooks into your audiobook folder
  New:
- **C210 · button · `AudiobooksTab.__init__`** (`nebula.py:21619`)
  Current:  
  > Import folder…
  New:
- **C211 · tooltip · `AudiobooksTab.__init__`** (`nebula.py:21620`)
  Current:  
  > Move a whole book folder, or a folder of book folders, into your audiobook folder
  New:
- **C212 · tooltip · `AudiobooksTab.__init__`** (`nebula.py:21630`)
  Current:  
  > The import runs in the background; this shows its progress
  New:
- **C213 · tooltip · `AudiobooksTab.__init__`** (`nebula.py:21656`)
  Current:  
  > Click a column heading to sort by it; double-click a title or chapter to play; right-click to play or add to queue
  New:
- **C214 · placeholder · `AudiobooksTab.__init__`** (`nebula.py:21659`)
  Current:  
  > Search titles, authors or chapters
  New:
- **C215 · tooltip · `AudiobooksTab.__init__`** (`nebula.py:21661`)
  Current:  
  > Type part of a title, author or chapter name
  New:
- **C216 · warning · `AudiobooksTab._prepare_target`** (`nebula.py:21725`)
  Current:  
  > Could not use {target}:
  > {exc}
  New:
- **C217 · text · `AudiobooksTab._render_books`** (`nebula.py:21823`)
  Current:  
  > {shown} of {count} title{('s' if count != 1 else '')}
  New:
- **C218 · text · `AudiobooksTab._render_books`** (`nebula.py:21826`)
  Current:  
  > {count} title{('s' if count != 1 else '')}
  New:
- **C219 · warning · `AudiobooksTab.import_folder`** (`nebula.py:21920`)
  Current:  
  > Choose a folder outside the audiobook folder it is being imported into.
  New:
- **C220 · notification · `AudiobooksTab._start_import`** (`nebula.py:22002`)
  Current:  
  > An import is already running
  New:
- **C221 · warning · `AudiobooksTab._import_failed`** (`nebula.py:22028`)
  Current:  
  > The import failed:
  > {last}
  New:

## Audio CD
*Internal component: `DiscTab`*

- **C222 · label · `DiscTab.__init__`** (`nebula.py:11274`)
  Current:  
  > Audio CD
  New:
- **C223 · label · `DiscTab.__init__`** (`nebula.py:11276`)
  Current:  
  > {len(disc.audio_tracks)} audio tracks
  New:
- **C224 · button · `DiscTab.__init__`** (`nebula.py:11329`)
  Current:  
  > Add ticked to queue
  New:
- **C225 · button · `DiscTab.__init__`** (`nebula.py:11330`)
  Current:  
  > Add CD to queue
  New:
- **C226 · button · `DiscTab.__init__`** (`nebula.py:11331`)
  Current:  
  > Shuffle CD into queue
  New:
- **C227 · tooltip · `DiscTab.__init__`** (`nebula.py:11332`)
  Current:  
  > Add the ticked tracks to the end of the queue; nothing starts playing
  New:
- **C228 · tooltip · `DiscTab.__init__`** (`nebula.py:11333`)
  Current:  
  > Add every track on the disc to the end of the queue
  New:
- **C229 · tooltip · `DiscTab.__init__`** (`nebula.py:11334`)
  Current:  
  > Add every track on the disc to the queue in random order
  New:
- **C230 · button · `DiscTab.__init__`** (`nebula.py:11346`)
  Current:  
  > Rip…
  New:
- **C231 · button · `DiscTab.__init__`** (`nebula.py:11347`)
  Current:  
  > Find release…
  New:
- **C232 · notification · `DiscTab.queue_checked`** (`nebula.py:11446`)
  Current:  
  > Tick the tracks you want to add first
  New:
- **C233 · notification · `DiscTab.rip_checked`** (`nebula.py:11476`)
  Current:  
  > Tick the tracks you want to rip first
  New:
- **C234 · warning · `DiscTab._rip`** (`nebula.py:11490`)
  Current:  
  > Choose a folder to rip to.
  New:
- **C235 · text · `DiscTab._ripped`** (`nebula.py:11506`)
  Current:  
  > Ripped {len(paths)} track(s) to {folder}
  New:
- **C236 · notification · `DiscTab._ripped`** (`nebula.py:11507`)
  Current:  
  > Ripped {len(paths)} track(s) to {folder}
  New:
- **C237 · notification · `DiscTab._start`** (`nebula.py:11512`)
  Current:  
  > A CD job is already running
  New:

## Preferences
*Internal component: `PreferencesDialog`*

- **C238 · window title · `PreferencesDialog.__init__`** (`nebula.py:7796`)
  Current:  
  > Preferences
  New:
- **C239 · tooltip · `PreferencesDialog._theme_page`** (`nebula.py:7889`)
  Current:  
  > Change the {label.lower()} colour
  New:
- **C240 · tooltip · `PreferencesDialog._theme_page`** (`nebula.py:7906`)
  Current:  
  > How thick the line around buttons is — 0 draws none
  New:
- **C241 · tooltip · `PreferencesDialog._theme_page`** (`nebula.py:7913`)
  Current:  
  > Change the colour of the line around buttons
  New:
- **C242 · tooltip · `PreferencesDialog._theme_page`** (`nebula.py:7922`)
  Current:  
  > This is the outline those two settings draw
  New:
- **C243 · label · `PreferencesDialog._theme_page`** (`nebula.py:7929`)
  Current:  
  > Preview: this is how text sits on a panel, with the accent on the left.
  New:
- **C244 · tooltip · `PreferencesDialog._library_page`** (`nebula.py:8025`)
  Current:  
  > Used until you choose a position with the library's fold button — after that the folders open the way you left them
  New:
- **C245 · button · `PreferencesDialog._audiobooks_page`** (`nebula.py:8046`)
  Current:  
  > Select folder…
  New:
- **C246 · label · `PreferencesDialog._audiobooks_page`** (`nebula.py:8052`)
  Current:  
  > Import and Import folder move audio into this destination and add it to the audiobook folders. Both run in the background; the Audiobooks tab shows their progress.
  New:
- **C247 · label · `PreferencesDialog._devices_page`** (`nebula.py:8071`)
  Current:  
  > Removing a device from the Devices tab only hides it there; its music, sync profiles and presets are untouched. A removed device stays out of the tab after a restart or a re-plug until it is restored here.
  New:
- **C248 · text · `PreferencesDialog._restore_removed`** (`nebula.py:8125`)
  Current:  
  > {name} will come back when you press Apply.
  New:
- **C249 · tooltip · `PreferencesDialog._playback_page`** (`nebula.py:8151`)
  Current:  
  > Click anywhere on the time bar to jump to that point. Turn this off to page with a click; dragging the handle still seeks.
  New:
- **C250 · label · `PreferencesDialog._playback_page`** (`nebula.py:8162`)
  Current:  
  > Play selection as (Music menu) plays once in any mode without changing this setting. Play album in order always keeps disc and track order.
  New:
- **C251 · label · `PreferencesDialog._playback_page`** (`nebula.py:8168`)
  Current:  
  > Buffering reads the tracks coming up into memory before the player needs them, which helps when the library is on a slow disk or a share. Every track coming up has its first 30 seconds read first, so the next one is ready to start, and a bigger size reads further ahead. Nothing is decoded and nothing is copied: the player opens the same file it always did, and Off reads nothing at all.
  New:
- **C252 · label · `PreferencesDialog._playback_page`** (`nebula.py:8177`)
  Current:  
  > The device buffer copies the tracks coming up from a phone or player into a local cache. The track playing now is copied first, then the ones after it while the size lasts, and playback uses a copy once it is complete. A size is a budget for whole tracks, so a single large track can be bigger than the size you pick. Copies are deleted when that device is disconnected or the app closes.
  New:
- **C253 · tooltip · `PreferencesDialog._sync_page`** (`nebula.py:8199`)
  Current:  
  > How many finished compares, syncs and verifications each profile's log keeps. Older runs are dropped as new ones finish.
  New:
- **C254 · label · `PreferencesDialog._sync_page`** (`nebula.py:8204`)
  Current:  
  > Each sync profile has its own Choose Target Folders button. It picks the selected device folder and the Music and Audiobooks folders below it, so changing one profile never changes another.
  New:
- **C255 · label · `PreferencesDialog._sync_page`** (`nebula.py:8210`)
  Current:  
  > Every compare, sync and verification adds one entry to that profile's log: when it ran, what it was, how many files were new, updated, restored or removed, any errors, and the file lines. The clock-and-page button above the change list opens it, newest first. A profile's log is deleted with the profile, and Clear log empties it without forgetting anything on the device.
  New:
- **C256 · label · `PreferencesDialog._backup_page`** (`nebula.py:8225`)
  Current:  
  > Backup and transfer
  New:
- **C257 · label · `PreferencesDialog._backup_page`** (`nebula.py:8228`)
  Current:  
  > Export selected settings to one JSON file, or import a file made by Nebula. Preferences are merged; sync profiles, presets and smart playlists replace the selected current ones. Account sign-ins are never exported.
  New:
- **C258 · button · `PreferencesDialog._backup_page`** (`nebula.py:8242`)
  Current:  
  > Export settings…
  New:
- **C259 · button · `PreferencesDialog._backup_page`** (`nebula.py:8244`)
  Current:  
  > Import settings…
  New:
- **C260 · warning · `PreferencesDialog._export_settings`** (`nebula.py:8263`)
  Current:  
  > Choose at least one kind of setting to export.
  New:
- **C261 · warning · `PreferencesDialog._export_settings`** (`nebula.py:8277`)
  Current:  
  > Could not export the settings:
  > {exc}
  New:
- **C262 · text · `PreferencesDialog._export_settings`** (`nebula.py:8280`)
  Current:  
  > Exported {len(groups)} setting group(s) to {path}
  New:
- **C263 · warning · `PreferencesDialog._import_settings`** (`nebula.py:8285`)
  Current:  
  > Choose at least one kind of setting to import.
  New:
- **C264 · warning · `PreferencesDialog._import_settings`** (`nebula.py:8296`)
  Current:  
  > Could not read the settings file:
  > {exc}
  New:
- **C265 · question · `PreferencesDialog._import_settings`** (`nebula.py:8301`)
  Current:  
  > Import these settings?
  > 
  > {chosen}
  > 
  > Preferences are merged. Selected sync profiles, presets and smart playlists replace the current ones. A backup is kept in config.json.bak.
  New:
- **C266 · warning · `PreferencesDialog._import_settings`** (`nebula.py:8310`)
  Current:  
  > Could not import the settings:
  > {exc}
  New:
- **C267 · text · `PreferencesDialog._import_settings`** (`nebula.py:8340`)
  Current:  
  > Imported {len(groups)} setting group(s) from {path}
  New:
- **C268 · message · `PreferencesDialog._import_settings`** (`nebula.py:8341`)
  Current:  
  > The selected settings were imported.
  New:
- **C269 · label · `PreferencesDialog._cd_page`** (`nebula.py:8359`)
  Current:  
  > Buffered tracks are read in the background into a temporary file, so starting one doesn't wait for the drive to spin up. The track playing now is read first and playback follows that read, then the tracks ahead of it, so the disc is read once in one pass and the drive stops when they are ready. Seeking past what has been read reads the drive, and the read ahead stands back while it does. Buffered files are deleted with the disc, and when the app closes, so nothing read from a disc stays behind.
  New:
- **C270 · label · `PreferencesDialog._cd_page`** (`nebula.py:8369`)
  Current:  
  > With the start-as-soon-as-identified option on, the tracks the depth covers are read as soon as a disc's table of contents has been read, before anything is queued, so the first track you play already comes from the buffer. With it off, buffering starts when a disc track is queued or played. The depth applies either way.
  New:
- **C271 · label · `PreferencesDialog._cd_page`** (`nebula.py:8377`)
  Current:  
  > Everything buffered from a disc is deleted the moment that disc leaves the drive - the app's eject, the tray button, the disc being pulled out, the drive being unplugged, or another disc taking its place - so a buffer never outlives the disc it was read from. Each drive keeps its own buffer, and a drive that says it is empty loses it even while another drive still holds a disc. A drive that is only spinning up, or not answering at all, is not taken as its disc having gone; if it cannot be asked for half a minute, the buffer it was read from goes too.
  New:
- **C272 · label · `PreferencesDialog._identify_page`** (`nebula.py:8394`)
  Current:  
  > When an audio CD goes in, the sources that are on are tried in this order. CDDB and MusicBrainz are matched by disc ID. Discogs has no disc ID lookup, so use Find release on the CD tab to search it.
  New:
- **C273 · button · `PreferencesDialog._identify_page`** (`nebula.py:8427`)
  Current:  
  > Sign in to Discogs…
  New:
- **C274 · text · `PreferencesDialog._id_numbers`** (`nebula.py:8439`)
  Current:  
  > {i + 1}. {ID_SOURCES[item.data(Qt.ItemDataRole.UserRole)]}
  New:
- **C275 · warning · `PreferencesDialog._discogs_connect`** (`nebula.py:8470`)
  Current:  
  > Could not start Discogs sign-in: {exc}
  New:
- **C276 · prompt · `PreferencesDialog._discogs_connect`** (`nebula.py:8473`)
  Current:  
  > Approve Nebula in the browser window that just opened, then paste the code Discogs shows you here:
  New:
- **C277 · warning · `PreferencesDialog._discogs_connect`** (`nebula.py:8482`)
  Current:  
  > Discogs did not accept the code: {exc}
  New:

## Extended tags
*Internal component: `ExtendedTagsDialog`*

- **C278 · label · `ExtendedTagsDialog.__init__`** (`nebula.py:12309`)
  Current:  
  > Metadata
  New:
- **C279 · tooltip · `ExtendedTagsDialog.__init__`** (`nebula.py:12341`)
  Current:  
  > Add a tag
  New:
- **C280 · tooltip · `ExtendedTagsDialog.__init__`** (`nebula.py:12345`)
  Current:  
  > Edit the selected value
  New:
- **C281 · tooltip · `ExtendedTagsDialog.__init__`** (`nebula.py:12349`)
  Current:  
  > Remove the selected tag
  New:
- **C282 · label · `ExtendedTagsDialog.__init__`** (`nebula.py:12359`)
  Current:  
  > Cover
  New:
- **C283 · tooltip · `ExtendedTagsDialog.__init__`** (`nebula.py:12369`)
  Current:  
  > Right-click for cover actions
  New:
- **C284 · tooltip · `ExtendedTagsDialog.__init__`** (`nebula.py:12388`)
  Current:  
  > Previous file
  New:
- **C285 · tooltip · `ExtendedTagsDialog.__init__`** (`nebula.py:12391`)
  Current:  
  > Next file
  New:
- **C286 · window title · `ExtendedTagsDialog._refresh`** (`nebula.py:12445`)
  Current:  
  > Tags — {count} files
  New:
- **C287 · text · `ExtendedTagsDialog._fill_cover`** (`nebula.py:12483`)
  Current:  
  > {_image_mime(data)}  ·  {pm.width()}×{pm.height()}
  > {fmt_human_size(len(data))}  ·  {role}
  New:
- **C288 · text · `ExtendedTagsDialog._fill_cover`** (`nebula.py:12488`)
  Current:  
  > A cover is embedded but could not be read
  New:

## Online metadata lookup
*Internal component: `OnlineLookupDialog`*

- **C289 · window title · `OnlineLookupDialog.__init__`** (`nebula.py:10873`)
  Current:  
  > Online metadata & cover lookup
  New:
- **C290 · label · `OnlineLookupDialog.__init__`** (`nebula.py:10898`)
  Current:  
  > Artist
  New:
- **C291 · label · `OnlineLookupDialog.__init__`** (`nebula.py:10900`)
  Current:  
  > Album
  New:
- **C292 · label · `OnlineLookupDialog.__init__`** (`nebula.py:10907`)
  Current:  
  > no preview
  New:
- **C293 · label · `OnlineLookupDialog.__init__`** (`nebula.py:10913`)
  Current:  
  > Search MusicBrainz by artist and album.
  New:
- **C294 · text · `OnlineLookupDialog.search`** (`nebula.py:10973`)
  Current:  
  > Enter an artist or an album name first.
  New:
- **C295 · text · `OnlineLookupDialog._show_results`** (`nebula.py:10987`)
  Current:  
  > No release found. Try a shorter artist or album name.
  New:
- **C296 · text · `OnlineLookupDialog._write_cover`** (`nebula.py:11056`)
  Current:  
  > Cover Art Archive has no front image for this release.
  New:
- **C297 · text · `OnlineLookupDialog._write_cover`** (`nebula.py:11074`)
  Current:  
  > Could not write a cover next to the selected files.
  New:
- **C298 · text · `OnlineLookupDialog.apply_tags`** (`nebula.py:11082`)
  Current:  
  > Fetching the track list for the release…
  New:

## Burn audio CD
*Internal component: `BurnDialog`*

- **C299 · window title · `BurnDialog.__init__`** (`nebula.py:11658`)
  Current:  
  > Burn to disc
  New:
- **C300 · checkbox · `BurnDialog.__init__`** (`nebula.py:11673`)
  Current:  
  > Write album and track names to the disc (CD-TEXT)
  New:
- **C301 · text · `BurnDialog._refresh`** (`nebula.py:11722`)
  Current:  
  > {fmt_time(self.total_seconds)} of music. Tracks are converted to CD audio (44.1 kHz, 16-bit, stereo) and split across discs at album breaks.
  New:
- **C302 · text · `BurnDialog._refresh`** (`nebula.py:11725`)
  Current:  
  > Files are written to a data disc (ISO 9660 with Joliet and Rock Ridge names). Most computers read these; many home and car CD players do not.
  New:

## Rip audio CD
*Internal component: `RipDialog`*

- **C303 · window title · `RipDialog.__init__`** (`nebula.py:11542`)
  Current:  
  > Rip audio CD
  New:
- **C304 · button · `RipDialog.__init__`** (`nebula.py:11555`)
  Current:  
  > Set to perceptually lossless
  New:
- **C305 · button · `RipDialog.__init__`** (`nebula.py:11560`)
  Current:  
  > Browse…
  New:
- **C306 · label · `RipDialog.__init__`** (`nebula.py:11569`)
  Current:  
  > Bitrate mode
  New:

## Find CD release
*Internal component: `FindReleaseDialog`*

- **C307 · window title · `FindReleaseDialog.__init__`** (`nebula.py:11195`)
  Current:  
  > Find release
  New:
- **C308 · placeholder · `FindReleaseDialog.__init__`** (`nebula.py:11203`)
  Current:  
  > Artist and album
  New:
- **C309 · label · `FindReleaseDialog.__init__`** (`nebula.py:11213`)
  Current:  
  > Sources are searched in the order set in Preferences > Identification.
  New:

## CD progress
*Internal component: `CdJobDialog`*

- **C310 · label · `CdJobDialog.__init__`** (`nebula.py:11160`)
  Current:  
  > Starting…
  New:

## Sync target folders
*Internal component: `SyncTargetsDialog`*

- **C311 · window title · `SyncTargetsDialog.__init__`** (`nebula.py:19786`)
  Current:  
  > Choose Target Folders
  New:
- **C312 · label · `SyncTargetsDialog.__init__`** (`nebula.py:19794`)
  Current:  
  > Pick the folder on the device, then the two folders below it. The actual paths are shown at the bottom.
  New:
- **C313 · button · `SyncTargetsDialog._row`** (`nebula.py:19827`)
  Current:  
  > Choose…
  New:
- **C314 · warning · `SyncTargetsDialog._choose_base`** (`nebula.py:19853`)
  Current:  
  > Choose a folder on this device.
  New:
- **C315 · message · `SyncTargetsDialog._choose_sub`** (`nebula.py:19863`)
  Current:  
  > Choose the selected folder on the device first.
  New:
- **C316 · warning · `SyncTargetsDialog._choose_sub`** (`nebula.py:19874`)
  Current:  
  > Choose the {label} folder inside {self.base.text() or 'the device root'}.
  New:
- **C317 · text · `SyncTargetsDialog._update_preview`** (`nebula.py:19891`)
  Current:  
  > Music: {self._full(self.music)}
  > Audiobooks: {self._full(self.audiobooks)}
  New:

## Sync log
*Internal component: `SyncLogDialog`*

- **C318 · window title · `SyncLogDialog.__init__`** (`nebula.py:19400`)
  Current:  
  > Sync log — {profile.name}
  New:
- **C319 · text · `SyncLogDialog._fill`** (`nebula.py:19439`)
  Current:  
  > {len(entries)} of the last {self.keep} run(s) kept · newest first
  New:
- **C320 · label · `SyncLogDialog._fill`** (`nebula.py:19441`)
  Current:  
  > No compare, sync or verification has run for this profile yet.
  New:
- **C321 · label · `SyncLogDialog._fill`** (`nebula.py:19453`)
  Current:  
  > <b>{when}</b> · {kind}
  New:
- **C322 · question · `SyncLogDialog._clear`** (`nebula.py:19492`)
  Current:  
  > Clear every entry in {self.profile.name}'s sync log?
  New:

## Sync selection
*Internal component: `SyncSelectionDialog`*

- **C323 · window title · `SyncSelectionDialog.__init__`** (`nebula.py:19538`)
  Current:  
  > Choose items to sync
  New:
- **C324 · label · `SyncSelectionDialog.__init__`** (`nebula.py:19581`)
  Current:  
  > Choose what should be copied to the device. Folder sync is on the previous screen.
  New:
- **C325 · text · `SyncSelectionDialog._update_summary`** (`nebula.py:19765`)
  Current:  
  > {count} item{('s' if count != 1 else '')} selected
  New:

## Smart playlist
*Internal component: `SmartPlaylistDialog`*

- **C326 · window title · `SmartPlaylistDialog.__init__`** (`nebula.py:10313`)
  Current:  
  > Smart playlist
  New:
- **C327 · label · `SmartPlaylistDialog.__init__`** (`nebula.py:10365`)
  Current:  
  > Rules
  New:
- **C328 · placeholder · `SmartPlaylistDialog._rule_row`** (`nebula.py:10387`)
  Current:  
  > value
  New:

## Group library by
*Internal component: `GroupByDialog`*

- **C329 · window title · `GroupByDialog.__init__`** (`nebula.py:10552`)
  Current:  
  > Group library by
  New:
- **C330 · label · `GroupByDialog.__init__`** (`nebula.py:10560`)
  Current:  
  > Group the collection by up to three levels.
  > Songs are listed under the last level.
  New:
- **C331 · label · `GroupByDialog.__init__`** (`nebula.py:10580`)
  Current:  
  > Saved groupings
  New:

## Find duplicates
*Internal component: `DuplicateDialog`*

- **C332 · window title · `DuplicateDialog.__init__`** (`nebula.py:10659`)
  Current:  
  > Find duplicates
  New:
- **C333 · label · `DuplicateDialog.__init__`** (`nebula.py:10664`)
  Current:  
  > Tracks matching on all three fields are listed together.
  New:
- **C334 · label · `DuplicateDialog.__init__`** (`nebula.py:10670`)
  Current:  
  > Match
  New:
- **C335 · button · `DuplicateDialog.__init__`** (`nebula.py:10699`)
  Current:  
  > Select all but the first
  New:
- **C336 · button · `DuplicateDialog.__init__`** (`nebula.py:10701`)
  Current:  
  > Remove selected from library
  New:
- **C337 · text · `DuplicateDialog.find`** (`nebula.py:10733`)
  Current:  
  > {len(groups)} duplicate group(s), {total} track(s)
  New:

## Organize files
*Internal component: `OrganizeDialog`*

- **C338 · window title · `OrganizeDialog.__init__`** (`nebula.py:10769`)
  Current:  
  > Organize files
  New:
- **C339 · label · `OrganizeDialog.__init__`** (`nebula.py:10774`)
  Current:  
  > {len(self.paths)} file(s). Placeholders: %artist% %albumartist% %album% %tracknumber% %discnumber% %date% %genre% %title% %composer%
  New:
- **C340 · button · `OrganizeDialog.__init__`** (`nebula.py:10787`)
  Current:  
  > Browse…
  New:
- **C341 · checkbox · `OrganizeDialog.__init__`** (`nebula.py:10794`)
  Current:  
  > Move files (otherwise copy them)
  New:
- **C342 · warning · `OrganizeDialog.accept`** (`nebula.py:10836`)
  Current:  
  > Pick an existing destination folder.
  New:

## Cover actions
*Internal component: `CoverMenu`*

- **C343 · menu · `CoverMenu.menu`** (`nebula.py:12135`)
  Current:  
  > Set cover type
  New:
- **C344 · warning · `CoverMenu.add`** (`nebula.py:12189`)
  Current:  
  > That file is not a readable image.
  New:
- **C345 · warning · `CoverMenu.replace`** (`nebula.py:12203`)
  Current:  
  > That file is not a readable image.
  New:
- **C346 · warning · `CoverMenu.adjust`** (`nebula.py:12238`)
  Current:  
  > The picture could not be written.
  New:

## Cover manager
*Internal component: `CoverManagerDialog`*

- **C347 · window title · `CoverManagerDialog.__init__`** (`nebula.py:11999`)
  Current:  
  > Manage covers
  New:

## Cover viewer
*Internal component: `CoverViewer`*

- **C348 · window title · `CoverViewer.__init__`** (`nebula.py:8536`)
  Current:  
  > Cover
  New:

## Copy to device
*Internal component: `CopyToDeviceDialog`*

- **C349 · window title · `CopyToDeviceDialog.__init__`** (`nebula.py:16555`)
  Current:  
  > Copy to device
  New:
- **C350 · placeholder · `CopyToDeviceDialog.__init__`** (`nebula.py:16583`)
  Current:  
  > (the whole device)
  New:
- **C351 · button · `CopyToDeviceDialog.__init__`** (`nebula.py:16585`)
  Current:  
  > Select folder…
  New:
- **C352 · checkbox · `CopyToDeviceDialog.__init__`** (`nebula.py:16591`)
  Current:  
  > Force transcode
  New:
- **C353 · message · `CopyToDeviceDialog._browse`** (`nebula.py:16700`)
  Current:  
  > {busy} Wait for it to finish before choosing a folder.
  New:
- **C354 · message · `CopyToDeviceDialog._browse`** (`nebula.py:16705`)
  Current:  
  > {device.name} is not mounted. Reconnect it and try again.
  New:

## Device folder
*Internal component: `DeviceFolderDialog`*

- **C355 · window title · `DeviceFolderDialog.__init__`** (`nebula.py:16486`)
  Current:  
  > Select device folder
  New:
- **C356 · label · `DeviceFolderDialog.__init__`** (`nebula.py:16504`)
  Current:  
  > Double-click a folder to go into it. The folder shown above is the one this device will browse.
  New:

## Edit tags
*Internal component: `EditTagsDialog`*

- **C357 · window title · `EditTagsDialog.__init__`** (`nebula.py:11753`)
  Current:  
  > Edit track information
  New:
- **C358 · text · `EditTagsDialog._switch`** (`nebula.py:11818`)
  Current:  
  > Track {row + 1} of {len(self.paths)}: {os.path.basename(path)}
  New:

## Adjust cover
*Internal component: `AdjustCoverDialog`*

- **C359 · window title · `AdjustCoverDialog.__init__`** (`nebula.py:11871`)
  Current:  
  > Adjust cover
  New:
- **C360 · label · `AdjustCoverDialog.__init__`** (`nebula.py:11884`)
  Current:  
  > Format
  New:
- **C361 · label · `AdjustCoverDialog.__init__`** (`nebula.py:11885`)
  Current:  
  > Quality
  New:
- **C362 · checkbox · `AdjustCoverDialog.__init__`** (`nebula.py:11902`)
  Current:  
  > Size
  New:

---

## Notes on what is not in this deck

- Standard dialog buttons (`OK`, `Cancel`, `Apply`, `Close`, `Yes`, `No`) and the keyboard-shortcut help body are not repeated here.
- Most menu commands are not repeated; they are labels rather than descriptions.
- Error strings shorter than four words and internal status strings shorter than five words were left out.
- The full README feature descriptions are separate prose, not in-app text, and are not part of this deck.
