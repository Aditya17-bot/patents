"""Controlled ablation of the junction-stage ranking.

The earlier comparison (v1: 1 of 43 slip junctions, v2: 21 of 43) changed more than the
ranking, so it cannot credit the ranking. Here discover2 is run twice per corridor with
every stage and constant fixed, changing only what slip candidates are ranked against:

  target    |corr(x_j, x_i)|           - the obvious choice
  residual  |corr(x_j, x_i - x_k)|     - the method

Scored with the same categories and recall-by-size as discovery_v2_eval.py.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset, discover, discover2, evaluate
from discovery_v2_eval import categorise, recall_by_size

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CORRIDORS = (("M25", "window_full_M25_A.json"), ("M1", "window_M1_A.json"))


def main():
    out = {"note": "only discover2.RANKING differs between the two runs", "corridors": {}}
    for name, manifest in CORRIDORS:
        c = dataset.load(manifest)
        truth = discover.truth_relations(c, evaluate.fit_node_signs(c))
        slip_total = sum(1 for t in truth if len(t) >= 3)
        res = {"slip_total": slip_total, "pair_total": sum(1 for t in truth if len(t) == 2)}
        for mode in ("target", "residual"):
            discover2.RANKING = mode
            t0 = time.time()
            rel, meta = discover2.discover(c.volumes, c.observed)
            found = [r["rows"] for r in rel]
            cats, prec = categorise(found, truth, c.shape[0])
            by_size = recall_by_size(found, truth)
            res[mode] = {"found": len(found), "categories": cats, "judged_precision": prec,
                         "recall_by_size": by_size,
                         "slip_recovered": sum(v["recovered"] for k, v in by_size.items()
                                               if k != "2"),
                         "seconds": round(time.time() - t0, 1)}
            print("%s %-8s found %d  slip %d/%d  precision %s" %
                  (name, mode, len(found), res[mode]["slip_recovered"], slip_total, prec),
                  flush=True)
        out["corridors"][name] = res
    discover2.RANKING = "residual"
    with open(os.path.join(RESULTS, "ablation_ranking.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/ablation_ranking.json")


if __name__ == "__main__":
    main()
