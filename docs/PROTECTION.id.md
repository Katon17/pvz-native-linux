# Perlindungan Karya — Membaca Ini Dulu

Dokumen ini menjelaskan **apa yang boleh, apa yang tidak boleh**, dan **apa yang
dilakukan pemilik proyek bila terjadi pelanggaran**.

> **English**: see [PROTECTION.md](PROTECTION.md)

Proyek: **pvz-native-linux** — <https://github.com/Katon17/pvz-native-linux>
Pemegang hak cipta: **Katon Bagaskoro**

---

## 1. Ringkasan satu paragraf

Kode di repo ini **bebas dipakai, dipelajari, dan dimodifikasi**, tapi **tidak
bebas diambil alih**. Siapa pun yang mendistribusikan versi modifikasi **wajib**
membuka sumbernya dengan lisensi yang sama, **wajib** mencantumkan kredit asli,
dan **tidak boleh** memakai nama atau identitas proyek ini untuk menyesatkan
orang bahwa versinya resmi.

---

## 2. Lisensi kode: GPL-3.0-or-later

Seluruh kode **milik proyek ini** (`scripts/`, `tools/`, `tests/`,
`build-deb.sh`, `packaging/`) dilisensikan **GNU General Public License versi 3
atau lebih baru**. Teks lengkap ada di [`LICENSE`](../LICENSE).

Konsekuensi hukum yang paling penting:

| Kamu boleh | Kamu wajib | Kamu tidak boleh |
|---|---|---|
| Pakai untuk apa saja, termasuk komersial | Bagikan kode sumber versi modifikasimu | Menutup sumber hasil modifikasi |
| Ubah sesukanya | Mempertahankan notis hak cipta asli | Mengklaim kode ini karyamu sendiri |
| Distribusikan ulang | Menyertakan teks lisensi | Menambah pembatasan di atas GPL |
| Pelajari & pelajari | Menyatakan perubahan yang kamu buat | Menuntut penulis asli atas kerusakan |

**Kalau kamu memakai kode ini di produkmu dan mengubahnya, sumbermu harus
terbuka.** Itu inti dari copyleft — bukan sekadar "gratis", tapi "tetap bebas
untuk orang berikutnya".

### Mengapa GPL-3.0 dan bukan MIT?

MIT membolehkan siapa pun mengambil kode, menutupnya, lalu menjualnya tanpa
memberi balik apa pun. Untuk proyek yang dibangun dari nol dengan ratusan jam
kerja — termasuk riset patch engine yang sulit — itu tidak adil. GPL memastikan
karya turunan tetap memberi manfaat balik ke komunitas.

### Mengapa bukan AGPL?

AGPL menambahkan klausa untuk layanan jaringan (SaaS). Proyek ini adalah
aplikasi desktop yang dijalankan lokal, jadi klausa itu tidak relevan dan hanya
akan mempersulit kompatibilitas dengan proyek lain. GPL-3.0 sudah cukup.

---

## 3. Engine: LGPL-3.0 (bukan milik kami)

Biner engine **PvZ-Portable** adalah karya pihak lain:

- Sumber: <https://github.com/wszqkzqk/PvZ-Portable>
- Lisensi: **LGPL-3.0-or-later**

Kami **tidak memiliki** engine itu dan **tidak bisa** mengubah lisensinya.
Kami hanya:

1. mengompilasinya dari sumber publik,
2. menerapkan patch kecil (didokumentasikan penuh di
   [`patches/widescreen.patch`](../patches/widescreen.patch)),
3. menyertakan diff tersebut — **ini kewajiban LGPL, bukan pilihan** (§4 LGPL).

Artinya: patch kami terhadap engine juga tunduk pada LGPL-3.0. Siapa pun boleh
memakainya ulang asalkan mematuhi LGPL.

**Yang tidak boleh:** membundel engine lalu mengklaim seluruhnya karya sendiri,
atau menutup modifikasi engine. Itu pelanggaran LGPL dan bisa dituntut oleh
pemegang hak cipta upstream **maupun** oleh siapa pun yang dirugikan.

---

## 4. Yang TIDAK dilindungi proyek ini

Supaya jelas dan tidak menyesatkan:

| Hal | Status |
|---|---|
| Aset game (`main.pak`, `properties/`, gambar, suara) | **© Electronic Arts Inc.** — bukan milik kami, tidak pernah kami distribusikan |
| Nama "Plants vs. Zombies", "PopCap", "EA" | Merek dagang Electronic Arts Inc. |
| Engine PvZ-Portable | LGPL-3.0, milik kontributor upstream |
| SDL3, SDL3_mixer | zlib license, milik kontributor SDL |
| libopenmpt | BSD-3-Clause |
| Font/gambar di repo ini (bila ada) | GPL-3.0, milik proyek ini |

**Paket ini tidak memuat satu byte pun aset game.** Itu bukan kebetulan — itu
keputusan hukum. Kalau kamu menemukan aset game di dalam paket rilis, itu bug
serius; laporkan lewat Security Policy.

---

## 5. Merek & identitas proyek

