"""Faults found on unmodified counts, and whether anything independent corroborates them.

Everything before this was measured on faults injected into real data, which proves the
mechanism but not that real detectors fail in ways it can see. Here nothing is injected.
The relations are recovered from the counts of the first half of March (no map), fitted
and thresholded there, and the second half is scanned in consecutive spans. Where
relations deviate, the attribution of faults.py names a detector. A detector is REPORTED
only when it shows the guilty signature: every one of its evaluable relations deviates,
and it has at least two. Several detectors may be reported in one span (each reported
detector's relations are set aside and attribution repeated).

The same scan run on the reference half, against thresholds drawn from that half, gives
the report rate expected by chance. It is in-sample and so optimistic; drift between the
halves inflates the test-half rate, which is why the corroboration below matters more
than the count.

Corroboration uses signals the method never sees:

  A. bin-sum integrity. Each WebTRIS record carries a total and, separately, counts per
     length class (and per speed bin, blank for MIDAS sites). On a healthy detector the
     bins sum to the total.
     The share of a detector's records in the span where either sum misses the total by
     more than one vehicle is compared with the same detector in the reference half and
     with every non-reported detector in the same span.
  B. record loss: share of the span's records absent, same comparisons.
  C. persistence (M25 only, where June 2025 is cached): with the March relations and
     calibration unchanged, the single bias of each detector is fitted over all of June.
     A real instrument fault should persist; reported detectors are ranked against all
     other eligible detectors on |June bias| / its March threshold scale.
  D. status: whether the site is still listed Active by WebTRIS today (fresh fetch).
  E. agreement with the map audit: whether a reported detector is a member of a
     surveyed relation that the audit found inconsistent with the counts (Section 8.4),
     compared with the base rate among eligible detectors.

Writes results/real_faults_<tag>.json.
"""
import json
import os
import sys
from datetime import date
from math import comb

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import classes, constrained, dataset, discover, discover2, faults, webtris

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
SPAN = 192
MAX_PER_SPAN = 5
LENGTH = classes.CLASS_COLUMNS
SPEED = ["0 - 10 mph", "11 - 15 mph", "16 - 20 mph", "21 - 25 mph", "26 - 30 mph",
         "31 - 35 mph", "36 - 40 mph", "41 - 45 mph", "46 - 50 mph", "51 - 55 mph",
         "56 - 60 mph", "61 - 70 mph", "71 - 80 mph", "80+ mph"]


def integrity(site_ids, keys, start, end):
    """bad[i, t] = True where a record's length or speed bins miss its total by > 1."""
    col = {k: j for j, k in enumerate(keys)}
    bad = np.zeros((len(site_ids), len(keys)), dtype=bool)
    seen = np.zeros_like(bad)
    for i, sid in enumerate(site_ids):
        for r in webtris.daily(sid, start, end):
            k = (r["Report Date"][:10], int(r["Time Interval"]))
            if k not in col:
                continue
            tot = r.get("Total Volume", "")
            if tot in ("", None):
                continue
            try:
                t = float(tot)
                ls = sum(float(r[c]) for c in LENGTH)
            except (KeyError, ValueError, TypeError):
                continue
            # MIDAS sites leave the speed bins blank; use them only where populated
            sp = [r.get(c, "") for c in SPEED]
            ss = sum(float(v) for v in sp) if all(v not in ("", None) for v in sp) else None
            j = col[k]
            seen[i, j] = True
            bad[i, j] = abs(ls - t) > 1 or (ss is not None and abs(ss - t) > 1)
    return bad, seen


def scan(resid, thresh, fitted, coeff, pool_rank, nodes_of, cols_all):
    reports = []
    for s0 in range(cols_all[0], cols_all[-1] - SPAN + 2, SPAN):
        cols = np.arange(s0, s0 + SPAN)
        ratio = faults.span_statistic(resid, cols) / thresh
        signed = faults.signed_span_mean(resid, cols)
        fired = {i for i in range(len(fitted)) if np.isfinite(ratio[i]) and ratio[i] > 1}
        n_fired = len(fired)
        done = set()
        for _ in range(MAX_PER_SPAN):
            if not fired:
                break
            masked = signed.copy()
            for i in done:
                masked[i] = np.nan
            ranking = faults.attribute(masked, thresh, fitted, coeff,
                                       [r for r in pool_rank if r not in
                                        {x["row"] for x in reports if x["span_start"] == s0}],
                                       nodes_of)
            if not ranking:
                break
            score, r, delta = ranking[0]
            own = [i for i in nodes_of.get(r, []) if np.isfinite(ratio[i]) and i not in done]
            k = sum(1 for i in own if ratio[i] > 1)
            if len(own) >= 2 and k == len(own):
                reports.append({"span_start": int(s0), "row": int(r), "bias": round(delta, 2),
                                "relations": len(own), "relations_fired_in_span": n_fired})
                done |= set(nodes_of.get(r, []))
                fired -= set(nodes_of.get(r, []))
            else:
                break
    return reports


