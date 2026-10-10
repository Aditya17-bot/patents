"""Worked examples of faults reported on unmodified counts, for the disclosure.

For a named detector: its daily mean count against each of its two tightest partners
(the detectors whose counts agreed with it most closely over the first half of March),
the partners against each other, the first day of March it stopped reporting, and its
share of absent records in April-June. Writes results/real_fault_examples.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset, webtris
from real_faults_followup import MONTHS, monthly_missing

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
EXAMPLES = (("window_M1_A.json", "M1/4669A"), ("window_full_M25_A.json", "M25/5814A"))


def example(manifest, name):
    c = dataset.load(manifest)
    with open(os.path.join(ROOT, "data", "webtris", "sites.json"), encoding="utf-8") as fh:
        desc = {str(s["Id"]): s["Description"] for s in json.load(fh)["sites"]}
    r = [i for i, s in enumerate(c.site_ids) if desc.get(str(s)) == name][0]
    ref = np.arange(c.shape[1] // 2)
    scores = []
    for j in range(c.shape[0]):
        if j == r:
            continue
        m = c.observed[r, ref] & c.observed[j, ref]
        if m.sum() < 400:
            continue
        x, y = c.volumes[r, ref][m], c.volumes[j, ref][m]
        scores.append((float(np.median(np.abs(x - y))) / max(x.mean(), y.mean()), j))
    scores.sort()
    a, b = scores[0][1], scores[1][1]
    dates = sorted({k[0] for k in c.keys})
    days = []
    first_absent = None
    for d in dates:
        cols = [j for j, k in enumerate(c.keys) if k[0] == d]

        def mean(i):
            v = c.volumes[i, cols][c.observed[i, cols]]
            return float(v.mean()) if v.size > 0.5 * len(cols) else None
        mr, ma, mb = mean(r), mean(a), mean(b)
        if mr is None and first_absent is None and d > dates[0]:
            first_absent = d
        days.append({"date": d,
                     "detector_over_partner_a": round(mr / ma, 4) if mr and ma else None,
                     "detector_over_partner_b": round(mr / mb, 4) if mr and mb else None,
                     "partner_a_over_partner_b": round(ma / mb, 4) if ma and mb else None})
    return {"detector": name, "partners": [desc.get(str(c.site_ids[a])),
                                            desc.get(str(c.site_ids[b]))],
            "first_day_absent": first_absent,
            "apr_jun_absent_share": monthly_missing(c.site_ids[r]), "days": days}


def main():
    out = {e[1]: example(*e) for e in EXAMPLES}
    with open(os.path.join(RESULTS, "real_fault_examples.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    for k, v in out.items():
        print(k, v["partners"], v["first_day_absent"], v["apr_jun_absent_share"])
        for d in v["days"]:
            print("  ", d)


if __name__ == "__main__":
    main()
