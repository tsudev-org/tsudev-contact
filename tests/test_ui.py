# -*- coding: utf-8 -*-
"""Kiểm thử giao diện PySide6 trọn kịch bản người dùng. Chạy offscreen, không cần màn hình.

Kịch bản: mở app -> nạp CSV -> tự ghép cột + tự kiểm tra -> lọc / tìm / phân trang ->
xuất vCard -> xuất báo cáo lỗi -> đổi chủ đề, ngôn ngữ -> tệp hỏng không làm sập app.
"""
from __future__ import annotations

import csv
import time

import pytest

pytest.importorskip('PySide6')

from PySide6.QtWidgets import QApplication, QFileDialog  # noqa: E402

from src.services.settings import THEMES, Settings  # noqa: E402
from src.ui.preview import pageWindow  # noqa: E402
from tests.fixtures.make_samples import main as makeSamples  # noqa: E402
from tests.vcard_reader import parseVcards  # noqa: E402


@pytest.fixture(scope='module')
def app():
    instance = QApplication.instance() or QApplication([])
    instance.setStyle('Fusion')
    return instance


@pytest.fixture
def samples(tmp_path):
    makeSamples(str(tmp_path))
    return tmp_path


@pytest.fixture
def window(app, tmp_path):
    from src.ui.main_window import MainWindow
    w = MainWindow(Settings(str(tmp_path / 'settings.json')))
    w.show()
    yield w
    w.close()
    w.deleteLater()
    app.processEvents()


def waitIdle(app, w, timeout=20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        app.processEvents()
        if w.task is None and not w.revalidateTimer.isActive():
            for _ in range(5):
                app.processEvents()
            return
        time.sleep(0.01)
    raise AssertionError('tác vụ nền không xong kịp')


def loadSample(app, w, samples, name='mau-1200-utf8.csv'):
    w.loadCsv(str(samples / name))
    waitIdle(app, w)
    waitIdle(app, w)


@pytest.mark.parametrize('current,last,expected', [
    (1, 5, [1, 2, 3, 4, 5]),
    (1, 120, [1, 2, 3, 4, 5, None, 120]),
    (60, 120, [1, None, 59, 60, 61, None, 120]),
    (120, 120, [1, None, 116, 117, 118, 119, 120]),
])
def test_toi_da_bay_o_phan_trang(current, last, expected):
    assert pageWindow(current, last) == expected


def test_nap_csv_tu_ghep_cot_va_kiem_tra(app, window, samples):
    loadSample(app, window, samples)
    mapping = window.mappingPanel.mapping()
    assert mapping['name'] == 'Họ và tên' and mapping['number'] == 'Số điện thoại'
    assert mapping['title'] == 'Chức vụ' and mapping['address'] is None
    s = window.summary
    assert (s.total, s.ok, s.warning, s.error) == (1200, 1194, 4, 2)
    assert window.exportButton.isEnabled() and window.reportButton.isEnabled()
    assert window.preview.summaryLabel.text() == '1-10 / 1.200'


def test_bo_ghep_truong_bat_buoc_thi_khong_xuat_duoc(app, window, samples):
    loadSample(app, window, samples)
    window.mappingPanel.combos['number'].setCurrentIndex(0)
    waitIdle(app, window)
    assert window.summary is None
    assert not window.exportButton.isEnabled()
    assert window.mappingPanel.combos['number'].property('invalid') is True


def test_loc_tim_khong_dau_va_doi_co_trang(app, window, samples):
    loadSample(app, window, samples)
    p = window.preview
    p._setStatusFilter('error')
    assert len(p.filtered) == 2
    p._setStatusFilter('all')
    p.goToPage(5)  # bản ghi đầu đang thấy là bản ghi thứ 41
    p.pageSizeBox.setCurrentIndex(2)  # 50 / trang
    assert p.page == 1 and p.pageSize == 50  # 41 nằm ở trang 1 khi 50 / trang
    p.goToPage(3)
    p.pageSizeBox.setCurrentIndex(0)  # về 10: bản ghi 101 -> trang 11
    assert p.page == 11
    target = window.records[100].values['name']
    p.searchBox.setText(target.upper().replace('Ễ', 'E'))
    p._applySearch()
    assert any(r.values['name'] == target for r in p.filtered)
    assert window.settings.get('pagesize.preview') == 10


def test_xuat_vcard_dung_so_lien_he_va_khong_bi_chen(app, window, samples, tmp_path, monkeypatch):
    loadSample(app, window, samples)
    out = tmp_path / 'ket-qua.vcf'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (str(out), '')))
    window.exportVcard()
    waitIdle(app, window)
    cards = parseVcards(out.read_bytes().decode('utf-8'))
    assert len(cards) == window.summary.exportable == 1198
    allTels = [v for card in cards for name, _, v in card if name == 'TEL']
    assert '19001234' not in allTels
    assert not any(v == 'Gia mao' for card in cards for name, _, v in card if name == 'FN')
    assert window.toast.isVisible()


def test_xuat_bao_cao_vo_hieu_cong_thuc(app, window, samples, tmp_path, monkeypatch):
    loadSample(app, window, samples)
    out = tmp_path / 'bao-cao.csv'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (str(out), '')))
    window.preview  # noqa: B018
    window.exportReport()
    waitIdle(app, window)
    with open(out, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    assert rows[0][0] == 'Dòng'
    assert len(rows) - 1 == 6
    assert not any(cell.startswith('=') for row in rows[1:] for cell in row)


def test_khong_ghi_de_tep_nguon(app, window, samples, monkeypatch):
    loadSample(app, window, samples)
    source = str(samples / 'mau-1200-utf8.csv')
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (source, '')))
    window.exportReport()
    waitIdle(app, window)
    with open(source, encoding='utf-8-sig') as f:
        assert f.readline().startswith('Họ và tên')


def test_tep_hong_bao_loi_khong_sap(app, window, tmp_path):
    bad = tmp_path / 'gia.csv'
    bad.write_bytes(b'PK\x03\x04\x00\x00binary')
    window.loadCsv(str(bad))
    waitIdle(app, window)
    assert window.data is None
    assert window.toast.isVisible()
    assert 'xlsx' in window.toast.textLabel.text()


def test_o_trang_hien_tai_to_nen_primary(app, window, samples):
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QToolButton
    loadSample(app, window, samples, 'mau-60-cham-phay.csv')
    current = next(b for b in window.preview.pagerHost.findChildren(QToolButton) if b.property('current'))
    image = window.grab().toImage()
    center = current.mapTo(window, current.rect().center())
    pixel = image.pixelColor(center.x() - 8, center.y())
    assert pixel.name() == QColor(window.tokens.color('primary')).name()


def test_doi_chu_de_va_ngon_ngu(app, window, samples):
    loadSample(app, window, samples, 'mau-60-cham-phay.csv')
    for theme in THEMES:
        window.setTheme(theme)
        app.processEvents()
    assert window.settings.get('theme') == THEMES[-1]
    window.setLanguageCode('en')
    assert window.exportButton.text() == 'Export vCard'
    assert 'semicolon' in window.fileMetaLabel.text()
    window.setLanguageCode('vi')
    assert window.exportButton.text() == 'Xuất vCard'
