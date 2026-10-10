"""Truth-free check: two slab sensors in one compartment see the same crop and the same pulses, so the
crop uptake each implies (litres per m2 per day = k * WC declines) should agree once each sensor is scaled
correctly. k per sensor from pre-drain pulses in the first half of the season (ratio of sums); agreement
tested on the second half. Baseline: one shared k for both (what an uncalibrated reading assumes).
"""
import json, os
import numpy as np
import pandas as pd
import agc
from pulse_gain import pulse_rises
from uptake_balance import daily_D

ROOT = os.path.join(os.path.dirname(__file__), "..")


def k_pulse(x, s, until):
    p = pulse_rises(x, s)
    p["day"] = p.t.dt.normalize()
    plat = x[f"WC_slab{s}"].groupby(x.index.normalize()).quantile(0.9)
    p["plat"] = p.day.map(plat)
    pre = p[(p.wc0 < p.plat - 3) & (p.rise > 0.3) & (p.vol > 0) & (p.day < until)]
    return float(pre.vol.sum() / pre.rise.sum()), len(pre)


def main():
    out = {}
    for team in agc.TEAMS:
        x, daily = agc.load(team)
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        k1, n1 = k_pulse(x, 1, split)
        k2, n2 = k_pulse(x, 2, split)
        d1, d2 = daily_D(x, 1), daily_D(x, 2)
        d = d1[["decl"]].join(d2[["decl"]], lsuffix="1", rsuffix="2", how="inner").dropna()
        d = d[(d.index >= split) & (d.decl1 > 1) & (d.decl2 > 1)]
        ks = (k1 + k2) / 2
        raw = (ks * d.decl1 - ks * d.decl2).abs() / (ks * (d.decl1 + d.decl2) / 2)
        cal = (k1 * d.decl1 - k2 * d.decl2).abs() / ((k1 * d.decl1 + k2 * d.decl2) / 2)
        out[team] = dict(k1=round(k1, 4), k2=round(k2, 4), n_pulses=[n1, n2], n_test_days=len(d),
                         pair_gap_shared_median=round(float(raw.median()), 3),
                         pair_gap_calibrated_median=round(float(cal.median()), 3),
                         decl_ratio_median=round(float((d.decl1 / d.decl2).median()), 3),
                         k_ratio_k2_over_k1=round(k2 / k1, 3))
        print(team, out[team])
    json.dump(out, open(os.path.join(ROOT, "results", "pair_agreement.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
