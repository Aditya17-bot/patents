"""Shared steps: matched sonde/laboratory pairs and the correction estimators.

Each site yields a time-ordered list of matched samples
    (time, lab ammonium, sonde ammonium, sonde conductivity, sonde temperature, days since service)
where the sonde values are the readings nearest to the laboratory sampling time (within
MATCH_MIN minutes) and a service is a gap longer than GAP_H hours in the ammonium record.

Estimators, each fitted only on samples taken before the one being corrected:
    offset   reading - median(prior departures)                       (single correction value)
    drift    reading - (a + b t), departure fitted linearly in time   (drift between checks)
    method   reading - (b + k * conductivity), k >= 0                 (cation interference)
A departure is sonde - lab, in mg/L N.
"""
import bisect
import datetime as dt
import json
import os
import statistics as S

import ea

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MATCH_MIN = int(os.environ.get("MATCH_MIN", 30))
GAP_H = 6
WINDOW = int(os.environ.get("WINDOW", 12))       # most recent prior samples used for a fit
MIN_PRIOR = int(os.environ.get("MIN_PRIOR", 6))  # prior samples needed before a sample is scored


def nearest(times, values, t, max_min):
    i = bisect.bisect_left(times, t)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(times):
            d = abs((times[j] - t).total_seconds()) / 60
            if d <= max_min and (best is None or d < best[0]):
                best = (d, values[j])
    return None if best is None else best[1]


def site_samples(s):
    """Matched samples for one paired site (see module docstring)."""
    amm = [r for r in ea.readings(s["station"] + "-amm-i-subdaily-mgL", s["opened"], s["closed"])
           if r[1] >= 0]
    cond = [r for r in ea.readings(s["station"] + "-cond-i-subdaily-uS", s["opened"], s["closed"])
            if r[1] > 0]
    try:
        temp = ea.readings(s["station"] + "-temp-i-subdaily-C", s["opened"], s["closed"])
    except Exception:
        temp = []
    if len(amm) < 500 or len(cond) < 500:
        return []
    at, av = [r[0] for r in amm], [r[1] for r in amm]
    ct, cv = [r[0] for r in cond], [r[1] for r in cond]
    tt, tv = [r[0] for r in temp], [r[1] for r in temp]
    serv = [at[0]] + [at[i] for i in range(1, len(at))
                      if (at[i] - at[i - 1]).total_seconds() > GAP_H * 3600]
    out = []
    for t, lab, unit, below, purpose in ea.samples(s["point"], "0111"):
        if not (s["opened"] <= t.date().isoformat() <= s["closed"]):
            continue
        a = nearest(at, av, t, MATCH_MIN)
        c = nearest(ct, cv, t, MATCH_MIN)
        if a is None or c is None:
            continue
        if abs(a - lab) < 1e-6:          # archive value copied from the sonde, not a laboratory result
            continue
        tc = nearest(tt, tv, t, MATCH_MIN) if tt else None
        k = bisect.bisect_right(serv, t) - 1
        out.append({"t": t, "lab": lab, "sonde": a, "sc": c, "temp": tc,
                    "since_service_d": (t - serv[k]).total_seconds() / 86400, "purpose": purpose})
    out.sort(key=lambda x: x["t"])
    return out


def fit_line(xs, ys):
    mx, my = S.mean(xs), S.mean(ys)
    sxx = sum((a - mx) ** 2 for a in xs)
    if sxx == 0:
        return 0.0, S.median(ys)
    k = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / sxx
    return k, my - k * mx


def fit_nonneg(xs, ys):
    """Least squares y = k x + b with k >= 0 (an interferent can only add to the reading)."""
    k, b = fit_line(xs, ys)
    if k < 0:
        return 0.0, S.median(ys)
    return k, b


def predict(prior, x, how):
    """Corrected ammonium for sample x from the prior samples, by estimator `how`."""
    p = prior[-WINDOW:]
    dep = [q["sonde"] - q["lab"] for q in p]
    if how == "raw":
        return x["sonde"]
    if how == "offset":
        return max(x["sonde"] - S.median(dep), 0.0)
    if how == "drift":
        t0 = p[0]["t"]
        k, b = fit_line([(q["t"] - t0).total_seconds() / 86400 for q in p], dep)
        return max(x["sonde"] - (b + k * (x["t"] - t0).total_seconds() / 86400), 0.0)
    if how == "method":
        k, b = fit_nonneg([q["sc"] for q in p], dep)
        return max(x["sonde"] - (b + k * x["sc"]), 0.0)
    if how == "method_free":                     # ablation: k not constrained to be >= 0
        k, b = fit_line([q["sc"] for q in p], dep)
        return max(x["sonde"] - (b + k * x["sc"]), 0.0)
    if how == "placebo_temp":                    # control: same fit on water temperature
        pp = [q for q in p if q["temp"] is not None]
        if len(pp) < 3 or x["temp"] is None:
            return max(x["sonde"] - S.median(dep), 0.0)
        k, b = fit_line([q["temp"] for q in pp], [q["sonde"] - q["lab"] for q in pp])
        return max(x["sonde"] - (b + k * x["temp"]), 0.0)
    if how == "placebo_shuffled":                # control: conductivity of a different prior sample
        sc = [q["sc"] for q in p]
        shuffled = sc[1:] + sc[:1]
        k, b = fit_nonneg(shuffled, dep)
        return max(x["sonde"] - (b + k * x["sc"]), 0.0)
    raise ValueError(how)


ESTIMATORS = ["raw", "offset", "drift", "method", "method_free", "placebo_temp", "placebo_shuffled"]


def scored(samples):
    """One-step-ahead predictions for every sample with enough prior samples."""
    rows = []
    for i in range(MIN_PRIOR, len(samples)):
        x = samples[i]
        r = {"t": x["t"].isoformat(), "lab": x["lab"], "sonde": x["sonde"], "sc": x["sc"],
             "since_service_d": x["since_service_d"]}
        for how in ESTIMATORS:
            r[how] = predict(samples[:i], x, how)
        rows.append(r)
    return rows


def load_sites(name="sites_amm.json"):
    return json.load(open(os.path.join(RESULTS, name)))


def dump(name, obj):
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, name), "w") as fh:
        json.dump(obj, fh, indent=1, default=str)
