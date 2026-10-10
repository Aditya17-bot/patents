"""
E3 operating envelope -- at what event amplitude and event count does the
cross-station coupling channel stop working?

The factorial (e3_repeat.py) established WHICH configuration detects. It ran at
one operating point: pulse amplitude 0.15 of channel range, 8 of 38 channels,
60 events over 7,107 intervals. A single operating point is not an envelope,
and Section 8.1 of the disclosure needs an envelope.

Swept, at the winning cell only (per-station models, raw across-station median
reference, scenario D = coupled pair plus a simultaneous venue-wide event):

  amplitude   fraction of the [0,1] channel range added at each event
  event count how many coupled exchanges occur in the observation window

Reported per point over N_TRIALS resampled pairs and injections:
  detection rate (coupled pair ranked first of 55), AUROC over pairs, median z.
"""

import json
import os
import sys
import time

import numpy as np
import torch

from e3_smd import CALIB_FRAC, OUT, W, Predictor, entities, load, residuals, windowize
from e3_coupling import (COUPLE_LAG, N_CH, apply_pulses, pair_couplings,
                         reference_reject, separation)
from e3_repeat import auroc_over_pairs, load_models

N_TRIALS = int(os.environ.get("E3_TRIALS", 20))
AMP_SWEEP = [0.02, 0.04, 0.06, 0.10, 0.15, 0.25]
EVENT_SWEEP = [10, 20, 40, 60, 90]
BASE_AMP = 0.15
BASE_EVENTS = 60
COND, RULE = "per_station", "raw_median"


def main():
    t0 = time.time()
    _, holdout = entities()
    shared, local = load_models(holdout)

    clean, calib = {}, {}
    for n in holdout:
        tr, _, _ = load(n)
        clean[n] = tr[int(len(tr) * CALIB_FRAC):]
        Xc, Yc = windowize(tr[:int(len(tr) * CALIB_FRAC)])
        r = residuals(local[n], Xc, Yc)
        calib[n] = (float(r.mean()), float(r.std()) or 1.0)
    L = min(len(v) for v in clean.values())
    clean = {n: v[:L] for n, v in clean.items()}
    print("%d stations, %d intervals, %d pairs, %d trials/point"
          % (len(holdout), L, len(holdout) * (len(holdout) - 1) // 2, N_TRIALS),
          flush=True)

    def point(amp, n_events):
        rows = []
        for t in range(N_TRIALS):
            rng = np.random.default_rng(9000 + t)
            i, j = rng.choice(len(holdout), size=2, replace=False)
            pair = tuple(sorted((holdout[i], holdout[j])))
            ev = np.sort(rng.choice(np.arange(50, L - 50), size=n_events, replace=False))
            cm = np.sort(rng.choice(np.arange(50, L - 50), size=n_events, replace=False))
            ch = rng.choice(38, size=N_CH, replace=False)
            sig = {n: apply_pulses(clean[n], cm, ch, amp) for n in holdout}
            sig[pair[0]] = apply_pulses(sig[pair[0]], ev, ch, amp)
            sig[pair[1]] = apply_pulses(sig[pair[1]], ev + COUPLE_LAG, ch, amp)
            R = {}
            for n in holdout:
                X, Y = windowize(sig[n])
                R[n] = residuals(local[n], X, Y)
            Ln = min(len(v) for v in R.values())
            R = {n: v[:Ln] for n, v in R.items()}
            cp = pair_couplings(reference_reject(R, holdout, RULE, calib), holdout)
            sep = separation(cp, pair)
            rows.append((sep["top_ranked"], sep["z_over_uncoupled"],
                         auroc_over_pairs(cp, pair), sep["target_r"]))
        z = np.array([r[1] for r in rows if r[1] is not None])
        return {
            "detection_rate_top_ranked": float(np.mean([r[0] for r in rows])),
            "auroc_over_pairs_mean": float(np.mean([r[2] for r in rows])),
            "z_median": float(np.median(z)),
            "target_r_median": float(np.median([r[3] for r in rows])),
        }

    out = {"config": dict(n_trials=N_TRIALS, model=COND, rule=RULE,
                          scenario="D_both", couple_lag=COUPLE_LAG,
                          n_channels=N_CH, base_amp=BASE_AMP,
                          base_events=BASE_EVENTS,
                          corpus="SMD group 3, MIT licence"),
           "amplitude_sweep": {}, "event_count_sweep": {}}

    print("\namplitude sweep (%d events fixed)" % BASE_EVENTS, flush=True)
    print("%8s %10s %10s %8s %10s" % ("amp", "detect", "AUROC", "z med", "target r"))
    for a in AMP_SWEEP:
        p = point(a, BASE_EVENTS)
        out["amplitude_sweep"][str(a)] = p
        print("%8.3f %10.2f %10.3f %8.2f %10.3f"
              % (a, p["detection_rate_top_ranked"], p["auroc_over_pairs_mean"],
                 p["z_median"], p["target_r_median"]), flush=True)

    print("\nevent-count sweep (amplitude %.2f fixed)" % BASE_AMP, flush=True)
    print("%8s %10s %10s %8s %10s" % ("events", "detect", "AUROC", "z med", "target r"))
    for e in EVENT_SWEEP:
        p = point(BASE_AMP, e)
        out["event_count_sweep"][str(e)] = p
        print("%8d %10.2f %10.3f %8.2f %10.3f"
              % (e, p["detection_rate_top_ranked"], p["auroc_over_pairs_mean"],
                 p["z_median"], p["target_r_median"]), flush=True)

    out["runtime_s"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, "e3_envelope.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nruntime %s s -> results/e3_envelope.json" % out["runtime_s"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
