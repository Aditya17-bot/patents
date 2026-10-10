"""Total and class balances enforced together, on one vector of unknowns.

Phase 8 measured that imposing conservation on each vehicle length class separately is
strictly worse than imposing it on the total, and the reason is physical. The four class
counts carry a classification error the total does not: a vehicle close to a bin
boundary is booked into different bins by different detectors. Those errors are
anti-correlated between adjacent bins, so they cancel when the four are added. The
measured tolerance bands say it outright - the shortest class alone needs a band of 60.1
vehicles where the total needs 46.5.

So the class relations are weaker than the total relation, but they are not the same
relation. Adding them up recovers the total one, which means the total constraint carries
information the four class constraints do not, and there is no reason to discard it.

This module therefore solves for the class-resolved values under both sets of
constraints at once:

    for every node n, every interval t
        | sum_c  ( up_c + sum_i sign_i slip_i,c - (1+a_n) down_c ) - b_n |  <=  tau_n
        | up_c + sum_i sign_i slip_i,c - (1+a_n,c) down_c - b_n,c |         <=  tau_n,c

The first line is exactly the constraint the total-only method imposes; the second adds
the per-class relations on top. The unknowns are the class-resolved values, and the
reconstructed total is their sum.

The prior is the total prior split by each detector's own measured class composition at
that time of day, so the starting point sums to precisely the total prior. That makes the
comparison clean: in the total coordinate the method starts exactly where the total-only
method starts, and any difference in the answer is attributable to the class constraints
alone and not to a different starting estimate.
"""

import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import classes
import constrained

N_CLASSES = len(classes.CLASS_NAMES)


def composition(cc, view_by_class, slot, weekend, floor=1e-6):
    """Each detector's class mix, per time-of-day slot and day type.

    Learned only from what the method is allowed to see. Heavy vehicles run at different
    hours from cars, so a single mix per detector would be a worse split than the data
    supports; a mix per slot costs nothing and is honest about that.
    """
    n_sites, n_cols = view_by_class[classes.CLASS_NAMES[0]].shape
    stack = np.stack([view_by_class[n] for n in classes.CLASS_NAMES])
    share = np.full((N_CLASSES, n_sites, n_cols), 1.0 / N_CLASSES)

    for is_we in (False, True):
        for s in range(96):
            cols = np.where((slot == s) & (weekend == is_we))[0]
            if cols.size == 0:
                continue
            block = stack[:, :, cols]                       # classes x sites x cols
            with np.errstate(invalid="ignore"):
                totals = np.nansum(block, axis=0)           # sites x cols
                counts = np.sum(~np.isnan(block[0]), axis=1)
                sums = np.nansum(block, axis=2)             # classes x sites
            denom = np.nansum(totals, axis=1)               # sites
            for i in range(n_sites):
                if counts[i] == 0 or denom[i] <= floor:
                    continue
                mix = sums[:, i] / denom[i]
                share[:, i, cols] = mix[:, None]

    # a detector with no history at all in some slot keeps the flat split
    share = np.where(np.isfinite(share), share, 1.0 / N_CLASSES)
    total = share.sum(axis=0, keepdims=True)
    total[total <= floor] = 1.0
    return share / total


