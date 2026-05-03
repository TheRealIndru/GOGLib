# Installing GOGLib

GOGLib has two parts: the GOGLib scripts themselves, and a download backend that
GOGLib drives. You install both.

## Linux

### Backend: lgogdownloader

Most Linux distros package an older version of lgogdownloader that has a known
crash when fetching some games (string-handling bug around GOG's CDN URLs,
fixed in v3.15). If your distro ships v3.12 or earlier, build from source:

```bash
sudo apt install -y build-essential cmake ninja-build pkg-config \
    libcurl4-openssl-dev libboost-regex-dev libboost-system-dev \
    libboost-filesystem-dev libboost-program-options-dev \
    libboost-date-time-dev libboost-iostreams-dev \
    libjsoncpp-dev librhash-dev libtinyxml2-dev libtidy-dev \
    libhtmlcxx-dev zlib1g-dev git

git clone https://github.com/Sude-/lgogdownloader.git
cd lgogdownloader
cmake -B build -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_BUILD_TYPE=Release \
    -DUSE_QT_GUI=OFF -GNinja
ninja -C build
sudo ninja -C build install

# Verify the version
hash -r
lgogdownloader --version    # should be 3.15+
```

Then authenticate:
```bash
lgogdownloader --login
```

### GOGLib

```bash
git clone https://github.com/TheRealIndru/GOGLib.git
cd GOGLib
chmod +x goglib goglib-rebuild-manifest

# Symlink onto your PATH
sudo ln -s "$PWD/goglib" /usr/local/bin/goglib
sudo ln -s "$PWD/goglib-rebuild-manifest" /usr/local/bin/goglib-rebuild-manifest

goglib --help
goglib config --write-default
```

## macOS

### Backend: lgogdownloader via Homebrew

```bash
brew install lgogdownloader
lgogdownloader --version
lgogdownloader --login
```

If Homebrew lags upstream and you hit the CDN crash, build from source as on
Linux (the CMake instructions above work, with macOS Boost installed via
`brew install boost cmake ninja jsoncpp tinyxml2 librhash htmlcxx tidy-html5`).

### GOGLib

Same as Linux. Drop `goglib` and `goglib-rebuild-manifest` somewhere on `$PATH`
(`/usr/local/bin/` or `~/bin/`).

## Windows

### Backend: gogrepoc

```powershell
# Install Python 3.9+ from python.org or the Microsoft Store
python --version

# Install gogrepoc
pip install gogrepoc

# Authenticate
gogrepoc login
```

Follow the browser-based GOG login flow.

### GOGLib

```powershell
# Clone the repo
git clone https://github.com/TheRealIndru/GOGLib.git
cd GOGLib

# Run via Python (Windows doesn't honour the shebang line)
python goglib --help
python goglib config --write-default
```

For convenience, create `goglib.cmd` somewhere on your `%PATH%`:

```cmd
@echo off
python "C:\path\to\GOGLib\goglib" %*
```

Then `goglib --help` works directly.

### Backend selection on Windows

GOGLib auto-picks `gogrepoc` on Windows. If you have lgogdownloader running
under WSL and prefer it (more battle-tested), set the backend explicitly in
`%APPDATA%\goglib\config.json`:

```json
{ "backend": "lgogdownloader" }
```

Then run goglib from inside WSL. The Windows-side `gogrepoc` and
WSL-side `lgogdownloader` are separate authentications; you'll log in once
per backend.

## Verifying the install

```bash
goglib config                       # Should print the effective config
goglib --help                       # Should list all subcommands
lgogdownloader --version            # (Linux/macOS) Should be 3.15+
gogrepoc --version                  # (Windows) Should print a version
```

If any of these fail, the corresponding tool isn't on your PATH.

## Upgrading

GOGLib is just two scripts in a Git repo, so:

```bash
cd /path/to/GOGLib
git pull
```

The manifest format is forward-compatible across goglib versions — your
existing manifest will continue to work after upgrading.
