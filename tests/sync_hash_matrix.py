#!/usr/bin/env python3
"""500 seeded end-to-end hash-sync matrix scenarios.

Run:  QT_QPA_PLATFORM=offscreen python3 -u tests/sync_hash_matrix.py

This is deliberately separate from tests/sync_hash_check.py. Each seed builds a fresh
library and device, performs a first sync, then applies a random but reproducible mix
of edits, removals, legacy duplicate records, ghost records, missing canonical copies,
manifest tampering, unknown extras, another profile's file and an old-target record.
It runs Mirror or Update, optionally Verify content, and checks the resulting device
tree, manifest ownership and a clean second compare.
"""
import os
import random
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import sync_hash_check as base  # sets the throw-away HOME and NEBULA_* roots
import nebula  # noqa: E402


def run_seed(seed):
    rng = random.Random(seed)
    count = rng.randint(1, 4)
    target = rng.choice(["Music", "Walkman_SD/Music", "Music/Artists", "", "Nested/Target"])
    folder = rng.choice(["Artists", "", "Music/Artists"])
    filesystem = rng.choice(["mtp", "exfat", "fat32"])
    s = base.Scene(target=target, music_folder=folder, filesystem=filesystem)
    tracks = []
    for i in range(count):
        rel = f"Artist {seed}/Album {seed}/{i + 1:02d} - Track.flac"
        s.add(rel, data=(f"old-{seed}-{i}-".encode() * 20))
        tracks.append(rel)
    s.sync()
    devs = {rel: s.dev(rel) for rel in tracks}
    fulls = {rel: s.full(devs[rel]) for rel in tracks}
    routes = {rel: s.route_key(rel) for rel in tracks}
    problems = []

    def require(condition, message):
        if not condition:
            problems.append(message)

    for rel in tracks:
        require(os.path.exists(fulls[rel]), f"initial copy missing: {rel}")
        require(open(fulls[rel], "rb").read() == s.data(rel),
                f"initial bytes differ: {rel}")

    order = tracks[:]
    rng.shuffle(order)
    removed = set(order[:rng.randint(0, count)])
    remaining = [rel for rel in tracks if rel not in removed]
    changed = set(rng.sample(remaining, rng.randint(0, len(remaining))))
    for rel in changed:
        if rng.random() < 0.5:
            payload = (f"new-{seed}-{tracks.index(rel)}-".encode() * 20)
        else:
            payload = s.data(rel) + b"-extra"
        base.write_bytes(s.files[rel], payload)
        base.bump(s.files[rel])

    for rel in removed:
        path = s.files.pop(rel)
        os.remove(path)
        s.selected.discard(rel)
        s.p.selection = [entry for entry in s.p.selection if entry["path"] != path]
    assert set(remaining) == set(s.selected)

    # A second recorded device path for a still-selected file: the reported bug.
    duplicates = {}
    for i, rel in enumerate(rng.sample(remaining, rng.randint(0, min(2, len(remaining))))):
        dev = f"Legacy Extra {seed}/{i + 1:02d} - Duplicate.flac"
        s.record_duplicate(rel, dev)
        duplicates[rel] = dev

    # A manifest record whose device file does not exist at all.
    ghosts = {}
    for i, rel in enumerate(rng.sample(remaining, rng.randint(0, min(1, len(remaining))))):
        dev = f"Legacy Ghost {seed}/{i + 1:02d} - Missing.flac"
        manifest = s.manifest()
        manifest.record(s.prefix + dev, s.route_key(rel),
                        os.path.getsize(s.files[rel]),
                        nebula.file_hash256(s.files[rel]), 0, s.p.id)
        manifest.save()
        ghosts[rel] = dev

    missing = set(rng.sample(remaining, rng.randint(0, len(remaining))))
    for rel in missing:
        os.remove(fulls[rel])

    # Files this profile does not own must survive every run.
    unknown = f"Keep/Unknown {seed}.flac"
    unknown_full = s.full(unknown)
    base.write_bytes(unknown_full, b"unknown-" + str(seed).encode())
    other = f"Other Profile {seed}.flac"
    other_full = s.full(other)
    base.write_bytes(other_full, b"other-" + str(seed).encode())
    manifest = s.manifest()
    manifest.record(s.prefix + other, "Other/File.flac", len(b"other"), "0" * 64, 0,
                    "other-profile")
    old_full = None
    if s.p.target.strip("/") and remaining:
        # A record under a previous target, deliberately outside the current prefix.
        old_full = os.path.join(s.dst, f"OldTarget {seed}", "Old.flac")
        base.write_bytes(old_full, b"old-target-" + str(seed).encode())
        manifest.record(f"OldTarget {seed}/Old.flac", s.route_key(remaining[0]),
                        1, "0" * 64, 0, s.p.id)
    manifest.save()

    # One manifest inconsistency, so the compare cannot only take the trusted path.
    tamper = rng.choice(["none", "forget", "wrong_hash", "wrong_rel"])
    if remaining and tamper != "none":
        rel = rng.choice(remaining)
        rec = manifest.get(s.prefix + devs[rel])
        if rec is not None:
            if tamper == "forget":
                manifest.forget(s.prefix + devs[rel])
            elif tamper == "wrong_hash":
                rec["hash"] = "0" * 64
            else:
                rec["rel"] = "Wrong/Elsewhere.flac"
            manifest.save()

    mode = rng.choice(["mirror", "update"])
    verify = rng.random() < 0.35
    s.p.mode = mode
    plan = s.compare(verify=verify)
    errors = nebula.execute(s.p, s.backend(), plan)
    require(errors == 0, f"sync errors: {errors}")
    by_rel = {}
    for action in plan:
        by_rel.setdefault(action.rel, []).append(action)

    # Every selected file is at its canonical path with the current PC bytes.
    for rel in remaining:
        require(os.path.exists(fulls[rel]), f"canonical missing after sync: {rel}")
        if os.path.exists(fulls[rel]):
            require(open(fulls[rel], "rb").read() == s.data(rel),
                    f"canonical bytes differ after sync: {rel}")
        require(any(a.kind in ("new", "restore", "changed", "equal")
                    for a in by_rel.get(s.route_key(rel), ())),
                f"no action for selected rel: {rel}")
        if rel in changed:
            require(any(a.kind in ("changed", "restore")
                        for a in by_rel.get(s.route_key(rel), ())),
                    f"edited file was not updated: {rel}")

    # Removed files obey the mode.
    for rel in removed:
        if mode == "mirror":
            require(not os.path.exists(fulls[rel]), f"removed file still present: {rel}")
            require(any(a.kind == "delete" and (a.dev or a.rel) == devs[rel]
                        for a in plan), f"removed file was not deleted: {rel}")
        else:
            require(os.path.exists(fulls[rel]), f"Update removed a file: {rel}")
            require(not any(a.kind == "delete" and (a.dev or a.rel) == devs[rel]
                            for a in plan), f"Update planned a delete: {rel}")

    # Duplicate paths: Mirror removes every one, Update keeps them.
    for rel, dev in duplicates.items():
        require(any(a.kind == "delete" and a.dev == dev for a in plan) == (mode == "mirror"),
                f"duplicate delete mismatch for {rel}: {mode}")
        require(os.path.exists(s.full(dev)) == (mode == "update"),
                f"duplicate file mismatch for {rel}: {mode}")

    # Ghost records are forgotten; they never become files.
    for rel, dev in ghosts.items():
        require(not os.path.exists(s.full(dev)), f"ghost became a file: {dev}")
        require(s.manifest().get(s.prefix + dev) is None,
                f"ghost record survived: {dev}")

    # Unowned files stay.
    require(os.path.exists(unknown_full), "unknown extra was removed")
    require(os.path.exists(other_full), "other profile's file was removed")
    if old_full is not None:
        require(os.path.exists(old_full), "old-target file was removed")

    # In Mirror, the manifest has exactly one owned record per selected rel, at the
    # canonical path. Update may keep extra records but must keep the canonical one.
    final_manifest = s.manifest()
    for rel in remaining:
        owned = [rec for rec in final_manifest.files.values()
                 if rec.get("profile") == s.p.id and rec.get("rel") == routes[rel]
                 and str(rec.get("dev") or "").lower()
                 .startswith(s.prefix.lower())]
        canonical = [rec for rec in owned
                     if str(rec.get("dev")).lower()
                     == (s.prefix + devs[rel]).lower()]
        require(bool(canonical), f"canonical manifest record missing: {rel}")
        if mode == "mirror":
            require(len(owned) == 1,
                    f"Mirror left {len(owned)} manifest paths for {rel}: "
                    f"{[rec.get('dev') for rec in owned]}")
    for rel in removed:
        if mode == "update":
            require(any(rec.get("rel") == routes[rel]
                        for rec in final_manifest.files.values()),
                    f"Update forgot a kept removed file: {rel}")

    # The next compare is clean: every selected file equal, no deletes.
    repeat = s.compare()
    for rel in remaining:
        actions = [a for a in repeat if a.rel == s.route_key(rel)]
        require(len(actions) == 1 and actions[0].kind == "equal",
                f"repeat not equal for {rel}: {[(a.kind, a.rel) for a in actions]}")
    require(not any(a.kind == "delete" for a in repeat),
            f"repeat planned deletes: {[(a.kind, a.rel) for a in repeat]}")

    return problems


def main():
    results = []
    for seed in range(500):
        try:
            problems = run_seed(seed)
        except Exception:
            problems = [traceback.format_exc(limit=4)]
        results.append((seed, problems))
        if problems:
            print(f"  FAIL  matrix[{seed}]  {problems[0]}")
    failed = [(seed, problems) for seed, problems in results if problems]
    print(f"\n{len(results) - len(failed)}/{len(results)} matrix scenarios passed")
    for seed, problems in failed:
        print(f"  seed {seed}:")
        for problem in problems:
            print(f"    {problem}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
