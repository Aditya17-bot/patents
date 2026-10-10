"""Pair admission data: travel-time lag and coupling for every direction of every pair.

For each candidate pair from network.py and each direction (target X, reference Y): the
lag in whole days (-2..+2) maximising the correlation of daily changes of ln Q, and the
coupling = correlation of daily ln Q after the lag, over water years 2021-2026.

Output: results/coupling.json  [[x, y, incr, lag_days, lag_corr, coupling], ...]
"""
import json
import math
import os

import numpy as np

import probe_daily as pd
import usgs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    P = json.load(open(os.path.join(ROOT, "results", "pairs.json")))
    sites = sorted({s for p in P["pairs"] for s in (p["up"], p["down"])})
    DV = usgs.dv(sites, pd.START, pd.END, stats=("00003",))
    rows = []
    for p in P["pairs"]:
        for x, y in ((p["down"], p["up"]), (p["up"], p["down"])):
            qx, qy = pd.series(DV, x, "00060"), pd.series(DV, y, "00060")
            hx = pd.series(DV, x, "00065")
            if len(qx) < 400 or len(qy) < 400 or len(hx) < 400:
                continue
            lag, lr = pd.lag_days(qx, qy)
            a = [(math.log(qx[d]), math.log(qy[pd.shift_day(d, -lag)])) for d in qx
                 if pd.shift_day(d, -lag) in qy and qx[d] > 0 and qy[pd.shift_day(d, -lag)] > 0]
            if len(a) < 300:
                continue
            c = float(np.corrcoef(np.array(a).T)[0, 1])
            rows.append((x, y, p["incr"], lag, round(lr, 3), round(c, 4)))
    rows.sort(key=lambda r: -r[5])
    json.dump(rows, open(os.path.join(ROOT, "results", "coupling.json"), "w"))
    for th in (0.9, 0.95, 0.98):
        print(th, sum(1 for r in rows if r[5] >= th), "directions")


if __name__ == "__main__":
    main()
