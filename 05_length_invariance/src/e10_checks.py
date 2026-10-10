"""E10 - checks raised by the review of the IDF-B: are the claims' evidence sound?

A  null        Is "one offset explains 97-99 % of the bias variance" evidence at all? The
               520 cm column dominates the variance, so a matrix with no link between
               boundaries also has a large first component. Here the 660 and 1160 cm
               columns are shuffled across units (breaking any per-unit link, keeping each
               column's spread) and the first-component share recomputed; the
               correlations between columns are reported too.
B  drivers     For units failing the cross-boundary test in March: at which boundary the
               departure is larger, and whether failing units have larger offsets (which
               would point to an error of the interpolated distribution, not a fault).
C  events      The cross-boundary test applied to the step of each dated event: is each
               change of one unit a change of length offset?
D  junction    A test the fit never saw. Consecutive mainline sites WITH a slip road
               between them are never admitted and never used in fitting; their two
               sites lie on different chains, each fixed by its own median. If the fitted
               biases are real and the median references of separate chains agree, the
               correction must reduce the disagreement across the junction too, down to
               what the slip-road traffic itself changes. Fitted on March, scored on
               April-June; control: the same with the biases of the units shuffled.
E  interp      Sensitivity of the offsets and of the test to the interpolated length
               distribution: lower anchor 200 / 300 cm, upper anchor 2000 / 3500 cm, and
               piecewise-linear instead of PCHIP interpolation.

Output: results/e10_checks.json
"""
import json
import os
import random
import sys

import numpy as np
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corridor
import e8_offset_model as e8
import e9_consistency as e9
import method
import pairs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MONTHS = e8.MONTHS
EDGES = e8.EDGES
N_PERM = 500
rng = np.random.default_rng(20250929)


def first_share(B):
    S = np.linalg.svd(B, compute_uv=False)
    return float(S[0] ** 2 / (S ** 2).sum())


# ------------------------------------------------------------------ A
def null_test(fits):
    B = np.array([f["bias"] for f in fits.values()])
    real = first_share(B)
    Z = B / B.std(axis=0)
    real_z = first_share(Z)
    null, null_z = [], []
    for _ in range(N_PERM):
        P = B.copy()
        P[:, 1] = rng.permutation(P[:, 1])
        P[:, 2] = rng.permutation(P[:, 2])
        null.append(first_share(P))
        null_z.append(first_share(P / P.std(axis=0)))
    return {"units": len(B), "rank1": round(real, 4),
            "rank1_null_mean": round(float(np.mean(null)), 4),
            "rank1_null_p99": round(float(np.quantile(null, 0.99)), 4),
            "rank1_standardised": round(real_z, 4),
            "rank1_standardised_null_mean": round(float(np.mean(null_z)), 4),
            "rank1_standardised_null_p99": round(float(np.quantile(null_z, 0.99)), 4),
            "corr_520_660": round(float(np.corrcoef(B[:, 0], B[:, 1])[0, 1]), 3),
            "corr_520_1160": round(float(np.corrcoef(B[:, 0], B[:, 2])[0, 1]), 3),
            "sd_points": [round(100 * float(x), 3) for x in B.std(axis=0)]}


# ------------------------------------------------------------------ B
def drivers(fits, F):
    rows = {d: e9.test(F, f["bias"]) for d, f in fits.items()}
    fail = [d for d in fits if not rows[d]["passes"] and "pred" in rows[d]]
    ok = [d for d in fits if rows[d]["passes"]]
    by660 = by1160 = 0
    for d in fail:
        b, p = fits[d]["bias"], rows[d]["pred"]
        if abs(b[1] - p[1]) >= abs(b[2] - p[2]):
            by660 += 1
        else:
            by1160 += 1
    q = lambda ds: round(float(np.median([abs(rows[d]["offset_cm"]) for d in ds])), 1) if ds else None
    return {"fail": len(fail), "fail_larger_departure_at_660": by660,
            "fail_larger_departure_at_1160": by1160,
            "median_abs_offset_cm_failing": q(fail), "median_abs_offset_cm_passing": q(ok)}


