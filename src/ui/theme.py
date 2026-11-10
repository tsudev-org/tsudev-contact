# -*- coding: utf-8 -*-
"""Sinh bảng màu + Qt Style Sheet từ token thiết kế. Không hard-code giá trị giao diện nào.

Quy chuẩn component: .standards/docs/DESIGN_SYSTEM.md mục 2-5 (nút cao 36px, radius-md,
focus ring 2px, bảng header bg-subtle chữ 600, thanh tiến trình 6px...).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTemporaryDir
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QPalette

from src.services.tokens import Tokens, loadTokens
from src.utils.resource_path import resourcePath

FONT_FILES = ('Inter-Regular.ttf', 'Inter-Medium.ttf', 'Inter-SemiBold.ttf', 'Inter-Bold.ttf')
_fontsLoaded = False
_assetDir: QTemporaryDir | None = None


def _arrowPath(t: Tokens) -> str:
    """QSS chỉ nhận ảnh qua đường dẫn: vẽ mũi tên theo màu token vào thư mục tạm riêng của app
    (QTemporaryDir tạo thư mục quyền 0700, tự xóa khi thoát)."""
    global _assetDir
    from src.ui import icons
    if _assetDir is None:
        _assetDir = QTemporaryDir()
    path = _assetDir.filePath(f'chevron-{t.theme}.png')
    icons.pixmap('chevron-down', t.color('text-secondary'), 16, 2.0).save(path)
    return path.replace('\\', '/')


def loadFonts() -> None:
    """Nạp font Inter đi kèm app (token: font-family), không phụ thuộc máy đã cài hay chưa."""
    global _fontsLoaded
    if _fontsLoaded:
        return
    for name in FONT_FILES:
        QFontDatabase.addApplicationFont(resourcePath(f'assets/fonts/{name}'))
    _fontsLoaded = True


def resolveTheme(choice: str) -> str:
    """'system' -> 'dark' hoặc 'light' theo hệ điều hành (DESIGN_SYSTEM mục 1)."""
    if choice != 'system':
        return choice
    hints = QGuiApplication.styleHints()
    scheme = hints.colorScheme() if hasattr(hints, 'colorScheme') else Qt.ColorScheme.Unknown
    return 'dark' if scheme == Qt.ColorScheme.Dark else 'light'


def appFont(t: Tokens) -> QFont:
    families = QFontDatabase.families()
    family = next((f for f in t.families() if f in families), None)
    font = QFont(family) if family else QFont()
    font.setPixelSize(t.size('body-desktop'))
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    return font


def buildPalette(t: Tokens) -> QPalette:
    c = lambda name: QColor(t.color(name))  # noqa: E731
    p = QPalette()
    roles = {
        QPalette.ColorRole.Window: 'bg-base', QPalette.ColorRole.Base: 'bg-surface',
        QPalette.ColorRole.AlternateBase: 'bg-subtle', QPalette.ColorRole.Button: 'bg-surface',
        QPalette.ColorRole.WindowText: 'text-primary', QPalette.ColorRole.Text: 'text-primary',
        QPalette.ColorRole.ButtonText: 'text-primary', QPalette.ColorRole.Highlight: 'primary',
        QPalette.ColorRole.HighlightedText: 'on-primary', QPalette.ColorRole.Link: 'text-link',
        QPalette.ColorRole.PlaceholderText: 'text-muted', QPalette.ColorRole.ToolTipBase: 'bg-surface',
        QPalette.ColorRole.ToolTipText: 'text-primary', QPalette.ColorRole.Mid: 'border',
        QPalette.ColorRole.Dark: 'border-strong', QPalette.ColorRole.Light: 'bg-surface',
    }
    for role, token in roles.items():
        p.setColor(role, c(token))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText):
        p.setColor(QPalette.ColorGroup.Disabled, role, c('text-muted'))
    return p


def buildStyleSheet(t: Tokens) -> str:
    c, sp, r = t.color, t.space, t.radius
    fs = t.size
    w = t.weight
    controlH = 36
    arrow = _arrowPath(t)
    return f"""
