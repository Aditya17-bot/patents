"""Recovering the conservation relations from the counts alone.

Every piece of prior art found in Phase 6 takes the network structure as given. de Souza
(2019) works from a known freeway station layout, Yin et al. (2017) from a known network
incidence matrix, and process-industry data reconciliation from a known flowsheet. The
structure is an input in all of them.

This module makes it an output. Given nothing but the matrix of counts - no site names,
no coordinates, no junction database, no naming convention - it searches for sparse
relations with coefficients in {-1, 0, +1} that hold across every interval:

    sum_i c_i * x_i(t)  ~  0    for all t,   c sparse, c_i in {-1, 0, +1}

Any such relation is a conservation law of the network expressed in the data. Recovering
one means recovering a node: which detectors bound it, and which way each contributes.

Method. For each detector in turn, treat it as the odd one out and use orthogonal
matching pursuit to find the small set of other detectors that best explains it. Rounding
the fitted coefficients to the nearest of {-1, 0, +1} and keeping only relations whose
residual is small enough turns a regression into a candidate physical law. Rounding is
what makes it physical: a relation with coefficient 0.83 is a correlation, a relation
with coefficient 1 is a statement that vehicles are conserved.

Validation is against the MIDAS-derived nodes from Phase 1, which the search never sees.
"""

import itertools
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import dataset
import evaluate

RESULTS = os.path.join(ROOT, "results")


def _omp_support(target, library, max_support):
    """Orthogonal matching pursuit: greedily pick columns that explain the target."""
    residual = target.copy()
    support = []
    for _ in range(max_support):
        scores = np.abs(library.T @ residual)
        scores[support] = -np.inf
        pick = int(np.argmax(scores))
        if not np.isfinite(scores[pick]):
            break
        support.append(pick)
        sub = library[:, support]
        coef, _, _, _ = np.linalg.lstsq(sub, target, rcond=None)
        residual = target - sub @ coef
    return support


def discover(volumes, observed, max_support=4, min_overlap=400,
             residual_tol_pct=4.0, round_tol=0.30, shortlist=12, enumerate_top=8):
    """Search for sparse signed conservation relations in the counts.

    residual_tol_pct - a relation is kept if its median absolute residual is within this
    percentage of the target detector's mean flow.
    round_tol - a fitted coefficient must lie within this distance of an integer in
    {-1, 0, +1} to be accepted, so near-misses are discarded rather than forced.
    shortlist - how many correlated detectors are considered per target.
    """
    n_sites = volumes.shape[0]
    found = []

    for target_row in range(n_sites):
        cols = observed[target_row].copy()
        if cols.sum() < min_overlap:
            continue

        # Shortlist by pairwise correlation before intersecting. Intersecting the
        # observed masks of every detector at once leaves almost nothing to fit on, so
        # the shortlist is built pairwise - where each candidate individually overlaps
        # the target - and only the shortlist is then intersected.
        scored = []
        for i in range(n_sites):
            if i == target_row:
                continue
            both = cols & observed[i]
            if both.sum() < min_overlap:
                continue
            a, b = volumes[target_row, both], volumes[i, both]
            if a.std() < 1e-9 or b.std() < 1e-9:
                continue
            scored.append((abs(float(np.corrcoef(a, b)[0, 1])), i))
        if len(scored) < 2:
            continue
        scored.sort(reverse=True)
        candidates = [i for _, i in scored[:shortlist]]

        shared = cols.copy()
        for i in candidates:
            shared &= observed[i]
        while shared.sum() < min_overlap and len(candidates) > 2:
            candidates = candidates[:-1]        # drop the weakest, recover intervals
            shared = cols.copy()
            for i in candidates:
                shared &= observed[i]
        if shared.sum() < min_overlap:
            continue

        target = volumes[target_row, shared]
        library = volumes[np.ix_(candidates, shared)].T
        mean_flow = float(target.mean())
        if mean_flow < 1:
            continue

        # Enumerate small subsets rather than taking a single greedy fit. Greedy pursuit
        # returns one explanation per detector, and for a mainline detector the best
        # single explanation is almost always the next mainline detector along, because
        # they correlate at r ~ 0.99. That systematically hides every relation involving
        # a slip road. Enumerating subsets finds those too, at trivial cost: the fits are
        # three columns wide.
        pool = list(range(min(enumerate_top, len(candidates))))
        for size in range(1, max_support + 1):
            for combo in itertools.combinations(pool, size):
                sub = library[:, list(combo)]
                coef, _, _, _ = np.linalg.lstsq(sub, target, rcond=None)

                rounded = np.round(coef)
                if np.max(np.abs(coef - rounded)) > round_tol:
                    continue
                if not np.all(np.isin(rounded, (-1.0, 0.0, 1.0))):
                    continue
                if np.count_nonzero(rounded) == 0:
                    continue

                residual = target - sub @ rounded
                median_abs = float(np.median(np.abs(residual)))
                if median_abs / mean_flow * 100.0 > residual_tol_pct:
                    continue

                relation = {target_row: 1}
                for k, c in zip(combo, rounded):
                    if c != 0:
                        relation[candidates[k]] = -int(c)
                if len(relation) < 2:
                    continue

                found.append({
                    "rows": {int(r): int(c) for r, c in relation.items()},
                    "intervals": int(shared.sum()),
                    "median_abs_residual": round(median_abs, 2),
                    "residual_pct_of_flow": round(median_abs / mean_flow * 100.0, 3),
                })

    return _dedupe(found)


