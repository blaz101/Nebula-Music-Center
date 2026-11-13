# Copyright (C) 2026 Roger Barthares
# SPDX-License-Identifier: GPL-3.0-only
"""Deep verification for nebula.py.

Run:  QT_QPA_PLATFORM=offscreen python3 tests/deep_check.py

Every run builds a throw-away home and points NEBULA_DATA/NEBULA_CACHE into it, so a
real library, config or device list on this machine can never be touched. The suite
covers the places a regression has actually hurt before: settings surviving a save and
a restart, the config backup, remembered devices and shared presets, the two grids, the
Audiobooks tab, playlists,
smart playlists, multi-folder and selected-item sync, and session restore. Exit code 0
means every check passed.
"""
import atexit
import ast
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave

HOME = tempfile.mkdtemp(prefix="nebula-deep-")
os.environ["HOME"] = HOME
DATA = os.path.join(HOME, "Nebula")
CACHE = os.path.join(HOME, ".cache", "Nebula")
os.environ["NEBULA_DATA"] = DATA
os.environ["NEBULA_CACHE"] = CACHE
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
atexit.register(shutil.rmtree, HOME, True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
sys.path.insert(0, ROOT)
sys.path.insert(0, ASSETS)

from mutagen.id3 import ID3, TALB, TCON, TDRC, TIT2, TPE1, TRCK  # noqa: E402
from mutagen.wave import WAVE  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import (QApplication, QFileDialog, QInputDialog,  # noqa: E402
                               QMessageBox, QPushButton)

import nebula  # noqa: E402

RESULTS = []
SECTION = [""]


def section(name):
    SECTION[0] = name
    print(f"\n== {name}")


def check(name, condition, detail=""):
    ok = bool(condition)
    RESULTS.append((SECTION[0], name, ok, detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + ("" if ok else f"   <- {detail}"))
    return ok


def ffmpeg(*args):
    return subprocess.run(["ffmpeg", "-y", "-v", "error", *args], capture_output=True,
                          text=True)


def write_wav(path, title, artist, album, track, seconds=1.0, year="1992"):
    with wave.open(path, "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(44100)
        n = int(44100 * seconds)
        f.writeframes(b"".join(struct.pack("<hh", int(900 * ((i // 40) % 3)), 0)
                               for i in range(n)))
    audio = WAVE(path)
    if audio.tags is None:
        audio.add_tags()
    audio.tags.add(TIT2(encoding=3, text=title))
    audio.tags.add(TPE1(encoding=3, text=artist))
    audio.tags.add(TALB(encoding=3, text=album))
    audio.tags.add(TRCK(encoding=3, text=str(track)))
    audio.tags.add(TDRC(encoding=3, text=year))
    audio.tags.add(TCON(encoding=3, text="Electronic"))
    audio.save()


def all_items(tree):
    out = []
    stack = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
    while stack:
        item = stack.pop()
        out.append(item)
        stack.extend(item.child(i) for i in range(item.childCount()))
    return out


# ---------------------------------------------------------------- fixtures
MUSIC = os.path.join(HOME, "Music")
ALBUM_A = os.path.join(MUSIC, "Aphex Twin", "Selected Ambient Works")
ALBUM_B = os.path.join(MUSIC, "Boards of Canada", "Music Has the Right")
os.makedirs(ALBUM_A)
os.makedirs(ALBUM_B)
WAV1 = os.path.join(ALBUM_A, "01 - Alpha.wav")
WAV2 = os.path.join(ALBUM_A, "02 - Beta.wav")
FLAC1 = os.path.join(ALBUM_B, "01 - Gamma.flac")
MP3A = os.path.join(ALBUM_B, "01 - Delta.mp3")
write_wav(WAV1, "Alpha", "Aphex Twin", "Selected Ambient Works", 1)
write_wav(WAV2, "Beta", "Aphex Twin", "Selected Ambient Works", 2)
ffmpeg("-i", WAV1, "-c:a", "flac", "-metadata", "title=Gamma", "-metadata",
       "artist=Boards of Canada", "-metadata", "album=Music Has the Right", "-metadata",
       "tracknumber=1", "-metadata", "date=1998", FLAC1)
ffmpeg("-i", WAV2, "-c:a", "libmp3lame", "-b:a", "128k", "-metadata", "title=Delta",
       "-metadata", "artist=MP3 Artist", "-metadata", "album=Compilation", "-metadata",
       "tracknumber=1", MP3A)

AB = os.path.join(HOME, "Audiobooks")
AB_BOOK = os.path.join(AB, "Dune")
os.makedirs(AB_BOOK)
chapters = "".join(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={i * 3000}\nEND={(i + 1) * 3000}\n"
                   f"title=Chapter {i + 1}\n" for i in range(4))
meta = os.path.join(HOME, "chapters.txt")
with open(meta, "w", encoding="utf-8") as f:
    f.write(";FFMETADATA1\n" + chapters)
ffmpeg("-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "12", "-c:a", "aac",
       os.path.join(HOME, "silence.m4a"))
AB_CH1 = os.path.join(AB_BOOK, "Chapter 01.m4b")
AB_CH2 = os.path.join(AB_BOOK, "Chapter 02.m4b")
for path, title in ((AB_CH1, "Chapter 01"), (AB_CH2, "Chapter 02")):
    ffmpeg("-i", os.path.join(HOME, "silence.m4a"), "-i", meta, "-map_metadata", "1",
           "-c", "copy", "-metadata", f"title={title}", "-metadata",
           "artist=Frank Herbert", "-metadata", "album=Dune", path)
AB_LOOSE = os.path.join(AB, "The Hobbit.m4b")
ffmpeg("-i", os.path.join(HOME, "silence.m4a"), "-c", "copy", "-metadata",
       "title=The Hobbit", "-metadata", "artist=J. R. R. Tolkien", AB_LOOSE)

app = QApplication([])
nebula.install_app_style(app)
nebula.detect_devices = lambda: []
nebula.cd_drive_states = lambda: {}


def fresh_config(**values):
    cfg = json.loads(json.dumps(nebula.DEFAULT_CONFIG))
    cfg.update(values)
    return cfg


# ---------------------------------------------------------------- isolation
section("isolation and version")
check("the suite writes only inside its throw-away home",
      nebula.CONFIG_FILE.startswith(HOME + os.sep) and nebula.DB_FILE.startswith(HOME + os.sep),
      (nebula.CONFIG_FILE, nebula.DB_FILE))
check("the real settings file was not opened",
      not nebula.CONFIG_FILE.startswith("/home/rba/Nebula"), nebula.CONFIG_FILE)
check("file dialogs use the system's native chooser",
      not (nebula.FILE_DIALOG_OPTIONS & QFileDialog.Option.DontUseNativeDialog)
      and nebula.DIRECTORY_DIALOG_OPTIONS == QFileDialog.Option.ShowDirsOnly,
      (nebula.FILE_DIALOG_OPTIONS, nebula.DIRECTORY_DIALOG_OPTIONS))
dialog_source = open(os.path.join(ROOT, "nebula.py"), encoding="utf-8").read()
dialog_calls = [
    node for node in ast.walk(ast.parse(dialog_source))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    and isinstance(node.func.value, ast.Name) and node.func.value.id == "QFileDialog"
    and node.func.attr.startswith("get")]
check("every file dialog call passes the native chooser options",
      len(dialog_calls) == 20 and all(
          any(keyword.arg == "options" and isinstance(keyword.value, ast.Name)
              and keyword.value.id in {"FILE_DIALOG_OPTIONS", "DIRECTORY_DIALOG_OPTIONS"}
              for keyword in call.keywords)
          for call in dialog_calls),
      [(call.func.attr, [keyword.arg for keyword in call.keywords]) for call in dialog_calls])
launcher = open(os.path.join(ROOT, "run.sh"), encoding="utf-8").read()
check("the launcher passes the desktop GTK theme to the native chooser",
      "GTK_THEME" in launcher
      and "org.gnome.desktop.interface gtk-theme" in launcher
      and "color-scheme" in launcher, launcher[:1200])
launcher_assignments = [line.strip() for line in launcher.splitlines()
                        if line.strip().startswith(("XDG_CONFIG_HOME=", "XDG_DATA_HOME="))]
check("the launcher leaves the desktop config and data homes alone",
      not launcher_assignments, launcher_assignments)
check("version is 1.27.1", nebula.VERSION == "1.27.1", nebula.VERSION)
readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
check("README title matches the version",
      readme.startswith("# Nebula Music Center 1.27.1\n"), readme[:40])
check("README has a 1.27.1 section", "## What's new in 1.27.1" in readme)
build = open(os.path.join(ROOT, "packaging", "build-deb.sh"), encoding="utf-8").read()
check("the package script builds 1.27.1", "\nV=1.27.1\n" in build, build[:200])

# ---------------------------------------------------------------- config
section("config: defaults, types, backup and recovery")
cfg = nebula.load_config()
check("every default key is present",
      all(k in cfg for k in nebula.DEFAULT_CONFIG), sorted(set(nebula.DEFAULT_CONFIG) - set(cfg)))
check("defaults keep the current UI revision", cfg["ui_revision"] == 42, cfg["ui_revision"])

cfg["library_folders"] = [MUSIC]
cfg["audiobook_folders"] = [AB]
cfg["volume"] = 11
cfg["tab"] = 2
cfg["window"] = [1111, 777]
cfg["device_registry"] = [{"id": "mass:/stick", "name": "Stick", "kind": "mass",
                           "root": "/stick", "uri": ""}]
cfg["device_names"] = {"mass:/stick": "My Stick"}
cfg["collections"] = [{"name": "Music", "folders": [MUSIC], "db": nebula.DB_FILE}]
cfg["active_collection"] = 0
nebula.save_config(cfg)
loaded = nebula.load_config()
check("library folders survive a save and load", loaded["library_folders"] == [MUSIC],
      loaded["library_folders"])
check("collections keep their folder list",
      loaded["collections"][0]["folders"] == [MUSIC], loaded["collections"])
check("remembered devices survive a save and load",
      loaded["device_registry"][0]["id"] == "mass:/stick", loaded["device_registry"])
check("device nicknames survive", loaded["device_names"] == {"mass:/stick": "My Stick"})
check("the audiobook folder list survives", loaded["audiobook_folders"] == [AB])
check("window, tab and volume survive",
      (loaded["window"], loaded["tab"], loaded["volume"]) == ([1111, 777], 2, 11),
      (loaded["window"], loaded["tab"], loaded["volume"]))

# a second save keeps the file it replaced
loaded["volume"] = 22
nebula.save_config(loaded)
backup = json.load(open(nebula.CONFIG_FILE + ".bak", encoding="utf-8"))
check("a save keeps the previous config as config.json.bak", backup["volume"] == 11,
      backup.get("volume"))
check("the backup holds the folders too", backup["library_folders"] == [MUSIC],
      backup.get("library_folders"))

# a truncated write is recovered from the backup instead of starting over
with open(nebula.CONFIG_FILE, "w", encoding="utf-8") as f:
    f.write('{"library_folders": [')
recovered = nebula.load_config()
check("a truncated config is read from the backup",
      recovered["library_folders"] == [MUSIC] and recovered["volume"] == 11,
      (recovered.get("library_folders"), recovered.get("volume")))
check("the recovery brings the devices back too",
      recovered["device_registry"][0]["id"] == "mass:/stick", recovered.get("device_registry"))

# an unreadable config with no backup keeps working with defaults
os.remove(nebula.CONFIG_FILE)
os.remove(nebula.CONFIG_FILE + ".bak")
check("no config at all still starts with defaults",
      nebula.load_config()["library_folders"] == [])
check("saving with no previous file does not fail",
      (nebula.save_config(fresh_config()), os.path.exists(nebula.CONFIG_FILE))[1])

# wrong types are repaired rather than crashing a tab
with open(nebula.CONFIG_FILE, "w", encoding="utf-8") as f:
    json.dump({"library_folders": "Music", "volume": "loud", "window": 12,
               "collections": "nope", "custom_key": {"kept": True}}, f)
repaired = nebula.load_config()
check("a string in place of the folder list is repaired",
      repaired["library_folders"] == [], repaired["library_folders"])
check("a bad number becomes the default", repaired["volume"] == 70, repaired["volume"])
check("an unknown key is left alone", repaired["custom_key"] == {"kept": True})
check("the repaired config has a usable collection",
      repaired["collections"][0]["name"] == "Music", repaired["collections"])

# the 1.07 tab-index migration must not run again, but must still work on old configs
with open(nebula.CONFIG_FILE, "w", encoding="utf-8") as f:
    json.dump({"ui_revision": 0, "tab": 2}, f)
migrated = nebula.load_config()
check("a pre-1.07 tab index moves past the new Audiobooks tab",
      migrated["tab"] == 3 and migrated["ui_revision"] == 42,
      (migrated["tab"], migrated["ui_revision"]))

section("collections")
cols = nebula.migrate_collections(fresh_config())
check("one default collection is created", len(cols) == 1 and cols[0]["name"] == "Music", cols)
cfg = fresh_config()
cfg["collections"] = [{"name": "Music", "folders": [], "db": "a.db"},
                      {"name": "Music", "folders": [], "db": "b.db"},
                      {"name": "", "folders": [], "db": "c.db"},
                      "junk"]
cols = nebula.migrate_collections(cfg)
check("duplicate collection names are made unique",
      [c["name"] for c in cols] == ["Music", "Music 2"], [c["name"] for c in cols])
check("a nameless collection is dropped", len(cols) == 2, cols)
cfg["active_collection"] = 99
check("an out-of-range collection index is clamped",
      nebula.migrate_collections(cfg) and cfg["active_collection"] == 1,
      cfg["active_collection"])
cfg["library_folders"] = [MUSIC]
nebula.store_active_collection(cfg)
check("the active collection's folder list follows the live one",
      cfg["collections"][1]["folders"] == [MUSIC], cfg["collections"])
check("a new collection database lives under library/collections",
      nebula.new_collection_db("Deep Test").startswith(
          os.path.join(nebula.LIBRARY_DIR, "collections") + os.sep))

# ---------------------------------------------------------------- library
section("tags, scanning and the library database")
tags = nebula.read_tags(WAV1)
check("WAV tags are read", tags["title"] == "Alpha" and tags["artist"] == "Aphex Twin",
      tags)
specs = nebula.read_specs(WAV1)
check("WAV specs are read",
      (specs["bits_per_sample"], specs["sample_rate"], specs["channels"]) == (16, 44100, 2),
      specs)
check("FLAC tags are read", nebula.read_tags(FLAC1)["artist"] == "Boards of Canada",
      nebula.read_tags(FLAC1))
check("MP3 tags are read", nebula.read_tags(MP3A)["title"] == "Delta")

section("tag writes: every field and format")
tag_values = {
    "title": "Matrix Title", "artist": "Matrix Artist", "album": "Matrix Album",
    "albumartist": "Matrix Album Artist", "tracknumber": "3/12",
    "discnumber": "1/2", "date": "2024", "genre": "Rock",
    "composer": "Matrix Composer", "comment": "Matrix Comment",
}
tag_sources = {
    "FLAC": (FLAC1, ".flac"),
    "M4A": (AB_CH1, ".m4a"),
    "MP3": (MP3A, ".mp3"),
    "WAV": (WAV1, ".wav"),
}
for label, (source, ext) in tag_sources.items():
    target = os.path.join(HOME, "matrix-" + label.lower() + ext)
    shutil.copyfile(source, target)
    skipped = nebula.write_tags(target, dict(tag_values))
    core = nebula.read_tags(target)
    extra = nebula.read_extra_tags(target)
    missing = [key for key, value in tag_values.items()
               if (extra.get(key, "") if key == "comment" else core.get(key, "")) != value]
    check(f"{label}: every tag writes and reads back", not skipped and not missing,
          (skipped, missing, core, extra))
    skipped = nebula.write_tags(target, {key: "" for key in tag_values})
    core = nebula.read_tags(target)
    extra = nebula.read_extra_tags(target)
    still = [key for key in tag_values
             if (extra.get(key, "") if key == "comment" else core.get(key, ""))]
    check(f"{label}: every tag clears again", not skipped and not still,
          (skipped, still, core, extra))

db_file = os.path.join(HOME, "library.db")
library = nebula.Library(db_file)
library.scan([MUSIC])
check("the scan indexes every track", library.count() == 4, library.count())
rows = library.tracks(order_by="title")
check("tracks come back ordered", [r["title"] for r in rows][:2] == ["Alpha", "Beta"],
      [r["title"] for r in rows])
check("the library knows a path", FLAC1 in library.by_path())
library.scan([MUSIC])
check("a rescan keeps the same track count", library.count() == 4, library.count())
gone = library.forget_prefix(ALBUM_A)
library.rescan = None
check("forgetting a folder drops only its tracks",
      gone == 2 and library.count() == 2, (gone, library.count()))
library.scan([MUSIC])
check("a rescan brings a forgotten folder back", library.count() == 4, library.count())

section("playlists and smart playlists")
playlists = nebula.PlaylistStore(lambda: [MUSIC])
playlists.write("Mix", [WAV1, FLAC1])
raw = open(playlists.path("Mix"), encoding="utf-8").read().splitlines()
check("a playlist starts with #EXTM3U", raw[0] == "#EXTM3U", raw[:2])
check("a playlist stores portable paths",
      raw[1] == os.path.join("Aphex Twin", "Selected Ambient Works", "01 - Alpha.wav"),
      raw[1:])
check("a playlist reads back to absolute paths", playlists.read("Mix") == [WAV1, FLAC1],
      playlists.read("Mix"))
external = os.path.join(HOME, "external.m3u8")
with open(external, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n" + MP3A + "\n")
imported = playlists.import_file(external)
check("an external .m3u8 is imported", imported and playlists.read(imported) == [MP3A],
      imported)
check("a playlist can be renamed", playlists.rename(imported, "Imported")
      and playlists.read("Imported") == [MP3A])
playlists.remove("Imported")
check("a playlist can be deleted", "Imported" not in playlists.names())

store = nebula.SmartStore(library)
never = next(p for p in nebula.SMART_PRESETS if p["name"] == "Never Played")
check("a smart playlist runs against the real library",
      len(store.preset_tracks(library, never)) == 4,
      len(store.preset_tracks(library, never)))
where, params = nebula.build_smart_where(
    [{"field": "artist", "op": "contains", "value": "Aphex"}])
check("the rule builder returns parameterised SQL", "?" in where and params == ["%Aphex%"],
      (where, params))
check("the rule builder query runs",
      [r["title"] for r in library.tracks(where=where, args=params)] == ["Alpha", "Beta"],
      library.tracks(where=where, args=params))
where, params = nebula.parse_filter("artist:Aphex")
check("the filter language parses a field",
      where and [r["title"] for r in library.tracks(where=where, args=params)][:2]
      == ["Alpha", "Beta"], (where, params))

# ---------------------------------------------------------------- main window
section("main window, menus and the two regressions")
boot = fresh_config()
boot["library_folders"] = [MUSIC]
boot["audiobook_folders"] = [AB]
boot["collections"] = [{"name": "Music", "folders": [MUSIC], "db": nebula.DB_FILE}]
boot["device_registry"] = [{"id": "mass:/stick", "name": "Stick", "kind": "mass",
                            "root": "/stick", "uri": ""}]
boot["device_names"] = {"mass:/stick": "My Stick"}
nebula.save_config(boot)

w = nebula.MainWindow()
w.show()
app.processEvents()
titles = [w.tabs.tabText(i) for i in range(w.tabs.count())]
check("the tabs are Music, Audiobooks, Tags, Devices, Syncing",
      titles == ["Music", "Audiobooks", "Tags", "Devices", "Syncing"], titles)
w.library_tab.refresh()
w.audiobooks_tab.refresh()
app.processEvents()


def menu_titles():
    return [a.text().replace("&", "") for a in w.menuBar().actions()]


check("the Music tab shows the player menus",
      menu_titles() == ["Music", "Playlist", "Tools", "Help"], menu_titles())
w.tabs.setCurrentWidget(w.audiobooks_tab)
app.processEvents()
check("the Audiobooks tab has its own menu set",
      menu_titles() == ["Audiobooks", "Playlist", "Tools", "Help"], menu_titles())
ab_menu = next(a.menu() for a in w.menuBar().actions() if a.text() == "&Audiobooks")
ab_actions = [a.text() for a in ab_menu.actions() if a.text()]
check("its menu has Select, Remove and Refresh",
      ab_actions == ["Select folder…", "Remove folder…", "Refresh"], ab_actions)
w.tabs.setCurrentWidget(w.tagger_tab)
app.processEvents()
check("the Tags tab still swaps to mp3tag's menus",
      menu_titles()[:3] == ["File", "Edit", "View"], menu_titles())
w.tabs.setCurrentWidget(w.library_tab)
app.processEvents()

check("the config still has the library folder after start-up",
      w.config["library_folders"] == [MUSIC], w.config["library_folders"])
check("the window lists the remembered device without it being plugged in",
      any(r["name"] == "My Stick" and not r["connected"]
          for r in w.devices_tab._device_rows()),
      w.devices_tab._device_rows())

# the 1.09 regression: the folder question must only appear when there are no folders
asked = []
real_question = QMessageBox.question
QMessageBox.question = staticmethod(
    lambda *a, **k: asked.append(a[2] if len(a) > 2 else "") or QMessageBox.No)
nebula.save_config(w.config)
w2 = nebula.MainWindow()
QTest.qWait(650)
check("an existing library folder is not asked about again", not asked, asked)
w2.close()
QMessageBox.question = real_question

# and the opposite: a genuinely empty config does ask once
empty = fresh_config()
empty["collections"] = [{"name": "Music", "folders": [], "db": nebula.DB_FILE}]
nebula.save_config(empty)
asked.clear()
QMessageBox.question = staticmethod(
    lambda *a, **k: asked.append(a[2] if len(a) > 2 else "") or QMessageBox.No)
w3 = nebula.MainWindow()
QTest.qWait(650)
check("an empty library asks for a folder", len(asked) == 1, asked)
w3.close()
QMessageBox.question = real_question
nebula.save_config(w.config)

prefs = nebula.PreferencesDialog(w.library_tab, w)
check("Preferences has an Audiobooks page",
      [prefs.sidebar.item(i).text() for i in range(prefs.sidebar.count())]
      == ["Theme", "Library", "Audiobooks", "Devices", "Playback", "Syncing",
          "Backup", "Audio CD", "Identification"],
      [prefs.sidebar.item(i).text() for i in range(prefs.sidebar.count())])
check("Preferences no longer has .aax import settings",
      not any(key in prefs.widgets for key in
              ("audiobook_import_mode", "audiobook_import_artist_album",
               "audiobook_import_keep_cover")))
check("target folders move out of Preferences into each sync profile",
      not any(key in prefs.widgets for key in
              ("device_music_folder", "device_audiobook_folder", "device_podcast_folder"))
      and w.sync_tab.target_button.text() == "Choose Target Folders"
      and not hasattr(w.sync_tab, "target")
      and not hasattr(w.sync_tab, "music_folder"))
check("Preferences has settings export and import",
      prefs.backup_export.text() == "Export settings…"
      and prefs.backup_import.text() == "Import settings…"
      and len(prefs.backup_checks) == 4
      and all(box.isChecked() for box in prefs.backup_checks.values()))
prefs.close()

# ---------------------------------------------------------------- grids
section("grids: movable columns, remembered order and widths")
ab_tab = w.audiobooks_tab
check("the Audiobooks grid is full width, with no folder panel",
      not hasattr(ab_tab, "folder_list") and not hasattr(ab_tab, "remove_btn"))
check("the Audiobooks header has no folder picker",
      not hasattr(ab_tab, "target_combo"))
check("the Import button uses the ordinary button style",
      ab_tab.import_btn.objectName() != "Primary", ab_tab.import_btn.objectName())
check("the Audiobooks grid has Cover, Title, Author, Chapters, Length",
      [ab_tab.tree.headerItem().text(i) for i in range(ab_tab.tree.columnCount())]
      == ["", "Title", "Author", "Chapters", "Length"])
check("the Audiobooks grid has a search box",
      ab_tab.search.placeholderText().startswith("Search")
      and ab_tab.search.isClearButtonEnabled(), ab_tab.search.placeholderText())
check("its columns can be dragged",
      ab_tab.tree.header().sectionsMovable())
w.config["grid_layouts"] = {}
ab_tab.tree.header().moveSection(0, 2)
ab_tab.tree._grid_store()
order = w.config["grid_layouts"]["audiobooks"]["order"]
check("a reordered column order is written to the config", order == [1, 2, 0, 3, 4], order)
ab_tab.tree.setColumnWidth(1, 321)
ab_tab.tree._grid_store()
widths = w.config["grid_layouts"]["audiobooks"]["widths"]
check("column widths are written too", widths[1] == 321, widths)
saved_layout = json.loads(json.dumps(w.config["grid_layouts"]["audiobooks"]))
ab2 = nebula.AudiobooksTab(w.player, dict(w.config, audiobook_folders=[AB]))
check("a fresh Audiobooks tab restores the order",
      [ab2.tree.header().logicalIndex(v) for v in range(5)] == saved_layout["order"],
      [ab2.tree.header().logicalIndex(v) for v in range(5)])
check("a fresh Audiobooks tab restores the width", ab2.tree.columnWidth(1) == 321,
      ab2.tree.columnWidth(1))
legacy = fresh_config(audiobook_folders=[AB], grid_layouts={
    "audiobooks": {"order": [1, 2, 0, 3], "widths": [300, 200, 80, 70]}})
legacy_tab = nebula.AudiobooksTab(w.player, legacy)
check("a 1.16 audiobook layout gains the cover column in front",
      [legacy_tab.tree.header().logicalIndex(v) for v in range(5)] == [0, 2, 3, 1, 4],
      [legacy_tab.tree.header().logicalIndex(v) for v in range(5)])
legacy_tab.close()

w.config["lib_details"] = True
w.library_tab._apply_columns()
check("the Music grid's columns can be dragged too",
      w.library_tab.tree.header().sectionsMovable())
header = w.library_tab.tree.header()
header.moveSection(0, 1)
w.library_tab.tree._grid_store()
lib_order = w.config["grid_layouts"]["library"]["order"]
check("the Music grid remembers its own order", lib_order == [1, 0] + list(range(2, len(lib_order))),
      lib_order)
check("the remembered order is applied when the grid is rebuilt",
      w.library_tab.tree.header().logicalIndex(0) == 1,
      [header.logicalIndex(v) for v in range(header.count())])
w.config["lib_details"] = False

# ---------------------------------------------------------------- audiobooks
section("audiobooks: titles, chapters and import")
ab_cfg = fresh_config(audiobook_folders=[AB])
ab = nebula.AudiobooksTab(w.player, ab_cfg)
names = [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())]
check("the Audiobooks header has no .aax import button", not hasattr(ab, "aax_btn"))
check("the .aax settings are gone",
      not any(key in fresh_config() for key in
              ("audiobook_import_mode", "audiobook_import_artist_album",
               "audiobook_import_keep_cover", "audible_activation_bytes",
               "rcrack_path", "rainbow_tables_dir")))
check("a subfolder is one title and a loose file is a title of its own",
      sorted(names) == ["Dune", "The Hobbit"], names)

# Opening the tab must not re-read every chapter's tags when nothing changed.
real_details = nebula.audiobook_details
detail_calls = []

def spy_details(paths, cache=None):
    detail_calls.append(list(paths))
    return real_details(paths, cache)

nebula.audiobook_details = spy_details
try:
    ab.refresh()
finally:
    nebula.audiobook_details = real_details
check("reopening an unchanged Audiobooks tab skips its tag and chapter scan",
      detail_calls == [], detail_calls)

ab._sort_by(3)
check("clicking Chapters sorts the titles by chapter count",
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())]
      == ["The Hobbit", "Dune"],
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())])
ab._sort_by(3)
check("clicking the same heading again reverses the sort",
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())]
      == ["Dune", "The Hobbit"],
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())])
check("the heading shows which way it is sorted",
      ab.tree.header().sortIndicatorSection() == 3
      and ab.tree.header().sortIndicatorOrder() == Qt.DescendingOrder,
      (ab.tree.header().sortIndicatorSection(), ab.tree.header().sortIndicatorOrder()))
