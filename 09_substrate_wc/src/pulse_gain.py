"""Sensor scale from metered water, per slab sensor.

k is litres per m2 of floor per 1 % WC reading. A correctly scaled sensor on a given slab type has one k
(slab volume per m2 / 100). Two estimates per sensor:
  k_pulse: pulse volume / WC rise, for pulses given while the slab is below its drain plateau
  k_day:   (metered irrigation - metered drain) / sum of the day's WC rises
Paired sensors in one compartment sit on the same slab type, so k1/k2 is their relative scale error.
"""
import json, os
import numpy as np
import pandas as pd
import agc

ROOT = os.path.join(os.path.dirname(__file__), "..")


def pulse_rises(x, s):
    wc = x[f"WC_slab{s}"]
    out = []
    idx = np.flatnonzero(x.irr.values > 0)
    for i in idx:
        if i < 2 or i + 3 >= len(x):
            continue
        before = wc.iloc[i - 1]
        after = wc.iloc[i:i + 3].max()
        if not (np.isfinite(before) and np.isfinite(after)):
            continue
        out.append((x.index[i], x.irr.iloc[i], before, after - before))
    return pd.DataFrame(out, columns=["t", "vol", "wc0", "rise"])


def analyse(team):
    x, daily = agc.load(team)
    res = {}
    for s in (1, 2):
        p = pulse_rises(x, s)
        p["day"] = p.t.dt.normalize()
        # drain plateau of the day = 90th pct of WC that day; pre-drain pulses start >= 3 % below it
        plat = x[f"WC_slab{s}"].groupby(x.index.normalize()).quantile(0.9)
        p["plat"] = p.day.map(plat)
        pre = p[(p.wc0 < p.plat - 3) & (p.rise > 0.3) & (p.vol > 0)]
        k_pulse = (pre.vol / pre.rise)
        # daily
        rises = p[p.rise > 0].groupby("day").rise.sum()
        dd = daily.join(rises.rename("rises"), how="inner")
        dd = dd[(dd.rises > 2) & (dd.Irr > 0.5)]
        k_day = (dd.Irr - dd.Drain) / dd.rises
        res[s] = dict(n_pre_pulses=int(len(pre)), k_pulse_median=round(float(k_pulse.median()), 4),
                      k_pulse_iqr=[round(float(q), 4) for q in k_pulse.quantile([.25, .75])],
                      n_days=int(len(dd)), k_day_median=round(float(k_day.median()), 4),
                      k_day_iqr=[round(float(q), 4) for q in k_day.quantile([.25, .75])],
                      wc_median=round(float(x[f"WC_slab{s}"].median()), 1))
    for k in ("k_pulse_median", "k_day_median"):
        res["ratio_" + k] = round(res[1][k] / res[2][k], 3)
    res["wc_median_diff"] = round(res[1]["wc_median"] - res[2]["wc_median"], 1)
    return res


def main():
    out = {t: analyse(t) for t in agc.TEAMS}
    for t, r in out.items():
        print(f"{t:14s} WC1-WC2 {r['wc_median_diff']:+5.1f} | k_pulse {r[1]['k_pulse_median']:.3f}/{r[2]['k_pulse_median']:.3f}"
              f" (n {r[1]['n_pre_pulses']}/{r[2]['n_pre_pulses']}) ratio {r['ratio_k_pulse_median']}"
              f" | k_day {r[1]['k_day_median']:.3f}/{r[2]['k_day_median']:.3f} ratio {r['ratio_k_day_median']}")
    json.dump(out, open(os.path.join(ROOT, "results", "pulse_gain.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
