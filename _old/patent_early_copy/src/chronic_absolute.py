"""Phase 11b - the same question, asked without a clean reference to lean on.

Phase 11 scores a chronic fault by comparing the recovered per-detector parameters
against the same parameters recovered from the unfaulted corridor. That is a fair
measurement of whether the decomposition *can* see a chronic bias, and it is the right
first experiment, but it is not the deployment situation and it should not be reported as
though it were. The defining property of a chronic fault is that it was already present
when the system was first observed. There is no unfaulted corridor to difference against.
Asking for one smuggles the onset assumption back in through the side door.

So this module asks the harder question. Take the network exactly as it arrives, fitted
calibration and all, decompose it once, and ask whether any detector's recovered bias is
an outlier *within the population of recovered biases*. No baseline, no clean period, no
before-and-after. A fault is then not a change but a position in a distribution.

Two consequences follow, and both are stated here rather than discovered by a reader.

First, the threshold has to come from the same run it judges, so it is a robust one:
the median and the median absolute deviation of the recovered population, which a small
number of faulty detectors cannot drag with them. A detector is flagged when its robust
z score exceeds k.

Second, and more awkwardly, a detector flagged on the unfaulted corridor cannot be
called a false alarm. The corridor is real road data and some of those detectors may
genuinely be miscounting - that is, after all, the premise of the whole exercise. What
can honestly be reported is how many detectors the criterion picks out when nothing has
been injected, which bounds the alarm rate from above, and is the number that matters
operationally whichever way the ambiguity resolves. Detectors already flagged at
baseline are excluded from the injection pool, so that a fault is never credited to a
detector the method had already singled out.

Fault type is decided the same way a deployment would have to decide it: without being
told. The gain and offset coordinates are scored on the same robust scale and whichever
is the larger outlier names the fault.
"""

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import chronic
import constrained
import dataset
import evaluate
import faults

RESULTS = os.path.join(ROOT, "results")

# scored in units the two coordinates share: an offset is already vehicles per interval,
# and a gain is converted to vehicles per interval by multiplying by the detector's own
# mean flow. Without that the two are incomparable and the larger-outlier rule is
# meaningless.
CASES = [("offset", -30.0), ("offset", -15.0), ("offset", -8.0),
         ("offset", 8.0), ("offset", 15.0), ("offset", 30.0),
         ("scale", 0.95), ("scale", 0.98), ("scale", 1.02), ("scale", 1.05)]


def robust_z(values, pool):
    """Robust z of every entry, with centre and scale taken from `pool` only."""
    sample = values[pool]
    centre = float(np.median(sample))
    mad = float(np.median(np.abs(sample - centre)))
    scale = 1.4826 * mad
    if scale < 1e-9:
        scale = float(np.std(sample)) or 1.0
    return np.abs(values - centre) / scale, centre, scale


def score(gain, offset, mean_flow, pool):
    """Per-detector outlier scores for both fault coordinates, on one common scale."""
    z_off, c_off, s_off = robust_z(offset, pool)
    gain_veh = gain * mean_flow
    z_gain, c_gain, s_gain = robust_z(gain_veh, pool)
    combined = np.maximum(z_off, z_gain)
    return {"z_offset": z_off, "z_gain": z_gain, "z": combined,
            "kind": np.where(z_gain >= z_off, "scale", "offset"),
            "scale_offset": s_off, "scale_gain": s_gain}


