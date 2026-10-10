"""
E3 repetition -- the single-trial result in e3_coupling.py is n = 1 (one injected
pair, one seed) and nothing from it is quotable until it is repeated.

This script repeats the operating case over many randomly chosen station pairs
and injection seeds, and reports distributions rather than point values:

  * detection rate  -- in how many trials is the genuinely coupled pair ranked
                       first out of all 55 station pairs
  * AUROC over pairs -- how well the coupling statistic ranks the one coupled
                       pair against the 54 uncoupled ones, averaged over trials
  * z over uncoupled -- separation of the coupled pair from the uncoupled
                       population, median and inter-quartile range

Factorial retained from e3_coupling.py:
  model condition   shared | per_station
  reference rule    none | raw_median | standardised_median
  scenario          C_pair_only | D_both  (D adds a simultaneous venue-wide event)

Also re-runs the station clock-skew sweep on the cell where the signal actually
exists, rather than on an assumed one. The first sweep was run on the shared
model, which the factorial then showed to be the weakest cell, so it measured
degradation of something that was not detecting in the first place.

Models are loaded from the caches written by e3_coupling.py, so every trial uses
the identical shared and per-station predictors. Only the injection changes.
"""

import json
import os
import sys
import time

import numpy as np
import torch

from e3_smd import CALIB_FRAC, OUT, W, Predictor, entities, load, residuals, windowize
from e3_coupling import (AMP, COUPLE_LAG, LAG_MAX, N_CH, N_EVENTS, RULES,
                         apply_pulses, pair_couplings, reference_reject,
                         separation)

N_TRIALS = int(os.environ.get("E3_TRIALS", 20))
SKEW_SWEEP = [0, 1, 2, 3, 4, 6, 8]
SHARED_CACHE = os.path.join(OUT, "shared_model.pt")
LOCAL_CACHE = os.path.join(OUT, "local_models.pt")


def load_models(holdout):
    d_in, d_out = W * 38, 38
    sh = Predictor(d_in, d_out)
    sh.load_state_dict(torch.load(SHARED_CACHE, map_location="cpu"))
    sh.eval()
    sd = torch.load(LOCAL_CACHE, map_location="cpu")
    loc = {}
    for n in holdout:
        m = Predictor(d_in, d_out)
        m.load_state_dict(sd[n])
        m.eval()
        loc[n] = m
    return sh, loc


def field(cond, shared, local, sig, holdout):
    R = {}
    for n in holdout:
        X, Y = windowize(sig[n])
        R[n] = residuals(shared if cond == "shared" else local[n], X, Y)
    L = min(len(v) for v in R.values())
    return {n: v[:L] for n, v in R.items()}


def auroc_over_pairs(couplings, target):
    """rank the one coupled pair against all uncoupled pairs."""
    tgt = couplings[target]
    others = np.array([v for k, v in couplings.items() if k != target])
    return float((others < tgt).mean() + 0.5 * (others == tgt).mean())


