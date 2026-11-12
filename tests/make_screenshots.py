"""Render Nebula UI screenshots offscreen with a generated demo library.

QT_QPA_PLATFORM=offscreen python3 tests/make_screenshots.py
Writes artifacts/*.png
"""
import os
import shutil
import struct
import sys
import tempfile
import wave

HOME = tempfile.mkdtemp(prefix="nebula-shots-")
os.environ["HOME"] = HOME
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import matplotlib  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from mutagen.flac import FLAC, Picture  # noqa: E402
from mutagen.id3 import APIC, TALB, TCON, TDRC, TIT2, TPE1, TRCK  # noqa: E402
from mutagen.wave import WAVE  # noqa: E402

import nebula  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QFontDatabase, QImage, QLinearGradient, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

OUT = os.path.join(ROOT, "artifacts")
os.makedirs(OUT, exist_ok=True)
MUSIC = os.path.join(HOME, "Music")
os.makedirs(MUSIC, exist_ok=True)

app = QApplication([])
nebula.install_app_style(app)

# the sandbox has no system fonts; borrow DejaVu from matplotlib so text renders
_MPL_FONTS = [
    "/opt/freestyle/python/lib/python3.12/site-packages/matplotlib/mpl-data/fonts/ttf",
    os.path.join(os.path.dirname(os.path.dirname(matplotlib.__file__)),
                 "matplotlib", "mpl-data", "fonts", "ttf"),
]
for _dir in _MPL_FONTS:
    if os.path.isdir(_dir):
        for _name in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf"):
            QFontDatabase.addApplicationFont(os.path.join(_dir, _name))
        app.setFont(QFont("DejaVu Sans", 10))
        break

PALETTES = [("#1b2a4a", "#7aa2f7", "#e0a96d"), ("#2a1b3d", "#bb9af7", "#9ece6a"),
            ("#3d1b1b", "#f7768e", "#e0af68"), ("#10331f", "#9ece6a", "#7dcfff")]


def cover_png(name, palette, size=600):
    img = QImage(size, size, QImage.Format_RGB32)
    p = QPainter(img)
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor(palette[0]))
    grad.setColorAt(1, QColor(palette[1]))
    p.fillRect(0, 0, size, size, grad)
    p.setPen(QColor(palette[2]))
    p.setFont(QFont("DejaVu Sans", 40, QFont.Bold))
    p.drawText(img.rect().adjusted(40, 0, -40, -60), Qt.AlignLeft | Qt.AlignBottom, name)
    p.end()
    path = os.path.join(HOME, name.replace(" ", "_") + ".png")
    img.save(path)
    return path


