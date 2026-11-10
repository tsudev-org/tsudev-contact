# -*- coding: utf-8 -*-
"""Luồng xử lý trọn vẹn: CSV đã đọc + bảng ghép cột -> danh sách liên hệ đã kiểm -> .vcf.

Không phụ thuộc giao diện. Giao diện chạy các hàm này ở thread nền và nhận tiến trình
qua callback; `CancelToken` cho phép người dùng hủy giữa chừng.
"""
from __future__ import annotations

import csv
import os
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass

from src.engine.csv_source import CsvData
from src.engine.fields import FIELDS, REQUIRED_FIELDS
from src.engine.validate import (
    STATUS_ERROR,
    STATUS_OK,
    STATUS_WARNING,
    ContactRecord,
    ValidationOptions,
    buildRecord,
    markDuplicates,
)
from src.engine.vcard import writeVcf

ProgressFn = Callable[[int, int], None]


class Cancelled(Exception):
    """Người dùng đã bấm Hủy."""


class CancelToken:
    def __init__(self):
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def isCancelled(self) -> bool:
        return self._event.is_set()

    def check(self) -> None:
        if self._event.is_set():
            raise Cancelled()


@dataclass
class ValidationSummary:
    total: int
    ok: int
    warning: int
    error: int
    duplicates: int

    @property
    def exportable(self) -> int:
        return self.ok + self.warning


class MappingError(ValueError):
    def __init__(self, code: str, **params):
        super().__init__(code)
        self.code = code
        self.params = params


def checkMapping(mapping: dict[str, str | None], headers: list[str]) -> None:
    """Bảng ghép phải có đủ trường bắt buộc và chỉ trỏ tới cột có thật."""
    for name in REQUIRED_FIELDS:
        if not mapping.get(name):
            raise MappingError('required_missing', field=name)
    for name, header in mapping.items():
        if name not in FIELDS:
            raise MappingError('unknown_field', field=name)
        if header and header not in headers:
            raise MappingError('unknown_column', column=header)


def validateRows(data: CsvData, mapping: dict[str, str | None], options: ValidationOptions,
                 onProgress: ProgressFn | None = None,
                 cancel: CancelToken | None = None) -> tuple[list[ContactRecord], ValidationSummary]:
    checkMapping(mapping, data.headers)
    indexOf = {name: data.headers.index(h) for name, h in mapping.items() if h}
    records: list[ContactRecord] = []
    total = data.rowCount
    for i, row in enumerate(data.rows):
        if cancel and i % 500 == 0:
            cancel.check()
        raw = {name: (row[idx] if idx < len(row) else '') for name, idx in indexOf.items()}
        records.append(buildRecord(data.lineNumbers[i], raw, options))
        if onProgress and (i % 200 == 0 or i + 1 == total):
            onProgress(i + 1, total)
    duplicates = markDuplicates(records, options)
    counts = {STATUS_OK: 0, STATUS_WARNING: 0, STATUS_ERROR: 0}
    for record in records:
        counts[record.status] += 1
    return records, ValidationSummary(total=total, ok=counts[STATUS_OK], warning=counts[STATUS_WARNING],
                                      error=counts[STATUS_ERROR], duplicates=duplicates)


def exportVcf(records: list[ContactRecord], path: str, sourcePath: str | None = None,
              onProgress: ProgressFn | None = None, cancel: CancelToken | None = None) -> int:
    """Ghi các liên hệ không lỗi ra .vcf. Trả về số liên hệ đã ghi."""
    if sourcePath and os.path.abspath(path) == os.path.abspath(sourcePath):
        raise ValueError('same_as_source')
    exportable = [r for r in records if r.status != STATUS_ERROR]
    total = len(exportable)

    def progress(count: int) -> None:
        if cancel and count % 500 == 0:
            cancel.check()
        if onProgress and (count % 200 == 0 or count == total):
            onProgress(count, total)

    return writeVcf(exportable, path, progress)


# Ký tự mở đầu khiến Excel/LibreOffice hiểu ô là công thức (CSV injection, OWASP).
_FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r', '＝', '＋', '－', '＠')


def csvSafe(value: str) -> str:
    """Vô hiệu hóa công thức trong ô CSV xuất ra bằng cách thêm dấu nháy đơn phía trước."""
    return "'" + value if value.startswith(_FORMULA_PREFIXES) else value


def exportIssueReport(records: list[ContactRecord], path: str,
                      describe: Callable[[ContactRecord], str], fieldLabels: dict[str, str],
                      statusLabels: dict[str, str]) -> int:
    """Ghi báo cáo các dòng có cảnh báo/lỗi ra CSV UTF-8 có BOM (Excel mở đúng tiếng Việt)."""
    rows = [r for r in records if r.issues]
    directory = os.path.dirname(os.path.abspath(path))
    fd, tempPath = tempfile.mkstemp(prefix='.tsudev-contact-', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([fieldLabels['row'], fieldLabels['status'], fieldLabels['issues'],
                             *(fieldLabels[name] for name in FIELDS)])
            for r in rows:
                writer.writerow([r.rowNumber, statusLabels[r.status], csvSafe(describe(r)),
                                 *(csvSafe(r.values[name]) for name in FIELDS)])
        os.replace(tempPath, path)
    except BaseException:
        try:
            os.unlink(tempPath)
        except OSError:
            pass
        raise
    return len(rows)
