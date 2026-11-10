# -*- coding: utf-8 -*-
"""Điểm vào ứng dụng."""
from __future__ import annotations

import sys


def main() -> int:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication

    from src.app_info import APP_SLUG, APP_VERSION, PUBLISHER
    from src.i18n import tr
    from src.services.settings import Settings, removeLegacyData
    from src.ui.main_window import MainWindow

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_SLUG)
    app.setApplicationDisplayName(APP_SLUG)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(PUBLISHER)
    app.setStyle('Fusion')  # vẽ đồng nhất trên mọi nền tảng, tôn trọng bảng màu từ token

    if sys.platform == 'win32':
        try:  # tách nhóm taskbar khỏi python.exe khi chạy từ mã nguồn
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f'{PUBLISHER}.{APP_SLUG}')
        except (AttributeError, OSError):
            pass

    window = MainWindow(Settings())
    window.show()
    if removeLegacyData():
        window.toast.show_('info', tr('toast.legacyRemoved'))
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
