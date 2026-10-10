"""Feasibility probe: raw sonde conductivity against laboratory conductivity.

For each paired site, the sonde reading closest to each lab sample (within MATCH_MIN)
gives r = ln(sonde / lab). Service events are found from the raw record itself: a gap
longer than GAP_H hours (sonde removed or swapped). The probe reports the spread of r,
whether r drifts with time since the last service, and how big the step in the record is
across services. Output: results/probe_error.json
"""
import datetime as dt
import json
import math
import os
import statistics as S
from concurrent.futures import ThreadPoolExecutor

import ea

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "probe_error.json")
MATCH_MIN = 30
GAP_H = 6


def site(s):
    m = s["station"] + "-cond-i-subdaily-uS"
    try:
        rd = ea.readings(m, s["opened"], s["closed"])
    except Exception as e:
        return {"station": s["station"], "error": str(e)}
    rd = [r for r in rd if r[1] > 0]
    if len(rd) < 1000:
        return {"station": s["station"], "n_readings": len(rd)}
    times = [r[0] for r in rd]
    # service events: gaps in the raw record
    serv = [times[0]] + [times[i] for i in range(1, len(times))
                         if (times[i] - times[i - 1]).total_seconds() > GAP_H * 3600]
    labs = ea.samples(s["point"], "0077")
    import bisect
    rows = []
    for t, v, *_ in labs:
        if v <= 0:
            continue
        i = bisect.bisect_left(times, t)
        best = None
        for j in (i - 1, i):
            if 0 <= j < len(times):
                d = abs((times[j] - t).total_seconds()) / 60
                if d <= MATCH_MIN and (best is None or d < best[0]):
                    best = (d, rd[j][1])
        if best is None:
            continue
        k = bisect.bisect_right(serv, t) - 1
        nxt = serv[k + 1] if k + 1 < len(serv) else None
        rows.append({"t": t.isoformat(), "lab": v, "sonde": best[1], "r": math.log(best[1] / v),
                     "since_service_d": (t - serv[k]).total_seconds() / 86400,
                     "interval_d": ((nxt - serv[k]).total_seconds() / 86400) if nxt else None})
    return {"station": s["station"], "label": s["label"], "n_readings": len(rd),
            "n_services": len(serv), "rows": rows}


def main():
    sites = json.load(open(os.path.join(ROOT, "results", "sites.json")))
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(site, sites))
    json.dump(res, open(OUT, "w"), indent=1, default=str)
    allr = []
    for r in res:
        rows = r.get("rows") or []
        if len(rows) < 5:
            continue
        rs = [x["r"] for x in rows]
        med = S.median(rs)
        dev = [x["r"] - med for x in rows]          # remove a constant site factor (reference temperature, cell constant)
        # drift with time since service: slope of deviation on days since service
        xs = [x["since_service_d"] for x in rows]
        mx = S.mean(xs)
        sxx = sum((a - mx) ** 2 for a in xs) or 1
        slope = sum((a - mx) * b for a, b in zip(xs, dev)) / sxx
        allr.append((r["station"], len(rows), r["n_services"], med, S.median([abs(d) for d in dev]),
                     slope * 30))
        for x, d in zip(rows, dev):
            x["dev"] = d
    print("sites with >= 5 matches:", len(allr))
    print("station  n  services  median ln(sonde/lab)  median |dev|  slope per 30 d")
    for a in sorted(allr, key=lambda a: -a[1])[:40]:
        print("%-9s %4d %5d  %+.3f  %.3f  %+.4f" % a)
    devs = [abs(x["dev"]) for r in res for x in (r.get("rows") or []) if "dev" in x]
    devs.sort()
    n = len(devs)
    print("all matched: n=%d  median |dev| %.3f  p90 %.3f" % (n, devs[n // 2], devs[int(0.9 * n)]))
    # pooled: |dev| by time since service bins
    bins = [(0, 7), (7, 14), (14, 28), (28, 56), (56, 9999)]
    for a, b in bins:
        v = sorted(abs(x["dev"]) for r in res for x in (r.get("rows") or [])
                   if "dev" in x and a <= x["since_service_d"] < b)
        if v:
            print("since service %3d-%4d d: n=%4d median |dev| %.3f  mean dev %+.3f" % (
                a, b, len(v), v[len(v) // 2],
                S.mean(x["dev"] for r in res for x in (r.get("rows") or []) if "dev" in x and a <= x["since_service_d"] < b)))


if __name__ == "__main__":
    main()
