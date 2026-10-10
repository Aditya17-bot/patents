"""Phase 11 - the fault that was there before anyone looked.

Phase 9 detects the *onset* of a fault: it fits each node's calibration on a clean
stretch and then notices when the residual moves. A reviewer put the obvious question to
that, and it is a good one. A loop whose sensitivity has drifted is usually a chronic
condition, not an event. If the detector was already miscounting when the calibration was
fitted, its bias is absorbed into that node's alpha and beta, the residual never moves,
and the method is structurally blind to it. Worse, the corrupted calibration is then used
to judge everything else at that node.

That blind spot is also, on inspection, where the remaining novelty is. Every fault
detection and isolation method in the control-engineering literature - parity space,
structured residuals, gross error detection, power-system state estimation - begins from a
*known and correct* system model, and asks which sensor disagrees with it. None of them
question the model, because in those settings the model is a flowsheet or an admittance
matrix that was surveyed, not inferred. Here the model is fitted from the very sensors
that are under suspicion, which is circular unless something breaks the circle.

This module breaks it. The observation is that a per-detector bias cannot hide in the
calibration coefficients without leaving a trace, because each detector enters the nodes
it belongs to with *different* coefficients: +1 where it is the upstream detector,
-(1 + alpha) where it is the downstream one, and the fitted sign where it is a slip road.
So if detector d carries a constant bias b, it pushes node n's fitted offset by
c(n, d) * b, and the vector of fitted offsets across the whole network satisfies

    beta  =  C b  +  (genuine per-node effects)

with C the known coefficient matrix. Solving that for a *sparse* b recovers which
detectors carry an anomalous constant offset and how large it is - without ever having
seen those detectors behave correctly.

The sparsity is what makes it a fault detector rather than a re-parameterisation. Every
detector has some small offset; that is ordinary instrument disagreement and it is what
the calibration is for. A fault is an outlier in that population, and the l1 solution
finds outliers rather than distributing the explanation evenly.

Identifiability has a limit that is worth stating rather than discovering later. If every
detector in the network were shifted by the same amount the node balances would be
unchanged, so the component of b lying in the null space of C is not recoverable. What is
recoverable is b up to that null space, which is exactly the part that distinguishes one
detector from its neighbours - and that is the part a fault lives in.
"""

import json
import os
import sys

import numpy as np
from scipy.optimize import linprog

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import constrained
import dataset
import evaluate
import faults

RESULTS = os.path.join(ROOT, "results")


def coefficient_matrix(fitted, calib, n_sites):
    """C, with one row per node and one column per detector."""
    C = np.zeros((len(fitted), n_sites))
    for i, f in enumerate(fitted):
        c = calib[f["node_id"]]
        C[i, f["up"]] += 1.0
        C[i, f["down"]] += c["down_coeff"]
        for row, sign in f["slips"]:
            C[i, row] += float(sign)
    return C


def offsets(fitted, calib):
    """beta, the fitted constant offset of each node's calibrated relation."""
    return np.array([calib[f["node_id"]]["const"] for f in fitted])


def decompose(C, beta, weights=None, ridge=1e-6):
    """Sparsest per-detector bias vector consistent with the fitted node offsets.

    Solved as a linear program in the standard l1 form: split b into non-negative
    positive and negative parts, and bound the weighted residual of C b - beta by a
    per-node slack that is itself minimised alongside the l1 norm.

        min  sum_j (b+_j + b-_j) * ridge  +  sum_i s_i
        s.t. -s <= W (C (b+ - b-) - beta) <= s,   b+, b-, s >= 0

    The ridge weight is small, so the fit comes first and sparsity only breaks ties
    between explanations that fit equally well. That ordering matters: a large sparsity
    weight would suppress a real second fault to keep the answer tidy.
    """
    n_nodes, n_sites = C.shape
    if weights is None:
        weights = np.ones(n_nodes)
    W = np.diag(weights)
    A = W @ C
    b = W @ beta

    # variables: [b+ (n_sites), b- (n_sites), s (n_nodes)]
    n_var = 2 * n_sites + n_nodes
    cost = np.concatenate([np.full(n_sites, ridge), np.full(n_sites, ridge),
                           np.ones(n_nodes)])

    upper = np.hstack([A, -A, -np.eye(n_nodes)])
    lower = np.hstack([-A, A, -np.eye(n_nodes)])
    a_ub = np.vstack([upper, lower])
    b_ub = np.concatenate([b, -b])

    res = linprog(cost, A_ub=a_ub, b_ub=b_ub,
                  bounds=[(0.0, None)] * n_var, method="highs")
    if res.status != 0:
        return None, None
    bias = res.x[:n_sites] - res.x[n_sites:2 * n_sites]
    residual = C @ bias - beta
    return bias, residual


