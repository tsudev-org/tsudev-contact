# -*- coding: utf-8 -*-
"""Thông tin định danh ứng dụng - khai báo một nơi duy nhất."""

APP_NAME = "Contacts"
APP_SLUG = "tsudev-contact"
# Quy ước: docs/DESIGN_SYSTEM.md mục 6 - {YY}.{M}.{DD}{NN}
# (26.8.2002 = bản phát hành thứ 02 ngày 20/08/2026). Bản trước quy ước: "5.2".
APP_VERSION = "26.11.1001"
APP_ARCH = "x64"
# Nhận diện hệ sinh thái: .standards/docs/ECOSYSTEM_IDENTITY.md mục 2.3.
APP_AUTHOR = "tsudev"
PUBLISHER = "tsudev"
ECOSYSTEM_URL = "https://tsudev.com"
# Trang sản phẩm - thay cho liên kết Facebook cũ (chủ project không còn dùng, 10/11/2026).
SUPPORT_URL = "https://contact.tsudev.com"
REPO_URL = "https://github.com/tsudev-org/tsudev-contact"
COPYRIGHT = "Copyright (c) 2026 tsudev"

# Tên file phát hành (không phần mở rộng) - dùng cho PyInstaller và scripts/build-win.ps1.
RELEASE_BASENAME = f"{APP_SLUG}_{APP_VERSION}_{APP_ARCH}-setup"
