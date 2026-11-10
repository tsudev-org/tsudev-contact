# -*- coding: utf-8 -*-
"""Kiểm tra và chuẩn hóa từng liên hệ trước khi xuất vCard.

Mỗi dòng CSV thành một `ContactRecord` mang trạng thái:
- `ok`      hợp lệ, xuất bình thường;
- `warning` vẫn xuất, nhưng có trường bị bỏ/sửa (email sai, ngày sinh sai, cắt bớt...);
- `error`   KHÔNG xuất (thiếu Tên hoặc không có SĐT hợp lệ).
Thông điệp lỗi là mã ổn định + tham số, giao diện tự dịch (src/i18n).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field as dataField
from datetime import date, timedelta

from src.engine.fields import FIELDS, MAX_LENGTH, MULTILINE_FIELDS
from src.engine.text import sanitizeField, viNormalizeText

STATUS_OK, STATUS_WARNING, STATUS_ERROR = 'ok', 'warning', 'error'

_PHONE_SPLIT = re.compile(r'[/;,|\n]+|\s{2,}|\s+(?:hoặc|hoac|or)\s+', re.IGNORECASE)
_PHONE_ALLOWED = re.compile(r'^\+?[\d\s().\-]+$')
_EMAIL = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
                    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")
_EMAIL_SPLIT = re.compile(r'[;,\s]+')
_DATE_DMY = re.compile(r'^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})$')
_DATE_YMD = re.compile(r'^(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})$')
MIN_PHONE_DIGITS, MAX_PHONE_DIGITS = 3, 15
MAX_PHONES = 5
MAX_EMAILS = 3
EXCEL_EPOCH = date(1899, 12, 30)


@dataclass
class Issue:
    code: str
    field: str = ''
    params: dict = dataField(default_factory=dict)
    isError: bool = False


@dataclass
class ContactRecord:
    rowNumber: int                     # số dòng trong file CSV (tính cả dòng tiêu đề)
    values: dict[str, str]             # giá trị hiển thị đã làm sạch
    phones: list[str] = dataField(default_factory=list)
    emails: list[str] = dataField(default_factory=list)
    birthday: str = ''                 # YYYY-MM-DD hoặc --MM-DD (không năm)
    issues: list[Issue] = dataField(default_factory=list)
    searchKey: str = ''

    @property
    def status(self) -> str:
        if any(i.isError for i in self.issues):
            return STATUS_ERROR
        return STATUS_WARNING if self.issues else STATUS_OK


@dataclass
class ValidationOptions:
    fixLeadingZero: bool = True        # Excel hay làm mất số 0 đầu: 912345678 -> 0912345678
    dropDuplicatePhones: bool = False  # liên hệ trùng SĐT với dòng trước -> không xuất


def normalizePhone(raw: str, fixLeadingZero: bool = True) -> tuple[str | None, str | None]:
    """Chuẩn hóa 1 số điện thoại. Trả về (số, mã_cảnh_báo) hoặc (None, mã_lỗi)."""
    candidate = raw.strip()
    if not candidate:
        return None, None
    if not any(ch.isdigit() for ch in candidate):
        return None, 'phone_no_digits'     # ô SĐT chứa chữ (chức danh, tên...) - thường do lệch cột
    if not _PHONE_ALLOWED.match(candidate):
        return None, 'phone_invalid_chars'
    hasPlus = candidate.startswith('+')
    digits = re.sub(r'\D', '', candidate)
    if digits.startswith('00') and not hasPlus:
        digits, hasPlus = digits[2:], True
    if not MIN_PHONE_DIGITS <= len(digits) <= MAX_PHONE_DIGITS:
        return None, 'phone_bad_length'
    warning = None
    if hasPlus:
        return '+' + digits, None
    if digits.startswith('84') and len(digits) == 11:
        return '+' + digits, None
    if fixLeadingZero and len(digits) == 9 and digits[0] in '35789':
        digits, warning = '0' + digits, 'phone_leading_zero_added'
    return digits, warning


def parseBirthday(raw: str) -> str | None:
    """Ngày sinh -> chuỗi vCard. Nhận DD/MM/YYYY, D-M-YYYY, YYYY-MM-DD, số ngày kiểu Excel."""
    text = raw.strip()
    if not text:
        return None
    try:
        if m := _DATE_DMY.match(text):
            return date(int(m[3]), int(m[2]), int(m[1])).isoformat()
        if m := _DATE_YMD.match(text):
            return date(int(m[1]), int(m[2]), int(m[3])).isoformat()
        if text.isdigit() and 1 <= int(text) <= 80_000:
            return (EXCEL_EPOCH + timedelta(days=int(text))).isoformat()
    except ValueError:
        return None
    return None


def buildRecord(rowNumber: int, raw: dict[str, str], options: ValidationOptions) -> ContactRecord:
    """Dựng một ContactRecord từ các ô CSV đã ghép theo trường."""
    issues: list[Issue] = []
    values: dict[str, str] = {}
    for name in FIELDS:
        clean, truncated = sanitizeField(raw.get(name), allowNewlines=name in MULTILINE_FIELDS,
                                         maxLength=MAX_LENGTH[name])
        values[name] = clean
        if truncated:
            issues.append(Issue('field_truncated', name, {'limit': MAX_LENGTH[name]}))

    if not values['name']:
        issues.append(Issue('name_missing', 'name', isError=True))

    phones: list[str] = []
    phoneIssue: str | None = None
    for part in _PHONE_SPLIT.split(values['number']):
        phone, code = normalizePhone(part, options.fixLeadingZero)
        if phone and phone not in phones:
            phones.append(phone)
        if code:
            if phone:
                issues.append(Issue(code, 'number', {'value': phone}))
            else:
                phoneIssue = code
    if len(phones) > MAX_PHONES:
        phones = phones[:MAX_PHONES]
        issues.append(Issue('phone_too_many', 'number', {'limit': MAX_PHONES}))
    if not phones:
        issues.append(Issue(phoneIssue or 'phone_missing', 'number', isError=True))
    elif phoneIssue:
        issues.append(Issue('phone_part_dropped', 'number'))

    emails: list[str] = []
    for part in _EMAIL_SPLIT.split(values['email']):
        if not part:
            continue
        if _EMAIL.match(part) and len(part) <= 254:
            if part.lower() not in (e.lower() for e in emails):
                emails.append(part)
        else:
            issues.append(Issue('email_invalid', 'email', {'value': part}))
    if len(emails) > MAX_EMAILS:
        emails = emails[:MAX_EMAILS]
        issues.append(Issue('email_too_many', 'email', {'limit': MAX_EMAILS}))

    birthday = ''
    if values['birthday']:
        parsed = parseBirthday(values['birthday'])
        if parsed and parsed <= date.today().isoformat() and parsed >= '1900-01-01':
            birthday = parsed
        else:
            issues.append(Issue('birthday_invalid', 'birthday', {'value': values['birthday']}))

    record = ContactRecord(rowNumber=rowNumber, values=values, phones=phones, emails=emails,
                           birthday=birthday, issues=issues)
    record.searchKey = viNormalizeText(' '.join([values['name'], values['organization'], values['title'],
                                                 ' '.join(phones), ' '.join(emails)]))
    return record


def markDuplicates(records: list[ContactRecord], options: ValidationOptions) -> int:
    """Đánh dấu liên hệ trùng SĐT với một dòng trước đó. Trả về số dòng trùng."""
    firstSeen: dict[str, int] = {}
    duplicates = 0
    for record in records:
        if record.status == STATUS_ERROR:
            continue
        keys = [_phoneKey(p) for p in record.phones]
        clash = next((firstSeen[k] for k in keys if k in firstSeen), None)
        if clash is not None:
            duplicates += 1
            record.issues.append(Issue('duplicate_phone', 'number', {'row': clash},
                                       isError=options.dropDuplicatePhones))
        for key in keys:
            firstSeen.setdefault(key, record.rowNumber)
    return duplicates


def _phoneKey(phone: str) -> str:
    """+84912... và 0912... là cùng một số."""
    if phone.startswith('+84'):
        return '0' + phone[3:]
    return phone