def main():
    t0 = time.time()
    _, holdout = entities()
    shared, local = load_models(holdout)

    clean = {}
    for n in holdout:
        tr, _, _ = load(n)
        clean[n] = tr[int(len(tr) * CALIB_FRAC):]
    L = min(len(v) for v in clean.values())
    clean = {n: v[:L] for n, v in clean.items()}
    n_pairs = len(holdout) * (len(holdout) - 1) // 2
    print("%d stations, %d intervals, %d pairs, %d trials"
          % (len(holdout), L, n_pairs, N_TRIALS), flush=True)

    calib = {}
    for cond in ("shared", "per_station"):
        calib[cond] = {}
        for n in holdout:
            tr, _, _ = load(n)
            Xc, Yc = windowize(tr[:int(len(tr) * CALIB_FRAC)])
            r = residuals(shared if cond == "shared" else local[n], Xc, Yc)
            calib[cond][n] = (float(r.mean()), float(r.std()) or 1.0)

    cells = {}
    for sc in ("C_pair_only", "D_both"):
        for cond in ("shared", "per_station"):
            for rule in RULES:
                cells["%s|%s|%s" % (sc, cond, rule)] = []

    for t in range(N_TRIALS):
        rng = np.random.default_rng(1000 + t)
        i, j = rng.choice(len(holdout), size=2, replace=False)
        pair = tuple(sorted((holdout[i], holdout[j])))
        ev = np.sort(rng.choice(np.arange(50, L - 50), size=N_EVENTS, replace=False))
        cm = np.sort(rng.choice(np.arange(50, L - 50), size=N_EVENTS, replace=False))
        ch = rng.choice(38, size=N_CH, replace=False)

        sig_c = {n: clean[n].copy() for n in holdout}
        sig_c[pair[0]] = apply_pulses(clean[pair[0]], ev, ch)
        sig_c[pair[1]] = apply_pulses(clean[pair[1]], ev + COUPLE_LAG, ch)

        sig_d = {n: apply_pulses(clean[n], cm, ch) for n in holdout}
        sig_d[pair[0]] = apply_pulses(sig_d[pair[0]], ev, ch)
        sig_d[pair[1]] = apply_pulses(sig_d[pair[1]], ev + COUPLE_LAG, ch)

        for sc, sig in (("C_pair_only", sig_c), ("D_both", sig_d)):
            for cond in ("shared", "per_station"):
                R = field(cond, shared, local, sig, holdout)
                for rule in RULES:
                    cp = pair_couplings(
                        reference_reject(R, holdout, rule, calib[cond]), holdout)
                    sep = separation(cp, pair)
                    v = np.array(list(cp.values()))
                    cells["%s|%s|%s" % (sc, cond, rule)].append({
                        "trial": t, "pair": list(pair),
                        "top_ranked": sep["top_ranked"],
                        "z": sep["z_over_uncoupled"],
                        "target_r": sep["target_r"],
                        "mean_r": float(v.mean()),
                        "auroc_pairs": auroc_over_pairs(cp, pair),
                    })
        print("  trial %2d/%d  pair %s-%s" % (t + 1, N_TRIALS, pair[0], pair[1]),
              flush=True)

    summary = {}
    for k, rows in cells.items():
        z = np.array([r["z"] for r in rows if r["z"] is not None])
        a = np.array([r["auroc_pairs"] for r in rows])
        summary[k] = {
            "n_trials": len(rows),
            "detection_rate_top_ranked": float(np.mean([r["top_ranked"] for r in rows])),
            "auroc_over_pairs_mean": float(a.mean()),
            "auroc_over_pairs_median": float(np.median(a)),
            "z_median": float(np.median(z)),
            "z_p25": float(np.quantile(z, 0.25)),
            "z_p75": float(np.quantile(z, 0.75)),
            "target_r_median": float(np.median([r["target_r"] for r in rows])),
            "uncoupled_mean_r_median": float(np.median([r["mean_r"] for r in rows])),
        }

    # ---- skew sweep on the best cell, chosen from the data ---------------
    best = max((k for k in summary if k.startswith("D_both")),
               key=lambda k: (summary[k]["detection_rate_top_ranked"],
                              summary[k]["auroc_over_pairs_mean"]))
    _, best_cond, best_rule = best.split("|")
    print("\n[skew] best D_both cell = %s / %s -- sweeping on it"
          % (best_cond, best_rule), flush=True)

    sweep = {}
    for s in SKEW_SWEEP:
        rows = []
        for t in range(N_TRIALS):
            rng = np.random.default_rng(5000 + t)
            i, j = rng.choice(len(holdout), size=2, replace=False)
            pair = tuple(sorted((holdout[i], holdout[j])))
            ev = np.sort(rng.choice(np.arange(50, L - 60), size=N_EVENTS, replace=False))
            cm = np.sort(rng.choice(np.arange(50, L - 60), size=N_EVENTS, replace=False))
            ch = rng.choice(38, size=N_CH, replace=False)
            sig = {}
            for n in holdout:
                o = int(rng.integers(-s, s + 1)) if s > 0 else 0
                b = cm + o
                sig[n] = apply_pulses(clean[n], b[(b >= 0) & (b < L)], ch)
            oa = int(rng.integers(-s, s + 1)) if s > 0 else 0
            ob = int(rng.integers(-s, s + 1)) if s > 0 else 0
            ea, eb = ev + oa, ev + COUPLE_LAG + ob
            sig[pair[0]] = apply_pulses(sig[pair[0]], ea[(ea >= 0) & (ea < L)], ch)
            sig[pair[1]] = apply_pulses(sig[pair[1]], eb[(eb >= 0) & (eb < L)], ch)
            R = field(best_cond, shared, local, sig, holdout)
            cp = pair_couplings(
                reference_reject(R, holdout, best_rule, calib[best_cond]), holdout)
            sep = separation(cp, pair)
            rows.append((sep["top_ranked"], sep["z_over_uncoupled"],
                         auroc_over_pairs(cp, pair)))
        det = float(np.mean([r[0] for r in rows]))
        zz = np.array([r[1] for r in rows if r[1] is not None])
        au = float(np.mean([r[2] for r in rows]))
        sweep[str(s)] = {"detection_rate_top_ranked": det,
                         "z_median": float(np.median(zz)),
                         "auroc_over_pairs_mean": au}
        print("  skew +-%d intervals: detection %.2f  z %.2f  AUROC %.3f"
              % (s, det, np.median(zz), au), flush=True)

    out = {
        "config": dict(n_trials=N_TRIALS, stations=holdout, n_pairs=n_pairs,
                       couple_lag=COUPLE_LAG, n_events=N_EVENTS, amp=AMP,
                       n_channels=N_CH, lag_max=LAG_MAX,
                       corpus="SMD group 3, MIT licence",
                       units="lags in reporting intervals (SMD = 1 min/sample)",
                       note="pairs and injection resampled per trial; models fixed"),
        "summary": summary,
        "trials": cells,
        "best_cell": best,
        "skew_sweep": sweep,
        "runtime_s": round(time.time() - t0, 1),
    }
    with open(os.path.join(OUT, "e3_repeat.json"), "w") as f:
        json.dump(out, f, indent=2)

    print("\n================= E3 REPEATED, n = %d TRIALS =================" % N_TRIALS)
    print("%-14s %-22s %10s %10s %9s" % ("model", "reference rule", "detect", "AUROC", "z med"))
    for sc in ("C_pair_only", "D_both"):
        print("-- %s" % sc)
        for cond in ("shared", "per_station"):
            for rule in RULES:
                s = summary["%s|%s|%s" % (sc, cond, rule)]
                print("%-14s %-22s %10.2f %10.3f %9.2f"
                      % (cond, rule, s["detection_rate_top_ranked"],
                         s["auroc_over_pairs_mean"], s["z_median"]))
    print("\nruntime %s s -> results/e3_repeat.json" % out["runtime_s"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
