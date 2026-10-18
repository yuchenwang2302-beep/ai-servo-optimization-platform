# Paper data and numerical figures

[中文说明](#中文说明)

Numerical records for *A Unified Task-Oriented Framework for Servo Parameter Identification and Controller Optimization*. This directory is the maintained location for the paper's data and plotting scripts.

The evaluated application is `paper-evaluation-v2` (`43f41420187ec528ac0cf2055a77cfa97bf7cdfa`). The application and model sources are in the parent repository. The data here include the 12-iteration PSO case and the two controller selections from the 13-member MOGOA archive.

## Use

Python 3.9 or later is required. From the repository root:

```powershell
python -m pip install -r paper/requirements.txt
python paper/verify.py
python paper/plot.py all
```

`verify.py` checks saved numerical records using NumPy. `plot.py` exports the three numerical figures as vector PDF and preview PNG to `paper/output/`. Use `python paper/plot.py 3`, `4`, or `5` for a single figure. These commands use the saved data without starting MATLAB.

| Paper item | File | Plot output |
| --- | --- | --- |
| Fig. 3: PSO and two fixed vectors | `data/single_objective.csv` | `ui_case_response.pdf` |
| Fig. 4: final archive and preference selections | `data/multiobjective_archive.csv`, `data/multiobjective_history.json` | `final_archive.pdf` |
| Fig. 5: low-overshoot and fast-settling responses | `data/multiobjective_responses.csv` | `selected_response.pdf` |
| Table I: task settings, timings and results | `data/results.json` | |
| Table II: parameter bounds and returned vector | `data/controller_parameters.csv` | |
| Table III: single-objective response checks | `data/results.json`, `data/single_objective.csv` | |
| Table IV: interruption and failure checks | `data/recovery.json` | |

`data/identification.csv` contains the 40-iteration residual history; its ten returned variables are in `results.json`. `data/multiobjective_gui.csv` retains the response selected automatically by the interface. The GUI selection and the two preference selections in Fig. 5 are identified separately in `results.json`.

All response CSV files retain 10,001 samples at their recorded precision. Time is in seconds and position is in per-unit, with one unit corresponding to 360 degrees. The reference changes from 0 to 0.5 p.u. at 0.5 s, and the simulation ends at 1 s.

## Metrics and selections

- Single-objective ISE is the trapezoidal integral of the squared error relative to the original position command. The 2% settling time is the first sampled time after the last band violation, measured from the reference step; the band is +/-0.01 p.u.
- The multi-objective vector contains steady-state error over the final 0.15 s, overshoot in percent, and the backend settling measure. That settling measure uses the last sample outside +/-0.005 p.u., measured from the step.
- Hypervolume uses the fixed reference `[0.0275 p.u., 22%, 0.55 s]`, normalized by that reference-box volume. `multiobjective_history.json` retains all twelve objective archives and HV values.
- The low-overshoot selection is archive member 4 (one-based), breaking minimum-overshoot ties by shorter settling measure. The fast-settling selection is member 8, with ties broken by lower overshoot. Their recorded overshoot/settling pairs are 0.15% / 0.1457 s and 0.85% / 0.1138 s.
- Archive parameter columns contain eleven active controller variables. The final `backend_auxiliary` column preserves the extra coordinate used internally by the MOGOA implementation; it is not passed as a controller gain. The interface's original weighted-closeness selection is member 12.

`verify.py` independently recomputes the response metrics and all twelve HV values, checks controller selections and model hashes, and verifies the stored recovery summaries. Single-precision backend averages and independent float64 averages are compared at the tolerances recorded in `results.json`.

## Replay saved controllers in MATLAB

MATLAB R2024b, Simulink and Motor Control Blockset are required. Open the repository root in MATLAB and run:

```matlab
addpath('paper');
replay_controllers;
```

This evaluates the saved PSO, midpoint, all-upper-bound, low-overshoot, fast-settling and original GUI-selected vectors. Outputs go to `runtime/paper_replay/`. It uses the saved vectors rather than repeating the stochastic searches. The numerical routines and their original model initialization remain in `matlab_scripts/`.

Source code follows the repository [license](../LICENSE); existing model and third-party terms are described in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## 中文说明

这里统一保存当前论文使用的数值数据和绘图脚本。以后修改论文结果时，更新本目录中的对应文件即可。

常用操作：

1. 查看参数：打开 `data/controller_parameters.csv`。
2. 查看曲线数据：打开 `data/single_objective.csv` 或 `data/multiobjective_responses.csv`。
3. 核对数值：在仓库根目录运行 `python paper/verify.py`。
4. 重新画图：运行 `python paper/plot.py all`，或把 `all` 换成 `3`、`4`、`5`。
5. 在 `paper/output/` 找到 PDF，上传到 Overleaf 的 `figures/` 文件夹，覆盖同名图片。

Python 绘图只读取现有数据。需要用原模型重新计算已保存控制器时，再使用上面的 MATLAB 命令。
