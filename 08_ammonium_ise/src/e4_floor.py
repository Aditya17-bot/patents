"""E4 (probe): estimate the sonde's calibration offset from the floor of its own record.

Between pollution pulses river ammonium falls back to a low background that varies little
between rivers, while an ISE's calibration offset varies widely between deployments. So
    offset ~ (low quantile of the sonde readings over the preceding FLOOR_DAYS) - background
where the background is the median, over the other sites, of the low quantile of their
laboratory results (leave one site out). Compared at every matched laboratory sample with:
raw reading; network constant (mean departure of the other sites, the fair baseline of E2).
Output: results/e4_floor.json
"""
import bisect
import json
import math
import os
import statistics as S
import datetime as dt

import core
import ea
from e2_coldstart import sign, summary

FLOOR_DAYS = float(os.environ.get("FLOOR_DAYS", 7))
Q = float(os.environ.get("FLOOR_Q", 0.05))


def quant(v, q):
    v = sorted(v)
    return v[int(q * (len(v) - 1))]


def main():
    sites = core.load_sites()
    data = {}
    for s in sites:
        try:
            smp = core.site_samples(s)
            amm = [r for r in ea.readings(s["station"] + "-amm-i-subdaily-mgL", s["opened"], s["closed"]) if r[1] >= 0]
        except Exception:
            continue
        if len(smp) >= 3:
            data[s["station"]] = (smp, [r[0] for r in amm], [r[1] for r in amm])
    keys = sorted(data)
    labq = {k: quant([x["lab"] for x in data[k][0]], 0.10) for k in keys}
    rows = []
    for held in keys:
        smp, at, av = data[held]
        bg = S.median(labq[k] for k in keys if k != held)
        deps = sorted(x["sonde"] - x["lab"] for k in keys if k != held for x in data[k][0])
        lo, hi = deps[int(0.01 * len(deps))], deps[int(0.99 * len(deps)) - 1]
        cmean = S.mean(d for d in deps if lo <= d <= hi)
        for x in smp:
            i1 = bisect.bisect_right(at, x["t"])
            i0 = bisect.bisect_left(at, x["t"] - dt.timedelta(days=FLOOR_DAYS))
            win = av[i0:i1]
            if len(win) < 96:                 # at least one day of 15-minute readings
                continue
            floor = quant(win, Q)
            rows.append({"station": held, "lab": x["lab"], "sonde": x["sonde"], "sc": x["sc"],
                         "raw": x["sonde"], "net_mean": max(x["sonde"] - cmean, 0.0),
                         "floor": max(x["sonde"] - (floor - bg), 0.0), "floor_value": floor, "bg": bg})
    err = {h: [abs(r[h] - r["lab"]) for r in rows] for h in ("raw", "net_mean", "floor")}
    per = {}
    for r in rows:
        per.setdefault(r["station"], []).append(r)
    out = {"floor_days": FLOOR_DAYS, "q": Q, "sites": len(per), "samples": len(rows),
           "all": {h: summary(v) for h, v in err.items()},
           "paired_vs_raw": sign(err["floor"], err["raw"]),
           "paired_vs_net_mean": sign(err["floor"], err["net_mean"]),
           "sites_better_than_net_mean": sum(1 for v in per.values()
                                             if S.mean(abs(r["floor"] - r["lab"]) for r in v) < S.mean(abs(r["net_mean"] - r["lab"]) for r in v))}
    import random
    rng = random.Random(3)
    ks = sorted(per)
    st = {"median": [], "p90": [], "trim": []}
    for _ in range(2000):
        pick = [rng.choice(ks) for _ in ks]
        a = sorted(abs(r["net_mean"] - r["lab"]) for k in pick for r in per[k])
        m = sorted(abs(r["floor"] - r["lab"]) for k in pick for r in per[k])
        st["median"].append(a[len(a) // 2] - m[len(m) // 2])
        st["p90"].append(a[int(0.9 * len(a))] - m[int(0.9 * len(m))])
        st["trim"].append(S.mean(a[:int(0.99 * len(a))]) - S.mean(m[:int(0.99 * len(m))]))
    out["bootstrap_vs_net_mean"] = {k: {"mean": S.mean(v), "ci95": [sorted(v)[50], sorted(v)[1949]]} for k, v in st.items()}
    sub = [r for r in rows if r["station"] != "E01566A"]
    out["without_E01566A"] = {"paired_vs_net_mean": sign([abs(r["floor"] - r["lab"]) for r in sub], [abs(r["net_mean"] - r["lab"]) for r in sub]),
                              "net_mean": summary([abs(r["net_mean"] - r["lab"]) for r in sub]),
                              "floor": summary([abs(r["floor"] - r["lab"]) for r in sub])}
    core.dump("e4_floor_%gd_q%g.json" % (FLOOR_DAYS, Q) if (FLOOR_DAYS, Q) != (7.0, 0.05) else "e4_floor.json", out)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
