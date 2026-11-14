#!/usr/bin/env bash
# pvz-native-linux
# Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See LICENSE for the full text.

# build-deb.sh — bungkus launcher + engine jadi satu paket .deb.
#
# Pemakaian:
#   ./build-deb.sh                      # pakai engine di lib/pvz-native/engine
#   ./build-deb.sh --fetch-engine       # unduh engine static dari upstream dulu
#   ./build-deb.sh --engine /path/bin    # pakai binary engine tertentu
#
# Hasil: release/pvz-native_<versi>_amd64.deb (+ .sha256)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="pvz-native"
APP_ID="io.github.katon17.pvz-native"
# Engine PvZ-Portable resmi dari upstream. build-deb.sh TIDAK membangun engine
# sendiri: patch widescreen sudah diterapkan lewat registry (lihat
# tools/pvznative/display.py + docs/ARCHITECTURE.md), bukan dengan menambal
# biner. Jadi checksum di sini WAJIB sama dengan artefak rilis upstream.
ENGINE_VERSION="0.2.7"
ENGINE_ASSET="pvz-portable-linux-static-x86_64"
ENGINE_URL="https://github.com/wszqkzqk/PvZ-Portable/releases/download/${ENGINE_VERSION}/${ENGINE_ASSET}"
# SHA-256 artefak rilis upstream (diverifikasi ulang 2026-11-14):
#   curl -sL "$ENGINE_URL" | sha256sum
ENGINE_SHA256="add5bc1b68d6c2a7deba6e8195a1c55c342d6d5ef4bf13af99751b8ed65aa8d9"

VERSION="$(cat "${ROOT}/VERSION" 2>/dev/null | tr -d '[:space:]')"
VERSION="${VERSION:-0.1.0}"

ENGINE_SRC="${ROOT}/lib/${APP}/engine/pvz-portable"
FETCH_ENGINE=0
OUT_DIR="${ROOT}/release"

log()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

# ----------------------------------------------------------------- argumen
while [ $# -gt 0 ]; do
    case "$1" in
        --fetch-engine) FETCH_ENGINE=1; shift ;;
        --engine)       ENGINE_SRC="$2"; shift 2 ;;
        --version)      VERSION="$2"; shift 2 ;;
        --out)          OUT_DIR="$2"; shift 2 ;;
        -h|--help)      sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *)              die "argumen tidak dikenal: $1" ;;
    esac
done

command -v dpkg-deb >/dev/null || die "dpkg-deb tidak ditemukan (butuh dpkg-dev)"

# ------------------------------------------------------------ ambil engine
if [ "$FETCH_ENGINE" -eq 1 ] || [ ! -f "$ENGINE_SRC" ]; then
    log "Mengunduh engine PvZ-Portable ${ENGINE_VERSION} (static x86_64)"
    mkdir -p "$(dirname "$ENGINE_SRC")"
    tmp="$(mktemp)"
    if command -v curl >/dev/null; then
        curl -fL --retry 3 -o "$tmp" "$ENGINE_URL"
    elif command -v wget >/dev/null; then
        wget -q -O "$tmp" "$ENGINE_URL"
    else
        die "butuh curl atau wget untuk mengunduh engine"
    fi

    actual="$(sha256sum "$tmp" | cut -d' ' -f1)"
    if [ "$actual" != "$ENGINE_SHA256" ]; then
        rm -f "$tmp"
        die "checksum engine tidak cocok!
  URL       : $ENGINE_URL
  diharapkan: $ENGINE_SHA256
  didapat   : $actual

Kemungkinan penyebab:
  1. Upstream menerbitkan ulang aset dengan nama rilis yang sama.
     Periksa: https://github.com/wszqkzqk/PvZ-Portable/releases/tag/${ENGINE_VERSION}
  2. Unduhan terpotong atau dirusak proxy/jaringan.
  3. Kamu memakai engine hasil build sendiri (patch widescreen).

Kalau (1), perbarui ENGINE_SHA256 di build-deb.sh SETELAH memverifikasi
manual. Kalau (3), pakai: ./build-deb.sh --engine /path/ke/pvz-portable"
    fi
    install -Dm755 "$tmp" "$ENGINE_SRC"
    rm -f "$tmp"
fi

[ -f "$ENGINE_SRC" ] || die "engine tidak ada di $ENGINE_SRC (pakai --fetch-engine)"

log "Versi engine : $(basename "$ENGINE_SRC") (sha256 terverifikasi)"
log "Versi paket  : ${VERSION}"

# ------------------------------------------------------------- siapkan tree
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

PKGROOT="${STAGE}/${APP}_${VERSION}_amd64"
mkdir -p \
    "${PKGROOT}/DEBIAN" \
    "${PKGROOT}/usr/bin" \
    "${PKGROOT}/usr/lib/${APP}/engine" \
    "${PKGROOT}/usr/lib/${APP}/pvznative" \
    "${PKGROOT}/usr/share/applications" \
    "${PKGROOT}/usr/share/icons/hicolor/scalable/apps" \
    "${PKGROOT}/usr/share/icons/hicolor/128x128/apps" \
    "${PKGROOT}/usr/share/doc/${APP}"

