# Contributing

Terima kasih sudah mau ikut. Dua hal penting sebelum mulai:

1. **Jangan pernah meng-attach aset game** (atau turunannya) ke issue, PR,
   atau komentar — termasuk screenshot `main.pak`, isi `properties/`, dan
   tautan unduhan. PR yang berisi aset akan ditutup tanpa diskusi.
2. **Jangan mengusulkan cara mendapatkan game secara ilegal.** Proyek ini
   hanya membantu orang yang sudah punya game-nya.

## Lingkup proyek

| Bagian | Di sini? |
|---|---|
| Launcher, wizard, ekstraksi aset | ✅ ya |
| Packaging (.deb, AppImage, Flatpak) | ✅ ya |
| Dokumentasi & troubleshooting | ✅ ya |
| Bug rendering/audio/gameplay di engine | ❌ laporkan ke [PvZ-Portable](https://github.com/wszqkzqk/PvZ-Portable) |

Kalau kamu menemukan bug yang ternyata ada di engine, tetap boleh buka issue
di sini agar bisa dikonfirmasi sebagai masalah launcher — nanti kita arahkan.

## Setup development

```bash
git clone https://github.com/Katon17/pvz-native-linux
cd pvz-native-linux

export PYTHONPATH="$PWD/tools"
export PVZ_ENGINE="$PWD/lib/pvz-native/engine/pvz-portable"

python3 -m pvznative doctor
python3 -m unittest discover -s tests -t tests -v
```

Butuh Python 3.9+. Untuk build engine: `./build-deb.sh --fetch-engine`.

## Sebelum mengirim PR

- [ ] `python3 -m unittest discover -s tests -t tests` hijau semua.
- [ ] `sh -n scripts/pvz-native` dan `bash -n build-deb.sh` tanpa error.
- [ ] Perubahan perilaku ditambahkan ke `CHANGELOG.md` bagian `[Unreleased]`.
- [ ] Tidak ada path absolut, kredensial, atau aset game di diff.
- [ ] Kalau menyentuh ekstraksi aset: tambahkan test yang membuat ISO/ZIP
      sintetis (lihat `tests/make_test_iso.py`).

## Gaya kode

**Python**
- Type hints di semua signature publik.
- `pathlib` untuk semua path, jangan string concat.
- Pesan error untuk user ditulis dalam Bahasa Indonesia dan harus menjawab
  "lalu aku harus apa?" — bukan sekadar menyebut apa yang gagal.
- Jangan menambah dependency eksternal. Proyek ini sengaja hanya memakai
  standard library agar instalasi tetap ringan.

**Shell**
- `#!/bin/sh` + `set -eu`, POSIX-compatible.
- Semua variabel diberi kutip: `"$VAR"`.
- Perhatikan `shellcheck` (`SC2086` disengaja pada `$PASSTHROUGH`, diberi
  komentar).

## Menambah dukungan distro

Untuk distro berbasis Debian, ubah `packaging/debian/`. Untuk distro lain,
prioritasnya adalah **AppImage** (satu file, jalan di mana-mana) sebelum
memecah ke format paket per-distro.

## Melaporkan bug

Sertakan output ini — sebagian besar laporan bisa diselesaikan dari sini:

```bash
pvz-native --doctor
pvz-native --verify
cat ~/.local/share/pvz-native/logs/*.log
```

Jangan menyertakan `main.pak` atau isi `properties/`. Nama file, ukuran, dan
checksum `main.pak` sudah cukup dan tidak melanggar hak cipta.

## Lisensi kontribusi

Dengan mengirim pull request, kamu menyatakan bahwa:

1. Karyamu **asli** atau kamu punya hak untuk menyumbangkannya;
2. Kamu setuju karyamu dilisensikan di bawah **GPL-3.0-or-later**, sama seperti
   proyek ini;
3. Kamu **tidak** keberatan namamu dicantumkan di riwayat commit dan daftar
   kontributor.

Proyek ini **tidak** meminta penyerahan hak cipta (CLA). Karyamu tetap milikmu;
kamu hanya memberi izin GPL kepada semua orang, termasuk proyek ini.

### Daftar periksa sebelum kirim PR

```
[ ] python3 -m unittest discover -s tests -t tests    → semua lulus
[ ] sh -n scripts/pvz-native && bash -n build-deb.sh  → tanpa galat
[ ] Tidak ada aset game di diff (main.pak, properties/, gambar/suara game)
[ ] Tidak ada kredensial, token, atau path pribadi yang ikut
[ ] CHANGELOG.md diperbarui bila mengubah perilaku
[ ] Bila mengubah patch engine: ENGINE_SHA256 ikut diperbarui di commit sama
[ ] Pesan commit mengikuti Conventional Commits (lihat di bawah)
```

## Gaya commit

```
<tipo>(<lingkup>): <ringkasan singkat>

Penjelasan opsional: kenapa perubahan ini perlu.
```

| Tipo | Untuk |
|---|---|
| `feat` | fitur baru |
| `fix` | perbaikan bug |
| `docs` | dokumentasi saja |
| `test` | menambah/memperbaiki test |
| `build` | build, packaging, dependensi |
| `refactor` | merapikan kode tanpa ubah perilaku |
| `legal` | lisensi, NOTICE, dokumen hukum |

Contoh:

```
fix(options): hormati centang Full Screen saat dimatikan

SwitchScreenMode keluar lebih awal lewat pemeriksaan
mIsWindowed == wantWindowed sehingga window SDL tidak pernah diubah.
Dipaksa dengan force=true dan mIsWindowed disinkronkan dari flag SDL.

Refs: #12
```

## Yang akan ditolak

- Kode yang mengambil jalan pintas dengan menyalin kode berlisensi tidak
  kompatibel (mis. GPL-2.0-only, kode proprietary).
- Perubahan yang menambah telemetri, analitik, atau koneksi jaringan apa pun
  tanpa diskusi lebih dulu.
- "Perbaikan" yang menghapus notis hak cipta atau atribusi.
- Bundel aset game dalam bentuk apa pun.
