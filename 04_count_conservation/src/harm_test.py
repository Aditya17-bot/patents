"""Do the recovered relations the survey cannot confirm damage the reconstruction?

Same setup as discovery_v2_eval (10 % withheld, discovery on the training view, same
prior). The training-view relations are categorised against the survey, and the
reconstruction is run twice: with every recovered relation, and with the relations lying
outside the span of the survey removed. Scored on all withheld values and, separately,
on the withheld values of detectors that belong to at least one such relation - the only
values those relations can touch. If the unconfirmed relations were wrong and imposed as
hard constraints, removing them would lower the error on those detectors.
Writes results/harm_test.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baselines, constrained, dataset, discover, discover2, evaluate
from discovery_v2_eval import categorise

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CORRIDORS = (("M25", "window_full_M25_A.json"), ("M1", "window_M1_A.json"))


def score(truth, filled, h, rows=None):
    m = h.copy()
    if rows is not None:
        keep = np.zeros(h.shape[0], dtype=bool)
        keep[list(rows)] = True
        m &= keep[:, None]
    e = filled[m] - truth[m]
    return {"cells": int(m.sum()), "MAE": round(float(np.abs(e).mean()), 3),
            "RMSE": round(float(np.sqrt((e ** 2).mean())), 3)}


def main(seed=0):
    out = {"corridors": {}}
    for name, manifest in CORRIDORS:
        c = dataset.load(manifest)
        truth_rel = discover.truth_relations(c, evaluate.fit_node_signs(c))
        h = dataset.make_mask(c, 0.10, seed, max_run=96)
        v = dataset.train_view(c, h)
        rel, _ = discover2.discover(np.nan_to_num(v, nan=0.0), ~np.isnan(v))
        cats = [next(iter(categorise([{int(k): int(x) for k, x in r["rows"].items()}],
                                     truth_rel, c.shape[0])[0]))
                for r in rel]
        outside = [r for r, k in zip(rel, cats) if k == "outside_map"]
        kept = [r for r, k in zip(rel, cats) if k != "outside_map"]
        touched = {int(x) for r in outside for x in r["rows"]}
        prior = baselines.knn_spatial(v, c.interval_index(), c.is_weekend())
        res = {"relations": len(rel), "outside_map": len(outside),
               "detectors_touched": len(touched),
               "prior_only": {"all": score(c.volumes, prior, h),
                              "touched": score(c.volumes, prior, h, touched)}}
        for label, rels in (("all_recovered", rel), ("without_outside_map", kept)):
            fitted = discover.relations_to_fitted(rels, c)
            filled, _ = constrained.reconstruct(c, v, fitted, prior)
            res[label] = {"constraints": len(fitted), "all": score(c.volumes, filled, h),
                          "touched": score(c.volumes, filled, h, touched)}
        out["corridors"][name] = res
        print(name, json.dumps(res), flush=True)
    with open(os.path.join(RESULTS, "harm_test.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
