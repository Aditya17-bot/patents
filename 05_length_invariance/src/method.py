"""The method: size each detector's length-class bias along a chain, and correct it.

For a pair of adjacent detectors observing the same vehicles, the share of vehicles
below each length-class boundary must agree. Along a chain of such pairs, detector i
and detector i+1 give one equation per boundary e:

    b[i](e) - b[i+1](e) = g[i](e)

where g is the measured share gap of the pair over matched intervals and b is each
detector's bias in the share below e. A chain of k+1 detectors gives k equations in
k+1 unknowns per boundary, so the biases are fixed up to a common constant. That
constant is set by requiring the median bias over the chain to be zero: the majority of
detectors on a chain is taken to be correctly calibrated, and the fleet's true length
distribution is identical along the chain because the vehicles are the same.

A detector is flagged where its bias at the most populated boundary (520 cm, where car
lengths end) exceeds both a noise limit, three standard errors of the same quantity
computed day by day, and a floor below which a correction would not be worth writing.

Correction reclassifies vehicles across boundaries and never changes an interval's total.
Two models of how a length offset moves vehicles are provided and are compared by
measurement in evaluate_e1.py:

    additive   S'(e) = S(e) - b(e)            constant share moved in every interval
    ratio      S'(e) = S(e) * (1 - b(e)/S̄(e)) share moved in proportion to the share
                                              below the boundary in that interval

where S(e) is the detector's share below e in one interval and S̄(e) its share over the
fitting period. The ratio model follows from the physics: an offset moves the vehicles
whose length lies within the offset of the boundary, and how many there are in a given
interval scales with how many vehicles are below the boundary at all.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import series

N_EDGES = len(series.EDGES_CM)
PRIMARY_EDGE = 0          # 520 cm
FLAG_SE_MULTIPLE = 3.0
FLAG_FLOOR = 0.01         # one percentage point of share below 520 cm


def cumulative(bins):
    """Counts below each edge, from one record's four bin counts."""
    out = []
    below = 0
    for n in bins[:-1]:
        below += n
        out.append(below)
    return out


def shares(data, keys):
    """Share below each edge over the given intervals: sum(below) / sum(all)."""
    below = [0] * N_EDGES
    total = 0
    for k in keys:
        bins = data[k][0]
        c = cumulative(bins)
        for e in range(N_EDGES):
            below[e] += c[e]
        total += sum(bins)
    return [x / total for x in below]


def by_day(keys):
    days = {}
    for k in keys:
        days.setdefault(k.split("_")[0], []).append(k)
    return days


def pair_gap(rec):
    """Share gap (up minus down) per edge, over all matched intervals and per day."""
    keys = rec["keys"]
    su, sd = shares(rec["a"], keys), shares(rec["b"], keys)
    gap = [su[e] - sd[e] for e in range(N_EDGES)]
    daily = {}
    for day, dk in by_day(keys).items():
        if len(dk) < 8:
            continue
        du, dd = shares(rec["a"], dk), shares(rec["b"], dk)
        daily[day] = [du[e] - dd[e] for e in range(N_EDGES)]
    return gap, daily, su, sd


def _median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


# How the common constant of a chain is fixed. "median": the median detector is taken as
# correct. "cluster": the largest set of detectors whose relative biases agree within
# CLUSTER_TOL at the primary boundary is taken as correct, and the constant is their
# median; with no two detectors agreeing it falls back to the median. See e2_injection.py
# (median vs cluster, results/e2_injection_*gauge.json): the cluster gauge localised
# fewer injected faults and flipped more flags on the short chains of this corridor.
GAUGE = "median"
CLUSTER_TOL = 0.01


def _relative(gaps):
    """Biases of k+1 detectors from k consecutive gaps, relative to the first detector."""
    b = [0.0]
    for g in gaps:
        b.append(b[-1] - g)
    return b


