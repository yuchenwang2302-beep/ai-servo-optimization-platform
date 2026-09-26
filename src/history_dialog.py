# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Bilingual run history, protected archives and retention controls."""
from datetime import datetime
import numpy as np
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QAbstractItemView, QPlainTextEdit)
from i18n import tr

STATES = {'succeeded': '运行完成', 'failed': '运行失败', 'timed_out': '运行超时',
          'cancelled': '已停止', 'starting': '正在启动 MATLAB…', 'running': '正在计算',
          'cleaning': '正在释放 MATLAB 资源…', 'stopping': '正在停止'}


class HistoryJob(QThread):
    ready = pyqtSignal(object)

    def __init__(self, store, action='refresh', path=None, archived=False, parent=None):
        super().__init__(parent)
        self.store, self.action, self.path, self.archived = store, action, path, archived

    def run(self):
        try:
            summary = None
            if self.action in ('automatic', 'cleanup'):
                summary = self.store.cleanup(force=self.action == 'cleanup', cancelled=self.isInterruptionRequested)
            elif self.action == 'archive':
                self.store.archive(self.path, self.archived)
            self.ready.emit({'records': self.store.records(), 'summary': summary, 'action': self.action})
        except Exception as exc:
            self.ready.emit({'error': str(exc), 'action': self.action})


class HistoryDialog(QDialog):
    def __init__(self, owner, store):
        super().__init__(owner)
        self.owner, self.store, self.records = owner, store, []
        self.setWindowTitle(tr('运行记录'))
        self.resize(900, 620)
        layout = QVBoxLayout(self)
        note = QLabel(tr('自动清理过期记录，额外保留最新 20 次；归档记录和未结束任务不会删除。7 天前已结束任务的仿真缓存可自动清理。'))
        note.setWordWrap(True)
        layout.addWidget(note)
        settings = QHBoxLayout()
        policy = store.policy()
        self.auto = QCheckBox(tr('自动清理'))
        self.auto.setChecked(policy['enabled'])
        self.days = QSpinBox()
        self.days.setRange(7, 3650); self.days.setValue(policy['days'])
        self.days.setSuffix(tr(' 天'))
        settings.addWidget(self.auto)
        settings.addWidget(QLabel(tr('保留最近')))
        settings.addWidget(self.days)
        settings.addStretch()
        self.save_button = QPushButton(tr('保存设置'))
        self.save_button.clicked.connect(self.save_policy)
        settings.addWidget(self.save_button)
        layout.addLayout(settings)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([tr(s) for s in ('运行日期', '算法', '类型', '状态', '计算耗时', '总耗时', '归档')])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.currentCellChanged.connect(self.show_record)
        layout.addWidget(self.table, 2)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        layout.addWidget(self.details, 1)
        buttons = QHBoxLayout()
        self.open_button = QPushButton(tr('打开记录文件夹'))
        self.open_button.clicked.connect(self.open_folder)
        self.archive_button = QPushButton(tr('归档 / 取消归档'))
        self.archive_button.clicked.connect(self.toggle_archive)
        self.refresh_button = QPushButton(tr('刷新'))
        self.refresh_button.clicked.connect(lambda: owner.start_history_job('refresh'))
        self.cleanup_button = QPushButton(tr('按规则清理'))
        self.cleanup_button.clicked.connect(self.cleanup)
        for button in (self.open_button, self.archive_button, self.refresh_button, self.cleanup_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.message = QLabel(tr('正在读取运行记录…'))
        self.message.setWordWrap(True)
        layout.addWidget(self.message)

    def set_busy(self, busy):
        for widget in (self.save_button, self.archive_button, self.refresh_button, self.cleanup_button):
            widget.setEnabled(not busy)
        if busy:
            self.message.setText(tr('正在处理运行记录…'))

    def selected(self):
        row = self.table.currentRow()
        return self.records[row] if 0 <= row < len(self.records) else None

    def populate(self, result):
        if 'error' in result:
            self.message.setText(tr('记录操作未完成：{error}', error=result['error']))
            return
        previous = self.selected()
        self.records = result['records']
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.records))
        selected = 0
        for row, record in enumerate(self.records):
            state = record['state']
            def seconds(key):
                value = state.get(key)
                return tr('{seconds:.2f}秒', seconds=value) if isinstance(value, (float, int)) else '—'
            values = [datetime.fromtimestamp(record['created']).strftime('%Y-%m-%d %H:%M:%S'),
                      record['request']['algorithm'], tr('优化算法' if record['mode'] == 'optimization' else '辨识算法'),
                      tr(STATES.get(state.get('state'), '状态未知')), seconds('calculation_seconds'),
                      seconds('elapsed_seconds'), tr('已归档') if record['archived'] else '—']
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
            if previous and previous['path'] == record['path']:
                selected = row
        self.table.blockSignals(False)
        if self.records:
            self.table.selectRow(selected)
        self.show_record()
        summary = result.get('summary')
        if summary is not None:
            message = tr('已清理 {runs} 次旧运行、{caches} 项缓存，释放 {size:.1f} MiB。',
                         runs=summary['removed_runs'], caches=summary['removed_caches'], size=summary['freed_bytes']/1024**2)
            if summary['errors']:
                message += tr(' {count} 项未能清理，已跳过。', count=len(summary['errors']))
            self.message.setText(message)
        else:
            self.message.setText(tr('共 {count} 次运行。归档会保留整次运行的文件。', count=len(self.records)))

    def show_record(self, *args):
        record = self.selected()
        self.open_button.setEnabled(record is not None)
        if record is None:
            self.details.clear()
            return
        request = record['request']
        lines = [f"{tr('算法')}: {request['algorithm']}", f"{tr('状态')}: {tr(STATES.get(record['state'].get('state'), '状态未知'))}"]
        for key, value in request.get('params', {}).items():
            if key not in ('parameter_bounds',) and not key.startswith('_'):
                lines.append(f"{tr('函数选项:' if key == 'objective' else key)}: {value}")
        path = record['path'] / 'result.npz'
        if self.store.safe(path) and path.is_file():
            try:
                with np.load(path, allow_pickle=False) as data:
                    if 'parameters' in data and data['parameters'].size:
                        lines.append(f"{tr('最优参数')}: {data['parameters'].reshape(-1).tolist()}")
                        lines.append(f"{tr('目标函数')}: {float(data['best']):.8g}")
            except (OSError, ValueError, KeyError):
                lines.append(tr('结果文件不可读，请打开记录文件夹检查。'))
        lines.append(str(record['path']))
        self.details.setPlainText('\n'.join(lines))

    def open_folder(self):
        record = self.selected()
        if record and self.store.safe(record['path']) and record['path'].is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(record['path'])))

    def toggle_archive(self):
        record = self.selected()
        if record:
            self.owner.start_history_job('archive', record['path'], not record['archived'])

    def save_policy(self):
        try:
            self.store.save_policy(self.auto.isChecked(), self.days.value())
            self.message.setText(tr('清理设置已保存，下次自动检查时生效。'))
            return True
        except (OSError, ValueError) as exc:
            self.message.setText(tr('记录操作未完成：{error}', error=exc))
            return False

    def cleanup(self):
        if self.save_policy():
            self.owner.start_history_job('cleanup')
