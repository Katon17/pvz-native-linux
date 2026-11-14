# Membangun dari Sumber

Panduan lengkap untuk membangun ulang **paket launcher** dan **engine** dari nol.

> **English**: see [BUILDING.md](BUILDING.md)

> **Untuk pengguna biasa:** kamu tidak perlu dokumen ini. Cukup
> `sudo apt install ./pvz-native_*_amd64.deb`.

---

## 1. Membangun paket launcher saja

Ini cara tercepat. Butuh ~10 detik dan tidak mengompilasi engine.

```bash
git clone https://github.com/Katon17/pvz-native-linux.git
cd pvz-native-linux

# Butuh biner engine sudah ada di lib/pvz-native/engine/pvz-portable
chmod +x build-deb.sh
./build-deb.sh
```

Hasil di `release/`:

```
pvz-native_0.5.2_amd64.deb
pvz-native_0.5.2_amd64.deb.sha256
pvz-native-0.5.2-x86_64.tar.gz
pvz-native-0.5.2-x86_64.tar.gz.sha256
```

### Kalau engine belum ada

```bash
./build-deb.sh --fetch-engine
```

Ini mengunduh rilis resmi PvZ-Portable dan memverifikasinya terhadap
`ENGINE_SHA256` yang dipin di skrip. Lihat §3.7.

### Opsi

| Flag | Efek |
|---|---|
| `--fetch-engine` | Unduh engine upstream bila belum ada |
| `--engine PATH` | Pakai biner engine hasil build sendiri |
| `--version X.Y.Z` | Timpa versi dari file `VERSION` |
| `--out DIR` | Tulis artefak ke direktori lain, bukan `release/` |

---

## 2. Dependensi build

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

Ruang disk yang dibutuhkan: **~2 GB** (source + build engine).

---

## 3. Membangun engine (PvZ-Portable + patch)

Ini bagian yang paling lama: **~25–40 menit** pada 2 core. Hanya perlu kalau
kamu mengubah kode engine — lihat §3.7 untuk jalur yang dipakai rilis resmi.

### 3.1 Ambil sumber

```bash
cd ~
git clone https://github.com/wszqkzqk/PvZ-Portable.git pvz-src
cd pvz-src
```

### 3.2 Terapkan patch proyek ini

```bash
git apply --stat  ~/pvz-native-linux/patches/widescreen.patch   # lihat dulu
git apply --check ~/pvz-native-linux/patches/widescreen.patch   # uji dulu
git apply         ~/pvz-native-linux/patches/widescreen.patch
```

### 3.3 SDL3 (statis)

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

> `-DSDL_X11_XTEST=OFF` wajib: tanpa itu build gagal di lingkungan tanpa
> header XTest.

### 3.4 SDL3_mixer (statis)

Semua tag 3.2.x membutuhkan SDL3 ≥ 3.4.0 — itulah alasan versi SDL di atas.

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

### 3.5 Shim `MPG123::mpg123`

CMake upstream mencari target `MPG123::mpg123` yang tidak diekspor distro
Debian. Buat `/tmp/mpg123_fix.cmake`:

```cmake
if(NOT TARGET MPG123::mpg123)
  add_library(MPG123::mpg123 SHARED IMPORTED)
  set_target_properties(MPG123::mpg123 PROPERTIES
    IMPORTED_LOCATION "/usr/lib/x86_64-linux-gnu/libmpg123.so"
    INTERFACE_INCLUDE_DIRECTORIES "/usr/include")
endif()
```

### 3.6 Kompilasi engine

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
cmake --build build -j1          # -j1 penting: hemat RAM (~1 GB/core)
strip -o /tmp/pvz-portable build/pvz-portable
```

### 3.7 Pasang ke repo & perbarui checksum

Ada dua jalur. **Jalur A** adalah yang dipakai rilis resmi; **jalur B** hanya
kalau kamu sengaja mengubah kode engine.

#### Jalur A — engine rilis upstream (dipakai rilis resmi)

Tidak perlu kompilasi sama sekali. `build-deb.sh --fetch-engine` mengunduh
artefak resmi dan memverifikasi checksum yang sudah dipin di skrip:

```bash
cd ~/pvz-native-linux
./build-deb.sh --fetch-engine
```

Patokan saat ini (diperbarui 2026-11-14):

```
ENGINE_VERSION = 0.2.7
ENGINE_ASSET   = pvz-portable-linux-static-x86_64
ENGINE_SHA256  = add5bc1b68d6c2a7deba6e8195a1c55c342d6d5ef4bf13af99751b8ed65aa8d9
```

Verifikasi manual kapan saja:

```bash
curl -sL https://github.com/wszqkzqk/PvZ-Portable/releases/download/0.2.7/pvz-portable-linux-static-x86_64 \
  | sha256sum
