"""Fetch and cache one month of 15-minute data for a slip-dense window of a corridor.

Run this once; webtris.py caches every response to data/webtris/, so the analysis in
phase2.py reads from disk and never re-hits the service.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import webtris

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

# Slip-dense stretch of the M25 clockwise carriageway, chosen in Phase 1.
WINDOW_NODES = 45
START = "01032025"
END = "31032025"


def window(road="M25", carriageway="A", n_nodes=WINDOW_NODES):
    """The contiguous run of nodes carrying the most slip roads."""
    path = os.path.join(RESULTS, "nodes_%s_%s.json" % (road, carriageway))
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    nodes = [n for n in data["nodes"] if n["usable"]]

    best_i, best_k = 0, -1
    for i in range(max(1, len(nodes) - n_nodes)):
        k = sum(1 for n in nodes[i:i + n_nodes] if n["slips"])
        if k > best_k:
            best_i, best_k = i, k
    return nodes[best_i:best_i + n_nodes]


def site_ids(nodes):
    ids = []
    seen = set()
    for n in nodes:
        for sid in [n["upstream"]["id"], n["downstream"]["id"]] + [s["id"] for s in n["slips"]]:
            if sid not in seen:
                seen.add(sid)
                ids.append(sid)
    return ids


def main(road="M25", carriageway="A", start=START, end=END,
         n_nodes=WINDOW_NODES, manifest_name="window.json"):
    nodes = window(road, carriageway, n_nodes)
    ids = site_ids(nodes)
    print("window: %s %s, %d nodes, %d sites, %s..%s"
          % (road, carriageway, len(nodes), len(ids), start, end))

    t0 = time.time()
    for i, sid in enumerate(ids, 1):
        rows = webtris.daily(sid, start, end)
        print("  [%3d/%3d] site %-6s rows=%d  (%.0fs elapsed)"
              % (i, len(ids), sid, len(rows), time.time() - t0), flush=True)

    manifest = {"road": road, "carriageway": carriageway,
                "start": start, "end": end,
                "node_ids": [n["node_id"] for n in nodes], "site_ids": ids}
    with open(os.path.join(RESULTS, manifest_name), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print("done in %.0fs" % (time.time() - t0))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "full":
        # Whole carriageway. Slow (~5.5 s per site), so run it in the background.
        road = a[1] if len(a) > 1 else "M25"
        cw = a[2] if len(a) > 2 else "A"
        main(road, cw, n_nodes=10 ** 6,
             manifest_name="window_full_%s_%s.json" % (road, cw))
    else:
        main()
