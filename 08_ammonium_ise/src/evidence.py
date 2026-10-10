"""Evidence for the IDF-B: ammonium sonde corrected by its own floor, anchored at laboratory samples.

For each site, matched samples (core.site_samples) are taken in time order and sample i is
corrected using only the readings up to its own time and the laboratory results before it.

    floor(t)   FLOOR_Q quantile of the sonde's ammonium readings over the FLOOR_DAYS before t
               (at least MIN_READ readings)
    gap g      median over the WINDOW most recent prior samples of floor(t_j) - (A(t_j) - L(t_j)):
               how far the floor sits above the true concentration's background at this site
    method     A(t) - (floor(t) - g), not below zero
Baselines from the same prior samples (current practice, reading - correction value):
    median     median of prior departures A - L                 (US 8,691,074: a fixed correction)
    last       departure of the most recent prior sample
    trend      departures fitted linearly in time, extrapolated to t
Ablation: floor_net  A(t) - (floor(t) - network background)   (floor without the laboratory anchor)
Cold start (no prior sample at the site): method uses the network background as g;
compared with the raw reading and with the network constant (mean departure of other sites).

Also: change of floor against change of departure between consecutive samples (the floor
follows the sensor offset), mechanism splits, alarms, station bootstrap, hold-out halves of the
stations, and sensitivity of FLOOR_DAYS, FLOOR_Q and WINDOW.
Outputs: results/ev_main.json, results/ev_rows.json, results/ev_sens.json
"""
import bisect
import datetime as dt
import json
import math
import os
import random
import statistics as S
import time

import core
import ea

FLOOR_DAYS, FLOOR_Q, WINDOW, MIN_READ = 7.0, 0.05, 12, 96
THRESHOLDS = (0.6, 1.0, 2.0)
BANDS = ((0, 0.2), (0.2, 1.0), (1.0, 3.0), (3.0, 1e9))


def quant(v, q):
    v = sorted(v)
    return v[int(q * (len(v) - 1))]


