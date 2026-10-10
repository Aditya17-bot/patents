"""09 screen probe: raw sonde dissolved-oxygen saturation against field measurements (EA 9901).

Reports the error distribution (sonde % sat - field % sat) at matched instants, its growth with
time since the sonde's last service (gap in the record), and the share of large errors.
Output: results/probe_do.json (in the 08 project, reusing its cached EA data)
"""
import bisect
import json
import statistics as S

import core
import ea


def main():
    rows = []
    for s in core.load_sites():
        try:
            do = [r for r in ea.readings(s["station"] + "-do-i-subdaily-pct", s["opened"], s["closed"]) if 0 < r[1] < 300]
            lab = ea.samples(s["point"], "9901")
        except Exception:
            continue
        if len(do) < 500:
            continue
        t = [r[0] for r in do]
        v = [r[1] for r in do]
        serv = [t[0]] + [t[i] for i in range(1, len(t)) if (t[i] - t[i - 1]).total_seconds() > 6 * 3600]
        for ts, val, *_ in lab:
            if not (s["opened"] <= ts.date().isoformat() <= s["closed"]):
                continue
            x = core.nearest(t, v, ts, 30)
            if x is None or abs(x - val) < 1e-6:
                continue
            k = bisect.bisect_right(serv, ts) - 1
            rows.append({"station": s["station"], "field": val, "sonde": x, "err": x - val,
                         "since_service_d": (ts - serv[k]).total_seconds() / 86400})
    e = sorted(abs(r["err"]) for r in rows)
    n = len(e)
    out = {"sites": len({r["station"] for r in rows}), "n": n, "median_abs": e[n // 2], "p90_abs": e[int(0.9 * n)],
           "share_over_10pp": sum(1 for x in e if x > 10) / n, "median_signed": S.median(r["err"] for r in rows)}
    bins = [(0, 7), (7, 21), (21, 42), (42, 1e9)]
    out["by_age"] = {"%g-%g" % b: {"n": len(sub), "median_abs": sorted(abs(r["err"]) for r in sub)[len(sub) // 2],
                                   "median_signed": S.median(r["err"] for r in sub)}
                     for b in bins for sub in [[r for r in rows if b[0] <= r["since_service_d"] < b[1]]] if sub}
    core.dump("probe_do.json", out)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
