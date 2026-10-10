"""The grid-topology baseline: bounded least squares with no roles given.

Low-voltage topology identification (e.g. Soft Computing 2022, doi 10.1007/s00500-022-07151-3;
Energies 17(7):1762, 2024) recovers which meters sit under a parent meter from the
conservation identity  parent = sum of children, fitted by least squares with coefficients
bounded in [0, 1] and read as membership (coefficient > 0.5 means "is a child"). There the
parent is known. Here it is not, so every detector is tried as the parent, which is the
most the method can be given without changing what it is.

Two variants, each run with two candidate-pool sizes:

  membership  coefficients in [0, 1], the published form. A junction whose slip flows in
              the opposite sense to the other children cannot be written this way unless
              the right detector happens to be chosen as parent; trying every parent gives
              it that chance.
  signed      coefficients in [-1, 1], a generalisation the grid art does not make, given
              here so that the failure cannot be blamed on sign alone.

The pool is the POOL detectors most correlated with the parent (the grid art's candidate
set is the meters on the feeder; along a motorway the equivalent is the detectors carrying
the same profile). The fitted relation is thresholded at 0.5 into {-1, 0, +1} and kept if
its residual is within discover2's self-derived limit - the same limit the method uses,
which the grid art has no way of deriving. Scored exactly as discover2 and OMP.
"""
import json
import os
import sys
import time

import numpy as np
from scipy.optimize import lsq_linear

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset, discover, discover2, evaluate
from discovery_v2_eval import categorise, recall_by_size

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CORRIDORS = (("M25", "window_full_M25_A.json"), ("M1", "window_M1_A.json"))
POOLS = (12, 30)


def pool_for(i, vol, obs, size):
    scored = []
    for j in range(vol.shape[0]):
        if j == i:
            continue
        both = obs[i] & obs[j]
        if both.sum() < discover2.MIN_OVERLAP or vol[j, both].std() < 1e-9:
            continue
        scored.append((abs(float(np.corrcoef(vol[i, both], vol[j, both])[0, 1])), j))
    scored.sort(reverse=True)
    pool = [j for _, j in scored[:size]]
    # grid methods need every meter in every sample: drop the most-missing member
    # until enough complete intervals remain
    while pool:
        rows = obs[i].copy()
        for j in pool:
            rows &= obs[j]
        if rows.sum() >= discover2.MIN_OVERLAP:
            return pool, rows
        pool.remove(min(pool, key=lambda j: obs[j].sum()))
    return [], None


def run_grid(c, limit, size, lower):
    vol, obs = c.volumes, c.observed
    found, seen = [], set()
    for i in range(vol.shape[0]):
        if obs[i].sum() < discover2.MIN_OVERLAP:
            continue
        pool, rows = pool_for(i, vol, obs, size)
        if not pool:
            continue
        A = vol[np.ix_(pool, np.where(rows)[0])].T
        coef = lsq_linear(A, vol[i, rows], bounds=(lower, 1.0)).x
        members = {j: int(np.sign(cf)) for j, cf in zip(pool, coef) if abs(cf) > 0.5}
        if not members:
            continue
        rel = {i: 1}
        for j, s in members.items():
            rel[j] = -s
        k = discover2.key(rel)
        if k in seen:
            continue
        p = discover2._resid_pct(rel, vol, obs)
        if p is not None and p <= limit:
            seen.add(k)
            found.append(rel)
    return found


def main():
    out = {"pools": list(POOLS), "threshold": 0.5, "corridors": {}}
    for name, manifest in CORRIDORS:
        c = dataset.load(manifest)
        truth = discover.truth_relations(c, evaluate.fit_node_signs(c))
        adj = discover2.ordering_stage(discover2.pair_stage(c.volumes, c.observed))
        limit = discover2.FLOOR_MULTIPLE * float(np.median(list(adj.values())))
        res = {"limit_pct_given": round(limit, 3)}
        for variant, lower in (("membership", 0.0), ("signed", -1.0)):
            for size in POOLS:
                t0 = time.time()
                found = run_grid(c, limit, size, lower)
                cats, prec = categorise(found, truth, c.shape[0])
                by = recall_by_size(found, truth)
                r = {"found": len(found), "categories": cats, "judged_precision": prec,
                     "recall_by_size": by,
                     "slip_recovered": sum(v["recovered"] for k, v in by.items() if k != "2"),
                     "slip_total": sum(v["of"] for k, v in by.items() if k != "2"),
                     "seconds": round(time.time() - t0, 1)}
                res["%s_pool%d" % (variant, size)] = r
                print(name, variant, size, r, flush=True)
        out["corridors"][name] = res
    with open(os.path.join(RESULTS, "baseline_grid.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/baseline_grid.json")


if __name__ == "__main__":
    main()
