"""What the physics alone can certify about a value it never saw.

Every reconstruction method returns a number. Almost none of them return a number with a
range attached, and a bare number is a poor thing to feed a downstream control dataset:
nothing downstream can tell a value that was pinned down by three live neighbours from a
value that was a guess.

The constraint set gives the range for free, and gives it as a guarantee rather than as a
confidence interval in the statistical sense. The feasible set is a polytope: the node
bands are two-sided linear inequalities and counts are non-negative. So for a missing
value x_j the smallest and largest values consistent with everything actually observed
around it are just

    min x_j   and   max x_j     subject to   lower <= A x <= upper,  x >= 0

two linear programs. Any number outside that interval contradicts the observed data
under the calibrated relation. This is a statement about the physical relation and the
neighbouring measurements, and it holds whatever estimator produced the point value.

Some values are not bounded above by the physics at all - a slip road at a node where two
other detectors are also missing can be arbitrarily large as long as its partners absorb
it. Those are reported as unbounded rather than given a fabricated width, and the share of
them is itself the useful number: it says how much of the reconstruction the network
geometry can actually vouch for.

The interval is then checked the only way that means anything: by counting how often the
withheld true value really does fall inside it.
"""

import json
import os
import sys
import time

import numpy as np
from scipy.optimize import linprog

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import baselines
import constrained
import dataset
import evaluate

RESULTS = os.path.join(ROOT, "results")


def _bounds_for_interval(A, lower, upper, cap, targets):
    """Per-coordinate min and max over the feasible polytope, for selected coordinates."""
    n = A.shape[1]
    a_ub = np.vstack([A, -A])
    b_ub = np.concatenate([upper, -lower])
    box = [(0.0, float(cap[j])) for j in range(n)]

    out = {}
    for j in targets:
        cost = np.zeros(n)
        cost[j] = 1.0
        lo = linprog(cost, A_ub=a_ub, b_ub=b_ub, bounds=box, method="highs")
        hi = linprog(-cost, A_ub=a_ub, b_ub=b_ub, bounds=box, method="highs")
        if lo.status != 0 or hi.status != 0:
            continue
        out[j] = (float(lo.x[j]), float(hi.x[j]))
    return out


