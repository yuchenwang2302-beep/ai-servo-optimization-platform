# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Real MATLAB comparison against a saved pre-refactor project directory."""
import argparse
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import matlab.engine
from matlab_process import OwnedWindowsProcess
from engine_task import EngineTask as MatlabWorker

parser = argparse.ArgumentParser()
parser.add_argument('baseline', type=Path)
args = parser.parse_args()
output = ROOT / 'runtime/structure_check/model_comparison'
output.mkdir(parents=True, exist_ok=True)
functions = {'fun_position': 'single_objective', 'fun_position_2': 'multi_objectives',
             'T_Jerk_FF_Step_2023_2': 'multi_objectives'}
for name, folder in functions.items():
    text = (args.baseline / 'matlab_scripts/optimization' / folder / (name + '.m')).read_text(encoding='utf-8-sig')
    text = text.replace(name, 'baseline_' + name, 1)
    (output / ('baseline_' + name + '.m')).write_text(text, encoding='utf-8')
eng = matlab.engine.start_matlab()
owned = OwnedWindowsProcess(eng.feature('getpid')) if sys.platform == 'win32' else None
log = io.StringIO()
report = []
try:
    eng.addpath(eng.genpath(str(ROOT/'matlab_scripts/optimization')), str(output), nargout=0)
    eng.cd(str(output), nargout=0)
    # Both a regular setting and a second load/controller setting.
    candidates = [([3.,6000.,2.,50.,1.,.02,.0001,20.,30.,50.,200.], .5),
                  ([4.,8000.,3.,70.,2.,.04,.0003,25.,40.,70.,400.], .3)]
    for index, (values, load) in enumerate(candidates):
        x = matlab.double(values)
        for name in functions:
            metrics = ('ITSE', 'ISE', 'IAE', 'ITAE') if name == 'fun_position' else (None,)
            for metric in metrics:
                arguments = (x, load, metric) if metric else (x, load)
                count = 4 if metric else 1
                before = getattr(eng, 'baseline_'+name)(*arguments, nargout=count, stdout=log, stderr=log)
                after = getattr(eng, name)(*arguments, nargout=count, stdout=log, stderr=log)
                if count == 1:
                    before, after = [before], [after]
                for old, new in zip(before, after):
                    np.testing.assert_array_equal(np.asarray(old), np.asarray(new))
                item = {'candidate': index+1, 'function': name, 'metric': metric, 'exactly_equal': True}
                report.append(item)
                print('PASS', item, flush=True)
finally:
    (output/'results.json').write_text(json.dumps(report,indent=2), encoding='utf-8')
    (output/'matlab.log').write_text(log.getvalue(), encoding='utf-8')
    cleanup = MatlabWorker('PSO', {})
    cleanup.data_folder = str(output)
    cleanup._log = log
    cleanup_error = cleanup._cleanup_engine(eng, owned)
    if cleanup_error:
        raise RuntimeError(cleanup_error)
