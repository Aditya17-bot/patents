"""E2: correction of a sonde with no laboratory history (new or relocated deployment).

Leave one site out: the interference coefficient is fitted on the matched samples of all
other sites and applied to every matched sample of the held-out site, from its first sample.
    raw        sonde reading
    net_offset reading - median departure of the other sites (one value for the network)
    method     reading - (b + k * conductivity), b and k >= 0 fitted on the other sites
    method_med same with a robust fit: k from the median of per-site slopes ... (see below)
The fit is least squares on departures; departures are clipped to the 1st-99th percentile of
the training pool so that gross sonde faults do not set the coefficient.
Output: results/e2_coldstart.json
"""
import json
import math
import os
import statistics as S

import core


def clip_pool(xs, ys):
    s = sorted(ys)
    lo, hi = s[int(0.01 * len(s))], s[int(0.99 * len(s)) - 1]
    keep = [(x, y) for x, y in zip(xs, ys) if lo <= y <= hi]
    return [k[0] for k in keep], [k[1] for k in keep]


def summary(e):
    e = sorted(e)
    n = len(e)
    return {"n": n, "mean": S.mean(e), "median": e[n // 2], "p90": e[int(0.9 * n)],
            "trimmed_mean_99": S.mean(e[:int(0.99 * n)])}


def sign(a, b):
    better = sum(1 for x, y in zip(a, b) if x < y - 1e-9)
    worse = sum(1 for x, y in zip(a, b) if x > y + 1e-9)
    n = better + worse
    return {"better": better, "of": n, "z": (better - n / 2) / math.sqrt(n / 4) if n else 0.0}


def main():
    rows = json.load(open(os.path.join(core.RESULTS, "e1_rows.json")))   # only for the station list
    sites = core.load_sites()
    samples = {}
    for s in sites:
        try:
            smp = core.site_samples(s)
        except Exception:
            continue
        if len(smp) >= 3:
            samples[s["station"]] = smp
    keys = sorted(samples)
    out_rows = []
    for held in keys:
        xs = [x["sc"] for k in keys if k != held for x in samples[k]]
        ys = [x["sonde"] - x["lab"] for k in keys if k != held for x in samples[k]]
        ts = [x["temp"] for k in keys if k != held for x in samples[k]]
        pool = [(x, y, t) for x, y, t in zip(xs, ys, ts)]
        s_ = sorted(ys)
        lo, hi = s_[int(0.01 * len(s_))], s_[int(0.99 * len(s_)) - 1]
        pool = [p for p in pool if lo <= p[1] <= hi]
        xs, ys = [p[0] for p in pool], [p[1] for p in pool]
        k, b = core.fit_nonneg(xs, ys)
        b0 = S.median(ys)
        bmean = S.mean(ys)                                   # same pool, k = 0: matched constant
        bmed = S.median(y - k * x for x, y in zip(xs, ys))   # method with a median intercept
        tp = [(p[2], p[1]) for p in pool if p[2] is not None]
        kt, bt = core.fit_line([a for a, _ in tp], [c for _, c in tp])
        sh = xs[len(xs) // 2:] + xs[:len(xs) // 2]          # conductivity moved to other samples
        ksh, bsh = core.fit_nonneg(sh, ys)
        for x in samples[held]:
            out_rows.append({"station": held, "lab": x["lab"], "sonde": x["sonde"], "sc": x["sc"],
                             "raw": x["sonde"], "net_offset": max(x["sonde"] - b0, 0.0),
                             "net_mean": max(x["sonde"] - bmean, 0.0),
                             "method": max(x["sonde"] - b - k * x["sc"], 0.0),
                             "method_median_b": max(x["sonde"] - bmed - k * x["sc"], 0.0),
                             "placebo_temp": max(x["sonde"] - bt - kt * x["temp"], 0.0) if x["temp"] is not None else max(x["sonde"] - bmean, 0.0),
                             "placebo_shuffled": max(x["sonde"] - bsh - ksh * x["sc"], 0.0),
                             "k": k, "b": b})
    H = ("raw", "net_offset", "net_mean", "method", "method_median_b", "placebo_temp", "placebo_shuffled")
    err = {h: [abs(r[h] - r["lab"]) for r in out_rows] for h in H}
    res = {"sites": len(keys), "samples": len(out_rows),
           "all": {h: summary(v) for h, v in err.items()},
           "paired_vs_raw": sign(err["method"], err["raw"]),
           "paired_vs_net_offset": sign(err["method"], err["net_offset"]),
           "paired_vs_net_mean": sign(err["method"], err["net_mean"]),
           "paired_median_b_vs_net_offset": sign(err["method_median_b"], err["net_offset"]),
           "paired_vs_placebo_temp": sign(err["method"], err["placebo_temp"]),
           "paired_vs_placebo_shuffled": sign(err["method"], err["placebo_shuffled"]),
           "k_per_1000uS_median": 1000 * S.median(r["k"] for r in out_rows),
           "b_median": S.median(r["b"] for r in out_rows)}
    per = {}
    for r in out_rows:
        per.setdefault(r["station"], []).append(r)
    res["sites_better_than_raw"] = sum(1 for v in per.values()
                                       if S.mean(abs(r["method"] - r["lab"]) for r in v) < S.mean(abs(r["raw"] - r["lab"]) for r in v))
    res["sites_better_than_net_mean"] = sum(1 for v in per.values()
                                            if S.mean(abs(r["method"] - r["lab"]) for r in v) < S.mean(abs(r["net_mean"] - r["lab"]) for r in v))
    res["sites_better_than_net_offset"] = sum(1 for v in per.values()
                                              if S.mean(abs(r["method"] - r["lab"]) for r in v) < S.mean(abs(r["net_offset"] - r["lab"]) for r in v))
    scs = sorted(r["sc"] for r in out_rows)
    cuts = [scs[len(scs) // 3], scs[2 * len(scs) // 3]]
    res["sc_cuts"] = cuts
    res["by_sc"] = {}
    for name, lo, hi in (("low", -1, cuts[0]), ("mid", cuts[0], cuts[1]), ("high", cuts[1], 1e12)):
        idx = [i for i, r in enumerate(out_rows) if lo < r["sc"] <= hi]
        res["by_sc"][name] = {h: summary([err[h][i] for i in idx]) for h in ("raw", "net_offset", "net_mean", "method")}
        res["by_sc"][name]["paired_vs_net_offset"] = sign([err["method"][i] for i in idx], [err["net_offset"][i] for i in idx])
        res["by_sc"][name]["paired_vs_net_mean"] = sign([err["method"][i] for i in idx], [err["net_mean"][i] for i in idx])
    # station bootstrap of median and trimmed-mean reductions against the network offset
    import random
    rng = random.Random(5)
    per_keys = sorted(per)
    for base in ("net_offset", "net_mean"):
        meds, trims, p90s = [], [], []
        for _ in range(2000):
            pick = [rng.choice(per_keys) for _ in per_keys]
            a = sorted(abs(r[base] - r["lab"]) for k in pick for r in per[k])
            m = sorted(abs(r["method"] - r["lab"]) for k in pick for r in per[k])
            meds.append(a[len(a) // 2] - m[len(m) // 2])
            p90s.append(a[int(0.9 * len(a))] - m[int(0.9 * len(m))])
            trims.append(S.mean(a[:int(0.99 * len(a))]) - S.mean(m[:int(0.99 * len(m))]))
        meds.sort()
        trims.sort()
        p90s.sort()
        res["bootstrap_vs_" + base] = {"median_reduction": {"mean": S.mean(meds), "ci95": [meds[50], meds[1949]]},
                                       "p90_reduction": {"mean": S.mean(p90s), "ci95": [p90s[50], p90s[1949]]},
                                       "trimmed_mean_reduction": {"mean": S.mean(trims), "ci95": [trims[50], trims[1949]]}}
    res["alarms"] = {}
    for T in (0.6, 1.0, 2.0):
        d = {"lab_exceed": sum(1 for r in out_rows if r["lab"] > T), "lab_below": sum(1 for r in out_rows if r["lab"] <= T)}
        for h in ("raw", "net_offset", "net_mean", "method"):
            d[h] = {"false_alarms": sum(1 for r in out_rows if r[h] > T and r["lab"] <= T),
                    "missed": sum(1 for r in out_rows if r[h] <= T and r["lab"] > T)}
        res["alarms"]["%g" % T] = d
    # controls: the same network fit on water temperature, and on conductivity shuffled
    # among the other sites' samples (breaks the sample-level link, keeps its distribution)
    core.dump("e2_coldstart.json", res)
    core.dump("e2_rows.json", out_rows)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