def run(manifest="window.json", fraction=0.10, seed=0, max_run=96,
        prior="knn_spatial", cap_multiple=3.0, max_intervals=None,
        out_name="confidence.json"):
    t0 = time.time()
    corridor = dataset.load(manifest)
    fitted = evaluate.fit_node_signs(corridor)
    slot, weekend = corridor.interval_index(), corridor.is_weekend()

    hidden = dataset.make_mask(corridor, fraction=fraction, seed=seed, max_run=max_run)
    view = dataset.train_view(corridor, hidden)

    # The bounds are part of the method, so the relations that define them are calibrated
    # on what the method may see. Calibrating on the full corridor would fit the band
    # using the very values whose coverage is then being counted.
    calib = constrained.calibrate(constrained.training_corridor(corridor, view),
                                  fitted, mode="scaled")
    p = baselines.METHODS[prior](view, slot, weekend)
    filled, _ = constrained.reconstruct(corridor, view, fitted, p)

    # the box the linear programs live in. Without an upper box the problem is unbounded
    # for any detector the physics does not pin down, and "unbounded" is exactly the
    # answer wanted there - so the cap is set well above anything the detector has ever
    # recorded and hitting it is reported as unbounded rather than as a width.
    row_max = np.array([np.nanmax(corridor.volumes[i]) if corridor.observed[i].any() else 1.0
                        for i in range(corridor.shape[0])])
    cap_row = np.maximum(cap_multiple * row_max, 10.0)

    missing = np.isnan(view)
    cols = np.where(missing.any(axis=0))[0]
    if max_intervals is not None and cols.size > max_intervals:
        rng = np.random.default_rng(seed)
        cols = np.sort(rng.choice(cols, size=max_intervals, replace=False))

    widths, covered, bounded, checked, unbounded = [], 0, 0, 0, 0
    width_by_unknowns = {}
    point_inside = 0

    for t in cols:
        unknown_rows = np.where(missing[:, t])[0]
        index_of = {row: k for k, row in enumerate(unknown_rows)}

        rows_A, centres, bands = [], [], []
        for f in fitted:
            c = calib[f["node_id"]]
            terms = [(f["up"], 1.0), (f["down"], c["down_coeff"])]
            terms += [(row, float(sign)) for row, sign in f["slips"]]
            if not any(r in index_of for r, _ in terms):
                continue
            a = np.zeros(unknown_rows.size)
            b = c["const"]
            ok = True
            for row, coeff in terms:
                if row in index_of:
                    a[index_of[row]] += coeff
                else:
                    v = view[row, t]
                    if not np.isfinite(v):
                        ok = False
                        break
                    b -= coeff * v
            if ok:
                rows_A.append(a)
                centres.append(b)
                bands.append(c["band"])

        if not rows_A:
            continue
        A = np.array(rows_A)
        centre = np.array(centres)
        band = np.array(bands)

        # only the coordinates that appear in some constraint can be bounded by physics
        targets = [j for j in range(unknown_rows.size)
                   if np.abs(A[:, j]).max() > 1e-9 and hidden[unknown_rows[j], t]]
        if not targets:
            continue

        got = _bounds_for_interval(A, centre - band, centre + band,
                                   cap_row[unknown_rows], targets)

        # how many unknowns share each target's node, which is what decides whether the
        # physics can pin it down at all
        for j, (lo, hi) in got.items():
            row = unknown_rows[j]
            truth = corridor.volumes[row, t]
            if not np.isfinite(truth):
                continue
            checked += 1
            n_share = int(max(1, np.abs(A[np.abs(A[:, j]) > 1e-9]).astype(bool).sum(axis=1).min()))
            is_bounded = hi < cap_row[row] - 1e-6
            if is_bounded:
                bounded += 1
                widths.append(hi - lo)
                width_by_unknowns.setdefault(n_share, []).append(hi - lo)
            else:
                unbounded += 1
            covered += int(lo - 1e-6 <= truth <= hi + 1e-6)
            point_inside += int(lo - 1e-6 <= filled[row, t] <= hi + 1e-6)

    out = {
        "manifest": manifest, "prior": prior, "seed": seed,
        "fraction_hidden": fraction, "cap_multiple": cap_multiple,
        "intervals_examined": int(cols.size),
        "values_checked": checked,
        "bounded_by_physics": bounded,
        "bounded_pct": round(100.0 * bounded / checked, 2) if checked else None,
        "unbounded": unbounded,
        "coverage_pct": round(100.0 * covered / checked, 2) if checked else None,
        "point_estimate_inside_pct": round(100.0 * point_inside / checked, 2) if checked else None,
        "median_width_vehicles": round(float(np.median(widths)), 2) if widths else None,
        "p90_width_vehicles": round(float(np.quantile(widths, 0.9)), 2) if widths else None,
        "width_by_unknowns_at_node": {
            str(k): {"n": len(v), "median_width": round(float(np.median(v)), 2)}
            for k, v in sorted(width_by_unknowns.items())},
        "seconds": round(time.time() - t0, 1),
    }

    print("manifest %s, %d values checked over %d intervals"
          % (manifest, checked, cols.size))
    print("bounded by the physics: %.2f%%  (the rest are not pinned down by any node)"
          % (out["bounded_pct"] or 0))
    print("true value inside the certified interval: %.2f%%" % (out["coverage_pct"] or 0))
    print("median certified width: %s vehicles per interval" % out["median_width_vehicles"])
    print("width by number of unknowns sharing the node:")
    for k, v in out["width_by_unknowns_at_node"].items():
        print("   %s unknown(s): n=%-6d median width %6.1f" % (k, v["n"], v["median_width"]))

    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/%s in %.0fs" % (out_name, out["seconds"]))
    return out


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window.json"
    name = sys.argv[2] if len(sys.argv) > 2 else "confidence.json"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    run(manifest, out_name=name, max_intervals=limit)
