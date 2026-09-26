# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Use the original Qt page and a real worker to verify one complete run."""
from pathlib import Path
import argparse
import json
import os
import sys
import time
import numpy as np
os.environ['QT_QPA_PLATFORM']='offscreen'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication,QLabel,QTabWidget
from second_window import SecondWindow
from i18n import set_language, tr

parser=argparse.ArgumentParser()
parser.add_argument('--mode',choices=['identification','single','multi'],default='single')
parser.add_argument('--language',choices=['zh','en'],default='zh')
parser.add_argument('--output',type=Path,default=ROOT/'runtime/functional_check')
args=parser.parse_args()
set_language(args.language)
output=args.output
output.mkdir(parents=True,exist_ok=True)
app=QApplication([])
QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
window=SecondWindow(maintenance=False);window.show();app.processEvents()
window.grab().save(str(output/'ui_after_idle.png'))
panel=window.tab_identification if args.mode=='identification' else window.tab_optimization
if args.mode!='identification':
    window.findChild(QTabWidget).setCurrentIndex(1)
    if args.mode=='multi':
        panel.identification_combo.setCurrentIndex(panel.identification_combo.findData('multi'))
        panel.params['种群大小 (N)'].setText('4')
        panel.params['存档大小 (ArchiveMaxSize)'].setText('8')
    else:
        panel.algorithm_combo.setCurrentText('GA')
        panel.function_combo.setCurrentText('ISE')
if args.mode!='multi':
    panel.params['群体粒子个数 (N)'].setText('2')
panel.params['最大迭代次数 (T)'].setText('1')
events=[];start=time.monotonic()
panel.start_run()
panel.worker.error.connect(lambda message:events.append({'error':message}))
panel.worker.status.connect(lambda message:print(message,flush=True))
def record_result(success, best, parameters, times, reference, position):
    measured = float(np.trapezoid((position-reference)**2, times))
    events.append({'success': bool(success and (args.mode=='multi' or np.isclose(best, measured, rtol=1e-6, atol=1e-10))),
                   'best': best, 'independent_ISE': measured, 'samples': len(times)})
    np.savez(output/'live_ui_tracking.npz', time=times, reference=reference, position=position)

def record_identification(curve, parameters, best):
    events.append({'success': bool(len(curve)==1 and len(parameters)==10 and np.isclose(curve[-1],best)),
                   'best':float(best),'parameters':parameters})

if args.mode=='identification':
    panel.worker.identification_finished.connect(record_identification)
else:
    panel.worker.optimization_finished.connect(record_result)

def finish():
    app.processEvents()
    texts=' '.join(label.text() for label in panel.info_form_widget.findChildren(QLabel))
    success=(len(events)==1 and events[0].get('success') and len(panel.gb_data)==1
             and panel.run_button.isEnabled() and not window._busy and tr('运行完成') in texts
             and (panel.line if args.mode=='identification' else panel.convergence_line).get_marker() == 'o')
    panel_result={'mode':args.mode,'language':args.language,'passed':bool(success),'events':events,'curve':panel.gb_data.tolist(),
                  'seconds':time.monotonic()-start,'displayed_text':texts,'run_directory':panel.worker.data_folder}
    (output/'live_ui_result.json').write_text(json.dumps(panel_result,ensure_ascii=False,indent=2),encoding='utf-8')
    window.grab().save(str(output/'ui_live_completed.png'))
    print('PASS' if success else 'FAIL',panel_result,flush=True)
    window.close();app.exit(0 if success else 1)

panel.worker.finished.connect(lambda:QTimer.singleShot(200,finish))
sys.exit(app.exec_())