def write_wav(path, seconds, tag, artist, album, track, year, genre, cover):
    with wave.open(path, "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(44100)
        n = int(44100 * seconds)
        f.writeframes(b"".join(struct.pack("<hh", int(900 * np.sin(2 * np.pi * 220 * i / 44100)), 0)
                               for i in range(n)))
    audio = WAVE(path)
    if audio.tags is None:
        audio.add_tags()
    for frame in (TIT2(encoding=3, text=tag), TPE1(encoding=3, text=artist),
                  TALB(encoding=3, text=album), TRCK(encoding=3, text=str(track)),
                  TDRC(encoding=3, text=year), TCON(encoding=3, text=genre)):
        audio.tags.add(frame)
    with open(cover, "rb") as f:
        audio.tags.add(APIC(encoding=3, mime="image/png", type=3, desc="Cover", data=f.read()))
    audio.save()


def write_flac(path, seconds, tag, artist, album, track, year, genre, cover, bits=24, rate=96000):
    sf.write(path, np.zeros((rate * seconds, 2), dtype="float32"), rate, subtype=f"PCM_{bits}")
    audio = FLAC(path)
    audio["title"] = tag
    audio["artist"] = artist
    audio["albumartist"] = artist
    audio["album"] = album
    audio["tracknumber"] = str(track)
    audio["date"] = year
    audio["genre"] = genre
    picture = Picture()
    picture.type = 3
    picture.mime = "image/png"
    with open(cover, "rb") as f:
        picture.data = f.read()
    audio.add_picture(picture)
    audio.save()


ALBUMS = [
    ("Faithless", "Reverence", "1995", "Electronic",
     ["Reverence", "Angeline", "Insomnia", "Salva Mea", "Don't Leave"], 0),
    ("Massive Attack", "Mezzanine", "1998", "Trip-Hop",
     ["Angel", "Risingson", "Teardrop", "Inertia Creeps", "Exchange"], 1),
    ("Air", "Moon Safari", "1998", "Ambient",
     ["La Femme d'Argent", "Sexy Boy", "All I Need", "Kelly Watch the Stars", "Ce Matin La"], 2),
    ("Bonobo", "Black Sands", "2010", "Downtempo",
     ["Prelude", "Kiara", "Kong", "Eyesdown", "El Toro"], 3),
]

demo_paths = []
for artist, album, year, genre, titles, pi in ALBUMS:
    folder = os.path.join(MUSIC, f"{artist} - {album}")
    os.makedirs(folder, exist_ok=True)
    cover = cover_png(album, PALETTES[pi])
    shutil.copyfile(cover, os.path.join(folder, "cover.png"))
    for idx, title in enumerate(titles, 1):
        if pi == 1 and idx in (2, 4):
            path = os.path.join(folder, f"{idx:02d} - {title}.flac")
            write_flac(path, 4, title, artist, album, idx, year, genre, cover)
        else:
            path = os.path.join(folder, f"{idx:02d} - {title}.wav")
            write_wav(path, 4, title, artist, album, idx, year, genre, cover)
        demo_paths.append(path)

cfg = nebula.load_config()
cfg["library_folders"] = [MUSIC]
cfg["volume"] = 64
cfg["split"] = [760, 640]
cfg["lib_columns"] = ["title", "artist", "album", "length", "year", "rating"]
nebula.save_config(cfg)

library = nebula.Library()
library.scan([MUSIC])

# ratings, plays and a couple of loved tracks so the columns mean something
by_album = {}
for row in library.tracks():
    by_album.setdefault(row["album"], []).append(row)
library.set_rating([r["path"] for r in by_album["Moon Safari"]], 5)
library.set_rating([r["path"] for r in by_album["Mezzanine"]], 4)
library.set_rating([r["path"] for r in by_album["Reverence"]][:3], 3)
library.set_loved([r["path"] for r in by_album["Moon Safari"][:2]], True)
for i, row in enumerate(library.tracks()):
    for _ in range((i * 3) % 7):
        library.play_count(row["path"])

w = nebula.MainWindow()
w.resize(1440, 900)
tab = w.library_tab
tab.refresh()
tab.reload_smart()
tab.reload_playlists()
tab.set_view("collection")


def shot(name, widget=None):
    app.processEvents()
    (widget or w).grab().save(os.path.join(OUT, name))
    print("wrote", name)


tab.tree.expandAll()
queue = [r["path"] for r in library.tracks()][:10]
w.player.set_queue(queue, 2)
w.player.play_index(2)
w.player.spectrum.set_playing(True)
for _ in range(4):
    w.player.spectrum.push_levels([0.25 + 0.6 * ((i * 7) % 11) / 11
                                   for i in range(nebula.SPECTRUM_BANDS)])

w.show()
app.processEvents()
shot("library.png")

def tree_items(tree):
    out = []
    stack = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
    while stack:
        item = stack.pop()
        out.append(item)
        stack.extend(item.child(i) for i in range(item.childCount()))
    return out

# one collapsed artist and one collapsed album, so both arrow states are visible
for _label in ("Bonobo", "Moon Safari"):
    _item = next((i for i in tree_items(tab.tree) if tab._node_label(i) == _label), None)
    if _item is not None:
        _item.setExpanded(False)
app.processEvents()
shot("library-collapsed.png")
tab.tree.expandAll()

tab.set_library_mode("covers")
shot("covers.png")
tab.set_library_mode("list")

tab.search.setText("year:>=1995 rating:>=4")
tab.refresh()
tab.tree.expandAll()
shot("filter.png")
tab.search.setText("")
tab.refresh()

tab.config["lib_columns"] = ["track", "title", "artist", "album", "year", "genre",
                             "length", "rating", "plays", "format"]
tab.grouping.setCurrentIndex(tab.grouping.findData("none"))
tab.refresh()
shot("flat.png")
tab.config["lib_columns"] = ["title", "artist", "album", "length", "year", "rating"]
tab.grouping.setCurrentIndex(tab.grouping.findData("artist_album"))
tab.refresh()

group_dialog = nebula.GroupByDialog(tab, ["genre", "decade", "album"],
                                     [{"name": "By decade", "levels": ["decade", "album"]},
                                      {"name": "Genre / artist", "levels": ["genre", "artist"]}])
group_dialog.resize(470, 520)
group_dialog.show()
app.processEvents()
shot("groupby.png", group_dialog)
group_dialog.close()

tab.set_view("smart")
shot("smart.png")

# real MusicBrainz lookup, when the network is available
tab.set_view("collection")
online_rows = [r for r in library.tracks() if r["album"] == "Black Sands"][:1]
online = nebula.OnlineLookupDialog(online_rows, library, w)
online.show()
app.processEvents()
try:
    online._show_results(nebula.mb_search_releases("Bonobo", "Black Sands"))
    import time as _time
    for _ in range(300):
        app.processEvents()
        worker = online._cover_worker
        if worker is None or worker.isFinished():
            break
        _time.sleep(0.05)
    if online._cover_worker is not None:
        online._cover_worker.wait(5000)
    for _ in range(120):
        app.processEvents()
        if online.preview.text() == "" and not online.preview.pixmap().isNull():
            break
        _time.sleep(0.03)
    app.processEvents()
    shot("online.png", online)
except Exception as exc:  # network blocked in this sandbox
    print("online lookup skipped:", exc)
online.close()

tab.set_view("collection")
dialog = nebula.CoverViewer(w.player._cover_bytes(w.player.current_path()),
                             "Teardrop", "Massive Attack — Mezzanine", w)
dialog.resize(760, 760)
dialog.show()
app.processEvents()
shot("cover.png", dialog)
dialog.close()

w.tabs.setCurrentWidget(w.tagger_tab)
w.tagger_tab.load_paths(queue[:4])
shot("tags.png")

w.tabs.setCurrentWidget(w.library_tab)
tab.set_view("playlists")
shot("playlists.png")
print("home:", HOME)
