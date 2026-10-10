"""Claim 5 on the claimed constraint set: does the irreconcilability report respond to a
real inconsistency in the observed records when the relations are recovered, not surveyed?

Same setup as discovery_v2_eval: 10 % of values withheld, relations recovered from the
training view (no map), bands calibrated on it, prior from the spatial estimator. An
interval can be reported irreconcilable only where some relation has an absent member
(that is where the projection runs), so each trial looks at the intervals of a short span
in which a relation containing the chosen detector has an absent member ("eligible").

For each trial the projection is run over the span twice: on the records as they are,
and with a fault injected into the chosen detector's OBSERVED records over the span. The
report works if eligible intervals are flagged far more often, and with a larger
shortfall, when the detector is faulty. Writes results/irreconcilable_test.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baselines, constrained, dataset, discover, discover2, faults

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CORRIDORS = (("M25", "window_full_M25_A.json"), ("M1", "window_M1_A.json"))
SPAN = 48
N_DET = 30
REPEATS = 2
CASES = (("offset", 40.0), ("offset", -40.0), ("scale", 0.8), ("stuck", 0.0))


def main(seed=0):
    rng = np.random.default_rng(seed)
    out = {"span_intervals": SPAN, "corridors": {}}
    for name, manifest in CORRIDORS:
        c = dataset.load(manifest)
        h = dataset.make_mask(c, 0.10, seed, max_run=96)
        v = dataset.train_view(c, h)
        rel, _ = discover2.discover(np.nan_to_num(v, nan=0.0), ~np.isnan(v))
        fitted = discover.relations_to_fitted(rel, c)
        train = constrained.training_corridor(c, v)
        calib = constrained.calibrate(train, fitted)
        scale = constrained.detector_scale(train)
        prior = baselines.knn_spatial(v, c.interval_index(), c.is_weekend())
        nodes_of = faults.node_membership(fitted)
        missing = np.isnan(v)
        cand = [r for r, idx in nodes_of.items() if len(idx) >= 2 and (~missing[r]).mean() > 0.85]
        pool = [cand[i] for i in sorted(rng.choice(len(cand), min(N_DET, len(cand)),
                                                   replace=False))]

        def eligible(r, cols):
            out_ = np.zeros(cols.size, dtype=bool)
            for i in nodes_of[r]:
                f = fitted[i]
                mem = [f["up"], f["down"]] + [x for x, _ in f["slips"]]
                others = [m for m in mem if m != r]
                out_ |= np.any(missing[np.ix_(others, cols)], axis=0) & ~missing[r, cols]
            return out_

        def flagged(view, cols):
            _, _, _, unrec, slack = constrained.project(prior[:, cols], view[:, cols],
                                                        fitted, calib, scale)
            return unrec.astype(bool), slack

        res = {"relations": len(fitted), "detectors": len(pool), "cases": {}}
        spans = []
        for r in pool:
            for _ in range(REPEATS):
                s0 = int(rng.integers(0, v.shape[1] - SPAN))
                spans.append((r, np.arange(s0, s0 + SPAN)))
        clean_hit, clean_n, clean_slack = 0, 0, []
        base = {}
        for k, (r, cols) in enumerate(spans):
            el = eligible(r, cols)
            fl, sl = flagged(v, cols)
            base[k] = (el, fl)
            clean_hit += int((fl & el).sum())
            clean_n += int(el.sum())
            clean_slack += sl
        res["clean"] = {"eligible_intervals": clean_n,
                        "flag_rate": round(clean_hit / clean_n, 4) if clean_n else None,
                        "mean_shortfall_vehicles": round(float(np.mean(clean_slack)), 2)
                        if clean_slack else 0.0}
        for mode, mag in CASES:
            hit, n, slacks = 0, 0, []
            for k, (r, cols) in enumerate(spans):
                el = base[k][0]
                vf = faults.inject_total(v, r, cols, mode, mag)
                fl, sl = flagged(vf, cols)
                hit += int((fl & el).sum())
                n += int(el.sum())
                slacks += sl
            res["cases"]["%s %g" % (mode, mag)] = {
                "eligible_intervals": n, "flag_rate": round(hit / n, 4) if n else None,
                "mean_shortfall_vehicles": round(float(np.mean(slacks)), 2) if slacks else 0.0}
        out["corridors"][name] = res
        print(name, json.dumps(res), flush=True)
    with open(os.path.join(RESULTS, "irreconcilable_test.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
