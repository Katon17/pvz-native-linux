# Spesifikasi Minimum & Rekomendasi

Dokumen ini menjawab satu pertanyaan: **"Apakah komputer saya sanggup?"**

Diuji pada **ThinkPad X270** (i5-7200U, Intel HD 620, 8 GB RAM, Linux Mint
22.3 XFCE, X11) — mesin kelas bawah tahun 2017. Kalau laptop itu bisa, hampir
semua laptop bisa.

---

## 1. Ringkasan cepat

| | Minimum mutlak | Rekomendasi | Diuji pada |
|---|---|---|---|
| **CPU** | x86_64 dengan SSE2 | 2 core, 1,6 GHz | i5-7200U (2C/4T, 2,5 GHz) |
| **RAM** | **1 GB** | 2 GB | 8 GB |
| **GPU** | OpenGL ES 2.0 **atau** OpenGL 2.1 | Intel HD 4000 ke atas | Intel HD 620 |
| **VRAM** | 128 MB (shared OK) | 256 MB | shared |
| **Disk** | **350 MB** kosong | 1 GB | — |
| **Layar** | 1024×768 | 1366×768 | 1366×768 |
| **OS** | glibc ≥ 2.34, x86_64 | Linux Mint 22.x / Ubuntu 24.04 | Mint 22.3 |
| **Desktop** | X11 atau Wayland | X11 + compositor | XFCE / X11 |

> **Catatan penting soal FPS.** PvZ mengunci logika game di **30 FPS**
> (kabut tebal) atau **60 FPS** (kabut tipis) — ini keputusan desain PopCap,
> bukan keterbatasan port. Jangan percaya klaim "100+ FPS" dari mana pun.

---

## 2. Rincian per komponen

### 2.1 CPU

- Wajib **x86_64** (amd64). Build ARM/ARM64 **belum tersedia**.
- Wajib **SSE2** — semua CPU x86_64 sejak 2003 punya ini. Tidak perlu cek.
- Tidak butuh AVX, AVX2, atau instruksi modern lain.

**Cek:**

```bash
uname -m                      # harus x86_64
grep -o -m1 sse2 /proc/cpuinfo   # harus muncul "sse2"
```

### 2.2 RAM

| Kondisi | Pemakaian nyata |
|---|---|
| Idle (menu utama) | ~180 MB |
| Bermain level biasa | ~250 MB |
| Level dengan banyak zombie | ~320 MB |
| Puncak saat loading aset | ~450 MB |

**1 GB sudah cukup** kalau desktop-nya ringan (XFCE, LXQt). GNOME/KDE dengan
banyak ekstensi sebaiknya 2 GB ke atas, karena desktop itu sendiri bisa makan
800 MB sebelum game dijalankan.

**Cek:**

```bash
free -h
```

### 2.3 GPU & driver

Ini bagian yang **paling sering jadi masalah**, jadi baca pelan-pelan.

**Yang dibutuhkan:** konteks **OpenGL ES 2.0** atau **OpenGL 2.1**. Engine
mencoba ES 2.0 dulu, lalu jatuh ke GL 2.1 kompatibilitas.

| GPU | Status | Catatan |
|---|---|---|
| Intel HD 3000 (Sandy Bridge) | ✅ jalan | GL 3.1 via `i965`/`crocus` |
| Intel HD 4000–620 | ✅ jalan mulus | `i965` / `iris` |
| Intel UHD 620+ | ✅ jalan mulus | `iris` |
| AMD HD 5000+ (GCN) | ✅ jalan | `radeonsi` |
| AMD lama (r600) | ⚠️ bisa jalan | butuh `libgl1-mesa-dri` lengkap |
| NVIDIA (nouveau) | ⚠️ bisa jalan | performa di bawah proprietary |
| NVIDIA proprietary | ✅ jalan | driver 470+ |
| GPU virtual (VMware/VirtualBox) | ⚠️ sering gagal | butuh 3D acceleration diaktifkan |
| Tanpa GPU / llvmpipe | ✅ jalan, lambat | software rendering, ~20–30 FPS |

**Verifikasi driver yang wajib:**

```bash
# 1. Driver GL terpasang?
sudo apt install libgl1-mesa-dri mesa-utils

# 2. Renderer apa yang dipakai?
glxinfo -B | grep -E "OpenGL renderer|OpenGL version|OpenGL core profile version"

# 3. Cari tahu driver mana yang aktif
ls /usr/lib/x86_64-linux-gnu/dri/ | grep -E "iris|i965|radeonsi|swrast|llvmpipe"
```

Yang **tidak boleh** muncul sebagai renderer: `llvmpipe` atau `softpipe`,
**kecuali** kamu memang tidak punya GPU. Kalau muncul padahal ada GPU, berarti
driver hardware belum terpasang — game akan jalan tapi lambat.

**Kalau `glxinfo` bilang galat konteks:** pakai `pvz-native --doctor`, ia
memeriksa driver, semua variabel lingkungan yang mengganggu (mis.
`MESA_GL_VERSION_OVERRIDE`), dan sesi desktop.

### 2.4 Disk

| Komponen | Ukuran |
|---|---|
| Paket `.deb` | 2,8 MB |
| Engine (terpasang) | 9,2 MB |
| Wizard + launcher (Python) | ~500 KB |
| Aset game (`main.pak` + `properties/`) | **~90 MB** |
| Cache shader & save | ~15 MB |
| **Total setelah instalasi** | **~120 MB** |
| Ruang kerja saat ekstraksi ISO | +200 MB sementara |

