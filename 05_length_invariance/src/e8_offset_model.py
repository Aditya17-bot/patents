"""E8 - is each detector's error one physical length offset? What does that buy?

A detector that adds an offset d (cm) to every length it measures reports, below boundary
e, the true share F(e - d) instead of F(e), where F is the cumulative length distribution
of the traffic stream. Its share bias at e is then F(e) - F(e - d), approximately f(e) d,
with f the length density at e. Because the vehicles are the same along a chain, F is
common to every detector of the chain, and the biases of all detectors at all boundaries
should factor as

    b_i(e) = d_i * f(e)          (rank one: one number per detector, one per boundary)

Measured here, on the March-June fits of both corridors:

A  structure   share of the variance of the detectors x boundaries bias matrix explained
               by rank one; the boundary loadings f(e)/f(520) per corridor and month; the
               loadings predicted from the corridor's own class shares (monotone PCHIP
               interpolation of the length CDF through the class boundaries); each
               detector's offset in cm (inverting F(520 - d) - F(520) = b(520)); and its
               residual from rank one, which marks a fault that is not a length offset
B  speed       each detector's speed bias, solved along the chain from the ratio of mean
               speeds in each pair exactly as the share biases are. A loop-spacing error
               k scales speed by k and length by about k as well, so it shows as an offset
               accompanied by a speed bias; an on-time (sensitivity or threshold) error
               shows as an offset with no speed bias
C  correction  biases fitted on March, applied to April-June: the per-boundary biases of
               claim 1 against the rank-one biases d_i f(e); scored at all three
               boundaries over pairs touching a corrected detector and over all admitted
               pairs, and separately for chains of three or four detectors
D  events      the step at every boundary in both pairs of each dated event

Output: results/e8_offset_model.json
"""
import json
import math
import os
import sys

import numpy as np
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e3_steps
import method
import pairs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MONTHS = ["2025-03", "2025-04", "2025-05", "2025-06"]
EDGES = [520, 660, 1160]
CDF_TOP = 2600          # cm; above the longest permitted articulated vehicle
RESIDUAL_LIMIT = 0.3    # |rank-one residual| / |b520| above which the fault is not an offset
BIG = 0.02              # detectors with |b520| above 2 points enter the offset statistics


def speed_bias(chain):
    """Speed bias per detector (log units), chain-solved with the median gauge."""
    g = []
    for up, down, nid, rec in chain:
        keys = rec["keys"]
        va = sum(rec["a"][k][2] for k in keys) / len(keys)
        vb = sum(rec["b"][k][2] for k in keys) / len(keys)
        g.append(math.log(va / vb))
    b = [0.0]
    for x in g:
        b.append(b[-1] - x)
    m = float(np.median(b))
    return [x - m for x in b]


def fit_month(road, month):
    out = {}
    for chain in pairs.chains(road, month):
        dets = [chain[0][0]] + [p[1] for p in chain]
        if len(dets) < 3:
            continue
        sb = speed_bias(chain)
        for f, s in zip(method.solve_chain(chain), sb):
            f["speed_bias"] = s
            out[f["detector"]] = f
    return out


def cdf_of(shares):
    x = [0, 250] + EDGES + [CDF_TOP]
    y = [0.0, 0.0] + list(shares) + [1.0]
    return PchipInterpolator(x, y)


