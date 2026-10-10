"""
E3(ii) and E3(iii) -- common-mode rejection and lagged cross-station coupling,
run as a factorial so that the disclosure's synergy argument is actually tested
rather than assumed.

Background. E3(i) (e3_smd.py) tested whether ONE shared normal-only model makes
raw residual MAGNITUDES commensurable across stations. It does not: on SMD the
shared model transferred thresholds WORSE than per-station models. So the
question this script asks is the one that survives that result --

  Where, if anywhere, does sharing the model actually buy something?

Two candidate answers, and they are separable:

  (1) The cross-station coupling statistic. Pearson correlation is invariant to
      per-station affine rescaling, so on its face coupling needs no
      commensurability at all. If that holds, Sec 4.1(e)'s synergy argument as
      written is too strong and must be narrowed.

  (2) The common-mode reference. Forming a reference ACROSS stations -- a
      median of the residual field at each timestep -- is NOT scale invariant.
      Subtracting the median of incommensurable residuals suppresses whichever
      station happens to have the largest residual scale, not the venue-wide
      event. If sharing helps anywhere, it should help here.

Factorial
  model condition   shared | per_station
  reference rule    none | raw_median | standardised_median
  scenario          A baseline, B common-mode only, C pair only, D both

  standardised_median applies the per-venue label-free calibration the
  disclosure already claims (standardise each station against its own normal
  calibration split) BEFORE forming the reference. Included because if
  calibration alone recovers the benefit, then the benefit is attributable to
  calibration and not to model sharing, and the claim must say so.

Corpus
  SMD held-out group 3 (11 entities), MIT licence. Shared model trained on
  groups 1 and 2 only. Per-station models trained on each held-out entity's own
  calibration normals. Identical architecture, optimiser and epochs in both.

Perturbations are injected into the RAW channel signal before the predictor,
never into the residual.

Units. SMD samples once per minute, so lags are in REPORTING INTERVALS, not
seconds. The disclosure's 1-3 s coupling lag maps to 1-3 intervals at a 1 Hz
station reporting rate. The mechanism is rate-agnostic; the corpus fixes only
the interval length. Stated in the results file.
"""

import json
import os
import sys
import time

import numpy as np
import torch

from e3_smd import (CALIB_FRAC, OUT, SEED, W, Predictor, entities, fit, load,
                    residuals, windowize)

LAG_MAX = 6            # reporting intervals searched in each direction
N_EVENTS = 60          # injected events per condition
PULSE_SD = 2.0         # Gaussian pulse width, intervals
AMP = 0.15             # pulse amplitude, in units of the [0,1] channel range
N_CH = 8               # channels perturbed per event (of 38)
COUPLE_LAG = 2         # lag of the genuinely coupled pair, intervals
JITTER_SWEEP = [0, 1, 2, 3, 5, 8]
RNG = np.random.default_rng(12345)

SHARED_CACHE = os.path.join(OUT, "shared_model.pt")
LOCAL_CACHE = os.path.join(OUT, "local_models.pt")
RULES = ("none", "raw_median", "standardised_median")


# ---------------------------------------------------------------- models ---

def get_models(train_group, holdout, store):
    d_in, d_out = W * 38, 38
    if os.path.exists(SHARED_CACHE):
        shared = Predictor(d_in, d_out)
        shared.load_state_dict(torch.load(SHARED_CACHE, map_location="cpu"))
        shared.eval()
        print("[shared] cached", flush=True)
    else:
        print("[shared] training on groups 1+2 ...", flush=True)
        Xs, Ys = [], []
        for n in train_group:
            tr, _, _ = load(n)
            a, b = windowize(tr)
            Xs.append(a)
            Ys.append(b)
        shared = fit(np.concatenate(Xs, 0), np.concatenate(Ys, 0), SEED, tag="shared")
        torch.save(shared.state_dict(), SHARED_CACHE)

    local = {}
    if os.path.exists(LOCAL_CACHE):
        sd = torch.load(LOCAL_CACHE, map_location="cpu")
        for n in holdout:
            m = Predictor(d_in, d_out)
            m.load_state_dict(sd[n])
            m.eval()
            local[n] = m
        print("[per-station] cached", flush=True)
    else:
        print("[per-station] training one model per held-out station ...", flush=True)
        for k, n in enumerate(holdout):
            local[n] = fit(store[n]["Xc"], store[n]["Yc"], SEED + 100 + k)
            print("    fitted %s" % n, flush=True)
        torch.save({n: local[n].state_dict() for n in holdout}, LOCAL_CACHE)
    return shared, local


# ----------------------------------------------------------- injection ----

def pulse_train(L, times, sd=PULSE_SD):
    t = np.arange(L, dtype=np.float32)
    s = np.zeros(L, dtype=np.float32)
    for c in times:
        s += np.exp(-0.5 * ((t - c) / sd) ** 2).astype(np.float32)
    return np.clip(s, 0.0, 1.0)


