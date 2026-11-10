# -*- coding: utf-8 -*-
"""Tùy chọn người dùng và bản dịch."""
import json
import re

import pytest

from src import i18n
from src.i18n import en, vi
from src.services import settings as settingsModule
from src.services.settings import DEFAULTS, Settings


def test_mac_dinh_khi_chua_co_file(tmp_path):
    s = Settings(str(tmp_path / 'settings.json'))
    assert {k: s.get(k) for k in DEFAULTS} == DEFAULTS
    assert s.get('language') == 'vi'


def test_ghi_nguyen_tu_va_doc_lai(tmp_path):
    path = tmp_path / 'sub' / 'settings.json'
    Settings(str(path)).set('pagesize.preview', 50)
    assert Settings(str(path)).get('pagesize.preview') == 50
    assert [p.name for p in path.parent.iterdir()] == ['settings.json']


@pytest.mark.parametrize('stored', [
    '{"pagesize.preview": 999, "theme": "hong", "language": "fr", "fixLeadingZero": "yes"}',
    '{"pagesize.preview": true}', 'không phải json', '[1, 2]',
])
def test_gia_tri_hong_hoac_la_quay_ve_mac_dinh(tmp_path, stored):
    path = tmp_path / 'settings.json'
    path.write_text(stored, encoding='utf-8')
    s = Settings(str(path))
    assert {k: s.get(k) for k in DEFAULTS} == DEFAULTS


def test_tu_choi_khoa_va_gia_tri_la(tmp_path):
    s = Settings(str(tmp_path / 'settings.json'))
    with pytest.raises(KeyError):
        s.set('lastFile', 'C:/danh-ba.csv')
    with pytest.raises(ValueError):
        s.set('pagesize.preview', 25)


def test_file_qua_lon_bi_bo_qua(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'theme': 'dark', 'pad': 'x' * 70_000}), encoding='utf-8')
    assert Settings(str(path)).get('theme') == 'system'


def test_xoa_csdl_tam_cua_ban_cu(tmp_path, monkeypatch):
    monkeypatch.setattr(settingsModule.tempfile, 'gettempdir', lambda: str(tmp_path))
    legacy = tmp_path / 'tsudev-contact'
    legacy.mkdir()
    (legacy / 'contacts_data.db').write_bytes(b'PII')
    (legacy / 'khac.txt').write_text('giữ lại', encoding='utf-8')
    removed = settingsModule.removeLegacyData()
    assert len(removed) == 1
    assert not (legacy / 'contacts_data.db').exists()
    assert (legacy / 'khac.txt').exists()


def test_hai_ban_dich_cung_bo_khoa_va_cung_tham_so():
    assert set(vi.STRINGS) == set(en.STRINGS)
    for key in vi.STRINGS:
        params = lambda s: set(re.findall(r'{(\w+)}', s))  # noqa: E731
        assert params(vi.STRINGS[key]) == params(en.STRINGS[key]), key


def test_moi_ma_loi_deu_co_ban_dich():
    import ast
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent / 'src' / 'core'
    codes = set()
    for path in root.glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            kind = getattr(getattr(node, 'func', None), 'id', '')
            if (isinstance(node, ast.Call) and kind in ('Issue', 'CsvError', 'MappingError')
                    and node.args and isinstance(node.args[0], ast.Constant)):
                prefix = {'Issue': 'issue', 'CsvError': 'csv', 'MappingError': 'mapping'}[kind]
                codes.add(f'{prefix}.{node.args[0].value}')
    from src.engine.validate import buildRecord  # noqa: F401 - mã lỗi phone_* trả về qua biến
    phoneCodes = ('phone_no_digits', 'phone_invalid_chars', 'phone_bad_length', 'phone_leading_zero_added')
    codes |= {f'issue.{c}' for c in phoneCodes}
    missing = sorted(c for c in codes if c not in vi.STRINGS)
    assert not missing


def test_dinh_dang_so_theo_ngon_ngu():
    i18n.setLanguage('vi')
    assert i18n.formatNumber(1128) == '1.128'
    i18n.setLanguage('en')
    assert i18n.formatNumber(1128) == '1,128'
    i18n.setLanguage('vi')
