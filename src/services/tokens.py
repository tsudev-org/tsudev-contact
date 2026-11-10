# -*- coding: utf-8 -*-
"""Đọc token giao diện từ `.standards/tokens/design-tokens.json` - nguồn chân lý duy nhất -
cộng phần ghi đè màu riêng của repo ở `tokens/extensions.tsudev-contact.json` (bảng đen + tím của
hệ tsudev, phiếu logs/handover/20261110-05). Chỉ hai chế độ: light, dark (chế độ Ấm đã bỏ).

CẤM hard-code màu, cỡ chữ, bo góc, spacing trong `src/` (.standards/AGENTS.md).
Mọi giá trị giao diện lấy qua đối tượng `Tokens`. Module này thuần Python, không phụ
thuộc bộ công cụ giao diện nào.
"""
from __future__ import annotations

import json
from functools import cache

from src.utils.resource_path import resourcePath

TOKENS_FILE = '.standards/tokens/design-tokens.json'
EXTENSIONS_FILE = 'tokens/extensions.tsudev-contact.json'
THEMES = ('light', 'dark')
DEFAULT_THEME = 'dark'
GENERIC_FAMILIES = {'system-ui', '-apple-system', 'sans-serif', 'serif', 'monospace'}


def _toPx(value) -> int:
    return int(str(value).replace('px', '').strip())


class Tokens:
    """Truy cập token theo một chủ đề cụ thể (light | dark)."""

    def __init__(self, data: dict, theme: str = DEFAULT_THEME):
        self._data = data
        self.theme = theme if theme in data['color'] else DEFAULT_THEME

    def color(self, name: str) -> str:
        return self._data['color'][self.theme][name]

    def size(self, name: str) -> int:
        """Cỡ chữ theo px, ví dụ size('body-desktop') -> 14."""
        return _toPx(self._data['typography']['font-size'][name])

    def space(self, step) -> int:
        """Khoảng cách theo bậc 4px, ví dụ space(4) -> 16."""
        return _toPx(self._data['spacing'][str(step)])

    def radius(self, name: str) -> int:
        return _toPx(self._data['radius'][name])

    def weight(self, name: str) -> int:
        return int(self._data['typography']['weight'][name])

    def motionMs(self, name: str) -> int:
        return int(str(self._data['motion'][name]).replace('ms', ''))

    def families(self, mono: bool = False) -> list[str]:
        """Chuỗi font dự phòng của token, đã bỏ tên generic của CSS."""
        spec = self._data['typography']['font-mono' if mono else 'font-family']
        names = [part.strip().strip("'\"") for part in spec.split(',')]
        return [n for n in names if n.lower() not in GENERIC_FAMILIES]


@cache
def _loadData() -> dict:
    with open(resourcePath(TOKENS_FILE), encoding='utf-8') as f:
        data = json.load(f)
    with open(resourcePath(EXTENSIONS_FILE), encoding='utf-8') as f:
        extensions = json.load(f)
    colors = {}
    for theme in THEMES:
        base = data['color'][theme]
        override = extensions['color'][theme]
        unknown = set(override) - set(base)
        if unknown:   # sai tên vai trò thì ghi đè im lặng không có tác dụng: dừng sớm
            raise ValueError(f'{EXTENSIONS_FILE}: vai trò không có trong bảng chuẩn ({theme}): {sorted(unknown)}')
        colors[theme] = {**base, **override}
    data['color'] = colors
    return data


@cache
def loadTokens(theme: str = DEFAULT_THEME) -> Tokens:
    return Tokens(_loadData(), theme)
