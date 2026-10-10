"""Discovery with a retention test derived from the counts alone, scored after the leak fix.

discovery_full.py kept any relation whose median residual was within 4% of flow, and then
scored precision against a 1.06% floor. That floor is the median residual of the surveyed
slip nodes in Phase 2 - it came from the network map, so a method claimed to need no map
cannot use it.

Here the floor is measured from the discovered relations themselves. A relation between
exactly two detectors (x_i = x_j) is plain continuity with no slip road between them, so
the median residual across those relations is the detectors' own disagreement - measured
without the map. A candidate is retained only if its residual is within FLOOR_MULTIPLE of
that floor. FLOOR_MULTIPLE is fixed here, before scoring, and not tuned against the survey.

The reconstruction configs are rerun because discovery_full.json (2026-08-03) predates the
constrained.py leak fix (2026-08-04).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baselines, constrained, dataset, discover, evaluate

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

FLOOR_MULTIPLE = 2.0


def self_floor(found):
    """Median residual, % of flow, over discovered two-detector relations."""
    pair = [f["residual_pct_of_flow"] for f in found if len(f["rows"]) == 2]
    if not pair:
        return None, 0
    return float(np.median(pair)), len(pair)


def retain(found, floor):
    return [f for f in found if f["residual_pct_of_flow"] <= FLOOR_MULTIPLE * floor]


def sweep(found, truth, n_sites, floor):
    """Precision and recall across multiples of the self-derived floor, for disclosure."""
    rows = []
    for m in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
        kept = [f for f in found if f["residual_pct_of_flow"] <= m * floor]
        s = discover.score(kept, truth)
        rows.append({"multiple": m, "kept": len(kept),
                     "exact": s["exact_matches"], "recall": s["recall_exact"],
                     "precision": s["precision_exact"],
                     "span": discover.span_coverage(kept, truth, n_sites)["coverage"]})
    return rows


def main(manifest="window_full_M25_A.json", seed=0):
    c = dataset.load(manifest)
    true_nodes = evaluate.fit_node_signs(c)
    truth = discover.truth_relations(c, true_nodes)
    n = c.shape[0]
    print("corridor %d sites, %d surveyed nodes" % (n, len(true_nodes)), flush=True)

    loose = discover.discover(c.volumes, c.observed)
    floor, n_pairs = self_floor(loose)
    strict = retain(loose, floor)
    print("self floor %.3f%% from %d pair relations; kept %d of %d"
          % (floor, n_pairs, len(strict), len(loose)), flush=True)

    out = {"manifest": manifest, "floor_multiple": FLOOR_MULTIPLE,
           "self_floor_pct": round(floor, 3), "pair_relations": n_pairs,
           "loose": {"score": discover.score(loose, truth),
                     "span": discover.span_coverage(loose, truth, n)},
           "strict": {"score": discover.score(strict, truth),
                      "span": discover.span_coverage(strict, truth, n)},
           "sweep": sweep(loose, truth, n, floor),
           "configs": {}}
    s = out["strict"]["score"]
    print("strict: exact %d/%d recall %.3f precision %.3f span %.3f"
          % (s["exact_matches"], s["true_relations"], s["recall_exact"],
             s["precision_exact"], out["strict"]["span"]["coverage"]), flush=True)

    # reconstruction: discovery rerun on the training view only, floor re-derived there
    h = dataset.make_mask(c, 0.10, seed, max_run=96)
    v = dataset.train_view(c, h)
    loose_train = discover.discover(np.nan_to_num(v, nan=0.0), ~np.isnan(v))
    floor_train, _ = self_floor(loose_train)
    strict_train = retain(loose_train, floor_train)
    disc_loose = discover.relations_to_fitted(loose_train, c)
    disc_strict = discover.relations_to_fitted(strict_train, c)
    out["train_floor_pct"] = round(floor_train, 3)

    prior = baselines.knn_spatial(v, c.interval_index(), c.is_weekend())
    runs = evaluate.gap_run_lengths(h)
    # scoring band from the full corridor, as in phase4/phase5: a reference, not an input
    calib = constrained.calibrate(c, true_nodes, mode="scaled")

    a0 = evaluate.accuracy(c.volumes, prior, h, runs)
    f0 = evaluate.feasibility(prior, true_nodes, calib, h)
    out["configs"]["none"] = {"MAE": a0["all"]["MAE"], "RMSE": a0["all"]["RMSE"],
                              "outside": f0["outside_band_pct"]}
    for label, nodes in (("surveyed", true_nodes),
                         ("discovered_loose", disc_loose),
                         ("discovered_strict", disc_strict),
                         ("both_strict", true_nodes + disc_strict)):
        filled, t = constrained.reconstruct(c, v, nodes, prior)
        a = evaluate.accuracy(c.volumes, filled, h, runs)
        f = evaluate.feasibility(filled, true_nodes, calib, h)
        out["configs"][label] = {"MAE": a["all"]["MAE"], "RMSE": a["all"]["RMSE"],
                                 "outside": f["outside_band_pct"],
                                 "constraints": len(nodes), "seconds": t["seconds"]}
        print("  %-18s MAE %7.2f  outside %6.2f%%  constraints %d  %.1fs"
              % (label, a["all"]["MAE"], f["outside_band_pct"], len(nodes),
                 t["seconds"]), flush=True)

    with open(os.path.join(RESULTS, "discovery_strict.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/discovery_strict.json", flush=True)


if __name__ == "__main__":
    main()
