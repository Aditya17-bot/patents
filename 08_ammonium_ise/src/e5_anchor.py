"""E5 (probe): floor tracking anchored at laboratory samples, over the life of each site.

Sample i of a site is corrected from the site's samples before i only.
    practice  reading - median of the prior departures (stale between laboratory samples)
    anchored  reading - (floor(t) - g), with g = median over prior samples of
              (floor(t_j) - departure_j): the laboratory samples fix how far the floor sits
              above the true background; the floor then follows offset changes between them
Samples with no prior sample use: practice = raw; anchored = floor - network background.
Output: results/e5_anchor.json
"""
import bisect
import datetime as dt
import json
import os
import random
import statistics as S

import core
import ea
from e2_coldstart import sign, summary
from e4_floor import FLOOR_DAYS, Q, quant


def main():
    sites = core.load_sites()
    data = {}
    for s in sites:
        try:
            smp = core.site_samples(s)
            amm = [r for r in ea.readings(s["station"] + "-amm-i-subdaily-mgL", s["opened"], s["closed"]) if r[1] >= 0]
        except Exception:
            continue
        at, av = [r[0] for r in amm], [r[1] for r in amm]
        keep = []
        for x in smp:
            i1 = bisect.bisect_right(at, x["t"])
            i0 = bisect.bisect_left(at, x["t"] - dt.timedelta(days=FLOOR_DAYS))
            if i1 - i0 >= 96:
                keep.append(dict(x, floor=quant(av[i0:i1], Q)))
        if len(keep) >= 3:
            data[s["station"]] = keep
    keys = sorted(data)
    labq = {k: quant([x["lab"] for x in data[k]], 0.10) for k in keys}
    rows = []
    for held in keys:
        bg = S.median(labq[k] for k in keys if k != held)
        smp = data[held]
        for i, x in enumerate(smp):
            prior = smp[:i][-core.WINDOW:]
            if prior:
                prac = max(x["sonde"] - S.median(q["sonde"] - q["lab"] for q in prior), 0.0)
                g = S.median(q["floor"] - (q["sonde"] - q["lab"]) for q in prior)
            else:
                prac, g = x["sonde"], bg
            anch = max(x["sonde"] - (x["floor"] - g), 0.0)
            serviced = bool(prior) and (x["t"] - prior[-1]["t"]).total_seconds() / 86400 > x["since_service_d"]
            rows.append({"station": held, "i": i, "lab": x["lab"], "sonde": x["sonde"], "since_service_d": x["since_service_d"],
                         "serviced_since_last_lab": serviced, "floor": x["floor"],
                         "practice": prac, "anchored": anch})
    err = {h: [abs(r[h] - r["lab"]) for r in rows] for h in ("practice", "anchored")}
    per = {}
    for r in rows:
        per.setdefault(r["station"], []).append(r)
    out = {"sites": len(per), "samples": len(rows), "all": {h: summary(v) for h, v in err.items()},
           "paired": sign(err["anchored"], err["practice"]),
           "sites_better": sum(1 for v in per.values()
                               if S.mean(abs(r["anchored"] - r["lab"]) for r in v) < S.mean(abs(r["practice"] - r["lab"]) for r in v))}
    later = [j for j, r in enumerate(rows) if r["i"] >= 1]
    out["with_prior_samples"] = {"practice": summary([err["practice"][j] for j in later]),
                                 "anchored": summary([err["anchored"][j] for j in later]),
                                 "paired": sign([err["anchored"][j] for j in later], [err["practice"][j] for j in later])}
    rng = random.Random(9)
    st = {"median": [], "p90": [], "trim": []}
    for _ in range(2000):
        pick = [rng.choice(keys) for _ in keys]
        a = sorted(abs(r["practice"] - r["lab"]) for k in pick for r in per[k] if r["i"] >= 1)
        m = sorted(abs(r["anchored"] - r["lab"]) for k in pick for r in per[k] if r["i"] >= 1)
        st["median"].append(a[len(a) // 2] - m[len(m) // 2])
        st["p90"].append(a[int(0.9 * len(a))] - m[int(0.9 * len(m))])
        st["trim"].append(S.mean(a[:int(0.99 * len(a))]) - S.mean(m[:int(0.99 * len(m))]))
    out["bootstrap_with_prior"] = {k: {"mean": S.mean(v), "ci95": [sorted(v)[50], sorted(v)[1949]]} for k, v in st.items()}
    for name, cond in (("serviced_since_last_lab", lambda r: r["i"] >= 1 and r["serviced_since_last_lab"]),
                       ("not_serviced", lambda r: r["i"] >= 1 and not r["serviced_since_last_lab"])):
        idx = [j for j, r in enumerate(rows) if cond(r)]
        out[name] = {"practice": summary([err["practice"][j] for j in idx]), "anchored": summary([err["anchored"][j] for j in idx]),
                     "paired": sign([err["anchored"][j] for j in idx], [err["practice"][j] for j in idx])}
    out["by_lab_band"] = {}
    for lo, hi in ((0, 0.2), (0.2, 1.0), (1.0, 3.0), (3.0, 1e9)):
        idx = [j for j, r in enumerate(rows) if r["i"] >= 1 and lo <= r["lab"] < hi]
        out["by_lab_band"]["%g-%g" % (lo, hi)] = {
            "practice": summary([err["practice"][j] for j in idx]), "anchored": summary([err["anchored"][j] for j in idx]),
            "paired": sign([err["anchored"][j] for j in idx], [err["practice"][j] for j in idx]),
            "under_read_anchored": sum(1 for j in idx if rows[j]["anchored"] < rows[j]["lab"]),
            "under_read_practice": sum(1 for j in idx if rows[j]["practice"] < rows[j]["lab"])}
    out["alarms"] = {}
    for T in (0.6, 1.0, 2.0):
        idx = [j for j, r in enumerate(rows) if r["i"] >= 1]
        d = {"lab_exceed": sum(1 for j in idx if rows[j]["lab"] > T), "lab_below": sum(1 for j in idx if rows[j]["lab"] <= T)}
        for h in ("sonde", "practice", "anchored"):
            d[h] = {"false_alarms": sum(1 for j in idx if rows[j][h] > T and rows[j]["lab"] <= T),
                    "missed": sum(1 for j in idx if rows[j][h] <= T and rows[j]["lab"] > T)}
        out["alarms"]["%g" % T] = d
    core.dump("e5_anchor.json", out)
    core.dump("e5_rows.json", rows)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
