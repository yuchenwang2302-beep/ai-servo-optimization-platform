# Restored multiobjective dependencies

These files were recovered from the user's existing `PyQTproject3` project,
under `matlab_scripts/optimization/test/MOGOA_lrh/MOGOA/`.
`UniformPoint.m` came from the PlatEMO 4.7 copy in the same project's test folder.
The paired `fun_position_2.m`, `T_Jerk_FF_Step_2023_2.m`, and
`Jerk_FF_Step_2023_2.slx` are stored in the parent directory.

Original author, reference, and copyright notices are retained in each file.
The recovered PlatEMO utilities require acknowledgement of PlatEMO in
publications that use them, as stated in their source headers.

The restoration includes fixes for duplicate archive entries, empty archives,
one-member ranking, invalid roulette weights, and tied TOPSIS objectives.
`servo_parallel_workers.m` limits the desktop's parallel pool to two workers
and falls back to serial evaluation when a new pool would exceed the available
memory budget or when the parallel toolbox is unavailable.

The inherited `GetOptimum` generates synthetic reference points. HV/IGD values
are therefore implementation diagnostics; they do not establish a known true
Pareto front for this motor model.

Local recovery provenance and original SHA-256 digests are recorded in
`docs/provenance/recovered_dependencies.json` (paths relative to the original
PyQTproject3 project). The original local record remains in
`runtime/functional_check/recovered_dependencies.json`.
