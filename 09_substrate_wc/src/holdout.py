"""Held-out test against the drain meter.

Calibrate each sensor's k from pre-drain pulses in the first half of the season only (no drain data used).
Predict the second half's daily retained water R = Irr - Drain (metered) as k * (sum of WC rises that day).
Baseline: one shared k for every sensor (the median over all sensors, as a factory scale would be).
"""
import json, os
import numpy as np
import pandas as pd
import agc
from pulse_gain import pulse_rises

ROOT = os.path.join(os.path.dirname(__file__), "..")


def per_sensor(team, s, x, daily):
    p = pulse_rises(x, s)
    p["day"] = p.t.dt.normalize()
    plat = x[f"WC_slab{s}"].groupby(x.index.normalize()).quantile(0.9)
    p["plat"] = p.day.map(plat)
    days = np.sort(p.day.unique())
    split = days[len(days) // 2]
    pre = p[(p.wc0 < p.plat - 3) & (p.rise > 0.3) & (p.vol > 0) & (p.day < split)]
    k_cal = float(pre.vol.sum() / pre.rise.sum())          # ratio of sums: beats 0.1-step quantisation
    rises = p[p.rise > 0].groupby("day").rise.sum()
    dd = daily.join(rises.rename("rises"), how="inner")
    dd = dd[(dd.rises > 2) & (dd.Irr > 0.5) & (dd.index >= split)]
    return k_cal, dd


def main():
    rows, ks = [], {}
    for team in agc.TEAMS:
        x, daily = agc.load(team)
        for s in (1, 2):
            k, dd = per_sensor(team, s, x, daily)
            ks[(team, s)] = k
            for day, r in dd.iterrows():
                rows.append(dict(team=team, s=s, day=str(day.date()), R=r.Irr - r.Drain, rises=r.rises))
    d = pd.DataFrame(rows)
    k_shared = float(np.median(list(ks.values())))
    d["k_cal"] = [ks[(t, s)] for t, s in zip(d.team, d.s)]
    d["err_cal"] = d.k_cal * d.rises - d.R
    d["err_shared"] = k_shared * d.rises - d.R
    summ = {}
    for (t, s), g in d.groupby(["team", "s"]):
        summ[f"{t}_{s}"] = dict(k_cal=round(ks[(t, s)], 4), n_days=len(g),
                               mae_cal=round(g.err_cal.abs().mean(), 3), mae_shared=round(g.err_shared.abs().mean(), 3),
                               bias_cal=round(g.err_cal.mean(), 3), bias_shared=round(g.err_shared.mean(), 3),
                               R_mean=round(g.R.mean(), 3))
    tot = dict(k_shared=round(k_shared, 4), n=len(d), R_mean=round(d.R.mean(), 3),
               mae_cal=round(d.err_cal.abs().mean(), 3), mae_shared=round(d.err_shared.abs().mean(), 3),
               median_abs_rel_cal=round((d.err_cal.abs() / d.R).median(), 3),
               median_abs_rel_shared=round((d.err_shared.abs() / d.R).median(), 3))
    for k, v in summ.items():
        print(k, v)
    print("ALL", tot)
    json.dump(dict(per_sensor=summ, all=tot), open(os.path.join(ROOT, "results", "holdout.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
