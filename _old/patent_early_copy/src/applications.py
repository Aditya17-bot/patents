"""Phase 7 — downstream technical actions taken on the reconstructed dataset.

The claim does not become a claim to congestion prediction, capacity planning or weather
analysis. Those areas are heavily patented and, in the case of deciding where to build
road capacity, risk being read in India as an administrative method, which `OpenTV`
makes an absolute bar.

They appear here for one purpose: to evidence the technical effect. The 2025 CRI
Guidelines want the effect tied to a concrete downstream technical action, and the
sharpest possible demonstration is that a real engineering process **gives different
answers** depending on whether it is fed the reconciled dataset or the unreconciled one.
Each experiment below therefore runs the same downstream computation twice and reports
the difference, rather than presenting the computation as an invention in itself.

Three downstream processes:

1. Saturation ranking - which segments are most often at high flow. Feeds capacity
   assessment. Measured: how far the ranking moves.
2. Rain sensitivity - how far flow falls at a site when it is raining. Feeds weather
   -responsive control. Measured: how far the per-site estimate moves.
3. Short-horizon forecasting - predict the next interval from recent ones. This is the
   strongest of the three, because the dataset is training data for a downstream model
   and better training data is an unambiguous technical improvement.
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
import webtris
import weather

RESULTS = os.path.join(ROOT, "results")


# ------------------------------------------------------- 1. saturation ranking

def saturation_ranking(matrix, percentile=90):
    """Share of intervals each detector spends above its own high-flow threshold.

    A segment that sits near its busiest state for a large share of the week is a
    candidate bottleneck. The threshold is per-detector, so a quiet slip road is not
    compared against a six-lane mainline.
    """
    thresholds = np.percentile(matrix, percentile, axis=1, keepdims=True)
    return (matrix >= thresholds).mean(axis=1)


def ranking_shift(score_a, score_b):
    """How far the ranking moves between two versions of the dataset."""
    order_a = np.argsort(-score_a)
    order_b = np.argsort(-score_b)
    rank_a = np.empty_like(order_a)
    rank_b = np.empty_like(order_b)
    rank_a[order_a] = np.arange(len(order_a))
    rank_b[order_b] = np.arange(len(order_b))
    shift = np.abs(rank_a - rank_b)

    top_a = set(order_a[:20].tolist())
    top_b = set(order_b[:20].tolist())
    return {
        "sites": int(len(shift)),
        "mean_rank_shift": round(float(shift.mean()), 2),
        "max_rank_shift": int(shift.max()),
        "sites_moving_over_5_places": int((shift > 5).sum()),
        "top20_overlap": len(top_a & top_b),
        "top20_changed": 20 - len(top_a & top_b),
    }


# ----------------------------------------------------------- 2. rain sensitivity

def rain_sensitivity(matrix, rain, min_wet=40):
    """Percentage change in flow at each detector between wet and dry intervals.

    Only intervals of the same time-of-day distribution matter, so the comparison is made
    within each time-of-day slot and then averaged, which stops a rainy rush hour being
    compared against a dry small hour.
    """
    wet = rain > 0.2  # mm in the hour; below this is drizzle indistinguishable from noise
    out = np.full(matrix.shape[0], np.nan)
    for i in range(matrix.shape[0]):
        if wet[i].sum() < min_wet:
            continue
        ratios = []
        for slot in range(0, 96):
            cols = np.arange(matrix.shape[1])
            in_slot = (cols % 96) == slot
            w = matrix[i, in_slot & wet[i]]
            d = matrix[i, in_slot & ~wet[i]]
            if w.size >= 2 and d.size >= 2 and d.mean() > 1:
                ratios.append(w.mean() / d.mean())
        if ratios:
            out[i] = (float(np.mean(ratios)) - 1.0) * 100.0
    return out


# ------------------------------------------------------------- 3. forecasting

def forecast_error(matrix, observed, lags=4, train_frac=0.6):
    """Predict each detector's next interval from its recent history.

    A deliberately simple, explainable predictor: least-squares on the previous `lags`
    intervals plus the detector's own time-of-day mean. The point is not to build the
    best forecaster, it is to hold the forecaster fixed and vary only the dataset it is
    trained on, so any difference is attributable to the data.

    Scored only where the target interval was genuinely observed, so the comparison is
    against real measurements and never against one method's own guesses.
    """
    n_sites, n_cols = matrix.shape
    split = int(n_cols * train_frac)
    slot = np.arange(n_cols) % 96

    errors = []
    for i in range(n_sites):
        tod = np.zeros(96)
        for s in range(96):
            vals = matrix[i, :split][slot[:split] == s]
            tod[s] = vals.mean() if vals.size else 0.0

        rows, targets = [], []
        for t in range(lags, split):
            rows.append(np.concatenate([matrix[i, t - lags:t], [tod[slot[t]], 1.0]]))
            targets.append(matrix[i, t])
        if len(rows) < 50:
            continue
        coef, _, _, _ = np.linalg.lstsq(np.array(rows), np.array(targets), rcond=None)

        for t in range(max(split, lags), n_cols):
            if not observed[i, t]:
                continue  # score against real measurements only
            features = np.concatenate([matrix[i, t - lags:t], [tod[slot[t]], 1.0]])
            errors.append(abs(float(features @ coef) - matrix[i, t]))

    return {"n_predictions": len(errors),
            "MAE": round(float(np.mean(errors)), 3) if errors else None}


def node_flow_forecast_error(matrix, observed, fitted, lags=4, train_frac=0.6):
    """Forecast the total flow passing through each node, not one detector at a time.

    Stated before running it, so it is not a metric chosen after seeing results: the
    per-detector forecaster above has no channel through which cross-detector consistency
    could help it. It reads one detector's history and predicts that detector, so making
    the detectors agree with each other is irrelevant to it, and the experiment cannot
    show the effect either way.

    A quantity defined *across* the detectors at a node is the case where consistency can
    matter, and predicting total flow through a junction is a real operational task. This
    is the fair test of whether reconciliation improves a downstream model.
    """
    n_cols = matrix.shape[1]
    split = int(n_cols * train_frac)
    slot = np.arange(n_cols) % 96

    errors = []
    for f in fitted:
        rows_idx = [f["up"], f["down"]] + [r for r, _ in f["slips"]]
        series = matrix[rows_idx].sum(axis=0)
        # score only where every detector at the node genuinely reported
        truth_ok = np.all(observed[rows_idx], axis=0)

        tod = np.zeros(96)
        for s in range(96):
            vals = series[:split][slot[:split] == s]
            tod[s] = vals.mean() if vals.size else 0.0

        rows, targets = [], []
        for t in range(lags, split):
            rows.append(np.concatenate([series[t - lags:t], [tod[slot[t]], 1.0]]))
            targets.append(series[t])
        if len(rows) < 50:
            continue
        coef, _, _, _ = np.linalg.lstsq(np.array(rows), np.array(targets), rcond=None)

        for t in range(max(split, lags), n_cols):
            if not truth_ok[t]:
                continue
            features = np.concatenate([series[t - lags:t], [tod[slot[t]], 1.0]])
            errors.append(abs(float(features @ coef) - series[t]))

    return {"n_predictions": len(errors),
            "MAE": round(float(np.mean(errors)), 3) if errors else None}


# ------------------------------------------------------------------------ main

def run(manifest="window_full_M25_A.json", seed=0, max_run=96):
    corridor = dataset.load(manifest)
    fitted = evaluate.fit_node_signs(corridor)
    hidden = dataset.make_mask(corridor, fraction=0.10, seed=seed, max_run=max_run)
    view = dataset.train_view(corridor, hidden)
    slot, weekend = corridor.interval_index(), corridor.is_weekend()

    print("corridor %d sites x %d intervals, %d nodes"
          % (corridor.shape[0], corridor.shape[1], len(fitted)))

    print("building the unreconciled dataset (strongest baseline)...")
    unreconciled = baselines.knn_spatial(view, slot, weekend)
    print("building the reconciled dataset...")
    reconciled, timing = constrained.reconstruct(corridor, view, fitted, unreconciled)

    out = {"manifest": manifest, "seed": seed,
           "corridor": {"sites": int(corridor.shape[0]),
                        "intervals": int(corridor.shape[1]),
                        "nodes": len(fitted)},
           "timing": timing}

    # 1 - saturation ranking
    sat_u = saturation_ranking(unreconciled)
    sat_r = saturation_ranking(reconciled)
    out["saturation_ranking"] = ranking_shift(sat_u, sat_r)
    print("\n1. saturation ranking (capacity assessment input)")
    for k, v in out["saturation_ranking"].items():
        print("   %-28s %s" % (k, v))

    # 2 - rain sensitivity
    with open(os.path.join(RESULTS, manifest), encoding="utf-8") as fh:
        win = json.load(fh)
    meta = {s["id"]: s for s in webtris.sites()}
    start = "%s-%s-%s" % (win["start"][4:], win["start"][2:4], win["start"][:2])
    end = "%s-%s-%s" % (win["end"][4:], win["end"][2:4], win["end"][:2])
    print("\n2. rain sensitivity (weather-responsive control input)")
    rain = weather.precipitation_by_interval(corridor, meta, start, end)
    wet_share = float((rain > 0.2).mean())
    rs_u = rain_sensitivity(unreconciled, rain)
    rs_r = rain_sensitivity(reconciled, rain)
    both = ~np.isnan(rs_u) & ~np.isnan(rs_r)
    out["rain_sensitivity"] = {
        "wet_interval_share": round(wet_share, 4),
        "sites_measured": int(both.sum()),
        "mean_effect_unreconciled_pct": round(float(rs_u[both].mean()), 3) if both.any() else None,
        "mean_effect_reconciled_pct": round(float(rs_r[both].mean()), 3) if both.any() else None,
        "mean_abs_difference_pct_points": round(float(np.abs(rs_u[both] - rs_r[both]).mean()), 3) if both.any() else None,
        "max_abs_difference_pct_points": round(float(np.abs(rs_u[both] - rs_r[both]).max()), 3) if both.any() else None,
    }
    for k, v in out["rain_sensitivity"].items():
        print("   %-32s %s" % (k, v))

    # 3 - downstream forecasting
    print("\n3. short-horizon forecasting (downstream model trained on each dataset)")
    fe_u = forecast_error(unreconciled, corridor.observed)
    fe_r = forecast_error(reconciled, corridor.observed)
    out["forecasting"] = {
        "unreconciled": fe_u, "reconciled": fe_r,
        "MAE_reduction_pct": (round(100.0 * (fe_u["MAE"] - fe_r["MAE"]) / fe_u["MAE"], 2)
                              if fe_u["MAE"] and fe_r["MAE"] else None),
    }
    print("   unreconciled MAE %s over %s predictions"
          % (fe_u["MAE"], fe_u["n_predictions"]))
    print("   reconciled   MAE %s" % fe_r["MAE"])
    print("   reduction    %s%%" % out["forecasting"]["MAE_reduction_pct"])

    print("\n4. node-flow forecasting (the quantity defined across detectors)")
    nf_u = node_flow_forecast_error(unreconciled, corridor.observed, fitted)
    nf_r = node_flow_forecast_error(reconciled, corridor.observed, fitted)
    out["node_flow_forecasting"] = {
        "unreconciled": nf_u, "reconciled": nf_r,
        "MAE_reduction_pct": (round(100.0 * (nf_u["MAE"] - nf_r["MAE"]) / nf_u["MAE"], 2)
                              if nf_u["MAE"] and nf_r["MAE"] else None),
    }
    print("   unreconciled MAE %s over %s predictions"
          % (nf_u["MAE"], nf_u["n_predictions"]))
    print("   reconciled   MAE %s" % nf_r["MAE"])
    print("   reduction    %s%%" % out["node_flow_forecasting"]["MAE_reduction_pct"])

    with open(os.path.join(RESULTS, "applications.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/applications.json")
    return out


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "window_full_M25_A.json")
