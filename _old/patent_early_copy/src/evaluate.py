"""Phase 3 — the evaluation harness every method is judged by.

Two families of measurement:

Accuracy — hide values the detectors actually reported, ask the method to reconstruct
them, compare against the truth. Reported overall and split by gap length, because the
methods differ sharply between a one-interval blink and a detector that is out for days.

Physical consistency — after reconstruction, does the completed dataset satisfy flow
conservation at the nodes? This is measured on the intervals where the method actually
had to invent a value at that node, since those are the only ones it could have broken.
No baseline has any mechanism to control this quantity.
"""

import itertools
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import baselines
import dataset

RESULTS = os.path.join(ROOT, "results")


# ------------------------------------------------------------------- accuracy

def gap_run_lengths(hidden):
    """Length of the hidden run each hidden cell belongs to."""
    lengths = np.zeros_like(hidden, dtype=int)
    for i in range(hidden.shape[0]):
        j = 0
        row = hidden[i]
        while j < row.size:
            if row[j]:
                k = j
                while k < row.size and row[k]:
                    k += 1
                lengths[i, j:k] = k - j
                j = k
            else:
                j += 1
    return lengths


def accuracy(truth, prediction, hidden, run_lengths):
    err = prediction[hidden] - truth[hidden]
    actual = truth[hidden]
    runs = run_lengths[hidden]

    def stats(mask):
        if mask.sum() == 0:
            return None
        e, a = err[mask], actual[mask]
        big = a > 20  # percentage error is meaningless on near-zero counts
        return {
            "n": int(mask.sum()),
            "MAE": round(float(np.abs(e).mean()), 2),
            "RMSE": round(float(np.sqrt((e ** 2).mean())), 2),
            "MAPE": (round(float((np.abs(e[big]) / a[big]).mean() * 100), 2)
                     if big.sum() else None),
            "bias": round(float(e.mean()), 2),
        }

    buckets = {
        "all": stats(np.ones_like(runs, dtype=bool)),
        "gap_1_4": stats(runs <= 4),
        "gap_5_16": stats((runs > 4) & (runs <= 16)),
        "gap_17_96": stats((runs > 16) & (runs <= 96)),
        "gap_over_96": stats(runs > 96),
    }
    return buckets


# --------------------------------------------------------- physical consistency

def fit_node_signs(corridor, min_intervals=200):
    """Learn each node's slip signs from intervals where every detector reported.

    Same procedure as Phase 2, expressed on the matrix. Nodes that cannot be fitted are
    dropped rather than guessed at.
    """
    fitted = []
    obs = corridor.observed
    vol = corridor.volumes
    for node in corridor.nodes:
        try:
            up = corridor.row_of[node["upstream"]["id"]]
            down = corridor.row_of[node["downstream"]["id"]]
            slips = [(corridor.row_of[s["id"]], s["ambiguous"]) for s in node["slips"]]
        except KeyError:
            continue
        if len(slips) > 4:
            continue

        rows = [up, down] + [r for r, _ in slips]
        complete = np.all(obs[rows], axis=0)
        if complete.sum() < min_intervals:
            continue

        options = [(-1, 0, 1) if amb else (-1, 1) for _, amb in slips]
        best = None
        for signs in (itertools.product(*options) if slips else [()]):
            resid = vol[up, complete] - vol[down, complete]
            for sign, (row, _) in zip(signs, slips):
                resid = resid + sign * vol[row, complete]
            score = float(np.median(np.abs(resid)))
            if best is None or score < best[0]:
                best = (score, signs)

        fitted.append({
            "node_id": node["node_id"],
            "up": up, "down": down,
            "slips": [(row, int(sign)) for (row, _), sign in zip(slips, best[1])],
            "baseline_residual": round(best[0], 2),
            "mean_flow": round(float(vol[down, complete].mean()), 1),
        })
    return fitted


