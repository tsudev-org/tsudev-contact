# -*- coding: utf-8 -*-
"""Chụp ảnh giao diện app cho website (website/public/anh/ung-dung-{sang,toi}.png) bằng QWidget.grab().

KHÔNG chụp màn hình desktop. Dữ liệu là mẫu giả của tests/fixtures/make_samples.py.
Chạy: QT_QPA_PLATFORM=offscreen .venv/bin/python tools/chup_anh_web.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from src.services.settings import Settings  # noqa: E402
from tests.fixtures.make_samples import main as makeSamples  # noqa: E402

OUT = os.path.join('website', 'public', 'anh')
SIZE = (1280, 820)


def waitIdle(app, w, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        app.processEvents()
        if w.task is None and not w.revalidateTimer.isActive():
            for _ in range(10):
                app.processEvents()
            return
        time.sleep(0.01)
    raise RuntimeError('tác vụ nền không xong kịp')


def main() -> None:
    app = QApplication.instance() or QApplication([])
    app.setStyle('Fusion')
    from src.ui.main_window import MainWindow
    with tempfile.TemporaryDirectory() as tmp:
        makeSamples(tmp)
        shots = (('light', 'all', 'ung-dung-sang.png'), ('dark', 'warning', 'ung-dung-toi.png'))
        for theme, statusFilter, name in shots:
            w = MainWindow(Settings(os.path.join(tmp, f'settings-{theme}.json')))
            w.setTheme(theme)
            w.resize(*SIZE)
            w.show()
            w.loadCsv(os.path.join(tmp, 'mau-60-cham-phay.csv'))
            waitIdle(app, w)
            waitIdle(app, w)
            if statusFilter != 'all':
                w.preview.filterButtons[statusFilter].click()
                waitIdle(app, w)
            w.resize(*SIZE)
            app.processEvents()
            assert w.grab().save(os.path.join(OUT, name)), name
            print('đã ghi', name, w.tokens.color('bg-base'))
            w.close()
            w.deleteLater()
            app.processEvents()


if __name__ == '__main__':
    main()
