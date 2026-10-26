# Multi-objective support functions

Helper functions for the MOGOA-based routines in the parent directory. Original author and reference notices are kept in each file; sources and terms are listed in [THIRD_PARTY_NOTICES.md](../../../../THIRD_PARTY_NOTICES.md).

Compared with the original helpers, the archive and selection functions handle duplicate or empty archives, single-member ranking, invalid roulette weights and tied TOPSIS objectives. `servo_parallel_workers.m` limits the parallel pool to two workers and runs serially when the Parallel Computing Toolbox or enough memory is not available.

## Hypervolume

`servo_hypervolume` uses the same fixed scales for all four routines: 0.025 p.u. steady-state error, 20% overshoot and 0.5 s settling time, matching the feasibility limits and post-step horizon of the 0.5 p.u. step model. `myHV` adds a 10% margin, so the reference point is `[0.0275, 22, 0.55]`. HV is normalized by the reference box; higher is better. The reference does not depend on population size, iteration count or observed objective values. Update it if the step command, horizon or constraints change.

Each progress MAT file stores `diagnostics.archive_objectives` and `diagnostics.hv`, so the HV history can be recomputed.
