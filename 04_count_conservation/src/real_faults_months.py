"""The unmodified-counts study of real_faults.py, repeated over March to June 2025.

Each corridor-month is treated exactly as March was: relations recovered from the first
half of the month (no map), thresholds from that half, the second half scanned in 2-day
spans, a detector reported only when every one of its relations (>= 2) deviates. The
outcome is then read from months the method never saw: whether the detector stopped
reporting (a month >= 95 % absent) in any of the three months after the scanned month.

Both groups are admitted by one rule judged before any report: >= 90 % of records present
in the reference half of the scanned month. Controls: CONTROLS detectors drawn at random
per corridor-month from the admitted, unreported detectors.

Two poolings are reported: per corridor-month (a detector reported in two months counts
twice, as do controls drawn twice), and per detector (a detector counts once, as
reported if it was ever reported, its outcome read after its first report; controls are
detectors never reported, outcome read after their first control month).
Writes results/real_faults_months.json.
"""
import json
import os
import sys

import numpy as np
from scipy.stats import fisher_exact

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset, real_faults, webtris
from fetch_months import month_range, prefetch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
CONTROLS = 40
RUNS = (("M25", 3, "window_full_M25_A.json", "full_M25_A"),
        ("M25", 4, "window_apr_M25_A.json", "apr_M25_A"),
        ("M25", 5, "window_may_M25_A.json", "may_M25_A"),
        ("M25", 6, "window_june_M25_A.json", "june_M25_A"),
        ("M1", 3, "window_M1_A.json", "M1_A"),
        ("M1", 4, "window_apr_M1_A.json", "apr_M1_A"),
        ("M1", 5, "window_may_M1_A.json", "may_M1_A"),
        ("M1", 6, "window_june_M1_A.json", "june_M1_A"))


def absent_share(sid, year, month):
    s, e = month_range(year, month)
    rows = webtris.daily(sid, s, e)
    if not rows:
        return 1.0
    return sum(1 for r in rows if r.get("Total Volume") in ("", None)) / len(rows)


def failed_after(sid, month):
    shares = [absent_share(sid, 2025, m) for m in (month + 1, month + 2, month + 3)]
    return any(v >= 0.95 for v in shares), [round(v, 4) for v in shares]


def main():
    units = []
    per_run = []
    for road, month, manifest, tag in RUNS:
        s, e = month_range(2025, month)
        path = os.path.join(RESULTS, "real_faults_%s.json" % tag)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                rf = json.load(fh)
        else:
            rf = real_faults.run(manifest, tag, s, e)
        c = dataset.load(manifest)
        ref = np.arange(c.shape[1] // 2)
        healthy = {c.site_ids[i] for i in range(c.shape[0]) if c.observed[i, ref].mean() >= 0.9}
        reported = sorted({r["site"] for r in rf["reports"]} & healthy)
        rng = np.random.default_rng(1000 * month + (1 if road == "M1" else 0))
        pool = sorted(healthy - set(reported))
        ctrl = [pool[k] for k in sorted(rng.choice(len(pool), min(CONTROLS, len(pool)),
                                                   replace=False))]
        rec = {"road": road, "month": month, "tag": tag,
               "reports": rf["reports_test"], "reports_reference_chance":
                   rf["reports_reference_chance"], "reported_admitted": len(reported),
               "reported_failed": 0, "control": len(ctrl), "control_failed": 0}
        for m in (month + 1, month + 2, month + 3):
            prefetch(list(reported) + ctrl, *month_range(2025, m))
        for sid in reported:
            f, sh = failed_after(sid, month)
            rec["reported_failed"] += int(f)
            units.append({"road": road, "site": sid, "month": month, "group": "reported",
                          "failed": f, "absent_next_three": sh})
        for sid in ctrl:
            f, sh = failed_after(sid, month)
            rec["control_failed"] += int(f)
            units.append({"road": road, "site": sid, "month": month, "group": "control",
                          "failed": f, "absent_next_three": sh})
        per_run.append(rec)
        print(rec, flush=True)

    def fisher(rf_, rn, cf, cn):
        return float("%.3g" % fisher_exact([[rf_, rn - rf_], [cf, cn - cf]],
                                           alternative="greater")[1])

    rf_ = sum(r["reported_failed"] for r in per_run)
    rn = sum(r["reported_admitted"] for r in per_run)
    cf = sum(r["control_failed"] for r in per_run)
    cn = sum(r["control"] for r in per_run)
    pooled = {"reported_failed": rf_, "reported": rn, "control_failed": cf, "control": cn,
              "fisher_exact_p_one_sided": fisher(rf_, rn, cf, cn)}

    # per detector: first appearance decides the group; ever-reported wins
    first = {}
    for u in sorted(units, key=lambda u: u["month"]):
        k = (u["road"], u["site"])
        if u["group"] == "reported":
            if k not in first or first[k]["group"] == "control":
                first[k] = u
        elif k not in first:
            first[k] = u
    ever = {(u["road"], u["site"]) for u in units if u["group"] == "reported"}
    rep_u = [u for k, u in first.items() if k in ever]
    ctl_u = [u for k, u in first.items() if k not in ever]
    dedup = {"reported_failed": sum(u["failed"] for u in rep_u), "reported": len(rep_u),
             "control_failed": sum(u["failed"] for u in ctl_u), "control": len(ctl_u)}
    dedup["fisher_exact_p_one_sided"] = fisher(dedup["reported_failed"], dedup["reported"],
                                               dedup["control_failed"], dedup["control"])
    out = {"runs": per_run, "pooled_per_month": pooled, "pooled_per_detector": dedup,
           "units": units}
    with open(os.path.join(RESULTS, "real_faults_months.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print("pooled per month", pooled)
    print("pooled per detector", dedup)


if __name__ == "__main__":
    main()