ab._sort_by(1)
check("sorting by Title puts the titles back in order",
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())]
      == ["Dune", "The Hobbit"],
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())])
dune = next(ab.tree.topLevelItem(i) for i in range(ab.tree.topLevelItemCount())
            if ab.tree.topLevelItem(i).text(1) == "Dune")
check("the title shows its chapter count", dune.text(3) == "2", dune.text(3))
check("the author is shown in its own column",
      dune.text(2) == "Frank Herbert", dune.text(2))
ab._sort_by(2)
check("clicking Author sorts by author",
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())]
      == ["Dune", "The Hobbit"],
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())])
ab._sort_by(1)
dune = next(ab.tree.topLevelItem(i) for i in range(ab.tree.topLevelItemCount())
            if ab.tree.topLevelItem(i).text(1) == "Dune")
check("a real .m4b chapter list is counted",
      nebula.m4b_chapter_count(AB_CH1) == 4, nebula.m4b_chapter_count(AB_CH1))
check("chapters are listed under the title", dune.childCount() == 2, dune.childCount())
check("the first chapter has a length", dune.child(0).text(4) not in ("", "0:00"),
      dune.child(0).text(4))
cover_file = os.path.join(AB_BOOK, "cover.png")
shutil.copyfile(os.path.join(ROOT, "nebula.png"), cover_file)
ab.refresh(force=True)
dune = next(ab.tree.topLevelItem(i) for i in range(ab.tree.topLevelItemCount())
            if ab.tree.topLevelItem(i).text(1) == "Dune")
