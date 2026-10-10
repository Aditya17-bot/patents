"""Phase 9 - injecting faults that are known, so the fault detector can be scored.

The method already reports intervals it cannot reconcile, and that report was offered as
a second technical effect: detection of a data-integrity fault. As it stood the claim
could not be checked. Real detectors do not come labelled, so a flag raised on the M25 in
March 2025 cannot be confirmed or refuted - which under the 2025 CRI Guidelines is the
difference between an evidenced technical effect and an asserted one.

So faults are injected deliberately, into real data, at a known detector over a known
span, and the flag is scored against ground truth that exists by construction.

Four fault modes, each a real failure of an inductive loop:

  scale     the loop under- or over-counts by a fixed percentage. Detuned sensitivity,
            the commonest drift mode.
  offset    a fixed number of phantom or lost vehicles per interval. Cross-talk from an
            adjacent loop, or a counter that misses a fixed dead time.
  stuck     the detector repeats a plausible constant. The failure mode that defeats every
            range check and every "is the value missing" test, because the value is
            neither missing nor absurd.
  classify  the length classifier drifts and books a share of one length class into the
            next one up. The total is unchanged, exactly.

The last one is the discriminating case. Its total is unchanged by construction, so no
balance written on total flow can detect it, at any threshold, ever - not because the
method is weak but because the fault is invisible in that coordinate. It is included to
test whether the class-resolved balances see what the total balance provably cannot.

THE TEST IS OVER A SPAN, NOT AN INTERVAL. Testing each interval on its own was tried
first and is the wrong instrument: the per-interval band flags 19% of clean intervals in
a held-out half-month, because the relation drifts slowly and a band fitted in week one
is not exactly the band of week three. A fault, unlike that drift and unlike measurement
noise, is persistent and one-sided, so the statistic is the mean calibrated residual over
a span of consecutive intervals.

THRESHOLD FROM CLEAN DATA, PER NODE. Two things were measured rather than assumed, and
both matter.

First, the residual is strongly serially correlated - it carries a time-of-day shape - so
the textbook standard error, the per-interval spread divided by root n, is badly wrong.
Scoring the span mean in those units was tried and the null statistic came out at 179
instead of about 1. The null distribution is therefore taken empirically, by drawing many
clean spans from the held-out half and reading the 99th percentile of the span mean off
them directly.

Second, the null has to be per node. Node quality varies by two orders of magnitude on
this corridor: over a two-day span one node's mean residual sits inside 1.08 vehicles on
a flow of 725, while another wanders to 32.2. A single pooled threshold is set by the
worst node and makes the good ones blind, which is what happened on the first attempt.
Each node therefore carries its own threshold, and the 1% false-positive rate holds at
each node separately.

CALIBRATION HYGIENE. The per-node calibration is fitted on one half of the record and
every fault is injected into the other, disjoint half. Fitted on the faulted data, the
calibration would absorb the fault and the experiment would be scoring its own leakage.

ATTRIBUTION. A flag says a node is inconsistent, not which detector is lying. The nodes
overlap - each mainline detector is downstream of one node and upstream of the next - so
a faulty detector makes every node it belongs to inconsistent, while an innocent
node-mate is only implicated in the one node they share. Suspicion is scored as the
weakest evidence against a detector: the minimum statistic across all the nodes it
belongs to. A guilty detector has every one of its nodes deviating, so its minimum is
large; an innocent neighbour has at least one clean node, so its minimum collapses. This
works only because the node structure overlaps, and only for detectors in more than one
node - which is stated as the method's limit rather than hidden by excluding the rest
silently.
"""

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import classes
import constrained
import dataset
import evaluate

RESULTS = os.path.join(ROOT, "results")


# ------------------------------------------------------------------ injection

def inject_total(volumes, row, cols, mode, magnitude):
    """Return a copy of `volumes` with one detector faulted over `cols`."""
    out = volumes.copy()
    seg = out[row, cols].copy()
    live = np.isfinite(seg)
    if mode == "scale":
        seg[live] = seg[live] * magnitude
    elif mode == "offset":
        seg[live] = np.maximum(seg[live] + magnitude, 0.0)
    elif mode == "stuck":
        if live.any():
            seg[live] = float(np.median(seg[live]))
    else:
        raise ValueError(mode)
    out[row, cols] = seg
    return out