# ------------------------------------------------------------------ C
def events(road, cdfs):
    out = []
    ev = json.load(open(os.path.join(RESULTS, "e8_offset_model.json")))["roads"][road]["events"]
    for e in ev:
        vecs = []
        if e["step_pair_upstream"]:
            vecs.append(np.array(e["step_pair_upstream"]))
        if e["step_pair_downstream"]:
            vecs.append(-np.array(e["step_pair_downstream"]))
        step = np.mean(vecs, axis=0)            # change of the unit's own bias
        m = MONTHS[min(3, e["day_index"] // 30)]
        t = e9.test(cdfs[m], list(step))
        out.append({"detector": e["detector"], "step": [round(float(x), 4) for x in step],
                    "offset_change_cm": round(t["offset_cm"], 1) if t["offset_cm"] is not None else None,
                    "pred": [round(x, 4) for x in t["pred"]] if "pred" in t else None,
                    "residual": round(t["residual"], 3) if t["residual"] is not None else None,
                    "passes": bool(t["passes"])})
    return out


# ------------------------------------------------------------------ D
def junction_pairs(road, month):
    """(last site of a chain, first site of the next chain) where every node between them
    is usable and at least one carries a slip road: the two sites lie on different chains
    and see the same through traffic plus and minus the slip-road traffic."""
    nodes = corridor.build_nodes(corridor.corridor_sites(road, "A"))
    idx_up = {n["upstream"]["id"]: i for i, n in enumerate(nodes)}
    idx_dn = {n["downstream"]["id"]: i for i, n in enumerate(nodes)}
    ch = pairs.chains(road, month)
    out = []
    for c1, c2 in zip(ch[:-1], ch[1:]):
        up, down = c1[-1][1], c2[0][0]
        if up not in idx_up or down not in idx_dn:
            continue
        i, j = idx_up[up], idx_dn[down]
        if j < i:
            continue
        span = nodes[i:j + 1]
        if all(n["usable"] for n in span) and any(n["slips"] for n in span):
            out.append((up, down, sum(len(n["slips"]) for n in span)))
    return out


def junction(road, fit):
    units = [d for d in fit if fit[d]["chain_size"] >= 3]
    out = {}
    for m in MONTHS[1:]:
        rows = []
        for up, down, nslip in junction_pairs(road, "2025-03"):
            if up not in fit or down not in fit:
                continue
            if fit[up]["chain_size"] < 3 or fit[down]["chain_size"] < 3:
                continue
            rec = pairs.pair_record(up, down, m)
            if rec is not None and abs(rec["ratio"] - 1.0) > 0.35:
                rec = None                                  # not a through-traffic pair
            if rec is None:
                continue
            raw = method.pair_gap(rec)[0][0]
            a = method.correct_series(rec["a"], fit[up], "additive")
            b = method.correct_series(rec["b"], fit[down], "additive")
            cor = method.pair_gap({"keys": rec["keys"], "a": a, "b": b})[0][0]
            ctrl = []
            for _ in range(20):
                fu, fd = random.sample(units, 2)
                a2 = method.correct_series(rec["a"], fit[fu], "additive")
                b2 = method.correct_series(rec["b"], fit[fd], "additive")
                ctrl.append(abs(method.pair_gap({"keys": rec["keys"], "a": a2, "b": b2})[0][0]))
            rows.append({"up": up, "down": down, "slips": nslip,
                         "ramp_share": round(abs(rec["ratio"] - 1.0), 4),
                         "raw": raw, "corrected": cor, "control": float(np.mean(ctrl))})
        if not rows:
            continue
        mean = lambda k, rs: round(100 * float(np.mean([abs(r[k]) for r in rs])), 2)
        small = [r for r in rows if r["ramp_share"] < 0.10]
        out[m] = {"pairs": len(rows), "raw": mean("raw", rows),
                  "corrected": mean("corrected", rows), "control_shuffled": mean("control", rows),
                  "improved": sum(1 for r in rows if abs(r["corrected"]) < abs(r["raw"])),
                  "ramp_share_median": round(float(np.median([r["ramp_share"] for r in rows])), 3),
                  "pairs_ramp_under_10pct": len(small),
                  "raw_ramp_under_10pct": mean("raw", small) if small else None,
                  "corrected_ramp_under_10pct": mean("corrected", small) if small else None}
        print(road, m, json.dumps(out[m]))
    return out


# ------------------------------------------------------------------ E
def cdf_variant(shares, lo=250, top=e8.CDF_TOP, kind="pchip"):
    x = [0, lo] + EDGES + [top]
    y = [0.0, 0.0] + list(shares) + [1.0]
    if kind == "pchip":
        return PchipInterpolator(x, y)
    xs, ys = np.array(x, float), np.array(y, float)

    class Lin:
        def __call__(self, v):
            return float(np.interp(v, xs, ys))

        def derivative(self):
            # slope at a class boundary: mean of the two adjoining segments
            return lambda v: (float(np.interp(v + 1.0, xs, ys))
                              - float(np.interp(v - 1.0, xs, ys))) / 2.0
    return Lin()


def interp(fits):
    shares = np.median(np.array([f["share"] for f in fits.values()]), axis=0)
    variants = {"baseline": dict(), "low 200": dict(lo=200), "low 300": dict(lo=300),
                "top 2000": dict(top=2000), "top 3500": dict(top=3500),
                "linear": dict(kind="linear")}
    base = None
    out = {}
    for name, kw in variants.items():
        F = cdf_variant(shares, **kw)
        rows = {d: e9.test(F, f["bias"]) for d, f in fits.items()}
        big = [d for d in fits if abs(fits[d]["bias"][0]) > e8.BIG and rows[d]["offset_cm"] is not None]
        offs = {d: rows[d]["offset_cm"] for d in big}
        cls = {d: rows[d]["passes"] for d in fits}
        if base is None:
            base = (offs, cls)
        ratio = [offs[d] / base[0][d] for d in big if d in base[0] and abs(base[0][d]) > 1]
        out[name] = {"median_abs_offset_cm": round(float(np.median([abs(v) for v in offs.values()])), 1),
                     "offset_ratio_to_baseline_median": round(float(np.median(ratio)), 3),
                     "fail": sum(1 for v in cls.values() if not v),
                     "class_agreement_with_baseline": round(
                         sum(1 for d in cls if cls[d] == base[1][d]) / len(cls), 3)}
    return out


def main():
    random.seed(1)
    report = {"roads": {}}
    for road in ("M25", "M1"):
        r = {"null": {}, "drivers": {}, "interp": {}}
        cdfs = {}
        fits_m = {}
        for m in MONTHS:
            fits = e8.fit_month(road, m)
            fits_m[m] = fits
            cdfs[m] = e9.corridor_cdf(fits)
            r["null"][m] = null_test(fits)
            r["drivers"][m] = drivers(fits, cdfs[m])
            r["interp"][m] = interp(fits)
            print(road, m, json.dumps(r["null"][m]), json.dumps(r["drivers"][m]))
        r["events"] = events(road, cdfs)
        r["junction"] = junction(road, fits_m["2025-03"])
        print(road, json.dumps(r["events"]))
        print(road, json.dumps(r["interp"]["2025-03"], indent=1))
        report["roads"][road] = r
    with open(os.path.join(RESULTS, "e10_checks.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
