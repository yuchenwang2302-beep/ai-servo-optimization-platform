# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Bilingual sign-in screen with an embedded campus photograph."""
from PyQt5 import QtCore, QtGui, QtWidgets

import codes_rc  # Registers the photograph independently of the working directory.
from i18n import APP_NAME, LANGUAGES, load_language, set_language, tr
from second_window import SecondWindow


class CampusPanel(QtWidgets.QWidget):
    """Crop the photograph proportionally; keep its gradient out of child widgets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.photo = QtGui.QPixmap(':/try/school.jpg')
        self.setMinimumWidth(300)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QtGui.QColor('#102d46'))
        if not self.photo.isNull():
            scale = max(self.width() / self.photo.width(), self.height() / self.photo.height())
            source_width, source_height = self.width() / scale, self.height() / scale
            # Keep the central building in view as the window changes shape.
            source = QtCore.QRectF((self.photo.width() - source_width) * 0.62,
                                  (self.photo.height() - source_height) * 0.5,
                                  source_width, source_height)
            painter.drawPixmap(QtCore.QRectF(self.rect()), self.photo, source)
        shade = QtGui.QLinearGradient(0, 0, 0, self.height())
        for position, alpha in ((0, 18), (0.35, 45), (0.65, 195), (1, 250)):
            shade.setColorAt(position, QtGui.QColor(13, 36, 56, alpha))
        painter.fillRect(self.rect(), shade)


class LanguageCombo(QtWidgets.QComboBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor('#61758a'), 1.4,
                                QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
        x, y = self.width() - 14, self.height() / 2
        painter.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(x - 3, y - 1.5),
                                             QtCore.QPointF(x, y + 1.5),
                                             QtCore.QPointF(x + 3, y - 1.5)]))


def _eye_icon(visible):
    """Draw both icon states at high resolution without an extra image dependency."""
    pixmap = QtGui.QPixmap(48, 48)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.scale(2, 2)
    painter.setPen(QtGui.QPen(QtGui.QColor('#61758a'), 1.6,
                            QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
    outline = QtGui.QPainterPath(QtCore.QPointF(2, 12))
    outline.cubicTo(7, 4, 17, 4, 22, 12)
    outline.cubicTo(17, 20, 7, 20, 2, 12)
    painter.drawPath(outline)
    painter.drawEllipse(QtCore.QPointF(12, 12), 3, 3)
    if visible:
        painter.drawLine(QtCore.QPointF(4, 3), QtCore.QPointF(20, 21))
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QtGui.QIcon(pixmap)


class PasswordEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEchoMode(self.Password)
        self.setTextMargins(0, 0, 36, 0)
        self.visibility_button = QtWidgets.QToolButton(self)
        self.visibility_button.setObjectName('passwordVisibility')
        self.visibility_button.setCheckable(True)
        self.visibility_button.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.visibility_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.visibility_button.setIconSize(QtCore.QSize(20, 20))
        self.visibility_button.toggled.connect(self._set_visible)
        self.refresh_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.visibility_button.setGeometry(self.width() - 39, (self.height() - 32) // 2, 32, 32)

    def _set_visible(self, visible):
        self.setEchoMode(self.Normal if visible else self.Password)
        self.refresh_text()

    def refresh_text(self):
        visible = self.visibility_button.isChecked()
        label = tr('隐藏密码' if visible else '显示密码')
        self.visibility_button.setIcon(_eye_icon(visible))
        self.visibility_button.setToolTip(label)
        self.visibility_button.setAccessibleName(label)


class Ui_Dialog:
    def setupUi(self, Dialog):
        selected_language = load_language()
        Dialog.setObjectName('Dialog')
        Dialog.setFont(QtGui.QFont('Microsoft YaHei', 10))
        Dialog.setMinimumSize(680, 440)
        screen = Dialog.screen() or QtWidgets.QApplication.primaryScreen()
        available = screen.availableGeometry()
        Dialog.resize(min(900, available.width() - 40), min(560, available.height() - 70))
        Dialog.setStyleSheet('''
            QDialog#Dialog, QWidget#loginForm { background: #ffffff; }
            QLabel { background: transparent; color: #233f54; font-size: 14px; }
            QLabel#projectTitle { color: #ffffff; font-size: 32px; font-weight: 600; }
            QLabel#projectDescription { color: #dbe8f2; font-size: 14px; }
            QLabel#welcomeTitle { color: #18364d; font-size: 26px; font-weight: 600; }
            QLabel#loginDescription { color: #687b8d; font-size: 13px; }
            QLabel#demoHint { color: #687b8d; font-size: 12px; }
            QLabel#languageLabel { color: #687b8d; font-size: 12px; }
            QLineEdit {
                color: #203b50; background: #f8fafc; border: 1px solid #d7e1e9;
                border-radius: 6px; padding: 0 12px; font-size: 14px;
                selection-background-color: #327de2;
            }
            QLineEdit:hover { border-color: #a7b9ca; }
            QLineEdit:focus { border: 1px solid #327de2; background: #ffffff; }
            QComboBox {
                color: #334d63; background: #f8fafc; border: 1px solid #dce5ed;
                border-radius: 5px; padding: 4px 10px; font-size: 12px;
            }
            QComboBox:focus { border-color: #327de2; }
            QComboBox::drop-down { width: 24px; border: none; }
            QComboBox::down-arrow { image: none; }
            QComboBox QAbstractItemView { color: #233f54; background: #ffffff; }
            QPushButton#pushButton {
                color: #ffffff; background: #327de2; border: 1px solid #327de2;
                border-radius: 6px; font-size: 14px; font-weight: 600;
            }
            QPushButton#pushButton:hover { background: #246bcb; border-color: #246bcb; }
            QPushButton#pushButton:pressed { background: #1b5bb3; }
            QPushButton#pushButton:focus { border: 2px solid #163e72; }
            QToolButton#passwordVisibility {
                background: transparent; border: 1px solid transparent; border-radius: 4px;
            }
            QToolButton#passwordVisibility:hover { background: #e9f0f7; }
            QToolButton#passwordVisibility:focus { border-color: #327de2; }
        ''')

        layout = QtWidgets.QHBoxLayout(Dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.frame = CampusPanel(Dialog)
        layout.addWidget(self.frame, 10)
        hero = QtWidgets.QVBoxLayout(self.frame)
        hero.setContentsMargins(32, 32, 32, 38)
        hero.setSpacing(0)
        hero.addStretch()
        accent = QtWidgets.QFrame()
        accent.setFixedSize(36, 3)
        accent.setStyleSheet('background: #80b7fc; border: none;')
        hero.addWidget(accent)
        hero.addSpacing(20)
        self.label = QtWidgets.QLabel(APP_NAME.replace(' Optimization', '\nOptimization')
                                     .replace(' Platform', '\nPlatform'))
        self.label.setObjectName('projectTitle')
        hero.addWidget(self.label)
        hero.addSpacing(16)
        self.project_description = QtWidgets.QLabel()
        self.project_description.setObjectName('projectDescription')
        self.project_description.setWordWrap(True)
        hero.addWidget(self.project_description)

        self.widget = QtWidgets.QWidget(Dialog)
        self.widget.setObjectName('loginForm')
        self.widget.setMinimumWidth(380)
        layout.addWidget(self.widget, 11)
        form = QtWidgets.QVBoxLayout(self.widget)
        form.setContentsMargins(36, 24, 36, 24)
        form.setSpacing(0)
        self.language_widget = QtWidgets.QWidget()
        language_layout = QtWidgets.QHBoxLayout(self.language_widget)
        language_layout.setContentsMargins(0, 0, 0, 0)
        language_layout.setSpacing(10)
        language_layout.addStretch()
        self.language_label = QtWidgets.QLabel()
        self.language_label.setObjectName('languageLabel')
        language_layout.addWidget(self.language_label)
        self.language_combo = LanguageCombo()
        self.language_combo.setObjectName('languageCombo')
        self.language_combo.setMinimumSize(106, 32)
        for text, code in LANGUAGES:
            self.language_combo.addItem(text, code)
        self.language_combo.setCurrentIndex(self.language_combo.findData(selected_language))
        self.language_label.setBuddy(self.language_combo)
        language_layout.addWidget(self.language_combo)
        form.addWidget(self.language_widget)
        form.addStretch()
        self.welcome_label = QtWidgets.QLabel()
        self.welcome_label.setObjectName('welcomeTitle')
        form.addWidget(self.welcome_label)
        form.addSpacing(8)
        self.description = QtWidgets.QLabel()
        self.description.setObjectName('loginDescription')
        self.description.setWordWrap(True)
        form.addWidget(self.description)
        form.addSpacing(26)
        self.label_2 = QtWidgets.QLabel()
        form.addWidget(self.label_2)
        form.addSpacing(8)
        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setObjectName('lineEdit')
        self.lineEdit.setFixedHeight(44)
        self.label_2.setBuddy(self.lineEdit)
        form.addWidget(self.lineEdit)
        form.addSpacing(18)
        self.label_3 = QtWidgets.QLabel()
        form.addWidget(self.label_3)
        form.addSpacing(8)
        self.lineEdit_2 = PasswordEdit()
        self.lineEdit_2.setObjectName('lineEdit_2')
        self.lineEdit_2.setFixedHeight(44)
        self.label_3.setBuddy(self.lineEdit_2)
        form.addWidget(self.lineEdit_2)
        form.addSpacing(24)
        self.pushButton = QtWidgets.QPushButton()
        self.pushButton.setObjectName('pushButton')
        self.pushButton.setFixedHeight(46)
        self.pushButton.setCursor(QtCore.Qt.PointingHandCursor)
        self.pushButton.setDefault(True)
        form.addWidget(self.pushButton)
        form.addSpacing(16)
        self.demo_hint = QtWidgets.QLabel()
        self.demo_hint.setObjectName('demoHint')
        self.demo_hint.setAlignment(QtCore.Qt.AlignCenter)
        self.demo_hint.setWordWrap(True)
        form.addWidget(self.demo_hint)
        form.addStretch()

        self.language_combo.currentIndexChanged.connect(lambda: self.change_language(Dialog))
        self.pushButton.clicked.connect(lambda: self.handle_login(Dialog))
        focus_order = (self.lineEdit, self.lineEdit_2, self.lineEdit_2.visibility_button,
                       self.pushButton, self.language_combo)
        for first, second in zip(focus_order, focus_order[1:]):
            Dialog.setTabOrder(first, second)
        self.retranslateUi(Dialog)
        self.lineEdit.setFocus()
        Dialog.move(available.center() - Dialog.rect().center())

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(f'{APP_NAME} · {tr("登录")}')
        self.project_description.setText(tr('参数辨识 · 控制优化'))
        self.welcome_label.setText(tr('欢迎使用'))
        self.description.setText(tr('登录以进入伺服系统研究工作台。'))
        self.pushButton.setText(tr('登录'))
        self.language_label.setText(tr('语言'))
        self.language_combo.setAccessibleName(tr('语言'))
        self.label_2.setText(tr('账号'))
        self.label_3.setText(tr('密码'))
        self.lineEdit.setAccessibleName(tr('账号'))
        self.lineEdit_2.setAccessibleName(tr('密码'))
        self.lineEdit.setPlaceholderText(tr('请输入账号'))
        self.lineEdit_2.setPlaceholderText(tr('请输入密码'))
        self.lineEdit_2.refresh_text()
        self.demo_hint.setText(tr('演示账号与密码均为 111'))

    def change_language(self, Dialog):
        set_language(self.language_combo.currentData(), persist=True)
        self.retranslateUi(Dialog)

    def handle_login(self, Dialog):
        if self.lineEdit.text() == '111' and self.lineEdit_2.text() == '111':
            self.open_next_window(Dialog)
        else:
            from notice_dialog import NoticeDialog
            self._error_dialog = NoticeDialog('登录失败', '账号或密码错误，请检查后重试。',
                                              Dialog, accept_text='返回登录')
            self._error_dialog.finished.connect(lambda: QtCore.QTimer.singleShot(0, self._focus_retry))
            self._error_dialog.finished.connect(self._error_dialog.deleteLater)
            self._error_dialog.show()

    def _focus_retry(self):
        field = self.lineEdit if self.lineEdit.text() != '111' else self.lineEdit_2
        if field.window().isVisible():
            field.window().activateWindow()
            field.setFocus(QtCore.Qt.OtherFocusReason)
            field.selectAll()

    def open_next_window(self, Dialog):
        self.second_window = SecondWindow()
        self.second_window.show()
        Dialog.close()


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(dialog)
    dialog.show()
    sys.exit(app.exec_())