def inject_classify(by_class, row, cols, share):
    """Move `share` of one length class into the next one up. Total is untouched.

    Applied to the shortest class, which is the busiest, so the absolute number of
    misclassified vehicles is largest and the fault has its best chance of being seen.
    """
    out = {name: m.copy() for name, m in by_class.items()}
    src, dst = classes.CLASS_NAMES[0], classes.CLASS_NAMES[1]
    seg = out[src][row, cols].copy()
    live = np.isfinite(seg)
    moved = np.zeros_like(seg)
    moved[live] = np.round(seg[live] * share)
    out[src][row, cols] = seg - moved
    out[dst][row, cols] = out[dst][row, cols] + moved
    return out, float(np.nansum(moved))


# ------------------------------------------------------------------- residuals

def residuals(volumes, fitted, calib):
    """Calibrated conservation residual per node per interval, nan where incomplete."""
    n_cols = volumes.shape[1]
    out = np.full((len(fitted), n_cols), np.nan)
    for i, f in enumerate(fitted):
        c = calib[f["node_id"]]
        rows = [f["up"], f["down"]] + [r for r, _ in f["slips"]]
        complete = np.all(np.isfinite(volumes[rows]), axis=0)
        value = volumes[f["up"]] + c["down_coeff"] * volumes[f["down"]]
        for row, sign in f["slips"]:
            value = value + sign * volumes[row]
        out[i] = np.where(complete, value - c["const"], np.nan)
    return out


def span_statistic(resid, cols, min_fraction=0.3):
    """Absolute mean calibrated residual over the span, in vehicles per interval.

    Returns nan for a node that did not have enough complete intervals in the span to say
    anything, rather than a small number that would read as evidence of innocence.
    """
    block = resid[:, cols]
    n = np.sum(np.isfinite(block), axis=1)
    with np.errstate(invalid="ignore"):
        mean = np.nanmean(block, axis=1)
    return np.where(n >= max(8, min_fraction * cols.size), np.abs(mean), np.nan)


def clean_thresholds(resid, test_cols, span, rng, draws=300, quantile=0.99):
    """Per-node decision threshold: the 99th percentile of the clean span statistic.

    Drawn from the same held-out half the faults are injected into, so the threshold and
    the test see the same drift, the same weather and the same weeks. Nodes that never
    accumulate enough clean spans get an infinite threshold, which makes them abstain
    rather than fire at random.
    """
    n_nodes = resid.shape[0]
    seen = [[] for _ in range(n_nodes)]
    for _ in range(draws):
        start = int(rng.integers(0, max(1, test_cols.size - span)))
        cols = test_cols[start:start + span]
        s = span_statistic(resid, cols)
        for i in range(n_nodes):
            if np.isfinite(s[i]):
                seen[i].append(float(s[i]))
    thresh = np.full(n_nodes, np.inf)
    usable = 0
    for i in range(n_nodes):
        if len(seen[i]) >= 30:
            thresh[i] = float(np.quantile(seen[i], quantile))
            usable += 1
    return thresh, usable


def class_ratio(resid_class, thresh_class, cols):
    """The classify test statistic: worst of the four class relations, in threshold units.

    A classifier drift moves vehicles between two adjacent length bins, so it shows up in
    those two class relations and nowhere else. Which two is not known in advance, so the
    test has to look at all four and fire on the worst - which is exactly what makes its
    false-alarm rate larger than the 1% each individual class threshold was set to.
    """
    ratio = np.full(next(iter(resid_class.values())).shape[0], np.nan)
    for name, resid in resid_class.items():
        with np.errstate(invalid="ignore"):
            ratio = np.fmax(ratio, span_statistic(resid, cols) / thresh_class[name])
    return ratio


