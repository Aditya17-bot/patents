"""Discovery scored on the full corridor, and its effect on reconciliation there."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baselines, constrained, dataset, discover, evaluate

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

def main(manifest="window_full_M25_A.json", seed=0):
    c = dataset.load(manifest)
    true_nodes = evaluate.fit_node_signs(c)
    truth = discover.truth_relations(c, true_nodes)
    print("corridor %d sites, %d surveyed nodes" % (c.shape[0], len(true_nodes)), flush=True)

    rel = discover.discover(c.volumes, c.observed)
    s = discover.score(rel, truth)
    span = discover.span_coverage(rel, truth, c.shape[0])
    val = discover.validity(rel)
    print("found %d | exact %d/%d (%.3f) | span coverage %.3f | valid share %.3f"
          % (s["relations_found"], s["exact_matches"], s["true_relations"],
             s["recall_exact"] or 0, span["coverage"] or 0, val["share"] or 0), flush=True)

    h = dataset.make_mask(c, 0.10, seed, max_run=96)
    v = dataset.train_view(c, h)
    rel_train = discover.discover(np.nan_to_num(v, nan=0.0), ~np.isnan(v))
    disc = discover.relations_to_fitted(rel_train, c)
    prior = baselines.knn_spatial(v, c.interval_index(), c.is_weekend())
    runs = evaluate.gap_run_lengths(h)
    calib = constrained.calibrate(c, true_nodes, mode="scaled")

    out = {"manifest": manifest, "score": s, "span": span, "validity": val,
           "discovered_usable": len(disc), "configs": {}}
    a0 = evaluate.accuracy(c.volumes, prior, h, runs)
    f0 = evaluate.feasibility(prior, true_nodes, calib, h)
    out["configs"]["none"] = {"MAE": a0["all"]["MAE"], "outside": f0["outside_band_pct"]}
    print("  %-20s MAE %7.2f  outside %6.2f%%" % ("none", a0["all"]["MAE"], f0["outside_band_pct"]), flush=True)

    for label, nodes in (("surveyed", true_nodes), ("discovered", disc),
                         ("both", true_nodes + disc)):
        filled, t = constrained.reconstruct(c, v, nodes, prior)
        a = evaluate.accuracy(c.volumes, filled, h, runs)
        f = evaluate.feasibility(filled, true_nodes, calib, h)
        out["configs"][label] = {"MAE": a["all"]["MAE"], "RMSE": a["all"]["RMSE"],
                                 "outside": f["outside_band_pct"],
                                 "constraints": len(nodes), "seconds": t["seconds"]}
        print("  %-20s MAE %7.2f  outside %6.2f%%  constraints %d  %.1fs"
              % (label, a["all"]["MAE"], f["outside_band_pct"], len(nodes), t["seconds"]), flush=True)

    with open(os.path.join(RESULTS, "discovery_full.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/discovery_full.json", flush=True)

if __name__ == "__main__":
    main()
