"""E6: the offset may jump only at a service and drifts at a bounded rate between services.

A long pollution episode lifts the floor with the river, and the plain method then removes real
ammonium. The electrode offset changes abruptly only when the sonde is serviced (recalibrated or
swapped: a gap in the record) and drifts slowly in between. So:

  seg      floor window starts no earlier than the last service before t (a window does not mix
           two calibrations); at least MIN_SEG readings, else the plain 7-day window
  guarded  offset path from the last laboratory sample, where the offset is known exactly
           (its departure); stepped every STEP_H hours to t: the target is F_seg - g; across a
           service the offset jumps to the target; between services it moves towards the target
           by at most RATE * elapsed days
  RATE     the 90th percentile of |change of departure| / days between consecutive samples with
           no service between them, measured on the OTHER half of the sondes (cross-fitted)

Compared on the same samples with the plain method and the practice chosen per sonde (evidence.py).
Output: results/e6_guard.json, results/e6_rows.json
"""
import bisect
import datetime as dt
import json
import os
import statistics as S

import core
import ea
import evidence as EV

GAP_H, MIN_SEG, STEP_H, RATE_Q = 6, 96, 6, 0.90
# drift reported by the manufacturer for the EXO ammonium ISE over a 73-day deployment, larger of
# the two sites (prior_art_raw/lit/ysi_exo_ammonium_uk.txt): 0.31 mg/L in 73 days
VENDOR_RATE = 0.31 / 73


def services(at):
    return [at[0]] + [at[i] for i in range(1, len(at)) if (at[i] - at[i - 1]).total_seconds() > GAP_H * 3600]


def floor(at, av, serv, t, seg):
    i1 = bisect.bisect_right(at, t)
    start = t - dt.timedelta(days=EV.FLOOR_DAYS)
    if seg:
        k = bisect.bisect_right(serv, t) - 1
        if k >= 0 and serv[k] > start:
            i0s = bisect.bisect_left(at, serv[k])
            if i1 - i0s >= MIN_SEG:
                return EV.quant(av[i0s:i1], EV.FLOOR_Q)
    i0 = bisect.bisect_left(at, start)
    return EV.quant(av[i0:i1], EV.FLOOR_Q) if i1 - i0 >= EV.MIN_READ else None


def rates(data, keys):
    out = []
    for k in keys:
        d = data[k]
        serv = services(d["at"])
        smp = d["samples"]
        for a, b in zip(smp, smp[1:]):
            days = (b["t"] - a["t"]).total_seconds() / 86400
            if days <= 0:
                continue
            if bisect.bisect_right(serv, b["t"]) != bisect.bisect_right(serv, a["t"]):
                continue                      # a service between them: not drift
            out.append(abs((b["sonde"] - b["lab"]) - (a["sonde"] - a["lab"])) / days)
    out.sort()
    return out[int(RATE_Q * (len(out) - 1))]


def run_site(d, g_by_sample, rate):
    at, av = d["at"], d["av"]
    serv = services(at)
    smp = d["samples"]
    res = []
    fseg = [floor(at, av, serv, x["t"], True) for x in smp]
    for i, x in enumerate(smp):
        if i == 0 or fseg[i] is None:
            res.append(None)
            continue
        prior = [(smp[j], fseg[j]) for j in range(max(0, i - EV.WINDOW), i) if fseg[j] is not None]
        if not prior:
            res.append(None)
            continue
        g = S.median(f - (p["sonde"] - p["lab"]) for p, f in prior)
        seg_val = max(x["sonde"] - (fseg[i] - g), 0.0)
        last = smp[i - 1]
        o = last["sonde"] - last["lab"]              # offset known exactly at the last sample
        tau = last["t"]
        while tau < x["t"]:
            nxt = min(tau + dt.timedelta(hours=STEP_H), x["t"])
            f = floor(at, av, serv, nxt, True)
            if f is not None:
                target = f - g
                if bisect.bisect_right(serv, nxt) != bisect.bisect_right(serv, tau):
                    o = target                       # service: a new calibration, jump allowed
                else:
                    step = rate * (nxt - tau).total_seconds() / 86400
                    o = min(max(target, o - step), o + step)
            tau = nxt
        res.append({"seg": seg_val, "guarded": max(x["sonde"] - o, 0.0)})
    return res


