# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Regression checks for the existing UI and MATLAB execution contract."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from scipy.io import savemat
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QTabWidget
from login import Ui_Dialog
from second_window import SecondWindow
from engine_task import EngineTask as MatlabWorker
from run_support import validate_params, read_curve, validate_tracking


def params(optimization=False):
    values = {'群体粒子个数 (N)': 4, '粒子维数 (D)': 11 if optimization else 10,
              '最大迭代次数 (T)': 2, '速度 (vref)': 200, 'objective': 'IAE'}
    for i, pair in enumerate(([1.5e-4,2.5e-4],[1.5e-4,2.5e-4],[.3,.4],[.006,.007],[5e-5,1e-4]),1):
        values[f'范围(t{i}L)'] = pair
    return values


class Future:
    def __init__(self, value=None, failure=None, pending=False):
        self.value, self.failure, self.pending = value, failure, pending
        self.cancelled = False
    def done(self): return not self.pending
    def result(self):
        if self.failure: raise RuntimeError(self.failure)
        return self.value
    def cancel(self):
        self.cancelled = True
        self.pending = False
        return True


class Engine:
    def __init__(self, failure=None, missing=None):
        self.failure, self.missing, self.closed = failure, missing, False
        self.args = None
        self.models_closed = False
        self.quit_requested = False
    def genpath(self, path): return path
    def addpath(self, *args, **kwargs): pass
    def cd(self, folder, **kwargs): self.folder = Path(folder)
    def which(self, name): return '' if name == self.missing else name
    def bdclose(self, *args, **kwargs): self.models_closed = True
    def eval(self, command, **kwargs):
        assert self.models_closed and command == 'quit force'
        self.quit_requested = True
    def quit(self): self.closed = True
    def __getattr__(self, name):
        def call(*args, **kwargs):
            self.args = (name, args, kwargs)
            prefix = 'pso' if name.startswith('pso') else 'ga'
            savemat(self.folder/(prefix+'_temp_data.mat'), {'gBV_record': [[1.0,0.0]], 'iter': [[2]]})
            if name in ('pso2','GA'):
                value = ([1.,0.], [1e-4]*10, 0.)
            else:
                value = (0., [1e-9]*11, [0.,1.], [0.,0.], [0.,0.])
            return Future(value, self.failure)
        return call


class ValidationTests(unittest.TestCase):
    def test_invalid_parameters_and_ranges(self):
        for key, value in [('群体粒子个数 (N)',0),('粒子维数 (D)',5),('最大迭代次数 (T)',-1),
                           ('速度 (vref)','nan'),('范围(t1L)','[2,1]'),('范围(t2L)','[1]')]:
            with self.subTest(key=key):
                values=params();values[key]=value
                with self.assertRaises(ValueError):validate_params('PSO',values)
        for algorithm, population in [('DE',3),('IA',3)]:
            values=params();values['群体粒子个数 (N)']=population
            with self.assertRaises(ValueError):validate_params(algorithm,values)

    def test_ranges_accept_scientific_notation(self):
        values=params();values['范围(t1L)']='[1.6e-4, 2.4e-4]'
        self.assertEqual(validate_params('PSO',values)['parameter_bounds'][0],[1.6e-4,2.4e-4])

    def test_curve_preserves_zero_and_iteration_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'curve.mat'
            savemat(path,{'gBV_record':[[3.,0.,99.]],'iter':[[2]]})
            np.testing.assert_array_equal(read_curve(path),[3.,0.])

    def test_tracking_rejects_empty_mismatched_or_nonfinite(self):
        for values in [([],[],[]),([0,1],[1],[1]),([0,1],[0,float('nan')],[0,0]),([1,0],[0,0],[0,0])]:
            with self.assertRaises(ValueError):validate_tracking(*values)


