# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Startup boundaries: real isolated interpreter plus controlled failure cases."""
import importlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_environment as diagnostics


class EnvironmentTests(unittest.TestCase):
    def test_all_runtime_packages_are_local_and_locked(self):
        report = diagnostics.collect_report()
        self.assertTrue(report['passed'], report['errors'])
        self.assertEqual(len(report['dependencies']), 16)
        self.assertEqual(report['external_site_packages'], [])
        self.assertFalse(report['user_site_enabled'])

    def test_wrong_interpreter_is_rejected(self):
        with patch.object(sys, 'executable', 'C:/unrelated/python.exe'):
            report = diagnostics.collect_report()
        self.assertFalse(report['passed'])
        self.assertTrue(any('system Python is unsupported' in e for e in report['errors']))

    def test_inherited_site_packages_are_rejected(self):
        with patch.object(sys, 'path', sys.path + ['C:/foreign/Lib/site-packages']):
            report = diagnostics.collect_report()
        self.assertFalse(report['passed'])
        self.assertEqual(len(report['external_site_packages']), 1)

    def test_missing_engine_is_reported_before_ui(self):
        original = importlib.import_module
        def unavailable(name, *args, **kwargs):
            if name == 'matlab.engine':
                raise ImportError('Engine absent for test')
            return original(name, *args, **kwargs)
        with patch.object(importlib, 'import_module', side_effect=unavailable):
            report = diagnostics.collect_report()
        self.assertFalse(report['passed'])
        self.assertIn('Engine absent for test', report['dependencies']['matlabengine']['error'])

    def test_wrong_package_version_is_rejected(self):
        original = diagnostics.metadata.distribution
        def changed(name):
            if name == 'numpy':
                class WrongVersion:
                    version = '0.0'
                    def locate_file(self, value):
                        return Path(sys.prefix) / 'Lib/site-packages'
                return WrongVersion()
            return original(name)
        with patch.object(diagnostics.metadata, 'distribution', side_effect=changed):
            report = diagnostics.collect_report()
        self.assertFalse(report['passed'])
        self.assertIn('Wrong version', report['dependencies']['numpy']['error'])

    def test_missing_model_is_reported(self):
        with patch.object(diagnostics, 'MODELS', ('missing_model.slx',)):
            report = diagnostics.collect_report()
        self.assertFalse(report['passed'])
        self.assertIn('Missing Simulink model: missing_model.slx', report['errors'])

    def test_batch_from_foreign_directory_ignores_python_overrides(self):
        with tempfile.TemporaryDirectory(prefix='servo foreign cwd ') as directory:
            # If Python honored these variables, startup would fail before importing the app.
            Path(directory, 'numpy.py').write_text("raise RuntimeError('foreign numpy imported')")
            env = dict(os.environ, PYTHONPATH=directory, PYTHONHOME=directory)
            result = subprocess.run([os.environ['COMSPEC'], '/d', '/c', str(ROOT / 'start_ui.bat'),
                                     '--check', '--no-pause'], cwd=directory, env=env,
                                    capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS: isolated project environment', result.stdout)

    def test_missing_environment_does_not_run_system_python(self):
        with tempfile.TemporaryDirectory(prefix='servo no venv ') as directory:
            batch = Path(directory) / 'start_ui.bat'
            shutil.copyfile(ROOT / 'start_ui.bat', batch)
            result = subprocess.run([os.environ['COMSPEC'], '/d', '/c', str(batch),
                                     '--check', '--no-pause'], cwd=directory,
                                    capture_output=True, text=True, timeout=15)
            self.assertFalse((Path(directory) / 'runtime').exists())
        self.assertEqual(result.returncode, 1)
        self.assertIn('Project environment is missing', result.stdout)

    def test_actual_launcher_opens_original_login(self):
        # Run the real launch path and close its Qt event loop after verifying the login.
        code = '''
import runpy, sys
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QDialog, QLineEdit
app = QApplication([])
def inspect():
    windows = [w for w in app.topLevelWidgets() if isinstance(w, QDialog) and w.isVisible()]
    ok = len(windows) == 1 and len(windows[0].findChildren(QLineEdit)) == 2
    print('LOGIN_VISIBLE' if ok else 'LOGIN_MISSING', flush=True)
    app.exit(0 if ok else 2)
QApplication.__new__ = staticmethod(lambda cls, *a, **kw: app)
QApplication.__init__ = lambda self, *a, **kw: None
QTimer.singleShot(400, inspect)
sys.argv = [sys.argv[1]]
runpy.run_path(sys.argv[0], run_name='__main__')
'''
        result = subprocess.run([sys.executable, '-I', '-c', code, str(ROOT / 'tools/start_ui.py')],
                                env=dict(os.environ, QT_QPA_PLATFORM='offscreen'),
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('LOGIN_VISIBLE', result.stdout)

    def test_native_failure_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory(prefix='servo native exit ') as directory:
            root = Path(directory)
            batch = root / 'start_ui.bat'
            # Substitute only the interpreter location to exercise the real batch error handling.
            launcher = (ROOT / 'start_ui.bat').read_text()
            launcher = launcher.replace('.venv\\Scripts\\python.exe', sys.executable)
            batch.write_text(launcher)
            (root / 'tools').mkdir()
            (root / 'tools/start_ui.py').write_text(
                'import ctypes; ctypes.windll.kernel32.ExitProcess(0xC0000005)')
            result = subprocess.run([os.environ['COMSPEC'], '/d', '/c', str(batch), '--no-pause'],
                                    capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('Startup failed', result.stdout)


if __name__ == '__main__':
    unittest.main()
