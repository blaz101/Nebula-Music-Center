# Sync, part 1 — scan and reconcile the device

**Fast hash only.** This file started as an exact clone of the supplied part-1 tree.
The branches marked **[tested]** are the corrections found while running the 763
scenario suites in `tests/sync_hash_check.py` and `tests/sync_hash_matrix.py`.

## Final tree

```
  Sync ──> ┌────────────────────────────────────────────────┐   Step 1:
           │  Hash PC library (music & audiobooks)          │   Scan
           └─────────┬──────────────────────────────────────┘
                     │  cached by size + mtime, so only edited files re-hash
                     ▼
             ┌──────────────────────────────────────────────┐
             │  Work out the one canonical device path      │
             │  target / media folder / library-relative     │
             │  path, sanitised for the device filesystem    │
             └─────────┬────────────────────────────────────┘
                       │
                       ▼
       ┌────────────────────────────────────────────────────────┐
       │  Compare the device folder and file names with the     │
       │  sync manifest (one listing; no device reads yet)      │
       └───┬─────────────────────┬─────────────────────────┬────┘
           │                     │                         │
           ▼                     ▼                         ▼
   ┌───────────────┐     ┌───────────────┐         ┌───────────────┐
   │ missing file  │     │  extra file   │         │    is on      │
   └───────┬───────┘     └───────┬───────┘         │   manifest    │
           │                     │                 └───────┬───────┘
           ▼                     ▼                         │
   ┌───────────────┐     ┌───────────────┐                 ▼
   │ is it still   │     │ does this     │         ┌───────────────┐
   │ in the PC     │     │ profile own   │         │ canonical,    │
   │ library?      │     │ this record?  │         │ own record,   │
   └───┬───────┬───┘     └───┬───────┬───┘         │ hash+size,    │
       │       │             │       │             │ time unmoved? │
   YES │       │ NO      YES │       │ NO          └───┬───────┬───┘
       ▼       ▼             ▼       ▼                 │       │
   ┌───────┐ ┌───────┐   ┌───────┐ ┌───────┐       YES │       │ NO
   │compare│ │ignore │   │is it a│ │leave  │           ▼       ▼
   │hash   │ │it;    │   │second │ │it     │     ┌─────────┐ ┌─────────┐
   │with   │ │forget │   │path   │ │alone: │     │identical│ │read the │
   │record │ │record │   │for the│ │another│     │(no read)│ │device   │
   └───┬───┘ └───────┘   │same   │ │profile│     └─────────┘ │once;    │
       │                 │rel?   │ │or an  │                 │equal or │
       ▼                 └───┬───┘ │unknown│                 │changed  │
   ┌───────┐                 │     │file   │                 └─────────┘
   │same?  │             YES │     └───────┘
   └─┬───┬─┘                 ▼
  YES│   │NO          ┌───────────────┐
     ▼   ▼            │Mirror: delete │
 ┌──────┐┌──────────┐ │the duplicate  │
 │restore││note it is│ │Update: leave  │
 │to the││changed;  │ └───────────────┘
 │device││step 2    │
 └──────┘│copies the│
         │new bytes │
         └────┬─────┘
              ▼
         ┌─────────┐
         │ update  │
         │ sync    │
         │ manifest│
         └─────────┘
```

## The rules behind the branches

1. **One canonical path per selected file.** The path is
   `target / media-folder / library-relative-path`, run through the device's
   filename rules. Device names are case-insensitive, so a collision gets a stable
   ` (2)` suffix. The manifest is keyed by that target-relative path. The path is
   part of a file's identity: the same bytes at another path are a duplicate, not an
   equal copy.
2. **A missing manifest file is restored only when the PC file still has the
   recorded content.** If the PC file changed, step 2 sends the new bytes. If the
   file left the selection, the record is forgotten and nothing is restored.
3. **A missing manifest entry can still be restored from the hash store.** The hash
   store records `synced_hash` and `dev` only after a successful transfer, so a lost
   manifest does not turn a previously synced file into a fresh copy.
4. **`is on manifest` is trusted only when all of the evidence agrees:** same
   profile, same source rel, same content hash, same device size, and no device
   timestamp move. A moved timestamp is a hint to read the device once; it is never
   proof that the content changed.
5. **Non-canonical paths are duplicates for a still-selected file.** This is the
   tested fix for the reported album. An old target, a wrong media folder, or a former
   filesystem name can leave records for the same source at another device path.
   Mirror deletes those copies; Update keeps them but never restores them.
6. **Only the current target is touched.** A record under an older target folder is
   not deleted from the device and is never used to classify the current path.
   Records outside the current target stay in the manifest so switching the target
   back remains cheap.
7. **Selected mode never deletes files it cannot prove it owns.** A file with no
   record from this profile is left alone, even in Mirror. Folder mode may examine
   extras because the folder itself is the profile's claim; its quick scan hashes an
   extra only when a library file shares its size, and adopts a hand-made copy when
   the content matches instead of copying the same bytes again.
8. **Fast means no device reads for the ordinary path.** A trusted manifest compare
   opens no device file. Device bytes are read only for a missing/foreign record, a
   moved timestamp, a stale size, or an explicit Verify content pass.

## Corrections found by the scenario suite

| # | Correction | Scenario evidence |
|---|------------|-------------------|
| 1 | A second recorded path for a selected rel is a duplicate, not a valid copy. | `duplicate: a second recorded path is removed by Mirror` |
| 2 | The post-sync verifier restores only the canonical path; it cannot resurrect `Artists/Artists/...`. | `bug: Verify content does not resurrect a legacy path` |
| 3 | Fixing a target that is a prefix of the correct one (`Music/Artists` → `Music`) cleans the old copies inside the new target. | `bug: fixing a target suffix plans the canonical copy and the old copy` |
| 4 | Fixing a doubled media folder (`Artists/Artists` → `Artists`) has the same cleanup. | `bug: correcting a doubled media folder deletes the old path` |
| 5 | A lost manifest can fall back to the hash store for a restore. | `manifest: a lost manifest still restores from the hash store` |
| 6 | Verify content re-hashes the PC copy too, so a restored timestamp cannot hide an edit. | `verify: Verify content bypasses the PC hash cache` |
| 7 | A folder-mode adopted copy stays adopted; the verifier does not add a canonical second copy beside it. | `folder: adopting does not create a second canonical copy` |
| 8 | Update keeps duplicates but never presents them as restored/equal live paths. | `duplicate: Update keeps the extra path` |

The full run is `263/263` focused scenarios plus `500/500` seeded matrix
scenarios: **763/763 passed**.
