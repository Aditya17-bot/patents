"""The closest art, run on the same data: can it recover the signed junction relations?

Two baselines, each given every advantage that does not change what it is:

IPCA (Narasimhan and Shah 2008; Rajeswaran and Narasimhan 2015). Recovers the constraint
matrix A (A x = 0) of a flow-conserving network from a data matrix of flows, with the noise
covariance estimated iteratively. It needs every flow observed in every sample, so it is
run on the complete-case submatrix: detectors are dropped, most-missing first, until at
least MIN_ROWS intervals have every remaining detector reporting. It is TOLD the number of
constraints (the number of surveyed relations among the retained detectors), which it would
not know in practice. Scored by (i) how many detectors survive complete-case selection,
(ii) the share of surveyed relations lying in the recovered constraint space, and
(iii) how many surveyed relations can be read off as rows of A in reduced row-echelon form
rounded to integers - i.e. whether it returns junctions or only a subspace.

OMP (matching pursuit, orthogonal variant). For each detector, greedily add the detector
most correlated with the current residual, refit by least squares over intervals in which
all selected detectors reported, up to four members. At each size, coefficients are rounded
and the relation kept if they are all +/-1 and the residual is within discover2's
self-derived limit (the same limit the method uses - an advantage, since OMP has no way of
deriving one). No ordering stage. Scored exactly as discover2.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset, discover, discover2, evaluate
from discovery_v2_eval import categorise, recall_by_size

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CORRIDORS = (("M25", "window_full_M25_A.json"), ("M1", "window_M1_A.json"))
MIN_ROWS = 300
OMP_MAX = 4
ROUND_TOL = discover2.ROUND_TOL


# ------------------------------------------------------------------ IPCA
def complete_case(obs):
    """Drop detectors, most-missing first, until MIN_ROWS intervals are complete."""
    keep = list(range(obs.shape[0]))
    while keep:
        rows = np.all(obs[keep], axis=0)
        if rows.sum() >= MIN_ROWS:
            return keep, rows
        miss = [(obs[k].sum(), k) for k in keep]
        keep.remove(min(miss)[1])
    return [], None


def ipca(X, m, iters=30):
    """Iterative PCA: constraint matrix A (m x n) with diagonal noise covariance."""
    n = X.shape[0]
    X = X - X.mean(axis=1, keepdims=True)
    sig = np.ones(n)
    for _ in range(iters):
        L = np.sqrt(sig)
        Y = X / L[:, None]
        w, V = np.linalg.eigh(Y @ Y.T / X.shape[1])
        As = V[:, :m].T                      # smallest-variance directions
        A = As / L[None, :]
        R = A @ X
        C = R @ R.T / X.shape[1]
        # diag(sig) such that A diag(sig) A^T ~ C, least squares on all entries
        G = np.array([np.outer(A[:, j], A[:, j]).ravel() for j in range(n)]).T
        s, _, _, _ = np.linalg.lstsq(G, C.ravel(), rcond=None)
        sig = np.clip(s, 1e-6 * max(s.max(), 1e-9), None)
    return A


def rref(A, tol=1e-9):
    A = A.copy()
    r, piv = 0, []
    for c in range(A.shape[1]):
        if r >= A.shape[0]:
            break
        p = r + np.argmax(np.abs(A[r:, c]))
        if abs(A[p, c]) < tol:
            continue
        A[[r, p]] = A[[p, r]]
        A[r] /= A[r, c]
        for q in range(A.shape[0]):
            if q != r:
                A[q] -= A[q, c] * A[r]
        piv.append(c)
        r += 1
    return A[:r]


def run_ipca(c, truth):
    keep, rows = complete_case(c.observed)
    kset = set(keep)
    sub = [t for t in truth if set(t) <= kset]
    out = {"detectors_total": c.shape[0], "detectors_retained": len(keep),
           "complete_intervals": int(rows.sum()) if rows is not None else 0,
           "surveyed_relations_total": len(truth),
           "surveyed_relations_among_retained": len(sub)}
    if not sub:
        return out
    pos = {k: a for a, k in enumerate(keep)}
    X = c.volumes[np.ix_(keep, np.where(rows)[0])]
    A = ipca(X, len(sub))
    # (ii) span containment
    Q, _ = np.linalg.qr(A.T)
    inside = 0
    for t in sub:
        v = np.zeros(len(keep))
        for r, s in t.items():
            v[pos[r]] = s
        if np.linalg.norm(v - Q @ (Q.T @ v)) / np.linalg.norm(v) < 0.1:
            inside += 1
    # (iii) readable signed relations
    R = rref(A)
    readable = set()
    for row in R:
        rr = np.round(row)
        if np.max(np.abs(row - rr)) <= ROUND_TOL and np.all(np.isin(rr[rr != 0], (-1, 1))):
            rel = {keep[j]: int(rr[j]) for j in np.nonzero(rr)[0]}
            readable.add(discover2.key(rel))
    tk = {discover2.key(t) for t in sub}
    out.update({"constraints_requested": len(sub), "in_recovered_span": inside,
                "rows_readable_as_signed_relations": len(readable),
                "surveyed_relations_read_off_exactly": len(readable & tk),
                "slip_relations_among_retained": sum(1 for t in sub if len(t) >= 3),
                "slip_relations_read_off_exactly": sum(
                    1 for t in sub if len(t) >= 3 and discover2.key(t) in readable)})
    return out


# ------------------------------------------------------------------ OMP
def run_omp(c, limit):
    vol, obs = c.volumes, c.observed
    n = vol.shape[0]
    found, seen = [], set()
    for i in range(n):
        if obs[i].sum() < discover2.MIN_OVERLAP:
            continue
        sel = []
        mask = obs[i].copy()
        resid = vol[i].copy()
        for _ in range(OMP_MAX):
            best, bj = -1.0, None
            for j in range(n):
                if j == i or j in sel:
                    continue
                b = mask & obs[j]
                if b.sum() < discover2.MIN_OVERLAP or vol[j, b].std() < 1e-9:
                    continue
                cc = abs(float(np.corrcoef(resid[b], vol[j, b])[0, 1]))
                if cc > best:
                    best, bj = cc, j
            if bj is None:
                break
            sel.append(bj)
            mask = mask & obs[bj]
            lib = vol[np.ix_(sel, np.where(mask)[0])].T
            coef, _, _, _ = np.linalg.lstsq(lib, vol[i, mask], rcond=None)
            resid = np.zeros(vol.shape[1])
            resid[mask] = vol[i, mask] - lib @ coef
            rounded = np.round(coef)
            if np.max(np.abs(coef - rounded)) <= ROUND_TOL and \
                    np.all(np.isin(rounded, (-1.0, 1.0))):
                rel = {i: 1}
                for j, cf in zip(sel, rounded):
                    rel[j] = -int(cf)
                k = discover2.key(rel)
                p = discover2._resid_pct(rel, vol, obs)
                if k not in seen and p is not None and p <= limit:
                    seen.add(k)
                    found.append(rel)
    return found


def main():
    out = {"min_rows_complete_case": MIN_ROWS, "omp_max_members": OMP_MAX, "corridors": {}}
    for name, manifest in CORRIDORS:
        c = dataset.load(manifest)
        truth = discover.truth_relations(c, evaluate.fit_node_signs(c))
        res = {}
        t0 = time.time()
        res["ipca"] = run_ipca(c, truth)
        res["ipca"]["seconds"] = round(time.time() - t0, 1)
        print(name, "IPCA", res["ipca"], flush=True)

        adj = discover2.ordering_stage(discover2.pair_stage(c.volumes, c.observed))
        limit = discover2.FLOOR_MULTIPLE * float(np.median(list(adj.values())))
        t0 = time.time()
        found = run_omp(c, limit)
        cats, prec = categorise(found, truth, c.shape[0])
        by = recall_by_size(found, truth)
        res["omp"] = {"limit_pct_given": round(limit, 3), "found": len(found),
                      "categories": cats, "judged_precision": prec, "recall_by_size": by,
                      "slip_recovered": sum(v["recovered"] for k, v in by.items() if k != "2"),
                      "slip_total": sum(v["of"] for k, v in by.items() if k != "2"),
                      "seconds": round(time.time() - t0, 1)}
        print(name, "OMP", res["omp"], flush=True)
        out["corridors"][name] = res
    with open(os.path.join(RESULTS, "baseline_structure.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/baseline_structure.json")


if __name__ == "__main__":
    main()
