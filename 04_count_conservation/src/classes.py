"""Vehicle-class-resolved conservation.

The detectors do not only count vehicles, they measure each vehicle's length and place
it in one of four bins. WebTRIS returns those four counts alongside the total, and the
four sum to the total (exactly, in 98.3% of records; the remainder differ by one vehicle
from rounding).

The physical point is simple and, unlike the total-flow identity, it cannot be argued
with: a car that enters a stretch of motorway does not leave it as a lorry. Vehicles are
conserved *within each length class independently*. So a node that previously supplied
one balance equation supplies four.

Four equations instead of one is not by itself a gain in determination, because the
unknowns multiply by four as well. The gain comes from composition. Each detector has
its own stable mix - a slip road serving a distribution park carries a far higher heavy
share than the mainline beside it - so the four class equations are not proportional to
one another across detectors. The class composition acts as a tracer. Where the total
balance alone leaves two missing detectors at a node underdetermined, the four class
balances can separate them, because the two detectors dilute the mix differently.

That is exactly the regime the total-only method was measured to be weakest in: its
accuracy gain decays as more data goes missing and the node systems become
underdetermined.

There is also a fault class that total-flow conservation is provably blind to. If a
detector's length classifier drifts and it books cars as vans, its total is unchanged by
construction, so no total-flow balance anywhere in the network can detect it. The class
balances detect it directly.

This module carries no new solver. It reuses the same calibration, the same tolerance
band derived from measured spread, and the same projection, applied per class, which is
the point: the constraint machinery is class-agnostic.
"""

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import dataset
import webtris

RESULTS = os.path.join(ROOT, "results")

# WebTRIS length bins, shortest first. These are the raw column names.
CLASS_COLUMNS = ["0 - 520 cm", "521 - 660 cm", "661 - 1160 cm", "1160+ cm"]
CLASS_NAMES = ["len_0_520", "len_521_660", "len_661_1160", "len_1160_plus"]


def load_series_by_class(site_id, start, end):
    """(date, interval) -> [c0, c1, c2, c3], or None where the record is missing.

    A missing record is missing in every class at once - verified over 20,000 records,
    the total and all four class counts are blank together, never separately. So the
    observed mask is shared and the class problem has exactly the same holes as the
    total problem.
    """
    rows = webtris.daily(site_id, start, end)
    series = {}
    for r in rows:
        key = (r["Report Date"][:10], int(r["Time Interval"]))
        vals = [r.get(c, "") for c in CLASS_COLUMNS]
        if any(v in ("", None) for v in vals):
            series[key] = None
        else:
            series[key] = [float(v) for v in vals]
    return series


class ClassCorridor(object):
    """A corridor resolved into vehicle length classes.

    `total` is the ordinary Corridor. `by_class` maps class name to a matrix with the
    same shape, the same rows in the same order, and the same observed mask.
    """

    def __init__(self, total, by_class):
        self.total = total
        self.by_class = by_class
        self.site_ids = total.site_ids
        self.keys = total.keys
        self.nodes = total.nodes
        self.row_of = total.row_of
        self.observed = total.observed

    @property
    def shape(self):
        return self.total.shape

    def view(self, name):
        """A single class as a Corridor, so the existing machinery accepts it unchanged."""
        return dataset.Corridor(self.by_class[name], self.observed,
                                self.site_ids, self.keys, self.nodes)


def load(manifest_name="window.json"):
    """Load the corridor and its four class matrices, aligned row for row."""
    total = dataset.load(manifest_name)
    with open(os.path.join(RESULTS, manifest_name), encoding="utf-8") as fh:
        win = json.load(fh)

    n_sites, n_cols = total.shape
    by_class = {name: np.full((n_sites, n_cols), np.nan) for name in CLASS_NAMES}

    for i, sid in enumerate(total.site_ids):
        s = load_series_by_class(sid, win["start"], win["end"])
        for j, k in enumerate(total.keys):
            v = s.get(k)
            if v is None:
                continue
            for c, name in enumerate(CLASS_NAMES):
                by_class[name][i, j] = v[c]

    return ClassCorridor(total, by_class)


def class_shares(cc):
    """Mean share of each class per detector, over the intervals it reported.

    This is the composition that makes the four balance equations independent across
    detectors. Reported so the claim that detectors differ in mix can be checked rather
    than asserted.
    """
    obs = cc.observed
    stack = np.stack([cc.by_class[n] for n in CLASS_NAMES])   # 4 x sites x intervals
    out = np.zeros((stack.shape[1], 4))
    for i in range(stack.shape[1]):
        if not obs[i].any():
            continue
        totals = stack[:, i, obs[i]].sum(axis=0)
        good = totals > 0
        if not good.any():
            continue
        out[i] = (stack[:, i, obs[i]][:, good] / totals[good]).mean(axis=1)
    return out


def composition_spread(cc, fitted):
    """How differently the detectors at a node are composed.

    For each node, the spread across its detectors of the heavy-vehicle share. A node
    whose detectors all carry the same mix gains nothing from the class equations; a node
    whose slip road carries a different mix gains the most. Measured, not assumed.
    """
    shares = class_shares(cc)
    heavy = shares[:, 2] + shares[:, 3]      # 661 cm and longer
    out = []
    for f in fitted:
        rows = [f["up"], f["down"]] + [r for r, _ in f["slips"]]
        vals = heavy[rows]
        vals = vals[vals > 0]
        if vals.size < 2:
            continue
        out.append({"node_id": f["node_id"],
                    "n_detectors": int(vals.size),
                    "heavy_share_min": round(float(vals.min()), 4),
                    "heavy_share_max": round(float(vals.max()), 4),
                    "heavy_share_spread": round(float(vals.max() - vals.min()), 4)})
    return out


def check_sums(cc, sample_rows=None):
    """Do the four classes add up to the total? Reported, because it bounds the method.

    Any systematic discrepancy here would propagate straight into a class-wise
    reconstruction, so it is measured rather than assumed away.
    """
    obs = cc.observed
    stack = sum(cc.by_class[n] for n in CLASS_NAMES)
    diff = stack[obs] - cc.total.volumes[obs]
    return {
        "records_checked": int(obs.sum()),
        "exact": int((np.abs(diff) < 1e-9).sum()),
        "exact_pct": round(100.0 * float((np.abs(diff) < 1e-9).mean()), 2),
        "max_abs_discrepancy": round(float(np.abs(diff).max()), 3),
        "mean_abs_discrepancy": round(float(np.abs(diff).mean()), 4),
    }


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window.json"
    cc = load(manifest)
    print("corridor %d sites x %d intervals" % cc.shape)
    print("class sums vs total:", check_sums(cc))

    shares = class_shares(cc)
    print("\nmean class share across detectors:")
    for c, name in enumerate(CLASS_NAMES):
        col = shares[:, c]
        col = col[col > 0]
        print("  %-16s mean %.4f   min %.4f   max %.4f"
              % (name, col.mean(), col.min(), col.max()))
