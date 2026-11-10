# -*- coding: utf-8 -*-
"""Cấu hình chung cho pytest: chạy giao diện Qt không cần màn hình, cô lập thư mục cấu hình."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def isolatedConfig(tmp_path, monkeypatch):
    """Không test nào được đụng vào settings.json thật của người dùng."""
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'config'))
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'config'))
    yield