def offset_cm(F, b520):
    """Solve F(520 - d) - F(520) = b520 for d by bisection on [-300, 300] cm.

    d > 0: the detector over-measures every length by d, so it counts fewer vehicles
    below the boundary and its share bias is negative."""
    target = F(520) + b520
    lo, hi = -300.0, 300.0
    if not (F(520 - hi) <= target <= F(520 - lo)):
        return float("nan")
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if F(520 - mid) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def structure(fits):
    dets = sorted(fits)
    B = np.array([fits[d]["bias"] for d in dets])
    U, S, Vt = np.linalg.svd(B, full_matrices=False)
    ev = S ** 2 / (S ** 2).sum()
    v = Vt[0] / Vt[0][0]
    shares = np.median(np.array([fits[d]["share"] for d in dets]), axis=0)
    F = cdf_of(shares)
    dens = np.array([F.derivative()(e) for e in EDGES])
    res, offs, sp = {}, {}, {}
    for d, b in zip(dets, B):
        k = b @ v / (v @ v)
        r = b - k * v
        res[d] = float(np.abs(r).max() / abs(b[0])) if abs(b[0]) > 0 else float("nan")
        offs[d] = offset_cm(F, b[0])
        sp[d] = fits[d]["speed_bias"]
    big = [d for d in dets if abs(fits[d]["bias"][0]) > BIG]
    rel = np.array([res[d] for d in big])
    ab = np.array([abs(offs[d]) for d in big if offs[d] == offs[d]])
    return {
        "detectors": len(dets),
        "rank1_variance": round(float(ev[0]), 4),
        "loadings": [round(float(x), 4) for x in v],
        "cdf_density_ratio": [1.0, round(float(dens[1] / dens[0]), 4),
                              round(float(dens[2] / dens[0]), 4)],
        "big": len(big),
        "big_residual_median": round(float(np.median(rel)), 4),
        "big_non_offset": int((rel > RESIDUAL_LIMIT).sum()),
        "offset_cm_q50_q75_q90": [round(float(np.quantile(ab, q)), 1) for q in (.5, .75, .9)],
        "density_520_per_cm": round(float(dens[0]), 6),
        "_res": res, "_offs": offs, "_speed": sp, "_v": v.tolist(),
    }


def speed_attribution(fits, st):
    """Relation of the length offset to the speed bias."""
    dets = [d for d in fits if abs(fits[d]["bias"][0]) > BIG and st["_offs"][d] == st["_offs"][d]]
    off = np.array([st["_offs"][d] for d in dets])
    sp = np.array([st["_speed"][d] for d in dets])
    r = float(np.corrcoef(off, sp)[0, 1])
    # a loop-spacing error k gives an offset of about (k - 1)(e + loop length) at e; with a
    # 2 m loop, 720 cm at 520 cm. Offset explained by the speed bias alone:
    explained = 720.0 * (np.exp(sp) - 1.0)
    small = np.abs(sp) < 0.01
    return {"n": len(dets), "corr_offset_speed_bias": round(r, 3),
            "speed_bias_abs_q50_q90": [round(float(np.quantile(np.abs(sp), q)), 4)
                                       for q in (.5, .9)],
            "share_with_speed_bias_under_1pct": round(float(small.mean()), 3),
            "offset_cm_explained_by_speed_q50": round(float(np.median(np.abs(explained))), 1),
            "offset_cm_q50": round(float(np.median(np.abs(off))), 1)}


def rank1_fits(fits, v):
    out = {}
    v = np.array(v)
    for d, f in fits.items():
        b = np.array(f["bias"])
        k = b @ v / (v @ v)
        g = dict(f)
        g["bias"] = list(k * v)
        out[d] = g
    return out


def score(road, month, fits, short_only=False):
    """Mean |gap| per boundary: touched pairs raw/corrected, all admitted raw/corrected."""
    t_raw, t_cor, a_raw, a_cor = [], [], [], []
    for chain in pairs.chains(road, month):
        for up, down, nid, rec in chain:
            raw = method.pair_gap(rec)[0]
            chosen = [d for d in (up, down) if d in fits and
                      (not short_only or fits[d]["chain_size"] <= 4)]
            a = rec["a"] if up not in chosen else method.correct_series(rec["a"], fits[up], "additive")
            b = rec["b"] if down not in chosen else method.correct_series(rec["b"], fits[down], "additive")
            cor = method.pair_gap({"keys": rec["keys"], "a": a, "b": b})[0]
            a_raw.append([abs(x) for x in raw])
            a_cor.append([abs(x) for x in cor])
            if chosen:
                t_raw.append([abs(x) for x in raw])
                t_cor.append([abs(x) for x in cor])
    mean = lambda rows: [round(sum(r[e] for r in rows) / len(rows), 5) for e in range(3)] if rows else None
    return {"touched_pairs": len(t_raw), "touched_raw": mean(t_raw),
            "touched_corrected": mean(t_cor), "all_pairs": len(a_raw),
            "all_raw": mean(a_raw), "all_corrected": mean(a_cor)}


