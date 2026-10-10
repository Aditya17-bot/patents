"""Phase 2 — characterise the gaps, and test whether the conservation identity holds.

Two questions, both answered from measured data rather than assumption:

1. Is the missing-data problem real? Rate, run lengths, and whether gaps hit sites
   independently or knock out the whole corridor at once. If gaps were always
   corridor-wide, no spatial method could ever help and the invention would be moot.

2. Does `upstream + entries - exits = downstream` actually close on this network, and
   how tightly? This is the empirical foundation of the whole invention. The plain
   continuity nodes (no slip roads at all, where the identity reduces to
   `upstream = downstream`) give the detector noise floor for free.

The sign of each slip road - whether it adds or removes vehicles - is not assumed from
the MIDAS letter convention. It is chosen per node as the assignment that minimises the
median absolute residual, so the topology is inferred from the balance itself.
"""

import collections
import itertools
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import webtris

RESULTS = os.path.join(ROOT, "results")


def load_series(site_id, start, end):
    """(date, interval) -> volume as float, or None where the record is missing."""
    rows = webtris.daily(site_id, start, end)
    series = {}
    for r in rows:
        key = (r["Report Date"][:10], int(r["Time Interval"]))
        raw = r.get("Total Volume", "")
        series[key] = float(raw) if raw not in ("", None) else None
    return series


# ---------------------------------------------------------------- missingness