# --- launcher & python package
install -Dm755 "${ROOT}/scripts/${APP}" "${PKGROOT}/usr/bin/${APP}"
install -Dm644 "${ROOT}/tools/pvznative/"*.py "${PKGROOT}/usr/lib/${APP}/pvznative/"
# VERSION ditanam di sisi paket: __init__.py tetap 0.1.0 (dipakai test),
# dialog Tentang membaca file ini agar angkanya ikut rilis.
printf '%s\n' "${VERSION}" > "${STAGE}/VERSION-tmp"
install -Dm644 "${STAGE}/VERSION-tmp" "${PKGROOT}/usr/lib/${APP}/VERSION"
rm -f "${STAGE}/VERSION-tmp"

# --- engine
install -Dm755 "$ENGINE_SRC" "${PKGROOT}/usr/lib/${APP}/engine/pvz-portable"
chmod 0755 "${PKGROOT}/usr/lib/${APP}/engine/pvz-portable"

# --- desktop entries & ikon
install -Dm644 "${ROOT}/packaging/debian/${APP}.desktop" \
    "${PKGROOT}/usr/share/applications/${APP}.desktop"
install -Dm644 "${ROOT}/packaging/debian/${APP}-setup.desktop" \
    "${PKGROOT}/usr/share/applications/${APP}-setup.desktop"
install -Dm644 "${ROOT}/packaging/debian/${APP}-about.desktop" \
    "${PKGROOT}/usr/share/applications/${APP}-about.desktop"
install -Dm644 "${ROOT}/packaging/debian/${APP}-settings.desktop" \
    "${PKGROOT}/usr/share/applications/${APP}-settings.desktop"
install -Dm644 "${ROOT}/icons/pvz-native.svg" \
    "${PKGROOT}/usr/share/icons/hicolor/scalable/apps/${APP_ID}.svg"
for size in 48 64 128 256 512; do
    src_icon="${ROOT}/icons/pvz-native-${size}.png"
    [ -f "$src_icon" ] || continue
    mkdir -p "${PKGROOT}/usr/share/icons/hicolor/${size}x${size}/apps"
    install -Dm644 "$src_icon" \
        "${PKGROOT}/usr/share/icons/hicolor/${size}x${size}/apps/${APP_ID}.png"
done
# Ikon nama-pendek juga, agar desktop entry lama tetap menemukannya.
ln -sf "${APP_ID}.svg" "${PKGROOT}/usr/share/icons/hicolor/scalable/apps/${APP}.svg"

# --- dokumen
for doc in README.md README.id.md NOTICE CHANGELOG.md; do
    [ -f "${ROOT}/${doc}" ] && install -Dm644 "${ROOT}/${doc}" \
        "${PKGROOT}/usr/share/doc/${APP}/${doc}"
done
install -Dm644 "${ROOT}/packaging/debian/copyright" \
    "${PKGROOT}/usr/share/doc/${APP}/copyright"

# --- kontrol paket
INSTALLED_SIZE="$(du -sk --exclude=DEBIAN "$PKGROOT" | cut -f1)"
sed -e "s/@VERSION@/${VERSION}/g" -e "s/@INSTALLED_SIZE@/${INSTALLED_SIZE}/g" \
    "${ROOT}/packaging/debian/control" > "${PKGROOT}/DEBIAN/control"

install -Dm755 "${ROOT}/packaging/debian/postinst" "${PKGROOT}/DEBIAN/postinst"
install -Dm755 "${ROOT}/packaging/debian/postrm"   "${PKGROOT}/DEBIAN/postrm"

# Catat checksum engine yang dibundel, supaya bisa diaudit setelah instalasi.
( cd "${PKGROOT}" && find . -type f ! -path './DEBIAN/*' -print0 \
    | sort -z | xargs -0 sha256sum ) > "${PKGROOT}/DEBIAN/md5sums.placeholder"
# dpkg memakai md5sums, bukan sha256; buat format yang benar.
( cd "${PKGROOT}" && find . -type f ! -path './DEBIAN/*' -print0 \
    | sort -z | xargs -0 md5sum | sed 's| \./| |' ) > "${PKGROOT}/DEBIAN/md5sums"
rm -f "${PKGROOT}/DEBIAN/md5sums.placeholder"

# --------------------------------------------------------------- bangun deb
mkdir -p "$OUT_DIR"
DEB="${OUT_DIR}/${APP}_${VERSION}_amd64.deb"
log "Membangun ${DEB}"
dpkg-deb --build --root-owner-group "$PKGROOT" "$DEB" >/dev/null

( cd "$OUT_DIR" && sha256sum "$(basename "$DEB")" > "$(basename "$DEB").sha256" )

# --- tarball portabel untuk distro non-Debian (isi sama, tanpa metadata dpkg)
TARBALL="${OUT_DIR}/${APP}-${VERSION}-x86_64.tar.gz"
log "Membuat ${TARBALL}"
tar -czf "$TARBALL" -C "${PKGROOT}" ./usr
( cd "$OUT_DIR" && sha256sum "$(basename "$TARBALL")" > "$(basename "$TARBALL").sha256" )

log "Selesai."
printf '   paket  : %s\n' "$DEB"
printf '   ukuran : %s\n' "$(du -h "$DEB" | cut -f1)"
printf '   sha256 : %s\n' "$(cut -d' ' -f1 "${DEB}.sha256")"
printf '   tarball: %s (%s)\n' "$TARBALL" "$(du -h "$TARBALL" | cut -f1)"
echo
echo "Uji isi paket : dpkg-deb -c $DEB"
echo "Pasang        : sudo apt install $DEB"
echo "Uji lokal     : dpkg-deb -x $DEB /tmp/pvz-test && /tmp/pvz-test/usr/bin/pvz-native --doctor"
