# -*- coding: utf-8 -*-
"""Hộp thoại Giới thiệu - ECOSYSTEM_IDENTITY mục 2.3: dấu hiệu, tên, phiên bản, liên kết tsudev.com."""
from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from src.app_info import APP_SLUG, APP_VERSION, COPYRIGHT, ECOSYSTEM_URL, REPO_URL, SUPPORT_URL
from src.i18n import tr
from src.services.tokens import Tokens
from src.ui.widgets import button, label
from src.utils.resource_path import resourcePath

# Chỉ mở đúng các địa chỉ cố định này - không bao giờ mở URL lấy từ dữ liệu người dùng.
_ALLOWED_URLS = (SUPPORT_URL, ECOSYSTEM_URL, REPO_URL)


def openTrustedUrl(url: str) -> bool:
    if url not in _ALLOWED_URLS:
        return False
    return QDesktopServices.openUrl(QUrl(url))


class AboutDialog(QDialog):
    def __init__(self, t: Tokens, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('about.title'))
        self.setModal(True)
        self.setFixedWidth(440)
        root = QVBoxLayout(self)
        root.setContentsMargins(t.space(6), t.space(6), t.space(6), t.space(6))
        root.setSpacing(t.space(4))

        head = QHBoxLayout()
        head.setSpacing(t.space(4))
        logo = QLabel()
        pm = QPixmap(resourcePath('assets/icons/app-128.png'))
        pm.setDevicePixelRatio(2.0)
        logo.setPixmap(pm)
        logo.setAccessibleName('tsudev')
        titles = QVBoxLayout()
        titles.setSpacing(t.space(1))
        name = label(APP_SLUG)
        name.setObjectName('brandName')
        titles.addWidget(name)
        titles.addWidget(label(tr('about.version', version=APP_VERSION), 'secondary'))
        titles.addStretch(1)
        head.addWidget(logo)
        head.addLayout(titles, 1)
        root.addLayout(head)

        root.addWidget(label(tr('about.description'), wrap=True))

        for text, url in ((tr('about.product'), SUPPORT_URL), (tr('about.ecosystem'), ECOSYSTEM_URL),
                          (tr('about.source'), REPO_URL)):
            row = QHBoxLayout()
            row.addWidget(label(text, 'secondary'))
            row.addStretch(1)
            link = button(url.replace('https://', ''), 'link')
            link.setToolTip(url)
            link.clicked.connect(lambda _=False, u=url: openTrustedUrl(u))
            row.addWidget(link)
            root.addLayout(row)

        root.addWidget(label(COPYRIGHT, 'muted'))
        footer = QHBoxLayout()
        footer.addStretch(1)
        close = button(tr('common.close'), 'primary')
        close.setDefault(True)
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        root.addLayout(footer)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
