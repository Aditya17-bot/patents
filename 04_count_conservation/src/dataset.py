"""Load a corridor month into matrix form, and mask values realistically for testing.

The matrix is sites x intervals. `observed` marks where the detector actually reported.
Evaluation works by hiding some of the *observed* values, asking a method to reconstruct
them, and comparing against what was hidden.

Masking deliberately reproduces the gap shape measured in Phase 2 rather than knocking
out values uniformly at random. Real gaps arrive as runs: a detector drops out and stays
out for a while. Uniform random masking would leave a live neighbour on both sides of
almost every hole, which flatters temporal interpolation enormously and would make the
comparison dishonest.
"""

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import phase2

RESULTS = os.path.join(ROOT, "results")


class Corridor(object):
    def __init__(self, volumes, observed, site_ids, keys, nodes):
        self.volumes = volumes        # float array, sites x intervals (nan where absent)
        self.observed = observed      # bool array, True where the detector reported
        self.site_ids = site_ids
        self.keys = keys              # list of (date, interval_index)
        self.nodes = nodes
        self.row_of = {sid: i for i, sid in enumerate(site_ids)}

    @property
    def shape(self):
        return self.volumes.shape

    def interval_index(self):
        """Time-of-day slot 0..95 for each column."""
        return np.array([k[1] for k in self.keys])

    def is_weekend(self):
        import datetime
        out = []
        for date, _ in self.keys:
            y, m, d = (int(x) for x in date.split("-"))
            out.append(datetime.date(y, m, d).weekday() >= 5)
        return np.array(out)


def load(manifest_name="window.json", drop_dead=True):
    with open(os.path.join(RESULTS, manifest_name), encoding="utf-8") as fh:
        win = json.load(fh)
    node_file = "nodes_%s_%s.json" % (win["road"], win["carriageway"])
    with open(os.path.join(RESULTS, node_file), encoding="utf-8") as fh:
        all_nodes = {n["node_id"]: n for n in json.load(fh)["nodes"]}

    series = {sid: phase2.load_series(sid, win["start"], win["end"])
              for sid in win["site_ids"]}
    keys = sorted({k for s in series.values() for k in s})

    site_ids = list(win["site_ids"])
    if drop_dead:
        site_ids = [sid for sid in site_ids
                    if any(v is not None for v in series[sid].values())]

    volumes = np.full((len(site_ids), len(keys)), np.nan)
    for i, sid in enumerate(site_ids):
        s = series[sid]
        for j, k in enumerate(keys):
            v = s.get(k)
            if v is not None:
                volumes[i, j] = v
    observed = ~np.isnan(volumes)

    live = set(site_ids)
    nodes = []
    for nid in win["node_ids"]:
        n = all_nodes[nid]
        if n["upstream"]["id"] not in live or n["downstream"]["id"] not in live:
            continue
        if any(s["id"] not in live for s in n["slips"]):
            continue
        nodes.append(n)

    return Corridor(volumes, observed, site_ids, keys, nodes)


def measured_run_lengths(observed):
    """Run lengths of the real gaps, to be resampled when masking."""
    runs = []
    for row in observed:
        run = 0
        for ok in row:
            if not ok:
                run += 1
            elif run:
                runs.append(run)
                run = 0
        if run:
            runs.append(run)
    return runs or [1]


def make_mask(corridor, fraction=0.10, seed=0, max_run=None):
    """Hide `fraction` of observed values as runs drawn from the measured gap shape.

    Returns a bool array, True where a value has been hidden for testing. Hidden values
    are only ever taken from cells the detector actually reported, so ground truth for
    every hidden cell is known.

    `max_run` caps the length of gap that may be drawn. The measured distribution mixes
    two physically different populations: short operational dropouts, and detectors that
    have simply died and stay dead for weeks. Sampling from the raw distribution lets the
    dead-detector runs dominate the cell count and drowns out the operational regime, so
    both regimes are reported separately rather than blended into one misleading average.
    """
    rng = np.random.default_rng(seed)
    runs = measured_run_lengths(corridor.observed)
    if max_run is not None:
        runs = [r for r in runs if r <= max_run] or [1]
    n_sites, n_intervals = corridor.shape

    target = int(fraction * corridor.observed.sum())
    hidden = np.zeros_like(corridor.observed)

    guard = 0
    while hidden.sum() < target and guard < target * 50:
        guard += 1
        length = int(runs[rng.integers(len(runs))])
        length = min(length, n_intervals)
        row = int(rng.integers(n_sites))
        start = int(rng.integers(max(1, n_intervals - length)))
        block = slice(start, start + length)
        # only hide cells that were genuinely observed, and never blank a whole row
        candidate = corridor.observed[row, block] & ~hidden[row, block]
        if not candidate.any():
            continue
        would_hide = hidden[row].sum() + candidate.sum()
        if would_hide > 0.6 * corridor.observed[row].sum():
            continue
        hidden[row, block] |= candidate
    return hidden


def train_view(corridor, hidden):
    """The array a method is allowed to see: observed values minus the hidden ones."""
    view = corridor.volumes.copy()
    view[hidden] = np.nan
    return view
