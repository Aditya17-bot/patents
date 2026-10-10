"""Recovering junction structure from the counts, slip roads included.

discover.py recovers plain continuity and almost nothing else. Measured on the full M25
corridor it found 724 two-detector relations and 2 larger ones; of the 43 surveyed
relations that involve a slip road it recovered 1. The cause is the shortlist: candidates
are ranked by correlation with the target detector, and a slip road correlates with the
mainline far more weakly than the next mainline detector does, so it never enters the
pool that is enumerated.

The slip flow is not what correlates with the mainline. It is what is left over when the
two mainline detectors either side of a junction are subtracted. So this module works in
three stages:

  1. Pair stage. Every detector pair whose counts agree (coefficient rounds to 1).
  2. Ordering stage. A pair (i, k) is removed where some j agrees with both i and k more
     tightly than i and k agree with each other - j lies between them. What remains is
     the chain of adjacent detectors along the carriageway: the order of the sites along
     the road, recovered without coordinates or names.
  3. Junction stage. For each detector, its mainline partner candidates are taken, the
     residual x_i - x_k is formed, and slip candidates are shortlisted by correlation
     with that residual. Subsets are fitted to the residual, coefficients rounded to
     {-1, +1}, and a relation is retained only if each of its members is necessary:
     dropping any one of them raises the residual by at least NECESSITY.

Retention is judged against a floor taken from the counts themselves - the median residual
of the adjacent pairs of stage 2 - never from the surveyed map.
"""
import itertools
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

MIN_OVERLAP = 400
ROUND_TOL = 0.30
PAIR_TOL_PCT = 4.0
NECESSITY = 1.5          # dropping a member must raise the residual by this factor
FLOOR_MULTIPLE = 2.0
PARTNERS = 6             # mainline partner candidates per detector
SLIP_SHORTLIST = 8       # residual-correlated slip candidates per partner
MAX_SLIPS = 3
# What slip candidates are ranked against: "residual" (x_i - x_k, the method) or
# "target" (x_i itself). The second exists only for the controlled ablation.
RANKING = "residual"


def _resid_pct(rel, vol, obs, absolute=False):
    rows = list(rel)
    both = np.all(obs[rows], axis=0)
    if both.sum() < MIN_OVERLAP:
        return None
    r = np.zeros(int(both.sum()))
    for row, c in rel.items():
        r = r + c * vol[row, both]
    flow = max(float(vol[row, both].mean()) for row in rows)
    if flow < 1:
        return None
    if absolute:
        return float(np.median(np.abs(r)))
    return float(np.median(np.abs(r))) / flow * 100.0


def _record(rel, pct, vol, obs):
    """Output row; median_abs_residual in vehicles is what the reconciler consumes."""
    return {"rows": rel, "residual_pct_of_flow": round(pct, 3),
            "median_abs_residual": round(_resid_pct(rel, vol, obs, absolute=True), 2)}


def pair_stage(vol, obs):
    """All pairs (i, k) with x_i ~ x_k, and their residual as % of flow."""
    n = vol.shape[0]
    pairs = {}
    for i in range(n):
        for k in range(i + 1, n):
            both = obs[i] & obs[k]
            if both.sum() < MIN_OVERLAP:
                continue
            a, b = vol[i, both], vol[k, both]
            if b.std() < 1e-9:
                continue
            coef = float(a @ b) / float(b @ b)
            if abs(coef - 1.0) > ROUND_TOL:
                continue
            flow = max(a.mean(), b.mean())
            if flow < 1:
                continue
            pct = float(np.median(np.abs(a - b))) / flow * 100.0
            if pct <= PAIR_TOL_PCT:
                pairs[(i, k)] = pct
    return pairs


def ordering_stage(pairs):
    """Drop (i, k) wherever some j sits between them: both (i, j) and (j, k) tighter."""
    nbr = {}
    for (i, k), p in pairs.items():
        nbr.setdefault(i, {})[k] = p
        nbr.setdefault(k, {})[i] = p
    kept = {}
    for (i, k), p in pairs.items():
        shortcut = False
        for j, pij in nbr.get(i, {}).items():
            if j == k:
                continue
            pjk = nbr.get(j, {}).get(k)
            if pjk is not None and pij < p and pjk < p:
                shortcut = True
                break
        if not shortcut:
            kept[(i, k)] = p
    return kept


