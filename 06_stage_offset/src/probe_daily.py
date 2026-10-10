"""Daily-resolution evaluation over every topology-derived gauge pair.

For each pair and each direction (target X, reference Y) and every field visit T at X
with a measured discharge, the stage offset at T is estimated from data available
BEFORE T only, and compared with the offset the hydrographer measured at T:

    s_meas(T) = R^-1(Q_meas) - GH_meas            (R = base rating of X)

Estimators (all real-time: nothing after T is used):
  base     s = 0                                  (base rating alone)
  carry    s = s_meas(P)                          (offset of the previous visit P; current practice)
  ratio    carry, then the neighbour's discharge-ratio change since P applied as a
           multiplicative factor (conventional reference-gauge comparison)
  offset   s = s_meas(P) + [D(T) - D(P)],  D = least-squares stage offset of the
           window's log discrepancies on the rating log-slope (the invention)
  gated    offset if the change |D(T) - D(P)| exceeds GATE_K times its noise and the
           stage-offset signature test passes; carry otherwise

Output: results/<name>.json
"""
import datetime as dt
import json
import math
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import core
import usgs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START, END = "2020-10-01", "2026-09-30"   # water years 2021-2026

WIN_D = int(os.environ.get("WIN_D", "21"))   # trailing window before T (days)
MIN_DAYS = 8                                  # usable days required in a window
STEADY_FT = float(os.environ.get("STEADY_FT", "0.25"))  # max day-to-day change of mean stage
GATE_K = float(os.environ.get("GATE_K", "2.0"))
Y_MODE = os.environ.get("Y_MODE", "published")
INJ = (0.1, 0.3)          # injected stage offsets (ft) for the sensitivity test
GAIN_MIN_PAST = 5         # earlier visits needed before the station's own gain is used
GAIN_PRIOR = 0.5          # gain until then
GAIN_MAX = 1.2