Nama **"pvz-native-linux"**, nama paket `pvz-native`, nama perintah
`pvz-native`, ikon proyek, dan nama **Katon Bagaskoro** sebagai penulis
**tidak** dilisensikan bersama kodenya.

Yang **boleh**:

- Menyebut "berdasarkan pvz-native-linux oleh Katon Bagaskoro" di README-mu.
- Memakai kode dalam fork, dengan nama berbeda.
- Menulis artikel/tutorial yang menyebut proyek ini.

Yang **tidak boleh**:

- Menerbitkan fork dengan nama sama lalu membuat orang mengira itu rilis resmi.
- Memakai ikon proyek untuk produk lain.
- Menghapus notis hak cipta lalu mengakuinya sebagai karyamu.
- Memakai nama penulis untuk memberi kesan dukungan/endorsement yang tidak ada.

---

## 6. Bila terjadi pelanggaran

Urutan langkah yang akan ditempuh:

1. **Kontak baik-baik.** Kami kirim pesan berisi tautan ke dokumen ini dan
   tenggat wajar (biasanya 14 hari) untuk memperbaiki.
2. **Takedown platform.** Bila tidak ada respons, kami ajukan laporan
   pelanggaran hak cipta ke GitHub / penyedia hosting sesuai DMCA atau
   ketentuan setara.
3. **Pencabutan lisensi.** Pelanggaran GPL berarti lisensi atas kode ini
   **berakhir otomatis** bagi pelanggar (§8 GPL-3.0). Setelah itu, penggunaan
   lanjutan adalah pelanggaran hak cipta biasa.
4. **Langkah hukum.** Bila perlu, kami tempuh jalur hukum di yurisdiksi yang
   berlaku.

**Bukti kepemilikan** yang tersedia: riwayat commit bertanda tangan, tanggal
rilis, checksum biner, dan arsip publik di GitHub Releases. Semua itu membuat
klaim "saya yang membuat ini duluan" mudah dibantah.

---

## 7. Yang perlu kamu lakukan saat fork

Checklist singkat agar fork-mu aman secara hukum:

```
[ ] Pertahankan LICENSE (GPL-3.0) dan NOTICE
[ ] Pertahankan notis "Copyright (C) 2026 Katon Bagaskoro"
[ ] Cantumkan di README: "Fork dari pvz-native-linux oleh Katon Bagaskoro"
[ ] Ganti nama paket & perintah bila kamu mendistribusikannya
[ ] Buka sumber modifikasimu (GPL mewajibkan)
[ ] Jangan sertakan aset game
[ ] Bila menyertakan engine ber-patch, sertakan patches/ juga (LGPL)
```

---

## 8. Bagaimana cara menghormati proyek ini dengan benar

Kalau proyek ini berguna untukmu, cara paling sederhana dan sah:

- ⭐ beri bintang di GitHub — membantu orang lain menemukannya,
- 🐛 laporkan bug dengan langkah reproduksi yang jelas,
- 🔧 kirim pull request, bukan salinan terpisah,
- ☕ dukung lewat [Saweria](https://saweria.co/Kabako) atau
  [Ko-fi](https://ko-fi.com/katonbagaskoro),
- 📣 sebutkan sumbernya saat membahas di forum.

Itu jauh lebih berharga daripada mengambil kode lalu menghapus nama penulisnya.

---

## 9. Pertanyaan yang sering muncul

**"Bolehkah saya menjual versi modifikasi?"**
Boleh, GPL mengizinkan. Tapi kamu **wajib** membuka sumbernya, mencantumkan
kredit, dan **tidak boleh** memakai nama proyek ini seolah-olah kamu rilis
resminya. Menjual tanpa membuka sumber = pelanggaran.

**"Bolehkah saya memakai kodenya di proyek closed-source?"**
Tidak. Kode GPL yang digabungkan ke proyek closed-source membuat seluruh
distribusi itu terikat GPL.

**"Bolehkah saya pakai sebagian kecil kode, misal satu fungsi?"**
Batas "bagian kecil" itu kabur dan berisiko. Kalau kamu menyalin kode yang
bermakna (bukan sekadar idiom umum), anggap GPL berlaku. Kalau butuh kepastian,
tanya dulu lewat issue.

**"Kalau saya hanya memakai alatnya, bukan kodenya?"**
Menjalankan atau menginstal perangkat lunak tidak menimbulkan kewajiban GPL.
Kewajiban muncul saat kamu **mendistribusikan** salinan atau versi modifikasi.

**"Saya menemukan orang menjual ulang paket ini di marketplace."**
Laporkan lewat jalur di §6. Sering kali itu pelanggaran merek sekaligus GPL.

---

## 10. Kontak

- Pelanggaran lisensi / takedown: buka issue berlabel `legal` atau hubungi
  pemilik lewat profil GitHub <https://github.com/Katon17>.
- Kerentanan keamanan: **jangan** buka issue publik — lihat
  [`SECURITY.md`](../SECURITY.md).

---

*Dokumen ini bukan nasihat hukum. Untuk sengketa bernilai besar, konsultasikan
dengan pengacara hak kekayaan intelektual di yurisdiksimu.*
