#!/usr/bin/env python3
"""Hash-sync scenario suite (200+ independent cases).

Run:  QT_QPA_PLATFORM=offscreen python3 -u tests/sync_hash_check.py

Every scenario builds its own source library and device folder inside a throw-away
home. The suite is deliberately broader than the app's main tests: it walks the
decisions in SYNC_PART1.md and SYNC_PART2.md one branch at a time, including the
target-folder accident that produced two copies of every edited track.
"""
import atexit
import json
import os
import shutil
import sys
import tempfile
import traceback

HOME = tempfile.mkdtemp(prefix="nebula-synchash-")
os.environ["HOME"] = HOME
os.environ["NEBULA_DATA"] = os.path.join(HOME, "Nebula")
os.environ["NEBULA_CACHE"] = os.path.join(HOME, ".cache", "Nebula")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
atexit.register(shutil.rmtree, HOME, True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
sys.path.insert(0, ROOT)
sys.path.insert(0, ASSETS)

import nebula  # noqa: E402

RESULTS = []
NEXT = [0]


def check(name, condition, detail=""):
    try:
        ok = bool(condition)
    except Exception:
        ok = False
        detail = traceback.format_exc(limit=3)
    RESULTS.append((name, ok, detail))
    if not ok:
        print("  FAIL  " + name + "   <- " + str(detail))


def write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return path


def sha(data):
    return nebula.hashlib.sha256(data).hexdigest()


def edit_same_size(path, byte=0x80):
    with open(path, "r+b") as f:
        f.seek(-1, os.SEEK_END)
        last = f.read(1)
        f.seek(-1, os.SEEK_END)
        f.write(bytes([last[0] ^ byte]))


def bump(path, seconds=10):
    st = os.stat(path)
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + seconds * 10**9))


class Scene:
    def __init__(self, **options):
        NEXT[0] += 1
        self.root = os.path.join(HOME, f"case-{NEXT[0]:04d}")
        self.src = os.path.join(self.root, "library")
        self.dst = os.path.join(self.root, "device")
        os.makedirs(self.src)
        os.makedirs(self.dst)
        self.files = {}
        self.kinds = {}
        self.selected = set()
        self._p = None
        self.options = dict(target="Music", music_folder="Artists",
                            audiobook_folder="Audiobooks", mode="mirror",
                            method="hash", filesystem="mtp", audio_only=True,
                            selection_mode="selected")
        self.options.update(options)

    # ---------------------------------------------------------------- source
    def add(self, rel, data=None, select=True, kind=None):
        if data is None:
            data = ("audio:" + rel).encode("utf-8")
        path = write_bytes(os.path.join(self.src, *rel.split("/")), data)
        self.files[rel] = path
        self.kinds[rel] = kind
        if select:
            self.selected.add(rel)
            if self._p is not None:
                entry = {"path": path, "rel": rel}
                if kind:
                    entry["kind"] = kind
                self._p.selection.append(entry)
        return path

    def data(self, rel):
        with open(self.files[rel], "rb") as f:
            return f.read()

    # ---------------------------------------------------------------- profile
    def make(self, **over):
        opts = dict(self.options)
        opts.update(over)
        if "selection" in opts:
            entries = opts.pop("selection")
        else:
            entries = []
            for rel in self.files:
                if rel not in self.selected:
                    continue
                entry = {"path": self.files[rel], "rel": rel}
                if self.kinds.get(rel):
                    entry["kind"] = self.kinds[rel]
                entries.append(entry)
        opts.setdefault("name", "Scenario")
        opts.setdefault("device_id", "folder:" + self.dst)
        opts.setdefault("source", self.src)
        opts.setdefault("sources", [self.src])
        opts.setdefault("selection", entries)
        self._p = nebula.Profile(**opts)
        return self._p

    @property
    def p(self):
        return self._p or self.make()

    @property
    def prefix(self):
        target = self.p.target.strip("/")
        return target + "/" if target else ""

    def backend(self):
        return nebula.LocalFolderBackend(self.dst)

    # ---------------------------------------------------------------- paths
    def route_key(self, rel):
        full = os.path.realpath(self.files[rel])
        files = nebula.profile_sync_files(self.p, False)
        for key, (path, _size) in files.items():
            if os.path.realpath(path) == full:
                return key
        raise KeyError((rel, list(files)))

    def dev(self, rel):
        files = nebula.profile_sync_files(self.p, False)
        names = nebula._sync_names(self.p, files.keys())
        return names[self.route_key(rel)]

    def full(self, dev):
        target = self.p.target.strip("/")
        return os.path.join(self.dst, *target.split("/"), *dev.split("/")) if target \
            else os.path.join(self.dst, *dev.split("/"))

    def has(self, rel):
        return os.path.exists(self.full(self.dev(rel)))

    def device_files(self):
        out = []
        for root, _dirs, names in os.walk(self.dst):
            for name in names:
                out.append(os.path.relpath(os.path.join(root, name), self.dst)
                           .replace(os.sep, "/"))
        return sorted(out)

    # ---------------------------------------------------------------- operations
    def compare(self, **kw):
        return nebula.compare(self.p, self.backend(), **kw)

    def sync(self, **kw):
        plan = self.compare(**kw)
        errors = nebula.execute(self.p, self.backend(), plan)
        return plan, errors

    def manifest(self):
        return nebula.DeviceManifest(self.p)

    def store(self):
        return nebula.HashStore(self.p)

    def record_duplicate(self, rel, dev, data=None):
        data = self.data(rel) if data is None else data
        full = self.full(dev)
        write_bytes(full, data)
        key = self.route_key(rel)
        manifest = self.manifest()
        manifest.record(self.prefix + dev, key, len(data), sha(data), 0, self.p.id)
        manifest.save()
        return full

    def select_only(self, rels):
        rels = set(rels)
        self.selected = set(rels)
        self.p.selection = [
            dict({"path": self.files[rel], "rel": rel},
                 **({"kind": self.kinds[rel]} if self.kinds.get(rel) else {}))
            for rel in self.files if rel in rels]


def rows(plan, include_equal=False):
    return sorted((a.kind, a.dev or a.rel) for a in plan
                  if include_equal or a.kind != "equal")


def kinds(plan):
    return sorted(a.kind for a in plan)


def one_new(scene, **kw):
    plan = scene.compare(**kw)
    return len(plan) == 1 and plan[0].kind == "new" and plan[0].dev == scene.dev(list(scene.files)[0])


