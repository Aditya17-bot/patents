"""E11: the drain-onset anchor against a field-capacity anchor of the kind described in US 8,862,277 /
US 8,751,052 (prior art P2), on the same data and the same tests.

P2 finds field capacity from the dynamic response after wetting: "When the soil is wetted above field
capacity, its moisture content will fall fairly quickly initially to a point where field capacity is
reached", then more slowly by evapotranspiration; in its adaptive mode the value is re-determined from
irrigation events with a time constant of about ten days. Implemented here, for each sensor and day, on the
fall after the last pulse of the day:
  r(t)   fall of the reading over the next 30 min, from each 5-min sample in the 4 h after the last pulse
  r0     largest r in the first hour; days with r0 < R0_MIN (no fast drainage fall) give no value
  FC     reading at the first sample after the r0 peak whose r is below FRAC x r0 (fast fall over)
and the anchor of each day is the median FC of the preceding 14 days (>= 3), exactly as the rolling
drain-onset anchor, so the only difference is the physical event that defines the daily value.
Tests on the held-out half, as for the drain-onset anchor:
  (1) reading at the first drained pulse of the day (drain EC probe, e8 label) less the anchor;
  (2) paired-sensor gap of the deficits (anchor - reading) in each compartment;
  (3) Spearman correlation, pooled over all sensor-days, of the deficit before the first pulse with the
      litres dosed until the first drained pulse (as e10_litres_to_drain.py), with a day bootstrap.
Output: results/e11_p2_anchor.json
"""
import json
import os
import warnings

import numpy as np
import pandas as pd

import agc
import rolling_anchor as RA
from e8_drain_cup import drain_ec, STEP, LAG

ROOT = os.path.join(os.path.dirname(__file__), "..")
R0_MIN = 0.5        # WC % per 30 min
FRAC = 0.3
warnings.filterwarnings("ignore", category=RuntimeWarning)


def p2_daily_fc(x, s):
    wc = x[f"WC_slab{s}"]
    pulses = x.index[x.irr.values > 0]
    last = pd.Series(pulses, index=pulses).groupby(pulses.normalize()).max()
    out = {}
    for day, t in last.items():
        w = wc[t:t + pd.Timedelta("4h30min")].values
        if len(w) < 54 or not np.isfinite(w).all():
            continue
        r = w[:-6] - w[6:]                       # fall over the next 30 min
        k0 = int(np.argmax(r[:12]))
        r0 = r[k0]
        if r0 < R0_MIN:
            continue
        below = np.flatnonzero(r[k0:] < FRAC * r0)
        if below.size == 0:
            continue
        out[day] = float(w[k0 + below[0]])
    return pd.Series(out)


def main():
    lev, gaps, cover, lit = {"p2": [], "onset": []}, {}, {}, []
    from offset_anchor import daily_plateau
    for team in agc.TEAMS:
        x, _ = agc.load(team)
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        e = drain_ec(team, x.index)
        ch = (e.diff().abs() >= STEP).astype(float)
        after = ch[::-1].rolling(LAG, min_periods=1).max()[::-1].shift(-1).fillna(0)
        pulses = x.index[x.irr.values > 0]
        pdays = pd.Series(pulses, index=pulses).groupby(pulses.normalize())
        refs = {}
        for s in (1, 2):
            fc = p2_daily_fc(x, s)
            P = daily_plateau(x, s)
            irr_days = len(pdays)
            cover["%s_%d" % (team, s)] = dict(p2_days=len(fc), onset_days=len(P), irrigated_days=irr_days)
            refs[s] = {"p2": RA.rolling_ref(fc, days), "onset": RA.rolling_ref(P, days)}
        for day, ts in pdays:
            if day < split:
                continue
            ts = list(ts)
            hit = [t for t in ts[1:] if after.get(t, 0) > 0]
            if not hit:
                continue
            t = hit[0]
            V = float(x.irr[ts[0]:t].sum())
            for s in (1, 2):
                wc0 = x[f"WC_slab{s}"][:ts[0]].iloc[-3:-1].median()
                rp, ro = refs[s]["p2"].get(day, np.nan), refs[s]["onset"].get(day, np.nan)
                if np.isfinite(wc0) and np.isfinite(rp) and np.isfinite(ro):
                    lit.append(dict(day=day, V=V, p2=rp - wc0, onset=ro - wc0))
            for s in (1, 2):
                cup = float(x[f"WC_slab{s}"][t:t + pd.Timedelta("30min")].median())
                for k in ("p2", "onset"):
                    r = refs[s][k].get(day, np.nan)
                    if np.isfinite(cup) and np.isfinite(r):
                        lev[k].append(dict(team=team, s=s, d=cup - r))
        g = {}
        sec = x[x.index.normalize() >= split]
        dn = sec.index.normalize()
        for k in ("p2", "onset"):
            d1 = refs[1][k].reindex(dn).values - sec.WC_slab1.values
            d2 = refs[2][k].reindex(dn).values - sec.WC_slab2.values
            gap = np.abs(d1 - d2)
            g[k] = round(float(np.nanmedian(gap)), 2)
        gaps[team] = g
    out = dict(R0_MIN=R0_MIN, FRAC=FRAC, coverage=cover, pair_gap=gaps, level={})
    for k, rows in lev.items():
        df = pd.DataFrame(rows)
        per = df.groupby(["team", "s"]).d.median()
        out["level"][k] = dict(n=len(df), pooled_median_abs=round(float(df.d.abs().median()), 2),
                               sensors_within_1=int((per.abs() <= 1).sum()), sensors=len(per),
                               per_sensor={"%s_%d" % i: round(float(v), 2) for i, v in per.items()})
    from scipy.stats import spearmanr
    L = pd.DataFrame(lit)
    out["litres_spearman"] = {k: round(float(spearmanr(L[k], L.V).correlation), 3) for k in ("p2", "onset")}
    rng = np.random.default_rng(0)
    by = {d: g for d, g in L.groupby("day")}
    keys = list(by)
    diff = []
    for _ in range(2000):
        b = pd.concat([by[keys[i]] for i in rng.integers(0, len(keys), len(keys))])
        diff.append(spearmanr(b.onset, b.V).correlation - spearmanr(b.p2, b.V).correlation)
    out["litres_onset_minus_p2_ci95"] = [round(float(q), 3) for q in np.quantile(diff, [.025, .975])]
    out["litres_n"] = len(L)
    out["pair_gap_median"] = {k: round(float(np.median([gaps[t][k] for t in gaps])), 2) for k in ("p2", "onset")}
    out["p2_days_share_median"] = round(float(np.median([c["p2_days"] / c["irrigated_days"] for c in cover.values()])), 3)
    out["onset_days_share_median"] = round(float(np.median([c["onset_days"] / c["irrigated_days"] for c in cover.values()])), 3)
    for k, v in out.items():
        print(k, v)
    json.dump(out, open(os.path.join(ROOT, "results", "e11_p2_anchor.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
