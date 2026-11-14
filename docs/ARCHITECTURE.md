# Arsitektur & Alur Data

Dokumen ini menjelaskan **bagaimana bagian-bagian proyek bekerja sama**, untuk
orang yang ingin memodifikasi atau mengaudit kode.

---

## 1. Gambaran besar

```
┌──────────────────────────────────────────────────────────────────┐
│  Pengguna                                                        │
│    ├── Menu aplikasi  ──► pvz-native (skrip sh)                  │
│    ├── Menu "Pengaturan" ─► pvz-native --settings                │
│    └── Menu "Tentang"    ─► pvz-native --about                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  /usr/bin/pvz-native            (POSIX sh, ~380 baris)           │
│    • parse argumen                                               │
│    • cek aset ada / belum                                        │
│    • export PVZ_WIDESCREEN                                       │
│    • exec engine                                                 │
└──────────────────────────────────────────────────────────────────┘
        │                              │
        │ aset belum ada               │ aset ada
        ▼                              ▼
┌──────────────────────────┐   ┌──────────────────────────────────┐
│ python3 -m pvznative     │   │ /usr/lib/pvz-native/engine/      │
│   setup  (wizard)        │   │   pvz-portable  (biner statis)   │
│   • deteksi ISO/ZIP/EXE  │   │   -resdir <assets>/              │
│   • scan & ekstrak       │   │   -savedir <saves>/              │
│   • verifikasi           │   └──────────────────────────────────┘
└──────────────────────────┘
```

---

## 2. Lapisan kode

| Lapisan | Lokasi | Bahasa | Tugas |
|---|---|---|---|
| **Launcher** | `scripts/pvz-native` | POSIX sh | Parsing argumen, cek aset, exec engine. Sengaja "bodoh" — semua logika berat di Python. |
| **Wizard & alat** | `tools/pvznative/` | Python 3.9+ | Deteksi sumber aset, ekstraksi CAB/ZIP/ISO, verifikasi, diagnosa. |
| **GUI** | `tools/pvznative/settings_gui.py`, `about.py` | Python + GTK3 | Jendela Pengaturan dan Tentang. |
| **Packaging** | `build-deb.sh`, `packaging/debian/` | sh + dpkg | Membangun `.deb` dan `.tar.gz`, menanam checksum engine. |
| **Engine** | `lib/pvz-native/engine/pvz-portable` | C++20 (biner) | PvZ-Portable — di-build terpisah, lihat §5. |
| **Test** | `tests/` | Python unittest | 68 test, tanpa perlu aset game asli. |

### Mengapa launcher ditulis sh, bukan Python?

Supaya tetap jalan walau Python rusak, dan supaya `pvz-native --where` tetap
bisa dipakai untuk mendiagnosa masalah Python. Aturan: **launcher tidak boleh
mengandung logika yang perlu di-test.** Semua yang bercabang rumit ada di
`tools/pvznative/` yang punya test.

---

## 3. Alur data aset

Aset **tidak pernah** ikut di dalam paket. Alurnya:

```
Sumber milik pengguna              Data pengguna
─────────────────────              ─────────────
ISO installer        ──┐
ZIP                  ──┤
Folder game          ──┼──► wizard ──► ~/.local/share/pvz-native/
Installer .exe       ──┘   (selective)     ├── assets/
                                            │   ├── main.pak
                                            │   └── properties/
                                            ├── saves/
                                            └── logs/
```

**Yang diekstrak hanya dua hal:** `main.pak` dan folder `properties/`.
Sisanya (installer, sisa ISO) tidak disalin dan tidak diubah.

### Deteksi sumber

| Jenis | Cara dideteksi |
|---|---|
| ISO 9660 | Magic `CD001` di offset 0x8001; level-1 uppercase ditangani (matching case-insensitive) |
| ZIP | Magic `PK\x03\x04` |
| Folder | Cek keberadaan `main.pak` + `properties/` |
| Installer `.exe` | Payload CAB dicari lewat magic `MSCF` di dalam biner, lalu `cabextract -F "*main.pak"` |

**Jebakan yang sudah ditangani:** ISO level-1 menyimpan nama folder dalam
huruf besar (`PROPERTIES/`), sedangkan kode mengharapkan `properties/`.
Pencocokan dilakukan case-insensitive untuk semua nama di dalam arsip.

---

## 4. Preferensi & penyimpanan state

| State | Lokasi | Format |
|---|---|---|
| Aset | `$XDG_DATA_HOME/pvz-native/assets/` | binary (dari pengguna) |
| Save game | `$XDG_DATA_HOME/pvz-native/saves/` | `userdata/` + `registry.regemu` |
| Log | `$XDG_DATA_HOME/pvz-native/logs/` | teks |
| Preferensi widescreen | `$XDG_CONFIG_HOME/pvz-native/widescreen` | `"1"` / `"0"` |
| Mode layar | `saves/registry.regemu` | custom binary, key `ScreenMode` |

### Format `registry.regemu`

```
"REGEMU" | u16 version=1 | u32 numKeys |
  per key: u32 nameLen | name (utf-8) | u8 type | value
```

Type `4` = integer, `2` = float, `1` = key kosong. Key yang benar-benar ditulis
engine: `CustomCursors, InProgress, MusicVolume, Muted, PreferredX, PreferredY,
ScreenMode, SfxVolume, WidescreenStretch, WaitForVSync`.

