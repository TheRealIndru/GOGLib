# GOGLib

Manifest-driven, cross-platform GOG library archival tool. Wraps an existing
GOG download backend (`lgogdownloader` on Linux/macOS, `gogrepoc` on Windows)
and adds the missing pieces for serious offline archiving:

- **Manifest tracks downloads independently of disk state** — back up your library to a NAS, delete the local copy, and `goglib sync` won't redownload anything.
- **Letter-by-letter batches** — `goglib sync --letter a` instead of "download all 4 TB at once". Pause and resume across sessions.
- **Franchise-based folder organization** — `Heroes_of_Might_and_Magic/1996_Heroes_2_-_Gold/` instead of a flat list of slugs.
- **Automatic version archiving** — when GOG patches a game, the old installer moves to `_versions/` instead of being overwritten.
- **OST format priority** — when an OST ships in FLAC + WAV + MP3, only fetch the FLAC.
- **Interactive language audit** — clean up unwanted-language extras safely (no false-positive auto-deletion).
- **Disaster recovery** — separate `goglib-rebuild-manifest` rebuilds the manifest from disk if you lose it.

GOGLib is a wrapper for download tools, not a downloader itself. You install one of the supported backends first; GOGLib invokes it.

## Status

Single-author tool, used in production by its author. Tested on Zorin OS 18 (Ubuntu Noble base) with a ~1100-game / 4+ TB library. Cross-platform paths are implemented and tested via CI on Ubuntu, macOS, and Windows runners. The `gogrepoc` backend (Windows) handles refresh/list/download but is less thoroughly battle-tested than the lgog backend; use a small library subset for first runs.

## Requirements