def flow_regimes(corridor):
    """Split the record into its busier and quieter halves, once, for the whole corridor.

    A constant offset contributes the same number of vehicles in both halves; a gain
    error contributes in proportion to the flow passing through the detector. Decomposing
    separately in each half therefore separates the two, and does it for a chronic fault,
    where there is no clean period to compare against - only two operating points.
    """
    total = np.nansum(corridor.volumes, axis=0)
    cut = np.nanmedian(total[np.isfinite(total)])
    high = np.where(total >= cut)[0]
    low = np.where(total < cut)[0]
    return high, low


def restrict(corridor, cols):
    return dataset.Corridor(corridor.volumes[:, cols], corridor.observed[:, cols],
                            corridor.site_ids, [corridor.keys[j] for j in cols],
                            corridor.nodes)


def detector_flow(corridor, cols):
    """Mean flow through each detector in the given intervals."""
    out = np.zeros(corridor.shape[0])
    for i in range(corridor.shape[0]):
        seg = corridor.volumes[i, cols]
        seg = seg[np.isfinite(seg)]
        if seg.size:
            out[i] = float(seg.mean())
    return out


def decompose_two_regime(corridor, fitted, weights, high, low, n_sites):
    """Per-detector gain and offset, recovered from the calibration at two flow levels.

    Returns (gain, offset, b_high, b_low). Solving

        b_high = gain * F_high + offset
        b_low  = gain * F_low  + offset

    per detector gives both, with the gain expressed as a fraction of that detector's own
    flow. Detectors whose two operating points are too close to separate are returned
    with a gain of zero rather than a number divided by nearly nothing.
    """
    # Deliberately the RIGID calibration, with the downstream coefficient pinned at -1
    # and only the offset free. The scale-and-offset calibration is what makes the
    # reconstruction work, and it is exactly what hides a chronic gain fault: a detector
    # counting 3% high is absorbed into its nodes' alpha and disappears. Refitting
    # without that degree of freedom leaves the fault nowhere to go but the offset, where
    # it shows up as flow-dependent and is therefore separable from a true offset.
    out = []
    for cols in (high, low):
        sub = restrict(corridor, cols)
        calib = constrained.calibrate(sub, fitted, mode="offset")
        C = coefficient_matrix(fitted, calib, n_sites)
        bias, _ = decompose(C, offsets(fitted, calib), weights)
        out.append(bias if bias is not None else np.zeros(n_sites))
    b_high, b_low = out

    f_high = detector_flow(corridor, high)
    f_low = detector_flow(corridor, low)
    spread = f_high - f_low
    gain = np.where(np.abs(spread) > 1.0, (b_high - b_low) / np.where(spread == 0, 1, spread), 0.0)
    offset = b_low - gain * f_low
    return gain, offset, b_high, b_low


def inject_chronic(volumes, row, mode, magnitude):
    """Fault the detector across the ENTIRE record, so no clean period exists."""
    out = volumes.copy()
    live = np.isfinite(out[row])
    if mode == "offset":
        out[row, live] = np.maximum(out[row, live] + magnitude, 0.0)
    elif mode == "scale":
        out[row, live] = out[row, live] * magnitude
    else:
        raise ValueError(mode)
    return out


