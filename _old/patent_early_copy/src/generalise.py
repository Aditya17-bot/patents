"""Does any of it hold anywhere else?

Every headline number so far comes from one carriageway of one motorway in one month.
That is exactly the objection an examiner raises against a measured technical effect, and
it is a fair one: a result that only exists on the M25 clockwise in March 2025 is a
property of that dataset, not of the method.

Three replications, all on data already fetched and cached:

  M25 clockwise, March 2025   the reference, restated for comparison
  M25 clockwise, June 2025    same road, same detectors, a different season
  M1 northbound, March 2025   a different motorway, different detectors, same month

The June run varies time while holding the network fixed. The M1 run varies the network
while holding time fixed. Between them they separate "this method works" from "this month
happened to suit it" and from "this stretch of road happened to suit it".

Nothing is tuned per corridor. The same calibration procedure, the same band quantile,
the same prior, the same masking, the same seeds.
"""

import json
import os
import statistics
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import baselines
import constrained
import dataset
import evaluate

RESULTS = os.path.join(ROOT, "results")

CORRIDORS = [
    ("M25 clockwise, March 2025", "window_full_M25_A.json"),
    ("M25 clockwise, June 2025", "window_june_M25_A.json"),
    ("M1 northbound, March 2025", "window_M1_A.json"),
]


def one(manifest, seeds=(0, 1, 2), fraction=0.10, max_run=96, prior="knn_spatial"):
    corridor = dataset.load(manifest)
    fitted = evaluate.fit_node_signs(corridor)
    slot, weekend = corridor.interval_index(), corridor.is_weekend()
    calib = constrained.calibrate(corridor, fitted, mode="scaled")
    prior_fn = baselines.METHODS[prior]

    mean_flow = float(np.mean([f["mean_flow"] for f in fitted])) if fitted else 0.0
    mean_band = float(np.mean([c["band"] for c in calib.values()])) if calib else 0.0

    rows = []
    for seed in seeds:
        t0 = time.time()
        hidden = dataset.make_mask(corridor, fraction=fraction, seed=seed, max_run=max_run)
        view = dataset.train_view(corridor, hidden)
        runs = evaluate.gap_run_lengths(hidden)

        p = prior_fn(view, slot, weekend)
        filled, timing = constrained.reconstruct(corridor, view, fitted, p)

        a0 = evaluate.accuracy(corridor.volumes, p, hidden, runs)["all"]["MAE"]
        a1 = evaluate.accuracy(corridor.volumes, filled, hidden, runs)["all"]["MAE"]
        f0 = evaluate.feasibility(p, fitted, calib, hidden)
        f1 = evaluate.feasibility(filled, fitted, calib, hidden)

        rows.append({"seed": seed,
                     "cells_hidden": int(hidden.sum()),
                     "prior_MAE": a0, "constrained_MAE": a1,
                     "gain_pct": round(100.0 * (a0 - a1) / a0, 2),
                     "outside_band_prior_pct": f0["outside_band_pct"],
                     "outside_band_constrained_pct": f1["outside_band_pct"],
                     "intervals_unreconciled": timing["intervals_unreconciled"],
                     "seconds": round(time.time() - t0, 1)})

    def spread(key):
        vals = [r[key] for r in rows]
        return {"mean": round(statistics.mean(vals), 3),
                "min": round(min(vals), 3), "max": round(max(vals), 3)}

    return {
        "manifest": manifest,
        "sites": int(corridor.shape[0]),
        "intervals": int(corridor.shape[1]),
        "nodes_fitted": len(fitted),
        "mean_node_flow": round(mean_flow, 1),
        "mean_band_vehicles": round(mean_band, 2),
        "band_pct_of_flow": round(100.0 * mean_band / mean_flow, 2) if mean_flow else None,
        "seeds": list(seeds),
        "prior_MAE": spread("prior_MAE"),
        "constrained_MAE": spread("constrained_MAE"),
        "gain_pct": spread("gain_pct"),
        "outside_band_prior_pct": spread("outside_band_prior_pct"),
        "outside_band_constrained_pct": spread("outside_band_constrained_pct"),
        "intervals_unreconciled": spread("intervals_unreconciled"),
        "runs": rows,
    }


def run(out_name="generalisation.json", seeds=(0, 1, 2)):
    out = {"seeds": list(seeds), "corridors": {}}
    print("%-28s %6s %6s %8s %8s %8s %9s %9s"
          % ("corridor", "sites", "nodes", "prior", "ours", "gain%",
             "outside0", "outside1"))
    for label, manifest in CORRIDORS:
        path = os.path.join(RESULTS, manifest)
        if not os.path.exists(path):
            print("%-28s  manifest not found, skipped" % label)
            continue
        r = one(manifest, seeds=seeds)
        out["corridors"][label] = r
        print("%-28s %6d %6d %8.2f %8.2f %7.2f%% %8.2f%% %8.2f%%"
              % (label, r["sites"], r["nodes_fitted"],
                 r["prior_MAE"]["mean"], r["constrained_MAE"]["mean"],
                 r["gain_pct"]["mean"],
                 r["outside_band_prior_pct"]["mean"],
                 r["outside_band_constrained_pct"]["mean"]))

    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/%s" % out_name)
    return out


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "generalisation.json")
