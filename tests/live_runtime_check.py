# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Opt-in real MATLAB cancellation, fault recovery and a longer computation."""
import io
import json
import os
from pathlib import Path
import sys
import time

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import matlab.engine
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from matlab_worker import MatlabWorker, RunLimits
from matlab_process import OwnedWindowsProcess
from engine_task import EngineTask


def main():
    output = ROOT / 'runtime/runtime_b/live_recovery'
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    beats = []
    timer = QTimer()
    timer.timeout.connect(lambda: beats.append(time.monotonic()))
    timer.start(50)
    report = []
    external = matlab.engine.start_matlab()
    owned_external = OwnedWindowsProcess(external.feature('getpid'))
    external_pid = int(external.feature('getpid'))
    print('Independent MATLAB session', external_pid, flush=True)

    def run_case(name, action=None, iterations=1, population=2, calculation=600):
        params = {'群体粒子个数 (N)': population, '粒子维数 (D)': 11,
                  '最大迭代次数 (T)': iterations, 'objective': 'ISE'}
        worker = MatlabWorker('PSO', params, True, output,
                              limits=RunLimits(180, calculation, 40, 8))
        events, progress, states = [], [], []
        worker.error.connect(lambda text: events.append({'error': text}))
        worker.cancelled.connect(lambda: events.append({'cancelled': True}))
        worker.optimization_finished.connect(lambda ok, best, p, t, r, y:
                                             events.append({'success': bool(ok), 'samples': len(t), 'best': best}))
        worker.progress.connect(lambda n, total: progress.append(n))
        worker.state_changed.connect(lambda state: states.append(state))
        started = time.monotonic()
        acted = None
        beat_start = len(beats)
        worker.start()
        print('RUN', name, flush=True)
        while worker.isRunning():
            app.processEvents()
            now = time.monotonic()
            if acted is None:
                if action == 'startup_stop' and now - started > 2:
                    worker.stop(); acted = now
                elif action == 'iteration_stop' and progress:
                    worker.stop(); acted = now
                elif action == 'engine_crash' and worker.state == 'running' and worker.engine_pid:
                    OwnedWindowsProcess(worker.engine_pid).close(wait_ms=0)
                    acted = now
            if now - started > 900:
                worker.stop()
                raise TimeoutError('Live test exceeded its outer deadline')
            time.sleep(.01)
        app.processEvents()
        external_ok = external.sqrt(4., background=True).result(timeout=10) == 2.
        assert external_ok
        expected = ('cancelled',) if action in ('startup_stop', 'iteration_stop') else (
            ('failed', 'timed_out') if action == 'engine_crash' else ('timed_out',) if calculation < 5 else ('succeeded',))
        assert worker.state in expected, (name, worker.state, events)
        assert len(events) == 1, events
        if acted is not None and action != 'engine_crash':
            assert time.monotonic() - acted < 30
        ticks = beats[beat_start:]
        maximum_gap = max((b - a for a, b in zip(ticks, ticks[1:])), default=0)
        assert maximum_gap < 3, maximum_gap
        item = {'name': name, 'passed': True, 'state': worker.state, 'states': states,
                'seconds': round(time.monotonic() - started, 3), 'progress': progress, 'events': events,
                'stop_seconds': round(time.monotonic() - acted, 3) if acted else None,
                'ui_timer_max_gap_seconds': round(maximum_gap, 4), 'external_matlab_alive': external_ok,
                'external_matlab_pid': external_pid, 'engine_pid': worker.engine_pid,
                'run_directory': worker.data_folder}
        report.append(item)
        (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print('PASS', name, worker.state, item['seconds'], flush=True)

    try:
        run_case('stop_during_startup', 'startup_stop')
        run_case('stop_after_real_iteration', 'iteration_stop', iterations=8, population=4)
        run_case('real_calculation_timeout', calculation=1)
        run_case('matlab_crash', 'engine_crash')
        run_case('retry_after_failure')
        run_case('longer_run', iterations=8, population=4)
    finally:
        cleanup = EngineTask('PSO', {})
        cleanup.data_folder = str(output)
        cleanup._log = io.StringIO()
        cleanup._cleanup_engine(external, owned_external)
    return 0


if __name__ == '__main__':
    sys.exit(main())
