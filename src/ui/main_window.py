# -*- coding: utf-8 -*-
"""Cửa sổ chính: 1. chọn tệp -> 2. ghép cột -> 3. xem trước và xuất.

Mọi việc nặng (đọc tệp, kiểm tra, ghi tệp) chạy ở `Task` nền; giao diện chỉ nhận
Signal. Kết quả của tác vụ cũ (người dùng đã đổi tệp/ghép cột) bị bỏ qua nhờ số thế hệ.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QDesktopServices, QGuiApplication, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.app_info import APP_SLUG
from src.engine.csv_source import CsvData, CsvError, readCsv
from src.engine.fields import FIELDS
from src.engine.pipeline import Cancelled, MappingError, ValidationSummary, exportIssueReport, exportVcf, validateRows
from src.engine.validate import STATUS_ERROR, ValidationOptions
from src.i18n import LANGUAGE_NAMES, describeIssues, formatNumber, setLanguage, tr
from src.services.settings import LANGUAGES, THEMES, Settings
from src.services.tokens import loadTokens
from src.ui import icons
from src.ui.about import AboutDialog
from src.ui.mapping import MappingPanel
from src.ui.preview import PreviewPanel
from src.ui.theme import applyTheme
from src.ui.widgets import Card, DropZone, Task, Toast, button, label
from src.utils.resource_path import resourcePath

REVALIDATE_DELAY_MS = 250
LEFT_PANEL_WIDTH = 440


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        setLanguage(settings.get('language'))
        self.themeName = applyTheme(QApplication.instance(), settings.get('theme'))
        self.tokens = t = loadTokens(self.themeName)
        self.data: CsvData | None = None
        self.records = []
        self.summary: ValidationSummary | None = None
        self.task: Task | None = None
        self.generation = 0

        self.setMinimumSize(1040, 680)
        self.resize(1280, 820)
        self.setWindowIcon(QPixmap(resourcePath('assets/icons/app-256.png')))

        page = QWidget()
        page.setObjectName('page')
        self.setCentralWidget(page)
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._buildHeader())

        body = QHBoxLayout()
        body.setContentsMargins(t.space(5), t.space(5), t.space(5), t.space(5))
        body.setSpacing(t.space(5))
        body.addWidget(self._buildLeftPanel())
        body.addWidget(self._buildRightPanel(), 1)
        root.addLayout(body, 1)
        root.addWidget(self._buildStatusBar())

        self.toast = Toast(page, t)
        self.revalidateTimer = QTimer(self)
        self.revalidateTimer.setSingleShot(True)
        self.revalidateTimer.setInterval(REVALIDATE_DELAY_MS)
        self.revalidateTimer.timeout.connect(self.startValidation)

        QShortcut(QKeySequence.StandardKey.Open, self, activated=self.browseCsv)
        QShortcut(QKeySequence('Ctrl+E'), self, activated=self.exportVcard)
        QShortcut(QKeySequence.StandardKey.Find, self, activated=lambda: self.preview.searchBox.setFocus())
        QShortcut(QKeySequence('F1'), self, activated=self.showAbout)
        hints = QGuiApplication.styleHints()
        if hasattr(hints, 'colorSchemeChanged'):
            hints.colorSchemeChanged.connect(lambda _: self.settings.get('theme') == 'system'
                                             and self.setTheme('system'))

        self.retranslate()
        self.restyle()
        self._updateActions()
        QTimer.singleShot(0, self.dropZone.browseButton.setFocus)

    # ================================================================ dựng giao diện
    def _buildHeader(self) -> QWidget:
        t = self.tokens
        header = QFrame()
        header.setObjectName('header')
        header.setFixedHeight(64)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(t.space(5), 0, t.space(4), 0)
        layout.setSpacing(t.space(3))
        logo = QLabel()
        pm = QPixmap(resourcePath('assets/icons/app-64.png'))
        pm.setDevicePixelRatio(2.0)
        logo.setPixmap(pm)
        logo.setAccessibleName('tsudev')
        names = QVBoxLayout()
        names.setSpacing(0)
        brand = label(APP_SLUG)
        brand.setObjectName('brandName')
        self.taglineLabel = label()
        self.taglineLabel.setObjectName('brandTagline')
        names.addStretch(1)
        names.addWidget(brand)
        names.addWidget(self.taglineLabel)
        names.addStretch(1)
        layout.addWidget(logo)
        layout.addLayout(names)
        layout.addStretch(1)

        self.themeButton = self._menuButton()
        self.themeMenu = QMenu(self)
        self.themeGroup = QActionGroup(self)
        self.themeActions: dict[str, QAction] = {}
        for name in THEMES:
            action = QAction(self, checkable=True)
            action.setChecked(self.settings.get('theme') == name)
            action.triggered.connect(lambda _=False, n=name: self.setTheme(n))
            self.themeGroup.addAction(action)
            self.themeMenu.addAction(action)
            self.themeActions[name] = action
        self.themeButton.setMenu(self.themeMenu)

        self.languageButton = self._menuButton()
        self.languageMenu = QMenu(self)
        self.languageGroup = QActionGroup(self)
        for code in LANGUAGES:
            action = QAction(LANGUAGE_NAMES[code], self, checkable=True)
            action.setChecked(self.settings.get('language') == code)
            action.triggered.connect(lambda _=False, c=code: self.setLanguageCode(c))
            self.languageGroup.addAction(action)
            self.languageMenu.addAction(action)
        self.languageButton.setMenu(self.languageMenu)

        self.aboutButton = button('', 'ghost')
        self.aboutButton.clicked.connect(self.showAbout)
        for widget in (self.themeButton, self.languageButton, self.aboutButton):
            layout.addWidget(widget)
        return header

    def _menuButton(self) -> QToolButton:
        b = QToolButton()
        b.setProperty('variant', 'ghost')
        b.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setIconSize(QSize(16, 16))
        return b

    def _buildLeftPanel(self) -> QWidget:
        t = self.tokens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(LEFT_PANEL_WIDTH)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        host = QWidget()
        host.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        column = QVBoxLayout(host)
        column.setContentsMargins(0, 0, t.space(3), 0)
        column.setSpacing(t.space(4))

        self.fileCard = Card(t)
        self.dropZone = DropZone(t)
        self.dropZone.fileDropped.connect(self.loadCsv)
        self.dropZone.browseRequested.connect(self.browseCsv)
        self.fileCard.body.addWidget(self.dropZone)
        fileRow = QHBoxLayout()
        fileRow.setSpacing(t.space(3))
        self.fileIcon = QLabel()
        fileText = QVBoxLayout()
        fileText.setSpacing(2)
        self.fileNameLabel = label('', 'fieldLabel')
        self.fileNameLabel.setTextFormat(Qt.TextFormat.PlainText)
        self.fileMetaLabel = label('', 'muted', wrap=True)
        fileText.addWidget(self.fileNameLabel)
        fileText.addWidget(self.fileMetaLabel)
        self.changeFileButton = button('')
        self.changeFileButton.clicked.connect(self.browseCsv)
        fileRow.addWidget(self.fileIcon, 0, Qt.AlignmentFlag.AlignTop)
        fileRow.addLayout(fileText, 1)
        fileRow.addWidget(self.changeFileButton, 0, Qt.AlignmentFlag.AlignVCenter)
        self.fileInfo = QWidget()
        self.fileInfo.setLayout(fileRow)
        self.fileInfo.setVisible(False)
        self.fileCard.body.addWidget(self.fileInfo)
        privacyRow = QHBoxLayout()
        privacyRow.setSpacing(t.space(2))
        self.privacyIcon = QLabel()
        self.privacyLabel = label('', 'muted', wrap=True)
        privacyRow.addWidget(self.privacyIcon, 0, Qt.AlignmentFlag.AlignTop)
        privacyRow.addWidget(self.privacyLabel, 1)
        self.fileCard.body.addLayout(privacyRow)
        column.addWidget(self.fileCard)

        self.mappingCard = Card(t)
        self.mappingHint = label('', 'secondary', wrap=True)
        self.mappingCard.body.addWidget(self.mappingHint)
        self.mappingPanel = MappingPanel(t)
        self.mappingPanel.changed.connect(self._scheduleValidation)
        self.mappingCard.body.addWidget(self.mappingPanel)
        self.fixZeroBox = QCheckBox()
        self.fixZeroBox.setChecked(self.settings.get('fixLeadingZero'))
        self.dropDupBox = QCheckBox()
        self.dropDupBox.setChecked(self.settings.get('dropDuplicatePhones'))
        for box, key in ((self.fixZeroBox, 'fixLeadingZero'), (self.dropDupBox, 'dropDuplicatePhones')):
            box.toggled.connect(lambda checked, k=key: (self.settings.set(k, checked), self._scheduleValidation()))
            self.mappingCard.body.addWidget(box)
        column.addWidget(self.mappingCard)
        column.addStretch(1)
        scroll.setWidget(host)
        return scroll

    def _buildRightPanel(self) -> QWidget:
        t = self.tokens
        card = Card(t)
        self.previewCard = card
        self.preview = PreviewPanel(t, self.settings.get('pagesize.preview'))
        self.preview.pageSizeChanged.connect(lambda size: self.settings.set('pagesize.preview', size))
        card.body.addWidget(self.preview, 1)
        actions = QHBoxLayout()
        actions.setSpacing(t.space(2))
        self.resultLabel = label('', 'secondary', wrap=True)
        actions.addWidget(self.resultLabel, 1)
        self.reportButton = button('')
        self.reportButton.clicked.connect(self.exportReport)
        self.exportButton = button('', 'primary')
        self.exportButton.clicked.connect(self.exportVcard)
        actions.addWidget(self.reportButton)
        actions.addWidget(self.exportButton)
        card.body.addLayout(actions)
        return card

    def _buildStatusBar(self) -> QWidget:
        t = self.tokens
        bar = QFrame()
        bar.setObjectName('statusBar')
        bar.setFixedHeight(40)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(t.space(5), 0, t.space(4), 0)
        layout.setSpacing(t.space(3))
        self.statusLabel = label('', 'secondary')
        self.statusLabel.setAccessibleName('status')
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(240)
        self.progress.setVisible(False)
        self.cancelButton = button('', 'ghost')
        self.cancelButton.setVisible(False)
        self.cancelButton.clicked.connect(self.cancelTask)
        layout.addWidget(self.statusLabel, 1)
        layout.addWidget(self.progress)
        layout.addWidget(self.cancelButton)
        return bar

    # ================================================================ ngôn ngữ / chủ đề
    def retranslate(self) -> None:
        self.setWindowTitle(tr('app.windowTitle'))
        self.taglineLabel.setText(tr('app.tagline'))
        self.themeButton.setText(tr('header.theme'))
        self.themeButton.setAccessibleName(tr('header.theme'))
        for name, action in self.themeActions.items():
            action.setText(tr(f'theme.{name}'))
        self.languageButton.setText(tr('header.language'))
        self.languageButton.setAccessibleName(tr('header.language'))
        self.aboutButton.setText(tr('header.about'))
        self.fileCard.setTitle(tr('step1.title'))
        self.dropZone.retranslate()
        self.changeFileButton.setText(tr('step1.change'))
        self.privacyLabel.setText(tr('step1.privacy'))
        self.mappingCard.setTitle(tr('step2.title'))
        self.mappingHint.setText(tr('step2.hint'))
        self.mappingPanel.retranslate()
        self.fixZeroBox.setText(tr('step2.fixLeadingZero'))
        self.dropDupBox.setText(tr('step2.dropDuplicates'))
        self.previewCard.setTitle(tr('step3.title'))
        self.preview.retranslate()
        self.exportButton.setText(tr('step3.exportVcf'))
        self.reportButton.setText(tr('step3.exportReport'))
        self.reportButton.setToolTip(tr('dialog.reportWarning'))
        self.cancelButton.setText(tr('common.cancel'))
        self._updateFileInfo()
        self._updateResult()

    def restyle(self) -> None:
        t = self.tokens
        secondary = t.color('text-secondary')
        self.themeButton.setIcon(icons.icon('sun', secondary))
        self.languageButton.setIcon(icons.icon('languages', secondary))
        self.aboutButton.setIcon(icons.icon('info', secondary))
        self.fileIcon.setPixmap(icons.pixmap('file', t.color('primary'), 24))
        self.privacyIcon.setPixmap(icons.pixmap('shield', t.color('success'), 16))
        self.exportButton.setIcon(icons.icon('download', t.color('on-primary')))
        self.reportButton.setIcon(icons.icon('report', t.color('text-primary')))
        self.dropZone.restyle(t)
        self.preview.restyle(t)
        self.toast.restyle(t)

    def setTheme(self, name: str) -> None:
        self.settings.set('theme', name)
        self.themeName = applyTheme(QApplication.instance(), name)
        self.tokens = loadTokens(self.themeName)
        self.restyle()

    def setLanguageCode(self, code: str) -> None:
        self.settings.set('language', code)
        setLanguage(code)
        self.retranslate()

    def showAbout(self) -> None:
        AboutDialog(self.tokens, self).open()

    # ================================================================ tác vụ nền
    def _runTask(self, fn, onDone, statusKey: str) -> None:
        self.cancelTask()
        self.generation += 1
        generation = self.generation
        task = Task(fn)
        self.task = task
        self.progress.setRange(0, 0)
        self.progress.setVisible(True)
        self.cancelButton.setVisible(True)
        self.statusLabel.setText(tr(statusKey, done=0, total=0))

        def onProgress(done: int, total: int) -> None:
            if generation != self.generation:
                return
            self.progress.setRange(0, max(total, 1))
            self.progress.setValue(done)
            self.statusLabel.setText(tr(statusKey, done=formatNumber(done), total=formatNumber(total)))

        def finish() -> None:
            if self.task is task:
                self.task = None
            self.progress.setVisible(False)
            self.cancelButton.setVisible(False)
            self._updateActions()

        def onFinished(result) -> None:
            if generation != self.generation:
                return
            finish()
            onDone(result)
            self._updateActions()

        def onFailed(exc) -> None:
            if generation != self.generation:
                return
            finish()
            self._showError(exc)

        task.signals.progress.connect(onProgress)
        task.signals.finished.connect(onFinished)
        task.signals.failed.connect(onFailed)
        self._updateActions()
        task.start()

    def cancelTask(self) -> None:
        if self.task:
            self.task.cancel.cancel()
            self.task = None
            self.generation += 1
            self.progress.setVisible(False)
            self.cancelButton.setVisible(False)
            self.statusLabel.setText(tr('progress.cancelled'))
            self._updateActions()

    def _showError(self, exc: BaseException) -> None:
        if isinstance(exc, Cancelled):
            self.statusLabel.setText(tr('progress.cancelled'))
            return
        if isinstance(exc, CsvError):
            message = tr(f'csv.{exc.code}', **exc.params)
        elif isinstance(exc, MappingError):
            params = dict(exc.params)
            if 'field' in params:
                params['field'] = tr(f"field.{params['field']}")
            message = tr(f'mapping.{exc.code}', **params)
        elif isinstance(exc, ValueError) and str(exc) == 'same_as_source':
            message = tr('dialog.sameAsSource')
        elif isinstance(exc, OSError):
            message = tr('dialog.writeFailed', reason=exc.strerror or exc.__class__.__name__)
        else:
            message = f'{exc.__class__.__name__}: {exc}'
        self.statusLabel.setText(message)
        self.toast.show_('error', message)

    # ================================================================ bước 1: tệp
    def browseCsv(self) -> None:
        start = os.path.dirname(self.data.path) if self.data else os.path.expanduser('~')
        path, _ = QFileDialog.getOpenFileName(self, tr('step1.dialogTitle'), start, tr('step1.filter'))
        if path:
            self.loadCsv(path)

    def loadCsv(self, path: str) -> None:
        self.data = None
        self.records = []
        self.summary = None
        self.preview.setRecords([])
        self._runTask(lambda progress, cancel: readCsv(path), self._onCsvLoaded, 'progress.reading')

    def _onCsvLoaded(self, data: CsvData) -> None:
        self.data = data
        self._updateFileInfo()
        self.mappingPanel.setData(data)  # phát `changed` -> tự kiểm tra dữ liệu
        self.changeFileButton.setFocus()

    def _updateFileInfo(self) -> None:
        data = self.data
        self.dropZone.setVisible(data is None)
        self.fileInfo.setVisible(data is not None)
        if data:
            self.fileNameLabel.setText(os.path.basename(data.path))
            self.fileNameLabel.setToolTip(data.path)
            self.fileMetaLabel.setText(tr('step1.meta', rows=formatNumber(data.rowCount),
                                          encoding=tr(f'encoding.{data.encoding}'),
                                          delimiter=tr(f'delimiter.{data.delimiter}')))

    # ================================================================ bước 2-3: kiểm tra
    def _scheduleValidation(self) -> None:
        if self.data and self.mappingPanel.isComplete():
            self.revalidateTimer.start()
        else:
            self.records, self.summary = [], None
            self.preview.setRecords([])
            self._updateResult()
            self._updateActions()

    def _options(self) -> ValidationOptions:
        return ValidationOptions(fixLeadingZero=self.fixZeroBox.isChecked(),
                                 dropDuplicatePhones=self.dropDupBox.isChecked())

    def startValidation(self) -> None:
        if not (self.data and self.mappingPanel.isComplete()):
            return
        data, mapping, options = self.data, self.mappingPanel.mapping(), self._options()
        self._runTask(lambda progress, cancel: validateRows(data, mapping, options, progress, cancel),
                      self._onValidated, 'progress.validating')

    def _onValidated(self, result) -> None:
        self.records, self.summary = result
        self.preview.setRecords(self.records)
        self._updateResult()
        self.statusLabel.setText(self.resultLabel.text())

    def _updateResult(self) -> None:
        s = self.summary
        self.resultLabel.setText(tr('progress.validated', total=formatNumber(s.total), ok=formatNumber(s.ok),
                                    warning=formatNumber(s.warning), error=formatNumber(s.error)) if s else '')

    def _updateActions(self) -> None:
        busy = self.task is not None
        s = self.summary
        self.exportButton.setEnabled(not busy and bool(s and s.exportable))
        self.reportButton.setEnabled(not busy and bool(s and (s.warning or s.error)))
        self.changeFileButton.setEnabled(not busy)
        self.dropZone.setEnabled(not busy)

    # ================================================================ xuất
    def _defaultPath(self, suffix: str, ext: str) -> str:
        base = os.path.splitext(self.data.path)[0] if self.data else os.path.join(os.path.expanduser('~'), 'danh-ba')
        return f'{base}{suffix}{ext}'

    def exportVcard(self) -> None:
        if not self.exportButton.isEnabled():
            return
        # QFileDialog tự hỏi trước khi ghi đè tệp đã có.
        path, _ = QFileDialog.getSaveFileName(self, tr('dialog.saveVcf'), self._defaultPath('', '.vcf'),
                                              tr('dialog.saveVcfFilter'))
        if not path:
            return
        if not path.lower().endswith('.vcf'):
            path += '.vcf'
        records, source = self.records, self.data.path

        def done(count: int) -> None:
            message = tr('toast.exported', count=formatNumber(count), file=os.path.basename(path))
            self.statusLabel.setText(message)
            self.toast.show_('success', message, tr('toast.openFolder'), lambda: self._openFolder(path))

        self._runTask(lambda progress, cancel: exportVcf(records, path, source, progress, cancel),
                      done, 'progress.exporting')

    def exportReport(self) -> None:
        if not self.reportButton.isEnabled():
            return
        path, _ = QFileDialog.getSaveFileName(self, tr('dialog.saveReport'),
                                              self._defaultPath(tr('dialog.reportSuffix'), '.csv'),
                                              tr('dialog.saveReportFilter'))
        if not path:
            return
        if not path.lower().endswith('.csv'):
            path += '.csv'
        if self.data and os.path.abspath(path) == os.path.abspath(self.data.path):
            self.toast.show_('error', tr('dialog.sameAsSource'))
            return
        labels = {'row': tr('field.row'), 'status': tr('field.status'), 'issues': tr('field.issues'),
                  **{name: tr(f'field.{name}') for name in FIELDS}}
        statuses = {key: tr(f'status.{key}') for key in ('ok', 'warning', STATUS_ERROR)}
        records = self.records

        def done(count: int) -> None:
            message = tr('toast.reportExported', count=formatNumber(count), file=os.path.basename(path))
            self.toast.show_('success', message, tr('toast.openFolder'), lambda: self._openFolder(path))

        self._runTask(lambda progress, cancel: exportIssueReport(records, path, describeIssues, labels, statuses),
                      done, 'progress.exporting')

    @staticmethod
    def _openFolder(path: str) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(os.path.abspath(path))))

    # ================================================================ sự kiện cửa sổ
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.toast.isVisible():
            self.toast.reposition()

    def closeEvent(self, event):
        if self.task is not None:
            answer = QMessageBox.question(self, tr('dialog.confirmCloseTitle'), tr('dialog.confirmClose'))
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.cancelTask()
        # Dữ liệu danh bạ chỉ nằm trong RAM - xóa tham chiếu để bộ nhớ được thu hồi.
        self.records, self.data = [], None
        self.preview.setRecords([])
        super().closeEvent(event)
