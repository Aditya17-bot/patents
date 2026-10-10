"""Split-half stability as an admission test for the hard constraint set.

Under the recovered constraints mean error falls but RMSE rises on both corridors
(discovery_v2_*.json): a minority of values get much worse. The likely cause is spurious
relations imposed as hard constraints. A relation that describes the road holds in every
part of the record; one that fits by coincidence need not. So a relation is admitted only
if its residual is within the self-derived limit in the first half of the month AND in the
second half, each measured separately. The limit is the one discover2 already derived; no
new constant is introduced.

Reported for both corridors: judged precision of the stable subset on the full month, and
reconstruction MAE / RMSE / outside-band with all recovered relations versus the stable
subset, using the same mask, prior and scoring as discovery_v2_eval.py.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baselines, constrained, dataset, discover, discover2, evaluate
from discovery_v2_eval import categorise, recall_by_size

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CORRIDORS = (("M25", "window_full_M25_A.json"), ("M1", "window_M1_A.json"))


def stable(records, vol, obs, limit):
    """Keep relations whose residual is within `limit` in each half of the record."""
    n = obs.shape[1]
    first = np.zeros(n, dtype=bool)
    first[: n // 2] = True
    keep = []
    for rec in records:
        ok = True
        for half in (first, ~first):
            p = discover2._resid_pct(rec["rows"], vol, obs & half)
            if p is None or p > limit:
                ok = False
                break
        if ok:
            keep.append(rec)
    return keep


def main(seed=0):
    out = {"rule": "residual within the self-derived limit in both halves of the record",
           "corridors": {}}
    for name, manifest in CORRIDORS:
        c = dataset.load(manifest)
        true_nodes = evaluate.fit_node_signs(c)
        truth = discover.truth_relations(c, true_nodes)
        res = {}

        # precision on the full month
        rel, meta = discover2.discover(c.volumes, c.observed)
        st = stable(rel, c.volumes, c.observed, meta["limit_pct"])
        for label, rs in (("all", rel), ("stable", st)):
            found = [r["rows"] for r in rs]
            cats, prec = categorise(found, truth, c.shape[0])
            by = recall_by_size(found, truth)
            res["recovery_" + label] = {
                "found": len(found), "categories": cats, "judged_precision": prec,
                "recall_by_size": by,
                "slip_recovered": sum(v["recovered"] for k, v in by.items() if k != "2")}
        print("%s recovery: all %d (precision %s)  stable %d (precision %s)" %
              (name, len(rel), res["recovery_all"]["judged_precision"], len(st),
               res["recovery_stable"]["judged_precision"]), flush=True)

        # reconstruction on the training view
        h = dataset.make_mask(c, 0.10, seed, max_run=96)
        v = dataset.train_view(c, h)
        vv, vo = np.nan_to_num(v, nan=0.0), ~np.isnan(v)
        rel_t, meta_t = discover2.discover(vv, vo)
        st_t = stable(rel_t, vv, vo, meta_t["limit_pct"])
        prior = baselines.knn_spatial(v, c.interval_index(), c.is_weekend())
        runs = evaluate.gap_run_lengths(h)
        calib = constrained.calibrate(c, true_nodes, mode="scaled")
        a0 = evaluate.accuracy(c.volumes, prior, h, runs)
        f0 = evaluate.feasibility(prior, true_nodes, calib, h)
        res["prior_only"] = {"MAE": a0["all"]["MAE"], "RMSE": a0["all"]["RMSE"],
                             "outside": f0["outside_band_pct"]}
        for label, rs in (("recovered_all", rel_t), ("recovered_stable", st_t)):
            nodes = discover.relations_to_fitted(rs, c)
            filled, t = constrained.reconstruct(c, v, nodes, prior)
            a = evaluate.accuracy(c.volumes, filled, h, runs)
            f = evaluate.feasibility(filled, true_nodes, calib, h)
            res[label] = {"MAE": a["all"]["MAE"], "RMSE": a["all"]["RMSE"],
                          "outside": f["outside_band_pct"], "constraints": len(nodes)}
            print("  %-17s MAE %.2f RMSE %.2f outside %.2f%% constraints %d" %
                  (label, a["all"]["MAE"], a["all"]["RMSE"], f["outside_band_pct"],
                   len(nodes)), flush=True)
        out["corridors"][name] = res
    with open(os.path.join(RESULTS, "stability_split_half.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/stability_split_half.json")


if __name__ == "__main__":
    main()
