"""Would a sparse or rotated variant of the closest art have found the junctions?

baselines_structure.py showed IPCA returns a constraint SPACE containing none of the
surveyed relations, and that its rows cannot be read as signed junctions. The natural
objection is that a sparsity-seeking variant would do better, since true junction
relations are sparse (2-5 members). Two such variants are run on the same complete-case
data IPCA was given (MIN_ROWS 1000, the more favourable of the two subsets tried):

  varimax   the IPCA constraint basis rotated by varimax, the standard route to
            interpretable sparse loadings; each rotated row is scaled so its largest entry
            is 1 and read off by rounding, as the IPCA rows were.
  lasso     sparse regression of each detector on all the others (L1 penalty, FISTA), swept over LAMBDAS; coefficients rounded, the relation kept if all
            members are +/-1 and its residual is within discover2's self-derived limit -
            the same limit and admission rule OMP and the grid baseline were given.

Scored exactly as the others: surveyed relations recovered exactly, slip-road junctions
recovered, judged precision. Writes results/baseline_sparse.json.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baselines_structure as BS
import dataset, discover, discover2, evaluate
from discovery_v2_eval import categorise, recall_by_size

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CORRIDORS = BS.CORRIDORS
MIN_ROWS = 1000
LAMBDAS = (0.01, 0.03, 0.1, 0.3)   # fraction of the largest useful penalty


def varimax(Phi, iters=100, tol=1e-6):
    """Varimax rotation of the columns of Phi (p x k)."""
    p, k = Phi.shape
    R = np.eye(k)
    d = 0.0
    for _ in range(iters):
        L = Phi @ R
        u, s, vh = np.linalg.svd(Phi.T @ (L ** 3 - L @ np.diag((L ** 2).sum(axis=0)) / p))
        R = u @ vh
        d_new = s.sum()
        if d_new < d * (1 + tol):
            break
        d = d_new
    return Phi @ R


def lasso_fista(A, y, lam, iters=500):
    """min 0.5/n ||y - A b||^2 + lam ||b||_1 by FISTA (accelerated proximal gradient)."""
    n, p = A.shape
    L = float(np.linalg.norm(A, 2) ** 2) / n
    b = np.zeros(p)
    z, t = b.copy(), 1.0
    for _ in range(iters):
        g = A.T @ (A @ z - y) / n
        u = z - g / L
        b_new = np.sign(u) * np.maximum(np.abs(u) - lam / L, 0.0)
        t_new = (1 + np.sqrt(1 + 4 * t * t)) / 2
        z = b_new + ((t - 1) / t_new) * (b_new - b)
        b, t = b_new, t_new
    return b


def read_rows(rows, keep):
    out = []
    for row in rows:
        m = np.max(np.abs(row))
        if m <= 0:
            continue
        v = row / m
        rr = np.round(v)
        if np.max(np.abs(v - rr)) <= BS.ROUND_TOL and np.all(np.isin(rr[rr != 0], (-1, 1))) \
                and (rr != 0).sum() >= 2:
            out.append({keep[j]: int(rr[j]) for j in np.nonzero(rr)[0]})
    return out


def scored(found, truth, n, extra):
    cats, prec = categorise(found, truth, n)
    by = recall_by_size(found, truth)
    d = {"found": len(found), "categories": cats, "judged_precision": prec,
         "recall_by_size": by,
         "slip_recovered": sum(v["recovered"] for k, v in by.items() if k != "2"),
         "slip_total": sum(v["of"] for k, v in by.items() if k != "2")}
    d.update(extra)
    return d


def main():
    BS.MIN_ROWS = MIN_ROWS
    out = {"min_rows_complete_case": MIN_ROWS, "lambdas": list(LAMBDAS), "corridors": {}}
    for name, manifest in CORRIDORS:
        c = dataset.load(manifest)
        truth = discover.truth_relations(c, evaluate.fit_node_signs(c))
        keep, rows = BS.complete_case(c.observed)
        kset = set(keep)
        sub = [t for t in truth if set(t) <= kset]
        X = c.volumes[np.ix_(keep, np.where(rows)[0])]
        adj = discover2.ordering_stage(discover2.pair_stage(c.volumes, c.observed))
        limit = discover2.FLOOR_MULTIPLE * float(np.median(list(adj.values())))
        res = {"detectors_retained": len(keep), "complete_intervals": int(rows.sum()),
               "surveyed_relations_among_retained": len(sub),
               "slip_relations_among_retained": sum(1 for t in sub if len(t) >= 3),
               "limit_pct_given": round(limit, 3)}

        t0 = time.time()
        A = BS.ipca(X, len(sub))
        Q, _ = np.linalg.qr(A.T)                   # orthonormal basis of the space
        rot = varimax(Q).T
        found = read_rows(rot, keep)
        res["varimax"] = scored(found, truth, c.shape[0],
                                {"seconds": round(time.time() - t0, 1)})
        print(name, "varimax", res["varimax"], flush=True)

        for lam_frac in LAMBDAS:
            t0 = time.time()
            found, seen = [], set()
            for a in range(len(keep)):
                others = [b for b in range(len(keep)) if b != a]
                Aa = X[others].T
                y = X[a]
                lam_max = float(np.max(np.abs(Aa.T @ y))) / y.size
                b = lasso_fista(Aa, y, lam_frac * lam_max)
                # relaxed Lasso: the L1 penalty shrinks every coefficient towards zero,
                # so a true unit coefficient would never round to 1. Refit by least
                # squares on the selected support before rounding, the standard remedy.
                sup = np.nonzero(np.abs(b) > 1e-6)[0]
                if sup.size == 0 or sup.size > 12:
                    continue
                refit, _, _, _ = np.linalg.lstsq(Aa[:, sup], y, rcond=None)
                b = np.zeros_like(b)
                b[sup] = refit
                rr = np.round(b)
                nz = np.nonzero(rr)[0]
                if nz.size == 0 or not np.all(np.isin(rr[nz], (-1, 1))):
                    continue
                rel = {keep[a]: 1}
                for j in nz:
                    rel[keep[others[j]]] = -int(rr[j])
                k = discover2.key(rel)
                if k in seen:
                    continue
                p = discover2._resid_pct(rel, c.volumes, c.observed)
                if p is not None and p <= limit:
                    seen.add(k)
                    found.append(rel)
            lab = "lasso_%g" % lam_frac
            res[lab] = scored(found, truth, c.shape[0],
                              {"seconds": round(time.time() - t0, 1)})
            print(name, lab, res[lab], flush=True)
        out["corridors"][name] = res
    with open(os.path.join(RESULTS, "baseline_sparse.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/baseline_sparse.json")


if __name__ == "__main__":
    main()
