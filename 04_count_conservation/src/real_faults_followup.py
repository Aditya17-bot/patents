"""Two checks on the detectors real_faults.py reported, each with a control group.

1. BRACKETING (March data, transparent). For each report, the reported detector's two
   tightest agreeing partners are found on the reference half (the detectors whose
   counts agreed with it most closely). Over the reported span: do the two partners still
   agree with EACH OTHER within the self-derived limit, while the reported detector
   disagrees with BOTH? If so, the vehicles cannot have gone anywhere between detectors
   that agree - the reported detector is miscounting. Detectors with fewer than two
   agreeing partners (most slip roads) are "not testable". Control: the same test on
   every non-reported detector over the same spans.

2. SUBSEQUENT FAILURE (April-June 2025, never seen by the method). Monthly share of
   absent records, fetched from WebTRIS, for every reported detector and for a random
   control sample. Both groups are admitted by one rule judged before any report: >= 90 %
   of records present in the reference half of March. A detector is counted as having
   failed if any of the three months is >= 95 % absent.

Writes results/real_faults_followup.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset, discover2, webtris

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
SPAN = 192
N_CONTROL = 40
CORRIDORS = (("M25", "window_full_M25_A.json", "real_faults_full_M25_A.json"),
             ("M1", "window_M1_A.json", "real_faults_M1_A.json"))
MONTHS = (("2025-04", "01042025", "30042025"), ("2025-05", "01052025", "31052025"),
          ("2025-06", "01062025", "30062025"))


def pct(a, b, vol, obs, cols):
    m = obs[a, cols] & obs[b, cols]
    if m.sum() < 16:
        return None
    x, y = vol[a, cols][m], vol[b, cols][m]
    f = max(x.mean(), y.mean())
    return float(np.median(np.abs(x - y))) / f * 100.0 if f >= 1 else None


def partners(r, vol, obs, ref, limit):
    out = []
    for j in range(vol.shape[0]):
        if j == r:
            continue
        p = pct(r, j, vol, obs, ref)
        if p is not None and p <= limit:
            out.append((p, j))
    out.sort()
    return [j for _, j in out[:2]]


def bracket(r, cols, vol, obs, ref, limit):
    pr = partners(r, vol, obs, ref, limit)
    if len(pr) < 2:
        return None
    a, b = pr
    pab, pra, prb = (pct(a, b, vol, obs, cols), pct(r, a, vol, obs, cols),
                     pct(r, b, vol, obs, cols))
    if None in (pab, pra, prb):
        return None
    return {"partners_agree": bool(pab <= limit), "detector_disagrees_with_both":
            bool(pra > limit and prb > limit), "pct_partners": round(pab, 3),
            "pct_to_partners": [round(pra, 3), round(prb, 3)]}


def monthly_missing(sid):
    out = {}
    for tag, s, e in MONTHS:
        rows = webtris.daily(sid, s, e)
        out[tag] = (round(sum(1 for r in rows if r.get("Total Volume") in ("", None))
                          / len(rows), 4) if rows else 1.0)
    return out


def main(seed=0):
    rng = np.random.default_rng(seed)
    res = {"span_intervals": SPAN, "control_sample": N_CONTROL, "corridors": {}}
    for name, manifest, rf in CORRIDORS:
        c = dataset.load(manifest)
        vol, obs = c.volumes, c.observed
        ref = np.arange(c.shape[1] // 2)
        adj = discover2.ordering_stage(discover2.pair_stage(vol[:, ref], obs[:, ref]))
        limit = discover2.FLOOR_MULTIPLE * float(np.median(list(adj.values())))
        with open(os.path.join(RESULTS, rf), encoding="utf-8") as fh:
            reps = json.load(fh)["reports"]
        row_of = {sid: i for i, sid in enumerate(c.site_ids)}
        reported = sorted({row_of[r["site"]] for r in reps if r["site"] in row_of})
        spans = sorted({r["span_start"] for r in reps})

        # 1. bracketing
        rep_b = []
        for r in reps:
            cols = np.arange(r["span_start"], r["span_start"] + SPAN)
            b = bracket(row_of[r["site"]], cols, vol, obs, ref, limit)
            rep_b.append({"site": r["site"], "span_start": r["span_start"], "bracket": b})
        # one admission rule for both groups, judged on the reference half only, i.e.
        # before any report: a detector already dropping out there is excluded from both
        healthy = set(i for i in range(c.shape[0]) if obs[i, ref].mean() >= 0.9)
        ctrl_rows = sorted(i for i in healthy if i not in reported)
        ctrl_b = []
        for i in ctrl_rows:
            for s0 in spans:
                b = bracket(i, np.arange(s0, s0 + SPAN), vol, obs, ref, limit)
                if b is not None:
                    ctrl_b.append(b)
        testable = [x["bracket"] for x in rep_b if x["bracket"] is not None]
        confirm = [b["partners_agree"] and b["detector_disagrees_with_both"] for b in testable]
        ctrl_confirm = [b["partners_agree"] and b["detector_disagrees_with_both"]
                        for b in ctrl_b]
        print(name, "bracket: reports testable %d, confirmed %d; control %d of %d"
              % (len(testable), sum(confirm), sum(ctrl_confirm), len(ctrl_b)), flush=True)

        # 2. subsequent failure
        ctrl_pick = [ctrl_rows[k] for k in sorted(rng.choice(len(ctrl_rows),
                                                             size=min(N_CONTROL,
                                                                      len(ctrl_rows)),
                                                             replace=False))]
        excluded = [c.site_ids[i] for i in reported if i not in healthy]
        rep_m = {c.site_ids[i]: monthly_missing(c.site_ids[i]) for i in reported
                 if i in healthy}
        ctl_m = {c.site_ids[i]: monthly_missing(c.site_ids[i]) for i in ctrl_pick}

        def failed(m):
            return any(v >= 0.95 for v in m.values())

        def mean_missing(ms):
            return round(float(np.mean([np.mean(list(m.values())) for m in ms.values()])), 4)
        print(name, "failed Apr-Jun: reported %d of %d; control %d of %d"
              % (sum(failed(m) for m in rep_m.values()), len(rep_m),
                 sum(failed(m) for m in ctl_m.values()), len(ctl_m)), flush=True)
        res["corridors"][name] = {
            "limit_pct": round(limit, 3),
            "bracketing": {"reports": len(reps), "testable": len(testable),
                           "confirmed": int(sum(confirm)),
                           "control_tests": len(ctrl_b),
                           "control_confirmed": int(sum(ctrl_confirm)),
                           "per_report": rep_b},
            "subsequent_failure": {"reported_detectors": len(rep_m),
                                   "reported_excluded_unhealthy_in_reference": excluded,
                                   "reported_failed": int(sum(failed(m) for m in rep_m.values())),
                                   "control_detectors": len(ctl_m),
                                   "control_failed": int(sum(failed(m) for m in ctl_m.values())),
                                   "reported_mean_missing": mean_missing(rep_m),
                                   "control_mean_missing": mean_missing(ctl_m),
                                   "reported": rep_m, "control": ctl_m}}
    from scipy.stats import fisher_exact
    rf = sum(v["subsequent_failure"]["reported_failed"] for v in res["corridors"].values())
    rn = sum(v["subsequent_failure"]["reported_detectors"] for v in res["corridors"].values())
    cf = sum(v["subsequent_failure"]["control_failed"] for v in res["corridors"].values())
    cn = sum(v["subsequent_failure"]["control_detectors"] for v in res["corridors"].values())
    odds, p = fisher_exact([[rf, rn - rf], [cf, cn - cf]], alternative="greater")
    res["pooled_subsequent_failure"] = {"reported_failed": rf, "reported": rn,
                                        "control_failed": cf, "control": cn,
                                        "fisher_exact_p_one_sided": round(float(p), 4)}
    print(res["pooled_subsequent_failure"])
    with open(os.path.join(RESULTS, "real_faults_followup.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print("wrote results/real_faults_followup.json")


if __name__ == "__main__":
    main()