check("the cover column shows a book's cover", not dune.icon(0).isNull())
ab.search.setText("hob")
check("the search box finds a title",
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())]
      == ["The Hobbit"],
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())])
ab.search.setText("frank")
check("the search box finds an author",
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())]
      == ["Dune"],
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())])
ab.search.clear()
check("the search box restores every title",
      ab.tree.topLevelItemCount() == 2, ab.tree.topLevelItemCount())
dune = next(ab.tree.topLevelItem(i) for i in range(ab.tree.topLevelItemCount())
            if ab.tree.topLevelItem(i).text(1) == "Dune")
check("the audiobook grid has a right-click menu",
      ab.tree.contextMenuPolicy() == Qt.CustomContextMenu)
book_paths = ab._book_paths[dune.data(0, Qt.UserRole)]
queued = []
real_add = ab.player.add_paths
ab.player.add_paths = lambda paths, **kwargs: queued.append((list(paths), kwargs))
ab._queue_item(dune)
check("right-clicking a title adds the whole book to the queue",
      queued and queued[-1][0] == book_paths
      and queued[-1][1].get("play_if_idle") is False, queued)
ab._queue_item(dune.child(0))
check("right-clicking a chapter adds that chapter to the queue",
      queued[-1][0] == [book_paths[0]], queued[-1])
