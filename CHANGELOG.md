# Changelog

All notable changes to GOGLib are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Cross-platform support: Linux/macOS via `lgogdownloader`, Windows via `gogrepoc`.
- Backend abstraction with auto-detection (override via `backend` config key).
- Per-OS default paths (XDG on Linux/macOS, `%APPDATA%` on Windows).
- GitHub Actions CI: syntax check + 98 unit tests on Python 3.9-3.12 × Ubuntu/macOS/Windows.
- Starter franchises file at `examples/franchises-starter.json` (~30 common franchises).
- Disaster-recovery tool `goglib-rebuild-manifest` for reconstructing the manifest from disk.

### Changed
- Letter-bucket filtering now uses display title with leading-article stripping
  (so "The Witcher" buckets under `w`, "A Plague Tale" under `p`).
- DLC files default to a flat `<base>/dlc/` directory with DLC slug prefixed
  to filenames (configurable via `flatten_dlc_folder`).
- OST format-priority blacklist (FLAC > WAV > MP3) applied at download time
  to save bandwidth, not just disk space.

### Fixed
- Blacklist patterns no longer use `^` anchor — lgogdownloader's path-matching
  semantics are unanchored regex_search; the leading anchor was breaking on
  some lgog versions that prefix paths with `/`.
- Blacklist now contains entire manifest regardless of current sync scope
  (previously scoped to current slugs only, which was correct but fragile).
- Filename detection in OST format-priority code: `path` field is the bare
  filename in lgog JSON, not a URL with slashes.

## [0.1.0] - Initial public release

First version published to GitHub. Core feature set: refresh, plan, sync,
process, audit, reorganize, forget, status, config subcommands.
