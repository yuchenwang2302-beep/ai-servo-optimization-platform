# Paper data and numerical figures

Numerical records and plotting scripts for *A Unified Task-Oriented Framework for Servo Controller Optimization*.

The reported experiments were recorded with tag `paper-evaluation-v2` (`43f41420187ec528ac0cf2055a77cfa97bf7cdfa`). Tag `optimization-ui-v1` contains the same numerical routines and Simulink models; it changes only the interface, which is restricted to controller tuning. The data here include the 12-iteration PSO case and the two controller selections from the 13-member MOGOA archive.

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

`data/multiobjective_gui.csv` retains the response selected automatically by the interface. The GUI selection and the two preference selections in Fig. 5 are identified separately in `results.json`.

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
