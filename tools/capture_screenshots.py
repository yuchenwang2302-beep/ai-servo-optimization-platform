# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Capture the current idle interface for the bilingual project guides."""
import os
from pathlib import Path
import sys
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from PyQt5.QtWidgets import QApplication, QDialog, QTabWidget
from PyQt5.QtGui import QFontDatabase
from PIL import Image
from i18n import set_language
from login import Ui_Dialog
from second_window import SecondWindow


def main():
    app = QApplication.instance() or QApplication([])
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
    output = ROOT / 'docs/images'
    output.mkdir(parents=True, exist_ok=True)

    def capture(widget, name):
        app.processEvents()
        app.processEvents()
        path = output / name
        assert widget.grab().save(str(path))
        with Image.open(path) as source:
            clean = Image.new(source.mode, source.size)
            clean.paste(source)
            clean.save(path)
        with Image.open(path) as saved:
            assert not saved.info, saved.info

    for language in ('zh', 'en'):
        set_language(language)
        dialog = QDialog()
        ui = Ui_Dialog()
        with patch('login.load_language', return_value=language):
            ui.setupUi(dialog)
        dialog.show()
        capture(dialog, f'login_{language}.png')
        dialog.close()
        window = SecondWindow(maintenance=False)
        window.resize(1366, 900)
        window.show()
        tabs = window.findChild(QTabWidget)
        assert tabs.count() == 1
        assert not hasattr(window, 'tab_identification')
        for mode, name in enumerate(('optimization', 'multiobjective')):
            window.tab_optimization.identification_combo.setCurrentIndex(mode)
            capture(window, f'{name}_{language}.png')
        window.close()
        window.deleteLater()
        dialog.deleteLater()
        app.processEvents()


if __name__ == '__main__':
    main()