def main():
    data = EV.load()
    rows, keys = EV.evaluate(data)
    halves = {"first": keys[0::2], "second": keys[1::2]}
    rate_for = {}
    mode = os.environ.get("RATE_MODE", "crossfit")
    for name, part in halves.items():
        other = halves["second" if name == "first" else "first"]
        r = {"crossfit": lambda: rates(data, other), "vendor": lambda: VENDOR_RATE, "hold": lambda: 0.0}[mode]()
        for k in part:
            rate_for[k] = r
    by = {}
    for r in rows:
        by.setdefault(r["station"], []).append(r)
    out_rows = []
    for k in keys:
        # same samples, same order as evidence.evaluate (floor window present)
        d = dict(data[k])
        d["samples"] = [x for x in data[k]["samples"]
                        if x["t"].isoformat() in {r["t"] for r in by[k]}]
        g = run_site(d, None, rate_for[k])
        for r, gv in zip(by[k], g):
            if r["i"] >= 1 and gv is not None:
                out_rows.append(dict(r, seg=gv["seg"], guarded=gv["guarded"], rate=rate_for[k]))
    E = lambda rs, h: [abs(r[h] - r["lab"]) for r in rs]
    H = ("practice_best", "last", "method", "seg", "guarded")
    out = {"rates_mgL_per_day": {n: rates(data, p) for n, p in halves.items()},
           "n": len(out_rows), "all": {h: EV.summary(E(out_rows, h)) for h in H},
           "paired_vs_practice_best": {h: EV.sign(E(out_rows, h), E(out_rows, "practice_best")) for h in H if h != "practice_best"},
           "guarded_vs_method": EV.sign(E(out_rows, "guarded"), E(out_rows, "method"))}
    out["by_lab_band"] = {}
    for lo, hi in EV.BANDS:
        sub = [r for r in out_rows if lo <= r["lab"] < hi]
        out["by_lab_band"]["%g-%g" % (lo, hi)] = {
            **{h: EV.summary(E(sub, h)) for h in H},
            "paired_guarded_vs_best": EV.sign(E(sub, "guarded"), E(sub, "practice_best")),
            "under_read": {h: sum(1 for r in sub if r[h] < r["lab"]) for h in H}}
    out["alarms"] = {}
    for T in EV.THRESHOLDS:
        d = {"lab_exceed": sum(1 for r in out_rows if r["lab"] > T)}
        for h in H:
            d[h] = {"false_alarms": sum(1 for r in out_rows if r[h] > T and r["lab"] <= T),
                    "missed": sum(1 for r in out_rows if r[h] <= T and r["lab"] > T)}
        out["alarms"]["%g" % T] = d
    per = {}
    for r in out_rows:
        per.setdefault(r["station"], []).append(r)
    out["sites_better_than_best"] = {h: sum(1 for v in per.values() if S.mean(E(v, h)) < S.mean(E(v, "practice_best")))
                                     for h in ("method", "seg", "guarded")}
    out["sites"] = len(per)
    out["bootstrap_guarded_vs_best"] = EV.site_boot(out_rows, "guarded", "practice_best", 21)
    out["bootstrap_method_vs_best"] = EV.site_boot(out_rows, "method", "practice_best", 21)
    tag = "" if os.environ.get("RATE_MODE", "crossfit") == "crossfit" else "_" + os.environ["RATE_MODE"]
    core.dump("e6_guard%s.json" % tag, out)
    core.dump("e6_rows%s.json" % tag, out_rows)
    print("rates", out["rates_mgL_per_day"], "n", out["n"], "sites", out["sites"])
    for h in H:
        a = out["all"][h]
        print("%-14s median %.3f p90 %.2f trim %.2f mean %.1f" % (h, a["median"], a["p90"], a["trimmed_mean_99"], a["mean"]))
    print("paired vs best", {h: (v["better"], v["of"], round(v["z"], 2)) for h, v in out["paired_vs_practice_best"].items()})
    print("guarded vs method", out["guarded_vs_method"])
    for k, v in out["by_lab_band"].items():
        print(k, {h: round(v[h]["median"], 3) for h in H}, "z", round(v["paired_guarded_vs_best"]["z"], 2), "under", v["under_read"])
    print("alarms", json.dumps({t: {h: (a[h]["false_alarms"], a[h]["missed"]) for h in H} for t, a in out["alarms"].items()}))
    print("sites better", out["sites_better_than_best"])
    print("boot guarded", json.dumps(out["bootstrap_guarded_vs_best"]))


if __name__ == "__main__":
    main()
