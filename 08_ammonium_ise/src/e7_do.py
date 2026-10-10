"""E7: dissolved oxygen tells a river episode from an electrode offset move.

Ammonium from sewage or slurry arrives with an oxygen demand, so a real episode lowers the
dissolved-oxygen saturation measured by the same sonde; a change of the ammonium electrode's
offset leaves the oxygen sensor untouched. Rule, fixed before scoring:

  o_floor = F(t) - g                    offset in force from the floor (claim 1)
  o_last  = A(t_last) - L(t_last)       offset at the most recent laboratory sample
  dDO     = median DO % over the floor window ending at t
            - median DO % over the floor window ending at t_last
  episode = (o_floor > o_last) and (dDO <= -DROP)
  offset  = o_last if episode else o_floor

DROP = 10 percentage points of saturation (also reported: 5 and 15, without choosing among them).
Samples without dissolved-oxygen readings in both windows keep o_floor.
Output: results/e7_do.json
"""
import bisect
import datetime as dt
import json
import os
import statistics as S

import core
import ea
import evidence as EV

DROP = 10.0
OTHER = (5.0, 15.0)
MIN_DO = 96


def do_med(dt_, dv, t):
    i1 = bisect.bisect_right(dt_, t)
    i0 = bisect.bisect_left(dt_, t - dt.timedelta(days=EV.FLOOR_DAYS))
    return S.median(dv[i0:i1]) if i1 - i0 >= MIN_DO else None


def main():
    data = EV.load()
    rows, keys = EV.evaluate(data)
    sites = {s["station"]: s for s in core.load_sites()}
    do = {}
    for k in keys:
        s = sites[k]
        try:
            r = [x for x in ea.readings(k + "-do-i-subdaily-pct", s["opened"], s["closed"]) if 0 <= x[1] <= 300]
        except Exception:
            r = []
        do[k] = ([x[0] for x in r], [x[1] for x in r])
    by = {}
    for r in rows:
        by.setdefault(r["station"], []).append(r)
    out_rows = []
    for k in keys:
        v = by[k]
        dtt, dvv = do[k]
        for i, r in enumerate(v):
            if r["i"] < 1:
                continue
            prev = v[i - 1]
            t, tl = dt.datetime.fromisoformat(r["t"]), dt.datetime.fromisoformat(prev["t"])
            o_floor = r["sonde"] - r["method"] if r["method"] > 0 else r["floor"] - r["g"]
            o_floor = r["floor"] - r["g"]
            o_last = prev["sonde"] - prev["lab"]
            d_now = do_med(dtt, dvv, t) if dtt else None
            d_then = do_med(dtt, dvv, tl) if dtt else None
            dDO = (d_now - d_then) if (d_now is not None and d_then is not None) else None
            rec = dict(r, dDO=dDO, o_floor=o_floor, o_last=o_last, has_do=dDO is not None)
            for drop in (DROP,) + OTHER:
                ep = dDO is not None and o_floor > o_last and dDO <= -drop
                off = o_last if ep else o_floor
                rec["do_%g" % drop] = max(r["sonde"] - off, 0.0)
                rec["episode_%g" % drop] = ep
            out_rows.append(rec)
    E = lambda rs, h: [abs(x[h] - x["lab"]) for x in rs]
    main_h = "do_%g" % DROP
    H = ("practice_best", "last", "method", main_h) + tuple("do_%g" % d for d in OTHER)
    out = {"drop_pp": DROP, "n": len(out_rows), "with_do": sum(1 for x in out_rows if x["has_do"]),
           "episodes": {("%g" % d): sum(1 for x in out_rows if x["episode_%g" % d]) for d in (DROP,) + OTHER},
           "all": {h: EV.summary(E(out_rows, h)) for h in H},
           "paired_vs_best": {h: EV.sign(E(out_rows, h), E(out_rows, "practice_best")) for h in H if h != "practice_best"},
           "paired_vs_method": {h: EV.sign(E(out_rows, h), E(out_rows, "method")) for h in H if h.startswith("do_")}}
    ep_rows = [x for x in out_rows if x["episode_%g" % DROP]]
    out["at_episodes"] = {h: EV.summary(E(ep_rows, h)) for h in ("practice_best", "method", main_h)}
    out["at_episodes_paired"] = EV.sign(E(ep_rows, main_h), E(ep_rows, "method"))
    out["by_lab_band"] = {}
    for lo, hi in EV.BANDS:
        sub = [x for x in out_rows if lo <= x["lab"] < hi]
        out["by_lab_band"]["%g-%g" % (lo, hi)] = {
            **{h: EV.summary(E(sub, h)) for h in ("practice_best", "method", main_h)},
            "paired_vs_method": EV.sign(E(sub, main_h), E(sub, "method")),
            "paired_vs_best": EV.sign(E(sub, main_h), E(sub, "practice_best"))}
    out["alarms"] = {}
    for T in EV.THRESHOLDS:
        d = {"lab_exceed": sum(1 for x in out_rows if x["lab"] > T)}
        for h in ("practice_best", "method", main_h):
            d[h] = {"false_alarms": sum(1 for x in out_rows if x[h] > T and x["lab"] <= T),
                    "missed": sum(1 for x in out_rows if x[h] <= T and x["lab"] > T)}
        out["alarms"]["%g" % T] = d
    halves = {"first": keys[0::2], "second": keys[1::2]}
    out["halves"] = {n: EV.sign(E([x for x in out_rows if x["station"] in p], main_h),
                                E([x for x in out_rows if x["station"] in p], "method")) for n, p in halves.items()}
    out["bootstrap_vs_best"] = EV.site_boot(out_rows, main_h, "practice_best", 31)
    per = {}
    for x in out_rows:
        per.setdefault(x["station"], []).append(x)
    out["sites_better_than_best"] = sum(1 for v in per.values() if S.mean(E(v, main_h)) < S.mean(E(v, "practice_best")))
    out["sites"] = len(per)
    core.dump("e7_do.json", out)
    core.dump("e7_rows.json", out_rows)
    print(json.dumps({k: out[k] for k in ("n", "with_do", "episodes", "paired_vs_best", "paired_vs_method",
                                          "at_episodes", "at_episodes_paired", "halves", "sites_better_than_best")}, indent=0, default=str))
    for h in H:
        a = out["all"][h]
        print("%-14s median %.3f p90 %.2f trim %.2f" % (h, a["median"], a["p90"], a["trimmed_mean_99"]))
    for k, v in out["by_lab_band"].items():
        print(k, {h: round(v[h]["median"], 3) for h in ("practice_best", "method", main_h)}, "vs method", v["paired_vs_method"])
    print("alarms", json.dumps({t: {h: (a[h]["false_alarms"], a[h]["missed"]) for h in ("practice_best", "method", main_h)} for t, a in out["alarms"].items()}))
    print("boot", json.dumps(out["bootstrap_vs_best"]))


if __name__ == "__main__":
    main()