# ======================================================================
# 1. Target, media folder and device-name routing
# ======================================================================
def group_routing():
    cases = [
        ("plain", "Artist/Album/01 - Track.flac", "Music", "Artists", "mtp",
         "Artists/Artist/Album/01 - Track.flac"),
        ("nested target", "Artist/Album/01 - Track.flac", "Walkman_SD/Music", "Artists", "mtp",
         "Artists/Artist/Album/01 - Track.flac"),
        ("target trailing slash", "Artist/Album/01 - Track.flac", "/Music/", "Artists", "mtp",
         "Artists/Artist/Album/01 - Track.flac"),
        ("relative already carries Artists", "Artists/Artist/Album/01.flac", "Music", "Artists", "mtp",
         "Artists/Artist/Album/01.flac"),
        ("no media folder", "Artist/Album/01.flac", "Music", "", "mtp", "Artist/Album/01.flac"),
        ("empty target", "Artist/Album/01.flac", "", "Artists", "mtp", "Artists/Artist/Album/01.flac"),
        ("nested media folder", "Artist/Album/01.flac", "Music", "Music/Artists", "mtp",
         "Music/Artists/Artist/Album/01.flac"),
        ("backslashes in a selection", "Artist\\Album\\01.flac", "Music", "Artists", "mtp",
         "Artists/Artist/Album/01.flac"),
        ("leading slash in a selection", "/Artist/Album/01.flac", "Music", "Artists", "mtp",
         "Artists/Artist/Album/01.flac"),
        ("CJK names", "月詠み/月が満ちる/01 - 廻想.flac", "Walkman_SD/Music", "Artists", "exfat",
         "Artists/月詠み/月が満ちる/01 - 廻想.flac"),
        ("emoji names", "Artist/🎵 Album/01 - Song.flac", "Music", "Artists", "exfat",
         "Artists/Artist/🎵 Album/01 - Song.flac"),
        ("unicode target", "Artist/Album/01.flac", "Музыка", "Artists", "exfat",
         "Artists/Artist/Album/01.flac"),
        ("spaces in target", "Artist/Album/01.flac", "My Music", "Artists", "mtp",
         "Artists/Artist/Album/01.flac"),
        ("deep source path", "A/B/C/D/E/01.flac", "Music", "Artists", "mtp",
         "Artists/A/B/C/D/E/01.flac"),
        ("audiobook tree", "Dune/Chapter 01.m4b", "Music", "Artists", "mtp",
         "Audiobooks/Dune/Chapter 01.m4b"),
        ("audiobook already routed", "Audiobooks/Dune/Chapter 01.m4b", "Music", "Artists", "mtp",
         "Audiobooks/Dune/Chapter 01.m4b"),
        ("custom audiobook folder", "Dune/Chapter 01.m4b", "Music", "Artists", "mtp",
         "Books/Dune/Chapter 01.m4b"),
        ("empty audiobook folder", "Dune/Chapter 01.m4b", "Music", "Artists", "mtp",
         "Dune/Chapter 01.m4b"),
    ]
    for label, rel, target, folder, fs, expected in cases:
        s = Scene(target=target, music_folder=folder,
                  audiobook_folder="Books" if label == "custom audiobook folder" else
                  ("" if label == "empty audiobook folder" else "Audiobooks"),
                  filesystem=fs)
        s.add(rel, kind="audiobook" if "audiobook" in label else "music")
        p = s.make()
        check("routing: " + label + " plans the canonical path",
              [(a.kind, a.dev) for a in s.compare()] == [("new", expected)],
              [(a.kind, a.dev) for a in s.compare()])
        plan, errors = s.sync()
        check("routing: " + label + " writes that exact path",
              errors == 0 and os.path.exists(s.full(expected)), (errors, s.device_files()))
        second = s.compare()
        check("routing: " + label + " is stable on the next compare",
              len(second) == 1 and second[0].kind == "equal" and not second[0].verified,
              [(a.kind, a.dev) for a in second])

    # A podcast selection is deliberately ignored.
    s = Scene()
    s.add("Show/episode.mp3", kind="podcast")
    check("routing: a podcast selection is paused and never copied",
          s.compare() == [] and s.device_files() == [], s.device_files())

    # A music file explicitly marked as an audiobook follows the audiobook folder.
    s = Scene()
    s.add("Book.m4b", kind="audiobook")
    s.sync()
    check("routing: a kind overrides the extension for the media tree",
          os.path.exists(s.full("Audiobooks/Book.m4b")), s.device_files())


def group_device_names():
    # FAT32 names lose what the filesystem cannot store; every other filesystem keeps
    # the PC name exactly.
    fat_cases = [
        ("question mark", "A/01 ?.flac", "A/01 .flac"),
        ("star", "A/01*.flac", "A/01.flac"),
        ("colon", "A/01:02.flac", "A/0102.flac"),
        ("double quote", 'A/01"02.flac', "A/0102.flac"),
        ("less than", "A/01<02.flac", "A/0102.flac"),
        ("greater than", "A/01>02.flac", "A/0102.flac"),
        ("pipe", "A/01|02.flac", "A/0102.flac"),
        ("backslash", "A/01\\02.flac", "A/01/02.flac"),
        ("control character", "A/01\x0102.flac", "A/0102.flac"),
        ("trailing dot folder", "A./01.flac", "A/01.flac"),
        ("trailing space folder", "A /01.flac", "A/01.flac"),
        ("all-illegal stem", "A/???.flac", "A/.flac"),
    ]
    for label, rel, expected in fat_cases:
        s = Scene(filesystem="fat32", music_folder="")
        s.add(rel)
        plan = s.compare()
        check("names: FAT32 strips " + label,
              len(plan) == 1 and plan[0].dev == expected,
              [(a.kind, a.dev) for a in plan])
        s.sync()
        check("names: FAT32 " + label + " lands at the stripped path",
              os.path.exists(s.full(expected)), s.device_files())

    for label, rel in [
            ("reserved characters", "A/01 ?*:<>|.flac"),
            ("CJK", "A/月が満ちる.flac"),
            ("combining marks", "A/e\u0301.flac"),
            ("trailing dot", "A./01.flac")]:
        s = Scene(filesystem="exfat", music_folder="")
        s.add(rel, select=True)
        plan = s.compare()
        expected = rel.replace("?", "?")  # exFAT keeps everything
        check("names: exFAT keeps " + label,
              len(plan) == 1 and plan[0].dev == expected,
              [(a.kind, a.dev) for a in plan])
        s.sync()
        check("names: exFAT " + label + " is byte-for-name on the device",
              os.path.exists(s.full(expected)), s.device_files())

    # Case-insensitive collisions get a stable suffix, and both copies survive.
    for count in (2, 3, 5):
        s = Scene(filesystem="exfat", music_folder="")
        rels = [("A/Song.flac" if i == 0 else f"A/song{i}.flac") for i in range(count)]
        # Same letters, different case and names that collide after lowercasing.
        rels = ["A/Song.flac"] + [f"A/SONG ({i}).flac" for i in range(1, count)]
        for rel in rels:
            s.add(rel)
        plan = s.compare()
        devs = sorted(a.dev for a in plan)
        check(f"names: a {count}-way case collision gets unique device names",
              len(devs) == count and len({d.lower() for d in devs}) == count
              and "A/Song.flac" in devs, devs)
        s.sync()
        check(f"names: all {count} colliding files arrive",
              sum(1 for f in s.device_files() if f.startswith("Music/A/")) == count,
              s.device_files())
        check(f"names: the {count}-way collision is stable on repeat",
              all(a.kind == "equal" for a in s.compare()),
              rows(s.compare(), include_equal=True))

    # Removing the first of a collision pair renumbers the survivor. That is a path
    # change and must be a copy plus a delete, never a duplicate.
    s = Scene(filesystem="exfat", music_folder="")
    s.add("A/Song.flac")
    s.add("A/SONG.flac")
    s.sync()
    first = s.files["A/Song.flac"]
    s.files.pop("A/Song.flac")
    s.selected.discard("A/Song.flac")
    s.p.selection = [e for e in s.p.selection if e["path"] != first]
    os.remove(first)
    plan = s.compare()
    check("names: removing one case-collision file deletes only its stale copy",
          any(a.kind == "delete" for a in plan)
          and any(a.kind == "equal" for a in plan)
          and not any(a.kind in ("new", "changed") for a in plan),
          [(a.kind, a.dev) for a in plan])


