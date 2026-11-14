# Kebijakan Keamanan

> **English**: see [SECURITY.md](SECURITY.md)

## Versi yang didukung

| Versi | Didukung |
|---|---|
| 0.5.x (terbaru) | ✅ ya |
| 0.4.x | ⚠️ hanya perbaikan keamanan kritis |
| ≤ 0.3.x | ❌ tidak |

Selalu gunakan rilis terbaru dari
[GitHub Releases](https://github.com/Katon17/pvz-native-linux/releases).

---

## Melaporkan kerentanan

**Jangan buka issue publik untuk masalah keamanan.**

Gunakan salah satu jalur privat:

1. **GitHub Security Advisory** (disarankan):
   <https://github.com/Katon17/pvz-native-linux/security/advisories/new>
2. Email: **cimong2356@gmail.com** dengan subjek `[SECURITY] pvz-native`.

Sertakan bila memungkinkan:

- versi paket (`pvz-native --version` atau `dpkg -l pvz-native`)
- distro & versi kernel (`uname -a`)
- langkah reproduksi
- dampak yang kamu perkirakan
- ada/tidaknya bukti konsep (jangan sertakan exploit siap pakai)

**Waktu respons yang kami usahakan:**

| Tahap | Target |
|---|---|
| Konfirmasi penerimaan | 3 hari kerja |
| Penilaian awal | 7 hari kerja |
| Perbaikan / mitigasi | 30 hari (bergantung tingkat keparahan) |
| Pengungkapan publik | setelah perbaikan dirilis, atas kesepakatan |

Kami akan mencantumkan namamu di kredit rilis bila kamu mengizinkan.

---

## Cakupan

### Termasuk dalam cakupan

| Area | Contoh masalah |
|---|---|
| **Ekstraksi arsip** | Path traversal (`../`) pada ISO/ZIP/CAB, symlink escape, zip bomb yang membuat memori habis |
| **Penanganan installer `.exe`** | Pencarian payload CAB yang salah batas sehingga menulis di luar folder tujuan |
| **Izin berkas** | Berkas aset/save dibuat dengan mode terlalu terbuka (world-writable) |
| **Injeksi argumen** | Nama berkas tanpa escape yang membuat argumen terpisah saat memanggil `cabextract`, `xdg-open`, atau engine |
| **Skrip launcher** | Path dengan spasi, newline, atau karakter shell yang tidak di-quote |
| **Registry parser** | Pembacaan `registry.regemu` yang rusak sehingga buffer overflow / crash |
| **Provenance biner** | Biner engine yang lolos verifikasi `ENGINE_SHA256` padahal berbeda |
| **Kebocoran data** | Apa pun yang mengirim berkas pengguna ke jaringan (seharusnya **tidak ada**) |

### Di luar cakupan

- Kerentanan di **engine PvZ-Portable** → laporkan ke
  [upstream](https://github.com/wszqkzqk/PvZ-Portable).
- Kerentanan di **SDL3 / SDL3_mixer / libopenmpt** → laporkan ke proyek masing-masing.
- Masalah yang butuh akses fisik ke mesin.
- Serangan yang mensyaratkan penyerang sudah punya hak root.
- Bug tampilan, suara, atau performa (gunakan issue biasa).
- Laporan otomatis dari pemindai tanpa bukti dampak nyata.

---

## Prinsip keamanan proyek ini

Beberapa hal yang sengaja dirancang begitu:

1. **Tidak ada jaringan saat bermain.** Launcher tidak mengunggah apa pun.
   Satu-satunya koneksi keluar adalah saat kamu sendiri membuka tautan donasi.
2. **Tidak ada eksekusi dari arsip.** Wizard hanya menyalin `main.pak` dan
   `properties/`; tidak pernah menjalankan berkas dari dalam ISO.
3. **Biner engine dipin checksum.** Build gagal bila biner tidak cocok dengan
   `ENGINE_SHA256` di `build-deb.sh`.
4. **Tanpa `sudo` saat bermain.** Semua data pengguna ditulis di direktori
   `$XDG_DATA_HOME` milik pengguna sendiri.
5. **Tanpa downloader aset.** Proyek ini tidak punya fitur "unduh game";
   aset harus kamu sediakan sendiri.

---

## Verifikasi paket rilis

Sebelum memasang, selalu periksa checksum:

```bash
cd ~/Downloads
sha256sum -c pvz-native_0.5.2_amd64.deb.sha256
# harus: pvz-native_0.5.2_amd64.deb: OK
```

Periksa juga isi paket — **tidak boleh** ada aset game:

```bash
dpkg-deb -c pvz-native_0.5.2_amd64.deb \
  | grep -iE 'main\.pak|LawnStrings|properties/' \
  && echo "MENCURIGAKAN" || echo "OK: bersih"
```

Periksa biner engine-nya:

```bash
rm -rf /tmp/v && mkdir /tmp/v
dpkg-deb -x pvz-native_0.5.2_amd64.deb /tmp/v
sha256sum /tmp/v/usr/lib/pvz-native/engine/pvz-portable
# bandingkan dengan ENGINE_SHA256 di build-deb.sh pada tag yang sama
```

Kalau checksum tidak cocok, **jangan pasang** dan laporkan.
