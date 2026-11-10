# -*- coding: utf-8 -*-
"""Đọc CSV phòng thủ, làm sạch dữ liệu, kiểm tra từng trường, đoán cột."""
from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.engine import csv_source
from src.engine.csv_source import CsvError, readCsv
from src.engine.fields import guessMapping
from src.engine.text import sanitizeField, viNormalizeText, viRemoveDiacritics
from src.engine.validate import (
    STATUS_ERROR,
    STATUS_OK,
    STATUS_WARNING,
    ValidationOptions,
    buildRecord,
    markDuplicates,
    normalizePhone,
    parseBirthday,
)


def write(tmp_path, content: bytes, name='danh-ba.csv'):
    path = tmp_path / name
    path.write_bytes(content)
    return str(path)


# ----------------------------------------------------------------- đọc CSV
@pytest.mark.parametrize('encoding,expected', [
    ('utf-8-sig', 'utf-8-sig'), ('utf-8', 'utf-8'), ('utf-16', 'utf-16'), ('cp1258', 'cp1258'),
])
def test_nhan_bang_ma(tmp_path, encoding, expected):
    text = 'Tên,SĐT\r\nLê Bích,0912345678\r\n'
    data = readCsv(write(tmp_path, text.encode(encoding)))
    assert data.encoding == expected
    assert data.headers == ['Tên', 'SĐT']
    assert data.rows[0][0] == 'Lê Bích'


@pytest.mark.parametrize('delimiter', [',', ';', '\t', '|'])
def test_nhan_dau_phan_cach(tmp_path, delimiter):
    text = delimiter.join(['Tên', 'SĐT', 'Ghi chú']) + '\n' + delimiter.join(['A', '0912345678', 'x']) + '\n'
    data = readCsv(write(tmp_path, text.encode('utf-8')))
    assert data.delimiter == delimiter
    assert data.rows == [['A', '0912345678', 'x']]


def test_so_dong_that_bo_qua_dong_trong_va_o_nhieu_dong(tmp_path):
    text = 'Tên,Ghi chú\n\nA,"dòng 1\ndòng 2"\n\nB,x\n'
    data = readCsv(write(tmp_path, text.encode('utf-8')))
    assert data.lineNumbers == [3, 6]


def test_tu_choi_file_nhi_phan(tmp_path):
    with pytest.raises(CsvError) as info:
        readCsv(write(tmp_path, b'PK\x03\x04\x00\x00\x00binary'))
    assert info.value.code == 'binary'


def test_tu_choi_file_qua_lon(tmp_path, monkeypatch):
    monkeypatch.setattr(csv_source, 'MAX_FILE_BYTES', 10)
    with pytest.raises(CsvError) as info:
        readCsv(write(tmp_path, b'a,b\n1,2\n3,4\n'))
    assert info.value.code == 'too_large'


def test_tu_choi_qua_nhieu_dong(tmp_path, monkeypatch):
    monkeypatch.setattr(csv_source, 'MAX_ROWS', 2)
    with pytest.raises(CsvError) as info:
        readCsv(write(tmp_path, b'a\n1\n2\n3\n'))
    assert info.value.code == 'too_many_rows'


def test_tu_choi_o_khong_lo(tmp_path, monkeypatch):
    monkeypatch.setattr(csv_source, 'MAX_CELL_CHARS', 100)
    with pytest.raises(CsvError) as info:
        readCsv(write(tmp_path, b'a,b\n"' + b'x' * 500 + b'",1\n'))
    assert info.value.code == 'malformed'


@pytest.mark.parametrize('content,code', [(b'', 'empty'), (b'Ten,SDT\n', 'no_rows')])
def test_file_rong(tmp_path, content, code):
    with pytest.raises(CsvError) as info:
        readCsv(write(tmp_path, content))
    assert info.value.code == code


def test_cot_trung_ten_hoac_rong_van_phan_biet(tmp_path):
    data = readCsv(write(tmp_path, 'Tên,,Tên\nA,b,c\n'.encode()))
    assert data.headers == ['Tên', 'Cột 2', 'Tên (2)']


@given(st.binary(max_size=2000))
def test_tinh_chat_byte_bat_ky_khong_lam_sap(tmp_path_factory, blob):
    path = tmp_path_factory.mktemp('fuzz') / 'x.csv'
    path.write_bytes(blob)
    try:
        data = readCsv(str(path))
    except CsvError:
        return
    assert data.headers and data.rows