# ======================================================================
# 2. The ordinary lifecycle: new, equal, changed, removed, selected, renamed
# ======================================================================
def group_lifecycle():
    s = Scene()
    s.add("Artist/Album/01 - Track.flac")
    first = s.compare()
    check("life: a first compare plans the file new",
          [(a.kind, a.dev) for a in first]
          == [("new", s.dev("Artist/Album/01 - Track.flac"))],
          [(a.kind, a.dev) for a in first])
    s.sync()
    track_dev = s.dev("Artist/Album/01 - Track.flac")
    track_full = s.full(track_dev)
    check("life: the first sync writes the canonical file", s.has("Artist/Album/01 - Track.flac"))
    second = s.compare()
    check("life: a repeat compare is equal and trusts the manifest",
          len(second) == 1 and second[0].kind == "equal" and not second[0].verified,
          [(a.kind, a.dev, a.verified) for a in second])

    # A trusted repeat must not open a device file at all.
    b = s.backend()
    reads = []
    real_open = b.open_read
    b.open_read = lambda rel: (reads.append(rel), real_open(rel))[1]
    try:
        fast = nebula.compare(s.p, b)
    finally:
        b.open_read = real_open
    check("life: a trusted repeat reads no device bytes", reads == [] and fast[0].kind == "equal",
          (reads, [(a.kind, a.dev) for a in fast]))

    # A changed PC file is one update, never an extra copy.
    src = s.files["Artist/Album/01 - Track.flac"]
    old_size = os.path.getsize(src)
    edit_same_size(src)
    bump(src)
    changed = s.compare()
    check("life: a same-size PC edit is one changed action",
          [(a.kind, a.dev) for a in changed] == [("changed", s.dev("Artist/Album/01 - Track.flac"))],
          [(a.kind, a.dev) for a in changed])
    s.sync()
    check("life: the changed copy replaces the device bytes",
          open(s.full(s.dev("Artist/Album/01 - Track.flac")), "rb").read() == s.data(
              "Artist/Album/01 - Track.flac"))
    check("life: a changed file does not create a second device path",
          len(s.device_files()) == 1, s.device_files())

    # A different-size edit takes the same path.
    with open(src, "ab") as f:
        f.write(b"more")
    plan = s.compare()
    check("life: a different-size PC edit is changed",
          [(a.kind, a.dev) for a in plan] == [("changed", s.dev("Artist/Album/01 - Track.flac"))],
          [(a.kind, a.dev) for a in plan])
    s.sync()

    # Touching a file without changing its bytes is equal, and may re-hash the PC file.
    bump(src)
    check("life: a PC timestamp-only touch stays equal",
          [a.kind for a in s.compare()] == ["equal"],
          [(a.kind, a.dev) for a in s.compare()])

    # A device file deleted outside the app is restored, not duplicated.
    os.remove(track_full)
    plan = s.compare()
    check("life: a deleted device copy is a restore",
          [(a.kind, a.dev) for a in plan]
          == [("restore", track_dev)],
          [(a.kind, a.dev) for a in plan])
    s.sync()
    check("life: the restore brings back exactly one copy",
          len(s.device_files()) == 1 and s.has("Artist/Album/01 - Track.flac"),
          s.device_files())

    # A source removed from the selection is deleted by Mirror and kept by Update.
    s.select_only([])
    plan = s.compare()
    check("life: unticking a synced item is a Mirror delete",
          [(a.kind, a.dev) for a in plan]
          == [("delete", track_dev)],
          [(a.kind, a.dev) for a in plan])
    s.p.mode = "update"
    check("life: Update leaves an unticked item alone",
          s.compare() == [] and os.path.exists(track_full))
    s.p.mode = "mirror"
    s.sync()
    check("life: the Mirror delete removes the unselected copy", not os.path.exists(track_full))
    check("life: a deleted selected file is no longer in the hash store",
          "Artist/Album/01 - Track.flac" not in s.store().records)

    # Ticking it again is new, not a stale equal.
    s.select_only(["Artist/Album/01 - Track.flac"])
    plan = s.compare()
    check("life: re-ticking a deleted item plans it new",
          [(a.kind, a.dev) for a in plan]
          == [("new", s.dev("Artist/Album/01 - Track.flac"))],
          [(a.kind, a.dev) for a in plan])
    s.sync()
    check("life: the re-ticked item returns once",
          len(s.device_files()) == 1, s.device_files())

    # Renaming the PC file changes its relative path. Mirror removes the old device
    # path; Update keeps it. There must never be two copies after a Mirror sync.
    s = Scene()
    s.add("Artist/Album/01 - Old.flac")
    s.sync()
    old_full = s.full(s.dev("Artist/Album/01 - Old.flac"))
    new_rel = "Artist/Album/01 - New.flac"
    os.rename(s.files["Artist/Album/01 - Old.flac"], os.path.join(s.src, "Artist", "Album", "01 - New.flac"))
    s.files[new_rel] = os.path.join(s.src, "Artist", "Album", "01 - New.flac")
    s.selected = {new_rel}
    s.p.selection = [{"path": s.files[new_rel], "rel": new_rel}]
    plan = s.compare()
    check("life: a renamed PC file is new plus delete under Mirror",
          sorted((a.kind, a.dev) for a in plan)
          == [("delete", "Artists/Artist/Album/01 - Old.flac"),
              ("new", "Artists/Artist/Album/01 - New.flac")],
          [(a.kind, a.dev) for a in plan])
    s.sync()
    check("life: the rename leaves only the new path",
          len(s.device_files()) == 1 and not os.path.exists(old_full),
          s.device_files())

    s = Scene()
    s.add("Artist/Album/01 - Old.flac")
    s.sync()
    os.rename(s.files["Artist/Album/01 - Old.flac"], os.path.join(s.src, "Artist", "Album", "01 - New.flac"))
    s.files[new_rel] = os.path.join(s.src, "Artist", "Album", "01 - New.flac")
    s.selected = {new_rel}
    s.p.selection = [{"path": s.files[new_rel], "rel": new_rel}]
    s.p.mode = "update"
    plan = s.compare()
    check("life: a renamed PC file under Update copies the new path and keeps the old",
          rows(plan) == [("new", "Artists/Artist/Album/01 - New.flac")],
          [(a.kind, a.dev) for a in plan])
    s.p.mode = "mirror"
    s.sync()
    check("life: switching back to Mirror removes the old renamed copy",
          not os.path.exists(old_full), s.device_files())

    # Adding a new source file next to an equal one.
    s = Scene()
    s.add("Artist/Album/01.flac")
    s.sync()
    s.add("Artist/Album/02.flac")
    plan = s.compare()
    check("life: adding one source file plans only that file new",
          rows(plan) == [("new", "Artists/Artist/Album/02.flac")],
          [(a.kind, a.dev) for a in plan])
    s.sync()
    check("life: the added file arrives beside the equal one",
          len(s.device_files()) == 2, s.device_files())

    # Dropping one of two source files.
    gone_dev = s.dev("Artist/Album/01.flac")
    gone_full = s.full(gone_dev)
    gone = s.files.pop("Artist/Album/01.flac")
    s.selected.discard("Artist/Album/01.flac")
    s.p.selection = [e for e in s.p.selection if e["path"] != gone]
    os.remove(gone)
    plan = s.compare()
    check("life: dropping one of two source files deletes only that path",
          rows(plan) == [("delete", gone_dev)],
          [(a.kind, a.dev) for a in plan])
    s.sync()
    check("life: the other file survives the delete",
          s.has("Artist/Album/02.flac") and not os.path.exists(gone_full),
          s.device_files())

    # Emptying the selection removes every owned copy under Mirror.
    s = Scene()
    for i in range(3):
        s.add(f"Artist/Album/0{i + 1}.flac")
    s.sync()
    s.select_only([])
    plan = s.compare()
    check("life: emptying a three-file selection deletes all three",
          len([a for a in plan if a.kind == "delete"]) == 3, rows(plan))
    s.sync()
    check("life: the emptied Mirror target has no audio left",
          [f for f in s.device_files() if f.endswith(".flac")] == [], s.device_files())

    # Multi-file runs are stable, not quadratic duplicates.
    for count in (1, 2, 3, 6):
        s = Scene()
        for i in range(count):
            s.add(f"Artist/Album/{i + 1:02d}.flac")
        plan = s.compare()
        check(f"life: {count} new files are all planned new",
              len(plan) == count and all(a.kind == "new" for a in plan), rows(plan))
        s.sync()
        check(f"life: {count} files reach the device",
              len(s.device_files()) == count, s.device_files())
        repeat = s.compare()
        check(f"life: {count} files compare equal on repeat",
              len(repeat) == count and all(a.kind == "equal" for a in repeat), rows(repeat))

    # Two source folders.
    s = Scene()
    s.add("Artist/Album/01.flac")
    second = os.path.join(s.root, "library2")
    write_bytes(os.path.join(second, "Other", "Book", "01.flac"), b"second-source")
    s.p.sources = [s.src, second]
    s.p.selection_mode = "folders"
    plan = s.compare()
    check("life: two source folders contribute at the same target",
          sorted(a.dev for a in plan) == ["Artists/Artist/Album/01.flac",
                                          "Artists/Other/Book/01.flac"],
          rows(plan))

    # Nothing to do.
    s = Scene()
    check("life: an empty selection plans nothing", s.compare() == [])

