# -*- mode: python ; coding: utf-8 -*-
# Tên file xuất ra theo .standards/docs/VERSIONING.md mục 2 - lấy từ src/app_info.py (nguồn duy nhất).
import sys

sys.path.insert(0, SPECPATH)
from src.app_info import RELEASE_BASENAME

a = Analysis(
    ['contacts.pyw'],
    pathex=['.'],  # để bundle nhìn thấy package src/
    binaries=[],
    datas=[
        ('assets/icons/app-256.png', 'assets/icons'),
        # Token của bộ quy ước là nguồn chân lý giao diện - src/services/tokens.py đọc lúc chạy
        ('.standards/tokens/design-tokens.json', '.standards/tokens'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Gói 1-file: sản phẩm phát hành là đúng 1 .exe mang tên theo quy ước.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=RELEASE_BASENAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icons/app.ico'],
)