ab.player.add_paths = real_add
check("the default import folder is ~/Music/Nebula - Audiobooks",
      nebula.audiobook_default_folder() ==
      os.path.join(HOME, "Music", "Nebula - Audiobooks"),
      nebula.audiobook_default_folder())
default_tab = nebula.AudiobooksTab(w.player, fresh_config())
check("with no folder configured the destination is the default folder",
      default_tab._target_folder() == nebula.audiobook_default_folder(),
      default_tab._target_folder())
check("with a folder configured its first folder is the destination",
      ab._target_folder() == AB, ab._target_folder())
check("the import progress bar is hidden when no import is running",
      ab.import_progress.isHidden(), ab.import_progress.isVisible())
check("an existing name gets a (2) suffix", nebula.unique_path(WAV1).endswith(" (2).wav"),
      nebula.unique_path(WAV1))
import_root = os.path.join(HOME, "import-src")
incoming = os.path.join(HOME, "import-dst")
os.makedirs(import_root)
os.makedirs(incoming)
to_import = os.path.join(import_root, "Incoming Book.m4b")
shutil.copyfile(AB_CH1, to_import)
ab_cfg["audiobook_import_target"] = incoming
ab_cfg["audiobook_folders"] = []
ab = nebula.AudiobooksTab(w.player, ab_cfg)
real_import_audio, real_import_folder = (
    ab.import_audio, ab.import_folder)
seen_imports = []
ab.import_audio = lambda background=True: seen_imports.append(("audio", background))
ab.import_folder = lambda background=True: seen_imports.append(("folder", background))
ab.import_btn.click()
ab.folder_btn.click()
ab.import_audio, ab.import_folder = (
    real_import_audio, real_import_folder)
check("every import button starts its work in the background",
      seen_imports == [("audio", True), ("folder", True)],
      seen_imports)
real_open = QFileDialog.getOpenFileNames
QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([to_import], ""))
ab.import_audio(background=False)
check("Import moves the file into the chosen folder",
      os.path.exists(os.path.join(incoming, "Incoming Book.m4b"))
      and not os.path.exists(to_import))
check("the import folder is added to the audiobook folders",
      incoming in ab_cfg["audiobook_folders"], ab_cfg["audiobook_folders"])
imported_path = os.path.join(incoming, "Incoming Book.m4b")
check("the imported file is in the grid",
      any(imported_path in paths for paths in ab._book_paths.values()),
      (imported_path, list(ab._book_paths.values())))
second = os.path.join(import_root, "Incoming Book.m4b")
shutil.copyfile(AB_CH2, second)
QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([second], ""))
ab.import_audio(background=False)
check("a second file of the same name does not overwrite the first",
      os.path.exists(os.path.join(incoming, "Incoming Book (2).m4b")),
      sorted(os.listdir(incoming)))
QFileDialog.getOpenFileNames = real_open

folder_book = os.path.join(HOME, "folder-source", "Folder Book")
os.makedirs(folder_book)
shutil.copyfile(AB_CH1, os.path.join(folder_book, "Part 1.m4b"))
real_dir = QFileDialog.getExistingDirectory
QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: folder_book)
ab.import_folder(background=False)
QFileDialog.getExistingDirectory = real_dir
check("Import folder moves a whole book folder",
      os.path.isdir(os.path.join(incoming, "Folder Book"))
      and not os.path.exists(folder_book), sorted(os.listdir(incoming)))