Sediakan **350 MB** kosong untuk aman. File ISO sumber tidak disalin utuh —
hanya `main.pak` dan `properties/` yang diekstrak.

### 2.5 Layar

| Resolusi | Hasil |
|---|---|
| 1024×768 (4:3) | ✅ pas, tanpa batang hitam |
| 1280×800 | ✅ jalan, ada batang hitam kecil |
| 1366×768 | ✅ target utama (diuji) |
| 1920×1080 | ✅ jalan, ada batang hitam |
| Di bawah 1024×768 | ⚠️ tidak diuji, kemungkinan UI terpotong |

**Soal batang hitam:** PvZ aslinya 4:3 (800×600). Di layar 16:9, ada dua pilihan:

- **Biarkan 4:3** → gambar utuh, batang hitam di kiri-kanan.
- **Isi seluruh layar (16:9)** → gambar direntangkan penuh. Beberapa elemen
  menu sedikit bergeser ke tepi, tapi gameplay 5 lajur tidak berubah.

Atur lewat **Options di dalam game** (baris *Fill Screen (16:9)*, aktif
default) atau jendela Pengaturan.

### 2.6 Sistem operasi

| Syarat | Nilai |
|---|---|
| Arsitektur | x86_64 (amd64) |
| glibc | ≥ 2.34 (Ubuntu 22.04 / Debian 12 / Mint 21 ke atas) |
| Python | ≥ 3.9 |
| Desktop | X11 atau Wayland |

**Didukung penuh:**

- Linux Mint 21.x / 22.x
- Ubuntu 22.04 / 24.04
- Debian 12 / 13
- Pop!_OS 22.04+
- Zorin OS 17+
- Fedora 39+ (lewat tarball, bukan `.deb`)
- Arch / Manjaro (lewat tarball)

**Belum didukung:** ARM, RISC-V, musl (Alpine), ChromeOS, WSL1.

### 2.7 Sesi desktop

| Sesi | Status |
|---|---|
| X11 (XFCE, MATE, Cinnamon, KDE) | ✅ paling stabil |
| Wayland (GNOME, KDE) | ✅ jalan lewat XWayland |
| Wayland tanpa XWayland | ❌ tidak jalan |
| SSH tanpa X forwarding | ❌ tidak jalan |
| multi-monitor | ✅ jalan, game penuh di satu layar |

---

## 3. Perbandingan nyata

Angka dari pengukuran pada ThinkPad X270, 1366×768, kabut rendah:

| Skenario | CPU | RAM | FPS |
|---|---|---|---|
| Menu utama | 3% | 180 MB | 60 |
| Level 1-2 (3 zombie) | 8% | 240 MB | 60 |
| Survival, gelombang 10 | 18% | 310 MB | 60 |
| Survival, gelombang 20+ | 26% | 340 MB | 60 (konsisten) |
| Loading aset pertama | 45% | 450 MB | — |

Beban CPU rendah karena engine hanya menggambar sprite 2D. Yang paling
menentukan justru **driver GPU**: kalau jatuh ke `llvmpipe`, CPU naik ke 70–90%.

---

## 4. Kalau terasa lambat

Coba berurutan:

```bash
# 1. Pastikan driver hardware yang dipakai, bukan software
glxinfo -B | grep "OpenGL renderer"

# 2. Matikan compositor saat bermain (XFCE)
xfconf-query -c xfwm4 -p /general/use_compositing -s false

# 3. Turunkan resolusi layar
xrandr --output eDP-1 --mode 1280x720

# 4. Jalankan diagnosa bawaan
pvz-native --doctor
```

Kalau `glxinfo` menunjukkan `llvmpipe` padahal kamu punya GPU, masalahnya
**di driver**, bukan di game. Lihat bagian 2.3.

---

## 5. Yang TIDAK dibutuhkan

Supaya tidak ada yang membuang waktu memasang hal yang tidak perlu:

- ❌ **Wine / Proton / Lutris** — ini port native, bukan pembungkus Windows.
- ❌ **Vulkan** — engine memakai OpenGL, Vulkan tidak dipakai.
- ❌ **Java / .NET / Electron** — tidak ada runtime tambahan.
- ❌ **Node.js / npm** — tidak dipakai sama sekali.
- ❌ **GPU diskrit** — grafis terintegrasi sudah lebih dari cukup.
- ❌ **SSD** — HDD 5400 rpm sudah cukup; loading aset ~2 detik.
- ❌ **Akses internet** saat bermain — hanya untuk instalasi awal.

---

## 6. Dependensi paket

Dicek otomatis oleh `apt` saat instalasi:

| Paket | Untuk apa |
|---|---|
| `python3` ≥ 3.9 | launcher & wizard |
| `python3-gi`, `gir1.2-gtk-3.0` | jendela Pengaturan & Tentang |
| `zenity` \| `kdialog` | dialog file saat memilih ISO |
| `cabextract` | ekstraksi dari installer `.exe` |
| `libopenmpt0`, `libmpg123-0`, `libvorbis0a`, `libvorbisfile3`, `libogg0` | audio |
| `libc6` ≥ 2.34, `zlib1g` | dasar |

Opsional tapi disarankan: `libgl1-mesa-dri` (driver GL), `mesa-utils`
(untuk `glxinfo`).

Kalau ada dependensi yang hilang, `pvz-native --doctor` akan menyebutkannya
satu per satu beserta perintah `apt install` yang tepat.