* {{ outline: none; }}
QWidget {{ color: {c('text-primary')}; font-size: {fs('body-desktop')}px; }}
QMainWindow, QDialog, #page {{ background: {c('bg-base')}; }}
QToolTip {{ background: {c('bg-surface')}; color: {c('text-primary')}; border: 1px solid {c('border-strong')};
           padding: {sp(1)}px {sp(2)}px; border-radius: {r('sm')}px; }}

#header {{ background: {c('bg-surface')}; border-bottom: 1px solid {c('border')}; }}
#brandName {{ font-size: {fs('h4')}px; font-weight: {w('semibold')}; }}
#brandTagline, .muted, QLabel[role="muted"] {{ color: {c('text-muted')}; font-size: {fs('sm')}px; }}
QLabel[role="secondary"] {{ color: {c('text-secondary')}; font-size: {fs('sm')}px; }}
QLabel[role="danger"] {{ color: {c('danger')}; font-weight: {w('semibold')}; }}
QLabel[role="cardTitle"] {{ font-size: {fs('body-desktop-lg')}px; font-weight: {w('semibold')}; }}
QLabel[role="fieldLabel"] {{ font-weight: {w('medium')}; }}
QLabel[role="emptyTitle"] {{ color: {c('text-secondary')}; font-size: {fs('body-desktop-lg')}px; }}

#card {{ background: {c('bg-surface')}; border: 1px solid {c('border')}; border-radius: {r('lg')}px; }}

#dropZone {{ background: {c('bg-subtle')}; border: 1px solid {c('border-control')}; border-radius: {r('lg')}px; }}
#dropZone[dragActive="true"] {{ border: 2px solid {c('primary')}; background: {c('bg-hover')}; }}

QPushButton, QToolButton {{
    min-height: {controlH}px; padding: 0 {sp(4)}px; border-radius: {r('md')}px;
    font-weight: {w('semibold')}; background: {c('bg-surface')}; color: {c('text-primary')};
    border: 1px solid {c('border-control')};
}}
QPushButton:hover, QToolButton:hover {{ background: {c('bg-hover')}; }}
QPushButton:focus, QToolButton:focus {{ border: 2px solid {c('focus-ring')}; }}
QPushButton:disabled, QToolButton:disabled {{ color: {c('text-muted')}; background: {c('bg-subtle')};
                                              border-color: {c('border')}; }}
QPushButton[variant="primary"] {{ background: {c('primary')}; color: {c('on-primary')}; border: 1px solid {c('primary')}; }}
QPushButton[variant="primary"]:hover {{ background: {c('primary-hover')}; border-color: {c('primary-hover')}; }}
QPushButton[variant="primary"]:pressed {{ background: {c('primary-active')}; }}
QPushButton[variant="primary"]:focus {{ border: 2px solid {c('focus-ring')}; }}
QPushButton[variant="primary"]:disabled {{ background: {c('bg-subtle')}; color: {c('text-muted')}; border-color: {c('border')}; }}
QPushButton[variant="ghost"], QToolButton[variant="ghost"] {{ background: transparent; border: 1px solid transparent; }}
QPushButton[variant="ghost"]:hover, QToolButton[variant="ghost"]:hover {{ background: {c('bg-hover')}; }}
QPushButton[variant="ghost"]:focus, QToolButton[variant="ghost"]:focus {{ border: 2px solid {c('focus-ring')}; }}
QToolButton::menu-indicator {{ image: none; width: 0; }}
QPushButton[variant="link"] {{ background: transparent; border: none; color: {c('text-link')};
                               padding: 0; min-height: 0; font-weight: {w('medium')}; text-decoration: underline; }}

QPushButton[role="filter"] {{ min-height: 32px; padding: 0 {sp(3)}px; font-weight: {w('medium')};
                              border-radius: {r('md')}px; }}
QPushButton[role="filter"]:checked {{ background: {c('bg-subtle')}; border: 1px solid {c('primary')}; color: {c('text-primary')}; }}

QToolButton[role="page"] {{ min-height: 32px; min-width: 32px; padding: 0 {sp(2)}px; font-weight: {w('medium')};
                            border: 1px solid {c('border')}; }}
QToolButton[role="page"][current="true"] {{ background: {c('primary')}; color: {c('on-primary')}; border: 1px solid {c('primary')}; }}
QToolButton[role="page"][current="true"]:focus {{ border: 2px solid {c('focus-ring')}; }}
QLabel[role="ellipsis"] {{ color: {c('text-muted')}; padding: 0 {sp(1)}px; }}

