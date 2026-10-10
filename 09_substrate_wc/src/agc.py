"""Loader for the Autonomous Greenhouse Challenge, 2nd edition (WUR, 2019-20; Kaggle mirror piantic/...).

One frame per compartment at 5-min steps: irrigation pulses (L/m2), two Grodan GroSens slab sensors
(WC %, EC dS/m, T degC), drain EC, and the daily metered irrigation and drain totals (L/m2).
"""
import os
import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "agc")
TEAMS = ["Reference", "AICU", "Automatoes", "Digilog", "IUACAAS", "TheAutomators"]


def _num(d):
    for c in d.columns:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def _time(excel_days):
    # timestamps are Excel serial days; round to the 5-min grid
    return pd.to_datetime(excel_days, unit="D", origin="1899-12-30").round("5min")


def load(team):
    c = pd.read_csv(os.path.join(DATA, team, "GreenhouseClimate.csv"), low_memory=False,
                    usecols=["%time", "Cum_irr", "water_sup", "EC_drain_PC", "Tair", "Tot_PAR"])
    g = pd.read_csv(os.path.join(DATA, team, "GrodanSens.csv"))
    c, g = _num(c), _num(g)
    c["t"], g["t"] = _time(c.pop("%time")), _time(g.pop("%time"))
    x = c.merge(g, on="t", how="left").set_index("t").sort_index()
    x = x[~x.index.duplicated()]

    # pulse volume: positive step of the daily cumulative irrigation. The counter resets shortly after
    # midnight (the 00:00 sample still holds the previous day's total), so a reset is detected by the
    # counter falling, not by the clock; at a reset the new value is the first pulse of the day.
    cum = x.Cum_irr
    d = cum.diff()
    reset = (d < 0).values
    d[reset] = cum[reset]
    x["irr"] = d.clip(lower=0).fillna(0)

    r = pd.read_csv(os.path.join(DATA, team, "Resources.csv"))
    r.columns = [k.strip() for k in r.columns]
    r = _num(r)
    r["day"] = pd.to_datetime(r.pop("%Time"), unit="D", origin="1899-12-30").dt.normalize()
    daily = r.set_index("day")[["Irr", "Drain"]]
    return x, daily
