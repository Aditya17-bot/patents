"""E11 - ground truth: are the fitted biases the detectors' real errors against human counts?

The Department for Transport publishes, as open data, manual classified counts at count
points on the motorway network: enumerators count each hour from 07:00 to 19:00 on one
day, by direction, by vehicle type (motorcycles, cars and taxis, buses and coaches, light
goods vehicles, rigid and articulated HGVs by axles). The counts are made by people, not
by the loops, so they are independent of every detector. Vehicle types are not lengths,
but they fix the length classes closely enough at two boundaries:

    below 660 cm   motorcycles, cars and taxis and light goods vehicles (vans up to 3.5 t),
                   less the longest vans; everything else (HGVs, buses) is longer
    above 1160 cm  articulated HGVs (13.6-16.5 m trailers and tractor), plus coaches and
                   drawbar combinations
    below 520 cm   motorcycles and cars plus the shorter vans: the van split is unknown,
                   so this boundary is only used with the van share as a covariate

For each count in March-June 2025 on the M25 and M1, and for each carriageway, the nearest
fitted detector within 2 km is taken, and kept only if its total count over the counted hours
agrees with the manual total within TOL (it then sees the same vehicles; the direction of
travel is the DfT direction that agrees). Hours are used where all four fifteen-minute
records are in free flow. One detector per count, so the counts are independent.

For each boundary the deviation of the detector's recorded share from the manual proxy is
compared with the detector's fitted bias (fitted on the same month from detector pairs
only; the manual counts play no part in the fit):

    deviation = alpha + beta * bias      beta = 1: the fitted bias is the real error
                                         alpha: common content of the proxy (long vans etc.)

and the spread of the deviations across counts is compared before and after correction.
Counts lie on different chains, each referred to its own median, so this also tests
whether separate chains share one absolute level.

Output: results/e11_ground_truth.json
"""
import json
import math
import os
import sys

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corridor
import e8_offset_model as e8
import method
import pairs
import series

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
DFT = os.path.join(ROOT, "data", "dft")
MONTHS = ["2025-03", "2025-04", "2025-05", "2025-06"]
MAX_DIST_M = 2000
TOL = 0.05              # |detector total / manual total - 1|
MIN_HOURS = 4
FREE_MPH = 50.0


def manual_counts(road):
    rows = json.load(open(os.path.join(DFT, "raw_counts_%s_2025.json" % road)))
    out = {}
    for r in rows:
        d = r["count_date"][:10]
        if d[:7] not in MONTHS:
            continue
        key = (r["count_point_id"], d)
        c = out.setdefault(key, {"lat": float(r["latitude"]), "lon": float(r["longitude"]),
                                 "date": d, "id": r["count_point_id"], "dirs": {}})
        c["dirs"].setdefault(r["direction_of_travel"], {})[int(r["hour"])] = {
            "total": r["all_motor_vehicles"],
            "short": r["two_wheeled_motor_vehicles"] + r["cars_and_taxis"],
            "lgv": r["lgvs"],
            "artic": (r["hgvs_3_or_4_articulated_axle"] + r["hgvs_5_articulated_axle"]
                      + r["hgvs_6_articulated_axle"]),
            "bus": r["buses_and_coaches"]}
    return list(out.values())


def detector_hours(site, date):
    data = series.load(site, date[:7])
    day = int(date[8:10])
    out = {}
    for h in range(24):
        recs = [data.get("%d_%d" % (day, 4 * h + q)) for q in range(4)]
        if any(r is None for r in recs) or any(r[2] <= FREE_MPH for r in recs):
            continue
        out[h] = recs
    return out


def shares(recs_by_hour, hours, fit=None):
    tot, below = 0, [0, 0, 0]
    for h in hours:
        for bins, total, speed in recs_by_hour[h]:
            if fit is not None:
                bins = method.correct_record(bins, fit, "additive")
            n = sum(bins)
            tot += n
            cum = 0
            for e in range(3):
                cum += bins[e]
                below[e] += cum
    return [b / tot for b in below], tot