def class_joint_thresholds(resid_class, thresh_class, test_cols, span, rng,
                           draws=300, quantile=0.99):
    """Per-node scale that restores the four-class test to 1% false positives.

    Each class relation carries its own 1% threshold, but the classify test fires when ANY
    of the four exceeds it. The false-alarm rate of that combined test is therefore
    somewhere between 1% and 4%, at a point set by how correlated the four class residuals
    are - which is a property of the data and cannot be assumed. Scoring detection against
    an uncalibrated combined test, and comparing it with a total-flow test that really is
    at 1%, would credit the class relations with sensitivity they had only bought by
    firing more often.

    So the null of the combined statistic is taken directly: draw clean spans, form the
    same worst-of-four ratio the test forms, and read its 99th percentile off. Dividing by
    that number makes the combined test 1% per node, and only then is the comparison with
    the total-flow test like for like.
    """
    n_nodes = next(iter(resid_class.values())).shape[0]
    seen = [[] for _ in range(n_nodes)]
    for _ in range(draws):
        start = int(rng.integers(0, max(1, test_cols.size - span)))
        cols = test_cols[start:start + span]
        ratio = class_ratio(resid_class, thresh_class, cols)
        for i in range(n_nodes):
            if np.isfinite(ratio[i]):
                seen[i].append(float(ratio[i]))
    scale = np.full(n_nodes, np.inf)
    usable = 0
    for i in range(n_nodes):
        if len(seen[i]) >= 30:
            scale[i] = max(float(np.quantile(seen[i], quantile)), 1e-9)
            usable += 1
    return scale, usable


def node_membership(fitted):
    nodes_of = {}
    for i, f in enumerate(fitted):
        for r in [f["up"], f["down"]] + [row for row, _ in f["slips"]]:
            nodes_of.setdefault(r, []).append(i)
    return nodes_of


def coefficients(fitted, calib):
    """The coefficient each detector carries in each node's balance relation.

    +1 where it is the upstream detector, -(1+alpha) where it is the downstream one, and
    the fitted slip sign where it is a slip road. This is the signature a bias at that
    detector would print on the network, and it is what makes attribution possible: the
    same error appears with a different, known coefficient at every node the detector
    belongs to.
    """
    coeff = {}
    for i, f in enumerate(fitted):
        c = calib[f["node_id"]]
        for row, k in ([(f["up"], 1.0), (f["down"], c["down_coeff"])]
                       + [(row, float(s)) for row, s in f["slips"]]):
            coeff[(i, row)] = coeff.get((i, row), 0.0) + k
    return coeff


def signed_span_mean(resid, cols, min_fraction=0.3):
    """Signed mean residual over the span. Sign carries the direction of the bias."""
    block = resid[:, cols]
    n = np.sum(np.isfinite(block), axis=1)
    with np.errstate(invalid="ignore"):
        mean = np.nanmean(block, axis=1)
    return np.where(n >= max(8, min_fraction * cols.size), mean, np.nan)


def attribute(mean_signed, thresh, fitted, coeff, candidates, nodes_of):
    """Which detector best explains the whole pattern of node deviations at once.

    A bias of delta at detector r shifts node i's mean residual by exactly c(i,r)*delta,
    with c known. So for each candidate the single delta that best explains all of its
    nodes is fitted by weighted least squares, and the candidate is scored by how much of
    the deviation that one number removes. Nodes are weighted by the inverse square of
    their own 1%-false-positive threshold, so a node that is quiet on clean data counts
    for more than one that wanders.

    A guilty detector explains every node it belongs to. An innocent neighbour of a
    guilty one can explain the single node they share, but is then contradicted by its
    other nodes, which are clean and pull the fitted delta back towards zero. That
    contradiction is what separates them, and it is why only detectors belonging to more
    than one node can be attributed at all.
    """
    best = []
    for r in candidates:
        idx = [i for i in nodes_of.get(r, [])
               if np.isfinite(mean_signed[i]) and np.isfinite(thresh[i])]
        if len(idx) < 2:
            continue
        m = np.array([mean_signed[i] for i in idx])
        c = np.array([coeff.get((i, r), 0.0) for i in idx])
        w = 1.0 / np.maximum(np.array([thresh[i] for i in idx]), 1e-6) ** 2
        denom = float((w * c * c).sum())
        if denom <= 1e-12:
            continue
        delta = float((w * c * m).sum() / denom)
        e0 = float((w * m * m).sum())
        ea = float((w * (m - c * delta) ** 2).sum())
        best.append((e0 - ea, r, delta))
    best.sort(reverse=True)
    return best


