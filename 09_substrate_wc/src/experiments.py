"""Robustness experiments for Section 8 (all on the cached AGC data).

E1 sensitivity: rolling window W in {7, 14, 28} days and drain-onset collapse threshold in {0.2, 0.3, 0.4}
   -> median over compartments of the second-half paired-sensor gap, and control-replay mismatch.
E2 per-day paired comparison: daily median |WC1 - WC2| raw vs rolling anchor; share of second-half days on
   which the anchor is lower, sign-test z, per compartment and pooled.
E3 plateau coverage and stability: share of irrigated days with a detected drain onset; day-to-day
   standard deviation of the plateau per sensor.
E4 processing time per sensor-day (plateau detection + rolling anchor + correction).
E5 whole season: same gap metric over all days after the first W days (no split).
Output: results/experiments.json
"""
import json, os, time
import numpy as np
import pandas as pd
import agc
from offset_anchor import daily_plateau
import rolling_anchor as RA

ROOT = os.path.join(os.path.dirname(__file__), "..")


def corrected(x, P, days, W, P_star, idx):
    ref = RA.rolling_ref(P, days, W=W).reindex(idx.normalize()).values
    return ref


def gap_and_mismatch(loaded, W, thr):
    plats, first = {}, []
    for t, x in loaded.items():
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        for s in (1, 2):
            P = daily_plateau(x, s, thr_frac=thr)
            plats[(t, s)] = P
            first.append(float(P[P.index < split].median()))
    P_star = float(np.median(first))
    S = P_star - 5
    gaps, mism = {}, []
    for t, x in loaded.items():
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        test = x[x.index >= split]
        e = {}
        for s in (1, 2):
            ref = RA.rolling_ref(plats[(t, s)], days, W=W).reindex(test.index.normalize()).values
            e[s] = test[f"WC_slab{s}"] - ref + P_star
            day = test[(test.index.hour >= 6) & (test.index.hour < 18)]
            raw = day[f"WC_slab{s}"]
            cor = e[s][day.index]
            ok = raw.notna() & np.isfinite(cor)
            mism.append(float(((raw[ok] < S) != (cor[ok] < S)).mean()))
        gaps[t] = float((e[1] - e[2]).abs().median())
    return P_star, gaps, mism, plats


def sign_z(better, of):
    return (better - of / 2) / np.sqrt(of / 4) if of else 0.0


def main():
    loaded = {t: agc.load(t)[0] for t in agc.TEAMS}
    out = {}
    # E1
    grid = []
    for W in (7, 14, 28):
        for thr in (0.2, 0.3, 0.4):
            P_star, gaps, mism, _ = gap_and_mismatch(loaded, W, thr)
            grid.append(dict(W=W, thr=thr, P_star=round(P_star, 2),
                             gap_median=round(float(np.median(list(gaps.values()))), 2),
                             gap_max=round(float(max(gaps.values())), 2),
                             mismatch_median=round(float(np.median(mism)), 3)))
            print("E1", grid[-1])
    out["E1_sensitivity"] = grid
    # baseline raw gap for reference
    raw = {}
    for t, x in loaded.items():
        days = np.sort(x.index.normalize().unique())
        test = x[x.index >= days[len(days) // 2]]
        raw[t] = float((test.WC_slab1 - test.WC_slab2).abs().median())
    out["E1_raw_gap_median"] = round(float(np.median(list(raw.values()))), 2)

    # E2 + E3 + E5 with the default constants
    P_star, gaps, mism, plats = gap_and_mismatch(loaded, RA.W, 0.3)
    e2, pooled_b, pooled_n, e3, e5 = {}, 0, 0, {}, {}
    for t, x in loaded.items():
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        e = {}
        for s in (1, 2):
            ref = RA.rolling_ref(plats[(t, s)], days).reindex(x.index.normalize()).values
            e[s] = x[f"WC_slab{s}"] - ref + P_star
        g_raw = (x.WC_slab1 - x.WC_slab2).abs().groupby(x.index.normalize()).median()
        g_cor = (e[1] - e[2]).abs().groupby(x.index.normalize()).median()
        d = pd.concat([g_raw, g_cor], axis=1, keys=["raw", "cor"]).dropna()
        dt = d[d.index >= split]
        b, n = int((dt.cor < dt.raw).sum()), int((dt.cor != dt.raw).sum())
        pooled_b += b; pooled_n += n
        e2[t] = dict(days=len(dt), anchor_lower=b, of=n, z=round(float(sign_z(b, n)), 2))
        irrigated = x.irr.groupby(x.index.normalize()).sum()
        n_irr = int((irrigated > 0.5).sum())
        e3[t] = {s: dict(plateau_days=int(len(plats[(t, s)])), irrigated_days=n_irr,
                         coverage=round(len(plats[(t, s)]) / n_irr, 3),
                         day_to_day_sd=round(float(plats[(t, s)].diff().std()), 2)) for s in (1, 2)}
        whole = d[d.index >= days[0] + pd.Timedelta(days=RA.W)]
        e5[t] = dict(raw=round(float(whole.raw.median()), 2), anchor=round(float(whole.cor.median()), 2))
    out["E2_daily_sign"] = dict(per_compartment=e2, pooled=dict(anchor_lower=pooled_b, of=pooled_n,
                                                                z=round(float(sign_z(pooled_b, pooled_n)), 2)))
    out["E3_coverage"] = {t: {str(s): v for s, v in r.items()} for t, r in e3.items()}
    out["E5_whole_season"] = e5
    print("E2", out["E2_daily_sign"]["pooled"])
    # E4 timing
    x = loaded["Reference"]
    days = np.sort(x.index.normalize().unique())
    t0 = time.perf_counter()
    for s in (1, 2):
        P = daily_plateau(x, s)
        ref = RA.rolling_ref(P, days).reindex(x.index.normalize()).values
        _ = x[f"WC_slab{s}"] - ref + P_star
    dt = time.perf_counter() - t0
    out["E4_timing"] = dict(sensor_days=2 * len(days), seconds=round(dt, 3),
                            ms_per_sensor_day=round(1000 * dt / (2 * len(days)), 2))
    print("E4", out["E4_timing"])
    json.dump(out, open(os.path.join(ROOT, "results", "experiments.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
