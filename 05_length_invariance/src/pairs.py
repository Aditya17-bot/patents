"""Adjacent detector pairs that observe the same vehicles, and the chains they form.

Two consecutive mainline detectors observe the same vehicles when no slip road joins or
leaves the carriageway between them. corridor.build_nodes() already lists, for each
consecutive mainline pair, the slip sites whose chainage falls between them; a pair with
none is a candidate.

A candidate is admitted for a given month only if its two total counts agree over the
matched intervals (the volume-balance gate). This excludes a pair at which one detector
has lost a lane, or at which an uninstrumented access exists, since in either case the
two detectors no longer see the same vehicles. Total counts are used for nothing else.

Consecutive admitted pairs that share a detector form a chain. Each interior detector of
a chain appears in two pairs, which is what localises a fault to one detector.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corridor
import series

# Free-flow condition. Dual-loop length measurement assumes a constant speed across the
# detector; in stop-go traffic acceleration corrupts it (Wu & Coifman 2014), so only
# intervals where both detectors report an average above this are compared.
MIN_SPEED_MPH = 50.0
# Minimum vehicles per interval at the upstream detector for the interval to be used.
MIN_VOLUME = 100
# Volume-balance gate: |sum(up) / sum(down) - 1| must be below this.
BALANCE_TOL = 0.03
# Minimum matched intervals for a pair to be admitted in a month.
MIN_INTERVALS = 500


def candidates(road, carriageway="A"):
    """Consecutive mainline pairs with no slip site between them, in chainage order."""
    nodes = corridor.build_nodes(corridor.corridor_sites(road, carriageway))
    out = []
    for n in nodes:
        if n["usable"] and not n["slips"]:
            out.append((n["upstream"]["id"], n["downstream"]["id"], n["node_id"]))
    return out


def matched(a, b):
    """Interval keys present at both detectors that satisfy the free-flow condition."""
    keys = []
    for k, (bins_a, tot_a, spd_a) in a.items():
        if k not in b:
            continue
        bins_b, tot_b, spd_b = b[k]
        if spd_a <= MIN_SPEED_MPH or spd_b <= MIN_SPEED_MPH:
            continue
        if tot_a < MIN_VOLUME or sum(bins_a) == 0 or sum(bins_b) == 0:
            continue
        keys.append(k)
    return keys


def pair_record(up, down, month):
    """Matched intervals and the volume-balance ratio for one pair and month."""
    a = series.load(up, month)
    b = series.load(down, month)
    keys = matched(a, b)
    if len(keys) < MIN_INTERVALS:
        return None
    ratio = sum(a[k][1] for k in keys) / sum(b[k][1] for k in keys)
    return {"keys": keys, "a": a, "b": b, "ratio": ratio,
            "admitted": abs(ratio - 1.0) < BALANCE_TOL}


def chains(road, month, carriageway="A"):
    """Admitted pairs grouped into chains of consecutive detectors.

    Returns a list of chains; each chain is a list of (up, down, node_id, record) in
    chainage order, where the down detector of one entry is the up detector of the next.
    Pairs that fail the gate, or lack data, break the chain.
    """
    out = []
    current = []
    for up, down, node_id in candidates(road, carriageway):
        rec = pair_record(up, down, month)
        if rec is None or not rec["admitted"]:
            if current:
                out.append(current)
            current = []
            continue
        if current and current[-1][1] != up:
            out.append(current)
            current = []
        current.append((up, down, node_id, rec))
    if current:
        out.append(current)
    return out
