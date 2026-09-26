# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Run with .venv/Scripts/python.exe tests/smoke_ui.py."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from PyQt5.QtWidgets import QApplication, QDialog, QTabWidget
from login import Ui_Dialog
from engine_task import EngineTask as MatlabWorker


class UiSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from i18n import set_language
        set_language('zh')
        preference = patch('login.load_language', return_value='zh')
        preference.start();self.addCleanup(preference.stop)

    def test_login_and_all_algorithm_forms_from_other_directory(self):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            try:
                dialog = QDialog()
                ui = Ui_Dialog()
                ui.setupUi(dialog)
                dialog.show()
                ui.lineEdit.setText('111')
                ui.lineEdit_2.setText('111')
                ui.handle_login(dialog)
                self.app.processEvents()
                window = ui.second_window
                self.assertTrue(window.isVisible())
                self.assertFalse(dialog.isVisible())
                tabs = window.findChild(QTabWidget)
                self.assertEqual(tabs.count(), 2)
                for index in range(tabs.count()):
                    tabs.setCurrentIndex(index)
                    self.app.processEvents()
                for index in range(window.tab_identification.algorithm_combo.count()):
                    window.tab_identification.algorithm_combo.setCurrentIndex(index)
                    self.assertTrue(window.tab_identification.params)
                opt = window.tab_optimization
                for kind in range(opt.identification_combo.count()):
                    opt.identification_combo.setCurrentIndex(kind)
                    for index in range(opt.algorithm_combo.count()):
                        opt.algorithm_combo.setCurrentIndex(index)
                        self.assertTrue(opt.params)
                self.assertNotEqual(window.tab_identification.data_files['PSO'], opt.data_files['PSO'])
                for owner in (window.tab_identification, opt):
                    self.assertTrue(all(Path(p).is_absolute() for p in owner.data_files.values()))
                window.close()
            finally:
                os.chdir(original_cwd)

    def test_missing_engine_reports_error_without_crash(self):
        worker = MatlabWorker('PSO', {'群体粒子个数 (N)': 4, '粒子维数 (D)': 11, '最大迭代次数 (T)': 1}, is_optimization=True)
        errors = []
        worker.error.connect(errors.append)
        with patch.dict(sys.modules, {'matlab': None, 'matlab.engine': None}):
            worker.run()
        self.assertEqual(len(errors), 1)
        self.assertIn('MATLAB Engine', errors[0])


if __name__ == '__main__':
    unittest.main()
