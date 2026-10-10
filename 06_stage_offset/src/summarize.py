"""Summaries of a daily evaluation file: accuracy of each estimator at field visits."""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    return json.load(open(os.path.join(ROOT, "results", name + ".json")))


def rows_of(d, min_coupling=0.0, max_incr=1.0):
    out = []
    for r in d["results"]:
        if not r.get("rows"):
            continue
        if not (r.get("coupling", 0) >= min_coupling) or r["incr"] > max_incr:
            continue
        for w in r["rows"]:
            w = dict(w)
            w["x"], w["y"], w["coupling"], w["incr"] = r["x"], r["y"], r["coupling"], r["incr"]
            out.append(w)
    return out


def stats(rows, label=""):
    if not rows:
        print(label, "no rows")
        return {}
    qm = np.array([w["q_meas"] for w in rows])
    res = {"n": len(rows), "targets": len({w["x"] for w in rows})}
    for k in ("q_base", "q_carry", "q_ratio", "q_ratio_gain", "q_off", "q_gated", "q_gain"):
        e = np.abs(np.array([w[k] for w in rows], float) / qm - 1) * 100
        e = e[np.isfinite(e)]
        res[k] = (round(float(np.median(e)), 2), round(float(np.mean(e)), 2), round(float(np.percentile(e, 90)), 1))
    sm = np.array([w["s_meas"] for w in rows])
    for k in ("s_prev", "s_off", "s_gated", "s_gain"):
        e = np.abs(np.array([w[k] for w in rows]) - sm)
        res["abs_err_" + k] = (round(float(np.median(e)), 3), round(float(np.mean(e)), 3))
    ch_true = sm - np.array([w["s_prev"] for w in rows])
    ch_est = np.array([w["change"] for w in rows])
    ok = np.isfinite(ch_est)
    res["r_change"] = round(float(np.corrcoef(ch_true[ok], ch_est[ok])[0, 1]), 3)
    res["gate_rate"] = round(float(np.mean([w["gate"] for w in rows])), 3)
    print(label, json.dumps(res))
    return res


def stable_ref(rows, th=0.05):
    return [w for w in rows if w.get("ref_stab") == w.get("ref_stab") and w["ref_stab"] <= th]


if __name__ == "__main__":
    d = load(sys.argv[1] if len(sys.argv) > 1 else "daily")
    for mc in (0.0, 0.9, 0.95, 0.98):
        rows = rows_of(d, min_coupling=mc)
        if len(sys.argv) > 2:
            rows = stable_ref(rows, float(sys.argv[2]))
        stats(rows, "coupling>=%.2f" % mc)
        big = [w for w in rows if abs(w["s_meas"] - w["s_prev"]) >= 0.10]
        stats(big, "   |true change|>=0.10ft")
        small = [w for w in rows if abs(w["s_meas"] - w["s_prev"]) < 0.05]
        stats(small, "   |true change|<0.05ft")
