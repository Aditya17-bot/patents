"""Feasibility probe: does a neighbouring gauge predict the rating offset that the
hydrographer later measures at a field visit?

For each admitted gauge pair and each direction (target X, reference Y), at every field
visit T at X with a measured discharge, the offset is estimated from the 14 days of
hourly data BEFORE T only (what a real-time system has), and compared with the measured
offset s_meas = R^-1(Q_meas) - GH_meas.

Output: results/probe.json
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
PAIRS = os.path.join(ROOT, "results", os.environ.get("PAIRS", "pairs.json"))
OUT = os.path.join(ROOT, "results", os.environ.get("PROBE_OUT", "probe.json"))

WINDOW_H = 14 * 24       # trailing window before each visit
PRIOR_VISITS = 6         # visits used to fix the flow ratio c
MIN_HOURS = 120          # usable hours required in the window
Y_MODE = os.environ.get("Y_MODE", "published")  # or "realtime"


def realtime_discharge(y, start, end):
    """Reference discharge as a real-time system would have computed it: base rating at the
    recorded stage plus the offset measured at the most recent earlier field visit."""
    r = usgs.rating(y, "exsa")
    if not r.get("table"):
        return None
    rat = core.Rating(r["table"])
    hy = core.hourly(usgs.iv(y, "00065", start, end))
    vis = [v for v in usgs.field_visits(y) if v["q"] > 0]
    times = [core.to_hour(v["time"]) for v in vis]
    shifts = []
    for v in vis:
        g = rat.g_of_q(v["q"])
        shifts.append(float(g - v["gh"]) if np.isfinite(g) else float("nan"))
    out = {}
    j = -1
    last = 0.0
    for k in sorted(hy):
        while j + 1 < len(times) and times[j + 1] <= k:
            j += 1
            if np.isfinite(shifts[j]):
                last = shifts[j]
        h, prov, fl = hy[k]
        q = float(rat.q(h + last))
        if np.isfinite(q):
            out[k] = (q, prov, fl)
    return out


def load_target(x, start, end):
    r = usgs.rating(x, "exsa")
    if not r.get("table"):
        return None
    beg = r.get("begin")
    begin = dt.datetime.strptime(beg[:14], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc) if beg and beg[0].isdigit() else None
    rat = core.Rating(r["table"], r.get("rating_id", ""), begin)
    hx = core.hourly(usgs.iv(x, "00065", start, end))
    qx = core.hourly(usgs.iv(x, "00060", start, end))
    visits = usgs.field_visits(x)
    return rat, hx, qx, visits


def run_direction(x, y, start, end):
    t = load_target(x, start, end)
    if t is None:
        return {"x": x, "y": y, "skip": "no rating"}
    rat, hx, qx, visits = t
    if Y_MODE == "realtime":
        qy = realtime_discharge(y, start, end)
        if qy is None:
            return {"x": x, "y": y, "skip": "no reference rating"}
    else:
        qy = core.hourly(usgs.iv(y, "00060", start, end))
    lag, lag_r = core.lag_hours(qx, qy)
    t0 = dt.datetime.fromisoformat(start).replace(tzinfo=dt.timezone.utc)
    t_rating = max(t0, rat.begin) if rat.begin else t0
    vis = [v for v in visits if v["time"] >= t_rating and v["q"] > 0]
    # measured offset at every visit
    for v in vis:
        v["s_meas"] = float(rat.g_of_q(v["q"]) - v["gh"])
        k = core.to_hour(v["time"])
        qy_v = [qy[kk][0] for kk in range(k - lag - 1, k - lag + 2) if kk in qy]
        v["c_v"] = math.log(np.mean(qy_v)) - math.log(v["q"]) if qy_v else float("nan")
    dcorr = core.daily_corr(qx, qy, lag)

    def window(k_a, k_b):
        ys, xs, hs = [], [], []
        for k in range(k_a, k_b):
            if k not in hx or (k - lag) not in qy:
                continue
            h, _, fl = hx[k]
            q, _, fly = qy[k - lag]
            if fl or fly or q <= 0:
                continue
            ln_r = rat.lnq(h)
            sl = rat.slope(h)
            if not (np.isfinite(ln_r) and np.isfinite(sl)) or sl <= 0:
                continue
            ys.append(math.log(q) - ln_r)
            xs.append(sl)
            hs.append(h)
        return np.array(ys), np.array(xs), np.array(hs)

    rows = []
    for i, v in enumerate(vis):
        prev = [w for w in vis[:i] if math.isfinite(w["s_meas"]) and math.isfinite(w["c_v"])]
        if len(prev) < PRIOR_VISITS or not math.isfinite(v["s_meas"]):
            continue
        P = prev[-1]
        prev = prev[-PRIOR_VISITS:]
        c = float(np.median([w["c_v"] for w in prev]))
        c_sd = float(np.std([w["c_v"] for w in prev]))
        kT = core.to_hour(v["time"])
        kP = core.to_hour(P["time"])
        yT, xT, hT = window(kT - WINDOW_H, kT)
        yP, xP, hP = window(kP, min(kP + WINDOW_H, kT))
        if len(yT) < MIN_HOURS or len(yP) < MIN_HOURS // 2:
            continue
        s_abs = core.offset_ls(yT, xT, c)
        dT = core.offset_ls(yT, xT, 0.0)
        dP = core.offset_ls(yP, xP, 0.0)
        s_delta = P["s_meas"] + (dT - dP)
        s_free, c_free, spread = core.offset_free_ratio(yT, xT)
        gh = v["gh"]
        q_base = float(rat.q(gh))
        q_carry = float(rat.q(gh + P["s_meas"]))
        qy_T = [qy[kk][0] for kk in range(kT - lag - 1, kT - lag + 2) if kk in qy]
        q_transfer = float(np.mean(qy_T) * math.exp(-P["c_v"])) if qy_T else float("nan")
        # conventional ratio correction carried in discharge units since the last visit
        rT = float(np.median(yT))
        rP = float(np.median(yP))
        q_ratio = q_carry * math.exp(rT - rP)
        rows.append({
            "time": v["time"].isoformat(), "prev_time": P["time"].isoformat(),
            "q_meas": v["q"], "gh": gh, "gh_prev": P["gh"], "rated": v.get("rated"),
            "control": v.get("control"), "s_meas": v["s_meas"], "s_prev": P["s_meas"],
            "c": c, "c_sd": c_sd, "s_abs": s_abs, "s_delta": s_delta, "dT": dT, "dP": dP,
            "s_free": s_free, "x_spread": spread, "n_T": len(yT), "n_P": len(yP),
            "h_win_med": float(np.median(hT)), "x_at_visit": float(rat.slope(gh)),
            "q_base": q_base, "q_carry": q_carry, "q_transfer": q_transfer, "q_ratio": q_ratio,
            "q_abs": float(rat.q(gh + s_abs)), "q_delta": float(rat.q(gh + s_delta)),
        })
    return {"x": x, "y": y, "lag_h": lag, "lag_r": lag_r, "rating_id": rat.rating_id,
            "rating_begin": rat.begin.isoformat() if rat.begin else None,
            "n_visits": len(vis), "daily_corr": dcorr, "rows": rows}


def main():
    P = json.load(open(PAIRS))
    start, end = P["start"], P["end"]
    jobs = []
    for p in P["pairs"]:
        jobs.append((p["down"], p["up"]))
        jobs.append((p["up"], p["down"]))
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else len(jobs)
    jobs = jobs[:lim]

    def go(j):
        try:
            return run_direction(j[0], j[1], start, end)
        except Exception as e:
            return {"x": j[0], "y": j[1], "skip": "error: %s" % e}

    res = []
    with ThreadPoolExecutor(6) as ex:
        for r in ex.map(go, jobs):
            res.append(r)
            print(r["x"], r["y"], r.get("skip", ""), r.get("lag_h"), len(r.get("rows", [])), flush=True)
    json.dump({"window_h": WINDOW_H, "prior_visits": PRIOR_VISITS, "results": res},
              open(OUT, "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
