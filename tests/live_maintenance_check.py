# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Real MATLAB/UI check for progress before iteration five and separate clocks."""
from pathlib import Path
import json
import os
import sys
import time
import numpy as np
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication, QTabWidget
from second_window import SecondWindow
from i18n import set_language

set_language('en')
output = ROOT / 'runtime/maintenance_check/live'
output.mkdir(parents=True, exist_ok=True)
app = QApplication([])
QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
window = SecondWindow(maintenance=False)
window.resize(1366, 720); window.show()
window.findChild(QTabWidget).setCurrentIndex(1)
panel = window.tab_optimization
panel.data_folder = str(output)
panel.params['群体粒子个数 (N)'].setText('2')
panel.params['最大迭代次数 (T)'].setText('3')
panel.function_combo.setCurrentText('ISE')
progress = []; states = []; errors = []; results = []
start = time.monotonic()
panel.start_run()
panel.worker.progress.connect(lambda count,total: progress.append({'iteration':count, 'seconds':time.monotonic()-start}))
panel.worker.state_changed.connect(lambda state: states.append(state))
panel.worker.status.connect(lambda text: print(text, flush=True))
panel.worker.error.connect(errors.append)
def result(success, best, parameters, times, reference, position):
    actual = float(np.trapezoid((position-reference)**2, times))
    results.append({'matches_ISE': bool(np.isclose(best, actual, rtol=1e-6, atol=1e-10)), 'best':best, 'actual_ISE':actual})
panel.worker.optimization_finished.connect(result)
def finish():
    total, calculation = panel.worker.timings()
    passed = bool(not errors and results and results[0]['matches_ISE'] and any(p['iteration'] < 3 for p in progress)
                  and panel.run_state == 'succeeded' and len(panel.gb_data) == 3
                  and 0 < calculation < total and not window._busy)
    report = {'passed':passed, 'progress':progress, 'states':states, 'errors':errors, 'results':results,
              'total_seconds':total, 'calculation_seconds':calculation, 'elapsed_label':panel.elapsed_label.text(),
              'run_directory':panel.worker.data_folder}
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    window.grab().save(str(output/'completed.png'))
    print(json.dumps(report,ensure_ascii=False),flush=True)
    window.close(); app.exit(0 if passed else 1)
panel.worker.finished.connect(lambda: QTimer.singleShot(200, finish))
sys.exit(app.exec_())
