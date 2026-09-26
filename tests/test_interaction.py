# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Validate visible feedback, correction, stopping and closing without MATLAB."""
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QTabWidget, QLabel
from second_window import SecondWindow
from matlab_worker import MatlabWorker, RunLimits
from run_support import ParameterValidationError, validate_params


class InteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        run_paths = patch('algorithm_page.data_directory', return_value=Path(temporary.name))
        run_paths.start(); self.addCleanup(run_paths.stop)
        self.window = SecondWindow(maintenance=False)
        self.window.show()
        self.window.findChild(QTabWidget).setCurrentIndex(1)
        self.panel = self.window.tab_optimization
        self.app.processEvents()

    def tearDown(self):
        if getattr(self.window, '_busy', False):
            self.panel.stop_run()
            self.wait_idle()
        for name in ('validation_dialog',):
            dialog = getattr(self.panel, name, None)
            if dialog is not None:
                dialog.reject()
        self.window.close()
        self.app.processEvents()

    def wait_idle(self):
        deadline = time.monotonic() + 15
        while getattr(self.window, '_busy', False) and time.monotonic() < deadline:
            self.app.processEvents()
            QTest.qWait(20)
        self.assertFalse(self.window._busy)

    def test_edit_feedback_clears_after_fix_without_popup(self):
        field = self.panel.params['群体粒子个数 (N)']
        field.setFocus();field.selectAll()
        QTest.keyClicks(field, '0')
        QTest.qWait(450)
        self.assertTrue(field.property('invalid'))
        self.assertTrue(self.panel.field_error_labels['群体粒子个数 (N)'].isVisible())
        self.assertIsNone(getattr(self.panel, 'validation_dialog', None))
        field.selectAll();QTest.keyClicks(field, '4');QTest.qWait(450)
        self.assertFalse(field.property('invalid'))
        self.assertFalse(self.panel.validation_summary.isVisible())

    def test_submit_highlights_all_errors_and_preserves_result(self):
        self.panel.gb_data = np.array([3., 2.])
        for key in ('群体粒子个数 (N)', '最大迭代次数 (T)'):
            self.panel.params[key].setText('0')
        QTest.mouseClick(self.panel.run_button, Qt.LeftButton)
        self.app.processEvents()
        self.assertFalse(hasattr(self.panel, 'worker'))
        self.assertEqual(sum(bool(w.property('invalid')) for w in self.panel.params.values()), 2)
        dialog = self.panel.validation_dialog
        self.assertTrue(dialog.isVisible())
        self.assertIn('群体', dialog.message.text())
        QTest.mouseClick(dialog.accept_button, Qt.LeftButton)
        QTest.qWait(30)
        self.assertTrue(self.panel.params['群体粒子个数 (N)'].hasFocus())
        np.testing.assert_array_equal(self.panel.gb_data, [3., 2.])

    def test_algorithm_constraints_and_fixed_dimensions(self):
        self.assertTrue(self.panel.params['粒子维数 (D)'].isReadOnly())
        for name, number in [('DE', '3'), ('IA', '3')]:
            self.panel.algorithm_combo.setCurrentText(name)
            self.panel.params['群体粒子个数 (N)'].setText(number)
            with self.assertRaises(ParameterValidationError) as caught:
                validate_params(name, self.panel.form_values(), True)
            self.assertIn('群体粒子个数 (N)', caught.exception.field_errors)
        self.panel.identification_combo.setCurrentText('多目标')
        self.assertTrue(self.panel.params['参数维度 (dim)'].isReadOnly())
        self.assertTrue(self.panel.params['目标函数数量 (obj_no)'].isReadOnly())

    def test_wrapped_errors_expand_rows_and_scroll_without_old_fields(self):
        old_fields = list(self.panel.params.values())
        self.panel.algorithm_combo.setCurrentText('IA')
        self.assertTrue(all(field.parentWidget().isHidden() for field in old_fields))
        self.panel.params['群体粒子个数 (N)'].setText('3')
        self.panel.params['最大迭代次数 (T)'].setText('0')
        self.panel.start_run()
        QTest.qWait(50)
        previous_bottom = -1
        for name, field in self.panel.params.items():
            holder = field.parentWidget()
            self.assertGreater(holder.y(), previous_bottom)
            previous_bottom = holder.geometry().bottom()
            error = self.panel.field_error_labels[name]
            if error.isVisible():
                self.assertGreaterEqual(error.height(), error.heightForWidth(error.width()))
                self.assertGreater(error.y(), field.geometry().bottom())
                self.assertLessEqual(error.geometry().bottom(), holder.height())
        self.assertGreater(self.panel.param_scroll_area.verticalScrollBar().maximum(), 0)

    def test_persistent_bad_curve_is_visible_and_recovers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.mat'
            path.write_bytes(b'broken MAT file')
            self.panel.data_files[self.panel.current_algorithm] = str(path)
            for _ in range(5):
                self.panel.check_data_update()
            self.assertTrue(self.panel.curve_warning.isVisible())
            from scipy.io import savemat
            savemat(path, {'gBV_record': [1.], 'iter': 1})
            self.panel.check_data_update()
            self.assertFalse(self.panel.curve_warning.isVisible())

    def factory(self, *args, **kwargs):
        args = list(args)
        args[1] = dict(args[1], _scenario='calculation_hang')
        return MatlabWorker(*args, **kwargs, limits=RunLimits(10, 20, 5, .3),
                            runner_script=ROOT / 'tests/fixtures/process_scenarios.py')

    def test_stop_button_restores_controls_and_shows_cancelled(self):
        with patch('algorithm_page.MatlabWorker', side_effect=self.factory):
            self.panel.start_run()
        QTest.qWait(300)
        self.assertTrue(self.panel.stop_button.isEnabled())
        self.assertFalse(self.window.tab_identification.run_button.isEnabled())
        QTest.mouseClick(self.panel.stop_button, Qt.LeftButton)
        self.wait_idle()
        self.assertTrue(self.panel.run_button.isEnabled())
        self.assertFalse(self.panel.stop_button.isEnabled())
        self.assertEqual(self.panel.run_state, 'cancelled')
        self.assertIn('已停止', ' '.join(x.text() for x in self.panel.info_form_widget.findChildren(QLabel)))

    def test_close_can_continue_then_stop_and_close(self):
        with patch('algorithm_page.MatlabWorker', side_effect=self.factory):
            self.panel.start_run()
        QTest.qWait(300)
        self.assertFalse(self.window.close())
        self.app.processEvents()
        dialog = self.window._close_dialog
        self.assertTrue(dialog.isVisible())
        QTest.mouseClick(dialog.reject_button, Qt.LeftButton)
        self.assertTrue(self.window.isVisible())
        self.assertTrue(self.window._busy)
        self.window.close();self.app.processEvents()
        QTest.mouseClick(self.window._close_dialog.accept_button, Qt.LeftButton)
        self.wait_idle()
        self.assertFalse(self.window.isVisible())

    def test_close_confirmation_after_task_finishes(self):
        with patch('algorithm_page.MatlabWorker', side_effect=self.factory):
            self.panel.start_run()
        self.window.close();self.app.processEvents()
        self.panel.stop_run();self.wait_idle()
        self.assertTrue(self.window._close_dialog.isVisible())
        QTest.mouseClick(self.window._close_dialog.accept_button, Qt.LeftButton)
        self.app.processEvents()
        self.assertFalse(self.window.isVisible())

    def test_large_workload_requires_explicit_run_choice(self):
        self.panel.params['群体粒子个数 (N)'].setText('1000')
        self.panel.start_run()
        self.assertTrue(self.panel.workload_dialog.isVisible())
        self.assertFalse(hasattr(self.panel, 'worker'))
        self.panel.workload_dialog.reject()
        self.assertFalse(hasattr(self.panel, 'worker'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