# ======================================================================
# 3. Manifest states: missing, untrusted, stale, duplicated, owned elsewhere
# ======================================================================
def group_manifest_states():
    rel = "Artist/Album/01.flac"
    dev = "Artists/Artist/Album/01.flac"

    def base():
        s = Scene()
        s.add(rel)
        s.sync()
        return s

    # Missing on the device, but the manifest remembers it.
    s = base()
    os.remove(s.full(dev))
    plan = s.compare()
    check("manifest: a missing canonical copy is a restore",
          rows(plan) == [("restore", dev)], rows(plan))
    s.sync()
    check("manifest: the restore recreates one copy",
          len(s.device_files()) == 1 and s.has(rel), s.device_files())

    # The manifest is gone but the hash store still says this profile wrote it.
    s = base()
    os.remove(s.full(dev))
    os.remove(s.manifest().path)
    plan = s.compare()
    check("manifest: a lost manifest still restores from the hash store",
          rows(plan) == [("restore", dev)], rows(plan))

    # Neither record survives: the file is new, not restored.
    s = base()
    os.remove(s.full(dev))
    os.remove(s.manifest().path)
    store = s.store()
    for key in list(store.records):
        store.records[key].pop("synced_hash", None)
        store.records[key].pop("dev", None)
    store.save()
    plan = s.compare()
    check("manifest: no record at all makes a missing file new",
          rows(plan) == [("new", dev)], rows(plan))

    # A canonical file with no manifest record is read once and adopted.
    s = base()
    os.remove(s.manifest().path)
    plan = s.compare()
    check("manifest: a canonical file with no record is read and adopted as equal",
          rows(plan, True) == [("equal", dev)] and plan[0].verified, rows(plan, True))
    check("manifest: adopting it records this profile as the owner",
          (s.manifest().get(s.prefix + dev) or {}).get("profile") == s.p.id,
          s.manifest().files)

    # No record and different bytes: changed, not equal.
    s = base()
    os.remove(s.manifest().path)
    write_bytes(s.full(dev), b"different-bytes-same-length" + b"x" * 0)
    edit_same_size(s.full(dev), 0x01)
    plan = s.compare()
    check("manifest: an unrecorded canonical file with different bytes is changed",
          rows(plan) == [("changed", dev)], rows(plan))

    # A record with the wrong content hash is not trusted; the app replaces the copy.
    s = base()
    m = s.manifest()
    rec = m.get(s.prefix + dev)
    rec["hash"] = "0" * 64
    m.save()
    plan = s.compare()
    check("manifest: a wrong recorded hash forces a changed copy",
          rows(plan) == [("changed", dev)], rows(plan))

    # A record with the wrong size is likewise not trusted.
    s = base()
    m = s.manifest()
    m.get(s.prefix + dev)["size"] = 1
    m.save()
    check("manifest: a wrong recorded size forces a changed copy",
          rows(s.compare()) == [("changed", dev)], rows(s.compare()))

    # A record that names another source is not evidence for this one.
    s = base()
    m = s.manifest()
    m.get(s.prefix + dev)["rel"] = "Other/File.flac"
    m.save()
    plan = s.compare()
    check("manifest: a record for another rel is read and re-owned",
          rows(plan, True) == [("equal", dev)] and plan[0].verified, rows(plan, True))
    check("manifest: re-owning fixes the recorded rel",
          (s.manifest().get(s.prefix + dev) or {}).get("rel") == dev, s.manifest().files)

    # A record from another profile is not trusted, but equal bytes are adopted.
    s = base()
    m = s.manifest()
    m.get(s.prefix + dev)["profile"] = "some-other-profile"
    m.save()
    plan = s.compare()
    check("manifest: another profile's equal record is re-owned after a read",
          rows(plan, True) == [("equal", dev)] and plan[0].verified, rows(plan, True))
    check("manifest: the adopted record now belongs to this profile",
          (s.manifest().get(s.prefix + dev) or {}).get("profile") == s.p.id,
          s.manifest().files)

    # A timestamp that moved by less than the two-second tolerance is ignored.
    s = base()
    m = s.manifest()
    m.get(s.prefix + dev)["mtime"] = os.path.getmtime(s.full(dev)) + 1.0
    m.save()
    check("manifest: a one-second clock move is trusted equal",
          rows(s.compare(), True) == [("equal", dev)] and not s.compare()[0].verified,
          rows(s.compare(), True))

    # A larger move is a hint to read, and equal bytes still mean equal.
    s = base()
    m = s.manifest()
    m.get(s.prefix + dev)["mtime"] = os.path.getmtime(s.full(dev)) - 20.0
    m.save()
    plan = s.compare()
    check("manifest: a large clock move re-reads equal bytes without copying",
          rows(plan, True) == [("equal", dev)] and plan[0].verified, rows(plan, True))

    # A device with no clock makes the timestamp hint useless; the bytes decide.
    s = base()
    os.utime(s.full(dev), (0, 0))
    plan = s.compare()
    check("manifest: a zero device timestamp re-reads instead of copying",
          plan[0].kind == "equal" and plan[0].verified, rows(plan, True))

    # Corrupt manifest JSON behaves like a missing manifest.
    s = base()
    write_bytes(s.manifest().path, b"{")
    plan = s.compare()
    check("manifest: corrupt JSON is ignored and equal bytes are adopted",
          rows(plan, True) == [("equal", dev)] and plan[0].verified, rows(plan, True))

    # Corrupt hash cache is rebuilt without losing the manifest trust.
    s = base()
    write_bytes(s.store().path, b"not json")
    plan = s.compare()
    check("manifest: corrupt hash cache is rebuilt and the file stays equal",
          plan[0].kind == "equal" and not plan[0].verified, rows(plan, True))

    # A record under a previous target is not a record for the current one.
    s = base()
    old_dev = s.dev(rel)
    s.p.target = "NewMusic"
    plan = s.compare()
    check("manifest: a record under the old target does not make the new path equal",
          len(plan) == 1 and plan[0].kind in ("new", "restore")
          and plan[0].dev == old_dev, [(a.kind, a.dev) for a in plan])
    s.sync()
    check("manifest: the old target copy is left alone after the target change",
          os.path.exists(os.path.join(s.dst, "Music", *old_dev.split("/"))),
          s.device_files())

    # An unselected owned file is deleted by Mirror, kept by Update.
    s = base()
    s.select_only([])
    mirror_plan = s.compare()
    check("manifest: an unselected owned file is deleted by Mirror",
          rows(mirror_plan) == [("delete", dev)], rows(mirror_plan))
    s.p.mode = "update"
    check("manifest: Update leaves an unselected owned file",
          rows(s.compare()) == [], rows(s.compare()))
    s.p.mode = "mirror"
    s.sync()
    check("manifest: the unselected copy is gone after the Mirror run",
          not os.path.exists(s.full(dev)))

    # A stale store record with no synced_hash is not evidence of a device copy.
    s = base()
    os.remove(s.manifest().path)
    s.select_only([])
    store = s.store()
    for rec in store.records.values():
        rec.pop("synced_hash", None)
        rec.pop("dev", None)
    store.save()
    check("manifest: a store record that never reached the device is ignored",
          rows(s.compare()) == [], rows(s.compare()))

    # A stale store record with no manifest still removes the file.
    s = base()
    os.remove(s.manifest().path)
    s.select_only([])
    plan = s.compare()
    check("manifest: a stale store record alone can delete its device copy",
          rows(plan) == [("delete", dev)], rows(plan))

    # A stale record whose device copy is already gone is dropped quietly.
    s = base()
    os.remove(s.full(dev))
    s.select_only([])
    plan = s.compare()
    check("manifest: a stale record for an already-missing file plans nothing",
          rows(plan) == [], rows(plan))
    check("manifest: that stale record is forgotten",
          s.manifest().get(s.prefix + dev) is None and not s.store().records,
          (s.manifest().files, s.store().records))

    # Non-audio is held to the audio-only rule.
    s = Scene(audio_only=False)
    s.add("Artist/Album/notes.txt", data=b"not audio")
    s.sync()
    s.select_only([])
    s.p.audio_only = True
    check("manifest: audio-only Mirror leaves an unselected non-audio file",
          rows(s.compare()) == [], rows(s.compare()))
    s.p.audio_only = False
    check("manifest: clearing audio-only makes the stale non-audio deletable",
          rows(s.compare()) == [("delete", "Artists/Artist/Album/notes.txt")],
          rows(s.compare()))

    # Duplicate device paths for a still-selected file: the central fix.
    s = base()
    dup = "Artists/Artists/Artist/Album/01.flac"
    s.record_duplicate(rel, dup)
    plan = s.compare()
    check("duplicate: a second recorded path is removed by Mirror",
          rows(plan) == [("delete", dup)], rows(plan))
    s.sync()
    check("duplicate: only the canonical path remains after the sync",
          s.device_files() == ["Music/" + dev], s.device_files())

    s = base()
    s.record_duplicate(rel, dup)
    s.p.mode = "update"
    check("duplicate: Update keeps the extra path",
          rows(s.compare()) == [] and os.path.exists(s.full(dup)), rows(s.compare()))

    s = base()
    s.record_duplicate(rel, "Artists/Artists/Artist/Album/01.flac")
    s.record_duplicate(rel, "Artists/Old/01.flac")
    plan = s.compare()
    check("duplicate: every extra recorded path is deleted, not just one",
          sorted(rows(plan)) == [("delete", "Artists/Artists/Artist/Album/01.flac"),
                                 ("delete", "Artists/Old/01.flac")], rows(plan))

    # A duplicate record with no file on the device is simply forgotten.
    s = base()
    m = s.manifest()
    m.record(s.prefix + dup, dev, os.path.getsize(s.files[rel]),
             nebula.file_hash256(s.files[rel]), 0, s.p.id)
    m.save()
    check("duplicate: a record for a missing extra plans nothing",
          rows(s.compare()) == [], rows(s.compare()))
    check("duplicate: the record for the missing extra is forgotten",
          s.manifest().get(s.prefix + dup) is None, s.manifest().files)

    # Duplicates owned by another profile are never touched.
    s = base()
    other = "Artists/Other/01.flac"
    write_bytes(s.full(other), s.data(rel))
    m = s.manifest()
    m.record(s.prefix + other, dev, len(s.data(rel)), sha(s.data(rel)), 0, "other-profile")
    m.save()
    check("duplicate: another profile's extra is left alone",
          rows(s.compare()) == [] and os.path.exists(s.full(other)),
          rows(s.compare()))

    # Corrupt ownership fields cannot delete anything.
    s = base()
    m = s.manifest()
    m.record(s.prefix + "Artists/EmptyRel/01.flac", "", 10, "0" * 64, 0, s.p.id)
    m.record("", dev, 10, "0" * 64, 0, s.p.id)
    m.save()
    check("duplicate: empty rel/dev records are ignored",
          rows(s.compare()) == [], rows(s.compare()))

    # A stale record must not delete the canonical path of a different selected file.
    s = Scene()
    s.add("Artist/One.flac")
    s.add("Artist/Two.flac")
    s.sync()
    m = s.manifest()
    one = s.prefix + s.dev("Artist/One.flac")
    two = s.prefix + s.dev("Artist/Two.flac")
    m.record(two, s.route_key("Artist/One.flac"), os.path.getsize(s.files["Artist/Two.flac"]),
             nebula.file_hash256(s.files["Artist/Two.flac"]), 0, s.p.id)
    # Remove the real record for Two and mark One unselected so its record can poison it.
    m.forget(two)
    m.record(two, s.route_key("Artist/One.flac"), 1, "0" * 64, 0, s.p.id)
    m.save()
    s.select_only(["Artist/Two.flac"])
    plan = s.compare()
    check("duplicate: a stale record cannot delete another selected file's canonical path",
          s.has("Artist/Two.flac")
          and not any(a.kind == "delete"
                      and (a.dev or "").lower() == s.dev("Artist/Two.flac").lower()
                      for a in plan),
          [(a.kind, a.dev) for a in plan])