def classify_fault(mean_high, mean_low, thresh, fitted, coeff, row, nodes_of,
                   flow_high, flow_low):
    """Scale bias or constant offset? Told apart by how the bias tracks flow.

    The span is cut into its busier and quieter halves. A detector that miscounts by a
    fixed percentage produces a deviation proportional to the flow through it, so the
    fitted delta grows with flow. A detector carrying a constant offset produces the same
    deviation in both halves. Fitting both models and taking the smaller weighted error
    names the fault type, and the fitted number is the size of the fault in percent or in
    vehicles per interval.
    """
    idx = [i for i in nodes_of.get(row, [])
           if np.isfinite(mean_high[i]) and np.isfinite(mean_low[i])
           and np.isfinite(thresh[i])]
    if len(idx) < 2 or flow_low <= 0 or flow_high <= 0:
        return None
    c = np.array([coeff.get((i, row), 0.0) for i in idx])
    w = 1.0 / np.maximum(np.array([thresh[i] for i in idx]), 1e-6) ** 2
    mh = np.array([mean_high[i] for i in idx])
    ml = np.array([mean_low[i] for i in idx])

    # offset model: the same delta in both halves
    den = float((w * c * c).sum()) * 2.0
    if den <= 1e-12:
        return None
    delta_off = float((w * c * (mh + ml)).sum() / den)
    err_off = float((w * (mh - c * delta_off) ** 2).sum()
                    + (w * (ml - c * delta_off) ** 2).sum())

    # scale model: delta proportional to that half's flow
    den_s = float((w * c * c).sum() * (flow_high ** 2 + flow_low ** 2))
    if den_s <= 1e-12:
        return None
    gamma = float((w * c * (mh * flow_high + ml * flow_low)).sum() / den_s)
    err_scale = float((w * (mh - c * gamma * flow_high) ** 2).sum()
                      + (w * (ml - c * gamma * flow_low) ** 2).sum())

    return {"type": "scale" if err_scale < err_off else "offset",
            "scale_pct": round(100.0 * gamma, 3),
            "offset_vehicles": round(delta_off, 2),
            "err_scale": err_scale, "err_offset": err_off}


def eligible_detectors(fitted, corridor, min_nodes=2):
    """Detectors in more than one node that reported nearly all month.

    A detector belonging to a single node cannot be separated from its node-mates by any
    parity argument. That is a property of the network, not of the method, and it is
    reported as the method's limit.
    """
    count = {}
    for f in fitted:
        for r in [f["up"], f["down"]] + [row for row, _ in f["slips"]]:
            count[r] = count.get(r, 0) + 1
    return sorted(r for r, k in count.items()
                  if k >= min_nodes and corridor.observed[r].mean() > 0.9)


# ------------------------------------------------------------------ experiment

