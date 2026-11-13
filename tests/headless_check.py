# Copyright (C) 2026 Roger Barthares
# SPDX-License-Identifier: GPL-3.0-only
"""Headless verification for nebula.py.

Run:  QT_QPA_PLATFORM=offscreen python3 tests/headless_check.py
It builds a throw-away home directory, generates real WAV/FLAC/MP3 files, and
exercises the library, smart playlists, playlists, player queue, tagger,
devices and sync engine. Exit code 0 means every check passed.
"""
import atexit
import json
import math
import os
import shutil
import subprocess
import urllib.error
import sqlite3
import struct
import sys
import tempfile
import threading
import time
import traceback
import wave

HOME = tempfile.mkdtemp(prefix="nebula-check-")
os.environ["HOME"] = HOME
# the app writes to two roots: settings/data, and a cache it may throw away. pin
# both inside the throw-away home so a real library on this machine can never be
# touched, and delete the whole home when the run ends (a run used to leave
# ~20 MB behind every time)
DATA_ROOT = os.path.join(HOME, "Nebula")
CACHE_ROOT = os.path.join(HOME, ".cache", "Nebula")
os.environ["NEBULA_DATA"] = DATA_ROOT
os.environ["NEBULA_CACHE"] = CACHE_ROOT
atexit.register(shutil.rmtree, HOME, True)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from mutagen.flac import FLAC  # noqa: E402
from mutagen.id3 import ID3, TALB, TCON, TDRC, TIT2, TPE1, TRCK  # noqa: E402
from mutagen.wave import WAVE  # noqa: E402

import nebula  # noqa: E402
from PySide6.QtCore import QEvent, QPointF, QSize, Qt, QUrl  # noqa: E402
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPixmap  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QTableWidgetSelectionRange  # noqa: E402

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


def tracks_in_tree(tree):
    out = []

    def walk(item):
        for i in range(item.childCount()):
            child = item.child(i)
            if child.data(0, nebula.PATH_ROLE):
                out.append(child)
            walk(child)
    walk(tree.invisibleRootItem())
    return out


def all_items(tree):
    out = []
    root = tree.invisibleRootItem() if hasattr(tree, "invisibleRootItem") else tree

    def walk(item):
        for i in range(item.childCount()):
            child = item.child(i)
            out.append(child)
            walk(child)
    walk(root)
    return out


def double_click(view, point):
    """Double-click a view at `point`.

    QTest.mouseDClick only delivers a mouse move on some offscreen Qt builds,
    so this sends the same MouseButtonDblClick event Qt's window system would.
    """
    viewport = view.viewport()
    QTest.mouseClick(viewport, Qt.LeftButton, Qt.NoModifier, point)
    event = QMouseEvent(QEvent.MouseButtonDblClick, QPointF(point),
                        QPointF(viewport.mapToGlobal(point)), Qt.LeftButton,
                        Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(viewport, event)


def find_item(tree, text, exact=True):
    stack = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
    while stack:
        item = stack.pop()
        labels = [item.text(i) for i in range(tree.columnCount())]
        hit = any((label == text) if exact else (text in label) for label in labels if label)
        if hit:
            return item
        stack.extend(item.child(i) for i in range(item.childCount()))
    return None


# ---------------------------------------------------------------- fixtures
MUSIC = os.path.join(HOME, "music")
ALBUM_A = os.path.join(MUSIC, "Aphex Twin - Selected")
ALBUM_B = os.path.join(MUSIC, "Boards of Canada - Music Has the Right")
os.makedirs(ALBUM_A)
os.makedirs(ALBUM_B)


def write_wav(path, seconds, title, artist, album, track, year, genre, albumartist=""):
    with wave.open(path, "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(44100)
        n = int(44100 * seconds)
        f.writeframes(b"".join(struct.pack("<hh", int(1200 * np.sin(2 * np.pi * 440 * i / 44100)), 0)
                               for i in range(n)))
    audio = WAVE(path)
    if audio.tags is None:
        audio.add_tags()
    audio.tags.add(TIT2(encoding=3, text=title))
    audio.tags.add(TPE1(encoding=3, text=artist))
    audio.tags.add(TALB(encoding=3, text=album))
    audio.tags.add(TRCK(encoding=3, text=str(track)))
    audio.tags.add(TDRC(encoding=3, text=year))
    audio.tags.add(TCON(encoding=3, text=genre))
    if albumartist:
        from mutagen.id3 import TPE2
        audio.tags.add(TPE2(encoding=3, text=albumartist))
    audio.save()


def write_flac(path, title, artist, album, track, year, genre, rate=96000, bits=24):
    sf.write(path, np.zeros((rate, 2), dtype="float32"), rate, subtype=f"PCM_{bits}")
    audio = FLAC(path)
    audio["title"] = title
    audio["artist"] = artist
    audio["album"] = album
    audio["tracknumber"] = str(track)
    audio["date"] = year
    audio["genre"] = genre
    audio.save()


def write_mp3(path, title, artist, album, track, year, genre):
    frame = b"\xff\xfb\x90\x00" + b"\x00" * 413   # MPEG1 L3, 128 kbps, 44.1 kHz, stereo
    with open(path, "wb") as f:
        f.write(frame * 120)
    tags = ID3()
    tags.add(TIT2(encoding=3, text=title))
    tags.add(TPE1(encoding=3, text=artist))
    tags.add(TALB(encoding=3, text=album))
    tags.add(TRCK(encoding=3, text=str(track)))
    tags.add(TDRC(encoding=3, text=year))
    tags.add(TCON(encoding=3, text=genre))
    tags.save(path, v2_version=3)


WAV1 = os.path.join(ALBUM_A, "01 - Alpha.wav")
WAV2 = os.path.join(ALBUM_A, "02 - Beta.wav")
FLAC1 = os.path.join(ALBUM_B, "01 - Gamma.flac")
MP3A = os.path.join(ALBUM_B, "01 - Delta.mp3")
MP3B = os.path.join(ALBUM_B, "02 - Epsilon.mp3")

write_wav(WAV1, 2.0, "Alpha", "Aphex Twin", "Selected Ambient Works", 1, "1992", "Electronic")
write_wav(WAV2, 3.0, "Beta", "Aphex Twin", "Selected Ambient Works", 2, "1992", "Electronic")
write_flac(FLAC1, "Gamma", "Boards of Canada", "Music Has the Right to Children", 1, "1998", "Electronic")
write_mp3(MP3A, "Delta", "MP3 Artist", "Compilation", 1, "1987", "Pop")
write_mp3(MP3B, "Epsilon", "Another Artist", "Compilation", 2, "1987", "Pop")

app = QApplication([])
nebula.install_app_style(app)

# No real drive in this harness: a disc in the machine's drive must not change the results.
# The CD sections below install their own fake drives and restore this stub.
def set_drives(device=None, *others):
    """What the one drive probe the watcher makes answers: these drives, and nothing else.

    The machine running this harness may have a real optical drive with a disc in it, so
    every CD check says which drives exist rather than letting it be found.
    """
    nebula.cd_drive_states = lambda: {device: "disc", **{d: "empty" for d in others}} \
        if device else {}


set_drives()

# ---------------------------------------------------------------- tags
section("tags and stream specs")

wav_tags = nebula.read_tags(WAV1)
check("WAV tags read through the ID3 fallback", wav_tags["title"] == "Alpha"
      and wav_tags["artist"] == "Aphex Twin" and wav_tags["date"] == "1992", wav_tags)
wav_specs = nebula.read_specs(WAV1)
check("WAV specs: 16-bit / 44.1 kHz stereo", wav_specs["bits_per_sample"] == 16
      and wav_specs["sample_rate"] == 44100 and wav_specs["channels"] == 2, wav_specs)
flac_specs = nebula.read_specs(FLAC1)
check("FLAC specs: 24-bit / 96 kHz", flac_specs["bits_per_sample"] == 24
      and flac_specs["sample_rate"] == 96000, flac_specs)
mp3_specs = nebula.read_specs(MP3A)
check("MP3 specs: 128 kbps / 44.1 kHz, no bit depth", mp3_specs["bitrate"] == 128000
      and mp3_specs["sample_rate"] == 44100 and mp3_specs["bits_per_sample"] == 0, mp3_specs)
check("format pill text", nebula.spec_parts(flac_specs)[:2] == ["FLAC", "24-bit / 96.0 kHz"],
      nebula.spec_parts(flac_specs))


class _FakeMP4Info:
    length = 3.0
    sample_rate = 44100
    channels = 2
    bitrate = 256000
    bits_per_sample = 0

    def __init__(self, codec, description):
        self.codec = codec
        self.codec_description = description


class _FakeMP4:
    tags = None

    def __init__(self, codec, description):
        self.info = _FakeMP4Info(codec, description)


_real_mutagen_file = nebula.mutagen.File
try:
    nebula.mutagen.File = lambda path, *a, **k: _FakeMP4("mp4a.40.2", "AAC")
    check("an AAC .m4a reports AAC, not ALAC",
          nebula.read_specs("/tmp/song.m4a")["filetype"] == "AAC"
          and nebula.filetype("/tmp/song.m4a") == "AAC"
          and nebula.tag_label("/tmp/song.m4a") == "MP4 (AAC)",
          (nebula.read_specs("/tmp/song.m4a")["filetype"],
           nebula.tag_label("/tmp/song.m4a")))
    nebula.mutagen.File = lambda path, *a, **k: _FakeMP4("mp4a.40.5", "AAC LC+SBR")
    check("HE-AAC is still AAC", nebula.tag_label("/tmp/song.m4a") == "MP4 (AAC)",
          nebula.tag_label("/tmp/song.m4a"))
    nebula.mutagen.File = lambda path, *a, **k: _FakeMP4("alac", "ALAC")
    check("a real ALAC .m4a still says ALAC",
          nebula.tag_label("/tmp/song.m4a") == "MP4 (ALAC)"
          and nebula.read_specs("/tmp/song.m4a")["filetype"] == "ALAC")
finally:
    nebula.mutagen.File = _real_mutagen_file
check("non-MP4 extensions keep their plain format name",
      nebula.filetype(FLAC1) == "FLAC" and nebula.filetype(WAV1) == "WAV")
check("Tag column labels FLAC and WAV", nebula.tag_label(FLAC1) == "FLAC (FLAC)"
      and nebula.tag_label(WAV1) == "WAV (ID3v2)",
      (nebula.tag_label(FLAC1), nebula.tag_label(WAV1)))

migrate_db = os.path.join(HOME, "migrate.db")
with sqlite3.connect(migrate_db) as c:
    c.execute("CREATE TABLE tracks (path TEXT PRIMARY KEY, mtime REAL, filetype TEXT)")
    c.execute("INSERT INTO tracks VALUES ('/music/old.m4a', 123.0, 'ALAC')")
nebula.Library(migrate_db)
with sqlite3.connect(migrate_db) as c:
    row = c.execute("SELECT mtime FROM tracks WHERE path='/music/old.m4a'").fetchone()
check("old ALAC-labelled m4a rows are queued for a rescan", row == (None,), row)
check("filename pattern parser",
      nebula.tags_from_filename("07 - Aphex Twin - Xtal.mp3", "%tracknumber% - %artist% - %title%")
      == {"tracknumber": "07", "artist": "Aphex Twin", "title": "Xtal"})
check("filename builder", nebula.filename_from_tags({"tracknumber": "7", "title": "Xtal"},
                                                     "%tracknumber% - %title%", ".mp3")
      == "07 - Xtal.mp3")

copy_wav = os.path.join(HOME, "copy.wav")
shutil.copyfile(WAV1, copy_wav)
nebula.write_tags(copy_wav, {"title": "Changed", "genre": "", "composer": "Someone"})
reread = nebula.read_tags(copy_wav)
check("write_tags on WAV (ID3 container)", reread["title"] == "Changed"
      and reread["genre"] == "" and reread["composer"] == "Someone", reread)
shutil.copyfile(FLAC1, os.path.join(HOME, "copy.flac"))
nebula.write_tags(os.path.join(HOME, "copy.flac"), {"album": "Retitled"})
check("write_tags on FLAC (easy layer)",
      nebula.read_tags(os.path.join(HOME, "copy.flac"))["album"] == "Retitled")

# ---------------------------------------------------------------- library
section("library, stats and smart playlists")
library = nebula.Library()
library.scan([MUSIC])
rows = library.tracks()
check("scan found all five tracks", len(rows) == 5, len(rows))
check("scan stored stream specs", any(r["sample_rate"] == 96000 and r["bits_per_sample"] == 24
                                      for r in rows))
check("default order sorts by album artist then album",
      [(r["albumartist"] or r["artist"] or "").lower() for r in rows]
      == sorted((r["albumartist"] or r["artist"] or "").lower() for r in rows),
      [r["title"] for r in rows])

added_before = {r["path"]: r["added"] for r in rows}
library.play_count(WAV1)
library.play_count(WAV1)
library.play_count(FLAC1)
library.scan([MUSIC])
after = {r["path"]: r for r in library.tracks()}
check("rescan keeps play counts", after[WAV1]["play_count"] == 2, after[WAV1]["play_count"])
check("rescan keeps the added timestamp", after[WAV1]["added"] == added_before[WAV1])

presets = {p["name"]: nebula.SmartStore.preset_tracks(library, p) for p in nebula.SMART_PRESETS}
check("Hi-Res Audio finds only the 24/96 track",
      [r["path"] for r in presets["Hi-Res Audio"]] == [FLAC1])
check("Top 50 Most Played ranks by plays",
      [r["path"] for r in presets["Top 50 Most Played"]][:2] == [WAV1, FLAC1],
      [r["title"] for r in presets["Top 50 Most Played"]])
check("Never Played excludes played tracks", len(presets["Never Played"]) == 3,
      [r["title"] for r in presets["Never Played"]])
check("80s & 90s Classics uses tag years", len(presets["80s & 90s Classics"]) == 5,
      [r["title"] for r in presets["80s & 90s Classics"]])
check("Recently Added returns the library", len(presets["Recently Added"]) == 5)
check("Random 100 returns the library", len(presets["Random 100"]) == 5)

store = nebula.SmartStore(library)
custom = {"name": "Lossless only", "match": "all", "limit": 0,
          "rules": [{"field": "filetype", "op": "is", "value": "flac"}]}
store.add(custom)
check("custom smart rule (file type is flac)",
      [r["path"] for r in store.tracks(custom)] == [FLAC1])
where, params = nebula.build_smart_where(
    [{"field": "genre", "op": "contains", "value": "electronic"},
     {"field": "bits_per_sample", "op": "is greater than", "value": "16"}], match="all")
check("rule builder returns parameterised SQL", "?" in where and len(params) == 2, where)
check("rule builder query runs", len(library.tracks(where=where, args=params)) == 1)
check("empty-value rule is ignored", nebula.build_smart_where(
    [{"field": "artist", "op": "contains", "value": ""}])[0] == "")

# ---------------------------------------------------------------- playlists
section("playlists (.m3u8)")
playlists = nebula.PlaylistStore(lambda: [MUSIC])
playlists.write("Mix", [WAV1, FLAC1])
raw = open(playlists.path("Mix"), encoding="utf-8").read().splitlines()
check("playlist header written", raw[0] == "#EXTM3U")
check("playlist stores portable paths", raw[1] == os.path.join("Aphex Twin - Selected",
                                                              "01 - Alpha.wav"), raw[1:])
check("playlist resolves back to absolute paths", playlists.read("Mix") == [WAV1, FLAC1])
ext = os.path.join(HOME, "external.m3u8")
with open(ext, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n" + WAV2 + "\n")
imported = playlists.import_file(ext)
check("import of an external .m3u8", imported == "external" and playlists.read(imported) == [WAV2])
check("rename playlist", playlists.rename("external", "imported") and playlists.read("imported") == [WAV2])
playlists.remove("imported")
check("delete playlist", "imported" not in playlists.names())

# ---------------------------------------------------------------- main window
section("main window, tree and queue")
early = nebula.load_config()
early["library_folders"] = [MUSIC]
nebula.save_config(early)
w = nebula.MainWindow()
w.show()
app.processEvents()
tab = w.library_tab
w.config["library_folders"] = [MUSIC]
tab.refresh()
tab.reload_smart()
check("five tabs", [w.tabs.tabText(i) for i in range(w.tabs.count())]
      == ["Music", "Audiobooks", "Tags", "Devices", "Syncing"])
logo_widget = w.tabs.cornerWidget(Qt.Corner.TopLeftCorner)
check("Nebula logo fills the tab row height",
      logo_widget.height() == max(36, w.tabs.tabBar().sizeHint().height())
      and not logo_widget.pixmap().isNull()
      and logo_widget.pixmap().height() == max(36, w.tabs.tabBar().sizeHint().height()),
      (logo_widget.height(), w.tabs.tabBar().sizeHint().height(),
       logo_widget.pixmap().height() if logo_widget.pixmap() else None))
check("the title bar uses the short name, the About box the full one",
      w.windowTitle() == f"Nebula {nebula.VERSION}"
      and nebula.APP_SHORT == "Nebula" and nebula.APP_NAME == "Nebula Music Center",
      f"{w.windowTitle()!r} {nebula.APP_SHORT!r} {nebula.APP_NAME!r}")


def menu_titles():
    return [a.text().replace("&", "") for a in w.menuBar().actions()]


check("library tab uses the player menus",
      menu_titles() == ["Music", "Playlist", "Tools", "Help"], menu_titles())
w.tabs.setCurrentWidget(w.tagger_tab)
app.processEvents()
check("tags tab swaps to mp3tag's menus",
      menu_titles() == ["File", "Edit", "View", "Convert", "Actions", "Tag Sources", "Help"],
      menu_titles())
tag_menus = {a.text().replace("&", ""): a.menu() for a in w.menuBar().actions()}
check("mp3tag File menu has open, save, revert and remove",
      [a.text() for a in tag_menus["File"].actions() if a.text()]
      == ["Open folder…", "Add files…", "Remove selected files", "Save tag",
          "Revert changes", "Close list", "Exit"],
      [a.text() for a in tag_menus["File"].actions()])
check("mp3tag Edit menu has undo, clipboard, selection and filter",
      [a.text() for a in tag_menus["Edit"].actions() if a.text()]
      == ["Undo", "Redo", "Cut", "Copy", "Paste", "Select all", "Deselect all",
          "Invert selection", "Filter", "Find and replace…"],
      [a.text() for a in tag_menus["Edit"].actions()])
check("mp3tag View menu toggles toolbar, panel, list, filter and columns",
      [a.text() for a in tag_menus["View"].actions() if a.text()]
      == ["Toolbar", "Tag panel", "File list", "Filter", "Columns", "Refresh"],
      [a.text() for a in tag_menus["View"].actions()])
check("mp3tag Convert menu offers both direction and Tag-Tag",
      [a.text() for a in tag_menus["Convert"].actions() if a.text()]
      == ["Filename → Tag…", "Tag → Filename…", "Tag → Tag…",
          "Auto-numbering wizard…"],
      [a.text() for a in tag_menus["Convert"].actions()])
tag_context = w.tagger_tab._build_table_menu()
tag_context_actions = [a.text() for a in tag_context.actions() if a.text()]
check("the tagger right-click menu no longer repeats filename/tag conversion",
      "Tag \u2190 Filename\u2026" not in tag_context_actions
      and "Filename \u2190 Tag\u2026" not in tag_context_actions
      and "Look up metadata & cover\u2026" in tag_context_actions,
      tag_context_actions)
tag_context.deleteLater()
view_actions = {a.text(): a for a in tag_menus["View"].actions() if a.text()}
columns_menu = tag_menus["View"].actions()[5].menu()
check("View > Columns lists every file-list column",
      [a.text() for a in columns_menu.actions() if a.text()]
      == ["Filename", "Title", "Track", "Artist", "Album artist", "Album",
          "Disc", "Tag", "Year", "Genre", "Comment"],
      [a.text() for a in columns_menu.actions()])
view_actions["Tag panel"].setChecked(False)
check("View > Tag panel hides the panel", w.tagger_tab.side_panel.isHidden())
view_actions["Tag panel"].setChecked(True)
check("View > Tag panel shows it again", not w.tagger_tab.side_panel.isHidden())
col_actions = {a.text(): a for a in columns_menu.actions() if a.text()}
col_actions["Genre"].setChecked(False)
check("View > Columns hides the genre column",
      w.tagger_tab.table.isColumnHidden(nebula.COLS.index("genre")))
col_actions["Genre"].setChecked(True)
check("View > Columns brings it back",
      not w.tagger_tab.table.isColumnHidden(nebula.COLS.index("genre")))
view_actions["Filter"].setChecked(False)
check("View > Filter hides the filter row", w.tagger_tab.filter_bar.isHidden())
view_actions["Filter"].setChecked(True)
check("tag shortcuts live on the mp3tag menu set",
      [a.shortcut().toString() for a in tag_menus["File"].actions()
       if a.text() == "Save tag"] == ["Ctrl+S"])
w.tabs.setCurrentWidget(w.library_tab)
app.processEvents()
check("switching back restores Music/Playlist/Tools/Help",
      menu_titles() == ["Music", "Playlist", "Tools", "Help"], menu_titles())
check("Ctrl+S follows the active menu set",
      not any(a.text() == "Save tag" and a.shortcut().toString()
              for a in tag_menus["File"].actions())
      and any(a.shortcut().toString() == "Ctrl+S"
              for a in w.menuBar().actions()[1].menu().actions()))
check("three strip buttons", len(tab.strip_buttons) == 3 and
      set(tab.strip_buttons) == {"collection", "playlists", "smart"})
tab.set_view("playlists")
check("strip switches the left panel", tab.pages.currentIndex() == 1
      and tab.config["view"] == "playlists")
tab.set_view("collection")
check("collection lists every track", len(tracks_in_tree(tab.tree)) == 5,
      len(tracks_in_tree(tab.tree)))
check("artist tree has A-Z letter dividers", find_item(tab.tree, "A") is not None)
check("library starts as one hierarchy column",
      tab.tree.columnCount() == 1 and tab.tree.isHeaderHidden(),
      (tab.tree.columnCount(), tab.tree.isHeaderHidden()))
fold_actions = {a.text(): a for a in tab.fold_btn.menu().actions()}
check("fold menu offers three modes",
      list(fold_actions) == ["Open all", "Open letter markers only", "Close all"], list(fold_actions))
fold_actions["Close all"].trigger()
check("close all collapses every node",
      not any(i.isExpanded() for i in all_items(tab.tree)))
fold_actions["Open all"].trigger()
check("open all expands every node",
      all(i.isExpanded() for i in all_items(tab.tree) if i.childCount()))
fold_actions["Open letter markers only"].trigger()
letter_nodes = [tab.tree.topLevelItem(i) for i in range(tab.tree.topLevelItemCount())
                if tab.tree.topLevelItem(i).data(0, nebula.KIND_ROLE) == "divider"]
check("letters mode opens every A-Z marker", letter_nodes and all(n.isExpanded() for n in letter_nodes),
      len(letter_nodes))
check("letters mode leaves artists and albums closed",
      not any(i.isExpanded() for i in all_items(tab.tree)
              if i.data(0, nebula.KIND_ROLE) != "divider"))

# The fold position is part of the library's state: a fresh tree (what a launch builds)
# must come back the way it was left, not at whatever the auto-open setting says.
section("library: the fold position is remembered")


def fold_state():
    """Every node's open/closed state, keyed by its label, for comparing trees."""
    return {tab._node_label(i): i.isExpanded() for i in all_items(tab.tree)}


for mode, label in (("all", "Open all"), ("none", "Close all"),
                    ("letters", "Open letter markers only")):
    fold_actions[label].trigger()
    saved = nebula.load_config().get("lib_fold")
    check(f"{label} is written to the config", saved == mode, saved)
    check(f"the menu ticks {label} and only it",
          fold_actions[label].isChecked()
          and sum(1 for a in fold_actions.values() if a.isChecked()) == 1,
          [(a.text(), a.isChecked()) for a in fold_actions.values()])
    before = fold_state()
    tab.tree.collapseAll()          # throw the position away, as a new window would
    tab.refresh()                   # refresh is what a launch ends up doing after the scan
    dividers = [tab.tree.topLevelItem(i) for i in range(tab.tree.topLevelItemCount())
                if tab.tree.topLevelItem(i).data(0, nebula.KIND_ROLE) == "divider"]
    if mode == "all":
        restored = all(i.isExpanded() for i in all_items(tab.tree) if i.childCount())
    elif mode == "letters":
        restored = (dividers and all(d.isExpanded() for d in dividers)
                    and not any(i.isExpanded() for i in all_items(tab.tree)
                                if i.data(0, nebula.KIND_ROLE) != "divider"))
    else:
        restored = not any(i.isExpanded() for i in all_items(tab.tree))
    check(f"a fresh tree comes back {label.lower()}", restored, fold_state())

fold_actions["Open letter markers only"].trigger()
check("the saved position survives into the next launch's config",
      nebula.load_config().get("lib_fold") == "letters")


def wait_for_scan(tab, want):
    for _ in range(400):
        app.processEvents()
        QTest.qWait(10)
        if not tab._scan.isRunning() and tab.library.count() == want:
            break
    app.processEvents()


extra = tempfile.mkdtemp(prefix="extra", dir=HOME)
shutil.copy(WAV1, extra)
w.config["library_folders"] = [MUSIC, extra]
tab.rescan(silent=True)
wait_for_scan(tab, 6)
check("silent rescan picks up a newly added folder",
      tab.library.count() == 6 and len(tracks_in_tree(tab.tree)) == 6,
      (tab.library.count(), len(tracks_in_tree(tab.tree))))
shutil.rmtree(extra)
tab.rescan(silent=True)
wait_for_scan(tab, 5)
check("removed folder is noticed without restarting",
      tab.library.count() == 5 and len(tracks_in_tree(tab.tree)) == 5,
      (tab.library.count(), len(tracks_in_tree(tab.tree))))
w.config["library_folders"] = [MUSIC]

drop = tempfile.mkdtemp(prefix="dropme", dir=HOME)
shutil.copy(WAV2, os.path.join(drop, "dropped.wav"))
w.config["library_folders"] = [MUSIC, drop]
tab.rescan(silent=True)
wait_for_scan(tab, 6)
tab.remove_folder(drop)
wait_for_scan(tab, 5)
check("removing a music folder drops its tracks at once",
      tab.library.count() == 5 and len(tracks_in_tree(tab.tree)) == 5,
      (tab.library.count(), len(tracks_in_tree(tab.tree))))
check("removing a music folder updates the config", drop not in w.config["library_folders"])
# and removing the last folder empties the library instead of being ignored
tab.remove_folder(MUSIC)
wait_for_scan(tab, 0)
check("removing the last folder empties the library",
      tab.library.count() == 0 and len(tracks_in_tree(tab.tree)) == 0,
      (tab.library.count(), len(tracks_in_tree(tab.tree))))
check("the empty library has no folders left", w.config["library_folders"] == [])
w.config["library_folders"] = [MUSIC]
nebula.store_active_collection(w.config)
nebula.save_config(w.config)
tab.rescan()
wait_for_scan(tab, 5)
check("re-adding the folder scans it back", tab.library.count() == 5 and
      len(tracks_in_tree(tab.tree)) == 5, tab.library.count())

# ---------------------------------------------------------------- device music
section("devices tab: the music on a device")
dev = w.devices_tab
check("the Devices tab has no PC folder page and no file view left",
      not hasattr(dev, "folder_table") and not hasattr(dev, "folders_btn")
      and not hasattr(dev, "phones_btn"),
      [n for n in ("folder_table", "folders_btn", "phones_btn") if hasattr(dev, n)])

music_dev = tempfile.mkdtemp(prefix="devmusic-", dir=HOME)
dev_music = os.path.join(music_dev, "Music")
for rel, fixture in (("Aphex Twin/Selected Ambient Works/01 - Xtal.wav", WAV1),
                     ("Aphex Twin/Selected Ambient Works/02 - Tha.wav", WAV2),
                     ("Boards of Canada/Geogaddi/01 - Ready Lets Go.wav", WAV1)):
    full = os.path.join(dev_music, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    shutil.copyfile(fixture, full)
shutil.copyfile(WAV1, os.path.join(music_dev, "loose.wav"))
music_device = nebula.Device(id=f"mass:{music_dev}", name="Walkman", kind="mass",
                              root=music_dev)
DEV_XTAL = "Music/Aphex Twin/Selected Ambient Works/01 - Xtal.wav"
DEV_THA = "Music/Aphex Twin/Selected Ambient Works/02 - Tha.wav"
DEV_BOC = "Music/Boards of Canada/Geogaddi/01 - Ready Lets Go.wav"
dev.set_devices([music_device])
check("a device opens on its Music folder, remembered per device",
      dev.device_dir() == "Music" and w.config["device_dirs"][music_device.id] == "Music",
      (dev.device_dir(), w.config.get("device_dirs")))
check("the device folder is what is listed, not the PC library",
      len(dev.music) == 3 and all(not e["rel"].startswith("loose") for e in dev.music),
      [e["rel"] for e in dev.music])
first = dev.music[0]
check("artist, album, track and title come out of the folder layout",
      first["artist"] == "Aphex Twin" and first["album"] == "Selected Ambient Works"
      and first["track"] == 1 and first["title"] == "Xtal", first)
check("the list shows the artists, each with its albums under it",
      dev.tree.topLevelItemCount() == 2
      and [dev.tree.topLevelItem(i).text(0) for i in range(2)]
      == ["Aphex Twin", "Boards of Canada"]
      and dev.tree.topLevelItem(0).childCount() == 1
      and dev.tree.topLevelItem(0).child(0).text(0) == "Selected Ambient Works",
      [dev.tree.topLevelItem(i).text(0) for i in range(dev.tree.topLevelItemCount())])
check("the album opens to its tracks, numbered",
      dev.tree.topLevelItem(0).child(0).childCount() == 2
      and dev.tree.topLevelItem(0).child(0).child(0).text(0) == "01. Xtal",
      dev.tree.topLevelItem(0).child(0).child(0).text(0))
check("the list is the tree's titles with their sizes, and nothing else",
      dev.tree.columnCount() == 2
      and [dev.tree.headerItem().text(i) for i in range(2)] == ["Title", "Size"]
      and dev.tree.topLevelItem(0).text(1).endswith("B")
      and dev.tree.topLevelItem(0).child(0).text(1).endswith("B")
      and dev.tree.topLevelItem(0).child(0).text(1) != "Aphex Twin",
      ([dev.tree.headerItem().text(i) for i in range(dev.tree.columnCount())],
       dev.tree.topLevelItem(0).child(0).text(1)))
check("the covers grid has one cover per album, named and counted",
      dev.covers.count() == 2
      and dev.covers.item(0).text().split("\n")
      == ["Selected Ambient Works", "Aphex Twin", "2 tracks"]
      and dev.covers.item(1).text().split("\n")[0] == "Geogaddi",
      [dev.covers.item(i).text() for i in range(dev.covers.count())])
check("cover tiles leave room for a long album and artist instead of clipping them",
      dev.covers.gridSize().height() >= 260
      and not dev.covers.uniformItemSizes()
      and dev.covers.item(0).sizeHint().height() >= 240
      and dev.covers.wordWrap(),
      (dev.covers.gridSize().height(), dev.covers.uniformItemSizes(),
       dev.covers.item(0).sizeHint().height()))
check("the summary counts the tracks, albums and size",
      dev.summary.text().startswith("3 tracks") and "2 albums" in dev.summary.text(),
      dev.summary.text())
dev.set_music_view("covers")
check("the List / Covers switch reaches the grid and is remembered",
      dev.views.currentWidget() is dev.covers
      and w.config["devices_music_view"] == "covers"
      and dev.covers_btn.isChecked() and not dev.list_btn.isChecked())
dev.set_music_view("list")
check("and back to the list, which is remembered too",
      dev.views.currentWidget() is dev.tree and w.config["devices_music_view"] == "list")
check("the List / Covers switch sits under the search box, not in the folder row",
      dev.list_btn.parent() is dev.view_row and dev.covers_btn.parent() is dev.view_row
      and dev.list_btn.parent() is not dev.toolbar
      and dev.music_box.layout().indexOf(dev.view_row)
      > dev.music_box.layout().indexOf(dev.search_box),
      (dev.list_btn.parent().objectName(), dev.covers_btn.parent().objectName()))
check("device action buttons keep compact natural widths",
      all(b.sizePolicy().horizontalPolicy() == nebula.QSizePolicy.Fixed
          for b in (dev.play_btn, dev.refresh_btn, dev.dir_btn)),
      [(b.text(), b.sizePolicy().horizontalPolicy())
       for b in (dev.play_btn, dev.refresh_btn, dev.dir_btn)])
check("the empty cover grid carries no misleading album hint",
      dev.covers.toolTip() == "", dev.covers.toolTip())

dev.set_device_dir("")
check("choosing the whole device lists everything on it, root included",
      len(dev.music) == 4 and any(e["rel"] == "loose.wav" for e in dev.music),
      [e["rel"] for e in dev.music])
check("the chosen device folder is kept per device",
      w.config["device_dirs"][music_device.id] == "")
dev.set_device_dir("Music")
check("and going back to Music lists only that folder", len(dev.music) == 3)

# A synced file is shown with the tags of the PC file it came from: the sync manifest
# remembers the source of each device path, so the library can answer.
library_row = next(iter(dev._library_rows().values()))
probe_dev = nebula.Profile(name="Device tab probe", device_id=music_device.id,
                            source=os.path.dirname(library_row["path"]), target="Music")
nebula.save_profiles(nebula.load_profiles() + [probe_dev])
probe_manifest = nebula.DeviceManifest(probe_dev)
probe_manifest.record("Music/synced.wav", os.path.basename(library_row["path"]), 10,
                      "0" * 64, 0.0, probe_dev.id)
probe_manifest.save()
mapped = dev._sync_rows({"Music/synced.wav": (10, 0)}, "Music/")
check("the device tab finds the library row a device file came from",
      mapped.get("Music/synced.wav") is not None
      and mapped["Music/synced.wav"]["path"] == library_row["path"], mapped)
enriched = dev._entry("Aphex Twin/Elsewhere/01 - Wrong Name.wav", 10, library_row)
check("a synced track is shown with its library tags, not its file name",
      enriched["title"] == library_row["title"]
      and enriched["album"] == library_row["album"] and enriched["library"] is not None,
      enriched)
check("a file the library does not know falls back to its folder layout",
      dev._entry("Some Artist/Some Album/03 - Song.wav", 10)["title"] == "Song")
nebula.save_profiles([p for p in nebula.load_profiles() if p.id != probe_dev.id])
try:
    os.remove(probe_manifest.path)
except OSError:
    pass

# Double-clicking means what the library's double-click means, and it means the
# album from that track on — never the whole device.
seen = []
real_play = dev.play_paths
dev.play_paths = lambda paths, queue=False: seen.append((list(paths), queue))
try:
    album_item = dev.tree.topLevelItem(0).child(0)
    check("the library's double-click preference defaults to queueing",
          w.config.get("lib_double_click") == "queue", w.config.get("lib_double_click"))
    dev._tree_double(album_item.child(1))
    check("double-clicking a track queues its album from that track on",
          seen == [([DEV_THA], True)], seen)
    seen.clear()
    dev.config["lib_double_click"] = "play"
    dev._tree_double(album_item.child(0))
    check("and plays it when the preference says play",
          seen == [([DEV_XTAL, DEV_THA], False)], seen)
    dev.config["lib_double_click"] = "queue"
    seen.clear()
    dev._tree_double(dev.tree.topLevelItem(1))
    check("double-clicking an artist queues all of its tracks",
          seen and len(seen[0][0]) == 1 and seen[0][1] is True, seen)
finally:
    dev.play_paths = real_play

# ---------------------------------------------------------------- copy to device
section("copy to device: one window, folders, bitrate and progress")
copy_root = tempfile.mkdtemp(prefix="devcopy-", dir=HOME)
copy_device = nebula.Device(id=f"mass:{copy_root}", name="Copy Walkman", kind="mass",
                            root=copy_root)
copy_lib = tempfile.mkdtemp(prefix="copylib-", dir=HOME)
nested_src = os.path.join(copy_lib, "Christopher Larkin",
                          "Hollow Knight Silksong (Original Soundtrack)",
                          "33 - Cogwork Core.wav")
os.makedirs(os.path.dirname(nested_src), exist_ok=True)
shutil.copyfile(WAV1, nested_src)
loose_src = os.path.join(HOME, "loose-copy.wav")
shutil.copyfile(WAV2, loose_src)
copy_cfg = {"library_folders": [copy_lib], "device_dirs": {copy_device.id: "Music"}}
dlg = nebula.CopyToDeviceDialog([copy_device], copy_cfg, [nested_src, loose_src],
                                copy_device.id)
check("copy to device asks everything in one window, on the remembered folder",
      dlg.windowTitle() == "Copy to device" and dlg.folder.text() == "Music"
      and dlg.device.currentData() == copy_device.id
      and dlg.chosen_device() is copy_device)
check("a copy keeps the library folders by default, and shows where the file lands",
      dlg.keep_folders()
      and dlg.rel_for(nested_src)
      == "Christopher Larkin/Hollow Knight Silksong (Original Soundtrack)/33 - Cogwork Core.wav"
      and "Christopher Larkin/" in dlg.preview.text(),
      (dlg.rel_for(nested_src), dlg.preview.text()))
dlg.layout_mode.setCurrentIndex(dlg.layout_mode.findData(False))
check("track(s) only drops the folders and says so",
      dlg.rel_for(nested_src) == "33 - Cogwork Core.wav"
      and "Music/33 - Cogwork Core.wav" in dlg.preview.text(), dlg.preview.text())
check("a file outside every library folder keeps its name with folders on",
      nebula.library_rel(loose_src, [copy_lib]) == "loose-copy.wav")
check("force transcode is off until it is asked for",
      not dlg.codec.isEnabled() and not dlg.bitrate.isEnabled()
      and dlg.codec_key() == "" and dlg.transcode() is None)
dlg.force.setChecked(True)
check("force transcode offers a codec and its own bitrates",
      dlg.codec.isEnabled() and dlg.bitrate.isEnabled()
      and dlg.bitrate.itemText(dlg.bitrate.count() - 1) == "320 kbps (CBR)",
      [dlg.bitrate.itemText(i) for i in range(dlg.bitrate.count())])
for codec, start in (("mp3", ("vbr", 2)), ("m4a", ("cbr", 256)), ("opus", ("vbr", 128))):
    dlg.codec.setCurrentIndex(dlg.codec.findData(codec))
    check(f"{codec} starts on the same setting a sync profile uses",
          dlg.transcode() == start, (dlg.transcode(), start))
# the chosen bitrate reaches ffmpeg instead of the codec default
dlg.codec.setCurrentIndex(dlg.codec.findData("m4a"))
chosen = next(i for i in range(dlg.bitrate.count())
              if dlg.bitrate.itemData(i) == ("cbr", 320))
dlg.bitrate.setCurrentIndex(chosen)
check("the chosen bitrate is what the copy will encode at",
      dlg.codec_key() == "m4a" and dlg.transcode() == ("cbr", 320), dlg.transcode())
dlg.codec.setCurrentIndex(dlg.codec.findData("opus"))
check("Opus reaches 256 kbps in Copy to device",
      any(dlg.bitrate.itemData(i) == ("vbr", 256)
          for i in range(dlg.bitrate.count())),
      [dlg.bitrate.itemData(i) for i in range(dlg.bitrate.count())])

# A sync profile stores the codec and its bitrate separately. The old fixed setting is
# still the default, and the manifest uses the signature to notice a bitrate change.
check("a sync profile stores a codec and bitrate independently",
      nebula.Profile(transcode="m4a").transcode_choice() == ("cbr", 256)
      and nebula.Profile(transcode="mp3", transcode_mode="cbr",
                         transcode_quality=320).transcode_choice() == ("cbr", 320)
      and nebula.Profile(transcode="opus", transcode_mode="vbr",
                         transcode_quality=256).transcode_choice() == ("vbr", 256),
      (nebula.Profile(transcode="m4a").transcode_choice(),
       nebula.Profile(transcode="mp3", transcode_mode="cbr",
                      transcode_quality=320).transcode_choice()))
check("a bitrate change changes the transcode manifest signature",
      nebula.Profile(transcode="mp3", transcode_mode="cbr",
                     transcode_quality=128).transcode_signature()
      != nebula.Profile(transcode="mp3", transcode_mode="cbr",
                        transcode_quality=320).transcode_signature())

enc_calls = []
real_run = nebula.subprocess.run


class _Encoded:
    returncode = 0
    stderr = ""


def _fake_ffmpeg(cmd, **_kwargs):
    enc_calls.append(cmd)
    with open(cmd[-1], "wb"):
        pass
    return _Encoded()


nebula.subprocess.run = _fake_ffmpeg
try:
    nebula.transcode_for_device(nested_src, "mp3", copy_root, "cbr", 192)
    nebula.transcode_for_device(nested_src, "m4a", copy_root, "cbr", 320)
    nebula.transcode_for_device(nested_src, "opus", copy_root, "vbr", 160)
    nebula.transcode_for_device(nested_src, "mp3", copy_root)
finally:
    nebula.subprocess.run = real_run
mp3_call, m4a_call, opus_call, default_call = enc_calls
check("MP3 CBR writes the chosen bitrate",
      mp3_call[mp3_call.index("-b:a") + 1] == "192k" and "-q:a" not in mp3_call)
check("AAC CBR writes the chosen bitrate", m4a_call[m4a_call.index("-b:a") + 1] == "320k")
check("Opus VBR writes the chosen target bitrate",
      opus_call[opus_call.index("-b:a") + 1] == "160k"
      and opus_call[opus_call.index("-vbr") + 1] == "on")
check("a transcode with no setting keeps the codec default",
      default_call[default_call.index("-q:a") + 1] == "2")

# a copy writes through the folders it is given, and reports its bytes
seen_bytes = []
nebula.Backend(copy_device).copy_in(
    nested_src, "Walkman_SD/Music/Christopher Larkin/Hollow Knight Silksong "
                "(Original Soundtrack)/33 - Cogwork Core.wav", progress=seen_bytes.append)
check("a copy into nested folders lands there and reports its bytes",
      seen_bytes and seen_bytes[-1] == 1.0
      and os.path.isfile(os.path.join(copy_root, "Walkman_SD", "Music", "Christopher Larkin",
                                      "Hollow Knight Silksong (Original Soundtrack)",
                                      "33 - Cogwork Core.wav")),
      seen_bytes)

# the badge in the tab bar's top-right corner shows the copy percentage
seen_badge = []
dev.activity.connect(seen_badge.append)
dev._activity_prefix = "Copying files to Walkman"
dev._run_progress(30, 100)
check("the badge at the top right reads the copy percentage",
      seen_badge[-1:] == ["Copying files to Walkman 30%"]
      and w.sync_activity.label.text() == "Copying files to Walkman 30%",
      (seen_badge, w.sync_activity.label.text()))
dev._activity_prefix = ""
dev.activity.emit("")
check("the badge is empty again when no copy runs", w.sync_activity.label.text() == "")
dlg.close()

# The manual path, end to end: a copy to a phone that is still charging waits, says so,
# and finishes on its own once the storage appears.
copy_wait_root = tempfile.mkdtemp(prefix="copywait-", dir=HOME)
copy_wait_device = nebula.Device(id="mtp:copywait", name="Waiting Walkman", kind="mtp",
                                 root=copy_wait_root, uri="mtp://copywait/")
wait_tab = nebula.DevicesTab(w.player, {"library_folders": [copy_lib]}, w.library)
wait_tab.devices = [copy_wait_device]
wait_tab.backend = nebula.Backend(copy_wait_device)
wait_badges = []
wait_tab.activity.connect(wait_badges.append)
wait_tab.upload([(nested_src, "33 - Cogwork Core.wav")], "Music")
for _ in range(300):
    app.processEvents()
    QTest.qWait(10)
    if "Waiting for" in wait_tab.sync_title.text():
        break
check("a manual copy to a charging phone waits instead of failing",
      "Waiting for Waiting Walkman" in wait_tab.sync_title.text()
      and not wait_tab.busy.isHidden(),
      (wait_tab.sync_title.text(), wait_tab.busy.isVisible()))
os.makedirs(os.path.join(copy_wait_root, "Walkman_SD", "Music"))
for _ in range(1000):
    app.processEvents()
    QTest.qWait(10)
    worker = getattr(wait_tab, "_worker", None)
    if worker is None or not worker.isRunning():
        break
app.processEvents()
copied_wait = os.path.join(copy_wait_root, "Walkman_SD", "Music",
                           "33 - Cogwork Core.wav")
check("once the phone answers, the waiting copy finishes on its own",
      os.path.isfile(copied_wait), sorted(os.walk(copy_wait_root)))
check("the top-right badge said it was waiting for file transfer",
      any("Waiting for Waiting Walkman" in line for line in wait_badges),
      wait_badges[-4:])
wait_tab.shutdown()
for _ in range(200):
    app.processEvents()
    QTest.qWait(10)
    if not wait_tab.is_loading():
        break

# ---------------------------------------------------------------- device search
section("devices tab: searching the device's music")

check("the view has a search box in the library's shape, and a filter hint",
      dev.search.parent().objectName() == "SearchBox"
      and dev.search.placeholderText()
      and dev.filter_hint.text().startswith("field:value filters"),
      (dev.search.parent().objectName(), dev.filter_hint.text()))

reloads = []
real_reload = dev.reload
dev.reload = lambda: reloads.append(1)
try:
    dev.search.setText("artist:aphex")
finally:
    dev.reload = real_reload
check("typing filters what is already read, it does not read the device again",
      not reloads, reloads)
check("artist: narrows the list and the covers to that artist",
      [i for i, _e in dev._visible()] == [0, 1] and dev.covers.count() == 1
      and [dev.tree.topLevelItem(i).text(0)
           for i in range(dev.tree.topLevelItemCount())] == ["Aphex Twin"],
      ([e["rel"] for _i, e in dev._visible()], dev.covers.count(),
       [dev.tree.topLevelItem(i).text(0) for i in range(dev.tree.topLevelItemCount())]))
check("the hint counts the matches and the summary keeps the device total",
      dev.filter_hint.text().startswith("2 matches")
      and dev.summary.text().startswith("2 tracks") and "3 on the device" in dev.summary.text(),
      (dev.filter_hint.text(), dev.summary.text()))
dev.search.setText('album:"Selected Ambient Works"')
check("a quoted album: value matches across spaces", len(dev._visible()) == 2)
dev.search.setText("track:>=2")
check("numeric terms compare (track:>=2)",
      [e["rel"] for _i, e in dev._visible()]
      == ["Aphex Twin/Selected Ambient Works/02 - Tha.wav"],
      [e["rel"] for _i, e in dev._visible()])
dev.search.setText("size:>0")
check("size: compares against the file size", len(dev._visible()) == 3)
dev.search.setText("-artist:aphex")
check("- excludes instead of matching",
      [e["rel"] for _i, e in dev._visible()]
      == ["Boards of Canada/Geogaddi/01 - Ready Lets Go.wav"],
      [e["rel"] for _i, e in dev._visible()])
dev.search.setText("geogaddi")
check("a bare word is a plain search of the path and tags", len(dev._visible()) == 1,
      [e["rel"] for _i, e in dev._visible()])
dev.search.setText('artist:"unclosed')
check("a query that will not parse says so and falls back to a plain search",
      dev._query_error == "unbalanced quote"
      and dev.filter_hint.objectName() == "Amber"
      and dev.filter_hint.text().startswith("Filter error"),
      (dev._query_error, dev.filter_hint.objectName(), dev.filter_hint.text()))
dev.search.setText("")
check("clearing the search brings the whole device back",
      len(dev._visible()) == 3 and dev.summary.text().startswith("3 tracks")
      and dev.filter_hint.objectName() == "Muted"
      and dev.filter_hint.text().startswith("field:value filters"),
      (len(dev._visible()), dev.summary.text(), dev.filter_hint.objectName()))

# Play and Queue act on what is shown, so a filtered device can be played or queued
# without selecting row by row.
seen = []
dev.play_paths = lambda paths, queue=False: seen.append((list(paths), queue))
try:
    dev.search.setText("artist:aphex")
    dev.queue_all()
    check("queuing adds what the filter shows, without starting it",
          seen == [([DEV_XTAL, DEV_THA], True)], seen)
    seen.clear()
    dev.play_all()
    check("Play starts what the filter shows",
          seen and len(seen[0][0]) == 2 and seen[0][1] is False, seen)
finally:
    dev.play_paths = real_play
dev.search.setText("")

# ---------------------------------------------------------------- device albums
section("devices tab: opening an album from the covers")
dev.set_music_view("covers")
dev._covers_click(dev.covers.item(0))
check("a click on a cover arms the album instead of switching at once",
      dev._album_focus is None and dev.views.currentWidget() is dev.covers,
      (dev._album_focus, dev.views.currentWidget() is dev.covers))
QTest.qWait(nebula.QApplication.doubleClickInterval() + 80)
app.processEvents()
check("the click then opens the album",
      dev._album_focus is not None and not dev.album_bar.isHidden()
      and dev.album_title.text() == "Selected Ambient Works"
      and dev.views.currentWidget() is dev.tree
      and dev.list_btn.isChecked() and not dev.covers_btn.isChecked(),
      (dev._album_focus, dev.album_bar.isHidden(), dev.album_title.text(),
       dev.views.currentWidget() is dev.tree))
check("the opened album lists only its own tracks",
      dev.tree.topLevelItemCount() == 1
      and dev.tree.topLevelItem(0).text(0) == "Aphex Twin"
      and dev.tree.topLevelItem(0).child(0).childCount() == 2,
      [dev.tree.topLevelItem(i).text(0)
       for i in range(dev.tree.topLevelItemCount())])
check("the album's tracks stay playable while it is open",
      dev.tree.topLevelItem(0).child(0).child(0).data(0, nebula.INDEX_ROLE) is not None)
dev.search.setText("tha")
check("search still works inside an opened album",
      len(dev._visible()) == 1, [e["rel"] for _i, e in dev._visible()])
dev.search.setText("")
dev.album_back.click()
check("the bar's back button returns to the covers with the album closed",
      dev._album_focus is None and dev.album_bar.isHidden()
      and dev.views.currentWidget() is dev.covers and dev.covers_btn.isChecked(),
      (dev._album_focus, dev.album_bar.isHidden(), dev.covers_btn.isChecked()))

seen.clear()
dev.play_paths = lambda paths, queue=False: seen.append((list(paths), queue))
try:
    dev._covers_click(dev.covers.item(0))
    dev._cover_double(dev.covers.item(0))
    check("double-clicking a cover queues the album and never opens it",
          seen == [([DEV_XTAL, DEV_THA], True)]
          and dev._album_focus is None and not dev._cover_click_timer.isActive(),
          (seen, dev._album_focus))
finally:
    dev.play_paths = real_play
dev.set_music_view("list")

# A context menu over several rows means all of them: the tree allows a multi-selection.
dev.tree.clearSelection()
dev.tree.topLevelItem(0).child(0).setSelected(True)
dev.tree.topLevelItem(1).setSelected(True)
check("the context menu acts on the whole selection",
      dev._menu_indexes(dev.tree.topLevelItem(0).child(0)) == [0, 1, 2],
      dev._menu_indexes(dev.tree.topLevelItem(0).child(0)))
dev.tree.clearSelection()
check("and on one row when only one is selected",
      dev._menu_indexes(dev.tree.topLevelItem(0)) == [0, 1],
      dev._menu_indexes(dev.tree.topLevelItem(0)))

# ---------------------------------------------------------------- device queue
section("devices tab: device music in the library's queue")
check("there is no bulk Queue button any more", not hasattr(dev, "queue_btn"))
check("the rows point at files that really exist on the device",
      all(os.path.isfile(dev.backend.local(p)) for p in dev._paths([0, 1, 2])),
      [dev.backend.local(p) for p in dev._paths([0, 1, 2])])
check("and the paths carry the folder the device is showing",
      dev._paths([0, 1, 2]) == [DEV_XTAL, DEV_THA, DEV_BOC], dev._paths([0, 1, 2]))

# A device track is queued as the file on the device, tagged with where it came from.
queue_dev = nebula.Profile(name="Device queue probe", device_id=music_device.id,
                            source=os.path.dirname(library_row["path"]), target="Music")
nebula.save_profiles(nebula.load_profiles() + [queue_dev])
queue_manifest = nebula.DeviceManifest(queue_dev)


def wait_device_buffer(path, seconds=10):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        QTest.qWait(20)
        if nebula.DEVICE_BUFFER.cached(path):
            return nebula.DEVICE_BUFFER.cached(path)
    return nebula.DEVICE_BUFFER.cached(path)


saved_queue, saved_index = list(w.player.queue), w.player.index
try:
    queue_manifest.record(DEV_XTAL, os.path.basename(library_row["path"]),
                          os.path.getsize(library_row["path"]), "0" * 64, 0.0,
                          queue_dev.id)
    queue_manifest.save()
    check("a synced device track maps back to its PC file",
          dev._library_map().get(DEV_XTAL) == library_row["path"], dev._library_map())

    start_index = w.player.index
    dev.play_paths([DEV_XTAL], queue=True)
    app.processEvents()
    device_path = dev.backend.local(DEV_XTAL)
    check("queueing it keeps the file on the device, not a PC copy",
          w.player.queue[-1:] == [device_path], w.player.queue[-3:])
    check("and it does not start the queue by itself",
          w.player.index == start_index, (start_index, w.player.index))
    info = nebula.DEVICE_QUEUE.get(device_path) or {}
    check("the queue entry says which device it came from",
          info.get("source") == "USB device" and info.get("device_id") == music_device.id,
          info)
    check("and the queue row has its own tags, read without a PC copy",
          info.get("meta", {}).get("title") == "Alpha", info.get("meta"))
    last = tab.table.rowCount() - 1
    check("the library queue says the source is the device",
          tab.table.item(last, 8).text() == "USB device"
          and tab.table.item(last, 1).text() == "Alpha",
          (tab.table.item(last, 8).text(), tab.table.item(last, 1).text()))

    # The device buffer copies the track ahead of playback, independently of its tags.
    cached = wait_device_buffer(device_path)
    check("the device buffer makes a local copy of the queued track",
          bool(cached) and os.path.isfile(cached)
          and cached.startswith(nebula.DEVICE_BUFFER_DIR), cached)
    with open(cached, "rb") as fh_cached, open(device_path, "rb") as fh_device:
        check("and the copy is byte-identical to the device file",
              fh_cached.read() == fh_device.read(), (cached, device_path))

    played = []
    real_set_source, real_play = w.player.player.setSource, w.player.player.play
    w.player.player.setSource = lambda url: played.append(url.toString())
    w.player.player.play = lambda: None
    try:
        w.player.play_index(len(w.player.queue) - 1)
    finally:
        w.player.player.setSource, w.player.player.play = real_set_source, real_play
        w.player.stop()
    check("playing it uses the buffered copy rather than the slow device read",
          played[-1:] == [QUrl.fromLocalFile(cached).toString()], played[-1:])

    # A file only the device holds keeps its own tags, title and format.
    dev.play_paths([DEV_THA], queue=True)
    app.processEvents()
    device_beta = dev.backend.local(DEV_THA)
    check("a file only the device holds is also queued from the device",
          w.player.queue[-1:] == [device_beta], w.player.queue[-3:])
    last = tab.table.rowCount() - 1
    check("so the queue shows its title, length, format and source",
          tab.table.item(last, 1).text() == "Beta"
          and tab.table.item(last, 4).text() != "0:00"
          and tab.table.item(last, 8).text() == "USB device"
          and tab.table.item(last, 9).text() == "WAV",
          (tab.table.item(last, 1).text(), tab.table.item(last, 4).text(),
           tab.table.item(last, 8).text(), tab.table.item(last, 9).text()))
    check("the queue tags are saved for the next launch",
          os.path.isfile(nebula.QUEUE_META_FILE), nebula.QUEUE_META_FILE)

    # A queue restored at the next launch comes back with the device source intact.
    nebula.DEVICE_QUEUE.clear()
    nebula.restore_device_queue_entries([device_path, device_beta])
    check("a restored device queue still says where its tracks came from",
          nebula.is_device_entry(device_path)
          and nebula.is_device_entry(device_beta)
          and nebula.device_entry_info(device_path).get("source") == "USB device",
          (nebula.is_device_entry(device_path), nebula.is_device_entry(device_beta),
           nebula.device_entry_info(device_path)))
finally:
    w.player.set_queue(saved_queue, saved_index if saved_queue else -1, play=False)
    nebula.DEVICE_BUFFER.forget()
    nebula.DEVICE_QUEUE.clear()
    nebula.save_profiles([p for p in nebula.load_profiles() if p.id != queue_dev.id])
    try:
        os.remove(queue_manifest.path)
    except OSError:
        pass

def drain_device_worker():
    for _ in range(600):
        app.processEvents()
        QTest.qWait(10)
        if not getattr(dev, "_worker", None) or not dev._worker.isRunning():
            break
    app.processEvents()
    QTest.qWait(50)
    app.processEvents()


# ---------------------------------------------------------------- copy to library
section("devices tab: copying the device's music into the library")

# The context menu offers Copy to library beside the actions it already had, and it
# names how many tracks it applies to.
row_labels = [label for label, _slot in dev.row_menu_actions([0, 1, 2]) if label]
check("the row menu offers Copy 3 tracks to library",
      "Copy 3 tracks to library" in row_labels, row_labels)
check("and keeps the queue it already had",
      "Add 3 tracks to queue" in row_labels and "Play 3 tracks" in row_labels, row_labels)
album_labels = [label for label, _slot in dev.album_menu_actions([0, 1], "Album") if label]
check("the cover menu offers Copy album to library",
      "Copy album to library" in album_labels and "Add to queue" in album_labels,
      album_labels)
check("the empty-area menu is unchanged",
      [label for label, _slot in dev.empty_menu_actions() if label]
      == ["Play everything", "Add everything to queue", "Select device folder…", "Refresh"],
      [label for label, _slot in dev.empty_menu_actions() if label])

copy_dir = tempfile.mkdtemp(prefix="devcopy-", dir=HOME)
w.config["library_folders"] = [copy_dir, MUSIC]
before = tab.library.count()
try:
    dev.copy_to_library([DEV_XTAL])
    drain_device_worker()
    copied = os.path.join(copy_dir, "Aphex Twin", "Selected Ambient Works", "01 - Xtal.wav")
    check("copying a device track puts it in the library, names and folders unchanged",
          os.path.isfile(copied), os.listdir(copy_dir))
    check("and the library shows it at once, without a full rescan",
          tab.library.count() == before + 1, (before, tab.library.count()))
    check("the device keeps its own file", os.path.isfile(dev.backend.local(DEV_XTAL)))

    dev.copy_to_library([DEV_XTAL])
    drain_device_worker()
    check("copying the same track again does not make a second copy",
          sorted(os.listdir(os.path.dirname(copied))) == ["01 - Xtal.wav"]
          and tab.library.count() == before + 1,
          sorted(os.listdir(os.path.dirname(copied))))

    other = os.path.join(copy_dir, "Aphex Twin", "Selected Ambient Works", "02 - Tha.wav")
    marker = b"a different file with that name"
    with open(other, "wb") as fh:
        fh.write(marker)
    dev.copy_to_library([DEV_THA])
    drain_device_worker()
    numbered = os.path.join(copy_dir, "Aphex Twin", "Selected Ambient Works",
                            "02 - Tha (2).wav")
    check("a different file using the name is kept, and the copy is numbered",
          os.path.isfile(numbered) and os.path.getsize(other) == len(marker),
          sorted(os.listdir(os.path.dirname(copied))))

    # A track the sync manifest says the library already has is not copied again.
    copy_dev = nebula.Profile(name="Copy probe", device_id=music_device.id,
                               source=os.path.dirname(library_row["path"]), target="Music")
    nebula.save_profiles(nebula.load_profiles() + [copy_dev])
    copy_manifest = nebula.DeviceManifest(copy_dev)
    try:
        copy_manifest.record(DEV_BOC, os.path.basename(library_row["path"]),
                             os.path.getsize(library_row["path"]), "0" * 64, 0.0,
                             copy_dev.id)
        copy_manifest.save()
        dev.copy_to_library([DEV_BOC])
        drain_device_worker()
        check("a track the library already holds is not copied again",
              not os.path.exists(os.path.join(copy_dir, "Boards of Canada")),
              os.listdir(copy_dir))
    finally:
        nebula.save_profiles([p for p in nebula.load_profiles() if p.id != copy_dev.id])
        try:
            os.remove(copy_manifest.path)
        except OSError:
            pass
finally:
    w.config["library_folders"] = [MUSIC]
    shutil.rmtree(copy_dir, ignore_errors=True)
    tab.rescan(silent=True)
    wait_for_scan(tab, 5)
check("removing the copy folder takes its tracks back out of the library",
      tab.library.count() == 5, tab.library.count())

check("a phone is labelled MTP and a stick USB",
      nebula.device_label(nebula.Device(id="a", name="Walkman", kind="mtp", root="/x"))
      == "MTP · Walkman"
      and nebula.device_label(nebula.Device(id="b", name="Stick", kind="mass", root="/y"))
      == "USB · Stick")

# ---------------------------------------------------------------- device bar
section("devices tab: the device bar and the sidebar")
stick_root = tempfile.mkdtemp(prefix="devbar-", dir=HOME)
phone_root = tempfile.mkdtemp(prefix="devbarphone-", dir=HOME)
os.makedirs(os.path.join(stick_root, "Music"), exist_ok=True)
# a fresh device list for this section: earlier sections remembered their own devices
w.config["device_registry"] = []
w.config["device_names"] = {}
dev._current_id = None
nebula.save_config(w.config)
dev.set_devices([])
fakes = [nebula.Device(id=f"mass:{stick_root}", name="Stick", kind="mass", root=stick_root),
         nebula.Device(id=f"mass:{phone_root}", name="Phone (USB)", kind="mass",
                        root=phone_root)]
dev.set_devices(fakes)
check("the top bar lists every device by name",
      [b.device_name for b in dev._device_buttons] == ["Stick", "Phone (USB)"],
      [b.device_name for b in dev._device_buttons])
check("the sidebar list is filled from the same devices",
      [dev.dev_list.item(i).text() for i in range(dev.dev_list.count())]
      == ["Stick", "Phone (USB)"],
      [dev.dev_list.item(i).text() for i in range(dev.dev_list.count())])
check("both views say a plugged-in device is connected",
      all(b.connected for b in dev._device_buttons)
      and [dev.dev_list.item(i).data(nebula.DEVICE_STATUS_ROLE)
           for i in range(dev.dev_list.count())] == ["connected", "connected"],
      [(b.device_name, b.connected) for b in dev._device_buttons])
check("the first device opens on arrival",
      dev.dev_list.currentRow() == 0 and dev.backend is not None
      and dev.backend.device.name == "Stick",
      dev.dev_list.currentRow())
check("queue sources name the device kind (MTP, iPod, USB)",
      nebula.device_source_label(nebula.Device(id="mtp:x", name="Phone", kind="mtp",
                                                 root="/x")) == "MTP device"
      and nebula.device_source_label(nebula.Device(id="mass:y", name="iPod Classic",
                                                     kind="mass", root="/x")) == "iPod"
      and nebula.device_source_label(nebula.Device(id="mass:z", name="Stick", kind="mass",
                                                     root="/x")) == "USB device",
      [nebula.device_source_label(d) for d in (
          nebula.Device(id="mtp:x", name="Phone", kind="mtp", root="/x"),
          nebula.Device(id="mass:y", name="iPod Classic", kind="mass", root="/x"),
          nebula.Device(id="mass:z", name="Stick", kind="mass", root="/x"))])
dev._device_buttons[1].click()
check("clicking a device in the bar selects it, and the list agrees",
      dev.dev_list.currentRow() == 1 and dev.backend.device.name == "Phone (USB)"
      and dev._device_buttons[1].isChecked() and not dev._device_buttons[0].isChecked(),
      (dev.dev_list.currentRow(), dev.backend.device.name if dev.backend else None))


def count_colour(pixmap, colour, slack=30):
    """Pixels of a grabbed widget that are the given colour (a dot drawn in it)."""
    image = pixmap.toImage()
    want = QColor(colour)
    total = 0
    for y in range(image.height()):
        for x in range(image.width()):
            c = image.pixelColor(x, y)
            if (c.alpha() > 100 and abs(c.red() - want.red()) < slack
                    and abs(c.green() - want.green()) < slack
                    and abs(c.blue() - want.blue()) < slack):
                total += 1
    return total


check("a connected device is drawn with a green dot",
      count_colour(dev._device_buttons[1].grab(), nebula.DEVICE_DOT_ON) > 10,
      count_colour(dev._device_buttons[1].grab(), nebula.DEVICE_DOT_ON))

# a nickname is what the bar and the sidebar show, and both it and the device are kept
w.config["device_names"] = {fakes[0].id: "NW-A306"}
nebula.save_config(w.config)
dev._render_devices()
check("a nickname replaces the device's own name in the bar and the sidebar",
      [b.device_name for b in dev._device_buttons] == ["NW-A306", "Phone (USB)"]
      and [dev.dev_list.item(i).text() for i in range(dev.dev_list.count())]
      == ["NW-A306", "Phone (USB)"],
      ([b.device_name for b in dev._device_buttons],
       [dev.dev_list.item(i).text() for i in range(dev.dev_list.count())]))
saved_devices = nebula.load_config()
check("devices and nicknames are remembered for the next launch",
      {r["id"] for r in saved_devices.get("device_registry", [])} >= {f.id for f in fakes}
      and saved_devices.get("device_names", {}).get(fakes[0].id) == "NW-A306",
      (saved_devices.get("device_registry"), saved_devices.get("device_names")))

# unplugging keeps the row (and its name) in both views, marked with a grey dot
dev.set_devices([fakes[1]])
check("an unplugged device keeps its row and its nickname, marked not connected",
      len(dev.rows) == 2 and [r["name"] for r in dev.rows] == ["NW-A306", "Phone (USB)"]
      and dev.rows[0]["connected"] is False
      and dev.dev_list.item(0).data(nebula.DEVICE_STATUS_ROLE) == "not connected"
      and dev.dev_list.item(1).data(nebula.DEVICE_STATUS_ROLE) == "connected",
      [(r["name"], r["connected"]) for r in dev.rows])
check("an unplugged device is drawn with a grey dot",
      count_colour(dev._device_buttons[0].grab(), nebula.DEVICE_DOT_OFF) > 10,
      count_colour(dev._device_buttons[0].grab(), nebula.DEVICE_DOT_OFF))
dev._select_index(0)
check("selecting an unplugged device shows no music and makes no false disconnect claim",
      dev.backend is None and not dev.music and dev.tree.topLevelItemCount() == 0
      and dev.covers.count() == 0 and "not connected" in dev.info.text()
      and "disconnected" not in dev.info.text().lower(),
      (dev.backend, len(dev.music), dev.info.text()))
dev.set_devices(fakes)
check("the top bar is the default layout",
      w.config["devices_layout"] == "bar"
      and dev.layout_stack.currentWidget() is dev.bar_container,
      w.config.get("devices_layout"))
dev.apply_layout("side")
check("the side layout puts the devices down the left",
      dev.layout_stack.currentWidget() is dev.side_container
      and w.config["devices_layout"] == "side"
      and dev.dev_side.parent() is dev.side_container and not dev.dev_side.isHidden())
check("the browser moves into the side frame with it",
      dev.music_box.parent() is dev.side_container)
dev.apply_layout("bar")
check("the bar layout puts them across the top",
      dev.layout_stack.currentWidget() is dev.bar_container
      and w.config["devices_layout"] == "bar"
      and dev.dev_bar.parent() is dev.bar_container and not dev.dev_bar.isHidden()
      and dev.music_box.parent() is dev.bar_container)

prefs_dev = nebula.PreferencesDialog(tab, w)
dev_combo = prefs_dev.widgets["devices_layout"]
check("Preferences offers both device layouts",
      [dev_combo.itemData(i) for i in range(dev_combo.count())] == ["bar", "side"],
      [dev_combo.itemText(i) for i in range(dev_combo.count())])
dev_combo.setCurrentIndex(dev_combo.findData("side"))
prefs_dev._ok()
check("Preferences saves the device layout and applies it at once",
      w.config["devices_layout"] == "side"
      and dev.layout_stack.currentWidget() is dev.side_container,
      w.config.get("devices_layout"))
prefs_dev.close()
dev.apply_layout("bar")

aphex_node = find_item(tab.tree, "Aphex Twin")
check("artist nodes show the full artist name", aphex_node is not None)
album_node = find_item(tab.tree, "Selected Ambient Works")
check("album nodes show the full album name", album_node is not None,
      [tab._node_label(i) for i in all_items(tab.tree)][:12])
alpha_item = next((i for i in tracks_in_tree(tab.tree)
                   if i.data(0, nebula.PATH_ROLE) == WAV1), None)
check("track rows read '%track#% %title%'",
      alpha_item is not None and alpha_item.text(0) == "01. Alpha",
      alpha_item.text(0) if alpha_item else "missing")
check("track rows sit under their album",
      alpha_item is not None and alpha_item.parent() is album_node)
probe = nebula.LibraryTree()
probe.setHeaderHidden(True)
probe.setIndentation(18)
probe_root = nebula.QTreeWidgetItem(probe, ["Bob Dylan"])
nebula.QTreeWidgetItem(probe_root, ["01. Blowin' in the Wind"])
probe.resize(240, 70)
probe.show()
app.processEvents()
probe_pix = probe.grab().toImage()
probe_rect = probe.visualItemRect(probe_root)
bright = sum(1 for x in range(max(0, probe_rect.left() - 18), probe_rect.left())
             for y in range(probe_rect.top(), probe_rect.bottom() + 1)
             if max(probe_pix.pixelColor(x, y).red(),
                    probe_pix.pixelColor(x, y).green(),
                    probe_pix.pixelColor(x, y).blue()) > 120)
check("collapsed artist rows show a visible expander triangle", bright >= 6, bright)
probe.close()
top_level = [tab.tree.topLevelItem(i) for i in range(tab.tree.topLevelItemCount())]
check("letter headers are the top level, flush left",
      bool(top_level) and all(i.data(0, nebula.KIND_ROLE) == "divider"
                              for i in top_level),
      [tab._node_label(i) for i in top_level])
a_section = find_item(tab.tree, "A")
check("artists nest under their letter",
      a_section is not None and a_section.childCount() > 0
      and a_section.child(0).data(0, nebula.KIND_ROLE) == "artist",
      a_section.childCount() if a_section else "missing")
check("search box has the clear and wrench controls",
      tab.search.parent().objectName() == "SearchBox"
      and tab.search_clear.text() == "✕" and tab.wrench.menu() is not None)
check("clear button starts hidden", tab.search_clear.isHidden())
tab.search.setText("x")
check("clear button appears with text", not tab.search_clear.isHidden())
tab.search_clear.click()
check("clear button empties the search", tab.search.text() == "")

for key, _label in nebula.GROUPINGS:
    tab.grouping.setCurrentIndex(tab.grouping.findData(key))
    tab.refresh()
    check(f"grouping '{key}' builds a tree", len(tracks_in_tree(tab.tree)) == 5,
          len(tracks_in_tree(tab.tree)))
tab.grouping.setCurrentIndex(tab.grouping.findData("artist_album"))
tab.refresh()
check("compilations grouped as Various Artists", find_item(tab.tree, "Various Artists") is not None)

tab.search.setText("Gamma")
tab.refresh()
check("search filters the tree", len(tracks_in_tree(tab.tree)) == 1)
tab.search.setText("")
tab.refresh()

tab.player.clear_queue()
tab.tree.expandAll()
app.processEvents()
alpha_item = next(i for i in tracks_in_tree(tab.tree) if i.data(0, nebula.PATH_ROLE) == WAV1)
rect = tab.tree.visualItemRect(alpha_item)
QTest.mouseClick(tab.tree.viewport(), Qt.LeftButton, Qt.NoModifier, rect.center())
check("single click on a library track queues nothing", tab.player.queue == [], tab.player.queue)
double_click(tab.tree, rect.center())
check("real double-click queues exactly one track", tab.player.queue == [WAV1], tab.player.queue)
tab.player.clear_queue()
tab._tree_double(alpha_item, 0)
check("double-click adds exactly that one track", tab.player.queue == [WAV1], tab.player.queue)
tab._tree_double(alpha_item, 0)
check("double-click again queues it twice", tab.player.queue == [WAV1, WAV1])
album_item = find_item(tab.tree, "Selected Ambient Works")
tab._tree_double(album_item, 0)
check("double-clicking an album adds its tracks", len(tab.player.queue) == 4, tab.player.queue)
check("queue table mirrors the player queue", tab.table.rowCount() == 4)
check("queue has the ten Strawberry columns",
      [tab.table.horizontalHeaderItem(i).text() for i in range(tab.table.columnCount())]
      == nebula.QUEUE_COLS)
check("queue shows real sample rate", tab.table.item(2, 5).text() == "44100 Hz",
      tab.table.item(2, 5).text())
check("queue shows bit depth or dash", tab.table.item(2, 6).text() == "16 Bit")
check("queue shows file type", tab.table.item(2, 9).text() == "WAV")
check("queue status strip", "4 tracks" in tab.queue_status.text(), tab.queue_status.text())

tab.undo()
check("undo removes the album add", len(tab.player.queue) == 2, tab.player.queue)
tab.redo()
check("redo restores it", len(tab.player.queue) == 4)

tab.player.set_queue([WAV1, WAV2, FLAC1])
tab._move_row(0, 2)
check("drag-reorder moves the row", tab.player.queue == [WAV2, FLAC1, WAV1], tab.player.queue)
tab.table.selectRow(0)
tab.remove_selected()
check("remove selected queue row", tab.player.queue == [FLAC1, WAV1], tab.player.queue)

tab.player.set_queue([WAV2, WAV1, FLAC1], 1)
tab.player._stopped = False       # this check is about sorting while a track is current
tab._sort_queue(4)
check("header click sorts by length ascending",
      tab.player.queue == [FLAC1, WAV1, WAV2], tab.player.queue)
check("sorting keeps the playing track selected", tab.player.current_path() == WAV1)
tab._sort_queue(4)
check("clicking again sorts descending", tab.player.queue == [WAV2, WAV1, FLAC1], tab.player.queue)

tab.player.set_queue([WAV1, FLAC1])
tab.current_playlist = "Queue snapshot"
tab.save_playlist()
check("save queue as playlist", playlists.read("Queue snapshot") == [WAV1, FLAC1])
tab.player.clear_queue()
tab.open_playlist("Queue snapshot")
check("open playlist loads the queue", tab.player.queue == [WAV1, FLAC1], tab.player.queue)

tab.reload_smart()
check("smart list shows presets plus custom", tab.smart_list.count() == 7, tab.smart_list.count())
dialog = nebula.SmartPlaylistDialog(tab, {"name": "Unplayed pop", "match": "all",
                                           "rules": [{"field": "genre", "op": "is", "value": "Pop"}]})
result = dialog.result_item()
check("rule builder dialog round-trips a rule",
      result["name"] == "Unplayed pop" and result["rules"][0]["value"] == "Pop", result)
dialog.close()

w.player.set_queue([FLAC1])
w.player._load_info(FLAC1)
pills = [w.player.pills_layout.itemAt(i).widget().text()
         for i in range(w.player.pills_layout.count())
         if w.player.pills_layout.itemAt(i).widget()]
check("player bar shows format pills",
      pills == nebula.spec_parts(nebula.read_specs(FLAC1)) and pills[0] == "FLAC"
      and pills[1] == "24-bit / 96.0 kHz", pills)
check("player bar states title and album", w.player.now_title.text() == "Gamma"
      and "Music Has the Right" in w.player.now_sub.text(),
      (w.player.now_title.text(), w.player.now_sub.text()))

# ---------------------------------------------------------------- device loading
section("devices tab: reading the device library")


def wait_for_device_scan(tab, seconds=10):
    for _ in range(int(seconds * 100)):
        app.processEvents()
        QTest.qWait(10)
        worker = getattr(tab, "_scan_worker", None)
        if not (worker and worker.isRunning()) and not tab._scan_retry.isActive():
            break
    app.processEvents()


mtp_root = tempfile.mkdtemp(prefix="devmtp-", dir=HOME)
try:
    os.makedirs(os.path.join(mtp_root, "Music"))
    for rel, fixture in (("Aphex Twin/Selected Ambient Works/01 - Xtal.wav", WAV1),
                         ("Aphex Twin/Selected Ambient Works/02 - Tha.wav", WAV2),
                         ("Boards of Canada/Geogaddi/01 - Ready Lets Go.wav", WAV1)):
        full = os.path.join(mtp_root, "Music", rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        shutil.copyfile(fixture, full)
    mtp_device = nebula.Device(id="mtp:host=Nebula_Test", name="Nebula Phone",
                                kind="mtp", root=mtp_root, uri="mtp://Nebula_Test/")
    before_queue = list(w.player.queue)
    before_track = w.player.current_path()
    dev.set_devices([mtp_device])
    check("an MTP device is read on a worker, without freezing the window",
          dev._scan_worker is not None and dev._scan_worker.isRunning(),
          dev._scan_worker)
    check("the status bar says the device library is loading",
          "Loading device library" in w.statusBar().currentMessage(),
          w.statusBar().currentMessage())
    check("the scan does not take over the progress bar at the bottom",
          dev.busy.isHidden(), dev.busy.isVisible())
    wait_for_device_scan(dev)
    check("the device's music appears once the scan is done",
          len(dev.music) == 3 and dev.summary.text().startswith("3 tracks"),
          (len(dev.music), dev.summary.text()))
    check("the MTP device opens on its Music folder once it answers",
          dev.device_dir() == "Music" and "Device folder: /Music" in dev.dir_label.text(),
          (dev.device_dir(), dev.dir_label.text()))
    check("and the capacity bar and folder controls are shown for a connected device",
          not dev.space.isHidden() and not dev.toolbar.isHidden()
          and not dev.dir_label.isHidden())
    check("the status bar is cleared after the scan",
          "Loading device library" not in w.statusBar().currentMessage(),
          w.statusBar().currentMessage())
    check("reading the device never starts playing it",
          w.player.current_path() == before_track
          and list(w.player.queue) == before_queue,
          (w.player.current_path(), list(w.player.queue)[-2:]))

    # The covers are read off the GUI thread too, so a scan that just finished still
    # gets its artwork instead of staying on the drawn placeholder.
    cover_png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                 b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00"
                 b"\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82")
    real_read_cover = nebula.read_cover
    nebula.read_cover = lambda path: cover_png if "Aphex Twin - Selected" in path else None
    try:
        dev.set_music_view("covers")
        first_key = dev.covers.item(0).data(nebula.COVER_ROLE)
        check("the covers view has its tiles and their artwork sources",
              dev.covers.count() == 2 and bool(first_key), first_key)
        for _ in range(200):
            app.processEvents()
            QTest.qWait(10)
            if dev._cover_cache.get(first_key) is not None:
                break
        check("the album art loads after the scan instead of staying a placeholder",
              dev._cover_cache.get(first_key) is not None,
              (first_key, dev._cover_cache.get(first_key)))
    finally:
        nebula.read_cover = real_read_cover
        loader = dev._cover_loader
        if loader is not None:
            loader.wait(2000)
        dev.set_music_view("list")

    # The fold menu is the library's, by the search box, and remembers its position.
    fold_labels = [a.text() for a in dev.fold_btn.menu().actions()]
    check("the fold menu sits by the search box with the library's three positions",
          dev.fold_btn.parent() is dev.search_box
          and fold_labels == ["Open all", "Open letter markers only", "Close all"],
          (dev.fold_btn.parent().objectName() if dev.fold_btn.parent() else None,
           fold_labels))
    dev._fold_all("none")
    check("Close all closes the artists",
          not dev.tree.topLevelItem(0).isExpanded()
          and w.config.get("dev_fold") == "none",
          (dev.tree.topLevelItem(0).isExpanded(), w.config.get("dev_fold")))
    dev._fold_all("all")
    artist_item = dev.tree.topLevelItem(0)
    check("Open all opens the artists, their albums and tracks",
          artist_item.isExpanded() and artist_item.child(0).isExpanded()
          and artist_item.child(0).childCount() == 2)
    dev._fold_all("letters")
    check("Open letter markers only opens the first level (artists, not tracks)",
          artist_item.isExpanded() and not artist_item.child(0).isExpanded())
    check("the fold position is saved for the next launch",
          nebula.load_config().get("dev_fold") == "letters")
    dev._fill_views()
    artist_item = dev.tree.topLevelItem(0)
    check("a redraw keeps the saved position, and the menu shows it",
          artist_item is not None and artist_item.isExpanded()
          and not artist_item.child(0).isExpanded()
          and sum(1 for a in dev.fold_actions.values() if a.isChecked()) == 1,
          [(a.text(), a.isChecked()) for a in dev.fold_actions.values()])

    # A sync has priority: not only is the device not read while one is writing to it,
    # the whole view is replaced so nothing here can start a read, play or copy. The
    # claim is on a path, so it covers every way of naming that device.
    section("devices tab: one device, one reader")
    probe_root = tempfile.mkdtemp(prefix="claim-", dir=HOME)
    nebula.DEVICE_CLAIMS.claim(os.path.join(probe_root, "Music"), "probe-claim",
                               "Syncing probe\u2026")
    try:
        check("a claim covers the folder and everything under it",
              nebula.DEVICE_CLAIMS.reason(probe_root) == "Syncing probe\u2026"
              and nebula.DEVICE_CLAIMS.reason(os.path.join(probe_root, "Music", "x.mp3"))
              == "Syncing probe\u2026")
        check("a sibling with the same prefix is a different path",
              nebula.DEVICE_CLAIMS.reason(probe_root + "2") == "")
        check("the claim's reason is what the note says",
              nebula.DEVICE_CLAIMS.reason(probe_root) == "Syncing probe\u2026")
    finally:
        nebula.DEVICE_CLAIMS.release("probe-claim")
        shutil.rmtree(probe_root, ignore_errors=True)
    check("releasing a claim frees the path", nebula.DEVICE_CLAIMS.reason(probe_root) == "")

    sync_device = nebula.Device(id="mtp:host=Nebula_Sync", name="Nebula Phone",
                                 kind="mtp", root=mtp_root, uri="mtp://Nebula_Sync/")
    sync_profile = nebula.Profile(name="Phone sync", device_id=sync_device.id,
                                  source=HOME, target="Music")
    dev.set_devices([sync_device])
    wait_for_device_scan(dev)
    check("the device library is loaded before the sync starts",
          len(dev.music) == 3, len(dev.music))
    holder = "test-sync"
    nebula.DEVICE_CLAIMS.claim(mtp_root, holder, "Syncing Phone sync\u2026")
    try:
        dev.busy_changed()
        check("a claim on the device replaces the music with the task's note",
              dev.views.currentWidget() is dev.sync_page
              and "Syncing Phone sync" in dev.sync_title.text(),
              (dev.views.currentWidget(), dev.sync_title.text()))
        check("and stops every read of the device from the tab",
              dev._scan_worker is None and not dev._scan_retry.isActive()
              and not dev.search_box.isEnabled() and not dev.toolbar.isEnabled(),
              (dev._scan_worker, dev._scan_retry.isActive(),
               dev.search_box.isEnabled(), dev.toolbar.isEnabled()))
        dev.reload()
        check("Refresh during a sync is refused, not queued behind it",
              dev.views.currentWidget() is dev.sync_page and dev._scan_worker is None
              and not dev._scan_retry.isActive(),
              (dev.views.currentWidget(), dev._scan_worker, dev._scan_retry.isActive()))
        dev.set_music_view("covers")
        check("the List / Covers switch cannot leave the sync note",
              dev.views.currentWidget() is dev.sync_page)
        dev.set_music_view("list")
        check("playing a device track is refused while the device is claimed",
              not dev._busy_reason() == "" and dev.play_paths([DEV_XTAL]) is None)
    finally:
        nebula.DEVICE_CLAIMS.release(holder)
        dev.busy_changed()
        wait_for_device_scan(dev)
    check("when the claim is gone the music and controls come back",
          dev.views.currentWidget() is dev.tree and dev.search_box.isEnabled()
          and dev.toolbar.isEnabled() and len(dev.music) == 3,
          (dev.views.currentWidget(), dev.search_box.isEnabled(),
           dev.toolbar.isEnabled(), len(dev.music)))
    # the tab's own hold, used by the sync tab, names the profile
    dev.sync_hold(sync_profile)
    check("the tab's own hold shows the profile's name",
          dev.views.currentWidget() is dev.sync_page
          and "Syncing Phone sync" in dev.sync_title.text(), dev.sync_title.text())
    dev.sync_finished()
    wait_for_device_scan(dev)
    check("the scan starts by itself when the sync is finished",
          len(dev.music) == 3 and dev.views.currentWidget() is dev.tree,
          (len(dev.music), dev.views.currentWidget()))

    # A track queued from the phone stays the phone's file, is labelled MTP in the
    # queue, and is buffered locally; pulling the phone out removes it and its copy.
    pc_before = list(w.player.queue)
    queued_before = len(w.player.queue)
    play_before = w.player.index
    dev.play_paths([DEV_XTAL], queue=True)
    app.processEvents()
    mtp_track = dev.backend.local(DEV_XTAL)
    check("a track queued from an MTP device is the phone's file, not the PC's",
          w.player.queue[-1:] == [mtp_track] and len(w.player.queue) == queued_before + 1,
          w.player.queue[-2:])
    check("and queueing it did not start playback", w.player.index == play_before,
          (play_before, w.player.index))
    mtp_last = tab.table.rowCount() - 1
    check("the queue names MTP device as its source",
          tab.table.item(mtp_last, 8).text() == "MTP device",
          tab.table.item(mtp_last, 8).text())
    mtp_cached = wait_device_buffer(mtp_track)
    check("the phone's track is copied into the device buffer",
          bool(mtp_cached) and os.path.isfile(mtp_cached), mtp_cached)

    # Pulling the device out leaves nothing behind: no ghost albums, no capacity for a
    # device that is not there, and no old folder path.
    dev.set_devices([])
    check("disconnecting removes the phone's queue entries and keeps the PC queue",
          w.player.queue == pc_before and mtp_track not in w.player.queue
          and not nebula.DEVICE_QUEUE,
          (w.player.queue, list(nebula.DEVICE_QUEUE)))
    check("and deletes the copy buffered from the phone",
          not os.path.exists(mtp_cached), mtp_cached)
    check("the disconnected tab names the device plainly and claims no false disconnect",
          dev.info.text() == "<b>Nebula Phone</b> — not connected"
          and "disconnected" not in dev.info.text().lower()
          and not [l for l in dev.dev_bar.findChildren(nebula.QLabel)
                   if "No device" in l.text()],
          (dev.info.text(), [l.text() for l in dev.dev_bar.findChildren(nebula.QLabel)]))
    check("disconnecting clears the device's music, tree and covers",
          dev.backend is None and not dev.music
          and dev.tree.topLevelItemCount() == 0 and dev.covers.count() == 0,
          (dev.backend, len(dev.music), dev.tree.topLevelItemCount(), dev.covers.count()))
    check("no capacity bar or old folder is shown without a device",
          dev.space.isHidden() and dev.toolbar.isHidden() and dev.dir_label.isHidden()
          and dev.dir_label.text() == ""
          and dev.summary.text() == "Plug it back in to browse its music.",
          (dev.space.isHidden(), dev.toolbar.isHidden(), dev.dir_label.isHidden(),
           dev.dir_label.text(), dev.summary.text()))
    check("the unplugged device keeps its row, greyed out, instead of vanishing",
          dev.dev_list.count() > 0 and any(
              not r["connected"] for r in dev.rows)
          and dev.dev_list.item(dev.dev_list.currentRow()).data(
              nebula.DEVICE_STATUS_ROLE) == "not connected",
          [(r["name"], r["connected"]) for r in dev.rows])
    check("there is no ghost cover left to click",
          dev.covers.count() == 0 and dev._visible() == [])
finally:
    w.sync_tab.worker = None
    dev.set_devices([])
    shutil.rmtree(mtp_root, ignore_errors=True)


# ---------------------------------------------------------------- per-device media tabs
section("devices tab: Music and Audiobooks tabs")
cat_root = tempfile.mkdtemp(prefix="devcategories-", dir=HOME)
cat_music = os.path.join(cat_root, "Music")
for rel, fixture in (("Artists/Aphex Twin/Selected/01 - Xtal.wav", WAV1),
                     ("Audiobooks/Dune/Chapter 01.m4b", WAV1),
                     ("Podcasts/Show/episode.mp3", WAV2)):
    full = os.path.join(cat_music, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    shutil.copyfile(fixture, full)
cat_device = nebula.Device(id=f"mass:{cat_root}", name="Categories", kind="mass",
                           root=cat_root)
cat_cfg = {"library_folders": [MUSIC], "device_dirs": {}, "device_categories": {},
           "devices_layout": "bar"}
cat_tab = nebula.DevicesTab(w.player, cat_cfg, w.library)
cat_tab.set_devices([cat_device])
check("a device has Music and Audiobooks tabs, without Podcasts",
      [cat_tab.category_tabs.tabText(i) for i in range(cat_tab.category_tabs.count())]
      == ["Music", "Audiobooks"],
      [cat_tab.category_tabs.tabText(i) for i in range(cat_tab.category_tabs.count())])
check("the one device read is separated by media kind",
      sorted((e["kind"], e["rel"]) for e in cat_tab.music)
      == [("audiobook", "Audiobooks/Dune/Chapter 01.m4b"),
          ("music", "Artists/Aphex Twin/Selected/01 - Xtal.wav"),
          ("podcast", "Podcasts/Show/episode.mp3")]
      and len(cat_tab._visible()) == 1,
      [(e["kind"], e["rel"]) for e in cat_tab.music])
reloads = []
real_cat_reload = cat_tab.reload
cat_tab.reload = lambda: reloads.append(1)
try:
    cat_tab.category_tabs.setCurrentIndex(1)
finally:
    cat_tab.reload = real_cat_reload
check("Audiobooks shows only books, without reading the device again",
      not reloads and cat_tab.category == "audiobook"
      and [e["rel"] for _i, e in cat_tab._visible()]
      == ["Audiobooks/Dune/Chapter 01.m4b"]
      and "audiobooks" in cat_tab.search.placeholderText().lower(),
      (reloads, [e["rel"] for _i, e in cat_tab._visible()]))
cat_tab.category_tabs.setCurrentIndex(0)
cat_tab.category_tabs.setCurrentIndex(1)
check("the chosen media tab is remembered per device",
      cat_cfg["device_categories"].get(cat_device.id) == "audiobook",
      cat_cfg.get("device_categories"))
cat_restore = nebula.DevicesTab(w.player, cat_cfg, w.library)
cat_restore.set_devices([cat_device])
check("the media tab comes back for that device on the next visit",
      cat_restore.category == "audiobook" and cat_restore.category_tabs.currentIndex() == 1,
      (cat_restore.category, cat_restore.category_tabs.currentIndex()))
cat_restore.shutdown()

cover_calls = []
real_cover = nebula.read_cover
nebula.read_cover = lambda path: (cover_calls.append(path), cover_png)[1]
try:
    cat_tab.category_tabs.setCurrentIndex(1)
    # Removing the Podcasts tab means this book view may already be warm from the
    # earlier category check; clear that cache so the instrumented cover reader is
    # exercised by a fresh load.
    cat_tab._stop_book_loader(2000)
    cat_tab._invalidate_books()
    cat_tab._fill_views()
    check("Devices > Audiobooks uses the Audiobooks tab's table",
          cat_tab.views.currentWidget() is cat_tab.books
          and cat_tab.view_row.isHidden() and cat_tab.fold_btn.isHidden()
          and [cat_tab.books.headerItem().text(i)
               for i in range(cat_tab.books.columnCount())]
          == ["", "Title", "Author", "Chapters", "Length"],
          (cat_tab.views.currentWidget(), cat_tab.view_row.isHidden(),
           [cat_tab.books.headerItem().text(i)
            for i in range(cat_tab.books.columnCount())]))
    check("one book folder is one table title, not a cover tile",
          cat_tab.books.topLevelItemCount() == 1
          and cat_tab.books.topLevelItem(0).text(1) == "Dune",
          [cat_tab.books.topLevelItem(i).text(1)
           for i in range(cat_tab.books.topLevelItemCount())])
    check("the List / Covers switch cannot take the book table away",
          cat_tab.set_music_view("covers") is None
          and cat_tab.views.currentWidget() is cat_tab.books,
          cat_tab.views.currentWidget())
    key = cat_tab.books.topLevelItem(0).data(0, nebula.COVER_ROLE)
    for _ in range(300):
        app.processEvents()
        QTest.qWait(10)
        if key in cat_tab._book_cache:
            break
    check("a device book's tags and cover are read from its own file",
          key in cat_tab._book_cache
          and any(path.endswith("Chapter 01.m4b") for path in cover_calls),
          (key, cover_calls, list(cat_tab._book_cache)))
    check("the book row carries author, chapter count and length",
          cat_tab.books.topLevelItem(0).text(2) == "Aphex Twin"
          and cat_tab.books.topLevelItem(0).text(3) == "1"
          and cat_tab.books.topLevelItem(0).text(4) == "0:02"
          and not cat_tab.books.topLevelItem(0).icon(0).isNull(),
          [cat_tab.books.topLevelItem(0).text(i) for i in range(5)])
    cat_tab.search.setText("dune")
    check("the book table's search keeps the matching title",
          cat_tab.books.topLevelItemCount() == 1, cat_tab.books.topLevelItemCount())
    cat_tab.search.setText("aphex")
    check("the book table searches the author read from the device file",
          cat_tab.books.topLevelItemCount() == 1, cat_tab.books.topLevelItemCount())
    cat_tab.search.setText("nothing here")
    check("a search with no books shows an empty table and says so",
          cat_tab.books.topLevelItemCount() == 0
          and cat_tab.summary.text() == "No audiobooks match the search",
          (cat_tab.books.topLevelItemCount(), cat_tab.summary.text()))
    cat_tab.search.setText("")
    cat_tab.set_music_view("list")
    cat_tab.category_tabs.setCurrentIndex(0)
    check("Music keeps its own list and brings the view switch back",
          cat_tab.views.currentWidget() is cat_tab.tree
          and not cat_tab.view_row.isHidden() and not cat_tab.fold_btn.isHidden(),
          (cat_tab.views.currentWidget(), cat_tab.view_row.isHidden(),
           cat_tab.fold_btn.isHidden()))
finally:
    nebula.read_cover = real_cover
    loader = cat_tab._book_loader
    if loader is not None:
        loader.wait(2000)
    cat_tab.shutdown()


# ---------------------------------------------------------------- player icons
section("player bar: transport and mode icons")


def icon_pixels(icon, size, colour, mode=QIcon.Normal, state=QIcon.Off):
    """Pixels of one icon pixmap that are the given colour (so a glyph in that colour)."""
    image = icon.pixmap(QSize(size, size), mode, state).toImage()
    want = QColor(colour)
    total = 0
    for y in range(image.height()):
        for x in range(image.width()):
            c = image.pixelColor(x, y)
            if (c.alpha() > 100 and abs(c.red() - want.red()) < 14
                    and abs(c.green() - want.green()) < 14
                    and abs(c.blue() - want.blue()) < 14):
                total += 1
    return total


black_palette = nebula.THEME_TEMPLATES["black"]
nebula.apply_theme(app, {"theme": {"template": "black", "base": "black", "colors": {}}})
pb = w.player
pb.refresh_theme()
check("the play button is the big circle and the others are smaller",
      pb.play_btn.objectName() == "PlayerBig" and pb.play_btn.width() == 44
      and pb.prev_btn.width() == pb.next_btn.width() == pb.stop_btn.width() < 44,
      (pb.play_btn.objectName(), pb.play_btn.width(), pb.prev_btn.width()))
# The row is laid out like a portable player: the two modes outside the transport.
row_widgets = None
for _lay in pb.findChildren(nebula.QHBoxLayout):
    _items = [_lay.itemAt(i).widget() for i in range(_lay.count())]
    if pb.shuffle_btn in _items:
        row_widgets = _items
        break
check("the transport row runs shuffle, previous, play, stop, next, repeat",
      row_widgets is not None and [w for w in row_widgets
                                   if w in (pb.shuffle_btn, pb.prev_btn, pb.play_btn,
                                            pb.stop_btn, pb.next_btn, pb.repeat_btn)]
      == [pb.shuffle_btn, pb.prev_btn, pb.play_btn, pb.stop_btn, pb.next_btn,
          pb.repeat_btn],
      row_widgets) 
for button, kind, size in ((pb.prev_btn, "previous", 22), (pb.stop_btn, "stop", 22),
                           (pb.next_btn, "next", 22)):
    check(f"the {kind} button draws its own glyph in the theme's text colour",
          icon_pixels(button.icon(), size, black_palette["text"]) >= 40,
          icon_pixels(button.icon(), size, black_palette["text"]))
play_icon = pb.play_btn.icon().pixmap(QSize(26, 26), QIcon.Normal, QIcon.Off).toImage()
pb._playing = True
pb._refresh_transport_icons()
pause_icon = pb.play_btn.icon().pixmap(QSize(26, 26), QIcon.Normal, QIcon.Off).toImage()
check("while playing the big circle shows pause bars",
      pause_icon != play_icon
      and icon_pixels(pb.play_btn.icon(), 26, black_palette["text"]) >= 40)
pb._playing = False
pb._refresh_transport_icons()
check("stopping puts the play triangle back",
      pb.play_btn.icon().pixmap(QSize(26, 26), QIcon.Normal, QIcon.Off).toImage() == play_icon)
check("the rings are drawn by the stylesheet in the theme's text colour",
      "QPushButton#PlayerButton" in app.styleSheet()
      and "2px solid #f2f2f2" in app.styleSheet()
      and "QPushButton#PlayerBig" in app.styleSheet(),
      [line for line in app.styleSheet().splitlines() if "PlayerButton" in line][:2])

check("shuffle and repeat sit outside the circles, so no ring is drawn around them",
      pb.shuffle_btn.objectName() == "PlayerToggle"
      and pb.repeat_btn.objectName() == "PlayerToggle"
      and "background: transparent; border: 0" in app.styleSheet(),
      (pb.shuffle_btn.objectName(), pb.repeat_btn.objectName()))
# OFF is the same drawing struck through, ON is the plain drawing: the two states are
# different shapes, not one shape in two shades.
nebula.apply_theme(app, {"theme": {"template": "black", "base": "black", "colors": {}}})
pb.refresh_theme()
shuffle_off_glyph = nebula.player_icon("shuffle_off", "#ffffff", 20)
shuffle_on_glyph = nebula.player_icon("shuffle", "#ffffff", 20)
repeat_off_glyph = nebula.player_icon("repeat_off", "#ffffff", 20)
repeat_on_glyph = nebula.player_icon("repeat", "#ffffff", 20)

def glyph_diffs(a, b):
    ia, ib = a.toImage(), b.toImage()
    return sum(1 for y in range(ia.height()) for x in range(ia.width())
               if ia.pixelColor(x, y) != ib.pixelColor(x, y))

check("an off shuffle is the shuffled arrows struck through",
      glyph_diffs(shuffle_off_glyph, shuffle_on_glyph) >= 30,
      glyph_diffs(shuffle_off_glyph, shuffle_on_glyph))
check("an off repeat is the loop struck through",
      glyph_diffs(repeat_off_glyph, repeat_on_glyph) >= 30,
      glyph_diffs(repeat_off_glyph, repeat_on_glyph))
check("repeat one is the loop with a 1 in the middle",
      glyph_diffs(nebula.player_icon("repeat_one", "#ffffff", 20), repeat_on_glyph) >= 8,
      glyph_diffs(nebula.player_icon("repeat_one", "#ffffff", 20), repeat_on_glyph))
pb.shuffle = False
pb._refresh_transport_icons()
check("an off shuffle is a grey glyph",
      icon_pixels(pb.shuffle_btn.icon(), 20, black_palette["muted"], QIcon.Normal,
                  QIcon.Off) >= 25,
      icon_pixels(pb.shuffle_btn.icon(), 20, black_palette["muted"], QIcon.Normal, QIcon.Off))
check("a shuffle that is on turns to the text colour",
      icon_pixels(pb.shuffle_btn.icon(), 20, black_palette["text"], QIcon.Normal,
                  QIcon.On) >= 25,
      icon_pixels(pb.shuffle_btn.icon(), 20, black_palette["text"], QIcon.Normal, QIcon.On))
check("an off repeat is a grey glyph too",
      icon_pixels(pb.repeat_btn.icon(), 20, black_palette["muted"], QIcon.Normal,
                  QIcon.Off) >= 25)
repeat_all = pb.repeat_btn.icon().pixmap(QSize(20, 20), QIcon.Normal, QIcon.On).toImage()
check("a repeat that is on turns to the text colour",
      icon_pixels(pb.repeat_btn.icon(), 20, black_palette["text"], QIcon.Normal,
                  QIcon.On) >= 25)
pb.repeat = "one"
pb._update_repeat_ui()
repeat_one = pb.repeat_btn.icon().pixmap(QSize(20, 20), QIcon.Normal, QIcon.On).toImage()
check("repeat one is on, with a 1 in the loop and so a different glyph",
      pb.repeat_btn.isChecked() and repeat_one != repeat_all
      and icon_pixels(pb.repeat_btn.icon(), 20, black_palette["text"], QIcon.Normal,
                      QIcon.On) >= 25)
check("repeat one and repeat all differ by more than an anti-aliased pixel or two",
      sum(1 for y in range(repeat_one.height()) for x in range(repeat_one.width())
          if repeat_one.pixelColor(x, y) != repeat_all.pixelColor(x, y)) >= 8,
      sum(1 for y in range(repeat_one.height()) for x in range(repeat_one.width())
          if repeat_one.pixelColor(x, y) != repeat_all.pixelColor(x, y)))
pb.repeat = "off"
pb._update_repeat_ui()
check("repeat off ticks nothing",
      not pb.repeat_btn.isChecked() and pb.repeat_btn.toolTip() == "Repeat off")


def painted(widget, colour):
    """Pixels a rendered widget paints in that colour: the button itself, not its icon."""
    image = widget.grab().toImage()
    want = QColor(colour)
    total = 0
    for y in range(image.height()):
        for x in range(image.width()):
            c = image.pixelColor(x, y)
            if (c.alpha() > 100 and abs(c.red() - want.red()) < 14
                    and abs(c.green() - want.green()) < 14
                    and abs(c.blue() - want.blue()) < 14):
                total += 1
    return total


# Qt asks a button for QIcon.Active as soon as it has focus or the pointer. The on/off
# colour has to survive that: these checks look at the pixels the button draws.
pb._set_shuffle(False)
pb.repeat = "off"
pb._update_repeat_ui()
pb.shuffle_btn.setFocus()
app.processEvents()
check("an off shuffle paints grey on the button, focused or not",
      painted(pb.shuffle_btn, black_palette["muted"]) >= 25
      and painted(pb.shuffle_btn, black_palette["text"]) == 0,
      (painted(pb.shuffle_btn, black_palette["muted"]),
       painted(pb.shuffle_btn, black_palette["text"])))
check("an off repeat paints grey on the button too",
      painted(pb.repeat_btn, black_palette["muted"]) >= 20
      and painted(pb.repeat_btn, black_palette["text"]) == 0,
      (painted(pb.repeat_btn, black_palette["muted"]),
       painted(pb.repeat_btn, black_palette["text"])))
check("the off glyph is the off glyph in QIcon.Active as well",
      icon_pixels(pb.shuffle_btn.icon(), 20, black_palette["muted"], QIcon.Active,
                  QIcon.Off) >= 25
      and icon_pixels(pb.repeat_btn.icon(), 20, black_palette["muted"], QIcon.Active,
                      QIcon.Off) >= 20)
pb._set_shuffle(True)
app.processEvents()
check("a shuffle that is on paints white on the button, focus and all",
      painted(pb.shuffle_btn, black_palette["text"]) >= 25,
      painted(pb.shuffle_btn, black_palette["text"]))

section("player: repeat one and shuffle")
pb._set_shuffle(True)
pb.repeat = "all"
pb._update_repeat_ui()
check("with repeat all the shuffle setting stands",
      pb.shuffle_btn.isChecked() and pb.shuffle_btn.isEnabled())
pb._cycle_repeat()
check("choosing repeat one switches shuffle off and leaves it insensitive",
      pb.repeat == "one" and not pb.shuffle_btn.isChecked()
      and not pb.shuffle_btn.isEnabled()
      and "Repeat one" in pb.shuffle_btn.toolTip(),
      (pb.repeat, pb.shuffle_btn.isChecked(), pb.shuffle_btn.isEnabled(),
       pb.shuffle_btn.toolTip()))
check("repeat one keeps the shuffle setting it interrupted",
      pb.shuffle and pb.config["shuffle"], (pb.shuffle, pb.config["shuffle"]))
check("while repeat one plays, playback does not shuffle", not pb._shuffle_active())
check("repeat one paints white with the 1 in it",
      painted(pb.repeat_btn, black_palette["text"]) >= 20, 
      painted(pb.repeat_btn, black_palette["text"]))
pb._cycle_repeat()
check("leaving repeat one brings the shuffle setting back",
      pb.repeat == "off" and pb.shuffle_btn.isChecked() and pb.shuffle_btn.isEnabled()
      and pb._shuffle_active(),
      (pb.repeat, pb.shuffle_btn.isChecked(), pb._shuffle_active()))
pb._cycle_repeat()
check("repeat off and repeat all both keep shuffle on",
      pb.repeat == "all" and pb.shuffle_btn.isChecked() and pb._shuffle_active())
pb._cycle_repeat()
pb._cycle_repeat()   # one, then back to off

section("player: the shuffled order")


class _Reversed:
    """Stands in for the random module so a shuffled pass has a known order."""

    @staticmethod
    def shuffle(seq):
        seq.reverse()


real_random = nebula.random
pb.stop()
pb.repeat = "off"
pb._update_repeat_ui()
pb._set_shuffle(False)
pb.set_queue([WAV1, WAV2, FLAC1])
pb.play_index(0)
nebula.random = _Reversed
pb._set_shuffle(True)
pb.play_index(0)      # the order opens with the track that is playing
first_pass = [pb.index]
for _ in range(2):
    pb.next()
    first_pass.append(pb.index)
check("a shuffled queue plays every track once, then stops",
      first_pass == [0, 2, 1]
      and pb.player.playbackState() == nebula.QMediaPlayer.StoppedState, first_pass)
check("the shuffled order is kept, not drawn again per track",
      pb._shuffle_order == [0, 2, 1] and pb._shuffle_pos == 2, pb._shuffle_order)

pb.repeat = "all"
pb._update_repeat_ui()
pb._set_shuffle(True)
pb.play_index(0)
pass_one = [pb.index]
for _ in range(2):
    pb.next()
    pass_one.append(pb.index)
pb.next()             # the pass ends: repeat all draws a new order
pass_two = [pb.index]
for _ in range(2):
    pb.next()
    pass_two.append(pb.index)
check("repeat all starts the shuffled queue again in a new order",
      pass_one == [0, 2, 1] and pass_two == [2, 1, 0] and pass_one != pass_two,
      (pass_one, pass_two))
check("the second pass is a fresh order over the whole queue",
      sorted(pass_two) == [0, 1, 2] and pb._shuffle_order == [2, 1, 0],
      (pass_two, pb._shuffle_order))
pb.prev()
check("previous walks back through the shuffled order",
      pb.index == 1 and pb._shuffle_pos == 1, (pb.index, pb._shuffle_pos))

pb._set_shuffle(False)
pb.repeat = "off"
pb._update_repeat_ui()
nebula.random = real_random
pb.stop()
pb.set_queue([])
check("switching shuffle off goes back to the queue's own order",
      not pb.shuffle_btn.isChecked() and not pb._shuffle_active())

light_palette = nebula.THEME_TEMPLATES["light"]
nebula.apply_theme(app, {"theme": {"template": "light", "base": "light", "colors": {}}})
pb.refresh_theme()
check("a light theme redraws the same glyphs in its dark text colour",
      icon_pixels(pb.prev_btn.icon(), 22, light_palette["text"]) >= 40
      and not icon_pixels(pb.prev_btn.icon(), 22, black_palette["text"]) >= 40,
      icon_pixels(pb.prev_btn.icon(), 22, light_palette["text"]))
w.apply_theme()
check("the whole bar follows the palette back", nebula.TEXT == nebula.THEME_TEMPLATES["dark"]["text"],
      nebula.TEXT)

w.player.spectrum.set_playing(True)
w.player.spectrum.push_levels([0.8] * nebula.SPECTRUM_BANDS)
check("spectrum accepts levels", max(w.player.spectrum.bands) >= 0.79)
w.player.spectrum.set_live(True)
w.player.spectrum._last_push = 0.0
w.player.spectrum.bands = [0.0] * nebula.SPECTRUM_BANDS
w.player.spectrum._tick()
check("spectrum falls back when the tap starves", max(w.player.spectrum.bands) > 0.05)
w.player.spectrum.grab()
w.player.spectrum.set_playing(True)
w.player.spectrum.push_levels([0.9] * nebula.SPECTRUM_BANDS)
w.player.stop()
check("Stop clears the spectrum analyser",
      max(w.player.spectrum.bands) == 0.0 and not w.player.spectrum._timer.isActive(),
      w.player.spectrum.bands[:4])

pm = QPixmap(300, 300)
pm.fill(QColor("#328fba"))
viewer = nebula.CoverViewer(pm, "Gamma", "Boards of Canada — Music Has the Right", w)
viewer.show()
check("cover viewer renders", not viewer.grab().isNull())
viewer.close()

# ---------------------------------------------------------------- tagger
section("batch tagger")
tagger = w.tagger_tab
tagger.load_paths([WAV1])
check("tagger loads tracks", len(tagger.files) == 1)
tagger.files[0]["tags"]["title"] = "Alpha (Remastered)"
tagger.save()
check("tagger writes tags", nebula.read_tags(WAV1)["title"] == "Alpha (Remastered)")
check("tagger refreshes the library",
      any(r["title"] == "Alpha (Remastered)" for r in w.library.tracks()))
tagger.table.item(0, 1).setText("Alpha Undo")
check("a cell edit is undoable",
      tagger.files[0]["tags"]["title"] == "Alpha Undo" and bool(tagger._undo_stack))
tagger.undo()
check("undo restores the saved title", tagger.files[0]["tags"]["title"] == "Alpha (Remastered)")
tagger.redo()
check("redo reapplies the edit", tagger.files[0]["tags"]["title"] == "Alpha Undo")
tagger.undo()
check("undoing the redo leaves the file clean",
      tagger.files[0]["tags"]["title"] == "Alpha (Remastered)" and not tagger._dirty())
tagger.load_paths([FLAC1])
tagger.filter_edit.setText("gamma")
check("tag-list filter hides non-matching files",
      tagger.table.isRowHidden(0) and not tagger.table.isRowHidden(1),
      [tagger.table.isRowHidden(r) for r in range(tagger.table.rowCount())])
tagger.filter_edit.setText("")
check("clearing the filter shows every file",
      not any(tagger.table.isRowHidden(r) for r in range(tagger.table.rowCount())))
tagger.table.selectRow(1)
tagger.remove_selected()
check("remove selected drops the row from the list", len(tagger.files) == 1)
tagger.undo()
check("undo restores a removed row", len(tagger.files) == 2)
check("tag toolbar has icon buttons for every action", len(tagger.tool_buttons) == 12,
      len(tagger.tool_buttons))
check("tag panel edits the core fields plus Comment",
      set(tagger.editors) == set(nebula.FIELDS + ["comment"]), list(tagger.editors))
tag_col = nebula.COLS.index("tag")
tagger.table.selectRow(0)
check("the Tag column names the container and tag family",
      tagger.table.item(0, tag_col).text() == "WAV (ID3v2)",
      tagger.table.item(0, tag_col).text())
tagger.table.selectRow(1)
check("a FLAC row reads FLAC (FLAC)", tagger.table.item(1, tag_col).text() == "FLAC (FLAC)",
      tagger.table.item(1, tag_col).text())
check("the Tag column is read-only",
      not (tagger.table.item(0, tag_col).flags() & Qt.ItemIsEditable))
comment_col = nebula.COLS.index("comment")
tagger.table.selectRow(0)
tagger.table.item(0, comment_col).setText("Remastered 2026")
tagger.save()
check("Comment edits are written to the file",
      nebula.read_extra_tags(WAV1).get("comment") == "Remastered 2026",
      nebula.read_extra_tags(WAV1))
tagger.table.item(0, comment_col).setText("")
tagger.save()
check("an emptied Comment is removed again",
      nebula.read_extra_tags(WAV1).get("comment", "") == "")
tagger.table.clearSelection()
tagger.table.selectRow(1)
tagger.case_convert("UPPER CASE")
check("menu case conversion uppercases the tags",
      tagger.files[1]["tags"]["title"] == "GAMMA", tagger.files[1]["tags"]["title"])
tagger.undo()
tagger.table.clearSelection()
tagger._sort_by(1)
titles_now = [f["tags"]["title"].lower() for f in tagger.files]
check("clicking a header sorts the file list", titles_now == sorted(titles_now), titles_now)
tagger._sort_by(0)
old_wav1 = WAV1
tagger.files[0]["newname"] = "01 - Alpha Renamed.wav"
tagger.save()
renamed = os.path.join(ALBUM_A, "01 - Alpha Renamed.wav")
check("tagger renames the file", os.path.exists(renamed))
WAV1 = renamed
paths_now = [r["path"] for r in w.library.tracks()]
check("library picks the renamed path", renamed in paths_now)
check("renaming drops the stale library row", old_wav1 not in paths_now)

# Regression: composer was silently dropped from M4A, so Ctrl+S cleared the dirty
# marker while Strawberry still showed the old value. Exercise the real tagger path.
m4a_composer_copy = os.path.join(HOME, "tagger-composer.m4a")
flac_composer_copy = os.path.join(HOME, "tagger-composer.flac")
composer_paths = []
if shutil.which("ffmpeg"):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=mono", "-t", "0.5", "-c:a", "aac",
                    m4a_composer_copy], check=True)
    composer_paths.append(m4a_composer_copy)
shutil.copyfile(FLAC1, flac_composer_copy)
composer_paths.append(flac_composer_copy)
tagger.load_paths(composer_paths)
tagger.table.selectAll()
tagger.editors["composer"].setCurrentText("Shared Composer")
tagger._panel_edit("composer")
tagger.save()
if m4a_composer_copy in composer_paths:
    check("tagger writes composer to M4A",
          nebula.read_tags(m4a_composer_copy)["composer"] == "Shared Composer",
          nebula.read_tags(m4a_composer_copy))
else:
    print("  SKIP  tagger composer M4A (ffmpeg not installed; limitation, not a pass)")
check("tagger writes composer to FLAC as well",
      nebula.read_tags(flac_composer_copy)["composer"] == "Shared Composer",
      nebula.read_tags(flac_composer_copy))
# the tagger indexed the copies; drop them so later filter counts see only the music folder
w.library.remove_paths(composer_paths)

# ---------------------------------------------------------------- tags tab: cover + extended
section("tags tab cover follows the selection")
cover_seen = []
_real_read_cover = nebula.read_cover_details


def _spy_details(path):
    cover_seen.append(path)
    return None, nebula.FRONT_COVER, nebula.DEFAULT_COVER_DESC


nebula.read_cover_details = _spy_details
try:
    tagger.load_paths([MP3A])
    names = [f["path"] for f in tagger.files]
    tagger.table.clearSelection()
    tagger._fill_cover()
    check("no selection shows the first file's cover", cover_seen[-1] == names[0],
          (cover_seen[-1:], names[0]))
    tagger.table.selectRow(1)
    check("selecting a row refreshes the cover", cover_seen[-1] == names[1],
          (cover_seen[-1:], names[1]))
    tagger.table.clearSelection()
    tagger.table.setRangeSelected(QTableWidgetSelectionRange(
        1, 0, 2, tagger.table.columnCount() - 1), True)
    tagger._fill_cover()
    check("multi-selection shows the first selected file's cover", cover_seen[-1] == names[1],
          (cover_seen[-1:], names[1]))
finally:
    nebula.read_cover_details = _real_read_cover

section("extended tags round trip")
ext_dir = os.path.join(HOME, "ext")
os.makedirs(ext_dir, exist_ok=True)
ext_files = {
    "mp3": os.path.join(ext_dir, "ext.mp3"),
    "flac": os.path.join(ext_dir, "ext.flac"),
    "wav": os.path.join(ext_dir, "ext.wav"),
}
shutil.copyfile(MP3A, ext_files["mp3"])
shutil.copyfile(FLAC1, ext_files["flac"])
shutil.copyfile(WAV1, ext_files["wav"])
ext_m4a = os.path.join(ext_dir, "ext.m4a")
if shutil.which("ffmpeg"):
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=mono", "-t", "0.5", "-c:a", "aac", ext_m4a], check=True)
    ext_files["m4a"] = ext_m4a
else:
    print("  SKIP  M4A round trip (ffmpeg not installed; limitation, not a pass)")

for kind, p in ext_files.items():
    skipped = nebula.write_extended(p, {"Mood": "Warm", "ENGINEER": "Ada"})
    got = nebula.read_extended(p)
    check(f"{kind}: free-form tags round trip",
          got.get("Mood") == "Warm" and got.get("ENGINEER") == "Ada" and not skipped,
          (got, skipped))
    check(f"{kind}: core fields are not listed as extended",
          not any(k.lower() in nebula.FIELDS for k in got), list(got))
    nebula.write_extended(p, {"Mood": ""})
    got = nebula.read_extended(p)
    check(f"{kind}: an empty value deletes the key",
          "Mood" not in got and got.get("ENGINEER") == "Ada", got)

# multi-selection in the tag panel: differing values show < keep >, edits hit every file
nebula.write_extended(ext_files["flac"], {"Mood": "Cool"})
nebula.write_extended(ext_files["mp3"], {"Mood": "Warm"})
tagger.load_paths([ext_files["mp3"], ext_files["flac"]])
names = [f["path"] for f in tagger.files]
mp3_row, flac_row = names.index(ext_files["mp3"]), names.index(ext_files["flac"])
tagger.table.clearSelection()
for r in (mp3_row, flac_row):
    tagger.table.setRangeSelected(QTableWidgetSelectionRange(
        r, 0, r, tagger.table.columnCount() - 1), True)
tagger._fill_ext()
mood_rows = [i for i, k in enumerate(tagger._ext_keys) if k == "Mood"]
check("multi-selection shows < keep > for a differing extended value",
      mood_rows and tagger.ext_table.item(mood_rows[0], 1).text() == nebula.KEEP,
      tagger._ext_keys)
tagger._apply_ext([mp3_row, flac_row], "Mood", "Hot")
tagger.save()
check("an edit with multi-selection is written to every file",
      nebula.read_extended(ext_files["mp3"]).get("Mood") == "Hot"
      and nebula.read_extended(ext_files["flac"]).get("Mood") == "Hot")
tagger.table.clearSelection()
tagger.table.selectRow(mp3_row)
tagger._fill_ext()
key_rows = [i for i, k in enumerate(tagger._ext_keys) if k == "ENGINEER"]
tagger.ext_table.selectRow(key_rows[0])
tagger._ext_remove()
check("removing a key drops it from the file entry",
      "ENGINEER" not in tagger.files[mp3_row]["tags"]["ext"])
tagger.undo()
check("undo restores removed extended keys",
      tagger.files[mp3_row]["tags"]["ext"].get("ENGINEER") == "Ada")
tagger.table.selectRow(mp3_row)
tagger._fill_ext()
key_rows = [i for i, k in enumerate(tagger._ext_keys) if k == "ENGINEER"]
tagger.ext_table.selectRow(key_rows[0])
tagger._ext_remove()
tagger.save()
check("removing a key deletes it from the file",
      "ENGINEER" not in nebula.read_extended(ext_files["mp3"]))
# saving the copies indexed them; drop them so the filter checks see only the music folder
w.library.remove_paths(list(ext_files.values()))

# ---------------------------------------------------------------- whole-tag window
section("extended tags window")
win_src = os.path.join(HOME, "ext_window.flac")
shutil.copyfile(os.path.join(HOME, "copy.flac"), win_src)
nebula.write_tags(win_src, {"title": "Window Title", "artist": "Window Artist"})
nebula.write_extended(win_src, {"Mood": "Warm", "Engineer": "Ada"})
tagger.load_paths([win_src])
win_row = [f["path"] for f in tagger.files].index(win_src)
win_entries = tagger.extended_entries([win_row])
win_dialog = nebula.ExtendedTagsDialog(win_entries, 0)


def window_rows(dialog):
    return {dialog.table.item(r, 0).text(): dialog.table.item(r, 1).text()
            for r in range(dialog.table.rowCount())}


shown = window_rows(win_dialog)
check("the window lists the core tags",
      shown.get("TITLE") == "Window Title" and shown.get("ARTIST") == "Window Artist",
      shown)
check("the window lists free-form tags beside them",
      shown.get("Mood") == "Warm" and shown.get("Engineer") == "Ada", shown)
check("the window is titled after the tag family",
      "FLAC" in win_dialog.windowTitle() and "ext_window.flac" in win_dialog.position.text(),
      (win_dialog.windowTitle(), win_dialog.position.text()))
win_dialog.set_tag("Conductor", "Bob")
win_dialog.set_tag("title", "Retitled")
win_dialog.remove_keys(["Engineer"])
shown = window_rows(win_dialog)
check("adding a tag puts it in the list", shown.get("Conductor") == "Bob", shown)
real_getitem, real_gettext = nebula.QInputDialog.getItem, nebula.QInputDialog.getText
try:
    nebula.QInputDialog.getItem = lambda *a, **k: ("Mixer", True)
    nebula.QInputDialog.getText = lambda *a, **k: ("Eve", True)
    win_dialog.add_btn.click()
finally:
    nebula.QInputDialog.getItem, nebula.QInputDialog.getText = real_getitem, real_gettext
check("the + button adds a tag by name and value",
      window_rows(win_dialog).get("Mixer") == "Eve", window_rows(win_dialog))
mixer_rows = [r for r in range(win_dialog.table.rowCount())
              if win_dialog.table.item(r, 0).text() == "Mixer"]
win_dialog.table.selectRow(mixer_rows[0])
win_dialog.del_btn.click()
check("the X button removes the selected tag",
      "Mixer" not in window_rows(win_dialog), window_rows(win_dialog))
check("removing a tag takes it out of the list and keeps the rest",
      "Engineer" not in shown and shown.get("Mood") == "Warm", shown)
win_dialog.accept()
tagger.apply_extended([win_row], win_entries)
check("the window's edits land in the Tags list unsaved",
      tagger.files[win_row]["tags"]["title"] == "Retitled"
      and tagger.files[win_row]["tags"]["ext"].get("Conductor") == "Bob"
      and "Engineer" not in tagger.files[win_row]["tags"]["ext"],
      tagger.files[win_row]["tags"])
tagger.save()
check("saving writes the tag added in the window",
      nebula.read_tags(win_src).get("title") == "Retitled"
      and nebula.read_extended(win_src).get("Conductor") == "Bob")
check("a tag removed in the window is deleted from the file",
      "Engineer" not in nebula.read_extended(win_src), nebula.read_extended(win_src))
two_files = nebula.ExtendedTagsDialog(tagger.extended_entries([win_row, win_row]), 0)
two_files._switch(1)
check("the arrows page through the selected files",
      two_files.current == 1 and "file 2 of 2" in two_files.position.text(),
      two_files.position.text())
second_src = os.path.join(HOME, "ext_window_2.flac")
shutil.copyfile(os.path.join(HOME, "copy.flac"), second_src)
nebula.write_tags(second_src, {"title": "Second Title", "artist": "Window Artist"})
nebula.write_extended(second_src, {"Mood": "Cold", "Engineer": "Grace"})
tagger.load_paths([second_src])
second_row = [f["path"] for f in tagger.files].index(second_src)
aggregate = tagger._extended_entry_for_rows([win_row, second_row])
aggregate_tags = aggregate[0]["tags"] if aggregate else {}
check("a multiple selection shows the union of every file's tags",
      bool(aggregate) and aggregate[0].get("multi")
      and aggregate_tags.get("Mood") == nebula.KEEP
      and aggregate_tags.get("Engineer") == nebula.KEEP,
      aggregate_tags)
check("a value shared by every selected file keeps its value",
      aggregate_tags.get("artist") == "Window Artist", aggregate_tags)
tagger.apply_extended([win_row], aggregate)
tagger.apply_extended([second_row], aggregate)
check("untouched < keep > values survive a multiple-selection apply",
      tagger.files[win_row]["tags"]["title"] == "Retitled"
      and tagger.files[second_row]["tags"]["title"] == "Second Title",
      (tagger.files[win_row]["tags"]["title"],
       tagger.files[second_row]["tags"]["title"]))
w.library.remove_paths([win_src, second_src])

# ---------------------------------------------------------------- sync
section("sync engine and device backend")
src = os.path.join(HOME, "sync_src")
dst = os.path.join(HOME, "sync_dst")
os.makedirs(os.path.join(src, "Aphex Twin - Selected Ambient Works"))
shutil.copyfile(WAV1, os.path.join(src, "Aphex Twin - Selected Ambient Works", "01 - Alpha.wav"))
shutil.copyfile(WAV2, os.path.join(src, "Aphex Twin - Selected Ambient Works", "02 - Beta.wav"))
os.makedirs(dst)
profile = nebula.Profile(name="Phone", device_id=f"folder:{dst}", source=src, target="Music")
backend = nebula.LocalFolderBackend(dst)
plan = nebula.compare(profile, backend)
check("first compare plans two new files",
      sorted(a.kind for a in plan) == ["new", "new"], [(a.kind, a.rel) for a in plan])
errors = nebula.execute(profile, backend, plan)
check("execute copies the files", errors == 0 and
      os.path.exists(os.path.join(dst, "Music", "Artists",
                                  "Aphex Twin - Selected Ambient Works",
                                  "01 - Alpha.wav")))
plan = nebula.compare(profile, backend)
check("second compare finds them equal", [a.kind for a in plan] == ["equal", "equal"],
      [a.kind for a in plan])
# Equal-length bit changes must be detected; size/mtime are not used as a proxy.
mirrored = os.path.join(dst, "Music", "Artists", "Aphex Twin - Selected Ambient Works",
                        "01 - Alpha.wav")
with open(mirrored, "r+b") as f:
    f.seek(-1, os.SEEK_END)
    last = f.read(1)
    f.seek(-1, os.SEEK_END)
    f.write(bytes([last[0] ^ 1]))
plan = nebula.compare(profile, backend)
changed = [a for a in plan if a.rel.endswith("01 - Alpha.wav")]
check("content compare catches a one-bit difference at equal size",
      len(changed) == 1 and changed[0].kind == "changed", changed)
nebula.execute(profile, backend, plan)
check("sync replaces content-changed file", nebula.files_equal(
      os.path.join(src, "Aphex Twin - Selected Ambient Works", "01 - Alpha.wav"),
      lambda: open(mirrored, "rb")))

# Hash mode: a file the PC recorded as synced but that is gone from the device is copied again.
hash_dst = os.path.join(HOME, "sync_hash_dst")
os.makedirs(hash_dst)
hash_profile = nebula.Profile(name="PhoneHash", device_id=f"folder:{hash_dst}", source=src,
                               target="Music", method="hash")
hash_backend = nebula.LocalFolderBackend(hash_dst)
nebula.execute(hash_profile, hash_backend, nebula.compare(hash_profile, hash_backend))
gone = os.path.join(hash_dst, "Music", "Artists", "Aphex Twin - Selected Ambient Works",
                    "02 - Beta.wav")
os.remove(gone)
hash_lines = []
hash_errors = nebula.execute(hash_profile, hash_backend,
                              nebula.compare(hash_profile, hash_backend), log=hash_lines.append)
check("hash sync restores a file missing from the device",
      hash_errors == 0 and os.path.exists(gone)
      and any("RESTORE" in line and "02 - Beta.wav" in line for line in hash_lines), hash_lines)

# Edit tags dialog: edits are written only on Save, and only for the fields that were typed.
tag_copy = os.path.join(HOME, "edit_tags.flac")
shutil.copyfile(os.path.join(HOME, "copy.flac"), tag_copy)
tag_dialog = nebula.EditTagsDialog([tag_copy], None)
tag_dialog._record("title", "Edited Title")
tag_dialog._save()
check("edit tags dialog saves the typed field",
      nebula.read_tags(tag_copy)["title"] == "Edited Title" and tag_dialog.saved == [tag_copy])

# Device-side names: FAT32 refuses * ? : " < > | \, a control character and a
# trailing space or dot, so those are dropped there; exFAT and MTP store the name as it is.
section("device file names")
check("reserved characters are dropped, spaces kept",
      nebula.device_rel("Artist - X/Album 1/01 - VAMPIRE - DECO*27.m4a")
      == "Artist - X/Album 1/01 - VAMPIRE - DECO27.m4a")
check("each reserved character is removed",
      nebula.device_rel('a*b?c:d"e<f>g|h\\i.mp3') == "abcdefghi.mp3")
names = nebula.device_map(["A/x*.m4a", "A/x?.m4a", "A/X.m4a"])
check("colliding device names get unique suffixes",
      len({v.lower() for v in names.values()}) == 3, names)
check("first clashing file (sorted order) keeps the plain name",
      names["A/X.m4a"] == "A/X.m4a" and names["A/x*.m4a"] == "A/x (2).m4a", names)
check("FAT32 also drops a control character and trims a trailing space or dot",
      nebula.device_rel("A/we\x01ird.mp3") == "A/weird.mp3"
      and nebula.device_rel("A/track ") == "A/track"
      and nebula.device_rel("A/track..") == "A/track",
      (nebula.device_rel("A/we\x01ird.mp3"), nebula.device_rel("A/track "),
       nebula.device_rel("A/track..")))
check("FAT32 keeps everything else, a space before the extension included",
      nebula.device_rel("A/01 - Tráck – em—dash.flac") == "A/01 - Tráck – em—dash.flac"
      and nebula.device_rel("A/track .mp3") == "A/track .mp3")
star_name_rel = "Artist - X/Album 1/01 - VAMPIRE - DECO*27.m4a"
check("exFAT and MTP keep a reserved character, name for name",
      nebula.device_rel(star_name_rel, "exfat") == star_name_rel
      and nebula.device_rel(star_name_rel, "mtp") == star_name_rel
      and nebula.device_rel('a*b?c:d"e<f>g|h\\i.mp3', "exfat") == 'a*b?c:d"e<f>g|h\\i.mp3',
      (nebula.device_rel(star_name_rel, "exfat"), nebula.device_rel(star_name_rel, "mtp")))
check("exFAT and MTP keep a name that ends in a space or a dot",
      nebula.device_rel("A/track ", "exfat") == "A/track "
      and nebula.device_rel("A/track ", "mtp") == "A/track "
      and nebula.device_rel("A/track.", "exfat") == "A/track.",
      (nebula.device_rel("A/track ", "exfat"), nebula.device_rel("A/track.", "mtp")))
check("exFAT keeps every character of a name but still resolves a case collision",
      nebula.device_map(["A/X.m4a", "A/x.m4a"], "exfat") == {"A/X.m4a": "A/X.m4a",
                                                              "A/x.m4a": "A/x (2).m4a"},
      nebula.device_map(["A/X.m4a", "A/x.m4a"], "exfat"))
check("the filesystem choice is per profile and FAT32 is what an old profile gets",
      nebula.Profile().filesystem == "fat32"
      and nebula.Profile(filesystem="exfat").filesystem == "exfat"
      and list(nebula.FILESYSTEMS) == ["fat32", "exfat", "mtp"],
      list(nebula.FILESYSTEMS))

star = os.path.join(src, "Aphex Twin - Selected Ambient Works", "03 - Gamma*.wav")
shutil.copyfile(WAV1, star)


class FlakyBackend(nebula.LocalFolderBackend):
    """Refuses one file; sync must log it and still copy the rest."""
    def copy_in(self, src_path, rel):
        if rel.endswith("02 - Beta.wav"):
            raise OSError("Input/output error")
        return super().copy_in(src_path, rel)


flaky_dst = os.path.join(HOME, "sync_flaky")
os.makedirs(flaky_dst)
flaky = FlakyBackend(flaky_dst)
lines = []
errors = nebula.execute(profile, flaky, nebula.compare(profile, flaky), log=lines.append)
check("one failing file is counted and the others still sync", errors == 1, errors)
check("the star file lands with its * dropped", os.path.exists(
      os.path.join(flaky_dst, "Music", "Artists", "Aphex Twin - Selected Ambient Works",
                   "03 - Gamma.wav")))
check("failure summary is written to the log", any("could not be written" in l for l in lines),
      lines[-2:])

plan = nebula.compare(profile, nebula.LocalFolderBackend(flaky_dst))
check("sanitized name compares equal on the next sync; only the refused file is still new",
      sorted((a.kind, a.rel) for a in plan if a.kind != "equal")
      ==      [("new", "Artists/Aphex Twin - Selected Ambient Works/02 - Beta.wav")],
      [(a.kind, a.rel) for a in plan])
os.remove(star)  # later mirror and device checks share this source folder
shutil.copyfile(WAV1, os.path.join(dst, "Music", "stray.wav"))
plan = nebula.compare(profile, backend)
check("mirror plans deletion of extras", any(a.kind == "delete" for a in plan),
      [(a.kind, a.rel) for a in plan])
nebula.execute(profile, backend, plan)
check("mirror deletes the extra file", not os.path.exists(os.path.join(dst, "Music", "stray.wav")))

profile.mode = "update"
plan = nebula.compare(profile, backend)
check("update mode never plans deletions", all(a.kind != "delete" for a in plan))
profiles_path = nebula.PROFILES_FILE
nebula.save_profiles([profile])
loaded = nebula.load_profiles()
check("sync profiles persist", len(loaded) == 1 and loaded[0].name == "Phone",
      [(p.name, p.device_id) for p in loaded])
card = nebula.Profile(name="Card", device_id=f"folder:{dst}", source=src, target="Music",
                       filesystem="exfat")
nebula.save_profiles([profile, card])
reloaded = nebula.load_profiles()
check("the device filesystem is saved with each profile",
      [(p.name, p.filesystem) for p in reloaded] == [("Phone", "fat32"), ("Card", "exfat")],
      [(p.name, p.filesystem) for p in reloaded])
with open(profiles_path, "w") as f:  # a profiles.json written before the setting existed
    json.dump([{"name": "Old", "source": src, "target": "Music"}], f)
older = nebula.load_profiles()
check("a profile saved before the setting existed loads as FAT32",
      len(older) == 1 and older[0].filesystem == "fat32", older)
nebula.save_profiles([profile])

dev_backend = nebula.Backend(nebula.Device(id=f"mass:{dst}", name="Stick", kind="mass", root=dst))
check("device lists folders", any(name == "Music" and isdir for name, isdir, _ in dev_backend.listdir("")))
try:
    dev_backend.local("../outside")
    traversal_rejected = False
except ValueError:
    traversal_rejected = True
check("device path traversal is rejected", traversal_rejected)
check("MTP URI preserves folders and escapes spaces", nebula.Backend(
      nebula.Device(id="mtp:test", name="Phone", kind="mtp", root=dst,
                     uri="mtp://phone/")).uri("Audio files/one song.mp3")
      == "mtp://phone/Audio%20files/one%20song.mp3")
check("device walks files", len(dev_backend.walk_files("Music")) == 2)
newfile = os.path.join(HOME, "new.wav")
shutil.copyfile(WAV1, newfile)
dev_backend.copy_in(newfile, "Music/new.wav")
check("device copy_in", os.path.exists(os.path.join(dst, "Music", "new.wav")))
outdir = os.path.join(HOME, "out")
os.makedirs(outdir)
dev_backend.copy_out("Music/new.wav", os.path.join(outdir, "new.wav"))
check("device copy_out", os.path.exists(os.path.join(outdir, "new.wav")))
dev_backend.remove("Music/new.wav")
check("device remove", not os.path.exists(os.path.join(dst, "Music", "new.wav")))
check("free space reported", dev_backend.free_space() is None
      or dev_backend.free_space()[1] > 0)
check("device detection returns a list", isinstance(nebula.detect_devices(), list))

# The profile's device filesystem decides what happens to a name on the way over: a star
# is kept on exFAT/MTP and dropped on FAT32, and switching the setting must not delete
# and rewrite a copy that is already on the device.
section("sync: the profile's device filesystem")
fs_home = os.path.join(HOME, "filesystem")
fs_lib = os.path.join(fs_home, "lib", "A - B", "Album 1")
os.makedirs(fs_lib)
shutil.copyfile(WAV1, os.path.join(fs_lib, "01 - DECO*27.wav"))
shutil.copyfile(WAV2, os.path.join(fs_lib, "02 - plain.wav"))

exfat_dst = os.path.join(fs_home, "exfat_card")
os.makedirs(exfat_dst)
exfat_profile = nebula.Profile(name="exFAT card", device_id=f"folder:{exfat_dst}",
                                source=os.path.join(fs_home, "lib"), target="Music",
                                method="hash", mode="mirror", filesystem="exfat")
exfat_backend = nebula.LocalFolderBackend(exfat_dst)
lines = []
exfat_plan = nebula.compare(exfat_profile, exfat_backend, log=lines.append)
check("an exFAT profile plans the PC name exactly, star and all",
      [(a.kind, a.dev) for a in exfat_plan] == [
          ("new", "Artists/A - B/Album 1/01 - DECO*27.wav"),
          ("new", "Artists/A - B/Album 1/02 - plain.wav")],
      [(a.kind, a.dev) for a in exfat_plan])
nebula.execute(exfat_profile, exfat_backend, exfat_plan, log=lines.append)
check("the star file lands on an exFAT device under its own name, with no NAME line",
      os.path.exists(os.path.join(exfat_dst, "Music", "Artists", "A - B", "Album 1",
                                  "01 - DECO*27.wav"))
      and not any(l.startswith("NAME") for l in lines), lines)

fat_dst = os.path.join(fs_home, "fat_card")
os.makedirs(fat_dst)
fat_profile = nebula.Profile(name="FAT card", device_id=f"folder:{fat_dst}",
                              source=os.path.join(fs_home, "lib"), target="Music",
                              method="hash", mode="mirror", filesystem="fat32")
fat_backend = nebula.LocalFolderBackend(fat_dst)
lines = []
nebula.execute(fat_profile, fat_backend,
                nebula.compare(fat_profile, fat_backend, log=lines.append), log=lines.append)
check("a FAT32 profile drops the star and the log says the name changed",
      os.path.exists(os.path.join(fat_dst, "Music", "Artists", "A - B", "Album 1",
                                  "01 - DECO27.wav"))
      and any(l.startswith("NAME") and "01 - DECO*27.wav" in l and "01 - DECO27.wav" in l
              for l in lines), lines)

# The copy on the card is under the FAT32 name; the manifest knows that, so switching the
# setting to exFAT adopts it instead of deleting it and writing the same bytes again.
fat_profile.filesystem = "exfat"
lines = []
switched = nebula.compare(fat_profile, fat_backend, log=lines.append)
check("switching FAT32 to exFAT adopts the copy already on the device",
      all(a.kind == "equal" for a in switched)
      and not any(l.startswith(("KEEP", "EXTRA", "NEW", "DELETE")) for l in lines),
      ([(a.kind, a.rel, a.dev) for a in switched], lines))
check("and nothing is copied or removed, so the card still holds both files",
      sorted(os.path.relpath(os.path.join(r, n), fat_dst)
             for r, _d, f in os.walk(fat_dst) for n in f)
      == ["Music/Artists/A - B/Album 1/01 - DECO27.wav",
          "Music/Artists/A - B/Album 1/02 - plain.wav"],
      sorted(os.walk(fat_dst)))

# MTP copies must land under the device's real names: the phone sees no %20.
mtp_root = os.path.join(HOME, "mtp_root")
os.makedirs(os.path.join(mtp_root, "Walkman_SD", "Music"))
mtp_backend = nebula.Backend(nebula.Device(id="mtp:probe", name="Probe", kind="mtp",
                                             root=mtp_root, uri="mtp://probe/"))
mtp_backend.copy_in(WAV1, "Walkman_SD/Music/Air/Moon Safari/01 - Alpha.wav")
copied = os.path.join(mtp_root, "Walkman_SD", "Music", "Air", "Moon Safari", "01 - Alpha.wav")
check("MTP copy keeps folders with spaces intact", os.path.exists(copied)
      and os.path.getsize(copied) == os.path.getsize(WAV1), sorted(os.listdir(os.path.join(
          mtp_root, "Walkman_SD", "Music"))))
check("MTP copy does not invent %20 folder names",
      not any("%20" in name for _root, dirs, _files in os.walk(mtp_root) for name in dirs))
mtp_backend.remove("Walkman_SD/Music/Air/Moon Safari/01 - Alpha.wav")
check("MTP remove clears the file", not os.path.exists(copied))

# Readiness asks inside a storage, because a phone in charging mode can list its
# storages and still refuse every read inside them.
check("an MTP device is ready when one of its storages answers",
      nebula.device_ready(mtp_backend.device) is True
      and nebula.device_ready(mtp_backend.device, "Walkman_SD/Music") is True)
check("a folder without a storage goes to the storage that already holds it",
      nebula._mtp_storage_path(mtp_backend, "Music") == "Walkman_SD/Music",
      nebula._mtp_storage_path(mtp_backend, "Music"))
empty_mtp_root = os.path.join(HOME, "mtp_empty_root")
os.makedirs(empty_mtp_root)
empty_mtp = nebula.Backend(nebula.Device(id="mtp:empty", name="Empty Phone", kind="mtp",
                                         root=empty_mtp_root, uri="mtp://empty/"))
try:
    nebula._mtp_storage_path(empty_mtp, "Music")
    refused = False
except OSError as e:
    refused = "File transfer" in str(e)
check("a copy with no readable storage says to choose File transfer", refused)

# A copy waits instead of failing while the phone is still charging. The storage is
# created while the waiter is already looking, so this exercises the retry itself.
wait_root = os.path.join(HOME, "mtp_wait_root")
os.makedirs(wait_root)
wait_device = nebula.Device(id="mtp:wait", name="Waiting Phone", kind="mtp",
                            root=wait_root, uri="mtp://wait/")
wait_backend = nebula.Backend(wait_device)
waiting_log = []
def _phone_switches_to_transfer():
    os.makedirs(os.path.join(wait_root, "Walkman_SD", "Music"))
switcher = threading.Timer(0.6, _phone_switches_to_transfer)
switcher.start()
try:
    waited_target = nebula.wait_for_mtp_target(wait_backend, "Music",
                                               log=waiting_log.append,
                                               label="Waiting Phone", timeout=15)
finally:
    switcher.cancel()
check("a copy waits for file transfer and then finds the phone's storage",
      waited_target == "Walkman_SD/Music"
      and any("Waiting for Waiting Phone" in line for line in waiting_log),
      (waited_target, waiting_log))
try:
    start = time.monotonic()
    nebula.wait_for_mtp_target(empty_mtp, "Music", label="Empty Phone", timeout=0.2)
    timed_out = False
except OSError as e:
    timed_out = ("File transfer" in str(e) and time.monotonic() - start < 5)
check("a phone that never answers ends the wait with the file-transfer advice", timed_out)
shutil.rmtree(os.path.join(wait_root, "Walkman_SD"))
check("the wait did not create anything on the phone", not os.listdir(wait_root))

# AAC and ALAC share the .m4a extension; the sample entry decides which it is.
def mp4_box(name, payload):
    return struct.pack(">I", len(payload) + 8) + name + payload

def sample_mp4(codec):
    sample = mp4_box(codec, b"\0" * 28)
    stsd = mp4_box(b"stsd", b"\0\0\0\0" + struct.pack(">I", 1) + sample)
    stbl = mp4_box(b"stbl", stsd)
    moov = mp4_box(b"moov", mp4_box(b"trak", mp4_box(b"mdia", mp4_box(b"minf", stbl))))
    return mp4_box(b"ftyp", b"M4A \0\0\0\0M4A mp42") + moov

aac_path = os.path.join(HOME, "lossy.m4a")
alac_path = os.path.join(HOME, "lossless.m4a")
open(aac_path, "wb").write(sample_mp4(b"mp4a"))
open(alac_path, "wb").write(sample_mp4(b"alac"))
check("AAC sample entry is reported as AAC",
      nebula.mp4_sample_codec(aac_path) == b"mp4a" and nebula.filetype(aac_path) == "AAC",
      (nebula.mp4_sample_codec(aac_path), nebula.filetype(aac_path)))
check("ALAC sample entry is reported as ALAC",
      nebula.mp4_sample_codec(alac_path) == b"alac" and nebula.filetype(alac_path) == "ALAC",
      (nebula.mp4_sample_codec(alac_path), nebula.filetype(alac_path)))

# stale codec values from older builds get re-read once (user_version 2)
stale_db = os.path.join(HOME, "stale.db")
conn = sqlite3.connect(stale_db)
conn.execute("CREATE TABLE tracks (path TEXT PRIMARY KEY, mtime REAL, filetype TEXT)")
conn.execute("INSERT INTO tracks VALUES (?, ?, ?)", (aac_path, 12345.0, "ALAC"))
conn.execute("INSERT INTO tracks VALUES (?, ?, ?)", (WAV1, 12345.0, "WAV"))
conn.execute("PRAGMA user_version=1")
conn.commit()
conn.close()
stale_lib = nebula.Library(stale_db)
rows = {r[0]: r for r in stale_lib._conn().execute(
    "SELECT path, mtime, filetype FROM tracks")}
version = stale_lib._conn().execute("PRAGMA user_version").fetchone()[0]
check("upgrade clears the cached codec of MP4 rows",
      rows[aac_path][1] is None and rows[aac_path][2] is None, rows[aac_path])
check("upgrade leaves non-MP4 rows alone", rows[WAV1][1] == 12345.0, rows[WAV1])
check("database user_version is 2 after the upgrade", version == 2, version)

# ---------------------------------------------------------------- 128-bit hash compare
section("128-bit hash compare")
hsrc = os.path.join(HOME, "hash_src")
hdst = os.path.join(HOME, "hash_dst")
album = "Boards of Canada - Geogaddi"
ha_rel, hb_rel = f"{album}/01 - Alpha.wav", f"{album}/02 - Beta.wav"
ha, hb = os.path.join(hsrc, ha_rel), os.path.join(hsrc, hb_rel)
os.makedirs(os.path.dirname(ha))
os.makedirs(hdst)
shutil.copyfile(WAV1, ha)
shutil.copyfile(WAV2, hb)
hprof = nebula.Profile(name="Hash", device_id=f"folder:{hdst}", source=hsrc,
                        target="Music", method="hash", mode="mirror", music_folder="")
hback = nebula.LocalFolderBackend(hdst)
hdev_alpha = os.path.join(hdst, "Music", album, "01 - Alpha.wav")
hdev_beta = os.path.join(hdst, "Music", album, "02 - Beta.wav")

plan = nebula.compare(hprof, hback)
check("hash mode: first compare plans every file as new",
      sorted(a.kind for a in plan) == ["new", "new"], [(a.kind, a.rel) for a in plan])
check("hash mode: each file gets a SHA-256 digest (64 hex characters)",
      all(len(a.hash) == 64 and int(a.hash, 16) >= 0 for a in plan), [a.hash for a in plan])
errors = nebula.execute(hprof, hback, plan)
check("hash mode: sync copies the files", errors == 0 and os.path.exists(hdev_alpha), errors)
check("hash mode: state database is written on the PC", os.path.exists(nebula.HashStore(hprof).path))
check("hash mode: unchanged library compares equal",
      [a.kind for a in nebula.compare(hprof, hback)] == ["equal", "equal"])

# A device timestamp that no longer matches the manifest is a hint the file may have
# changed outside the app. The bytes decide: read both copies instead of copying a
# file that is still identical just because its clock moved.
os.utime(hdev_alpha, (0, 0))
moved = next(a for a in nebula.compare(hprof, hback) if a.rel == ha_rel)
check("hash mode: a moved device timestamp is re-read, not called changed blind",
      moved.kind == "equal" and moved.verified, moved)
nebula.execute(hprof, hback, nebula.compare(hprof, hback))
check("hash mode: the re-read refreshes the manifest timestamp",
      all(a.kind == "equal" for a in nebula.compare(hprof, hback)))

# a cached hash is reused while size and mtime are unchanged (no re-read)
store = nebula.HashStore(hprof)
store.records[ha_rel]["hash"] = "0" * 64
store.save()
cached = next(a for a in nebula.compare(hprof, hback) if a.rel == ha_rel)
check("hash mode: unchanged size and mtime reuse the cached hash", cached.hash == "0" * 64,
      cached.hash)
store = nebula.HashStore(hprof)
store.records[ha_rel]["hash"] = ""  # empty forces a re-hash, restoring the real digest
store.save()
check("hash mode: a forced re-hash restores the real digest",
      all(a.kind == "equal" for a in nebula.compare(hprof, hback)))

# an equal-size, one-bit edit must be found; a real edit always moves the mtime
with open(ha, "r+b") as f:
    f.seek(-1, os.SEEK_END)
    last = f.read(1)
    f.seek(-1, os.SEEK_END)
    f.write(bytes([last[0] ^ 1]))
st = os.stat(ha)
os.utime(ha, ns=(st.st_atime_ns, st.st_mtime_ns + 10**9))
changed = [a for a in nebula.compare(hprof, hback) if a.rel == ha_rel]
check("hash mode: equal-size one-bit change is detected",
      len(changed) == 1 and changed[0].kind == "changed", changed)
nebula.execute(hprof, hback, nebula.compare(hprof, hback))
check("hash mode: the changed file is copied again",
      nebula.files_equal(ha, lambda: open(hdev_alpha, "rb")))

section("sync manifest and verification")
# The manifest says what was written, per device path, only after a copy succeeded.
manifest = nebula.DeviceManifest(hprof)
rec = manifest.get("Music/" + ha_rel)
check("the manifest records a completed transfer by device path",
      rec is not None and rec["rel"] == ha_rel and rec["size"] == os.path.getsize(ha)
      and rec["hash"] == nebula.file_hash256(ha) and rec["profile"] == hprof.id,
      rec)
check("the manifest is keyed by the device identity, not the profile",
      os.path.basename(manifest.path)
      == nebula.hashlib.sha1(hprof.device_id.encode("utf-8")).hexdigest()[:20] + ".json"
      and nebula.DeviceManifest(nebula.Profile(device_id="folder:/elsewhere")).path
      != manifest.path, manifest.path)

# A trusted manifest compare must not read the device at all.
dev_reads = []
real_open = hback.open_read
hback.open_read = lambda rel: (dev_reads.append(rel), real_open(rel))[1]
try:
    fast_plan = nebula.compare(hprof, hback)
finally:
    hback.open_read = real_open
check("fast hash: a trusted manifest compare reads no device file",
      dev_reads == [] and all(a.kind == "equal" and not a.verified for a in fast_plan),
      (dev_reads, [(a.kind, a.verified) for a in fast_plan]))

# A same-size edit on the device with its timestamp put back is the known blind spot.
st = os.stat(hdev_alpha)
with open(hdev_alpha, "r+b") as f:
    f.seek(-1, os.SEEK_END)
    last = f.read(1)
    f.seek(-1, os.SEEK_END)
    f.write(bytes([last[0] ^ 1]))
os.utime(hdev_alpha, ns=(st.st_atime_ns, st.st_mtime_ns))
blind = next(a for a in nebula.compare(hprof, hback) if a.rel == ha_rel)
check("fast hash: an untracked same-size device edit is not noticed by the manifest",
      blind.kind == "equal" and not blind.verified, blind)
verified = next(a for a in nebula.compare(hprof, hback, verify=True) if a.rel == ha_rel)
check("Verify content reads the device and catches that edit",
      verified.kind == "changed", verified)
nebula.execute(hprof, hback, nebula.compare(hprof, hback, verify=True))
check("the verified compare copies the device-edited file again",
      nebula.files_equal(ha, lambda: open(hdev_alpha, "rb")))

# A verification leaves the manifest saying what the device actually holds: every file
# it read is recorded again from that read, and a record whose device copy turned out
# to be different is dropped rather than left claiming the PC content.
alpha_key = ("Music/" + ha_rel).lower()
beta_key = ("Music/" + hb_rel).lower()
fresh = nebula.DeviceManifest(hprof)
stale = dict(fresh.get(alpha_key))
stale["mtime"] = 987654.0     # a device clock that means nothing in particular
fresh.files[alpha_key] = stale
fresh.save()
nebula.compare(hprof, hback, verify=True)
rewritten = nebula.DeviceManifest(hprof).get(alpha_key)
check("a verification records the device's content and no timestamp at all",
      rewritten is not None and float(rewritten["mtime"]) == 0.0, rewritten)
check("the rewritten record still carries the verified content",
      rewritten["hash"] == nebula.file_hash256(hdev_alpha)
      and rewritten["size"] == os.path.getsize(hdev_alpha)
      and rewritten["rel"] == ha_rel and rewritten["profile"] == hprof.id, rewritten)

st_beta = os.stat(hdev_beta)
with open(hdev_beta, "r+b") as f:
    f.seek(-1, os.SEEK_END)
    last = f.read(1)
    f.seek(-1, os.SEEK_END)
    f.write(bytes([last[0] ^ 1]))
os.utime(hdev_beta, ns=(st_beta.st_atime_ns, st_beta.st_mtime_ns))
check("the manifest still claims that copy before anything is read",
      nebula.DeviceManifest(hprof).get(beta_key) is not None)
verify_plan = nebula.compare(hprof, hback, verify=True)
check("verification reads the edited device copy and plans it as changed",
      next(a for a in verify_plan if a.rel == hb_rel).kind == "changed",
      [(a.kind, a.rel) for a in verify_plan])
check("a record whose verified device copy differs is dropped from the manifest",
      nebula.DeviceManifest(hprof).get(beta_key) is None)
nebula.execute(hprof, hback, verify_plan)
check("syncing it again puts the record back with the copied content",
      (nebula.DeviceManifest(hprof).get(beta_key) or {}).get("hash")
      == nebula.file_hash256(hdev_beta))

# A file missing from the device is planned as a restore; the PC original stays.
os.remove(hdev_alpha)
restore_plan = nebula.compare(hprof, hback)
restore = next(a for a in restore_plan if a.rel == ha_rel)
check("fast hash: a missing device file is planned as a restore",
      restore.kind == "restore" and os.path.exists(ha), restore)
nebula.execute(hprof, hback, restore_plan)
check("the restore brings the PC copy back to the device",
      os.path.exists(hdev_alpha) and nebula.files_equal(ha, lambda: open(hdev_alpha, "rb")))

# Verify content indexes the whole device folder, not only the files this profile syncs:
# a file put on the device by hand gets a record of its own content, and the manifest
# ends up describing what the device holds — with no timestamp in it at all.
hand_rel = "ripped-by-hand.wav"
hand_dev = os.path.join(hdst, "Music", hand_rel)
with open(hand_dev, "wb") as f:
    f.write(b"RIFF" + b"\x00\x11" * 4096)
device_plan = nebula.compare(hprof, hback, verify=True)
indexed = nebula.DeviceManifest(hprof).get(("Music/" + hand_rel).lower())
check("Verify content records a device file the library does not have",
      indexed is not None and indexed["hash"] == nebula.file_hash256(hand_dev)
      and indexed["rel"] == "" and float(indexed["mtime"]) == 0.0, indexed)
check("...the library's own files sit in the same manifest beside it",
      indexed is not None
      and nebula.DeviceManifest(hprof).get(alpha_key)["hash"]
      == nebula.file_hash256(hdev_alpha))
check("...and Mirror still plans that device-only file for removal",
      any(a.kind == "delete" and a.rel == hand_rel for a in device_plan),
      [(a.kind, a.rel) for a in device_plan])

# A device whose clock is useless cannot change the result: a record made by a
# verification has no timestamp to compare, so a scrambled clock re-reads nothing.
for _f in (hdev_alpha, hdev_beta):
    os.utime(_f, (4242, 4242))
clock_reads = []
real_open = hback.open_read
hback.open_read = lambda rel: (clock_reads.append(rel), real_open(rel))[1]
try:
    clockless = nebula.compare(hprof, hback)
except Exception:
    hback.open_read = real_open
    raise
hback.open_read = real_open
check("after a verification a scrambled device clock compares equal without a read",
      clock_reads == [] and {a.rel: a.kind for a in clockless if a.rel in (ha_rel, hb_rel)}
      == {ha_rel: "equal", hb_rel: "equal"},
      (clock_reads, [(a.kind, a.rel) for a in clockless]))

# An audio-only profile verifies audio only; with the box cleared, every file is read.
hand_txt = os.path.join(hdst, "Music", "notes.txt")
with open(hand_txt, "w") as f:
    f.write("not music")
hprof.audio_only = True
nebula.compare(hprof, hback, verify=True)
check("Verify content skips non-audio files when the profile is audio only",
      nebula.DeviceManifest(hprof).get("music/notes.txt") is None)
hprof.audio_only = False
nebula.compare(hprof, hback, verify=True)
check("with Only audio files cleared, Verify content reads every file on the device",
      nebula.DeviceManifest(hprof).get("music/notes.txt") is not None)
hprof.audio_only = True
for _path in (hand_dev, hand_txt):
    try:
        os.remove(_path)
    except OSError:
        pass
final_manifest = nebula.DeviceManifest(hprof)
final_manifest.forget("Music/" + hand_rel)
final_manifest.forget("Music/notes.txt")
final_manifest.save()

# Fast hash never disappears on MTP; the transport changes the cost, not the choice.
mtp_hash_root = os.path.join(HOME, "mtp_hash")
os.makedirs(mtp_hash_root)
mtp_hash_backend = nebula.Backend(nebula.Device(id="mtp:fasthash", name="Phone", kind="mtp",
                                                  root=mtp_hash_root, uri="mtp://phone/"))
mtp_hash_profile = nebula.Profile(name="MTP fast", device_id="mtp:fasthash", source=hsrc,
                                   target="Music", method="hash")
mtp_new = nebula.compare(mtp_hash_profile, mtp_hash_backend)
check("fast hash is offered and planned for an MTP device",
      sorted(a.kind for a in mtp_new) == ["new", "new"],
      [(a.kind, a.rel) for a in mtp_new])
nebula.execute(mtp_hash_profile, mtp_hash_backend, mtp_new)
check("fast hash compares an MTP device's synced files equal",
      [a.kind for a in nebula.compare(mtp_hash_profile, mtp_hash_backend)]
      == ["equal", "equal"],
      [a.kind for a in nebula.compare(mtp_hash_profile, mtp_hash_backend)])


class HashProbe(nebula.LocalFolderBackend):
    """Records the thread of every device write and refuses one file, so the failure path runs."""
    def __init__(self, root):
        super().__init__(root)
        self.threads = set()

    def copy_in(self, src_path, rel):
        self.threads.add(threading.get_ident())
        if rel.endswith("02 - Beta.wav"):
            raise OSError("Input/output error")
        return super().copy_in(src_path, rel)


flaky_hdst = os.path.join(HOME, "hash_flaky")
os.makedirs(flaky_hdst)
flaky_prof = nebula.Profile(name="Hash flaky", device_id=f"folder:{flaky_hdst}", source=hsrc,
                             target="Music", method="hash", music_folder="")
probe = HashProbe(flaky_hdst)
lines = []
errors = nebula.execute(flaky_prof, probe, nebula.compare(flaky_prof, probe), log=lines.append)
check("hash mode: a refused file is counted and the others still sync", errors == 1, errors)
check("a refused transfer is never recorded in the manifest",
      nebula.DeviceManifest(flaky_prof).get("Music/" + ha_rel) is not None
      and nebula.DeviceManifest(flaky_prof).get("Music/" + hb_rel) is None,
      nebula.DeviceManifest(flaky_prof).files)
check("hash mode: a refused file stays new on the next compare",
      sorted((a.kind, a.rel) for a in nebula.compare(flaky_prof, probe)
             if a.kind != "equal") == [("new", hb_rel)],
      [(a.kind, a.rel) for a in nebula.compare(flaky_prof, probe)])
check("hash mode: device writes run on one worker thread, not the UI thread",
      len(probe.threads) == 1 and threading.get_ident() not in probe.threads, probe.threads)
check("hash mode: the failure is reported in the log",
      any("could not be written" in l for l in lines), lines[-2:])
retry = nebula.LocalFolderBackend(flaky_hdst)
nebula.execute(flaky_prof, retry, nebula.compare(flaky_prof, retry))
check("hash mode: the refused file syncs on the next run",
      os.path.exists(os.path.join(flaky_hdst, "Music", album, "02 - Beta.wav")))

# deletion: removed from the library -> removed from the device and the database
os.remove(hb)
plan = nebula.compare(hprof, hback)
check("hash mode: a file gone from the library is planned for deletion",
      [(a.kind, a.rel) for a in plan if a.kind != "equal"] == [("delete", hb_rel)],
      [(a.kind, a.rel) for a in plan])
nebula.execute(hprof, hback, plan)
check("hash mode: the deletion removes the device file", not os.path.exists(hdev_beta))
check("hash mode: the deleted file leaves the state database",
      hb_rel not in nebula.HashStore(hprof).records)

# update mode never plans deletions, even for files it has synced before
shutil.copyfile(WAV2, hb)
nebula.execute(hprof, hback, nebula.compare(hprof, hback))
os.remove(hb)
hprof.mode = "update"
check("hash mode: update never plans deletions",
      all(a.kind != "delete" for a in nebula.compare(hprof, hback)))
hprof.mode = "mirror"

section("quick scan of the device folder")
# One listing drives both halves of a fast compare: what the library has and the device
# lacks is copied back, and what the device holds and the library does not claim is
# checked before mirror mode removes anything.
qsrc = os.path.join(HOME, "scan_src")
qdst = os.path.join(HOME, "scan_dst")
qalbum = "Boards of Canada - Geogaddi"
q_rel, q_beta = f"{qalbum}/01 - Alpha.wav", f"{qalbum}/02 - Beta.wav"
os.makedirs(os.path.dirname(os.path.join(qsrc, q_rel)))
os.makedirs(qdst)
shutil.copyfile(WAV1, os.path.join(qsrc, q_rel))
shutil.copyfile(WAV2, os.path.join(qsrc, q_beta))
qprof = nebula.Profile(name="Scan", device_id=f"folder:{qdst}", source=qsrc, target="Music",
                        method="hash", mode="mirror", music_folder="")
qback = nebula.LocalFolderBackend(qdst)
real_scan_open = qback.open_read


def scan_compare():
    """Compare qprof, keeping the log and recording every device file that was read."""
    reads = []
    qback.open_read = lambda rel: (reads.append(rel), real_scan_open(rel))[1]
    lines = []
    try:
        plan = nebula.compare(qprof, qback, log=lines.append)
    finally:
        qback.open_read = real_scan_open
    return plan, lines, reads


# A library file copied onto the device by hand has no manifest record: it is adopted
# where it is, and neither removed nor written a second time.
hand = os.path.join(qdst, "Music", q_rel)
os.makedirs(os.path.dirname(hand))
shutil.copyfile(os.path.join(qsrc, q_rel), hand)
plan, lines, reads = scan_compare()
alpha = next(a for a in plan if a.rel == q_rel)
check("quick scan: a library file copied on by hand is adopted, not removed",
      alpha.kind == "equal" and alpha.verified and not alpha.extra
      and not any(a.kind == "delete" for a in plan),
      [(a.kind, a.rel, a.extra) for a in plan])
check("quick scan: the scan reports what it listed",
      any(l.startswith("SCAN") and "listed 1 file(s)" in l for l in lines), lines)
errors = nebula.execute(qprof, qback, plan)
check("quick scan: the hand copy is still on the device afterwards",
      errors == 0 and os.path.exists(hand)
      and os.path.getsize(hand) == os.path.getsize(os.path.join(qsrc, q_rel)), errors)

# The same content under a name of its own: kept where it is.
loose = os.path.join(qdst, "Music", "loose", "alpha-rip.wav")
os.makedirs(os.path.dirname(loose))
shutil.copyfile(hand, loose)
os.remove(hand)
plan, lines, reads = scan_compare()
alpha = next(a for a in plan if a.rel == q_rel)
check("quick scan: a copy under another name is kept and adopted where it is",
      alpha.kind == "equal" and alpha.verified and alpha.extra
      and alpha.dev == "loose/alpha-rip.wav"
      and not any(a.kind == "delete" for a in plan),
      [(a.kind, a.rel, a.extra, a.dev) for a in plan])
check("quick scan: the kept copy is named in the log, and only it was read",
      any(l.startswith("KEEP") and "alpha-rip.wav" in l for l in lines)
      and reads == ["Music/loose/alpha-rip.wav"], (lines, reads))

plan, lines, reads = scan_compare()
check("quick scan: the kept copy stays adopted on the next compare, with no device read",
      all(a.kind == "equal" for a in plan) and reads == [],
      (reads, [(a.kind, a.rel) for a in plan]))

# A second copy of content the device already holds is a duplicate.
dup = os.path.join(qdst, "Music", "loose", "alpha-copy.wav")
shutil.copyfile(loose, dup)
plan, lines, reads = scan_compare()
check("quick scan: a duplicate of content already on the device is removed once",
      [(a.kind, a.rel, a.extra) for a in plan if a.kind != "equal"]
      == [("delete", "loose/alpha-copy.wav", True)]
      and any("second copy of" in l for l in lines),
      (lines, [(a.kind, a.rel, a.extra) for a in plan]))

# A size no library file shares cannot be library content, so no read is spent on it.
odd = os.path.join(qdst, "Music", "Junk", "odd.wav")
os.makedirs(os.path.dirname(odd))
with open(odd, "wb") as f:
    f.write(b"\0" * (max(os.path.getsize(os.path.join(qsrc, q_rel)),
                         os.path.getsize(os.path.join(qsrc, q_beta))) + 111))
plan, lines, reads = scan_compare()
check("quick scan: a size no library file shares is settled without reading the file",
      ("delete", "Junk/odd.wav", True) in [(a.kind, a.rel, a.extra) for a in plan]
      and not any("odd.wav" in r for r in reads)
      and any("no library file of this size" in l for l in lines),
      (reads, [l for l in lines if l.startswith("EXTRA")]))
errors = nebula.execute(qprof, qback, plan)
check("quick scan: mirror removes both extras and keeps the adopted copy",
      errors == 0 and not os.path.exists(odd) and not os.path.exists(dup)
      and os.path.exists(loose),
      (errors, sorted(os.listdir(os.path.join(qdst, "Music")))))

# Update never deletes, so its scan reports the extra and reads nothing at all.
keepme = os.path.join(qdst, "Music", "Junk", "keepme.wav")
os.makedirs(os.path.dirname(keepme), exist_ok=True)
shutil.copyfile(loose, keepme)
qprof.mode = "update"
plan, lines, reads = scan_compare()
check("quick scan: update reports an extra but neither removes nor reads it",
      all(a.kind != "delete" for a in plan) and reads == []
      and any(l.startswith("EXTRA") and "keepme.wav" in l and "left alone" in l for l in lines),
      (reads, lines))
qprof.mode = "mirror"
os.remove(keepme)

# A library file that was dropped is still on the device: mirror deletes it once, and the
# scan must not plan the same removal a second time.
dedup_src = os.path.join(HOME, "scan_dedup_src")
dedup_dst = os.path.join(HOME, "scan_dedup_dst")
os.makedirs(dedup_src)
os.makedirs(dedup_dst)
shutil.copyfile(WAV1, os.path.join(dedup_src, "gone.wav"))
dprof = nebula.Profile(name="Dedup", device_id=f"folder:{dedup_dst}", source=dedup_src,
                        target="Music", method="hash", mode="mirror", music_folder="")
dback = nebula.LocalFolderBackend(dedup_dst)
nebula.execute(dprof, dback, nebula.compare(dprof, dback))
os.remove(os.path.join(dedup_src, "gone.wav"))
lines = []
plan = nebula.compare(dprof, dback, log=lines.append)
check("quick scan: a file dropped from the library is removed once, not twice",
      [(a.kind, a.rel, a.extra) for a in plan if a.kind != "equal"]
      == [("delete", "gone.wav", False)], [(a.kind, a.rel, a.extra) for a in plan])
errors = nebula.execute(dprof, dback, plan, log=lines.append)
check("quick scan: that removal reports no error", errors == 0, (errors, lines[-2:]))

# A device folder that lists nothing must plan no removals: an unreadable mount looks
# exactly like an empty one.
empty_dst = os.path.join(HOME, "scan_empty")
os.makedirs(empty_dst)
eprof = nebula.Profile(name="Empty", device_id=f"folder:{empty_dst}", source=qsrc,
                        target="Music", method="hash", mode="mirror", music_folder="")
plan = nebula.compare(eprof, nebula.LocalFolderBackend(empty_dst))
check("quick scan: a device folder that lists nothing plans no removals",
      plan and all(a.kind in ("new", "restore") for a in plan),
      [(a.kind, a.rel) for a in plan])

# A sync must leave one copy of each file under the target: the manifest's device path
# already carries the target folder, and prefixing it again nested Music inside Music.
nest_src = os.path.join(HOME, "scan_nest_src")
nest_dst = os.path.join(HOME, "scan_nest_dst")
os.makedirs(os.path.join(nest_src, "Album"))
os.makedirs(nest_dst)
shutil.copyfile(WAV1, os.path.join(nest_src, "Album", "01.wav"))
nprof = nebula.Profile(name="Nest", device_id=f"folder:{nest_dst}", source=nest_src,
                        target="Music", method="hash", mode="mirror", music_folder="")
nback = nebula.LocalFolderBackend(nest_dst)
lines = []
nebula.execute(nprof, nback, nebula.compare(nprof, nback, log=lines.append),
                log=lines.append)
check("a sync leaves one copy under the target, with no target folder nested inside itself",
      sorted(os.path.relpath(os.path.join(r, n), nest_dst)
             for r, _d, f in os.walk(nest_dst) for n in f) == ["Music/Album/01.wav"]
      and not any("MISSING" in l for l in lines), (lines, sorted(os.walk(nest_dst))))
check("the manifest records the device path with one target prefix",
      (nebula.DeviceManifest(nprof).get("Music/Album/01.wav") or {}).get("dev")
      == "Music/Album/01.wav", nebula.DeviceManifest(nprof).files)

# autosync must wait for the phone to answer, not fire on the mount alone
locked_root = os.path.join(HOME, "locked_mtp")
os.makedirs(locked_root)
sync_tab = nebula.SyncTab({"library_folders": [src]})
locked = nebula.Device(id="mtp:locked", name="Locked Phone", kind="mtp",
                        root=locked_root, uri="mtp://locked/")
locked_store = os.path.join(locked_root, "Internal storage")
sync_tab.devices = [locked]
sync_tab.profiles = [nebula.Profile(name="Walkman", device_id=locked.id, source=src,
                                     target="Music", mode="update", autosync=True)]
check("device_ready is false for an empty mount", nebula.device_ready(locked) is False)
os.makedirs(locked_store)
check("device_ready is true once a storage answers", nebula.device_ready(locked) is True)
shutil.rmtree(locked_store)
# A ready answer from the previous connection must not start the sync on a re-plug.
sync_tab._ready_cache[locked.id] = (True, time.monotonic())
sync_tab.set_devices([locked], newly_connected=[locked])
check("autosync waits while the phone is still locked",
      sync_tab.worker is None and len(sync_tab.autosync_queue) == 1,
      (sync_tab.worker, len(sync_tab.autosync_queue)))
check("autosync does not trust a ready answer from the previous connection",
      not sync_tab._ready_cache.get(locked.id, (False,))[0], sync_tab._ready_cache)
check("waiting for the device is explained in the log",
      "Waiting for Locked Phone" in sync_tab.log.toPlainText(),
      sync_tab.log.toPlainText()[-120:])
check("autosync retry timer is armed", sync_tab._autosync_timer.isActive())
sync_tab.set_devices([], newly_connected=[])
check("unplugging while waiting drops the autosync",
      not sync_tab.autosync_queue and not sync_tab._autosync_timer.isActive(),
      sync_tab.autosync_queue)
check("the dropped autosync is reported",
      "autosync skipped" in sync_tab.log.toPlainText())

# Switching autosync on while the player is already here is a sync request too; before
# this, only plugging the device in queued one.
sync_tab.profiles = [nebula.Profile(name="Toggle", device_id=locked.id, source=src,
                                     target="Music", mode="update")]
sync_tab._reload_list(0)
sync_tab.set_devices([locked], newly_connected=[])
toggle = sync_tab.profiles[0]
sync_tab.autosync.setChecked(True)
check("autosync switched on while connected queues a run at once",
      toggle.autosync and len(sync_tab.autosync_queue) == 1
      and sync_tab.autosync_queue[0] is toggle,
      (toggle.autosync, len(sync_tab.autosync_queue)))
check("the queued run waits for the phone instead of firing on the mount",
      sync_tab.worker is None and sync_tab._autosync_timer.isActive(),
      (sync_tab.worker, sync_tab._autosync_timer.isActive()))
sync_tab.autosync.setChecked(False)
check("autosync switched off drops the queued run",
      not toggle.autosync and not sync_tab.autosync_queue
      and not sync_tab._autosync_timer.isActive(),
      (toggle.autosync, sync_tab.autosync_queue, sync_tab._autosync_timer.isActive()))

# the dot next to the device follows whether the phone can be read right now
section("sync tab: device status dot")
sync_tab.profiles = [sync_tab.profiles[0]]
sync_tab._reload_list(0)
sync_tab._show_profile(0)


def dot():
    return sync_tab.device_status.text()


def wait_ready(tab, device_id):
    """The readiness answer is asked on a worker: let it arrive before reading the dot."""
    for _ in range(300):
        app.processEvents()
        QTest.qWait(10)
        probe = getattr(tab, "_ready_probe", None)
        if not tab._ready_in_flight and (probe is None or not probe.isRunning()):
            break
    tab._ready_cache.pop(device_id, None)      # a refresh asks again, as the poll does
    tab.refresh_status()
    for _ in range(300):
        app.processEvents()
        QTest.qWait(10)
        if not tab._ready_in_flight:
            break
    app.processEvents()


sync_tab.set_devices([locked], newly_connected=[])
wait_ready(sync_tab, locked.id)
check("dot: a plugged-in phone that is not readable yet is gray",
      "waiting for File transfer" in dot() and nebula.MUTED in dot()
      and nebula.STATUS_GREEN not in dot(), dot())
os.makedirs(locked_store)
sync_tab._ready_cache.pop(locked.id, None)
sync_tab.refresh_status()  # what the device poll calls every few seconds
wait_ready(sync_tab, locked.id)
check("dot: turns green once the phone answers, without re-plugging",
      "connected" in dot() and nebula.STATUS_GREEN in dot(), dot())
shutil.rmtree(locked_store)
sync_tab._ready_cache.pop(locked.id, None)
sync_tab.refresh_status()
wait_ready(sync_tab, locked.id)
check("dot: back to gray when the phone stops answering",
      "waiting for File transfer" in dot() and nebula.MUTED in dot(), dot())
sync_tab.set_devices([], newly_connected=[])
check("dot: gray and 'not connected' once unplugged",
      "not connected" in dot() and nebula.MUTED in dot()
      and nebula.STATUS_GREEN not in dot(), dot())

# A sync owns the mount: the 3-second poll must not list it. That probe would queue
# behind the transfer on gvfs and freeze the window for as long as the file takes.
section("sync tab: no device probe while a sync is running")
ready = nebula.Device(id="mtp:ready", name="Ready Phone", kind="mtp",
                      root=locked_root, uri="mtp://ready/")
kept_profiles, kept_devices = list(sync_tab.profiles), list(sync_tab.devices)
os.makedirs(locked_store)
sync_tab.devices = [ready]
sync_tab.profiles = [nebula.Profile(name="Phone", device_id=ready.id, source=src,
                                     target="Music", method="hash")]
sync_tab._reload_list(0)
sync_tab._show_profile(0)
probes = []
real_ready = nebula.device_ready
nebula.device_ready = lambda d: (probes.append(d.id), real_ready(d))[1]
try:
    # A task owns the device: the claim is what the poll and the dot both read now,
    # so no probe is started at all.
    nebula.DEVICE_CLAIMS.claim(locked_root, "test-claim", "Syncing Phone\u2026")
    sync_tab.refresh_status()
    check("a syncing device is not listed by the poll", not probes, probes)
    check("the dot says syncing, in amber",
          "syncing" in dot() and nebula.AMBER in dot(), dot())
    check("the tooltip says the library comes back after the sync",
          "read again" in sync_tab.device_status.toolTip(),
          sync_tab.device_status.toolTip())
    nebula.DEVICE_CLAIMS.release("test-claim")
    sync_tab._ready_cache.pop(ready.id, None)
    sync_tab.refresh_status()
    for _ in range(300):
        app.processEvents()
        QTest.qWait(10)
        if not sync_tab._ready_in_flight:
            break
    app.processEvents()
    check("once idle the poll reads the device again", probes == [ready.id], probes)
    check("and the dot is green again",
          "connected" in dot() and nebula.STATUS_GREEN in dot(), dot())
finally:
    nebula.DEVICE_CLAIMS.release("test-claim")
    nebula.device_ready = real_ready
    shutil.rmtree(locked_store, ignore_errors=True)
    sync_tab.profiles, sync_tab.devices = kept_profiles, kept_devices
    sync_tab._reload_list(0)
    sync_tab._show_profile(0)

# last sync: a Compare leaves it alone, a finished sync records and saves the time,
# and the status line shows it
section("sync tab: last sync time")
lp = sync_tab.profiles[0]
sync_tab._refresh_device_status()
check("a profile that never synced says so", "never synced" in dot(), dot())
sync_tab._done(([], 0), False, lp)
check("a Compare does not record a sync", lp.last_sync == "", lp.last_sync)
sync_tab._done(([], 0), True, lp)
stamp = lp.last_sync
check("a finished sync records the time as YYYY-MM-DD HH:MM",
      len(stamp) == 16 and stamp[4] == "-" and stamp[10] == " ", stamp)
check("the sync time is saved with the profile",
      any(q.id == lp.id and q.last_sync == stamp for q in nebula.load_profiles()))
check("the status line shows the last sync time", f"last sync {stamp}" in dot(), dot())
check("a finished run ends the bar on Done, not on 0% when nothing needed copying",
      (sync_tab._finish_progress(False), sync_tab.progress.format(),
       sync_tab.progress.value(), sync_tab.progress.maximum())[1:]
      == ("Done", 100, 100),
      (sync_tab.progress.format(), sync_tab.progress.value()))
check("a cancelled run says Stopped instead of claiming it finished",
      (sync_tab.progress.setFormat("%p%"), sync_tab._finish_progress(True),
       sync_tab.progress.format())[2] == "Stopped", sync_tab.progress.format())
check("a bit-by-bit sync adds no last-verified note: that compare was exact",
      "verified" not in dot() and lp.last_sync_method == "bytes",
      (dot(), lp.last_sync_method))

# In Fast hash the manifest is trusted, so the line says when the device contents were
# last read in full — and says plainly when they never were.
section("sync tab: last verified")
hp = nebula.Profile(name="Phone", device_id=f"folder:{hdst}", source=hsrc, target="Music",
                     method="hash", mode="update", last_sync="2026-10-27 09:00",
                     last_sync_method="hash")
sync_tab.profiles = [hp]
sync_tab._reload_list(0)
sync_tab._show_profile(0)
check("a hash profile whose device files were never read says so",
      "not verified in full" in dot() and "last verified" not in dot(), dot())
hp.last_verified = "2026-10-27 09:05"
sync_tab._refresh_device_status()
check("a hash profile shows when the device contents were last verified",
      "last verified 2026-10-27 09:05" in dot(), dot())
check("the tooltip admits the manifest is trusted, not proof",
      "hashed in full" in sync_tab.device_status.toolTip(),
      sync_tab.device_status.toolTip())
hp.last_sync_method = "bytes"
sync_tab._refresh_device_status()
check("after a bit-by-bit sync there is no note: that sync was exact",
      "verified" not in dot(), dot())
hp.last_sync_method = "hash"
hp.method = "bytes"
sync_tab._refresh_device_status()
check("Bit-by-bit mode needs no last-verified note at all",
      "verified" not in dot(), dot())

# What a finished run records: a fast compare claims nothing, a fast sync records its
# method, and only a run that read the device copies claims a verification.
section("sync tab: recording verification and method")
rec = nebula.SyncTab({"library_folders": [src]})
rp = nebula.Profile(name="Rec", device_id=f"folder:{hdst}", source=hsrc, target="Music",
                     method="hash", mode="update")
rec.profiles = [rp]
rec._reload_list(0)
rec._show_profile(0)
rec._verify_used = False
rec._done(([], 0), False, rp)
check("a fast compare claims no verification and records no sync",
      rp.last_verified == "" and rp.last_sync == "", (rp.last_verified, rp.last_sync))
rec._done(([], 0), True, rp)
check("a fast sync records the time and the method it used, not a verification",
      bool(rp.last_sync) and rp.last_sync_method == "hash" and rp.last_verified == "",
      (rp.last_sync, rp.last_sync_method, rp.last_verified))
rec._verify_used = True
rec._verify_stats = {"device_files": 1, "device_read": 1,
                     "device_unreadable": 0, "matches": 1}
rec._done(([], 0), True, rp)
check("a verified sync also records when the device was last verified",
      rp.last_verified == rp.last_sync and rp.last_verified != ""
      and "last verified" in rec.device_status.text(),
      (rp.last_verified, rec.device_status.text()))
check("the verification time is saved with the profile",
      any(q.id == rp.id and q.last_verified == rp.last_verified
          for q in nebula.load_profiles()), rp.last_verified)
# An empty folder proves nothing, however fast it is: no verification stamp and no
# claim that matches were exact.
rp.last_verified = ""
rec._verify_used = True
rec._verify_stats = {}
rec._done(([], 0), False, rp)
check("an empty verification does not claim the device was verified",
      rp.last_verified == "" and "empty" in rec.status.text()
      and "nothing was verified" in rec.status.text(),
      (rp.last_verified, rec.status.text()))
bp = nebula.Profile(name="Bytes", device_id=f"folder:{hdst}", source=hsrc, target="Music",
                     method="bytes", mode="update")
rec.profiles = [bp]
rec._reload_list(0)
rec._show_profile(0)
rec._verify_used = False
rec._done(([], 0), False, bp)
check("a bit-by-bit compare records that the device copies were read",
      bp.last_verified != "" and bp.last_sync == "", (bp.last_verified, bp.last_sync))
# put the shared tab back on its own profile, so the checks below drive that one
sync_tab.profiles = [lp]
sync_tab._reload_list(0)

# Compare by: Bit-by-bit or Fast hash; picking one saves it to the profile
section("sync tab: Compare by option")
check("Compare by offers Bit-by-bit and Fast hash",
      [sync_tab.method.itemData(i) for i in range(sync_tab.method.count())] == ["bytes", "hash"]
      and sync_tab.method.itemText(0).startswith("Bit-by-bit")
      and sync_tab.method.itemText(1).startswith("Fast hash"),
      [sync_tab.method.itemText(i) for i in range(sync_tab.method.count())])
check("the Bit-by-bit note admits it reads the device copy in full",
      "reads every file on the device" in sync_tab.method.toolTip()
      and "trusts the sync manifest" in sync_tab.method.toolTip(),
      sync_tab.method.toolTip())
sync_tab.method.setCurrentIndex(sync_tab.method.findData("hash"))
check("choosing Fast hash saves it to the profile",
      lp.method == "hash" and any(q.id == lp.id and q.method == "hash"
                                  for q in nebula.load_profiles()), lp.method)
check("Fast hash offers the Verify content button and admits it is not proof",
      sync_tab.verify_btn.isVisibleTo(sync_tab) and sync_tab.verify_btn.isEnabled()
      and sync_tab.verify_btn.text() == "Verify content"
      and "trusts the sync manifest" in sync_tab.method.toolTip()
      and "read and hash every file" in sync_tab.verify_btn.toolTip().lower(),
      (sync_tab.verify_btn.isVisibleTo(sync_tab), sync_tab.method.toolTip(),
       sync_tab.verify_btn.toolTip()))
check("the profile form has three check boxes, including LRC",
      [b.text() for b in sync_tab.findChildren(nebula.QCheckBox)]
      == ["Only audio files", "Include LRC files", "Autosync"],
      [b.text() for b in sync_tab.findChildren(nebula.QCheckBox)])

# Include LRC files: the picker lists audio, but the matching lyric sidecar travels
# with a selected audio file. It must also survive the profile save/load round trip.
sync_tab.include_lrc.setChecked(True)
check("Include LRC files is saved to the profile",
      sync_tab.current().include_lrc
      and any(q.id == sync_tab.current().id and q.include_lrc
              for q in nebula.load_profiles()), sync_tab.current())
sync_tab.include_lrc.setChecked(False)
check("Include LRC files can be switched off again",
      not sync_tab.current().include_lrc
      and not any(q.id == sync_tab.current().id and q.include_lrc
                  for q in nebula.load_profiles()), sync_tab.current())

lrc_dir = os.path.join(HOME, "lrc-sync")
os.makedirs(os.path.join(lrc_dir, "Artist", "Album"))
lrc_audio = os.path.join(lrc_dir, "Artist", "Album", "01.flac")
lrc_file = os.path.join(lrc_dir, "Artist", "Album", "01.lrc")
shutil.copyfile(FLAC1, lrc_audio)
with open(lrc_file, "w", encoding="utf-8") as f:
    f.write("[00:01.00]line one\n")
lrc_profile = nebula.Profile(name="LRC", source=lrc_dir, sources=[lrc_dir],
                             selection_mode="selected",
                             selection=[{"path": lrc_audio,
                                         "rel": "Artist/Album/01.flac",
                                         "kind": "music"}],
                             audio_only=True, include_lrc=True, target="Music")
lrc_files = nebula.profile_sync_files(lrc_profile, True)
check("Include LRC files adds the sidecar to selected audio",
      len(lrc_files) == 2 and lrc_file in [p for p, _s in lrc_files.values()], lrc_files)
lrc_profile.include_lrc = False
check("LRC is absent when the option is off",
      len(nebula.profile_sync_files(lrc_profile, True)) == 1)
lrc_profile.include_lrc = True
lrc_device = os.path.join(HOME, "lrc-device")
os.makedirs(lrc_device)
lrc_backend = nebula.LocalFolderBackend(lrc_device)
lrc_plan = nebula.compare(lrc_profile, lrc_backend)
lrc_errors = nebula.execute(lrc_profile, lrc_backend, lrc_plan)
lrc_dev_file = os.path.join(lrc_device, "Music", "Artists", "Artist", "Album", "01.lrc")
check("Include LRC files copies the sidecar to the device",
      lrc_errors == 0 and os.path.exists(lrc_dev_file), (lrc_errors, lrc_dev_file))
check("the copied LRC is equal on the next compare",
      all(a.kind == "equal" for a in nebula.compare(lrc_profile, lrc_backend)))
sync_tab.method.setCurrentIndex(sync_tab.method.findData("bytes"))
check("Bit-by-bit hides the Verify content button because the compare is already exact",
      not sync_tab.verify_btn.isVisibleTo(sync_tab) and not sync_tab.verify_btn.isEnabled()
      and "reads every file on the device" in sync_tab.method.toolTip(),
      (sync_tab.verify_btn.isVisibleTo(sync_tab), sync_tab.method.toolTip()))

# Device filesystem: the file name a device can store is a property of the profile.
section("sync tab: device filesystem")
check("the picker offers FAT32, exFAT and MTP and starts on FAT32",
      [sync_tab.filesystem.itemData(i) for i in range(sync_tab.filesystem.count())]
      == ["fat32", "exfat", "mtp"]
      and sync_tab.filesystem.currentData() == "fat32" and sync_tab.filesystem.isEnabled(),
      [sync_tab.filesystem.itemText(i) for i in range(sync_tab.filesystem.count())])
check("the FAT32 note names what cannot be stored and what still is",
      all(ch in nebula.FILESYSTEM_NOTES["fat32"] for ch in ('*', '?', '"', '<', '>', '|'))
      and "ends in a space or a dot" in nebula.FILESYSTEM_NOTES["fat32"]
      and "Spaces" in nebula.FILESYSTEM_NOTES["fat32"], nebula.FILESYSTEM_NOTES["fat32"])
sync_tab.filesystem.setCurrentIndex(sync_tab.filesystem.findData("exfat"))
check("choosing exFAT saves it to the profile",
      lp.filesystem == "exfat"
      and any(q.id == lp.id and q.filesystem == "exfat" for q in nebula.load_profiles()),
      lp.filesystem)
check("the exFAT line promises the name is kept character for character",
      sync_tab.filesystem_note.text() == "Names stay exactly as on the PC"
      and not sync_tab.filesystem_note.wordWrap()
      and "not one character is changed" in sync_tab.filesystem.toolTip()
      and "UTF-16" in sync_tab.filesystem.toolTip(),
      (sync_tab.filesystem_note.text(), sync_tab.filesystem.toolTip()))
check("the line is short and does not wrap, so a squeezed form cannot overlap rows",
      not sync_tab.filesystem_note.wordWrap()
      and len(sync_tab.filesystem_note.text()) <= 45
      and sync_tab.filesystem_note.sizeHint().height() <= 22,
      (sync_tab.filesystem_note.text(), sync_tab.filesystem_note.sizeHint()))
sync_tab.filesystem.setCurrentIndex(sync_tab.filesystem.findData("fat32"))
check("the FAT32 line says the names lose something, and the tooltip says what",
      sync_tab.filesystem_note.text() == "Names lose what FAT32 cannot store"
      and all(ch in sync_tab.filesystem.toolTip() for ch in ('*', '?', '"', '<', '>', '|'))
      and "ends in a space or a dot" in sync_tab.filesystem_note.toolTip()
      and sync_tab.filesystem_note.toolTip() == sync_tab.filesystem.toolTip(),
      (sync_tab.filesystem_note.text(), sync_tab.filesystem.toolTip()))
sync_tab.filesystem.setCurrentIndex(sync_tab.filesystem.findData("exfat"))
check("the MTP note says the same and names the mode that reports a refused name",
      "not one character is changed" in nebula.FILESYSTEM_NOTES["mtp"]
      and "ERROR" in nebula.FILESYSTEM_NOTES["mtp"], nebula.FILESYSTEM_NOTES["mtp"])
sync_tab.plan = [nebula.Action("new", "a.wav", 10, "a.wav")]
sync_tab.filesystem.setCurrentIndex(sync_tab.filesystem.findData("mtp"))
check("changing the filesystem drops a reviewed plan: its names were made for the old one",
      sync_tab.plan is None and lp.filesystem == "mtp", (sync_tab.plan, lp.filesystem))
sync_tab.filesystem.setCurrentIndex(sync_tab.filesystem.findData("fat32"))
check("back on FAT32 the profile is stored as FAT32 again",
      lp.filesystem == "fat32"
      and any(q.id == lp.id and q.filesystem == "fat32" for q in nebula.load_profiles()),
      lp.filesystem)
empty_fs_tab = nebula.SyncTab({"library_folders": [src]})
empty_fs_tab.profiles = []
empty_fs_tab._reload_list(0)
check("with no profile chosen the filesystem picker is off",
      not empty_fs_tab.filesystem.isEnabled(), empty_fs_tab.filesystem.isEnabled())

lp.method = "hash"
sync_tab.plan_verify = False
check("a reviewed plan keeps the verification level it was compared with",
      sync_tab._verify_choice(lp, reuse_plan=True) is False
      and sync_tab._verify_choice(lp, force=True) is True,
      (sync_tab._verify_choice(lp, reuse_plan=True), sync_tab._verify_choice(lp, force=True)))
check("verification is never chosen without the button, and never for autosync",
      sync_tab._verify_choice(lp) is False
      and sync_tab._verify_choice(lp, auto=True, force=True) is False
      and sync_tab._verify_choice(lp, reuse_plan=True, force=True) is False,
      (sync_tab._verify_choice(lp), sync_tab._verify_choice(lp, auto=True, force=True)))
lp.method = "bytes"
check("Bit-by-bit ignores a forced verification: it reads both copies anyway",
      sync_tab._verify_choice(lp, force=True) is False, sync_tab._verify_choice(lp, force=True))

# The Verify content button must run a compare that reads the device, so stand in
# for the worker thread and watch what the click decides.


class _QuietSignal:
    def connect(self, *_a, **_k):
        pass


class QuietWorker:
    """A Worker that accepts its signals and never starts, so a run can be inspected."""
    progress = log = done = failed = _QuietSignal()

    def __init__(self, fn, parent=None):
        self.fn = fn

    def isRunning(self):
        return False

    def start(self):
        pass


real_worker = nebula.Worker
verify_tab = nebula.SyncTab({"library_folders": [src]})
verify_tab.profiles = [hprof]
verify_tab._reload_list(0)
verify_tab._show_profile(0)
try:
    nebula.Worker = QuietWorker
    hprof.method = "hash"
    verify_tab._method_changed()
    verify_tab.verify_btn.click()
finally:
    nebula.Worker = real_worker
check("pressing Verify content compares with a full read of the device copies",
      verify_tab._verify_used is True, verify_tab._verify_used)
check("the running verification is the button highlighted, not Compare",
      verify_tab.verify_btn.objectName() == "Primary"
      and verify_tab.compare_btn.objectName() == ""
      and verify_tab.sync_btn.objectName() == "",
      (verify_tab.verify_btn.objectName(), verify_tab.compare_btn.objectName()))
verify_tab._idle()
check("and it goes back to grey when it is done",
      verify_tab.verify_btn.objectName() == "" and verify_tab.compare_btn.objectName() == "",
      verify_tab.verify_btn.objectName())
try:
    nebula.Worker = QuietWorker
    hprof.method = "bytes"
    verify_tab._method_changed()
    verify_tab.verify_btn.click()
finally:
    nebula.Worker = real_worker
check("a click that cannot verify nothing (Bit-by-bit) asks for no verification",
      verify_tab._verify_used is False, verify_tab._verify_used)
hprof.method = "hash"

# Neither mode disappears for MTP: transport changes the cost, not the choice.
mtp_ui = nebula.SyncTab({"library_folders": [src]})
mtp_ui.devices = [nebula.Device(id="mtp:ui", name="Phone", kind="mtp",
                                 root=mtp_hash_root, uri="mtp://phone/")]
mtp_ui.profiles = [nebula.Profile(name="MTP", device_id="mtp:ui", source=hsrc,
                                   target="Music", method="hash")]
mtp_ui._reload_list(0)
mtp_ui._show_profile(0)
check("both comparison modes stay available for an MTP device",
      mtp_ui.method.isEnabled() and mtp_ui.method.count() == 2
      and mtp_ui.verify_btn.isEnabled(),
      (mtp_ui.method.count(), mtp_ui.verify_btn.isEnabled()))

section("sync: trust wording")
word_tab = nebula.SyncTab({"library_folders": [src]})
word_tab.profiles = [hprof]
word_tab._reload_list(0)
word_tab._show_profile(0)
hprof.method = "hash"
word_tab._verify_used = False
word_tab._done((nebula.compare(hprof, hback), 0), False, hprof)
check("a fast compare says the equal files were not verified byte for byte",
      "not verified byte for byte" in word_tab.status.text()
      and "cached, unverified" in word_tab.summary.text(),
      (word_tab.status.text(), word_tab.summary.text()))
word_tab._verify_used = True
word_tab._verify_stats = {"device_files": 2, "device_read": 2,
                          "device_unreadable": 0, "matches": 2}
word_tab._done(([], 0), False, hprof)
check("a verified compare says the device was hashed in full and the manifest rebuilt",
      "hashed" in word_tab.status.text() and "manifest" in word_tab.status.text(),
      word_tab.status.text())
hprof.method = "bytes"
word_tab._done(([], 0), False, hprof)
check("a bit-by-bit compare says every file was compared byte for byte",
      word_tab.status.text().startswith("Bit-by-bit")
      and "byte for byte" in word_tab.status.text(), word_tab.status.text())
word_tab._show_plan([nebula.Action("restore", hb_rel, 1234, hb_rel)], "hash", False)
check("restore rows are labelled and counted separately",
      word_tab.table.rowCount() == 2
      and "copied back" in word_tab.table.item(0, 0).text()
      and "restore" in word_tab.table.item(1, 0).text().lower()
      and "Restored 1" in word_tab.summary.text(),
      (word_tab.table.item(0, 0).text(), word_tab.table.item(1, 0).text(),
       word_tab.summary.text()))
word_tab._show_plan([nebula.Action("equal", hb_rel, 10, hb_rel, "0" * 64, verified=True,
                                    extra=True),
                     nebula.Action("equal", ha_rel, 10, ha_rel, "1" * 64),
                     nebula.Action("delete", "stray.wav", 10, "stray.wav", extra=True)],
                    "hash", False)
check("the summary counts scanned extras apart from equal files",
      "Equal 1" in word_tab.summary.text() and "Extra 2" in word_tab.summary.text(),
      word_tab.summary.text())
hprof.method = "hash"

# Compare / Sync / Compare+Sync: Compare plans only, Sync runs the reviewed plan,
# Compare+Sync compares fresh and then runs it
section("sync tab: Compare, Sync and Compare+Sync")
check("buttons are named Compare, Sync and Compare+Sync",
      (sync_tab.compare_btn.text(), sync_tab.sync_btn.text(), sync_tab.both_btn.text())
      == ("Compare", "Sync", "Compare+Sync"),
      (sync_tab.compare_btn.text(), sync_tab.sync_btn.text(), sync_tab.both_btn.text()))

real_box = nebula.QMessageBox
messages = []


class QuietBox:
    """Stands in for QMessageBox so the headless run never blocks on a dialog."""
    Yes = real_box.Yes

    @staticmethod
    def question(*_a, **_k):
        return real_box.Yes

    @staticmethod
    def information(*a, **_k):
        messages.append(a[2])

    warning = information


def wait_for(tab):
    tab.worker.wait(20000)
    for _ in range(10):
        app.processEvents()


nebula.QMessageBox = QuietBox
try:
    sync_tab.profiles = [hprof]
    sync_tab._reload_list(0)
    sync_tab._show_profile(0)
    sync_tab.run(sync=False)
    wait_for(sync_tab)
    check("Compare plans the Beta deletion and does not touch the device",
          sync_tab.plan_profile == hprof.id
          and any(a.kind == "delete" and a.rel == hb_rel for a in sync_tab.plan)
          and os.path.exists(hdev_beta),
          (sync_tab.plan_profile, [(a.kind, a.rel) for a in sync_tab.plan or []]))

    ha3 = os.path.join(hsrc, album, "03 - Gamma.wav")
    hdev_gamma = os.path.join(hdst, "Music", album, "03 - Gamma.wav")
    shutil.copyfile(WAV1, ha3)
    sync_tab.run(sync=True, reuse_plan=True)
    wait_for(sync_tab)
    check("Sync runs only the reviewed plan, so the new Gamma file waits",
          not os.path.exists(hdev_gamma) and not os.path.exists(hdev_beta),
          os.path.exists(hdev_gamma))

    sync_tab.run(sync=True)
    wait_for(sync_tab)
    check("Compare+Sync compares fresh and copies the new Gamma file",
          os.path.exists(hdev_gamma))

    messages.clear()
    sync_tab.plan = None
    sync_tab.run(sync=True, reuse_plan=True)
    check("Sync with no reviewed list asks for Compare first",
          messages and "Compare" in messages[-1] and not sync_tab.worker.isRunning(), messages)
finally:
    nebula.QMessageBox = real_box

# buttons are grey at rest and blue only for the task that is running
sync_tab._set_busy(None)
check("idle buttons are not highlighted",
      sync_tab.compare_btn.objectName() == "" and sync_tab.sync_btn.objectName() == "",
      (sync_tab.compare_btn.objectName(), sync_tab.sync_btn.objectName()))
sync_tab._set_busy("compare")
check("Compare turns blue while comparing",
      sync_tab.compare_btn.objectName() == "Primary" and sync_tab.sync_btn.objectName() == "")
sync_tab._set_busy("sync")
check("Sync turns blue while syncing",
      sync_tab.sync_btn.objectName() == "Primary" and sync_tab.compare_btn.objectName() == "")
check("Verify content is an ordinary button, not a ghost one",
      sync_tab.verify_btn.objectName() == ""
      and sync_tab.verify_btn.objectName() == sync_tab.compare_btn.objectName()
      and sync_tab.verify_btn.objectName() == sync_tab.both_btn.objectName(),
      (sync_tab.verify_btn.objectName(), sync_tab.compare_btn.objectName()))
sync_tab._set_busy("verify")
check("Verify content turns blue while verifying, and Compare stays grey",
      sync_tab.verify_btn.objectName() == "Primary"
      and sync_tab.compare_btn.objectName() == ""
      and sync_tab.sync_btn.objectName() == "",
      (sync_tab.verify_btn.objectName(), sync_tab.compare_btn.objectName()))
sync_tab._idle()
check("finishing returns every button to grey",
      sync_tab.compare_btn.objectName() == "" and sync_tab.sync_btn.objectName() == ""
      and sync_tab.verify_btn.objectName() == "",
      (sync_tab.compare_btn.objectName(), sync_tab.verify_btn.objectName()))
seen = []
sync_tab.activity.connect(seen.append)
sync_tab._running_name = "Walkman"
sync_tab._on_progress(17, 20, "Syncing 01.wav")
check("activity reports profile name and percent", seen and seen[-1] == "Walkman 85%", seen)
glyph = nebula.sync_glyph(15).toImage()
white = sum(1 for x in range(glyph.width()) for y in range(glyph.height())
            if glyph.pixelColor(x, y).alpha() > 128
            and min(glyph.pixelColor(x, y).red(), glyph.pixelColor(x, y).green(),
                    glyph.pixelColor(x, y).blue()) > 200)
check("sync glyph draws white strokes", white >= 6, white)

# ---------------------------------------------------------------- migration
section("v2 database migration")
legacy_path = os.path.join(HOME, "legacy.db")
conn = sqlite3.connect(legacy_path)
conn.execute("CREATE TABLE tracks (path TEXT PRIMARY KEY, mtime REAL, "
             + ", ".join(f"{f} TEXT" for f in nebula.FIELDS) + ", length REAL)")
old_cols = ["path", "mtime"] + nebula.FIELDS + ["length"]
conn.execute(f"INSERT INTO tracks ({','.join(old_cols)}) VALUES ({','.join('?' * len(old_cols))})",
             [WAV2, os.path.getmtime(WAV2), "Beta", "Aphex Twin", "Selected Ambient Works",
              "", "2", "", "1992", "Electronic", "", 3.0])
conn.commit()
conn.close()
legacy = nebula.Library(legacy_path)
check("v2 database opens and migrates", legacy.count() == 1, legacy.count())
legacy.scan([MUSIC])
legacy_rows = {r["path"]: r for r in legacy.tracks()}
check("rescan fills the new spec columns", legacy_rows[WAV2]["sample_rate"] == 44100,
      legacy_rows[WAV2].get("sample_rate"))
legacy.play_count(WAV2)
legacy.scan([MUSIC])
check("migrated rows keep play counts on rescan",
      {r["path"]: r for r in legacy.tracks()}[WAV2]["play_count"] == 1)

# ---------------------------------------------------------------- filters
section("Strawberry filter language")


def fq(text):
    where, params = nebula.parse_filter(text)
    return w.library.tracks(where=where, args=params)


check("empty filter is a no-op", nebula.parse_filter("") == ("", []))
check("filter: field term", len(fq("artist:aphex")) == 2, len(fq("artist:aphex")))
check("filter: quoted value", len(fq('album:"Selected Ambient Works"')) == 2)
check("filter: numeric comparison", len(fq("samplerate:>=96000")) == 1)
check("filter: bitrate with k suffix", len(fq("bitrate:>1m")) == 2,
      len(fq("bitrate:>1m")))
check("filter: bitrate picks the compressed flac", len(fq("bitrate:<10k")) == 1,
      len(fq("bitrate:<10k")))
check("filter: bare word searches all text fields", len(fq("pop")) == 2)
check("filter: negation", len(fq("electronic -title:gamma")) == 2)
check("filter: OR", len(fq("title:alpha OR title:delta")) == 2)
check("filter: parentheses", len(fq("(title:alpha OR title:beta) artist:aphex")) == 2)
check("filter: year", len(fq("year:1987")) == 2)
check("filter: length comparison", len(fq("length:<2")) == 1, len(fq("length:<2")))
check("filter: duration parsing", nebula.parse_filter("length:>=1:00")[1] == [60.0])
check("filter: unknown field falls back to text", len(fq("bogus:alpha")) == 0,
      len(fq("bogus:alpha")))
try:
    nebula.parse_filter('artist:"unclosed')
    raised = False
except nebula.FilterError:
    raised = True
check("filter: unbalanced quote raises FilterError", raised)

tab.search.setText("artist:aphex")
tab.refresh()
check("filter box drives the tree", len(tracks_in_tree(tab.tree)) == 2,
      len(tracks_in_tree(tab.tree)))
check("filter hint reports the match count", "2 match" in tab.filter_hint.text(),
      tab.filter_hint.text())
tab.search.setText('artist:"unclosed')
tab.refresh()
check("broken filter falls back to a text search", len(tracks_in_tree(tab.tree)) == 0,
      len(tracks_in_tree(tab.tree)))
tab.search.setText("")
tab.refresh()

# ---------------------------------------------------------------- rating/skip
section("ratings, loved, skip counts")
w.library.set_rating([WAV1, WAV2], 5)
rows = {r["path"]: r for r in w.library.tracks()}
check("rating stored", rows[WAV1]["rating"] == 5 and rows[WAV2]["rating"] == 5)
check("rating filter", len(fq("rating:>=5")) == 2)
w.library.set_rating([WAV1], 0)
check("clearing a rating", {r["path"]: r for r in w.library.tracks()}[WAV1]["rating"] == 0)
w.library.set_loved([WAV1], True)
check("loved flag stored", {r["path"]: r for r in w.library.tracks()}[WAV1]["loved"] == 1)
w.library.increment_skip(WAV1)
w.library.increment_skip(WAV1)
check("skip counter increments", {r["path"]: r for r in w.library.tracks()}[WAV1]["skipcount"] == 2)
w.library.scan([MUSIC])
kept = {r["path"]: r for r in w.library.tracks()}
check("rescan keeps rating, loved and skip counts",
      kept[WAV2]["rating"] == 5 and kept[WAV1]["loved"] == 1 and kept[WAV1]["skipcount"] == 2,
      (kept[WAV2]["rating"], kept[WAV1]["loved"], kept[WAV1]["skipcount"]))

tab.refresh()
check("tooltip mentions the rating and the loved flag",
      "★★★★★" in next(i for i in tracks_in_tree(tab.tree)
                       if i.data(0, nebula.PATH_ROLE) == WAV2).toolTip(0))

# ---------------------------------------------------------------- grouping
section("grouping dialog, details columns and sorting")
tab.config["grouping"] = "artist_album"
tab.config["lib_details"] = True
tab.refresh()
header = [tab.tree.headerItem().text(i) for i in range(tab.tree.columnCount())]
check("details header follows the configured columns",
      header == [nebula.LIB_COLUMN_LABELS[k] for k in tab.config["lib_columns"]], header)
rating_col = tab.columns.index("rating")
wav2_item = next(i for i in tracks_in_tree(tab.tree)
                 if i.data(0, nebula.PATH_ROLE) == WAV2)
check("rating column shows stars", wav2_item.text(rating_col) == "★★★★★",
      wav2_item.text(rating_col))
album_node = find_item(tab.tree, "Selected Ambient Works")
check("album node shows the year and the album length",
      album_node is not None
      and album_node.text(tab.columns.index("year")) == "1992"
      and album_node.text(tab.columns.index("length")) == "0:05",
      album_node.text(tab.columns.index("year")) if album_node else "missing")

dialog = nebula.GroupByDialog(tab, ["genre", "album"], [])
dialog.combos[0].setCurrentIndex(dialog.combos[0].findData("composer"))
dialog.combos[1].setCurrentIndex(dialog.combos[1].findData("album"))
check("group-by dialog picks three levels", dialog.pick() == ["composer", "album"], dialog.pick())
dialog.saved = [{"name": "Wide", "levels": ["artist", "album"]}]
dialog._refresh_saved()
check("saved grouping list renders", dialog.saved_list.count() == 1)
dialog.close()

tab.config["saved_groupings"] = [{"name": "By composer", "levels": ["composer", "album"]}]
tab._rebuild_saved_menu()
tab.apply_saved_grouping(tab.config["saved_groupings"][0])
check("applying a saved grouping",
      tab.config["grouping"] == "custom" and tab.config["grouping_levels"] == ["composer", "album"],
      (tab.config["grouping"], tab.config["grouping_levels"]))
check("saved grouping builds the tree", len(tracks_in_tree(tab.tree)) == 5)
check("composer nodes appear",
      any(tab._node_label(item) == "Unknown composer" for item in all_items(tab.tree)))

tab.config["grouping"] = "custom"
tab.config["grouping_levels"] = ["genre", "artist", "album"]
tab.refresh()
genre_nodes = [item for item in all_items(tab.tree)
               if item.data(0, nebula.KIND_ROLE) == "group"]
check("three-level grouping builds genre nodes",
      any(tab._node_label(node) == "Electronic" for node in genre_nodes),
      [tab._node_label(n) for n in genre_nodes])
electronic = next(n for n in genre_nodes if tab._node_label(n) == "Electronic")
check("three-level grouping nests artists under the genre",
      electronic.child(0).data(0, nebula.KIND_ROLE) == "artist")

tab.config["grouping"] = "none"
tab.refresh()
check("flat list puts songs at the top level", tab.tree.topLevelItemCount() == 5,
      tab.tree.topLevelItemCount())
tab._sort_by_column(tab.columns.index("length"))
lengths = [float(tab._rows_cache[tab.tree.topLevelItem(i).data(0, nebula.PATH_ROLE)]["length"])
           for i in range(tab.tree.topLevelItemCount())]
check("header click sorts by length", lengths == sorted(lengths), lengths)
tab._sort_by_column(tab.columns.index("length"))
lengths = [float(tab._rows_cache[tab.tree.topLevelItem(i).data(0, nebula.PATH_ROLE)]["length"])
           for i in range(tab.tree.topLevelItemCount())]
check("second header click reverses the order", lengths == sorted(lengths, reverse=True), lengths)
tab._sort_by_column(tab.columns.index("length"))
check("third header click restores the album order", tab.lib_sort is None)

# ---------------------------------------------------------------- covers
section("cover grid and view toggles")
tab.config["grouping"] = "artist_album"
tab.refresh()
tab.set_library_mode("covers")
check("covers mode switches the stack", tab.stack.currentWidget() is tab.covers)
check("cover grid groups artists", tab.covers.count() == 3, tab.covers.count())
check("cover tiles have artwork", not tab.covers.item(0).icon().isNull())

# A click opens an album; a double-click queues it and must never also open it.
first_cover = tab.covers.item(0)
cover_paths = list(first_cover.data(Qt.UserRole))
cover_title = first_cover.text().split("\n")[0]
QTest.mouseClick(tab.covers.viewport(), Qt.LeftButton, Qt.NoModifier,
                 tab.covers.visualItemRect(first_cover).center())
for _ in range(120):
    app.processEvents()
    QTest.qWait(10)
    if tab._album_focus is not None:
        break
check("a single click opens that album",
      tab._album_focus is not None and sorted(tab._album_focus[0]) == sorted(cover_paths),
      tab._album_focus)
check("the opened album shows its tracks and nothing else",
      tab.stack.currentWidget() is tab.tree
      and sorted(i.data(0, nebula.PATH_ROLE) for i in tracks_in_tree(tab.tree))
      == sorted(cover_paths), len(tracks_in_tree(tab.tree)))
check("the bar above the list names the album",
      not tab.album_bar.isHidden() and tab.album_title.text() == cover_title,
      (tab.album_bar.isHidden(), tab.album_title.text()))
tab.close_album()
check("back goes to the cover grid again",
      tab._album_focus is None and tab.stack.currentWidget() is tab.covers
      and tab.album_bar.isHidden())

tab.set_library_mode("covers")
tab.open_album(cover_paths, cover_title)
tab.set_library_mode("list")
check("choosing List leaves an opened album behind",
      tab._album_focus is None and tab.album_bar.isHidden())
tab.set_library_mode("covers")
tab.refresh()
second_cover = tab.covers.item(1)
queue_paths = list(second_cover.data(Qt.UserRole))
tab.player.clear_queue()
cover_point = tab.covers.visualItemRect(second_cover).center()
double_click(tab.covers, cover_point)
for _ in range(60):
    app.processEvents()
    QTest.qWait(10)
    if tab.player.queue:
        break
QTest.qWait(max(120, QApplication.doubleClickInterval()) + 120)
app.processEvents()
check("a double-click still queues the album",
      sorted(tab.player.queue) == sorted(queue_paths), tab.player.queue)
check("and a double-click never opens it on the way", tab._album_focus is None)
tab.player.clear_queue()

check("the covers tooltip mentions both gestures",
      "Click to open" in tab.covers.item(0).toolTip()
      and "queue" in tab.covers.item(0).toolTip(), tab.covers.item(0).toolTip())
tab.set_library_mode("list")
check("list mode switches back", tab.stack.currentWidget() is tab.tree)

tab.config["lib_details"] = True
tab.refresh()
before_cols = tab.tree.columnCount()
tab._toggle_column("album", False)
check("hiding a column updates the table", tab.tree.columnCount() == before_cols - 1,
      (before_cols, tab.tree.columnCount(), tab.config.get("lib_columns")))
tab._toggle_column("album", True)
check("showing a column again", tab.tree.columnCount() == before_cols,
      (before_cols, tab.tree.columnCount()))

tab._toggle_details(False)
check("details off leaves a single column", tab.tree.columnCount() == 1 and tab.tree.isHeaderHidden())
tab._toggle_details(True)
check("details on restores the columns", tab.tree.columnCount() == before_cols)
tab.config["lib_show_dividers"] = False
tab.refresh()
check("dividers can be hidden",
      not any(tab.tree.topLevelItem(i).data(0, nebula.KIND_ROLE) == "divider"
              for i in range(tab.tree.topLevelItemCount())))
tab.config["lib_show_dividers"] = True
tab.refresh()

labels = [a.text() for a in tab.library_menu.actions()]
check("library menu offers grouping and duplicates",
      "Group by…" in labels and "Find duplicates…" in labels, labels)

# ---------------------------------------------------------------- actions
section("library actions: queue next, locate, search, organize, duplicates")
tab.player.set_queue([WAV1, WAV2], 0)
tab.queue_next([FLAC1])
check("queue to play next inserts after the current track",
      tab.player.queue == [WAV1, FLAC1, WAV2] and tab.player.index == 0, tab.player.queue)

tab.player.clear_queue()
tab.refresh()
tab.tree.expandAll()
wav1_item = next(i for i in tracks_in_tree(tab.tree)
                 if i.data(0, nebula.PATH_ROLE) == WAV1)
QTest.mouseClick(tab.tree.viewport(), Qt.MiddleButton, Qt.NoModifier,
                 tab.tree.visualItemRect(wav1_item).center())
check("middle click enqueues the track", tab.player.queue == [WAV1], tab.player.queue)

tab.player.set_queue([WAV1, WAV2], 0)
tab.player._stopped = False        # locate playing needs a current track, not a stopped queue
tab.refresh()
tab.locate_playing()
check("locate playing selects the current track",
      tab.tree.currentItem() is not None
      and tab.tree.currentItem().data(0, nebula.PATH_ROLE) == WAV1)
tab.search_for_path(WAV2)
check("search for this builds a field filter", tab.search.text().startswith('artist:"Aphex Twin"'),
      tab.search.text())
tab.search.setText("")
tab.refresh()

stats = w.library.stats()
check("collection statistics", stats["tracks"] == w.library.count() and stats["length"] > 0
      and stats["albums"] >= 3, stats)

org_root = os.path.join(HOME, "organize")
os.makedirs(org_root)
org_src = os.path.join(org_root, "loose.wav")
shutil.copyfile(WAV1, org_src)
org_tags = nebula.read_tags(org_src)
pattern = "%artist%/%album%/%tracknumber% - %title%"
expected_rel = nebula.format_path_pattern(org_tags, pattern)
check("pattern formatter pads the track number",
      expected_rel.startswith("Aphex Twin/Selected Ambient Works/01 - "), expected_rel)
results = nebula.organize_paths([org_src], pattern, org_root)
expected = os.path.join(org_root, expected_rel + ".wav")
check("organize moves the file into the pattern path",
      os.path.exists(expected) and not os.path.exists(org_src), (expected, results))
check("organize reports the new path", results and results[0][1] == expected, results)

dup_dir = os.path.join(HOME, "dups")
os.makedirs(dup_dir)
dup_a = os.path.join(dup_dir, "a.wav")
dup_b = os.path.join(dup_dir, "b.wav")
for dup in (dup_a, dup_b):
    shutil.copyfile(WAV1, dup)
    nebula.write_tags(dup, {"title": "Twin", "artist": "Duplicate Artist",
                             "album": "Two Copies", "tracknumber": "1"})
    w.library.update_track(dup)
groups = [g for g in w.library.duplicate_groups() if len(g) == 2
          and {r["path"] for r in g} == {dup_a, dup_b}]
check("duplicate finder groups identical tracks", len(groups) == 1, groups)
dup_dialog = nebula.DuplicateDialog(w.library, w)
header_item = next(dup_dialog.tree.topLevelItem(i)
                   for i in range(dup_dialog.tree.topLevelItemCount())
                   if dup_dialog.tree.topLevelItem(i).childCount() == 2
                   and dup_dialog.tree.topLevelItem(i).child(0).text(0) in ("a.wav", "b.wav"))
states = [header_item.child(j).checkState(0) for j in range(header_item.childCount())]
check("duplicates default to keeping the first",
      states[0] == Qt.Unchecked and states[1] == Qt.Checked, states)
count_before = w.library.count()
dup_dialog.remove_selected()
check("removing duplicates drops one library row", w.library.count() == count_before - 1,
      (count_before, w.library.count()))
check("removing duplicates leaves the files on disk",
      os.path.exists(dup_a) and os.path.exists(dup_b))
duplicate_row = next(p for p in (dup_a, dup_b) if p not in dup_dialog.removed)
w.library.forget(duplicate_row)
dup_dialog.close()
tab.refresh()

# ---------------------------------------------------------------- A-Z details
section("A-Z hierarchy details and track labels")
tab.config["grouping"] = "artist_album"
tab.refresh()
tab.tree.expandAll()
app.processEvents()
title_col = tab.columns.index("title")
alpha_node = next(i for i in tracks_in_tree(tab.tree)
                  if i.data(0, nebula.PATH_ROLE) == WAV1)
check("tracks are labelled '01. Title'",
      "01. " in alpha_node.text(title_col)
      and alpha_node.text(title_col).endswith("Alpha (Remastered)"),
      alpha_node.text(title_col))
album_node = find_item(tab.tree, "Selected Ambient Works")
check("album nodes keep their artwork slot",
      album_node is not None and album_node.childCount() > 0)
tab.config["lib_track_prefix"] = False
tab.refresh()
tab.tree.expandAll()
alpha_node = next(i for i in tracks_in_tree(tab.tree)
                  if i.data(0, nebula.PATH_ROLE) == WAV1)
check("track-number prefix can be turned off",
      "01. " not in alpha_node.text(title_col)
      and alpha_node.text(title_col).endswith("Alpha (Remastered)"),
      alpha_node.text(title_col))
tab.config["lib_track_prefix"] = True
tab.refresh()

# ---------------------------------------------------------------- folder nesting
section("folder grouping nests as deep as the filesystem")
nest_root = os.path.join(HOME, "nested")
nest_first = os.path.join(nest_root, "First")
nest_second = os.path.join(nest_first, "Second")
os.makedirs(nest_second)
nest_deep = os.path.join(nest_second, "Deep")
os.makedirs(nest_deep)
nest_a = os.path.join(nest_deep, "01 - Alpha.wav")
nest_b = os.path.join(nest_first, "02 - Beta.wav")
shutil.copyfile(WAV1, nest_a)
shutil.copyfile(WAV2, nest_b)
w.library.update_track(nest_a)
w.library.update_track(nest_b)
old_folders = list(tab.config["library_folders"])
tab.config["library_folders"] = [nest_root] + old_folders
tab.config["grouping"] = "custom"
tab.config["grouping_levels"] = ["folder", "album"]
tab.refresh()
tab.tree.expandAll()
first_node = find_item(tab.tree, "First")
second_node = find_item(tab.tree, "Second")
deep_node = find_item(tab.tree, "Deep")
check("folder level creates one node per directory", first_node is not None
      and second_node is not None and deep_node is not None)
check("sub-folders nest instead of consuming the level",
      second_node is not None and second_node.parent() is first_node,
      second_node.parent().text(0) if second_node is not None else "missing")
check("remaining grouping levels continue below the deepest folder",
      any(i.data(0, nebula.KIND_ROLE) == "album" for i in all_items(deep_node))
      if deep_node is not None else False)
check("tracks under the nested folder are reachable",
      any(i.data(0, nebula.PATH_ROLE) == nest_a for i in tracks_in_tree(tab.tree)))
check("a file directly in the first folder is kept",
      any(i.data(0, nebula.PATH_ROLE) == nest_b for i in tracks_in_tree(tab.tree)))
tab.config["grouping"] = "artist_album"
tab.config["library_folders"] = old_folders
w.library.remove_paths([nest_a, nest_b])
tab.refresh()

# ---------------------------------------------------------------- delete / trash
section("delete to trash")
trash_copy = os.path.join(HOME, "delete-me.wav")
shutil.copyfile(WAV1, trash_copy)
w.library.update_track(trash_copy)
removed, failed = w.library.delete_paths([trash_copy], to_trash=True)
trashed = os.path.join(nebula.DATA_ROOT, "trash", "files", "delete-me.wav")
check("delete_paths removes the file", removed == [trash_copy]
      and not os.path.exists(trash_copy), (removed, failed))
check("the file lands in the Trash", os.path.exists(trashed), trashed)
check("the library row is gone", trash_copy not in w.library.by_path())
check("trashinfo was written",
      os.path.exists(os.path.join(nebula.DATA_ROOT, "trash", "info",
                                  "delete-me.wav.trashinfo")))

# ---------------------------------------------------------------- ReplayGain
section("ReplayGain")
rg_copy = os.path.join(HOME, "rg.wav")
shutil.copyfile(WAV2, rg_copy)
check("ReplayGain tags are written", nebula.write_replaygain(rg_copy, -7.5, 0.98, -6.0, 0.99))
rg = nebula.read_replaygain(rg_copy)
check("ReplayGain tags read back", rg["track_gain"] is not None
      and abs(rg["track_gain"] + 7.5) < 0.01
      and abs(rg["album_gain"] + 6.0) < 0.01
      and abs(rg["track_peak"] - 0.98) < 0.001, rg)
check("-6.02 dB is a half-volume factor",
      abs(nebula.replaygain_factor(-6.02) - 0.5) < 0.01,
      nebula.replaygain_factor(-6.02))
check("peak guard caps a boost",
      abs(nebula.replaygain_factor(6.0, 0.0, 0.5) - 2.0) < 0.01,
      nebula.replaygain_factor(6.0, 0.0, 0.5))
check("pre-amp shifts the factor",
      nebula.replaygain_factor(-6.02, 6.02) > 0.99)
check("ebur128 output parses",
      nebula.parse_ebur128("    I:         -23.0 LUFS\n"
                            "    Peak:       -1.0 dBFS") == (-23.0, -1.0))
w.library.update_track(rg_copy)
check("the library stores the gain",
      abs(w.library.by_path()[rg_copy]["rg_track_gain"] + 7.5) < 0.01,
      w.library.by_path()[rg_copy].get("rg_track_gain"))
w.player._rg_values = rg
w.player.set_rg_mode("track")
w.player.vol.setValue(100)
w.player._apply_volume()
check("track gain is applied to the output volume",
      abs(w.player.audio.volume() - nebula.replaygain_factor(-7.5, 0.0, 0.98)) < 0.02,
      w.player.audio.volume())
check("the RG button reflects the mode", w.player.rg_btn.text().startswith("RG"))
w.player.set_rg_mode("off")
w.player.vol.setValue(70)
w.player._apply_volume()
check("turning ReplayGain off restores the plain volume",
      abs(w.player.audio.volume() - 0.7) < 0.02, w.player.audio.volume())
w.library.remove_paths([rg_copy])

# ---------------------------------------------------------------- online lookup
section("MusicBrainz parsing and the lookup dialog")
search_payload = {"releases": [{
    "id": "11111111-2222-3333-4444-555555555555",
    "title": "Selected Ambient Works",
    "date": "1992-02-12", "country": "GB", "track-count": 2, "score": 100,
    "artist-credit": [{"name": "Aphex Twin"}],
    "release-group": {"primary-type": "Album"},
    "label-info": [{"label": {"name": "Apollo"}}],
}]}
releases = nebula.parse_mb_releases(search_payload)
check("release search parses", len(releases) == 1
      and releases[0]["title"] == "Selected Ambient Works"
      and releases[0]["artist"] == "Aphex Twin"
      and releases[0]["tracks"] == 2
      and releases[0]["labels"] == ["Apollo"], releases)
release_payload = {
    "id": "11111111-2222-3333-4444-555555555555",
    "title": "Selected Ambient Works",
    "date": "1992-02-12",
    "artist-credit": [{"name": "Aphex Twin"}],
    "label-info": [{"label": {"name": "Apollo"}}],
    "genres": [{"name": "ambient techno"}],
    "media": [{"position": 1, "tracks": [
        {"number": "1", "title": "Xtal", "length": 294000},
        {"number": "2", "title": "Tha", "length": 546000},
    ]}],
}
release = nebula.parse_mb_release(release_payload)
check("release details parse", release["title"] == "Selected Ambient Works"
      and release["date"] == "1992-02-12"
      and release["genres"] == ["ambient techno"]
      and [t["title"] for t in release["tracks"]] == ["Xtal", "Tha"], release)
check("cover art URL", nebula.caa_front_url("abc", 250)
      == "https://coverartarchive.org/release/abc/front-250")

calls = []
real_http_get = nebula.http_get
real_interval = nebula.MB_MIN_INTERVAL
real_delay = nebula.MB_RETRY_DELAY
nebula.MB_MIN_INTERVAL = 0.0
nebula.MB_RETRY_DELAY = 0.0

def flaky_get(url, timeout=10, accept="application/json"):
    calls.append(url)
    if len(calls) < 3:
        raise urllib.error.HTTPError(url, 503, "Service Temporarily Unavailable", {}, None)
    return json.dumps(search_payload).encode("utf-8")

nebula.http_get = flaky_get
try:
    retried = nebula.mb_search_releases("Aphex Twin", "Selected Ambient Works")
finally:
    nebula.http_get = real_http_get
    nebula.MB_MIN_INTERVAL = real_interval
    nebula.MB_RETRY_DELAY = real_delay
check("a 503 answer is retried until the search succeeds",
      len(retried) == 1 and len(calls) == 3, (len(retried), len(calls)))
check("503 failures explain what to do",
      "503" in nebula.mb_error_text("HTTPError: HTTP Error 503: "
                                     "Service Temporarily Unavailable"))

calls[:] = []
def fallback_get(url, timeout=10, accept="application/json"):
    calls.append(url)
    if len(calls) == 1:
        return json.dumps({"releases": []}).encode("utf-8")
    return json.dumps(search_payload).encode("utf-8")

nebula.http_get = fallback_get
nebula.MB_MIN_INTERVAL = 0.0
try:
    loose = nebula.mb_search_releases("Aphex Twin", "Selected Ambient Works")
finally:
    nebula.http_get = real_http_get
    nebula.MB_MIN_INTERVAL = real_interval
check("an empty artist+album search falls back to the album",
      len(loose) == 1 and len(calls) == 2, (len(loose), len(calls)))
mb_copy = os.path.join(HOME, "mb.wav")
mb_copy2 = os.path.join(HOME, "mb2.wav")
shutil.copyfile(WAV1, mb_copy)
shutil.copyfile(WAV2, mb_copy2)
w.library.update_track(mb_copy)
w.library.update_track(mb_copy2)
mb_rows = [w.library.by_path()[mb_copy], w.library.by_path()[mb_copy2]]
mb_dialog = nebula.OnlineLookupDialog(mb_rows, w.library, w)
check("dialog pre-fills the artist and album", mb_dialog.artist_edit.text() == "Aphex Twin"
      and "Selected Ambient Works" in mb_dialog.album_edit.text(),
      (mb_dialog.artist_edit.text(), mb_dialog.album_edit.text()))
mb_dialog._show_results(releases)
check("results fill the list and enable the buttons",
      mb_dialog.results_list.count() == 1 and mb_dialog.apply_btn.isEnabled())
mb_dialog._apply_release(release)
mb_tags = nebula.read_tags(mb_copy)
check("applying a release writes album tags",
      mb_tags["album"] == "Selected Ambient Works"
      and mb_tags["albumartist"] == "Aphex Twin"
      and mb_tags["title"] == "Xtal"
      and mb_tags["date"] == "1992", mb_tags)
check("applying a release refreshes the library row",
      w.library.by_path()[mb_copy]["title"] == "Xtal")
mb_dialog.close()
w.library.remove_paths([mb_copy, mb_copy2])

# ---------------------------------------------------------------- collections
section("multiple collections")
cols = nebula.migrate_collections(w.config)
check("a default collection exists", len(cols) == 1 and cols[0]["folders"] == [MUSIC],
      cols)
other_db = nebula.new_collection_db("Second")
w.config["collections"].append({"name": "Second", "folders": [], "db": other_db})
w.switch_collection(1)
check("switching changes the database file",
      os.path.abspath(w.library.db_file) == os.path.abspath(other_db),
      (w.library.db_file, other_db))
check("the new collection starts empty", w.library.count() == 0, w.library.count())
check("the collection combo follows",
      w.library_tab.collection_combo.currentText() == "Second")
w.config["library_folders"].append(MUSIC)
nebula.store_active_collection(w.config)
w.library.scan([MUSIC])
check("the second collection scans its own folders", w.library.count() == 5,
      w.library.count())
w.switch_collection(0)
check("switching back restores the first library", w.library.count() >= 5,
      w.library.count())
check("the first collection still holds its tracks", FLAC1 in w.library.by_path())
check("the collection combo is back on the first entry",
      w.library_tab.collection_combo.currentIndex() == 0)

# ---------------------------------------------------------------- columns / spectrum
section("draggable columns and decoded spectrum")
header = tab.tree.header()
check("the header is movable", header.sectionsMovable())
before_order = list(w.config["lib_columns"])
if len(before_order) > 1:
    header.moveSection(header.visualIndex(0), len(before_order) - 1)
    app.processEvents()
check("dragging a column persists the new order",
      w.config["lib_columns"] != before_order
      and sorted(w.config["lib_columns"]) == sorted(before_order),
      (before_order, w.config["lib_columns"]))
w.config["lib_columns"] = before_order
tab.refresh()
wave = [0.5 * math.sin(2 * math.pi * 1000 * i / 44100) for i in range(512)]
levels = nebula.spectral_levels(wave, 44100)
check("spectral levels come from real samples",
      len(levels) == nebula.SPECTRUM_BANDS and max(levels) > 0.3,
      (len(levels), max(levels) if levels else None))
decoder = nebula.DecodedSpectrum(w.player, w.player.spectrum)
decoder.levels = {0: [0.1] * nebula.SPECTRUM_BANDS,
                  40: [0.9] * nebula.SPECTRUM_BANDS}
check("decoded frames are indexed by play position",
      decoder.levels_at(3200)[0] == 0.9 and decoder.levels_at(100)[0] == 0.1)
check("the player exposes its tap mode", w.player.tap.mode in ("buffer", "decoder", ""))

# ---------------------------------------------------------------- 0.52 shuffle and preferences
section("0.52 shuffle modes, album order and preferences")
import random

ORDER_ROWS = [
    {"path": "a1", "artist": "Artist A", "album": "Alpha", "tracknumber": "2", "title": "b",
     "play_count": 5, "rating": 3, "loved": 0},
    {"path": "a2", "artist": "Artist A", "album": "Alpha", "tracknumber": "1", "title": "a",
     "play_count": 1, "rating": 5, "loved": 1},
    {"path": "b1", "artist": "Artist B", "album": "Beta", "tracknumber": "1", "title": "c",
     "play_count": 9, "rating": 0, "loved": 0},
    {"path": "b2", "artist": "Artist B", "album": "Beta", "tracknumber": "2", "title": "d",
     "play_count": 2, "rating": 4, "loved": 0},
]
SEEDS = range(25)


def order_paths(mode, album="in_order", seed=1):
    return [r["path"] for r in nebula.order_queue(ORDER_ROWS, mode, album, random.Random(seed))]


ALBUM_BLOCKS = (["a2", "a1", "b1", "b2"], ["b1", "b2", "a2", "a1"])
check("in order keeps the selection order", order_paths("off") == ["a1", "a2", "b1", "b2"])
check("shuffle albums keeps each album's tracks in order",
      all(order_paths("albums", seed=s) in ALBUM_BLOCKS for s in SEEDS))
check("shuffle albums varies with the seed",
      len({tuple(order_paths("albums", seed=s)) for s in SEEDS}) == 2)
check("album order setting applies to in-order play",
      all(order_paths("off", "shuffle_albums", s) in ALBUM_BLOCKS for s in SEEDS))
check("shuffle artists keeps each artist's albums together",
      all(order_paths("artists", seed=s) in ALBUM_BLOCKS for s in SEEDS))
check("shuffle inside albums keeps albums in order",
      all(set(order_paths("inside", seed=s)[:2]) == {"a1", "a2"}
          and set(order_paths("inside", seed=s)[2:]) == {"b1", "b2"} for s in SEEDS))
check("shuffle all keeps every track",
      all(sorted(order_paths("shuffle", seed=s)) == ["a1", "a2", "b1", "b2"] for s in SEEDS))
ARTIST_OF = {r["path"]: r["artist"] for r in ORDER_ROWS}
check("spread artists never repeats an artist back to back",
      all(all(ARTIST_OF[a] != ARTIST_OF[b] for a, b in zip(order, order[1:]))
          for order in (order_paths("spread", seed=s) for s in SEEDS)))
check("loved tracks come first", all(order_paths("loved", seed=s)[0] == "a2" for s in SEEDS))
check("least played first", order_paths("least_played") == ["a2", "b2", "a1", "b1"],
      order_paths("least_played"))
check("most played first", order_paths("most_played") == ["b1", "a1", "b2", "a2"],
      order_paths("most_played"))
check("top rated first", order_paths("top_rated") == ["a2", "b2", "a1", "b1"],
      order_paths("top_rated"))

dialog = nebula.PreferencesDialog(tab, w)
check("preferences has theme, library, audiobooks, devices, playback, sync, backup, CD and identification pages",
      dialog.sidebar.count() == 9 and dialog.pages.count() == 9
      and [dialog.sidebar.item(i).text() for i in range(9)]
      == ["Theme", "Library", "Audiobooks", "Devices", "Playback", "Syncing",
          "Backup", "Audio CD", "Identification"],
      [dialog.sidebar.item(i).text() for i in range(dialog.sidebar.count())])
combo = dialog.widgets["shuffle_mode"]
combo.setCurrentIndex(combo.findData("least_played"))
dialog.widgets["album_play_order"].setCurrentIndex(
    dialog.widgets["album_play_order"].findData("shuffle_albums"))
dialog.widgets["lib_show_dividers"].setChecked(False)
dialog._ok()
saved = nebula.load_config()
check("preferences OK saves the playback and library settings",
      saved["shuffle_mode"] == "least_played" and saved["album_play_order"] == "shuffle_albums"
      and saved["lib_show_dividers"] is False, saved)
check("preferences apply to the open library", tab.config["shuffle_mode"] == "least_played")
dialog.close()

# Theme: the built-in templates, the colour swatches and the accent.
tdlg = nebula.PreferencesDialog(tab, w)
strip_before = tab.strip_buttons["collection"].icon().pixmap(24, 24).toImage()
check("the theme page offers the three templates plus Custom",
      [tdlg.theme_combo.itemData(i) for i in range(tdlg.theme_combo.count())]
      == ["light", "dark", "black", "custom"],
      [tdlg.theme_combo.itemData(i) for i in range(tdlg.theme_combo.count())])
check("the templates are different palettes",
      len({tuple(sorted(t.items())) for t in nebula.THEME_TEMPLATES.values()}) == 3)
tdlg.theme_combo.setCurrentIndex(tdlg.theme_combo.findData("light"))
check("choosing a template fills the palette",
      tdlg._theme_palette()["bg"] == nebula.THEME_TEMPLATES["light"]["bg"]
      and tdlg._theme_palette()["text"] == nebula.THEME_TEMPLATES["light"]["text"],
      str(tdlg.theme_state))
check("the swatches show the template colours",
      all(tdlg.swatches[k][1].text() == nebula.THEME_TEMPLATES["light"][k] for k in ("bg", "panel", "accent")),
      tdlg.swatches["bg"][1].text())
real_color = nebula.QColorDialog.getColor
nebula.QColorDialog.getColor = lambda *a, **k: QColor("#c04a2a")
try:
    tdlg._pick_color("accent")
finally:
    nebula.QColorDialog.getColor = real_color
check("a colour picked by hand switches to Custom and keeps the template as its base",
      tdlg.theme_combo.currentData() == "custom"
      and tdlg._theme_palette()["accent"] == "#c04a2a"
      and tdlg._theme_palette()["bg"] == nebula.THEME_TEMPLATES["light"]["bg"],
      str(tdlg.theme_state))
check("the accent's hover colour follows the accent",
      tdlg._theme_palette()["accent_hover"] != nebula.THEME_TEMPLATES["light"]["accent_hover"],
      tdlg._theme_palette()["accent_hover"])
tdlg._ok()
saved_theme = nebula.load_config().get("theme") or {}
check("Preferences saves the theme",
      nebula.theme_settings({"theme": saved_theme})["palette"]["accent"] == "#c04a2a",
      str(saved_theme))
check("applying the theme restyles the window", "#c04a2a" in app.styleSheet())
check("the sidebar icons are redrawn for the new palette",
      tab.strip_buttons["collection"].icon().pixmap(24, 24).toImage() != strip_before)
check("the palette is live for the painters", nebula.ACCENT == "#c04a2a", nebula.ACCENT)
tdlg._theme_reset()
check("reset to template drops the colours changed by hand",
      tdlg._theme_palette()["accent"] == nebula.THEME_TEMPLATES["light"]["accent"],
      str(tdlg.theme_state))
tdlg.theme_combo.setCurrentIndex(tdlg.theme_combo.findData("dark"))
tdlg._ok()
check("switching back to Dark restores the dark palette",
      nebula.ACCENT == nebula.THEME_TEMPLATES["dark"]["accent"], nebula.ACCENT)

# The line around buttons: saved with the theme, and actually drawn.
section("theme: the line around buttons")
check("the theme page has an outline width and colour",
      tdlg.btn_border_width.minimum() == 0 and tdlg.btn_border_width.maximum() >= 6
      and bool(tdlg.btn_border_color.toolTip()), tdlg.btn_border_width.maximum())
check("a width is clamped to something sane",
      nebula.button_border_settings({"button_border": {"width": 99}})["width"] == 8
      and nebula.button_border_settings({"button_border": {"width": -4}})["width"] == 0)
check("an empty colour follows the template's button line",
      nebula.theme_settings({"theme": {"base": "dark"}})["button_border"]["color"]
      == nebula.THEME_TEMPLATES["dark"]["button_border"],
      nebula.theme_settings({"theme": {"base": "dark"}})["button_border"])
tdlg.btn_border_width.setValue(3)
real_color = nebula.QColorDialog.getColor
nebula.QColorDialog.getColor = lambda *a, **k: QColor("#ff8800")
try:
    tdlg._pick_button_border_color()
except Exception as exc:  # pragma: no cover - the picker must not raise
    check("the outline colour picker runs", False, repr(exc))
finally:
    nebula.QColorDialog.getColor = real_color
check("the picker stores the outline colour and width",
      tdlg.theme_state["button_border"]["color"] == "#ff8800"
      and tdlg.btn_border_width.value() == 3, tdlg.theme_state["button_border"])
tdlg._ok()
saved_border = nebula.theme_settings(nebula.load_config())["button_border"]
check("Preferences saves the outline with the theme",
      saved_border == {"width": 3, "color": "#ff8800"}, saved_border)
check("the window's stylesheet draws that line",
      "border: 3px solid #ff8800" in app.styleSheet())


def grab_button(width, color):
    """Render a real button with an outline and count the pixels of its colour."""
    nebula.apply_theme(app, {"theme": {"template": "dark", "base": "dark", "colors": {},
                                        "button_border": {"width": width, "color": color}}})
    button = nebula.QPushButton("Sample")
    button.resize(140, 34)
    button.show()
    app.processEvents()
    image = button.grab().toImage()
    button.close()
    wanted = QColor(color)
    return sum(1 for y in range(image.height()) for x in range(image.width())
               if image.pixelColor(x, y) == wanted)


thick_pixels = grab_button(3, "#ff8800")
thin_pixels = grab_button(1, "#ff8800")
no_pixels = grab_button(0, "#ff8800")
check("a thicker outline paints more of the colour",
      thick_pixels > thin_pixels > 0, (thick_pixels, thin_pixels))
check("0 px draws no line at all", no_pixels == 0, no_pixels)
w.apply_theme()
check("the window is back on the saved theme", nebula.BTN_BORDER_W == 3,
      nebula.BTN_BORDER_W)
tdlg._theme_reset()
check("reset to template drops the outline back to the template's line",
      tdlg.theme_state["button_border"] == {"width": 1, "color": ""},
      tdlg.theme_state["button_border"])
tdlg._ok()
tdlg.close()

# Check boxes: the style's own box is a dark outline on a dark background and vanishes
# on Black AMOLED, so BranchArrowStyle paints it. Render one box per theme and look at
# the pixels instead of trusting the stylesheet.
section("theme: check box visibility")


def rel_luminance(color):
    c = QColor(color)

    def channel(value):
        value /= 255.0
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    return (0.2126 * channel(c.red()) + 0.7152 * channel(c.green())
            + 0.0722 * channel(c.blue()))


def contrast(a, b):
    la, lb = rel_luminance(a), rel_luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def grab_checkbox(theme, checked):
    nebula.set_palette(nebula.THEME_TEMPLATES[theme])
    app.setStyleSheet(nebula.build_style())
    box = nebula.QCheckBox("")
    box.setChecked(checked)
    box.resize(60, 20)
    box.show()
    app.processEvents()
    return box.grab().toImage()


def indicator_pixels(image, theme):
    """Pixels inside the left-hand indicator that differ from the widget background."""
    bg = QColor(nebula.THEME_TEMPLATES[theme]["bg"])
    out = []
    for y in range(image.height()):
        for x in range(1, min(15, image.width())):
            c = image.pixelColor(x, y)
            if (abs(c.red() - bg.red()) + abs(c.green() - bg.green())
                    + abs(c.blue() - bg.blue())) > 30:
                out.append(c)
    return out


check("no stylesheet rule takes the check box drawing away from the style",
      "::indicator" not in nebula.build_style(),
      "an indicator rule would drop the tick inside a filled box")
for theme_name, palette in nebula.THEME_TEMPLATES.items():
    check(f"{theme_name}: the unticked box outline contrasts with its background",
          contrast(palette["check_border"], palette["bg"]) >= 3.0
          and contrast(palette["check_border"], palette["panel"]) >= 3.0,
          (palette["check_border"], palette["bg"],
           round(contrast(palette["check_border"], palette["bg"]), 2)))
    outline = indicator_pixels(grab_checkbox(theme_name, False), theme_name)
    check(f"{theme_name}: an unticked box is drawn, not blended into the background",
          len(outline) >= 20, len(outline))
    filled = indicator_pixels(grab_checkbox(theme_name, True), theme_name)
    accent = QColor(palette["accent"])
    check(f"{theme_name}: a ticked box is filled with the accent colour",
          sum(1 for c in filled if abs(c.red() - accent.red()) + abs(c.green() - accent.green())
              + abs(c.blue() - accent.blue()) < 40) >= 40, len(filled))
    check(f"{theme_name}: the tick stays visible inside the ticked box",
          sum(1 for c in filled if c.lightness() >= 200) >= 6,
          sum(1 for c in filled if c.lightness() >= 200))
nebula.set_palette(nebula.THEME_TEMPLATES["dark"])
app.setStyleSheet(nebula.build_style())

w.tabs.setCurrentWidget(tab)
app.processEvents()
menus = {a.text().replace("&", ""): a.menu() for a in w.menuBar().actions()}
check("Tools > Preferences is bound to Ctrl+P",
      any(a.text() == "Preferences…" and a.shortcut().toString() == "Ctrl+P"
          for a in menus["Tools"].actions()))
as_menu = next(a.menu() for a in menus["Music"].actions() if a.text() == "Play selection as")
check("Music menu offers every shuffle mode",
      [a.text() for a in as_menu.actions()] == [label for _k, label, _h in nebula.SHUFFLE_MODES],
      [a.text() for a in as_menu.actions()])

tab.player.clear_queue()
tab.refresh()
tab.tree.expandAll()
tab.tree.clearSelection()
for item in tracks_in_tree(tab.tree):
    if item.data(0, nebula.PATH_ROLE) in (WAV1, WAV2):
        item.setSelected(True)
tab._enqueue_paths(tab.selected_paths(), mode="shuffle")
check("queueing with a mode keeps the selected tracks",
      sorted(tab.player.queue) == sorted([WAV1, WAV2]), tab.player.queue)
tab.player.clear_queue()
check("shuffle order helper keeps the same tracks",
      sorted(tab._ordered([WAV1, WAV2], "shuffle")) == sorted([WAV1, WAV2]))

tab.config["shuffle_mode"] = "off"
tab.config["album_play_order"] = "in_order"
tab.config["lib_show_dividers"] = True
nebula.save_config(tab.config)

# ---------------------------------------------------------------- audio CD
section("audio CD")
import subprocess  # noqa: E402
import time  # noqa: E402

REAL_READ_CD_TOC = nebula.read_cd_toc  # the tests below replace the module's name with a fake
# CDDB is looked up on every insert and the harness has no network, so it answers "not in
# the database" by default; the CDDB checks below swap in answers of their own.
REAL_CDDB_REQUEST = nebula.cddb_request
CDDB_MISS = "202 No match found.\n"
CDDB_DEFAULT_URL = nebula.CDDB_SERVERS[0][1]


def cddb_miss(command, server=""):
    return CDDB_MISS, server or CDDB_DEFAULT_URL


def reset_cddb():
    """Forget which CDDB server answered and which was skipped, between checks."""
    nebula.CDDB_STATE["url"] = ""
    nebula.CDDB_STATE["dead"].clear()


nebula.cddb_request = cddb_miss
reset_cddb()

# The app watches the drives on a thread of its own. These checks stop it and run one pass
# by hand (poll_cd below) so every insert and removal happens at a known point; the thread
# itself, and that it never touches a drive from the GUI thread, is checked further down.
w._cd_watcher.stop()
w._cd_watcher.wait(5000)

# The MusicBrainz documentation's test vector: tracks 1-6, lead-out 95462 (pregap included).
VECTOR_OFFSETS = [150, 15363, 32314, 46592, 63414, 80489]
VECTOR_LEADOUT = 95462
VECTOR_ID = "49HHV7Eb8UKF3aQiNmu1GR8vKTY-"
VECTOR_LBAS = [off - nebula.CD_PREGAP for off in VECTOR_OFFSETS]
VECTOR_LEADOUT_LBA = VECTOR_LEADOUT - nebula.CD_PREGAP
MB_RELEASE = {
    "id": "rel-test", "title": "Test Album", "date": "2001-02-03",
    "artist-credit": [{"name": "Test Artist", "joinphrase": ""}],
    "media": [{"discs": [{"id": VECTOR_ID}],
               "tracks": [{"position": i + 1, "title": f"Song {i + 1}"} for i in range(6)]}],
}


def fake_toc_ioctl(lbas, leadout_lba, data_tracks=()):
    """Stand-in for the kernel's CDROM table-of-contents ioctls."""
    def ioctl(fd, request, arg):
        if request == nebula.CD_IOCTL_TOC_HEADER:
            arg[0], arg[1] = 1, len(lbas)
            return 0
        if request == nebula.CD_IOCTL_TOC_ENTRY:
            number = arg[0]
            lba = leadout_lba if number == nebula.CD_LEADOUT else lbas[number - 1]
            adr_ctrl = 0x14 if number in data_tracks else 0x10  # control bit 0x04 marks data
            struct.pack_into("=BBBxi", arg, 0, number, adr_ctrl, 1, lba)
            return 0
        raise OSError("unexpected ioctl")
    return ioctl


def read_fake_disc(lbas, leadout_lba, data_tracks=()):
    """read_cd_toc over the fake ioctls, with os.open and os.close stubbed out."""
    real = (os.open, os.close, nebula.fcntl.ioctl)
    os.open = lambda path, flags: 99
    os.close = lambda fd: None
    nebula.fcntl.ioctl = fake_toc_ioctl(lbas, leadout_lba, data_tracks)
    try:
        return REAL_READ_CD_TOC("/dev/sr0")
    finally:
        os.open, os.close, nebula.fcntl.ioctl = real


def read_vector_disc():
    return read_fake_disc(VECTOR_LBAS, VECTOR_LEADOUT_LBA)


def fake_musicbrainz(by_disc_id):
    """mb_get stand-in. The release is found by disc ID, or only by table of contents."""
    seen = []

    def get(url, *args, **kwargs):
        seen.append(url)
        hit = "discid/-?toc=" in url or (by_disc_id and f"discid/{VECTOR_ID}?" in url)
        return json.dumps({"releases": [MB_RELEASE] if hit else []}).encode("utf-8")
    return get, seen


def probe_codec(path):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                           "stream=codec_name", "-of", "csv=p=0", path],
                          capture_output=True, text=True, check=True).stdout.strip()


def probe_bitrate(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=bit_rate",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout
    return int(float(out.strip()))


disc = read_vector_disc()
check("the table of contents reads all six audio tracks",
      [t.number for t in disc.audio_tracks] == [1, 2, 3, 4, 5, 6] and disc.leadout == VECTOR_LEADOUT_LBA,
      str(disc.leadout))
check("the disc ID matches the MusicBrainz test vector", disc.disc_id == VECTOR_ID, disc.disc_id)

mixed = read_fake_disc([0, 15213, 32164], 40000, data_tracks=(3,))
check("a data track is not listed as audio",
      [t.number for t in mixed.audio_tracks] == [1, 2] and not mixed.track(3).audio,
      str([t.audio for t in mixed.tracks]))
check("the disc ID covers the data track too",
      mixed.disc_id == nebula.mb_disc_id(1, 3, 40000, {1: 0, 2: 15213, 3: 32164}), mixed.disc_id)

try:
    read_fake_disc([0, 15213], 30000, data_tracks=(1, 2))
    refused = False
except OSError:
    refused = True
check("a data-only disc is refused", refused)

real_mb_get = nebula.mb_get
get, seen = fake_musicbrainz(by_disc_id=True)
nebula.mb_get = get
try:
    found = nebula.mb_lookup_disc(disc)
finally:
    nebula.mb_get = real_mb_get
check("a disc ID match fills in the release and the track titles",
      found and disc.album == "Test Album" and disc.artist == "Test Artist"
      and disc.date == "2001-02-03" and disc.track(1).title == "Song 1" and len(seen) == 1, str(seen))

fresh = read_vector_disc()
get, seen = fake_musicbrainz(by_disc_id=False)
nebula.mb_get = get
try:
    found = nebula.mb_lookup_disc(fresh)
finally:
    nebula.mb_get = real_mb_get
check("without a disc ID match, the table of contents finds the release",
      found and fresh.album == "Test Album" and len(seen) == 2
      and "toc=1+6+95462+150+15363+32314+46592+63414+80489&" in seen[1], str(seen))

# CDDB: a second, separately computed disc ID, so discs MusicBrainz has never seen still get
# names. The table of contents is the worked example from the freedb/cd-discid documentation.
CDDB_OFFSETS = [150, 23115, 42165, 60015, 79512, 101560, 118757, 136605, 159492, 176067, 198875]
CDDB_LEADOUT = 2957 * nebula.CD_FRAMES_PER_SECOND - nebula.CD_PREGAP


def cddb_disc(device="/dev/sr0", disc_id=""):
    return nebula.CdDisc(device,
                          [nebula.CdTrack(n + 1, off - nebula.CD_PREGAP, 0, True)
                           for n, off in enumerate(CDDB_OFFSETS)],
                          CDDB_LEADOUT, disc_id=disc_id)


cddb_example = cddb_disc()
check("the CDDB disc ID matches the freedb example", nebula.cddb_disc_id(cddb_example) == "7c0b8b0b",
      nebula.cddb_disc_id(cddb_example))

cddb_commands = []


def cddb_fake(query_answer=CDDB_MISS, read_answer="", url=CDDB_DEFAULT_URL):
    """cddb_request stand-in that records the command and answers query or read."""
    def request(command, server=""):
        cddb_commands.append(command)
        return (read_answer if command.startswith("cddb read") else query_answer), url
    return request


nebula.cddb_request = cddb_fake("200 rock 7c0b8b0b Test Artist / Test Album\n")
try:
    cddb_hits, cddb_url = nebula.cddb_query(cddb_example)
finally:
    nebula.cddb_request = cddb_miss
check("a CDDB lookup sends the disc ID, every frame offset and the lead-out in seconds",
      cddb_commands == ["cddb query 7c0b8b0b 11 " + " ".join(str(o) for o in CDDB_OFFSETS) + " 2957"],
      str(cddb_commands))
check("an exact CDDB answer names the category, the disc ID and the title",
      cddb_hits == [("rock", "7c0b8b0b", "Test Artist / Test Album")]
      and cddb_url == CDDB_DEFAULT_URL, str(cddb_hits))

cddb_commands.clear()
nebula.cddb_request = cddb_fake("210 Found exact matches, list follows (to be replaced)\n"
                                 "rock 7c0b8b0b First\njazz 0a0b0c0d Second\n.\n")
try:
    cddb_hits, _url = nebula.cddb_query(cddb_example)
finally:
    nebula.cddb_request = cddb_miss
check("a list of CDDB matches is kept in the server's order",
      [h[1] for h in cddb_hits] == ["7c0b8b0b", "0a0b0c0d"], str(cddb_hits))

cddb_commands.clear()
nebula.cddb_request = cddb_fake("202 No match found.\n")
try:
    cddb_missed = nebula.cddb_lookup_disc(cddb_disc())
finally:
    nebula.cddb_request = cddb_miss
check("a disc CDDB doesn't know isn't read further", cddb_missed is False
      and cddb_commands == ["cddb query 7c0b8b0b 11 " + " ".join(str(o) for o in CDDB_OFFSETS) + " 2957"],
      str(cddb_commands))

cddb_commands.clear()
nebula.cddb_request = cddb_fake(
    "200 rock 7c0b8b0b Test Artist / Test Album\n",
    "210 rock 7c0b8b0b CDDB record successfully read.\n"
    "DTITLE=Test Artist / Test Al\nDTITLE=bum\nDYEAR=2001\nDGENRE=Rock\n"
    "TTITLE0=First Song\nTTITLE1=Second\nTTITLE1= Song\nTTITLE2=Third\\nTake\n.\n")
cddb_filled = cddb_disc()
try:
    cddb_found = nebula.cddb_lookup_disc(cddb_filled)
finally:
    nebula.cddb_request = cddb_miss
check("CDDB fills the artist, album, year and the joined track titles",
      cddb_found and cddb_filled.artist == "Test Artist" and cddb_filled.album == "Test Album"
      and cddb_filled.date == "2001" and cddb_filled.track(1).title == "First Song"
      and cddb_filled.track(2).title == "Second Song" and cddb_filled.track(3).title == "Third\nTake",
      f"{cddb_filled.artist!r} {cddb_filled.album!r} {cddb_filled.track(2).title!r} "
      f"{cddb_filled.track(3).title!r}")
check("the read uses the category and disc ID the query returned",
      cddb_commands[-1] == "cddb read rock 7c0b8b0b", str(cddb_commands[-1:]))

nebula.cddb_request = cddb_fake("200 rock 7c0b8b0b x\n", "210 rock 7c0b8b0b read\n.\n")
cddb_empty = cddb_disc()
try:
    cddb_empty_found = nebula.cddb_lookup_disc(cddb_empty)
finally:
    nebula.cddb_request = cddb_miss
check("a CDDB entry with no names counts as no match, so the next source is tried",
      cddb_empty_found is False and cddb_empty.album == "", repr(cddb_empty.album))

# A CDDB server that is down must not end the lookup: the next one is asked, and the dead
# server is remembered so it doesn't cost every insert a wait.
reset_cddb()
check("CDDB tries GNUdb, then the freedb mirror, then RetroBridge",
      nebula.cddb_endpoints() == [url for _name, url in nebula.CDDB_SERVERS],
      str(nebula.cddb_endpoints()))

cddb_http_urls = []


def cddb_http(url, timeout=10, accept="application/json"):
    """http_get stand-in: GNUdb is down, the freedb mirror answers."""
    cddb_http_urls.append(url)
    if "gnudb.gnudb.org" in url:
        raise urllib.error.URLError(OSError(101, "Network is unreachable"))
    if "cmd=cddb+query" in url:
        return b"200 misc 7c0b8b0b Portishead / Dummy\n"
    return ("210 misc 7c0b8b0b entry follows\nDTITLE=Portishead / Dummy\nDYEAR=1994\n"
            "TTITLE0=Mysterons\nTTITLE1=Sour Times\n.\n").encode("utf-8")


real_http_get = nebula.http_get
nebula.cddb_request = REAL_CDDB_REQUEST      # the real request code, with only HTTP faked
nebula.http_get = cddb_http
try:
    fallback_disc = cddb_disc()
    fallback_found = nebula.cddb_lookup_disc(fallback_disc)
finally:
    nebula.http_get = real_http_get
    nebula.cddb_request = cddb_miss
check("a dead CDDB server is skipped and the next one names the disc",
      fallback_found and fallback_disc.artist == "Portishead" and fallback_disc.album == "Dummy"
      and fallback_disc.date == "1994" and fallback_disc.track(2).title == "Sour Times",
      f"{fallback_disc.artist!r} {fallback_disc.album!r} {fallback_disc.track(2).title!r}")
check("the next server asked is the freedb mirror",
      [url.split("?")[0] for url in cddb_http_urls[:2]]
      == [nebula.CDDB_SERVERS[0][1], nebula.CDDB_SERVERS[1][1]],
      str(cddb_http_urls[:2]))
check("the server that answered is remembered and tried first next time",
      nebula.CDDB_STATE["url"] == nebula.CDDB_SERVERS[1][1]
      and nebula.cddb_endpoints()[0] == nebula.CDDB_SERVERS[1][1], str(nebula.cddb_endpoints()))
check("the server that didn't answer is skipped while its cooldown lasts",
      nebula.CDDB_SERVERS[0][1] not in nebula.cddb_endpoints(), str(nebula.cddb_endpoints()))
nebula.CDDB_STATE["dead"][nebula.CDDB_SERVERS[0][1]] = (
    time.monotonic() - nebula.CDDB_DEAD_SECONDS - 1)
check("a skipped server is tried again after the cooldown",
      nebula.CDDB_SERVERS[0][1] in nebula.cddb_endpoints(), str(nebula.cddb_endpoints()))

reset_cddb()
cddb_http_urls.clear()


def cddb_all_down(url, timeout=10, accept="application/json"):
    cddb_http_urls.append(url)
    raise urllib.error.URLError(OSError(101, "Network is unreachable"))


nebula.http_get = cddb_all_down
nebula.cddb_request = REAL_CDDB_REQUEST
try:
    cddb_down_error = ""
    try:
        nebula.cddb_lookup_disc(cddb_disc())
    except OSError as exc:
        cddb_down_error = str(exc)
finally:
    nebula.http_get = real_http_get
    nebula.cddb_request = cddb_miss
check("with every CDDB server unreachable the lookup says so instead of hanging",
      cddb_down_error.startswith("no server answered") and "Network is unreachable" in cddb_down_error,
      cddb_down_error)
check("every CDDB server was tried before giving up", len(cddb_http_urls) == 3, str(cddb_http_urls))
reset_cddb()

# A source that says "no match" and one that can't be reached are different results.
get, seen = fake_musicbrainz(by_disc_id=True)
real_mb_get_cddb = nebula.mb_get
nebula.cddb_request = cddb_fake(CDDB_MISS)
nebula.mb_get = get
try:
    source, errors, answered = nebula.identify_disc(
        read_vector_disc(), {"id_order": [["cddb", True], ["musicbrainz", True]]})
finally:
    nebula.mb_get = real_mb_get_cddb
    nebula.cddb_request = cddb_miss
check("a CDDB miss falls through to MusicBrainz, which answers",
      source == "musicbrainz" and errors == [] and answered is True, f"{source} {errors} {answered}")


def cddb_down(command, server=""):
    raise OSError("no server answered (last: gnudb.gnudb.org: [Errno 101] Network is unreachable)")


def mb_down(url, *args, **kwargs):
    raise urllib.error.URLError(OSError(101, "Network is unreachable"))


nebula.cddb_request = cddb_down
nebula.mb_get = mb_down
try:
    source, errors, answered = nebula.identify_disc(
        read_vector_disc(), {"id_order": [["cddb", True], ["musicbrainz", True]]})
finally:
    nebula.mb_get = real_mb_get_cddb
    nebula.cddb_request = cddb_miss
check("when no source could be asked, identify_disc says nothing answered",
      source == "" and answered is False and len(errors) == 2, f"{source} {errors} {answered}")

# How the CD tab words the result: a dead source alongside a real "not found" is not a
# failed lookup, and a disc named by another source keeps the failure in the tooltip only.
msg_tab = nebula.DiscTab(w, read_vector_disc())
msg_tab.lookup_finished(False, "CDDB: no server answered", "", "CDDB or MusicBrainz", True)
check("a disc no source knows says so and names the source that was down",
      msg_tab.status.text() == "6 tracks \u00b7 not found on CDDB or MusicBrainz \u00b7 CDDB: no server answered",
      msg_tab.status.text())
msg_tab.lookup_finished(False, "CDDB: no server answered", "", "CDDB or MusicBrainz", False)
check("when no source answered, the status still reports a failed lookup",
      "lookup failed" in msg_tab.status.text(), msg_tab.status.text())
msg_tab.lookup_finished(True, "CDDB: no server answered", "MusicBrainz", "CDDB or MusicBrainz", True)
check("a disc named by another source doesn't show the failed source in the status",
      msg_tab.status.text() == "6 tracks \u00b7 MusicBrainz"
      and msg_tab.status.toolTip() == "CDDB: no server answered",
      f"{msg_tab.status.text()!r} {msg_tab.status.toolTip()!r}")
msg_tab.deleteLater()

# Eject: the disc only counts as ejected once the drive reports its tray open with no disc.
def fake_drive(eject_states, ignore_eject=False):
    """A drive whose status moves through eject_states (one per poll) after the eject ioctl."""
    state = {"ejected": False, "polls": 0, "ejects": 0}

    def ioctl(fd, request, arg):
        if request == nebula.CD_IOCTL_EJECT:
            state["ejects"] += 1
            state["ejected"] = not ignore_eject
            return 0
        if request == nebula.CD_IOCTL_LOCK_DOOR:
            return 0
        if request == nebula.CD_IOCTL_DRIVE_STATUS:
            if not state["ejected"]:
                return nebula.CD_STATUS_DISC_OK
            state["polls"] += 1
            return eject_states[min(state["polls"] - 1, len(eject_states) - 1)]
        raise OSError("unexpected ioctl")
    return ioctl, state


with tempfile.NamedTemporaryFile() as fake_node:
    real_ioctl, real_wait, real_which = nebula.fcntl.ioctl, nebula.CD_EJECT_WAIT, nebula.shutil.which
    try:
        nebula.CD_EJECT_WAIT = 0.5
        nebula.shutil.which = lambda name, *a, **k: None if name == "eject" else real_which(name, *a, **k)
        ioctl, state = fake_drive([nebula.CD_STATUS_NOT_READY, nebula.CD_STATUS_NOT_READY,
                                   nebula.CD_STATUS_TRAY_OPEN])
        nebula.fcntl.ioctl = ioctl
        nebula.eject_cd(fake_node.name)
        check("eject returns once the tray is open, not while the drive is still moving",
              state["ejects"] == 1 and state["polls"] >= 3, str(state))

        ioctl, state = fake_drive([nebula.CD_STATUS_DISC_OK], ignore_eject=True)
        nebula.fcntl.ioctl = ioctl
        try:
            nebula.eject_cd(fake_node.name)
            stuck = False
        except OSError as exc:
            stuck = "still in the drive" in str(exc)
        check("a disc that stays in the drive is reported, not treated as ejected", stuck, str(state))

        ioctl, state = fake_drive([nebula.CD_STATUS_NOT_READY])
        nebula.fcntl.ioctl = ioctl
        try:
            nebula.eject_cd(fake_node.name)
            busy = False
        except OSError:
            busy = True
        check("a drive that stays not ready is not treated as ejected", busy, str(state))
    finally:
        nebula.fcntl.ioctl = real_ioctl
        nebula.CD_EJECT_WAIT = real_wait
        nebula.shutil.which = real_which

# The CD tab, queue and rip, with the drive, table of contents, MusicBrainz and cdparanoia faked.
real_states, real_toc, real_rip = nebula.cd_drive_states, nebula.read_cd_toc, nebula.cdparanoia_rip
fake_rips = []


def fake_cdparanoia_rip(device, number, wav_path, frames=0, progress=None, cancel=lambda: False):
    fake_rips.append(number)
    shutil.copyfile(WAV1, wav_path)
    if progress:
        progress(1.0)
    return True


def poll_cd(window):
    """One pass of the drive watcher, run in this thread so the result is known at once."""
    window._cd_watcher._check()
    app.processEvents()


tools = next(a.menu() for a in w.menuBar().actions() if a.text().replace("&", "") == "Tools")
tool_texts = [a.text().replace("&", "") for a in tools.actions()]
check("the Tools menu has Audio CD and Eject entries",
      any("Audio CD" in t for t in tool_texts) and any("Eject" in t for t in tool_texts), str(tool_texts))

set_drives("/dev/sr0")
nebula.read_cd_toc = lambda device: read_vector_disc()
nebula.mb_get = fake_musicbrainz(by_disc_id=True)[0]
nebula.cdparanoia_rip = fake_cdparanoia_rip
try:
    # The watcher thread runs between the lines above, so it may have read the real drive
    # before the fake table of contents went in — and a real read that failed holds that
    # drive in its retry cooldown, which would swallow this poll. Starting the disc from a
    # clean slate keeps a real drive in the machine from deciding the result.
    w._cd_watcher.pause()
    w._cd_watcher.resume()
    poll_cd(w)
    tab = w.disc_tab
    check("inserting a CD adds a CD tab", tab is not None and w.tabs.indexOf(tab) >= 0)
    w._cd_lookup.wait(10000)
    app.processEvents()
    check("the lookup names the release and titles the tracks",
          tab.heading.text() == "Test Album" and tab.table.item(0, 2).text() == "Song 1",
          tab.heading.text())
    check("the CD tab lists the album, artist, year and totals like the queue entries",
          tab.fields["album"].text() == "Test Album"
          and tab.fields["artist"].text() == "Test Artist"
          and "2001" in tab.fields["year"].text()
          and tab.fields["tracks"].text() == "6"
          and tab.fields["length"].text()
          == nebula.fmt_time(sum(t.frames for t in tab.disc.audio_tracks)
                              / nebula.CD_FRAMES_PER_SECOND),
          {k: v.text() for k, v in tab.fields.items()})
    check("the tab lists each track with its length",
          tab.table.rowCount() == 6 and tab.table.item(0, 1).text() == "1"
          and tab.table.item(0, 3).text() == "3:22", tab.table.item(0, 3).text())
    poll_cd(w)
    check("polling the same disc does not add a second CD tab",
          sum(isinstance(w.tabs.widget(i), nebula.DiscTab) for i in range(w.tabs.count())) == 1)
    w.show_disc_tab()
    check("the CD tab opens from the menu", w.tabs.currentWidget() is tab)

    added = []
    real_add = w.player.add_paths
    w.player.add_paths = lambda paths, *a, **k: added.extend(paths)
    try:
        tab.queue_checked()
        app.processEvents()
    finally:
        w.player.add_paths = real_add
    expected = [nebula.cd_entry(tab.disc, n) for n in range(1, 7)]
    check("ticked tracks are queued straight off the disc, without ripping",
          added == expected and fake_rips == [] and all(nebula.is_cd_entry(p) for p in added),
          str(added))
    check("a queued CD entry carries the disc and track metadata",
          nebula.cd_entry_parts(expected[0]) == ("/dev/sr0", 1)
          and nebula.cd_entry_meta(expected[0])["title"] == "Song 1"
          and nebula.cd_entry_meta(expected[0])["artist"] == "Test Artist",
          str(nebula.cd_entry_meta(expected[0])))
    idle_player = nebula.PlayerBar({})
    idle_player.add_paths([expected[0]], play_if_idle=False)
    check("adding a CD track to an idle queue leaves it stopped",
          idle_player.queue == [expected[0]] and idle_player.index == -1,
          (idle_player.queue, idle_player.index))

    # The right-click menu on the CD track list acts on the selected tracks.
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QTableWidgetSelectionRange
    real_menu = nebula.QMenu
    menus = []

    class FakeMenu:
        def __init__(self, parent=None):
            self.actions = []
            menus.append(self)

        def addAction(self, label, fn=None):
            self.actions.append((label, fn))

        def addSeparator(self):
            pass

        def exec(self, pos):
            pass

    def menu_action(menu, label):
        return next(fn for text, fn in menu.actions if text == label)

    def right_click(row):
        tab.table.itemAt = lambda pos: tab.table.item(row, 1)
        tab._context_menu(QPoint(0, 0))

    real_exec_rip = nebula.RipDialog.exec
    real_add_menu = w.player.add_paths
    try:
        nebula.QMenu = FakeMenu
        tab.table.clearSelection()
        tab.table.setRangeSelected(QTableWidgetSelectionRange(1, 0, 2, 3), True)
        right_click(1)
        labels = [label for label, _ in menus[-1].actions]
        check("the CD track menu offers queue, rip and tick actions",
              labels == ["Add ticked to queue", "Add whole CD to queue", "Shuffle CD into queue",
                        "Rip\u2026", "Tick selected", "Untick selected"], str(labels))
        check("right-clicking a selected track keeps the selection",
              tab._selected_rows() == [1, 2], str(tab._selected_rows()))

        added.clear()
        w.player.add_paths = lambda paths, *a, **k: added.extend(paths)
        rips_before_menu = len(fake_rips)
        menu_action(menus[-1], "Add ticked to queue")()
        app.processEvents()
        check("Add to queue from the menu queues the selected tracks only",
              added == [nebula.cd_entry(tab.disc, 2), nebula.cd_entry(tab.disc, 3)], str(added))
        check("Add to queue does not rip anything", len(fake_rips) == rips_before_menu,
              str(fake_rips[rips_before_menu:]))

        added.clear()
        menu_action(menus[-1], "Add whole CD to queue")()
        check("Add whole CD queues every track, not just the selected ones",
              added == [nebula.cd_entry(tab.disc, n) for n in range(1, 7)], str(added))
        added.clear()
        menu_action(menus[-1], "Shuffle CD into queue")()
        check("Shuffle CD queues every track exactly once, in its own order",
              sorted(added) == sorted(nebula.cd_entry(tab.disc, n) for n in range(1, 7))
              and len(added) == 6, str(added))

        right_click(5)
        check("right-clicking an unselected track selects only that track",
              tab._selected_rows() == [5], str(tab._selected_rows()))
        menu_action(menus[-1], "Untick selected")()
        check("Untick selected unticks only the selected track",
              tab.checked_numbers() == [1, 2, 3, 4, 5], str(tab.checked_numbers()))
        menu_action(menus[-1], "Tick selected")()
        check("Tick selected ticks it again", tab.checked_numbers() == [1, 2, 3, 4, 5, 6],
              str(tab.checked_numbers()))

        tab.table.clearSelection()
        tab.table.setRangeSelected(QTableWidgetSelectionRange(0, 0, 1, 3), True)
        right_click(0)
        nebula.RipDialog.exec = lambda self: nebula.QDialog.DialogCode.Accepted
        before = len(fake_rips)
        menu_action(menus[-1], "Rip\u2026")()
        tab._worker.wait(20000)
        app.processEvents()
        check("Rip from the menu rips the selected tracks only", fake_rips[before:] == [1, 2],
              str(fake_rips[before:]))
    finally:
        nebula.QMenu = real_menu
        nebula.RipDialog.exec = real_exec_rip
        w.player.add_paths = real_add_menu
        del tab.table.itemAt
        tab.table.clearSelection()

    # The Rip button: the rip dialog, the progress window, the files on disk, and the failure paths.
    # Click the real Rip button: the real rip dialog opens, is accepted, and a progress window runs the job.
    from PySide6.QtCore import QTimer

    def accept_open_rip_dialog():
        for widget in app.topLevelWidgets():
            if isinstance(widget, nebula.RipDialog) and widget.isVisible():
                widget.accept()

    previous_job = tab._job_dialog
    before_click = len(fake_rips)
    QTimer.singleShot(300, accept_open_rip_dialog)
    tab.btn_rip.click()
    if tab._worker is not None:
        tab._worker.wait(20000)
    app.processEvents()
    check("clicking Rip runs the rip after the dialog is accepted",
          len(fake_rips) - before_click == 6, str(fake_rips[before_click:]))
    check("clicking Rip opens a progress window",
          tab._job_dialog is not None and tab._job_dialog is not previous_job, str(tab.status.text()))

    real_exec, real_warning, real_which = nebula.RipDialog.exec, nebula.QMessageBox.warning, nebula.shutil.which
    warned = []
    try:
        nebula.RipDialog.exec = lambda self: nebula.QDialog.DialogCode.Accepted
        before = len(fake_rips)
        tab.rip_checked()
        tab._worker.wait(20000)
        app.processEvents()
        base = os.path.join(w.rip_folder(), nebula.cd_safe_name(tab.disc.artist), nebula.cd_safe_name(tab.disc.album))
        ripped = [os.path.join(base, f"{n:02d} - {nebula.cd_safe_name(tab.disc.track(n).title or f'Track {n:02d}')}.flac") for n in range(1, 7)]
        check("the Rip button writes each ticked track to the folder",
              all(os.path.getsize(p) > 0 for p in ripped) and fake_rips[before:] == list(range(1, 7)),
              base)
        check("the rip progress window closes when the rip is done",
              tab._job_dialog is not None and not tab._job_dialog.isVisible(), str(tab.status.text()))

        nebula.cdparanoia_rip = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("drive busy"))
        tab.rip_checked()
        tab._worker.wait(20000)
        app.processEvents()
        check("a failed rip shows the error in its progress window",
              "drive busy" in tab._job_dialog.status.text() and not tab._job_dialog.close_btn.isHidden(),
              tab._job_dialog.status.text())
        nebula.cdparanoia_rip = fake_cdparanoia_rip

        nebula.shutil.which = lambda name, *a, **k: None if name == "cdparanoia" else real_which(name, *a, **k)
        nebula.QMessageBox.warning = lambda *a, **k: warned.append(a[2] if len(a) > 2 else str(k))
        tab.rip_checked()
        check("ripping without cdparanoia names the missing tool",
              any("cdparanoia" in m for m in warned), str(warned))
    finally:
        nebula.RipDialog.exec = real_exec
        nebula.QMessageBox.warning = real_warning
        nebula.shutil.which = real_which
        nebula.cdparanoia_rip = fake_cdparanoia_rip

    # Playing a queued CD track: a local server streams the PCM off the drive and seeks by Range.
    section("CD streaming")
    import io  # noqa: E402
    import urllib.request  # noqa: E402

    short = nebula.cd_entry(tab.disc, 2)
    nebula.CD_ENTRIES[short]["length"] = 40 / nebula.CD_FRAMES_PER_SECOND   # a short fake track
    frames = 40
    pcm_bytes = frames * nebula.CD_BYTES_PER_FRAME
    total = 44 + pcm_bytes

    def cd_pattern(count):
        return bytes((i * 31 + 7) % 251 for i in range(count))

    reader_calls = []
    real_reader = nebula.cd_stream_reader

    class FakePcm:
        def __init__(self, data):
            self.stdout = io.BytesIO(data)
            self.returncode = 0

        def poll(self):
            return 0

        def kill(self):
            pass

        def wait(self, timeout=None):
            return 0

    def fake_reader(device, number, sector=0):
        """Raw PCM from a sector onward, like cdparanoia's track[.sector] span."""
        reader_calls.append((device, number, sector))
        start = min(sector * nebula.CD_BYTES_PER_FRAME, pcm_bytes)
        return FakePcm(cd_pattern(pcm_bytes)[start:])

    nebula.cd_stream_reader = fake_reader
    try:
        url = nebula.cd_stream_url(short)
        check("a CD queue entry becomes a local stream URL",
              url.startswith("http://127.0.0.1:") and "/cd?" in url, url)
        check("the seek span is track[seconds.sectors] as cdparanoia expects",
              nebula.cd_track_span(2) == "2" and nebula.cd_track_span(2, 100) == "2[1.25]",
              nebula.cd_track_span(2, 100))
        with urllib.request.urlopen(url, timeout=20) as resp:
            body = resp.read()
        check("the stream serves a WAV header and the whole track",
              body[:4] == b"RIFF" and body[8:12] == b"WAVE" and len(body) == total,
              f"{body[:12]!r} {len(body)}")
        check("the WAV header carries the track length",
              body[40:44] == (pcm_bytes).to_bytes(4, "little"), body[36:44])
        check("the stream announces Range support", resp.headers.get("Accept-Ranges") == "bytes")
        check("the PCM comes from cdparanoia", reader_calls[-1] == ("/dev/sr0", 2, 0), str(reader_calls))
        check("the samples follow the disc position", body[44:] == cd_pattern(pcm_bytes))

        # That read of the drive is kept as it plays, so the track is buffered afterwards;
        # the two checks below are about the drive itself, so drop the copy again. Waiting
        # for the fill to finish keeps the deletion from racing its last chunk.
        import time  # noqa: E402

        end = time.monotonic() + 10
        while time.monotonic() < end and nebula._CD_TEES:
            time.sleep(0.02)
        kept = nebula.cd_entry_cache_file(short)
        check("a track streamed in full is kept in the buffer for next time",
              nebula.cd_cache_size(kept) == total, (nebula.cd_cache_size(kept), total))
        for stale in (kept, nebula.cd_part_path(kept)):
            try:
                os.remove(stale)
            except OSError:
                pass

        start = 44 + nebula.CD_BYTES_PER_FRAME * 3 + 100
        request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{start + 999}"})
        with urllib.request.urlopen(request, timeout=20) as resp:
            part = resp.read()
        check("a seek is answered with 206 and the requested bytes",
              resp.status == 206 and len(part) == 1000
              and part == cd_pattern(pcm_bytes)[start - 44:start - 44 + 1000],
              f"{resp.status} {len(part)}")
        check("a seek restarts the reader at the right sector",
              ("/dev/sr0", 2, 3) in reader_calls, str(reader_calls))
        check("the seek reports its span",
              resp.headers.get("Content-Range") == f"bytes {start}-{start + 999}/{total}",
              resp.headers.get("Content-Range"))

        nebula.cd_stream_reader = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no disc"))
        failed = False
        try:
            urllib.request.urlopen(url, timeout=20).read()
        except urllib.error.HTTPError as exc:
            failed = exc.code == 503
        check("a drive that cannot read answers 503", failed)
    finally:
        nebula.cd_stream_reader = real_reader
        nebula.CD_ENTRIES.pop(short, None)

    # Buffering: tracks coming up are read into a cache in the background, and the stream
    # server serves them from disk, so a CD track starts without waiting for the drive.
    section("CD buffering")
    import time  # noqa: E402

    real_buffer_dir = nebula.CD_BUFFER_DIR
    nebula.CD_BUFFER_DIR = os.path.join(HOME, "cd-buffer")
    nebula.CD_BUFFER._failed.clear()
    nebula.CD_BUFFER.plan([], False)
    small = nebula.CdDisc("/dev/sr0",
                           [nebula.CdTrack(1, 0, 300, True, "Buffer One"),
                            nebula.CdTrack(2, 300, 300, True, "Buffer Two")], 600,
                           disc_id="buffer-test-disc")
    entry_one, entry_two = nebula.cd_entry(small, 1), nebula.cd_entry(small, 2)
    cache_one = nebula.cd_entry_cache_file(entry_one)
    cache_two = nebula.cd_entry_cache_file(entry_two)
    buffered_calls = []

    def buffered_reader(device, number, sector=0):
        buffered_calls.append((device, number, sector))
        data = cd_pattern(300 * nebula.CD_BYTES_PER_FRAME)
        return FakePcm(data[min(sector * nebula.CD_BYTES_PER_FRAME, len(data)):])

    def wait_ready(entry, seconds=15):
        end = time.monotonic() + seconds
        while time.monotonic() < end and not nebula.CD_BUFFER.ready(entry):
            time.sleep(0.05)
        return nebula.CD_BUFFER.ready(entry)

    prefs_cd = nebula.PreferencesDialog(w.library_tab, w)
    depth = prefs_cd.widgets.get("cd_buffer")
    check("Preferences offers a CD buffer depth",
          depth is not None and [depth.itemData(i) for i in range(depth.count())] == [0, 1, 2, 3, 4, -1],
          str(depth))
    depth.setCurrentIndex(depth.findData(2))
    prefs_cd._ok()
    prefs_cd.close()
    check("the CD buffer depth is saved", nebula.load_config().get("cd_buffer") == 2,
          str(nebula.load_config().get("cd_buffer")))
    w.config["cd_buffer"] = 3

    nebula.cd_stream_reader = buffered_reader
    try:
        nebula.CD_BUFFER.plan([entry_one, entry_two], True)
        check("CD tracks ahead of playback are buffered to disk",
              wait_ready(entry_one) and wait_ready(entry_two))
        size = os.path.getsize(cache_one) if os.path.exists(cache_one) else 0
        with open(cache_one, "rb") as fh:
            head = fh.read(4)
        check("the buffered track is a complete WAV",
              size == nebula.CD_WAV_HEADER + 300 * nebula.CD_BYTES_PER_FRAME and head == b"RIFF",
              f"{size} {head!r}")

        buffered_calls.clear()
        url = nebula.cd_stream_url(entry_one)
        with urllib.request.urlopen(url, timeout=20) as resp:
            body = resp.read()
        with open(cache_one, "rb") as fh:
            on_disk = fh.read()
        check("a buffered track plays without reading the drive again",
              buffered_calls == [] and body == on_disk, str(buffered_calls))

        request = urllib.request.Request(url, headers={"Range": "bytes=1000-1999"})
        with urllib.request.urlopen(request, timeout=20) as resp:
            part = resp.read()
        check("seeking a buffered track reads the file, not the disc",
              resp.status == 206 and part == on_disk[1000:2000] and buffered_calls == [],
              f"{resp.status} {buffered_calls}")

        w.config["cd_buffer"] = 1
        w.player.set_queue([WAV1, entry_one, entry_two], 0)
        check("only the tracks within the buffer depth are kept",
              os.path.exists(cache_one) and not os.path.exists(cache_two), cache_two)

        w.config["cd_buffer"] = 0
        w.player.refresh_cd_buffer()
        check("turning the buffer off removes the cached tracks",
              not os.path.exists(cache_one) and not os.path.exists(cache_two), cache_one)

        w.config["cd_buffer"] = 1
        w.player.set_queue([WAV1, entry_one], 0)
        check("the player buffers CD tracks queued after a file", wait_ready(entry_one))

        w.config["cd_buffer"] = 2
        w.player.set_queue([entry_one, entry_two], 0)
        check("the buffer refills while a buffered track plays",
              wait_ready(entry_two), nebula.cd_entry_cache_file(entry_two))

        # The depth is tracks: 0 reads nothing, N keeps the track playing plus N ahead, and
        # All queued CD tracks keeps every CD entry queued after the current one. The last
        # one used to keep none at all, so a disc set to All buffered nothing.
        many = nebula.CdDisc("/dev/sr0",
                              [nebula.CdTrack(n, (n - 1) * 300, 300, True, f"Buffer {n}")
                               for n in range(1, 4)], 900, disc_id="buffer-test-disc")
        trio = [nebula.cd_entry(many, n) for n in range(1, 4)]
        seen = []
        real_cd_plan = nebula.CD_BUFFER.plan
        nebula.CD_BUFFER.plan = lambda keep, allow_fetch: seen.append((list(keep), allow_fetch))
        try:
            w.player._stopped = False        # these depths are about the track playing now
            for depth, count in ((0, 0), (1, 2), (-1, 3)):
                w.config["cd_buffer"] = depth
                w.player.set_queue(list(trio), 0)
                check(f"CD buffer depth {depth} keeps {count} track(s) of three",
                      seen[-1][0] == trio[:count], (depth, seen[-1][0]))
                check(f"CD buffer depth {depth} tees a live track only when it is on",
                      nebula.CD_BUFFER.teeing == (depth != 0), nebula.CD_BUFFER.teeing)
        finally:
            nebula.CD_BUFFER.plan = real_cd_plan
        w.config["cd_buffer"] = 2

        # A track played straight off the disc keeps what it is already reading: no extra
        # drive work, no second reader, and the track is on disk the next time.
        size_one = nebula.CD_WAV_HEADER + 300 * nebula.CD_BYTES_PER_FRAME
        for stale in (cache_one, nebula.cd_part_path(cache_one)):
            try:
                os.remove(stale)
            except OSError:
                pass
        buffered_calls.clear()
        url = nebula.cd_stream_url(entry_one)
        with urllib.request.urlopen(url, timeout=20) as resp:
            live_body = resp.read()
        check("a track streamed off the disc is kept as it plays",
              wait_ready(entry_one) and len(live_body) == size_one,
              (nebula.CD_BUFFER.ready(entry_one), len(live_body), size_one))
        with open(cache_one, "rb") as fh:
            kept = fh.read()
        check("the kept copy is the audio that was played", kept == live_body, len(kept))
        check("reading it off the disc called the reader once",
              len(buffered_calls) == 1, buffered_calls)
        buffered_calls.clear()
        with urllib.request.urlopen(url, timeout=20) as resp:
            again = resp.read()
        check("playing that track again reads the buffer, not the drive",
              buffered_calls == [] and again == kept, buffered_calls)

        # A track the buffer is reading plays as the read arrives: the stream server follows
        # the file the buffer is writing instead of opening a reader of its own, so the disc
        # is read once, in one pass, and playback doesn't wait for the whole track to land.
        long_disc = nebula.CdDisc("/dev/sr1",       # its own drive, so its key is its own
                                  [nebula.CdTrack(1, 0, 3000, True, "Long One")], 3000,
                                  disc_id="buffer-long")
        long_entry = nebula.cd_entry(long_disc, 1)
        long_cache = nebula.cd_entry_cache_file(long_entry)
        long_pattern = cd_pattern(3000 * nebula.CD_BYTES_PER_FRAME)
        long_calls = []

        class SlowStream:
            """Hands out bytes a chunk at a time, so reading this track takes a moment."""

            def __init__(self, data):
                self._buf = io.BytesIO(data)

            def read(self, count):
                time.sleep(0.02)
                return self._buf.read(count)

        def slow_reader(device, number, sector=0):
            long_calls.append((device, number, sector))
            start = min(sector * nebula.CD_BYTES_PER_FRAME, len(long_pattern))
            pcm = FakePcm(long_pattern[start:])
            pcm.stdout = SlowStream(long_pattern[start:])
            return pcm

        def wait_idle(seconds=10):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                with nebula.CD_BUFFER._lock:
                    if not nebula.CD_BUFFER._filling and nebula.CD_BUFFER._proc is None:
                        return True
                time.sleep(0.05)
            return False

        def forget(*paths):
            for stale in paths:
                try:
                    os.remove(stale)
                except OSError:
                    pass

        nebula.cd_stream_reader = slow_reader
        nebula.CD_BUFFER.plan([], False)
        wait_idle()
        long_calls.clear()
        holds = []
        real_live_begin = nebula.CD_BUFFER.live_begin
        nebula.CD_BUFFER.live_begin = lambda device: (holds.append(device),
                                                      real_live_begin(device))
        try:
            nebula.CD_BUFFER.plan([long_entry], True)
            with urllib.request.urlopen(nebula.cd_stream_url(long_entry), timeout=90) as resp:
                while_read = resp.read()
            check("a track the buffer is reading plays as it is read",
                  while_read == nebula.cd_wav_header(len(long_pattern)) + long_pattern,
                  len(while_read))
            check("that took one read of the drive, the buffer's own",
                  len(long_calls) == 1, long_calls)
            check("playback following the buffer never takes the drive itself",
                  holds == [], holds)
        finally:
            nebula.CD_BUFFER.live_begin = real_live_begin
        # Playing the whole track means the buffer's read of it lands: the file is named a
        # moment after the last bytes are served, so this waits for the name rather than
        # asking for it in the same instant the stream finished.
        check("the whole track is on disk once it has played", wait_ready(long_entry, 10),
              nebula.CD_BUFFER.ready(long_entry))

        # Playback goes first: while it reads the drive, a read ahead stands back and keeps
        # what it has read, then carries on where it stopped.
        forget(long_cache, nebula.cd_part_path(long_cache))
        nebula.CD_BUFFER.plan([], False)
        wait_idle()
        long_calls.clear()
        nebula.CD_BUFFER.plan([long_entry], True)
        end = time.monotonic() + 5
        while time.monotonic() < end and not long_calls:
            time.sleep(0.05)
        # wait for the read to put bytes down, so the file being checked is one read halfway
        end = time.monotonic() + 5
        while time.monotonic() < end and nebula.cd_cache_size(
                nebula.cd_part_path(long_cache)) <= nebula.CD_WAV_HEADER:
            time.sleep(0.05)
        nebula.CD_BUFFER.live_begin("/dev/sr1")     # playback wants the drive now
        check("a read ahead gives the drive up when playback wants it",
              nebula.CD_BUFFER._proc is None and nebula.CD_BUFFER._filling == "",
              (nebula.CD_BUFFER._filling, nebula.CD_BUFFER._proc))
        during = len(long_calls)
        time.sleep(0.4)
        check("nothing reads the disc while playback is reading it",
              len(long_calls) == during, long_calls)
        check("the half-read track is still there to carry on from",
              nebula.cd_cache_size(nebula.cd_part_path(long_cache)) > nebula.CD_WAV_HEADER,
              nebula.cd_cache_size(nebula.cd_part_path(long_cache)))
        nebula.CD_BUFFER.live_end("/dev/sr1")
        check("the read carries on once playback is done with the drive",
              wait_ready(long_entry, 60), nebula.CD_BUFFER._filling)
        with open(long_cache, "rb") as fh:
            whole_long = fh.read()
        check("the track it carries on with is the whole track, in order",
              whole_long == nebula.cd_wav_header(len(long_pattern)) + long_pattern,
              len(whole_long))

        # A seek past what the buffer has read reads the drive, so it never waits for the
        # buffer to catch up.
        forget(long_cache, nebula.cd_part_path(long_cache))
        long_calls.clear()
        nebula.CD_BUFFER.plan([long_entry], True)
        seek_frame = 2000
        at = nebula.CD_WAV_HEADER + seek_frame * nebula.CD_BYTES_PER_FRAME
        request = urllib.request.Request(nebula.cd_stream_url(long_entry),
                                         headers={"Range": "bytes=%d-%d" % (at, at + 999)})
        with urllib.request.urlopen(request, timeout=30) as resp:
            seeked = resp.read()
        want = long_pattern[seek_frame * nebula.CD_BYTES_PER_FRAME:][:1000]
        check("a seek past what has been buffered reads the drive",
              resp.status == 206 and seeked == want
              and ("/dev/sr1", 1, seek_frame) in long_calls,
              (resp.status, long_calls[-2:]))
        nebula.CD_BUFFER.plan([], False)
        wait_idle()
        nebula.cd_stream_reader = buffered_reader
        nebula.CD_ENTRIES.pop(long_entry, None)

        # An interrupted read carries on where it stopped, so audio that was read off the
        # disc once is never read a second time.
        part = nebula.cd_part_path(cache_two)
        pattern = cd_pattern(300 * nebula.CD_BYTES_PER_FRAME)
        done = nebula.CD_WAV_HEADER + nebula.CD_BYTES_PER_FRAME * 40
        with open(part, "wb") as fh:
            fh.write(nebula.cd_wav_header(len(pattern)))
            fh.write(pattern[:done - nebula.CD_WAV_HEADER])
        resumed = []

        def resuming_reader(device, number, sector=0):
            resumed.append(sector)
            start = min(sector * nebula.CD_BYTES_PER_FRAME, len(pattern))
            return FakePcm(pattern[start:])

        nebula.cd_stream_reader = resuming_reader
        with nebula.CD_BUFFER._lock:
            nebula.CD_BUFFER._keep = [entry_two]
            nebula.CD_BUFFER._allow = True
            nebula.CD_BUFFER._gen += 1
            gen = nebula.CD_BUFFER._gen
        nebula.CD_BUFFER._fill(entry_two, gen)
        with open(cache_two, "rb") as fh:
            whole = fh.read()
        check("an interrupted buffer read carries on from where it stopped",
              resumed == [40] and whole == nebula.cd_wav_header(len(pattern)) + pattern,
              (resumed, len(whole)))
        nebula.cd_stream_reader = buffered_reader

        # The buffer says what it is doing, so the drive noise has an explanation.
        for stale in (cache_one, cache_two, nebula.cd_part_path(cache_one),
                      nebula.cd_part_path(cache_two)):
            try:
                os.remove(stale)
            except OSError:
                pass
        with nebula.CD_BUFFER._lock:
            nebula.CD_BUFFER._keep = [entry_one, entry_two]
            nebula.CD_BUFFER._allow = True
            nebula.CD_BUFFER._filling = entry_one
        message = nebula.CD_BUFFER.status()
        check("the buffer names the track it is reading and how many are left",
              nebula.cd_entry_meta(entry_one)["title"] in message
              and "2 track(s)" in message, message)
        nebula.CD_BUFFER.plan([], False)   # also prunes the copies held for those tracks
        check("an idle buffer says nothing at all", nebula.CD_BUFFER.status() == "",
              nebula.CD_BUFFER.status())

        # And the player bar says where a CD track is coming from.
        def cd_pills():
            return [w.player.pills_layout.itemAt(i).widget().text()
                    for i in range(w.player.pills_layout.count())
                    if w.player.pills_layout.itemAt(i).widget()]

        nebula.CD_BUFFER.plan([entry_one], True)
        wait_ready(entry_one)
        w.player._load_cd_info(entry_one)
        check("a buffered CD track says it is playing from the buffer",
              "from buffer" in cd_pills(), cd_pills())

        # A track the buffer is still reading is served from what it has written so far, so
        # the bar says the buffer is the source rather than pretending it is the drive.
        forget(cache_one)
        nebula.CD_BUFFER.plan([entry_one], True)
        with nebula.CD_BUFFER._lock:
            nebula.CD_BUFFER._filling = entry_one
        with open(nebula.cd_part_path(cache_one), "wb") as fh:
            fh.write(nebula.cd_wav_header(size_one - nebula.CD_WAV_HEADER))
            fh.write(b"\0" * 4096)
        w.player._load_cd_info(entry_one)
        check("a track the buffer is still reading says it is playing from the buffer",
              "from buffer" in cd_pills() and not nebula.CD_BUFFER.ready(entry_one), cd_pills())
        with nebula.CD_BUFFER._lock:
            nebula.CD_BUFFER._filling = ""
        nebula.CD_BUFFER.plan([], False)   # drops the copy that is no longer wanted
        w.player._load_cd_info(entry_one)
        check("a CD track with no buffered copy says it is playing from the disc",
              not os.path.exists(cache_one) and "from disc" in cd_pills(), cd_pills())
        for entry in trio:
            nebula.CD_ENTRIES.pop(entry, None)
    finally:
        nebula.cd_stream_reader = real_reader
        w.config["cd_buffer"] = 0
        w.player.set_queue([])
        nebula.CD_BUFFER.plan([], False)
        nebula.CD_BUFFER_DIR = real_buffer_dir
        nebula.CD_ENTRIES.pop(entry_one, None)
        nebula.CD_ENTRIES.pop(entry_two, None)

    # Buffering tracks played from the PC: the tracks coming up are read into memory ahead
    # of the player, the next track's first 30 seconds before anything is read deeper, so
    # starting one never waits for a slow disk or a share.
    section("buffering tracks played from the PC")
    file_lib = os.path.join(HOME, "buffer-lib")
    os.makedirs(file_lib, exist_ok=True)

    def buffered_fixture(name, mb):
        path = os.path.join(file_lib, name)
        with open(path, "wb") as fh:
            fh.truncate(mb * 1024 ** 2)
        return path

    playing = buffered_fixture("01 - playing.flac", 60)
    next_track = buffered_fixture("02 - next.flac", 60)
    after_track = buffered_fixture("03 - after.flac", 60)
    short_track = buffered_fixture("04 - short.flac", 1)

    prefs_buf = nebula.PreferencesDialog(w.library_tab, w)
    picker = prefs_buf.widgets.get("file_buffer_mb")
    check("Preferences offers a buffer for tracks playing from the PC",
          picker is not None
          and [picker.itemData(i) for i in range(picker.count())]
          == list(nebula.FILE_BUFFER_MB)
          and nebula.FILE_BUFFER_MB[0] == 0 and nebula.FILE_BUFFER_DEFAULT == 30,
          None if picker is None else [picker.itemText(i) for i in range(picker.count())])
    device_picker = prefs_buf.widgets.get("device_buffer_mb")
    check("Preferences offers a buffer for tracks playing from a device",
          device_picker is not None
          and [device_picker.itemData(i) for i in range(device_picker.count())]
          == list(nebula.DEVICE_BUFFER_MB)
          and nebula.DEVICE_BUFFER_MB[0] == 0
          and nebula.DEVICE_BUFFER_DEFAULT == 128,
          None if device_picker is None else [device_picker.itemText(i)
                                               for i in range(device_picker.count())])
    picker.setCurrentIndex(picker.findData(128))
    device_picker.setCurrentIndex(device_picker.findData(256))
    prefs_buf._ok()
    prefs_buf.close()
    check("the buffer size is saved", nebula.load_config().get("file_buffer_mb") == 128,
          str(nebula.load_config().get("file_buffer_mb")))
    check("the device buffer size is saved too",
          nebula.load_config().get("device_buffer_mb") == 256,
          str(nebula.load_config().get("device_buffer_mb")))
    w.config["file_buffer_mb"] = 30
    w.config["device_buffer_mb"] = 128

    nebula.FILE_BUFFER.plan([next_track, after_track], 30 * 1024 ** 2)
    wanted = list(nebula.FILE_BUFFER._wanted)
    check("the next track's first 30 seconds are read before anything is read deeper",
          len(wanted) >= 3 and wanted[0] == (next_track, 0, nebula.buffer_seconds(next_track, 30))
          and wanted[1] == (after_track, 0, nebula.buffer_seconds(after_track, 30))
          and wanted[2][0] == next_track and wanted[2][1] > 0,
          wanted[:3])
    check("that first read is at least 30 seconds of audio",
          wanted[0][2] >= int(30 * nebula.BYTES_PER_SECOND_CD), wanted[0])
    check("the size caps the whole plan",
          sum(length for _p, _o, length in wanted) <= 30 * 1024 ** 2,
          sum(length for _p, _o, length in wanted))

    def wait_file_buffer(seconds=30):
        end = time.monotonic() + seconds
        while time.monotonic() < end and nebula.FILE_BUFFER._wanted:
            time.sleep(0.02)
        return not nebula.FILE_BUFFER._wanted

    planned_bytes = sum(length for _p, _o, length in wanted)
    check("the read-ahead really reads the bytes the plan asked for",
          wait_file_buffer() and nebula.FILE_BUFFER.read_bytes == planned_bytes,
          (nebula.FILE_BUFFER.read_bytes, planned_bytes))
    check("a finished read-ahead leaves the status line empty",
          nebula.FILE_BUFFER.status() == "", nebula.FILE_BUFFER.status())

    huge_a = buffered_fixture("05 - huge a.flac", 200)
    huge_b = buffered_fixture("06 - huge b.flac", 200)
    nebula.FILE_BUFFER.plan([huge_a, huge_b], 512 * 1024 ** 2)
    deeper = sum(_l for _p, _o, _l in nebula.FILE_BUFFER._wanted)
    check("a bigger size reads further ahead of the track playing",
          deeper > 30 * 1024 ** 2, deeper)
    seen_status = ""
    end = time.monotonic() + 15
    while time.monotonic() < end and not seen_status:
        text = nebula.FILE_BUFFER.status()
        if "huge a.flac" in text:
            seen_status = text
        time.sleep(0.005)
    check("the status line names the track being read ahead", seen_status != "",
          (seen_status, nebula.FILE_BUFFER.status()))
    check("a bigger size really reads those bytes too",
          wait_file_buffer() and nebula.FILE_BUFFER.read_bytes == deeper,
          (nebula.FILE_BUFFER.read_bytes, deeper))

    nebula.FILE_BUFFER.plan([short_track], 30 * 1024 ** 2)
    check("a track shorter than 30 seconds is read whole and no further",
          nebula.FILE_BUFFER._wanted == [(short_track, 0, 1024 ** 2)],
          nebula.FILE_BUFFER._wanted)
    nebula.FILE_BUFFER.plan([], 0)
    check("turned off, nothing is read at all", nebula.FILE_BUFFER._wanted == [],
          nebula.FILE_BUFFER._wanted)

    # Watch what the player asks the buffer to read, rather than what the reader has
    # already got through, so the check does not race the read itself.
    recorded = []
    real_file_plan = nebula.FILE_BUFFER.plan
    nebula.FILE_BUFFER.plan = lambda paths, budget: recorded.append((list(paths), budget))
    try:
        w.config["file_buffer_mb"] = 128
        w.player.set_queue([playing, next_track, after_track], 0)
        check("the track playing now is left to the player and the next one is read",
              recorded[-1] == ([next_track, after_track], 128 * 1024 ** 2), recorded[-1])
        w.config["file_buffer_mb"] = 0
        w.player.set_queue([playing, next_track, after_track], 0)
        check("with the size at Off the player reads nothing ahead",
              recorded[-1] == ([], 0), recorded[-1])
    finally:
        nebula.FILE_BUFFER.plan = real_file_plan
    nebula.FILE_BUFFER.plan([], 0)
    w.config["file_buffer_mb"] = 30
    w.player.set_queue([], None)

    # A slow drive can't make the desktop offer to force-quit the app any more: the drives are
    # probed, a new disc's table of contents is read, and the tray is opened, all off the GUI
    # thread. The watcher thread is started here and runs for real, unlike the checks above.
    section("CD insert and eject stay responsive")
    real_read_toc, real_eject = nebula.read_cd_toc, nebula.eject_cd
    gui_thread = threading.get_ident()
    probe_threads = []

    def slow_probe():
        """A drive still spinning up holds its node open for seconds, and this records where."""
        probe_threads.append(threading.get_ident())
        time.sleep(1.0)
        return {"/dev/sr0": "disc"}

    def slow_toc(device):
        time.sleep(1.0)
        return read_vector_disc()

    def slow_eject(device):
        time.sleep(1.0)

    def wait_for(predicate, seconds=20):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            app.processEvents()
            if predicate():
                return True
            time.sleep(0.02)
        app.processEvents()
        return predicate()

    nebula.cd_drive_states = slow_probe
    nebula.read_cd_toc = slow_toc
    w._cd_watcher._state = "none"
    w._cd_watcher.device = None
    w._cd_watcher._paused = False
    w._disc_lost()                            # no CD tab before the disc goes in
    try:
        began = time.monotonic()
        w._cd_watcher.start()
        started = time.monotonic() - began
        check("starting the drive watcher doesn't block the window", started < 0.2, f"{started:.2f}s")
        # The probe sleeps for a second and the table of contents for another; the window must
        # keep answering throughout, so time every turn of its event loop.
        gaps = []
        end = time.monotonic() + 1.5
        while time.monotonic() < end:
            turn = time.monotonic()
            app.processEvents()
            gaps.append(time.monotonic() - turn)
            time.sleep(0.01)
        check("the window keeps answering while a slow drive is probed",
              gaps and max(gaps) < 0.2, f"{max(gaps):.2f}s")
        check("the drives are probed, and the disc read, off the GUI thread",
              probe_threads and all(t != gui_thread for t in probe_threads),
              f"{len(probe_threads)} probe(s), gui={gui_thread} {probe_threads[:3]}")
        check("the CD tab appears when the table of contents arrives",
              wait_for(lambda: w.disc_tab is not None))

        nebula.eject_cd = slow_eject
        set_drives()                            # the disc leaves as the tray opens
        began = time.monotonic()
        w.eject_disc()
        blocked = time.monotonic() - began
        check("ejecting returns to the window before the tray opens", blocked < 0.5,
              f"{blocked:.2f}s")
        check("the status bar says the disc is being ejected",
              "Ejecting" in w.statusBar().currentMessage(), w.statusBar().currentMessage())
        w._cd_eject.wait(10000)
        app.processEvents()
        check("the CD tab closes once the tray is open",
              w.disc_tab is None and w._cd_device is None, str(w._cd_device))
        # Give the watcher a pass or two after the eject: a stale read must not bring the tab back.
        end = time.monotonic() + 2.5
        while time.monotonic() < end:
            app.processEvents()
            time.sleep(0.02)
        check("the disc is not reported again after the eject", w.disc_tab is None, str(w.disc_tab))
    finally:
        w._cd_watcher.stop()
        w._cd_watcher.wait(5000)
        nebula.eject_cd = real_eject
        nebula.read_cd_toc = real_read_toc
        set_drives()
        poll_cd(w)

    played, counted = [], []
    real_set_source = w.player.player.setSource
    real_on_play = w.player.on_play
    try:
        w.player.player.setSource = lambda source: played.append(source.toString())
        w.player.on_play = lambda path: counted.append(path)
        stream_entry = nebula.cd_entry(tab.disc, 1)
        w.player.set_queue([stream_entry, WAV1], 0, play=True)
    finally:
        w.player.player.setSource = real_set_source
        w.player.on_play = real_on_play
        nebula.CD_ENTRIES.pop(stream_entry, None)
    check("playing a CD entry hands the player the stream, not a file",
          played and played[0].startswith("http://127.0.0.1:"), str(played))
    check("a CD entry never counts as a library play", counted == [], str(counted))
    check("the now-playing bar shows the disc track",
          w.player.now_title.text() == "Song 1" and "Test Artist" in w.player.now_sub.text(),
          w.player.now_title.text())
    w.player.set_queue([])

    set_drives()
    poll_cd(w)
    check("removing the CD takes its tab away", w.disc_tab is None and w.tabs.indexOf(tab) < 0)

    # Identification sources: the priority list, CDDB and MusicBrainz lookups, Find release,
    # and Discogs sign-in.
    from PySide6.QtCore import Qt  # noqa: E402
    check("sources default to CDDB, Discogs then MusicBrainz, and off ones are skipped",
          nebula.id_order({}) == ["cddb", "discogs", "musicbrainz"]
          and          nebula.id_order({"id_order": [["musicbrainz", True], ["discogs", False]]})
          == ["cddb", "musicbrainz"])
    check("a config saved before CDDB existed gains it first, switched on",
          nebula.id_order_entries({"id_order": [["musicbrainz", True], ["discogs", False]]})
          == [["cddb", True], ["musicbrainz", True], ["discogs", False]],
          str(nebula.id_order_entries({"id_order": [["musicbrainz", True], ["discogs", False]]})))
    # The app key ships in nebula.py, so blank it here to test the not-set-up path, then restore it.
    shipped_key = nebula.DISCOGS_CONSUMER_KEY
    nebula.DISCOGS_CONSUMER_KEY = ""
    raised = False
    try:
        nebula.discogs_begin_auth()
    except OSError:
        raised = True
    check("Discogs sign-in refuses to start without the app key", raised and not nebula.discogs_connected(
        {"discogs_token": "t", "discogs_secret": "s"}))

    prefs = nebula.PreferencesDialog(w.library_tab, w)
    ids = prefs.id_list
    check("preferences lists the sources in priority order",
          [ids.item(i).data(Qt.ItemDataRole.UserRole) for i in range(ids.count())]
          == ["cddb", "discogs", "musicbrainz"]
          and ids.item(0).text() == "1. CDDB", ids.item(0).text())
    check("Discogs says why it is unavailable in this build", "not set up" in prefs.discogs_status.text(),
          prefs.discogs_status.text())
    nebula.DISCOGS_CONSUMER_KEY = shipped_key
    ids.setCurrentRow(1)
    prefs._id_move(-1)
    ids.item(1).setCheckState(Qt.CheckState.Unchecked)
    check("the Up button moves a source and renumbers the list",
          ids.item(0).text() == "1. Discogs" and ids.item(1).text() == "2. CDDB", ids.item(1).text())
    prefs._ok()
    check("Preferences saves the source order and on/off state",
          nebula.load_config().get("id_order")
          == [["discogs", True], ["cddb", False], ["musicbrainz", True]],
          str(nebula.load_config().get("id_order")))
    prefs.close()

    # With MusicBrainz switched off, inserting a CD does not query it.
    real_mb_get_id = nebula.mb_get
    queried = []

    def mb_none(url, *args, **kwargs):
        queried.append(url)
        return json.dumps({"releases": []}).encode("utf-8")

    w.config["id_order"] = [["cddb", False], ["musicbrainz", False], ["discogs", True]]
    set_drives("/dev/sr0")
    nebula.read_cd_toc = lambda device: read_vector_disc()
    nebula.mb_get = mb_none
    cddb_before = len(cddb_commands)
    try:
        poll_cd(w)
        if getattr(w, "_cd_lookup", None) is not None:
            w._cd_lookup.wait(10000)
        app.processEvents()
        check("with every disc-ID source switched off, a CD is not looked up on insert",
              queried == [] and len(cddb_commands) == cddb_before and w.disc_tab is not None,
              f"{queried} {cddb_commands[cddb_before:]}")
    finally:
        nebula.mb_get = real_mb_get_id
        set_drives()
        poll_cd(w)

    # With CDDB switched on, the disc is named from it and MusicBrainz is never asked.
    cddb_commands.clear()
    queried.clear()
    nebula.cddb_request = cddb_fake(
        "200 rock 7c0b8b0b CDDB Artist / CDDB Album\n",
        "210 rock 7c0b8b0b CDDB record successfully read.\n"
        "DTITLE=CDDB Artist / CDDB Album\nDYEAR=1999\nTTITLE0=CDDB One\nTTITLE1=CDDB Two\n.\n")
    w.config["id_order"] = [["cddb", True], ["musicbrainz", True], ["discogs", True]]
    set_drives("/dev/sr0")
    nebula.read_cd_toc = lambda device: read_vector_disc()
    nebula.mb_get = mb_none
    try:
        poll_cd(w)
        w._cd_lookup.wait(10000)
        app.processEvents()
        ctab = w.disc_tab
        check("CDDB names the disc on insert, before MusicBrainz is asked",
              ctab is not None and ctab.heading.text() == "CDDB Album"
              and ctab.fields["album"].text() == "CDDB Album"
              and ctab.fields["artist"].text() == "CDDB Artist"
              and ctab.table.item(0, 2).text() == "CDDB One" and "CDDB" in ctab.status.text()
              and queried == [],
              f"{ctab.heading.text() if ctab else None!r} {ctab.status.text() if ctab else None!r} {queried}")
        check("the CDDB query carries this disc's ID, then its answer is read",
              len(cddb_commands) == 2
              and cddb_commands[0].startswith("cddb query " + nebula.cddb_disc_id(ctab.disc) + " 6 ")
              and cddb_commands[1] == "cddb read rock 7c0b8b0b", str(cddb_commands))
    finally:
        nebula.mb_get = real_mb_get_id
        nebula.cddb_request = cddb_miss
        set_drives()
        poll_cd(w)
        w.config["id_order"] = [["cddb", True], ["discogs", True], ["musicbrainz", True]]
        nebula.save_config(w.config)

    # Find release: search the enabled sources, then fill the CD from the release picked.
    def mb_router(url, *args, **kwargs):
        if "/release/rel-test?" in url:
            return json.dumps(MB_RELEASE).encode("utf-8")
        if "discid/" in url:
            return json.dumps({"releases": []}).encode("utf-8")
        return json.dumps({"releases": []}).encode("utf-8")

    searches = []

    def fake_search(query):
        searches.append(query)
        return [{"source": "musicbrainz", "id": "rel-test", "title": "Test Artist \u2014 Test Album", "year": "2001"}]

    real_search, real_find_exec = nebula.mb_text_search, nebula.FindReleaseDialog.exec
    nebula.mb_get = mb_router
    nebula.mb_text_search = fake_search
    set_drives("/dev/sr0")
    try:
        find_disc = read_vector_disc()
        dlg = nebula.FindReleaseDialog({"id_order": [["discogs", True], ["musicbrainz", True]]}, find_disc)
        dlg.query.setText("Test Artist Test Album")
        dlg.run_search()
        check("Find release lists each enabled source's matches",
              dlg.results.count() == 1 and "[MusicBrainz]" in dlg.results.item(0).text()
              and searches == ["Test Artist Test Album"], dlg.results.count())
        check("an unsigned Discogs source is reported, not searched",
              "Discogs: not signed in" in dlg.status.text(), dlg.status.text())
        dlg.results.setCurrentRow(0)
        dlg.accept_choice()
        check("choosing a result returns it", dlg.chosen is not None and dlg.chosen["id"] == "rel-test",
              str(dlg.chosen))
        dlg.close()

        poll_cd(w)
        ftab = w.disc_tab
        w._cd_lookup.wait(10000)
        app.processEvents()
        before = ftab.table.item(0, 2).text()

        def pick(self):
            self.query.setText("Test Artist Test Album")
            self.run_search()
            self.results.setCurrentRow(0)
            self.chosen = self.results.currentItem().data(Qt.ItemDataRole.UserRole)
            return nebula.QDialog.DialogCode.Accepted

        nebula.FindReleaseDialog.exec = pick
        ftab.btn_find.click()
        ftab._worker.wait(20000)
        app.processEvents()
        check("the Find release button fills the CD from the chosen release",
              before != "Song 1" and ftab.table.item(0, 2).text() == "Song 1"
              and ftab.heading.text() == "Test Album"
              and ftab.fields["artist"].text() == "Test Artist",
              f"{before!r} -> {ftab.table.item(0, 2).text()!r}")
    finally:
        nebula.mb_get = real_mb_get_id
        nebula.mb_text_search = real_search
        nebula.FindReleaseDialog.exec = real_find_exec
        set_drives()
        poll_cd(w)

    # Removing a disc: its tab and its queued tracks go, since a cd:// entry can't play
    # without the disc that holds it.
    section("disc removal clears the queue")

    gone_disc = nebula.CdDisc("/dev/sr0",
                               [nebula.CdTrack(1, 0, 300, True, "Gone One"),
                                nebula.CdTrack(2, 300, 300, True, "Gone Two")], 600,
                               disc_id="gone-disc")
    kept_disc = nebula.CdDisc("/dev/sr1",
                               [nebula.CdTrack(1, 0, 300, True, "Kept")], 300,
                               disc_id="kept-disc")
    gone_one, gone_two = nebula.cd_entry(gone_disc, 1), nebula.cd_entry(gone_disc, 2)
    kept_entry = nebula.cd_entry(kept_disc, 1)

    nebula.CD_BUFFER._keep = [gone_one, gone_two]
    w.player.set_queue([WAV1, gone_one, gone_two, WAV2], 1)
    removed = w.player.drop_cd_entries("/dev/sr0")
    check("removing a disc takes its tracks out of the queue",
          removed == 2 and w.player.queue == [WAV1, WAV2], str(w.player.queue))
    check("the track after the disc's last one becomes the queue position",
          w.player.index == 1, str(w.player.index))
    check("the dropped entries are forgotten",
          gone_one not in nebula.CD_ENTRIES and gone_two not in nebula.CD_ENTRIES,
          str(list(nebula.CD_ENTRIES)[-2:]))
    check("the CD buffer stops holding a removed disc's tracks",
          nebula.CD_BUFFER._keep == [], str(nebula.CD_BUFFER._keep))

    gone_one = nebula.cd_entry(gone_disc, 1)
    w.player.set_queue([WAV1, gone_one], 1)
    check("a disc still in its drive keeps its queued tracks",
          w.player.drop_cd_entries("/dev/sr0", "gone-disc") == 0 and w.player.queue == [WAV1, gone_one],
          str(w.player.queue))

    w.player.set_queue([kept_entry, gone_one], 0)
    check("another drive's tracks stay when one disc goes",
          w.player.drop_cd_entries("/dev/sr0") == 1 and w.player.queue == [kept_entry],
          str(w.player.queue))

    gone_one, gone_two = nebula.cd_entry(gone_disc, 1), nebula.cd_entry(gone_disc, 2)
    w.player.set_queue([WAV1, gone_one, kept_entry, gone_two], 0)
    removed_all = w.player.drop_cd_entries()
    check("with no disc in any drive, every CD track leaves the queue",
          removed_all == 3 and w.player.queue == [WAV1],
          f"{removed_all} removed, {w.player.queue}")

    # The window: pulling the disc out closes the tab, clears the queue and says so.
    set_drives("/dev/sr0")
    nebula.read_cd_toc = lambda device: read_vector_disc()
    poll_cd(w)
    w._cd_lookup.wait(10000)
    app.processEvents()
    pull_tab = w.disc_tab
    pull_entries = [nebula.cd_entry(pull_tab.disc, 1), nebula.cd_entry(pull_tab.disc, 2)]
    w.player.set_queue([WAV1] + pull_entries, 1)
    set_drives()
    poll_cd(w)
    check("pulling the disc out closes the tab and clears its tracks from the queue",
          w.disc_tab is None and w.player.queue == [WAV1], str(w.player.queue))
    check("the status bar says the disc's tracks left the queue",
          "Disc removed" in w.statusBar().currentMessage(), w.statusBar().currentMessage())

    # Ejecting from the app does the same for that drive.
    keep_one = nebula.cd_entry(kept_disc, 1)
    w.player.set_queue([WAV1, keep_one], 1)
    set_drives()
    w._ejected("/dev/sr1")
    check("ejecting from the app also clears that disc's queued tracks",
          w.player.queue == [WAV1] and "left the queue" in w.statusBar().currentMessage(),
          f"{w.player.queue} {w.statusBar().currentMessage()!r}")

    # A different disc in the same drive: the old disc's tracks go, the new one's stay.
    set_drives("/dev/sr0")
    nebula.read_cd_toc = lambda device: read_vector_disc()
    poll_cd(w)
    w._cd_lookup.wait(10000)
    app.processEvents()
    old_entries = [nebula.cd_entry(w.disc_tab.disc, n) for n in (1, 2)]
    w.player.set_queue([WAV1] + old_entries, 1)
    nebula.read_cd_toc = lambda device: read_fake_disc([0, 9999], 30000)
    w._cd_watcher._state, w._cd_watcher.device = "none", None
    poll_cd(w)
    w._cd_lookup.wait(10000)
    app.processEvents()
    check("a different disc in the same drive drops the previous disc's tracks",
          w.player.queue == [WAV1], str(w.player.queue))

    nebula.read_cd_toc = REAL_READ_CD_TOC
    set_drives()
    poll_cd(w)
    w.player.set_queue([])
    for stale_entry in (gone_one, gone_two, kept_entry, keep_one):
        nebula.CD_ENTRIES.pop(stale_entry, None)

    # A disc's buffer is deleted the moment the disc leaves its drive, whatever took it out:
    # the app's eject, the tray's own button, the disc being pulled, the drive being
    # unplugged, or another disc taking its place.
    section("a disc's buffer goes when the disc does")
    buffer_home = os.path.join(HOME, "cd-buffer-gone")
    nebula.CD_BUFFER_DIR = buffer_home
    nebula.CD_BUFFER.plan([], False)
    nebula.CD_BUFFER._failed.clear()
    nebula.cd_stream_reader = buffered_reader
    bye_disc = nebula.CdDisc("/dev/sr0",
                              [nebula.CdTrack(1, 0, 300, True, "Bye One"),
                               nebula.CdTrack(2, 300, 300, True, "Bye Two")], 600,
                              disc_id="bye-disc")
    bye_entries = [nebula.cd_entry(bye_disc, n) for n in (1, 2)]
    drive_dir = nebula.cd_drive_dir("/dev/sr0")

    def drive_files():
        return sorted(os.listdir(drive_dir)) if os.path.isdir(drive_dir) else []

    def hold_buffer(*entries, disc_id="bye-disc"):
        """A finished track and a half-read one, as a disc leaves in the middle of a read."""
        with nebula.CD_BUFFER._lock:
            nebula.CD_BUFFER._keep = list(entries)
            nebula.CD_BUFFER._allow = True
        nebula.CD_BUFFER.set_disc("/dev/sr0", disc_id)
        os.makedirs(drive_dir, exist_ok=True)
        for entry in entries:
            cache = nebula.cd_entry_cache_file(entry)
            with open(cache, "wb") as fh:
                fh.write(nebula.cd_wav_header(300 * nebula.CD_BYTES_PER_FRAME))
                fh.write(b"\0" * 512)
        with open(nebula.cd_part_path(nebula.cd_entry_cache_file(entries[-1])), "wb") as fh:
            fh.write(nebula.cd_wav_header(300 * nebula.CD_BYTES_PER_FRAME))
            fh.write(b"\1" * 2048)

    # Pulled out by hand: the watcher sees a drive with no disc in it.
    hold_buffer(*bye_entries)
    w._cd_device = "/dev/sr0"
    set_drives()
    poll_cd(w)
    check("a disc pulled out of its drive takes its buffer with it",
          nebula.cd_buffer_files() == [] and drive_files() == [],
          (nebula.cd_buffer_files(), drive_files()))
    check("a disc pulled out with nothing queued says its buffer was deleted",
          "disc removed" in w.statusBar().currentMessage().lower()
          and "buffer" in w.statusBar().currentMessage(), w.statusBar().currentMessage())

    # Ejected from the app's CD tab.
    w.player.set_queue([])
    hold_buffer(*bye_entries)
    w._cd_device = "/dev/sr0"
    w._ejected("/dev/sr0")
    check("ejecting the disc from the app deletes its buffer too",
          nebula.cd_buffer_files() == [], nebula.cd_buffer_files())

    # Another disc taking its place in the same drive.
    hold_buffer(*bye_entries)
    nebula.CD_BUFFER.set_disc("/dev/sr0", "another-disc")
    check("a disc that replaces another deletes the one that left",
          nebula.cd_buffer_files() == [], nebula.cd_buffer_files())
    mine = nebula.cd_entry_cache_file(
        nebula.cd_entry(nebula.CdDisc("/dev/sr0",
                                        [nebula.CdTrack(1, 0, 300, True, "Mine")], 300,
                                        disc_id="another-disc"), 1))
    os.makedirs(drive_dir, exist_ok=True)
    with open(mine, "wb") as fh:
        fh.write(b"RIFF")
    nebula.CD_BUFFER.set_disc("/dev/sr0", "another-disc")
    check("the disc that is still in the drive keeps its own buffer",
          os.path.exists(mine), nebula.cd_buffer_files())

    # Only a drive that says it is empty counts as proof that its disc has gone: one that
    # is spinning up, moving its tray or not answering at all says nothing about its disc.
    real_online = w.config.get("online_lookup", True)
    w.config["online_lookup"] = False          # no lookup runs in these checks
    nebula.CD_BUFFER.plan([], False)
    hold_buffer(*bye_entries)
    w._cd_device = "/dev/sr0"
    nebula.cd_drive_states = lambda: {"/dev/sr0": "busy"}
    w.statusBar().clearMessage()
    poll_cd(w)
    check("a drive that cannot answer yet is not taken as its disc being removed",
          nebula.cd_buffer_files() != [] and drive_files() != [] and w._cd_device == "/dev/sr0",
          (nebula.cd_buffer_files(), w._cd_device))
    check("nothing is said about a disc that may still be in the drive",
          "removed" not in w.statusBar().currentMessage().lower(),
          w.statusBar().currentMessage())

    # A drive that cannot answer for half a minute is a different matter: its disc can no
    # longer be confirmed at all, so what was read from it goes.
    w._cd_watcher._busy_since = time.monotonic() - (nebula.CD_BUSY_GONE + 1)
    poll_cd(w)
    check("a drive that cannot answer for long enough loses the buffer it was read from",
          nebula.cd_buffer_files() == [] and drive_files() == [] and w._cd_device is None,
          (nebula.cd_buffer_files(), w._cd_device))

    # A drive that says it is empty loses its buffer even while another drive holds a disc.
    other_disc = nebula.CdDisc("/dev/sr1",
                                [nebula.CdTrack(1, 0, 300, True, "Other")], 300,
                                disc_id="other-disc")
    other_entry = nebula.cd_entry(other_disc, 1)
    os.makedirs(nebula.cd_drive_dir("/dev/sr1"), exist_ok=True)
    with open(nebula.cd_entry_cache_file(other_entry), "wb") as fh:
        fh.write(nebula.cd_wav_header(300 * nebula.CD_BYTES_PER_FRAME))
    nebula.CD_BUFFER.set_disc("/dev/sr1", "other-disc")
    nebula.cd_drive_states = lambda: {"/dev/sr0": "disc", "/dev/sr1": "empty"}
    w._cd_watcher._state, w._cd_watcher.device = "ready", "/dev/sr0"
    poll_cd(w)
    check("a drive that says it is empty loses its buffer even when another holds a disc",
          not os.path.exists(nebula.cd_entry_cache_file(other_entry)),
          nebula.cd_buffer_files())
    nebula.CD_BUFFER.set_disc("/dev/sr1", "other-disc")
    poll_cd(w)
    check("and it is not reported over and over once its buffer has gone",
          nebula.cd_buffer_files() == [], nebula.cd_buffer_files())

    # A drive that stops answering and then reports a disc has its table of contents read
    # again, which is how a disc swapped in between two checks is noticed.
    set_drives("/dev/sr0")
    nebula.read_cd_toc = lambda device: read_vector_disc()
    w._cd_watcher._state, w._cd_watcher.device = "none", None
    poll_cd(w)
    app.processEvents()
    same_tab = w.disc_tab
    w._cd_watcher._busy_since = 0.0
    w._cd_watcher._unconfirmed = True       # a drive stopped answering, then answered again
    poll_cd(w)
    check("the same disc read again keeps the tab it already has",
          same_tab is not None and w.disc_tab is same_tab, str(w.disc_tab))

    swapped = [nebula.cd_entry(same_tab.disc, n) for n in (1, 2)]
    w.player.set_queue([WAV1] + swapped, 1)
    nebula.read_cd_toc = lambda device: read_fake_disc([0, 9999], 30000)
    w._cd_watcher._unconfirmed = True
    poll_cd(w)
    app.processEvents()
    check("a disc swapped in while the drive never went quiet is noticed",
          w.disc_tab is not None and w.disc_tab is not same_tab, str(w.disc_tab))
    check("the disc that left that way loses its buffer and its queued tracks",
          nebula.cd_buffer_files() == [] and w.player.queue == [WAV1],
          (nebula.cd_buffer_files(), w.player.queue))
    w.player.set_queue([])
    nebula.read_cd_toc = lambda device: read_vector_disc()
    w._cd_watcher._state, w._cd_watcher.device = "none", None
    poll_cd(w)                              # back to no disc for the checks after this

    # A read that starts after the buffer has been deleted writes nothing at all: the fill
    # asks for the entry it was told to read, and it is not wanted any more.
    hold_buffer(*bye_entries)
    stale_gen = nebula.CD_BUFFER._gen
    nebula.CD_BUFFER.forget("/dev/sr0")
    nebula.CD_BUFFER._fill(bye_entries[0], stale_gen)
    check("a read that starts after the buffer was deleted writes nothing",
          nebula.cd_buffer_files() == [] and drive_files() == [],
          (nebula.cd_buffer_files(), drive_files()))
    w.config["online_lookup"] = real_online

    # A failed read belongs to the disc it was reading. A queue entry is only this drive
    # and this track number, so a record kept against the entry would hold up the same
    # track number of the disc that comes next.
    nebula.CD_BUFFER.plan([], False)
    old_entry = nebula.cd_entry(nebula.CdDisc("/dev/sr0",
                                                [nebula.CdTrack(1, 0, 300, True, "Old")], 300,
                                                disc_id="old-disc"), 1)
    nebula.CD_BUFFER.set_disc("/dev/sr0", "old-disc")
    nebula.CD_BUFFER._failed.clear()
    nebula.CD_BUFFER._failed[nebula.cd_entry_cache_file(old_entry)] = time.monotonic()
    nebula.CD_BUFFER.set_disc("/dev/sr0", "new-disc")     # that disc is replaced
    check("a failed read of a disc that has gone does not hold up the disc after it",
          nebula.CD_BUFFER._failed == {}, nebula.CD_BUFFER._failed)

    # A read that was in flight cannot write the buffer back afterwards.
    nebula.cd_stream_reader = slow_reader
    nebula.CD_BUFFER.plan([], False)
    slow_disc = nebula.CdDisc("/dev/sr0",
                               [nebula.CdTrack(1, 0, 3000, True, "Slow One")], 3000,
                               disc_id="slow-disc")
    slow_entry = nebula.cd_entry(slow_disc, 1)
    nebula.CD_BUFFER.set_disc("/dev/sr0", "slow-disc")
    nebula.CD_BUFFER.plan([slow_entry], True)
    end = time.monotonic() + 5
    while time.monotonic() < end and not nebula.CD_BUFFER._filling:
        time.sleep(0.05)
    nebula.CD_BUFFER.forget("/dev/sr0")
    time.sleep(3.5)                       # long enough for a finished read to name its file
    check("a read that was in flight cannot put the buffer back after it is deleted",
          nebula.cd_buffer_files() == [] and nebula.CD_BUFFER._proc is None,
          (nebula.cd_buffer_files(), nebula.CD_BUFFER._proc))
    nebula.CD_BUFFER.plan([], False)

    # Buffering a disc the moment it is identified, rather than when it is queued.
    section("buffering a disc as soon as it is identified")
    early_dir = os.path.join(HOME, "cd-buffer-early")
    nebula.CD_BUFFER_DIR = early_dir
    nebula.CD_BUFFER._failed.clear()
    nebula.cd_stream_reader = buffered_reader
    early_disc = nebula.CdDisc("/dev/sr0",
                                [nebula.CdTrack(n, (n - 1) * 300, 300, True, f"Early {n}")
                                 for n in range(1, 5)], 1200, disc_id="early-disc")
    early_entries = [nebula.cd_entry(early_disc, n) for n in range(1, 5)]
    w.config["cd_buffer"] = 3
    online_before = w.config.get("online_lookup", True)
    w.config["online_lookup"] = False      # no lookup, no network in this check

    prefs_early = nebula.PreferencesDialog(w.library_tab, w)
    option = prefs_early.widgets.get("cd_buffer_early")
    check("Preferences offers buffering a disc as soon as it is identified",
          option is not None and not option.isChecked(), str(option))
    option.setChecked(True)
    prefs_early._ok()
    prefs_early.close()
    check("that option is saved", nebula.load_config().get("cd_buffer_early") is True,
          str(nebula.load_config().get("cd_buffer_early")))
    w.config["cd_buffer_early"] = True

    planned = []
    real_cd_plan = nebula.CD_BUFFER.plan
    nebula.CD_BUFFER.plan = lambda keep, allow_fetch: (planned.append(list(keep)),
                                                       real_cd_plan(keep, allow_fetch))
    try:
        # The disc goes in with the option on: its own tracks are kept ready at once.
        set_drives("/dev/sr0")
        nebula.read_cd_toc = lambda device: early_disc
        w._cd_watcher._state, w._cd_watcher.device = "none", None
        poll_cd(w)
        app.processEvents()
        check("the disc's own tracks are kept ready as soon as it is identified",
              w.disc_tab is not None and planned[-1][:3] == early_entries[:3],
              (w.disc_tab is not None, planned[-1]))
        check("the disc's tracks are read with nothing queued",
              wait_ready(early_entries[0]) and wait_ready(early_entries[2]),
              [nebula.CD_BUFFER.ready(e) for e in early_entries])
        check("the depth still caps what is read",
              not nebula.CD_BUFFER.ready(early_entries[3]),
              [nebula.CD_BUFFER.ready(e) for e in early_entries])

        # Turned off, the queue is the only reason to read a disc ahead.
        w.config["cd_buffer_early"] = False
        w.sync_disc_buffer()
        check("with the option off, nothing is buffered until a track is queued",
              planned[-1] == [], planned[-1])

        # On again with a track of the disc queued: what is queued comes first.
        w.config["cd_buffer_early"] = True
        w.sync_disc_buffer()
        w.player.set_queue([early_entries[2]], 0)
        check("the queued track and the ones after it come before the disc's own",
              planned[-1] == [early_entries[2]] + early_entries[:2], planned[-1])
        w.player.set_queue([])
    finally:
        nebula.CD_BUFFER.plan = real_cd_plan

    # And an unqueued disc's buffer goes when the disc does, like any other.
    w.config["cd_buffer_early"] = True
    w.sync_disc_buffer()
    check("the disc's tracks are read again once the option is back on",
          wait_ready(early_entries[0], 20), [nebula.CD_BUFFER.ready(e) for e in early_entries])
    check("the disc's buffer is there while the disc is",
          nebula.cd_buffer_files() != [], nebula.cd_buffer_files())
    set_drives()
    poll_cd(w)
    check("an unqueued disc's buffer goes when the disc does too",
          nebula.cd_buffer_files() == [], nebula.cd_buffer_files())
    w.config["cd_buffer_early"] = False
    w.config["online_lookup"] = online_before
    nebula.CD_BUFFER_DIR = real_buffer_dir
    nebula.cd_stream_reader = real_reader
    set_drives()
    nebula.read_cd_toc = REAL_READ_CD_TOC
    nebula.CD_BUFFER.plan([], False)
    for stale_entry in (early_entries + bye_entries + [slow_entry, other_entry]
                        + swapped):
        nebula.CD_ENTRIES.pop(stale_entry, None)

    # Discogs: the OAuth sign-in, the signed requests, search and release fill, with HTTP faked.
    real_key, real_secret = nebula.DISCOGS_CONSUMER_KEY, nebula.DISCOGS_CONSUMER_SECRET
    real_urlopen = nebula.urllib.request.urlopen
    sent = []

    class FakeResponse:
        def __init__(self, body, ctype):
            self._body, self.headers = body, {"Content-Type": ctype}

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout=None):
        sent.append(req)
        url = req.full_url
        if url.endswith("/oauth/request_token"):
            return FakeResponse(b"oauth_token=tok&oauth_token_secret=tsec&oauth_callback_confirmed=true", "text/plain")
        if url.endswith("/oauth/access_token"):
            return FakeResponse(b"oauth_token=acc&oauth_token_secret=accsec", "text/plain")
        if "/database/search" in url:
            return FakeResponse(json.dumps({"results": [{"id": 1234, "title": "Test Artist - Test Album",
                                                       "year": 2001}]}).encode("utf-8"), "application/json")
        if url.endswith("/releases/1234"):
            return FakeResponse(json.dumps({
                "title": "Test Album", "year": 2001, "artists": [{"name": "Test Artist (2)"}],
                "tracklist": [{"type_": "track", "title": f"Song {i + 1}"} for i in range(6)],
            }).encode("utf-8"), "application/json")
        raise OSError("unexpected request " + url)

    try:
        nebula.DISCOGS_CONSUMER_KEY, nebula.DISCOGS_CONSUMER_SECRET = "consumer", "shh"
        nebula.urllib.request.urlopen = fake_urlopen
        token, secret, url = nebula.discogs_begin_auth()
        auth = sent[-1].get_header("Authorization")
        check("Discogs sign-in starts with a request token and the approval page",
              (token, secret) == ("tok", "tsec")
              and url == "https://www.discogs.com/oauth/authorize?oauth_token=tok", url)
        check("Discogs requests are signed with the app key and secret",
              auth.startswith("OAuth ") and 'oauth_consumer_key="consumer"' in auth
              and 'oauth_signature="shh%26"' in auth, auth)
        acc_token, acc_secret = nebula.discogs_finish_auth(token, secret, "CODE123")
        auth = sent[-1].get_header("Authorization")
        check("the pasted code is traded for an access token", (acc_token, acc_secret) == ("acc", "accsec"))
        check("the code is sent as the verifier with the request token",
              'oauth_verifier="CODE123"' in auth and 'oauth_token="tok"' in auth, auth)
        hits = nebula.discogs_search("Test", acc_token, acc_secret)
        check("Discogs search returns each release with its year",
              hits == [{"source": "discogs", "id": "1234", "title": "Test Artist - Test Album", "year": "2001"}],
              str(hits))
        rel_disc = read_vector_disc()
        nebula.discogs_apply_release(rel_disc, "1234", acc_token, acc_secret)
        check("a Discogs release fills in artist, album, year and the audio track titles",
              rel_disc.artist == "Test Artist" and rel_disc.album == "Test Album" and rel_disc.date == "2001"
              and rel_disc.audio_tracks[0].title == "Song 1" and rel_disc.audio_tracks[5].title == "Song 6",
              f"{rel_disc.artist!r} {rel_disc.album!r} {rel_disc.date!r}")
        check("with the app key set, a saved Discogs sign-in counts as connected",
              nebula.discogs_connected({"discogs_token": acc_token, "discogs_secret": acc_secret}))
    finally:
        nebula.DISCOGS_CONSUMER_KEY, nebula.DISCOGS_CONSUMER_SECRET = real_key, real_secret
        nebula.urllib.request.urlopen = real_urlopen

    # The real cdparanoia_rip, run against a stand-in cdparanoia that writes its WAV slowly:
    # progress must move while it runs, and cancel must stop it partway through the track.
    import time as _time
    stub_dir = os.path.join(HOME, "stub-bin")
    os.makedirs(stub_dir, exist_ok=True)
    stub = os.path.join(stub_dir, "cdparanoia")
    with open(stub, "w") as f:
        f.write(f"#!{sys.executable}\n"
                "import sys, time\n"
                "with open(sys.argv[-1], 'wb') as out:\n"
                "    out.write(b'\\0' * 44)\n"
                "    for _ in range(100):\n"
                "        out.write(b'\\0' * 4096)\n"
                "        out.flush()\n"
                "        time.sleep(0.05)\n")
    os.chmod(stub, 0o755)
    old_path = os.environ["PATH"]
    os.environ["PATH"] = stub_dir + os.pathsep + old_path
    nebula.cdparanoia_rip = real_rip
    try:
        seen = []
        wav_full = os.path.join(HOME, "stub-full.wav")
        ok = nebula.cdparanoia_rip("/dev/sr0", 1, wav_full, 170, seen.append)
        check("the real cdparanoia_rip reports progress while the track is read",
              ok and len(set(seen)) >= 3 and seen == sorted(seen) and seen[-1] == 1.0 and os.path.exists(wav_full),
              str(seen))
        polls = []

        def cancel_after_two():
            polls.append(1)
            return len(polls) > 2

        wav_cut = os.path.join(HOME, "stub-cut.wav")
        started = _time.monotonic()
        ok = nebula.cdparanoia_rip("/dev/sr0", 1, wav_cut, 170, None, cancel_after_two)
        took = _time.monotonic() - started
        check("cancel stops cdparanoia partway through a track",
              ok is False and took < 2.5, f"ok={ok} took={took:.2f}s")
    finally:
        os.environ["PATH"] = old_path
        nebula.cdparanoia_rip = fake_cdparanoia_rip

    # Rip every codec and mode, with the release tags filled in from MusicBrainz.
    set_drives("/dev/sr0")
    rip_disc = read_vector_disc()
    nebula.mb_lookup_disc(rip_disc)
    out_dir = os.path.join(HOME, "rips")
    JOBS = [("flac", "", 8, ".flac", "flac"), ("alac", "", None, ".m4a", "alac"),
            ("mp3", "vbr", 0, ".mp3", "mp3"), ("mp3", "cbr", 192, ".mp3", "mp3"),
            ("m4a", "vbr", 1.5, ".m4a", "aac"), ("m4a", "cbr", 256, ".m4a", "aac"),
            ("opus", "vbr", 128, ".opus", "opus"), ("opus", "cbr", 256, ".opus", "opus")]
    jobs = [(1, os.path.join(out_dir, f"{c}-{m or 'lossless'}{ext}"), c, m, q)
            for c, m, q, ext, _want in JOBS]
    written = nebula.rip_cd_tracks(rip_disc, jobs)
    check("every codec and mode writes its file",
          written == [j[1] for j in jobs] and all(os.path.getsize(p) > 0 for p in written))
    for (c, m, _q, _ext, want), path in zip(JOBS, written):
        got = probe_codec(path)
        check(f"{c} {m or 'lossless'} encodes as {want}", got == want, got)
    for path, want in ((written[3], 192000), (written[5], 256000), (written[7], 256000)):
        got = probe_bitrate(path)
        check(f"{os.path.basename(path)} is about {want // 1000} kbps", abs(got - want) <= want * 0.15, str(got))
    src = sf.read(WAV1, dtype="int16")[0]
    for path in written[:2]:
        dec = os.path.join(out_dir, "decoded-" + os.path.basename(path) + ".wav")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path, dec], check=True)
        check(f"{os.path.basename(path)} decodes bit-identical to the disc",
              np.array_equal(sf.read(dec, dtype="int16")[0], src))
    tags = FLAC(written[0])
    check("ripped tracks carry the release tags",
          tags["title"] == ["Song 1"] and tags["album"] == ["Test Album"] and tags["tracknumber"] == ["1"],
          str(dict(tags)))

    args = nebula.rip_ffmpeg_args("mp3", "vbr", 0, "in.wav", "out.mp3", [("title", "X")])
    check("MP3 VBR uses the -q:a scale", args[args.index("-q:a") + 1] == "0" and "-b:a" not in args)
    args = nebula.rip_ffmpeg_args("m4a", "cbr", 256, "in.wav", "out.m4a", [])
    check("AAC CBR uses -b:a", args[args.index("-b:a") + 1] == "256k")
    args = nebula.rip_ffmpeg_args("opus", "vbr", 128, "in.wav", "out.opus", [])
    check("Opus VBR turns -vbr on", args[args.index("-vbr") + 1] == "on"
          and args[args.index("-b:a") + 1] == "128k")
    args = nebula.rip_ffmpeg_args("flac", "", 8, "in.wav", "out.flac", [])
    check("FLAC passes its compression level", args[args.index("-compression_level") + 1] == "8")
    check("every lossy codec and mode has a perceptually lossless note",
          all((c, m) in nebula.RIP_PERCEPTUAL and (c, m) in nebula.RIP_QUALITY
              for c in nebula.RIP_CODECS if c not in nebula.RIP_LOSSLESS for m in ("vbr", "cbr")))

    dlg = nebula.RipDialog(out_dir, {}, w)
    dlg.codec.setCurrentIndex(dlg.codec.findData("m4a"))
    dlg.mode.setCurrentIndex(dlg.mode.findData("vbr"))
    dlg.quality.setValue(0.5)
    dlg._perceptual()
    s = dlg.settings()
    check("the perceptually lossless button sets AAC VBR to its starting point",
          s["codec"] == "m4a" and s["mode"] == "vbr" and s["quality"] == 1.5, str(s))
    check("the lossy hint explains perceptually lossless", "erceptually lossless" in dlg.hint.text(),
          dlg.hint.text())
    dlg.codec.setCurrentIndex(dlg.codec.findData("flac"))
    s = dlg.settings()
    check("FLAC uses a compression level and no mode",
          s["codec"] == "flac" and s["quality"] == 5 and s["mode"] == "", str(s))
    dlg.codec.setCurrentIndex(dlg.codec.findData("mp3"))
    dlg.mode.setCurrentIndex(dlg.mode.findData("cbr"))
    check("VBR can be switched off for a lossy codec",
          dlg.settings()["mode"] == "cbr" and not dlg.mode.isHidden() and not dlg.mode_label.isHidden(),
          str(dlg.settings()))
    dlg.codec.setCurrentIndex(dlg.codec.findData("flac"))
    check("the bitrate mode row is hidden for lossless codecs",
          dlg.mode.isHidden() and dlg.mode_label.isHidden())
    dlg.codec.setCurrentIndex(dlg.codec.findData("opus"))
    check("the chosen bitrate mode is remembered after a lossless codec",
          dlg.settings()["mode"] == "cbr", str(dlg.settings()))
    dlg.mode.setCurrentIndex(dlg.mode.findData("vbr"))
    check("VBR can be switched back on for a lossy codec", dlg.settings()["mode"] == "vbr", str(dlg.settings()))
    dlg.codec.setCurrentIndex(dlg.codec.findData("alac"))
    check("ALAC has no quality setting", dlg.settings()["quality"] is None)
    dlg.close()
finally:
    set_drives()
    poll_cd(w)
    nebula.cd_drive_states, nebula.read_cd_toc = real_states, real_toc
    nebula.cdparanoia_rip, nebula.mb_get = real_rip, real_mb_get


# ---------------------------------------------------------------- burning discs
section("burning discs")
import shutil  # noqa: E402
import time  # noqa: E402
import wave  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog, QListWidgetItem, QMenu, QMessageBox  # noqa: E402

BURN_HOME = os.path.join(HOME, "burn")
FAKE_BIN = os.path.join(HOME, "fakebin")
FAKE_OUT = os.path.join(HOME, "fakeout")
FAKE_LOG = os.path.join(HOME, "fakelog.txt")
for folder in (BURN_HOME, FAKE_BIN, FAKE_OUT):
    os.makedirs(folder, exist_ok=True)

TONE = os.path.join(BURN_HOME, "tone.wav")          # 1 s, mono, 22.05 kHz
SECOND = os.path.join(BURN_HOME, "second.wav")
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                "sine=frequency=440:duration=1", "-ac", "1", "-ar", "22050", TONE], check=True)
shutil.copyfile(TONE, SECOND)


def make_tagged(name, title):
    """A FLAC of the tone, tagged as a track of the album Discovery."""
    out = os.path.join(BURN_HOME, name)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", TONE, "-c:a", "flac",
                    "-metadata", f"title={title}", "-metadata", "artist=Band",
                    "-metadata", "album=Discovery", out], check=True)
    return out


OPENING = make_tagged("opening.flac", "Opening")
CLOSING = make_tagged("closing.flac", "Closing")


def wav_format(path):
    with wave.open(path, "rb") as r:
        return (r.getnchannels(), r.getsampwidth(), r.getframerate(), r.getnframes())


def read_text(path):
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def cdrdao_accepts(toc):
    return subprocess.run(["cdrdao", "show-toc", toc], capture_output=True, text=True,
                          timeout=60).returncode == 0


class FakeProc:
    def __init__(self, out):
        self.stdout, self.stderr, self.returncode = out, "", 0


real_run = nebula.subprocess.run


def status_of(text):
    nebula.subprocess.run = lambda *a, **k: FakeProc(text)
    try:
        return nebula.burn_disc_status("/dev/sr0")
    finally:
        nebula.subprocess.run = real_run


real_which = nebula.shutil.which


def missing_for(kind, convert, absent):
    nebula.shutil.which = lambda name, *a, **k: None if name in absent else real_which(name)
    try:
        return nebula.burn_missing_tools(kind, convert)
    finally:
        nebula.shutil.which = real_which


# disc status, read from cdrdao disk-info
check("an empty disc reads as blank, even though cdrdao also reports it appendable",
      status_of("Disc status: empty\nAppendable: yes\n") == "blank")
check("a closed disc is used", status_of("Disc status: complete\n") == "used")
check("a half-written disc is used", status_of("Disc status: incomplete\n") == "used")
check("a disc with a session is used", status_of("Sessions: 1\n") == "used")
check("no disc in the drive reads as none", status_of("Unit not ready, no disc\n") == "none")
check("an unrecognised answer is unknown, not blank", status_of("something odd\n") == "unknown")

# tools a burn needs
check("an audio burn needs cdrdao and ffmpeg",
      missing_for("audio", None, {"cdrdao", "ffmpeg"}) == ["cdrdao", "ffmpeg"])
check("a data burn needs wodim and genisoimage, and ffmpeg only when converting",
      missing_for("data", None, {"wodim", "genisoimage", "ffmpeg"}) == ["wodim", "genisoimage"]
      and missing_for("data", "mp3", {"ffmpeg"}) == ["ffmpeg"])

# write speeds
check("write speeds go down to 1x", nebula.burn_speed_choices(52) == [1, 2, 4, 8, 12, 16, 20, 24, 32, 40, 48, 52],
      str(nebula.burn_speed_choices(52)))
check("a 4x drive offers 1x, 2x and 4x", nebula.burn_speed_choices(4) == [1, 2, 4])

# splitting a playlist across discs
def tracks_of(album, count, seconds):
    return [dict(path=f"/music/{album}/{i:02d}.flac", title=f"{album} {i}", artist="Artist",
                 album=album, seconds=seconds) for i in range(1, count + 1)]


weight = lambda i: i["seconds"] + nebula.BURN_LEADIN
playlist = tracks_of("Alpha", 10, 240) + tracks_of("Beta", 10, 240) + tracks_of("Gamma", 10, 240)
discs = nebula.burn_split(playlist, nebula.burn_disc_seconds(80), weight, lambda i: i["album"])
check("a 120-minute playlist splits into three 80-minute discs at album breaks",
      [sorted({t["album"] for t in d}) for d in discs] == [["Alpha"], ["Beta"], ["Gamma"]]
      and all(sum(weight(t) for t in d) <= nebula.burn_disc_seconds(80) for d in discs),
      str([len(d) for d in discs]))
try:
    nebula.burn_split([dict(seconds=5000, title="Opera", album="X")], nebula.burn_disc_seconds(80),
                       weight, lambda i: i["album"])
    too_big = False
except ValueError:
    too_big = True
check("a track longer than a disc is refused", too_big)

# CD-TEXT table of contents. cdrdao only takes 44.1 kHz stereo WAVs, so the tracks are
# transcoded first, as a real burn does.
toc_tone = os.path.join(BURN_HOME, "toc-tone.wav")
toc_second = os.path.join(BURN_HOME, "toc-second.wav")
nebula.burn_to_wav(TONE, toc_tone)
nebula.burn_to_wav(SECOND, toc_second)
tracks = [dict(wav=toc_tone, title="Alpha One", artist="Band", album="Discovery"),
          dict(wav=toc_second, title='Say "hi"', artist="Band", album="Discovery")]
cdtext_toc = nebula.burn_toc_text(tracks, cdtext=True)
plain_toc = nebula.burn_toc_text(tracks, cdtext=False)
check("the TOC names the album, tracks and performer when CD-TEXT is on",
      'TITLE "Discovery"' in cdtext_toc and 'TITLE "Alpha One"' in cdtext_toc
      and "TITLE \"Say 'hi'\"" in cdtext_toc and 'PERFORMER "Band"' in cdtext_toc, cdtext_toc)
check("CD-TEXT can be left off", "CD_TEXT" not in plain_toc and plain_toc.count("TRACK AUDIO") == 2)
mixed_toc = nebula.burn_toc_text([dict(tracks[0]), dict(tracks[1], album="Other", artist="Someone")])
check("a mixed-album disc has no album title and 'Various Artists'",
      'TITLE ""' in mixed_toc and 'PERFORMER "Various Artists"' in mixed_toc, mixed_toc)
for name, text in (("cdtext.toc", cdtext_toc), ("plain.toc", plain_toc)):
    path = os.path.join(BURN_HOME, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    check(f"cdrdao accepts the generated {name}", cdrdao_accepts(path))

# transcoding to WAV
padded = os.path.join(BURN_HOME, "padded.wav")
nebula.burn_to_wav(TONE, padded, pad_to=4.0)
fmt = wav_format(padded)
check("a short track is padded to four seconds of 44.1 kHz stereo 16-bit",
      fmt[:3] == (2, 2, 44100) and abs(fmt[3] - 176400) <= 2, str(fmt))
plain_wav = os.path.join(BURN_HOME, "plain.wav")
nebula.burn_to_wav(TONE, plain_wav)
check("a track converts to WAV without padding", abs(wav_format(plain_wav)[3] - 44100) <= 2,
      str(wav_format(plain_wav)))

# data disc image
iso_unit = os.path.join(BURN_HOME, "unit.iso")
nebula.burn_iso([(TONE, "001 tone.wav"), (FLAC1, "002 Song.flac")], "Mix Tape", iso_unit)
listing = subprocess.run(["isoinfo", "-J", "-l", "-i", iso_unit], capture_output=True, text=True).stdout
info = subprocess.run(["isoinfo", "-d", "-i", iso_unit], capture_output=True, text=True).stdout
check("the ISO holds the files under their numbered names",
      "001 tone.wav" in listing and "002 Song.flac" in listing, listing[-300:])
check("the ISO volume label comes from the playlist name", "Mix_Tape" in info)
check("no ISO staging folder is left behind",
      not [n for n in os.listdir(BURN_HOME) if n.startswith("isostage-")])

# dialog: speed list follows the drive, CD-TEXT only on audio discs
real_max_speed = nebula.burn_max_speed
nebula.burn_max_speed = lambda device: 24
try:
    dlg = nebula.BurnDialog(["/dev/sr0"], 3600, w)
    speeds = [dlg.speed.itemData(i) for i in range(dlg.speed.count())]
    check("the speed list runs from 1x up to the drive's 24x", speeds[0] == 1 and speeds[-1] == 24, str(speeds))
    dlg.kind.setCurrentIndex(dlg.kind.findData("audio"))
    check("an audio disc is written with CD-TEXT names by default",
          dlg.settings()["kind"] == "audio" and dlg.settings()["cdtext"] is True
          and dlg.settings()["convert"] is None, str(dlg.settings()))
    dlg.kind.setCurrentIndex(dlg.kind.findData("data"))
    dlg.convert.setCurrentIndex(dlg.convert.findData("mp3"))
    check("a data disc can be converted to MP3 and has no CD-TEXT",
          dlg.settings()["kind"] == "data" and dlg.settings()["convert"] == "mp3"
          and dlg.settings()["cdtext"] is False, str(dlg.settings()))
    dlg.close()
finally:
    nebula.burn_max_speed = real_max_speed

# end to end: fake cdrdao and wodim record what they are asked to do
def make_fake(name, body):
    path = os.path.join(FAKE_BIN, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    os.chmod(path, 0o755)


make_fake("cdrdao", """#!/bin/sh
echo "cdrdao $*" >> "$FAKE_LOG"
if [ "$1" = "disk-info" ]; then
  echo "Disc status: empty"
  echo "Appendable: yes"
  exit 0
fi
if [ "$1" = "write" ]; then
  for a in "$@"; do toc="$a"; done
  cp "$toc" "$FAKE_OUT/last.toc"
  grep -o 'FILE "[^"]*"' "$toc" | cut -d '"' -f 2 | while read -r f; do cp "$f" "$FAKE_OUT/$(basename "$f")"; done
fi
exit 0
""")
make_fake("wodim", """#!/bin/sh
echo "wodim $*" >> "$FAKE_LOG"
case "$*" in *-prcap*) echo "Maximum write speed: 24 KB/s (CD 24x)"; exit 0;; esac
for a in "$@"; do iso="$a"; done
cp "$iso" "$FAKE_OUT/last.iso"
exit 0
""")


def reset_fakes():
    for name in os.listdir(FAKE_OUT):
        os.remove(os.path.join(FAKE_OUT, name))
    open(FAKE_LOG, "w").close()


def fake_log():
    return read_text(FAKE_LOG).splitlines()


def wait_for_burn(timeout=180):
    deadline = time.monotonic() + timeout
    while w._burn_job is not None and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.05)
    QApplication.processEvents()
    return w._burn_job is None


real_split = nebula.burn_split
real_drives = nebula.cd_drive_nodes
real_exec = nebula.BurnDialog.exec
real_settings = nebula.BurnDialog.settings
real_question = QMessageBox.question
real_path = os.environ["PATH"]
scripted = {}


def run_burn(paths, label, settings, split=None):
    scripted.clear()
    scripted.update(settings)
    nebula.burn_split = split or real_split
    try:
        w.burn_paths(paths, label)
        return wait_for_burn()
    finally:
        nebula.burn_split = real_split


nebula.burn_max_speed = lambda device: 24
nebula.cd_drive_nodes = lambda: ["/dev/sr0"]
nebula.BurnDialog.exec = lambda self: QDialog.Accepted
nebula.BurnDialog.settings = lambda self: dict(scripted)
QMessageBox.question = lambda *a, **k: QMessageBox.Ok if "has been ejected" in a[2] else QMessageBox.Yes
os.environ["PATH"] = FAKE_BIN + os.pathsep + real_path
os.environ["FAKE_LOG"], os.environ["FAKE_OUT"] = FAKE_LOG, FAKE_OUT
try:
    reset_fakes()
    ok = run_burn([OPENING, CLOSING], "Discovery",
                  dict(kind="audio", device="/dev/sr0", speed=1, minutes=80, cdtext=True, convert=None))
    lines = fake_log()
    check("an audio burn at 1x runs cdrdao at that speed and ejects",
          ok and any(l.startswith("cdrdao write --device /dev/sr0 --speed 1 --eject") for l in lines), str(lines))
    toc = read_text(os.path.join(FAKE_OUT, "last.toc"))
    check("the disc carries the album and track names as CD-TEXT",
          'TITLE "Discovery"' in toc and 'TITLE "Opening"' in toc and 'TITLE "Closing"' in toc
          and 'PERFORMER "Band"' in toc, toc[:200])
    for n in (1, 2):
        p = os.path.join(FAKE_OUT, f"track{n:02d}.wav")
        fmt = wav_format(p) if os.path.exists(p) else None
        check(f"track {n:02d} is 44.1 kHz stereo 16-bit and at least four seconds",
              fmt is not None and fmt[:3] == (2, 2, 44100) and fmt[3] >= 176400 - 2, str(fmt))
    check("the burn leaves no scratch folders behind",
          not [n for n in os.listdir(nebula.TMP_DIR) if n.startswith("burn-")])
    check("the status bar reports a finished burn",
          w.statusBar().currentMessage() == "Burn complete: 1 disc(s)", w.statusBar().currentMessage())

    reset_fakes()
    ok = run_burn([FLAC1, TONE], "Mix Tape",
                  dict(kind="data", device="/dev/sr0", speed=8, minutes=80, cdtext=False, convert=None))
    lines = fake_log()
    check("a data burn at 8x runs wodim at that speed and ejects",
          ok and any("dev=/dev/sr0 speed=8 -data -eject" in l for l in lines), str(lines))
    iso = os.path.join(FAKE_OUT, "last.iso")
    listing = subprocess.run(["isoinfo", "-J", "-l", "-i", iso], capture_output=True, text=True).stdout
    check("the data disc keeps the original files in order",
          "001 " in listing and ".flac" in listing and "002 tone.wav" in listing, listing[-300:])

    for codec, ext in (("mp3", ".mp3"), ("opus", ".opus")):
        reset_fakes()
        ok = run_burn([FLAC1, TONE], "Mix Tape",
                      dict(kind="data", device="/dev/sr0", speed=8, minutes=80, cdtext=False, convert=codec))
        iso = os.path.join(FAKE_OUT, "last.iso")
        extracted = os.path.join(BURN_HOME, f"extracted{ext}")
        if os.path.exists(iso):
            with open(extracted, "wb") as fh:
                subprocess.run(["isoinfo", "-J", "-i", iso, "-x", f"/002 tone{ext}"], stdout=fh, check=False)
        got = probe_codec(extracted) if os.path.exists(extracted) and os.path.getsize(extracted) else ""
        check(f"a data disc converted to {codec} holds {codec} files", ok and got == codec, f"got {got!r}")

    nebula.burn_split = lambda items, limit, weight, album: [items[:1], items[1:]]
    reset_fakes()
    try:
        ok = run_burn([OPENING, CLOSING], "Two Discs",
                      dict(kind="audio", device="/dev/sr0", speed=4, minutes=80, cdtext=True, convert=None),
                      split=lambda items, limit, weight, album: [items[:1], items[1:]])
    finally:
        nebula.burn_split = real_split
    lines = fake_log()
    check("a two-disc burn writes both discs, asking for the second blank in between",
          ok and sum(l.startswith("cdrdao write") for l in lines) == 2
          and w.statusBar().currentMessage() == "Burn complete: 2 disc(s)",
          (ok, w.statusBar().currentMessage(), lines))

    reset_fakes()
    nebula.cd_drive_nodes = lambda: []
    w.burn_paths([TONE], "x")
    check("with no drive, Burn to Disc says so and burns nothing",
          fake_log() == [] and w.statusBar().currentMessage() == "No optical drive found",
          w.statusBar().currentMessage())
    nebula.cd_drive_nodes = lambda: ["/dev/sr0"]
finally:
    os.environ["PATH"] = real_path

# menus: album/track menu and playlist menu offer Burn to Disc
menus = []
# PySide6's own QMenu.exec cannot be patched on the class, so the menus the window builds
# are swapped for a subclass that records its items instead of blocking.
class RecordingMenu(QMenu):
    def exec(self, *a, **k):
        menus.append([act.text() for act in self.actions()])
        return None


real_menu_class = nebula.QMenu
nebula.QMenu = RecordingMenu
lt = w.library_tab
cover = QListWidgetItem("Discovery\nBand")
cover.setData(Qt.UserRole, [OPENING, CLOSING])
lt.covers.addItem(cover)
road = QListWidgetItem("Road Trip")
road.setData(nebula.SMART_ROLE, "Road Trip")
lt.playlist_list.addItem(road)
w.show()
QApplication.processEvents()
try:
    lt._covers_menu(lt.covers.visualItemRect(cover).center())
    lt._playlist_menu(lt.playlist_list.visualItemRect(road).center())
finally:
    nebula.QMenu = real_menu_class
    lt.covers.takeItem(lt.covers.row(cover))
    lt.playlist_list.takeItem(lt.playlist_list.row(road))
check("the album menu offers Burn to Disc", len(menus) >= 1 and "Burn to Disc\u2026" in menus[0], str(menus))
check("the playlist menu offers Burn to Disc", len(menus) >= 2 and "Burn to Disc\u2026" in menus[1], str(menus))

menus.clear()
nebula.QMenu = RecordingMenu
try:
    tagger._table_menu(tagger.table.visualItemRect(tagger.table.item(0, 0)).center())
finally:
    nebula.QMenu = real_menu_class
check("the tags file list offers Extended tags\u2026 on right-click",
      bool(menus) and "Extended tags\u2026" in menus[0], str(menus[:1]))

nebula.burn_max_speed = real_max_speed
nebula.cd_drive_nodes = real_drives
nebula.BurnDialog.exec = real_exec
nebula.BurnDialog.settings = real_settings
QMessageBox.question = real_question

# ---------------------------------------------------------------- session
section("session restore and config")
w.player.set_queue([WAV1, FLAC1])
w.library_tab._save_queue_state()
w.close()
saved = nebula.load_config()
check("queue saved on close", saved["queue"] == [WAV1, FLAC1], saved["queue"])
w2 = nebula.MainWindow()
check("queue restored on start", len(w2.player.queue) == 2, w2.player.queue)
check("volume and repeat survive", 0 <= w2.config["volume"] <= 100)
w2.close()

# ---------------------------------------------------------------- one data folder
section("two folders: settings and data apart from the rebuildable cache")
check("the data root is ~/Nebula", nebula.DATA_ROOT == DATA_ROOT, nebula.DATA_ROOT)
check("the cache root is ~/.cache/Nebula", nebula.CACHE_ROOT == CACHE_ROOT,
      nebula.CACHE_ROOT)
for _name in ("settings", "library", "sync"):
    check(f"the {_name} folder exists under the data root",
          os.path.isdir(os.path.join(DATA_ROOT, _name)), os.listdir(DATA_ROOT))
for _name in ("covers", "tmp"):
    check(f"the {_name} folder exists under the cache root only",
          os.path.isdir(os.path.join(CACHE_ROOT, _name))
          and not os.path.exists(os.path.join(DATA_ROOT, _name)),
          (os.listdir(DATA_ROOT), os.listdir(CACHE_ROOT)))
check("the config lives in settings/",
      nebula.CONFIG_FILE == os.path.join(DATA_ROOT, "settings", "config.json")
      and nebula.PROFILES_FILE == os.path.join(DATA_ROOT, "settings", "profiles.json")
      and nebula.SMART_FILE == os.path.join(DATA_ROOT, "settings", "smart_playlists.json"),
      nebula.CONFIG_FILE)
check("queue rows for device tracks live in settings/",
      nebula.QUEUE_META_FILE == os.path.join(DATA_ROOT, "settings", "queue-meta.json"),
      nebula.QUEUE_META_FILE)
check("the library and its collections live in library/",
      nebula.DB_FILE == os.path.join(DATA_ROOT, "library", "library.db")
      and nebula.new_collection_db("probe").startswith(
          os.path.join(DATA_ROOT, "library", "collections") + os.sep),
      nebula.DB_FILE)
check("exported playlists live in library/playlists/",
      nebula.PLAYLIST_DIR == os.path.join(DATA_ROOT, "library", "playlists"),
      nebula.PLAYLIST_DIR)
check("sync manifests and hashes live in sync/",
      nebula.MANIFEST_DIR == os.path.join(DATA_ROOT, "sync", "manifests")
      and nebula.HASH_DIR == os.path.join(DATA_ROOT, "sync", "hashdb"),
      nebula.MANIFEST_DIR)
check("covers get their own folder in the cache root",
      nebula.COVERS_DIR == os.path.join(CACHE_ROOT, "covers")
      and os.path.dirname(nebula._cover_cache_path("probe-mbid", 500)) == nebula.COVERS_DIR,
      nebula.COVERS_DIR)
check("every buffer lives in tmp/ under the cache root",
      nebula.CD_BUFFER_DIR == os.path.join(CACHE_ROOT, "tmp", "cd-buffer")
      and nebula.DEVICE_BUFFER_DIR == os.path.join(CACHE_ROOT, "tmp", "device-buffer"),
      (nebula.CD_BUFFER_DIR, nebula.DEVICE_BUFFER_DIR))
check("the cache root, covers and tmp are marked rebuildable, so backups skip them",
      all(os.path.isfile(os.path.join(p, "CACHEDIR.TAG"))
          for p in (nebula.CACHE_ROOT, nebula.COVERS_DIR, nebula.TMP_DIR)),
      os.listdir(nebula.TMP_DIR))

_stale = os.path.join(nebula.TMP_DIR, "stale-buffer")
_live = os.path.join(nebula.TMP_DIR, "live-buffer")
os.makedirs(_stale, exist_ok=True)
os.makedirs(_live, exist_ok=True)
write_text(os.path.join(_stale, "left-over.flac"), "flac")
write_text(os.path.join(_live, "playing.flac"), "flac")
_old_time = time.time() - 3 * 86400
os.utime(_stale, (_old_time, _old_time))
check("a buffer left by an old session is removed", nebula.prune_tmp() >= 1
      and not os.path.exists(_stale))
check("a buffer from this session is kept", os.path.exists(_live))
shutil.rmtree(_live, ignore_errors=True)

# ---------------------------------------------------------------- summary
section("summary")
failed = [r for r in RESULTS if not r[2]]
print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
for sec, name, _ok, detail in failed:
    print(f"  FAILED [{sec}] {name}: {detail}")
print(f"\nscratch home: {HOME} (removed when the run ends)")
sys.exit(1 if failed else 0)
