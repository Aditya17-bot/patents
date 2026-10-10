"""Cache the 15-minute series needed by E7 for the directions scored in E1."""
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import usgs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
e1 = json.load(open(os.path.join(ROOT, "results", "e1_interpolation.json")))
dirs = sorted({(q["x"], q["y"]) for q in e1["records"]})
jobs = set()
for x, y in dirs:
    jobs |= {(x, "00065"), (x, "00060"), (y, "00060")}
jobs = sorted(jobs)
print(len(jobs), "series", flush=True)


def go(j):
    try:
        usgs.iv(j[0], j[1], "2023-10-01", "2026-09-30")
        return j, "ok"
    except Exception as e:
        return j, "ERR %s" % e


with ThreadPoolExecutor(6) as ex:
    for i, f in enumerate(as_completed([ex.submit(go, j) for j in jobs])):
        print(i, *f.result(), flush=True)