def apply_pulses(x, times, channels, amp=AMP):
    y = x.copy()
    p = pulse_train(len(x), times)
    for c in channels:
        y[:, c] = np.clip(y[:, c] + amp * p, 0.0, 1.0)
    return y


# ------------------------------------------------------------ coupling ----

def zscore(a):
    s = a.std()
    return (a - a.mean()) / (s if s > 1e-12 else 1.0)


def max_lagged_corr(a, b, lag_max=LAG_MAX):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    n = len(a)
    best = -1.0
    for lag in range(-lag_max, lag_max + 1):
        if lag >= 0:
            u, v = a[:n - lag], b[lag:]
        else:
            u, v = a[-lag:], b[:n + lag]
        if len(u) < 32:
            continue
        r = float(np.dot(zscore(u), zscore(v)) / len(u))
        if r > best:
            best = r
    return best


def pair_couplings(R, names):
    out = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            out[(a, b)] = max_lagged_corr(R[a], R[b])
    return out


def reference_reject(R, names, rule, calib_stats):
    """remove the across-station common component under the named rule."""
    if rule == "none":
        return dict(R)
    if rule == "raw_median":
        M = np.vstack([R[n] for n in names])
        ref = np.median(M, axis=0)
        return {n: R[n] - ref for n in names}
    if rule == "standardised_median":
        Z = {n: (R[n] - calib_stats[n][0]) / calib_stats[n][1] for n in names}
        ref = np.median(np.vstack([Z[n] for n in names]), axis=0)
        return {n: Z[n] - ref for n in names}
    raise ValueError(rule)


def separation(couplings, target_pair):
    tgt = couplings[target_pair]
    others = np.array([v for k, v in couplings.items() if k != target_pair])
    mu, sd = others.mean(), others.std()
    return {
        "target_r": float(tgt),
        "others_mean_r": float(mu),
        "others_max_r": float(others.max()),
        "z_over_uncoupled": float((tgt - mu) / sd) if sd > 1e-12 else None,
        "n_uncoupled_pairs_above": int((others >= tgt).sum()),
        "top_ranked": bool((others >= tgt).sum() == 0),
        "margin_over_next": float(tgt - others.max()),
    }


# ------------------------------------------------------------- driver -----

