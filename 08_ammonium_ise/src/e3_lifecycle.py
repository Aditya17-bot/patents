"""E3: correction over the life of a deployment, from its first reading.

For each held-out site, samples are taken in time order; sample i is corrected using only
the other sites (network) and the site's own samples before i.
    practice   i = 0: raw reading; i >= 1: reading - median of the site's prior departures
               (one correction value from laboratory samples, as in US 8,691,074 B2)
    method     k from the network fit (k >= 0, other sites only); b = network intercept at
               i = 0, then b = median over the site's prior samples of (departure - k * K)
    method_sitek  as method, but once the site has >= MIN_SITE_K prior samples, k and b are
               refitted on the site's own recent samples (k >= 0)
Results by number of prior site samples: 0, 1-2, 3-5, 6-11, >= 12.
Output: results/e3_lifecycle.json
"""
import json
import math
import os
import statistics as S

import core
from e2_coldstart import clip_pool, sign, summary

MIN_SITE_K = 12
N0 = 6        # weight of the network coefficient, in samples (fixed before scoring)
BINS = ((0, 0), (1, 2), (3, 5), (6, 11), (12, 10 ** 6))


def main():
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
    rows = []
    for held in keys:
        xs = [x["sc"] for k in keys if k != held for x in samples[k]]
        ys = [x["sonde"] - x["lab"] for k in keys if k != held for x in samples[k]]
        xs, ys = clip_pool(xs, ys)
        kn, bn = core.fit_nonneg(xs, ys)
        smp = samples[held]
        for i, x in enumerate(smp):
            prior = smp[:i][-core.WINDOW:]
            if i == 0:
                prac = x["sonde"]
                b = bn
            else:
                prac = max(x["sonde"] - S.median(q["sonde"] - q["lab"] for q in prior), 0.0)
                b = S.median(q["sonde"] - q["lab"] - kn * q["sc"] for q in prior)
            meth = max(x["sonde"] - b - kn * x["sc"], 0.0)
            if i >= MIN_SITE_K:
                ks, bs = core.fit_nonneg([q["sc"] for q in prior], [q["sonde"] - q["lab"] for q in prior])
                sitek = max(x["sonde"] - bs - ks * x["sc"], 0.0)
            else:
                sitek = meth
            # shrink: k moves from the network value to the site's own as samples arrive
            if len(prior) >= 3:
                ks, _ = core.fit_nonneg([q["sc"] for q in prior], [q["sonde"] - q["lab"] for q in prior])
                n = len(prior)
                kk = (N0 * kn + n * ks) / (N0 + n)
                bb = S.median(q["sonde"] - q["lab"] - kk * q["sc"] for q in prior)
            else:
                kk, bb = kn, b
            shrink = max(x["sonde"] - bb - kk * x["sc"], 0.0)
            rows.append({"station": held, "i": i, "t": x["t"].isoformat(), "lab": x["lab"],
                         "sonde": x["sonde"], "sc": x["sc"], "practice": prac, "method": meth,
                         "method_sitek": sitek, "shrink": shrink, "k_used": kk, "k_net": kn, "b_net": bn})
    err = {h: [abs(r[h] - r["lab"]) for r in rows] for h in ("practice", "method", "method_sitek", "shrink")}
    out = {"sites": len(keys), "samples": len(rows), "all": {h: summary(v) for h, v in err.items()},
           "paired_vs_practice": sign(err["method"], err["practice"]),
           "sitek_vs_practice": sign(err["method_sitek"], err["practice"]),
           "shrink_vs_practice": sign(err["shrink"], err["practice"]),
           "by_prior": {}}
    for lo, hi in BINS:
        idx = [j for j, r in enumerate(rows) if lo <= r["i"] <= hi]
        out["by_prior"]["%d-%d" % (lo, hi) if hi < 10 ** 6 else ">=%d" % lo] = {
            "practice": summary([err["practice"][j] for j in idx]),
            "method": summary([err["method"][j] for j in idx]),
            "method_sitek": summary([err["method_sitek"][j] for j in idx]),
            "shrink": summary([err["shrink"][j] for j in idx]),
            "paired": sign([err["method"][j] for j in idx], [err["practice"][j] for j in idx]),
            "paired_shrink": sign([err["shrink"][j] for j in idx], [err["practice"][j] for j in idx])}
    per = {}
    for r in rows:
        per.setdefault(r["station"], []).append(r)
    out["sites_shrink_better"] = sum(1 for v in per.values()
                                     if S.mean(abs(r["shrink"] - r["lab"]) for r in v)
                                     < S.mean(abs(r["practice"] - r["lab"]) for r in v))
    out["sites_method_better"] = sum(1 for v in per.values()
                                     if S.mean(abs(r["method"] - r["lab"]) for r in v)
                                     < S.mean(abs(r["practice"] - r["lab"]) for r in v))
    # station bootstrap of the trimmed-mean reduction (99 %), method against practice
    import random
    rng = random.Random(11)
    red = []
    for _ in range(2000):
        pick = [rng.choice(keys) for _ in keys]
        a = sorted(abs(r["practice"] - r["lab"]) for k in pick for r in per[k])
        m = sorted(abs(r["shrink"] - r["lab"]) for k in pick for r in per[k])
        red.append(S.mean(a[:int(0.99 * len(a))]) - S.mean(m[:int(0.99 * len(m))]))
    red.sort()
    out["bootstrap_trimmed_reduction"] = {"mean": S.mean(red), "ci95": [red[50], red[1949]]}
    # alarms at fixed thresholds
    out["alarms"] = {}
    for T in (0.6, 1.0, 2.0):
        d = {"lab_exceed": sum(1 for r in rows if r["lab"] > T), "lab_below": sum(1 for r in rows if r["lab"] <= T)}
        for h in ("sonde", "practice", "method", "shrink"):
            d[h] = {"false_alarms": sum(1 for r in rows if r[h] > T and r["lab"] <= T),
                    "missed": sum(1 for r in rows if r[h] <= T and r["lab"] > T)}
        out["alarms"]["%g" % T] = d
    core.dump("e3_lifecycle.json", out)
    core.dump("e3_rows.json", rows)
    print(json.dumps({k: v for k, v in out.items() if k != "by_prior"}, indent=1))
    for k, v in out["by_prior"].items():
        print(k, "n=%d" % v["practice"]["n"], "median practice %.3f method %.3f shrink %.3f" % (
            v["practice"]["median"], v["method"]["median"], v["shrink"]["median"]),
            "p90 %.2f %.2f" % (v["practice"]["p90"], v["shrink"]["p90"]),
            "trimmed %.3f %.3f %.3f" % (v["practice"]["trimmed_mean_99"], v["method"]["trimmed_mean_99"], v["shrink"]["trimmed_mean_99"]),
            "z shrink %.2f (%d/%d)" % (v["paired_shrink"]["z"], v["paired_shrink"]["better"], v["paired_shrink"]["of"]))


if __name__ == "__main__":
    main()
