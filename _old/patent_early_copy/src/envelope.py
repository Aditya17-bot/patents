"""Computational cost, and the operating envelope.

Two things an examiner will push on, and one the 2025 CRI Guidelines explicitly reward.

COST. The Guidelines name latency, throughput and memory as system-level technical
improvements in their own right, independent of accuracy. Measured here like for like:
same machine, same data, same masking, wall time and peak memory for every method.

ENVELOPE. Two questions. How does the method behave as the data gets worse - if it only
works at 10% missing it is a laboratory result. And how sensitive is it to the tolerance
band - if performance swings wildly with the band, the band is a tuned constant dressed
up as a measurement, which is exactly the attack to expect.
"""

import json
import os
import sys
import time
import tracemalloc

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import baselines
import constrained
import dataset
import evaluate

RESULTS = os.path.join(ROOT, "results")


def measured(fn, *args, **kwargs):
    """Wall time and peak additional memory for one call."""
    tracemalloc.start()
    t0 = time.time()
    result = fn(*args, **kwargs)
    elapsed = time.time() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, round(elapsed, 3), round(peak / 1e6, 1)


def cost(manifest="window.json", seed=0):
    corridor = dataset.load(manifest)
    fitted = evaluate.fit_node_signs(corridor)
    hidden = dataset.make_mask(corridor, fraction=0.10, seed=seed, max_run=96)
    view = dataset.train_view(corridor, hidden)
    slot, weekend = corridor.interval_index(), corridor.is_weekend()

    out = {"corridor": {"sites": int(corridor.shape[0]),
                        "intervals": int(corridor.shape[1]),
                        "cells": int(corridor.shape[0] * corridor.shape[1]),
                        "nodes": len(fitted)},
           "methods": {}}

    print("%-24s %10s %12s" % ("method", "seconds", "peak MB"))
    priors = {}
    for name, fn in baselines.METHODS.items():
        filled, secs, mb = measured(fn, view, slot, weekend)
        priors[name] = filled
        out["methods"][name] = {"seconds": secs, "peak_MB": mb}
        print("%-24s %10.3f %12.1f" % (name, secs, mb))

    best = min(priors, key=lambda n: evaluate.accuracy(
        corridor.volumes, priors[n], hidden,
        evaluate.gap_run_lengths(hidden))["all"]["MAE"])

    (filled, _), secs, mb = measured(
        constrained.reconstruct, corridor, view, fitted, priors[best])
    out["methods"]["constraint step alone"] = {"seconds": secs, "peak_MB": mb,
                                               "applied_to": best}
    print("%-24s %10.3f %12.1f   (on top of %s)" % ("constraint step", secs, mb, best))

    with open(os.path.join(RESULTS, "cost.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


def envelope(manifest="window.json", fractions=(0.05, 0.10, 0.20, 0.40),
             band_scales=(0.0, 0.5, 1.0, 2.0), seed=0):
    corridor = dataset.load(manifest)
    fitted = evaluate.fit_node_signs(corridor)
    slot, weekend = corridor.interval_index(), corridor.is_weekend()
    calib_ref = constrained.calibrate(corridor, fitted, mode="scaled")

    out = {"missingness": {}, "band_sensitivity": {}}

    print("\n--- performance vs how much data is missing ---")
    print("%8s %10s %10s %10s %10s" % ("hidden", "prior MAE", "ours MAE", "gain %", "outside %"))
    for frac in fractions:
        hidden = dataset.make_mask(corridor, fraction=frac, seed=seed, max_run=96)
        view = dataset.train_view(corridor, hidden)
        runs = evaluate.gap_run_lengths(hidden)
        prior = baselines.knn_spatial(view, slot, weekend)
        filled, _ = constrained.reconstruct(corridor, view, fitted, prior)

        a0 = evaluate.accuracy(corridor.volumes, prior, hidden, runs)["all"]["MAE"]
        a1 = evaluate.accuracy(corridor.volumes, filled, hidden, runs)["all"]["MAE"]
        fe = evaluate.feasibility(filled, fitted, calib_ref, hidden)
        gain = 100.0 * (a0 - a1) / a0
        out["missingness"]["%.2f" % frac] = {
            "prior_MAE": a0, "ours_MAE": a1, "gain_pct": round(gain, 2),
            "outside_band_pct": fe["outside_band_pct"],
            "cells_hidden": int(hidden.sum())}
        print("%8.0f%% %10.2f %10.2f %10.2f %10.2f"
              % (frac * 100, a0, a1, gain, fe["outside_band_pct"]))

    print("\n--- sensitivity to the tolerance band ---")
    print("%12s %10s %10s %12s" % ("band scale", "MAE", "outside %", "band veh"))
    hidden = dataset.make_mask(corridor, fraction=0.10, seed=seed, max_run=96)
    view = dataset.train_view(corridor, hidden)
    runs = evaluate.gap_run_lengths(hidden)
    prior = baselines.knn_spatial(view, slot, weekend)
    for scale in band_scales:
        filled, timing = constrained.reconstruct(corridor, view, fitted, prior,
                                                 tol_scale=scale)
        a = evaluate.accuracy(corridor.volumes, filled, hidden, runs)["all"]["MAE"]
        fe = evaluate.feasibility(filled, fitted, calib_ref, hidden)
        out["band_sensitivity"]["%.1f" % scale] = {
            "MAE": a, "outside_band_pct": fe["outside_band_pct"],
            "mean_band_vehicles": timing["mean_band_vehicles"]}
        print("%12.1f %10.2f %10.2f %12.1f"
              % (scale, a, fe["outside_band_pct"], timing["mean_band_vehicles"]))

    with open(os.path.join(RESULTS, "envelope.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/envelope.json")
    return out


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window.json"
    cost(manifest)
    envelope(manifest)
