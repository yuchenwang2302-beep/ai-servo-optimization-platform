# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Small nonblocking dialogs without QMessageBox's platform-dependent internals."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from i18n import tr


class NoticeDialog(QDialog):
    def __init__(self, title, message, parent=None, accept_text='返回修改', reject_text=None):
        super().__init__(parent)
        title, message, accept_text = tr(title), tr(message), tr(accept_text)
        reject_text = tr(reject_text) if reject_text else None
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModal)
        self.setMinimumWidth(420)
        self.setMaximumWidth(560)
        self.setStyleSheet('QDialog {background:#ffffff;} QLabel {color:#334155; font:10pt "Microsoft YaHei";} '
                          'QPushButton {min-width:90px; padding:8px 14px; border:1px solid #cbd5e1; border-radius:5px;}')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(16)
        heading = QLabel(title)
        heading.setStyleSheet('font:bold 12pt "Microsoft YaHei"; color:#a4262c;')
        layout.addWidget(heading)
        self.message = QLabel(message)
        self.message.setTextFormat(Qt.PlainText)
        self.message.setWordWrap(True)
        self.message.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.message)
        row = QHBoxLayout()
        row.addStretch()
        self.accept_button = QPushButton(accept_text)
        self.accept_button.clicked.connect(self.accept)
        row.addWidget(self.accept_button)
        if reject_text:
            self.reject_button = QPushButton(reject_text)
            self.reject_button.clicked.connect(self.reject)
            self.reject_button.setDefault(True)
            row.addWidget(self.reject_button)
        else:
            self.accept_button.setDefault(True)
        layout.addLayout(row)
