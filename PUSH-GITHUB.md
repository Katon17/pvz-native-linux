# Cara Push ke GitHub (lewat terminal)

Panduan langkah demi langkah. Salin blok per blok ke terminal **di laptopmu**,
bukan di server ini.

> Sudah dicek: semua URL di repo memakai `Katon17`, email
> `cimong2356@gmail.com`, dan `VERSION` = `0.5.2`. 68 test lulus, paket
> berhasil dibangun.

---

## 0. Prasyarat di laptopmu

```bash
sudo apt update && sudo apt install -y git
git --version
```

Kalau belum punya akun GitHub yang punya hak tulis ke `Katon17` (akunmu sendiri),
lewati semua urusan SSH di bawah dan pakai Personal Access Token (§3b).

---

## 1. Siapkan identitas git

```bash
git config --global user.name  "Katon Bagaskoro"
git config --global user.email "cimong2356@gmail.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
```

---

## 2. Ambil berkas proyek

Repo ini disusun di workspace, jadi kamu perlu **mengunduh foldernya** lebih
dulu. Dari halaman workspace, unduh folder `pvz-native-linux` (atau
`pvz-native-0.5.2-source.tar.gz` bila tersedia), lalu:

```bash
cd ~/Unduhan                     # atau ~/Downloads
tar xzf pvz-native-0.5.2-source.tar.gz   # kalau berbentuk tar.gz
cd pvz-native-linux
ls -la
```

Yang harus terlihat: `LICENSE`, `NOTICE`, `SECURITY.md`, `README.md`,
`VERSION`, `docs/`, `tools/`, `scripts/`, `packaging/`, `.github/`.

---

## 3. Autentikasi ke GitHub

### 3a. SSH (disarankan, sekali pasang)

```bash
ls ~/.ssh/id_ed25519.pub 2>/dev/null || ssh-keygen -t ed25519 -C "cimong2356@gmail.com"
cat ~/.ssh/id_ed25519.pub
```

Salin keluarannya, buka <https://github.com/settings/keys> → **New SSH key** →
tempel → **Add SSH key**. Lalu uji:

```bash
ssh -T git@github.com
# harus: "Hi Katon17! You've successfully authenticated..."
```

### 3b. Token (kalau SSH tidak bisa)

Buat di <https://github.com/settings/tokens> → **Generate new token (classic)**
→ scope **`repo`** + **`workflow`**. Simpan tokennya (hanya muncul sekali).

Git akan menanyakannya sebagai "password" saat push. Supaya tidak ditanya
berulang:

```bash
git config --global credential.helper store   # disimpan di ~/.git-credentials
```

> ⚠️ `credential.helper store` menyimpan token dalam teks biasa. Di laptop
> pribadi itu praktis; di komputer bersama pakai `cache --timeout=3600`.

---

## 4. Inisialisasi repo & commit pertama

```bash
cd ~/Unduhan/pvz-native-linux

git init
git add -A
git status --short | head -30
```

**Periksa dulu** — pastikan `release/` dan `lib/.../pvz-portable` **tidak**
ikut (sudah dikecualikan `.gitignore`). Kalau keduanya muncul, hentikan dan
cek `.gitignore`.

```bash
# pastikan tidak ada aset game yang ikut
git ls-files | grep -iE 'main\.pak$|LawnStrings|^properties/' && echo "STOP!" || echo "OK bersih"
```

Commit:

```bash
git commit -m "feat: rilis awal pvz-native 0.5.2

Port native Plants vs. Zombies untuk Linux (PvZ-Portable + patch
widescreen). Launcher, wizard ekstraksi aset, jendela Pengaturan, dan
dialog Tentang di dalam game.

- patch widescreen: viewport stretch 16:9, aktif secara default
- centang Fill Screen (16:9) di Options dalam game
- Tentang/About di Options: penulis, kredit, tombol donasi
- 68 unit test, tanpa aset game di repo

Lisensi: GPL-3.0-or-later (launcher), LGPL-3.0 (engine upstream)."
```

---

