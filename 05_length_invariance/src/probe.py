"""Feasibility probe: do adjacent detectors that see the same vehicles disagree on length?

M25 and M1, carriageway A. Every pair of consecutive mainline detectors with no slip road
between them (pairs.candidates), over the intervals both reported with average speed
above 50 mph (pairs.matched). No volume gate here, so the probe also shows what the gate
is for. Reported for March 2025:

    volume ratio up/down                    same vehicles or not
    |gap| in share below 520 cm             size of the disagreement
    relative gap in share above 1160 cm     the same for the longest class
    correlation of the gap with the ratio of the two detectors' mean speeds
                                            a speed error would show here
    correlation of each pair's gap, March vs each later month, over pairs balanced in
    both months                             persistence: a detector property, not noise

Output: results/probe.json
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import method
import pairs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MONTHS = ["2025-03", "2025-04", "2025-05", "2025-06"]


def pct(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


def corr(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy)


def pair_stats(rec):
    keys = rec["keys"]
    a, b = rec["a"], rec["b"]
    su, sd = method.shares(a, keys), method.shares(b, keys)
    long_u, long_d = 1 - su[-1], 1 - sd[-1]
    spd_u = sum(a[k][2] for k in keys) / len(keys)
    spd_d = sum(b[k][2] for k in keys) / len(keys)
    return {"ratio": rec["ratio"], "gap520": su[0] - sd[0],
            "rel_gap_long": (long_u - long_d) / (0.5 * (long_u + long_d)),
            "speed_ratio": spd_u / spd_d, "admitted": rec["admitted"]}


def main():
    report = {"roads": {}}
    for road in ("M25", "M1"):
        per_month = {}
        for m in MONTHS:
            rows = {}
            for up, down, nid in pairs.candidates(road):
                rec = pairs.pair_record(up, down, m)
                if rec is not None:
                    rows[nid] = pair_stats(rec)
            per_month[m] = rows
        march = per_month[MONTHS[0]]
        gaps = [abs(r["gap520"]) for r in march.values()]
        worst = max(march, key=lambda n: abs(march[n]["gap520"]))
        out = {
            "pairs_march": len(march),
            "volume_ratio_median": round(pct([r["ratio"] for r in march.values()], 0.5), 4),
            "abs_gap520_median": round(pct(gaps, 0.5), 4),
            "abs_gap520_p90": round(pct(gaps, 0.9), 4),
            "abs_gap520_max": round(max(gaps), 4),
            "abs_gap520_max_pair": worst,
            "abs_gap520_max_pair_volume_ratio": round(march[worst]["ratio"], 4),
            "abs_rel_gap_long_median": round(
                pct([abs(r["rel_gap_long"]) for r in march.values()], 0.5), 4),
            "abs_rel_gap_long_p90": round(
                pct([abs(r["rel_gap_long"]) for r in march.values()], 0.9), 4),
            "corr_gap520_speed_ratio": round(
                corr([r["gap520"] for r in march.values()],
                     [r["speed_ratio"] for r in march.values()]), 3),
            "persistence": {},
        }
        for m in MONTHS[1:]:
            later = per_month[m]
            both = [n for n in march if n in later
                    and march[n]["admitted"] and later[n]["admitted"]]
            out["persistence"][m] = {
                "pairs": len(both),
                "corr_gap520_vs_march": round(corr([march[n]["gap520"] for n in both],
                                                   [later[n]["gap520"] for n in both]), 3)}
        # Per-pair values, for the figures: ratio, gap and admission per month.
        out["pairs"] = {nid: {m: {"ratio": round(per_month[m][nid]["ratio"], 5),
                                  "gap520": round(per_month[m][nid]["gap520"], 5),
                                  "admitted": per_month[m][nid]["admitted"]}
                              for m in MONTHS if nid in per_month[m]}
                        for nid in march}
        report["roads"][road] = out
        print(road, json.dumps({k: v for k, v in out.items() if k != "pairs"}))
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "probe.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
