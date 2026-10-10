"""Phase 8b - do the class balances add anything once the total balance is kept?

Phase 8 answered a narrower question and answered it no: class balances *instead of* the
total balance are worse. This asks whether they are worth anything *on top of* it.

The comparison is built so that only one thing differs between the two arms. Both start
from the same total prior, split into classes by the same measured composition, so both
begin at the same point in the total coordinate. Both enforce the same total band. The
only difference is whether the four class bands are also imposed.

  A        the prior, unconstrained
  C        total constraint, solved on the total directly - the method as measured so far
  E_total  total constraint, solved on the class-split vector          sanity check on C
  E_both   total constraint plus the four class constraints            the question

E_total exists to prove the harness is not the thing making the difference. It solves a
mathematically equivalent problem to C in a larger space; if it does not land close to C,
nothing else in this table can be trusted.
"""

import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import baselines
import classes
import constrained
import dataset
import evaluate
import joint

RESULTS = os.path.join(ROOT, "results")


def run(manifest="window.json", fractions=(0.05, 0.10, 0.20, 0.40), seed=0,
        prior="knn_spatial", max_run=96, out_name="classwise_joint.json"):
    t_start = time.time()
    cc = classes.load(manifest)
    total = cc.total
    fitted = evaluate.fit_node_signs(total)
    slot, weekend = total.interval_index(), total.is_weekend()
    prior_fn = baselines.METHODS[prior]
    calib_total = constrained.calibrate(total, fitted, mode="scaled")

    print("corridor %d sites x %d intervals, %d nodes fitted"
          % (total.shape[0], total.shape[1], len(fitted)))

    out = {"corridor": {"sites": int(total.shape[0]), "intervals": int(total.shape[1]),
                        "nodes_fitted": len(fitted)},
           "prior": prior, "seed": seed, "max_run": max_run, "missingness": {}}

    print("\n%8s %9s %9s %9s %9s  %9s %9s"
          % ("hidden", "A", "C", "E_total", "E_both", "E vs C", "outside%"))

    for frac in fractions:
        hidden = dataset.make_mask(total, fraction=frac, seed=seed, max_run=max_run)
        view_total = dataset.train_view(total, hidden)
        runs = evaluate.gap_run_lengths(hidden)
        truth = total.volumes

        prior_total = prior_fn(view_total, slot, weekend)
        a = evaluate.accuracy(truth, prior_total, hidden, runs)["all"]["MAE"]

        filled_c, timing_c = constrained.reconstruct(total, view_total, fitted, prior_total)
        c = evaluate.accuracy(truth, filled_c, hidden, runs)["all"]["MAE"]

        _, sum_t, diag_t = joint.reconstruct(cc, hidden, prior_total, fitted, slot,
                                             weekend, use_total=True, use_class=False)
        e_total = evaluate.accuracy(truth, sum_t, hidden, runs)["all"]["MAE"]

        stack_b, sum_b, diag_b = joint.reconstruct(cc, hidden, prior_total, fitted, slot,
                                                   weekend, use_total=True, use_class=True)
        e_both = evaluate.accuracy(truth, sum_b, hidden, runs)["all"]["MAE"]

        per_class = {}
        for ci, name in enumerate(classes.CLASS_NAMES):
            per_class[name] = evaluate.accuracy(cc.by_class[name], stack_b[ci],
                                                hidden, runs)["all"]["MAE"]

        fe_c = evaluate.feasibility(filled_c, fitted, calib_total, hidden)
        fe_b = evaluate.feasibility(sum_b, fitted, calib_total, hidden)

        out["missingness"]["%.2f" % frac] = {
            "cells_hidden": int(hidden.sum()),
            "A_prior_MAE": a,
            "C_total_MAE": c,
            "E_total_only_MAE": e_total,
            "E_total_and_class_MAE": e_both,
            "gain_E_over_C_pct": round(100.0 * (c - e_both) / c, 2),
            "gain_E_over_A_pct": round(100.0 * (a - e_both) / a, 2),
            "outside_band_pct_C": fe_c["outside_band_pct"],
            "outside_band_pct_E": fe_b["outside_band_pct"],
            "class_MAE_under_E": per_class,
            "intervals_unreconciled_C": timing_c["intervals_unreconciled"],
            "intervals_unreconciled_E": diag_b["intervals_unreconciled"],
            "constraints_per_interval_C": timing_c["mean_constraints_per_interval"],
            "constraints_per_interval_E": diag_b["mean_constraints_per_interval"],
            "seconds_C": timing_c["seconds"],
            "seconds_E": diag_b["seconds"],
        }
        print("%7.0f%% %9.2f %9.2f %9.2f %9.2f  %8.2f%% %9.2f"
              % (frac * 100, a, c, e_total, e_both,
                 100.0 * (c - e_both) / c, fe_b["outside_band_pct"]))

    out["seconds"] = round(time.time() - t_start, 1)
    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/%s in %.0fs" % (out_name, out["seconds"]))
    return out


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window.json"
    name = sys.argv[2] if len(sys.argv) > 2 else "classwise_joint.json"
    run(manifest, out_name=name)
