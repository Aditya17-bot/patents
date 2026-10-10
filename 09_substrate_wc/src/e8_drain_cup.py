"""E8: test against an instrument that is not a slab sensor — the drain-cup EC probe of the process computer.

The drain EC (EC_drain_PC, 5 min) only changes when fresh drain water reaches the cup. A pulse is labelled
"drained" when the drain EC moves by >= 0.15 dS/m within 15 min after it. Checks of the label:
  - rate after pulses on days with metered drain = 0, and in quiet periods (no pulse 30 min before / 60 min
    after): should be near zero.
Tests on the second half of the season (labels never used to fit anything):
  (1) Onset agreement: per sensor-day, reading at the first drained pulse (drain cup) vs the plateau found
      from the collapse of the slab sensor's own pulse rise. Is the anchor the physical drain?
      Also the clock time of the two onsets.
  (2) Level at physical drain: reading at the first drained pulse of each sensor-day (drain cup), less
      (a) the common constant P* (raw reading), (b) a one-off commissioning anchor (first 14 onset days,
      P1-style), (c) the rolling anchor from the past 14 days only. If the corrected reading means the
      same physical state on every slab, (c) is near zero for all 12 sensors. Pooled median |error|.
  (3) Reported, not used: AUC of the pre-pulse reading/deficit for "this pulse drains" (one threshold, all
      sensors). The pre-pulse level alone separates drained pulses weakly for every variant.
Output: results/e8_drain_cup.json
"""
import json, os
import numpy as np
import pandas as pd
import agc
from pulse_gain import pulse_rises
from offset_anchor import daily_plateau
import rolling_anchor as RA

ROOT = os.path.join(os.path.dirname(__file__), "..")
STEP = 0.15         # dS/m change of drain EC that marks fresh drain in the cup
LAG = 3             # samples after the pulse (15 min)
COMM_DAYS = 14


def drain_ec(team, index):
    c = pd.read_csv(os.path.join(agc.DATA, team, "GreenhouseClimate.csv"), low_memory=False,
                    usecols=["%time", "EC_drain_PC"])
    c = agc._num(c)
    c["t"] = agc._time(c.pop("%time"))
    c = c.set_index("t")
    return c[~c.index.duplicated()].EC_drain_PC.reindex(index)


def collapse_onsets(x, s, thr_frac=0.3):
    """Clock time of the drain onset found by the rule of offset_anchor.daily_plateau."""
    p = pulse_rises(x, s)
    p["day"] = p.t.dt.normalize()
    out = {}
    for day, g in p.groupby("day"):
        g = g[g.vol > 0]
        if len(g) < 6 or g.rise.iloc[:4].median() < 0.5:
            continue
        late = g.iloc[3:][g.rise.iloc[3:] < thr_frac * g.rise.iloc[:4].median()]
        if not late.empty:
            out[day] = late.t.iloc[0]
    return pd.Series(out)


