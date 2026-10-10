"""Processing time of the full method for one station direction over the study period."""
import json
import os
import time

import numpy as np

import probe_daily as pd
import usgs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "results", "daily.json")))
dirs = [(r["x"], r["y"]) for r in d["results"] if r.get("rows")][:10]
sites = sorted({s for xy in dirs for s in xy})
DV = usgs.dv(sorted({s for p in json.load(open(os.path.join(ROOT, "results", "pairs.json")))["pairs"]
                     for s in (p["up"], p["down"])}), pd.START, pd.END, stats=("00003",))
secs, years, days_used = [], [], []
pd.INJ = ()
for x, y in dirs:
    t = time.perf_counter()
    r = pd.run(x, y, DV)
    secs.append(time.perf_counter() - t)
    years.append(6.0)
    days_used.append(len(r.get("rows", [])))
out = {"directions": len(dirs), "seconds_per_direction_median": round(float(np.median(secs)), 3),
       "seconds_per_direction_max": round(float(np.max(secs)), 3),
       "years_per_direction": 6.0,
       "ms_per_station_day": round(1000 * float(np.median(secs)) / (6 * 365.25), 3),
       "note": "full re-computation of all windows, lags and visit estimates of one target-reference "
               "direction over water years 2021-2026 on one CPU core (Python, cached inputs)"}
json.dump(out, open(os.path.join(ROOT, "results", "e6_timing.json"), "w"), indent=1)
print(out)
