# Plants vs. Zombies — Native Linux (`.deb`)

🇬🇧 **English**: see [README.md](README.md)

[![Release](https://img.shields.io/badge/rilis-v0.1.0-blue.svg)](https://github.com/Katon17/pvz-native-linux/releases)
[![Platform](https://img.shields.io/badge/platform-Linux%20x86__64-orange.svg)](#kebutuhan-sistem)
[![Aset](https://img.shields.io/badge/aset-tidak%20disertakan-critical.svg)](#legal)

Launcher dan pengelola aset untuk **Plants vs. Zombies: Game of the Year**
versi **native Linux** — tanpa Wine, tanpa emulator, tanpa Proton — dibangun
di atas engine open source [PvZ-Portable](https://github.com/wszqkzqk/PvZ-Portable).

Kamu cukup menunjuk file game milikmu sendiri (ISO, folder Steam, atau ZIP).
Launcher akan mengekstrak asetnya, memasang entry menu dengan ikon yang benar,
lalu menjalankan game sebagai program Linux biasa.

---

## Kenapa proyek ini ada

Engine upstream memberimu binary lalu bilang "taruh `main.pak` dan folder
`properties/` di sebelahnya". Itu wajar buat developer. Tapi nggak wajar buat
kamu yang cuma pengen main di Linux Mint.

Yang dibereskan launcher ini:

| Masalah yang biasanya kamu temui | Yang dilakukan launcher |
|---|---|
| "`main.pak`-nya ditaruh di mana?" | Wizard first-run mengekstraknya untukmu |
| Mount ISO butuh `fuse`/`7z`/root | **Pembaca ISO9660 murni Python** — tanpa tool eksternal, tanpa root |
| CD resmi isinya *installer*, bukan file longgar | Membaca CAB **di dalam** installer dan mengekstrak `main.pak` — tanpa Wine, tanpa Windows |
| Aset Steam GOTY (1.2.0.1096) punya bug kosmetik | Versi aset dideteksi **sebelum** main, lalu diberi peringatan |
| Game diklik tapi tidak terjadi apa-apa | Engine keluar dengan kode 0 walau gagal fatal — launcher memeriksa log dan menampilkan dialog sungguhan |
| Data game tercampur ke `/usr` | Aset disimpan di home directory, aman saat update paket |
| Tidak ada menu entry, ikon generik | `.desktop` native dengan set ikon lengkap |

---

## Instalasi

### Cara cepat (Debian / Ubuntu / Linux Mint / Pop!_OS)

Unduh `pvz-native_0.1.0_amd64.deb` dari
[Releases](https://github.com/Katon17/pvz-native-linux/releases), lalu:

```bash
sudo apt install ./pvz-native_0.1.0_amd64.deb
```

Sebaiknya verifikasi dulu:

```bash
sha256sum -c pvz-native_0.1.0_amd64.deb.sha256
```

### Pertama kali dijalankan

Buka menu → **Games → Plants vs. Zombies**. Wizard akan menanyakan lokasi file
gamenya:

1. **ISO / ZIP / installer (.exe)** — arahkan ke disc image, arsip, atau file
   `PlantsVsZombiesSetup.exe` resmi. ISO disc installer **didukung**: wizard
   mengambil `main.pak` dari CAB di dalamnya.
2. **Folder** — arahkan ke folder `PlantsVsZombies` dari Steam, EA App, atau
   instalasi lama.

Library Steam dideteksi otomatis. Aset disalin ke
`~/.local/share/pvz-native/assets/`, lalu game langsung jalan. Peluncuran
berikutnya tidak menanyakan apa pun lagi.

### Distro lain

File `.deb` pada dasarnya arsip tar dengan metadata tambahan:

```bash
tar -xf pvz-native-0.1.0.tar.gz -C ~/.local
pvz-native --setup
```

Catatan: binary engine upstream dibangun terhadap glibc, jadi tidak jalan di
sistem musl tanpa build ulang.

---

## Kebutuhan sistem

| | Minimum | Rekomendasi |
|---|---|---|
| **OS** | Distro glibc x86_64 apa pun | Linux Mint 22.x / Ubuntu 24.04 |
| **CPU** | x86_64 dengan SSE2 | CPU 15 tahun terakhir mana pun |
| **GPU** | OpenGL ES 2.0 **atau** OpenGL 2.1 | Apa pun dengan Mesa/`libgl1-mesa-dri` yang bekerja |
| **RAM** | 2 GB | 4 GB |
| **Disk** | ~120 MB (paket) + ~90 MB (aset) | SSD |
| **Sesi** | X11 atau Wayland (SDL3 menangani keduanya) | — |

> PvZ itu game lama. Kalau kompositormu jalan mulus, ini juga jalan. Jangan
> berharap tulisan "100+ FPS" di sini — logika game aslinya memang dikunci
> 30/60 FPS.

---

## Kontrol

| Aksi | Tombol |
|---|---|
| Gerakkan kursor / ambil matahari | Mouse |
| Tanam kartu tanaman | Klik kiri |
| Sekop | Klik sekop lalu klik tanamannya |
| Jeda | `Esc` |
| Fullscreen | `Alt`+`Enter` |
| Keluar | Tutup jendela atau `Esc` → menu |

---

## Lokasi file

| Isi | Lokasi |
|---|---|
| Aset hasil ekstrak | `~/.local/share/pvz-native/assets/` |
| Save game / profil | `~/.local/share/pvz-native/saves/` |
| Log percobaan gagal | `~/.local/share/pvz-native/logs/` |
| State launcher | `~/.config/pvz-native/state.json` |
| Binary engine | `/usr/lib/pvz-native/engine/pvz-portable` |

Tidak ada yang ditulis ke `/usr` setelah instalasi, dan uninstall paket
**tidak pernah** menghapus save game-mu.

---

## Perintah CLI

```bash
pvz-native                      # main (setup otomatis kalau perlu)
pvz-native --setup              # ulangi wizard aset
pvz-native --setup --iso ~/pvz.iso --yes    # tanpa dialog
pvz-native --inspect ~/pvz.iso              # cek sumber tanpa memasang
pvz-native --where              # tampilkan semua path
pvz-native --doctor             # diagnosa engine, aset, dan driver GL
pvz-native --verify             # validasi ulang aset terpasang
pvz-native --debug              # log engine tampil di terminal
pvz-native display fullscreen   # mode layar (atau windowed / show)
pvz-native --settings          # jendela Pengaturan (tanpa terminal)
pvz-native uninstall            # hapus aset, save tetap aman
```

### Periksa sumber aset sebelum memasang

`--inspect` tidak menyalin apa pun. Berguna untuk memastikan sebuah ISO
layak dipakai sebelum menjalankan wizard:

```bash
pvz-native --inspect ~/Downloads/Plants\ Vs\ Zombies.iso
```

Keluar dengan kode 2 dan penjelasan kalau ISO itu tidak berisi `main.pak`
yang kompatibel (~42,8 MiB, 3.195 entri).

Variabel lingkungan:

| Variabel | Efek |
|---|---|
| `PVZ_ENGINE` | Pakai binary engine lain |
| `PVZ_NATIVE_ASSETS` | Ganti folder aset |
| `PVZ_NATIVE_DEBUG=1` | Log engine tetap tampil di terminal |
| `PVZ_NATIVE_NO_GUI=1` | Paksa mode teks |

---

## Troubleshooting

### Ubah tampilan — semua dari dalam game

Buka **Options** di menu utama, lalu ada lima baris:

```
Music              [----------]
Sound FX           [----------]
3D Acceleration    [x]
Full Screen        [x]
Fill Screen (16:9) [x]     <-- ini yang mengisi layar penuh
```

**Fill Screen (16:9) sudah tercentang saat pertama kali dipasang**, jadi game
langsung tampil penuh tanpa perlu disetel apa pun.

Hilangkan centangnya kalau lebih suka rasio asli 4:3 (ada batang hitam di
kiri-kanan). Perubahan langsung terlihat setelah klik OK, dan tersimpan.

### Tentang & dukungan

**Di dalam game:** buka **Options**, lalu klik tulisan kecil
**"Tentang / About"** di bawah baris *Fill Screen (16:9)*. Muncul panel berisi
nama pembuat (**Katon Bagaskoro**) dan **dua tombol** yang bisa langsung
diklik untuk membuka browser:

| Tombol | Membuka |
|---|---|
| Saweria | <https://saweria.co/Kabako> |
| Ko-fi | <https://ko-fi.com/katonbagaskoro> |

Klik di mana saja di luar tombol untuk menutup panel.

**Di luar game:** tombol **Tentang** di jendela Pengaturan menampilkan versi, pembuat
(**Katon Bagaskoro**), dan tautan dukungan:

- Saweria — <https://saweria.co/Kabako>
- Ko-fi — <https://ko-fi.com/katonbagaskoro>

Bisa juga langsung dari menu aplikasi (**Plants vs. Zombies — Tentang**) atau:

```bash
pvz-native --about
```

**Full Screen** dan **Fill Screen (16:9)** itu dua hal berbeda:

| Centang | Artinya |
|---|---|
| Full Screen | Jendela menutupi seluruh layar (tanpa title bar) |
| Fill Screen (16:9) | Gambar direntangkan mengisi lebar layar |

Keduanya bisa diatur sendiri-sendiri, dan pilihanmu tersimpan sampai lain kali.

### Layar penuh tapi ada batang hitam di kiri-kanan

Paket ini memakai engine yang sudah dipatch, jadi batang hitam bisa
dihilangkan:

```bash
pvz-native --wide       # isi seluruh layar (tanpa batang hitam)
pvz-native --no-wide    # kembali ke rasio 4:3 asli
```

Pilihan tersimpan, jadi cukup sekali. `PVZ_WIDESCREEN=1 pvz-native` juga bisa
dipakai untuk sekali jalan.

Konsekuensinya: karena layar PvZ aslinya 4:3, peregangan ke 16:9 membuat
beberapa elemen UI bergeser sedikit (papan "START ADVENTURE" dan tombol
Options/Help/Quit lebih ke tepi). Gameplay tidak terpengaruh.

Kalau ingin tampilan paling rapi, jalankan di jendela berasio 4:3:
`pvz-native --display windowed`.

### Detail teknis rasio 4:3

Ini **disengaja**, bukan bug. Engine menjaga rasio asli 4:3:

```
GLInterface.cpp:  vw = height * 4 / 3;   // letterbox
SexyAppBase:      mWidescreenAware = false;
                  mWindowAspect.Set(4, 3);
```

Layar PvZ memang dirancang 4:3 — memaksanya ke 16:9 akan memotong bagian
atas/bawah atau meregangkan gambar. Tidak ada opsi untuk mengubahnya tanpa
mengubah kode engine.

Yang bisa dilakukan:

```bash
pvz-native display fullscreen   # penuh, dengan batang hitam kiri-kanan
pvz-native display windowed     # jendela, bisa di-resize bebas
pvz-native display show         # lihat mode sekarang
```

Kamu juga bisa mencentang **Full Screen** di menu Options dalam game.

### "Driver OpenGL tidak bisa membuat konteks" / layar hitam

```bash
sudo apt install libgl1-mesa-dri mesa-utils
unset MESA_GL_VERSION_OVERRIDE LIBGL_ALWAYS_SOFTWARE
LIBGL_ALWAYS_SOFTWARE=1 pvz-native --debug
```

Kalau rendering software jalan tapi hardware tidak, masalahnya di driver,
bukan di game. Cek `glxinfo -B`.

### "missing resource compiled/reanim/…" / game langsung menutup diri

Wizard juga **menolak** sumber seperti ini, jadi kamu tidak akan pernah
sampai ke tahap "terpasang" dengan aset yang salah.

`main.pak`-mu berasal dari build lain. `main.pak` PC 1.2.0.1073 yang sah
berukuran ~42,8 MiB dengan 3195 entri dan memuat
`reanim/LoadBar_sprout.reanim`. File 24 MB bertanggal 2009 adalah build
reduced/lama dan tidak bisa dipakai engine ini.

```bash
pvz-native --verify                 # periksa entri wajib + ukuran
pvz-native --setup --force          # arahkan ke rilis PC yang lengkap
```

Kalau engine tidak mengeluarkan pesan sama sekali, jalankan dengan log:

Jalankan dengan log terlihat:

```bash
pvz-native --debug
```

Engine keluar dengan kode 0 walaupun gagal fatal, dan crash keras menghasilkan
128+sinyal — karena itu launcher sekarang menyebutkan sinyalnya (SIGSEGV,
SIGABRT, …) dan menyimpan log ke
`~/.local/share/pvz-native/logs/last-crash.log`.

Penyebab paling sering di Intel HD / Mesa lama adalah driver GL yang belum
lengkap atau rusak:

```bash
pvz-native --doctor        # cetak GPU, renderer OpenGL, Vulkan ICD, driver DRI
LIBGL_ALWAYS_SOFTWARE=1 pvz-native --debug
```

### "FATAL ERROR — Failed to load image: properties/partner_logo"

Asetmu tidak lengkap: `resources.xml` (di dalam `main.pak`) mendeklarasikan
`partner_logo`, tetapi gambarnya dikirim sebagai **file longgar** di installer.
Sudah diperbaiki di 0.2.1. Jalankan ulang penyiapan:

```bash
pvz-native --setup --force
pvz-native --verify      # harus menampilkan "aset gambar: 691/691 tersedia"
```

### Wizard bilang `main.pak` tidak ditemukan di installer

ISO disc installer **didukung** — dibaca lewat `cabextract` (sudah menjadi
dependensi paket). Kalau menjalankan dari source:

```bash
sudo apt install cabextract
```

Masih gagal? Sebagian installer memecah data ke beberapa file, atau memakai
DRM khusus. Untuk kasus itu, pasang game sekali di Windows/Wine lalu arahkan
wizard ke folder `PlantsVsZombies` hasil instalasinya.

### Aset mana yang sebaiknya dipakai?

`main.pak` dari ISO CD bersifat **ter-XOR** (`0x4D37BD37` di disk, bukan
`0xBAC04AC0`). Itu normal dan didukung: engine melakukan XOR balik saat
memuat. Pakai apa adanya, jangan "diperbaiki".

ISO CD tidak menyertakan `properties/default.xml`, tapi file itu **opsional**
bagi engine ini (`properties/*` hanya lapisan override).

Aset diambil dari **dua tempat** lalu digabung ke satu folder `properties/`:

| Sumber | Isinya |
|---|---|
| Di dalam `main.pak` | `resources.xml`, `LawnStrings.txt`, `ZombatarTOS.txt` |
| File longgar di installer | `partner.xml`, `partner_logo.jpg`, `*.sig` |

Keduanya wajib. `--verify` mengaudit setiap deklarasi `<Image path="…">` di
`resources.xml` terhadap file yang benar-benar ada di disk.

### Teks Almanac hilang, label "Restart" tidak ada, zombie tampil `???`

Kamu memakai aset **Steam GOTY 1.2.0.1096**. Gameplay lengkap; ini perbedaan
kosmetik yang didokumentasikan upstream. Pakai rilis standalone PopCap
**1.2.0.1073** untuk hasil bersih.

### Game jalan tapi layar tidak muncul (Wayland)

Coba `SDL_VIDEODRIVER=x11 pvz-native`. Kalau jendela muncul tapi tidak pernah
fullscreen, kompositormu kemungkinan menahan fullscreen — tekan `Alt`+`Enter`.

---

## Build dari source

```bash
git clone https://github.com/Katon17/pvz-native-linux
cd pvz-native-linux
./build-deb.sh --fetch-engine     # unduh + verifikasi engine upstream
```

Hasil: `release/pvz-native_0.1.0_amd64.deb` beserta file `.sha256`.

Untuk mengembangkan launcher tanpa build ulang:

```bash
export PYTHONPATH="$PWD/tools"
export PVZ_ENGINE="$PWD/lib/pvz-native/engine/pvz-portable"
python3 -m pvznative doctor
```

Jalankan test (tidak butuh aset asli — ISO sintetis dibuat otomatis):

```bash
python3 -m unittest discover -s tests -t tests -v
```

---

## Legal

**Paket ini tidak mengandung aset game.** Tidak ada satu byte pun artwork,
audio, atau data milik PopCap/EA di dalam `.deb`.

- Kamu wajib menyediakan `main.pak` dan `properties/` dari salinan yang **kamu
  miliki sendiri** (Steam app 3590, EA App, atau CD original).
- Wizard hanya menyalin file dari penyimpananmu ke home directory-mu. Tidak
  ada yang diunggah ke mana pun.
- Engine yang dibundel (`PvZ-Portable`) adalah reimplementasi open source
  independen karya Zhou Qiankang, berlisensi **LGPL-3.0-or-later**.
- "Plants vs. Zombies" adalah merek dagang Electronic Arts Inc. Proyek ini
  tidak resmi, non-komersial, dan tidak berafiliasi dengan EA maupun PopCap.

Lihat [NOTICE](NOTICE) untuk pernyataan lengkap.

## Kredit

- **Launcher & packaging**: [Katon Bagaskoro (@Katon17)](https://github.com/Katon17)
- **Engine**: [PvZ-Portable](https://github.com/wszqkzqk/PvZ-Portable) karya
  Zhou Qiankang — bagian tersulit justru di sini
- **Framework asli**: PopCap SexyAppFramework, direimplementasi komunitas

## Lisensi

Launcher dan packaging: **GPL-3.0-or-later**.
Binary engine: **LGPL-3.0-or-later**.
