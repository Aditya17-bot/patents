"""Scale matters for dry-back, not for the plateau level.

Daily dry-back = (day's drain-onset plateau) - (minimum WC before the first pulse next morning), in WC %.
It is the main steering variable in rockwool irrigation (how far the slab is allowed to dry overnight).
Paired sensors see the same crop and pulses, so their true dry-backs should match; raw readings differ by
the sensors' gain ratio. Rolling relative gain over the past 28 days by two routes:
    G_rise = a2/a1 (pre-drain rise per litre),  G_decl = b2/b1 (daily WC decline)
applied as dryback2 / G only when the two routes agree within 10 %, else no scale.
Metric: second-half median |dryback1 - dryback2*| / mean dry-back.
"""
import json, os
import numpy as np
import pandas as pd
import agc
from offset_anchor import daily_plateau
from dripper_ratio import weekly_a, weekly_b

ROOT = os.path.join(os.path.dirname(__file__), "..")
WIN = pd.Timedelta(days=28)


def daily_dryback(x, s):
    wc = x[f"WC_slab{s}"].rolling(3, center=True, min_periods=1).median()
    P = daily_plateau(x, s)
    first_pulse = x.irr[x.irr > 0].groupby(x.irr[x.irr > 0].index.normalize()).apply(lambda v: v.index[0])
    out = {}
    for day, p in P.items():
        nxt = day + pd.Timedelta(days=1)
        if nxt not in first_pulse.index:
            continue
        seg = wc[day + pd.Timedelta("16h"):first_pulse[nxt]]
        if len(seg) > 24:
            out[day] = p - float(seg.min())
    return pd.Series(out)


def rolling_gain(num, den, days):
    r = (num / den).dropna()
    g = {}
    for d in days:
        w = r[(r.index >= d - WIN) & (r.index < d)]
        g[d] = float(w.median()) if len(w) >= 3 else np.nan
    return pd.Series(g)


def main():
    res = {}
    for team in agc.TEAMS:
        x, _ = agc.load(team)
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        d1, d2 = daily_dryback(x, 1), daily_dryback(x, 2)
        db = pd.concat([d1, d2], axis=1, keys=["d1", "d2"]).dropna()
        db = db[(db.index >= split) & (db.d1 > 1) & (db.d2 > 1)]
        Gr = rolling_gain(weekly_a(x, 2), weekly_a(x, 1), db.index)
        Gd = rolling_gain(weekly_b(x, 2), weekly_b(x, 1), db.index)
        agree = ((Gr - Gd).abs() / Gr <= 0.10)
        G = Gr.where(agree, 1.0).fillna(1.0)
        G_ung = Gr.fillna(1.0)
        m = (db.d1 + db.d2) / 2
        raw = ((db.d1 - db.d2).abs() / m).median()
        gated = ((db.d1 - db.d2 / G).abs() / ((db.d1 + db.d2 / G) / 2)).median()
        ungated = ((db.d1 - db.d2 / G_ung).abs() / ((db.d1 + db.d2 / G_ung) / 2)).median()
        res[team] = dict(n_days=len(db), dryback1_median=round(float(db.d1.median()), 2),
                         dryback2_median=round(float(db.d2.median()), 2),
                         share_days_routes_agree=round(float(agree.mean()), 2),
                         gap_raw=round(float(raw), 3), gap_scale_ungated=round(float(ungated), 3),
                         gap_scale_gated=round(float(gated), 3))
        print(team, res[team])
    med = {k: round(float(np.median([v[k] for v in res.values()])), 3)
           for k in ("gap_raw", "gap_scale_ungated", "gap_scale_gated")}
    res["median_over_compartments"] = med
    print(med)
    json.dump(res, open(os.path.join(ROOT, "results", "dryback.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