class WorkerTests(unittest.TestCase):
    def test_cleanup_releases_engine_before_owned_process(self):
        events=[]
        class ClosingModels:
            def result(self, timeout):
                events.append(('model_wait',timeout))
                raise TimeoutError('model close stalled')
        class TestEngine:
            def bdclose(self,*args,**kwargs):
                events.append(('bdclose_async',kwargs['background']))
                return ClosingModels()
            def eval(self,*args,**kwargs):
                events.append('unexpected_exit_evaluation')
            def quit(self):events.append('release_engine')
        class OwnedProcess:
            def close(self):
                events.append('close_owned_process')
                return True
        with tempfile.TemporaryDirectory() as directory:
            worker=MatlabWorker('PSO',params(),data_folder=directory)
            worker._log=io.StringIO()
            self.assertIsNone(worker._cleanup_engine(TestEngine(),OwnedProcess()))
            self.assertEqual(events,[('bdclose_async',True),('model_wait',5),
                                     'release_engine','close_owned_process'])
            self.assertIn('model close stalled',worker._log.getvalue())
            self.assertIn('owned process',worker._log.getvalue())

    @unittest.skipUnless(os.name == 'nt', 'Windows process lifecycle')
    def test_owned_process_cleanup(self):
        from matlab_process import OwnedWindowsProcess
        for hangs in (False, True):
            child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)' if hangs else 'pass'],
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                process = OwnedWindowsProcess(child.pid)
                if not hangs:
                    child.wait(timeout=10)
                self.assertEqual(process.close(wait_ms=0), hangs)
                child.wait(timeout=10)
            finally:
                if child.poll() is None:
                    child.terminate(); child.wait(timeout=10)

    def test_objective_and_cleanup_before_result(self):
        engine=Engine();events=[]
        with tempfile.TemporaryDirectory() as directory:
            worker=MatlabWorker('PSO',params(True),True,directory,lambda **kwargs:Future(engine))
            worker.optimization_finished.connect(lambda *args:events.append(engine.closed))
            worker.run()
            self.assertEqual(events,[True])
            self.assertTrue(engine.models_closed)
            self.assertFalse(engine.quit_requested)
            self.assertEqual(engine.args[1][-1],'IAE')
            self.assertTrue(all(isinstance(x,float) for x in engine.args[1][:-1]))

    def test_error_still_cleans_up(self):
        engine=Engine(failure='simulation failed');errors=[]
        with tempfile.TemporaryDirectory() as directory:
            worker=MatlabWorker('PSO',params(True),True,directory,lambda **kwargs:Future(engine))
            worker.error.connect(errors.append);worker.run()
            self.assertEqual(errors,['simulation failed']);self.assertTrue(engine.closed)

    def test_missing_dependency_is_reported(self):
        engine=Engine(missing='Jerk_FF_Step_2023');errors=[]
        with tempfile.TemporaryDirectory() as directory:
            worker=MatlabWorker('PSO',params(True),True,directory,lambda **kwargs:Future(engine))
            worker.error.connect(errors.append);worker.run()
            self.assertIn('Jerk_FF_Step_2023',errors[0]);self.assertTrue(engine.closed)

    def test_cancel_future_and_isolate_runs(self):
        worker=MatlabWorker('PSO',params(True),True);future=Future(pending=True)
        worker.stop()
        from engine_task import RunCancelled
        with self.assertRaises(RunCancelled):worker._wait(future)
        self.assertTrue(future.cancelled)
        self.assertNotEqual(worker.data_file,MatlabWorker('PSO',params(True),True).data_file)


