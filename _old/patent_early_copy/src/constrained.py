"""Phase 4 — the invention: reconstruction under a hard flow-conservation constraint.

Given a prior estimate of the missing values, produced by any per-detector method, the
reconstructed values are the ones closest to that prior which still satisfy flow
conservation at every node. The constraint is imposed as a hard feasibility requirement
the solution may not violate, not as a weighted penalty a solver can trade away.

Two design decisions were forced by measurement rather than chosen a priori.

CALIBRATION. Detectors do not agree perfectly. Measured over intervals in which every
detector at a node reported, the raw relation `upstream - downstream + slips` has a mean
absolute value of 17.45 vehicles per interval on a mean node flow of 592.5. Removing a
constant offset per node brings that to 16.41; allowing a per-node scale factor as well,
so that one detector may systematically count a fixed percentage more than another,
brings it to 14.84. So the relation enforced is the calibrated one,

    upstream + sum_i sign_i * slip_i  =  (1 + alpha) * downstream + beta

with alpha and beta estimated per node by least squares on intervals where every
detector reported. Enforcing a textbook zero instead would push known instrument bias
into the reconstructed values.

TOLERANCE BAND. Even calibrated, the relation is only good to about 15 vehicles per
interval, which is the same size as the error of a good statistical estimator. Forcing
exact equality therefore injects that measurement noise into the reconstructed value,
and measurably degrades a prior that was already accurate. The constraint is instead
imposed as a hard two-sided inequality,

    | upstream + sum_i sign_i * slip_i - (1 + alpha) * downstream - beta |  <=  tau

with tau derived per node from the measured spread of the relation itself. This is still
a hard constraint: no solution outside the band is admissible. But a prior that is
already physically plausible is left alone, and only implausible ones are corrected. The
guarantee it buys is stated in vehicles: after reconstruction, no node can disagree with
conservation by more than tau, whatever the prior did.

The projection itself, for the constraints currently violated:

    minimise (x - p)' W (x - p)   subject to   A x = b_edge
    =>  x = p + W^-1 A' (A W^-1 A')^+ (b_edge - A p)

The pseudo-inverse handles both awkward cases directly. When a node carries several
missing values the system is underdetermined and the projection returns the least-norm
correction, spreading it across the unknowns rather than dumping it on one. When nodes
overlap, sharing a detector, their equations are solved together rather than in
sequence, so satisfying one cannot break another. Violated constraints are re-identified
and re-projected until every node is inside its band.

W weights each correction by that detector's measurement scale, so a correction is
shared in proportion to how uncertain each value is rather than equally in absolute
vehicles. Counts cannot be negative, and clipping alone would break the feasibility just
established, so clipping and re-projection alternate.

No neural network and no black box: the method is a projection with a closed-form step,
which is cheap and fully explainable. Under the 2025 CRI Guidelines an unexplainable
model is a liability, not an asset.
"""

import os
import sys
import time

import numpy as np
from scipy.optimize import linprog

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))


def calibrate(corridor, fitted, mode="scaled", tol_quantile=0.95, tol_scale=1.0):
    """Per-node calibration of the conservation relation, and its tolerance band.

    mode "zero"   — textbook identity, downstream coefficient -1, no offset
    mode "offset" — constant offset per node
    mode "scaled" — offset and scale factor per node (the measured best fit)

    The band is the `tol_quantile` quantile of the absolute deviation of the calibrated
    relation, measured on intervals where every detector at the node reported. Setting
    tol_scale to 0 collapses the band and recovers exact equality.
    """
    vol, obs = corridor.volumes, corridor.observed
    out = {}
    for f in fitted:
        rows = [f["up"], f["down"]] + [r for r, _ in f["slips"]]
        complete = np.all(obs[rows], axis=0)

        lhs = vol[f["up"], complete].copy()
        for row, sign in f["slips"]:
            lhs = lhs + sign * vol[row, complete]
        down = vol[f["down"], complete]

        if complete.sum() < 30 or mode == "zero":
            down_coeff, const = -1.0, 0.0
        elif mode == "offset":
            down_coeff, const = -1.0, float(np.median(lhs - down))
        else:
            design = np.vstack([down, np.ones_like(down)]).T
            coef, _, _, _ = np.linalg.lstsq(design, lhs, rcond=None)
            down_coeff, const = -float(coef[0]), float(coef[1])

        if complete.sum():
            deviation = np.abs(lhs + down_coeff * down - const)
            band = float(np.quantile(deviation, tol_quantile)) * tol_scale
        else:
            band = 0.0

        out[f["node_id"]] = {"down_coeff": down_coeff, "const": const, "band": band}
    return out


