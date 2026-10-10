"""E5 - does refitting track detectors whose calibration changes? Fixed fit vs rolling fit.

E1 fitted once on March and its gain on the M1 decayed by June; E3 found dated steps in
single detectors' length measurement. If biases drift or step, refitting on the most
recent month should hold the gain. Compared, on the same scoring pairs as E1:

    fixed      biases fitted on March, applied to April, May and June
    rolling    biases fitted on the month before, applied to the month after
               (March -> April, April -> May, May -> June)

Policy: correct every detector with a fit on a chain of 3 or more, additive model (the
best policy in E1). Scored per month: mean |gap| below 520 cm over the pairs touched,
raw and corrected, and the number of touched pairs made worse by more than one point.

Output: results/e5_refit.json
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import method
import pairs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MONTHS = ["2025-03", "2025-04", "2025-05", "2025-06"]


def fit(road, month):
    fits = {}
    for chain in pairs.chains(road, month):
        for f in method.solve_chain(chain):
            if f["chain_size"] >= 3:
                fits[f["detector"]] = f
    return fits


def score(road, month, fits):
    raw, corr, worse = [], [], 0
    for chain in pairs.chains(road, month):
        for up, down, nid, rec in chain:
            if up not in fits and down not in fits:
                continue
            a = rec["a"] if up not in fits else \
                method.correct_series(rec["a"], fits[up], "additive")
            b = rec["b"] if down not in fits else \
                method.correct_series(rec["b"], fits[down], "additive")
            g_raw = method.pair_gap(rec)[0][0]
            g_cor = method.pair_gap({"keys": rec["keys"], "a": a, "b": b})[0][0]
            raw.append(abs(g_raw))
            corr.append(abs(g_cor))
            if abs(g_cor) > abs(g_raw) + 0.01:
                worse += 1
    return {"touched_pairs": len(raw),
            "raw_mean_abs_gap_520": round(sum(raw) / len(raw), 5),
            "corrected_mean_abs_gap_520": round(sum(corr) / len(corr), 5),
            "worse_by_1pt": worse}


def main():
    report = {"policy": "all/additive, chains of 3 or more", "roads": {}}
    for road in ("M25", "M1"):
        fits = {m: fit(road, m) for m in MONTHS}
        res = {"fixed": {}, "rolling": {}}
        for i, month in enumerate(MONTHS[1:], start=1):
            res["fixed"][month] = score(road, month, fits[MONTHS[0]])
            res["rolling"][month] = score(road, month, fits[MONTHS[i - 1]])
            print(road, month, "fixed", res["fixed"][month])
            print(road, month, "rolling", res["rolling"][month])
        report["roads"][road] = res
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "e5_refit.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
