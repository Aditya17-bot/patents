"""E9: uncertainty and robustness of the main effects.

1. Cluster bootstrap: visits at one station are not independent, so stations (targets) are
   resampled with replacement, B times, and the reduction of mean absolute discharge error
   recomputed.
2. Station hold-out: the stations, sorted by number, are dealt alternately into two halves,
   with every constant frozen; the effect is reported on each half separately.
3. Sensitivity: the gain prior and warm-up; the coupling threshold; the window length and
   the steadiness threshold (probe_daily rerun into daily_w14, daily_w28, daily_s15,
   daily_s35 by rebuild.sh).

Output: results/e9_bootstrap.json
"""
import json
import os

import numpy as np

import experiments as EX

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = 2000
MIN_VISITS = 5


def boot(recs, a, b, mask=None, seed=0):
    if mask is not None:
        recs = [q for q, m in zip(recs, mask) if m]
    by = {}
    for q in recs:
        by.setdefault(q["x"], []).append((q[a], q[b]))
    keys = sorted(by)
    rng = np.random.default_rng(seed)
    red = []
    for _ in range(B):
        pick = rng.integers(0, len(keys), len(keys))
        ea = np.concatenate([[v[0] for v in by[keys[i]]] for i in pick])
        eb = np.concatenate([[v[1] for v in by[keys[i]]] for i in pick])
        red.append(float(np.mean(ea) - np.mean(eb)))
    ea_all = np.array([q[a] for q in recs])
    eb_all = np.array([q[b] for q in recs])
    st = [k for k in keys if len(by[k]) >= MIN_VISITS]
    better = sum(1 for k in st if np.mean([v[1] for v in by[k]]) < np.mean([v[0] for v in by[k]]))
    return {"n": len(recs), "stations": len(keys),
            "baseline_mean": round(float(np.mean(ea_all)), 2), "method_mean": round(float(np.mean(eb_all)), 2),
            "reduction_pts": round(float(np.mean(ea_all) - np.mean(eb_all)), 2),
            "ci95": [round(float(np.percentile(red, 2.5)), 2), round(float(np.percentile(red, 97.5)), 2)],
            "stations_with_5plus": len(st), "stations_better": better}


def big(recs, k="true_dev"):
    return [abs(q[k]) >= EX.BIG for q in recs]


def e1_summary(recs):
    bg = big(recs)
    return {"n": len(recs), "stations": len({q["x"] for q in recs}),
            "all": [round(float(np.mean([q[k] for q in recs])), 2) for k in ("e_lin", "e_hat")],
            "all_paired": EX.paired([q["e_lin"] for q in recs], [q["e_hat"] for q in recs]),
            "big": [round(float(np.mean([q[k] for q, m in zip(recs, bg) if m])), 2) for k in ("e_lin", "e_hat")]}


def main():
    pub, rt = EX.load("daily"), EX.load("daily_rt")
    r1 = EX.interpolation(pub)
    r1rt = EX.interpolation(rt)
    r2rt = EX.realtime(rt)
    ow = [EX.is_open_water(q) for q in r1]
    bg1 = big(r1)
    out = {"B": B, "min_visits": MIN_VISITS,
           "e1_all": boot(r1, "e_lin", "e_hat"),
           "e1_open_water": boot(r1, "e_lin", "e_hat", ow),
           "e1_big": boot(r1, "e_lin", "e_hat", bg1),
           "e1_big_vs_flood_step": boot(r1, "e_step", "e_hat", bg1),
           "e1_open_water_big": boot(r1, "e_lin", "e_hat", [o and b for o, b in zip(ow, bg1)]),
           "e1_vs_practice": boot(r1, "e_prac", "e_hat"),
           "e1_open_water_vs_practice": boot(r1, "e_prac", "e_hat", ow),
           "e1_rt_all": boot(r1rt, "e_lin", "e_hat"),
           "e1_rt_big": boot(r1rt, "e_lin", "e_hat", big(r1rt)),
           "e2_rt_all": boot(r2rt, "e_carry", "e_gain"),
           "e2_rt_big": boot(r2rt, "e_carry", "e_gain", big(r2rt, "true_change"))}

    # station hold-out: constants frozen; stations sorted by number and dealt alternately
    # into two halves
    order = sorted({q["x"] for q in r1})
    half_of = {x: i % 2 for i, x in enumerate(order)}
    ip_path = os.path.join(ROOT, "results", "daily_ip.json")
    if os.path.exists(ip_path):
        rip = EX.interpolation(EX.load("daily_ip"))
        out["e1_ip_all"] = boot(rip, "e_lin", "e_hat")
        out["e1_ip_vs_practice"] = boot(rip, "e_prac", "e_hat")
        out["e1_ip_open_water"] = boot(rip, "e_lin", "e_hat", [EX.is_open_water(q) for q in rip])
    out["holdout"] = {}
    for half, par in (("first", 0), ("second", 1)):
        sub = [q for q in r1 if half_of[q["x"]] == par]
        out["holdout"][half] = e1_summary(sub)

    # sensitivity of E1 to the gain prior and warm-up length
    grid = []
    keep = (EX.GAIN_PRIOR, EX.GAIN_MIN_PAST)
    for prior in (0.0, 0.25, 0.5, 0.75):
        for mp in (3, 5, 8):
            EX.GAIN_PRIOR, EX.GAIN_MIN_PAST = prior, mp
            rr = EX.interpolation(pub)
            s = e1_summary(rr)
            grid.append({"prior": prior, "min_past": mp, "all_mean": s["all"][1], "big_mean": s["big"][1]})
    EX.GAIN_PRIOR, EX.GAIN_MIN_PAST = keep
    out["sensitivity"] = grid
    out["sensitivity_range_all"] = [min(g["all_mean"] for g in grid), max(g["all_mean"] for g in grid)]
    out["sensitivity_range_big"] = [min(g["big_mean"] for g in grid), max(g["big_mean"] for g in grid)]

    # sensitivity to the coupling threshold, window length and steadiness threshold
    var = []
    keep_c = EX.MIN_COUPLING
    for c in (0.90, 0.95, 0.97):
        EX.MIN_COUPLING = c
        var.append(dict(e1_summary(EX.interpolation(pub)), what="coupling", value=c))
    EX.MIN_COUPLING = keep_c
    for name, what, value in (("daily_w14", "window_days", 14), ("daily_w28", "window_days", 28),
                              ("daily_s15", "steady_ft", 0.15), ("daily_s35", "steady_ft", 0.35)):
        path = os.path.join(ROOT, "results", name + ".json")
        if os.path.exists(path):
            var.append(dict(e1_summary(EX.interpolation(EX.load(name))), what=what, value=value))
    out["variants"] = var
    json.dump(out, open(os.path.join(ROOT, "results", "e9_bootstrap.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
