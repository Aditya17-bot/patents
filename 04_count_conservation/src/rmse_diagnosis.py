"""Where does the RMSE regression under the recovered constraints come from?

Reproduces the discovery_v2_eval reconstruction (same mask, same training-view discovery,
same prior) and, for every withheld cell, records the change in squared error the
constraint caused. Breaks the added squared error down by:

  - whether the cell's interval was reconciled or flagged irreconcilable,
  - how many unknowns the violated constraints had to be shared across,
  - the size of the correction applied to the cell.

Writes results/rmse_diagnosis_<tag>.json; with a second argument "vertex", reruns under
the first version's restart rule and writes rmse_diagnosis_<tag>_vertexfallback.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baselines, constrained, dataset, discover, discover2, evaluate

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def setup(manifest, seed=0):
    c = dataset.load(manifest)
    h = dataset.make_mask(c, 0.10, seed, max_run=96)
    v = dataset.train_view(c, h)
    rel, _ = discover2.discover(np.nan_to_num(v, nan=0.0), ~np.isnan(v))
    disc = discover.relations_to_fitted(rel, c)
    prior = baselines.knn_spatial(v, c.interval_index(), c.is_weekend())
    return c, h, v, disc, prior


def interval_status(c, v, fitted, prior):
    """Per interval: reconciled (0) or irreconcilable (1), using the solver's own test."""
    train = constrained.training_corridor(c, v)
    calib = constrained.calibrate(train, fitted)
    scale = constrained.detector_scale(train)
    _, n_con, n_cor, n_unrec, _ = constrained.project(prior, v, fitted, calib, scale)
    return n_con, n_cor, n_unrec


def breakdown(c, h, v, filled, prior, n_unrec):
    truth = c.volumes
    cells = np.argwhere(h)
    e0 = prior[h] - truth[h]
    e1 = filled[h] - truth[h]
    d = e1 ** 2 - e0 ** 2
    t = cells[:, 1]
    unrec = n_unrec[t] > 0
    corr = np.abs(filled[h] - prior[h])
    out = {"cells": int(h.sum()),
           "rmse_prior": round(float(np.sqrt((e0 ** 2).mean())), 2),
           "rmse_constrained": round(float(np.sqrt((e1 ** 2).mean())), 2),
           "mae_prior": round(float(np.abs(e0).mean()), 2),
           "mae_constrained": round(float(np.abs(e1).mean()), 2),
           "added_sq_error_total": round(float(d.sum()), 0)}
    for name, m in (("irreconcilable_intervals", unrec), ("reconciled_intervals", ~unrec)):
        out[name] = {"cells": int(m.sum()),
                     "added_sq_error": round(float(d[m].sum()), 0),
                     "mae_prior": round(float(np.abs(e0[m]).mean()), 2) if m.any() else None,
                     "mae_constrained": round(float(np.abs(e1[m]).mean()), 2) if m.any() else None}
    # correction-size buckets
    edges = [0, 1, 20, 50, 100, 200, 1e9]
    buckets = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (corr >= lo) & (corr < hi)
        buckets.append({"correction_from": lo, "correction_to": hi if hi < 1e9 else None,
                        "cells": int(m.sum()), "added_sq_error": round(float(d[m].sum()), 0),
                        "mae_prior": round(float(np.abs(e0[m]).mean()), 2) if m.any() else None,
                        "mae_constrained": round(float(np.abs(e1[m]).mean()), 2) if m.any() else None})
    out["by_correction_size"] = buckets
    # worst cells
    order = np.argsort(-d)[:15]
    out["worst_cells"] = [{"row": int(cells[k, 0]), "t": int(cells[k, 1]),
                           "truth": float(truth[cells[k, 0], cells[k, 1]]),
                           "prior": round(float(e0[k] + truth[cells[k, 0], cells[k, 1]]), 1),
                           "filled": round(float(e1[k] + truth[cells[k, 0], cells[k, 1]]), 1),
                           "irreconcilable": bool(unrec[k])} for k in order]
    return out


def main(manifest, fallback="nearest"):
    constrained.FALLBACK = fallback
    tag = manifest.replace("window_", "").replace(".json", "")
    if fallback != "nearest":
        tag += "_" + fallback + "fallback"
    c, h, v, disc, prior = setup(manifest)
    filled, info = constrained.reconstruct(c, v, disc, prior)
    _, _, n_unrec = interval_status(c, v, disc, prior)
    res = {"manifest": manifest, "fallback": fallback, "constraints": len(disc),
           "solver": info,
           "breakdown": breakdown(c, h, v, filled, prior, n_unrec)}
    print(json.dumps(res["breakdown"], indent=1)[:3000], flush=True)
    with open(os.path.join(RESULTS, "rmse_diagnosis_%s.json" % tag), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main(*(sys.argv[1:3] or ["window_M1_A.json"]))
