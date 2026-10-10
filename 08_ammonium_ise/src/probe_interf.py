"""Probe: does a conductivity-scaled interference term correct the ammonium sonde?

Model (Nikolsky-Eisenman, linearised): reported = true + k * SC + b, with SC the sonde's own
conductivity at the same instant standing in for the interfering cations (Na+, K+).
Per site, samples are ordered in time; k and b are fitted on the first half and scored on
the second half against the lab result. Baselines: raw sonde; offset only (b = median of
first-half over-read). Error: absolute error in mg/L N and its log ratio.
Output: results/probe_interf.json
"""
import bisect
import datetime as dt
import json
import math
import os
import statistics as S

import ea

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "probe_interf.json")


def fit(xs, ys):
    """Least-squares y = k x + b; falls back to offset only when x has no spread."""
    mx, my = S.mean(xs), S.mean(ys)
    sxx = sum((a - mx) ** 2 for a in xs)
    if sxx == 0:
        return 0.0, S.median(ys)
    k = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / sxx
    return k, my - k * mx


def main():
    sites = {s["station"]: s for s in json.load(open(os.path.join(ROOT, "results", "sites.json")))}
    amm = json.load(open(os.path.join(ROOT, "results", "probe_amm.json")))
    out, pooled = [], {"raw": [], "offset": [], "interf": []}
    for r in amm:
        rows = r.get("rows") or []
        if len(rows) < 12:
            continue
        s = sites[r["station"]]
        cond = ea.readings(s["station"] + "-cond-i-subdaily-uS", s["opened"], s["closed"])
        ct = [c[0] for c in cond]
        data = []
        for x in rows:
            t = dt.datetime.fromisoformat(x["t"])
            i = bisect.bisect_left(ct, t)
            if i < len(ct) and abs((ct[i] - t).total_seconds()) <= 3600:
                data.append((t, x["lab"], x["sonde"], cond[i][1]))
        data.sort()
        if len(data) < 12:
            continue
        h = len(data) // 2
        tr, te = data[:h], data[h:]
        b0 = S.median(x[2] - x[1] for x in tr)
        k, b = fit([x[3] for x in tr], [x[2] - x[1] for x in tr])
        e = {"raw": [], "offset": [], "interf": []}
        for t, lab, son, sc in te:
            e["raw"].append(abs(son - lab))
            e["offset"].append(abs(son - b0 - lab))
            e["interf"].append(abs(max(son - (k * sc + b), 0.0) - lab))
        for key in e:
            pooled[key] += e[key]
        out.append({"station": s["station"], "n_test": len(te), "k_per_1000uS": 1000 * k, "b": b,
                    "mae": {key: S.mean(v) for key, v in e.items()},
                    "median": {key: S.median(v) for key, v in e.items()}})
    better = sum(1 for o in out if o["mae"]["interf"] < o["mae"]["offset"])
    print("sites", len(out), "test samples", len(pooled["raw"]))
    for key, v in pooled.items():
        v = sorted(v)
        print("%-7s mean %.3f  median %.3f  p90 %.3f mg/L" % (key, S.mean(v), v[len(v) // 2], v[int(0.9 * len(v))]))
    print("sites where interference term beats offset-only (MAE):", better, "of", len(out))
    for o in sorted(out, key=lambda o: -o["n_test"])[:20]:
        print("%-9s n=%3d k=%+.3f mg/L per 1000 uS  raw %.3f  offset %.3f  interf %.3f" % (
            o["station"], o["n_test"], o["k_per_1000uS"], o["mae"]["raw"], o["mae"]["offset"], o["mae"]["interf"]))
    json.dump({"sites": out, "pooled": {k: sorted(v) for k, v in pooled.items()}}, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