def match(road, fits, cw, taken):
    sites = corridor.corridor_sites(road, cw)
    mains = [s for s in sites if s["role"] == "mainline"]
    rows = []
    for c in manual_counts(road):
        fit = fits[c["date"][:7]]
        near = sorted((corridor.haversine_m(c["lat"], c["lon"], s["lat"], s["lon"]), s["id"])
                      for s in mains if s["id"] in fit and fit[s["id"]]["chain_size"] >= 3)
        near = [x for x in near if x[0] <= MAX_DIST_M]
        best = None
        for dist, sid in near[:1]:
            hrs = detector_hours(sid, c["date"])
            for dname, man in c["dirs"].items():
                if (c["id"], c["date"], dname) in taken:
                    continue
                hours = [h for h in man if h in hrs]
                if len(hours) < MIN_HOURS:
                    continue
                det_total = sum(sum(sum(r[0]) for r in hrs[h]) for h in hours)
                man_total = sum(man[h]["total"] for h in hours)
                ratio = det_total / man_total
                if best is None or abs(ratio - 1) < abs(best["ratio"] - 1):
                    best = {"site": sid, "dist_m": round(dist), "direction": dname,
                            "hours": hours, "ratio": ratio, "hrs": hrs, "man": man}
        if best is None:
            rows.append({"count_point": c["id"], "date": c["date"], "matched": False,
                         "reason": "no fitted detector within 2 km with data"})
            continue
        if abs(best["ratio"] - 1) > TOL:
            rows.append({"count_point": c["id"], "date": c["date"], "matched": False,
                         "reason": "totals differ by %.1f %%" % (100 * (best["ratio"] - 1)),
                         "site": best["site"]})
            continue
        taken.add((c["id"], c["date"], best["direction"]))
        hours, man, hrs = best["hours"], best["man"], best["hrs"]
        T = sum(man[h]["total"] for h in hours)
        prox = {"short": sum(man[h]["short"] for h in hours) / T,
                "lgv": sum(man[h]["lgv"] for h in hours) / T,
                "artic": sum(man[h]["artic"] for h in hours) / T,
                "bus": sum(man[h]["bus"] for h in hours) / T}
        f = fit_of(fits, c["date"], best["site"])
        raw, _ = shares(hrs, hours)
        cor, _ = shares(hrs, hours, f)
        rows.append({"count_point": c["id"], "date": c["date"], "matched": True,
                     "site": best["site"], "dist_m": best["dist_m"],
                     "direction": best["direction"], "hours": len(hours),
                     "total_ratio": round(best["ratio"], 4), "proxy": prox,
                     "raw": raw, "corrected": cor, "bias": f["bias"],
                     "chain_size": f["chain_size"]})
    return rows


def fit_of(fits, date, site):
    return fits[date[:7]][site]


def cached(site, month):
    return os.path.exists(os.path.join(series.SERIES, "%s_%s.json" % (site, month)))


def chains_cached(road, month, cw):
    """pairs.chains(), with a candidate whose records were not fetched treated as a break
    (carriageway B was fetched only within 8 km of each count point)."""
    out, current = [], []
    for up, down, node_id in pairs.candidates(road, cw):
        rec = None
        if cached(up, month) and cached(down, month):
            rec = pairs.pair_record(up, down, month)
        if rec is None or not rec["admitted"]:
            if current:
                out.append(current)
            current = []
            continue
        if current and current[-1][1] != up:
            out.append(current)
            current = []
        current.append((up, down, node_id, rec))
    if current:
        out.append(current)
    return out


def fit_month(road, month, cw):
    out = {}
    for chain in chains_cached(road, month, cw):
        if len(chain) + 1 < 3:
            continue
        for f in method.solve_chain(chain):
            out[f["detector"]] = f
    return out


def regress(x, y):
    x, y = np.array(x), np.array(y)
    A = np.vstack([np.ones_like(x), x]).T
    coef, res, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss = ((y - pred) ** 2).sum()
    n = len(x)
    se_b = math.sqrt(ss / (n - 2) / ((x - x.mean()) ** 2).sum()) if n > 2 else float("nan")
    return {"alpha_pts": round(100 * coef[0], 2), "beta": round(float(coef[1]), 3),
            "beta_se": round(se_b, 3), "r": round(float(np.corrcoef(x, y)[0, 1]), 3)}