# ======================================================================
# 4. Verify content: exact reads, canonical restores, no resurrection
# ======================================================================
def group_verify():
    rel = "Artist/Album/01.flac"
    dev = "Artists/Artist/Album/01.flac"
    s = Scene()
    s.add(rel)
    s.sync()
    plan = s.compare(verify=True)
    check("verify: an untouched file is equal because it was read",
          plan[0].kind == "equal" and plan[0].verified, rows(plan, True))
    check("verify: the manifest record carries no timestamp",
          float((s.manifest().get(s.prefix + dev) or {}).get("mtime", -1)) == 0.0,
          s.manifest().files)

    # A same-size device edit with its old timestamp is invisible to Fast hash but
    # impossible to hide from Verify content.
    s = Scene()
    s.add(rel)
    s.sync()
    full = s.full(dev)
    st = os.stat(full)
    edit_same_size(full, 0x11)
    os.utime(full, ns=(st.st_atime_ns, st.st_mtime_ns))
    check("verify: Fast hash misses a same-size edit with a restored timestamp",
          s.compare()[0].kind == "equal", rows(s.compare(), True))
    verify_plan = s.compare(verify=True)
    check("verify: Verify content catches that exact edit",
          rows(verify_plan, True) == [("changed", dev)], rows(verify_plan, True))

    # Verify content also reads the PC side, so a PC edit with a restored timestamp
    # cannot hide behind the PC hash cache.
    s = Scene()
    s.add(rel)
    s.sync()
    st = os.stat(s.files[rel])
    edit_same_size(s.files[rel], 0x22)
    os.utime(s.files[rel], ns=(st.st_atime_ns, st.st_mtime_ns))
    verify_plan = s.compare(verify=True)
    check("verify: Verify content bypasses the PC hash cache",
          rows(verify_plan, True) == [("changed", dev)], rows(verify_plan, True))

    # Missing canonical copy: Verify restores it.
    s = Scene()
    s.add(rel)
    s.sync()
    os.remove(s.full(dev))
    plan = s.compare(verify=True)
    check("verify: a missing canonical file is a restore", rows(plan) == [("restore", dev)],
          rows(plan))
    s.sync()
    check("verify: the restore lands on the canonical path", s.has(rel) and len(s.device_files()) == 1,
          s.device_files())

    # A non-canonical record with no file must not be restored by Verify.
    s = Scene()
    s.add(rel)
    s.sync()
    m = s.manifest()
    ghost = "Artists/Artists/Artist/Album/01.flac"
    m.record(s.prefix + ghost, s.route_key(rel), os.path.getsize(s.files[rel]),
             nebula.file_hash256(s.files[rel]), 0, s.p.id)
    m.save()
    s.compare(verify=True)
    check("verify: a ghost duplicate record is not recreated",
          not os.path.exists(s.full(ghost)) and len(s.device_files()) == 1,
          s.device_files())

    # Verify also finds and removes a real duplicate under Mirror.
    s = Scene()
    s.add(rel)
    s.sync()
    s.record_duplicate(rel, ghost)
    plan = s.compare(verify=True)
    check("verify: Verify content still plans the duplicate for deletion",
          any(a.kind == "delete" and a.dev == ghost for a in plan), rows(plan))
    s.sync()
    check("verify: the duplicate is gone after executing that plan",
          len(s.device_files()) == 1, s.device_files())

    # Audio-only Verify skips notes; clearing it indexes them.
    s = Scene(selection_mode="folders", music_folder="")
    s.add("Album/01.flac", select=False)
    s.sync()
    notes = os.path.join(s.dst, "Music", "Album", "notes.txt")
    write_bytes(notes, b"notes")
    s.compare(verify=True)
    check("verify: audio-only skips a non-audio device file",
          s.manifest().get("music/album/notes.txt") is None, s.manifest().files)
    s.p.audio_only = False
    s.compare(verify=True)
    check("verify: clearing audio-only indexes the non-audio file",
          s.manifest().get("music/album/notes.txt") is not None, s.manifest().files)

    # Stats count real reads.
    s = Scene(selection_mode="folders", music_folder="")
    s.add("Album/01.flac", select=False)
    s.sync()
    stats = {}
    s.compare(verify=True, stats=stats)
    check("verify: stats report the device file read",
          stats.get("device_files", 0) >= 1 and stats.get("device_read", 0) >= 1, stats)

    # Corrupt manifest is rebuilt from the exact read.
    s = Scene()
    s.add(rel)
    s.sync()
    write_bytes(s.manifest().path, b"[]")
    plan = s.compare(verify=True)
    check("verify: a corrupt manifest is rebuilt from device bytes",
          plan[0].kind == "equal" and plan[0].verified, rows(plan, True))

