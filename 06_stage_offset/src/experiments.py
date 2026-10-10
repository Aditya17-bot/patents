"""Evidence for the IDF-B, computed from the per-visit evaluation files.

Inputs:  results/daily.json     (reference discharge = the neighbour's published record)
         results/daily_rt.json  (reference discharge = what the neighbour computes in real
                                 time: its base rating plus its last measured offset)
Outputs: results/e1_interpolation.json  record computation between visits (leave-one-out)
         results/e2_realtime.json       real-time offset since the last visit
         results/e3_injection.json      response to stage offsets injected into real records
         results/e4_ablation.json       stage units vs discharge-ratio units; gain vs fixed
         results/e5_detection.json      detecting a large offset change before the visit
"""
import datetime as dt
import json
import math
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
MIN_COUPLING = 0.95
BIG = 0.10            # ft: an offset departure the hydrographer would act on
GAIN_MIN_PAST, GAIN_PRIOR, GAIN_MAX = 5, 0.5, 1.2


def load(name):
    return json.load(open(os.path.join(RES, name + ".json")))


def directions(d, min_c=None):
    min_c = MIN_COUPLING if min_c is None else min_c
    out = []
    for r in d["results"]:
        if r.get("rows") and r.get("coupling", 0) >= min_c:
            out.append(r)
    return out


