"""Parse every cached site-month used by the experiments into data/series/ (run once)."""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pairs
import series

ids = set()
for road in ("M25", "M1"):
    for up, down, _ in pairs.candidates(road):
        ids.add(up)
        ids.add(down)
jobs = [(i, m) for i in sorted(ids) for m in series.MONTHS]
print("site-months to parse: %d" % len(jobs))
with ThreadPoolExecutor(4) as pool:
    list(pool.map(lambda j: series.load(*j), jobs))
print("done")