def run(manifest="window_full_M25_A.json", seed=0, n_detectors=25, k=3.5,
        out_name="chronic_absolute.json"):
    rng = np.random.default_rng(seed)
    corridor = dataset.load(manifest)
    fitted = evaluate.fit_node_signs(corridor)
    n_sites = corridor.shape[0]
    nodes_of = faults.node_membership(fitted)

    base_calib = constrained.calibrate(corridor, fitted, mode="scaled")
    band = np.array([base_calib[f["node_id"]]["band"] for f in fitted])
    weights = 1.0 / np.maximum(band, 1.0)

    high, low = chronic.flow_regimes(corridor)
    all_cols = np.arange(corridor.shape[1])
    mean_flow = chronic.detector_flow(corridor, all_cols)

    pool = [r for r, idx in nodes_of.items()
            if len(idx) >= 2 and corridor.observed[r].mean() > 0.9]
    pool_idx = np.array(sorted(pool))

    base_gain, base_offset, _, _ = chronic.decompose_two_regime(
        corridor, fitted, weights, high, low, n_sites)
    base = score(base_gain, base_offset, mean_flow, pool_idx)

    flagged_base = pool_idx[base["z"][pool_idx] > k]
    clean_pool = [int(r) for r in pool_idx if r not in set(flagged_base.tolist())]
    # Ranking over the whole line-up is not the operational question once the corridor has
    # standing outliers of its own: a detector that was already the largest outlier stays
    # the largest outlier whatever is injected elsewhere, so rank-1 over everything is
    # driven by the existing population rather than by the injected fault. Both are
    # reported - the first because it is the honest number for a cold start, the second
    # because it is the question that remains after the standing outliers are triaged.
    new_pool = np.array(clean_pool)

    print("corridor %d detectors, %d nodes, %d in the multi-node pool"
          % (n_sites, len(fitted), pool_idx.size))
    print("no fault injected, threshold k=%.1f on the robust z of the recovered bias:" % k)
    print("  flagged: %d of %d detectors (%.1f%%)"
          % (flagged_base.size, pool_idx.size, 100.0 * flagged_base.size / pool_idx.size))
    print("  robust scale of the recovered population: offset %.2f veh, gain %.2f veh"
          % (base["scale_offset"], base["scale_gain"]))
    print("  these are not necessarily false alarms - some may be genuinely miscounting;")
    print("  they bound the alarm rate from above and are excluded from the test pool.")

    tested = list(clean_pool)
    if len(tested) > n_detectors:
        pick = rng.choice(len(tested), size=n_detectors, replace=False)
        tested = [tested[i] for i in sorted(pick)]

    out = {"manifest": manifest, "seed": seed, "threshold_k": k,
           "nodes": len(fitted), "detectors": n_sites,
           "pool": int(pool_idx.size),
           "flagged_without_injection": int(flagged_base.size),
           "flagged_without_injection_pct": round(
               100.0 * flagged_base.size / pool_idx.size, 2),
           "robust_scale_offset_veh": round(base["scale_offset"], 3),
           "robust_scale_gain_veh": round(base["scale_gain"], 3),
           "detectors_tested": len(tested),
           "cases": []}

    print("\n%-44s %6s %9s %9s %9s %9s %9s"
          % ("injected chronic fault", "trials", "detected", "rank1all", "rank1new",
             "type", "extra"))

    for mode, magnitude in CASES:
        detected = rank1 = rank1_new = top3_new = type_ok = extra = trials = 0
        recovered = []
        for row in tested:
            faulted = chronic.inject_chronic(corridor.volumes, row, mode, magnitude)
            sub = dataset.Corridor(faulted, corridor.observed, corridor.site_ids,
                                   corridor.keys, corridor.nodes)
            gain, offset, _, _ = chronic.decompose_two_regime(
                sub, fitted, weights, high, low, n_sites)
            flow = chronic.detector_flow(sub, all_cols)
            s = score(gain, offset, flow, pool_idx)
            trials += 1

            over = pool_idx[s["z"][pool_idx] > k]
            detected += int(s["z"][row] > k)
            rank1 += int(pool_idx[np.argmax(s["z"][pool_idx])] == row)
            order_new = new_pool[np.argsort(-s["z"][new_pool])]
            rank1_new += int(order_new[0] == row)
            top3_new += int(row in order_new[:3].tolist())
            type_ok += int(s["kind"][row] == mode and s["z"][row] > k)
            # detectors flagged that were not flagged before and are not the injected one
            extra += int(np.setdiff1d(over, np.append(flagged_base, row)).size)
            recovered.append(float(offset[row]) if mode == "offset"
                             else float(gain[row]))

        entry = {"mode": mode, "magnitude": magnitude, "trials": trials,
                 "detected": round(detected / trials, 4),
                 "identified_rank1": round(rank1 / trials, 4),
                 "identified_rank1_excluding_standing": round(rank1_new / trials, 4),
                 "identified_top3_excluding_standing": round(top3_new / trials, 4),
                 "type_named_correctly": round(type_ok / trials, 4),
                 "extra_detectors_flagged_per_trial": round(extra / trials, 3),
                 "median_recovered_absolute": round(float(np.median(recovered)), 4)}
        out["cases"].append(entry)

        label = ("constant %s of %.0f veh/interval, all month"
                 % ("loss" if magnitude < 0 else "gain", abs(magnitude))
                 if mode == "offset"
                 else "%s-count by %.0f%%, all month"
                 % ("under" if magnitude < 1 else "over", abs(100 * (magnitude - 1))))
        print("%-44s %6d %8.1f%% %8.1f%% %8.1f%% %8.1f%% %9.2f"
              % (label, trials, 100 * entry["detected"],
                 100 * entry["identified_rank1"],
                 100 * entry["identified_rank1_excluding_standing"],
                 100 * entry["type_named_correctly"],
                 entry["extra_detectors_flagged_per_trial"]))

    with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/%s" % out_name)
    return out


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "window_full_M25_A.json"
    name = sys.argv[2] if len(sys.argv) > 2 else "chronic_absolute.json"
    kk = float(sys.argv[3]) if len(sys.argv) > 3 else 3.5
    run(manifest, out_name=name, k=kk)
