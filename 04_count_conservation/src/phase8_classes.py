"""Phase 8 - does resolving the balance by vehicle class actually help?

Four numbers, because three of the four possible explanations for any gain have to be
ruled out before the fourth can be claimed:

  A  prior on the total                      the ordinary baseline
  B  sum of per-class priors                 class decomposition alone, no constraint
  C  constrained total                       the method as measured so far
  D  sum of per-class constrained            the method with class-resolved constraints

B is the ablation that matters. Splitting the data into four thinner, cleaner series and
imputing each separately may improve the estimate all by itself, with no extra physics
involved at all. If D beats C but not B, the gain came from the decomposition and the
class constraints earned nothing. Only D over both B and C is evidence for the claim.

The sweep over how much data is hidden is the point of the experiment rather than a
robustness check. The total-only method's advantage was measured to decay as the node
systems become underdetermined. If the class equations supply real extra information the
decay should be slower, and if they do not, it should not be.
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

RESULTS = os.path.join(ROOT, "results")


def sign_agreement(cc, fitted):
    """Fit the slip signs independently on each class and see whether they agree.

    The signs encode the physical topology - which slip roads add vehicles and which
    remove them. They were learned from the total flow. If the same signs fall out of
    each length class independently, the topology recovered is a property of the road
    and not an artefact of one particular aggregate.
    """
    per_class = {}
    for name in classes.CLASS_NAMES:
        per_class[name] = {f["node_id"]: tuple(s for _, s in f["slips"])
                           for f in evaluate.fit_node_signs(cc.view(name))}
    reference = {f["node_id"]: tuple(s for _, s in f["slips"]) for f in fitted}

    agree, compared, slipped_agree, slipped_compared = 0, 0, 0, 0
    for nid, ref in reference.items():
        for name in classes.CLASS_NAMES:
            got = per_class[name].get(nid)
            if got is None:
                continue
            compared += 1
            agree += int(got == ref)
            if ref:                       # nodes with no slip road have nothing to agree on
                slipped_compared += 1
                slipped_agree += int(got == ref)
    return {
        "node_class_pairs_compared": compared,
        "sign_agreement_pct": round(100.0 * agree / compared, 2) if compared else None,
        "slip_node_pairs_compared": slipped_compared,
        "slip_node_agreement_pct": (round(100.0 * slipped_agree / slipped_compared, 2)
                                    if slipped_compared else None),
    }


def run(manifest="window.json", fractions=(0.05, 0.10, 0.20, 0.40), seed=0,
        prior="knn_spatial", max_run=96, out_name="classwise.json"):
    t_start = time.time()
    cc = classes.load(manifest)
    total = cc.total
    fitted = evaluate.fit_node_signs(total)
    slot, weekend = total.interval_index(), total.is_weekend()
    prior_fn = baselines.METHODS[prior]

    print("corridor %d sites x %d intervals, %d nodes fitted"
          % (total.shape[0], total.shape[1], len(fitted)))

    sums = classes.check_sums(cc)
    print("class sums equal total in %.2f%% of records (max discrepancy %.0f vehicle)"
          % (sums["exact_pct"], sums["max_abs_discrepancy"]))

    spread = classes.composition_spread(cc, fitted)
    spreads = sorted(s["heavy_share_spread"] for s in spread)
    print("heavy-share spread within a node: median %.3f  p90 %.3f  max %.3f"
          % (spreads[len(spreads) // 2], spreads[int(len(spreads) * 0.9)], spreads[-1]))

    agreement = sign_agreement(cc, fitted)
    print("slip signs recovered per class agree with the total-flow fit in %s%% of cases"
          % agreement["slip_node_agreement_pct"])

    # calibration of the total relation, used to score every variant on the same footing
    calib_total = constrained.calibrate(total, fitted, mode="scaled")
    calib_class = {name: constrained.calibrate(cc.view(name), fitted, mode="scaled")
                   for name in classes.CLASS_NAMES}

    band_report = {}
    for name in classes.CLASS_NAMES:
        bands = [c["band"] for c in calib_class[name].values()]
        band_report[name] = round(float(np.mean(bands)), 2)
    band_report["total"] = round(
        float(np.mean([c["band"] for c in calib_total.values()])), 2)
    print("mean tolerance band, vehicles per interval:",
          "  ".join("%s %.1f" % (k, v) for k, v in band_report.items()))

    out = {"corridor": {"sites": int(total.shape[0]), "intervals": int(total.shape[1]),
                        "nodes_fitted": len(fitted)},
           "prior": prior, "seed": seed, "max_run": max_run,
           "class_sum_check": sums,
           "composition_spread": {
               "median": spreads[len(spreads) // 2],
               "p90": spreads[int(len(spreads) * 0.9)],
               "max": spreads[-1],
               "nodes": len(spread)},
           "sign_agreement": agreement,
           "mean_band_vehicles": band_report,
           "missingness": {}}

    print("\n%8s %10s %10s %10s %10s %9s %9s"
          % ("hidden", "A prior", "B class", "C constr", "D class+c",
             "D vs C", "D vs B"))

    for frac in fractions:
        hidden = dataset.make_mask(total, fraction=frac, seed=seed, max_run=max_run)
        view_total = dataset.train_view(total, hidden)
        runs = evaluate.gap_run_lengths(hidden)
        truth = total.volumes

        prior_total = prior_fn(view_total, slot, weekend)
        a = evaluate.accuracy(truth, prior_total, hidden, runs)["all"]["MAE"]

        filled_total, timing_total = constrained.reconstruct(
            total, view_total, fitted, prior_total)
        c = evaluate.accuracy(truth, filled_total, hidden, runs)["all"]["MAE"]

        prior_sum = np.zeros_like(prior_total)
        filled_sum = np.zeros_like(prior_total)
        per_class = {}
        unreconciled = 0
        for name in classes.CLASS_NAMES:
            cview = cc.view(name)
            view_c = dataset.train_view(cview, hidden)
            prior_c = prior_fn(view_c, slot, weekend)
            filled_c, timing_c = constrained.reconstruct(cview, view_c, fitted, prior_c)
            prior_sum += prior_c
            filled_sum += filled_c
            unreconciled += timing_c["intervals_unreconciled"]
            per_class[name] = {
                "prior_MAE": evaluate.accuracy(cview.volumes, prior_c, hidden,
                                               runs)["all"]["MAE"],
                "constrained_MAE": evaluate.accuracy(cview.volumes, filled_c, hidden,
                                                     runs)["all"]["MAE"],
                "intervals_unreconciled": timing_c["intervals_unreconciled"],
            }

        b = evaluate.accuracy(truth, prior_sum, hidden, runs)["all"]["MAE"]
        d = evaluate.accuracy(truth, filled_sum, hidden, runs)["all"]["MAE"]

        fe_a = evaluate.feasibility(prior_total, fitted, calib_total, hidden)
        fe_c = evaluate.feasibility(filled_total, fitted, calib_total, hidden)
        fe_d = evaluate.feasibility(filled_sum, fitted, calib_total, hidden)

        out["missingness"]["%.2f" % frac] = {
            "cells_hidden": int(hidden.sum()),
            "A_prior_total_MAE": a,
            "B_class_prior_sum_MAE": b,
            "C_constrained_total_MAE": c,
            "D_class_constrained_sum_MAE": d,
            "gain_C_over_A_pct": round(100.0 * (a - c) / a, 2),
            "gain_D_over_A_pct": round(100.0 * (a - d) / a, 2),
            "gain_D_over_B_pct": round(100.0 * (b - d) / b, 2),
            "gain_D_over_C_pct": round(100.0 * (c - d) / c, 2),
            "outside_band_pct": {"A": fe_a["outside_band_pct"],
                                 "C": fe_c["outside_band_pct"],
                                 "D": fe_d["outside_band_pct"]},
            "intervals_unreconciled_total": timing_total["intervals_unreconciled"],
            "intervals_unreconciled_classwise": unreconciled,
            "per_class": per_class,
        }

        print("%7.0f%% %10.2f %10.2f %10.2f %10.2f %8.2f%% %8.2f%%"
              % (frac * 100, a, b, c, d,
                 100.0 * (c - d) / c, 100.0 * (b - d) / b))

    out["seconds"] = round(time.time() - t_start, 1)
    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/%s in %.0fs" % (out_name, out["seconds"]))
    return out


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window.json"
    name = sys.argv[2] if len(sys.argv) > 2 else "classwise.json"
    run(manifest, out_name=name)
