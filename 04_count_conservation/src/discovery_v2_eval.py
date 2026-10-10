"""Scores discover2 against the surveyed map and reruns reconstruction after the leak fix.

Every recovered relation is put in one of four categories rather than scored against the
survey list alone, because the survey is incomplete (it covers 295 of the 367 M25 sites):

  exact            the surveyed relation, verbatim
  implied          not listed, but a linear combination of surveyed relations
  unmapped_site    involves a site no surveyed relation covers - cannot be judged
  outside_map      judgeable, and not implied by the map - counted as an error

Reconstruction discovers on the training view only, so no withheld value reaches the
constraint set; the scoring band is calibrated on the full corridor as a reference.
"""
import json
import os
import sys
import time
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baselines, constrained, dataset, discover, discover2, evaluate

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def categorise(found, truth, n):
    tk = {discover2.key(x) for x in truth}
    covered = set().union(*[set(x) for x in truth])
    T = np.zeros((len(truth), n))
    for a, x in enumerate(truth):
        for r, v in x.items():
            T[a, r] = v
    cat = Counter()
    for r in found:
        if discover2.key(r) in tk:
            cat["exact"] += 1
            continue
        v = np.zeros(n)
        for k, c in r.items():
            v[k] = c
        co, _, _, _ = np.linalg.lstsq(T.T, v, rcond=None)
        if np.linalg.norm(T.T @ co - v) < 1e-6:
            cat["implied"] += 1
        elif not set(r) <= covered:
            cat["unmapped_site"] += 1
        else:
            cat["outside_map"] += 1
    judged = cat["exact"] + cat["implied"] + cat["outside_map"]
    return dict(cat), round((cat["exact"] + cat["implied"]) / judged, 3) if judged else None


def recall_by_size(found, truth):
    fk = {discover2.key(r) for r in found}
    out = {}
    for size, total in sorted(Counter(len(x) for x in truth).items()):
        hit = sum(1 for x in truth if len(x) == size and discover2.key(x) in fk)
        out[str(size)] = {"recovered": hit, "of": total}
    return out


def main(manifest="window_full_M25_A.json", seed=0):
    c = dataset.load(manifest)
    n = c.shape[0]
    true_nodes = evaluate.fit_node_signs(c)
    truth = discover.truth_relations(c, true_nodes)
    tag = manifest.replace("window_", "").replace(".json", "")
    print("%s: %d sites, %d surveyed relations" % (tag, n, len(truth)), flush=True)

    t0 = time.time()
    rel, meta = discover2.discover(c.volumes, c.observed, verbose=True)
    secs = round(time.time() - t0, 1)
    found = [r["rows"] for r in rel]
    with open(os.path.join(RESULTS, "recovered2_%s.json" % tag), "w", encoding="utf-8") as fh:
        json.dump([{str(k): v for k, v in r.items()} for r in found], fh)
    cats, judged_precision = categorise(found, truth, n)
    by_size = recall_by_size(found, truth)
    print("  categories %s, judged precision %s" % (cats, judged_precision), flush=True)
    print("  recall by size %s" % by_size, flush=True)

    out = {"manifest": manifest, "sites": n, "surveyed_relations": len(truth),
           "sites_in_survey": len(set().union(*[set(x) for x in truth])),
           "meta": meta, "seconds": secs, "found": len(found),
           "found_by_size": {str(k): v for k, v in sorted(Counter(len(r) for r in found).items())},
           "categories": cats, "judged_precision": judged_precision,
           "recall_by_size": by_size, "configs": {}}

    h = dataset.make_mask(c, 0.10, seed, max_run=96)
    v = dataset.train_view(c, h)
    rel_train, meta_train = discover2.discover(np.nan_to_num(v, nan=0.0), ~np.isnan(v))
    disc = discover.relations_to_fitted(rel_train, c)
    out["train_meta"] = meta_train

    prior = baselines.knn_spatial(v, c.interval_index(), c.is_weekend())
    runs = evaluate.gap_run_lengths(h)
    calib = constrained.calibrate(c, true_nodes, mode="scaled")
    a0 = evaluate.accuracy(c.volumes, prior, h, runs)
    f0 = evaluate.feasibility(prior, true_nodes, calib, h)
    out["configs"]["prior_only"] = {"MAE": a0["all"]["MAE"], "RMSE": a0["all"]["RMSE"],
                                    "outside": f0["outside_band_pct"]}
    print("  %-12s MAE %7.2f  outside %6.2f%%" % ("prior_only", a0["all"]["MAE"],
                                                 f0["outside_band_pct"]), flush=True)
    for label, nodes in (("surveyed", true_nodes), ("recovered", disc),
                         ("both", true_nodes + disc)):
        filled, t = constrained.reconstruct(c, v, nodes, prior)
        a = evaluate.accuracy(c.volumes, filled, h, runs)
        f = evaluate.feasibility(filled, true_nodes, calib, h)
        out["configs"][label] = {"MAE": a["all"]["MAE"], "RMSE": a["all"]["RMSE"],
                                 "outside": f["outside_band_pct"],
                                 "constraints": len(nodes), "seconds": t["seconds"]}
        print("  %-12s MAE %7.2f  outside %6.2f%%  constraints %d"
              % (label, a["all"]["MAE"], f["outside_band_pct"], len(nodes)), flush=True)

    with open(os.path.join(RESULTS, "discovery_v2_%s.json" % tag), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/discovery_v2_%s.json" % tag, flush=True)


if __name__ == "__main__":
    main(*(sys.argv[1:2] or ["window_full_M25_A.json"]))
