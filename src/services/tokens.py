# -*- coding: utf-8 -*-
"""Đọc `.standards/tokens/design-tokens.json` - nguồn chân lý duy nhất cho màu/cỡ chữ/spacing.

CẤM hard-code màu, cỡ chữ, bo góc, spacing ở bất kỳ đâu trong `src/`
(AGENTS.md mục 6). Mọi giá trị giao diện phải lấy qua đối tượng `Tokens` này.
"""
import json
from functools import lru_cache

from src.utils.resource_path import resourcePath

# Token dùng thẳng bản sao chỉ-đọc của bộ quy ước (QU-STD-1) - không giữ bản sao riêng.
TOKENS_FILE = '.standards/tokens/design-tokens.json'
DEFAULT_THEME = 'light'


def _toPx(value) -> int:
    """'14px' → 14."""
    return int(str(value).replace('px', '').strip())


class Tokens:
    """Truy cập token theo chủ đề đang chọn (light | warm | dark)."""

    def __init__(self, data: dict, theme: str = DEFAULT_THEME):
        self._data = data
        self.theme = theme if theme in data['color'] else DEFAULT_THEME
        self._availableFamilies = None

    # --- Màu ---
    def color(self, name: str) -> str:
        """Ví dụ: color('primary'), color('text-muted'), color('danger')."""
        return self._data['color'][self.theme][name]

    # --- Kích thước ---
    def size(self, name: str) -> int:
        """Cỡ chữ theo px. Ví dụ: size('body-desktop') → 14."""
        return _toPx(self._data['typography']['font-size'][name])

    def space(self, step) -> int:
        """Spacing theo bậc 4px. Ví dụ: space(4) → 16."""
        return _toPx(self._data['spacing'][str(step)])

    def radius(self, name: str) -> int:
        return _toPx(self._data['radius'][name])

    def weight(self, name: str) -> str:
        """Quy đổi weight số của token sang từ khóa tkinter ('normal' | 'bold')."""
        return 'bold' if int(self._data['typography']['weight'][name]) >= 600 else 'normal'

    # --- Font cho tkinter ---
    def _families(self) -> set:
        if self._availableFamilies is None:
            try:
                from tkinter import font as tkFont
                self._availableFamilies = {f.lower() for f in tkFont.families()}
            except Exception:
                self._availableFamilies = set()
        return self._availableFamilies

    # Tên font generic của CSS - tkinter không hiểu, loại khỏi chuỗi fallback
    GENERIC_FAMILIES = {'system-ui', '-apple-system', 'sans-serif', 'serif', 'monospace'}

    def _pickFamily(self, key: str) -> str:
        """Chọn font đầu tiên trong chuỗi fallback của token mà hệ thống có sẵn."""
        candidates = [
            part.strip().strip("'\"")
            for part in self._data['typography'][key].split(',')
        ]
        candidates = [c for c in candidates if c.lower() not in self.GENERIC_FAMILIES]
        available = self._families()
        for name in candidates:
            if name.lower() in available:
                return name
        return candidates[-1]

    def font(self, sizeName: str = 'body-desktop', weightName: str = 'regular',
             mono: bool = False, slant: str = None, underline: bool = False) -> tuple:
        """Trả về tuple font tkinter. Cỡ chữ dùng số ÂM = đơn vị pixel (đúng token px)."""
        family = self._pickFamily('font-mono' if mono else 'font-family')
        spec = [family, -self.size(sizeName)]
        styles = []
        if self.weight(weightName) == 'bold':
            styles.append('bold')
        if slant:
            styles.append(slant)
        if underline:
            styles.append('underline')
        if styles:
            spec.append(' '.join(styles))
        return tuple(spec)


@lru_cache(maxsize=None)
def loadTokens(theme: str = DEFAULT_THEME) -> Tokens:
    """Nạp token 1 lần cho mỗi chủ đề (kết quả được cache)."""
    with open(resourcePath(TOKENS_FILE), 'r', encoding='utf-8') as f:
        return Tokens(json.load(f), theme)
