# -*- coding: utf-8 -*-
"""Đa ngôn ngữ tối giản: tiếng Việt là mặc định và là nguồn chuẩn; tiếng Anh là bản dịch.

Dùng: `tr('key', n=3)`. Khóa thiếu ở bản dịch -> rơi về tiếng Việt; thiếu cả ở tiếng
Việt -> trả chính khóa (test `tests/test_i18n.py` chặn trường hợp này).
"""
from __future__ import annotations

from src.i18n import en, vi

DEFAULT_LANGUAGE = 'vi'
CATALOGS = {'vi': vi.STRINGS, 'en': en.STRINGS}
LANGUAGE_NAMES = {'vi': 'Tiếng Việt', 'en': 'English'}

_current = DEFAULT_LANGUAGE


def setLanguage(code: str) -> None:
    global _current
    _current = code if code in CATALOGS else DEFAULT_LANGUAGE


def language() -> str:
    return _current


def tr(key: str, **params) -> str:
    text = CATALOGS[_current].get(key) or vi.STRINGS.get(key) or key
    if params:
        try:
            return text.format(**params)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def formatNumber(value: int) -> str:
    """Dấu phân cách hàng nghìn: 1.128 (tiếng Việt), 1,128 (tiếng Anh)."""
    text = f'{value:,}'
    return text.replace(',', '.') if _current == 'vi' else text


def describeIssue(issue) -> str:
    """Một vấn đề (src/engine/validate.Issue) -> câu đọc được theo ngôn ngữ hiện tại."""
    params = dict(issue.params)
    if issue.field:
        params.setdefault('field', tr(f'field.{issue.field}'))
    return tr(f'issue.{issue.code}', **params)


def describeIssues(record) -> str:
    return '; '.join(describeIssue(i) for i in record.issues)
