"""Fetch and cache every series the experiments need (parallel, with progress)."""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import usgs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(ROOT, "results", sys.argv[1] if len(sys.argv) > 1 else "pairs.json")))
start, end = P["start"], P["end"]
sites = sorted({s for p in P["pairs"] for s in (p["up"], p["down"])})
jobs = []
for s in sites:
    jobs += [("iv", s, "00060"), ("iv", s, "00065"), ("fv", s, None), ("rt", s, None)]


def go(j):
    k, s, p = j
    t = time.time()
    try:
        if k == "iv":
            usgs.iv(s, p, start, end)
        elif k == "fv":
            usgs.field_visits(s)
        else:
            usgs.rating(s, "exsa")
        return j, "ok", time.time() - t
    except Exception as e:
        return j, "ERR %s" % e, time.time() - t


done = 0
with ThreadPoolExecutor(int(os.environ.get("THREADS", "6"))) as ex:
    futs = [ex.submit(go, j) for j in jobs]
    for f in as_completed(futs):
        j, st, dt_ = f.result()
        done += 1
        print(done, len(jobs), j, st, round(dt_, 1), flush=True)