def project(prior_total, share, view_total, view_by_class, fitted,
            calib_total, calib_class, scale, use_total=True, use_class=True,
            max_iters=200, tol=1e-6):
    """Project the class-split prior onto the intersection of both constraint sets.

    Returns the four reconstructed class matrices and per-interval diagnostics. The
    caller sums them to get the reconstructed total.
    """
    n_sites, n_cols = view_total.shape
    missing = np.isnan(view_total)

    out = np.stack([np.where(missing, prior_total * share[c], view_by_class[name])
                    for c, name in enumerate(classes.CLASS_NAMES)])

    n_constraints = np.zeros(n_cols, dtype=int)
    n_corrected = np.zeros(n_cols, dtype=int)
    n_unreconciled = np.zeros(n_cols, dtype=int)
    slack_seen = []

    for t in range(n_cols):
        unknown_rows = np.where(missing[:, t])[0]
        if unknown_rows.size == 0:
            continue
        index_of = {row: k for k, row in enumerate(unknown_rows)}
        n_unknown = unknown_rows.size
        width = N_CLASSES * n_unknown

        rows_A, centres, bands = [], [], []
        for f in fitted:
            terms_total = [(f["up"], 1.0),
                           (f["down"], calib_total[f["node_id"]]["down_coeff"])]
            terms_total += [(row, float(sign)) for row, sign in f["slips"]]
            if not any(r in index_of for r, _ in terms_total):
                continue

            if use_total:
                c = calib_total[f["node_id"]]
                a = np.zeros(width)
                b = c["const"]
                for row, coeff in terms_total:
                    if row in index_of:
                        k = index_of[row]
                        for cl in range(N_CLASSES):
                            a[N_CLASSES * k + cl] += coeff
                    else:
                        b -= coeff * view_total[row, t]
                rows_A.append(a)
                centres.append(b)
                bands.append(c["band"])

            if use_class:
                for cl, name in enumerate(classes.CLASS_NAMES):
                    cc_ = calib_class[name][f["node_id"]]
                    terms = [(f["up"], 1.0), (f["down"], cc_["down_coeff"])]
                    terms += [(row, float(sign)) for row, sign in f["slips"]]
                    a = np.zeros(width)
                    b = cc_["const"]
                    ok = True
                    for row, coeff in terms:
                        if row in index_of:
                            a[N_CLASSES * index_of[row] + cl] += coeff
                        else:
                            v = view_by_class[name][row, t]
                            if not np.isfinite(v):
                                ok = False
                                break
                            b -= coeff * v
                    if ok:
                        rows_A.append(a)
                        centres.append(b)
                        bands.append(cc_["band"])

        if not rows_A:
            continue
        A = np.array(rows_A)
        centre = np.array(centres)
        band = np.array(bands)
        n_constraints[t] = A.shape[0]

        x0 = np.empty(width)
        w_inv = np.empty(width)
        for k, row in enumerate(unknown_rows):
            for cl in range(N_CLASSES):
                x0[N_CLASSES * k + cl] = out[cl, row, t]
                # a correction is shared in proportion to how much flow that class of
                # that detector actually carries, so a heavy-vehicle count is not asked
                # to absorb a correction sized for the car count
                w_inv[N_CLASSES * k + cl] = max(scale[row] * share[cl, row, t], 1.0)

        value = A @ x0
        if (np.abs(value - centre) <= band + tol).all() and (x0 >= 0).all():
            continue

        lower, upper = centre - band, centre + band
        x, _ = constrained._dykstra(x0, A, lower, upper, w_inv,
                                    max_iters=max_iters, tol=tol * 1e-1)

        if not constrained._feasible(x, A, lower, upper, tol):
            slack, witness = constrained._minimum_slack(A, lower, upper)
            if slack is None:
                pass
            elif slack <= tol:
                x_retry, _ = constrained._dykstra(x0, A, lower, upper, w_inv,
                                                  max_iters=max_iters * 5, tol=tol * 1e-2)
                if constrained._feasible(x_retry, A, lower, upper, tol):
                    x = x_retry
                else:
                    x, _ = constrained._dykstra(witness, A, lower, upper, w_inv,
                                                max_iters=max_iters * 3, tol=tol * 1e-1)
            else:
                n_unreconciled[t] = 1
                slack_seen.append(slack)

        for k, row in enumerate(unknown_rows):
            for cl in range(N_CLASSES):
                out[cl, row, t] = x[N_CLASSES * k + cl]
        n_corrected[t] = 1

    diag = {
        "intervals_constrained": int((n_constraints > 0).sum()),
        "intervals_corrected": int(n_corrected.sum()),
        "intervals_unreconciled": int(n_unreconciled.sum()),
        "mean_unreconciled_slack_vehicles": (round(float(np.mean(slack_seen)), 2)
                                             if slack_seen else 0.0),
        "mean_constraints_per_interval": round(float(n_constraints.mean()), 2),
        "use_total": use_total, "use_class": use_class,
    }
    return out, diag


def reconstruct(cc, hidden, prior_total, fitted, slot, weekend,
                use_total=True, use_class=True, mode="scaled"):
    """Convenience wrapper: mask in, reconstructed total and class matrices out."""
    import dataset

    view_total = dataset.train_view(cc.total, hidden)
    view_by_class = {}
    for name in classes.CLASS_NAMES:
        v = cc.by_class[name].copy()
        v[hidden] = np.nan
        view_by_class[name] = v

    calib_total = constrained.calibrate(cc.total, fitted, mode=mode)
    calib_class = {name: constrained.calibrate(cc.view(name), fitted, mode=mode)
                   for name in classes.CLASS_NAMES}
    scale = constrained.detector_scale(cc.total)
    share = composition(cc, view_by_class, slot, weekend)

    t0 = time.time()
    out, diag = project(prior_total, share, view_total, view_by_class, fitted,
                        calib_total, calib_class, scale,
                        use_total=use_total, use_class=use_class)
    diag["seconds"] = round(time.time() - t0, 2)
    return out, out.sum(axis=0), diag
