# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic subprocess faults for supervisor tests; never imports MATLAB."""
import json
from pathlib import Path
import subprocess
import sys
import time

if sys.stdin.readline().strip() != 'start':
    sys.exit(2)
request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
root = Path(request['run_directory'])
scenario = request['params'].get('_scenario', 'success')


def send(event, **kw):
    print(json.dumps(dict(event=event, **kw)), flush=True)


child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)'],
                         creationflags=subprocess.CREATE_NO_WINDOW)
(root / 'child_pid.json').write_text(json.dumps(child.pid))
send('engine', pid=child.pid)
if scenario == 'crash':
    sys.exit(23)
if scenario != 'startup_hang':
    send('state', state='running', text='正在计算…')
if scenario == 'cleanup_hang':
    send('state', state='cleaning', text='正在清理…')
if scenario in ('startup_hang', 'calculation_hang', 'cleanup_hang'):
    while True:
        time.sleep(1)
if scenario == 'error':
    send('error', text='模拟计算失败')
    sys.exit(0)
import numpy as np
from scipy.io import savemat
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from algorithm_catalog import data_filename
count = request['params']['最大迭代次数 (T)']
curve = np.arange(count, 0, -1, dtype=float)
savemat(root / data_filename(request['algorithm'], request['optimization']),
        {'iter': count, 'gBV_record': curve})
send('state', state='cleaning', text='正在清理…')
if scenario != 'missing_result':
    if request['optimization']:
        np.savez(root / 'result.npz', best=1., parameters=[1.] * 11,
                 time=[0., 1.], reference=[0., 1.], position=[0., 0.])
    else:
        np.savez(root / 'result.npz', best=1., parameters=[1.] * 10, curve=curve)
send('result')
