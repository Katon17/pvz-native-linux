# Building from Source

A complete guide to rebuilding the **launcher package** and the **engine** from
scratch.

> **Bahasa Indonesia**: lihat [BUILDING.id.md](BUILDING.id.md)

> **For regular users:** you do not need this document. Just run
> `sudo apt install ./pvz-native_*_amd64.deb`.

---

## 1. Building just the launcher package

This is the fastest route. Takes ~10 seconds and does not compile the engine.

```bash
git clone https://github.com/Katon17/pvz-native-linux.git
cd pvz-native-linux

# Requires an engine binary at lib/pvz-native/engine/pvz-portable
chmod +x build-deb.sh
./build-deb.sh
```

Output in `release/`:

```
pvz-native_0.5.2_amd64.deb
pvz-native_0.5.2_amd64.deb.sha256
pvz-native-0.5.2-x86_64.tar.gz
pvz-native-0.5.2-x86_64.tar.gz.sha256
```

### If the engine is not there yet

```bash
./build-deb.sh --fetch-engine
```

This downloads the official PvZ-Portable release and verifies it against the
`ENGINE_SHA256` pinned in the script. See §3.7.

### Options

| Flag | Effect |
|---|---|
| `--fetch-engine` | Download the upstream engine if missing |
| `--engine PATH` | Use an engine binary you built yourself |
| `--version X.Y.Z` | Override the version from the `VERSION` file |
| `--out DIR` | Write artifacts somewhere other than `release/` |

---

## 2. Build dependencies

```bash
sudo apt update
sudo apt install -y \
    build-essential cmake ninja-build git \
    dpkg-dev curl cabextract \
    python3 python3-gi gir1.2-gtk-3.0 \
    libopenmpt-dev libmpg123-dev libvorbis-dev libogg-dev zlib1g-dev \
    libgl1-mesa-dev libx11-dev libxext-dev libxrandr-dev libxi-dev \
    libxcursor-dev libxfixes-dev libxss-dev libwayland-dev \
    libxkbcommon-dev libegl1-mesa-dev libgles2-mesa-dev
```

Disk space needed: **~2 GB** (source + engine build).

---

## 3. Building the engine (PvZ-Portable + patch)

This is the slow part: **~25–40 minutes** on 2 cores. Only needed if you modify
engine code — see §3.7 for the route the official release uses.

### 3.1 Fetch the source

```bash
cd ~
git clone https://github.com/wszqkzqk/PvZ-Portable.git pvz-src
cd pvz-src
```

### 3.2 Apply this project's patch

```bash
git apply --stat  ~/pvz-native-linux/patches/widescreen.patch   # inspect first
git apply --check ~/pvz-native-linux/patches/widescreen.patch   # dry run
git apply         ~/pvz-native-linux/patches/widescreen.patch
```

### 3.3 SDL3 (static)

```bash
cd ~
git clone --depth 1 --branch release-3.4.20 https://github.com/libsdl-org/SDL.git SDL-src
cmake -S SDL-src -B SDL-src/build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=$HOME/sysroot \
    -DSDL_SHARED=OFF -DSDL_STATIC=ON \
    -DSDL_TESTS=OFF -DSDL_EXAMPLES=OFF \
    -DSDL_X11_XTEST=OFF
cmake --build SDL-src/build -j1
cmake --install SDL-src/build
```

> `-DSDL_X11_XTEST=OFF` is required: without it the build fails in an
> environment lacking the XTest headers.

### 3.4 SDL3_mixer (static)

Every 3.2.x tag requires SDL3 ≥ 3.4.0 — that is why the SDL version above
matters.

```bash
git clone --depth 1 https://github.com/libsdl-org/SDL_mixer.git sdl3-mixer-src
cmake -S sdl3-mixer-src -B sdl3-mixer-src/build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=$HOME/sysroot \
    -DCMAKE_PREFIX_PATH=$HOME/sysroot \
    -DBUILD_SHARED_LIBS=OFF \
    -DSDLMIXER_TESTS=OFF -DSDLMIXER_EXAMPLES=OFF
cmake --build sdl3-mixer-src/build -j1
cmake --install sdl3-mixer-src/build
```

### 3.5 `MPG123::mpg123` shim

Upstream CMake looks for an `MPG123::mpg123` target that Debian does not export.
Create `/tmp/mpg123_fix.cmake`:

```cmake
if(NOT TARGET MPG123::mpg123)
  add_library(MPG123::mpg123 SHARED IMPORTED)
  set_target_properties(MPG123::mpg123 PROPERTIES
    IMPORTED_LOCATION "/usr/lib/x86_64-linux-gnu/libmpg123.so"
    INTERFACE_INCLUDE_DIRECTORIES "/usr/include")
endif()
```

### 3.6 Compile the engine

```bash
cd ~/pvz-src
cmake -S . -B build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$HOME/sysroot;/usr" \
    -DCMAKE_PROJECT_INCLUDE=/tmp/mpg123_fix.cmake \
    -DBUILD_STATIC=ON \
    -DDO_FIX_BUGS=ON \
    -DOPENMPT_LIBRARY=/usr/lib/x86_64-linux-gnu/libopenmpt.so \
    -DOPENMPT_INCLUDE_DIR=/usr/include
cmake --build build -j1          # -j1 matters: keeps RAM use at ~1 GB/core
strip -o /tmp/pvz-portable build/pvz-portable
```

