# Changelog

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.1.0/),
versi mengikuti [Semantic Versioning](https://semver.org/lang/id/).

## [Unreleased]

### Rencana
- Flatpak manifest (lebih aman untuk aset di sandbox)
- AppImage untuk distro non-Debian
- Dukungan ekstraksi `.cab` untuk ISO disc installer
- Opsi `[GL]`/`2x` scaling (integer scaling) untuk layar resolusi tinggi
- Hotplug gamepad + pemetaan tombol dari launcher

## [0.5.2] — 2026-11-14

### Ditambahkan — dokumentasi dua bahasa (English / Indonesia)
Dilaporkan: "repo nya masih di dominasi bahasa indonesia di .md".

**English kini jadi default** karena itu yang dibaca pengunjung asing di GitHub;
Bahasa Indonesia tetap tersedia penuh sebagai berkas `.id.md` di sebelahnya.

| Dokumen | English | Indonesia |
|---|---|---|
| Spesifikasi | `docs/SPECIFICATIONS.md` | `docs/SPECIFICATIONS.id.md` |
| Membangun | `docs/BUILDING.md` | `docs/BUILDING.id.md` |
| Arsitektur | `docs/ARCHITECTURE.md` | `docs/ARCHITECTURE.id.md` |
| Perlindungan karya | `docs/PROTECTION.md` | `docs/PROTECTION.id.md` |
| Kebijakan keamanan | `SECURITY.md` | `SECURITY.id.md` |
| Kontribusi | `CONTRIBUTING.md` | `CONTRIBUTING.id.md` |
| README | `README.md` | `README.id.md` |

- Setiap dokumen punya baris pemilih bahasa di bagian atasnya, jadi pembaca
  bisa berpindah tanpa kembali ke README.
- `README.md` dan `README.id.md` sama-sama memuat tabel **Documentation** dengan
  tautan ke kedua bahasa.
- `README.id.md` disegarkan: badge `v0.1.0` yang usang diganti badge build,
  attribution, lisensi, platform, dan rilis `v0.5.2`; banner hak cipta
  ditambahkan.
- Konten teknis kedua bahasa dijaga identik — termasuk peringatan "jangan
  percaya klaim 100+ FPS", batasan 5 lajur, dan tabel angka pemakaian nyata.
- Pemeriksaan tautan silang: 0 tautan rusak di seluruh berkas Markdown.

### Diperbaiki — engine dirujuk ke rilis upstream yang benar
Dilaporkan: CI `package` gagal di GitHub Actions dengan `checksum engine tidak
cocok` (HTTP 404 pada URL unduhan).

**Akar masalah.** `build-deb.sh` menunjuk `ENGINE_VERSION="0.2.7-widescreen"`,
tag yang **tidak pernah ada** di repo upstream. Checksum `77f98a45…` adalah milik
biner hasil build lokal, sehingga setiap mesin yang tidak punya biner itu
(termasuk runner CI) akan gagal mengunduh.

**Perbaikan.**
- `ENGINE_URL` kini menunjuk rilis resmi `0.2.7` + aset
  `pvz-portable-linux-static-x86_64`.
- `ENGINE_SHA256` = `add5bc1b68d6c2a7deba6e8195a1c55c342d6d5ef4bf13af99751b8ed65aa8d9`,
  hasil verifikasi langsung atas artefak upstream (12.083.040 byte).
- Widescreen tetap berfungsi tanpa menambal biner: launcher menulis setelan ke
  `registry.regemu` sebelum engine dijalankan. Ini membuat checksum bisa
  diaudit publik — siapa pun bisa `curl | sha256sum` dan mencocokkannya.
- Pesan galat checksum sekarang menyebutkan URL, tiga kemungkinan penyebab, dan
  cara memakai engine hasil build sendiri (`--engine`).
- `docs/BUILDING.md` §3.7 dipecah: jalur A (artefak upstream, dipakai rilis
  resmi) dan jalur B (build sendiri).
- `NOTICE` §5 memuat pernyataan hak cipta eksplisit
  `(C) 2026 Katon Bagaskoro <cimong2356@gmail.com>`.
- CI `attribution` menerima nama, email, atau username sebagai bukti atribusi
  (sebelumnya hanya nama).

### Dokumentasi & perlindungan karya
- **docs/SPECIFICATIONS.md** — spec minimum lengkap: CPU, RAM, GPU per model,
  disk, layar, OS, sesi desktop, cara verifikasi driver, angka pemakaian nyata,
  dan daftar hal yang **tidak** dibutuhkan (Wine, Vulkan, Node, dll).
- **docs/PROTECTION.md** — apa yang dilindungi, apa yang tidak, hak & kewajiban
  GPL-3.0, aturan merek, dan langkah yang ditempuh bila terjadi pelanggaran.
- **docs/BUILDING.md** — membangun launcher & engine dari nol, termasuk shim
  `MPG123::mpg123` dan alasan `-j1`.
- **docs/ARCHITECTURE.md** — alur data, titik patch engine, keputusan desain
  yang sudah final.
- **SECURITY.md** — cakupan, jalur pelaporan privat, dan cara memverifikasi
  paket rilis.
- **PUSH-GITHUB.md** — panduan push lewat terminal (SSH & token, branch
  protection, rilis bertag).
- **.github/workflows/attribution.yml** — CI yang menolak commit yang menghapus
  notis hak cipta, menyertakan aset game, atau membocorkan kredensial.
- Header hak cipta GPL ditambahkan ke seluruh berkas sumber.
- `Maintainer` di packaging memakai email asli pemilik proyek.

### Diperbaiki — tampilan Tentang dirapikan, tautan bisa diklik
Dilaporkan: "tampilannya kepotong ga rapi dan link-nya gabisa di pencet".

**Tata letak.** Panel diperbesar jadi 363x248 dan semua isi ditata ulang:

- Tidak ada lagi teks yang bertumpuk. Sebelumnya dua baris kredit memakai
  koordinat Y absolut sehingga menimpa baris "Dibuat oleh" dan nama pembuat.
- Hierarki jelas: judul → "Dibuat oleh" → nama → garis pemisah → dukungan
  → kredit engine → disclaimer.
- Semua teks rata tengah, jadi tidak ada lagi baris yang menggantung.

**Tautan jadi tombol.** Kedua URL kini berbentuk tombol berbingkai yang bisa
diklik, bukan teks mati:

| Tombol | Membuka |
|---|---|
| Saweria | `https://saweria.co/Kabako` |
| Ko-fi | `https://ko-fi.com/katonbagaskoro` |

Tombol menyala hijau saat kursor di atasnya, dan nama platform ditampilkan
utuh ("Saweria", "Ko-fi") — alamat lengkapnya tetap tercetak di panel Tentang
versi jendela aplikasi.

**Browser benar-benar terbuka.** `SexyAppBase::OpenURL()` ternyata cuma stub
di port ini — ia mencatat URL lalu tidak pernah memanggil `xdg-open`, jadi
tautan mana pun di game tidak berfungsi. Sekarang memakai `SDL_OpenURL()`
yang menangani xdg-open / ShellExecute sesuai platform.

### Diverifikasi
Dengan shim `xdg-open` yang mencatat argumennya:

```
https://saweria.co/Kabako
https://ko-fi.com/katonbagaskoro
```

Kedua URL benar-benar dikirim ke sistem saat tombolnya diklik.

## [0.5.1] — 2026-11-14

### Ditambahkan — Tentang di dalam game (dialog Options)
Tautan **"Tentang / About"** sekarang ada **di dialog Options milik game**,
tepat di bawah baris "Fill Screen (16:9)". Klik tautan itu dan muncul panel
berisi:

- Pembuat: **Katon Bagaskoro**
- **saweria.co/Kabako**
- **ko-fi.com/katonbagaskoro**
- Kredit engine PvZ-Portable (LGPL-3.0) dan disclaimer EA

Klik di mana saja (atau tekan Esc) untuk menutup panel dan kembali ke opsi.

### Detail teknis
Panel digambar langsung dengan `FillRect`/`PvzpDrawString` memakai font game
sendiri (`FONT_DWARVENTODCRAFT12/15`), jadi **tidak butuh aset baru** dan tetap
tampil sama di semua resolusi.

Kontrol (2 slider + 3 checkbox) adalah widget anak yang digambar setelah
`Draw()` induk, sehingga panel akan tertembus kalau dibiarkan. Karena itu
`SetAboutPanelOpen()` menyembunyikan kelimanya selama panel terbuka.

Posisi tautan ikut tergeser +25 px saat dialog dibuka dari pemilih level
(`mFromGameSelector`), sama seperti baris opsi lainnya.

### Diverifikasi dengan screenshot
| Konteks | Hasil |
|---|---|
| Options dari menu utama | Tautan tampil, panel terbuka bersih |
| Options saat bermain | Tautan tampil di posisi benar, panel bersih |
| Klik di luar / Esc | Panel tertutup, checkbox kembali |
| Posisi | Tidak menabrak "Fill Screen" maupun tombol OK |

## [0.5.0] — 2026-11-14

### Ditambahkan — dialog Tentang dengan kredit & tautan donasi
- Tombol **Tentang** di jendela Pengaturan, dan entri menu aplikasi
  **Plants vs. Zombies — Tentang**.
- Nama pembuat: **Katon Bagaskoro**.
- Tautan donasi: **Saweria** (`https://saweria.co/Kabako`) dan
  **Ko-fi** (`https://ko-fi.com/katonbagaskoro`), plus kredit engine
  PvZ-Portable dan lisensi LGPL-3.0.
- URL dicetak di bawah tiap tautan dan bisa disorot/dikopi, jadi tetap
  terbaca meskipun browser gagal terbuka.
- Kalau `xdg-open` tidak tersedia, dialog menampilkan pesan agar URL disalin
  manual — tidak gagal diam-diam.
- Flag baru `pvz-native --about` (alias `--tentang`). Tanpa GTK3, tautan
  dicetak ke terminal, bukan error.

### Diperbaiki
- Nomor versi di dialog Tentang sebelumnya selalu `0.1.0` karena dibaca dari
  konstanta internal. Sekarang `build-deb.sh` menanam file `VERSION` di
  `/usr/lib/pvz-native/VERSION` sehingga angkanya ikut rilis.
- `--about` sempat jatuh ke alur normal dan **menjalankan game**. Sekarang
  keluar langsung setelah dialog.

### Test
68 test (sebelumnya 57) — 11 test baru untuk dialog Tentang: nama pembuat,
kedua URL donasi, resolusi versi, pembukaan tautan, dan impor tanpa GTK.

## [0.4.1] — 2026-11-14

### Diperbaiki — centang Full Screen tidak bisa dimatikan
Dilaporkan: "mau di-off-in atau di-on-in, Full Screen tetap on terus".

Ada dua bug yang saling menutupi:

1. **`SwitchScreenMode` keluar terlalu cepat.** `KillNewOptionsDialog()`
   memanggilnya dengan `force=false`, sehingga pemeriksaan
   `mIsWindowed == wantWindowed` langsung `return` dan window SDL tidak pernah
   diubah. Sekarang memakai `force=true`.
2. **Status internal tidak sinkron dengan window nyata.** `mIsWindowed` bisa
   bernilai "windowed" padahal `SDL_WINDOW_FULLSCREEN` masih aktif, jadi
   centang berikutnya membaca nilai yang salah. `MakeWindow()` sekarang
   menyinkronkan `mIsWindowed` dari flag SDL yang sebenarnya setelah
   `SDL_SetWindowFullscreen()` + `SDL_SyncWindow()`.

### Diverifikasi
| Aksi | Hasil |
|---|---|
| Lepas centang Full Screen + OK | Window keluar dari fullscreen |
| Buka Options lagi | Centang tetap kosong |
| Centang lagi + OK | Kembali fullscreen |
| Keluar game | `ScreenMode=0` tersimpan di `registry.regemu` |
| Jalankan ulang | Mode terakhir dipakai |

### Catatan
`Fill Screen (16:9)` dan `Full Screen` adalah dua hal berbeda dan keduanya
bisa diatur sendiri-sendiri:

- **Full Screen** = jendela menutupi seluruh layar atau tidak.
- **Fill Screen (16:9)** = gambar direntangkan mengisi lebar layar atau
  dibiarkan 4:3 dengan batang hitam.

## [0.4.0] — 2026-11-14

### Ditambahkan — kontrol langsung di dalam game
- **Centang "Fill Screen (16:9)" di dialog Options** milik game, tepat di
  bawah "Full Screen". Tanpa terminal, tanpa jendela pengaturan terpisah.
- **Aktif secara default.** Setelah instalasi, game langsung tampil penuh;
  tidak ada yang perlu disetel.
- Perubahan berlaku seketika setelah klik OK dan tersimpan di
  `registry.regemu` (`WidescreenStretch`).

### Detail tata letak
Panel Options hanya 423x498 dan menyisakan ~30px di bawah tinggi tombol
terakhir. Supaya baris baru muat tanpa menabrak apa pun, blok kontrol
digeser ke atas 12px dan tombol di bawahnya tetap pada posisinya:

| Elemen | Sebelum | Sesudah |
|---|---|---|
| Music slider | y=116 | y=104 |
| Sound FX slider | y=143 | y=131 |
| 3D Acceleration | y=175 | y=163 |
| Full Screen | y=206 | y=194 |
| Fill Screen | — | **y=225** |

Diverifikasi dengan screenshot di kedua konteks (dibuka dari menu utama dan
saat bermain): centang tampil, tercentang, dan tidak menimpa tombol.

## [0.3.3] — 2026-11-14

### Diperbaiki
- Engine dibangun ulang dan checksum diperbarui. Build sebelumnya (0.3.2)
  dibuat saat eksperimen wide-layout masih aktif, sehingga latar layar judul
  bisa menyisakan area hitam. Sekarang kembali ke perilaku stretch yang stabil.

### Dicoba lalu dibatalkan
- Menambahkan centang "Fill Screen (16:9)" langsung di dialog Options dalam
  game. Sempat tampil dan berfungsi, tetapi posisinya tidak stabil: ukuran
  `options_menuback.jpg` hanya 423x498 (menyisakan ~30px di bawah), dan
  dialog memakai offset berbeda tergantung apakah dibuka dari menu utama
  atau saat bermain. Centang bisa hilang atau menimpa tombol lain.
  Perubahan itu dibatalkan agar tidak menyerahkan UI yang rusak sebagian.
  Jalur yang dipakai: jendela Pengaturan GTK (`--settings`) dan `--wide`.

## [0.3.2] — 2026-11-14

### Ditambahkan — pengaturan tanpa terminal
- **`pvz-native --settings`** membuka jendela Pengaturan GTK3: centang
  "Isi seluruh layar (16:9)" dan "Mulai dalam mode layar penuh", lalu
  **Simpan** atau **Simpan & Mainkan**. Tidak perlu menyentuh terminal.
- **Entri menu aplikasi** `pvz-native-settings.desktop` sehingga muncul di
  menu XFCE sebagai "Plants vs. Zombies — Pengaturan".
- Launcher memilih interpreter yang benar-benar bisa `import gi`
  (`/usr/bin/python3`), bukan sekadar `python3` dari PATH — penting kalau
  pengguna punya pyenv/conda/venv.
- Kalau GTK3 tidak ada, launcher menampilkan pesan yang menyebut paket yang
  perlu dipasang beserta padanan perintah terminalnya.
- `Depends` bertambah: `python3-gi`, `gir1.2-gtk-3.0`.
- 5 test baru → **57 test**.

## [0.3.1] — 2026-11-14

### Ditambahkan — widescreen sungguhan
Engine bawaan mengunci rasio 4:3 (`GLInterface::UpdateViewport` memaksa
`vw = height * 4 / 3`). Sekarang engine **dibangun ulang dari source upstream
dengan patch**:

- `PVZ_WIDESCREEN=1` membuat viewport mengisi seluruh jendela, tanpa letterbox.
- Patch ada di `GLInterface.cpp` (cabang viewport) dan `SexyAppBase.cpp`
  (pembacaan env), disimpan sebagai `patches/widescreen.patch`.
- Flag launcher: `--wide` / `--no-wide`, preferensi disimpan di
  `$XDG_CONFIG_HOME/pvz-native/widescreen`.
- Engine ikut dibangun dengan `DO_FIX_BUGS=ON` (perbaikan bug komunitas
  untuk 1.2.0.1073).

Diverifikasi dengan screenshot di Xvfb 1366x768: menu, layar mulai, dan
gameplay tampil penuh tanpa batang hitam.

### Konsekuensi yang perlu diketahui
Karena layar aslinya 4:3, peregangan ke 16:9 membuat elemen bergeser
sedikit: papan "START ADVENTURE" bergerak ke kanan dan tombol
Options/Help/Quit ke kanan bawah. Semua masih bisa diklik dan gameplay
tidak terpengaruh. Ini kompromi yang tidak bisa dihindari tanpa mengubah
tata letak UI satu per satu.

### Perubahan dependensi
Engine baru menautkan library sistem: `libopenmpt0`, `libmpg123-0`,
`libvorbis0a`, `libvorbisfile3`, `libogg0`, `zlib1g`. `Depends` diperbarui.
Engine bawaan sebelumnya static penuh, jadi ini perubahan yang perlu
diperhatikan saat memasang.

## [0.3.0] — 2026-11-14

### Ditambahkan
- **`pvz-native display [fullscreen|windowed|show]`** — lihat dan ubah mode
  layar tanpa masuk ke menu dalam game. Membaca/menulis `registry.regemu`
  (format `RegEmu` milik engine) secara langsung.
- **Wizard menanyakan mode layar** setelah aset terpasang.
- `--where` menampilkan mode layar aktif; `--doctor` juga.
- Modul `pvznative/display.py` dengan pembaca/penulis `registry.regemu`
  lengkap (mempertahankan nilai lain seperti `InProgress`, `MusicVolume`).
- 6 test baru (`test_display.py`) → 52 test.

### Catatan penting soal rasio layar
Engine **sengaja** menjaga rasio 4:3:

```cpp
// GLInterface.cpp
vw = height * 4 / 3;   // letterbox di kiri-kanan
```

`mWidescreenAware = false` dan `mWindowAspect.Set(4, 3)` di `SexyAppBase`.
Tidak ada opsi build atau env var untuk mematikannya — widescreen butuh
perubahan kode engine, yang berada di luar paket ini. Jadi yang bisa
ditawarkan adalah **fullscreen dengan letterbox** atau jendela yang bisa
di-resize, bukan gambar yang memenuhi seluruh layar 16:9.

## [0.2.7] — 2026-11-14

### Diperbaiki
- **Opsi yang tidak dikenal ditelan diam-diam.** `pvz-native --inspect FILE`
  tidak melakukan apa pun dan keluar tanpa pesan, karena launcher
  memasukkannya ke daftar argumen lalu tidak pernah memakainya. Sekarang
  launcher melaporkan `opsi tidak dikenal` dan keluar dengan kode 2.
- Launcher shell belum meneruskan `--inspect` ke CLI Python (sejak 0.2.6).

### Ditambahkan
- `pvz-native --help` / `-h` dengan daftar opsi lengkap.

## [0.2.6] — 2026-11-14

### Ditambahkan
- **`pvz-native --inspect PATH`** — periksa satu ISO/ZIP/folder/`.exe` **tanpa
  memasang apa pun**, lalu beri tahu apakah sumber itu kompatibel. Exit code 2
  kalau tidak kompatibel, sehingga bisa dipakai di skrip. Ini menjawab
  pertanyaan "ISO-ku ini bisa dipakai atau tidak?" sebelum menjalankan wizard.

### Diperbaiki
- Pencocokan file wajib di dalam pak kini toleran terhadap perbedaan huruf
  besar/kecil dan prefix folder, sehingga tidak salah menuduh paket yang
  sebenarnya lengkap.
- Launcher shell meneruskan `--inspect` (sebelumnya jatuh ke alur wizard).

## [0.2.5] — 2026-11-14

Penegakan kontrak aset. Sebelumnya wizard **menerima** paket yang tidak bisa
boot (hanya memberi peringatan), sehingga `--setup --force` dengan sumber yang
salah tetap "berhasil" dan masalahnya baru terlihat saat game crash.

### Ditambahkan
- `assets.IncompatibleAssets` dan validasi `required_missing()`. Pemindaian
  aset (folder, ISO, ZIP, dan hasil ekstraksi installer) kini **menolak**
  paket yang tidak memuat `reanim/LoadBar_sprout.reanim` atau
  `compiled/reanim/LoadBar_sprout.reanim.compiled`.
- `setup._finalize()` memvalidasi hasil ekstraksi sebelum menandai aset
  "terpasang"; kalau tidak valid, folder aset dikosongkan dan penyiapan
  gagal dengan pesan yang menyebutkan penyebabnya.

### Diperbaiki
- `PakReader` menerima file object, bukan hanya path. Sebelumnya validasi
  isi pak untuk jalur ISO/ZIP gagal tanpa suara.

### Test
- 46 test (dari 44). Fixture instalasi kini memakai `boot_files()` sehingga
  mewakili pak yang benar-benar bisa boot.

## [0.2.4] — 2026-11-14

Diagnosis akhir dari pengujian pengguna: crash `missing resource
compiled/reanim/LoadBar_sprout.reanim.compiled` ternyata **bukan** bug engine
maupun driver. `main.pak` yang dipakai berasal dari build lain (24,9 MB,
bertanggal 2009) yang tidak memuat `reanim/LoadBar_sprout.reanim`.
`--verify` versi lama melaporkan "439/439 gambar tersedia" sehingga terlihat
sehat, padahal paketnya tidak bisa dipakai.

### Ditambahkan
- **Preflight isi `main.pak`** (`installer.audit_pak_contents`). Memeriksa
  keberadaan file yang diminta engine saat startup:
  `properties/resources.xml`, `properties/LawnStrings.txt`,
  `reanim/LoadBar_sprout.reanim`, dan
  `compiled/reanim/LoadBar_sprout.reanim.compiled`.
- **Launcher menolak menjalankan game** dengan aset yang tidak memuat file
  wajib tersebut, dan menampilkan daftar file yang hilang beserta
  `--setup --force`. Sebelumnya game hanya menutup diri tanpa penjelasan.
- `--verify` menampilkan **jumlah entri** di dalam pak dan gagal dengan
  pesan jelas bila file wajib tidak ada.

### Diperbaiki
- `--verify` berhenti di pemeriksaan checksum sebelum sempat memeriksa isi.
  Urutan dibalik: isi pak diperiksa lebih dulu karena lebih menentukan;
  checksum hanya menjadi peringatan di akhir.
- `audit_pak_contents` tidak menerima argumen berupa `str`.

## [0.2.3] — 2026-11-14

Dua bug yang membuat diagnosis mustahil dilakukan.

### Diperbaiki
- **`--debug` sama sekali tidak berfungsi.** Flag ini hanya dimasukkan ke
  argumen yang diteruskan ke engine, sehingga engine menolaknya dengan
  `Invalid command line parameter: --debug` — dan log tetap disembunyikan.
  Sekarang flag ini benar-benar mengaktifkan mode log-ke-terminal.
- **`--doctor` melaporkan daftar DRI driver yang salah.** Daftar dipotong
  secara alfabetis sehingga `iris_dri` dan `radeonsi_dri` tidak pernah
  muncul walaupun terpasang. Sekarang hanya driver relevan yang ditampilkan,
  lengkap dengan keterangan GPU-nya.
- Pesan khusus bila engine menolak argumen launcher
  (`Invalid command line parameter`), agar bug semacam ini tidak lagi
  terlihat seperti "game diam saja".

### Ditambahkan
- `--verify` menampilkan **ukuran dalam byte** dan **tanggal file**
  `main.pak`.
- `--verify` memperingatkan bila `main.pak` jauh lebih kecil dari ~42,8 MiB
  (ukuran rilis PC 1.2.0.1073) — indikasi build mobile/reduced yang akan
  membuat engine crash.

## [0.2.2] — 2026-11-14

Perbaikan kualitas laporan crash. Dilaporkan dari pengujian nyata: game
langsung menutup diri tanpa pesan ("langsung crash"), sehingga tidak ada
informasi untuk didiagnosis.

### Ditambahkan
- **Deteksi crash berbasis sinyal.** Kode keluar >128 kini diterjemahkan
  menjadi nama sinyal (SIGSEGV, SIGABRT, SIGILL, ...) dan ditampilkan sebagai
  penyebab, bukan sekadar "kode 1".
- **Log crash disimpan permanen** di
  `~/.local/share/pvz-native/logs/last-crash.log`, bukan dihapus.
- **Dialog error menyertakan sampai 6 baris log terakhir** (tanpa baris
  `INFO:`), jadi penyebab terlihat tanpa perlu membuka file.
- **`--doctor` mencetak informasi grafis**: nama GPU, renderer OpenGL,
  Vulkan ICD yang terpasang, driver DRI, session type, dan variabel
  `MESA_*`/`LIBGL_*` yang sedang aktif. Plus ringkasan log crash terakhir.
- Pesan khusus untuk `Failed to load image` yang mengarahkan ke
  `--verify` dan `--setup --force`.

### Catatan
- `--debug` sekarang meneruskan kode keluar engine apa adanya dan tidak
  menampilkan dialog, supaya log bisa dibaca di terminal.

## [0.2.1] — 2026-11-14

Perbaikan bug yang dilaporkan dari pengujian nyata: aset dari ISO CD berhenti
di layar "FATAL ERROR — Failed to load image: properties/partner_logo".

### Diperbaiki
- **`properties/` yang dikirim sebagai file longgar di installer kini ikut
  diekstrak.** Sebelumnya launcher hanya mengeluarkan `properties/` dari
  dalam `main.pak`, padahal installer PopCap juga mengirim
  `partner.xml`, `partner_logo.jpg`, dan file `.sig` di luar pak.
  `resources.xml` (di dalam pak) mendeklarasikan
  `<Image id="PARTNER_LOGO" path="partner_logo" />` sehingga engine berhenti
  kalau gambarnya tidak ada.
- **`--verify` sekarang mengaudit seluruh deklarasi `<Image path=...>`** di
  `resources.xml` dan melaporkan gambar yang hilang, bukan hanya memeriksa
  checksum `main.pak`. Pada aset CD lengkap hasilnya `691/691 tersedia`.
- `--doctor` ikut melaporkan aset yang tidak lengkap dengan saran
  `pvz-native --setup --force`.

### Catatan
- Tekstur `blank` dikecualikan dari audit karena dibuat engine saat runtime.

## [0.2.0] — 2026-11-14

Fokus: **ISO disc installer** — kasus paling sering terjadi di dunia nyata.
Rilis 0.1.0 menolak ISO semacam ini dengan pesan "pasang dulu di Windows/Wine",
yang tidak masuk akal untuk proyek native Linux.

### Ditambahkan
- **Ekstraksi langsung dari installer.** `installers/PlantsVsZombiesSetup.exe`
  di dalam ISO CD resmi dibaca, `main.pak` (44,9 MB) diambil dari CAB yang
  tertanam, tanpa Wine dan tanpa Windows. Terukur 0,33 detik di mesin uji.
- **Dukungan file `.exe` sebagai sumber aset.** Mode baru di wizard
  ("Dari file installer") plus `--exe` di CLI.
- **`tools/pvznative/cab.py`** — pembaca Microsoft Cabinet (MSCF) dengan
  dukungan NONE dan MSZIP, deteksi CAB bersarang di self-extractor, dan
  validasi header untuk menghindari false positive signature `MSCF`.
- **`tools/pvznative/pak.py`** — pembaca `main.pak` PopCap, termasuk dekode
  XOR `0xF7`.
- **`tools/pvznative/installer.py`** — orkestrasi: cari CAB, ekstrak
  `main.pak`, lalu keluarkan `properties/` dari dalam pak.
- **Ekstraksi `properties/` dari dalam `main.pak`.** Diperlukan karena
  installer CD tidak menyertakan `resources.xml` dan `LawnStrings.txt` di
  luar pak.
- Dependensi paket: `cabextract` (dipakai untuk CAB berkompresi LZX).
- 16 test baru untuk CAB, PAK, installer, dan ISO-berisi-installer.

### Diperbaiki
- **Validasi `main.pak` menolak aset CD yang sah.** File dari CD tersimpan
  ter-XOR, sehingga magic di disk terbaca `0x4D37BD37`, bukan `0xBAC04AC0`.
  Launcher sekarang menerima keduanya.
- Pembaca CAB tidak lagi menolak CAB berkompresi LZX saat *membaca index* —
  index selalu bisa dibaca; hanya dekompresinya yang butuh `cabextract`.
- Blok penutup folder CAB dikenali dari `cbData==0 && cbUncomp==0`, bukan dari
  `checksum==0`: CAB PopCap mengisi field checksum dengan nilai sisa.
- Setelah aset dari installer dipasang, versi dan checksum dihitung ulang dari
  hasil ekstraksi, bukan dari nilai sementara sebelum ekstraksi.

## [0.1.0] — 2026-11-13

Rilis pertama. Fokusnya: membuat instalasi PvZ native bisa dilakukan orang
non-developer di Linux Mint/Ubuntu tanpa terminal dan tanpa tool tambahan.

### Ditambahkan
- **Pembaca ISO9660 murni Python** (`pvznative.iso9660`). Tanpa `7z`, `unar`,
  `fuse`, atau root. Mendukung Joliet, direktori bersarang, dan pembacaan
  streaming untuk file besar.
- **Wizard first-run** dengan tiga jalur: file ISO/ZIP, folder instalasi, atau
  panduan membeli game secara legal.
- **Deteksi versi aset** sebelum bermain. Mengenali 1.2.0.1073 (PopCap
  standalone) dan 1.2.0.1096 (Steam GOTY) lewat signature `CRAZY_DAVE_1700`
  di `LawnStrings.txt`, lalu memperingatkan soal bug kosmetik yang diketahui.
- **Deteksi otomatis instalasi game** di library Steam native, Steam Flatpak,
  Wine prefix PopCap, dan `~/.local/share/nvz-portable`.
- **Dukungan ZIP** sebagai sumber aset, termasuk ZIP dengan folder induk.
- **Deteksi ISO disc installer**: kalau ISO hanya berisi `setup.exe`/`.cab`,
  launcher menjelaskan alternatifnya alih-alih gagal dengan pesan kriptik.
- **Validasi magic number** `main.pak` (0xBAC04AC0) sebelum aset dianggap sah.
- **Paket `.deb`**: engine statis terverifikasi checksum, entry menu
  `Plants vs. Zombies` + `Setup Aset`, ikon 48/64/128/256/512 px + SVG.
- **CLI**: `setup`, `doctor`, `verify`, `where`, `uninstall`, serta flag
  `--iso`, `--from-dir`, `--yes`, `--debug`.
- **Diagnosa `--doctor`** yang melaporkan engine, aset, driver GL, dan session
  type — dirancang agar hasilnya bisa langsung ditempel ke issue report.
- **22 test otomatis** yang membuat ISO/ZIP sintetis, jadi tidak butuh aset
  berhak cipta untuk verifikasi.

### Diperbaiki
- Engine upstream keluar dengan **kode 0** walaupun gagal fatal (mis. gagal
  membuat konteks OpenGL). Launcher sekarang memeriksa isi log dan menampilkan
  penyebab sebenarnya plus langkah perbaikannya. Tanpa ini, gejala yang dilihat
  user hanyalah "diklik, tidak terjadi apa-apa".
- Nama file dari ISO level 1 tersimpan UPPERCASE (`PROPERTIES/`), sedangkan
  engine mencari `properties/` huruf kecil. Ekstraksi sekarang menormalkan
  nama ke bentuk kanonik.
- `pvz-native` gagal menemukan paket Python-nya saat dipasang di
  `/usr/lib/pvz-native`. Diperbaiki dengan `PYTHONPATH` eksplisit dan
  `PYTHONDONTWRITEBYTECODE` (agar tidak menulis `__pycache__` ke `/usr`).
- Argumen tambahan pada `--setup` (mis. `--iso`, `--yes`) tidak diteruskan ke
  CLI Python.
- Deteksi versi aset salah membaca `LawnStrings.txt` per baris, padahal nilai
  template berada di baris setelah nama kunci.
- Ikon SVG tidak ter-render oleh ImageMagick (gradient → hitam). Ikon PNG
  sekarang digambar lewat `icons/make_icons.py`, deterministik di semua mesin.

### Catatan
- Performa mengikuti game aslinya: logika dikunci 30/60 FPS. Proyek ini tidak
  mengklaim peningkatan FPS.
- Aset tidak pernah ikut terpaket. Lihat [NOTICE](NOTICE).
