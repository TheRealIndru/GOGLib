# Using GOGLib

This guide walks through a typical archival workflow and the most common
day-to-day operations.

## Workflow: archiving a large library to external storage

The recommended pattern is **download to local SSD, archive to external
drive, free up the SSD, repeat per letter**.

```bash
# One-time setup
goglib config --write-default
goglib refresh                                    # 20-40 min for 1000+ games

# For each letter (or batch):
goglib plan --letter num                          # Preview
goglib sync --letter num                          # Download
rsync -av --remove-source-files ~/GOGLibrary/ /mnt/external/GOG/
find ~/GOGLibrary -type d -empty -delete

goglib sync --letter a
rsync -av --remove-source-files ~/GOGLibrary/ /mnt/external/GOG/
# ...

goglib status                                     # Track overall progress
```

Why letter-by-letter? Two reasons:

1. **You can pause anywhere.** Shut down between letters; come back tomorrow.
2. **The manifest doesn't care where files are.** After `rsync --remove-source-files`,
   the local `~/GOGLibrary/` is empty but the manifest still records every file.
   The next sync skips them.

## Workflow: filling in franchise mappings as you go

You don't have to map every game upfront. Sync some games to Standalone, then
fill in franchise mappings, then run `reorganize` to move them into franchise
folders.

```bash
# After syncing a batch
goglib status                                     # Note 'unmapped' count

# Find slugs you might want to map
python3 -c "
import json
with open('$HOME/.local/share/goglib/library.json') as f:
    for g in sorted(json.load(f), key=lambda x: x.get('gamename','')):
        if 'witcher' in g.get('gamename','').lower():
            print(f\"{g['gamename']:<55s}  {g.get('title','')}\")"

# Edit franchises.json to add mappings
$EDITOR ~/.config/goglib/franchises.json

# Preview what would move
goglib reorganize --dry-run

# Apply
goglib reorganize
```

## Workflow: handling game updates

When GOG ships a new version of a game you already have, the new file has a
different filename (version baked in). `goglib sync` will fetch it; the old
file's manifest entry stays. Both versions are now tracked.

In the rare case GOG keeps the same filename but ships different content,
goglib detects the destination collision and moves the old file to
`_versions/<slug>/<timestamp>/<filename>` before installing the new one.

To check if any games have updates available:

```bash
goglib refresh
goglib plan --letter all | grep -E "(NEW|PARTIAL)"
```

## Workflow: testing on a small subset

Before unleashing a full sync, test on the smallest segment:

```bash
goglib plan --letter num                          # Usually only a handful of games
goglib sync --letter num
ls ~/GOGLibrary/                                  # Verify structure
goglib status
```

Then sync that letter again — should show `Done. 0 added` (manifest blacklist
is working).

## Common operations

### Find what would download

```bash
goglib plan                                       # Everything
goglib plan --letter w                            # Just W games
goglib plan --game witcher                        # Anything with 'witcher' in slug
goglib plan --letter w --game ^the_witcher        # 'w' AND specific regex
```

### Force a re-download of something

The manifest is the source of truth. To force a re-download:

```bash
goglib forget --game ^heroes_of_might_and_magic_3 --yes
goglib sync --game ^heroes_of_might_and_magic_3
```

### Audit unwanted-language extras

GOG ships extras (manuals, soundtracks) without language metadata in the API,
so they can't be filtered at download time without false positives (Polish
"pol" filename suffix vs "Price of Loyalty" abbreviation, for example).
Instead, audit them interactively after download:

```bash
goglib audit
# Each match: [k]eep / [d]elete / [s]kip rest of game / [q]uit
```

Decisions are remembered (entries marked `audited: true` in the manifest).
Re-runs skip already-audited files unless you pass `--review-all`.

### Reorganize after editing franchises.json

```bash
$EDITOR ~/.config/goglib/franchises.json
goglib reorganize --dry-run                       # Preview
goglib reorganize                                 # Apply
```

This works even when files are spread across SSD + external drive — every
manifest entry has its current `destination` path stored.

### Recover from a corrupted/lost manifest

```bash
# Try restoring from snapshot first
ls ~/.local/share/goglib/manifest-snapshots/      # If you set up the cron job
cp ~/.local/share/goglib/manifest-snapshots/manifest-XXXXX.json \
   ~/.local/share/goglib/manifest.json

# Or reconstruct from disk
goglib-rebuild-manifest                           # Dry-run preview
goglib-rebuild-manifest --write                   # Actually write

# When scanning multiple drives:
goglib-rebuild-manifest --scan ~/GOGLibrary --scan /mnt/external/GOG --write
```

## Scheduled syncs

Once everything is set up, you can have GOGLib run periodically to pick up
new games and updates automatically.

### Linux/macOS: cron

```cron
# Refresh weekly, sync nightly
30 3 * * 0 flock -n /tmp/goglib-refresh.lock /usr/local/bin/goglib refresh   >> ~/.local/share/goglib/cron.log 2>&1
30 4 * * * flock -n /tmp/goglib-sync.lock    /usr/local/bin/goglib sync      >> ~/.local/share/goglib/cron.log 2>&1
```

### Windows: Task Scheduler

Open Task Scheduler → Create Basic Task. Set action to `python` with arguments
`C:\path\to\GOGLib\goglib refresh`. Repeat for `sync` with desired schedule.

For "windowless" execution (no console pop-up), use `pythonw.exe` instead of
`python.exe`.

## Tips

- **Run `plan` before `sync`.** Always. Preview is non-destructive.
- **Run `sync` twice on the same letter as a sanity check.** The second run should
  show `Total size: 0 B` and `Done. 0 added` — confirming the manifest works.
- **Back up the manifest.** See [BACKUP.md](BACKUP.md). Losing it doesn't lose
  your library, but it loses your "what's already done" state.
- **Don't move `_versions/`.** GOGLib uses this dir for version-archived files;
  moving it could cause future updates to overwrite instead of archive.