# ======================================================================
# 5. The reported failure: an edited album gained a second legacy path
# ======================================================================
def group_reported_bug():
    tracks = [
        "月詠み/月が満ちる/01 - 廻想.flac",
        "月詠み/月が満ちる/02 - 生きるよすが.flac",
        "月詠み/月が満ちる/03 - ヨダカ.flac",
        "月詠み/月が満ちる/04 - 醜悪.flac",
        "月詠み/月が満ちる/05 - 暮れに茜、芥と花束.flac",
        "月詠み/月が満ちる/06 - メデ.flac",
        "月詠み/月が満ちる/07 - アメイセンソウ.flac",
        "月詠み/月が満ちる/08 - 白夜.flac",
        "月詠み/月が満ちる/09 - 月が満ちる.flac",
    ]

    def album():
        s = Scene(target="Walkman_SD/Music", filesystem="exfat")
        for i, rel in enumerate(tracks):
            s.add(rel, data=(f"track-{i}-old".encode() * 100))
        s.sync()
        return s

    s = album()
    check("bug: the nine-track album first syncs exactly nine copies",
          len(s.device_files()) == len(tracks), s.device_files())
    check("bug: every canonical path is recorded once",
          len(s.manifest().files) == len(tracks), s.manifest().files)

    # Edit the local tags/content of every track, and leave the old wrong-target
    # copies on the device under the doubled Artists tree.
    for i, rel in enumerate(tracks):
        full = s.files[rel]
        write_bytes(full, f"track-{i}-new".encode() * 100)
        bump(full)
        s.record_duplicate(rel, "Artists/" + s.dev(rel))

    plan = s.compare()
    changed = [a for a in plan if a.kind == "changed"]
    deleted = [a for a in plan if a.kind == "delete"]
    check("bug: nine edited tracks are nine updates, not eighteen new copies",
          len(changed) == len(tracks), [(a.kind, a.dev) for a in plan])
    check("bug: the nine stale legacy paths are all planned for deletion",
          len(deleted) == len(tracks), [(a.kind, a.dev) for a in plan])
    s.sync()
    check("bug: after the sync the album has exactly nine files",
          len(s.device_files()) == len(tracks), s.device_files())
    check("bug: no device path contains the doubled Artists folder",
          not any(f.count("Artists/") > 1 for f in s.device_files()),
          s.device_files())
    check("bug: the manifest keeps exactly one path per track",
          len(s.manifest().files) == len(tracks), s.manifest().files)

    # The next compares stay quiet and cheap.
    b = s.backend()
    reads = []
    real_open = b.open_read
    b.open_read = lambda rel: (reads.append(rel), real_open(rel))[1]
    try:
        repeat = nebula.compare(s.p, b)
    finally:
        b.open_read = real_open
    check("bug: the cleaned album compares equal without reading device bytes",
          len(repeat) == len(tracks) and all(a.kind == "equal" for a in repeat)
          and reads == [], (reads, rows(repeat)))

    verify_plan = s.compare(verify=True)
    s.sync(verify=True)
    check("bug: Verify content does not resurrect a legacy path",
          len(s.device_files()) == len(tracks), s.device_files())
    check("bug: Verify content reports nine exact equals",
          len(verify_plan) == len(tracks) and all(a.verified for a in verify_plan),
          rows(verify_plan, True))

    # A wrong target that is a prefix of the correct one is the exact accident.
    s = Scene(target="Music/Artists")
    rel = "月詠み/月が満ちる/01 - 廻想.flac"
    s.add(rel)
    s.sync()
    old_dev = "Artists/" + s.dev(rel)
    old_full = s.full(old_dev)
    s.p.target = "Music"
    plan = s.compare()
    new_dev = s.dev(rel)
    check("bug: fixing a target suffix plans the canonical copy and the old copy",
          any(a.kind in ("new", "restore") and a.dev == new_dev for a in plan)
          and any(a.kind == "delete" and a.dev == old_dev for a in plan),
          [(a.kind, a.dev) for a in plan])
    s.sync()
    check("bug: fixing the target leaves one canonical copy only",
          s.has(rel) and not os.path.exists(old_full) and len(s.device_files()) == 1,
          s.device_files())

    # A wrong media folder produces the same doubled segment and is cleaned the same way.
    s = Scene(music_folder="Artists/Artists")
    s.add(rel)
    s.sync()
    old_dev = s.dev(rel)
    s.p.music_folder = "Artists"
    plan = s.compare()
    check("bug: correcting a doubled media folder deletes the old path",
          any(a.kind == "delete" and a.dev == old_dev for a in plan),
          [(a.kind, a.dev) for a in plan])
    s.sync()
    check("bug: the corrected media folder leaves one copy",
          len(s.device_files()) == 1 and s.has(rel), s.device_files())

    # Unrelated device files are not collateral damage.
    s = album()
    unrelated = os.path.join(s.dst, "Walkman_SD", "Music", "Keep", "notes.txt")
    write_bytes(unrelated, b"keep me")
    for rel in tracks:
        s.record_duplicate(rel, "Artists/" + s.dev(rel))
    s.sync()
    check("bug: cleaning the album leaves an unrelated target file alone",
          os.path.exists(unrelated) and len(s.device_files()) == len(tracks) + 1,
          s.device_files())

    # One duplicate only affects that one track.
    s = album()
    s.record_duplicate(tracks[4], "Artists/" + s.dev(tracks[4]))
    plan = s.compare()
    check("bug: a single legacy duplicate deletes only that track",
          len([a for a in plan if a.kind == "delete"]) == 1,
          [(a.kind, a.dev) for a in plan])
    s.sync()
    check("bug: the other eight tracks stay in place",
          len(s.device_files()) == len(tracks), s.device_files())

