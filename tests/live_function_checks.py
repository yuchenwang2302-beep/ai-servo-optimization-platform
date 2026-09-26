# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Opt-in real MATLAB/Simulink checks. Run groups separately to save intermediate results."""
from pathlib import Path
import argparse
import io
import json
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import matlab.engine
from engine_task import EngineTask as MatlabWorker
from matlab_process import OwnedWindowsProcess
from run_support import IDENTIFICATION, SINGLE, MULTI, validate_params, read_curve

parser = argparse.ArgumentParser()
parser.add_argument('--group', choices=['identification', 'single', 'multi'], required=True)
parser.add_argument('--algorithms', nargs='*')
parser.add_argument('--output', type=Path, default=ROOT / 'runtime/functional_check')
args = parser.parse_args()
output = args.output
output.mkdir(parents=True, exist_ok=True)
report = []
if args.algorithms and (output/f'{args.group}_results.json').exists():
    report = [item for item in json.loads((output/f'{args.group}_results.json').read_text())
              if item['algorithm'] not in args.algorithms]
eng = matlab.engine.start_matlab()
owned_process = OwnedWindowsProcess(eng.feature('getpid')) if sys.platform == 'win32' else None
original_path = eng.path()
print('MATLAB', eng.version(), flush=True)
try:
    eng.addpath(str(ROOT/'tests'),nargout=0)
    eng.matlab_regressions(str(ROOT),nargout=0)
    for algorithm in args.algorithms or (IDENTIFICATION if args.group == 'identification' else SINGLE if args.group == 'single' else MULTI):
        started = time.perf_counter()
        try:
            eng.bdclose('all', nargout=0)
            eng.path(original_path, nargout=0)
            eng.eval('clear functions; clearvars;', nargout=0)
            iterations = 1 if algorithm == 'IA' else 2
            population = 2 if algorithm in ('IA', 'FA') else 4
            if args.group == 'multi':
                values = {'种群大小 (N)': 4, '存档大小 (ArchiveMaxSize)': 8, '参数维度 (dim)': 11,
                          '目标函数数量 (obj_no)': 3, '最大迭代次数 (T)': 2}
                iterations = 2
            else:
                values = {'群体粒子个数 (N)': population, '粒子维数 (D)': 10 if args.group == 'identification' else 11,
                          '最大迭代次数 (T)': iterations, 'objective': 'IAE', '速度 (vref)': 200}
                for index, bound in enumerate(([1.6e-4,2.4e-4],[1.6e-4,2.4e-4],[.31,.39],[.0061,.0069],[6e-5,9e-5]),1):
                    values[f'范围(t{index}L)'] = bound
            worker = MatlabWorker(algorithm, values, is_optimization=args.group != 'identification')
            worker.params = validate_params(algorithm, values, worker.is_optimization)
            worker._log = io.StringIO()
            Path(worker.data_folder).mkdir(parents=True)
            worker._setup_matlab_path(eng)
            eng.cd(worker.data_folder, nargout=0)
            eng.rng(42., 'twister', nargout=0)
            print('RUN', args.group, algorithm, flush=True)
            result = worker._run_optimization(eng) if worker.is_optimization else worker._run_identification(eng)
            curve = read_curve(worker.data_file)
            assert len(curve) == iterations, (len(curve), iterations)
            assert np.isfinite(curve).all(), curve
            if args.group == 'identification':
                returned_curve, parameters, best = result
                np.testing.assert_allclose(curve, returned_curve)
                bounds = np.asarray(worker.params['parameter_bounds'])
                assert np.all(np.asarray(parameters[:5]) >= bounds[:,0])
                assert np.all(np.asarray(parameters[:5]) <= bounds[:,1])
                assert np.isclose(best, curve[-1])
                details = {'best': best, 'parameters': parameters}
            else:
                _, best, parameters, times, reference, position = result
                details = {'samples': len(times), 'best': best, 'parameters': parameters}
                if args.group == 'single':
                    measured = float(np.trapezoid(np.abs(position-reference), times))
                    assert np.isclose(best, measured, rtol=1e-6, atol=1e-10), (best, measured)
                    assert np.isclose(best, curve[-1])
                    details['independent_IAE'] = measured
                np.savez(output/f'{args.group}_{algorithm}_tracking.npz', time=times, reference=reference, position=position)
            report.append(dict(algorithm=algorithm, passed=True, seconds=round(time.perf_counter()-started,2),
                               curve=curve.tolist(), run_directory=worker.data_folder, **details))
            print('PASS', algorithm, report[-1]['seconds'], flush=True)
        except Exception:
            report.append(dict(algorithm=algorithm, passed=False, error=traceback.format_exc()))
            print('FAIL', algorithm, report[-1]['error'], flush=True)
        finally:
            if 'worker' in locals() and hasattr(worker, '_log'):
                (Path(worker.data_folder)/'matlab.log').write_text(worker._log.getvalue(),encoding='utf-8')
            (output/f'{args.group}_results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
finally:
    cleanup=MatlabWorker('PSO',{})
    cleanup.data_folder=str(output)
    cleanup._log=io.StringIO()
    cleanup_error=cleanup._cleanup_engine(eng,owned_process)
    if cleanup_error:
        print('Engine cleanup:',cleanup_error,flush=True)
        report.append({'passed':False,'error':cleanup_error})
sys.exit(0 if all(item['passed'] for item in report) else 1)