def boundary_stats(rows, e, proxy_fn, covariate=None):
    dev_raw = [r["raw"][e] - proxy_fn(r["proxy"]) for r in rows]
    dev_cor = [r["corrected"][e] - proxy_fn(r["proxy"]) for r in rows]
    bias = [r["bias"][e] for r in rows]
    if covariate is not None:
        # remove the part of the deviation carried by the van share (common coefficient,
        # fitted on the recorded data and applied unchanged to the corrected data)
        z = np.array([covariate(r["proxy"]) for r in rows])
        A = np.vstack([np.ones_like(z), z, np.array(bias)]).T
        coef = np.linalg.lstsq(A, np.array(dev_raw), rcond=None)[0]
        dev_raw = list(np.array(dev_raw) - coef[1] * z)
        dev_cor = list(np.array(dev_cor) - coef[1] * z)
    rho = spearmanr(bias, dev_raw)
    i = int(np.argmax(np.abs(bias)))
    keep = [k for k in range(len(bias)) if k != i]
    drop = regress([bias[k] for k in keep], [dev_raw[k] for k in keep])
    sd = lambda v: round(100 * float(np.std(v, ddof=1)), 2)
    mad = lambda v: round(100 * float(np.median(np.abs(np.array(v) - np.median(v)))), 2)
    return {"n": len(rows), "fit_raw_deviation_on_bias": regress(bias, dev_raw),
            "spearman": round(float(rho.correlation), 3), "spearman_p": float(rho.pvalue),
            "without_largest_bias": drop,
            "sd_deviation_raw_pts": sd(dev_raw), "sd_deviation_corrected_pts": sd(dev_cor),
            "mad_raw_pts": mad(dev_raw), "mad_corrected_pts": mad(dev_cor),
            "mean_deviation_corrected_pts": round(100 * float(np.mean(dev_cor)), 2),
            "points": [{"road": r["road"], "site": r["site"], "bias_pts": round(100 * b_, 3),
                        "dev_raw_pts": round(100 * float(a_), 3),
                        "dev_corrected_pts": round(100 * float(c_), 3)}
                       for r, b_, a_, c_ in zip(rows, bias, dev_raw, dev_cor)],
            "closer_after_correction": sum(
                1 for a, b in zip(dev_raw, dev_cor)
                if abs(b - np.median(dev_cor)) < abs(a - np.median(dev_raw)))}


def main():
    report = {"tol": TOL, "max_dist_m": MAX_DIST_M, "roads": {}}
    allrows = []
    for road in ("M25", "M1"):
        rows = []
        taken = set()
        for cw in ("A", "B"):
            fits = {m: fit_month(road, m, cw) for m in MONTHS}
            part = match(road, fits, cw, taken)
            for r in part:
                r["road"], r["carriageway"] = road, cw
            rows += part
        allrows += rows
        report["roads"][road] = {"counts": len(rows),
                                 "matched": sum(1 for r in rows if r["matched"]),
                                 "rows": rows}
        print(road, "counts", len(rows), "matched", report["roads"][road]["matched"])
    ok = [r for r in allrows if r["matched"]]
    report["pooled"] = {
        "matched": len(ok),
        "b660": boundary_stats(ok, 1, lambda p: p["short"] + p["lgv"]),
        "b1160": boundary_stats(ok, 2, lambda p: 1.0 - p["artic"]),
        "b520": boundary_stats(ok, 0, lambda p: p["short"], covariate=lambda p: p["lgv"]),
    }
    for road in ("M25", "M1"):
        sub = [r for r in ok if r["road"] == road]
        report["roads"][road]["b520"] = boundary_stats(sub, 0, lambda p: p["short"],
                                                       covariate=lambda p: p["lgv"])
        report["roads"][road]["b660"] = boundary_stats(sub, 1, lambda p: p["short"] + p["lgv"])
    print(json.dumps(report["pooled"], indent=1))
    for road in ("M25", "M1"):
        print(road, json.dumps({k: report["roads"][road][k] for k in ("b520", "b660")}))
    with open(os.path.join(RESULTS, "e11_ground_truth.json"), "w") as fh:
        json.dump(report, fh, indent=1, default=float)


if __name__ == "__main__":
    main()
