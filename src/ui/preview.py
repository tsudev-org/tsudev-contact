# -*- coding: utf-8 -*-
"""Bảng xem trước danh bạ: lọc trạng thái, tìm không dấu, phân trang theo DATA_TABLE.md.

Chân bảng chia ba: bộ chọn số bản ghi (trái) - dòng tóm tắt (giữa) - phân trang (phải).
"""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QStyledItemDelegate,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.engine.fields import FIELDS
from src.engine.text import viNormalizeText
from src.engine.validate import STATUS_ERROR, STATUS_OK, STATUS_WARNING, ContactRecord
from src.i18n import describeIssues, formatNumber, tr
from src.services.settings import PAGE_SIZES
from src.services.tokens import Tokens
from src.ui import icons
from src.ui.widgets import button, label

COLUMNS = ('row', 'status', *FIELDS, 'issues')
STATUS_COLORS = {STATUS_OK: 'success', STATUS_WARNING: 'warning', STATUS_ERROR: 'danger'}
STATUS_ICONS = {STATUS_OK: 'check', STATUS_WARNING: 'warning', STATUS_ERROR: 'error'}
SEARCH_DEBOUNCE_MS = 300
MAX_PAGE_CELLS = 7


def pageWindow(current: int, last: int) -> list[int | None]:
    """Tối đa 7 ô: < 1 ... 5 6 7 ... 13 >. None = dấu ba chấm."""
    if last <= MAX_PAGE_CELLS:
        return list(range(1, last + 1))
    if current <= 4:
        return [1, 2, 3, 4, 5, None, last]
    if current >= last - 3:
        return [1, None, *range(last - 4, last + 1)]
    return [1, None, current - 1, current, current + 1, None, last]


def cellText(record: ContactRecord, column: str) -> str:
    if column == 'row':
        return str(record.rowNumber)
    if column == 'status':
        return tr(f'status.{record.status}')
    if column == 'issues':
        return describeIssues(record)
    if column == 'number':
        return ', '.join(record.phones) or record.values['number']
    if column == 'email':
        return ', '.join(record.emails) or record.values['email']
    if column == 'birthday' and record.birthday and len(record.birthday) == 10:
        y, m, d = record.birthday.split('-')
        return f'{d}/{m}/{y}'
    return record.values[column].replace('\n', ' · ')


