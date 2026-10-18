"""Check the recorded paper results without starting MATLAB."""
from pathlib import Path
import csv
import hashlib
import json

import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPO = ROOT.parent


def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def series(name):
    z = np.genfromtxt(DATA / name, delimiter=",", names=True)
    t = z["time_s"]
    assert len(t) == 10001 and np.all(np.diff(t) > 0), name
    assert all(np.isfinite(z[k]).all() for k in z.dtype.names), name
    return z


def controller_parameters():
    with (DATA / "controller_parameters.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows, {k: np.array([float(row[k]) for row in rows])
                  for k in rows[0] if k != "parameter"}


def single_metrics(z, name):
    t, r, y = z["time_s"], z["reference_pu"], z[name]
    error = y - r
    step = t[np.flatnonzero(r != r[0])[0]]
    outside = np.flatnonzero((t >= step) & (abs(error) > abs(r[-1]) * 0.02))
    settling = (None if len(outside) and outside[-1] == len(t) - 1 else
                float(t[outside[-1] + 1] - step) if len(outside) else 0.0)
    return {
        "ISE": float(np.trapezoid(error ** 2, t)),
        "overshoot_percent": float(max(0, (y.max() - r[-1]) / abs(r[-1]) * 100)),
        "settling_2percent_seconds": settling,
    }


def multi_metrics(z, name):
    t, r, y = z["time_s"], z["reference_pu"], z[name]
    desired = r[-1]
    steady = abs(desired - np.mean(y[t >= t[-1] - 0.15]))
    overshoot = max(0, (y.max() - desired) / abs(desired) * 100)
    outside = np.flatnonzero((y > desired + 0.005) | (y < desired - 0.005))
    settling = max(0.0, t[outside[-1]] - 0.5) if len(outside) else 0.0
    if steady > 0.01:
        settling = 0.5
    return np.array([steady, overshoot, settling])


def box_hv(objectives, reference):
    """Independent 3-D box-union volume in the fixed normalized reference box."""
    q = np.atleast_2d(objectives).astype(float) / np.asarray(reference)
    q = q[np.all(np.isfinite(q), axis=1) & np.all(q <= 1, axis=1)]
    assert np.all(q >= 0)
    if not len(q):
        return 0.0
    total = 0.0
    xs = np.unique(np.r_[q[:, 0], 1.0])
    for x0, x1 in zip(xs[:-1], xs[1:]):
        active = q[q[:, 0] <= x0]
        ys = np.unique(np.r_[active[:, 1], 1.0])
        for y0, y1 in zip(ys[:-1], ys[1:]):
            zs = active[active[:, 1] <= y0, 2]
            if len(zs):
                total += (x1 - x0) * (y1 - y0) * (1 - float(np.min(zs)))
    return float(total)