def days(a, b):
    return (dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days


_RATINGS = {}


def rating(site):
    """Base rating of a station, from the cached rating table (probe_daily.load_rating)."""
    if site not in _RATINGS:
        import probe_daily
        _RATINGS[site] = probe_daily.load_rating(site)
    return _RATINGS[site]


def qerr(rat, gh, q_meas, s_est):
    """Absolute discharge error (%) at the visit: the base rating read at the visit's gauge
    height plus the estimated offset, against the discharge measured at the visit."""
    return abs(float(rat.q(gh + s_est)) / q_meas - 1.0) * 100.0


def gain(hist):
    if len(hist) < GAIN_MIN_PAST:
        return GAIN_PRIOR
    a = np.array([h[0] for h in hist])
    b = np.array([h[1] for h in hist])
    return float(np.clip(np.sum(a * b) / max(float(np.sum(a * a)), 1e-12), 0.0, GAIN_MAX))


def summ(e, nd=2):
    e = np.asarray(e, float)
    e = e[np.isfinite(e)]
    if len(e) == 0:
        return None
    return {"n": int(len(e)), "median": round(float(np.median(e)), nd),
            "mean": round(float(np.mean(e)), nd), "p90": round(float(np.percentile(e, 90)), max(nd - 1, 1))}


def paired(e_a, e_b):
    """Share of cases where b beats a, and a sign-test z for b < a."""
    a, b = np.asarray(e_a), np.asarray(e_b)
    ok = np.isfinite(a) & np.isfinite(b) & (a != b)
    wins = int(np.sum(b[ok] < a[ok]))
    n = int(np.sum(ok))
    z = (wins - n / 2) / math.sqrt(n / 4) if n else float("nan")
    return {"better": wins, "of": n, "share": round(wins / n, 3) if n else None, "z": round(z, 2)}


# ---- window statistics stored by probe_daily: w = [n, sum x, sum y, sum x^2, sum x y]
def w_add(a, b):
    return [u + v for u, v in zip(a, b)]


def w_D(w):
    """Stage-unit discrepancy of a window with no flow-ratio term: sum(x y) / sum(x^2)."""
    return w[4] / w[3]


def w_m(w):
    """sum(x) / sum(x^2): the factor by which a flow ratio c enters w_D (w_D = s + c m)."""
    return w[1] / w[3]


def w_ybar(w):
    return w[2] / w[0]


def ratio_at_visit(w, s_visit):
    """Flow ratio c of a window next to a visit, given the offset measured at the visit:
    the c for which the least-squares offset of (y - c) on x equals the measured offset."""
    return (w_D(w) - s_visit) / w_m(w)


def offset_given_ratio(w, c):
    """Least-squares stage offset of a window with the flow ratio c removed."""
    return w_D(w) - c * w_m(w)


def usable(hist, t):
    """Earlier departures whose ground truth was known before time t. A departure at visit
    T is scored against the visit after it (N), so it may be used only once N is past; in
    the leave-one-out test this keeps the left-out visit's own measurement out of the gain."""
    return [h[:2] for h in hist if h[2] < t]


def peak_between(a, b):
    """Day of the highest daily mean stage between visit P and visit N (the largest flood),
    from the rows of the two visit intervals P-T and T-N."""
    pk = [(w["peak_h"], w["peak_day"]) for w in (a, b) if w.get("peak_day")]
    return max(pk)[1] if pk else None


RISE_FT = 0.5        # a rise counted by the per-rise practice baseline (twice the steady-day limit)
RATIO_TEST = math.log(1.10)   # synthetic flow-ratio change between the visits (10 % inflow)


def w_shift(w, dy):
    """Window statistics with a constant dy added to every log discrepancy."""
    return [w[0], w[1], w[2] + dy * w[0], w[3], w[4] + dy * w[1]]


def rise_offset(a, b, tT, sP, sN, s_lin):
    """Per-rise practice (Kennedy [N5], gravel control changing only during rises): the
    change between P and N split equally over the rises of RISE_FT or more between them."""
    ev = sorted(c for c, h in (a.get("rises", []) + b.get("rises", [])) if h >= RISE_FT)
    if not ev:
        return s_lin
    return sP + (sN - sP) * sum(1 for c in ev if c < tT) / len(ev)


PRACTICE = ("e_lin", "e_step", "e_ramp", "e_rise")


# ---- other fits of a stage offset to y - c against x (claims 1 and 3 leave the fit open)
def fit_median(yx, c):
    """Median of the per-day offsets (y - c) / x."""
    return float(np.median([(y - c) / x for y, x in yx]))


def fit_wmedian(yx, c):
    """Weighted median of the per-day offsets (y - c) / x, weights x^2 (the least-squares
    weights), so that low-stage days count most."""
    v = sorted(((y - c) / x, x * x) for y, x in yx)
    half, acc = 0.5 * sum(w for _, w in v), 0.0
    for o, w in v:
        acc += w
        if acc >= half:
            return float(o)
    return float(v[-1][0])


def ratio_for_fit(yx, s_visit, fit):
    """Flow ratio c for which the fit of a window next to a visit returns the measured
    offset (the fit decreases as c increases, since x > 0): bisection."""
    lo, hi = -10.0, 10.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if fit(yx, mid) > s_visit:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


FITS = {"median": fit_median, "wmedian": fit_wmedian}


def interpolation(d):
    """E1, E4: leave-one-out at each visit T between visits P and N.

    Baselines (offset at T from the visits P and N alone):
      lin   linear in time between P and N                    (published-record practice)
      step  the whole change placed at the largest flood between P and N
      ramp  prorated linearly from P up to the largest flood, constant after it
    Method (claim 1): the flow ratio c is fixed at each visit from the measured offset and
      interpolated in time; the window's offset with c removed is s_raw; the estimate is
      s_lin + g (s_raw - s_lin), g learned from the station's earlier visits.
    Ablations: no flow-ratio term (D alone, as in draft 1), g = 1, discharge-ratio units
      (mean or median log discrepancy instead of stage units)."""
    recs = []
    for r in directions(d):
        rat = rating(r["x"])
        if rat is None:
            continue
        ws = sorted(r["rows"], key=lambda w: w["day"])
        H = {"anc": [], "noc": [], "rmean": [], "rmed": [], "median": [], "wmedian": []}
        hist_prac = []            # (errors of each practice baseline, day of N) at earlier visits
        half = 0.5 * d["win_d"]
        for i in range(len(ws) - 1):
            a, b = ws[i], ws[i + 1]
            if b["prev_day"] != a["day"] or "wT" not in a:
                continue
            tP, tT, tN = a["prev_day"], a["day"], b["day"]
            f = days(tT, tP) / max(days(tN, tP), 1)
            sP, sT, sN = a["s_prev"], a["s_meas"], b["s_meas"]
            s_lin = sP + (sN - sP) * f
            pk = peak_between(a, b)
            if pk is None:
                s_step = s_ramp = s_lin
            elif pk < tT:
                s_step = s_ramp = sN
            else:
                s_step = sP
                s_ramp = sP + (sN - sP) * days(tT, tP) / max(days(pk, tP), 1)
            s_rise = rise_offset(a, b, tT, sP, sN, s_lin)
            wP, wN, wT = a["wP"], b["wT"], w_add(a["wT"], b["wP"])
            # the invention: flow ratio anchored at the visits, offset in stage units
            cP, cN = ratio_at_visit(wP, sP), ratio_at_visit(wN, sN)
            s_raw = offset_given_ratio(wT, cP + (cN - cP) * f)
            dev = s_raw - s_lin
            # ablation: no flow-ratio term (departure of D from its own interpolation)
            dev_noc = w_D(wT) - (w_D(wP) + (w_D(wN) - w_D(wP)) * f)
            # ablation: discharge-ratio units, mean and median of the log discrepancy
            dev_rmean = w_ybar(wT) - (w_ybar(wP) + (w_ybar(wN) - w_ybar(wP)) * f)
            mT = 0.5 * (a["mT"] + b["mP"])
            dev_rmed = mT - (a["mP"] + (b["mT"] - a["mP"]) * f)
            gh, q = a["gh"], a["q_meas"]
            q_lin = float(rat.q(gh + s_lin))
            if not (np.isfinite(q_lin) and q_lin > 0):
                continue
            g, g_noc = gain(usable(H["anc"], tT)), gain(usable(H["noc"], tT))
            g_rmean, g_rmed = gain(usable(H["rmean"], tT)), gain(usable(H["rmed"], tT))
            s_hat = s_lin + g * dev
            # the same estimator with other fits (needs the per-day values)
            alt = {}
            if a.get("yxP") and b.get("yxT") and a.get("yxT") and b.get("yxP"):
                yxW = a["yxT"] + b["yxP"]
                for nm, fit in FITS.items():
                    cPf = ratio_for_fit(a["yxP"], sP, fit)
                    cNf = ratio_for_fit(b["yxT"], sN, fit)
                    dvf = fit(yxW, cPf + (cNf - cPf) * f) - s_lin
                    alt[nm] = (dvf, s_lin + gain(usable(H[nm], tT)) * dvf)
            # synthetic test: the flow ratio changes by RATIO_TEST linearly from P to N, the
            # offset does not; how much of it leaks into the estimated offset (ft)?
            gapPN = max(days(tN, tP), 1)
            fP, fN = min(half / gapPN, 0.5), max(1 - half / gapPN, 0.5)
            sP_, sN_, sT_ = (w_shift(wP, RATIO_TEST * fP), w_shift(wN, RATIO_TEST * fN),
                             w_shift(wT, RATIO_TEST * f))
            cP_, cN_ = ratio_at_visit(sP_, sP), ratio_at_visit(sN_, sN)
            leak_anc = g * (offset_given_ratio(sT_, cP_ + (cN_ - cP_) * f) - s_raw)
            leak_noc = g_noc * ((w_D(sT_) - (w_D(sP_) + (w_D(sN_) - w_D(sP_)) * f)) - dev_noc)
            # second form: the flow ratio steps by RATIO_TEST at the largest flood between the
            # visits (an inflow that changes with the storm), again with no offset change
            if pk is not None:
                pk_d = days(pk, tP)
                st = lambda t_: RATIO_TEST if t_ > pk_d else 0.0
                kP_, kN_, kT_ = (w_shift(wP, st(half)), w_shift(wN, st(days(tN, tP) - half)),
                                 w_shift(wT, st(days(tT, tP))))
                cPs, cNs = ratio_at_visit(kP_, sP), ratio_at_visit(kN_, sN)
                step_anc = g * (offset_given_ratio(kT_, cPs + (cNs - cPs) * f) - s_raw)
                step_noc = g_noc * ((w_D(kT_) - (w_D(kP_) + (w_D(kN_) - w_D(kP_)) * f)) - dev_noc)
            else:
                step_anc = step_noc = float("nan")
            rec = {"x": r["x"], "y": r["y"], "day": tT, "gap_days": days(tN, tP),
                   "control": a.get("control"), "x_visit": a["x_visit"],
                   "x_window": wT[1] / wT[0], "s_meas": sT, "s_lin": s_lin, "s_hat": s_hat,
                   "s_step": s_step, "s_ramp": s_ramp, "dev": dev, "true_dev": sT - s_lin,
                   "gain": g,
                   "e_lin": qerr(rat, gh, q, s_lin), "e_hat": qerr(rat, gh, q, s_hat),
                   "e_step": qerr(rat, gh, q, s_step), "e_ramp": qerr(rat, gh, q, s_ramp),
                   "e_rise": qerr(rat, gh, q, s_rise),
                   "leak_anc_ft": leak_anc, "leak_noc_ft": leak_noc,
                   "step_anc_ft": step_anc, "step_noc_ft": step_noc,
                   "e_median": qerr(rat, gh, q, alt["median"][1]) if alt else float("nan"),
                   "e_wmedian": qerr(rat, gh, q, alt["wmedian"][1]) if alt else float("nan"),
                   "e_fix": qerr(rat, gh, q, s_lin + dev),
                   "e_noc": qerr(rat, gh, q, s_lin + g_noc * dev_noc),
                   "e_rmean": abs(q_lin * math.exp(g_rmean * dev_rmean) / q - 1) * 100,
                   "e_rmed": abs(q_lin * math.exp(g_rmed * dev_rmed) / q - 1) * 100}
            # practice chosen per station: the baseline with the lowest mean error over the
            # station's earlier visits whose ground truth was known before T (linear first)
            past = [h for h, tn in hist_prac if tn < tT]
            pick = "e_lin" if not past else min(PRACTICE, key=lambda k: (np.mean([h[k] for h in past]), k))
            rec["e_prac"] = rec[pick]
            rec["prac_pick"] = pick
            if all(np.isfinite(v) for k, v in rec.items()
                   if k.startswith("e_") and k not in ("e_median", "e_wmedian")):
                recs.append(rec)
                hist_prac.append(({k: rec[k] for k in PRACTICE}, tN))
            H["anc"].append((dev, sT - s_lin, tN))
            for nm in alt:
                H[nm].append((alt[nm][0], sT - s_lin, tN))
            H["noc"].append((dev_noc, sT - s_lin, tN))
            H["rmean"].append((dev_rmean, math.log(q / q_lin), tN))
            H["rmed"].append((dev_rmed, math.log(q / q_lin), tN))
    return recs


def realtime(d):
    """E2: offset at T from data before T only. Baseline: the offset measured at the last
    visit P carried forward. Method (claim 2): the flow ratio fixed at P from the measured
    offset and the window after P; the offset of the window before T with that ratio
    removed gives the change since P, applied with a gain learned from earlier visits."""
    recs = []
    for r in directions(d):
        rat = rating(r["x"])
        if rat is None:
            continue
        rows = [w for w in sorted(r["rows"], key=lambda w: w["day"]) if "wT" in w]
        hist = []
        for w in rows:
            sP = w["s_prev"]
            change = offset_given_ratio(w["wT"], ratio_at_visit(w["wP"], sP)) - sP
            g = gain(hist)
            gh, q = w["gh"], w["q_meas"]
            rec = {"x": r["x"], "day": w["day"], "control": w.get("control"),
                   "true_change": w["s_meas"] - sP, "change": change, "noise": w["noise"],
                   "e_carry": qerr(rat, gh, q, sP), "e_gain": qerr(rat, gh, q, sP + g * change),
                   "e_base": qerr(rat, gh, q, 0.0)}
            if all(np.isfinite(v) for k, v in rec.items() if k.startswith("e_")):
                recs.append(rec)
            hist.append((change, w["s_meas"] - sP))
    return recs


def block(recs, a, b, mask=None):
    if mask is not None:
        recs = [q for q, m in zip(recs, mask) if m]
    return {"baseline": summ([q[a] for q in recs]), "method": summ([q[b] for q in recs]),
            "paired": paired([q[a] for q in recs], [q[b] for q in recs])}


def auc(scores, labels):
    s = np.asarray(scores)
    y = np.asarray(labels, bool)
    pos, neg = s[y], s[~y]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]))
    ranks = np.empty(len(order))
    ranks[order] = np.arange(1, len(order) + 1)
    return float((np.sum(ranks[:len(pos)]) - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def is_ice(q):
    return bool(q.get("control")) and "ice" in q["control"].lower()


def is_open_water(q):
    """No ice reported at the visit and the visit in April to November."""
    return not is_ice(q) and q["day"][5:7] not in ("12", "01", "02", "03")


BASELINES = ("e_lin", "e_step", "e_ramp", "e_rise", "e_prac")


def strongest_baseline(recs):
    """The baseline with the lowest mean error on these visits."""
    return min(BASELINES, key=lambda k: np.mean([q[k] for q in recs]))


def e1_blocks(recs):
    big = [abs(q["true_dev"]) >= BIG for q in recs]
    ice = [is_ice(q) for q in recs]
    ow = [is_open_water(q) for q in recs]
    out = {"n": len(recs), "targets": len({q["x"] for q in recs}),
           "directions": len({(q["x"], q["y"]) for q in recs}),
           "r_dev": round(float(np.corrcoef([q["dev"] for q in recs],
                                            [q["true_dev"] for q in recs])[0, 1]), 3),
           "n_big": int(sum(big)),
           "abs_offset_err_m": {"lin": summ([0.3048 * abs(q["s_lin"] - q["s_meas"]) for q in recs], 4),
                                "method": summ([0.3048 * abs(q["s_hat"] - q["s_meas"]) for q in recs], 4)},
           "gain": summ([q["gain"] for q in recs])}
    for name, mask in (("all", None), ("big", big), ("ice", ice), ("open_water", ow),
                       ("open_water_big", [o and b for o, b in zip(ow, big)])):
        sub = recs if mask is None else [q for q, m in zip(recs, mask) if m]
        out[name] = block(sub, "e_lin", "e_hat")
        out[name]["baselines"] = {k: summ([q[k] for q in sub]) for k in BASELINES}
        sb = strongest_baseline(sub)
        out[name]["strongest"] = {"key": sb, "baseline": summ([q[sb] for q in sub]),
                                  "paired": paired([q[sb] for q in sub], [q["e_hat"] for q in sub])}
    # visits by interval length: the leave-one-out interval P-N is about twice the
    # interval between consecutive visits
    gap_med = float(np.median([q["gap_days"] for q in recs]))
    out["gap_median_days"] = gap_med
    out["short_gap"] = block(recs, "e_lin", "e_hat", [q["gap_days"] <= gap_med for q in recs])
    out["long_gap"] = block(recs, "e_lin", "e_hat", [q["gap_days"] > gap_med for q in recs])
    return out


def main():
    pub, rt = load("daily"), load("daily_rt")
    ip = load("daily_ip") if os.path.exists(os.path.join(RES, "daily_ip.json")) else None
    meta = {"min_coupling": MIN_COUPLING, "big_ft": BIG, "win_d": pub["win_d"],
            "steady_ft": pub["steady_ft"], "min_days": pub["min_days"],
            "period": [pub["start"], pub["end"]]}

    # ---------------- E1 record computation between visits
    e1 = {"meta": meta}
    for name, d in (("published", pub), ("realtime", rt), ("interp", ip)):
        if d is None:
            continue
        recs = interpolation(d)
        e1[name] = e1_blocks(recs)
        if name == "published":
            e1["records"] = recs
            big = [abs(q["true_dev"]) >= BIG for q in recs]
            ow = [is_open_water(q) for q in recs]
            # E4 ablation on the same records
            ratio_key = min(("e_rmean", "e_rmed"), key=lambda k: np.mean([q[k] for q in recs]))
            variants = {"linear_time": "e_lin", "flood_step": "e_step", "flood_ramp": "e_ramp",
                        "per_rise": "e_rise", "practice_per_station": "e_prac",
                        "fit_median": "e_median", "fit_weighted_median": "e_wmedian",
                        "no_ratio_term": "e_noc", "ratio_units": ratio_key,
                        "stage_units_no_gain": "e_fix", "stage_units_gain": "e_hat"}
            e4 = {"meta": meta, "ratio_variant": ratio_key}
            for lab, mask in (("all", None), ("big", big), ("open_water", ow)):
                sub = recs if mask is None else [q for q, m in zip(recs, mask) if m]
                e4[lab] = {k: summ([q[v] for q in sub]) for k, v in variants.items()}
                e4[lab]["stage_vs_ratio"] = paired([q[ratio_key] for q in sub], [q["e_hat"] for q in sub])
                e4[lab]["with_vs_without_ratio_term"] = paired([q["e_noc"] for q in sub],
                                                               [q["e_hat"] for q in sub])
                e4[lab]["vs_practice_per_station"] = paired([q["e_prac"] for q in sub],
                                                            [q["e_hat"] for q in sub])
                for fk in ("e_median", "e_wmedian"):
                    e4[lab][fk + "_vs_practice"] = paired([q["e_prac"] for q in sub], [q[fk] for q in sub])
            picks = [q["prac_pick"] for q in recs]
            e4["practice_picks"] = {k: picks.count(k) for k in PRACTICE}
            # synthetic flow-ratio change of RATIO_TEST between the visits, no offset change:
            # absolute offset it produces (m), with and without the flow-ratio term
            e4["ratio_leak_m"] = {"ratio_change_ln": round(RATIO_TEST, 4),
                                  "with_ratio_term": summ([0.3048 * abs(q["leak_anc_ft"]) for q in recs], 4),
                                  "without_ratio_term": summ([0.3048 * abs(q["leak_noc_ft"]) for q in recs], 4)}
            e4["ratio_step_m"] = {
                "with_ratio_term": summ([0.3048 * abs(q["step_anc_ft"]) for q in recs], 4),
                "without_ratio_term": summ([0.3048 * abs(q["step_noc_ft"]) for q in recs], 4),
                "share_over_big_with": round(float(np.mean([abs(q["step_anc_ft"]) >= BIG for q in recs
                                                             if np.isfinite(q["step_anc_ft"])])), 3),
                "share_over_big_without": round(float(np.mean([abs(q["step_noc_ft"]) >= BIG for q in recs
                                                                if np.isfinite(q["step_noc_ft"])])), 3),
                "paired": paired([abs(q["step_noc_ft"]) for q in recs if np.isfinite(q["step_anc_ft"])],
                                 [abs(q["step_anc_ft"]) for q in recs if np.isfinite(q["step_anc_ft"])])}
            # stage units against ratio units by how far the visit's log-slope is from the
            # window's (terciles of |ln(x_visit / x_window)|)
            lx = np.array([abs(math.log(q["x_visit"] / q["x_window"])) for q in recs])
            t1, t2 = np.percentile(lx, [100 / 3, 200 / 3])
            e4["by_slope_difference"] = []
            for lo, hi in ((0.0, t1), (t1, t2), (t2, np.inf)):
                sub = [q for q, v in zip(recs, lx) if lo <= v < hi]
                e4["by_slope_difference"].append(
                    {"lo": round(float(lo), 3), "hi": round(float(hi), 3) if np.isfinite(hi) else None,
                     "n": len(sub), "stage_units": summ([q["e_hat"] for q in sub]),
                     "ratio_units": summ([q[ratio_key] for q in sub]),
                     "paired": paired([q[ratio_key] for q in sub], [q["e_hat"] for q in sub])})
    json.dump(e1, open(os.path.join(RES, "e1_interpolation.json"), "w"), indent=1)
    json.dump(e4, open(os.path.join(RES, "e4_ablation.json"), "w"), indent=1)

    # ---------------- E2 real time
    e2 = {"meta": meta}
    rtf = load("daily_rtf") if os.path.exists(os.path.join(RES, "daily_rtf.json")) else None
    for name, d in (("published", pub), ("realtime", rt), ("rtfinal", rtf)):
        if d is None:
            continue
        recs = realtime(d)
        big = [abs(q["true_change"]) >= BIG for q in recs]
        r = float(np.corrcoef([q["change"] for q in recs], [q["true_change"] for q in recs])[0, 1])
        e2[name] = {"n": len(recs), "targets": len({q["x"] for q in recs}), "r_change": round(r, 3),
                    "n_big": int(sum(big)),
                    "all": block(recs, "e_carry", "e_gain"), "big": block(recs, "e_carry", "e_gain", big),
                    "open_water": block(recs, "e_carry", "e_gain", [is_open_water(q) for q in recs]),
                    "base_rating_alone": summ([q["e_base"] for q in recs])}
        # E5 detection: does |change|/noise single out large true changes before the visit?
        if name == "published":
            sc = [abs(q["change"]) / max(q["noise"], 1e-6) for q in recs]
            e5 = {"meta": meta, "auc_z": round(auc(sc, big), 3),
                  "auc_abs": round(auc([abs(q["change"]) for q in recs], big), 3),
                  "n": len(recs), "n_big": int(sum(big))}
    json.dump(e2, open(os.path.join(RES, "e2_realtime.json"), "w"), indent=1)
    json.dump(e5, open(os.path.join(RES, "e5_detection.json"), "w"), indent=1)

    # ---------------- E3 injection: known offsets added to real records
    e3 = {"meta": meta}
    for inj in ("0.10", "0.30"):
        resp, resp_r = [], []
        for r in directions(pub):
            for w in r["rows"]:
                wi = w.get("inj", {}).get("w_" + inj)
                if not wi or "wT" not in w:
                    continue
                cP = ratio_at_visit(w["wP"], w["s_prev"])
                v = offset_given_ratio(wi, cP) - offset_given_ratio(w["wT"], cP)
                if np.isfinite(v):
                    resp.append(v)
                    resp_r.append(w["inj"].get("ratio_" + inj))
        resp = np.array(resp)
        e3[inj] = {"n": len(resp), "median_ft": round(float(np.median(resp)), 4),
                   "p10_ft": round(float(np.percentile(resp, 10)), 4),
                   "p90_ft": round(float(np.percentile(resp, 90)), 4),
                   "median_ratio_change": round(float(np.median(resp_r)), 4),
                   "ratio_change_cv": round(float(np.std(resp_r) / abs(np.mean(resp_r))), 3),
                   "stage_units_cv": round(float(np.std(resp) / abs(np.mean(resp))), 3)}
    json.dump(e3, open(os.path.join(RES, "e3_injection.json"), "w"), indent=1)
    print(json.dumps({"e1": {k: v for k, v in e1.items() if k != "records"}, "e2": e2, "e3": e3,
                      "e4": e4, "e5": e5}, indent=1)[:12000])


if __name__ == "__main__":
    main()
