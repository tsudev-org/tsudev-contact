# -*- coding: utf-8 -*-
"""Bước 2: ghép cột CSV vào trường vCard, kèm giá trị mẫu để người dùng nhận ra cột."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QWidget

from src.engine.csv_source import CsvData
from src.engine.fields import FIELDS, REQUIRED_FIELDS, guessMapping
from src.i18n import tr
from src.services.tokens import Tokens
from src.ui.widgets import label, repolish

SAMPLE_MAX_CHARS = 40


class MappingPanel(QWidget):
    changed = Signal()

    def __init__(self, t: Tokens, parent=None):
        super().__init__(parent)
        self.data: CsvData | None = None
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(t.space(3))
        grid.setVerticalSpacing(t.space(1))
        grid.setColumnStretch(1, 1)
        self.labels: dict[str, QLabel] = {}
        self.combos: dict[str, QComboBox] = {}
        self.samples: dict[str, QLabel] = {}
        for i, name in enumerate(FIELDS):
            nameLabel = label('', 'fieldLabel')
            labelBox = QHBoxLayout()
            labelBox.setSpacing(2)
            labelBox.addWidget(nameLabel)
            if name in REQUIRED_FIELDS:
                star = label('*', 'danger')
                star.setAccessibleName('')
                labelBox.addWidget(star)
            labelBox.addStretch(1)
            combo = QComboBox()
            combo.setProperty('compact', True)
            combo.setEnabled(False)
            combo.setMinimumWidth(120)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(12)
            combo.currentIndexChanged.connect(lambda _=0, n=name: self._onChanged(n))
            nameLabel.setBuddy(combo)
            sample = label('', 'muted')
            sample.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            grid.addLayout(labelBox, i * 2, 0, Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(combo, i * 2, 1)
            grid.addWidget(sample, i * 2 + 1, 1)
            self.labels[name], self.combos[name], self.samples[name] = nameLabel, combo, sample
        self.retranslate()

    def retranslate(self) -> None:
        for name in FIELDS:
            text = tr(f'field.{name}')
            self.labels[name].setText(text)
            self.combos[name].setAccessibleName(text + (' *' if name in REQUIRED_FIELDS else ''))
            if self.combos[name].count():
                self.combos[name].setItemText(0, tr('step2.unused'))
            self._updateSample(name)

    def setData(self, data: CsvData) -> None:
        self.data = data
        guessed = guessMapping(data.headers)
        for name in FIELDS:
            combo = self.combos[name]
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(tr('step2.unused'), None)
            for header in data.headers:
                combo.addItem(header, header)
            target = guessed.get(name)
            combo.setCurrentIndex(data.headers.index(target) + 1 if target else 0)
            combo.setEnabled(True)
            combo.blockSignals(False)
            self._updateSample(name)
            self._markInvalid(name)
        self.changed.emit()

    def mapping(self) -> dict[str, str | None]:
        return {name: self.combos[name].currentData() for name in FIELDS}

    def isComplete(self) -> bool:
        current = self.mapping()
        return self.data is not None and all(current[name] for name in REQUIRED_FIELDS)

    def _onChanged(self, name: str) -> None:
        self._updateSample(name)
        self._markInvalid(name)
        self.changed.emit()

    def _markInvalid(self, name: str) -> None:
        combo = self.combos[name]
        combo.setProperty('invalid', name in REQUIRED_FIELDS and self.data is not None and not combo.currentData())
        repolish(combo)

    def _updateSample(self, name: str) -> None:
        sampleLabel = self.samples[name]
        header = self.combos[name].currentData()
        if not self.data or not header:
            sampleLabel.setText('')
            sampleLabel.setVisible(False)
            return
        value = self.data.sampleValue(header).replace('\n', ' ')
        if len(value) > SAMPLE_MAX_CHARS:
            value = value[:SAMPLE_MAX_CHARS - 1] + '…'
        # Hiển thị dạng văn bản thuần: dữ liệu CSV không bao giờ được hiểu là HTML.
        sampleLabel.setTextFormat(Qt.TextFormat.PlainText)
        sampleLabel.setText(tr('step2.sample', value=value) if value else tr('step2.noSample'))
        sampleLabel.setVisible(True)
