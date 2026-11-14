"""Buat ikon PNG (dan SVG flat) untuk pvz-native.

Dijalankan sekali saat development; hasilnya ikut di-commit:
    python3 icons/make_icons.py

Kenapa PIL dan bukan konversi SVG: renderer SVG bawaan ImageMagick tidak
mendukung gradient dan menghasilkan ikon hitam. Menggambar langsung dengan
PIL memberi hasil yang bisa diprediksi di semua mesin build.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SCALE = 4                     # supersampling supaya tepi halus
SIZE = 512 * SCALE


def _rounded_background(size: int) -> Image.Image:
    """Latar hijau dengan gradasi vertikal + sudut membulat."""
    top = (58, 140, 62)
    bottom = (16, 74, 30)
    canvas = Image.new("RGB", (size, size), bottom)
    draw = ImageDraw.Draw(canvas)
    for y in range(size):
        ratio = y / max(1, size - 1)
        color = tuple(
            int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3)
        )
        draw.line([(0, y), (size, y)], fill=color)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(size * 0.19), fill=255
    )
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(canvas, (0, 0), mask)
    return out


def _ellipse(draw: ImageDraw.ImageDraw, box, fill, outline=None, width=0) -> None:
    draw.ellipse(box, fill=fill, outline=outline, width=width)


def build_icon(px: int = 512) -> Image.Image:
    size = px * SCALE
    image = _rounded_background(size)
    draw = ImageDraw.Draw(image)

    def s(value: float) -> float:
        """Skala koordinat dari kanvas 512 ke kanvas kerja."""
        return value * SCALE * (px / 512)

    leaf = (150, 214, 90, 255)
    leaf_dark = (40, 108, 44, 255)
    stem = (46, 118, 50, 255)

    # --- batang
    draw.line(
        [(s(300), s(260)), (s(300), s(455))],
        fill=stem,
        width=int(s(36)),
    )

    # --- daun (dua elips miring)
    left = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(left).ellipse(
        [s(150), s(360), s(300), s(430)], fill=leaf
    )
    left = left.rotate(-16, resample=Image.BICUBIC, center=(s(300), s(400)))
    image.alpha_composite(left)

    right = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(right).ellipse(
        [s(300), s(330), s(430), s(395)], fill=leaf
    )
    right = right.rotate(14, resample=Image.BICUBIC, center=(s(300), s(362)))
    image.alpha_composite(right)

    draw = ImageDraw.Draw(image)

    # --- kepala peashooter
    _ellipse(draw, [s(190), s(80), s(410), s(300)], leaf, leaf_dark, int(s(7)))
    # highlight
    _ellipse(draw, [s(238), s(120), s(292), s(158)], (233, 255, 205, 90))

    # --- moncong
    _ellipse(draw, [s(372), s(150), s(468), s(246)], (93, 187, 69, 255), leaf_dark, int(s(7)))
    _ellipse(draw, [s(402), s(180), s(438), s(216)], (13, 31, 12, 150))

    # --- mata
    _ellipse(draw, [s(322), s(122), s(366), s(186)], (16, 35, 15, 255))
    _ellipse(draw, [s(338), s(132), s(350), s(146)], (255, 255, 255, 230))

    # --- Tux kecil (penanda port Linux)
    tux_x, tux_y, tux_w = s(52), s(286), s(150)
    tux_box = [tux_x, tux_y, tux_x + tux_w, tux_y + tux_w * 1.18]
    _ellipse(draw, tux_box, (11, 22, 32, 255))
    body = [
        tux_x + tux_w * 0.22, tux_y + tux_w * 0.52,
        tux_x + tux_w * 0.78, tux_y + tux_w * 1.02,
    ]
    _ellipse(draw, body, (253, 246, 227, 255))
    # mata
    _ellipse(draw, [tux_x + tux_w * 0.24, tux_y + tux_w * 0.22,
                    tux_x + tux_w * 0.46, tux_y + tux_w * 0.48], (255, 255, 255, 255))
    _ellipse(draw, [tux_x + tux_w * 0.54, tux_y + tux_w * 0.22,
                    tux_x + tux_w * 0.76, tux_y + tux_w * 0.48], (255, 255, 255, 255))
    _ellipse(draw, [tux_x + tux_w * 0.30, tux_y + tux_w * 0.28,
                    tux_x + tux_w * 0.40, tux_y + tux_w * 0.40], (11, 22, 32, 255))
    _ellipse(draw, [tux_x + tux_w * 0.60, tux_y + tux_w * 0.28,
                    tux_x + tux_w * 0.70, tux_y + tux_w * 0.40], (11, 22, 32, 255))
    # paruh
    draw.polygon(
        [
            (tux_x + tux_w * 0.50, tux_y + tux_w * 0.50),
            (tux_x + tux_w * 0.86, tux_y + tux_w * 0.60),
            (tux_x + tux_w * 0.50, tux_y + tux_w * 0.70),
        ],
        fill=(249, 168, 37, 255),
    )
    # kaki
    _ellipse(draw, [tux_x + tux_w * 0.20, tux_y + tux_w * 0.98,
                    tux_x + tux_w * 0.52, tux_y + tux_w * 1.10], (249, 168, 37, 255))
    _ellipse(draw, [tux_x + tux_w * 0.48, tux_y + tux_w * 0.98,
                    tux_x + tux_w * 0.80, tux_y + tux_w * 1.10], (249, 168, 37, 255))

    return image.resize((px, px), Image.LANCZOS)


FLAT_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-label="Plants vs. Zombies native Linux">
  <!-- Ikon flat: tanpa gradient/filter supaya render konsisten di semua toolkit. -->
  <rect width="512" height="512" rx="97" fill="#1d5c26"/>
  <rect width="512" height="256" rx="97" fill="#2e8b3e"/>
  <rect y="200" width="512" height="312" fill="#1d5c26"/>

  <!-- batang -->
  <rect x="283" y="290" width="34" height="170" rx="17" fill="#2e7632"/>
  <!-- daun -->
  <ellipse cx="215" cy="400" rx="78" ry="37" fill="#96d65a" transform="rotate(-16 215 400)"/>
  <ellipse cx="368" cy="365" rx="74" ry="34" fill="#96d65a" transform="rotate(14 368 365)"/>

  <!-- kepala -->
  <circle cx="300" cy="190" r="110" fill="#96d65a" stroke="#286c2c" stroke-width="7"/>
  <circle cx="263" cy="141" r="37" fill="#e9ffd0" opacity="0.55"/>
  <!-- moncong -->
  <circle cx="420" cy="198" r="48" fill="#5dbb45" stroke="#286c2c" stroke-width="7"/>
  <circle cx="420" cy="198" r="18" fill="#0d1f0c" opacity="0.55"/>
  <!-- mata -->
  <ellipse cx="344" cy="154" rx="22" ry="32" fill="#10230f"/>
  <circle cx="350" cy="140" r="7" fill="#ffffff" opacity="0.9"/>

  <!-- Tux -->
  <g transform="translate(52 286)">
    <ellipse cx="75" cy="88" rx="75" ry="88" fill="#0b1620"/>
    <ellipse cx="75" cy="105" rx="42" ry="52" fill="#fdf6e3"/>
    <ellipse cx="52" cy="52" rx="17" ry="20" fill="#ffffff"/>
    <ellipse cx="98" cy="52" rx="17" ry="20" fill="#ffffff"/>
    <circle cx="53" cy="55" r="8" fill="#0b1620"/>
    <circle cx="97" cy="55" r="8" fill="#0b1620"/>
    <path d="M75 75l27 16-27 16-27-16z" fill="#f9a825"/>
    <ellipse cx="54" cy="158" rx="24" ry="9" fill="#f9a825"/>
    <ellipse cx="98" cy="158" rx="24" ry="9" fill="#f9a825"/>
  </g>
</svg>
"""


def main() -> None:
    for px, name in ((48, "pvz-native-48.png"), (64, "pvz-native-64.png"),
                     (128, "pvz-native-128.png"), (256, "pvz-native-256.png"),
                     (512, "pvz-native-512.png")):
        icon = build_icon(px)
        out = HERE / name
        icon.save(out, "PNG", optimize=True)
        print(f"{out.name}: {out.stat().st_size} byte")
    (HERE / "pvz-native.svg").write_text(FLAT_SVG, encoding="utf-8")
    print("pvz-native.svg: ditulis (flat)")


if __name__ == "__main__":
    main()