check("the imported folder appears as a title",
      any(ab.tree.topLevelItem(i).text(1) == "Folder Book"
          for i in range(ab.tree.topLevelItemCount())),
      [ab.tree.topLevelItem(i).text(1) for i in range(ab.tree.topLevelItemCount())])
book_shelf = os.path.join(HOME, "folder-source", "Book Shelf")
for book in ("First Book", "Second Book"):
    os.makedirs(os.path.join(book_shelf, book))
    shutil.copyfile(AB_CH2, os.path.join(book_shelf, book, "Chapter.m4b"))
QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: book_shelf)
ab.import_folder(background=False)
QFileDialog.getExistingDirectory = real_dir
check("Import folder imports each book inside a shelf folder",
      os.path.isdir(os.path.join(incoming, "First Book"))
      and os.path.isdir(os.path.join(incoming, "Second Book")),
      sorted(os.listdir(incoming)))

remove_cfg = fresh_config(audiobook_folders=[AB, incoming])
remove_tab = nebula.AudiobooksTab(w.player, remove_cfg)
real_get_item = QInputDialog.getItem
QInputDialog.getItem = staticmethod(lambda *a, **k: (AB, True))
remove_tab.remove_folder()
check("Remove folder takes the folder away without touching the files",
      remove_cfg["audiobook_folders"] == [incoming] and os.path.isdir(AB),
      remove_cfg["audiobook_folders"])
QInputDialog.getItem = real_get_item

# ---------------------------------------------------------------- devices
section("devices and presets")
dev_cfg = fresh_config()
dev1 = nebula.Device(id="mass:/stick", name="Stick", kind="mass", root="/media/stick")
dev2 = nebula.Device(id="mtp:host=PHONE", name="Phone", kind="mtp", root="/run/phone",
                     uri="mtp://PHONE/")
check("a new device is recorded", nebula.remember_device(dev_cfg, dev1) is True)
check("recording it again changes nothing", nebula.remember_device(dev_cfg, dev1) is False)
check("the record has id, name, kind and root",
      dev_cfg["device_registry"][0] ==
      {"id": "mass:/stick", "name": "Stick", "kind": "mass", "root": "/media/stick",
       "uri": ""}, dev_cfg["device_registry"])
nebula.remember_device(dev_cfg, dev2)
nebula.save_config(dev_cfg)
reloaded = nebula.load_config()
check("remembered devices survive a restart",
      [r["id"] for r in reloaded["device_registry"]] == ["mass:/stick", "mtp:host=PHONE"],
      reloaded["device_registry"])

dev_root = os.path.join(HOME, "stick")
os.makedirs(os.path.join(dev_root, "Music"), exist_ok=True)
live_stick = nebula.Device(id="mass:/stick", name="Stick", kind="mass", root=dev_root)
dev_tab = nebula.DevicesTab(w.player, reloaded, nebula.Library(db_file))
dev_tab.set_devices([live_stick])
app.processEvents()
rows = dev_tab._device_rows()
check("a plugged-in device is connected and an absent one is still listed",
      [(r["id"], r["connected"]) for r in rows] ==
      [("mass:/stick", True), ("mtp:host=PHONE", False)],
      [(r["id"], r["connected"]) for r in rows])
reloaded["device_names"] = {"mtp:host=PHONE": "Walkman"}
dev_tab._render_devices()
check("a nickname is used for a device that is not here",
      [r["name"] for r in dev_tab._device_rows()] == ["Stick", "Walkman"],
      [r["name"] for r in dev_tab._device_rows()])
dev_tab.set_devices([])
check("unplugging keeps both rows, now marked absent",
      all(not r["connected"] for r in dev_tab._device_rows())
      and len(dev_tab._device_rows()) == 2, dev_tab._device_rows())

index = next(i for i, r in enumerate(dev_tab._device_rows()) if r["id"] == "mtp:host=PHONE")
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
dev_tab._remove_device(index)
QMessageBox.question = real_question
check("removing a device hides it and remembers the removal",
      "mtp:host=PHONE" in reloaded["removed_devices"]
      and [r["id"] for r in dev_tab._device_rows()] == ["mass:/stick"],
      (reloaded["removed_devices"], [r["id"] for r in dev_tab._device_rows()]))
reloaded["removed_devices"].pop("mtp:host=PHONE", None)
nebula.save_config(reloaded)
dev_tab.refresh_list()
check("restoring it brings the row back with its name",
      [r["id"] for r in dev_tab._device_rows()] == ["mass:/stick", "mtp:host=PHONE"],
      [r["id"] for r in dev_tab._device_rows()])

presets = [nebula.DevicePreset(name="Stick sync", device_id="mass:/stick", source=MUSIC,
                               target="Music", mode="mirror", method="hash"),
           nebula.DevicePreset(name="Walkman sync", device_id="mtp:host=PHONE",
                               source=ALBUM_A, target="Music/Walkman", mode="add",
                               method="bytes", filesystem="exfat")]
nebula.save_presets(presets)
loaded_presets = nebula.load_presets()
check("presets keep their saved ids for compatibility",
      [(p.name, p.device_id) for p in loaded_presets] ==
      [("Stick sync", "mass:/stick"), ("Walkman sync", "mtp:host=PHONE")],
      [(p.name, p.device_id) for p in loaded_presets])
check("presets are shared, not filtered by device",
      len(nebula.load_presets()) == 2, nebula.load_presets())
check("a preset keeps its method and filesystem",
      loaded_presets[1].method == "bytes" and loaded_presets[1].filesystem == "exfat",
      (loaded_presets[1].method, loaded_presets[1].filesystem))
profile = nebula.Profile(name="temp", device_id="mtp:host=PHONE")
loaded_presets[1].apply_to(profile)
check("choosing a preset loads it into the profile",
      (profile.source, profile.target, profile.mode, profile.method, profile.filesystem,
       profile.sources) == (ALBUM_A, "Music/Walkman", "add", "bytes", "exfat", [ALBUM_A]),
      (profile.source, profile.target, profile.mode, profile.method, profile.filesystem,
       profile.sources))
check("presets are not lost when the device registry is",
      ("device_registry" not in fresh_config() and len(nebula.load_presets()) == 2))

# the Syncing tab shows every preset, whichever device the profile targets
w.sync_tab.presets = nebula.load_presets()
w.sync_tab.profiles = [nebula.Profile(name="Shared", device_id="mass:/stick", source=MUSIC)]
w.sync_tab._reload_list()
check("the Syncing tab lists presets saved for another device",
      w.sync_tab.preset.count() == 3, w.sync_tab.preset.count())
check("a profile can save a shared preset even when it has no device",
      w.sync_tab.preset_save.isEnabled())
w.sync_tab._fill_presets(loaded_presets[1].id)
check("a shared preset can be chosen from the list",
      w.sync_tab.preset.currentData() == loaded_presets[1].id,
      w.sync_tab.preset.currentData())
w.sync_tab.preset.setCurrentIndex(0)
w.sync_tab.preset.setCurrentIndex(w.sync_tab.preset.findData(loaded_presets[1].id))
check("the chosen preset is saved on the profile",
      w.sync_tab.current().preset_id == loaded_presets[1].id,
      getattr(w.sync_tab.current(), "preset_id", ""))
nebula.save_profiles(w.sync_tab.profiles)
restored_preset_profiles = nebula.load_profiles()
check("the chosen preset id survives a profile reload",
      restored_preset_profiles[0].preset_id == loaded_presets[1].id,
      restored_preset_profiles[0].preset_id)
w.sync_tab.profiles = restored_preset_profiles
w.sync_tab._reload_list()
check("the preset is selected again after a restart",
      w.sync_tab.preset.currentData() == loaded_presets[1].id,
      w.sync_tab.preset.currentData())

# force-transcode controls the Bitrate row
bit_profile = nebula.Profile(name="Bits", source=MUSIC)
w.sync_tab.profiles = [bit_profile]
w.sync_tab._reload_list()
check("Bitrate is hidden when Force transcode is off",
      w.sync_tab.transcode_bitrate.isHidden() and w.sync_tab.bitrate_label.isHidden())
codec_index = next(i for i in range(w.sync_tab.transcode.count())
                   if w.sync_tab.transcode.itemData(i))
w.sync_tab.transcode.setCurrentIndex(codec_index)
check("Bitrate appears when a transcode codec is chosen",
      not w.sync_tab.transcode_bitrate.isHidden()
      and w.sync_tab.transcode_bitrate.isEnabled())
w.sync_tab.transcode.setCurrentIndex(0)
check("Bitrate disappears again when transcode is turned off",
      w.sync_tab.transcode_bitrate.isHidden() and w.sync_tab.bitrate_label.isHidden())