def event_steps(road):
    ev = json.load(open(os.path.join(RESULTS, "e3_step_events.json")))["roads"][road]["events"]
    cands = pairs.candidates(road)
    into = {c[1]: c for c in cands}
    out_of = {c[0]: c for c in cands}
    rows = []
    for e in ev:
        d, day = e["detector"], e["day_index"]
        vecs = []
        for up, down in ((into[d][0], d), (d, out_of[d][1])):
            ser = {}
            for m in e3_steps.MONTHS:
                rec = pairs.pair_record(up, down, m)
                if rec is None or not rec["admitted"]:
                    continue
                for dd, gaps in method.pair_gap(rec)[1].items():
                    ser[e3_steps.day_index(m, int(dd))] = gaps
            before = [ser[k] for k in sorted(ser) if day - 15 <= k < day]
            after = [ser[k] for k in sorted(ser) if day <= k < day + 15]
            vecs.append([round(float(x), 4) for x in
                         (np.mean(after, axis=0) - np.mean(before, axis=0))]
                        if before and after else None)
        rows.append({"detector": d, "day_index": day, "step_pair_downstream": vecs[0],
                     "step_pair_upstream": vecs[1]})
    return rows


def main():
    report = {"residual_limit": RESIDUAL_LIMIT, "big_threshold": BIG, "roads": {}}
    for road in ("M25", "M1"):
        fits = {m: fit_month(road, m) for m in MONTHS}
        st = {m: structure(fits[m]) for m in MONTHS}
        r = {"structure": {m: {k: v for k, v in st[m].items() if not k.startswith("_")}
                           for m in MONTHS},
             "speed": {m: speed_attribution(fits[m], st[m]) for m in MONTHS}}
        # persistence of the fault type: non-offset in March and again in June
        big_m = {d for d in fits["2025-03"] if abs(fits["2025-03"][d]["bias"][0]) > BIG}
        big_j = {d for d in fits["2025-06"] if abs(fits["2025-06"][d]["bias"][0]) > BIG}
        both = sorted(big_m & big_j)
        nm = {d for d in both if st["2025-03"]["_res"][d] > RESIDUAL_LIMIT}
        nj = {d for d in both if st["2025-06"]["_res"][d] > RESIDUAL_LIMIT}
        r["fault_type_persistence"] = {"detectors_big_in_march_and_june": len(both),
                                       "non_offset_march": len(nm), "non_offset_june": len(nj),
                                       "non_offset_both": len(nm & nj)}
        # correction: per-boundary against rank one, fitted on March
        per = fits["2025-03"]
        r1 = rank1_fits(per, st["2025-03"]["_v"])
        r["correction"] = {}
        for m in MONTHS[1:]:
            r["correction"][m] = {"per_boundary": score(road, m, per),
                                  "rank_one": score(road, m, r1),
                                  "per_boundary_short_chains": score(road, m, per, True),
                                  "rank_one_short_chains": score(road, m, r1, True)}
            print(road, m, json.dumps(r["correction"][m]))
        # per-detector values for the figures (March and June)
        r["per_detector"] = {}
        for m in ("2025-03", "2025-06"):
            r["per_detector"][m] = {
                d: {"bias": [round(x, 5) for x in fits[m][d]["bias"]],
                    "chain_size": fits[m][d]["chain_size"],
                    "offset_cm": (round(st[m]["_offs"][d], 1)
                                  if st[m]["_offs"][d] == st[m]["_offs"][d] else None),
                    "speed_bias": round(st[m]["_speed"][d], 5),
                    "residual": (round(st[m]["_res"][d], 4)
                                 if st[m]["_res"][d] == st[m]["_res"][d] else None)}
                for d in fits[m]}
        r["events"] = event_steps(road)
        report["roads"][road] = r
        print(road, json.dumps(r["structure"]["2025-03"]))
        print(road, json.dumps(r["speed"]["2025-03"]))
        print(road, json.dumps(r["fault_type_persistence"]))
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "e8_offset_model.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