def _dedupe(found):
    """Collapse relations that are the same law found from different starting points."""
    seen, out = set(), []
    for rel in found:
        rows = rel["rows"]
        key = tuple(sorted(rows.items()))
        flipped = tuple(sorted((r, -c) for r, c in rows.items()))
        if key in seen or flipped in seen:
            continue
        seen.add(key)
        out.append(rel)
    return out


def truth_relations(corridor, fitted):
    """The Phase 1 nodes, expressed in the same form, as ground truth."""
    truth = []
    for f in fitted:
        rel = {f["up"]: 1, f["down"]: -1}
        for row, sign in f["slips"]:
            if sign:
                rel[row] = rel.get(row, 0) + int(sign)
        truth.append({r: c for r, c in rel.items() if c != 0})
    return truth


def score(found, truth):
    """How many of the real conservation relations were recovered, and how cleanly."""
    def key(rows):
        items = tuple(sorted(rows.items()))
        flip = tuple(sorted((r, -c) for r, c in rows.items()))
        return min(items, flip)

    truth_keys = {key(t) for t in truth}
    found_keys = {key({int(r): int(c) for r, c in f["rows"].items()}) for f in found}

    exact = truth_keys & found_keys
    truth_sets = {frozenset(dict(k).keys()) for k in truth_keys}
    found_sets = {frozenset(dict(k).keys()) for k in found_keys}
    same_members = truth_sets & found_sets

    return {
        "relations_found": len(found_keys),
        "true_relations": len(truth_keys),
        "exact_matches": len(exact),
        "recall_exact": round(len(exact) / len(truth_keys), 3) if truth_keys else None,
        "precision_exact": round(len(exact) / len(found_keys), 3) if found_keys else None,
        "correct_detector_set_any_signs": len(same_members),
        "note": ("exact match understates recovery; a surveyed relation can be implied "
                 "by a combination of discovered ones without appearing verbatim - see "
                 "span_coverage"),
        "recall_detector_set": (round(len(same_members) / len(truth_sets), 3)
                                if truth_sets else None),
    }


def main(manifest="window.json"):
    corridor = dataset.load(manifest)
    fitted = evaluate.fit_node_signs(corridor)
    print("corridor %d sites x %d intervals; %d known nodes withheld from the search"
          % (corridor.shape[0], corridor.shape[1], len(fitted)))

    found = discover(corridor.volumes, corridor.observed)
    truth = truth_relations(corridor, fitted)
    result = score(found, truth)

    print("\nrecovered from the counts alone, with no map and no site names:")
    for k, v in result.items():
        print("  %-34s %s" % (k, v))

    if found:
        best = sorted(found, key=lambda f: f["residual_pct_of_flow"])[:5]
        print("\n  tightest relations found:")
        for f in best:
            terms = " ".join("%+d*d%d" % (c, r) for r, c in sorted(f["rows"].items()))
            print("    %-46s residual %5.2f%% of flow over %d intervals"
                  % (terms, f["residual_pct_of_flow"], f["intervals"]))

    out = {"manifest": manifest, "score": result, "relations": found}
    with open(os.path.join(RESULTS, "discovery.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/discovery.json")
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "window.json")


# --------------------------------------------------- the decisive experiment

def relations_to_fitted(relations, corridor):
    """Express discovered relations in the node form the reconciler consumes.

    Which detector is called "upstream" and which "downstream" is arbitrary here - the
    calibration step fits a coefficient on the downstream term anyway, so any consistent
    labelling of a signed relation works.
    """
    fitted = []
    for n, rel in enumerate(relations):
        rows = {int(r): int(c) for r, c in rel["rows"].items()}
        pos = [r for r, c in rows.items() if c > 0]
        neg = [r for r, c in rows.items() if c < 0]
        if not pos or not neg:
            continue
        up, down = pos[0], neg[0]
        slips = [(r, c) for r, c in rows.items() if r not in (up, down)]
        used = [up, down] + [r for r, _ in slips]
        complete = np.all(corridor.observed[used], axis=0)
        if complete.sum() < 100:
            continue
        fitted.append({
            "node_id": "discovered_%d" % n,
            "up": up, "down": down, "slips": slips,
            "baseline_residual": rel["median_abs_residual"],
            "mean_flow": round(float(corridor.volumes[down, complete].mean()), 1),
        })
    return fitted