# a profile can hold several source folders
w.sync_tab.sources_list.clear()
w.sync_tab.sources_list.addItem(MUSIC)
w.sync_tab.sources_list.addItem(ALBUM_B)
w.sync_tab._store()
check("a profile keeps every folder added to it",
      w.sync_tab.current().sources == [MUSIC, ALBUM_B]
      and w.sync_tab.current().source == MUSIC, w.sync_tab.current().sources)
w.sync_tab.selection_mode.setCurrentIndex(
    max(w.sync_tab.selection_mode.findData("selected"), 0))
check("choosing Selected items hides the folder list and its label",
      w.sync_tab.source_box.isHidden() and w.sync_tab.source_label.isHidden()
      and not w.sync_tab.select_btn.isHidden())
w.sync_tab.selection_mode.setCurrentIndex(
    max(w.sync_tab.selection_mode.findData("folders"), 0))
check("folder mode shows the source folder row again",
      not w.sync_tab.source_box.isHidden() and not w.sync_tab.source_label.isHidden())

section("sync engine")
src = os.path.join(HOME, "sync-src")
dst = os.path.join(HOME, "sync-dst")
os.makedirs(os.path.join(src, "Aphex Twin", "Selected Ambient Works"))
shutil.copyfile(WAV1, os.path.join(src, "Aphex Twin", "Selected Ambient Works",
                                   "01 - Alpha.wav"))
shutil.copyfile(WAV2, os.path.join(src, "Aphex Twin", "Selected Ambient Works",
                                   "02 - Beta.wav"))
os.makedirs(dst)
sync_profile = nebula.Profile(name="Stick", device_id=f"folder:{dst}", source=src,
                              target="Music")
backend = nebula.LocalFolderBackend(dst)
plan = nebula.compare(sync_profile, backend)
check("the first compare plans both files as new",
      sorted(a.kind for a in plan) == ["new", "new"], [(a.kind, a.rel) for a in plan])
check("execute copies them without errors", nebula.execute(sync_profile, backend, plan) == 0)
mirrored = os.path.join(dst, "Music", "Artists", "Aphex Twin", "Selected Ambient Works",
                        "01 - Alpha.wav")
check("the copied file is equal", os.path.exists(mirrored)
      and nebula.files_equal(os.path.join(src, "Aphex Twin", "Selected Ambient Works",
                                          "01 - Alpha.wav"), lambda: open(mirrored, "rb")))
check("a second compare finds everything equal",
      [a.kind for a in nebula.compare(sync_profile, backend)] == ["equal", "equal"],
      [a.kind for a in nebula.compare(sync_profile, backend)])
with open(mirrored, "r+b") as f:
    f.seek(-1, os.SEEK_END)
    last = f.read(1)
    f.seek(-1, os.SEEK_END)
    f.write(bytes([last[0] ^ 1]))
changed = [a for a in nebula.compare(sync_profile, backend) if a.kind == "changed"]
check("a one-bit change at the same size is caught", len(changed) == 1, changed)
nebula.execute(sync_profile, backend, nebula.compare(sync_profile, backend))
check("the changed file is repaired", nebula.files_equal(
    os.path.join(src, "Aphex Twin", "Selected Ambient Works", "01 - Alpha.wav"),
    lambda: open(mirrored, "rb")))
extra = os.path.join(dst, "Music", "Extra", "extra.mp3")
os.makedirs(os.path.dirname(extra), exist_ok=True)
shutil.copyfile(MP3A, extra)
plan = nebula.compare(sync_profile, backend)
check("mirror notices a file the library does not have",
      any(a.kind in ("extra", "delete") for a in plan), [(a.kind, a.rel) for a in plan])
nebula.execute(sync_profile, backend, plan)
check("mirror removes the extra file", not os.path.exists(extra))

hash_dst = os.path.join(HOME, "hash-dst")
os.makedirs(hash_dst)
hash_profile = nebula.Profile(name="Hash", device_id=f"folder:{hash_dst}", source=src,
                              target="Music", method="hash")
hash_backend = nebula.LocalFolderBackend(hash_dst)
nebula.execute(hash_profile, hash_backend, nebula.compare(hash_profile, hash_backend))
restore = os.path.join(hash_dst, "Music", "Artists", "Aphex Twin", "Selected Ambient Works",
                       "02 - Beta.wav")
os.remove(restore)
nebula.execute(hash_profile, hash_backend, nebula.compare(hash_profile, hash_backend))
check("hash sync restores a file deleted from the device", os.path.exists(restore))
nebula.save_profiles([hash_profile])
check("sync profiles survive a restart",
      nebula.load_profiles()[0].name == "Hash"
      and nebula.load_profiles()[0].method == "hash")
check("device file names drop FAT32-reserved characters",
      nebula.device_rel("A/VAMPIRE - DECO*27.m4a") == "A/VAMPIRE - DECO27.m4a",
      nebula.device_rel("A/VAMPIRE - DECO*27.m4a"))

src2_root = os.path.join(HOME, "sync-src2")
src2 = os.path.join(src2_root, "Second")
os.makedirs(src2)
shutil.copyfile(FLAC1, os.path.join(src2, "01 - Second.flac"))
multi_dst = os.path.join(HOME, "multi-dst")
os.makedirs(multi_dst)
multi_profile = nebula.Profile(name="Multi", device_id=f"folder:{multi_dst}", source=src,
                               sources=[src, src2_root], target="Music")
multi_backend = nebula.LocalFolderBackend(multi_dst)
multi_plan = nebula.compare(multi_profile, multi_backend)
check("both sync folders are planned together",
      sorted((a.kind, a.rel) for a in multi_plan) ==
      [("new", "Artists/Aphex Twin/Selected Ambient Works/01 - Alpha.wav"),
       ("new", "Artists/Aphex Twin/Selected Ambient Works/02 - Beta.wav"),
       ("new", "Artists/Second/01 - Second.flac")],
      [(a.kind, a.rel) for a in multi_plan])
nebula.execute(multi_profile, multi_backend, multi_plan)
check("both source folders reach the device",
      os.path.exists(os.path.join(multi_dst, "Music", "Artists", "Second",
                                  "01 - Second.flac"))
      and os.path.exists(os.path.join(multi_dst, "Music", "Artists", "Aphex Twin",
                                      "Selected Ambient Works", "01 - Alpha.wav")))

sel_dst = os.path.join(HOME, "selected-dst")
os.makedirs(sel_dst)
selected_rel = "Artists/Aphex Twin/Selected Ambient Works/01 - Alpha.wav"
sel_profile = nebula.Profile(
    name="Selected", device_id=f"folder:{sel_dst}", source=src, sources=[src],
    target="Music", mode="mirror", selection_mode="selected",
    selection=[{"path": WAV1, "rel": selected_rel}])
sel_backend = nebula.LocalFolderBackend(sel_dst)
sel_plan = nebula.compare(sel_profile, sel_backend)
check("selected mode plans only the chosen item",
      [(a.kind, a.rel) for a in sel_plan] == [("new", selected_rel)],
      [(a.kind, a.rel) for a in sel_plan])
nebula.execute(sel_profile, sel_backend, sel_plan)
check("only the chosen item is copied",
      os.path.exists(os.path.join(sel_dst, "Music", selected_rel))
      and not os.path.exists(os.path.join(sel_dst, "Music", "Artists", "Aphex Twin",
                                          "Selected Ambient Works", "02 - Beta.wav")))
sel_extra = os.path.join(sel_dst, "Music", "Other", "keep.mp3")
os.makedirs(os.path.dirname(sel_extra), exist_ok=True)
shutil.copyfile(MP3A, sel_extra)
sel_plan = nebula.compare(sel_profile, sel_backend)
check("selected mode leaves files it never synced alone",
      not any(a.kind == "delete" for a in sel_plan) and os.path.exists(sel_extra),
      [(a.kind, a.rel) for a in sel_plan])
nebula.execute(sel_profile, sel_backend, sel_plan)
check("the file it never synced is still there after a sync", os.path.exists(sel_extra))

# A copy this profile synced before and has now unticked is removed by Mirror only.
beta_rel = "Artists/Aphex Twin/Selected Ambient Works/02 - Beta.wav"
both_profile = nebula.Profile(
    name="Selected both", device_id=f"folder:{sel_dst}", source=src, sources=[src],
    target="Music", mode="mirror", selection_mode="selected",
    selection=[{"path": WAV1, "rel": selected_rel}, {"path": WAV2, "rel": beta_rel}])
both_plan = nebula.compare(both_profile, sel_backend)
check("a second ticked item is planned as new",
      sorted((a.kind, a.rel) for a in both_plan) ==
      [("equal", selected_rel), ("new", beta_rel)],
      [(a.kind, a.rel) for a in both_plan])
