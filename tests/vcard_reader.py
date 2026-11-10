# -*- coding: utf-8 -*-
"""Bộ đọc vCard tối giản, CHỈ dùng trong test - độc lập với bộ ghi để kiểm chéo.

Làm đúng các bước một điện thoại làm: bỏ gập dòng (RFC 6350 mục 3.2), tách thẻ theo
BEGIN/END, tách tên thuộc tính tại dấu ':' đầu tiên, giải thoát giá trị.
"""
from __future__ import annotations


def _unescape(value: str) -> str:
    out, i = [], 0
    while i < len(value):
        ch = value[i]
        if ch == '\\' and i + 1 < len(value):
            nxt = value[i + 1]
            out.append('\n' if nxt in 'nN' else nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _splitUnescaped(value: str, sep: str) -> list[str]:
    parts, current, i = [], [], 0
    while i < len(value):
        if value[i] == '\\' and i + 1 < len(value):
            current.append(value[i:i + 2])
            i += 2
            continue
        if value[i] == sep:
            parts.append(''.join(current))
            current = []
        else:
            current.append(value[i])
        i += 1
    parts.append(''.join(current))
    return parts


def parseVcards(text: str) -> list[list[tuple[str, str, str]]]:
    """-> danh sách thẻ; mỗi thẻ là [(TÊN, tham số, giá trị đã giải thoát)]."""
    assert '\n' not in text.replace('\r\n', ''), 'xuống dòng trần (không CRLF)'
    unfolded = text.replace('\r\n ', '').replace('\r\n\t', '')
    cards, current = [], None
    for line in unfolded.split('\r\n'):
        if not line:
            continue
        head, _, value = line.partition(':')
        name, _, params = head.partition(';')
        name = name.upper()
        if name == 'BEGIN' and value.upper() == 'VCARD':
            assert current is None, 'BEGIN lồng trong thẻ khác'
            current = []
        elif name == 'END' and value.upper() == 'VCARD':
            assert current is not None
            cards.append(current)
            current = None
        else:
            assert current is not None, f'dòng nằm ngoài thẻ: {line!r}'
            if name in ('N', 'ADR'):
                parts = [_unescape(p) for p in _splitUnescaped(value, ';')]
                current.append((name, params, ';'.join(parts)))
            else:
                current.append((name, params, _unescape(value)))
    assert current is None, 'thẻ chưa đóng'
    return cards
