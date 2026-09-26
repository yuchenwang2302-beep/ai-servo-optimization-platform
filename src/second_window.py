# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Main window: page composition and the shared MATLAB run lock."""
from i18n import APP_NAME, tr
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QGraphicsDropShadowEffect
from notice_dialog import NoticeDialog
from PyQt5.QtGui import QColor
from identification_tab import IdentificationTab
from optimization_tab import OptimizationTab
from responsive_page import ResponsivePage
from history_dialog import HistoryDialog, HistoryJob
from run_history import RunStore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QPushButton


class SecondWindow(QMainWindow):
    def __init__(self, *, maintenance=True):
        super().__init__()
        self.run_store = RunStore()
        self._maintenance_enabled = maintenance
        self._history_job = None
        self._history_dialog = None

        # 设置主窗口样式
        self.setWindowTitle(APP_NAME)
        available = QApplication.primaryScreen().availableGeometry()
        self.resize(min(1400, available.width() - 40), min(900, available.height() - 70))
        self.move(available.center() - self.rect().center())

        # 设置全局样式表
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QWidget {
                font: 10pt "Microsoft YaHei";
            }
            QLabel {
                color: #333333;
            }
        """)

        # 创建主窗口的中心部件
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 顶部标签页样式改进
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 5px;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #e5e7eb;
                color: #4b5563;
                min-width: 160px;
                padding: 8px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 1px solid #d1d5db;
                margin-right: 12px;
                font: bold 10pt "Microsoft YaHei";
            }
            QTabBar::tab:last {
                margin-right: 0px;
            }
            QTabBar::tab:selected {
                background: #3b82f6;
                color: white;
                border-bottom: 2px solid #2563eb;
            }
            QTabBar::tab:hover {
                background: #dbeafe;
            }
        """)
        main_layout.addWidget(tab_widget)

        self.tab_optimization = OptimizationTab(self)
        self.tab_identification = IdentificationTab(self)
        tab_widget.addTab(ResponsivePage(self.tab_identification), tr("辨识算法"))
        tab_widget.addTab(ResponsivePage(self.tab_optimization), tr("优化算法"))

        shadow = QGraphicsDropShadowEffect(central_widget)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(5, 5)
        central_widget.setGraphicsEffect(shadow)
        self.history_button = QPushButton(tr('运行记录'))
        self.history_button.clicked.connect(self.open_history)
        self.statusBar().addPermanentWidget(self.history_button)
        self._maintenance_timer = QTimer(self)
        self._maintenance_timer.setInterval(60 * 60 * 1000)
        self._maintenance_timer.timeout.connect(lambda: self.start_history_job('automatic'))
        if maintenance:
            self._maintenance_timer.start()
            QTimer.singleShot(1000, lambda: self.isVisible() and self.start_history_job('automatic'))

    def open_history(self):
        if self._history_dialog is None:
            self._history_dialog = HistoryDialog(self, self.run_store)
        screen = self.screen().availableGeometry()
        self._history_dialog.resize(min(900, screen.width() - 40), min(620, screen.height() - 60))
        self._history_dialog.show()
        self._history_dialog.raise_()
        self.start_history_job('refresh')

    def start_history_job(self, action='refresh', path=None, archived=False):
        if self._history_job is not None:
            return
        job = HistoryJob(self.run_store, action, path, archived, self)
        self._history_job = job
        if self._history_dialog is not None:
            self._history_dialog.set_busy(True)
        job.ready.connect(self.history_ready)
        job.finished.connect(self.history_finished)
        job.start()

    def history_ready(self, result):
        if self._history_dialog is not None:
            self._history_dialog.populate(result)

    def history_finished(self):
        job = self._history_job
        self._history_job = None
        if job is not None:
            job.deleteLater()
        if self._history_dialog is not None:
            self._history_dialog.set_busy(False)
        if getattr(self, '_close_after_maintenance', False):
            self.close()

    def closeEvent(self, event):
        if getattr(self, '_busy', False):
            event.ignore()
            page = getattr(self, '_active_page', None)
            if page is None or getattr(self, '_close_after_run', False):
                self.statusBar().showMessage(tr('请等待本次计算退出。'))
                return
            if getattr(self, '_close_dialog', None) is not None and self._close_dialog.isVisible():
                return
            dialog = NoticeDialog('计算尚未结束', '停止本次计算并关闭窗口？未完成的任务不会生成最终结果。',
                                  parent=self, accept_text='停止并关闭', reject_text='继续运行')
            def selected():
                self._close_after_run = True
                if getattr(self, '_busy', False):
                    page.stop_run()
                else:
                    self.close()
            dialog.accepted.connect(selected)
            self._close_dialog = dialog
            dialog.show()
            return
        if self._history_job is not None:
            self._close_after_maintenance = True
            self._history_job.requestInterruption()
            event.ignore()
            return
        self._maintenance_timer.stop()
        self.tab_identification.data_timer.stop()
        self.tab_optimization.data_timer.stop()
        event.accept()

    def set_run_busy(self, busy):
        self._busy = busy
        for page in (self.tab_identification, self.tab_optimization):
            page.run_button.setEnabled(not busy)
            page.algorithm_combo.setEnabled(not busy)
            page.runtime_minutes.setEnabled(not busy)
            page.stop_button.setEnabled(busy and page is getattr(self, '_active_page', None)
                                        and page.run_state in ('starting', 'running'))
            for field in page.params.values():
                field.setEnabled(not busy)
        self.tab_optimization.identification_combo.setEnabled(not busy)
        self.tab_optimization.function_combo.setEnabled(not busy and self.tab_optimization.identification_combo.currentData() == 'single')

    def release_run(self):
        self.set_run_busy(False)
        self._active_page = None
        if self._maintenance_enabled and not getattr(self, '_close_after_run', False):
            self.start_history_job('automatic')
        if getattr(self, '_close_after_run', False):
            self.close()
        elif getattr(self, '_close_dialog', None) is not None and self._close_dialog.isVisible():
            self._close_dialog.message.setText(tr('计算已结束，是否关闭窗口？'))
            self._close_dialog.accept_button.setText(tr('关闭窗口'))
        if self.statusBar().currentMessage() in (tr('正在释放 MATLAB 资源…'), tr('计算结束，正在完成线程清理。')):
            self.statusBar().showMessage(tr('计算完成。'))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SecondWindow()
    window.show()
    sys.exit(app.exec_())
