"""E10: the morning drain deficit against the litres the slab took before it drained.

Each morning the slab is refilled by pulses until it drains. The water dosed from the first pulse of the day
up to the first pulse after which the drain EC probe registers fresh drain (label of e8_drain_cup.py) is
what the slab took up to drainage: its overnight dry-back plus the crop's uptake over the refill, read from
the dose meter and the drain probe only, without any slab sensor and without the batching daily drain
meter. If the drain deficit of a sensor before the first pulse measures the water missing from the slab, it
must predict those litres; with a single scale k (litres per m2 per WC %) for all sensors of one slab type.

Per sensor-day of the held-out half (the anchors only use past days or the first half):
  V    litres per m2 dosed from the first pulse to the first drained pulse (both included)
  D    anchor - reading just before the first pulse, for three anchors: P* on the raw reading,
       a one-off commissioning anchor (first 14 onset days), the rolling anchor (past 14 days)
Reported: Spearman correlation of V with D pooled over all sensor-days (one scale for every slab) and per
sensor (offset-free within a sensor), and for each sensor the scale V / D (median over days with D >= 3 WC %),
the litre route to the gain; its ratio between the two sensors of a compartment is compared with the
relative gain of the rise route and the decline route (scale_offset.json).
Output: results/e10_litres_to_drain.json
"""
import json
import os
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import agc
import rolling_anchor as RA
from e8_drain_cup import drain_ec, STEP, LAG, COMM_DAYS
from offset_anchor import daily_plateau

ROOT = os.path.join(os.path.dirname(__file__), "..")
D_MIN = 3.0
N_BOOT = 2000
warnings.filterwarnings("ignore", category=RuntimeWarning)


def main():
    P_star = json.load(open(os.path.join(ROOT, "results", "rolling_anchor.json")))["P_star"]
    so = json.load(open(os.path.join(ROOT, "results", "scale_offset.json")))
    rows = []
    for team in agc.TEAMS:
        x, _ = agc.load(team)
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        e = drain_ec(team, x.index)
        ch = (e.diff().abs() >= STEP).astype(float)
        after = ch[::-1].rolling(LAG, min_periods=1).max()[::-1].shift(-1).fillna(0)
        pulses = x.index[x.irr.values > 0]
        pdays = pd.Series(pulses, index=pulses).groupby(pulses.normalize())
        anchors = {}
        for s in (1, 2):
            P = daily_plateau(x, s)
            anchors[s] = (float(P.iloc[:COMM_DAYS].median()), RA.rolling_ref(P, days))
        for day, ts in pdays:
            if day < split:
                continue
            ts = list(ts)
            hit = [t for t in ts[1:] if after.get(t, 0) > 0]
            if not hit:
                continue
            t0, t1 = ts[0], hit[0]
            V = float(x.irr[t0:t1].sum())
            for s in (1, 2):
                wc0 = x[f"WC_slab{s}"][:t0].iloc[-3:-1].median()     # reading just before the first pulse
                comm, ref = anchors[s]
                r = ref.get(day, np.nan)
                if not (np.isfinite(wc0) and np.isfinite(r)):
                    continue
                rows.append(dict(team=team, s=s, day=day, V=V, n_pulses=ts.index(t1) + 1,
                                 raw=P_star - wc0, comm=comm - wc0, roll=r - wc0))
    df = pd.DataFrame(rows)
    out = dict(n_sensor_days=len(df), D_min=D_MIN, V_median=round(float(df.V.median()), 3),
               V_iqr=[round(float(q), 3) for q in df.V.quantile([.25, .75])], pooled={}, per_sensor={},
               litre_gain={})
    for k in ("raw", "comm", "roll"):
        rho = spearmanr(df[k], df.V).correlation
        out["pooled"][k] = round(float(rho), 3)
    # bootstrap over days (all sensors of a resampled day move together)
    rng = np.random.default_rng(0)
    udays = np.array(list({d for d in df.day}), dtype=object)
    by_day = {d: g for d, g in df.groupby("day")}
    diff_raw, diff_comm = [], []
    for _ in range(N_BOOT):
        b = pd.concat([by_day[d] for d in rng.choice(udays, len(udays))])
        r = {k: spearmanr(b[k], b.V).correlation for k in ("raw", "comm", "roll")}
        diff_raw.append(r["roll"] - r["raw"])
        diff_comm.append(r["roll"] - r["comm"])
    out["boot_roll_minus_raw_ci95"] = [round(float(q), 3) for q in np.quantile(diff_raw, [.025, .975])]
    out["boot_roll_minus_comm_ci95"] = [round(float(q), 3) for q in np.quantile(diff_comm, [.025, .975])]
    out["n_days"] = len(udays)
    for (team, s), g in df.groupby(["team", "s"]):
        rho = spearmanr(g.roll, g.V).correlation
        gg = g[g.roll >= D_MIN]
        out["per_sensor"]["%s_%d" % (team, s)] = dict(
            days=len(g), spearman=round(float(rho), 3),
            litres_per_wc=round(float((gg.V / gg.roll).median()), 4) if len(gg) >= 5 else None,
            days_D_ge_min=len(gg))
    for team in agc.TEAMS:
        a, b = (out["per_sensor"].get("%s_%d" % (team, s), {}).get("litres_per_wc") for s in (1, 2))
        if a and b:
            # sensor gain is inversely proportional to litres per WC %; G = gain2 / gain1 as in scale_offset
            out["litre_gain"][team] = dict(G_litre=round(a / b, 3),
                                           G_rise=so[team]["G_first_half"],
                                           G_decline=so[team]["G_decl_first_half"])
    lg = out["litre_gain"].values()
    out["litre_gain_same_side_of_1_as_rise"] = sum((v["G_litre"] - 1) * (v["G_rise"] - 1) > 0 for v in lg)
    out["litre_gain_within_15pct_of_rise"] = sum(abs(v["G_litre"] / v["G_rise"] - 1) <= 0.15 for v in lg)
    out["litre_gain_compartments"] = len(out["litre_gain"])
    rs = [v["spearman"] for v in out["per_sensor"].values()]
    out["per_sensor_spearman_median"] = round(float(np.median(rs)), 3)
    out["per_sensor_spearman_range"] = [round(float(min(rs)), 3), round(float(max(rs)), 3)]
    for k, v in out.items():
        print(k, v)
    json.dump(out, open(os.path.join(ROOT, "results", "e10_litres_to_drain.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
