"""Phase 4 runner — every baseline, then the same baseline with the constraint applied.

Pairing each prior against its own constrained version isolates the contribution of the
invention. Any difference is attributable to the constraint alone, because everything
else in the pipeline is identical.

Three quantities are reported for every method:

* accuracy against withheld ground truth, overall and by gap length;
* raw conservation residual, in physical terms the vehicles that appear from or vanish
  into nothing across a node;
* feasibility, the share of node-intervals falling outside the measured tolerance band.
  This is the guarantee: for the invention it is zero by construction.
"""

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import baselines
import constrained
import dataset
import evaluate

RESULTS = os.path.join(ROOT, "results")


def run(manifest="window.json", fraction=0.10, seed=0, max_run=96,
        regime="operational", out_name="phase4_operational.json"):
    corridor = dataset.load(manifest)
    fitted = evaluate.fit_node_signs(corridor)
    hidden = dataset.make_mask(corridor, fraction=fraction, seed=seed, max_run=max_run)
    view = dataset.train_view(corridor, hidden)
    runs = evaluate.gap_run_lengths(hidden)
    slot, weekend = corridor.interval_index(), corridor.is_weekend()

    # the calibration everything is judged against
    calib = constrained.calibrate(corridor, fitted, mode="scaled")
    mean_band = float(np.mean([c["band"] for c in calib.values()]))
    mean_flow = float(np.mean([f["mean_flow"] for f in fitted]))

    print("%s: %d sites x %d intervals, %d nodes, %d cells hidden"
          % (regime, corridor.shape[0], corridor.shape[1], len(fitted), hidden.sum()))
    print("  mean node flow %.1f veh/interval, mean tolerance band %.1f veh (%.2f%%)"
          % (mean_flow, mean_band, 100 * mean_band / mean_flow))

    out = {"regime": regime,
           "corridor": {"sites": int(corridor.shape[0]),
                        "intervals": int(corridor.shape[1]),
                        "nodes_fitted": len(fitted),
                        "mean_node_flow": round(mean_flow, 1),
                        "mean_band_vehicles": round(mean_band, 2)},
           "mask": {"fraction": fraction, "seed": seed, "max_run": max_run,
                    "cells_hidden": int(hidden.sum())},
           "methods": {}}

    header = ("  %-38s %7s %8s %9s %9s" % ("method", "MAE", "RMSE", "resid%", "outside%"))

    def record(name, filled, timing=None):
        acc = evaluate.accuracy(corridor.volumes, filled, hidden, runs)
        cons = evaluate.consistency(filled, fitted, hidden)
        feas = evaluate.feasibility(filled, fitted, calib, hidden)
        out["methods"][name] = {"accuracy": acc, "consistency": cons,
                                "feasibility": feas, "timing": timing}
        print("  %-38s %7.2f %8.2f %9.3f %9.2f"
              % (name, acc["all"]["MAE"], acc["all"]["RMSE"],
                 cons["median_residual_pct_of_flow"], feas["outside_band_pct"]))
        return acc

    print(header)
    priors = {}
    for name, fn in baselines.METHODS.items():
        filled = fn(view, slot, weekend)
        priors[name] = filled
        record(name, filled)

    print("  --- invention: calibrated relation, hard tolerance band ---")
    for name, prior in priors.items():
        filled, timing = constrained.reconstruct(corridor, view, fitted, prior)
        record("constrained(%s)" % name, filled, timing)

    print("  --- ablations on the strongest prior ---")
    best_prior = min(priors, key=lambda n: out["methods"][n]["accuracy"]["all"]["MAE"])
    for kwargs, label in [
            ({"tol_scale": 0.0}, "exact equality, no band"),
            ({"mode": "zero"}, "textbook zero, no calibration"),
            ({"mode": "offset"}, "offset calibration only"),
            ({"weighting": "uniform"}, "uniform weighting"),
    ]:
        filled, timing = constrained.reconstruct(
            corridor, view, fitted, priors[best_prior], **kwargs)
        record("ablation(%s: %s)" % (best_prior, label), filled, timing)

    out["best_prior"] = best_prior
    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("  wrote results/%s" % out_name)
    return out


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window.json"
    run(manifest, max_run=96, regime="operational", out_name="phase4_operational.json")
    print()
    run(manifest, max_run=None, regime="all_gaps", out_name="phase4_all_gaps.json")
