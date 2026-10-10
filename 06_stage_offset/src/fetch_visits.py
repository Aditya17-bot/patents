"""Sequentially cache ratings and field visits for the targets of coupled pairs (the open
field-measurement API allows 1,000 requests an hour; the client waits on HTTP 429)."""
import json
import os
import sys

import usgs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(ROOT, "results", "coupling.json")))
th = float(sys.argv[1]) if len(sys.argv) > 1 else 0.9
targets = []
for x, y, incr, lag, lr, c in rows:
    if c >= th:
        for s in (x, y):
            if s not in targets:
                targets.append(s)
print(len(targets), "sites", flush=True)
for i, s in enumerate(targets):
    usgs.rating(s, "exsa")
    v = usgs.field_visits(s)
    print(i, s, len(v), flush=True)