# ----------------------------------------------------------------- làm sạch
def test_lam_sach_bo_ky_tu_vo_hinh_va_dao_chieu():
    clean, _ = sanitizeField('Nguyễn​ Văn‮ A\x00\x07')
    assert clean == 'Nguyễn Văn A'


def test_lam_sach_chuan_hoa_nfc():
    decomposed = 'Nguyễn'
    clean, _ = sanitizeField(decomposed)
    assert clean == 'Nguyễn'


def test_lam_sach_cat_bot_va_bao():
    clean, truncated = sanitizeField('x' * 50, maxLength=10)
    assert (clean, truncated) == ('x' * 10, True)


def test_bo_dau_tieng_viet_ca_chu_d():
    assert viRemoveDiacritics('Đặng Đình Đức') == 'Dang Dinh Duc'
    assert viNormalizeText('  Trần   THỊ  ') == 'tran thi'


# ----------------------------------------------------------------- kiểm từng trường
@pytest.mark.parametrize('raw,expected', [
    ('0912 345 678', ('0912345678', None)),
    ('0912.345.678', ('0912345678', None)),
    ('(024) 3825-1234', ('02438251234', None)),
    ('+84 912 345 678', ('+84912345678', None)),
    ('84912345678', ('+84912345678', None)),
    ('0084912345678', ('+84912345678', None)),
    ('912345678', ('0912345678', 'phone_leading_zero_added')),
    ('113', ('113', None)),
    ('09123abc', (None, 'phone_invalid_chars')),
    ('Chủ tịch xã', (None, 'phone_no_digits')),
    ('12', (None, 'phone_bad_length')),
    ('1234567890123456', (None, 'phone_bad_length')),
])
def test_chuan_hoa_so_dien_thoai(raw, expected):
    assert normalizePhone(raw) == expected


def test_khong_tu_them_so_0_khi_tat_tuy_chon():
    assert normalizePhone('912345678', fixLeadingZero=False) == ('912345678', None)


@pytest.mark.parametrize('raw,expected', [
    ('01/02/1990', '1990-02-01'), ('1-2-1990', '1990-02-01'), ('1990-02-01', '1990-02-01'),
    ('32874', '1990-01-01'), ('31/02/1990', None), ('hôm qua', None),
])
def test_ngay_sinh(raw, expected):
    assert parseBirthday(raw) == expected


def test_trang_thai_ban_ghi():
    opts = ValidationOptions()
    assert buildRecord(2, {'name': 'A', 'number': '0912345678'}, opts).status == STATUS_OK
    warn = buildRecord(2, {'name': 'A', 'number': '0912345678', 'email': 'sai@'}, opts)
    assert warn.status == STATUS_WARNING and warn.emails == []
    assert buildRecord(2, {'name': '', 'number': '0912345678'}, opts).status == STATUS_ERROR
    assert buildRecord(2, {'name': 'A', 'number': 'abc'}, opts).status == STATUS_ERROR


def test_ngay_sinh_tuong_lai_bi_bo():
    record = buildRecord(2, {'name': 'A', 'number': '0912345678', 'birthday': '01/01/2999'}, ValidationOptions())
    assert record.birthday == '' and record.issues[0].code == 'birthday_invalid'


@pytest.mark.parametrize('drop,expectedStatus', [(False, STATUS_WARNING), (True, STATUS_ERROR)])
def test_danh_dau_trung_so_ke_ca_khac_dinh_dang(drop, expectedStatus):
    opts = ValidationOptions(dropDuplicatePhones=drop)
    records = [buildRecord(2, {'name': 'A', 'number': '0912345678'}, opts),
               buildRecord(3, {'name': 'B', 'number': '+84 912 345 678'}, opts)]
    assert markDuplicates(records, opts) == 1
    assert records[0].status == STATUS_OK
    assert records[1].status == expectedStatus
    assert records[1].issues[-1].params == {'row': 2}


# ----------------------------------------------------------------- đoán cột
def test_doan_cot_tieng_viet_va_google_contacts():
    assert guessMapping(['Họ và tên', 'Số điện thoại', 'Chức vụ', 'Ghi chú'])['title'] == 'Chức vụ'
    google = guessMapping(['Name', 'Phone 1 - Value', 'E-mail 1 - Value', 'Organization 1 - Name'])
    assert google['number'] == 'Phone 1 - Value'
    assert google['email'] == 'E-mail 1 - Value'


def test_moi_cot_chi_gan_cho_mot_truong():
    mapping = guessMapping(['Tên', 'SĐT'])
    assert mapping['name'] == 'Tên' and mapping['number'] == 'SĐT'
    assert sum(1 for v in mapping.values() if v) == 2