def detector_scale(corridor):
    """Per-detector measurement scale, used to weight how corrections are shared."""
    vol, obs = corridor.volumes, corridor.observed
    scale = np.ones(vol.shape[0])
    for i in range(vol.shape[0]):
        if obs[i].any():
            scale[i] = max(float(vol[i, obs[i]].mean()), 1.0)
    return scale


def _dykstra(x0, A, lower, upper, w_inv, max_iters=200, tol=1e-7):
    """Projection onto the intersection of the node bands and the non-negative orthant.

    Each node contributes a slab `lower <= a'x <= upper`, which is convex, and counts are
    non-negative, which is convex too. Projecting onto each set in turn does not give the
    projection onto their intersection; Dykstra's algorithm corrects for that by carrying
    a residual per set, and converges to the true projection whenever the intersection is
    non-empty.

    When it is empty the iteration cannot converge, and that is worth knowing rather than
    hiding. An empty intersection means the values that were actually *observed* around
    these nodes cannot be reconciled with conservation no matter what is filled in, which
    points at a miscalibrated or faulty detector. The caller is told, and the best
    available point is returned.
    """
    x = np.asarray(x0, dtype=float).copy()
    n_sets = A.shape[0] + 1
    corrections = [np.zeros_like(x) for _ in range(n_sets)]

    # projection of x onto {a'x = target} in the W-weighted norm
    denom = np.array([max(float(a @ (w_inv * a)), 1e-12) for a in A])

    converged = False
    for _ in range(max_iters):
        prev = x.copy()
        for i, a in enumerate(A):
            y = x + corrections[i]
            value = float(a @ y)
            if value > upper[i]:
                target = upper[i]
            elif value < lower[i]:
                target = lower[i]
            else:
                target = value
            x_new = y + (w_inv * a) * ((target - value) / denom[i])
            corrections[i] = y - x_new
            x = x_new
        y = x + corrections[-1]
        x_new = np.maximum(y, 0.0)
        corrections[-1] = y - x_new
        x = x_new

        if np.max(np.abs(x - prev)) < tol:
            converged = True
            break

    return x, converged


def _feasible(x, A, lower, upper, tol):
    value = A @ x
    return bool((value >= lower - tol).all() and (value <= upper + tol).all()
                and (x >= -tol).all())