## 5. Buat repo di GitHub

Lewat web: <https://github.com/new>

| Kolom | Isi |
|---|---|
| Repository name | `pvz-native-linux` |
| Description | `Native Linux port of Plants vs. Zombies (PvZ-Portable). Own your own assets.` |
| Visibility | **Public** |
| Initialize with README | **jangan dicentang** |
| .gitignore / license | **jangan dipilih** (sudah ada di repo) |

Klik **Create repository**.

---

## 6. Hubungkan & push

```bash
cd ~/Unduhan/pvz-native-linux

# SSH
git remote add origin git@github.com:Katon17/pvz-native-linux.git

# atau HTTPS
# git remote add origin https://github.com/Katon17/pvz-native-linux.git

git branch -M main
git push -u origin main
```

Kalau berhasil, buka <https://github.com/Katon17/pvz-native-linux>.

---

## 7. Periksa hasilnya

1. **Actions** → workflow `build` dan `attribution` harus hijau.
   Kalau `build` merah di tahap package, biasanya karena
   `ENGINE_SHA256` tidak cocok — lihat `docs/BUILDING.md` §3.7.
2. **Settings → General → Features** → centang **Discussions** (opsional).
3. **Settings → Code security** → aktifkan **Dependabot alerts** dan
   **Secret scanning** (gratis untuk repo publik).
4. **Settings → Branches** → tambah aturan untuk `main`:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass → pilih `Test` dan `check-notice`
   - Ini mencegah orang lain menghapus notis hak cipta lewat PR.

---

## 8. Rilis versi (tag)

```bash
cd ~/Unduhan/pvz-native-linux
echo "0.5.2" > VERSION
git add -A
git commit -m "chore: rilis 0.5.2"
git tag -a v0.5.2 -m "pvz-native 0.5.2"
git push origin main --follow-tags
```

Tag `v*` memicu CI membangun `.deb` dan menerbitkannya di
**Releases**. Setelah selesai, ambil tautan unduhan dari sana dan tempel di
README.

---

## 9. Kalau ada yang salah

| Gejala | Penyebab | Solusi |
|---|---|---|
| `remote: Permission denied` | Akun tidak punya hak tulis | Pastikan login sebagai `Katon17`; cek `git remote -v` |
| `failed to push some refs` | Repo remote sudah punya commit | `git pull --rebase origin main` lalu push lagi |
| `Support for password authentication was removed` | Pakai password, bukan token | Pakai token (§3b) atau SSH (§3a) |
| `ENGINE_SHA256 mismatch` di CI | Biner tidak ada / berbeda | Bangun engine (`docs/BUILDING.md`) atau pakai `--fetch-engine` + perbarui checksum |
| `gh` tidak ada | Belum dipasang | `sudo apt install gh` lalu `gh auth login` |

---

## 10. Alternatif: pakai GitHub CLI

Kalau lebih suka satu perintah:

```bash
sudo apt install -y gh
gh auth login                      # pilih SSH, ikuti instruksinya

cd ~/Unduhan/pvz-native-linux
git init && git add -A
git commit -m "feat: rilis awal pvz-native 0.5.2"
gh repo create pvz-native-linux --public --source=. --remote=origin --push
```

---

## 11. Setelah push — lindungi proyekmu

Tiga langkah yang paling berdampak:

1. **Branch protection** untuk `main` (§7 poin 4) — mencegah penghapusan notis
   lisensi lewat PR langsung.
2. **Rilis bertag + checksum** (§8) — memberi jejak publik bertanggal. Kalau
   nanti ada yang mengaku sebagai pembuat asli, riwayat tag dan waktu commit
   adalah buktinya.
3. **Jangan hapus `patches/widescreen.patch`** — itu kewajiban LGPL sekaligus
   bukti bahwa engine yang kamu distribusikan memang berasal dari sumber
   terbuka.

Baca juga [`docs/PROTECTION.md`](docs/PROTECTION.md) untuk penjelasan lengkap
apa yang dilindungi dan apa yang tidak.