nebula.execute(both_profile, sel_backend, both_plan)
both_profile.selection = [{"path": WAV1, "rel": selected_rel}]
both_profile.mode = "update"
update_plan = nebula.compare(both_profile, sel_backend)
check("update plans no deletion for an item that is no longer selected",
      not any(a.kind == "delete" for a in update_plan),
      [(a.kind, a.rel) for a in update_plan])
nebula.execute(both_profile, sel_backend, update_plan)
check("update leaves the unselected copy on the device",
      os.path.exists(os.path.join(sel_dst, "Music", beta_rel)))
both_profile.mode = "mirror"
untick_plan = nebula.compare(both_profile, sel_backend)
check("mirror plans to delete the item that is no longer selected",
      sorted((a.kind, a.rel) for a in untick_plan) ==
      [("delete", beta_rel), ("equal", selected_rel)],
      [(a.kind, a.rel) for a in untick_plan])
nebula.execute(both_profile, sel_backend, untick_plan)
check("the unselected copy is removed and the other one stays",
      not os.path.exists(os.path.join(sel_dst, "Music", beta_rel))
      and os.path.exists(os.path.join(sel_dst, "Music", selected_rel)))
check("deleting an unselected item leaves a file the profile never wrote",
      os.path.exists(sel_extra))

# The same rule for Fast hash.
sel_hash_dst = os.path.join(HOME, "selected-hash-dst")
os.makedirs(sel_hash_dst)
sel_hash_profile = nebula.Profile(
    name="Selected hash", device_id=f"folder:{sel_hash_dst}", source=src, sources=[src],
    target="Music", method="hash", mode="mirror", selection_mode="selected",
    selection=[{"path": WAV1, "rel": selected_rel}, {"path": WAV2, "rel": beta_rel}])
sel_hash_backend = nebula.LocalFolderBackend(sel_hash_dst)
nebula.execute(sel_hash_profile, sel_hash_backend,
               nebula.compare(sel_hash_profile, sel_hash_backend))
hash_extra = os.path.join(sel_hash_dst, "Music", "Other", "keep.mp3")
os.makedirs(os.path.dirname(hash_extra), exist_ok=True)
shutil.copyfile(MP3A, hash_extra)
sel_hash_profile.selection = [{"path": WAV1, "rel": selected_rel}]
hash_untick = nebula.compare(sel_hash_profile, sel_hash_backend)
check("hash mirror plans to delete the item that is no longer selected",
      sorted((a.kind, a.rel) for a in hash_untick) ==
      [("delete", beta_rel), ("equal", selected_rel)],
      [(a.kind, a.rel) for a in hash_untick])
nebula.execute(sel_hash_profile, sel_hash_backend, hash_untick)
check("hash mirror removes the unselected copy and keeps the other",
      not os.path.exists(os.path.join(sel_hash_dst, "Music", beta_rel))
      and os.path.exists(os.path.join(sel_hash_dst, "Music", selected_rel)))
check("hash mirror leaves a file it never synced alone", os.path.exists(hash_extra))

selection_dlg = nebula.SyncSelectionDialog(
    fresh_config(library_folders=[MUSIC], audiobook_folders=[AB]),
    library, [], None)
selection_labels = [selection_dlg.tree.topLevelItem(i).text(0).split(" (")[0]
                    for i in range(selection_dlg.tree.topLevelItemCount())]
music_rows = sum(1 for row in library.tracks()
                 if "podcast" not in str(row.get("genre") or "").lower())
book_files = sum(len(paths) for _name, paths in nebula.audiobook_books([AB]))
check("the selection window has Music and Audiobooks groups, without Podcasts",
      selection_labels == ["Music", "Audiobooks"], selection_labels)
check("everything is selected by default",
      len(selection_dlg.entries()) == music_rows + book_files,
      (len(selection_dlg.entries()), music_rows, book_files))
check("the selection tree starts collapsed",
      all(not selection_dlg.tree.topLevelItem(i).isExpanded()
          for i in range(selection_dlg.tree.topLevelItemCount())))
music_group = selection_dlg.tree.topLevelItem(0)
aphex_artist = next((music_group.child(i) for i in range(music_group.childCount())
                     if music_group.child(i).text(0) == "Aphex Twin"), None)
aphex_album = next((aphex_artist.child(i) for i in range(aphex_artist.childCount())
                    if aphex_artist.child(i).text(0) == "Selected Ambient Works"), None) \
    if aphex_artist is not None else None
check("Music opens as artist > album > tracks",
      aphex_artist is not None and aphex_album is not None
      and aphex_album.parent() is aphex_artist and aphex_album.childCount() >= 2
      and all(aphex_album.child(i).data(0, Qt.UserRole)
              for i in range(aphex_album.childCount())),
      (aphex_artist.text(0) if aphex_artist else None,
       aphex_album.childCount() if aphex_album else None))
check("Music does not list every track as a direct child",
      music_group.childCount() > 0
      and all(music_group.child(i).childCount() > 0
              for i in range(music_group.childCount())),
      [music_group.child(i).text(0) for i in range(music_group.childCount())])
audio_group = selection_dlg.tree.topLevelItem(1)
check("audiobook titles start collapsed",
      all(not audio_group.child(i).isExpanded() for i in range(audio_group.childCount())))
check("the selection buttons are Select All and Unselect All",
      {"Select All", "Unselect All"} <= {b.text() for b in
                                          selection_dlg.findChildren(QPushButton)})
check("an audiobook keeps its book folder on the device",
      any(e["rel"].startswith("Dune/") for e in selection_dlg.entries()),
      [e["rel"] for e in selection_dlg.entries()][:6])
all_entries = selection_dlg.entries()
without_dune = [entry for entry in all_entries if not entry["rel"].startswith("Dune/")]
partial = nebula.SyncSelectionDialog(
    fresh_config(library_folders=[MUSIC], audiobook_folders=[AB]), library,
    without_dune, None)
partial_books = partial.tree.topLevelItem(1)
dune_book = next(partial_books.child(i) for i in range(partial_books.childCount())
                 if partial_books.child(i).text(0) == "Dune")
check("a book with all chapters unselected reopens unchecked",
      dune_book.checkState(0) == Qt.Unchecked
      and all(dune_book.child(i).checkState(0) == Qt.Unchecked
              for i in range(dune_book.childCount())))
none_dlg = nebula.SyncSelectionDialog(
    fresh_config(library_folders=[MUSIC], audiobook_folders=[AB]), library,
    [], None, select_all=False)
check("an explicitly empty selection stays empty", none_dlg.entries() == [])

class PodcastLibrary:
    def tracks(self):
        return [
            {"path": os.path.join(MUSIC, "Podcasts", "Show", "episode.mp3"),
             "title": "Episode", "artist": "", "album": "", "genre": ""},
            {"path": WAV1, "title": "Tagged podcast", "artist": "", "album": "",
             "genre": "Podcast"},
        ]

podcast_dlg = nebula.SyncSelectionDialog(
    fresh_config(library_folders=[MUSIC], audiobook_folders=[]),
    PodcastLibrary(), [], None)
podcast_labels = [podcast_dlg.tree.topLevelItem(i).text(0).split(" (")[0]
                  for i in range(podcast_dlg.tree.topLevelItemCount())]
check("podcast tracks are kept out of the sync selection by tag or folder",
      podcast_dlg.entries() == [] and podcast_labels == ["Music", "Audiobooks"],
      (podcast_dlg.entries(), podcast_labels))
podcast_dlg.close()
selection_dlg._select_none()
check("Unselect All clears every item", selection_dlg.entries() == [])
check("Unselect All clears the music artist branches",
      music_group.checkState(0) == Qt.Unchecked)
selection_dlg._select_all()
check("Select All selects every item again",
      len(selection_dlg.entries()) == music_rows + book_files)
check("Select All restores the music tree", music_group.checkState(0) == Qt.Checked)
partial.close()
none_dlg.close()
selection_dlg.close()

# Every profile carries its own target tree. Music and books land below the chosen
# device folder; podcasts are paused and are not offered or copied.
os.makedirs(os.path.join(src, "Podcasts", "Show"), exist_ok=True)
shutil.copyfile(MP3A, os.path.join(src, "Podcasts", "Show", "episode.mp3"))
routed_dst = os.path.join(HOME, "routed-dst")
os.makedirs(routed_dst)
routed_profile = nebula.Profile(name="Routed", device_id=f"folder:{routed_dst}",
                               source=src, sources=[src, AB], target="Music",
                               audiobook_roots=[AB])
