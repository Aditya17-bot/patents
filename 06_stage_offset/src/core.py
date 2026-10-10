"""Core numerics: base stage-discharge rating, hourly series, lag, stage-offset estimator.

Notation (gauge X is the gauge whose rating offset is estimated; gauge Y is a gauge on
the same river with no significant inflow or abstraction between them):

  R(g)        base rating of X: discharge at effective stage g (ft -> ft^3/s)
  h(t)        gage height recorded at X
  s           stage offset ("shift"): true discharge = R(h + s)
  Q_Y(t)      discharge at Y
  tau         travel-time lag from Y to X (hours; negative if Y is downstream)
  y(t)        ln Q_Y(t - tau) - ln R(h(t))        log discrepancy
  x(t)        d ln R / dg at g = h(t)             rating log-slope (1/ft)
  c           ln(Q_Y / Q_X) = flow ratio between the gauges (inflow, abstraction)

Since ln R(h + s) ~= ln R(h) + s * x(t),   y(t) ~= c + s * x(t).

A stage offset therefore produces a discrepancy that scales with the rating log-slope
(large at low stage, small at high stage); a flow-ratio change produces one that does
not. The estimator converts each hour's discrepancy into stage units through x(t) and
aggregates in stage units.
"""
import bisect
import datetime as dt
import math

import numpy as np


class Rating:
    """Base rating built from a NWIS expanded shift-adjusted table (h, shift, Q).

    The table lists, for each recorded stage h, the shift s(h) in force and
    Q = R(h + s(h)). The base rating is therefore R tabulated at g = h + s(h)."""

    def __init__(self, rows, rating_id="", begin=None):
        pts = sorted({round(h + s, 4): q for h, s, q in rows if q > 0}.items())
        g = [p[0] for p in pts]
        lq = [math.log(p[1]) for p in pts]
        keep_g, keep_l = [], []
        for a, b in zip(g, lq):  # strictly increasing in both
            if keep_g and (a <= keep_g[-1] or b <= keep_l[-1]):
                continue
            keep_g.append(a)
            keep_l.append(b)
        self.g = np.array(keep_g)
        self.lq = np.array(keep_l)
        self.rating_id = rating_id
        self.begin = begin
        self.gmin, self.gmax = self.g[0], self.g[-1]

    def lnq(self, g):
        return np.interp(g, self.g, self.lq, left=np.nan, right=np.nan)

    def q(self, g):
        return np.exp(self.lnq(g))

    def g_of_q(self, q):
        return np.interp(np.log(q), self.lq, self.g, left=np.nan, right=np.nan)

    def slope(self, g, dg=0.05):
        """d ln R / d g by central difference over +-dg ft."""
        return (self.lnq(np.asarray(g) + dg) - self.lnq(np.asarray(g) - dg)) / (2 * dg)


def hourly(series):
    """15-min (t, v, quals) -> dict hour_index -> (mean value, provisional flag, flagged)."""
    acc = {}
    for t, v, qual in series:
        k = int(t.timestamp() // 3600)
        a = acc.setdefault(k, [0.0, 0, False, False])
        a[0] += v
        a[1] += 1
        if "P" in qual:
            a[2] = True
        if any(q in ("Ice", "Eqp", "Bkw", "Mnt", "Dis", "Ssn", "Fld", "Rat") for q in qual):
            a[3] = True
    return {k: (a[0] / a[1], a[2], a[3]) for k, a in acc.items()}


def to_hour(t):
    return int(t.timestamp() // 3600)


def lag_hours(hx, hy, max_lag=72):
    """Travel-time lag Y -> X: maximise correlation of hourly changes of ln Q."""
    keys = sorted(set(hx) | set(hy))
    if len(set(hx) & set(hy)) < 2000:
        return 0, float("nan")
    k0, k1 = keys[0], keys[-1]
    n = k1 - k0 + 1
    ax = np.full(n, np.nan)
    ay = np.full(n, np.nan)
    for k, v in hx.items():
        ax[k - k0] = math.log(max(v[0], 1e-3))
    for k, v in hy.items():
        ay[k - k0] = math.log(max(v[0], 1e-3))
    dx = np.diff(ax)
    dy = np.diff(ay)
    best, bestr = 0, -2.0
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            a, b = dx[lag:], dy[:len(dy) - lag]
        else:
            a, b = dx[:lag], dy[-lag:]
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() < 1000:
            continue
        r = float(np.corrcoef(a[ok], b[ok])[0, 1])
        if r > bestr:
            best, bestr = lag, r
    return best, bestr


def daily_corr(hx, hy, lag):
    """Correlation of daily mean ln Q between X and lagged Y (pair coupling)."""
    dx, dy = {}, {}
    for k, v in hx.items():
        dx.setdefault(k // 24, []).append(v[0])
    for k, v in hy.items():
        dy.setdefault((k + lag) // 24, []).append(v[0])
    a, b = [], []
    for d in dx:
        if d in dy and len(dx[d]) >= 20 and len(dy[d]) >= 20:
            a.append(math.log(max(np.mean(dx[d]), 1e-3)))
            b.append(math.log(max(np.mean(dy[d]), 1e-3)))
    if len(a) < 300:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def offset_ls(y, x, c):
    """Stage offset by least squares of (y - c) on x without intercept: weights each
    hour by its rating log-slope, so low-stage hours (most sensitive) count most."""
    y = np.asarray(y) - c
    x = np.asarray(x)
    ok = np.isfinite(y) & np.isfinite(x)
    if ok.sum() == 0:
        return float("nan")
    return float(np.sum(x[ok] * y[ok]) / np.sum(x[ok] ** 2))


def offset_fixed_ratio(y, x, c):
    """Stage offset from hourly discrepancies with the flow ratio c fixed:
    per-hour s_h = (y_h - c) / x_h, aggregated by the median (stage units)."""
    s = (np.asarray(y) - c) / np.asarray(x)
    s = s[np.isfinite(s)]
    if len(s) == 0:
        return float("nan"), 0
    return float(np.median(s)), len(s)


def offset_free_ratio(y, x):
    """Joint fit y = c + s x (Theil-Sen slope for robustness). Returns (s, c, spread of x)."""
    y = np.asarray(y)
    x = np.asarray(x)
    ok = np.isfinite(y) & np.isfinite(x)
    y, x = y[ok], x[ok]
    if len(x) < 24:
        return float("nan"), float("nan"), 0.0
    spread = float(np.percentile(x, 90) - np.percentile(x, 10))
    # Theil-Sen on a subsample of pairs
    rng = np.random.default_rng(0)
    n = len(x)
    i = rng.integers(0, n, 4000)
    j = rng.integers(0, n, 4000)
    dxx = x[j] - x[i]
    good = np.abs(dxx) > 1e-3
    if good.sum() < 50:
        return float("nan"), float("nan"), spread
    slope = float(np.median((y[j] - y[i])[good] / dxx[good]))
    c = float(np.median(y - slope * x))
    return slope, c, spread