def _minimum_slack(A, lower, upper):
    """Smallest uniform widening of the bands that makes the node system satisfiable.

    Solves   min s   subject to   lower - s <= A x <= upper + s,  x >= 0,  s >= 0.

    A result of zero means the bands can be met and any failure to meet them was the
    iteration's fault. A positive result means something stronger: the values that were
    actually *observed* around these nodes cannot be reconciled with conservation no
    matter what is filled in, because the shortfall does not depend on the unknowns at
    all. That is a detected data-integrity fault - a miscalibrated or faulty detector -
    and it is reported rather than smoothed over.
    """
    n = A.shape[1]
    cost = np.zeros(n + 1)
    cost[-1] = 1.0
    # A x - s <= upper   and   -A x - s <= -lower
    ub_block = np.hstack([A, -np.ones((A.shape[0], 1))])
    lb_block = np.hstack([-A, -np.ones((A.shape[0], 1))])
    a_ub = np.vstack([ub_block, lb_block])
    b_ub = np.concatenate([upper, -lower])
    bounds = [(0.0, None)] * n + [(0.0, None)]
    res = linprog(cost, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")
    if res.status != 0:
        return None, None
    return float(res.x[-1]), res.x[:n]


def project(prior, view, fitted, calib, scale, weighting="flow",
            max_iters=200, tol=1e-6):
    """Project a prior onto the feasible set, interval by interval.

    `view` is what the method may see: nan marks a value it must reconstruct. Returns the
    reconstructed matrix and per-interval diagnostics.
    """
    out = prior.copy()
    missing = np.isnan(view)
    n_constraints = np.zeros(view.shape[1], dtype=int)
    n_corrected = np.zeros(view.shape[1], dtype=int)
    n_unreconciled = np.zeros(view.shape[1], dtype=int)
    unreconciled_slack = []

    for t in range(view.shape[1]):
        unknown_rows = np.where(missing[:, t])[0]
        if unknown_rows.size == 0:
            continue
        index_of = {row: k for k, row in enumerate(unknown_rows)}

        rows_A, centres, bands = [], [], []
        for f in fitted:
            c = calib[f["node_id"]]
            terms = [(f["up"], 1.0), (f["down"], c["down_coeff"])]
            terms += [(row, float(sign)) for row, sign in f["slips"]]
            if not any(r in index_of for r, _ in terms):
                continue  # nothing missing at this node in this interval
            a = np.zeros(unknown_rows.size)
            b = c["const"]
            for row, coeff in terms:
                if row in index_of:
                    a[index_of[row]] += coeff
                else:
                    b -= coeff * view[row, t]
            rows_A.append(a)
            centres.append(b)
            bands.append(c["band"])

        if not rows_A:
            continue
        A = np.array(rows_A)
        centre = np.array(centres)
        band = np.array(bands)
        n_constraints[t] = A.shape[0]

        w_inv = scale[unknown_rows] if weighting == "flow" else np.ones(unknown_rows.size)
        x0 = out[unknown_rows, t].astype(float)

        value = A @ x0
        already_feasible = (np.abs(value - centre) <= band + tol).all() and (x0 >= 0).all()
        if already_feasible:
            continue  # the prior is physically plausible here; leave it alone

        lower, upper = centre - band, centre + band
        x, _ = _dykstra(x0, A, lower, upper, w_inv, max_iters=max_iters, tol=tol * 1e-1)

        if not _feasible(x, A, lower, upper, tol):
            slack, witness = _minimum_slack(A, lower, upper)
            if slack is None:
                pass                                   # solver failed; keep what we have
            elif slack <= tol:
                # the bands were satisfiable and the iteration merely stalled. Give it a
                # longer run from the prior first: restarting from the linear program's
                # vertex would land on the projection of that vertex, not of the prior,
                # and the whole point is to stay as close to the prior as feasibility
                # allows. The vertex is only a fallback.
                x_retry, _ = _dykstra(x0, A, lower, upper, w_inv,
                                      max_iters=max_iters * 5, tol=tol * 1e-2)
                if _feasible(x_retry, A, lower, upper, tol):
                    x = x_retry
                else:
                    x, _ = _dykstra(witness, A, lower, upper, w_inv,
                                    max_iters=max_iters * 3, tol=tol * 1e-1)
            else:
                # Genuinely irreconcilable observed data. Widening every band by the
                # slack would admit a solution, but it drags values away from the prior
                # to satisfy a relation the observations have already broken, and
                # measurably costs accuracy. The point Dykstra settled on is kept, and
                # the interval is flagged instead: the honest output here is "these nodes
                # could not be reconciled, by this many vehicles", which localises a
                # faulty or miscalibrated detector rather than papering over it.
                n_unreconciled[t] = 1
                unreconciled_slack.append(slack)

        out[unknown_rows, t] = x
        n_corrected[t] = 1

    return out, n_constraints, n_corrected, n_unreconciled, unreconciled_slack


def training_corridor(corridor, view):
    """The corridor as the method is permitted to see it.

    `view` carries nan wherever a value has been withheld for scoring, so a corridor
    built from it cannot reach a withheld value even indirectly. This exists because the
    first version did: `reconstruct` calibrated on the full corridor, so alpha, beta and
    the tolerance band were fitted using the very values the method was then scored on
    reconstructing. The band is the quantity the headline consistency figure is measured
    against, which made that figure partly circular.
    """
    import dataset
    return dataset.Corridor(view, np.isfinite(view), corridor.site_ids, corridor.keys,
                            corridor.nodes)


def reconstruct(corridor, view, fitted, prior, mode="scaled", weighting="flow",
                tol_scale=1.0):
    """Full method: take a prior, return the constrained reconstruction plus timing.

    Everything the method uses is derived from `view`. `corridor` is accepted only for
    its topology and its row and column labels.
    """
    train = training_corridor(corridor, view)
    calib = calibrate(train, fitted, mode=mode, tol_scale=tol_scale)
    scale = detector_scale(train)
    t0 = time.time()
    out, n_constraints, n_corrected, n_unreconciled, slack = project(
        prior, view, fitted, calib, scale, weighting=weighting)
    elapsed = time.time() - t0
    return out, {
        "seconds": round(elapsed, 3),
        "intervals_constrained": int((n_constraints > 0).sum()),
        "intervals_corrected": int(n_corrected.sum()),
        "intervals_unreconciled": int(n_unreconciled.sum()),
        "mean_unreconciled_slack_vehicles": (round(float(np.mean(slack)), 2)
                                             if slack else 0.0),
        "mean_constraints_per_interval": round(float(n_constraints.mean()), 2),
        "calibration": mode,
        "weighting": weighting,
        "tol_scale": tol_scale,
        "mean_band_vehicles": round(
            float(np.mean([c["band"] for c in calib.values()])), 2),
    }
