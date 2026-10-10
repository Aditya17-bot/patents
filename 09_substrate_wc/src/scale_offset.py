"""Scale + rolling offset together.

Relative gain of the pair from pre-drain rise per litre (first half only): G = a2 / a1, so sensor 2's
WC excursions are G times sensor 1's for the same water change. Correction for sensor 2 about its own
rolling plateau:  WC2* = P* + (WC2 - P2(d)) / G.  Sensor 1: WC1* = P* + (WC1 - P1(d)).
Compared with offset-only (rolling anchor). Gated variant: G is applied only when the rise route and the
decline route (G_decl = b2 / b1, first half) agree within 10 %; otherwise offset only. Metric: second-half median |WC1* - WC2*| and the same for
the daily WC decline (uptake proxy, smoothed): |decl1 - decl2/G| / mean.
"""
import json, os
import numpy as np
import pandas as pd
import agc
from offset_anchor import daily_plateau
from rolling_anchor import rolling_ref
from dripper_ratio import weekly_a, weekly_b

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    res = {}
    for team in agc.TEAMS:
        x, _ = agc.load(team)
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        a1, a2 = weekly_a(x, 1), weekly_a(x, 2)
        G = float((a2[a2.index < split] / a1[a1.index < split]).median())
        b1h, b2h = weekly_b(x, 1), weekly_b(x, 2)
        G_decl = float((b2h[b2h.index < split] / b1h[b1h.index < split]).median())
        agree = abs(G - G_decl) / G <= 0.10
        Gg = G if agree else 1.0          # gated: scale only when both physical routes agree
        test = x[x.index >= split]
        day = test.index.normalize()
        P1 = rolling_ref(daily_plateau(x, 1), days).reindex(day).values
        P2 = rolling_ref(daily_plateau(x, 2), days).reindex(day).values
        e1 = test.WC_slab1 - P1
        e2 = test.WC_slab2 - P2
        gap_off = (e1 - e2).abs()
        gap_full = (e1 - e2 / G).abs()
        gap_gated = (e1 - e2 / Gg).abs()
        b1, b2 = weekly_b(x, 1), weekly_b(x, 2)
        bt = pd.concat([b1, b2], axis=1, keys=["b1", "b2"]).dropna()
        bt = bt[bt.index >= split]
        u_off = ((bt.b1 - bt.b2).abs() / ((bt.b1 + bt.b2) / 2)).median()
        u_full = ((bt.b1 - bt.b2 / G).abs() / ((bt.b1 + bt.b2 / G) / 2)).median()
        u_gated = ((bt.b1 - bt.b2 / Gg).abs() / ((bt.b1 + bt.b2 / Gg) / 2)).median()
        res[team] = dict(G_first_half=round(G, 3), G_decl_first_half=round(G_decl, 3), routes_agree=bool(agree),
                         wc_gap_gated=round(float(gap_gated.median()), 2), uptake_gap_gated=round(float(u_gated), 3),
                         wc_gap_raw=round(float((test.WC_slab1 - test.WC_slab2).abs().median()), 2),
                         wc_gap_offset=round(float(gap_off.median()), 2),
                         wc_gap_offset_scale=round(float(gap_full.median()), 2),
                         uptake_gap_offset=round(float(u_off), 3),
                         uptake_gap_offset_scale=round(float(u_full), 3))
        print(team, res[team])
    med = {k: round(float(np.median([v[k] for v in res.values()])), 3)
           for k in ("wc_gap_raw", "wc_gap_offset", "wc_gap_offset_scale", "wc_gap_gated",
                     "uptake_gap_offset", "uptake_gap_offset_scale", "uptake_gap_gated")}
    res["median_over_compartments"] = med
    print(med)
    json.dump(res, open(os.path.join(ROOT, "results", "scale_offset.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