def junction_stage(vol, obs, pair_tol_ok):
    """Relations x_i - x_k + sum s_j x_j ~ 0 with slips found from the pair residual."""
    n = vol.shape[0]
    found = []
    for i in range(n):
        if obs[i].sum() < MIN_OVERLAP:
            continue
        # mainline partners: most correlated detectors of similar flow
        scored = []
        for k in range(n):
            if k == i:
                continue
            both = obs[i] & obs[k]
            if both.sum() < MIN_OVERLAP:
                continue
            a, b = vol[i, both], vol[k, both]
            if a.std() < 1e-9 or b.std() < 1e-9:
                continue
            ratio = b.mean() / max(a.mean(), 1e-9)
            if not 0.5 <= ratio <= 2.0:
                continue
            scored.append((abs(float(np.corrcoef(a, b)[0, 1])), k))
        scored.sort(reverse=True)
        for _, k in scored[:PARTNERS]:
            if (min(i, k), max(i, k)) in pair_tol_ok:
                continue            # already plain continuity, nothing to explain
            base = obs[i] & obs[k]
            resid_full = vol[i] - vol[k]
            rank_ref = resid_full if RANKING == "residual" else vol[i]
            cands = []
            for j in range(n):
                if j in (i, k):
                    continue
                both = base & obs[j]
                if both.sum() < MIN_OVERLAP:
                    continue
                x = vol[j, both]
                if x.std() < 1e-9:
                    continue
                cands.append((abs(float(np.corrcoef(rank_ref[both], x)[0, 1])), j))
            cands.sort(reverse=True)
            pool = [j for _, j in cands[:SLIP_SHORTLIST]]
            for size in range(1, MAX_SLIPS + 1):
                for combo in itertools.combinations(pool, size):
                    both = base.copy()
                    for j in combo:
                        both &= obs[j]
                    if both.sum() < MIN_OVERLAP:
                        continue
                    target = resid_full[both]
                    lib = vol[np.ix_(list(combo), both)].T
                    coef, _, _, _ = np.linalg.lstsq(lib, target, rcond=None)
                    rounded = np.round(coef)
                    if np.max(np.abs(coef - rounded)) > ROUND_TOL:
                        continue
                    if not np.all(np.isin(rounded, (-1.0, 1.0))):
                        continue
                    rel = {i: 1, k: -1}
                    for j, c in zip(combo, rounded):
                        rel[j] = -int(c)
                    found.append(rel)
    return found


def necessary(rel, vol, obs, own):
    """Every member earns its place: removing it worsens the residual by NECESSITY."""
    if len(rel) <= 2:
        return True
    for r in rel:
        sub = {k: v for k, v in rel.items() if k != r}
        p = _resid_pct(sub, vol, obs)
        if p is not None and p < NECESSITY * own:
            return False
    return True


def key(rel):
    items = tuple(sorted(rel.items()))
    flip = tuple(sorted((r, -c) for r, c in rel.items()))
    return min(items, flip)


def discover(vol, obs, verbose=False):
    pairs = pair_stage(vol, obs)
    adjacent = ordering_stage(pairs)
    floor = float(np.median(list(adjacent.values()))) if adjacent else None
    limit = FLOOR_MULTIPLE * floor
    if verbose:
        print("  pairs %d, adjacent after ordering %d, self floor %.3f%%"
              % (len(pairs), len(adjacent), floor), flush=True)

    tight_pairs = {p for p, v in adjacent.items() if v <= limit}
    out, seen = [], set()
    for (i, k), p in adjacent.items():
        if p <= limit:
            rel = {i: 1, k: -1}
            seen.add(key(rel))
            out.append(_record(rel, p, vol, obs))

    cands = junction_stage(vol, obs, tight_pairs)
    if verbose:
        print("  junction candidates %d" % len(cands), flush=True)
    for rel in cands:
        k = key(rel)
        if k in seen:
            continue
        seen.add(k)
        p = _resid_pct(rel, vol, obs)
        if p is None or p > limit:
            continue
        if not necessary(rel, vol, obs, p):
            continue
        out.append(_record(rel, p, vol, obs))
    return out, {"pairs": len(pairs), "adjacent": len(adjacent),
                 "self_floor_pct": round(floor, 3), "limit_pct": round(limit, 3)}