def auc(pos, neg):
    """P(score of a positive > score of a negative), ties half."""
    s = np.concatenate([pos, neg])
    r = pd.Series(s).rank().values
    n1, n0 = len(pos), len(neg)
    return float((r[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def main():
    P_star = json.load(open(os.path.join(ROOT, "results", "rolling_anchor.json")))["P_star"]
    rows, lev, label_check, onset = [], [], {}, {}
    for team in agc.TEAMS:
        x, daily = agc.load(team)
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        e = drain_ec(team, x.index)
        ch = (e.diff().abs() >= STEP).astype(float)
        after = ch[::-1].rolling(LAG, min_periods=1).max()[::-1].shift(-1).fillna(0)
        pulse = x.irr > 0
        quiet = (x.irr[::-1].rolling(12, min_periods=1).max()[::-1] == 0) & (x.irr.rolling(6, min_periods=1).max() == 0)
        dr = daily.Drain.reindex(x.index.normalize()).values
        label_check[team] = dict(after_pulse=round(float(after[pulse].mean()), 3),
                                 after_pulse_metered_drain_zero=round(float(after[pulse & (dr == 0)].mean()), 3),
                                 quiet=round(float(after[quiet].mean()), 4),
                                 pulses_metered_drain_zero=int((pulse & (dr == 0)).sum()))
        onset[team] = {}
        for s in (1, 2):
            wc = x[f"WC_slab{s}"]
            P = daily_plateau(x, s)
            T = collapse_onsets(x, s)
            comm = float(P.iloc[:COMM_DAYS].median())
            ref = RA.rolling_ref(P, days)
            p = pulse_rises(x, s)
            p = p[p.vol > 0]
            p["day"] = p.t.dt.normalize()
            p["drained"] = after.reindex(p.t).values > 0
            p = p[(p.day >= split) & np.isfinite(p.wc0)]
            p["ref"] = ref.reindex(p.day).values
            p = p[np.isfinite(p.ref)]
            d, dt = [], []
            for day, g in p.groupby("day"):
                hit = g.iloc[1:][g.iloc[1:].drained]        # first drained pulse after the day's first pulse
                if hit.empty:
                    continue
                t = hit.t.iloc[0]
                cup = float(wc[t:t + pd.Timedelta("30min")].median())
                if not np.isfinite(cup):
                    continue
                lev.append(dict(team=team, s=s, raw=cup - P_star, comm=cup - comm, roll=cup - g.ref.iloc[0]))
                if day in P.index:
                    d.append(cup - P[day])
                    dt.append((t - T[day]).total_seconds() / 60)
            d, dt = np.array(d), np.array(dt)
            onset[team][s] = dict(n_days=len(d), median_diff=round(float(np.median(d)), 2),
                                  median_abs_diff=round(float(np.median(np.abs(d))), 2),
                                  time_cup_minus_collapse_min_median=round(float(np.median(dt)), 0),
                                  time_abs_le_60min=round(float((np.abs(dt) <= 60).mean()), 2))
            for r in p.itertuples():
                rows.append(dict(team=team, s=s, drained=r.drained, raw=r.wc0,
                                 deficit_comm=comm - r.wc0, deficit_roll=r.ref - r.wc0))
    lev = pd.DataFrame(lev)
    level = {}
    for k in ("raw", "comm", "roll"):
        per = lev.groupby(["team", "s"])[k].median()
        level[k] = dict(pooled_median_abs=round(float(lev[k].abs().median()), 2),
                        pooled_p90_abs=round(float(lev[k].abs().quantile(0.9)), 2),
                        sensor_medians_range=[round(float(per.min()), 2), round(float(per.max()), 2)],
                        sensors_within_1=int((per.abs() <= 1).sum()),
                        per_sensor={"%s_%d" % i: round(float(v), 2) for i, v in per.items()})
    df = pd.DataFrame(rows)
    pos, neg = df[df.drained], df[~df.drained]
    pooled_auc = dict(raw=auc(pos.raw.values, neg.raw.values),
                      commissioning=auc(-pos.deficit_comm.values, -neg.deficit_comm.values),
                      rolling=auc(-pos.deficit_roll.values, -neg.deficit_roll.values))
    oab = [v["median_abs_diff"] for t in onset.values() for v in t.values() if v["n_days"] >= 10]
    tab = [v["time_abs_le_60min"] for t in onset.values() for v in t.values() if v["n_days"] >= 10]
    out = dict(step_dS_m=STEP, lag_min=5 * LAG, P_star=P_star, label_check=label_check,
               onset_cup_vs_collapse=onset,
               onset_median_abs_diff_over_sensors=round(float(np.median(oab)), 2),
               onset_time_within_60min_median_share=round(float(np.median(tab)), 2),
               level_at_cup_onset_n=len(lev), level_at_cup_onset=level,
               n_pulses=len(df), n_drained=int(df.drained.sum()),
               pre_pulse_auc_not_used={k: round(v, 3) for k, v in pooled_auc.items()})
    for k, v in out.items():
        print(k, v)
    json.dump(out, open(os.path.join(ROOT, "results", "e8_drain_cup.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