### 3.7 Install into the repo & update the checksum

There are two routes. **Route A** is what the official release uses; **route B**
only applies if you deliberately changed engine code.

#### Route A — upstream release engine (used by official releases)

No compilation at all. `build-deb.sh --fetch-engine` downloads the official
artifact and verifies the checksum pinned in the script:

```bash
cd ~/pvz-native-linux
./build-deb.sh --fetch-engine
```

Current pins (updated 2026-11-14):

```
ENGINE_VERSION = 0.2.7
ENGINE_ASSET   = pvz-portable-linux-static-x86_64
ENGINE_SHA256  = add5bc1b68d6c2a7deba6e8195a1c55c342d6d5ef4bf13af99751b8ed65aa8d9
```

Verify manually at any time:

```bash
curl -sL https://github.com/wszqkzqk/PvZ-Portable/releases/download/0.2.7/pvz-portable-linux-static-x86_64 \
  | sha256sum
```

> **Important:** widescreen is **not** produced by patching the binary. The
> launcher writes the value into `registry.regemu` before starting the engine
> (see `tools/pvznative/display.py`). That is why the engine can be the stock
> upstream artifact — and why anyone can audit its checksum.

#### Route B — engine built by yourself

If you modified the engine, the upstream checksum no longer applies:

```bash
cp /tmp/pvz-portable ~/pvz-native-linux/lib/pvz-native/engine/pvz-portable
chmod +x ~/pvz-native-linux/lib/pvz-native/engine/pvz-portable

SHA=$(sha256sum /tmp/pvz-portable | awk '{print $1}')
cd ~/pvz-native-linux
sed -i "s/^ENGINE_SHA256=.*/ENGINE_SHA256=\"$SHA\"/" build-deb.sh
git diff build-deb.sh     # make sure only the checksum line changed
```

The consequence: `--fetch-engine` will **reject** that binary (checksum
mismatch), and users can no longer match the binary against an upstream release.
For local builds it is cleaner to use
`./build-deb.sh --engine /path/to/pvz-portable` without touching
`ENGINE_SHA256`.

**Never** swap the binary without updating the checksum in the same commit.
That check is the only safety net against an unknown binary.

---

## 4. Verifying the build

```bash
# 1. Test suite
python3 -m unittest discover -s tests -t tests

# 2. Package produced and checksum matches
cd release && sha256sum -c ./*.sha256

# 3. No game assets leaked into the package
dpkg-deb -c pvz-native_*.deb | grep -iE 'main\.pak|LawnStrings|properties/' \
  && echo "FAIL: game assets present!" || echo "OK: clean"

# 4. Binary in the package = the expected binary
rm -rf /tmp/v && mkdir /tmp/v && dpkg-deb -x pvz-native_*.deb /tmp/v
sha256sum /tmp/v/usr/lib/pvz-native/engine/pvz-portable
grep ENGINE_SHA256 ../build-deb.sh     # must match

# 5. Smoke test without a GUI
XDG_DATA_HOME=/tmp/xdg /tmp/v/usr/bin/pvz-native --where
XDG_DATA_HOME=/tmp/xdg /tmp/v/usr/bin/pvz-native --doctor || true
```

---

## 5. Running the tests

```bash
python3 -m unittest discover -s tests -t tests -v
```

68 tests, no real game assets required — ISOs and CABs are synthesised inside
the tests. Safe to run on public CI.

| File | Coverage |
|---|---|
| `test_assets.py` | ISO/ZIP/folder detection, file selection |
| `test_installer.py` | CAB payload extraction from `.exe` |
| `test_display.py` | Reading/writing `registry.regemu` |
| `test_settings_gui.py` | Widescreen preference |
| `test_about.py` | About dialog, donation links, version |

---

## 6. CI/CD

`.github/workflows/build.yml` runs three stages:

1. **test** — Python 3.10 / 3.12 / 3.13 matrix, shell syntax check.
2. **package** — builds the `.deb`, verifies checksums, ensures **no game
   assets** are packaged, smoke-tests the extracted binary.
3. **release** — on a pushed `v*` tag, uploads the `.deb` + `.sha256` to GitHub
   Releases.

### Releasing a new version

```bash
echo "0.6.0" > VERSION
# update CHANGELOG.md
git add -A
git commit -m "chore: release 0.6.0"
git tag -a v0.6.0 -m "pvz-native 0.6.0"
git push origin main --follow-tags
```

The tag triggers CI to build and publish the release automatically.

---

## 7. Common build problems

| Symptom | Cause | Fix |
|---|---|---|
| `Target MPG123::mpg123 not found` | Debian does not export the target | Add the shim `/tmp/mpg123_fix.cmake` (§3.5) |
| `SDL3 >= 3.4.0 required` | SDL3 too old | Use `release-3.4.20` |
| Engine build runs out of memory | `-j` too high | Use `-j1` |
| `XTest.h: No such file` | XTest required | `-DSDL_X11_XTEST=OFF` |
| `ENGINE_SHA256 mismatch` | Binary differs from the pin | Use route A (§3.7), or rebuild and update the checksum (§3.7 route B) |
| `gi` not found | Wrong interpreter | The GUI only runs with `/usr/bin/python3` |
| `cmake --build` succeeds but behaviour differs | An old binary is still installed | Re-run `strip -o`, replace the file, check `sha256sum` |
