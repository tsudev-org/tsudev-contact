# -*- coding: utf-8 -*-
"""Bộ dựng vCard: thoát ký tự, gập dòng, chống chèn liên hệ giả (lỗ hổng 10/11/2026)."""
from __future__ import annotations

import os
import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.engine.validate import ContactRecord, ValidationOptions, buildRecord
from src.engine.vcard import CRLF, MAX_LINE_OCTETS, buildVcard, escapeValue, foldLine, writeVcf
from tests.vcard_reader import parseVcards

REV = '20261110T000000Z'


def makeRecord(**raw) -> ContactRecord:
    raw.setdefault('name', 'Nguyễn Văn A')
    raw.setdefault('number', '0912345678')
    return buildRecord(2, raw, ValidationOptions())


def test_ten_chua_xuong_dong_khong_sinh_duoc_lien_he_gia():
    """Tái hiện đúng payload đã khai thác được ở bản cũ."""
    payload = 'An\nEND:VCARD\nBEGIN:VCARD\nVERSION:3.0\nFN:Gia mao\nTEL:19001234\nEND:VCARD\nBEGIN:VCARD'
    record = makeRecord(name=payload, notes=payload, organization=payload, address=payload)
    text = buildVcard(record, REV)
    cards = parseVcards(text)
    assert len(cards) == 1
    assert [p for p in cards[0] if p[0] == 'TEL'] == [('TEL', 'TYPE=CELL,PREF', '0912345678')]
    assert len(re.findall(r'(?m)^BEGIN:VCARD', text)) == 1
    # Không dòng vật lý nào bắt đầu bằng thuộc tính do kẻ tấn công đặt
    assert not re.search(r'(?m)^(FN:Gia|TEL:1900)', text)


@pytest.mark.parametrize('raw,expected', [
    ('a;b', 'a\\;b'), ('a,b', 'a\\,b'), ('a\\b', 'a\\\\b'), ('a\nb', 'a\\nb'), ('a\r\nb', 'a\\nb'),
    ('\\n', '\\\\n'),
])
def test_thoat_ky_tu_dac_biet(raw, expected):
    assert escapeValue(raw) == expected


def test_gap_dong_khong_cat_giua_ky_tu_utf8():
    line = 'NOTE:' + 'Nguyễn Thị Hồng Nhung ' * 20
    folded = foldLine(line)
    for physical in folded.split(CRLF):
        assert len(physical.encode('utf-8')) <= MAX_LINE_OCTETS
    assert folded.replace(CRLF + ' ', '') == line


def test_dung_crlf_va_co_truong_N_bat_buoc():
    text = buildVcard(makeRecord(), REV)
    assert text.endswith('END:VCARD\r\n')
    assert '\n' not in text.replace('\r\n', '')
    assert 'N:;Nguyễn Văn A;;;\r\n' in text
    assert 'REV:20261110T000000Z' in text


def test_nhieu_so_dien_thoai_va_email():
    record = makeRecord(number='0912 345 678 / 024.3825.1234', email='a@x.vn; b@y.vn')
    cards = parseVcards(buildVcard(record, REV))
    tels = [v for name, _, v in cards[0] if name == 'TEL']
    emails = [v for name, _, v in cards[0] if name == 'EMAIL']
    assert tels == ['0912345678', '02438251234']
    assert emails == ['a@x.vn', 'b@y.vn']


_TEXT = st.text(alphabet=st.characters(blacklist_categories=('Cs',)), max_size=300)


@settings(max_examples=300, deadline=None)
@given(name=_TEXT, org=_TEXT, notes=_TEXT, address=_TEXT, title=_TEXT)
def test_tinh_chat_moi_gia_tri_quay_ve_nguyen_ven_trong_dung_mot_the(name, org, notes, address, title):
    """Với MỌI chuỗi đầu vào: luôn đúng 1 thẻ, và giải mã ra đúng giá trị đã làm sạch."""
    record = makeRecord(name=name or 'x', organization=org, notes=notes, address=address, title=title)
    text = buildVcard(record, REV)
    cards = parseVcards(text)
    assert len(cards) == 1
    props = {}
    for prop, _, value in cards[0]:
        props.setdefault(prop, value)
    assert props['FN'] == record.values['name']
    if record.values['organization']:
        assert props['ORG'] == record.values['organization']
    if record.values['notes']:
        assert props['NOTE'] == record.values['notes']
    if record.values['title']:
        assert props['TITLE'] == record.values['title']
    for physical in text.split(CRLF):
        assert len(physical.encode('utf-8')) <= MAX_LINE_OCTETS


def test_ghi_file_nguyen_tu_khong_de_lai_file_tam(tmp_path):
    target = tmp_path / 'out.vcf'
    count = writeVcf([makeRecord(), makeRecord(name='B')], str(target))
    assert count == 2
    assert [p.name for p in tmp_path.iterdir()] == ['out.vcf']
    assert len(parseVcards(target.read_bytes().decode('utf-8'))) == 2


def test_loi_giua_chung_giu_nguyen_file_cu(tmp_path):
    target = tmp_path / 'out.vcf'
    target.write_text('cũ', encoding='utf-8')

    def explode(_count):
        raise RuntimeError('đĩa đầy')

    with pytest.raises(RuntimeError):
        writeVcf([makeRecord()], str(target), onProgress=explode)
    assert target.read_text(encoding='utf-8') == 'cũ'
    assert os.listdir(tmp_path) == ['out.vcf']
