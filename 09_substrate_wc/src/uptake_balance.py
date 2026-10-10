"""Step 1: daily slab water balance with uptake taken from the sensor's own declines.

Water balance per m2 of floor over one day (midnight to midnight):
    Irr - Drain = U + dS
U (crop uptake) shows on the sensor as the WC fall between pulses and overnight; dS is the WC change
over the day. Both are k x (WC %), so  Irr - Drain = k * (sum of WC declines + WC_end - WC_start).
The right-hand bracket is "D" (WC % per day). If the sensor reads in proportion to slab water, D tracks the
metered retained water and the slope is the sensor scale k.
Declines are taken as falls between consecutive 5-min samples outside pulses and their 15-min aftermath;
single-sample spikes (> 2 % in 5 min with recovery) are removed first.
"""
import json, os
import numpy as np
import pandas as pd
import agc

ROOT = os.path.join(os.path.dirname(__file__), "..")


def despike(wc, jump=2.0):
    w = wc.copy()
    d1, d2 = w.diff(), w.diff(-1)
    spike = (d1.abs() > jump) & (d2.abs() > jump) & (np.sign(d1) == np.sign(d2))
    w[spike] = np.nan
    return w.interpolate(limit=2)


def daily_D(x, s):
    wc = despike(x[f"WC_slab{s}"])
    pulse = x.irr > 0
    # mask pulses and the 3 samples after them (wetting and drainage response)
    near = pulse.copy()
    for k in range(1, 4):
        near |= pulse.shift(k, fill_value=False)
    dw = wc.diff()
    decl = (-dw).where((~near) & (dw < 0), 0.0)
    day = x.index.normalize()
    g = pd.DataFrame({"decl": decl, "wc": wc, "day": day})
    out = g.groupby("day").agg(decl=("decl", "sum"), wc0=("wc", "first"), wc1=("wc", "last"),
                               n=("wc", lambda v: v.notna().sum()))
    out["D"] = out.decl + (out.wc1 - out.wc0)
    return out[out.n > 250]          # >= ~21 h of sensor data


def fit_k(D, R):
    return float((D * R).sum() / (D * D).sum())


def main():
    res, rows = {}, []
    for team in agc.TEAMS:
        x, daily = agc.load(team)
        for s in (1, 2):
            d = daily_D(x, s).join(daily, how="inner").dropna()
            d = d[(d.Irr > 0.5) & (d.D > 0)]
            d["R"] = d.Irr - d.Drain
            r = float(np.corrcoef(d.D, d.R)[0, 1])
            k = fit_k(d.D, d.R)
            half = d.index[len(d) // 2]
            k1 = fit_k(d.D[d.index < half], d.R[d.index < half])
            k2 = fit_k(d.D[d.index >= half], d.R[d.index >= half])
            res[f"{team}_{s}"] = dict(n_days=len(d), corr_D_R=round(r, 3), k=round(k, 4),
                                      k_half1=round(k1, 4), k_half2=round(k2, 4),
                                      mae_fit=round(float((k * d.D - d.R).abs().mean()), 3),
                                      R_mean=round(float(d.R.mean()), 3))
            for day, v in d.iterrows():
                rows.append(dict(team=team, s=s, day=str(day.date()), D=v.D, R=v.R))
            print(team, s, res[f"{team}_{s}"])
    json.dump(res, open(os.path.join(ROOT, "results", "uptake_balance.json"), "w"), indent=1)
    pd.DataFrame(rows).to_csv(os.path.join(ROOT, "results", "uptake_balance_days.csv"), index=False)


if __name__ == "__main__":
    main()
