#!/usr/bin/env python3
"""Sinh bộ icon desktop của tsudev-contact từ dấu hiệu thu gọn tsudev.

Nguồn: assets/brand/logo-mark.png - bản sinh từ dây chuyền chính thức
(repo tsudev-org/tsudev, packages/brand/build-assets.js -> apps/frontend-main/public/brand/logo-mark.png).
Đối chiếu SHA-256 ở BRAND_SHA256 bên dưới; lệch nghĩa là nguồn đã đổi, lấy lại từ repo tsudev.

Chạy: python tools/gen_icons.py   (cần Pillow)
Quy tắc: .standards/docs/BRAND_ASSETS.md mục 7 - .ico nhiều lớp 16..256, nội suy LANCZOS, giữ alpha.
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'assets' / 'brand' / 'logo-mark.png'
OUT = ROOT / 'assets' / 'icons'
BRAND_SHA256 = '4cb423dc6a3e8d978f80ec7805109c2c4bdaf0a24578dbd6fb2d4a05d0817198'
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
PNG_SIZES = [32, 64, 128, 256, 512]


def squarify(im: Image.Image) -> Image.Image:
    """Đặt dấu hiệu giữa nền vuông trong suốt; chừa vùng an toàn nhỏ (BRAND_ASSETS mục 6)."""
    w, h = im.size
    side = int(max(w, h) * 1.08)
    canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2), im)
    return canvas


def main() -> int:
    digest = hashlib.sha256(SRC.read_bytes()).hexdigest()
    if digest != BRAND_SHA256:
        sys.exit(f'Sai SHA-256 của {SRC.name}: {digest} - lấy lại từ repo tsudev.')
    square = squarify(Image.open(SRC).convert('RGBA'))
    OUT.mkdir(parents=True, exist_ok=True)
    square.resize((256, 256), Image.LANCZOS).save(
        OUT / 'app.ico', format='ICO', sizes=[(s, s) for s in ICO_SIZES])
    for size in PNG_SIZES:
        square.resize((size, size), Image.LANCZOS).save(OUT / f'app-{size}.png', optimize=True)
    print(f'Đã sinh {1 + len(PNG_SIZES)} file vào {OUT.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
