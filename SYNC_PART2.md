# Sync, part 2 — reconcile the library with the manifest

**Fast hash only.** This file started as an exact clone of the supplied part-2 tree.
The branches marked **[tested]** are the corrections found while running the 763
scenario suites in `tests/sync_hash_check.py` and `tests/sync_hash_matrix.py`.

## Final tree

```
  Step 2:
  comparison    ┌─────────────────────────────────────────────┐
                │  Compare the newly updated sync manifest    │
                │  to the PC library                          │
                └──────┬───────────────────┬─────────────┬────┘
                       │                   │             │
                       ▼                   ▼             ▼
         ┌──────────────────────┐ ┌─────────────────┐ ┌─────────────────┐
         │ extra file in library│ │ removed file    │ │ both are equal  │
         └──────────┬───────────┘ │ from library    │ └────────┬────────┘
                    │             └────────┬────────┘          │
                    │                      │                   │
                    ▼                      ▼                   │
         ┌──────────────────────┐ ┌─────────────────┐          │
         │ add to the device at │ │ Mirror: delete  │          │
         │ its canonical path   │ │ from device     │          │
         │ (new/changed)        │ │ Update: keep    │          │
         └──────────┬───────────┘ └────────┬────────┘          │
                    │                      │                   │
                    │                      │                   │
                    |                      |                   |
                    |                      ▼                   |
                    |---------------> ┌─────────┐ <------------|
                                      │  done   │
                                      └─────────┘

  Before "done", the manifest also answers:
    canonical file missing + own record      -> restore (copy from PC)
    canonical file present + record agrees   -> equal (no device read)
    canonical file present + record differs  -> changed (copy from PC)
    extra recorded path for a selected rel   -> Mirror delete (duplicate)
    extra recorded path under another target -> leave alone
```

## Path-qualified identity

The target-relative path is the identity key, not a free-floating content hash.

Example:

- PC: `/home/rba/Music/Artists/Daft Punk/Discovery/01 - One More Time.m4a`
- target folder: `Music`
- device: `/storage/Walkman_SD/Music/Artists/Daft Punk/Discovery/01 - One More Time.m4a`
- manifest key: `Artists/Daft Punk/Discovery/01 - One More Time.m4a`
- the record lists `dev` as `Walkman_SD/Music/Artists/...`, `rel` as the key above,
  the source size, and the SHA-256 of the bytes that were copied.

That means:

1. A matching SHA-256 at a different device path is **not** an equal copy. It is a
   duplicate or a copy of the same source under an old path, and Mirror removes it.
2. Two PC files with identical bytes but different paths are two separate records
   and two separate device files.
3. The hash store is keyed by the routed source rel and remembers what this profile
   last wrote (`synced_hash`, `dev`). The manifest is keyed by the full device path
   and remembers the transfer. Both are needed for a safe restore after a lost file.
4. Changing only a tag that does not change the PC path changes the contents, so the
   action is `changed` at the same canonical path — never a second copy. A rename or
   an organized path is `new` plus `delete` under Mirror.

## What changed after testing

- **Canonical-only verification.** After a sync, the verifier checks one canonical
  path for each selected file. It no longer walks every manifest record and copies
  whatever it names, which is what recreated the doubled `Artists` tree.
- **Duplicate cleanup in step 1.** A still-selected file can have only one live
  device path. Every other recorded path for the same source is planned as a delete
  under Mirror and left alone under Update.
- **Old target scope.** A record outside the current target is not used for equality
  and is not deleted. A record inside the current target but at a non-canonical path
  is a duplicate and is cleaned up.
- **No adoption in selected mode.** A non-canonical copy is never accepted as the
  canonical copy. The canonical path is restored or copied, then the duplicate is
  removed.
- **Folder-mode adoption is preserved.** If a folder-mode copy was adopted under a
  hand-made name, the verifier sees that a live recorded copy exists and does not add
  a canonical second copy beside it.
- **Verify content is exact on both sides.** It forces a fresh PC hash as well as a
  fresh device read, so a same-size edit with its timestamp restored cannot hide
  behind the hash cache.
- **Write then delete.** A plan copies/restores the canonical file before removing
  duplicate or stale paths, so an interrupted run leaves the source copy available
  for the next restore.

The full run is `263/263` focused scenarios plus `500/500` seeded matrix
scenarios: **763/763 passed**.
