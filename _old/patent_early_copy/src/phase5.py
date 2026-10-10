"""Phase 5 — robustness. Vary the mask seed and report the spread, not a single run.

A single lucky mask proves nothing. Every headline number in the disclosure has to be
one that holds up when the experiment is repeated, so each configuration is run over
several seeds and the spread is reported alongside the mean.
"""

import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import phase4

RESULTS = os.path.join(ROOT, "results")


def summarise(runs, key):
    """Mean and range across seeds for one method, one metric."""
    values = [r["methods"][key[0]][key[1]][key[2]][key[3]] if len(key) == 4
              else r["methods"][key[0]][key[1]][key[2]] for r in runs]
    return {"mean": round(statistics.mean(values), 3),
            "min": round(min(values), 3),
            "max": round(max(values), 3),
            "n_seeds": len(values)}


def run(manifest="window.json", seeds=(0, 1, 2), max_run=96, regime="operational",
        out_name="phase5_robustness.json"):
    runs = []
    for seed in seeds:
        print("=== seed %d ===" % seed)
        runs.append(phase4.run(manifest, seed=seed, max_run=max_run, regime=regime,
                               out_name="_scratch_phase5.json"))

    methods = sorted(runs[0]["methods"])
    table = {}
    for m in methods:
        table[m] = {
            "MAE": summarise(runs, (m, "accuracy", "all", "MAE")),
            "RMSE": summarise(runs, (m, "accuracy", "all", "RMSE")),
            "residual_pct": summarise(runs, (m, "consistency",
                                             "median_residual_pct_of_flow")),
            "outside_band_pct": summarise(runs, (m, "feasibility", "outside_band_pct")),
        }

    print("\n%-40s %-22s %-22s" % ("method", "MAE mean [min-max]", "outside% mean [min-max]"))
    for m in methods:
        a, f = table[m]["MAE"], table[m]["outside_band_pct"]
        print("%-40s %7.2f [%6.2f-%6.2f]  %6.2f [%5.2f-%5.2f]"
              % (m, a["mean"], a["min"], a["max"], f["mean"], f["min"], f["max"]))

    out = {"manifest": manifest, "regime": regime, "seeds": list(seeds),
           "corridor": runs[0]["corridor"], "table": table}
    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/%s" % out_name)

    scratch = os.path.join(RESULTS, "_scratch_phase5.json")
    if os.path.exists(scratch):
        os.remove(scratch)
    return out


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window.json"
    out_name = sys.argv[2] if len(sys.argv) > 2 else "phase5_robustness.json"
    run(manifest, out_name=out_name)