QLineEdit, QComboBox {{
    min-height: {controlH - 2}px; padding: 0 {sp(3)}px; border-radius: {r('md')}px;
    background: {c('bg-surface')}; border: 1px solid {c('border-control')}; color: {c('text-primary')};
    selection-background-color: {c('primary')}; selection-color: {c('on-primary')};
}}
QLineEdit:focus, QComboBox:focus {{ border: 2px solid {c('focus-ring')}; }}
QLineEdit[role="search"] {{ padding-left: {sp(1)}px; }}
QComboBox::drop-down {{ border: none; width: 28px; subcontrol-origin: padding; subcontrol-position: center right; }}
QComboBox::down-arrow {{ image: url("{arrow}"); width: 14px; height: 14px; }}
QComboBox:disabled {{ background: {c('bg-subtle')}; color: {c('text-muted')}; border-color: {c('border')}; }}
QComboBox[invalid="true"] {{ border: 1px solid {c('danger')}; }}
QComboBox[compact="true"] {{ min-height: 30px; padding: 0 {sp(2)}px; }}
QComboBox QAbstractItemView {{ background: {c('bg-surface')}; border: 1px solid {c('border-strong')};
    selection-background-color: {c('bg-hover')}; selection-color: {c('text-primary')}; padding: {sp(1)}px; outline: 0; }}

QCheckBox {{ spacing: {sp(2)}px; }}

QProgressBar {{ background: {c('bg-subtle')}; border: none; border-radius: {r('sm')}px; max-height: 6px; min-height: 6px; }}
QProgressBar::chunk {{ background: {c('primary')}; border-radius: {r('sm')}px; }}

QTableView {{ background: {c('bg-surface')}; border: none; gridline-color: {c('border')};
              selection-background-color: {c('bg-hover')}; selection-color: {c('text-primary')};
              alternate-background-color: {c('bg-surface')}; }}
QTableView::item {{ padding: 0 {sp(3)}px; border-bottom: 1px solid {c('border')}; }}
QTableView::item:hover {{ background: {c('bg-hover')}; }}
QHeaderView::section {{ background: {c('bg-subtle')}; color: {c('text-primary')}; font-weight: {w('semibold')};
    border: none; border-bottom: 1px solid {c('border')}; padding: {sp(2)}px {sp(3)}px; }}
#tableFrame {{ background: {c('bg-surface')}; border: 1px solid {c('border')}; border-radius: {r('lg')}px; }}
#tableFooter {{ background: {c('bg-subtle')}; border-top: 1px solid {c('border')};
               border-bottom-left-radius: {r('lg')}px; border-bottom-right-radius: {r('lg')}px; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle {{ background: {c('border-strong')}; border-radius: 4px; min-height: 24px; min-width: 24px; }}
QScrollBar::handle:hover {{ background: {c('border-control')}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

QMenu {{ background: {c('bg-surface')}; border: 1px solid {c('border-strong')}; border-radius: {r('md')}px; padding: {sp(1)}px; }}
QMenu::item {{ min-height: 32px; padding: 0 {sp(6)}px 0 {sp(3)}px; border-radius: {r('sm')}px; }}
QMenu::item:selected {{ background: {c('bg-hover')}; }}
QMenu::indicator {{ width: 14px; height: 14px; left: {sp(1)}px; }}

#toast {{ background: {c('bg-surface')}; border: 1px solid {c('border-strong')}; border-radius: {r('md')}px; }}
#toast[level="success"] {{ border-left: 3px solid {c('success')}; }}
#toast[level="error"] {{ border-left: 3px solid {c('danger')}; }}
#toast[level="info"] {{ border-left: 3px solid {c('info')}; }}
#statusBar {{ background: {c('bg-surface')}; border-top: 1px solid {c('border')}; }}
"""


def applyTheme(app, choice: str) -> str:
    """Áp chủ đề cho toàn app. Trả về chủ đề thật đã áp (light | dark)."""
    loadFonts()
    theme = resolveTheme(choice)
    t = loadTokens(theme)
    app.setFont(appFont(t))
    app.setPalette(buildPalette(t))
    app.setStyleSheet(buildStyleSheet(t))
    return theme
