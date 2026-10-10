"""Correcting the attributed detector's output, measured end to end.

faults.py detects a fault, names a detector and, for scale and offset faults, estimates
its size. That is a diagnosis. This module closes the loop and measures what the
diagnosis is worth as a correction of the detector's output record:

  1. detect      any relation containing the detector exceeds its 1%-false-positive
                 span threshold (faults.py, unchanged);
  2. attribute   the TOP-RANKED detector is corrected, whichever it is. If attribution
                 names an innocent detector, the innocent is "corrected" and the damage is
                 counted; the faulty one stays faulty;
  3. correct     two corrections are measured:
                   parametric   the fitted fault model is inverted - scale: x (1 - gamma);
                                offset: x - delta. Keeps the detector's own interval-to-
                                interval detail. Only for spans typed scale or offset.
                   substitution each interval of the span is replaced by the value that
                                sets the calibrated residual of each relation containing
                                the detector to zero, median over those relations. Needs
                                no fault model, so it also covers a stuck detector.
                 "auto" = parametric where the span was typed, otherwise substitution.

Relations are recovered from the counts by discover2 on the calibration half only, and
calibration and thresholds come from the clean data, as in faults.py (topology="recovered").
Scored on the injected detector over the faulted span against the clean record:
MAE before correction (the faulted output) and after. Every trial counts, including missed
detections and wrong attributions. Damage to innocent detectors is reported separately.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import classes, constrained, dataset, discover, discover2, faults

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CASES = ([("none", 0.0)]
         + [("scale", g) for g in (0.80, 0.90, 0.95, 1.05, 1.10)]
         + [("offset", k) for k in (-30.0, -15.0, -8.0, 8.0, 15.0, 30.0)]
         + [("stuck", 0.0)])


def substitute(volumes, row, cols, fitted, calib, idx):
    """Per interval, the value of `row` that zeroes each relation's calibrated residual."""
    est = np.full(cols.size, np.nan)
    per = []
    for i in idx:
        f = fitted[i]
        c = calib[f["node_id"]]
        terms = [(f["up"], 1.0), (f["down"], c["down_coeff"])] + \
                [(r, float(s)) for r, s in f["slips"]]
        own = sum(k for r, k in terms if r == row)
        if abs(own) < 1e-9:
            continue
        other = np.full(cols.size, -c["const"])
        for r, k in terms:
            if r != row:
                other = other + k * volumes[r, cols]
        per.append(-other / own)
    if per:
        with np.errstate(all="ignore"):
            est = np.nanmedian(np.vstack(per), axis=0)
    return np.maximum(est, 0.0)


def correct(volumes, row, cols, fitted, calib, nodes_of, typing):
    x = volumes[row, cols].copy()
    sub = substitute(volumes, row, cols, fitted, calib, nodes_of.get(row, []))
    sub = np.where(np.isfinite(sub), sub, x)
    if typing is None:
        par = None
    elif typing["type"] == "scale":
        par = x * (1.0 - typing["scale_pct"] / 100.0)
    else:
        par = np.maximum(x - typing["offset_vehicles"], 0.0)
    auto = par if par is not None else sub
    return {"parametric": par, "substitution": sub, "auto": auto}