def daydiff(a, b):
    return (dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days


def shift_day(d, n):
    return (dt.date.fromisoformat(d) + dt.timedelta(days=n)).isoformat()


def series(DV, site, par):
    return {d: v for d, (v, c) in DV.get(site, {}).get(par, {}).get("00003", {}).items()}


def visits_with_offset(site, rat, t_from):
    out = []
    for v in usgs.field_visits(site):
        if v["q"] <= 0 or v["time"] < t_from:
            continue
        g = rat.g_of_q(v["q"])
        if not np.isfinite(g):
            continue
        v = dict(v)
        v["s_meas"] = float(g - v["gh"])
        v["day"] = v["time"].date().isoformat()
        out.append(v)
    return out


def load_rating(site):
    r = usgs.rating(site, "exsa")
    if not r.get("table"):
        return None
    beg = r.get("begin") or ""
    begin = (dt.datetime.strptime(beg[:14], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
             if beg[:1].isdigit() else None)
    rat = core.Rating(r["table"], r.get("rating_id", ""), begin)
    return rat if len(rat.g) > 10 else None


def realtime_q(DV, site, interpolate=False):
    """Reference discharge recomputed from the neighbour's own stage, base rating and field
    visits. interpolate=False: what a real-time system computes, the offset measured at the
    most recent earlier visit. interpolate=True: a record finalised between the neighbour's
    own visits, the offset interpolated linearly in time between the visits before and
    after each day (days outside the neighbour's visits are left out)."""
    rat = load_rating(site)
    if rat is None:
        return None
    hy = series(DV, site, "00065")
    vis = visits_with_offset(site, rat, dt.datetime(1900, 1, 1, tzinfo=dt.timezone.utc))
    out, j, last = {}, -1, 0.0
    for d in sorted(hy):
        while j + 1 < len(vis) and vis[j + 1]["day"] < d:
            j += 1
            last = vis[j]["s_meas"]
        if interpolate:
            if j < 0 or j + 1 >= len(vis):
                continue
            a, b = vis[j], vis[j + 1]
            f = daydiff(d, a["day"]) / max(daydiff(b["day"], a["day"]), 1)
            off = a["s_meas"] + f * (b["s_meas"] - a["s_meas"])
        else:
            off = last
        q = float(rat.q(hy[d] + off))
        if np.isfinite(q):
            out[d] = q
    return out


def finalised_to_date(DV, site):
    """Reference discharge as known in real time at a time `now`: for days that lie between
    two of the neighbour's own field visits made before `now`, its offset interpolated
    between those visits (its record finalised to date); after its last visit before
    `now`, that visit's offset carried forward. Returns q(day, now)."""
    rat = load_rating(site)
    if rat is None:
        return None
    hy = series(DV, site, "00065")
    vis = visits_with_offset(site, rat, dt.datetime(1900, 1, 1, tzinfo=dt.timezone.utc))
    days_v = [v["day"] for v in vis]
    import bisect

    def q(d, now):
        if d not in hy or now is None or d >= now:
            return None
        j = bisect.bisect_left(days_v, d) - 1          # last visit before d
        if j < 0:
            return None
        a = vis[j]
        if j + 1 < len(vis) and vis[j + 1]["day"] < now:
            b = vis[j + 1]
            f = daydiff(d, a["day"]) / max(daydiff(b["day"], a["day"]), 1)
            off = a["s_meas"] + f * (b["s_meas"] - a["s_meas"])
        else:
            off = a["s_meas"]
        v = float(rat.q(hy[d] + off))
        return v if np.isfinite(v) else None
    return q


IV_MODE = os.environ.get("IV_MODE") == "1"
IV_START, IV_END = "2023-10-01", "2026-09-30"


def iv_days(x, y, rat):
    """Per-day (y, x, h) from the 15-minute records: the base rating and its log-slope are
    applied to every 15-minute stage, and the reference discharge is lagged in hours."""
    try:
        hx = core.hourly(usgs.iv(x, "00065", IV_START, IV_END))
        qx = core.hourly(usgs.iv(x, "00060", IV_START, IV_END))
        qy = core.hourly(usgs.iv(y, "00060", IV_START, IV_END))
    except Exception:
        return None
    lag_h, _ = core.lag_hours(qx, qy)
    acc = {}
    for k, (h, _, fl) in hx.items():
        q = qy.get(k - lag_h)
        if fl or q is None or q[2] or q[0] <= 0:
            continue
        ln_r = float(rat.lnq(h))
        sl = float(rat.slope(h))
        if not (np.isfinite(ln_r) and np.isfinite(sl)) or sl <= 0:
            continue
        d = dt.datetime.fromtimestamp(k * 3600, dt.timezone.utc).date().isoformat()
        a = acc.setdefault(d, [0.0, 0.0, 0.0, 0])
        a[0] += math.log(q[0]) - ln_r
        a[1] += sl
        a[2] += h
        a[3] += 1
    return {d: (a[0] / a[3], a[1] / a[3], a[2] / a[3]) for d, a in acc.items() if a[3] >= 20}


def lag_days(qx, qy):
    best, bestr = 0, -2
    for lag in (-2, -1, 0, 1, 2):
        a, b = [], []
        for d in qx:
            d1 = shift_day(d, -1)
            dy, dy1 = shift_day(d, -lag), shift_day(d1, -lag)
            if d1 in qx and dy in qy and dy1 in qy and min(qx[d], qx[d1], qy[dy], qy[dy1]) > 0:
                a.append(math.log(qx[d] / qx[d1]))
                b.append(math.log(qy[dy] / qy[dy1]))
        if len(a) > 300:
            r = float(np.corrcoef(a, b)[0, 1])
            if r > bestr:
                best, bestr = lag, r
    return best, bestr


def run(x, y, DV):
    rat = load_rating(x)
    if rat is None:
        return {"x": x, "y": y, "skip": "no rating"}
    hx = series(DV, x, "00065")
    qx = series(DV, x, "00060")
    NOW = [None]
    qy_now = None
    if Y_MODE == "rtfinal":
        qy_now = finalised_to_date(DV, y)
    if Y_MODE in ("realtime", "rtfinal"):
        qy = realtime_q(DV, y)
    elif Y_MODE == "interp":
        qy = realtime_q(DV, y, interpolate=True)
    else:
        qy = series(DV, y, "00060")
    if not qy or len(hx) < 400 or len(qx) < 400:
        return {"x": x, "y": y, "skip": "no data"}
    lag, lag_r = lag_days(qx, qy)
    ivday = iv_days(x, y, rat) if IV_MODE else None
    if IV_MODE and ivday is None:
        return {"x": x, "y": y, "skip": "no 15-minute data cached"}
    # pair coupling: correlation of daily ln Q (published) over the whole period
    a = [(math.log(qx[d]), math.log(qy[shift_day(d, -lag)])) for d in qx
         if shift_day(d, -lag) in qy and qx[d] > 0 and qy[shift_day(d, -lag)] > 0]
    coupling = float(np.corrcoef(np.array(a).T)[0, 1]) if len(a) > 300 else float("nan")

    t_from = max(dt.datetime.fromisoformat(START).replace(tzinfo=dt.timezone.utc),
                 rat.begin or dt.datetime(1900, 1, 1, tzinfo=dt.timezone.utc))
    vis = visits_with_offset(x, rat, t_from)
    # stability of the reference station's own control: offset changes between its visits
    raty = load_rating(y)
    vis_y = (visits_with_offset(y, raty, dt.datetime(2015, 1, 1, tzinfo=dt.timezone.utc))
             if raty is not None else [])

    def ref_stability(day):
        prev = [v for v in vis_y if v["day"] < day and daydiff(day, v["day"]) <= 730]
        if len(prev) < 4:
            return float("nan")
        return float(np.median(np.abs(np.diff([v["s_meas"] for v in prev]))))

    def day_obs(d, inj=0.0):
        """(y, x) for day d if usable: steady stage, positive reference discharge.
        inj: a stage-sensor offset injected for the sensitivity test (sensor reads low by inj,
        so the offset to be found increases by inj)."""
        if d not in hx:
            return None
        dp, dn = shift_day(d, -1), shift_day(d, 1)
        if dp not in hx or dn not in hx:
            return None
        if abs(hx[d] - hx[dp]) > STEADY_FT or abs(hx[dn] - hx[d]) > STEADY_FT:
            return None
        if ivday is not None:
            o = ivday.get(d)
            if o is None or inj:
                return None
            return o
        q = qy_now(shift_day(d, -lag), NOW[0]) if qy_now else qy.get(shift_day(d, -lag))
        if not q or q <= 0:
            return None
        h = hx[d] - inj
        ln_r = float(rat.lnq(h))
        sl = float(rat.slope(h))
        if not (np.isfinite(ln_r) and np.isfinite(sl)) or sl <= 0:
            return None
        return math.log(q) - ln_r, sl, h

    def window(d_from, d_to, inj=0.0):  # [d_from, d_to)
        ys, xs, hs = [], [], []
        n = daydiff(d_to, d_from)
        for i in range(max(n, 0)):
            o = day_obs(shift_day(d_from, i), inj)
            if o:
                ys.append(o[0])
                xs.append(o[1])
                hs.append(o[2])
        return np.array(ys), np.array(xs), np.array(hs)

    rows = []
    for i in range(1, len(vis)):
        T, P = vis[i], vis[i - 1]
        NOW[0] = T["day"]
        if T["day"] == P["day"]:
            continue
        yT, xT, hT = window(shift_day(T["day"], -WIN_D), T["day"])
        p_end = min(shift_day(P["day"], WIN_D + 1), T["day"])
        yP, xP, hP = window(shift_day(P["day"], 1), p_end)
        if len(yT) < MIN_DAYS or len(yP) < MIN_DAYS:
            continue
        dT = core.offset_ls(yT, xT, 0.0)
        dP = core.offset_ls(yP, xP, 0.0)
        # noise of D: scatter of per-day offsets about the fit, propagated to the LS estimate
        rT = yT - dT * xT
        rP = yP - dP * xP
        sdT = float(np.std(rT) / math.sqrt(np.sum(xT ** 2)))
        sdP = float(np.std(rP) / math.sqrt(np.sum(xP ** 2)))
        change = dT - dP
        noise = math.hypot(sdT, sdP)
        # stage-offset signature: within the T window, does the discrepancy change scale with
        # the log-slope (offset) better than a constant ratio does?
        yy = np.concatenate([yP, yT])
        xx = np.concatenate([xP, xT])
        after = np.concatenate([np.zeros(len(yP)), np.ones(len(yT))])
        # model A (offset change): y = a + b*xP_flag... fitted as y - cP = ds * x * after
        cP = float(np.median(yP - dP * xP))
        resA = yy - cP - (dP + after * change) * xx
        cT_ratio = float(np.median(yT - dP * xT))     # ratio change: constant shift in y
        resB = yy - np.where(after == 1, cT_ratio, cP) - dP * xx
        sse_a, sse_b = float(np.sum(resA ** 2)), float(np.sum(resB ** 2))
        s_off = P["s_meas"] + change
        gate = abs(change) > GATE_K * noise and sse_a <= sse_b
        s_gated = s_off if gate else P["s_meas"]
        gh = T["gh"]
        q_carry = float(rat.q(gh + P["s_meas"]))
        ratio_change = float(np.median(yT) - np.median(yP))
        inj_resp = {}
        for inj in INJ:
            yI, xI, _ = window(shift_day(T["day"], -WIN_D), T["day"], inj)
            if len(yI) >= MIN_DAYS:
                inj_resp["%.2f" % inj] = core.offset_ls(yI, xI, 0.0) - dP - change
                inj_resp["ratio_%.2f" % inj] = float(np.median(yI) - np.median(yP)) - ratio_change
                inj_resp["w_%.2f" % inj] = [int(len(yI)), float(np.sum(xI)), float(np.sum(yI)),
                                            float(np.sum(xI ** 2)), float(np.sum(xI * yI))]
        # sufficient statistics of each window (n, sum x, sum y, sum x^2, sum x y), so that
        # estimators with a flow-ratio term can be formed from the stored rows
        def wstats(yy_, xx_):
            return [int(len(yy_)), float(np.sum(xx_)), float(np.sum(yy_)),
                    float(np.sum(xx_ ** 2)), float(np.sum(xx_ * yy_))]
        # largest flood between P and T: day of the highest daily mean stage
        between = [(hx[dd], dd) for dd in (shift_day(P["day"], k) for k in range(1, daydiff(T["day"], P["day"])))
                   if dd in hx]
        pk_h, pk_day = max(between) if between else (float("nan"), None)
        # rises between P and T: runs of days on which the daily mean stage increases, each
        # kept as (day of its crest, total rise in ft)
        rises, run_start = [], None
        days_pt = [shift_day(P["day"], k) for k in range(0, daydiff(T["day"], P["day"]) + 1)]
        for k in range(1, len(days_pt)):
            d0, d1 = days_pt[k - 1], days_pt[k]
            up = d0 in hx and d1 in hx and hx[d1] > hx[d0]
            if up and run_start is None:
                run_start = d0
            if (not up or k == len(days_pt) - 1) and run_start is not None:
                crest = d1 if up else d0
                if crest > P["day"] and crest < T["day"]:
                    rises.append((crest, float(hx[crest] - hx[run_start])))
                run_start = None
        rows.append({
            "wT": wstats(yT, xT), "wP": wstats(yP, xP), "peak_day": pk_day, "peak_h": pk_h,
            "rises": rises,
            "yxT": [[round(float(u), 6), round(float(v), 6)] for u, v in zip(yT, xT)],
            "yxP": [[round(float(u), 6), round(float(v), 6)] for u, v in zip(yP, xP)],
            "inj": inj_resp, "ratio_change": ratio_change, "ref_stab": ref_stability(T["day"]),
            "mT": float(np.median(yT)), "mP": float(np.median(yP)),
            "day": T["day"], "prev_day": P["day"], "gap_days": daydiff(T["day"], P["day"]),
            "q_meas": T["q"], "gh": gh, "gh_prev": P["gh"], "rated": T.get("rated"),
            "control": T.get("control"), "control_prev": P.get("control"),
            "s_meas": T["s_meas"], "s_prev": P["s_meas"],
            "dT": dT, "dP": dP, "change": change, "noise": noise, "sse_offset": sse_a,
            "sse_ratio": sse_b, "gate": bool(gate),
            "s_off": s_off, "s_gated": s_gated, "nT": len(yT), "nP": len(yP),
            "h_T_med": float(np.median(hT)), "h_P_med": float(np.median(hP)),
            "x_T_med": float(np.median(xT)), "x_P_med": float(np.median(xP)),
            "x_visit": float(rat.slope(gh)),
            "q_base": float(rat.q(gh)), "q_carry": q_carry,
            "q_ratio": q_carry * math.exp(ratio_change),
            "q_off": float(rat.q(gh + s_off)), "q_gated": float(rat.q(gh + s_gated)),
        })
    # adaptive gain: regression of measured offset changes on estimated changes over the
    # earlier visits of this station (only information available before each visit)
    for i, w in enumerate(rows):
        past = rows[:i]
        if len(past) >= GAIN_MIN_PAST:
            a = np.array([p["change"] for p in past])
            b = np.array([p["s_meas"] - p["s_prev"] for p in past])
            g = float(np.clip(np.sum(a * b) / max(float(np.sum(a * a)), 1e-9), 0.0, GAIN_MAX))
            ar = np.array([p["ratio_change"] for p in past])
            br = np.array([math.log(p["q_meas"] / p["q_carry"]) for p in past])
            gr = float(np.clip(np.sum(ar * br) / max(float(np.sum(ar * ar)), 1e-9), 0.0, GAIN_MAX))
        else:
            g = gr = GAIN_PRIOR
        w["gain"], w["gain_ratio"] = g, gr
        w["s_gain"] = w["s_prev"] + g * w["change"]
        w["q_gain"] = float(rat.q(w["gh"] + w["s_gain"]))
        w["q_ratio_gain"] = w["q_carry"] * math.exp(gr * w["ratio_change"])
    return {"x": x, "y": y, "lag_d": lag, "lag_r": lag_r, "coupling": coupling,
            "rating_id": rat.rating_id, "rating_begin": rat.begin.isoformat() if rat.begin else None,
            "n_visits": len(vis), "rows": rows}


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "daily"
    P = json.load(open(os.path.join(ROOT, "results", "pairs.json")))
    sites = sorted({s for p in P["pairs"] for s in (p["up"], p["down"])})
    DV = usgs.dv(sites, START, END, stats=("00003",))
    pinfo = {}
    for p in P["pairs"]:
        pinfo[(p["down"], p["up"])] = p
        pinfo[(p["up"], p["down"])] = p
    MIN_C = float(os.environ.get("MIN_COUPLING", "0.9"))
    coup = json.load(open(os.path.join(ROOT, "results", "coupling.json")))
    jobs = [(x, y, pinfo[(x, y)]) for x, y, incr, lag, lr, c in coup if c >= MIN_C]
    res = []
    for x, y, p in jobs:
        try:
            r = run(x, y, DV)
        except Exception as e:
            r = {"x": x, "y": y, "skip": "error: %r" % e}
        r["incr"] = p["incr"]
        r["names"] = (p["up_name"], p["down_name"])
        res.append(r)
    out = {"start": START, "end": END, "win_d": WIN_D, "min_days": MIN_DAYS, "steady_ft": STEADY_FT,
           "gate_k": GATE_K, "y_mode": Y_MODE, "results": res}
    json.dump(out, open(os.path.join(ROOT, "results", name + ".json"), "w"), indent=1, default=str)
    print("directions", len(res), "with rows", sum(1 for r in res if r.get("rows")),
          "rows", sum(len(r.get("rows", [])) for r in res))


if __name__ == "__main__":
    main()
