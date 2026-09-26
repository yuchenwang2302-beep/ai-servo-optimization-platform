# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Exercise the real Windows supervisor against contained subprocess failures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from matlab_worker import MatlabWorker, RunLimits
from matlab_process import OwnedWindowsProcess


class RuntimeTests(unittest.TestCase):
    def make_worker(self, directory, scenario='success', **limits):
        params = {'群体粒子个数 (N)': 4, '粒子维数 (D)': 11, '最大迭代次数 (T)': 2,
                  'objective': 'IAE', '_scenario': scenario}
        values = dict(startup=10, calculation=10, cleanup=10, cancellation=.3)
        values.update(limits)
        return MatlabWorker('PSO', params, True, directory, limits=RunLimits(**values),
                            runner_script=ROOT / 'tests/fixtures/process_scenarios.py')

    def check_run(self, worker, expected):
        events = []
        owned = []
        worker.error.connect(lambda text: events.append(('error', text)))
        worker.cancelled.connect(lambda: events.append(('cancelled',)))
        worker.optimization_finished.connect(lambda *args: events.append(('result',)))
        def acquire_handle():
            deadline = time.monotonic() + 10
            path = Path(worker.data_folder) / 'child_pid.json'
            while not path.exists() and time.monotonic() < deadline:
                time.sleep(.01)
            if path.exists():
                # The fixture keeps this child alive until the containing job ends.
                try:
                    owned.append(OwnedWindowsProcess(json.loads(path.read_text())))
                except OSError:
                    pass
        watcher = threading.Thread(target=acquire_handle)
        watcher.start()
        start = time.monotonic()
        worker.run()
        watcher.join(timeout=11)
        self.assertFalse(watcher.is_alive())
        self.assertEqual(worker.state, expected, events)
        self.assertEqual(len(events), 1, events)
        self.assertLess(time.monotonic() - start, 15)
        self.assertFalse(worker.running)
        for child in owned:
            try:
                self.assertEqual(child.kernel.WaitForSingleObject(child.handle, 0), 0,
                                 'A descendant survived the completed run')
            finally:
                child.close(wait_ms=0)
        return events

    def test_success_cleans_descendants_before_result(self):
        with tempfile.TemporaryDirectory() as directory:
            worker = self.make_worker(directory)
            self.assertEqual(self.check_run(worker, 'succeeded'), [('result',)])

    def test_startup_calculation_and_cleanup_deadlines(self):
        with tempfile.TemporaryDirectory() as directory:
            for scenario, limits in [('startup_hang', {'startup': .8}),
                                     ('calculation_hang', {'calculation': .3}),
                                     ('cleanup_hang', {'cleanup': .3})]:
                with self.subTest(stage=scenario):
                    worker = self.make_worker(directory, scenario, **limits)
                    messages = []
                    worker.status.connect(lambda text: messages.append((worker.state, text)))
                    events = self.check_run(worker, 'timed_out')
                    self.assertIn('超过设定时限', events[0][1])
                    stopping = [text for state, text in messages if state == 'stopping']
                    self.assertTrue(stopping)
                    self.assertIn('正在停止', stopping[-1])
                    self.assertNotIn('已停止', stopping[-1])
                    self.assertIn('已停止', events[0][1])

    def test_crash_missing_result_and_reported_error(self):
        with tempfile.TemporaryDirectory() as directory:
            for scenario in ('crash', 'missing_result', 'error'):
                with self.subTest(scenario=scenario):
                    self.check_run(self.make_worker(directory, scenario), 'failed')

    def test_stop_then_retry_does_not_touch_unrelated_process(self):
        sentinel = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'],
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            with tempfile.TemporaryDirectory() as directory:
                worker = self.make_worker(directory, 'calculation_hang')
                timer = threading.Timer(.7, worker.stop)
                timer.start()
                try:
                    self.assertEqual(self.check_run(worker, 'cancelled'), [('cancelled',)])
                finally:
                    timer.cancel()
                self.assertIsNone(sentinel.poll())
                next_run = self.make_worker(directory)
                self.assertNotEqual(worker.data_folder, next_run.data_folder)
                self.check_run(next_run, 'succeeded')
                self.assertIsNone(sentinel.poll())
        finally:
            sentinel.terminate()
            sentinel.wait(timeout=5)

    def test_cancellation_before_start_creates_no_process(self):
        with tempfile.TemporaryDirectory() as directory:
            worker = self.make_worker(directory)
            events = []
            worker.cancelled.connect(lambda: events.append(True))
            worker.stop()
            worker.run()
            self.assertEqual(events, [True])
            self.assertIsNone(worker.process_pid)
            self.assertEqual(worker.state, 'cancelled')

    def test_parent_exit_reclaims_private_children(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = subprocess.Popen([sys.executable, '-I', str(ROOT / 'tests/fixtures/job_parent.py'), directory],
                                      stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            handles = []
            try:
                ready = Path(directory) / 'ready.json'
                deadline = time.monotonic() + 10
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertTrue(ready.exists())
                handles = [OwnedWindowsProcess(pid) for pid in json.loads(ready.read_text()).values()]
                parent.stdin.write(b'exit\n');parent.stdin.flush()
                parent.wait(timeout=5)
                for owned in handles:
                    self.assertEqual(owned.kernel.WaitForSingleObject(owned.handle, 5000), 0)
            finally:
                if parent.poll() is None:
                    parent.terminate();parent.wait(timeout=5)
                parent.stdin.close()
                for owned in handles:
                    owned.close(wait_ms=0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
