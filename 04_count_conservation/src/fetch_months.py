"""Write per-month manifests from the March windows and prefetch their counts.

Same site lists and topology files as March; only the dates change. Every response is
cached by webtris.py, so this runs once. A small thread pool is used because the service
answers one page at a time; six concurrent requests is the ceiling used here.
"""
import calendar
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import webtris

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
WORKERS = 6


def month_range(year, month):
    last = calendar.monthrange(year, month)[1]
    return "01%02d%d" % (month, year), "%02d%02d%d" % (last, month, year)


def manifest(base, tag, year, month):
    with open(os.path.join(RESULTS, base), encoding="utf-8") as fh:
        m = json.load(fh)
    m["start"], m["end"] = month_range(year, month)
    name = "window_%s.json" % tag
    with open(os.path.join(RESULTS, name), "w", encoding="utf-8") as fh:
        json.dump(m, fh)
    return name, m


def prefetch(sites, start, end):
    def one(sid):
        try:
            return sid, len(webtris.daily(sid, start, end))
        except Exception as e:           # noqa: BLE001 - report and carry on
            return sid, "error %s" % e
    with ThreadPoolExecutor(WORKERS) as ex:
        return list(ex.map(one, sites))


def sites_of(names, start, end):
    """Prefetch arbitrary site ids for one month (used for outcome months)."""
    return prefetch(list(names), start, end)


PLAN = (("window_full_M25_A.json", "apr_M25_A", 2025, 4),
        ("window_full_M25_A.json", "may_M25_A", 2025, 5),
        ("window_M1_A.json", "apr_M1_A", 2025, 4),
        ("window_M1_A.json", "may_M1_A", 2025, 5),
        ("window_M1_A.json", "june_M1_A", 2025, 6))

if __name__ == "__main__":
    for base, tag, y, mo in PLAN:
        name, m = manifest(base, tag, y, mo)
        res = prefetch(m["site_ids"], m["start"], m["end"])
        bad = [r for r in res if not isinstance(r[1], int)]
        print("%s: %d sites fetched, %d errors" % (name, len(res), len(bad)), flush=True)
        for r in bad[:5]:
            print("   ", r, flush=True)
