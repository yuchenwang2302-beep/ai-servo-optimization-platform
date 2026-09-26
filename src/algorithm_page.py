# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Shared form, run lifecycle and convergence display for the two Qt pages."""
from i18n import tr
from pathlib import Path
import logging
import time

import numpy as np
from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                            QPushButton, QSpinBox, QProgressBar, QLayout, QSizePolicy)
from notice_dialog import NoticeDialog

from algorithm_catalog import IDENTIFICATION, SINGLE, MULTI, default_parameters, data_filename
from matlab_worker import MatlabWorker
from project_paths import data_directory
from run_support import validate_params, read_curve, ParameterValidationError, parameter_rules

logger = logging.getLogger(__name__)


class FieldErrorLabel(QLabel):
    """Keep wrapped feedback readable inside the fixed-height parameter scroller."""
    def __init__(self):
        super().__init__()
        self.setWordWrap(True)
        self.setStyleSheet('color:#b4232a; font-size:9pt; border:none; background:transparent;')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def setText(self, text):
        super().setText(text)
        self.setMinimumHeight(max(0, self.heightForWidth(self.width())) if text else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.text():
            self.setMinimumHeight(max(0, self.heightForWidth(event.size().width())))


class AlgorithmPage(QWidget):
    def __init__(self, parent, optimization=False, data_folder=None):
        super().__init__(parent)
        self.parent_window = parent
        self.is_optimization = optimization
        self.data_folder = str(data_folder or data_directory(optimization))
        algorithms = tuple(SINGLE) + MULTI if optimization else IDENTIFICATION
        self.data_files = {name: str(Path(self.data_folder) / data_filename(name, optimization))
                           for name in algorithms}
        self.gb_data = np.array([])
        self.last_update_iter = 0
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.check_data_update)
        self.run_state = 'idle'
        self._touched = set()
        self._validation_timer = QTimer(self)
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self.validate_visible_fields)
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self.update_elapsed)
        self._read_failures = 0

    def setup_run_controls(self, layout):
        box = QWidget(self)
        column = QVBoxLayout(box)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(5)
        self.validation_summary = QLabel()
        self.validation_summary.setWordWrap(True)
        self.validation_summary.setStyleSheet('color:#a4262c; background:#fff0f0; border-radius:5px; padding:5px;')
        self.validation_summary.hide()
        column.addWidget(self.validation_summary)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.run_button.setFixedSize(240, 44)
        buttons.addWidget(self.run_button)
        self.stop_button = QPushButton(tr('停止计算'))
        self.stop_button.setFixedSize(105, 44)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet('QPushButton {border:1px solid #d1d5db; border-radius:6px; padding:5px;} '
                                      'QPushButton:enabled {color:#a4262c; background:#fff5f5;}')
        self.stop_button.clicked.connect(self.stop_run)
        buttons.addWidget(self.stop_button)
        buttons.addStretch()
        column.addLayout(buttons)
        options = QHBoxLayout()
        options.addWidget(QLabel(tr('最长计算')))
        self.runtime_minutes = QSpinBox()
        self.runtime_minutes.setRange(1, 1440)
        self.runtime_minutes.setValue(240)
        self.runtime_minutes.setSuffix(tr(' 分钟'))
        self.runtime_minutes.setToolTip(tr('从开始计算计时。达到时限后停止本次任务；MATLAB 启动与退出另设保护时限。'))
        options.addWidget(self.runtime_minutes)
        options.addStretch()
        self.log_button = QPushButton(tr('查看日志'))
        self.log_button.setEnabled(False)
        self.log_button.clicked.connect(self.open_run_logs)
        options.addWidget(self.log_button)
        column.addLayout(options)
        self.elapsed_label = QLabel('')
        self.elapsed_label.setWordWrap(True)
        column.addWidget(self.elapsed_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(tr('尚未运行'))
        self.progress_bar.setStyleSheet('QProgressBar {border:1px solid #d1d5db; border-radius:4px; text-align:center;} '
                                       'QProgressBar::chunk {background:#93c5fd; border-radius:3px;}')
        column.addWidget(self.progress_bar)
        self.run_status_label = QLabel(tr('完成一次迭代后更新进度与曲线。'))
        self.run_status_label.setWordWrap(True)
        self.run_status_label.setStyleSheet('color:#526578; font-size:9pt;')
        column.addWidget(self.run_status_label)
        self.curve_warning = QLabel()
        self.curve_warning.setWordWrap(True)
        self.curve_warning.setStyleSheet('color:#9a5b00; font-size:9pt;')
        self.curve_warning.hide()
        column.addWidget(self.curve_warning)
        layout.addWidget(box)

    def open_run_logs(self):
        if hasattr(self, 'worker') and Path(self.worker.data_folder).is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.worker.data_folder))

    def update_elapsed(self):
        total, calculation = self.run_timings()
        def clock(value):
            hours, rest = divmod(int(value), 3600)
            minutes, seconds = divmod(rest, 60)
            return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
        self.elapsed_label.setText(tr('计算耗时 {calculation} / 总耗时 {total}',
                                       calculation=clock(calculation), total=clock(total)))
        self.log_button.setEnabled(Path(self.worker.data_folder).is_dir())

    def run_timings(self):
        worker = getattr(self, 'worker', None)
        if hasattr(worker, 'timings'):
            return worker.timings()
        now = time.monotonic()
        total = max(0., getattr(self, '_run_ended', None) or now) - getattr(self, '_run_started', now)
        start = getattr(self, '_calculation_started', None)
        calculation = max(0., (getattr(self, '_calculation_ended', None) or now) - start) if start else 0.
        return max(0., total), calculation

    def handle_run_state(self, state):
        if state == 'running' and getattr(self, '_calculation_started', None) is None:
            self._calculation_started = time.monotonic()
        elif state != 'running' and getattr(self, '_calculation_started', None) is not None and getattr(self, '_calculation_ended', None) is None:
            self._calculation_ended = time.monotonic()
        self.run_state = state
        self.stop_button.setEnabled(state in ('starting', 'running'))
        if state == 'starting':
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, self._run_params['最大迭代次数 (T)'])
            self.progress_bar.setValue(self.last_update_iter)
            self.progress_bar.setFormat(tr('%v / %m 次迭代'))
        color = '#a4262c' if state in ('failed', 'timed_out') else '#526578'
        self.run_status_label.setStyleSheet(f'color:{color}; font-size:9pt;')

    def handle_run_status(self, text):
        text = tr(text)
        self.run_status_label.setText(text)
        self.parent_window.statusBar().showMessage(text)

    def handle_progress(self, iteration, total):
        self.last_update_iter = max(self.last_update_iter, iteration)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(self.last_update_iter)
        self.progress_bar.setFormat(tr('%v / %m 次迭代'))

    def stop_run(self):
        if hasattr(self, 'worker') and getattr(self.parent_window, '_busy', False):
            self.worker.stop()
            self.handle_run_state('stopping')
            self.handle_run_status('正在停止本次计算并清理资源…')

    def handle_worker_cancelled(self):
        self.check_data_update()
        self.update_info_labels({'状态': '已停止', '完成迭代': str(self.last_update_iter),
                                 '说明': '本次未生成完整结果，可调整参数后重新运行。'})

    def finish_run(self):
        self._run_ended = time.monotonic()
        self.data_timer.stop()
        self.elapsed_timer.stop()
        self.update_elapsed()
        self.stop_button.setEnabled(False)
        self.run_button.setText(tr('重新运行' if self.run_state in ('failed', 'timed_out', 'cancelled') else '运行算法'))
        self.parent_window.release_run()

    def form_values(self):
        values = {key: widget.text() for key, widget in self.params.items()}
        if self.is_optimization:
            values['objective'] = self.function_combo.currentText()
        return values

    def validate_visible_fields(self):
        if getattr(self.parent_window, '_busy', False):
            return
        try:
            validate_params(self.current_algorithm, self.form_values(), self.is_optimization)
            errors = {}
        except ParameterValidationError as exc:
            errors = exc.field_errors
        self.show_field_errors(errors, self._touched)

    def field_edited(self, name, field, immediate=False):
        if self.params.get(name) is not field:
            return
        self._touched.add(name)
        if immediate:
            self.validate_visible_fields()
        else:
            self._validation_timer.start(350)

    def show_field_errors(self, errors, fields=None):
        visible_errors = 0
        for name, field in self.params.items():
            message = errors.get(name, '') if fields is None or name in fields else ''
            field.setProperty('invalid', bool(message))
            field.style().unpolish(field)
            field.style().polish(field)
            self.field_error_labels[name].setText(message)
            self.field_error_labels[name].setVisible(bool(message))
            visible_errors += bool(message)
        self.validation_summary.setText(tr('请修正红色标记的 {count} 项参数后再运行。', count=visible_errors))
        self.validation_summary.setVisible(bool(visible_errors))

    def explain_invalid_parameters(self, errors):
        self._touched = set(self.params)
        self.show_field_errors(errors)
        name = next((key for key in self.params if key in errors), None)
        def focus_error():
            if name in self.params:
                field = self.params[name]
                self.param_scroll_area.ensureWidgetVisible(field.parentWidget(), 10, 10)
                self.parent_window.activateWindow()
                field.setFocus(Qt.OtherFocusReason)
                field.selectAll()
        focus_error()
        if getattr(self, 'validation_dialog', None) is not None and self.validation_dialog.isVisible():
            return
        dialog = NoticeDialog('请检查输入参数', '\n\n'.join(list(errors.values())[:4]), self.parent_window)
        def dismissed(_):
            QTimer.singleShot(0, focus_error)
            self.validation_dialog = None
            dialog.deleteLater()
        dialog.finished.connect(dismissed)
        self.validation_dialog = dialog
        dialog.show()

    def algorithm_selected(self):
        self._validation_timer.stop()
        self._touched.clear()
        self.field_error_labels = {}
        self.validation_summary.hide()
        while self.param_form_layout.count():
            child = self.param_form_layout.takeAt(0)
            if child.widget():
                child.widget().hide()
                child.widget().deleteLater()
        self.param_form_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.param_form_layout.setFormAlignment(Qt.AlignTop)
        self.current_algorithm = self.algorithm_combo.currentText()
        self.params = {key: QLineEdit(value) for key, value in
                       default_parameters(self.current_algorithm, self.is_optimization).items()}
        for key, field in self.params.items():
            label = QLabel(tr(key))
            label.setFont(QFont('Microsoft YaHei', 12))
            label.setStyleSheet("font: 12pt 'Microsoft YaHei'; color: #24898f;")
            holder = QWidget()
            holder.setObjectName('parameterField')
            holder.setStyleSheet('QWidget#parameterField {border:none; background:transparent;}')
            holder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            column = QVBoxLayout(holder)
            column.setSizeConstraint(QLayout.SetMinimumSize)
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(2)
            field.setStyleSheet('QLineEdit {border:1px solid #a3abbd; border-radius:4px; padding:3px; min-height:18px; background:#f9fafb;} '
                               'QLineEdit[invalid="true"] {border:2px solid #d9363e; background:#fff5f5;} '
                               'QLineEdit[readOnly="true"] {color:#64748b; background:#f1f5f9;}')
            rule = parameter_rules(self.current_algorithm, self.is_optimization).get(key)
            if rule and rule[0] == rule[1]:
                field.setReadOnly(True)
                field.setToolTip(tr('模型固定参数，无需修改。'))
            elif rule:
                field.setToolTip(tr('请输入 {lower}–{upper} 的整数。', lower=rule[0], upper=rule[1]) + (tr(' IA 要求偶数。') if self.current_algorithm == 'IA' and '(N)' in key else ''))
            elif '(t' in key:
                field.setToolTip(tr('格式：[下限, 上限]，两者为正且下限小于上限；支持科学计数法。'))
            error_label = FieldErrorLabel()
            error_label.hide()
            self.field_error_labels[key] = error_label
            column.addWidget(field)
            column.addWidget(error_label)
            self.param_form_layout.addRow(label, holder)
            field.textEdited.connect(lambda _, name=key, item=field: self.field_edited(name, item))
            field.editingFinished.connect(lambda name=key, item=field: self.field_edited(name, item, True))

    @property
    def convergence_plot(self):
        if self.is_optimization:
            return self.convergence_ax, self.convergence_canvas
        return self.ax, self.canvas

    @property
    def curve_ylabel(self):
        algorithm = getattr(self, '_run_algorithm', self.current_algorithm)
        return tr('HV（超体积）' if self.is_optimization and algorithm in MULTI else '适应度值')

    def start_run(self, *, confirmed=False):
        owner = self.parent_window
        if getattr(owner, '_busy', False):
            owner.statusBar().showMessage(tr('已有算法正在运行，请等待完成。'))
            return
        try:
            params = validate_params(self.current_algorithm, self.form_values(), self.is_optimization)
        except ParameterValidationError as exc:
            owner.statusBar().showMessage(tr('参数错误：{error}', error=exc))
            self.explain_invalid_parameters(exc.field_errors)
            return
        self.show_field_errors({})
        population = params.get('群体粒子个数 (N)', params.get('种群大小 (N)', 0))
        large = (population >= 1000 or params.get('存档大小 (ArchiveMaxSize)', 0) >= 2000
                 or population * params['最大迭代次数 (T)'] >= 100000)
        if large and not confirmed:
            if getattr(self, 'workload_dialog', None) is not None and self.workload_dialog.isVisible():
                return
            self.workload_dialog = NoticeDialog('计算规模较大',
                tr('当前种群、存档或迭代设置可能需要较长计算时间，并占用较多内存。建议先用较小设置验证。\n\n本次最长计算时间：{minutes} 分钟。是否继续？', minutes=self.runtime_minutes.value()), self.parent_window,
                accept_text='继续计算', reject_text='返回修改')
            self.workload_dialog.accepted.connect(lambda: self.start_run(confirmed=True))
            self.workload_dialog.show()
            return
        self._run_algorithm = self.current_algorithm
        self._run_params = params
        self.start_time = time.time()
        self._run_started = time.monotonic()
        self._run_ended = self._calculation_started = self._calculation_ended = None
        self._read_failures = 0
        self.curve_warning.hide()
        self.last_update_iter = 0
        self.gb_data = np.array([])
        self.clear_info_labels()
        self.add_info_label('状态', '正在启动 MATLAB…')
        self.worker = MatlabWorker(self._run_algorithm, params, self.is_optimization, self.data_folder,
                                   runtime_limit_seconds=self.runtime_minutes.value() * 60)
        owner._active_page = self
        self.data_files[self._run_algorithm] = self.worker.data_file
        signal = self.worker.optimization_finished if self.is_optimization else self.worker.identification_finished
        signal.connect(self.final_results_received)
        self.worker.error.connect(self.handle_worker_error)
        self.worker.status.connect(self.handle_run_status)
        self.worker.state_changed.connect(self.handle_run_state)
        self.worker.progress.connect(self.handle_progress)
        self.worker.finished.connect(self.finish_run)
        self.worker.cancelled.connect(self.handle_worker_cancelled)
        ax, canvas = self.convergence_plot
        ax.clear()
        ax.set_title(tr('{algorithm} 适应度进化图', algorithm=self._run_algorithm), fontsize=14, fontweight='bold')
        ax.set_ylabel(self.curve_ylabel, fontsize=12)
        if not self.is_optimization:
            ax.set_xlabel(tr('迭代次数'), fontsize=12)
        ax.set_xlim(0, params['最大迭代次数 (T)'])
        ax.grid(True)
        canvas.draw()
        if self.is_optimization:
            self.ref_line.set_data([], [])
            self.pos_line.set_data([], [])
            self.tracking_canvas.draw()
        owner.set_run_busy(True)
        self.handle_run_state('starting')
        self.handle_run_status('正在启动 MATLAB…')
        self.elapsed_timer.start(1000)
        self.update_elapsed()
        self.data_timer.start(1000)
        self.worker.start()

    def handle_worker_error(self, error_msg):
        self.data_timer.stop()
        self.parent_window.statusBar().showMessage(tr('算法错误：{error}', error=error_msg))
        elapsed = max(0., time.time() - getattr(self, 'start_time', time.time()))
        self.update_info_labels({'状态': '运行超时' if self.run_state == 'timed_out' else '运行失败',
                                 '运行时间': tr('{seconds:.2f}秒', seconds=elapsed), '错误详情': error_msg})

    def check_data_update(self):
        algorithm = getattr(self, '_run_algorithm', self.current_algorithm)
        path = self.data_files.get(algorithm)
        if not path:
            return
        try:
            curve = read_curve(path)
            if not np.isfinite(curve).all():
                raise ValueError(tr('曲线包含无效数值。'))
        except (OSError, ValueError, KeyError, TypeError, IndexError):
            if Path(path).exists() or self.last_update_iter:
                self._read_failures += 1
                if self._read_failures >= 5:
                    self.curve_warning.setText(tr('暂时无法读取曲线数据，计算仍在继续；可查看日志。'))
                    self.curve_warning.show()
            return
        self._read_failures = 0
        self.curve_warning.hide()
        if not np.array_equal(curve, self.gb_data, equal_nan=True):
            self.last_update_iter = max(self.last_update_iter, len(curve))
            self.gb_data = curve
            self.update_plot_from_data()
            if hasattr(self, '_run_params'):
                self.handle_progress(len(curve), self._run_params['最大迭代次数 (T)'])

    def update_plot_from_data(self):
        if not len(self.gb_data):
            return
        try:
            ax, canvas = self.convergence_plot
            ax.clear()
            if not self.is_optimization:
                ax.set_xlabel(tr('迭代次数'), fontsize=12)
            ax.set_ylabel(self.curve_ylabel, fontsize=12)
            algorithm = getattr(self, '_run_algorithm', self.current_algorithm)
            ax.set_title(tr('{algorithm} 适应度进化图', algorithm=algorithm), fontsize=14, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.6)
            valid = np.isfinite(self.gb_data)
            x_data = np.arange(1, len(self.gb_data) + 1)[valid]
            y_data = self.gb_data[valid]
            if len(x_data):
                label = tr('HV（超体积）' if self.is_optimization and algorithm in MULTI else '全局最优值')
                line, = ax.plot(x_data, y_data, 'b-', linewidth=2,
                                marker='o' if len(x_data) == 1 else None, markersize=4, label=label)
                if self.is_optimization:
                    self.convergence_line = line
                else:
                    self.line = line
                max_iter = getattr(self, '_run_params', {}).get('最大迭代次数 (T)', len(self.gb_data))
                ax.set_xlim(0, max_iter)
                y_min, y_max = np.min(y_data), np.max(y_data)
                y_range = y_max - y_min
                if y_range == 0:
                    y_range = 1
                    y_min -= .5
                    y_max += .5
                margin = y_range * .1
                ax.set_ylim(y_min - margin, y_max + margin)
            ax.legend(loc='upper right')
            canvas.draw()
        except Exception:
            logger.exception('更新图表错误')

    def update_convergence_plot(self):
        self.update_plot_from_data()

    def clear_info_labels(self):
        while self.info_form_layout.count():
            child = self.info_form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def add_info_label(self, key, value):
        label_key, label_value = QLabel(tr(key)), QLabel(tr(value))
        for label, color in ((label_key, '#24898f'), (label_value, '#5d98f5')):
            label.setFont(QFont('Microsoft YaHei', 12))
            label.setStyleSheet(f"font: 12pt 'Microsoft YaHei'; color: {color}; padding: 5px;")
        label_value.setWordWrap(True)
        self.info_form_layout.addRow(label_key, label_value)
        self.info_form_widget.update()
        self.info_scroll_area.update()

    def update_info_labels(self, results):
        if '运行时间' in results and hasattr(self, '_run_started'):
            total, calculation = self.run_timings()
            results = dict(results)
            del results['运行时间']
            results['计算耗时'] = tr('{seconds:.2f}秒', seconds=calculation)
            results['总耗时'] = tr('{seconds:.2f}秒', seconds=total)
        self.clear_info_labels()
        for key, value in results.items():
            self.add_info_label(key, value)