routed_plan = nebula.compare(routed_profile, nebula.LocalFolderBackend(routed_dst))
check("the profile sends music and audiobooks, but not podcasts",
      sorted((a.kind, a.rel) for a in routed_plan) == [
          ("new", "Artists/Aphex Twin/Selected Ambient Works/01 - Alpha.wav"),
          ("new", "Artists/Aphex Twin/Selected Ambient Works/02 - Beta.wav"),
          ("new", "Audiobooks/Dune/Chapter 01.m4b"),
          ("new", "Audiobooks/Dune/Chapter 02.m4b"),
          ("new", "Audiobooks/The Hobbit.m4b")],
      [(a.kind, a.rel) for a in routed_plan])
nebula.execute(routed_profile, nebula.LocalFolderBackend(routed_dst), routed_plan)
check("the rendered paths use the selected folder and its music/audiobook subfolders",
      os.path.exists(os.path.join(routed_dst, "Music", "Artists", "Aphex Twin",
                                  "Selected Ambient Works", "01 - Alpha.wav"))
      and os.path.exists(os.path.join(routed_dst, "Music", "Audiobooks", "Dune",
                                      "Chapter 01.m4b"))
      and not os.path.exists(os.path.join(routed_dst, "Music", "Podcasts", "Show",
                                          "episode.mp3")))
target_dialog = nebula.SyncTargetsDialog(routed_profile, routed_dst)
target_dialog.base.setText("Walkman/Music")
target_dialog.music.setText("Artists")
target_dialog.audiobooks.setText("Audiobooks")
check("Choose Target Folders edits only the Music and Audiobooks paths",
      target_dialog.values() == ("Walkman/Music", "Artists", "Audiobooks")
      and "Walkman/Music/Audiobooks" in target_dialog.preview.text()
      and "Podcasts" not in target_dialog.preview.text()
      and not hasattr(target_dialog, "podcasts"),
      (target_dialog.values(), target_dialog.preview.text()))
target_dialog.close()
legacy_podcast_profile = nebula.Profile(
    name="Legacy podcast", selection_mode="selected",
    selection=[{"path": WAV1, "rel": "Podcasts/Show/episode.wav", "kind": "podcast"}])
check("a legacy podcast selection is ignored by the sync engine",
      nebula.profile_sync_files(legacy_podcast_profile) == {},
      nebula.profile_sync_files(legacy_podcast_profile))
inactive_dst = os.path.join(HOME, "inactive-dst")
os.makedirs(os.path.join(inactive_dst, "Music", "Audiobooks"))
os.makedirs(os.path.join(inactive_dst, "Music", "Podcasts", "Keep"))
shutil.copyfile(AB_CH1, os.path.join(inactive_dst, "Music", "Audiobooks", "keep.m4b"))
shutil.copyfile(MP3A, os.path.join(inactive_dst, "Music", "Podcasts", "Keep", "keep.mp3"))
inactive_profile = nebula.Profile(name="Music only", device_id=f"folder:{inactive_dst}",
                                 source=src, sources=[src], target="Music", mode="mirror")
inactive_plan = nebula.compare(inactive_profile, nebula.LocalFolderBackend(inactive_dst))
check("a music profile does not delete the Audiobooks or Podcasts trees it is not sending",
      not any(a.kind == "delete" and (a.rel.startswith("Audiobooks/")
                                       or a.rel.startswith("Podcasts/"))
              for a in inactive_plan)
      and os.path.exists(os.path.join(inactive_dst, "Music", "Podcasts", "Keep",
                                      "keep.mp3")),
      [(a.kind, a.rel) for a in inactive_plan])

saved_profiles = nebula.load_profiles()
empty_profile = nebula.Profile(name="Empty selection", selection_mode="selected",
                               selection=[], selection_all=False)
nebula.save_profiles([empty_profile])
loaded_empty = nebula.load_profiles()[0]
check("an empty selected-item choice survives a profile reload",
      loaded_empty.selection_mode == "selected" and not loaded_empty.selection
      and loaded_empty.selection_all is False)
nebula.save_profiles(saved_profiles)

# ---------------------------------------------------------------- session
section("session restore and the reported data loss")
w.config["library_folders"] = [MUSIC]
w.config["device_registry"] = [
    {"id": "mass:/stick", "name": "Stick", "kind": "mass", "root": "/stick", "uri": ""},
    {"id": "mtp:host=PHONE", "name": "Phone", "kind": "mtp", "root": "/run/phone",
     "uri": "mtp://PHONE/"}]
w.config["device_names"] = {"mtp:host=PHONE": "Walkman"}
w.config["volume"] = 63
w.tabs.setCurrentIndex(1)
app.processEvents()
w.player.set_queue([WAV1, FLAC1])
w.library_tab._save_queue_state()
nebula.save_config(w.config)
w.close()

restored = nebula.load_config()
check("the library folder is still there after closing",
      restored["library_folders"] == [MUSIC], restored["library_folders"])
check("both remembered devices are still there after closing",
      [r["id"] for r in restored["device_registry"]] == ["mass:/stick", "mtp:host=PHONE"],
      restored["device_registry"])
check("the queue survives the restart", restored["queue"] == [WAV1, FLAC1],
      restored["queue"])
check("volume and tab survive the restart",
      restored["volume"] == 63 and restored["tab"] == 1,
      (restored["volume"], restored["tab"]))

asked.clear()
QMessageBox.question = staticmethod(
    lambda *a, **k: asked.append(a[2] if len(a) > 2 else "") or QMessageBox.No)
w4 = nebula.MainWindow()
QTest.qWait(650)
check("the next launch restores the queue", len(w4.player.queue) == 2, w4.player.queue)
check("the next launch restores the remembered devices",
      [r["id"] for r in w4.devices_tab._device_rows()] == ["mass:/stick", "mtp:host=PHONE"],
      w4.devices_tab._device_rows())
check("the next launch does not ask for the library folder", not asked, asked)
QMessageBox.question = real_question
w4.close()

# reproduce the exact 1.09 accident: a stray defaults write, then recovery
good = json.loads(json.dumps(restored))
nebula.save_config(good)
nebula.save_config(fresh_config())          # the bad write
check("the bad write left an empty folder list in place",
      nebula.load_config()["library_folders"] == [])
backup_data = json.load(open(nebula.CONFIG_FILE + ".bak", encoding="utf-8"))
check("the backup still has the folders and devices",
      backup_data["library_folders"] == [MUSIC]
      and len(backup_data["device_registry"]) == 2, backup_data.get("library_folders"))
with open(nebula.CONFIG_FILE, "w", encoding="utf-8") as f:
    f.write("{")
check("a damaged config after the bad write comes back from the backup",
      nebula.load_config()["library_folders"] == [MUSIC],
      nebula.load_config()["library_folders"])

# ---------------------------------------------------------------- settings backup
section("settings backup")
w.config["discogs_token"] = "secret-token"
w.config["discogs_secret"] = "secret-secret"
backup_groups = {"preferences", "sync_profiles", "device_presets", "smart_playlists"}
backup = nebula.build_settings_bundle(w.config, backup_groups)
check("a settings backup has all four parts",
      set(backup) >= {"nebula_settings", "preferences", "sync_profiles",
                      "device_presets", "smart_playlists"}, set(backup))
check("a settings backup leaves credentials out",
      not ({"discogs_token", "discogs_secret"}
           & set(backup["preferences"])), backup["preferences"].keys())
backup_path = os.path.join(HOME, "settings-backup.json")
nebula.write_settings_bundle(backup_path, w.config, backup_groups)
loaded_backup = nebula.read_settings_bundle(backup_path)
check("an exported settings file reads back",
      loaded_backup.get("preferences", {}).get("volume") == w.config["volume"])
try:
    nebula.read_settings_bundle(nebula.CONFIG_FILE)
    bad_backup = False
except ValueError:
    bad_backup = True
check("an ordinary JSON file is not mistaken for a settings backup", bad_backup)
import_cfg = fresh_config(discogs_token="keep-me", volume=1)
import_bundle = {"nebula_settings": 1, "preferences": {"volume": 13,
                  "discogs_token": "do-not-copy"}}
imported = nebula.apply_settings_bundle(import_bundle, import_cfg, {"preferences"})
check("importing merges preferences and keeps credentials",
      import_cfg["volume"] == 13 and import_cfg["discogs_token"] == "keep-me"
      and imported.get("preferences") is True,
      (import_cfg["volume"], import_cfg["discogs_token"]))
try:
    nebula.apply_settings_bundle({"nebula_settings": 1}, import_cfg, {"preferences"})
    missing_ok = False
except ValueError:
    missing_ok = True
check("a settings file missing a selected part is refused", missing_ok)

# ---------------------------------------------------------------- summary
section("summary")
failed = [r for r in RESULTS if not r[2]]
print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
for sec, name, _ok, detail in failed:
    print(f"  FAILED [{sec}] {name}: {detail}")
print(f"\nscratch home: {HOME} (removed when the run ends)")
sys.exit(1 if failed else 0)