- Python 3.9 or newer
- A GOG download backend on your PATH:
  - **Linux/macOS:** [`lgogdownloader`](https://github.com/Sude-/lgogdownloader) (3.15 or newer recommended; older versions had a CDN-related crash)
  - **Windows:** [`gogrepoc`](https://github.com/Yepoleb/gogrepoc) (`pip install gogrepoc`)

## Install

```bash
git clone https://github.com/TheRealIndru/GOGLib.git
cd GOGLib
chmod +x goglib goglib-rebuild-manifest

# Either drop them on your PATH:
sudo ln -s "$PWD/goglib" /usr/local/bin/goglib
sudo ln -s "$PWD/goglib-rebuild-manifest" /usr/local/bin/goglib-rebuild-manifest

# Or just run them in place:
./goglib --help
```

On Windows, run via `python goglib` from PowerShell, or set up a `.cmd` shim. See [docs/INSTALL.md](docs/INSTALL.md) for per-OS details.

## Quick start

```bash
# 1. Authenticate the backend (one-time)
lgogdownloader --login    # Linux/macOS
# or:
gogrepoc login            # Windows

# 2. Initialize GOGLib's config and franchise file
goglib config --write-default

# 3. Refresh the library cache (slow first time — 20-40 min for 1000+ games)
goglib refresh

# 4. See what would be downloaded for, say, the numerics batch
goglib plan --letter num

# 5. Actually download
goglib sync --letter num

# 6. Move that batch off your SSD to your archive drive
rsync -av --remove-source-files ~/GOGLibrary/ /mnt/external/GOG/
find ~/GOGLibrary -type d -empty -delete

# 7. Continue with the next letter — manifest knows what's already done
goglib sync --letter a
goglib sync --letter b
# ... etc
```

## Subcommands

| Command | What it does |
|---|---|
| `refresh` | Refresh backend cache + dump library JSON. Slow; run weekly or after buying new games. |
| `plan [--letter X]` | Non-destructive preview of what would download. Always run before `sync` first time. |
| `sync [--letter X]` | Download new files and organize into the library tree. |
| `process [--letter X]` | Re-run post-processing on existing staging without re-downloading (recovery from interrupted sync). |
| `audit [--review-all]` | Interactively review extras matching language tokens (e.g. find `_german.zip` files when you only want English). |
| `reorganize [--dry-run]` | Move files to match the current franchise/naming config. Useful after editing `franchises.json`. |
| `forget --letter X` | Remove matching entries from manifest so next sync re-downloads them. |
| `status` | Manifest summary — file count, total size, by-letter histogram. |
| `config [--write-default]` | Show effective config or write defaults to `~/.config/goglib/config.json`. |

## File locations

| File | Linux/macOS | Windows |
|---|---|---|
| Config | `~/.config/goglib/config.json` | `%APPDATA%\goglib\config.json` |
| Franchises | `~/.config/goglib/franchises.json` | `%APPDATA%\goglib\franchises.json` |
| Manifest | `~/.local/share/goglib/manifest.json` | `%APPDATA%\goglib\manifest.json` |
| Library snapshot | `~/.local/share/goglib/library.json` | `%APPDATA%\goglib\library.json` |
| Sync log | `~/.local/share/goglib/sync.log` | `%APPDATA%\goglib\sync.log` |
| Library tree | `~/GOGLibrary/` | `~\Documents\GOGLibrary\` |
| Staging tree | `~/GOGStaging/` | `~\Documents\GOGStaging\` |

All paths can be overridden in config.

## How the manifest works

The manifest is the source of truth — disk state is never consulted for "should I download this?". Each successfully downloaded file gets an entry like:

```json
"7th_legion/setup_7th_legion_2.0.0.5.exe": {
  "slug": "7th_legion",
  "title": "7th Legion",
  "original_filename": "setup_7th_legion_2.0.0.5.exe",
  "renamed": "7th_legion_2.0.0.5.exe",
  "destination": "/home/indru/GOGLibrary/Standalone/7th_Legion/7th_legion_2.0.0.5.exe",
  "size": 267386880,
  "kind": "installers",
  "downloaded_at": "2026-04-27T15:42:18",
  "status": "downloaded"
}
```

When you run `sync`, GOGLib generates a backend blacklist from the manifest, so the backend won't re-fetch anything. **Move the file anywhere you want — the manifest doesn't care.** Lose the manifest, and `goglib-rebuild-manifest` can reconstruct it by scanning your library directories.

When GOG patches a game (new version → new filename), the new file isn't in your manifest, so it downloads. The old file's manifest entry stays. You now have both versions tracked. The old file lives wherever you moved it.

See [docs/USAGE.md](docs/USAGE.md) for more on the workflow, [docs/BACKUP.md](docs/BACKUP.md) for protecting your manifest.

## Franchise organization

`franchises.json` maps GOG slugs to franchise/year/title metadata. With it, files land in `<library>/<Franchise>/<year>_<title>/` instead of `<library>/Standalone/<title>/`.

```json
{
  "_comment": "Map slug -> {franchise, year, title}.",
  "heroes_of_might_and_magic_2_gold_edition": {
    "franchise": "Heroes of Might and Magic",
    "year": 1996,
    "title": "Heroes of Might and Magic 2 - Gold"
  }
}
```

A starter file for the 30 most common franchises is in [`examples/franchises-starter.json`](examples/franchises-starter.json). For most users, hand-curating this file pays off quickly. Without a franchise mapping, a game just lands in `Standalone/`.

After editing `franchises.json`, run `goglib reorganize --dry-run` to preview moves, then `goglib reorganize` to apply.

## Backend selection

GOGLib auto-picks a backend per OS, but you can force one in `config.json`:

```json
{ "backend": "lgogdownloader" }
```

Valid: `auto`, `lgogdownloader`, `gogrepoc`.

If you have lgogdownloader running under WSL on a Windows machine and prefer it over gogrepoc, set `"backend": "lgogdownloader"`.

## Disaster recovery

If you lose the manifest:

```bash
goglib-rebuild-manifest                # dry-run preview
goglib-rebuild-manifest --write        # actually rebuild
goglib status                          # verify
```

If something looks wrong, restore from the auto-backup (`manifest.json.before-rebuild-<timestamp>`).

## Limitations

- Cloud saves are not handled — GOGLib focuses on installers, patches, and extras.
- Galaxy-only DLC distribution (some recent titles) requires the backend's Galaxy support, which lgogdownloader has but is less polished.
- gogrepoc's JSON output may diverge from lgogdownloader's; the gogrepoc backend reshapes minimally but full feature parity isn't guaranteed.

## Contributing

Bug reports and PRs welcome. Run tests with:

```bash
pip install pytest
pytest tests/ -v
```

CI runs the full test matrix (Python 3.9-3.12 × Ubuntu/macOS/Windows) on every commit.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
