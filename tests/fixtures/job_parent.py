# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Exit without finally blocks; Windows must reclaim the contained process tree."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from process_job import ProcessJob
directory = Path(sys.argv[1])
job = ProcessJob()
request = directory / 'request.json'
request.write_text(json.dumps({'run_directory': str(directory), 'algorithm': 'PSO', 'optimization': True,
                              'params': {'_scenario': 'calculation_hang'}}))
child = subprocess.Popen([sys.executable, '-I', str(ROOT / 'tests/fixtures/process_scenarios.py'), str(request)],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         creationflags=subprocess.CREATE_NO_WINDOW | 4)
job.assign(child.pid)
job.resume(child.pid)
child.stdin.write(b'start\n');child.stdin.flush()
deadline = time.monotonic() + 10
while not (directory / 'child_pid.json').exists() and time.monotonic() < deadline:
    time.sleep(.01)
(directory / 'ready.json').write_text(json.dumps({'worker_pid': child.pid,
    'child_pid': json.loads((directory / 'child_pid.json').read_text())}))
sys.stdin.readline()
os._exit(0)
