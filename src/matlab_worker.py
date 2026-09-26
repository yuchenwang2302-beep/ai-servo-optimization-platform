# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Qt supervisor: MATLAB calls live in a bounded, private process tree."""
from i18n import tr, language
from dataclasses import dataclass
from datetime import datetime
import copy
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import traceback
import uuid

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from algorithm_catalog import data_filename
from project_paths import data_directory
from run_support import validate_params, validate_tracking, read_curve
from process_job import ProcessJob


@dataclass(frozen=True)
class RunLimits:
    startup: float = 180
    calculation: float = 4 * 60 * 60
    cleanup: float = 40
    cancellation: float = 8


class MatlabWorker(QThread):
    identification_finished = pyqtSignal(object, object, object)
    optimization_finished = pyqtSignal(bool, float, list, np.ndarray, np.ndarray, np.ndarray)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    cancelled = pyqtSignal()
    progress = pyqtSignal(int, int)
    state_changed = pyqtSignal(str)

    def __init__(self, algorithm, params, is_optimization=False, data_folder=None,
                 runtime_limit_seconds=14400, *, limits=None, runner_script=None):
        super().__init__()
        self.algorithm = algorithm
        self.params = copy.deepcopy(params)
        self.is_optimization = is_optimization
        self.limits = limits or RunLimits(calculation=float(runtime_limit_seconds))
        if not all(np.isfinite(v) and v > 0 for v in vars(self.limits).values()):
            raise ValueError(tr('运行时限必须为大于零的有限数值。'))
        self.runner_script = Path(runner_script or Path(__file__).with_name('compute_process.py'))
        folder = Path(data_folder or data_directory(is_optimization))
        self.data_folder = str(folder / (datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:8]))
        self.data_file = str(Path(self.data_folder) / data_filename(algorithm, is_optimization))
        self._stop = threading.Event()
        self.running = False
        self.state = 'idle'
        self.engine_pid = None
        self.process_pid = None
        self._started = None
        self._ended = None
        self._calculation_started = None
        self._calculation_ended = None

    def stop(self):
        self._stop.set()

    def timings(self):
        now = time.monotonic()
        total = max(0., (self._ended or now) - self._started) if self._started is not None else 0.
        calculation = (max(0., (self._calculation_ended or now) - self._calculation_started)
                       if self._calculation_started is not None else 0.)
        return total, calculation

    def _state(self, state, message):
        now = time.monotonic()
        if state == 'running' and self._calculation_started is None:
            self._calculation_started = now
        elif state != 'running' and self._calculation_started is not None and self._calculation_ended is None:
            self._calculation_ended = now
        self.state = state
        self.state_changed.emit(state)
        self.status.emit(message)
        try:
            (Path(self.data_folder) / 'run_state.json').write_text(json.dumps({
                'state': state, 'message': message, 'process_pid': self.process_pid,
                'engine_pid': self.engine_pid, 'limits_seconds': vars(self.limits),
                'elapsed_seconds': self.timings()[0],
                'calculation_seconds': self.timings()[1],
            }, ensure_ascii=False, indent=2), encoding='utf-8')
        except OSError:
            pass

    def _load_result(self):
        with np.load(Path(self.data_folder) / 'result.npz', allow_pickle=False) as data:
            best = float(data['best'])
            parameters = np.asarray(data['parameters'], dtype=float).reshape(-1).tolist()
            if not np.isfinite(best) or not np.isfinite(parameters).all():
                raise ValueError(tr('计算结果包含无效数值。'))
            curve = read_curve(self.data_file)
            if len(curve) != self.params['最大迭代次数 (T)'] or not np.isfinite(curve).all():
                raise ValueError(tr('最终收敛数据缺失或不完整，请查看本次运行日志。'))
            if self.is_optimization:
                return (True, best, parameters, *validate_tracking(data['time'], data['reference'], data['position']))
            returned = np.asarray(data['curve']).reshape(-1)
            if len(parameters) != 10 or not np.array_equal(returned, curve):
                raise ValueError(tr('辨识结果与最终曲线不一致。'))
            return returned, parameters, best

    def run(self):
        process = job = reader = None
        reader_done = threading.Event()
        messages = queue.Queue()
        error = None
        outcome = None
        result = None
        forced = False
        self._started = time.monotonic()
        self.running = True
        directory = Path(self.data_folder)
        try:
            self.params = validate_params(self.algorithm, self.params, self.is_optimization)
            directory.mkdir(parents=True, exist_ok=True)
            if self._stop.is_set():
                outcome = 'cancelled'
            else:
                request = directory / 'request.json'
                request.write_text(json.dumps({'algorithm': self.algorithm, 'params': self.params,
                    'language': language(),
                    'optimization': self.is_optimization, 'run_directory': str(directory)},
                    ensure_ascii=False, indent=2), encoding='utf-8')
                job = ProcessJob()
                self._state('starting', tr('正在启动 MATLAB…'))
                with (directory / 'process.log').open('w', encoding='utf-8') as log:
                    process = subprocess.Popen([sys.executable, '-I', '-X', 'utf8', '-X', 'faulthandler',
                        str(self.runner_script), str(request)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=log, text=True, encoding='utf-8', errors='replace', bufsize=1,
                        creationflags=subprocess.CREATE_NO_WINDOW | 0x00000004, cwd=directory)  # CREATE_SUSPENDED
                    self.process_pid = process.pid
                    job.assign(process.pid)
                    job.resume(process.pid)

                    def read_messages():
                        try:
                            for line in process.stdout:
                                messages.put(line)
                        finally:
                            reader_done.set()

                    reader = threading.Thread(target=read_messages, daemon=True)
                    reader.start()
                    process.stdin.write('start\n')
                    process.stdin.flush()
                    deadline = time.monotonic() + self.limits.startup
                    stop_deadline = None
                    last_progress_check = 0
                    last_iteration = 0
                    child_outcome = None
                    while True:
                        now = time.monotonic()
                        while not messages.empty():
                            line = messages.get_nowait()
                            try:
                                message = json.loads(line)
                            except (ValueError, TypeError):
                                log.write(line)
                                log.flush()
                                continue
                            event = message.get('event')
                            if event == 'engine':
                                self.engine_pid = int(message['pid'])
                                if not job.contains(self.engine_pid):
                                    from matlab_process import OwnedWindowsProcess
                                    OwnedWindowsProcess(self.engine_pid).close(wait_ms=0)
                                    raise RuntimeError(tr('MATLAB 未进入本次任务的进程保护范围，已中止启动。'))
                            elif event == 'state' and stop_deadline is None:
                                state = message['state']
                                if state != self.state:
                                    deadline = now + {'starting': self.limits.startup,
                                        'running': self.limits.calculation, 'cleaning': self.limits.cleanup}[state]
                                    self._state(state, message['text'])
                            elif event == 'error':
                                error = message['text']
                                child_outcome = 'failed'
                            elif event in ('result', 'cancelled'):
                                child_outcome = event
                        # Drain the pipe after exit before deciding whether a final result arrived.
                        if process.poll() is not None and reader_done.is_set() and messages.empty():
                            if stop_deadline is not None:
                                break
                            if process.returncode != 0:
                                error = error or tr('计算进程异常退出（代码 {code}），请查看日志后重新运行。', code=process.returncode)
                            elif child_outcome == 'result':
                                result = self._load_result()
                            elif child_outcome != 'failed':
                                error = tr('计算进程未返回完整结果，请查看日志后重新运行。')
                            outcome = 'failed' if error else 'succeeded'
                            break
                        if stop_deadline is None:
                            if self._stop.is_set():
                                outcome = 'cancelled'
                                self._state('stopping', tr('正在停止本次计算并清理资源…'))
                                stop_deadline = now + self.limits.cancellation
                            elif now >= deadline:
                                stage = {'starting': 'MATLAB 启动', 'running': '计算', 'cleaning': '资源清理'}.get(self.state, '任务')
                                error = tr('{stage}超过设定时限，已停止本次任务。可查看日志、调整时限后重新运行。', stage=tr(stage))
                                outcome = 'timed_out'
                                self._state('stopping', tr('{stage}超过设定时限，正在停止本次计算并清理资源…', stage=tr(stage)))
                                stop_deadline = now + self.limits.cancellation
                            if stop_deadline is not None:
                                try:
                                    process.stdin.write('stop\n')
                                    process.stdin.flush()
                                except (OSError, ValueError):
                                    pass
                        if stop_deadline is not None and now >= stop_deadline:
                            forced = True
                            break  # close() holds descendant identities before terminating the job.
                        if now - last_progress_check >= 1:
                            last_progress_check = now
                            try:
                                curve = read_curve(self.data_file)
                                if len(curve) > last_iteration and np.isfinite(curve).all():
                                    last_iteration = len(curve)
                                    self.progress.emit(last_iteration, self.params['最大迭代次数 (T)'])
                            except (OSError, ValueError, KeyError, TypeError, IndexError):
                                pass  # UI separately reports persistent MAT-read failures.
                        time.sleep(.05)
        except Exception as exc:
            error = str(exc)
            outcome = 'failed'
            try:
                directory.mkdir(parents=True, exist_ok=True)
                (directory / 'supervisor_error.log').write_text(traceback.format_exc(), encoding='utf-8')
            except OSError:
                pass
        finally:
            # Unexpected exits also stop the calculation clock before cleanup.
            if self._calculation_started is not None and self._calculation_ended is None:
                self._calculation_ended = time.monotonic()
            if job is not None:
                try:
                    job.close()
                except Exception as exc:
                    error = tr('资源清理失败：{error}', error=exc)
                    outcome = 'failed'
            if process is not None:
                if process.poll() is None:
                    process.terminate()  # Exact Popen child only; may still be waiting for the handshake.
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    error = tr('后台进程未能按时退出，请查看日志。')
                    outcome = 'failed'
                if process.stdin:
                    try:
                        process.stdin.close()
                    except OSError:
                        pass  # The child may have exited while a stop command was flushing.
                if reader:
                    reader.join(timeout=1)
                if process.stdout and reader_done.is_set():
                    process.stdout.close()
            self.running = False
            self._ended = time.monotonic()
        if outcome == 'succeeded' and result is not None:
            if self.is_optimization:
                self.optimization_finished.emit(*result)
            else:
                self.identification_finished.emit(*result)
            self._state('succeeded', tr('计算完成。'))
        elif outcome == 'cancelled':
            self._state('cancelled', tr('计算已停止；未生成完整结果。') + (tr(' 已回收本次后台进程。') if forced else ''))
            self.cancelled.emit()
        else:
            self._state(outcome or 'failed', error or tr('计算未完成。'))
            self.error.emit(error or tr('计算未完成。'))
