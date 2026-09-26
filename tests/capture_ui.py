# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Capture unchanged forms and pixels; --source can point to a baseline backup."""
import argparse
import json
import os
from pathlib import Path
import sys

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=ROOT)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(args.source / 'src'))
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication, QDialog, QTabWidget
from login import Ui_Dialog
from second_window import SecondWindow

app = QApplication([])
QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
dialog = QDialog()
ui = Ui_Dialog()
ui.setupUi(dialog)
dialog.show()
app.processEvents()
dialog.grab().save(str(args.output / 'login.png'))
dialog.close()
window = SecondWindow(maintenance=False)
window.show()
app.processEvents()
window.grab().save(str(args.output / 'identification.png'))
forms = {}
page = window.tab_identification if hasattr(window.tab_identification, 'params') else window
for i in range(page.algorithm_combo.count()):
    page.algorithm_combo.setCurrentIndex(i)
    forms['identification/' + page.current_algorithm] = {k: v.text() for k, v in page.params.items()}
window.findChild(QTabWidget).setCurrentIndex(1)
page = window.tab_optimization
for mode, name in enumerate(('single', 'multi')):
    page.identification_combo.setCurrentIndex(mode)
    app.processEvents()
    window.grab().save(str(args.output / (name + '.png')))
    for i in range(page.algorithm_combo.count()):
        page.algorithm_combo.setCurrentIndex(i)
        forms[name + '/' + page.current_algorithm] = {k: v.text() for k, v in page.params.items()}
(args.output / 'forms.json').write_text(json.dumps(forms, ensure_ascii=False, indent=2), encoding='utf-8')
window.close()
