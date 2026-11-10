# -*- coding: utf-8 -*-
"""Tùy chọn người dùng: lưu trong thư mục cấu hình riêng của người dùng, ghi nguyên tử.

- Windows: %LOCALAPPDATA%\\tsudev-contact\\settings.json
- Linux/macOS: $XDG_CONFIG_HOME/tsudev-contact (mặc định ~/.config/tsudev-contact)

KHÔNG dùng thư mục temp dùng chung (bản cũ dùng %TEMP% / /tmp: đường dẫn đoán trước được,
máy nhiều người dùng trên Linux có thể bị cài symlink). File này chỉ chứa tùy chọn hiển
thị - tuyệt đối không chứa dữ liệu danh bạ. Mọi giá trị đọc ra đều được kiểm lại.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

APP_DIRNAME = 'tsudev-contact'
SETTINGS_FILE = 'settings.json'
MAX_SETTINGS_BYTES = 64 * 1024

THEMES = ('system', 'light', 'warm', 'dark')
LANGUAGES = ('vi', 'en')
PAGE_SIZES = (10, 20, 50, 100, 200)       # .standards/docs/DATA_TABLE.md mục 2

DEFAULTS = {
    'theme': 'system',
    'language': 'vi',
    'pagesize.preview': 10,
    'fixLeadingZero': True,
    'dropDuplicatePhones': False,
}
_VALIDATORS = {
    'theme': lambda v: v in THEMES,
    'language': lambda v: v in LANGUAGES,
    'pagesize.preview': lambda v: type(v) is int and v in PAGE_SIZES,
    'fixLeadingZero': lambda v: type(v) is bool,
    'dropDuplicatePhones': lambda v: type(v) is bool,
}


def configDir() -> str:
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA') or os.path.expanduser(r'~\AppData\Local')
    else:
        base = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    return os.path.join(base, APP_DIRNAME)


def settingsPath() -> str:
    return os.path.join(configDir(), SETTINGS_FILE)


class Settings:
    """Đọc một lần, ghi nguyên tử mỗi khi đổi. Lỗi đọc/ghi không bao giờ làm sập app."""

    def __init__(self, path: str | None = None):
        self.path = path or settingsPath()
        self._values = dict(DEFAULTS)
        self._load()

    def _load(self) -> None:
        try:
            if os.path.getsize(self.path) > MAX_SETTINGS_BYTES:
                return
            with open(self.path, encoding='utf-8') as f:
                stored = json.load(f)
        except (OSError, ValueError):
            return
        if isinstance(stored, dict):
            for key, value in stored.items():
                if key in _VALIDATORS and _VALIDATORS[key](value):
                    self._values[key] = value

    def get(self, key: str):
        return self._values[key]

    def set(self, key: str, value) -> None:
        if key not in _VALIDATORS:
            raise KeyError(f'Tùy chọn không hợp lệ: {key}')
        if not _VALIDATORS[key](value):
            raise ValueError(f'Giá trị không hợp lệ cho {key}: {value!r}')
        self._values[key] = value
        self._save()

    def _save(self) -> None:
        directory = os.path.dirname(self.path)
        try:
            os.makedirs(directory, exist_ok=True)
            fd, tempPath = tempfile.mkstemp(prefix='.settings-', suffix='.tmp', dir=directory)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(self._values, f, ensure_ascii=False, indent=2)
                os.replace(tempPath, self.path)
            except BaseException:
                try:
                    os.unlink(tempPath)
                except OSError:
                    pass
                raise
        except OSError:
            pass  # đĩa đầy / chỉ-đọc: mất tùy chọn hiển thị, app vẫn chạy


def removeLegacyData() -> list[str]:
    """Xóa dữ liệu các bản cũ để lại trong thư mục temp, gồm CSDL chứa danh bạ (PII).

    Bản <= 26.8.2002 ghi `contacts_data.db` (toàn bộ danh bạ lần chuyển gần nhất) vào
    %TEMP%\\tsudev-contact và không bao giờ xóa. Chỉ xóa đúng các tên file app đã tạo,
    và chỉ khi đó là file thường (không theo symlink).
    """
    removed = []
    legacyDir = os.path.join(tempfile.gettempdir(), APP_DIRNAME)
    for name in ('contacts_data.db', 'contacts_data.db-journal', 'settings.json'):
        path = os.path.join(legacyDir, name)
        try:
            if os.path.isfile(path) and not os.path.islink(path):
                os.remove(path)
                removed.append(path)
        except OSError:
            pass
    try:
        if os.path.isdir(legacyDir) and not os.path.islink(legacyDir) and not os.listdir(legacyDir):
            os.rmdir(legacyDir)
    except OSError:
        pass
    return removed
