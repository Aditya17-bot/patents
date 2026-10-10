"""Evidence for the IDF-B: one-step-ahead correction of the ammonium sonde record.

    python src/experiments.py            -> results/e1_main.json (+ printed summary)

E1  accuracy at laboratory samples: raw, offset (single correction value), drift (linear in
    time between checks), method (conductivity interference term, k >= 0); ablation
    (unconstrained k) and controls (temperature instead of conductivity; conductivity
    shuffled among prior samples).
E2  by laboratory concentration band and by conductivity tercile.
E3  station bootstrap of the mean reduction against the offset baseline (2000 draws).
E4  alarm test at fixed thresholds: false alarms and missed exceedances against the lab.
E5  physics: fitted k positive share, within-site correlation of departure and conductivity,
    across-site relation of median over-read and median conductivity.
"""
import json
import math
import os
import random
import statistics as S
from concurrent.futures import ThreadPoolExecutor

import core

THRESHOLDS = (0.6, 1.0, 2.0)          # mg/L N, example alarm thresholds
BANDS = ((0, 0.2), (0.2, 1.0), (1.0, 1e9))


def summary(errs):
    e = sorted(errs)
    n = len(e)
    return {"n": n, "mean": S.mean(e), "median": e[n // 2], "p90": e[int(0.9 * n)]} if n else {"n": 0}


def sign_test(a, b):
    """Paired: how often |a| < |b| among pairs where they differ; normal-approximation z."""
    better = sum(1 for x, y in zip(a, b) if x < y - 1e-9)
    worse = sum(1 for x, y in zip(a, b) if x > y + 1e-9)
    n = better + worse
    z = (better - n / 2) / math.sqrt(n / 4) if n else 0.0
    return {"better": better, "of": n, "z": z}


def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for k, i in enumerate(o):
            r[i] = k
        return r
    rx, ry = rank(x), rank(y)
    mx, my = S.mean(rx), S.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def pearson(x, y):
    mx, my = S.mean(x), S.mean(y)
    den = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / den if den else float("nan")


def one(s):
    try:
        smp = core.site_samples(s)
    except Exception as e:
        return {"station": s["station"], "error": str(e)}
    return {"station": s["station"], "label": s["label"], "samples": smp, "rows": core.scored(smp)}


def main():
    sites = core.load_sites()
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(one, sites))
    res = [r for r in res if r.get("rows")]
    rows = [dict(x, station=r["station"]) for r in res for x in r["rows"]]
    err = {h: [abs(x[h] - x["lab"]) for x in rows] for h in core.ESTIMATORS}
    out = {"meta": {"window": core.WINDOW, "min_prior": core.MIN_PRIOR, "match_min": core.MATCH_MIN,
                    "sites_paired": len(sites), "sites_scored": len(res), "samples_scored": len(rows),
                    "samples_matched": sum(len(r["samples"]) for r in res),
                    "period": [min(x["t"] for x in rows)[:10], max(x["t"] for x in rows)[:10]]},
           "all": {h: summary(err[h]) for h in core.ESTIMATORS}}
    out["paired"] = {h: sign_test(err["method"], err[h]) for h in core.ESTIMATORS if h != "method"}
    # E2 bands
    out["by_lab_band"] = {}
    for a, b in BANDS:
        idx = [i for i, x in enumerate(rows) if a <= x["lab"] < b]
        out["by_lab_band"]["%g-%g" % (a, b)] = {
            h: summary([err[h][i] for i in idx]) for h in ("raw", "offset", "drift", "method")}
        out["by_lab_band"]["%g-%g" % (a, b)]["paired_vs_offset"] = sign_test(
            [err["method"][i] for i in idx], [err["offset"][i] for i in idx])
    scs = sorted(x["sc"] for x in rows)
    cuts = [scs[len(scs) // 3], scs[2 * len(scs) // 3]]
    out["sc_terciles_uScm"] = cuts
    out["by_sc_tercile"] = {}
    for name, lo, hi in (("low", -1, cuts[0]), ("mid", cuts[0], cuts[1]), ("high", cuts[1], 1e12)):
        idx = [i for i, x in enumerate(rows) if lo < x["sc"] <= hi]
        out["by_sc_tercile"][name] = {h: summary([err[h][i] for i in idx]) for h in ("raw", "offset", "method")}
        out["by_sc_tercile"][name]["paired_vs_offset"] = sign_test(
            [err["method"][i] for i in idx], [err["offset"][i] for i in idx])
    # per site
    per = []
    for r in res:
        e = {h: [abs(x[h] - x["lab"]) for x in r["rows"]] for h in ("raw", "offset", "drift", "method")}
        per.append({"station": r["station"], "label": r["label"], "n": len(r["rows"]),
                    "mae": {h: S.mean(v) for h, v in e.items()},
                    "median_sc": S.median(x["sc"] for x in r["samples"])})
    out["sites"] = per
    out["sites_method_better_than_offset"] = sum(1 for p in per if p["mae"]["method"] < p["mae"]["offset"])
    # E3 station bootstrap
    rng = random.Random(7)
    by = {}
    for x in rows:
        by.setdefault(x["station"], []).append(x)
    keys = sorted(by)
    boots = {"offset": [], "drift": [], "raw": []}
    for _ in range(2000):
        pick = [rng.choice(keys) for _ in keys]
        xs = [x for k in pick for x in by[k]]
        m = S.mean(abs(x["method"] - x["lab"]) for x in xs)
        for h in boots:
            boots[h].append(S.mean(abs(x[h] - x["lab"]) for x in xs) - m)
    out["bootstrap_reduction_mgL"] = {h: {"mean": S.mean(v), "ci95": [sorted(v)[50], sorted(v)[1949]]}
                                      for h, v in boots.items()}
    # E4 alarms
    out["alarms"] = {}
    for T in THRESHOLDS:
        d = {"lab_exceed": sum(1 for x in rows if x["lab"] > T)}
        for h in ("raw", "offset", "drift", "method"):
            d[h] = {"false_alarms": sum(1 for x in rows if x[h] > T and x["lab"] <= T),
                    "missed": sum(1 for x in rows if x[h] <= T and x["lab"] > T)}
        out["alarms"]["%g" % T] = d
    # E5 physics
    ks, rs, med_dep, med_sc = [], [], [], []
    for r in res:
        smp = r["samples"]
        dep = [x["sonde"] - x["lab"] for x in smp]
        sc = [x["sc"] for x in smp]
        k, b = core.fit_line(sc, dep)
        ks.append(k)
        if len(smp) >= 8:
            rs.append(pearson(sc, dep))
        med_dep.append(S.median(dep))
        med_sc.append(S.median(sc))
    out["physics"] = {"k_positive": sum(1 for k in ks if k > 0), "k_n": len(ks),
                      "k_median_mgL_per_1000uS": 1000 * S.median(ks),
                      "within_site_r_median": S.median(rs), "within_site_r_positive": sum(1 for r in rs if r > 0),
                      "within_site_r_n": len(rs),
                      "across_site_spearman_overread_vs_sc": spearman(med_sc, med_dep),
                      "across_sites": [[a, b] for a, b in zip(med_sc, med_dep)]}
    core.dump("e1_main.json", out)
    core.dump("e1_rows.json", rows)
    print(json.dumps({k: out[k] for k in ("meta", "all", "paired")}, indent=1, default=str))
    print("sites method < offset:", out["sites_method_better_than_offset"], "of", len(per))
    print("bootstrap:", json.dumps(out["bootstrap_reduction_mgL"]))
    print("bands:", json.dumps({k: {h: round(v[h]["mean"], 3) for h in ("raw", "offset", "method")} for k, v in out["by_lab_band"].items()}))
    print("sc terciles:", json.dumps({k: {h: round(v[h]["mean"], 3) for h in ("raw", "offset", "method")} for k, v in out["by_sc_tercile"].items()}))
    print("alarms:", json.dumps(out["alarms"]))
    print("physics:", json.dumps({k: v for k, v in out["physics"].items() if k != "across_sites"}))


if __name__ == "__main__":
    main()