def consistency(matrix, fitted, hidden):
    """Conservation residual of a completed dataset, where values were invented.

    Restricting to intervals in which at least one detector at that node was hidden is
    the fair comparison: those are the intervals the method is responsible for.
    """
    per_node = []
    for f in fitted:
        rows = [f["up"], f["down"]] + [r for r, _ in f["slips"]]
        touched = np.any(hidden[rows], axis=0)
        if touched.sum() == 0:
            continue
        resid = matrix[f["up"], touched] - matrix[f["down"], touched]
        for row, sign in f["slips"]:
            resid = resid + sign * matrix[row, touched]
        flow = matrix[f["down"], touched].mean()
        per_node.append({
            "node_id": f["node_id"],
            "intervals": int(touched.sum()),
            "median_abs_residual": float(np.median(np.abs(resid))),
            "pct_of_flow": float(np.median(np.abs(resid)) / flow * 100) if flow > 0 else None,
        })

    pcts = sorted(p["pct_of_flow"] for p in per_node if p["pct_of_flow"] is not None)
    return {
        "nodes": len(per_node),
        "median_residual_pct_of_flow": round(pcts[len(pcts) // 2], 3) if pcts else None,
        "p90_residual_pct_of_flow": round(pcts[int(len(pcts) * 0.9)], 3) if pcts else None,
        "worst_node_pct": round(pcts[-1], 3) if pcts else None,
        "per_node": per_node,
    }


def feasibility(matrix, fitted, calib, hidden):
    """How often, and by how much, a completed dataset falls outside the allowed band.

    This is the guarantee the invention offers and the baselines cannot: after
    reconstruction, no node may disagree with calibrated conservation by more than its
    band. Measured only on intervals where the method had to invent a value at that node.
    """
    violations, exceed, total = 0, [], 0
    for f in fitted:
        c = calib[f["node_id"]]
        rows = [f["up"], f["down"]] + [r for r, _ in f["slips"]]
        touched = np.any(hidden[rows], axis=0)
        if touched.sum() == 0:
            continue
        value = matrix[f["up"], touched] + c["down_coeff"] * matrix[f["down"], touched]
        for row, sign in f["slips"]:
            value = value + sign * matrix[row, touched]
        dev = np.abs(value - c["const"])
        outside = dev - c["band"]
        total += int(touched.sum())
        violations += int((outside > 1e-6).sum())
        if (outside > 1e-6).any():
            exceed.extend(outside[outside > 1e-6].tolist())
    return {
        "node_intervals_checked": total,
        "outside_band": violations,
        "outside_band_pct": round(100.0 * violations / total, 2) if total else None,
        "mean_exceedance_vehicles": round(float(np.mean(exceed)), 2) if exceed else 0.0,
        "max_exceedance_vehicles": round(float(np.max(exceed)), 2) if exceed else 0.0,
    }


# ----------------------------------------------------------------------- main

def run(manifest="window.json", fraction=0.10, seed=0, methods=None,
        max_run=None, regime="all_gaps", out_name="baselines.json", corridor=None,
        fitted=None):
    if corridor is None:
        corridor = dataset.load(manifest)
    print("corridor: %d live sites x %d intervals, %d nodes"
          % (corridor.shape[0], corridor.shape[1], len(corridor.nodes)))

    if fitted is None:
        fitted = fit_node_signs(corridor)
    print("nodes with fitted conservation relation: %d" % len(fitted))
    print("regime: %s (max gap %s)" % (regime, max_run or "uncapped"))

    hidden = dataset.make_mask(corridor, fraction=fraction, seed=seed, max_run=max_run)
    view = dataset.train_view(corridor, hidden)
    runs = gap_run_lengths(hidden)
    print("hidden %d of %d observed cells (%.1f%%)"
          % (hidden.sum(), corridor.observed.sum(),
             100.0 * hidden.sum() / corridor.observed.sum()))

    slot = corridor.interval_index()
    weekend = corridor.is_weekend()

    chosen = methods or list(baselines.METHODS)
    out = {"corridor": {"sites": int(corridor.shape[0]),
                        "intervals": int(corridor.shape[1]),
                        "nodes_fitted": len(fitted)},
           "mask": {"fraction": fraction, "seed": seed, "regime": regime,
                    "max_run": max_run, "cells_hidden": int(hidden.sum())},
           "methods": {}}

    for name in chosen:
        fn = baselines.METHODS[name]
        filled = fn(view, slot, weekend)
        acc = accuracy(corridor.volumes, filled, hidden, runs)
        cons = consistency(filled, fitted, hidden)
        out["methods"][name] = {"accuracy": acc, "consistency": cons}
        print("  %-22s MAE %7.2f  RMSE %7.2f   conservation residual %6.2f%% of flow"
              % (name, acc["all"]["MAE"], acc["all"]["RMSE"],
                 cons["median_residual_pct_of_flow"] or float("nan")))

    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/%s" % out_name)
    return out


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window.json"
    shared = dataset.load(manifest)
    signs = fit_node_signs(shared)
    # Operational dropouts: gaps up to one day. This is the regime the invention targets,
    # and the one where neighbouring detectors are still reporting.
    run(manifest, max_run=96, regime="operational", out_name="baselines_operational.json",
        corridor=shared, fitted=signs)
    print()
    # Everything, including detectors that died and stayed dead for weeks.
    run(manifest, regime="all_gaps", out_name="baselines_all_gaps.json",
        corridor=shared, fitted=signs)
