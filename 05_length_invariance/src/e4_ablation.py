"""E4 - does each admission condition earn its place? Fit with it removed, score as usual.

Biases are fitted on March with one condition relaxed at a time, then scored on April-June
exactly as in E1 (standard gate and free-flow condition for the scoring pairs, so every
variant is judged on the same pairs and intervals):

    claimed            volume-balance gate 3 %, free flow above 50 mph
    no volume gate     any volume ratio admitted to the fit (lane loss, unmodelled access)
    loose volume gate  10 %
    no free-flow       every interval with both detectors reporting, any speed

Policy scored: correct every detector with a March fit on a chain of 3 or more, additive
model (the best policy in E1). Also reported: median day-to-day standard error of the
fitted bias below 520 cm, which is where the free-flow condition should show.

Output: results/e4_ablation.json
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluate_e1
import method
import pairs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
STANDARD = {"BALANCE_TOL": pairs.BALANCE_TOL, "MIN_SPEED_MPH": pairs.MIN_SPEED_MPH}
VARIANTS = [
    ("claimed", {}),
    ("no volume gate", {"BALANCE_TOL": 1e9}),
    ("loose volume gate 10%", {"BALANCE_TOL": 0.10}),
    ("no free-flow condition", {"MIN_SPEED_MPH": -1.0}),
]


def set_params(overrides):
    for k, v in STANDARD.items():
        setattr(pairs, k, overrides.get(k, v))


def score(road, fits):
    set_params({})
    out = {}
    for month in evaluate_e1.EVAL_MONTHS:
        raw, corr = [], []
        for chain in pairs.chains(road, month):
            for up, down, nid, rec in chain:
                chosen = {d: fits[d] for d in (up, down)
                          if d in fits and fits[d]["chain_size"] >= 3}
                if not chosen:
                    continue
                a = method.correct_series(rec["a"], chosen[up], "additive") \
                    if up in chosen else rec["a"]
                b = method.correct_series(rec["b"], chosen[down], "additive") \
                    if down in chosen else rec["b"]
                raw.append(abs(method.pair_gap(rec)[0][0]))
                corr.append(abs(method.pair_gap({"keys": rec["keys"], "a": a, "b": b})[0][0]))
        out[month] = {"touched_pairs": len(raw),
                      "raw_mean_abs_gap_520": round(sum(raw) / len(raw), 5),
                      "corrected_mean_abs_gap_520": round(sum(corr) / len(corr), 5)}
    return out


def main():
    report = {"policy": "all/additive", "variants": {}}
    for name, overrides in VARIANTS:
        report["variants"][name] = {}
        for road in ("M25", "M1"):
            set_params(overrides)
            fits = evaluate_e1.fit(road)
            ses = sorted(f["se"][0] for f in fits.values()
                         if f["chain_size"] >= 3 and f["se"][0] == f["se"][0])
            on3 = sum(1 for f in fits.values() if f["chain_size"] >= 3)
            res = {"fitted_on_chains_of_3_or_more": on3,
                   "median_se_520": round(ses[len(ses) // 2], 5) if ses else None,
                   "scores": score(road, fits)}
            report["variants"][name][road] = res
            print(name, road, json.dumps(res))
    set_params({})
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "e4_ablation.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