# ======================================================================
# 6. Folder mode and the bytes method still behave exactly as before
# ======================================================================
def group_folder_and_bytes():
    s = Scene(selection_mode="folders", music_folder="")
    s.add("Album/01.flac", select=False)
    plan = s.compare()
    check("folder: a first folder compare is new",
          rows(plan) == [("new", "Album/01.flac")], rows(plan))
    s.sync()
    check("folder: the folder sync writes the file",
          os.path.exists(os.path.join(s.dst, "Music", "Album", "01.flac")),
          s.device_files())
    check("folder: a repeat folder compare is equal",
          all(a.kind == "equal" for a in s.compare()), rows(s.compare(), True))

    # An unknown extra with a size no library file shares is deleted without a read.
    extra = os.path.join(s.dst, "Music", "Junk", "odd.flac")
    write_bytes(extra, b"x" * 999)
    plan = s.compare()
    check("folder: an unknown extra is deleted by Mirror",
          any(a.kind == "delete" and a.extra for a in plan), rows(plan))
    s.sync()
    check("folder: the extra is gone after the sync", not os.path.exists(extra))

    # A library copy under a hand-made name is adopted, not copied again.
    canonical = os.path.join(s.dst, "Music", "Album", "01.flac")
    loose = os.path.join(s.dst, "Music", "loose", "01-copy.flac")
    os.remove(canonical)
    write_bytes(loose, s.data("Album/01.flac"))
    plan = s.compare()
    adopted = next(a for a in plan if a.rel == "Album/01.flac")
    check("folder: a hand copy is adopted where it is",
          adopted.kind == "equal" and adopted.extra, rows(plan, True))
    s.sync()
    check("folder: adopting does not create a second canonical copy",
          os.path.exists(loose) and not os.path.exists(canonical), s.device_files())

    # Update reports an extra but leaves it alone.
    s.p.mode = "update"
    keep = os.path.join(s.dst, "Music", "Junk", "keep.flac")
    write_bytes(keep, b"keep")
    plan = s.compare()
    check("folder: Update leaves an unknown extra",
          not any(a.kind == "delete" for a in plan) and os.path.exists(keep), rows(plan))

    # Bytes method: a same-size device edit is caught by the byte comparison.
    s = Scene(method="bytes", music_folder="", selection_mode="folders")
    s.add("Album/01.flac", select=False)
    s.sync()
    check("bytes: a repeat compare is equal",
          all(a.kind == "equal" for a in s.compare()), rows(s.compare(), True))
    dev_full = s.full("Album/01.flac")
    edit_same_size(dev_full, 0x40)
    plan = s.compare()
    check("bytes: a same-size device edit is changed",
          rows(plan) == [("changed", "Album/01.flac")], rows(plan))
    s.sync()
    check("bytes: the changed copy is repaired",
          open(dev_full, "rb").read() == s.data("Album/01.flac"))

    # Bytes Mirror deletion and selected-item ownership.
    stray = os.path.join(s.dst, "Music", "Junk", "stray.flac")
    write_bytes(stray, b"stray")
    plan = s.compare()
    check("bytes: Mirror deletes an unknown extra",
          any(a.kind == "delete" for a in plan), rows(plan))
    s.sync()
    check("bytes: the extra is gone", not os.path.exists(stray))
    # Bytes selected-item ownership is a separate profile: folder mode always sends
    # everything in its source, so it has no selection to untick.
    s2 = Scene(method="bytes", music_folder="")
    s2.add("Album/01.flac")
    s2.sync()
    s2.select_only([])
    s2.p.mode = "update"
    check("bytes: Update keeps an unselected copy",
          not any(a.kind == "delete" for a in s2.compare()), rows(s2.compare()))
    s2.p.mode = "mirror"
    check("bytes: Mirror deletes an unselected copy",
          rows(s2.compare()) == [("delete", "Album/01.flac")], rows(s2.compare()))