def run(manifest, tag, start, end, june_manifest=None, seed=0):
    rng = np.random.default_rng(seed)
    total = classes.load(manifest).total
    n_cols = total.shape[1]
    split = n_cols // 2
    ref_cols, test_cols = np.arange(split), np.arange(split, n_cols)
    rel, _ = discover2.discover(total.volumes[:, ref_cols], total.observed[:, ref_cols])
    fitted = discover.relations_to_fitted(rel, total)
    sub = dataset.Corridor(total.volumes[:, ref_cols], total.observed[:, ref_cols],
                           total.site_ids, [total.keys[j] for j in ref_cols], total.nodes)
    calib = constrained.calibrate(sub, fitted, mode="scaled")
    resid = faults.residuals(total.volumes, fitted, calib)
    thresh, _ = faults.clean_thresholds(resid, ref_cols, SPAN, rng)
    nodes_of = faults.node_membership(fitted)
    coeff = faults.coefficients(fitted, calib)
    pool_rank = sorted(r for r, idx in nodes_of.items() if len(idx) >= 2)
    eligible = set(faults.eligible_detectors(fitted, total))

    test_rep = scan(resid, thresh, fitted, coeff, pool_rank, nodes_of, test_cols)
    ref_rep = scan(resid, thresh, fitted, coeff, pool_rank, nodes_of, ref_cols)
    n_test_spans = len(range(test_cols[0], test_cols[-1] - SPAN + 2, SPAN))
    n_ref_spans = len(range(ref_cols[0], ref_cols[-1] - SPAN + 2, SPAN))
    print("%s: %d relations, %d detectors in >=2 relations; reports: test %d over %d "
          "spans, reference (chance) %d over %d spans"
          % (tag, len(fitted), len(pool_rank), len(test_rep), n_test_spans, len(ref_rep),
             n_ref_spans), flush=True)

    # A, B: integrity and record loss
    bad, seen = integrity(total.site_ids, total.keys, start, end)
    obs = total.observed

    def rate(m, rows, cols):
        vals = [float(m[r, cols].mean()) for r in rows]
        return float(np.mean(vals)) if vals else None

    for rep in test_rep:
        r, cols = rep["row"], np.arange(rep["span_start"], rep["span_start"] + SPAN)
        others = [x for x in pool_rank if x != r]
        sv = seen[r, cols]
        rep["site"] = total.site_ids[r]
        rep["binsum_bad_span"] = round(float(bad[r, cols][sv].mean()), 4) if sv.any() else None
        rv = seen[r, ref_cols]
        rep["binsum_bad_reference"] = round(float(bad[r, ref_cols][rv].mean()), 4) if rv.any() else None
        oth = []
        for o in others:
            ov = seen[o, cols]
            if ov.any():
                oth.append(float(bad[o, cols][ov].mean()))
        rep["binsum_bad_others_median"] = round(float(np.median(oth)), 4) if oth else None
        rep["binsum_bad_rank_pct"] = (round(100.0 * np.mean([rep["binsum_bad_span"] > x
                                                              for x in oth]), 1)
                                      if oth and rep["binsum_bad_span"] is not None else None)
        rep["missing_span"] = round(1 - float(obs[r, cols].mean()), 4)
        rep["missing_reference"] = round(1 - float(obs[r, ref_cols].mean()), 4)
        rep["missing_others_median"] = round(float(np.median(
            [1 - float(obs[o, cols].mean()) for o in others])), 4)

    # D: status today
    fresh = webtris._get("sites", "sites_%s.json" % date.today().strftime("%Y%m%d"))
    status = {str(s["Id"]): s.get("Status") for s in fresh.get("sites", [])}
    names = {str(s["Id"]): s.get("Description") or s.get("Name") for s in fresh.get("sites", [])}
    for rep in test_rep:
        rep["status_today"] = status.get(str(rep["site"]))
        rep["name"] = names.get(str(rep["site"]))
    reported = sorted({rep["row"] for rep in test_rep})
    rest = [r for r in pool_rank if r not in reported]
    inactive_rep = [status.get(str(total.site_ids[r])) != "Active" for r in reported]
    inactive_rest = [status.get(str(total.site_ids[r])) != "Active" for r in rest]

    # E: map-audit agreement
    audit_path = os.path.join(RESULTS, "map_audit_%s.json" % tag)
    in_flag_rep = in_flag_rest = None
    if os.path.exists(audit_path):
        with open(audit_path, encoding="utf-8") as fh:
            flagged = json.load(fh)["control"]["flagged"]
        members = set()
        for f in flagged:
            members |= {str(k) for k in f["relation"]}
        in_flag_rep = [str(total.site_ids[r]) in members for r in reported]
        in_flag_rest = [str(total.site_ids[r]) in members for r in rest]

    # C: persistence into June
    persistence = None
    if june_manifest:
        jt = classes.load(june_manifest).total
        jrow = {sid: i for i, sid in enumerate(jt.site_ids)}
        vol_j = np.full((total.shape[0], jt.shape[1]), np.nan)
        for i, sid in enumerate(total.site_ids):
            if sid in jrow:
                vol_j[i] = np.where(jt.observed[jrow[sid]], jt.volumes[jrow[sid]], np.nan)
        resid_j = faults.residuals(vol_j, fitted, calib)
        mean_j = faults.signed_span_mean(resid_j, np.arange(jt.shape[1]), min_fraction=0.2)
        biases = {}
        for score, r, delta in faults.attribute(mean_j, thresh, fitted, coeff, pool_rank,
                                                nodes_of):
            idx = [i for i in nodes_of[r] if np.isfinite(thresh[i])]
            scale = float(np.median([thresh[i] for i in idx])) if idx else np.nan
            biases[r] = abs(delta) / scale if scale and np.isfinite(scale) else np.nan
        # the detector's own March bias sign against its June bias sign
        rep_scores = [biases[r] for r in reported if r in biases and np.isfinite(biases[r])]
        rest_scores = [biases[r] for r in rest if r in biases and np.isfinite(biases[r])]
        pct_rank = [100.0 * np.mean([x > y for y in rest_scores]) for x in rep_scores]
        same_sign = []
        signed_j = {r: d for _, r, d in faults.attribute(mean_j, thresh, fitted, coeff,
                                                          pool_rank, nodes_of)}
        for rep in test_rep:
            if rep["row"] in signed_j:
                rep["june_bias"] = round(signed_j[rep["row"]], 2)
                same_sign.append(np.sign(signed_j[rep["row"]]) == np.sign(rep["bias"]))
        persistence = {"reported_with_june_bias": len(rep_scores),
                       "reported_median_percentile_among_others": (
                           round(float(np.median(pct_rank)), 1) if pct_rank else None),
                       "reported_in_top_quartile": int(sum(p >= 75 for p in pct_rank)),
                       "same_sign_as_march": int(sum(same_sign)),
                       "same_sign_binomial_p_one_sided": round(float(sum(
                           comb(len(same_sign), k) for k in range(int(sum(same_sign)),
                                                              len(same_sign) + 1))
                           / 2.0 ** len(same_sign)), 4) if same_sign else None,
                       "same_sign_of": len(same_sign),
                       "reported_median_norm_bias": (round(float(np.median(rep_scores)), 3)
                                                     if rep_scores else None),
                       "others_median_norm_bias": (round(float(np.median(rest_scores)), 3)
                                                   if rest_scores else None)}

    def frac(x):
        return round(float(np.mean(x)), 4) if x else None

    bad_ratio = [rep["binsum_bad_span"] > max(rep["binsum_bad_reference"] or 0, 1e-9) * 2
                 for rep in test_rep if rep["binsum_bad_span"] is not None]
    above_med = [rep["binsum_bad_span"] > (rep["binsum_bad_others_median"] or 0)
                 for rep in test_rep if rep["binsum_bad_span"] is not None]
    out = {"manifest": manifest, "span_intervals": SPAN, "relations": len(fitted),
           "detectors_in_two_or_more": len(pool_rank), "eligible": len(eligible),
           "test_spans": n_test_spans, "reference_spans": n_ref_spans,
           "reports_test": len(test_rep), "reports_reference_chance": len(ref_rep),
           "detectors_reported": len(reported),
           "binsum": {"reports_with_rate_over_2x_own_reference": int(sum(bad_ratio)),
                      "reports_with_rate_above_others_median": int(sum(above_med)),
                      "of": len(bad_ratio),
                      "overall_bad_rate_all_detectors": round(float(bad[seen].mean()), 4)},
           "status_not_active_today": {"reported": frac(inactive_rep),
                                       "others": frac(inactive_rest),
                                       "n_reported": len(inactive_rep),
                                       "n_others": len(inactive_rest)},
           "in_map_audit_flagged_relation": {"reported": frac(in_flag_rep),
                                             "others": frac(in_flag_rest)},
           "persistence_june": persistence,
           "reports": test_rep,
           "reference_reports": ref_rep}
    with open(os.path.join(RESULTS, "real_faults_%s.json" % tag), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(json.dumps({k: v for k, v in out.items() if k not in ("reports", "reference_reports")},
                     indent=1, default=str), flush=True)
    return out


if __name__ == "__main__":
    run("window_full_M25_A.json", "full_M25_A", "01032025", "31032025",
        june_manifest="window_june_M25_A.json")
    run("window_M1_A.json", "M1_A", "01032025", "31032025")