def run(manifest="window_full_M25_A.json", span=192, seed=0, n_detectors=40, repeats=3,
        out_name="correction_M25_A.json"):
    rng = np.random.default_rng(seed)
    total = classes.load(manifest).total
    n_cols = total.shape[1]
    split = n_cols // 2
    train_cols, test_cols = np.arange(split), np.arange(split, n_cols)

    rel, meta = discover2.discover(total.volumes[:, train_cols], total.observed[:, train_cols])
    fitted = discover.relations_to_fitted(rel, total)
    sub_c = dataset.Corridor(total.volumes[:, train_cols], total.observed[:, train_cols],
                             total.site_ids, [total.keys[j] for j in train_cols], total.nodes)
    calib = constrained.calibrate(sub_c, fitted, mode="scaled")
    clean = total.volumes
    resid_clean = faults.residuals(clean, fitted, calib)
    thresh, usable = faults.clean_thresholds(resid_clean, test_cols, span, rng)
    nodes_of = faults.node_membership(fitted)
    coeff = faults.coefficients(fitted, calib)
    pool_rank = sorted(r for r, idx in nodes_of.items() if len(idx) >= 2)
    pool = faults.eligible_detectors(fitted, total)
    n_eligible = len(pool)
    if len(pool) > n_detectors:
        pick = rng.choice(len(pool), size=n_detectors, replace=False)
        pool = [pool[i] for i in sorted(pick)]
    print("%d relations, %d eligible, %d under test" % (len(fitted), n_eligible, len(pool)),
          flush=True)

    out = {"manifest": manifest, "topology": "recovered (discover2, calibration half)",
           "relations": len(fitted), "detectors_eligible": n_eligible,
           "detectors_tested": len(pool), "repeats": repeats, "span_intervals": span,
           "cases": []}
    for mode, mag in CASES:
        before, after = [], {"parametric": [], "substitution": [], "auto": []}
        n_trials = n_det = n_right = n_typed = 0
        innocent_damage = []
        for row in pool:
            for _ in range(repeats):
                start = int(rng.integers(0, max(1, test_cols.size - span)))
                cols = test_cols[start:start + span]
                if total.observed[row, cols].mean() <= 0.8:
                    continue
                faulted = clean if mode == "none" else \
                    faults.inject_total(clean, row, cols, mode, mag)
                resid_f = faults.residuals(faulted, fitted, calib)
                ratio = faults.span_statistic(resid_f, cols) / thresh
                vals = [ratio[i] for i in nodes_of.get(row, []) if np.isfinite(ratio[i])]
                if not vals:
                    continue
                n_trials += 1
                live = np.isfinite(clean[row, cols]) & np.isfinite(faulted[row, cols])
                err0 = float(np.mean(np.abs(faulted[row, cols][live] - clean[row, cols][live])))
                before.append(err0)
                # detection as faults.py scores it: a relation containing the detector
                # under test exceeds its threshold. Attribution then ranks every detector.
                fired = max(vals) > 1.0
                if not fired:
                    for k in after:
                        after[k].append(err0)
                    continue
                n_det += 1
                ranking = faults.attribute(faults.signed_span_mean(resid_f, cols), thresh,
                                           fitted, coeff, pool_rank, nodes_of)
                if not ranking:
                    for k in after:
                        after[k].append(err0)
                    continue
                named = ranking[0][1]
                flow = faulted[named, cols]
                ok = np.isfinite(flow)
                typing = None
                if ok.sum() > 16:
                    cut = float(np.median(flow[ok]))
                    hi, lo = cols[ok][flow[ok] >= cut], cols[ok][flow[ok] < cut]
                    if hi.size > 8 and lo.size > 8:
                        typing = faults.classify_fault(
                            faults.signed_span_mean(resid_f, hi),
                            faults.signed_span_mean(resid_f, lo), thresh, fitted, coeff,
                            named, nodes_of, float(flow[ok][flow[ok] >= cut].mean()),
                            float(flow[ok][flow[ok] < cut].mean()))
                n_typed += int(typing is not None)
                fixes = correct(faulted, named, cols, fitted, calib, nodes_of, typing)
                if named == row and mode != "none":
                    n_right += 1
                    for k, v in fixes.items():
                        vv = v if v is not None else fixes["substitution"]
                        after[k].append(float(np.mean(np.abs(vv[live] - clean[row, cols][live]))))
                else:
                    for k in after:
                        after[k].append(err0)
                    m = np.isfinite(clean[named, cols])
                    v = fixes["auto"]
                    innocent_damage.append(float(np.mean(np.abs(v[m] - clean[named, cols][m]))))
        if not n_trials:
            continue
        e = {"mode": mode, "magnitude": mag, "trials": n_trials,
             "detected": round(n_det / n_trials, 4),
             "attributed_correctly": round(n_right / n_trials, 4),
             "mae_before": round(float(np.mean(before)), 2),
             "mae_after": {k: round(float(np.mean(v)), 2) for k, v in after.items()},
             "innocent_corrections": len(innocent_damage),
             "innocent_mae_introduced": (round(float(np.mean(innocent_damage)), 2)
                                         if innocent_damage else 0.0)}
        if e["mae_before"] > 0:
            e["error_removed_pct_auto"] = round(
                100.0 * (1 - e["mae_after"]["auto"] / e["mae_before"]), 1)
        out["cases"].append(e)
        print(e, flush=True)
    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/%s" % out_name)


if __name__ == "__main__":
    run(*(sys.argv[1:2] or ["window_full_M25_A.json"]),
        out_name=(sys.argv[2] if len(sys.argv) > 2 else "correction_M25_A.json"))