def summary(e):
    e = sorted(e)
    n = len(e)
    if not n:
        return {"n": 0}
    return {"n": n, "mean": S.mean(e), "median": e[n // 2], "p90": e[int(0.9 * n)],
            "trimmed_mean_99": S.mean(e[:max(1, int(0.99 * n))])}


def sign(a, b):
    better = sum(1 for x, y in zip(a, b) if x < y - 1e-9)
    worse = sum(1 for x, y in zip(a, b) if x > y + 1e-9)
    n = better + worse
    return {"better": better, "worse": worse, "of": n, "z": (better - n / 2) / math.sqrt(n / 4) if n else 0.0}


def pearson(x, y):
    mx, my = S.mean(x), S.mean(y)
    den = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / den if den else float("nan")


def load():
    """Matched samples with the raw ammonium record of each paired site."""
    out = {}
    for s in core.load_sites():
        try:
            smp = core.site_samples(s)
            amm = [r for r in ea.readings(s["station"] + "-amm-i-subdaily-mgL", s["opened"], s["closed"]) if r[1] >= 0]
        except Exception:
            continue
        if len(smp) >= 3:
            out[s["station"]] = {"site": s, "samples": smp, "at": [r[0] for r in amm], "av": [r[1] for r in amm]}
    return out


def with_floor(d, days, q):
    """Samples of one site with floor(t); samples whose window holds too few readings are dropped."""
    at, av = d["at"], d["av"]
    keep = []
    for x in d["samples"]:
        i1 = bisect.bisect_right(at, x["t"])
        i0 = bisect.bisect_left(at, x["t"] - dt.timedelta(days=days))
        if i1 - i0 >= MIN_READ:
            keep.append(dict(x, floor=quant(av[i0:i1], q)))
    return keep


def evaluate(data, days=FLOOR_DAYS, q=FLOOR_Q, window=WINDOW):
    smp = {k: with_floor(v, days, q) for k, v in data.items()}
    smp = {k: v for k, v in smp.items() if len(v) >= 3}
    keys = sorted(smp)
    labq = {k: quant([x["lab"] for x in smp[k]], 0.10) for k in keys}
    deps_all = {k: [x["sonde"] - x["lab"] for x in smp[k]] for k in keys}
    rows = []
    for held in keys:
        bg = S.median(labq[k] for k in keys if k != held)
        pool = sorted(d for k in keys if k != held for d in deps_all[k])
        lo, hi = pool[int(0.01 * len(pool))], pool[int(0.99 * len(pool)) - 1]
        cnet = S.mean(d for d in pool if lo <= d <= hi)
        s = smp[held]
        for i, x in enumerate(s):
            prior = s[:i][-window:]
            r = {"station": held, "i": i, "t": x["t"].isoformat(), "lab": x["lab"], "sonde": x["sonde"],
                 "floor": x["floor"], "since_service_d": x["since_service_d"], "raw": x["sonde"],
                 "floor_net": max(x["sonde"] - (x["floor"] - bg), 0.0),
                 "net_const": max(x["sonde"] - cnet, 0.0)}
            if prior:
                dep = [p["sonde"] - p["lab"] for p in prior]
                g = S.median(p["floor"] - (p["sonde"] - p["lab"]) for p in prior)
                r["median"] = max(x["sonde"] - S.median(dep), 0.0)
                r["last"] = max(x["sonde"] - dep[-1], 0.0)
                if len(prior) >= 2:
                    t0 = prior[0]["t"]
                    k, b = core.fit_line([(p["t"] - t0).total_seconds() / 86400 for p in prior], dep)
                    r["trend"] = max(x["sonde"] - (b + k * (x["t"] - t0).total_seconds() / 86400), 0.0)
                else:
                    r["trend"] = r["last"]
                r["serviced_since_last_lab"] = (x["t"] - prior[-1]["t"]).total_seconds() / 86400 > x["since_service_d"]
            else:
                g = bg
            r["g"] = g
            r["method"] = max(x["sonde"] - (x["floor"] - g), 0.0)
            rows.append(r)
    # two-tier alarm values: watch = the larger, confirmed = the smaller of the floor-tracked and the
    # last-sample corrections (two independent estimates of the offset in force)
    for r in rows:
        if r["i"] >= 1:
            r["watch"] = max(r["method"], r["last"])
            r["confirmed"] = min(r["method"], r["last"])
    # practice chosen per site: of median, last and trend, the one with the lowest mean error on the
    # site's earlier scored samples (at least 3), otherwise median
    by = {}
    for r in rows:
        by.setdefault(r["station"], []).append(r)
    for v in by.values():
        done = []
        for r in v:
            if r["i"] >= 1:
                if len(done) >= 3:
                    best = min(("median", "last", "trend"), key=lambda h: S.mean(abs(q[h] - q["lab"]) for q in done))
                else:
                    best = "median"
                r["practice_best"] = r[best]
                r["practice_best_choice"] = best
                done.append(r)
    return rows, keys


def err(rows, h):
    return [abs(r[h] - r["lab"]) for r in rows]


def site_boot(rows, a, b, seed, filt=lambda r: True, n=2000):
    per = {}
    for r in rows:
        if filt(r):
            per.setdefault(r["station"], []).append(r)
    keys = sorted(per)
    rng = random.Random(seed)
    st = {"median": [], "p90": [], "trimmed_mean_99": []}
    for _ in range(n):
        pick = [rng.choice(keys) for _ in keys]
        ea_ = sorted(abs(r[a] - r["lab"]) for k in pick for r in per[k])
        eb = sorted(abs(r[b] - r["lab"]) for k in pick for r in per[k])
        st["median"].append(eb[len(eb) // 2] - ea_[len(ea_) // 2])
        st["p90"].append(eb[int(0.9 * len(eb))] - ea_[int(0.9 * len(ea_))])
        st["trimmed_mean_99"].append(S.mean(eb[:int(0.99 * len(eb))]) - S.mean(ea_[:int(0.99 * len(ea_))]))
    return {k: {"mean": S.mean(v), "ci95": [sorted(v)[int(0.025 * n)], sorted(v)[int(0.975 * n) - 1]]} for k, v in st.items()}


def main():
    data = load()
    rows, keys = evaluate(data)
    later = [r for r in rows if r["i"] >= 1]
    first = [r for r in rows if r["i"] == 0]
    out = {"meta": {"floor_days": FLOOR_DAYS, "floor_q": FLOOR_Q, "window": WINDOW, "min_read": MIN_READ,
                    "match_min": core.MATCH_MIN, "sites_paired": len(core.load_sites()), "sites": len(keys),
                    "samples": len(rows), "samples_with_prior": len(later),
                    "period": [min(r["t"] for r in rows)[:10], max(r["t"] for r in rows)[:10]],
                    "readings": sum(len(data[k]["av"]) for k in keys)}}
    H = ("raw", "median", "last", "trend", "practice_best", "floor_net", "method")
    out["with_prior"] = {h: summary(err(later, h)) for h in H}
    out["with_prior_paired"] = {h: sign(err(later, "method"), err(later, h)) for h in H if h != "method"}
    per = {}
    for r in later:
        per.setdefault(r["station"], []).append(r)
    out["sites_better"] = {h: sum(1 for v in per.values() if S.mean(err(v, "method")) < S.mean(err(v, h)))
                           for h in ("median", "last", "trend", "practice_best")}
    out["sites_with_prior"] = len(per)
    out["bootstrap_vs_median"] = site_boot(rows, "method", "median", 9, lambda r: r["i"] >= 1)
    out["bootstrap_vs_last"] = site_boot(rows, "method", "last", 10, lambda r: r["i"] >= 1)
    out["bootstrap_vs_practice_best"] = site_boot(rows, "method", "practice_best", 11, lambda r: r["i"] >= 1)
    # cold start
    out["cold_start"] = {h: summary(err(rows, h)) for h in ("raw", "net_const", "floor_net")}
    out["cold_start_paired"] = {h: sign(err(rows, "floor_net"), err(rows, h)) for h in ("raw", "net_const")}
    out["first_sample"] = {h: summary(err(first, h)) for h in ("raw", "net_const", "method")}
    out["first_sample_paired"] = {h: sign(err(first, "method"), err(first, h)) for h in ("raw", "net_const")}
    # mechanism: floor follows the offset between consecutive laboratory samples
    dfl, ddp = [], []
    by = {}
    for r in rows:
        by.setdefault(r["station"], []).append(r)
    for v in by.values():
        for a, b in zip(v, v[1:]):
            dfl.append(b["floor"] - a["floor"])
            ddp.append((b["sonde"] - b["lab"]) - (a["sonde"] - a["lab"]))
    pairs = sorted(zip(dfl, ddp), key=lambda p: p[1])
    lo, hi = int(0.01 * len(pairs)), int(0.99 * len(pairs))
    trim = pairs[lo:hi]
    k_, b_ = core.fit_line([p[0] for p in trim], [p[1] for p in trim])
    out["floor_follows_offset"] = {"n": len(pairs), "r_trimmed": pearson([p[0] for p in trim], [p[1] for p in trim]),
                                   "slope_departure_on_floor": k_, "same_sign": sum(1 for a, b in pairs if a * b > 0),
                                   "opposite_sign": sum(1 for a, b in pairs if a * b < 0)}
    # splits
    out["serviced"] = {}
    for name, f in (("serviced_since_last_lab", lambda r: r["serviced_since_last_lab"]),
                    ("not_serviced", lambda r: not r["serviced_since_last_lab"])):
        sub = [r for r in later if f(r)]
        out["serviced"][name] = {"median": summary(err(sub, "median")), "last": summary(err(sub, "last")),
                                 "method": summary(err(sub, "method")),
                                 "paired": sign(err(sub, "method"), err(sub, "median")),
                                 "paired_last": sign(err(sub, "method"), err(sub, "last"))}
    out["by_lab_band"] = {}
    for lo_, hi_ in BANDS:
        sub = [r for r in later if lo_ <= r["lab"] < hi_]
        out["by_lab_band"]["%g-%g" % (lo_, hi_)] = {
            "median": summary(err(sub, "median")), "method": summary(err(sub, "method")),
            "paired": sign(err(sub, "method"), err(sub, "median")),
            "under_read_median": sum(1 for r in sub if r["median"] < r["lab"]),
            "under_read_method": sum(1 for r in sub if r["method"] < r["lab"])}
    out["alarms"] = {}
    for T in THRESHOLDS:
        d = {"lab_exceed": sum(1 for r in later if r["lab"] > T), "lab_below": sum(1 for r in later if r["lab"] <= T)}
        for h in ("raw", "median", "last", "trend", "practice_best", "method", "watch", "confirmed"):
            d[h] = {"false_alarms": sum(1 for r in later if r[h] > T and r["lab"] <= T),
                    "missed": sum(1 for r in later if r[h] <= T and r["lab"] > T)}
        out["alarms"]["%g" % T] = d
    # hold-out halves of the stations (constants frozen above, stations dealt alternately)
    out["halves"] = {}
    for hname, part in (("first", keys[0::2]), ("second", keys[1::2])):
        sub = [r for r in later if r["station"] in part]
        out["halves"][hname] = {"sites": len(part), "median": summary(err(sub, "median")),
                                "practice_best": summary(err(sub, "practice_best")),
                                "method": summary(err(sub, "method")), "paired": sign(err(sub, "method"), err(sub, "median")),
                                "paired_best": sign(err(sub, "method"), err(sub, "practice_best"))}
    # processing time per sample of the correction (floor and gap), on one core
    t0 = time.perf_counter()
    for _ in range(3):
        evaluate({k: data[k] for k in keys[:10]})
    out["timing_s_per_10_sites"] = (time.perf_counter() - t0) / 3
    core.dump("ev_main.json", out)
    core.dump("ev_rows.json", rows)
    # sensitivity
    sens = []
    for days, q, w in ((3, 0.05, 12), (14, 0.05, 12), (7, 0.02, 12), (7, 0.10, 12), (7, 0.05, 6), (7, 0.05, 20)):
        rr, kk = evaluate(data, days, q, w)
        lt = [r for r in rr if r["i"] >= 1]
        sens.append({"floor_days": days, "floor_q": q, "window": w, "sites": len(kk), "n": len(lt),
                     "median": summary(err(lt, "median")), "practice_best": summary(err(lt, "practice_best")),
                     "method": summary(err(lt, "method")),
                     "paired": sign(err(lt, "method"), err(lt, "median")),
                     "paired_best": sign(err(lt, "method"), err(lt, "practice_best"))})
    core.dump("ev_sens.json", sens)
    print(json.dumps({k: out[k] for k in ("meta", "with_prior", "with_prior_paired", "sites_better", "sites_with_prior",
                                          "bootstrap_vs_median", "floor_follows_offset", "first_sample", "first_sample_paired",
                                          "halves", "timing_s_per_10_sites")}, indent=1, default=str))
    for s in sens:
        print("days %g q %.2f w %d: n %d median %.3f best %.3f -> %.3f  z %.2f zbest %.2f" % (s["floor_days"], s["floor_q"], s["window"], s["n"],
              s["median"]["median"], s["practice_best"]["median"], s["method"]["median"], s["paired"]["z"], s["paired_best"]["z"]))


if __name__ == "__main__":
    main()
