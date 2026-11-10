# -*- coding: utf-8 -*-
"""Đọc file CSV người dùng chọn một cách phòng thủ.

Mọi file đầu vào là dữ liệu không tin cậy:
- Trần kích thước file, số dòng, số cột, độ dài một ô - chặn file độc làm cạn RAM.
- Tự nhận bảng mã (UTF-8 có/không BOM, UTF-16 có BOM, Windows-1258) và báo rõ đã dùng
  bảng mã nào. KHÔNG dùng `errors='ignore'` - bỏ lặng lẽ ký tự hỏng là mất dữ liệu.
- Tự nhận dấu phân cách (`,` `;` tab `|`) - Excel ở nhiều máy xuất CSV bằng `;`.
"""
from __future__ import annotations

import codecs
import csv
import io
import os
import unicodedata
from dataclasses import dataclass, field

MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 200
MAX_CELL_CHARS = 65_536
SNIFF_CHARS = 64 * 1024
DELIMITERS = ',;\t|'

ENCODING_LABELS = {
    'utf-8-sig': 'UTF-8 (có BOM)',
    'utf-8': 'UTF-8',
    'utf-16': 'UTF-16',
    'cp1258': 'Windows-1258 (tiếng Việt)',
}
DELIMITER_LABELS = {',': 'dấu phẩy', ';': 'dấu chấm phẩy', '\t': 'tab', '|': 'gạch đứng'}


class CsvError(Exception):
    """Lỗi đọc CSV có thông điệp tiếng Việt để hiển thị thẳng cho người dùng.

    `code` ổn định để giao diện tra bản dịch; `params` là tham số chèn vào thông điệp.
    """

    def __init__(self, code: str, message: str, **params):
        super().__init__(message)
        self.code = code
        self.params = params


@dataclass
class CsvData:
    path: str
    encoding: str
    delimiter: str
    headers: list[str]
    rows: list[list[str]] = field(repr=False)
    # Số dòng thật trong file (dòng tiêu đề = 1) của từng bản ghi - để người dùng mở file
    # ra đúng chỗ, kể cả khi file có dòng trống xen giữa hay ô nhiều dòng.
    lineNumbers: list[int] = field(default_factory=list, repr=False)

    @property
    def rowCount(self) -> int:
        return len(self.rows)

    def sampleValue(self, header: str) -> str:
        """Giá trị khác rỗng đầu tiên của một cột - để người dùng nhận ra cột khi ghép."""
        try:
            index = self.headers.index(header)
        except ValueError:
            return ''
        for row in self.rows[:50]:
            if index < len(row) and row[index].strip():
                return row[index].strip()
        return ''


def _decode(raw: bytes) -> tuple[str, str]:
    if raw.startswith(codecs.BOM_UTF8):
        return raw.decode('utf-8-sig'), 'utf-8-sig'
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        try:
            return raw.decode('utf-16'), 'utf-16'
        except UnicodeDecodeError as exc:
            raise CsvError('bad_encoding', 'File có dấu UTF-16 nhưng nội dung hỏng.') from exc
    try:
        return raw.decode('utf-8'), 'utf-8'
    except UnicodeDecodeError:
        pass
    try:
        # Excel trên Windows tiếng Việt lưu "CSV" theo bảng mã ANSI = Windows-1258.
        return raw.decode('cp1258'), 'cp1258'
    except UnicodeDecodeError as exc:
        raise CsvError('bad_encoding',
                       'Không nhận được bảng mã của file. Hãy lưu lại file dưới dạng "CSV UTF-8".') from exc


def _sniffDelimiter(text: str) -> str:
    sample = text[:SNIFF_CHARS]
    try:
        return csv.Sniffer().sniff(sample, delimiters=DELIMITERS).delimiter
    except csv.Error:
        firstLine = sample.split('\n', 1)[0]
        counts = {d: firstLine.count(d) for d in DELIMITERS}
        best = max(counts, key=counts.get)
        return best if counts[best] else ','


def readCsv(path: str) -> CsvData:
    """Đọc toàn bộ CSV vào bộ nhớ sau khi đã qua mọi trần an toàn."""
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        raise CsvError('unreadable', f'Không mở được file: {exc.strerror or exc}') from exc
    if size == 0:
        raise CsvError('empty', 'File CSV rỗng.')
    if size > MAX_FILE_BYTES:
        sizeMb, limitMb = size // (1024 * 1024), MAX_FILE_BYTES // (1024 * 1024)
        raise CsvError('too_large', f'File quá lớn ({sizeMb} MB). Giới hạn {limitMb} MB.',
                       sizeMb=sizeMb, limitMb=limitMb)
    try:
        with open(path, 'rb') as f:
            raw = f.read(MAX_FILE_BYTES + 1)
    except OSError as exc:
        raise CsvError('unreadable', f'Không mở được file: {exc.strerror or exc}') from exc
    if b'\x00' in raw[:4096] and not raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        raise CsvError('binary', 'File không phải văn bản CSV (có vẻ là file nhị phân, ví dụ .xlsx đổi đuôi).')

    text, encoding = _decode(raw)
    delimiter = _sniffDelimiter(text)

    previousLimit = csv.field_size_limit()
    csv.field_size_limit(MAX_CELL_CHARS)
    try:
        reader = csv.reader(io.StringIO(text, newline=''), delimiter=delimiter, strict=False)
        headers: list[str] | None = None
        rows: list[list[str]] = []
        lineNumbers: list[int] = []
        startLine = 1
        for record in reader:
            recordLine, startLine = startLine, reader.line_num + 1
            if headers is None:
                headers = [unicodedata.normalize('NFC', h).strip() for h in record]
                continue
            if not any(cell.strip() for cell in record):
                continue
            if len(rows) >= MAX_ROWS:
                raise CsvError('too_many_rows', f'File có hơn {MAX_ROWS} dòng dữ liệu - hãy chia nhỏ file.',
                               limit=MAX_ROWS)
            rows.append(record)
            lineNumbers.append(recordLine)
    except csv.Error as exc:
        raise CsvError('malformed', f'File CSV sai cấu trúc (dòng {reader.line_num}): {exc}',
                       line=reader.line_num) from exc
    finally:
        csv.field_size_limit(previousLimit)

    if not headers or not any(headers):
        raise CsvError('no_header', 'Không tìm thấy dòng tiêu đề (tên cột) ở đầu file.')
    if len(headers) > MAX_COLUMNS:
        raise CsvError('too_many_columns', f'File có {len(headers)} cột, vượt giới hạn {MAX_COLUMNS}.',
                       count=len(headers), limit=MAX_COLUMNS)
    headers = _dedupeHeaders(headers)
    if not rows:
        raise CsvError('no_rows', 'File CSV chỉ có dòng tiêu đề, không có dữ liệu.')
    return CsvData(path=path, encoding=encoding, delimiter=delimiter, headers=headers, rows=rows,
                   lineNumbers=lineNumbers)


def _dedupeHeaders(headers: list[str]) -> list[str]:
    """Cột trùng tên hoặc rỗng vẫn phải chọn được riêng: đặt tên 'Cột 3', 'Tên (2)'..."""
    seen: dict[str, int] = {}
    result = []
    for i, header in enumerate(headers, start=1):
        name = header or f'Cột {i}'
        if name in seen:
            seen[name] += 1
            name = f'{name} ({seen[name]})'
        else:
            seen[name] = 1
        result.append(name)
    return result
