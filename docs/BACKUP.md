# Backing up the manifest

Your manifest (`manifest.json`) is the most important file in your GOGLib
installation. Lose it and goglib won't know what's already downloaded —
the next sync would re-fetch everything.

The library files themselves are replaceable (re-download from GOG); the
manifest is your "what is downloaded and where" state.

## Layer 1: atomic writes (built-in)

GOGLib writes to `manifest.json.tmp` then atomically renames to
`manifest.json`. A crash mid-write leaves the previous version intact. No
configuration needed.

## Layer 2: rolling local snapshots (recommended)

A cron job that copies the manifest hourly to a timestamped file, keeping
14 days of history.

### Linux/macOS

```bash
mkdir -p ~/.local/share/goglib/manifest-snapshots

# Edit your crontab
crontab -e

# Add this line:
0 * * * * cp ~/.local/share/goglib/manifest.json ~/.local/share/goglib/manifest-snapshots/manifest-$(date +\%Y\%m\%d-\%H).json && find ~/.local/share/goglib/manifest-snapshots/ -name 'manifest-*.json' -mtime +14 -delete
```

Recovery:
```bash
ls ~/.local/share/goglib/manifest-snapshots/      # Find the right snapshot
cp ~/.local/share/goglib/manifest-snapshots/manifest-20260427-15.json \
   ~/.local/share/goglib/manifest.json
goglib status                                     # Verify
```

### Windows: Task Scheduler

Create a daily task running PowerShell:

```powershell
$src = "$env:APPDATA\goglib\manifest.json"
$dst = "$env:APPDATA\goglib\manifest-snapshots\manifest-$(Get-Date -Format 'yyyyMMdd-HH').json"
New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
Copy-Item $src $dst
# Cleanup older than 14 days
Get-ChildItem "$env:APPDATA\goglib\manifest-snapshots\manifest-*.json" `
    | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } `
    | Remove-Item
```

## Layer 3: off-machine backup (strongly recommended)

If your SSD fails, local snapshots fail with it. Sync to your NAS or external
drive on a schedule.

### Linux/macOS via cron + rsync

```bash
# Adjust /mnt/nas/... to match your actual NAS mount
15 * * * * rsync -a ~/.local/share/goglib/ /mnt/nas/goglib-backup/state/ && rsync -a ~/.config/goglib/ /mnt/nas/goglib-backup/config/
```

The 15-minute offset from the local snapshot job avoids them running at the
exact same time.

### Windows via Task Scheduler + robocopy

```powershell
robocopy $env:APPDATA\goglib \\NAS\goglib-backup\state /MIR /R:3 /W:5
```

### What to back up

The whole config + state directory is small (< 10 MB), so just back it all:

| File | Replaceable? |
|---|---|
| `manifest.json` | **No — irreplaceable** |
| `franchises.json` | **No — your hand-curated mapping** |
| `config.json` | Easy to recreate |
| `library.json` | Yes (regeneratable via `goglib refresh`, but takes 20-40 min) |
| `sync.log` | Historical only; nice to have |

Worth keeping daily snapshots of `library.json` too — that's your historical
record of what was once in your GOG library, useful if a game gets delisted
later.

## Layer 4: rebuild from disk (last-resort recovery)

If you lose everything — no snapshots, no NAS backup — `goglib-rebuild-manifest`
can reconstruct the manifest by scanning your library directories and matching
each file back to GOG metadata.

```bash
# Always dry-run first to see what would be matched
goglib-rebuild-manifest

# Scan multiple drives in one pass
goglib-rebuild-manifest --scan ~/GOGLibrary --scan /mnt/external/GOG-archive

# When you're satisfied with the dry-run output:
goglib-rebuild-manifest --write
```

Rebuilt entries get marked `"rebuilt": true` so you can tell which were
reconstructed vs original. Original-download timestamps are lost (mtime is
used instead), and audit decisions are gone (you'd be re-prompted on next
audit run). Files renamed manually outside goglib won't be matched.

For this reason, **rebuild is recovery, not a backup substitute.** Keep the
rolling snapshots.

## Recovery decision tree

```
Manifest seems wrong?
├── Was it just modified by goglib?
│   └── Restore from local snapshot (Layer 2)
├── Local snapshots also gone (whole SSD failed)?
│   └── Restore from NAS backup (Layer 3)
├── No off-machine backup either?
│   └── Rebuild from disk (Layer 4)
└── No disk either?
    └── Re-download everything from GOG (4+ days of bandwidth for full library)
```

The cost difference between layers 3 and 4 is one cron job. Set it up.
