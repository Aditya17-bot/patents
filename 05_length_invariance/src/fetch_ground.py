"""Fetch the WebTRIS records needed for E11: mainline sites of both carriageways within
WINDOW_M of each DfT manual count point, for the month of the count (March-June 2025).

One request per site-month (page_size 5000 returns the whole month). Every response is
cached by webtris.py under data/webtris/, then parsed once into data/series/.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corridor
import e11_ground_truth as e11
import series
import webtris

WINDOW_M = 8000


def main():
    todo = set()
    for road in ("M25", "M1"):
        counts = e11.manual_counts(road)
        for cw in ("A", "B"):
            mains = [s for s in corridor.corridor_sites(road, cw) if s["role"] == "mainline"]
            for c in counts:
                for s in mains:
                    if corridor.haversine_m(c["lat"], c["lon"], s["lat"], s["lon"]) <= WINDOW_M:
                        todo.add((s["id"], c["date"][:7]))
    todo = sorted(todo)
    need = [(sid, m) for sid, m in todo
            if not os.path.exists(os.path.join(series.SERIES, "%s_%s.json" % (sid, m)))]
    print("site-months in windows", len(todo), "to fetch", len(need), flush=True)
    def one(item):
        sid, m = item
        start, end = series.MONTHS[m]
        webtris.daily(sid, start, end, page_size=5000)
        series.load(sid, m)

    # six requests at a time; each response is cached, so a rerun resumes
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i, _ in enumerate(pool.map(one, need)):
            if i % 100 == 0:
                print(i, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
