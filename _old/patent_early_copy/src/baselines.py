"""Phase 3 — the known methods of reconstructing missing traffic records.

These are the prior art. They are implemented carefully and given every reasonable
advantage, because an invention that only beats a strawman proves nothing, and a weak
comparison is the easiest thing in the world for an examiner or an evaluator to attack.

Each function takes the partially-observed matrix (nan where a value is not available to
the method) and returns a fully filled matrix of the same shape.
"""

import numpy as np


def _nan_to_row_mean(filled):
    """Last resort for cells no method could reach: that detector's own mean."""
    for i in range(filled.shape[0]):
        row = filled[i]
        bad = np.isnan(row)
        if bad.any():
            good = row[~bad]
            row[bad] = good.mean() if good.size else 0.0
    return filled


def historical_mean(view, slot, weekend):
    """Mean of the same detector at the same time-of-day slot on the same day type.

    The standard first-resort method: "what does this detector usually do at 4pm on a
    weekday?" Uses no information from any other detector.
    """
    out = view.copy()
    for i in range(view.shape[0]):
        for is_we in (False, True):
            for s in range(96):
                cols = np.where((slot == s) & (weekend == is_we))[0]
                if cols.size == 0:
                    continue
                vals = view[i, cols]
                good = vals[~np.isnan(vals)]
                if good.size == 0:
                    continue
                fill = good.mean()
                out[i, cols] = np.where(np.isnan(vals), fill, vals)
    return _nan_to_row_mean(out)


def linear_interpolation(view, slot, weekend):
    """Straight line between the last and next value the same detector reported.

    Strong on short gaps, which Phase 2 showed dominate. Gaps at the very start or end of
    the record have no value on one side, so they fall back to the historical mean.
    """
    out = view.copy()
    n_cols = view.shape[1]
    x = np.arange(n_cols)
    for i in range(view.shape[0]):
        row = out[i]
        good = ~np.isnan(row)
        if good.sum() >= 2:
            row[~good] = np.interp(x[~good], x[good], row[good])
        out[i] = row
    still_bad = np.isnan(out)
    if still_bad.any():
        hm = historical_mean(view, slot, weekend)
        out[still_bad] = hm[still_bad]
    return _nan_to_row_mean(out)


def knn_spatial(view, slot, weekend, k=5, min_overlap=200):
    """Borrow from the detectors that behave most like this one.

    For each pair of detectors a scale factor is learned on the intervals where both
    reported, so a small slip road can lend its shape to a busy mainline detector. The
    estimate is the median over the k most similar detectors that reported in that
    interval. This is the standard spatial-similarity approach, and it is the closest
    prior art in spirit: it uses the neighbours, but only as statistical company, with no
    physical relation forced between the values.
    """
    n_sites, n_cols = view.shape
    obs = ~np.isnan(view)

    corr = np.full((n_sites, n_sites), -np.inf)
    ratio = np.ones((n_sites, n_sites))
    for i in range(n_sites):
        for j in range(n_sites):
            if i == j:
                continue
            both = obs[i] & obs[j]
            if both.sum() < min_overlap:
                continue
            a, b = view[i, both], view[j, both]
            if a.std() < 1e-9 or b.std() < 1e-9:
                continue
            corr[i, j] = np.corrcoef(a, b)[0, 1]
            denom = b.mean()
            ratio[i, j] = (a.mean() / denom) if denom > 1e-9 else 1.0

    out = view.copy()
    for i in range(n_sites):
        neighbours = np.argsort(-corr[i])
        neighbours = [j for j in neighbours if np.isfinite(corr[i, j])][:k]
        if not neighbours:
            continue
        missing_cols = np.where(np.isnan(view[i]))[0]
        for c in missing_cols:
            ests = [view[j, c] * ratio[i, j] for j in neighbours if obs[j, c]]
            if ests:
                out[i, c] = float(np.median(ests))

    still_bad = np.isnan(out)
    if still_bad.any():
        hm = historical_mean(view, slot, weekend)
        out[still_bad] = hm[still_bad]
    return _nan_to_row_mean(out)


def soft_impute(view, slot, weekend, rank=8, iters=60, shrink=0.02):
    """Low-rank matrix completion by iterative soft-thresholded SVD.

    The standard academic method for this problem. It exploits the fact that a
    detectors-by-intervals matrix is close to low rank, because traffic patterns repeat.
    Like the others it imposes no physical relation between the reconstructed values; the
    structure it finds is purely statistical.
    """
    obs = ~np.isnan(view)
    filled = historical_mean(view, slot, weekend)  # sensible starting point

    row_mean = filled.mean(axis=1, keepdims=True)
    row_std = filled.std(axis=1, keepdims=True)
    row_std[row_std < 1e-9] = 1.0

    z = (filled - row_mean) / row_std
    target = (view - row_mean) / row_std

    for _ in range(iters):
        u, s, vt = np.linalg.svd(z, full_matrices=False)
        thresh = shrink * s[0] if s.size else 0.0
        s_shrunk = np.maximum(s - thresh, 0.0)
        s_shrunk[rank:] = 0.0
        z_new = (u * s_shrunk) @ vt
        z = np.where(obs, target, z_new)

    out = z * row_std + row_mean
    out = np.where(obs, view, out)
    return _nan_to_row_mean(np.maximum(out, 0.0))


METHODS = {
    "historical_mean": historical_mean,
    "linear_interpolation": linear_interpolation,
    "knn_spatial": knn_spatial,
    "soft_impute": soft_impute,
}