Diubah lewat `pvznative/display.py` (CLI) dan `settings_gui.py` (GUI) — keduanya
memakai fungsi yang sama, jadi tidak ada logika ganda.

---

## 5. Patch engine

Engine adalah **biner pihak ketiga** (PvZ-Portable, LGPL-3.0). Kami tidak
mengubah apa pun tanpa mendokumentasikannya.

| Berkas | Isi |
|---|---|
| `patches/widescreen.patch` | Diff lengkap terhadap upstream (635 baris), sumber kewajiban LGPL. |
| `ENGINE_SHA256` di `build-deb.sh` | Checksum biner yang diizinkan masuk paket. Build gagal kalau tidak cocok. |

**Aturan yang dipegang:** kalau patch berubah, checksum **wajib** diperbarui di
commit yang sama. Ini mencegah biner tak dikenal masuk paket tanpa jejak.

### Apa yang diubah patch

1. `GLInterface.cpp` — cabang *stretch* di `UpdateViewport()` saat
   `gWideScreenStretch` aktif (viewport jadi `0,0,1366,768` alih-alih
   `171,0,1024,768`).
2. `SexyAppBase.cpp` — baca `PVZ_WIDESCREEN` + key registry, default **aktif**.
3. `NewOptionsDialog.cpp/.h` — baris "Fill Screen (16:9)", panel Tentang,
   tombol donasi (`SDL_OpenURL`).
4. `Window.cpp` — sinkronisasi `mIsWindowed` dengan flag SDL sebenarnya.
5. `LawnApp.cpp` — `SwitchScreenMode(..., true)` agar perubahan mode tidak
   diabaikan.

---

## 6. Alur render (kenapa widescreen bekerja)

```
LawnApp::Init
  mWidth = gLogicalWidth   (800 normal, 1067 saat stretch)
       │
       ▼
GLInterface::Init
  mWidth = mApp->mWidth
  glUniformMatrix4fv(ortho 0..mWidth)     ← ruang gambar horizontal melebar
       │
       ▼
GLInterface::UpdateViewport()   ← TITIK PATCH
  mode normal : viewport 171,0,1024,768   (pillarbox 4:3)
  mode stretch: viewport 0,0,1366,768     (isi penuh 16:9)
       │
       ▼
glViewport(...) setiap frame
```

Gameplay tetap **5 lajur**. Yang berubah hanya pemetaan koordinat ke layar;
logika grid, tabrakan, dan jumlah lajur tidak disentuh.

**Batas yang harus diketahui:** aset reanimasi berkanvas tetap 800×600. Karena
itu tidak mungkin menambah lajur tanpa mengganti aset — pendekatan itu sudah
dicoba dan ditolak.

---

## 7. Alur GUI

```
pvz-native --settings
  └─ cek GTK_PYTHON (/usr/bin/python3, bukan python pyenv/venv)
     └─ python3 -m pvznative settings
        ├─ baca state: read_wide(), display.screen_mode()
        ├─ tampilkan 2 checkbox + 4 tombol
        └─ aksi:
            Simpan           → display.set_screen_mode(), write_wide()
            Simpan & Mainkan → apply_now() → Popen(launcher, start_new_session)
            Tentang          → about.run(parent)
```

**Kenapa interpreter GTK dicari terpisah:** `python3-gi` hanya terpasang untuk
`/usr/bin/python3`. Kalau pengguna punya pyenv/conda/venv aktif, `python3` bisa
menunjuk ke sana dan `import gi` gagal. Launcher memeriksa beberapa kandidat dan
memilih yang benar-benar punya `gi`.

---

## 8. Pengujian

| Jenis | Perintah | Cakupan |
|---|---|---|
| Unit test | `python3 -m unittest discover -s tests -t tests` | 68 test: parser, ekstraksi CAB, registry, preferensi, dialog Tentang |
| Shell syntax | `sh -n scripts/pvz-native && bash -n build-deb.sh` | sintaks |
| Build | `./build-deb.sh` | paket terbentuk + checksum cocok |
| Integritas | `dpkg-deb -c release/*.deb` | memastikan **tidak ada** aset game terpaket |

Test sengaja memakai **ISO/CAB sintetis** yang dibuat di dalam test, bukan aset
game asli. Jadi suite bisa dijalankan di CI publik tanpa melanggar hak cipta.

---

## 9. Keputusan desain yang sudah final

Dicatat supaya tidak diusulkan ulang:

| Keputusan | Alasan |
|---|---|
| **Tanpa Wine/Proton** | Ini port native; Wine ditolak sejak awal. |
| **Aset tidak pernah dibundel** | Kewajiban legal; paket tanpa aset = distribusi aman. |
| **Stretch, bukan tambah lajur** | Aset reanimasi terkunci 800×600. Menambah lajur mustahil tanpa mengganti aset. |
| **Launcher POSIX sh** | Harus tetap jalan saat Python bermasalah. |
| **50 lajur? tidak.** | Gameplay tetap 5 lajur sesuai desain asli. |
| **Biner engine dipin checksum** | Mencegah biner tak dikenal masuk rilis. |
| **Runtime hooking ditolak** | Engine statis, 0 simbol GL/SDL undefined — secara teknis mustahil. |
