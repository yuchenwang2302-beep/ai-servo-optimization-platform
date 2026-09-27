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

`servo_hypervolume` evaluates all four multi-objective routines with fixed
physical scales: `[0.025 p.u., 20 percent, 0.5 s]` for steady-state error,
overshoot and settling time in the supplied 0.5-p.u. step model. These are the
feasibility limits and post-step simulation horizon. The PlatEMO-derived `myHV`
uses a 10% margin, giving the physical reference point `[0.0275, 22, 0.55]`,
and reports volume normalized by the reference box. Higher HV is better for
this fixed configuration. Archive capacity can make the history nonmonotonic.
The reference does not depend on population, iteration or observed maxima.
Update the configuration if model command, horizon or constraints change.

Each progress MAT file also stores `diagnostics.archive_objectives` (one matrix
per completed iteration) and `diagnostics.hv` (scales, reference and counts),
so the plotted history can be independently recalculated. Existing progress
readers still use `gBV_record` and `iter`. Search and archive selection are
unchanged. The inherited `GetOptimum` remains only in unused legacy IGD/DM/
DeltaP calculations; those values are not exposed or interpreted as servo
performance because a true reference Pareto front is not available.

Local recovery provenance and original SHA-256 digests are recorded in
`docs/provenance/recovered_dependencies.json` (paths relative to the original
PyQTproject3 project). The original local record remains in
`runtime/functional_check/recovered_dependencies.json`.
