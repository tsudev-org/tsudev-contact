#!/usr/bin/env python3
"""Sinh bộ icon desktop của tsudev-contact từ dấu hiệu thu gọn tsudev.

Nguồn: assets/brand/app/icon-512.png - logo SẢN PHẨM tsudev-contact (chủ dự án giao
13/11/2026), bản vuông bo góc do website/scripts/brand-assets.mjs sinh từ ảnh gốc DUY NHẤT
assets/brand/source/logo-contact.png. Đổi logo: thay ảnh gốc, chạy brand-assets.mjs, rồi chạy
script này. (Trước 13/11 nguồn là con cú dùng chung, ghim SHA-256; ghim đó bỏ vì CI đã chạy
`brand-assets.mjs --check` để bắt mọi lệch giữa ảnh gốc và bản sinh.)
Đối chiếu SHA-256 ở BRAND_SHA256 bên dưới; lệch nghĩa là nguồn đã đổi, lấy lại từ repo tsudev.

Chạy: python tools/gen_icons.py   (cần Pillow)
Quy tắc: .standards/docs/BRAND_ASSETS.md mục 7 - .ico nhiều lớp 16..256, nội suy LANCZOS, giữ alpha.
"""
from __future__ import annotations

import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'assets' / 'brand' / 'app' / 'icon-512.png'
OUT = ROOT / 'assets' / 'icons'
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
PNG_SIZES = [32, 64, 128, 256, 512]


def squarify(im: Image.Image) -> Image.Image:
    """Đặt dấu hiệu giữa nền vuông trong suốt; chừa vùng an toàn nhỏ (BRAND_ASSETS mục 6)."""
    w, h = im.size
    side = int(max(w, h) * 1.02)  # ô biểu tượng đã có lề riêng
    canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2), im)
    return canvas


def main() -> int:
    if not SRC.exists():
        sys.exit(f'Thiếu {SRC} - chạy: node website/scripts/brand-assets.mjs')
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
