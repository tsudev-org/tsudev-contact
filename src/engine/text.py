# -*- coding: utf-8 -*-
"""Xử lý chuỗi dùng chung: làm sạch dữ liệu đầu vào và chuẩn hóa tiếng Việt để so khớp.

Module DUY NHẤT chứa hai hàm bỏ dấu / chuẩn hóa (.standards/docs/SEARCH_AND_FILTER.md mục 3.2).
Nơi khác MUST nhập từ đây, không viết lặp.
"""
from __future__ import annotations

import re
import unicodedata

# Ký tự điều khiển hướng chữ (Trojan Source) và ký tự vô hình hay dùng để giả mạo tên:
# "Nguyễn Văn A" và "Nguyễn​Văn A" trông y hệt nhưng là hai liên hệ khác nhau.
_INVISIBLE = dict.fromkeys(map(ord, (
    '​', '‌', '‍', '⁠', '﻿', '­',
    '‪', '‫', '‬', '‭', '‮',
    '⁦', '⁧', '⁨', '⁩', '‎', '‏', '؜',
)))
_WHITESPACE_RUN = re.compile(r'[ \t  - 　]+')


def _isControl(ch: str) -> bool:
    return unicodedata.category(ch) == 'Cc'


def sanitizeField(value: object, *, allowNewlines: bool = False, maxLength: int = 0) -> tuple[str, bool]:
    """Làm sạch một ô dữ liệu. Trả về (chuỗi sạch, có_bị_cắt_bớt).

    - Chuẩn hóa Unicode NFC (hai cách gõ dấu tiếng Việt về một).
    - Bỏ ký tự điều khiển C0/C1 và ký tự vô hình/đảo chiều chữ.
    - Gộp khoảng trắng, bỏ khoảng trắng đầu/cuối.
    - `allowNewlines`: giữ xuống dòng (chuẩn hóa về `\n`), dùng cho Ghi chú/Địa chỉ.
    - `maxLength > 0`: cắt bớt phần vượt trần để chặn ô dữ liệu khổng lồ.
    """
    if value is None:
        return '', False
    text = unicodedata.normalize('NFC', str(value)).translate(_INVISIBLE)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = []
    for line in text.split('\n'):
        cleaned = ''.join(' ' if ch == '\t' else ch for ch in line if ch == '\t' or not _isControl(ch))
        lines.append(_WHITESPACE_RUN.sub(' ', cleaned).strip())
    text = ('\n' if allowNewlines else ' ').join(line for line in lines if line)
    truncated = bool(maxLength) and len(text) > maxLength
    if truncated:
        text = text[:maxLength].rstrip()
    return text, truncated


def viRemoveDiacritics(text: str) -> str:
    """Bỏ dấu tiếng Việt. Xử lý riêng đ/Đ vì NFD không tách được hai ký tự này."""
    decomposed = unicodedata.normalize('NFD', text)
    stripped = ''.join(ch for ch in decomposed if not unicodedata.combining(ch))
    return stripped.replace('đ', 'd').replace('Đ', 'D')


def viNormalizeText(text: str) -> str:
    """Chuẩn hóa để so khớp: NFC -> chữ thường -> bỏ dấu -> gộp khoảng trắng."""
    normalized = viRemoveDiacritics(unicodedata.normalize('NFC', text).lower())
    return ' '.join(normalized.split())


def normalizeHeaderKey(header: str) -> str:
    """Khóa so khớp tên cột: như viNormalizeText nhưng bỏ cả khoảng trắng và dấu câu."""
    return ''.join(ch for ch in viNormalizeText(header) if ch.isalnum())