class ContactModel(QAbstractTableModel):
    """Chỉ giữ MỘT trang bản ghi - bảng không bao giờ dựng hàng nghìn ô cùng lúc."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.page: list[ContactRecord] = []

    def setPage(self, records: list[ContactRecord]) -> None:
        self.beginResetModel()
        self.page = records
        self.endResetModel()

    def rowCount(self, parent=None):
        return 0 if parent is not None and parent.isValid() else len(self.page)

    def columnCount(self, parent=None):
        return 0 if parent is not None and parent.isValid() else len(COLUMNS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        record = self.page[index.row()]
        column = COLUMNS[index.column()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.AccessibleTextRole):
            return cellText(record, column)
        if role == Qt.ItemDataRole.ToolTipRole and column in ('issues', 'notes', 'address', 'name'):
            text = describeIssues(record) if column == 'issues' else record.values[column]
            return text or None
        if role == Qt.ItemDataRole.UserRole:
            return record.status
        if role == Qt.ItemDataRole.TextAlignmentRole and column == 'row':
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return tr(f'field.{COLUMNS[section]}')
        return None


class StatusDelegate(QStyledItemDelegate):
    """Badge trạng thái: icon + chữ (màu không đứng một mình - DESIGN_SYSTEM mục 1)."""

    def __init__(self, tokens: Tokens, parent=None):
        super().__init__(parent)
        self.tokens = tokens

    def paint(self, painter: QPainter, option, index):
        status = index.data(Qt.ItemDataRole.UserRole)
        text = index.data()
        t = self.tokens
        color = QColor(t.color(STATUS_COLORS[status]))
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fm = QFontMetrics(option.font)
        badgeW = 16 + 4 + fm.horizontalAdvance(text) + 16
        badgeH = 22
        rect = QRect(option.rect.x() + t.space(3), option.rect.center().y() - badgeH // 2 + 1, badgeW, badgeH)
        fill = QColor(color)
        fill.setAlphaF(0.12)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, t.radius('sm'), t.radius('sm'))
        painter.drawPixmap(rect.x() + 8, rect.y() + 4, icons.pixmap(STATUS_ICONS[status], color.name(), 14))
        painter.setPen(QColor(t.color('text-primary')))
        painter.drawText(rect.adjusted(8 + 14 + 4, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        fm = QFontMetrics(option.font)
        return QSize(fm.horizontalAdvance(index.data() or '') + 60, 36)


class PreviewPanel(QWidget):
    pageSizeChanged = Signal(int)

    def __init__(self, t: Tokens, pageSize: int, parent=None):
        super().__init__(parent)
        self.tokens = t
        self.records: list[ContactRecord] = []
        self.filtered: list[ContactRecord] = []
        self.statusFilter = 'all'
        self.query = ''
        self.page = 1
        self.pageSize = pageSize if pageSize in PAGE_SIZES else PAGE_SIZES[0]

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(t.space(3))

        # --- Thanh lọc + tìm kiếm
        toolbar = QHBoxLayout()
        toolbar.setSpacing(t.space(2))
        self.filterGroup = QButtonGroup(self)
        self.filterGroup.setExclusive(True)
        self.filterButtons: dict[str, QToolButton] = {}
        for key in ('all', STATUS_OK, STATUS_WARNING, STATUS_ERROR):
            b = button('')
            b.setProperty('role', 'filter')
            b.setCheckable(True)
            b.setChecked(key == 'all')
            b.clicked.connect(lambda _=False, k=key: self._setStatusFilter(k))
            self.filterGroup.addButton(b)
            self.filterButtons[key] = b
            toolbar.addWidget(b)
        toolbar.addStretch(1)
        self.searchBox = QLineEdit()
        self.searchBox.setClearButtonEnabled(True)
        self.searchBox.setProperty('role', 'search')
        self.searchBox.setMinimumWidth(260)
        self.searchBox.setMaxLength(200)
        toolbar.addWidget(self.searchBox)
        root.addLayout(toolbar)
        self.searchTimer = QTimer(self)
        self.searchTimer.setSingleShot(True)
        self.searchTimer.setInterval(SEARCH_DEBOUNCE_MS)
        self.searchTimer.timeout.connect(self._applySearch)
        self.searchBox.textChanged.connect(lambda _: self.searchTimer.start())

        # --- Bảng trong khung radius-lg
        frame = QFrame()
        frame.setObjectName('tableFrame')
        frameLayout = QVBoxLayout(frame)
        frameLayout.setContentsMargins(1, 1, 1, 1)
        frameLayout.setSpacing(0)
        self.model = ContactModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)  # mật độ Compact cho tool desktop
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.statusDelegate = StatusDelegate(t, self.table)
        self.table.setItemDelegateForColumn(COLUMNS.index('status'), self.statusDelegate)
        widths = {'row': 64, 'status': 120, 'name': 200, 'number': 150, 'email': 190, 'organization': 170,
                  'title': 130, 'address': 200, 'birthday': 100, 'notes': 200}
        for i, column in enumerate(COLUMNS):
            if column in widths:
                self.table.setColumnWidth(i, widths[column])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        self.emptyLabel = label('', 'emptyTitle', wrap=True)
        self.emptyLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.emptyLabel.setContentsMargins(t.space(8), t.space(8), t.space(8), t.space(8))
        frameLayout.addWidget(self.table, 1)
        frameLayout.addWidget(self.emptyLabel, 1)

        # --- Chân bảng 48px: trái bộ chọn, giữa tóm tắt, phải phân trang
        footer = QFrame()
        footer.setObjectName('tableFooter')
        footer.setFixedHeight(48)
        footerLayout = QHBoxLayout(footer)
        footerLayout.setContentsMargins(t.space(4), 0, t.space(4), 0)
        footerLayout.setSpacing(t.space(2))
        self.pageSizeBox = QComboBox()
        self.pageSizeBox.setProperty('compact', True)
        for size in PAGE_SIZES:
            self.pageSizeBox.addItem(str(size), size)
        self.pageSizeBox.setCurrentIndex(PAGE_SIZES.index(self.pageSize))
        self.pageSizeBox.currentIndexChanged.connect(self._onPageSizeChanged)
        self.perPageLabel = label('', 'muted')
        left = QHBoxLayout()
        left.setSpacing(t.space(2))
        left.addWidget(self.pageSizeBox)
        left.addWidget(self.perPageLabel)
        self.summaryLabel = label('', 'muted')
        self.summaryLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pager = QHBoxLayout()
        self.pager.setContentsMargins(0, 0, 0, 0)
        self.pager.setSpacing(t.space(1))
        self.pagerHost = QWidget()
        self.pagerHost.setLayout(self.pager)
        # Chỉ làm trong suốt chính khung chứa: stylesheet không có bộ chọn sẽ đè cả nền các nút trang con.
        self.pagerHost.setObjectName('pagerHost')
        self.pagerHost.setStyleSheet('#pagerHost { background: transparent; }')
        footerLayout.addLayout(left, 1)
        footerLayout.addWidget(self.summaryLabel, 1)
        footerLayout.addWidget(self.pagerHost, 1, Qt.AlignmentFlag.AlignRight)
        frameLayout.addWidget(footer)
        root.addWidget(frame, 1)

        self.retranslate()
        self._refresh()

    # ------------------------------------------------------------ public
    def setRecords(self, records: list[ContactRecord]) -> None:
        self.records = records
        for record in records:  # khóa tìm kiếm theo ngôn ngữ không đổi -> tính một lần
            if not record.searchKey:
                record.searchKey = viNormalizeText(record.values['name'])
        self.page = 1
        self._applyFilters()

    def retranslate(self) -> None:
        names = {'all': 'filter.all', STATUS_OK: 'filter.ok', STATUS_WARNING: 'filter.warning',
                 STATUS_ERROR: 'filter.error'}
        counts = self._counts()
        for key, b in self.filterButtons.items():
            b.setText(f'{tr(names[key])}  {formatNumber(counts[key])}')
            b.setAccessibleName(tr(names[key]))
        self.searchBox.setPlaceholderText(tr('step3.search'))
        self.searchBox.setAccessibleName(tr('step3.searchLabel'))
        self.perPageLabel.setText(tr('table.perPage'))
        self.pageSizeBox.setAccessibleName(tr('table.pageSizeLabel'))
        self.pagerHost.setAccessibleName(tr('table.pagination'))
        self.model.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, len(COLUMNS) - 1)
        self.model.layoutChanged.emit()
        self._refresh()

    def restyle(self, t: Tokens) -> None:
        self.tokens = t
        self.statusDelegate.tokens = t
        for action in self.searchBox.actions():
            self.searchBox.removeAction(action)
        self.searchBox.addAction(icons.icon('search', t.color('text-muted')), QLineEdit.ActionPosition.LeadingPosition)
        for key, b in self.filterButtons.items():
            if key != 'all':
                b.setIcon(icons.icon(STATUS_ICONS[key], t.color(STATUS_COLORS[key])))
        self._refresh()

    # ------------------------------------------------------------ lọc / trang
    def _counts(self) -> dict[str, int]:
        counts = {'all': len(self.records), STATUS_OK: 0, STATUS_WARNING: 0, STATUS_ERROR: 0}
        for record in self.records:
            counts[record.status] += 1
        return counts

    def _setStatusFilter(self, key: str) -> None:
        self.statusFilter = key
        self.page = 1
        self._applyFilters()

    def _applySearch(self) -> None:
        self.query = viNormalizeText(self.searchBox.text())
        self.page = 1  # đổi từ khóa -> về trang 1, giữ cỡ trang (DATA_TABLE mục 4)
        self._applyFilters()

    def _applyFilters(self) -> None:
        q = self.query
        self.filtered = [r for r in self.records
                         if (self.statusFilter == 'all' or r.status == self.statusFilter)
                         and (not q or q in r.searchKey)]
        self.retranslate()

    def _onPageSizeChanged(self) -> None:
        newSize = self.pageSizeBox.currentData()
        firstVisible = (self.page - 1) * self.pageSize  # giữ bản ghi đầu đang nhìn thấy
        self.pageSize = newSize
        self.page = firstVisible // newSize + 1
        self._refresh()
        self.pageSizeChanged.emit(newSize)
        self.summaryLabel.setAccessibleDescription(tr('table.announce', count=newSize))
        self.pageSizeBox.setFocus()

    @property
    def lastPage(self) -> int:
        return max(1, -(-len(self.filtered) // self.pageSize))

    def goToPage(self, page: int) -> None:
        self.page = min(max(1, page), self.lastPage)
        self._refresh()

    def _refresh(self) -> None:
        self.page = min(self.page, self.lastPage)
        start = (self.page - 1) * self.pageSize
        pageRecords = self.filtered[start:start + self.pageSize]
        self.model.setPage(pageRecords)
        hasRows = bool(pageRecords)
        self.table.setVisible(hasRows)
        self.emptyLabel.setVisible(not hasRows)
        if not self.records:
            self.emptyLabel.setText(tr('step3.empty'))
        elif not hasRows:
            self.emptyLabel.setText(tr('step3.noResult', query=self.searchBox.text().strip())
                                    if self.query else tr('step3.noRows'))
        total, allCount = len(self.filtered), len(self.records)
        if not total:
            summary = ''
        elif self.lastPage == 1 and total == allCount:
            summary = tr('table.single', count=formatNumber(total))
        else:
            key = 'table.summaryFiltered' if total != allCount else 'table.summary'
            summary = tr(key, start=formatNumber(start + 1), end=formatNumber(start + len(pageRecords)),
                         total=formatNumber(total), all=formatNumber(allCount))
        self.summaryLabel.setText(summary)
        self._buildPager()

    def _buildPager(self) -> None:
        while self.pager.count():
            item = self.pager.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.filtered:
            return
        t = self.tokens
        prev = self._pageButton('', self.page - 1)
        prev.setIcon(icons.icon('chevron-left', t.color('text-primary')))
        prev.setAccessibleName(tr('table.prev'))
        prev.setEnabled(self.page > 1)  # ở trang đầu: Disabled, KHÔNG ẩn
        self.pager.addWidget(prev)
        for number in pageWindow(self.page, self.lastPage):
            if number is None:
                self.pager.addWidget(label('…', 'ellipsis'))
                continue
            b = self._pageButton(str(number), number)
            b.setProperty('current', number == self.page)
            if number == self.page:
                b.setAccessibleDescription('current')
            b.setAccessibleName(tr('table.page', page=number))
            self.pager.addWidget(b)
        nxt = self._pageButton('', self.page + 1)
        nxt.setIcon(icons.icon('chevron-right', t.color('text-primary')))
        nxt.setAccessibleName(tr('table.next'))
        nxt.setEnabled(self.page < self.lastPage)
        self.pager.addWidget(nxt)

    def _pageButton(self, text: str, target: int) -> QToolButton:
        b = QToolButton()
        b.setText(text)
        b.setProperty('role', 'page')
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(lambda _=False, p=target: self.goToPage(p))
        return b

    def currentPageRecords(self) -> list[ContactRecord]:
        return list(self.model.page)

