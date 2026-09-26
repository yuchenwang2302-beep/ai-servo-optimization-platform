# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""MATLAB calls, executed only inside the supervised computation process."""
from i18n import tr
from datetime import datetime
from pathlib import Path
import copy
import importlib
import io
import os
import threading
import time
import traceback
import uuid

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from project_paths import PROJECT_ROOT, data_directory
from algorithm_catalog import IDENTIFICATION, SINGLE, data_filename
from run_support import validate_params, validate_tracking


class RunCancelled(Exception):
    pass


class EngineTask(QThread):
    identification_finished = pyqtSignal(object, object, object)
    optimization_finished = pyqtSignal(bool, float, list, np.ndarray, np.ndarray, np.ndarray)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    cancelled = pyqtSignal()
    progress = pyqtSignal(int, int)
    state_changed = pyqtSignal(str)
    engine_started = pyqtSignal(int)
    # QThread.finished is emitted only after run() and engine cleanup return.

    def __init__(self, algorithm, params, is_optimization=False, data_folder=None, engine_factory=None,
                 run_directory=None):
        super().__init__()
        self.algorithm = algorithm
        self.params = copy.deepcopy(params)
        self.is_optimization = is_optimization
        self.engine_factory = engine_factory
        self.running = True
        self._stop = threading.Event()
        folder = Path(data_folder or data_directory(is_optimization))
        self.data_folder = str(run_directory or folder / (datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:8]))
        self.data_file = str(Path(self.data_folder) / data_filename(algorithm, is_optimization))

    def _wait(self, future, startup=False):
        started = time.monotonic()
        while not future.done():
            if self._stop.is_set():
                accepted = future.cancel()
                if startup and not accepted and future.done():
                    return future.result()
                raise RunCancelled()
            if startup and time.monotonic() - started > 180:
                future.cancel()
                raise RuntimeError(tr('MATLAB 启动超过 3 分钟，请先打开 MATLAB 检查登录授权后重试。'))
            self._stop.wait(.1)
        return future.result()

    def _call(self, eng, function, *args, nargout):
        return self._wait(getattr(eng, function)(*args, nargout=nargout, background=True,
                                                stdout=self._log, stderr=self._log))

    def _cleanup_engine(self, eng, owned_process):
        """Release Engine before closing its private process; do not eval quit."""
        error = None

        def trace(message):
            self._log.write(message + '\n')
            try:
                (Path(self.data_folder) / 'matlab.log').write_text(self._log.getvalue(), encoding='utf-8')
            except OSError:
                pass

        trace('Closing models asynchronously.')
        try:
            future = eng.bdclose('all', nargout=0, background=True, stdout=self._log, stderr=self._log)
            if future is not None:
                future.result(timeout=5)
        except Exception as exc:
            trace(f'Closing models: {type(exc).__name__}: {exc}')
        # eval('quit force') can leave an outstanding evaluation that prevents
        # Engine from releasing its connection. Use the Engine lifecycle API,
        # then wait for (or close) only the native process owned by this run.
        trace('Releasing MATLAB Engine connection.')
        try:
            eng.quit()
        except Exception as exc:
            error = tr('MATLAB 资源释放失败：{error}', error=exc)
        if owned_process is not None:
            trace('Waiting for this run\'s owned MATLAB process.')
            try:
                if owned_process.close():
                    trace('MATLAB exit timed out; closed this run\'s owned process.')
            except Exception as exc:
                error = error or tr('MATLAB 资源释放失败：{error}', error=exc)
        trace('MATLAB cleanup complete.')
        return error

    def run(self):
        eng = None
        owned_process = None
        result = None
        error = None
        self._log = io.StringIO()
        try:
            self.params = validate_params(self.algorithm, self.params, self.is_optimization)
            if self._stop.is_set():
                raise RunCancelled()
            Path(self.data_folder).mkdir(parents=True, exist_ok=True)
            self._log = LiveLog(Path(self.data_folder) / 'matlab.log')
            self.state_changed.emit('starting')
            self.status.emit(tr('正在启动 MATLAB…'))
            try:
                factory = self.engine_factory or importlib.import_module('matlab.engine').start_matlab
            except (ImportError, OSError) as exc:
                raise RuntimeError(tr('MATLAB Engine 不可用，请为当前 Python 安装与本机 MATLAB 匹配的 Engine。')) from exc
            eng = self._wait(factory(background=True), startup=True)
            if os.name == 'nt' and self.engine_factory is None:
                from matlab_process import OwnedWindowsProcess
                owned_process = OwnedWindowsProcess(eng.feature('getpid'))
                self.engine_started.emit(int(eng.feature('getpid')))
            self._setup_matlab_path(eng)
            eng.cd(self.data_folder, nargout=0)
            if self._stop.is_set():
                raise RunCancelled()
            self.state_changed.emit('running')
            self.status.emit(tr('正在计算，完成迭代后更新曲线…'))
            result = self._run_optimization(eng) if self.is_optimization else self._run_identification(eng)
        except RunCancelled:
            pass
        except Exception as exc:
            error = str(exc)
            if Path(self.data_folder).exists():
                (Path(self.data_folder) / 'error.log').write_text(traceback.format_exc(), encoding='utf-8')
        finally:
            if eng is not None:
                self.state_changed.emit('cleaning')
                self.status.emit(tr('正在释放 MATLAB 资源…'))
                cleanup_error = self._cleanup_engine(eng, owned_process)
                error = error or cleanup_error
            if Path(self.data_folder).exists():
                try:
                    (Path(self.data_folder) / 'matlab.log').write_text(self._log.getvalue(), encoding='utf-8')
                except OSError:
                    pass
        self.running = False
        if self._stop.is_set():
            self.cancelled.emit()
        elif error:
            self.error.emit(error)
        elif result is not None:
            if self.is_optimization:
                self.optimization_finished.emit(*result)
            else:
                self.identification_finished.emit(*result)

    def _setup_matlab_path(self, eng):
        base = PROJECT_ROOT / 'matlab_scripts'
        eng.addpath(str(base / 'common'), nargout=0)
        if not self.is_optimization:
            folder = base / 'identification'
            required = [IDENTIFICATION[self.algorithm], 'Spd_Discrete', 'Spd_Discrete2']
        elif self.algorithm in SINGLE:
            folder = base / 'optimization/single_objective'
            required = [SINGLE[self.algorithm], 'fun_position', 'servo_error_metric', 'Jerk_FF_Step_2023']
        else:
            folder = base / 'optimization/multi_objectives'
            required = [self.algorithm, 'fun_position_2', 'T_Jerk_FF_Step_2023_2', 'Jerk_FF_Step_2023_2',
                        'dominates', 'UpdateArchive', 'RankingProcess', 'HandleFullArchive',
                        'RouletteWheelSelection', 'GetOptimum', 'myIGD', 'myHV', 'myDM', 'myDeltaP',
                        'distance', 'S_func', 'UniformPoint', 'servo_parallel_workers']
            if self.algorithm == 'MDF_MOGOA':
                required += ['enhanced_gradient', 'adaptive_mutation']
            required += ['LevyFlight', 'initializationWithLevy'] if self.algorithm == 'LVMOGOA' else ['initialization']
        if not folder.is_dir():
            raise FileNotFoundError(tr('MATLAB 脚本目录不存在：{folder}', folder=folder))
        if self.is_optimization:
            eng.addpath(str(base / 'optimization/common'), nargout=0)
            required += ['simulate_servo_position', 'servo_search_bounds']
        eng.addpath(eng.genpath(str(folder)), nargout=0)
        required += ['servo_save_progress']
        missing = [name for name in required if not eng.which(name)]
        if missing:
            raise RuntimeError(tr('缺少 MATLAB 函数或模型：{names}', names=', '.join(missing)))

    @staticmethod
    def _solution(best, parameters, dimension):
        best = float(best)
        parameters = np.asarray(parameters, dtype=float).reshape(-1)
        if not np.isfinite(best) or len(parameters) != dimension or not np.isfinite(parameters).all():
            raise ValueError(tr('算法没有返回有效的最优值或参数，请检查模型和搜索范围。'))
        return best, parameters.tolist()

    def _run_identification(self, eng):
        p = self.params
        matlab = importlib.import_module('matlab')
        curve, parameters, best = self._call(eng, IDENTIFICATION[self.algorithm],
            float(p['群体粒子个数 (N)']), float(p['粒子维数 (D)']), float(p['最大迭代次数 (T)']),
            float(p['速度 (vref)']), matlab.double(p['parameter_bounds']), nargout=3)
        best, parameters = self._solution(best, parameters, 10)
        curve = np.asarray(curve, dtype=float).reshape(-1)
        if len(curve) != p['最大迭代次数 (T)'] or not np.isfinite(curve).all():
            raise ValueError(tr('辨识收敛曲线不完整或含无效数值。'))
        return curve, parameters, best

    def _run_optimization(self, eng):
        p = self.params
        if self.algorithm in SINGLE:
            best, parameters, *tracking = self._call(eng, SINGLE[self.algorithm],
                float(p['群体粒子个数 (N)']), float(p['粒子维数 (D)']),
                float(p['最大迭代次数 (T)']), p.get('objective', 'ITSE'), nargout=5)
            best, parameters = self._solution(best, parameters, 11)
        else:
            tracking = self._call(eng, self.algorithm, float(p['种群大小 (N)']),
                float(p['存档大小 (ArchiveMaxSize)']), float(p['最大迭代次数 (T)']),
                float(p['参数维度 (dim)']), float(p['目标函数数量 (obj_no)']), nargout=3)
            best, parameters = 0., []
        return (True, best, parameters, *validate_tracking(*tracking))

    def stop(self):
        self.running = False
        self._stop.set()


class LiveLog(io.StringIO):
    """Flush MATLAB output immediately, including when the process later stalls."""
    def __init__(self, path):
        super().__init__()
        self.path = path
        path.write_text('', encoding='utf-8')

    def write(self, value):
        result = super().write(value)
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(value)
        return result