def reconciliation_without_a_map(manifest="window.json", seed=0, max_run=96):
    """Reconcile using only what the counts revealed, and compare against using the map.

    Discovery runs on the training view alone, so relations are never learned from the
    values later used to score the reconstruction.
    """
    import baselines
    import constrained

    corridor = dataset.load(manifest)
    true_nodes = evaluate.fit_node_signs(corridor)
    hidden = dataset.make_mask(corridor, fraction=0.10, seed=seed, max_run=max_run)
    view = dataset.train_view(corridor, hidden)
    view_observed = ~np.isnan(view)
    slot, weekend = corridor.interval_index(), corridor.is_weekend()

    print("discovering relations from the training data only...")
    volumes_for_search = np.nan_to_num(view, nan=0.0)
    relations = discover(volumes_for_search, view_observed)
    discovered = relations_to_fitted(relations, corridor)
    print("  %d relations found, %d usable as constraints" % (len(relations), len(discovered)))

    prior = baselines.knn_spatial(view, slot, weekend)
    runs = evaluate.gap_run_lengths(hidden)

    out = {"manifest": manifest, "seed": seed,
           "true_nodes": len(true_nodes), "discovered_relations": len(discovered)}

    # everything is scored against the surveyed node list, so the two are comparable
    calib_true = constrained.calibrate(corridor, true_nodes, mode="scaled")

    for label, nodes in (("surveyed topology", true_nodes),
                         ("discovered topology", discovered)):
        filled, timing = constrained.reconstruct(corridor, view, nodes, prior)
        acc = evaluate.accuracy(corridor.volumes, filled, hidden, runs)
        feas = evaluate.feasibility(filled, true_nodes, calib_true, hidden)
        out[label] = {"MAE": acc["all"]["MAE"], "RMSE": acc["all"]["RMSE"],
                      "outside_band_pct": feas["outside_band_pct"],
                      "seconds": timing["seconds"]}
        print("  %-22s MAE %7.2f   outside band %6.2f%%"
              % (label, acc["all"]["MAE"], feas["outside_band_pct"]))

    acc0 = evaluate.accuracy(corridor.volumes, prior, hidden, runs)
    feas0 = evaluate.feasibility(prior, true_nodes, calib_true, hidden)
    out["no constraint"] = {"MAE": acc0["all"]["MAE"],
                            "outside_band_pct": feas0["outside_band_pct"]}
    print("  %-22s MAE %7.2f   outside band %6.2f%%"
          % ("no constraint", acc0["all"]["MAE"], feas0["outside_band_pct"]))

    with open(os.path.join(RESULTS, "discovery_reconciliation.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/discovery_reconciliation.json")
    return out


def span_coverage(found, truth, n_sites, tol=1e-6):
    """Fraction of surveyed relations lying in the span of the discovered ones.

    The right measure of recovery. Exact matching asks whether a surveyed relation was
    found verbatim, but the surveyed list is only one decomposition of the network's
    conservation structure. If a surveyed relation is a combination of relations that
    were discovered, the structure *was* recovered - it is simply written down in a
    different basis, and it constrains the reconstruction identically.
    """
    if not found:
        return {"covered": 0, "of": len(truth), "coverage": 0.0}

    matrix = np.zeros((len(found), n_sites))
    for i, rel in enumerate(found):
        for r, c in rel["rows"].items():
            matrix[i, int(r)] = float(c)

    covered = 0
    for t in truth:
        vec = np.zeros(n_sites)
        for r, c in t.items():
            vec[int(r)] = float(c)
        coef, _, _, _ = np.linalg.lstsq(matrix.T, vec, rcond=None)
        residual = float(np.linalg.norm(matrix.T @ coef - vec))
        if residual <= tol * max(1.0, float(np.linalg.norm(vec))):
            covered += 1

    return {"covered": covered, "of": len(truth),
            "coverage": round(covered / len(truth), 3) if truth else None}


def validity(found, noise_floor_pct=1.06):
    """Share of discovered relations that hold tighter than the measured noise floor.

    A relation holding to less than the detectors' own disagreement is a conservation law
    of the network, whether or not it appears on the surveyed list. This is the honest
    precision measure: it asks whether what was found is true, not whether it matches a
    list that was never complete.
    """
    if not found:
        return {"valid": 0, "of": 0, "share": None}
    tight = [f for f in found if f["residual_pct_of_flow"] <= noise_floor_pct]
    return {"valid": len(tight), "of": len(found),
            "share": round(len(tight) / len(found), 3),
            "noise_floor_pct": noise_floor_pct}