def field(model_cond, shared, local, sig, holdout):
    R = {}
    for n in holdout:
        X, Y = windowize(sig[n])
        m = shared if model_cond == "shared" else local[n]
        R[n] = residuals(m, X, Y)
    L = min(len(v) for v in R.values())
    return {n: v[:L] for n, v in R.items()}


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    train_group, holdout = entities()

    store, clean = {}, {}
    for n in holdout:
        tr, _, _ = load(n)
        cut = int(len(tr) * CALIB_FRAC)
        Xc, Yc = windowize(tr[:cut])
        store[n] = dict(Xc=Xc, Yc=Yc)
        clean[n] = tr[cut:]
    L = min(len(v) for v in clean.values())
    clean = {n: v[:L] for n, v in clean.items()}

    shared, local = get_models(train_group, holdout, store)

    # per-station calibration statistics, from each station's OWN normals,
    # under each model condition. This is the label-free per-venue calibration.
    calib = {}
    for cond in ("shared", "per_station"):
        calib[cond] = {}
        for n in holdout:
            m = shared if cond == "shared" else local[n]
            r = residuals(m, store[n]["Xc"], store[n]["Yc"])
            calib[cond][n] = (float(r.mean()), float(r.std()) or 1.0)

    events = np.sort(RNG.choice(np.arange(50, L - 50), size=N_EVENTS, replace=False))
    cm_ev = np.sort(RNG.choice(np.arange(50, L - 50), size=N_EVENTS, replace=False))
    channels = RNG.choice(38, size=N_CH, replace=False)
    pair = (holdout[0], holdout[1])
    print("\n%d held-out stations, %d common normal intervals each" % (len(holdout), L))
    print("injected pair %s <-> %s at lag %d intervals\n" % (pair[0], pair[1], COUPLE_LAG),
          flush=True)

    # ---- scenarios, as raw signal fields -------------------------------
    scen = {}
    scen["A_baseline"] = {n: clean[n] for n in holdout}
    scen["B_common_mode_only"] = {n: apply_pulses(clean[n], cm_ev, channels)
                                  for n in holdout}
    s = {n: clean[n].copy() for n in holdout}
    s[pair[0]] = apply_pulses(clean[pair[0]], events, channels)
    s[pair[1]] = apply_pulses(clean[pair[1]], events + COUPLE_LAG, channels)
    scen["C_pair_only"] = s
    s = {n: apply_pulses(clean[n], cm_ev, channels) for n in holdout}
    s[pair[0]] = apply_pulses(s[pair[0]], events, channels)
    s[pair[1]] = apply_pulses(s[pair[1]], events + COUPLE_LAG, channels)
    scen["D_both"] = s

    results = {
        "config": dict(lag_max=LAG_MAX, n_events=N_EVENTS, pulse_sd=PULSE_SD,
                       amp=AMP, n_channels=N_CH, couple_lag=COUPLE_LAG,
                       stations=holdout, injected_pair=list(pair),
                       common_length=int(L), n_pairs=len(holdout) * (len(holdout) - 1) // 2,
                       corpus="SMD group 3, MIT licence",
                       units="lags in reporting intervals (SMD = 1 min/sample)",
                       rules=list(RULES)),
        "cells": {},
    }

    print("%-20s %-14s %-22s %9s %9s %8s %7s"
          % ("scenario", "model", "reference rule", "mean r", "target r", "z", "top"))
    print("-" * 96)
    for sname, sig in scen.items():
        for cond in ("shared", "per_station"):
            R = field(cond, shared, local, sig, holdout)
            for rule in RULES:
                Rr = reference_reject(R, holdout, rule, calib[cond])
                cp = pair_couplings(Rr, holdout)
                v = np.array(list(cp.values()))
                sep = separation(cp, pair)
                key = "%s|%s|%s" % (sname, cond, rule)
                results["cells"][key] = {
                    "scenario": sname, "model": cond, "rule": rule,
                    "mean_r": float(v.mean()), "median_r": float(np.median(v)),
                    "max_r": float(v.max()), "p95_r": float(np.quantile(v, 0.95)),
                    **sep,
                }
                z = sep["z_over_uncoupled"]
                print("%-20s %-14s %-22s %9.4f %9.4f %8s %7s"
                      % (sname, cond, rule, v.mean(), sep["target_r"],
                         ("%.2f" % z) if z is not None else "  n/a",
                         "yes" if sep["top_ranked"] else "no"), flush=True)

    # ---- suppression of the venue-wide event, per model x rule ----------
    supp = {}
    for cond in ("shared", "per_station"):
        base = results["cells"]["A_baseline|%s|none" % cond]["mean_r"]
        raw = results["cells"]["B_common_mode_only|%s|none" % cond]["mean_r"]
        for rule in RULES[1:]:
            rej = results["cells"]["B_common_mode_only|%s|%s" % (cond, rule)]["mean_r"]
            supp["%s|%s" % (cond, rule)] = {
                "floor_no_injection_mean_r": base,
                "with_event_no_rejection_mean_r": raw,
                "with_event_after_rejection_mean_r": rej,
                "suppression_pct_of_injected_excess":
                    float(100.0 * (raw - rej) / (raw - base)) if raw - base > 1e-9 else None,
                "residual_excess_over_floor": float(rej - base),
            }
    results["common_mode_suppression"] = supp

    # ---- clock-skew sweep, best cell only -------------------------------
    print("\n[E] station clock-skew sweep (shared model, standardised_median)",
          flush=True)
    sweep = {}
    for j in JITTER_SWEEP:
        sig = {}
        for n in holdout:
            off = int(RNG.integers(-j, j + 1)) if j > 0 else 0
            b = cm_ev + off
            sig[n] = apply_pulses(clean[n], b[(b >= 0) & (b < L)], channels)
        oa = int(RNG.integers(-j, j + 1)) if j > 0 else 0
        ob = int(RNG.integers(-j, j + 1)) if j > 0 else 0
        ea, eb = events + oa, events + COUPLE_LAG + ob
        sig[pair[0]] = apply_pulses(sig[pair[0]], ea[(ea >= 0) & (ea < L)], channels)
        sig[pair[1]] = apply_pulses(sig[pair[1]], eb[(eb >= 0) & (eb < L)], channels)
        R = field("shared", shared, local, sig, holdout)
        Rr = reference_reject(R, holdout, "standardised_median", calib["shared"])
        sep = separation(pair_couplings(Rr, holdout), pair)
        sweep[str(j)] = sep
        print("  skew +-%d intervals: target r %.4f  z %s  top-ranked %s"
              % (j, sep["target_r"],
                 ("%.2f" % sep["z_over_uncoupled"]) if sep["z_over_uncoupled"] else "n/a",
                 sep["top_ranked"]), flush=True)
    results["sync_skew_sweep"] = sweep

    results["runtime_s"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, "e3_coupling.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("\n=============== E3(ii) COMMON-MODE SUPPRESSION ===============")
    for k, v in supp.items():
        print("  %-32s suppressed %5.1f%% of injected excess"
              % (k, v["suppression_pct_of_injected_excess"] or float("nan")))
    print("\n=============== E3(iii) COUPLED PAIR, SCENARIO D ===============")
    for cond in ("shared", "per_station"):
        for rule in RULES:
            c = results["cells"]["D_both|%s|%s" % (cond, rule)]
            print("  %-12s %-22s target r %.4f  z %s  top-ranked %s"
                  % (cond, rule, c["target_r"],
                     ("%.2f" % c["z_over_uncoupled"]) if c["z_over_uncoupled"] else "n/a",
                     c["top_ranked"]))
    print("\nruntime %s s -> results/e3_coupling.json" % results["runtime_s"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
