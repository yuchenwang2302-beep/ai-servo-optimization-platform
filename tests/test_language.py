# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Check language selection, unchanged computation contracts and process handoff."""
import ast
import json
import os
from pathlib import Path
import re
import string
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QPushButton, QTabWidget
import i18n
from algorithm_catalog import MULTI
from login import Ui_Dialog
from second_window import SecondWindow
from matlab_worker import MatlabWorker, RunLimits
from run_support import ParameterValidationError, validate_params
from test_functions import Engine, Future
from engine_task import EngineTask


class LanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.previous_language = i18n.language()
        self.temp = tempfile.TemporaryDirectory()
        run_paths = patch('algorithm_page.data_directory', return_value=Path(self.temp.name))
        run_paths.start(); self.addCleanup(run_paths.stop)
        self.settings = QSettings(str(Path(self.temp.name) / 'settings.ini'), QSettings.IniFormat)
        self.settings_patch = patch('i18n._settings', return_value=self.settings)
        self.settings_patch.start()
        login_window = patch('login.SecondWindow', side_effect=lambda: SecondWindow(maintenance=False))
        login_window.start(); self.addCleanup(login_window.stop)
        self.windows = []
        i18n.set_language('en')

    def tearDown(self):
        for window in reversed(self.windows):
            window.close()
        self.app.processEvents()
        self.settings_patch.stop()
        self.temp.cleanup()
        i18n.set_language(self.previous_language)

    def login(self):
        dialog = QDialog()
        ui = Ui_Dialog()
        ui.setupUi(dialog)
        dialog.show()
        self.windows.append(dialog)
        self.app.processEvents()
        return dialog, ui

    def main_window(self):
        window = SecondWindow(maintenance=False)
        window.show()
        self.windows.append(window)
        self.app.processEvents()
        return window

    def assert_english(self, text):
        self.assertFalse(re.search('[\u4e00-\u9fff]', text), text)

    def test_login_switch_remembers_choice_and_preserves_credentials(self):
        dialog, ui = self.login()
        self.assertEqual(ui.language_combo.currentData(), 'zh')
        ui.lineEdit.setText('111');ui.lineEdit_2.setText('111')
        for code in ('en', 'zh', 'en'):
            ui.language_combo.setCurrentIndex(ui.language_combo.findData(code))
            self.assertEqual(ui.lineEdit.text(), '111')
            self.assertEqual(ui.lineEdit_2.text(), '111')
            self.assertEqual(self.settings.value('language'), code)
            self.assertEqual(ui.pushButton.text(), 'Sign in' if code == 'en' else '登录')
        another, restored = self.login()
        self.assertEqual(restored.language_combo.currentData(), 'en')
        another.close()
        QTest.keyClick(ui.lineEdit_2, Qt.Key_Return)
        self.app.processEvents()
        self.windows.append(ui.second_window)
        self.assertTrue(ui.second_window.isVisible())
        self.assertEqual(ui.second_window.windowTitle(), i18n.APP_NAME)

    def test_unknown_saved_language_falls_back_to_chinese(self):
        self.settings.setValue('language', 'unknown')
        dialog, ui = self.login()
        self.assertEqual(ui.language_combo.currentData(), 'zh')
        self.assertEqual(dialog.windowTitle(), f'{i18n.APP_NAME} · 登录')

    def test_wrong_login_uses_selected_language(self):
        i18n.set_language('en', persist=True)
        dialog, ui = self.login()
        QTest.mouseClick(ui.pushButton, Qt.LeftButton)
        self.app.processEvents()
        self.assertEqual(ui._error_dialog.windowTitle(), 'Sign-in failed')
        self.assert_english(ui._error_dialog.message.text())
        ui._error_dialog.accept()
        self.assertTrue(dialog.isVisible())

    def test_password_visibility_keyboard_and_translation(self):
        dialog, ui = self.login()
        ui.lineEdit_2.setText('111')
        ui.lineEdit.setFocus()
        QTest.keyClick(ui.lineEdit, Qt.Key_Tab)
        self.assertTrue(ui.lineEdit_2.hasFocus())
        self.assertEqual(ui.lineEdit_2.echoMode(), QLineEdit.Password)
        QTest.keyClick(ui.lineEdit_2, Qt.Key_Tab)
        toggle = ui.lineEdit_2.visibility_button
        self.assertTrue(toggle.hasFocus())
        QTest.keyClick(toggle, Qt.Key_Space)
        self.assertEqual(ui.lineEdit_2.echoMode(), QLineEdit.Normal)
        ui.language_combo.setCurrentIndex(ui.language_combo.findData('en'))
        self.assertEqual(toggle.accessibleName(), 'Hide password')
        self.assertEqual(ui.lineEdit_2.text(), '111')
        QTest.mouseClick(toggle, Qt.LeftButton)
        self.assertEqual(ui.lineEdit_2.echoMode(), QLineEdit.Password)
        self.assertEqual(toggle.accessibleName(), 'Show password')
        self.assertTrue(dialog.isVisible())
        self.assertFalse(hasattr(ui, 'second_window'))

    def test_login_retry_focus_and_success(self):
        dialog, ui = self.login()
        ui.lineEdit.setText('wrong')
        ui.lineEdit_2.setText('wrong')
        for field in (ui.lineEdit, ui.lineEdit_2):
            QTest.mouseClick(ui.pushButton, Qt.LeftButton)
            self.app.processEvents()
            ui._error_dialog.accept()
            QTest.qWait(30)
            self.assertTrue(field.hasFocus())
            self.assertEqual(field.selectedText(), 'wrong')
            QTest.keyClicks(field, '111')
        QTest.keyClick(ui.lineEdit_2, Qt.Key_Return)
        self.app.processEvents()
        self.windows.append(ui.second_window)
        self.assertFalse(dialog.isVisible())
        self.assertTrue(ui.second_window.isVisible())

    def test_all_english_forms_keep_original_defaults_and_mode_contracts(self):
        baseline = json.loads((ROOT / 'tests/fixtures/original_forms.json').read_text(encoding='utf-8'))
        window = self.main_window()
        tabs = window.findChild(QTabWidget)
        self.assertEqual([tabs.tabText(i) for i in range(2)], ['Identification', 'Optimization'])
        visited = 0
        for index, page in enumerate((window.tab_identification, window.tab_optimization)):
            tabs.setCurrentIndex(index)
            for mode in range(2 if index else 1):
                if index:
                    page.identification_combo.setCurrentIndex(mode)
                    self.assertEqual(page.identification_combo.currentData(), 'multi' if mode else 'single')
                    self.assertEqual(page.function_combo.isEnabled(), not mode)
                    window.set_run_busy(True);window.release_run()
                    self.assertEqual(page.function_combo.isEnabled(), not mode)
                for algorithm in range(page.algorithm_combo.count()):
                    page.algorithm_combo.setCurrentIndex(algorithm)
                    self.app.processEvents()
                    prefix = 'identification' if not index else 'multi' if mode else 'single'
                    values = {k: v.text() for k, v in page.params.items()}
                    self.assertEqual(values, baseline[prefix + '/' + page.current_algorithm])
                    normalized = validate_params(page.current_algorithm, page.form_values(), bool(index))
                    self.assertEqual(normalized['最大迭代次数 (T)'], int(values['最大迭代次数 (T)']))
                    for label in page.findChildren(QLabel):
                        if label.isVisible():self.assert_english(label.text())
                    visited += 1
        self.assertEqual(visited, 16)

    def test_english_validation_focus_and_wrapped_error(self):
        window = self.main_window();window.findChild(QTabWidget).setCurrentIndex(1)
        page = window.tab_optimization
        page.algorithm_combo.setCurrentText('IA')
        page.params['群体粒子个数 (N)'].setText('3')
        page.gb_data = np.array([3., 1.])
        page.start_run();QTest.qWait(80)
        self.assertFalse(hasattr(page, 'worker'))
        self.assertIn('even population', page.validation_dialog.message.text())
        self.assert_english(page.validation_summary.text())
        error = page.field_error_labels['群体粒子个数 (N)']
        self.assertGreaterEqual(error.height(), error.heightForWidth(error.width()))
        page.validation_dialog.accept();QTest.qWait(50)
        self.assertTrue(page.params['群体粒子个数 (N)'].hasFocus())
        np.testing.assert_array_equal(page.gb_data, [3., 1.])

    def test_english_complete_run_keeps_engine_arguments_and_translates_results(self):
        window = self.main_window();window.findChild(QTabWidget).setCurrentIndex(1)
        page = window.tab_optimization
        page.params['最大迭代次数 (T)'].setText('2')
        page.function_combo.setCurrentText('IAE')
        engine = Engine()
        def factory(*args, **kwargs):
            kwargs.pop('runtime_limit_seconds')
            return EngineTask(*args, **kwargs, engine_factory=lambda **kw: Future(engine))
        with patch('algorithm_page.MatlabWorker', side_effect=factory):
            page.start_run()
        deadline = time.monotonic() + 10
        while window._busy and time.monotonic() < deadline:QTest.qWait(20)
        self.assertFalse(window._busy)
        self.assertEqual(engine.args[1][-1], 'IAE')
        labels = ' '.join(label.text() for label in page.info_form_widget.findChildren(QLabel))
        self.assertIn('Completed', labels);self.assertIn('Best parameters', labels)
        self.assert_english(labels)
        self.assert_english(page.run_status_label.text())
        self.assertEqual(page.convergence_ax.get_title(), 'PSO fitness convergence')
        self.assertEqual(page.run_button.text(), 'Run algorithm')
        self.assertTrue(engine.closed)

    def test_multiobjective_title_and_disabled_criterion_in_both_languages(self):
        for code, title, criterion in [('en', 'MOGOA HV history', 'Overshoot'),
                                        ('zh', 'MOGOA HV 历史', '超调')]:
            i18n.set_language(code)
            page = self.main_window().tab_optimization
            page.identification_combo.setCurrentIndex(page.identification_combo.findData('multi'))
            page._run_algorithm = 'MOGOA'
            page.gb_data = np.array([.7, .8])
            page.update_plot_from_data()
            self.assertEqual(page.convergence_ax.get_title(), title)
            self.assertEqual(page.function_combo.currentText(), criterion)
            self.assertFalse(page.function_combo.isEnabled())

    def test_english_timeout_releases_controls_and_translates_close_dialog(self):
        window = self.main_window();window.findChild(QTabWidget).setCurrentIndex(1)
        page = window.tab_optimization
        def factory(*args, **kwargs):
            args = list(args);args[1] = dict(args[1], _scenario='calculation_hang')
            return MatlabWorker(*args, **kwargs, limits=RunLimits(10, .4, 5, .2),
                                runner_script=ROOT / 'tests/fixtures/process_scenarios.py')
        with patch('algorithm_page.MatlabWorker', side_effect=factory):page.start_run()
        window.close();self.app.processEvents()
        self.assert_english(window._close_dialog.message.text())
        self.assertEqual(window._close_dialog.reject_button.text(), 'Keep running')
        window._close_dialog.reject()
        deadline = time.monotonic() + 15
        while window._busy and time.monotonic() < deadline:QTest.qWait(20)
        self.assertFalse(window._busy)
        self.assertEqual(page.run_state, 'timed_out')
        self.assertIn('exceeded its time limit', page.run_status_label.text())
        self.assertEqual(page.run_button.text(), 'Run again')
        request = json.loads((Path(page.worker.data_folder) / 'request.json').read_text(encoding='utf-8'))
        self.assertEqual(request['language'], 'en')

    def test_computation_process_uses_request_language_before_validation(self):
        request = Path(self.temp.name) / 'request.json'
        request.write_text(json.dumps({'language': 'en', 'algorithm': 'PSO', 'optimization': True,
            'run_directory': self.temp.name, 'params': {'群体粒子个数 (N)': 4, '粒子维数 (D)': 11,
            '最大迭代次数 (T)': 0}}), encoding='utf-8')
        process = subprocess.Popen([sys.executable, '-I', str(ROOT / 'src/compute_process.py'), str(request)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            process.stdin.write('start\n');process.stdin.flush()
            process.wait(timeout=15)
            events = [json.loads(line) for line in process.stdout]
            self.assertEqual(process.returncode, 0, process.stderr.read())
            self.assertEqual(events[0]['event'], 'error')
            self.assertIn('Max. iterations', events[0]['text'])
            self.assert_english(events[0]['text'])
        finally:
            if process.poll() is None:process.terminate();process.wait(timeout=5)
            process.stdin.close();process.stdout.close();process.stderr.close()

    def test_catalog_covers_display_calls_and_preserves_format_fields(self):
        formatter = string.Formatter()
        fields = lambda text: {field for _, field, _, _ in formatter.parse(text) if field is not None}
        for source, translated in i18n.EN.items():
            self.assertEqual(fields(source), fields(translated), source)
            self.assert_english(translated)
        for path in (ROOT / 'src').glob('*.py'):
            if path.name in ('codes_rc.py', 'i18n.py'):continue
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'tr':
                    if node.args and isinstance(node.args[0], ast.Constant):
                        self.assertIn(node.args[0].value, i18n.EN, (path.name, node.lineno))


if __name__ == '__main__':
    unittest.main(verbosity=2)
