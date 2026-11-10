# -*- coding: utf-8 -*-
"""Danh mục trường vCard hỗ trợ và cách đoán cột CSV tương ứng."""
from __future__ import annotations

from src.engine.text import normalizeHeaderKey

# Thứ tự ở đây là thứ tự hiển thị trên giao diện và trong bảng xem trước.
FIELDS = ('name', 'number', 'email', 'organization', 'title', 'address', 'birthday', 'notes')
REQUIRED_FIELDS = ('name', 'number')

# Trần độ dài từng trường (ký tự) - chặn ô dữ liệu khổng lồ làm treo app hoặc điện thoại.
MAX_LENGTH = {
    'name': 200, 'number': 200, 'email': 320, 'organization': 300, 'title': 200,
    'address': 500, 'birthday': 40, 'notes': 4000,
}
MULTILINE_FIELDS = ('address', 'notes')

# Tên cột thường gặp (Google Contacts, Outlook, Excel tiếng Việt), đã chuẩn hóa bằng
# normalizeHeaderKey. Khớp nguyên tên trước, rồi mới khớp một phần.
FIELD_ALIASES = {
    'name': ('name', 'ten', 'hoten', 'hovaten', 'fullname', 'displayname', 'contactname', 'tenlienhe'),
    'number': ('number', 'phone', 'sdt', 'sodienthoai', 'dienthoai', 'didong', 'mobile', 'tel', 'cell'),
    'email': ('email', 'mail', 'thudientu'),
    'organization': ('organization', 'org', 'company', 'congty', 'tochuc', 'donvi', 'coquan'),
    'title': ('title', 'jobtitle', 'chucvu', 'chucdanh', 'position'),
    'address': ('address', 'diachi', 'addr'),
    'birthday': ('birthday', 'bday', 'ngaysinh', 'dob', 'birthdate'),
    'notes': ('notes', 'note', 'ghichu', 'comment', 'mota'),
}


def guessMapping(headers: list[str]) -> dict[str, str | None]:
    """Đoán cột CSV cho từng trường. Không đoán được -> None. Một cột chỉ gán cho một trường."""
    keyed = [(h, normalizeHeaderKey(h)) for h in headers]
    used: set[str] = set()
    result: dict[str, str | None] = {}
    for field in FIELDS:
        result[field] = _guessOne(field, keyed, used)
        if result[field]:
            used.add(result[field])
    return result


def _guessOne(field: str, keyed: list[tuple[str, str]], used: set[str]) -> str | None:
    aliases = FIELD_ALIASES.get(field, (field,))
    for alias in aliases:
        for original, key in keyed:
            if key == alias and original not in used:
                return original
    for alias in aliases:
        if len(alias) < 3:  # 'org', 'sdt'... khớp một phần với chuỗi ngắn quá dễ nhầm
            continue
        for original, key in keyed:
            if alias in key and original not in used:
                return original
    return None
