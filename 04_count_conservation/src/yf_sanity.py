"""Sanity check of the Yang-Yang-Fan implementation in yf_compare.py.

Over the whole test half (not a 2-day span), a scale fault is injected at each of the
first N determined detectors in turn, and the estimated theta ratio is compared with the
value the injected fault implies. If the implementation is right, estimate and
expectation agree when the data are plentiful; the gap on 2-day spans is then the
method's own data requirement, not a defect of the implementation.
Writes results/yf_sanity_M1_A.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import classes, evaluate, faults
import yf_compare as Y

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
N = 20
GAIN = 0.90


def main():
    total = classes.load("window_M1_A.json").total
    vol = np.where(total.observed, total.volumes, np.nan)
    n = total.shape[1]
    ref, test = np.arange(n // 2), np.arange(n // 2, n)
    A = Y.node_matrix(evaluate.fit_node_signs(total), vol.shape[0])
    th_ref = Y.yf_theta(vol, ref, A)
    th_clean = Y.yf_theta(vol, test, A)
    det = np.nonzero(np.any(A != 0, axis=0) & (th_ref > Y.THETA_MIN + 0.01)
                     & (th_ref < Y.THETA_MAX - 0.01))[0][:N]
    rows = []
    for r in det:
        f = faults.inject_total(vol, int(r), test, "scale", GAIN)
        th = Y.yf_theta(f, test, A)
        expect = th_clean[r] / GAIN / th_ref[r]
        got = th[r] / th_ref[r]
        rows.append({"row": int(r), "expected_ratio": round(float(expect), 4),
                     "estimated_ratio": round(float(got), 4)})
    err = [abs(x["estimated_ratio"] - x["expected_ratio"]) for x in rows]
    out = {"gain": GAIN, "window": "test half (%d intervals)" % test.size, "detectors": len(rows),
           "median_abs_ratio_error": round(float(np.median(err)), 4),
           "max_abs_ratio_error": round(float(np.max(err)), 4), "rows": rows}
    with open(os.path.join(RESULTS, "yf_sanity_M1_A.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print({k: v for k, v in out.items() if k != "rows"})


if __name__ == "__main__":
    main()
