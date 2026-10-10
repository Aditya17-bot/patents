"""E2 - known faults injected into real detectors: are they localised and sized?

April 2025, chains of four or more detectors. For each detector X in turn, vehicles are
moved across the 520 cm boundary in X's own record, in every interval, so that X's share
below 520 cm changes by a known amount; the other boundaries and every total are left
alone. Two injection shapes are used, so the test does not simply replay the model the
method corrects with:

    additive  every interval's share shifted by the same amount
    ratio     every interval's share scaled, the amount moved following the fleet mix

The chain is then re-solved. Recorded per injection:
    localised     X shows the largest change in fitted bias on its chain
    size error    |fitted change at X - injected change at X|, the injected change being
                  measured on the modified record itself (rounding included)
    newly flagged X was not flagged before and is after (for |injection| >= 2 points)
    false flags   other detectors on the chain whose flag state changed

Output: results/e2_injection.json
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import method
import pairs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MONTH = "2025-04"
SIZES = [-0.10, -0.05, -0.02, 0.02, 0.05, 0.10]
SHAPES = ["additive", "ratio"]


def inject(data, keys, delta, shape):
    """Copy of data with the share below 520 cm moved by delta over the given keys."""
    total_n = sum(sum(data[k][0]) for k in keys)
    base_share = sum(data[k][0][0] for k in keys) / total_n
    out = dict(data)
    for k in keys:
        bins, tot, spd = data[k]
        n = sum(bins)
        if n == 0:
            continue
        s = bins[0] / n
        s_new = s + delta if shape == "additive" else s * (1 + delta / base_share)
        target = int(round(min(1.0, max(0.0, s_new)) * n))
        pool = bins[0] + bins[1]           # only the 520 cm boundary moves
        target = min(max(target, 0), pool)
        out[k] = [[target, pool - target, bins[2], bins[3]], tot, spd]
    return out


def share520(data, keys):
    return sum(data[k][0][0] for k in keys) / sum(sum(data[k][0]) for k in keys)


def modified_chain(chain, x, delta, shape):
    """Chain with detector x's record replaced by an injected copy, in every pair."""
    new = []
    realised = []
    for up, down, nid, rec in chain:
        rec2 = dict(rec)
        if up == x:
            rec2["a"] = inject(rec["a"], rec["keys"], delta, shape)
            realised.append(share520(rec2["a"], rec["keys"]) - share520(rec["a"], rec["keys"]))
        if down == x:
            rec2["b"] = inject(rec["b"], rec["keys"], delta, shape)
            realised.append(share520(rec2["b"], rec["keys"]) - share520(rec["b"], rec["keys"]))
        new.append((up, down, nid, rec2))
    return new, sum(realised) / len(realised)


def main():
    report = {"month": MONTH, "sizes": SIZES, "shapes": SHAPES, "roads": {}}
    for road in ("M25", "M1"):
        rows = []
        for chain in pairs.chains(road, MONTH):
            if len(chain) + 1 < 4:
                continue
            base = {f["detector"]: f for f in method.solve_chain(chain)}
            for x in base:
                for shape in SHAPES:
                    for delta in SIZES:
                        ch2, realised = modified_chain(chain, x, delta, shape)
                        after = {f["detector"]: f for f in method.solve_chain(ch2)}
                        change = {d: after[d]["bias"][0] - base[d]["bias"][0] for d in base}
                        top = max(change, key=lambda d: abs(change[d]))
                        false_flags = sum(1 for d in base if d != x and
                                          after[d]["flagged"] != base[d]["flagged"])
                        rows.append({
                            "shape": shape, "delta": delta, "realised": realised,
                            "localised": top == x,
                            "size_error": abs(change[x] - realised),
                            "newly_flagged": (not base[x]["flagged"]) and after[x]["flagged"],
                            "was_flagged": base[x]["flagged"],
                            "false_flags": false_flags, "chain_size": len(base)})
        summary = {"injections": len(rows)}
        for shape in SHAPES:
            for delta in SIZES:
                r = [x for x in rows if x["shape"] == shape and x["delta"] == delta]
                errs = sorted(x["size_error"] for x in r)
                fresh = [x for x in r if not x["was_flagged"]]
                summary["%s %+.2f" % (shape, delta)] = {
                    "n": len(r),
                    "localised": round(sum(x["localised"] for x in r) / len(r), 4),
                    "median_size_error": round(errs[len(errs) // 2], 5),
                    "p90_size_error": round(errs[int(0.9 * len(errs))], 5),
                    "newly_flagged_of_unflagged": "%d/%d" % (
                        sum(x["newly_flagged"] for x in fresh), len(fresh)),
                    "false_flag_changes_per_injection": round(
                        sum(x["false_flags"] for x in r) / len(r), 4)}
        # By chain size, all shapes and sizes pooled: the median gauge of a chain with an
        # even number of detectors is the mean of the two middle biases, and moves by up to
        # half of a fault injected into one of them.
        by_size = {}
        for x in rows:
            n = x["chain_size"]
            key = str(n) if n <= 6 else "7+"
            by_size.setdefault(key, []).append(x)
        summary["by_chain_size"] = {}
        for key in sorted(by_size, key=lambda k: int(k.rstrip("+"))):
            r = by_size[key]
            rel = sorted(x["size_error"] / abs(x["delta"]) for x in r)
            summary["by_chain_size"][key] = {
                "injections": len(r),
                "localised": round(sum(x["localised"] for x in r) / len(r), 4),
                "median_size_error_over_injection": round(rel[len(rel) // 2], 4),
                "p90_size_error_over_injection": round(rel[int(0.9 * len(rel))], 4),
                "false_flag_changes_per_injection": round(
                    sum(x["false_flags"] for x in r) / len(r), 4)}
        report["roads"][road] = summary
        print(road, json.dumps(summary, indent=1))
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "e2_injection.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