class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        run_paths = patch('algorithm_page.data_directory', return_value=Path(temporary.name))
        run_paths.start(); self.addCleanup(run_paths.stop)
        from i18n import set_language
        set_language('zh')
        preference = patch('login.load_language', return_value='zh')
        preference.start();self.addCleanup(preference.stop)
        login_window = patch('login.SecondWindow', side_effect=lambda: SecondWindow(maintenance=False))
        login_window.start(); self.addCleanup(login_window.stop)
        self.window=SecondWindow(maintenance=False);self.window.show()
    def tearDown(self):
        self.window.set_run_busy(False);self.window.close();self.app.processEvents()
    def wait_for_worker(self):
        deadline=time.monotonic()+5
        while getattr(self.window,'_busy',False) and time.monotonic()<deadline:
            self.app.processEvents();QTest.qWait(10)
        self.assertFalse(self.window._busy)

    def test_two_pages_and_all_forms(self):
        original = json.loads((ROOT/'tests/fixtures/original_forms.json').read_text(encoding='utf-8'))
        self.assertEqual(self.window.findChild(QTabWidget).count(),2)
        for i in range(self.window.tab_identification.algorithm_combo.count()):
            self.window.tab_identification.algorithm_combo.setCurrentIndex(i)
            values={k:v.text() for k,v in self.window.tab_identification.params.items()}
            self.assertEqual(values,original['identification/'+self.window.tab_identification.current_algorithm])
            validate_params(self.window.tab_identification.current_algorithm,values)
        panel=self.window.tab_optimization
        for mode in range(2):
            panel.identification_combo.setCurrentIndex(mode)
            for i in range(panel.algorithm_combo.count()):
                panel.algorithm_combo.setCurrentIndex(i)
                values={k:v.text() for k,v in panel.params.items()}
                self.assertEqual(values,original[('single/' if mode==0 else 'multi/')+panel.current_algorithm])
                values['objective']=panel.function_combo.currentText()
                validate_params(panel.current_algorithm,values,True)

    def test_invalid_input_preserves_previous_result(self):
        self.window.tab_identification.gb_data=np.array([3.,2.]);self.window.tab_identification.params['最大迭代次数 (T)'].setText('0')
        self.window.tab_identification.run_identification()
        np.testing.assert_array_equal(self.window.tab_identification.gb_data,[3.,2.])
        self.assertFalse(hasattr(self.window.tab_identification,'worker'))

    def test_busy_locks_both_pages_and_prevents_close(self):
        self.window.set_run_busy(True)
        self.assertFalse(self.window.tab_identification.algorithm_combo.isEnabled())
        self.assertFalse(self.window.tab_optimization.run_button.isEnabled())
        self.assertFalse(self.window.close());self.assertTrue(self.window.isVisible())
        self.window.tab_optimization.run_optimization()
        self.assertFalse(hasattr(self.window.tab_optimization,'worker'))

    def test_completed_run_reads_final_curve_and_can_run_again(self):
        panel=self.window.tab_optimization
        def factory(*args,**kwargs):
            kwargs.pop('runtime_limit_seconds', None)
            kwargs['engine_factory']=lambda **kw:Future(Engine())
            return MatlabWorker(*args,**kwargs)
        with patch('algorithm_page.MatlabWorker',side_effect=factory):
            for _ in range(2):
                panel.run_optimization();self.wait_for_worker()
                np.testing.assert_array_equal(panel.gb_data,[1.,0.])
                labels=' '.join(x.text() for x in panel.info_form_widget.findChildren(QLabel))
                self.assertIn('运行完成',labels);self.assertIn('1e-09',labels)
                self.assertTrue(panel.run_button.isEnabled())

    def test_failure_releases_controls(self):
        panel=self.window.tab_optimization
        def factory(*args,**kwargs):
            kwargs.pop('runtime_limit_seconds', None)
            kwargs['engine_factory']=lambda **kw:Future(Engine(failure='test failure'))
            return MatlabWorker(*args,**kwargs)
        with patch('algorithm_page.MatlabWorker',side_effect=factory):
            panel.run_optimization();self.wait_for_worker()
        self.assertTrue(panel.run_button.isEnabled())
        self.assertIn('test failure',' '.join(x.text() for x in panel.info_form_widget.findChildren(QLabel)))

    def test_identification_forwards_ranges_and_displays_final_result(self):
        engine=Engine()
        def factory(*args,**kwargs):
            kwargs.pop('runtime_limit_seconds', None)
            kwargs['engine_factory']=lambda **kw:Future(engine)
            return MatlabWorker(*args,**kwargs)
        self.window.tab_identification.params['Lq轴电感范围(t1L)'].setText('[1.6e-4, 2.4e-4]')
        self.window.tab_identification.params['最大迭代次数 (T)'].setText('2')
        with patch('algorithm_page.MatlabWorker',side_effect=factory), patch.dict(sys.modules,{'matlab':SimpleNamespace(double=lambda value:value)}):
            self.window.tab_identification.run_identification();self.wait_for_worker()
        self.assertEqual(engine.args[1][-1][0],[1.6e-4,2.4e-4])
        np.testing.assert_array_equal(self.window.tab_identification.gb_data,[1.,0.])
        self.assertIn('运行完成',' '.join(x.text() for x in self.window.tab_identification.info_form_widget.findChildren(QLabel)))

    def test_one_iteration_has_visible_point(self):
        self.window.tab_identification.gb_data = np.array([0.])
        self.window.tab_identification._run_params = {'最大迭代次数 (T)': 1}
        self.window.tab_identification.update_plot_from_data()
        self.assertEqual(self.window.tab_identification.line.get_marker(), 'o')
        panel = self.window.tab_optimization
        panel.gb_data = np.array([0.])
        panel._run_params = {'最大迭代次数 (T)': 1}
        panel._run_algorithm = 'MOGOA'
        panel.update_convergence_plot()
        self.assertEqual(panel.convergence_line.get_marker(), 'o')
        self.assertEqual(panel.convergence_line.get_label(), 'HV（超体积）')

    def test_login_button_and_enter(self):
        for enter in (False,True):
            dialog=QDialog();ui=Ui_Dialog();ui.setupUi(dialog);dialog.show()
            ui.lineEdit.setText('111');ui.lineEdit_2.setText('111')
            if enter:QTest.keyClick(ui.lineEdit_2,Qt.Key_Return)
            else:QTest.mouseClick(ui.pushButton,Qt.LeftButton)
            self.app.processEvents()
            self.assertTrue(ui.second_window.isVisible());ui.second_window.close()
        dialog=QDialog();ui=Ui_Dialog();ui.setupUi(dialog)
        ui.pushButton.click();self.app.processEvents()
        self.assertTrue(ui._error_dialog.isVisible())
        ui._error_dialog.accept();dialog.close()


if __name__=='__main__':unittest.main(verbosity=2)
