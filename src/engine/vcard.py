# -*- coding: utf-8 -*-
"""Dựng và ghi file vCard 3.0 (RFC 2426) theo cách KHÔNG thể bị chèn.

Lỗ hổng cũ (đã tái hiện 10/11/2026): ô Tên chứa xuống dòng sinh được nguyên một
liên hệ giả trong file .vcf. Ở đây mọi giá trị đi qua `escapeValue` - thoát `\\`, `;`,
`,` và xuống dòng theo RFC 6350 mục 3.4 - rồi dòng dài được gập theo mục 3.2, nên
mỗi giá trị luôn nằm gọn trong đúng một thuộc tính.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Callable, Iterable
from datetime import UTC, datetime

from src.engine.validate import ContactRecord

CRLF = '\r\n'
MAX_LINE_OCTETS = 75


def escapeValue(value: str) -> str:
    """Thoát ký tự đặc biệt của vCard. Thứ tự quan trọng: `\\` phải thoát trước tiên."""
    return (value.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,')
            .replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n'))


def foldLine(line: str) -> str:
    """Gập dòng dài hơn 75 octet; không cắt ngang giữa một ký tự UTF-8 nhiều byte."""
    if len(line.encode('utf-8')) <= MAX_LINE_OCTETS:
        return line
    parts: list[str] = []
    current, currentBytes, limit = [], 0, MAX_LINE_OCTETS
    for ch in line:
        size = len(ch.encode('utf-8'))
        if currentBytes + size > limit:
            parts.append(''.join(current))
            current, currentBytes, limit = [], 0, MAX_LINE_OCTETS - 1  # chừa 1 octet cho dấu cách đầu dòng
        current.append(ch)
        currentBytes += size
    parts.append(''.join(current))
    return (CRLF + ' ').join(parts)


def buildVcard(record: ContactRecord, revision: str) -> str:
    """Dựng một khối vCard. `revision` là dấu thời gian UTC dạng 20261110T120000Z."""
    v = record.values
    name = escapeValue(v['name'])
    lines = [
        'BEGIN:VCARD',
        'VERSION:3.0',
        f'FN:{name}',
        # N bắt buộc ở vCard 3.0. Đặt cả họ tên vào phần "tên" để mọi điện thoại hiển thị
        # đúng nguyên chuỗi tiếng Việt, không tự đảo thành "A Văn Nguyễn".
        f'N:;{name};;;',
    ]
    for index, phone in enumerate(record.phones):
        prefix = 'TEL;TYPE=CELL,PREF' if index == 0 else 'TEL;TYPE=CELL'
        lines.append(f'{prefix}:{escapeValue(phone)}')
    for email in record.emails:
        lines.append(f'EMAIL;TYPE=INTERNET:{escapeValue(email)}')
    if v['organization']:
        lines.append(f"ORG:{escapeValue(v['organization'])}")
    if v['title']:
        lines.append(f"TITLE:{escapeValue(v['title'])}")
    if v['address']:
        lines.append(f"ADR;TYPE=HOME:;;{escapeValue(v['address'])};;;;")
    if record.birthday:
        lines.append(f'BDAY:{record.birthday}')
    if v['notes']:
        lines.append(f"NOTE:{escapeValue(v['notes'])}")
    lines.append(f'REV:{revision}')
    lines.append('END:VCARD')
    return ''.join(foldLine(line) + CRLF for line in lines)


def utcRevision(now: datetime | None = None) -> str:
    """Dấu thời gian REV theo UTC thật (bản cũ lấy giờ máy rồi gắn chữ Z - sai 7 giờ)."""
    return (now or datetime.now(UTC)).astimezone(UTC).strftime('%Y%m%dT%H%M%SZ')


def writeVcf(records: Iterable[ContactRecord], path: str,
             onProgress: Callable[[int], None] | None = None) -> int:
    """Ghi file .vcf nguyên tử: ghi ra file tạm cùng thư mục rồi đổi tên.

    Đang ghi mà lỗi (đĩa đầy, bị hủy) thì file đích cũ còn nguyên, không để lại file dở.
    """
    revision = utcRevision()
    directory = os.path.dirname(os.path.abspath(path))
    fd, tempPath = tempfile.mkstemp(prefix='.tsudev-contact-', suffix='.tmp', dir=directory)
    count = 0
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            for record in records:
                f.write(buildVcard(record, revision))
                count += 1
                if onProgress:
                    onProgress(count)
        os.replace(tempPath, path)
    except BaseException:
        try:
            os.unlink(tempPath)
        except OSError:
            pass
        raise
    return count
