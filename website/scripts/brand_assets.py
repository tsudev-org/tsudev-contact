#!/usr/bin/env python3
"""Sinh tài sản thương hiệu cho contact.tsudev.com (chạy tay khi thương hiệu đổi, kết quả được commit).

Nguồn: đầu ra của dây chuyền thương hiệu tsudev (repo tsudev-org/tsudev, packages/brand/build-assets.js),
tức apps/frontend-main/public/. Không sửa ảnh nguồn; chỉ sao chép hoặc thu nhỏ (LANCZOS), không phóng to.

  python3 website/scripts/brand_assets.py --tsudev ~/projects/tsudev --fonts <thư mục BeVietnamPro-*.ttf>

Đã chạy 10/11/2026 với font từ ~/projects/app-la-ban/design/fonts (Be Vietnam Pro, OFL).

Cần Pillow.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "public"
COPY = ["apple-touch-icon.png", "favicon-96x96.png", "favicon-32x32.png", "favicon-16x16.png",
        "android-chrome-192x192.png", "android-chrome-512x512.png",
        "android-chrome-maskable-192x192.png", "android-chrome-maskable-512x512.png"]
# Token màu (tsudev-standards/tokens/design-tokens.json, chế độ light)
BG = "#EEF4FB"
SURFACE = "#FFFFFF"
TEXT = "#1C2B3A"
TEXT2 = "#44607C"
PRIMARY = "#2563EB"
BORDER = "#C9D9EC"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsudev", required=True, type=Path)
    ap.add_argument("--fonts", required=True, type=Path)
    a = ap.parse_args()
    src = a.tsudev / "apps/frontend-main/public"
    (OUT / "brand").mkdir(parents=True, exist_ok=True)

    for name in COPY:
        shutil.copyfile(src / name, OUT / name)
        print(f"sao {name} ({sha(src / name)})")
    shutil.copyfile(src / "brand/logo-mark.png", OUT / "brand/logo-mark.png")

    # favicon.ico nhiều lớp 16/24/32/48/64/128/256 (ECOSYSTEM_IDENTITY mục 5), thu nhỏ từ bản 512
    icon = Image.open(src / "android-chrome-512x512.png").convert("RGBA")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    icon.save(OUT / "favicon.ico", sizes=[(s, s) for s in sizes])
    print("sinh favicon.ico", sizes)

    # og-image.png 1200x630
    W, H = 1200, 630
    og = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(og)
    d.rounded_rectangle((48, 48, W - 48, H - 48), radius=32, fill=SURFACE, outline=BORDER, width=2)
    mark = Image.open(src / "brand/logo-mark.png").convert("RGBA")
    mh = 320
    mw = round(mark.width * mh / mark.height)
    mark = mark.resize((mw, mh), Image.LANCZOS)
    og.paste(mark, (110, (H - mh) // 2), mark)
    bold = ImageFont.truetype(str(a.fonts / "BeVietnamPro-Bold.ttf"), 62)
    reg = ImageFont.truetype(str(a.fonts / "BeVietnamPro-Regular.ttf"), 30)
    semi = ImageFont.truetype(str(a.fonts / "BeVietnamPro-SemiBold.ttf"), 30)
    x = 110 + mw + 56
    d.text((x, 180), "tsudev-contact", font=bold, fill=TEXT)
    d.text((x, 272), "Chuyển danh bạ CSV sang vCard", font=reg, fill=TEXT2)
    d.text((x, 316), "Ngoại tuyến, kiểm tra từng dòng, tiếng Việt", font=reg, fill=TEXT2)
    d.rounded_rectangle((x, 400, x + 270, 456), radius=28, fill=PRIMARY)
    d.text((x + 135, 428), "contact.tsudev.com", font=ImageFont.truetype(str(a.fonts / "BeVietnamPro-SemiBold.ttf"), 20), fill="#FFFFFF", anchor="mm")
    d.text((W - 110, H - 100), "tsudev", font=semi, fill=TEXT, anchor="rs")
    og.save(OUT / "og-image.png", optimize=True)
    print("sinh og-image.png", og.size)


if __name__ == "__main__":
    main()
