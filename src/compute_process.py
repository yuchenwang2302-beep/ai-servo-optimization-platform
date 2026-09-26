# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Private computation entry point. The GUI owns its Windows job and deadlines."""
import json
from pathlib import Path
import sys
import threading


def send(event, **payload):
    print(json.dumps(dict(event=event, **payload), ensure_ascii=True), flush=True)


def main():
    # Do not import/start MATLAB before the parent has contained this process.
    if sys.stdin.readline().strip() != 'start':
        return 2
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import numpy as np
    from engine_task import EngineTask
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    from i18n import set_language, tr
    set_language(request.get('language', 'zh'))
    directory = Path(request['run_directory'])
    task = EngineTask(request['algorithm'], request['params'], request['optimization'], run_directory=directory)

    def status(state):
        text = {'starting': '正在启动 MATLAB…', 'running': '正在计算，完成迭代后更新曲线…',
                'cleaning': '正在释放 MATLAB 资源…'}[state]
        send('state', state=state, text=tr(text))

    def save_identification(curve, parameters, best):
        np.savez(directory / 'result.npz', curve=curve, parameters=parameters, best=best)
        send('result')

    def save_optimization(success, best, parameters, times, reference, position):
        np.savez(directory / 'result.npz', best=best, parameters=parameters,
                 time=times, reference=reference, position=position)
        send('result')

    task.state_changed.connect(status)
    task.engine_started.connect(lambda pid: send('engine', pid=pid))
    task.error.connect(lambda text: send('error', text=text))
    task.cancelled.connect(lambda: send('cancelled'))
    task.identification_finished.connect(save_identification)
    task.optimization_finished.connect(save_optimization)

    def commands():
        for line in sys.stdin:
            if line.strip() == 'stop':
                task.stop()
        task.stop()  # Parent disconnected; its job also guarantees tree cleanup.

    threading.Thread(target=commands, daemon=True).start()
    task.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
