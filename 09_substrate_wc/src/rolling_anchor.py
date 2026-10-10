"""Next-step 1: rolling (causal) offset re-anchoring vs a fixed first-half anchor.

Each sensor's reference plateau on day d = median of its daily drain-onset plateaus in days [d-W, d-1]
(past only, so it can run live). Every sensor is mapped to one common slab-type plateau P*:
    corrected WC_s(t) = WC_s(t) - P_s(d) + P*
P* = median of all sensors' first-half plateaus (one constant for the slab type). Metric: paired-sensor
gap |WC1 - WC2| in the second half for raw / fixed anchor / rolling anchor. The pair gap does not depend
on P*; P* only sets the absolute level.
"""
import json, os
import numpy as np
import pandas as pd
import agc
from offset_anchor import daily_plateau

ROOT = os.path.join(os.path.dirname(__file__), "..")
W = 14          # days in the rolling window
MIN_DAYS = 3    # plateau days needed in the window, else keep the last anchor


def rolling_ref(P, days, W=W):
    ref, last = {}, np.nan
    for d in days:
        win = P[(P.index >= d - pd.Timedelta(days=W)) & (P.index < d)]
        if len(win) >= MIN_DAYS:
            last = float(win.median())
        ref[d] = last
    return pd.Series(ref)


def main():
    loaded = {t: agc.load(t)[0] for t in agc.TEAMS}
    plats, first = {}, []
    for t, x in loaded.items():
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        for s in (1, 2):
            P = daily_plateau(x, s)
            plats[(t, s)] = P
            first.append(float(P[P.index < split].median()))
    p_star = float(np.median(first))
    res = dict(P_star=round(p_star, 2), window_days=W, teams={})
    for t, x in loaded.items():
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        test = x[x.index >= split]
        day = test.index.normalize()
        corr = {}
        for s in (1, 2):
            P = plats[(t, s)]
            fixed = float(P[P.index < split].median())
            roll = rolling_ref(P, days)
            corr[(s, "fixed")] = test[f"WC_slab{s}"] - fixed + p_star
            corr[(s, "roll")] = test[f"WC_slab{s}"] - roll.reindex(day).values + p_star
        gaps = dict(raw=(test.WC_slab1 - test.WC_slab2).abs(),
                    fixed=(corr[(1, "fixed")] - corr[(2, "fixed")]).abs(),
                    rolling=(corr[(1, "roll")] - corr[(2, "roll")]).abs())
        r = {k: round(float(v.median()), 2) for k, v in gaps.items()}
        r.update({k + "_p90": round(float(v.quantile(0.9)), 2) for k, v in gaps.items()})
        # how far each corrected sensor sits from P* at drain onset in the test half (absolute level)
        for s in (1, 2):
            P = plats[(t, s)]
            Pt = P[P.index >= split]
            rr = rolling_ref(P, days).reindex(Pt.index)
            r[f"onset_err_raw_{s}"] = round(float((Pt - p_star).abs().median()), 2)
            r[f"onset_err_roll_{s}"] = round(float((Pt - rr + p_star - p_star).abs().median()), 2)
        res["teams"][t] = r
        print(t, r)
    allg = {k: np.median([v[k] for v in res["teams"].values()]) for k in ("raw", "fixed", "rolling")}
    res["median_over_compartments"] = {k: round(float(v), 2) for k, v in allg.items()}
    print("P*", round(p_star, 2), "median over compartments", res["median_over_compartments"])
    json.dump(res, open(os.path.join(ROOT, "results", "rolling_anchor.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
