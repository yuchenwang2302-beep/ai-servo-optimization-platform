# User guide

[中文](使用指南.md) · [Project overview](../README.en.md)

## Quick start

On a configured computer, double-click **[start_ui.bat](../start_ui.bat)** in the repository root. Alternatively, open the project folder in VS Code and run:

```powershell
.\start_ui.bat
```

1. Select **中文 / English** in the upper-right corner of the sign-in window.
2. Use **111** for both the demo username and password. Click the button or press Enter.
3. Select an identification or optimization mode, choose an algorithm, enter parameters and click **Run algorithm**.

Passwords are hidden by default. Use the eye icon to show or hide the password, and Tab to move between fields and controls. After a failed sign-in, dismissing the message selects the input that needs correction so it can be replaced directly.

Changing the language updates the sign-in window immediately. The main window uses the selected language, and the next launch restores it. To change the language again, use the selector at sign-in. Algorithm identifiers, default values and computation logic are unchanged. The preference is stored in the current Windows user's configuration directory; passwords are not stored there.

The launcher uses the project's own Python and isolated `.venv`. Before opening the interface, it checks dependency versions, MATLAB Engine, the MATLAB installation and model files. Failed checks stop startup and report the reason; the launcher does not fall back to system Python. Reports are saved under `runtime/startup/`.

MATLAB starts automatically when **Run algorithm** is clicked. Opening the sign-in window does not start MATLAB or validate a license. Actual computation requires a valid license. The demo sign-in is an entry screen, not an authentication or access-control system.

## Installation and environment

The current installer and process-management implementation target **64-bit Windows**. Install and authorize the following first:

- MATLAB **R2024b**;
- Simulink;
- Motor Control Blockset;
- Parallel Computing Toolbox can be used for multi-objective parallel computation; the existing implementation uses sequential execution when parallel execution is unavailable.

The application requires a full MATLAB installation. MATLAB Runtime is not a substitute. The main versions verified on the development computer are:

| Component | Version |
| --- | --- |
| MATLAB / Simulink | R2024b Update 6 |
| MATLAB Engine for Python | 24.2.2 |
| Python | 3.12.14, 64-bit |
| PyQt5 / Qt | 5.15.11 / 5.15.2 |
| NumPy / SciPy / Matplotlib | 2.0.2 / 1.13.1 / 3.9.4 |

From a new project directory that does not yet contain an environment, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\setup_environment.ps1
.\start_ui.bat --check
```

Installation requires internet access to download pinned Python, build-tool and dependency versions, with file-integrity checks. The base Python runtime is installed in `.python/` and runtime dependencies in `.venv/`. The script does not modify system Python or the system PATH. An existing valid environment is checked and retained; an invalid or incomplete environment is reported without being overwritten.

Do not copy `.venv` directly to another computer or project path. Preserve the old environment and rebuild at the new location. For everyday use, launch through `start_ui.bat`; manual environment activation and global `python` or `login` commands are unnecessary. Detailed maintenance and recovery instructions are available in the [environment guide](../docs/环境与维护.md).

## Time limits and stopping

| Interface field | Meaning |
| --- | --- |
| Max. iterations | The number of iterations the algorithm is configured to perform; computation ends when they complete normally |
| Time limit | Measured from the start of algorithm computation; defaults to **240 minutes**, adjustable to **1–1440 minutes** before a run |
| Compute | Time spent in the computation phase; stops accumulating when stopping or cleanup starts |
| Total | Total elapsed time, including MATLAB startup, computation and shutdown |

Reaching the computation time limit **triggers the stop sequence**. MATLAB startup and cleanup have separate protective time limits. Cancellation and process shutdown also take time, so total elapsed time can exceed the configured computation limit.

Click **Stop** during a run to request cancellation. Controls are restored after this run's resources have been released. Closing the main window during computation offers a choice to keep running or stop and close. Cancelled, timed-out and failed runs are not presented as complete successful results. After adjusting parameters or resolving the error, click **Run again**.

Every algorithm publishes convergence data after each completed iteration. The UI refreshes approximately once per second, so fast iterations may be displayed together. The count remains zero during initialization and the first simulation. A timeout first reports that the run is stopping and releasing resources; it reports stopped only after shutdown completes. See the [validation record](../docs/validation.md) for details of cancellation and timeout handling.

The main window adapts to the available screen. Narrow windows place controls above plots and allow scrolling when needed; wide windows retain the side-by-side layout.

## Run data and logs

Each run receives a separate timestamped directory with a unique identifier:

```text
runtime/identification/<run-id>/
runtime/optimization/<run-id>/
```

| File | Contents |
| --- | --- |
| `request.json` | Algorithm, input parameters, interface language and run directory |
| `run_state.json` | Latest run state, time limits, process identifiers, computation time and total time |
| `*_temp_data.mat` | Convergence data saved by the algorithm |
| `result.npz` | Results returned by the computation process; these must pass validation before the UI reports success |
| `matlab.log` / `process.log` | MATLAB output and computation-process diagnostics |
| `error.log` / `supervisor_error.log` | Error details when the corresponding failure occurs |

Files are generated as the run progresses. An early cancellation or startup failure may produce only some of them. **Open logs** opens the current run directory. Original MATLAB and operating-system error messages retain their source language.

**Run history**, at the bottom right of the main window, lists previous parameters, status and available results. Open a run folder or archive the complete run to protect it from automatic deletion. Archiving is a retention flag, not a separate backup; copy the directory when sharing or making an independent backup. Older records without computation-phase timing display “—”.

Automatic cleanup is enabled by default and checked after opening the main window, hourly, and after a run finishes. It keeps records from the last **30 days**, plus the latest **20 finished, unarchived runs**. Archived, unfinished and incomplete records are protected. For finished, unarchived runs older than **7 days**, rebuildable `slprj/` and `*.slxc` simulation caches can be cleared while retaining results, curves and logs.

The history window lets you disable automatic cleanup or change retention to 7–3650 days. **Clean up by policy** saves the current settings and applies the same rules immediately; it does not erase all history. Settings are stored in `runtime/retention.json`, with the latest cleanup summary in `runtime/last_cleanup.json`. Cleanup only manages recognized records directly within the two run directories above; historical test reports, unknown folders, links and junctions are not recursively deleted.

`runtime/` is excluded from Git. These records do not provide complete experiment versioning or checkpoint-based resumption.
