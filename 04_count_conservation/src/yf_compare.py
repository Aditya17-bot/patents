"""The closest art to Claim 12, run on the same faults: Yang, Yang and Fan (2019).

Yang, Yang and Fan, "Networked sensor data error estimation", Transportation Research
Part B 122:20-39, model each sensor's reading as y = (1 + beta) x + noise and estimate
theta = 1 / (1 + beta) per sensor from nodal flow balance on a GIVEN network, A (theta o x)
= 0, by the generalised method of moments: the balance is averaged over groups of
observations and the squared moment conditions are minimised. Sensors whose theta departs
from 1 are malfunctioning, and their data are corrected as theta * y.

Implemented here as published in its static form, with the surveyed junction list as the
network it requires:

  moments   for each surveyed node and each block of BLOCK consecutive intervals, the
            node balance of the block means (intervals in which every member reported);
  estimate  theta minimising ||M theta||^2 + LAMBDA * ||theta - 1||^2 subject to
            0.5 <= theta <= 1.5 (the small ridge fixes the scale the homogeneous system
            leaves free and holds a sensor in no node at 1; the bounds stop a weakly
            determined sensor collapsing to theta ~ 0, which the unbounded form was
            measured to do, and are in the method's favour);
  change    the method is given the same advantage as ours: theta is also estimated on
            the clean reference half, and a sensor's statistic in a span is
            |theta_span / theta_ref - 1|, thresholded at the 99th percentile of the same
            statistic over clean spans (the same 1 % rule ours uses);
  correct   the named sensor's counts over the span are multiplied by
            theta_span / theta_ref.

Three arms run on IDENTICAL injected faults (same detectors, spans and generator):
  yf_surveyed    Yang-Yang-Fan on the surveyed map;
  ours_surveyed  our attribution and correction (correction.py) on the surveyed map;
  ours_recovered our attribution and correction on relations recovered from the counts,
                 no map - the configuration of Claim 12.
The pool is the detectors all three can address (>= 2 surveyed nodes, >= 2 recovered
relations, a determined Yang-Yang-Fan theta, >= 90 % present). How many detectors each arm can address at all is reported
separately. Scored as correction.py: every trial counts, wrong corrections are charged.
Writes results/yf_compare_<tag>.json.
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import lsq_linear

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import classes, constrained, correction, dataset, discover, discover2, evaluate, faults

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
SPAN = 192
BLOCK = 16
LAMBDA = 1e-3
THETA_MIN, THETA_MAX = 0.5, 1.5      # sensor bias within +/-50 %
CASES = ([("none", 0.0)] + [("scale", g) for g in (0.90, 0.95, 1.05, 1.10)]
         + [("offset", k) for k in (-15.0, 15.0)] + [("stuck", 0.0)])


# ------------------------------------------------------------------ Yang-Yang-Fan
def node_matrix(fitted, n):
    A = np.zeros((len(fitted), n))
    for k, f in enumerate(fitted):
        A[k, f["up"]] += 1.0
        A[k, f["down"]] -= 1.0
        for r, s in f["slips"]:
            A[k, r] += float(s)
    return A


def yf_theta(vol, cols, A):
    n = vol.shape[0]
    rows = []
    for k in range(A.shape[0]):
        mem = np.nonzero(A[k])[0]
        for b0 in range(0, cols.size - BLOCK + 1, BLOCK):
            blk = cols[b0:b0 + BLOCK]
            sub = vol[np.ix_(mem, blk)]
            ok = np.all(np.isfinite(sub), axis=0)
            if ok.sum() < BLOCK // 2:
                continue
            row = np.zeros(n)
            row[mem] = A[k, mem] * sub[:, ok].mean(axis=1)
            rows.append(row)
    if not rows:
        return np.ones(n)
    M = np.array(rows)
    # ridge towards 1, written as extra rows, and theta bounded to a physically plausible
    # range: without the bounds a weakly determined sensor collapses towards theta = 0,
    # i.e. the balance is met by switching the sensor off, which no bias model intends
    scale = float(np.sqrt(np.mean(np.sum(M * M, axis=0)[np.any(M != 0, axis=0)])))
    lam = np.sqrt(LAMBDA) * scale
    Mr = np.vstack([M, lam * np.eye(n)])
    rhs = np.concatenate([np.zeros(M.shape[0]), lam * np.ones(n)])
    return lsq_linear(Mr, rhs, bounds=(THETA_MIN, THETA_MAX), method="bvls").x


class YF:
    def __init__(self, vol, fitted, ref_cols, test_cols, rng, draws=60):
        self.A = node_matrix(fitted, vol.shape[0])
        self.theta_ref = yf_theta(vol, ref_cols, self.A)
        # a sensor whose reference theta sits on a bound is not determined by the
        # moments; the published health test (theta against its estimated variance)
        # would not reject it, so it is not eligible to be named
        self.members = (np.any(self.A != 0, axis=0)
                        & (self.theta_ref > THETA_MIN + 0.01)
                        & (self.theta_ref < THETA_MAX - 0.01))
        stats = []
        for _ in range(draws):
            s0 = int(rng.integers(0, test_cols.size - SPAN))
            stats.append(self.stat(vol, test_cols[s0:s0 + SPAN])[0])
        st = np.array(stats)
        self.thr = np.where(self.members, np.quantile(st, 0.99, axis=0), np.inf)

    def stat(self, vol, cols):
        th = yf_theta(vol, cols, self.A)
        return np.abs(th / self.theta_ref - 1.0), th

    def run(self, faulted, row, cols):
        s, th = self.stat(faulted, cols)
        ratio = s / self.thr
        if not np.isfinite(ratio[row]) or ratio[row] <= 1.0:
            return None, None
        named = int(np.nanargmax(np.where(self.members, ratio, -np.inf)))
        return named, faulted[named, cols] * th[named] / self.theta_ref[named]


# ------------------------------------------------------------------ our arm
class Ours:
    def __init__(self, total, fitted, ref_cols, test_cols, rng):
        sub = dataset.Corridor(total.volumes[:, ref_cols], total.observed[:, ref_cols],
                               total.site_ids, [total.keys[j] for j in ref_cols], total.nodes)
        self.fitted = fitted
        self.calib = constrained.calibrate(sub, fitted, mode="scaled")
        resid = faults.residuals(total.volumes, fitted, self.calib)
        self.thresh, _ = faults.clean_thresholds(resid, test_cols, SPAN, rng)
        self.nodes_of = faults.node_membership(fitted)
        self.coeff = faults.coefficients(fitted, self.calib)
        self.pool_rank = sorted(r for r, i in self.nodes_of.items() if len(i) >= 2)

    def run(self, faulted, row, cols):
        resid = faults.residuals(faulted, self.fitted, self.calib)
        ratio = faults.span_statistic(resid, cols) / self.thresh
        vals = [ratio[i] for i in self.nodes_of.get(row, []) if np.isfinite(ratio[i])]
        if not vals or max(vals) <= 1.0:
            return None, None
        rk = faults.attribute(faults.signed_span_mean(resid, cols), self.thresh, self.fitted,
                              self.coeff, self.pool_rank, self.nodes_of)
        if not rk:
            return None, None
        named = rk[0][1]
        flow = faulted[named, cols]
        ok = np.isfinite(flow)
        typing = None
        if ok.sum() > 16:
            cut = float(np.median(flow[ok]))
            hi, lo = cols[ok][flow[ok] >= cut], cols[ok][flow[ok] < cut]
            if hi.size > 8 and lo.size > 8:
                typing = faults.classify_fault(
                    faults.signed_span_mean(resid, hi), faults.signed_span_mean(resid, lo),
                    self.thresh, self.fitted, self.coeff, named, self.nodes_of,
                    float(flow[ok][flow[ok] >= cut].mean()),
                    float(flow[ok][flow[ok] < cut].mean()))
        fixes = correction.correct(faulted, named, cols, self.fitted, self.calib,
                                   self.nodes_of, typing)
        return named, fixes["auto"]


# ------------------------------------------------------------------ experiment
def run(manifest, tag, seed=0, n_detectors=40, repeats=3):
    rng = np.random.default_rng(seed)
    total = classes.load(manifest).total
    vol = np.where(total.observed, total.volumes, np.nan)
    n_cols = total.shape[1]
    ref_cols, test_cols = np.arange(n_cols // 2), np.arange(n_cols // 2, n_cols)
    surveyed = evaluate.fit_node_signs(total)
    rel, _ = discover2.discover(total.volumes[:, ref_cols], total.observed[:, ref_cols])
    recovered = discover.relations_to_fitted(rel, total)

    arms = {"yf_surveyed": YF(vol, surveyed, ref_cols, test_cols, rng),
            "ours_surveyed": Ours(total, surveyed, ref_cols, test_cols, rng),
            "ours_recovered": Ours(total, recovered, ref_cols, test_cols, rng)}
    healthy = total.observed.mean(axis=1) > 0.9
    in_s = {r for r, i in faults.node_membership(surveyed).items() if len(i) >= 1}
    in_s2 = {r for r, i in faults.node_membership(surveyed).items() if len(i) >= 2}
    in_r2 = {r for r, i in faults.node_membership(recovered).items() if len(i) >= 2}
    coverage = {"detectors_live": int(total.shape[0]),
                "yf_surveyed_in_any_node": len([r for r in in_s if healthy[r]]),
                "yf_surveyed_identifiable": int(np.sum(arms["yf_surveyed"].members
                                                       & healthy)),
                "ours_surveyed_in_two_or_more": len([r for r in in_s2 if healthy[r]]),
                "ours_recovered_in_two_or_more": len([r for r in in_r2 if healthy[r]])}
    yf_ok = set(np.nonzero(arms["yf_surveyed"].members)[0].tolist())
    pool = sorted(r for r in in_s2 & in_r2 & yf_ok if healthy[r])
    if len(pool) > n_detectors:
        pool = [pool[i] for i in sorted(rng.choice(len(pool), n_detectors, replace=False))]
    print(tag, coverage, "pool", len(pool), flush=True)

    out = {"manifest": manifest, "surveyed_nodes": len(surveyed),
           "recovered_relations": len(recovered), "coverage": coverage,
           "pool": len(pool), "repeats": repeats, "cases": []}
    for mode, mag in CASES:
        acc = {a: {"before": 0.0, "after": 0.0, "right": 0, "wrong": 0, "damage": 0.0,
                   "right_before": 0.0, "right_after": 0.0}
               for a in arms}
        n = 0
        for row in pool:
            for _ in range(repeats):
                s0 = int(rng.integers(0, test_cols.size - SPAN))
                cols = test_cols[s0:s0 + SPAN]
                if total.observed[row, cols].mean() <= 0.8:
                    continue
                faulted = vol if mode == "none" else \
                    faults.inject_total(vol, row, cols, mode, mag)
                live = np.isfinite(vol[row, cols]) & np.isfinite(faulted[row, cols])
                err0 = float(np.mean(np.abs(faulted[row, cols][live] - vol[row, cols][live])))
                n += 1
                for a, arm in arms.items():
                    named, fixed = arm.run(faulted, row, cols)
                    acc[a]["before"] += err0
                    if named is None:
                        acc[a]["after"] += err0
                    elif named == row and mode != "none":
                        acc[a]["right"] += 1
                        e1 = float(np.mean(np.abs(fixed[live] - vol[row, cols][live])))
                        acc[a]["after"] += e1
                        acc[a]["right_before"] += err0
                        acc[a]["right_after"] += e1
                    else:
                        acc[a]["wrong"] += 1
                        acc[a]["after"] += err0
                        m = np.isfinite(vol[named, cols]) & np.isfinite(fixed)
                        acc[a]["damage"] += float(np.mean(np.abs(fixed[m]
                                                                 - vol[named, cols][m])))
        e = {"mode": mode, "magnitude": mag, "trials": n}
        for a, v in acc.items():
            tot_after = v["after"] + v["damage"]
            e[a] = {"named_correctly": round(v["right"] / n, 4) if n else None,
                    "wrong_corrections": v["wrong"],
                    "mae_before": round(v["before"] / n, 2) if n else None,
                    "mae_after_incl_damage": round(tot_after / n, 2) if n else None,
                    "net_error_removed": (round(1 - tot_after / v["before"], 4)
                                          if v["before"] else None),
                    "damage_per_trial": round(v["damage"] / n, 2) if n else None,
                    "error_removed_when_named_correctly": (
                        round(1 - v["right_after"] / v["right_before"], 4)
                        if v["right_before"] else None)}
        out["cases"].append(e)
        print(tag, mode, mag, {a: (e[a]["named_correctly"], e[a]["net_error_removed"],
                                   e[a]["wrong_corrections"]) for a in arms}, flush=True)
    with open(os.path.join(RESULTS, "yf_compare_%s.json" % tag), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "M1"
    if which == "M1":
        run("window_M1_A.json", "M1_A")
    else:
        run("window_full_M25_A.json", "full_M25_A")