# ======================================================================
# 7. Path-qualified identity: same bytes in two places are two files
# ======================================================================
def group_identity():
    s = Scene()
    s.add("Artist/One.flac", data=b"identical bytes")
    s.add("Artist/Two.flac", data=b"identical bytes")
    plan = s.compare()
    check("identity: identical content at two paths is two new files",
          len(plan) == 2 and all(a.kind == "new" for a in plan), rows(plan))
    s.sync()
    check("identity: both paths exist on the device",
          s.has("Artist/One.flac") and s.has("Artist/Two.flac"), s.device_files())
    check("identity: the manifest keeps both paths", len(s.manifest().files) == 2,
          s.manifest().files)
    edit_same_size(s.files["Artist/One.flac"], 0x08)
    bump(s.files["Artist/One.flac"])
    plan = s.compare()
    check("identity: changing one path changes only that path",
          rows(plan) == [("changed", "Artists/Artist/One.flac")], rows(plan))
    s.sync()
    s.select_only(["Artist/Two.flac"])
    plan = s.compare()
    check("identity: deleting one path leaves the identical other",
          rows(plan) == [("delete", "Artists/Artist/One.flac")]
          and s.has("Artist/Two.flac"), rows(plan))

    # Same basename in different folders is not a duplicate either.
    s = Scene()
    s.add("A/01.flac", data=b"same")
    s.add("B/01.flac", data=b"same")
    s.sync()
    check("identity: same basename in two folders stays two files",
          len([f for f in s.device_files() if f.endswith("/01.flac")]) == 2,
          s.device_files())


# ======================================================================
# 8. Stability across library sizes and mixed edits
# ======================================================================
def group_stability():
    for count in range(1, 11):
        s = Scene()
        for i in range(count):
            s.add(f"Artist/Album/{i + 1:02d}.flac")
        plan = s.compare()
        check(f"stability: {count} files plan new",
              len(plan) == count and all(a.kind == "new" for a in plan), rows(plan))
        s.sync()
        check(f"stability: {count} files land once",
              len(s.device_files()) == count, s.device_files())
        repeat = s.compare()
        check(f"stability: {count} files are equal on repeat",
              len(repeat) == count and all(a.kind == "equal" for a in repeat),
              rows(repeat, True))

    s = Scene()
    for i in range(6):
        s.add(f"Artist/Album/{i + 1:02d}.flac")
    s.sync()
    for i in (0, 2, 4):
        edit_same_size(s.files[f"Artist/Album/{i + 1:02d}.flac"], 0x04)
        bump(s.files[f"Artist/Album/{i + 1:02d}.flac"])
    plan = s.compare()
    check("stability: three of six edits are three changed actions",
          len([a for a in plan if a.kind == "changed"]) == 3, rows(plan))
    s.sync()
    check("stability: the mixed edit run leaves six files",
          len(s.device_files()) == 6, s.device_files())
    s.select_only([f"Artist/Album/{i:02d}.flac" for i in (1, 3, 6)])
    plan = s.compare()
    check("stability: unticking half plans three deletes",
          len([a for a in plan if a.kind == "delete"]) == 3, rows(plan))
    s.sync()
    check("stability: three files remain after the partial mirror",
          len(s.device_files()) == 3, s.device_files())

# === APPEND ===

def main():
    groups = [group_routing, group_device_names, group_lifecycle,
              group_manifest_states, group_verify, group_reported_bug,
              group_folder_and_bytes, group_identity, group_stability]
    for group in groups:
        try:
            group()
        except Exception:
            RESULTS.append((group.__name__, False, traceback.format_exc()))
            print("GROUP CRASH", group.__name__)
            traceback.print_exc()
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} scenarios passed")
    for name, _ok, detail in failed:
        print("  FAILED", name, detail)
    print(f"scratch home: {HOME}")
    sys.exit(1 if failed or len(RESULTS) < 200 else 0)


if __name__ == "__main__":
    main()
