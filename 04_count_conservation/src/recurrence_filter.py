"""A map-free remedy for spurious recovered relations: require recurrence in a past period.

harm_test.py showed that recovered relations lying outside the span of the survey cost a
little accuracy on the detectors they touch, so some of them are spurious. The survey
cannot be used to remove them in operation - the method has no map. But a physical
relation holds in every period, and a chance combination does not, so a relation can be
admitted only if the same relation (same detectors by site identifier, same signs) was
also recovered in an earlier period.

Tested causally on June 2025: relations are recovered from the June training view (10 %
withheld, as discovery_v2_eval), and the reconstruction of the withheld June values is
run with (1) all of them, (2) only those also recovered from the whole of May, and (3) for
reference only, those the survey does not contradict (the map-based oracle the method
cannot use). Writes results/recurrence_filter.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baselines, constrained, dataset, discover, discover2, evaluate
from discovery_v2_eval import categorise
from harm_test import score
from recurrence import recovered, site_key

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CORRIDORS = (("M25", "window_june_M25_A.json", "window_may_M25_A.json"),
             ("M1", "window_june_M1_A.json", "window_may_M1_A.json"))


def main(seed=0):
    out = {"corridors": {}}
    for name, june, may in CORRIDORS:
        c = dataset.load(june)
        truth = discover.truth_relations(c, evaluate.fit_node_signs(c))
        h = dataset.make_mask(c, 0.10, seed, max_run=96)
        v = dataset.train_view(c, h)
        rel, _ = discover2.discover(np.nan_to_num(v, nan=0.0), ~np.isnan(v))
        cm, rm = recovered(may)
        past = {site_key(r, cm.site_ids) for r in rm}
        rows = [{int(k): int(x) for k, x in r["rows"].items()} for r in rel]
        cats = [next(iter(categorise([r], truth, c.shape[0])[0])) for r in rows]
        recur = [site_key(r, c.site_ids) in past for r in rows]
        count = {}
        for k, ok in zip(cats, recur):
            d = count.setdefault(k, {"relations": 0, "kept_by_recurrence": 0})
            d["relations"] += 1
            d["kept_by_recurrence"] += int(ok)
        outside = {int(x) for r, k in zip(rel, cats) if k == "outside_map" for x in r["rows"]}
        prior = baselines.knn_spatial(v, c.interval_index(), c.is_weekend())
        res = {"relations": len(rel), "by_category": count,
               "prior_only": {"all": score(c.volumes, prior, h),
                              "touched": score(c.volumes, prior, h, outside)}}
        sets = {"all_recovered": rel,
                "recurring_in_may": [r for r, ok in zip(rel, recur) if ok],
                "oracle_without_outside_map": [r for r, k in zip(rel, cats)
                                               if k != "outside_map"]}
        for label, rs in sets.items():
            fitted = discover.relations_to_fitted(rs, c)
            filled, _ = constrained.reconstruct(c, v, fitted, prior)
            filled_view = filled
            res[label] = {"constraints": len(fitted),
                          "all": score(c.volumes, filled_view, h),
                          "touched": score(c.volumes, filled_view, h, outside)}
        out["corridors"][name] = res
        print(name, json.dumps(res), flush=True)
    with open(os.path.join(RESULTS, "recurrence_filter.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
