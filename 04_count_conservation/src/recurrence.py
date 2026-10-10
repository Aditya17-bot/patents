"""Are the recovered relations that the survey cannot confirm real, or artefacts?

A relation recovered in March that the surveyed map does not contain is either a genuine
conservation relation the survey omits, or a chance combination that happened to pass
the retention test on that month's counts. The two can be told apart without ground
truth: a physical relation holds in every month, a chance one does not. So discover2 is
run, unchanged, on each later month of the same corridor (April, May, June 2025), and
every March relation is checked for exact recurrence (same detectors by site identifier,
same signs, up to overall sign).

The recurrence rate of March relations the survey confirms exactly is the reference
rate for a relation known to be real. The question is whether the unconfirmed categories
recur at a comparable rate. Writes results/recurrence.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset, discover, discover2, evaluate
from discovery_v2_eval import categorise

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CORRIDORS = (("M25", "window_full_M25_A.json",
              ("window_apr_M25_A.json", "window_may_M25_A.json", "window_june_M25_A.json")),
             ("M1", "window_M1_A.json",
              ("window_apr_M1_A.json", "window_may_M1_A.json", "window_june_M1_A.json")))


def site_key(rel, site_ids):
    items = tuple(sorted((site_ids[r], c) for r, c in rel.items()))
    flip = tuple(sorted((site_ids[r], -c) for r, c in rel.items()))
    return min(items, flip)


def recovered(manifest):
    cache = os.path.join(RESULTS, "recovered_month_%s" % manifest.replace("window_", ""))
    c = dataset.load(manifest)
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as fh:
            rels = [{int(r): int(v) for r, v in x.items()} for x in json.load(fh)]
    else:
        found, _ = discover2.discover(c.volumes, c.observed)
        rels = [{int(r): int(v) for r, v in f["rows"].items()} for f in found]
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump([{str(r): v for r, v in x.items()} for x in rels], fh)
    return c, rels


def one_category(rel, truth, n):
    cats, _ = categorise([rel], truth, n)
    return next(iter(cats))


def main():
    out = {"corridors": {}}
    for name, march, later in CORRIDORS:
        c, rels = recovered(march)
        truth = discover.truth_relations(c, evaluate.fit_node_signs(c))
        later_keys = []
        for m in later:
            cm, rm = recovered(m)
            later_keys.append({site_key(r, cm.site_ids) for r in rm})
            print(name, m, len(rm), "relations", flush=True)
        by = {}
        for r in rels:
            cat = one_category(r, truth, c.shape[0])
            k = site_key(r, c.site_ids)
            hits = sum(k in ks for ks in later_keys)
            d = by.setdefault(cat, {"relations": 0, "recur_in_all_3": 0, "recur_in_any": 0,
                                    "months_recurring_total": 0})
            d["relations"] += 1
            d["recur_in_all_3"] += int(hits == len(later_keys))
            d["recur_in_any"] += int(hits > 0)
            d["months_recurring_total"] += hits
        for d in by.values():
            d["share_recur_all_3"] = round(d["recur_in_all_3"] / d["relations"], 4)
            d["share_recur_any"] = round(d["recur_in_any"] / d["relations"], 4)
            d["mean_months_recurring"] = round(d["months_recurring_total"] / d["relations"], 3)
        out["corridors"][name] = {"march_relations": len(rels), "by_category": by}
        print(name, json.dumps(by, indent=1), flush=True)
    with open(os.path.join(RESULTS, "recurrence.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