def _reference_set(b):
    """Indices of the detectors taken as correctly calibrated, from primary-edge biases."""
    if GAUGE == "median":
        return list(range(len(b)))
    best = None
    for c in b:
        members = [i for i, x in enumerate(b) if abs(x - c) <= CLUSTER_TOL]
        spread = sum(abs(b[i] - c) for i in members)
        if best is None or (len(members), -spread) > (len(best[0]), -best[1]):
            best = (members, spread)
    if len(best[0]) < 2:
        return list(range(len(b)))
    return best[0]


def _chain_bias(gaps, ref=None):
    """Biases of k+1 detectors from k consecutive gaps, gauge fixed on the reference set."""
    b = _relative(gaps)
    if ref is None:
        ref = list(range(len(b)))
    m = _median([b[i] for i in ref])
    return [x - m for x in b]


def solve_chain(chain):
    """Per-detector bias, its day-to-day standard error, and the flag, for one chain.

    chain: list of (up, down, node_id, record) in chainage order, as pairs.chains().
    Returns a list of dicts, one per detector, in chainage order.
    """
    detectors = [chain[0][0]] + [p[1] for p in chain]
    fitted = [pair_gap(p[3]) for p in chain]

    ref = _reference_set(_relative([f[0][PRIMARY_EDGE] for f in fitted]))
    bias = []
    for e in range(N_EDGES):
        bias.append(_chain_bias([f[0][e] for f in fitted], ref))

    # Day-by-day solution over the days on which every pair of the chain has data, on
    # the same reference set, so that the standard error measures noise, not the gauge.
    common = set(fitted[0][1])
    for f in fitted[1:]:
        common &= set(f[1])
    daily_bias = {}
    for day in sorted(common):
        daily_bias[day] = [_chain_bias([f[1][day][e] for f in fitted], ref)
                           for e in range(N_EDGES)]

    # Each detector's own share over the fitting period, for the ratio model.
    own_share = [fitted[0][2]] + [f[3] for f in fitted]

    out = []
    for i, det in enumerate(detectors):
        se = []
        for e in range(N_EDGES):
            xs = [daily_bias[d][e][i] for d in daily_bias]
            if len(xs) >= 5:
                mean = sum(xs) / len(xs)
                var = sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)
                se.append(math.sqrt(var / len(xs)))
            else:
                se.append(float("nan"))
        b0, s0 = bias[PRIMARY_EDGE][i], se[PRIMARY_EDGE]
        flagged = (len(detectors) >= 3 and not math.isnan(s0)
                   and abs(b0) > FLAG_SE_MULTIPLE * s0 and abs(b0) > FLAG_FLOOR)
        out.append({
            "detector": det,
            "bias": [bias[e][i] for e in range(N_EDGES)],
            "se": se,
            "share": own_share[i],
            "n_days": len(daily_bias),
            "chain_size": len(detectors),
            "flagged": flagged,
        })
    return out


def correct_record(bins, fit, model):
    """Reclassify one interval's bin counts by a detector's fitted bias.

    The total is preserved; vehicles move only across boundaries, and the corrected
    counts below successive boundaries are kept non-decreasing.
    """
    n = sum(bins)
    if n == 0:
        return list(bins)
    cum = cumulative(bins)
    new_cum = []
    for e in range(N_EDGES):
        s = cum[e] / n
        if model == "additive":
            s_new = s - fit["bias"][e]
        elif model == "ratio":
            ref = fit["share"][e]
            s_new = s * (1.0 - fit["bias"][e] / ref) if ref > 0 else s
        else:
            raise ValueError(model)
        s_new = min(1.0, max(0.0, s_new))
        new_cum.append(int(round(s_new * n)))
    for e in range(1, N_EDGES):
        new_cum[e] = max(new_cum[e], new_cum[e - 1])
    new_bins = [new_cum[0]]
    for e in range(1, N_EDGES):
        new_bins.append(new_cum[e] - new_cum[e - 1])
    new_bins.append(n - new_cum[-1])
    return new_bins


def correct_series(data, fit, model):
    """A corrected copy of one detector's series; speeds and totals untouched."""
    out = {}
    for k, (bins, total, speed) in data.items():
        out[k] = [correct_record(bins, fit, model), total, speed]
    return out
