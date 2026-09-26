# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Retention safety, responsive geometry, and calculation/total clock boundaries."""
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QTabWidget
from run_history import RunStore
from second_window import SecondWindow
from matlab_worker import MatlabWorker
from algorithm_catalog import default_parameters
from i18n import set_language


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'runtime'
        self.store = RunStore(self.root)
        self.now = time.time()

    def record(self, age, index=0, state='succeeded', archived=False):
        stamp = datetime.fromtimestamp(self.now - age * 86400).strftime('%Y%m%d_%H%M%S')
        path = self.root / 'optimization' / f'{stamp}_{index:08x}'
        path.mkdir(parents=True)
        (path / 'request.json').write_text(json.dumps({'algorithm': 'PSO', 'params': {}}))
        (path / 'run_state.json').write_text(json.dumps({'state': state}))
        (path / 'result.npz').write_bytes(b'keep my experiment')
        for child in path.iterdir():
            os.utime(child, (self.now-age*86400,)*2)
        if archived:
            self.store.archive(path, True)
        return path

    def test_age_and_latest_twenty_both_protect_records(self):
        old = self.record(60)
        for i in range(21): self.record(40, i+1)
        recent = self.record(1, 30)
        report = self.store.cleanup(now=self.now)
        self.assertEqual(report['removed_runs'], 3)
        self.assertFalse(old.exists()); self.assertTrue(recent.exists())
        self.assertEqual(len(self.store.records()), 20)

    def test_recent_runs_are_not_deleted_to_force_a_count_limit(self):
        for i in range(25): self.record(1, i)
        self.assertEqual(self.store.cleanup(now=self.now)['removed_runs'], 0)
        self.assertEqual(len(self.store.records()), 25)

    def test_archived_and_running_and_unknown_folders_are_preserved(self):
        protected = [self.record(100, 1, archived=True), self.record(100, 2, state='running')]
        unknown = self.root / 'optimization' / 'personal-data'
        unknown.mkdir(); (unknown/'important.txt').write_text('preserve')
        protected.append(unknown)
        for i in range(20): self.record(40, i+10)
        self.store.cleanup(now=self.now)
        self.assertTrue(all(path.exists() for path in protected))

    def test_only_rebuildable_caches_are_removed_from_retained_runs(self):
        path = self.record(10)
        (path/'slprj').mkdir(); (path/'slprj'/'generated.bin').write_bytes(b'123')
        (path/'model.slxc').write_bytes(b'456')
        (path/'curve.mat').write_bytes(b'result')
        result = self.store.cleanup(now=self.now)
        self.assertEqual(result['removed_caches'], 2)
        self.assertEqual(result['freed_bytes'], 6)
        self.assertTrue((path/'result.npz').exists()); self.assertTrue((path/'curve.mat').exists())
        self.assertFalse((path/'slprj').exists())

    def test_disabled_auto_cleanup_and_manual_cleanup(self):
        path = self.record(10); (path/'model.slxc').write_bytes(b'cache')
        self.store.save_policy(False, 14)
        self.assertEqual(self.store.cleanup(now=self.now)['removed_caches'], 0)
        self.assertEqual(self.store.cleanup(now=self.now, force=True)['removed_caches'], 1)

    def test_archive_toggle_and_policy_persist(self):
        path = self.record(50)
        self.store.archive(path, True)
        self.assertTrue(RunStore(self.root).records()[0]['archived'])
        self.store.archive(path, False)
        self.assertFalse(self.store.records()[0]['archived'])
        self.store.save_policy(True, 60)
        self.assertEqual(RunStore(self.root).policy()['days'], 60)
        with self.assertRaises(ValueError): self.store.save_policy(True, 0)

    def test_interrupted_cleanup_preserves_remaining_records(self):
        old = self.record(100)
        for i in range(20): self.record(40, i+1)
        self.store.cleanup(now=self.now, cancelled=lambda: True)
        self.assertTrue(old.exists())

    def test_links_and_outside_paths_are_never_followed(self):
        path = self.record(100)
        for i in range(20): self.record(40, i+1)
        outside = Path(self.temp.name)/'outside'; outside.mkdir()
        (outside/'important.txt').write_text('keep')
        link = path/'external'
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != 'nt': self.skipTest('Links are unavailable')
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)],
                           check=True, capture_output=True)
        result = self.store.cleanup(now=self.now)
        self.assertTrue(path.exists()); self.assertTrue((outside/'important.txt').exists())
        self.assertEqual(len(result['errors']), 1)
        self.assertFalse(self.store.safe(outside))

    def test_malformed_metadata_is_not_deletable(self):
        path = self.record(100)
        (path/'run_state.json').write_text('[]')
        self.assertEqual(self.store.records(), [])
        self.store.cleanup(now=self.now)
        self.assertTrue(path.exists())


class DisplayAndClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_both_languages_fit_small_windows_and_keep_desktop_columns(self):
        for lang in ('zh', 'en'):
            set_language(lang)
            window = SecondWindow(maintenance=False)
            window.show()
            tabs = window.findChild(QTabWidget)
            for width, height in ((800, 600), (1366, 720), (1920, 1000)):
                window.resize(width, height)
                for index in (0, 1):
                    tabs.setCurrentIndex(index)
                    self.app.processEvents(); self.app.processEvents()
                    page = tabs.widget(index)
                    self.assertEqual((window.width(), window.height()), (width, height))
                    self.assertEqual(page.horizontalScrollBar().maximum(), 0)
                    self.assertEqual(page.compact, width < 1100)
                    page.verticalScrollBar().setValue(page.verticalScrollBar().maximum())
                    self.app.processEvents()
                    self.assertLessEqual(page.widget().height() + page.widget().y(), page.viewport().height())
            window.close(); window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        set_language('zh')

    def test_calculation_clock_excludes_startup_and_cleanup_and_freezes(self):
        with tempfile.TemporaryDirectory() as directory:
            worker = MatlabWorker('PSO', default_parameters('PSO', True), True, directory)
            Path(worker.data_folder).mkdir()
            worker._started = 100.
            with patch('matlab_worker.time.monotonic', return_value=110.) as clock:
                worker._state('starting', '')
                self.assertEqual(worker.timings(), (10., 0.))
                clock.return_value = 120.; worker._state('running', '')
                clock.return_value = 125.; self.assertEqual(worker.timings(), (25., 5.))
                worker._state('stopping', '')
                clock.return_value = 130.; self.assertEqual(worker.timings(), (30., 5.))
                worker._ended = 131.; clock.return_value = 200.
                self.assertEqual(worker.timings(), (31., 5.))

    def test_history_archive_settings_and_cache_cleanup_in_both_languages(self):
        for lang in ('zh', 'en'):
            set_language(lang)
            with tempfile.TemporaryDirectory() as directory:
                store = RunStore(Path(directory)/'runtime')
                stamp = (datetime.now()-timedelta(days=10)).strftime('%Y%m%d_%H%M%S')
                path = store.root/'optimization'/f'{stamp}_12345678'
                path.mkdir(parents=True)
                (path/'request.json').write_text(json.dumps({'algorithm':'PSO','params':{'objective':'ISE'}}))
                (path/'run_state.json').write_text(json.dumps({'state':'succeeded','elapsed_seconds':20,'calculation_seconds':10}))
                (path/'model.slxc').write_bytes(b'cache')
                for child in path.iterdir(): os.utime(child,(time.time()-10*86400,)*2)
                window = SecondWindow(maintenance=False);window.run_store=store
                window.show();window.open_history()
                def wait():
                    deadline=time.monotonic()+5
                    while window._history_job is not None and time.monotonic()<deadline: QTest.qWait(10)
                    self.assertIsNone(window._history_job)
                wait();dialog=window._history_dialog
                self.assertEqual(dialog.table.rowCount(),1)
                dialog.toggle_archive();wait()
                self.assertTrue(store.records()[0]['archived'])
                dialog.days.setValue(14);dialog.auto.setChecked(False)
                dialog.cleanup();wait()
                self.assertTrue((path/'model.slxc').exists())
                dialog.toggle_archive();wait();dialog.cleanup();wait()
                self.assertFalse((path/'model.slxc').exists())
                self.assertTrue((path/'request.json').exists())
                self.assertEqual(store.policy()['days'],14)
                self.assertFalse(store.policy()['enabled'])
                if lang == 'en':
                    import re
                    for text in (dialog.windowTitle(), dialog.message.text(), dialog.details.toPlainText()):
                        self.assertIsNone(re.search('[\u4e00-\u9fff]',text))
                dialog.close();window.close();window.deleteLater()
                QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
        set_language('zh')


if __name__ == '__main__': unittest.main(verbosity=2)
