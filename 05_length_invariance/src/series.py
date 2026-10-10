"""Per-site 15-minute series of length-class counts, total volume and average speed.

WebTRIS daily reports are paged JSON, about 3,000 rows a month per site. Reading them for
every experiment is slow, so each site-month is parsed once into a compact form and
written to data/series/. Blank fields stay blank: a slot is kept only if every length bin,
the total and the average speed were all reported.

A slot is identified by its day of the month and its 15-minute index within the day
(0-95), both taken from the report itself.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import webtris

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERIES = os.path.join(ROOT, "data", "series")

LENGTH_BINS = ["0 - 520 cm", "521 - 660 cm", "661 - 1160 cm", "1160+ cm"]
# Upper edge, in centimetres, of each length bin but the last. The share of vehicles
# below an edge is what the method compares between detectors.
EDGES_CM = [520, 660, 1160]

MONTHS = {
    "2025-03": ("01032025", "31032025"),
    "2025-04": ("01042025", "30042025"),
    "2025-05": ("01052025", "31052025"),
    "2025-06": ("01062025", "30062025"),
}


def _parse(rows):
    out = {}
    for r in rows:
        try:
            bins = [int(r[k]) for k in LENGTH_BINS]
            total = int(r["Total Volume"])
            speed = float(r["Avg mph"])
            day = int(r["Report Date"][8:10])
            slot = int(r["Time Interval"])
        except (KeyError, TypeError, ValueError):
            continue
        out["%d_%d" % (day, slot)] = [bins, total, speed]
    return out


def load(site_id, month):
    """{'day_slot': [[n0, n1, n2, n3], total, avg_mph]} for one site and month."""
    os.makedirs(SERIES, exist_ok=True)
    path = os.path.join(SERIES, "%s_%s.json" % (site_id, month))
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    start, end = MONTHS[month]
    data = _parse(webtris.daily(site_id, start, end))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, separators=(",", ":"))
    return data


def share_below(bins, total):
    """Share of vehicles below each edge in EDGES_CM, from one record's bin counts."""
    below = 0
    shares = []
    for n in bins[:-1]:
        below += n
        shares.append(below / total)
    return shares
