"""Next-step 2: gain-free dripper-delivery ratio per slab.

For a slab sensor with unknown gain g, slab water volume V, dripper delivery share f (litres reaching this
slab per litre of compartment dose) and plant demand share u:
    rise per litre dosed (pre-drain)  a = g * f / V
    WC decline per day (uptake)       b = g * u * U / V      (U = compartment uptake per m2)
    rho = a / b = f / (u * U)                                 -> g and V cancel
Within one compartment U is common, so rho1 / rho2 = (f1/u1) / (f2/u2): the relative water delivered per
unit demand of the two slabs, free of sensor gain. 1 = both slabs receive water in proportion to demand.
Reported per week; stability and step changes are of interest (dripper clogging / emitter wear).
"""
import json, os
import numpy as np
import pandas as pd
import agc
from pulse_gain import pulse_rises
from uptake_balance import daily_D

ROOT = os.path.join(os.path.dirname(__file__), "..")


def weekly_a(x, s):
    p = pulse_rises(x, s)
    p["day"] = p.t.dt.normalize()
    plat = x[f"WC_slab{s}"].groupby(x.index.normalize()).quantile(0.9)
    p["plat"] = p.day.map(plat)
    pre = p[(p.wc0 < p.plat - 3) & (p.rise > 0.3) & (p.vol > 0)].set_index("day")
    w = pre[["vol", "rise"]].resample("W-MON").sum()
    return (w.rise / w.vol)[w.vol > 0.5]


def weekly_b(x, s):
    y = x.copy()
    y[f"WC_slab{s}"] = x[f"WC_slab{s}"].rolling(3, center=True, min_periods=1).median()
    d = daily_D(y, s)
    return d.decl.resample("W-MON").mean()


def main():
    res = {}
    for team in agc.TEAMS:
        x, _ = agc.load(team)
        rho = {}
        for s in (1, 2):
            rho[s] = weekly_a(x, s) / weekly_b(x, s)
        r = (rho[1] / rho[2]).dropna()
        r = r[np.isfinite(r)]
        g_a = (weekly_a(x, 1) / weekly_a(x, 2)).dropna()
        g_b = (weekly_b(x, 1) / weekly_b(x, 2)).dropna()
        res[team] = dict(weeks=len(r), rho_ratio_median=round(float(r.median()), 3),
                         rho_ratio_iqr=[round(float(q), 3) for q in r.quantile([.25, .75])],
                         rise_ratio_median=round(float(g_a.median()), 3),
                         decline_ratio_median=round(float(g_b.median()), 3),
                         rho_ratio_first4=round(float(r.iloc[:4].median()), 3),
                         rho_ratio_last4=round(float(r.iloc[-4:].median()), 3),
                         weekly=[round(float(v), 3) for v in r.values])
        print(team, {k: v for k, v in res[team].items() if k != "weekly"})
    json.dump(res, open(os.path.join(ROOT, "results", "dripper_ratio.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
