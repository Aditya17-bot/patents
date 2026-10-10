"""Step 2: offset anchor at drain onset.

A rockwool slab of one type drains when it reaches its drainage plateau, a fixed water content set by the
slab's pore structure. Each day the plateau shows on the sensor as the level where pulse rises collapse
(water passes through instead of being stored). Two sensors on the same slab type should read the same
plateau; a difference is sensor offset (+ scale). Calibrate on the first half of the season:
    corrected WC = P_ref + (WC - P_s) * (k_s / k_ref)
with P_s the sensor's median daily plateau and k_s its pulse scale (sensor 1 taken as reference).
Test on the second half: does the paired-sensor WC gap shrink?
"""
import json, os
import numpy as np
import pandas as pd
import agc
from pulse_gain import pulse_rises
from pair_agreement import k_pulse

ROOT = os.path.join(os.path.dirname(__file__), "..")


def daily_plateau(x, s, thr_frac=0.3):
    """Plateau of each day = median WC in the 30 min after the first pulse whose rise is < 30 % of
    that day's median pre-drain rise (i.e. the slab has started to drain)."""
    p = pulse_rises(x, s)
    p["day"] = p.t.dt.normalize()
    wc = x[f"WC_slab{s}"]
    out = {}
    for day, g in p.groupby("day"):
        g = g[g.vol > 0]
        if len(g) < 6:
            continue
        early = g.rise.iloc[:4]
        if early.median() < 0.5:
            continue
        thr = thr_frac * early.median()
        late = g.iloc[3:][g.rise.iloc[3:] < thr]
        if late.empty:
            continue
        t = late.t.iloc[0]
        out[day] = float(wc[t:t + pd.Timedelta("30min")].median())
    return pd.Series(out)


def main():
    res = {}
    for team in agc.TEAMS:
        x, _ = agc.load(team)
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        P1, P2 = daily_plateau(x, 1), daily_plateau(x, 2)
        k1, _ = k_pulse(x, 1, split)
        k2, _ = k_pulse(x, 2, split)
        p1, p2 = float(P1[P1.index < split].median()), float(P2[P2.index < split].median())
        test = x[x.index >= split]
        w1, w2 = test.WC_slab1, test.WC_slab2
        gap_raw = (w1 - w2).abs()
        w2_off = w2 - p2 + p1                                  # offset only
        w2_full = p1 + (w2 - p2) * (k2 / k1)                   # offset + scale
        gap_off = (w1 - w2_off).abs()
        gap_full = (w1 - w2_full).abs()
        pg = P1.to_frame("p1").join(P2.to_frame("p2"), how="inner")
        pg_test = pg[pg.index >= split]
        res[team] = dict(plateau1=round(p1, 1), plateau2=round(p2, 1), n_plateau_days=[len(P1), len(P2)],
                         plateau_gap_test_median=round(float((pg_test.p1 - pg_test.p2).median()), 2),
                         plateau_gap_test_iqr=[round(float(q), 2) for q in (pg_test.p1 - pg_test.p2).quantile([.25, .75])],
                         k2_over_k1=round(k2 / k1, 3),
                         wc_gap_raw_median=round(float(gap_raw.median()), 2),
                         wc_gap_offset_median=round(float(gap_off.median()), 2),
                         wc_gap_offset_scale_median=round(float(gap_full.median()), 2))
        print(team, res[team])
    json.dump(res, open(os.path.join(ROOT, "results", "offset_anchor.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