def run(manifest="window.json", span=192, seed=0, n_detectors=16, repeats=3,
        out_name="faults.json"):
    rng = np.random.default_rng(seed)
    cc = classes.load(manifest)
    total = cc.total
    fitted = evaluate.fit_node_signs(total)
    n_cols = total.shape[1]
    n_sites = total.shape[0]

    split = n_cols // 2
    train_cols = np.arange(split)
    test_cols = np.arange(split, n_cols)

    def sub(volumes):
        return dataset.Corridor(volumes[:, train_cols], total.observed[:, train_cols],
                                total.site_ids, [total.keys[j] for j in train_cols],
                                total.nodes)

    calib = constrained.calibrate(sub(total.volumes), fitted, mode="scaled")
    calib_class = {name: constrained.calibrate(sub(cc.by_class[name]), fitted,
                                               mode="scaled")
                   for name in classes.CLASS_NAMES}

    resid_clean = residuals(total.volumes, fitted, calib)
    thresh, usable = clean_thresholds(resid_clean, test_cols, span, rng)

    resid_class_clean = {name: residuals(cc.by_class[name], fitted, calib_class[name])
                         for name in classes.CLASS_NAMES}
    thresh_class = {}
    for name in classes.CLASS_NAMES:
        thresh_class[name], _ = clean_thresholds(resid_class_clean[name], test_cols,
                                                 span, rng)
    # its own generator, deliberately. Drawing these spans from `rng` would advance the
    # shared stream and change both the detector sample and every injection span, so the
    # whole table would move and the effect of the calibration could not be read off
    # against the previously published one.
    joint_scale, joint_usable = class_joint_thresholds(
        resid_class_clean, thresh_class, test_cols, span,
        np.random.default_rng(seed + 100003))

    nodes_of = node_membership(fitted)
    coeff = coefficients(fitted, calib)
    coeff_class = {name: coefficients(fitted, calib_class[name])
                   for name in classes.CLASS_NAMES}
    finite = thresh[np.isfinite(thresh)]

    print("corridor %d sites, %d nodes fitted" % (n_sites, len(fitted)))
    print("calibrated on %d intervals, faults injected into the other %d"
          % (train_cols.size, test_cols.size))
    print("span %d intervals (%.1f days); %d of %d nodes carry a usable threshold"
          % (span, span / 96.0, usable, len(fitted)))
    print("per-node threshold at 1%% false positives, vehicles per interval: "
          "median %.2f  min %.2f  max %.2f"
          % (np.median(finite), finite.min(), finite.max()))
    fin_j = joint_scale[np.isfinite(joint_scale)]
    print("worst-of-four class test needs scaling by median %.2f (min %.2f max %.2f) "
          "to sit at 1%% too; %d of %d nodes"
          % (np.median(fin_j), fin_j.min(), fin_j.max(), joint_usable, len(fitted)))

    # every detector in more than one node is a candidate the ranking has to reject,
    # whatever its own coverage - narrowing the line-up to the healthy detectors would
    # make attribution look better than it is
    pool_rank = sorted(r for r, idx in nodes_of.items() if len(idx) >= 2)

    all_eligible = eligible_detectors(fitted, total)
    pool = list(all_eligible)
    if len(pool) > n_detectors:
        pick = rng.choice(len(pool), size=n_detectors, replace=False)
        pool = [pool[i] for i in sorted(pick)]
    print("detectors under test: %d of %d that belong to >=2 nodes\n"
          % (len(pool), len(all_eligible)))

    out = {"manifest": manifest, "span_intervals": span, "seed": seed,
           "nodes_fitted": len(fitted), "nodes_with_threshold": usable,
           "detectors_tested": len(pool), "detectors_eligible": len(all_eligible),
           "repeats_per_detector": repeats,
           "train_intervals": int(train_cols.size), "test_intervals": int(test_cols.size),
           "false_positive_rate_by_construction": 0.01,
           "threshold_vehicles": {"median": round(float(np.median(finite)), 2),
                                  "min": round(float(finite.min()), 2),
                                  "max": round(float(finite.max()), 2)},
           "class_joint_scale": {"median": round(float(np.median(fin_j)), 3),
                                 "min": round(float(fin_j.min()), 3),
                                 "max": round(float(fin_j.max()), 3),
                                 "nodes": joint_usable},
           "cases": []}

    cases = ([("none", 0.0)]
             + [("scale", g) for g in (0.80, 0.90, 0.95, 0.98, 0.99, 0.995,
                                       1.005, 1.01, 1.02, 1.05, 1.10)]
             + [("offset", k) for k in (-30.0, -15.0, -8.0, -4.0, -2.0,
                                        2.0, 4.0, 8.0, 15.0, 30.0)]
             + [("stuck", 0.0)]
             # share 0.0 moves no vehicles, so it runs clean data through the identical
             # four-class pathway: the false-alarm control for the classify test, which
             # the `none` case above does not provide because that one is read through
             # the total relation
             + [("classify", s) for s in (0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.40)])

    print("%-9s %7s %7s %9s %10s %9s %9s %11s %8s"
          % ("mode", "size", "trials", "detect", "detect@1%", "attrib@1", "attrib@3",
             "total-blind", "type ok"))

    for mode, magnitude in cases:
        detected, top1, top3, trials = 0, 0, 0, 0
        detected_cal, cal_trials = 0, 0
        blind, typed_ok, typed_n, sized = [], 0, 0, []
        for row in pool:
            for _ in range(repeats):
                start = int(rng.integers(0, max(1, test_cols.size - span)))
                cols = test_cols[start:start + span]
                if total.observed[row, cols].mean() <= 0.8:
                    continue

                if mode == "classify":
                    faulted_class, _ = inject_classify(cc.by_class, row, cols, magnitude)
                    resid_c = {name: residuals(faulted_class[name], fitted,
                                               calib_class[name])
                               for name in classes.CLASS_NAMES}
                    ratio = class_ratio(resid_c, thresh_class, cols)
                    # the same statistic held to the same 1% false-alarm rate as the
                    # total-flow test, which is the only footing on which the two can be
                    # compared
                    ratio_cal = ratio / joint_scale
                    ranking = [attribute(signed_span_mean(resid_c[name], cols),
                                         thresh_class[name], fitted,
                                         coeff_class[name], pool_rank, nodes_of)
                               for name in classes.CLASS_NAMES]
                    # best explanation over the four class relations
                    merged = {}
                    for rk in ranking:
                        for score_, r_, _ in rk:
                            merged[r_] = max(merged.get(r_, 0.0), score_)
                    order = [r_ for r_, _ in sorted(merged.items(),
                                                    key=lambda kv: -kv[1])]
                    # the identical fault read through the total balance, which cannot
                    # move: the four classes still add up to exactly the same total
                    faulted_total = sum(faulted_class[n] for n in classes.CLASS_NAMES)
                    rt = span_statistic(residuals(faulted_total, fitted, calib),
                                        cols) / thresh
                    vals_t = [rt[i] for i in nodes_of.get(row, []) if np.isfinite(rt[i])]
                    if vals_t:
                        blind.append(float(max(vals_t) > 1.0))
                    typing = None
                else:
                    ratio_cal = None
                    if mode == "none":
                        faulted = total.volumes
                    else:
                        faulted = inject_total(total.volumes, row, cols, mode, magnitude)
                    resid_f = residuals(faulted, fitted, calib)
                    ratio = span_statistic(resid_f, cols) / thresh
                    signed = signed_span_mean(resid_f, cols)
                    order = [r_ for _, r_, _ in
                             attribute(signed, thresh, fitted, coeff, pool_rank, nodes_of)]

                    flow = faulted[row, cols]
                    live = np.isfinite(flow)
                    typing = None
                    if live.sum() > 16 and mode in ("scale", "offset"):
                        cut = float(np.median(flow[live]))
                        hi = cols[live][flow[live] >= cut]
                        lo = cols[live][flow[live] < cut]
                        if hi.size > 8 and lo.size > 8:
                            typing = classify_fault(
                                signed_span_mean(resid_f, hi),
                                signed_span_mean(resid_f, lo),
                                thresh, fitted, coeff, row, nodes_of,
                                float(flow[live][flow[live] >= cut].mean()),
                                float(flow[live][flow[live] < cut].mean()))

                vals = [ratio[i] for i in nodes_of.get(row, []) if np.isfinite(ratio[i])]
                if not vals:
                    continue
                trials += 1
                detected += int(max(vals) > 1.0)
                if ratio_cal is not None:
                    vals_cal = [ratio_cal[i] for i in nodes_of.get(row, [])
                                if np.isfinite(ratio_cal[i])]
                    if vals_cal:
                        cal_trials += 1
                        detected_cal += int(max(vals_cal) > 1.0)
                if order:
                    top1 += int(order[0] == row)
                    top3 += int(row in order[:3])

                if typing is not None:
                    typed_n += 1
                    typed_ok += int(typing["type"] == mode)
                    sized.append(typing["scale_pct"] if mode == "scale"
                                 else typing["offset_vehicles"])

        if not trials:
            continue
        entry = {"mode": mode, "magnitude": magnitude, "trials": trials,
                 "detection_rate": round(detected / trials, 4),
                 "attribution_top1": round(top1 / trials, 4),
                 "attribution_top3": round(top3 / trials, 4)}
        if mode == "classify":
            entry["detection_rate_via_total_balance"] = (
                round(float(np.mean(blind)), 4) if blind else None)
            if cal_trials:
                entry["detection_rate_at_matched_1pct"] = round(detected_cal / cal_trials, 4)
                entry["calibrated_trials"] = cal_trials
        if typed_n:
            entry["type_correct"] = round(typed_ok / typed_n, 4)
            entry["estimated_size_median"] = round(float(np.median(sized)), 3)
            entry["true_size"] = (round(100.0 * (magnitude - 1.0), 3)
                                  if mode == "scale" else magnitude)
        out["cases"].append(entry)
        print("%-9s %7.3f %7d %8.1f%% %9s %8.1f%% %8.1f%% %11s %8s"
              % (mode, magnitude, trials, 100 * entry["detection_rate"],
                 ("%.1f%%" % (100 * entry["detection_rate_at_matched_1pct"]))
                 if cal_trials else "-",
                 100 * entry["attribution_top1"], 100 * entry["attribution_top3"],
                 ("%.1f%%" % (100 * entry["detection_rate_via_total_balance"]))
                 if mode == "classify" else "-",
                 ("%.0f%%" % (100 * entry["type_correct"])) if typed_n else "-"))

    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/%s" % out_name)
    return out


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window.json"
    name = sys.argv[2] if len(sys.argv) > 2 else "faults.json"
    run(manifest, out_name=name)