def verify():
    results = read("results.json")
    for name, expected in results["model_sha256"].items():
        raw = (REPO / name).read_bytes()
        normalized = raw.replace(b"\r\n", b"\n") if name.endswith(".m") else raw
        assert (hashlib.sha256(raw).hexdigest() == expected or
                hashlib.sha256(normalized).hexdigest() == results["model_sha256_lf_text"][name]), name

    rows, parameters = controller_parameters()
    assert [r["parameter"] for r in rows] == results["parameter_order"]
    np.testing.assert_array_equal(parameters["lower"], results["lower_bounds"])
    np.testing.assert_array_equal(parameters["upper"], results["upper_bounds"])
    for name, p in parameters.items():
        assert np.all(p >= parameters["lower"]) and np.all(p <= parameters["upper"]), name

    identification = np.genfromtxt(DATA / "identification.csv", delimiter=",", names=True)
    id_case, pso_case = results["primary_cases"]
    assert id_case["state"] == pso_case["state"] == "succeeded"
    assert len(identification) == id_case["iterations"] == 40
    np.testing.assert_array_equal(identification["residual"], id_case["curve"])
    assert identification["residual"][-1] == id_case["best"]
    assert len(id_case["parameters"]) == 10
    assert len(pso_case["curve"]) == pso_case["iterations"] == 12
    np.testing.assert_array_equal(parameters["pso"], pso_case["parameters"])

    single = series("single_objective.csv")
    for name, record in results["single_objective_checks"].items():
        np.testing.assert_array_equal(parameters[name], record["parameters"])
        actual = single_metrics(single, name)
        assert np.isclose(actual["ISE"], record["ISE"], rtol=1e-12, atol=1e-14), name
        for key in ["overshoot_percent", "settling_2percent_seconds"]:
            assert np.isclose(actual[key], record[key], rtol=1e-9, atol=1e-12), (name, key)
    assert np.isclose(single_metrics(single, "pso")["ISE"], pso_case["best"], rtol=1e-12, atol=1e-14)
    print("PASS: identification history, PSO vector, and three single-objective responses.")

    history = read("multiobjective_history.json")
    assert len(history["curve"]) == len(history["archive_objectives"]) == 12
    computed_hv = [box_hv(f, history["reference"]) for f in history["archive_objectives"]]
    np.testing.assert_allclose(computed_hv, history["curve"], rtol=1e-12, atol=1e-14)
    assert history["curve"][-1] == results["multiobjective"]["final_reported_HV"]
    archive = np.genfromtxt(DATA / "multiobjective_archive.csv", delimiter=",", names=True)
    objectives = np.column_stack([archive[k] for k in ["steady_state_error_pu", "overshoot_percent", "settling_measure_s"]])
    np.testing.assert_array_equal(objectives, history["archive_objectives"][-1])
    assert len(archive) == 13
    low = int(np.lexsort((objectives[:, 0], objectives[:, 2], objectives[:, 1]))[0])
    fast = int(np.lexsort((objectives[:, 0], objectives[:, 1], objectives[:, 2]))[0])
    assert low != fast
    pair = series("multiobjective_responses.csv")
    for name, index in [("low_overshoot", low), ("fast_settling", fast)]:
        record = results["archive_pair"]["cases"][name]
        assert index == record["archive_index_zero_based"]
        np.testing.assert_array_equal(objectives[index], record["archive_objectives"])
        np.testing.assert_array_equal(parameters[name], [archive[k][index] for k in results["parameter_order"]])
        assert np.all(np.isclose(multi_metrics(pair, name), record["replay_objectives"], rtol=1e-7,
                                  atol=results["archive_pair"]["independent_check_atol"])), name

    gui = results["multiobjective"]
    weighted = ((objectives.max(axis=0) - objectives) /
                np.maximum(np.ptp(objectives, axis=0), np.finfo(float).eps)) * gui["selection_weights"]
    positive = np.linalg.norm(weighted - weighted.max(axis=0), axis=1)
    negative = np.linalg.norm(weighted - weighted.min(axis=0), axis=1)
    chosen = int(np.argmax(negative / np.maximum(positive + negative, np.finfo(float).eps)))
    assert chosen == gui["selected_archive_index"]
    np.testing.assert_array_equal(parameters["gui_selected"], [archive[k][chosen] for k in results["parameter_order"]])
    assert np.all(np.isclose(multi_metrics(series("multiobjective_gui.csv"), "position_pu"),
                              gui["selected_response_objectives"], rtol=1e-7,
                              atol=gui["response_objective_absolute_tolerance"]))
    print("PASS: all 12 HV values, 13 archive members, GUI selection, and both replayed selections.")

    recovery = read("recovery.json")
    assert len(recovery["checks"]) == 30
    for check in recovery["checks"]:
        assert check["passed"] and check["controls_restored"] and check["independent_matlab_alive"]
        assert check["process_cleanup"]["remaining_processes"] == 0
        assert check["process_cleanup"]["exit_signals_verified"] and check["all_recorded_processes_exited"]
    for name, expected in recovery["summary"].items():
        checks = [c for c in recovery["checks"] if c["condition"] == name]
        assert len(checks) == expected["n"] == 5
        latency = [c["latency_seconds"] if c["latency_seconds"] is not None else c["total_seconds"] for c in checks]
        assert np.isclose(np.median(latency), expected["median_seconds"], atol=1e-12)
        assert np.isclose(max(latency), expected["max_seconds"], atol=1e-12)
        if expected["exited_before_grace"] is not None:
            assert sum(c["termination_path"] == "exited_before_grace" for c in checks) == expected["exited_before_grace"]
            assert sum(c["termination_path"] == "grace_expired" for c in checks) == expected["grace_expired"]
    assert results["automatic_checks"]["tests_run"] == results["automatic_checks"]["passed"] == 67
    print("PASS: recorded interruption latencies, cleanup, 10 retries, and automated-test summary.")
    print("All recorded-data checks passed. MATLAB was not started.")


if __name__ == "__main__":
    verify()