def gap_stats(series_by_site):
    """Missingness rate, run lengths, and how far gaps are shared across sites."""
    all_keys = sorted({k for s in series_by_site.values() for k in s})

    per_site = {}
    run_lengths = []
    dead_sites = []
    for sid, series in series_by_site.items():
        vals = [series.get(k) for k in all_keys]
        missing = sum(1 for v in vals if v is None)
        per_site[sid] = missing / len(vals) if vals else 1.0
        if per_site[sid] > 0.99:
            dead_sites.append(sid)
            continue  # a permanently dead detector would swamp the run-length picture
        run = 0
        for v in vals:
            if v is None:
                run += 1
            elif run:
                run_lengths.append(run)
                run = 0
        if run:
            run_lengths.append(run)

    live = [sid for sid in series_by_site if sid not in dead_sites]
    simultaneous = collections.Counter()
    for k in all_keys:
        n_missing = sum(1 for sid in live if series_by_site[sid].get(k) is None)
        simultaneous[n_missing] += 1

    rates = sorted(per_site.values())
    runs = sorted(run_lengths)
    return {
        "sites": len(series_by_site),
        "sites_dead_whole_month": len(dead_sites),
        "dead_site_ids": dead_sites,
        "intervals": len(all_keys),
        "missing_rate_overall": round(
            sum(1 for s in series_by_site.values() for k in all_keys
                if s.get(k) is None) / max(1, len(all_keys) * len(series_by_site)), 4),
        "missing_rate_excluding_dead": round(
            sum(1 for sid in live for k in all_keys
                if series_by_site[sid].get(k) is None) / max(1, len(all_keys) * len(live)), 4),
        "per_site_rate_median": round(statistics.median(rates), 4) if rates else None,
        "per_site_rate_p90": round(rates[int(len(rates) * 0.9)], 4) if rates else None,
        "gap_runs": len(runs),
        "run_len_median": runs[len(runs) // 2] if runs else None,
        "run_len_p90": runs[int(len(runs) * 0.9)] if runs else None,
        "run_len_max": runs[-1] if runs else None,
        "run_len_1_to_4": sum(1 for r in runs if r <= 4),
        "intervals_with_no_live_site_missing": simultaneous.get(0, 0),
        "intervals_with_all_live_sites_missing": simultaneous.get(len(live), 0),
    }


# ------------------------------------------------------- conservation identity

def node_residuals(node, series_by_site, min_intervals=200):
    """Best-fitting slip signs for one node, and the residuals they produce.

    Each slip is tried as an entry (+1), an exit (-1), or as not belonging to this node
    at all (0, only allowed for slips Phase 1 flagged ambiguous). The combination with
    the smallest median absolute residual wins.
    """
    up = series_by_site.get(node["upstream"]["id"])
    down = series_by_site.get(node["downstream"]["id"])
    if up is None or down is None:
        return None

    slips = [s for s in node["slips"] if s["id"] in series_by_site]
    if len(slips) > 4:
        return None  # combinatorics not worth it; these nodes are rare

    keys = [k for k in up
            if up.get(k) is not None and down.get(k) is not None
            and all(series_by_site[s["id"]].get(k) is not None for s in slips)]
    if len(keys) < min_intervals:
        return None

    options = [(-1, 0, 1) if s["ambiguous"] else (-1, 1) for s in slips]
    best = None
    for signs in itertools.product(*options) if slips else [()]:
        residuals = []
        for k in keys:
            r = up[k] - down[k]
            for sign, s in zip(signs, slips):
                r += sign * series_by_site[s["id"]][k]
            residuals.append(r)
        score = statistics.median([abs(r) for r in residuals])
        if best is None or score < best[0]:
            best = (score, signs, residuals)

    score, signs, residuals = best
    flows = [down[k] for k in keys]
    abs_res = sorted(abs(r) for r in residuals)
    return {
        "node_id": node["node_id"],
        "n_slips": len(slips),
        "signs": {s["marker"]: sg for s, sg in zip(slips, signs)},
        "intervals": len(keys),
        "mean_flow": round(statistics.mean(flows), 1),
        "median_abs_residual": round(score, 2),
        "p90_abs_residual": round(abs_res[int(len(abs_res) * 0.9)], 2),
        "mean_residual": round(statistics.mean(residuals), 2),
        "median_abs_residual_pct_of_flow": round(
            100.0 * score / statistics.mean(flows), 2) if statistics.mean(flows) else None,
    }


def main():
    with open(os.path.join(RESULTS, "window.json"), encoding="utf-8") as fh:
        win = json.load(fh)
    with open(os.path.join(RESULTS, "nodes_%s_%s.json" % (win["road"], win["carriageway"])),
              encoding="utf-8") as fh:
        nodes = {n["node_id"]: n for n in json.load(fh)["nodes"]}

    print("loading %d sites..." % len(win["site_ids"]))
    series_by_site = {sid: load_series(sid, win["start"], win["end"])
                      for sid in win["site_ids"]}

    gaps = gap_stats(series_by_site)
    print("\n--- missingness ---")
    for k, v in gaps.items():
        if k != "dead_site_ids":
            print("  %-40s %s" % (k, v))

    print("\n--- conservation residuals ---")
    results = []
    for nid in win["node_ids"]:
        r = node_residuals(nodes[nid], series_by_site)
        if r:
            results.append(r)

    plain = [r for r in results if r["n_slips"] == 0]
    slipped = [r for r in results if r["n_slips"] > 0]

    def report(label, group):
        if not group:
            print("  %-22s none" % label)
            return None
        pcts = sorted(r["median_abs_residual_pct_of_flow"] for r in group)
        print("  %-22s n=%3d  median residual %5.2f%% of flow   p90 across nodes %5.2f%%"
              % (label, len(group), pcts[len(pcts) // 2], pcts[int(len(pcts) * 0.9)]))
        return pcts[len(pcts) // 2]

    noise_floor = report("plain continuity", plain)
    with_slips = report("with slip roads", slipped)

    out = {"window": win, "gaps": gaps, "nodes": results,
           "summary": {"nodes_evaluated": len(results),
                       "plain_continuity_nodes": len(plain),
                       "slip_nodes": len(slipped),
                       "noise_floor_pct": noise_floor,
                       "slip_node_residual_pct": with_slips}}
    with open(os.path.join(RESULTS, "phase2.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/phase2.json")


if __name__ == "__main__":
    main()