```

> **Penting:** widescreen **tidak** dihasilkan dengan menambal biner. Launcher
> menulis nilai ke `registry.regemu` sebelum engine dijalankan (lihat
> `tools/pvznative/display.py`). Karena itu biner engine bisa memakai artefak
> resmi apa adanya — dan itu membuat checksum bisa diaudit siapa pun.

#### Jalur B — engine hasil build sendiri

Kalau kamu memodifikasi engine, checksum upstream tidak berlaku lagi:

```bash
cp /tmp/pvz-portable ~/pvz-native-linux/lib/pvz-native/engine/pvz-portable
chmod +x ~/pvz-native-linux/lib/pvz-native/engine/pvz-portable

SHA=$(sha256sum /tmp/pvz-portable | awk '{print $1}')
cd ~/pvz-native-linux
sed -i "s/^ENGINE_SHA256=.*/ENGINE_SHA256=\"$SHA\"/" build-deb.sh
git diff build-deb.sh     # pastikan hanya baris checksum yang berubah
```

Konsekuensinya: `--fetch-engine` akan **menolak** biner itu (checksum beda), dan
pengguna tidak bisa lagi mencocokkan biner dengan rilis upstream. Untuk build
lokal, lebih bersih pakai `./build-deb.sh --engine /path/ke/pvz-portable` tanpa
mengubah `ENGINE_SHA256`.

**Jangan pernah** mengganti biner tanpa memperbarui checksum di commit yang
sama. Ini satu-satunya jaring pengaman terhadap biner tak dikenal.

---

## 4. Verifikasi hasil build

```bash
# 1. Test suite
python3 -m unittest discover -s tests -t tests

# 2. Paket terbentuk dan checksum cocok
cd release && sha256sum -c ./*.sha256

# 3. Tidak ada aset game yang bocor ke paket
dpkg-deb -c pvz-native_*.deb | grep -iE 'main\.pak|LawnStrings|properties/' \
  && echo "GAGAL: ada aset game!" || echo "OK: bersih"

# 4. Biner di paket = biner yang diharapkan
rm -rf /tmp/v && mkdir /tmp/v && dpkg-deb -x pvz-native_*.deb /tmp/v
sha256sum /tmp/v/usr/lib/pvz-native/engine/pvz-portable
grep ENGINE_SHA256 ../build-deb.sh     # harus sama

# 5. Smoke test tanpa GUI
XDG_DATA_HOME=/tmp/xdg /tmp/v/usr/bin/pvz-native --where
XDG_DATA_HOME=/tmp/xdg /tmp/v/usr/bin/pvz-native --doctor || true
```

---

## 5. Menjalankan test

```bash
python3 -m unittest discover -s tests -t tests -v
```

68 test, tanpa butuh aset game asli — ISO dan CAB dibuat sintetis di dalam
test. Aman dijalankan di CI publik.

| Berkas | Cakupan |
|---|---|
| `test_assets.py` | Deteksi ISO/ZIP/folder, pemilihan berkas |
| `test_installer.py` | Ekstraksi payload CAB dari `.exe` |
| `test_display.py` | Baca/tulis `registry.regemu` |
| `test_settings_gui.py` | Preferensi widescreen |
| `test_about.py` | Dialog Tentang, tautan donasi, versi |

---

## 6. CI/CD

`.github/workflows/build.yml` menjalankan tiga tahap:

1. **test** — matriks Python 3.10 / 3.12 / 3.13, cek sintaks shell.
2. **package** — build `.deb`, verifikasi checksum, pastikan **tidak ada aset
   game** terpaket, smoke test biner hasil ekstrak.
3. **release** — saat tag `v*` di-push, unggah `.deb` + `.sha256` ke GitHub
   Releases.

### Merilis versi baru

```bash
echo "0.6.0" > VERSION
# perbarui CHANGELOG.md
git add -A
git commit -m "chore: rilis 0.6.0"
git tag -a v0.6.0 -m "pvz-native 0.6.0"
git push origin main --follow-tags
```

Tag memicu CI membangun dan menerbitkan rilis otomatis.

---

## 7. Masalah build yang sering muncul

| Gejala | Penyebab | Solusi |
|---|---|---|
| `Target MPG123::mpg123 not found` | Debian tidak mengekspor target | Pasang shim `/tmp/mpg123_fix.cmake` (§3.5) |
| `SDL3 >= 3.4.0 required` | SDL3 terlalu lama | Pakai `release-3.4.20` |
| Build engine kehabisan memori | `-j` terlalu tinggi | Pakai `-j1` |
| `XTest.h: No such file` | Butuh XTest | `-DSDL_X11_XTEST=OFF` |
| `ENGINE_SHA256 mismatch` | Biner beda dari yang dipin | Pakai jalur A (§3.7), atau build ulang lalu perbarui checksum (§3.7 jalur B) |
| `gi` tidak ditemukan | Interpreter salah | GUI hanya jalan dengan `/usr/bin/python3` |
| `cmake --build` sukses tapi perilaku beda | Biner lama masih terpasang | `strip -o` ulang, ganti file, cek `sha256sum` |