def run(manifest="window_full_M25_A.json", seed=0, n_detectors=25,
        out_name="chronic.json"):
    rng = np.random.default_rng(seed)
    corridor = dataset.load(manifest)
    fitted = evaluate.fit_node_signs(corridor)
    n_sites = corridor.shape[0]
    nodes_of = faults.node_membership(fitted)

    base_calib = constrained.calibrate(corridor, fitted, mode="scaled")
    C = coefficient_matrix(fitted, base_calib, n_sites)
    beta = offsets(fitted, base_calib)

    # a node whose relation is loose should not out-vote a tight one
    band = np.array([base_calib[f["node_id"]]["band"] for f in fitted])
    weights = 1.0 / np.maximum(band, 1.0)

    base_bias, base_resid = decompose(C, beta, weights)
    if base_bias is None:
        print("linear program failed on the unfaulted network")
        return None

    high, low = flow_regimes(corridor)
    base_gain, base_offset, _, _ = decompose_two_regime(
        corridor, fitted, weights, high, low, n_sites)

    pool = [r for r, idx in nodes_of.items()
            if len(idx) >= 2 and corridor.observed[r].mean() > 0.9]
    print("corridor %d detectors, %d nodes; %d detectors belong to >=2 nodes"
          % (n_sites, len(fitted), len(pool)))
    print("baseline per-detector offsets recovered from the network's own calibration:")
    active = base_bias[np.abs(base_bias) > 1e-6]
    print("  non-zero for %d of %d detectors; median |offset| %.2f, p90 %.2f, max %.2f"
          % (active.size, n_sites,
             np.median(np.abs(active)) if active.size else 0.0,
             np.quantile(np.abs(active), 0.9) if active.size else 0.0,
             np.abs(active).max() if active.size else 0.0))
    print("  residual of the decomposition: median %.2f vehicles, max %.2f"
          % (np.median(np.abs(base_resid)), np.abs(base_resid).max()))

    tested = list(pool)
    if len(tested) > n_detectors:
        pick = rng.choice(len(tested), size=n_detectors, replace=False)
        tested = [tested[i] for i in sorted(pick)]

    out = {"manifest": manifest, "seed": seed, "nodes": len(fitted),
           "detectors": n_sites, "detectors_multinode": len(pool),
           "detectors_tested": len(tested),
           "baseline": {
               "nonzero_offsets": int(active.size),
               "median_abs_offset": round(float(np.median(np.abs(active))), 3) if active.size else 0.0,
               "max_abs_offset": round(float(np.abs(active).max()), 3) if active.size else 0.0,
               "median_abs_residual": round(float(np.median(np.abs(base_resid))), 3),
           },
           "cases": []}

    print("\n%-28s %7s %10s %10s %10s"
          % ("injected chronic fault", "trials", "recovered", "ranked 1st", "in top 3"))

    for mode, magnitude in [("offset", -30.0), ("offset", -15.0), ("offset", -8.0),
                            ("offset", 8.0), ("offset", 15.0), ("offset", 30.0),
                            ("scale", 0.95), ("scale", 0.98),
                            ("scale", 1.02), ("scale", 1.05)]:
        recovered, top1, top3, trials, shifts = 0, 0, 0, 0, []
        for row in tested:
            faulted = inject_chronic(corridor.volumes, row, mode, magnitude)
            sub = dataset.Corridor(faulted, corridor.observed, corridor.site_ids,
                                   corridor.keys, corridor.nodes)
            gain, offset, _, _ = decompose_two_regime(
                sub, fitted, weights, high, low, n_sites)
            trials += 1

            # the fault is the CHANGE in the recovered parameter, since every detector
            # carries some ordinary offset of its own that is not a fault
            if mode == "offset":
                delta = offset - base_offset
                expected = magnitude
            else:
                delta = gain - base_gain
                expected = magnitude - 1.0

            order = np.argsort(-np.abs(delta))
            order = [int(r) for r in order if r in nodes_of and len(nodes_of[r]) >= 2]
            top1 += int(order[0] == row)
            top3 += int(row in order[:3])
            shifts.append(float(delta[row]))

            if abs(delta[row] - expected) < 0.35 * abs(expected):
                recovered += 1

        if not trials:
            continue
        entry = {"mode": mode, "magnitude": magnitude, "trials": trials,
                 "identified_top1": round(top1 / trials, 4),
                 "identified_top3": round(top3 / trials, 4),
                 "median_recovered_shift": round(float(np.median(shifts)), 4),
                 "true_shift": magnitude if mode == "offset" else round(magnitude - 1.0, 4),
                 "magnitude_within_35pct": round(recovered / trials, 4)}
        out["cases"].append(entry)

        label = ("constant %s of %.0f veh/interval, all month"
                 % ("loss" if magnitude < 0 else "gain", abs(magnitude))
                 if mode == "offset"
                 else "%s-count by %.0f%%, all month"
                 % ("under" if magnitude < 1 else "over", abs(100 * (magnitude - 1))))
        print("%-44s %6d %9.4f %9.4f %8.1f%% %8.1f%%"
              % (label, trials, entry["true_shift"], entry["median_recovered_shift"],
                 100 * entry["identified_top1"], 100 * entry["identified_top3"]))

    # control: no fault at all, so any identification is spurious
    print("\ncontrol (no fault injected): the decomposition is unchanged by construction,")
    print("so the meaningful control is the baseline offset spread printed above.")

    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/%s" % out_name)
    return out


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window_full_M25_A.json"
    name = sys.argv[2] if len(sys.argv) > 2 else "chronic.json"
    run(manifest, out_name=name)
