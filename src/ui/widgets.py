# -*- coding: utf-8 -*-
"""Widget dùng chung: thẻ (card), vùng kéo-thả, thông báo nổi (toast), tác vụ nền."""
from __future__ import annotations

import os
import traceback
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from src.engine.pipeline import CancelToken
from src.i18n import tr
from src.services.tokens import Tokens
from src.ui import icons


def label(text: str = '', role: str | None = None, wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    if role:
        widget.setProperty('role', role)
    widget.setWordWrap(wrap)
    return widget


def button(text: str = '', variant: str | None = None) -> QPushButton:
    widget = QPushButton(text)
    if variant:
        widget.setProperty('variant', variant)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    return widget


def repolish(widget: QWidget) -> None:
    """Áp lại stylesheet sau khi đổi thuộc tính động (variant, invalid...)."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class Card(QFrame):
    """Khối nội dung nền bg-surface, viền border, radius-lg (DESIGN_SYSTEM mục 2)."""

    def __init__(self, t: Tokens, parent=None):
        super().__init__(parent)
        self.setObjectName('card')
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(t.space(4), t.space(4), t.space(4), t.space(4))
        self.body.setSpacing(t.space(3))
        self.titleLabel = label('', 'cardTitle')
        self.body.addWidget(self.titleLabel)

    def setTitle(self, text: str) -> None:
        self.titleLabel.setText(text)
        self.titleLabel.setAccessibleName(text)


class DropZone(QFrame):
    """Vùng kéo-thả tệp CSV. Chỉ nhận đúng MỘT tệp cục bộ."""

    fileDropped = Signal(str)
    browseRequested = Signal()

    def __init__(self, t: Tokens, parent=None):
        super().__init__(parent)
        self.setObjectName('dropZone')
        self.setAcceptDrops(True)
        self.setProperty('dragActive', False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.space(4), t.space(4), t.space(4), t.space(4))
        layout.setSpacing(t.space(2))
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iconLabel = QLabel()
        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titleLabel = label('', 'fieldLabel')
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.orLabel = label('', 'muted')
        self.orLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.browseButton = button('')
        self.browseButton.clicked.connect(self.browseRequested)
        for widget in (self.iconLabel, self.titleLabel, self.orLabel):
            layout.addWidget(widget)
        layout.addWidget(self.browseButton, 0, Qt.AlignmentFlag.AlignCenter)
        self.restyle(t)

    def retranslate(self) -> None:
        self.titleLabel.setText(tr('step1.drop'))
        self.orLabel.setText(tr('step1.or'))
        self.browseButton.setText(tr('step1.browse'))
        self.browseButton.setAccessibleName(tr('step1.dialogTitle'))

    def restyle(self, t: Tokens) -> None:
        self.iconLabel.setPixmap(icons.pixmap('upload', t.color('primary'), 32, 1.5))
        self.browseButton.setIcon(icons.icon('file', t.color('text-primary')))

    @staticmethod
    def _localFile(event) -> str | None:
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if len(urls) != 1 or not urls[0].isLocalFile():
            return None
        path = urls[0].toLocalFile()
        return path if os.path.isfile(path) else None

    def _setActive(self, active: bool) -> None:
        self.setProperty('dragActive', active)
        repolish(self)

    def dragEnterEvent(self, event):
        if self._localFile(event):
            event.acceptProposedAction()
            self._setActive(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._setActive(False)

    def dropEvent(self, event):
        self._setActive(False)
        path = self._localFile(event)
        if path:
            event.acceptProposedAction()
            self.fileDropped.emit(path)


class Toast(QFrame):
    """Thông báo nổi góc phải-trên, tự đóng 4s (lỗi 6s) - DESIGN_SYSTEM mục 5."""

    def __init__(self, parent: QWidget, t: Tokens):
        super().__init__(parent)
        self.setObjectName('toast')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(t.space(4), t.space(3), t.space(2), t.space(3))
        layout.setSpacing(t.space(3))
        self.iconLabel = QLabel()
        self.textLabel = label(wrap=True)
        self.textLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.actionButton = button('', 'link')
        self.closeButton = button('', 'ghost')
        self.closeButton.setFixedSize(28, 28)
        self.closeButton.setStyleSheet('min-height: 0; padding: 0;')
        self.closeButton.clicked.connect(self.hide)
        layout.addWidget(self.iconLabel, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.textLabel, 1)
        layout.addWidget(self.actionButton)
        layout.addWidget(self.closeButton, 0, Qt.AlignmentFlag.AlignTop)
        self.setFixedWidth(420)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        self._action: Callable | None = None
        self.actionButton.clicked.connect(self._runAction)
        self.tokens = t
        self.hide()

    def restyle(self, t: Tokens) -> None:
        self.tokens = t

    def _runAction(self):
        if self._action:
            self._action()
        self.hide()

    def show_(self, level: str, text: str, actionText: str = '', action: Callable | None = None) -> None:
        t = self.tokens
        colorName = {'success': 'success', 'error': 'danger'}.get(level, 'info')
        iconName = {'success': 'check', 'error': 'error'}.get(level, 'info')
        self.setProperty('level', level)
        repolish(self)
        self.iconLabel.setPixmap(icons.pixmap(iconName, t.color(colorName), 18))
        self.closeButton.setIcon(icons.icon('close', t.color('text-secondary')))
        self.closeButton.setAccessibleName(tr('common.close'))
        self.textLabel.setText(text)
        self.textLabel.setAccessibleName(text)
        self._action = action
        self.actionButton.setText(actionText)
        self.actionButton.setVisible(bool(actionText and action))
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self.timer.start(6000 if level == 'error' else 4000)

    def reposition(self) -> None:
        parent = self.parentWidget()
        margin = self.tokens.space(4)
        self.move(parent.width() - self.width() - margin, margin + 64)


class _TaskSignals(QObject):
    progress = Signal(int, int)
    finished = Signal(object)
    failed = Signal(object)


class Task(QRunnable):
    """Chạy hàm nặng ở thread nền. Hàm nhận (onProgress, cancelToken).

    Chỉ phát Signal về main thread - Qt tự xếp hàng sang thread giao diện, không có
    widget nào bị chạm từ thread nền (bài học lỗi `root.after` ở bản tkinter).
    """

    def __init__(self, fn: Callable):
        super().__init__()
        self.fn = fn
        self.signals = _TaskSignals()
        self.cancel = CancelToken()
        self.setAutoDelete(False)

    def run(self):
        try:
            result = self.fn(self.signals.progress.emit, self.cancel)
        except BaseException as exc:  # noqa: BLE001 - mọi lỗi đều phải về tới giao diện
            exc.__traceback_text__ = traceback.format_exc()
            self.signals.failed.emit(exc)
        else:
            self.signals.finished.emit(result)

    def start(self) -> None:
        QThreadPool.globalInstance().start(self)
