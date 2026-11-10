# -*- mode: python ; coding: utf-8 -*-
# Đóng gói tsudev-contact (PySide6) thành MỘT file .exe.
# Tên file theo .standards/docs/VERSIONING.md mục 2 - lấy từ src/app_info.py (nguồn duy nhất).
import sys

sys.path.insert(0, SPECPATH)
from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct,
                                                 StringTable, VarFileInfo, VarStruct, VSVersionInfo)

from src.app_info import (APP_SLUG, APP_VERSION, COPYRIGHT, ECOSYSTEM_URL, PUBLISHER,
                          RELEASE_BASENAME)

# Siêu dữ liệu bản cài - .standards/docs/ECOSYSTEM_IDENTITY.md mục 2.3.
_parts = tuple(int(p) for p in APP_VERSION.split('.')) + (0,)
VERSION_INFO = VSVersionInfo(
    ffi=FixedFileInfo(filevers=_parts, prodvers=_parts),
    kids=[
        StringFileInfo([StringTable('042a04b0', [
            StringStruct('CompanyName', PUBLISHER),
            StringStruct('FileDescription', 'tsudev-contact - Chuyển danh bạ CSV sang vCard'),
            StringStruct('FileVersion', APP_VERSION),
            StringStruct('InternalName', APP_SLUG),
            StringStruct('LegalCopyright', COPYRIGHT),
            StringStruct('OriginalFilename', f'{RELEASE_BASENAME}.exe'),
            StringStruct('ProductName', APP_SLUG),
            StringStruct('ProductVersion', APP_VERSION),
            StringStruct('Comments', ECOSYSTEM_URL),
        ])]),
        VarFileInfo([VarStruct('Translation', [0x042A, 1200])]),
    ],
)

# Module Qt/Python không dùng - bỏ để file nhỏ hơn và bề mặt tấn công hẹp hơn.
# App KHÔNG kết nối mạng, nên QtNetwork cũng bị loại.
EXCLUDES = [
    'tkinter', 'PIL', 'unittest', 'pydoc', 'xmlrpc', 'http.server',
    'PySide6.QtNetwork', 'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
    'PySide6.QtPdf', 'PySide6.QtPdfWidgets', 'PySide6.QtSql', 'PySide6.QtTest', 'PySide6.QtXml',
    'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets', 'PySide6.QtDBus', 'PySide6.QtConcurrent',
    'PySide6.QtPrintSupport', 'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtUiTools',
    'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets', 'PySide6.QtSpatialAudio',
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebChannel',
    'PySide6.QtWebSockets', 'PySide6.QtNetworkAuth', 'PySide6.QtQuick3D', 'PySide6.Qt3DCore',
]

a = Analysis(
    ['contacts.pyw'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/icons/app-64.png', 'assets/icons'),
        ('assets/icons/app-128.png', 'assets/icons'),
        ('assets/icons/app-256.png', 'assets/icons'),
        ('assets/fonts/Inter-Regular.ttf', 'assets/fonts'),
        ('assets/fonts/Inter-Medium.ttf', 'assets/fonts'),
        ('assets/fonts/Inter-SemiBold.ttf', 'assets/fonts'),
        ('assets/fonts/Inter-Bold.ttf', 'assets/fonts'),
        ('assets/fonts/Inter-LICENSE.txt', 'assets/fonts'),
        ('THIRD-PARTY-NOTICES.md', '.'),
        ('.standards/tokens/design-tokens.json', '.standards/tokens'),
        ('tokens/extensions.tsudev-contact.json', 'tokens'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=1,
)

# Bỏ plugin Qt không dùng (định dạng ảnh lạ, kết nối mạng, TLS, nền tảng khác...).
_DROP_PLUGINS = ('imageformats/qtiff', 'imageformats/qwebp', 'imageformats/qgif', 'imageformats/qicns',
                 'imageformats/qtga', 'imageformats/qwbmp', 'imageformats/qpdf', 'tls/', 'networkinformation/',
                 'platforminputcontexts/', 'generic/', 'qmltooling/', 'opengl32sw', 'Qt6Network', 'Qt6Qml',
                 'Qt6Quick', 'Qt6Pdf', 'Qt6OpenGL', 'Qt6VirtualKeyboard')
a.binaries = [b for b in a.binaries if not any(d in b[0].replace('\\', '/') for d in _DROP_PLUGINS)]
a.datas = [d for d in a.datas if '/translations/' not in d[0].replace('\\', '/')
           or d[0].replace('\\', '/').split('/')[-1].startswith(('qtbase_vi', 'qtbase_en'))]

pyz = PYZ(a.pure)

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
    upx=False,  # UPX làm phần mềm diệt virus báo nhầm nhiều hơn và hỏng chữ ký số
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icons/app.ico'],
    version=VERSION_INFO,
)
