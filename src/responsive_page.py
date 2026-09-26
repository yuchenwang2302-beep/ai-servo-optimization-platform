# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""A scrollable page that stacks controls above plots on narrow displays."""
from PyQt5.QtWidgets import QScrollArea, QFrame, QBoxLayout, QSizePolicy


class ResponsivePage(QScrollArea):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.compact = None
        self.setFrameShape(QFrame.NoFrame)
        self.setWidgetResizable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(0, 0)
        self.setWidget(page)
        page.setAutoFillBackground(False)
        self.setStyleSheet('QScrollArea {background:transparent; border:none;}')

    def resizeEvent(self, event):
        compact = self.viewport().width() < 1100
        if compact != self.compact:
            self.compact = compact
            layout = self.page.layout()
            layout.setDirection(QBoxLayout.BottomToTop if compact else QBoxLayout.LeftToRight)
            layout.setStretch(0, 0 if compact else (3 if self.page.is_optimization else 1))
            layout.setStretch(1, 0 if compact else (2 if self.page.is_optimization else 1))
            self.page.updateGeometry()
        super().resizeEvent(event)
