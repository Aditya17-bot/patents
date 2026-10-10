"""E1 - out-of-sample: fit biases on March, correct April-June, measure adjacent agreement.

Nothing fitted here sees the evaluation months. For every pair admitted in an evaluation
month (by the same volume-balance gate, which correction cannot affect because totals are
preserved), the share gap below each boundary is measured on the raw archive and on the
archive corrected with the March biases.

Policies compared:
    none               the archive as published
    flagged/additive   correct only flagged detectors, additive model
    flagged/ratio      correct only flagged detectors, ratio model
    all/additive       correct every detector with a March fit on a chain of 3 or more
    all/ratio          the same, ratio model

Metrics, per road and month:
    mean |gap| per boundary over all admitted pairs, and over the pairs touching a
    corrected detector; the interval-level mean |gap| below 520 cm on touched pairs,
    which is where the additive and ratio models differ; and the number of touched pairs
    whose |gap| below 520 cm got worse by more than one percentage point.

Output: results/e1_out_of_sample.json and results/fit_march_<road>.json.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import method
import pairs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
FIT_MONTH = "2025-03"
EVAL_MONTHS = ["2025-04", "2025-05", "2025-06"]
POLICIES = [("none", None, None), ("flagged/additive", "flagged", "additive"),
            ("flagged/ratio", "flagged", "ratio"), ("all/additive", "all", "additive"),
            ("all/ratio", "all", "ratio")]


def fit(road):
    fits = {}
    for chain in pairs.chains(road, FIT_MONTH):
        for f in method.solve_chain(chain):
            fits[f["detector"]] = f
    return fits


def interval_gap(a, b, keys):
    """Mean over intervals of |share below 520 cm, up minus down|."""
    tot = 0.0
    n = 0
    for k in keys:
        ba, bb = a[k][0], b[k][0]
        na, nb = sum(ba), sum(bb)
        if na == 0 or nb == 0:
            continue
        tot += abs(ba[0] / na - bb[0] / nb)
        n += 1
    return tot / n if n else float("nan")


def evaluate(road, fits):
    out = {}
    for month in EVAL_MONTHS:
        chains = pairs.chains(road, month)
        rows = {name: {"all": [], "touched": [], "interval": [], "worse": 0}
                for name, _, _ in POLICIES}
        n_pairs = 0
        for chain in chains:
            for up, down, node_id, rec in chain:
                n_pairs += 1
                raw_gap = method.pair_gap(rec)[0]
                for name, scope, model in POLICIES:
                    chosen = {}
                    if scope is not None:
                        for det in (up, down):
                            f = fits.get(det)
                            if f is None or f["chain_size"] < 3:
                                continue
                            if scope == "all" or f["flagged"]:
                                chosen[det] = f
                    a = rec["a"] if up not in chosen else \
                        method.correct_series(rec["a"], chosen[up], model)
                    b = rec["b"] if down not in chosen else \
                        method.correct_series(rec["b"], chosen[down], model)
                    corrected = {"keys": rec["keys"], "a": a, "b": b}
                    gap = method.pair_gap(corrected)[0]
                    r = rows[name]
                    r["all"].append([abs(g) for g in gap])
                    touched = bool(chosen) if scope is not None else None
                    r.setdefault("_touched_mask", []).append(touched)
                    if scope is not None and chosen:
                        r["touched"].append([abs(g) for g in gap])
                        r["interval"].append(interval_gap(a, b, rec["keys"]))
                        if abs(gap[0]) > abs(raw_gap[0]) + 0.01:
                            r["worse"] += 1
        # Raw values on the same touched pairs, per policy, for a like-for-like baseline.
        none_all = rows["none"]["all"]
        summary = {"admitted_pairs": n_pairs}
        for name, scope, model in POLICIES:
            r = rows[name]
            entry = {"mean_abs_gap_all": _mean_cols(r["all"])}
            if scope is not None:
                mask = r["_touched_mask"]
                raw_touched = [none_all[i] for i, m in enumerate(mask) if m]
                entry["touched_pairs"] = len(r["touched"])
                entry["mean_abs_gap_touched_raw"] = _mean_cols(raw_touched)
                entry["mean_abs_gap_touched"] = _mean_cols(r["touched"])
                entry["interval_gap_520_touched"] = _mean(r["interval"])
                entry["touched_worse_by_1pt"] = r["worse"]
            summary[name] = entry
        # Interval-level raw baseline on the pairs touched by the "all" scope.
        out[month] = summary
    return out


def _mean(xs):
    xs = [x for x in xs if x == x]
    return round(sum(xs) / len(xs), 5) if xs else None


def _mean_cols(rows):
    if not rows:
        return None
    return [round(sum(r[e] for r in rows) / len(rows), 5) for e in range(method.N_EDGES)]


def raw_interval_gap(road, fits, scope):
    """Interval-level raw gap below 520 cm on pairs the given scope would touch."""
    out = {}
    for month in EVAL_MONTHS:
        vals = []
        for chain in pairs.chains(road, month):
            for up, down, node_id, rec in chain:
                touched = False
                for det in (up, down):
                    f = fits.get(det)
                    if f and f["chain_size"] >= 3 and (scope == "all" or f["flagged"]):
                        touched = True
                if touched:
                    vals.append(interval_gap(rec["a"], rec["b"], rec["keys"]))
        out[month] = _mean(vals)
    return out


def main():
    os.makedirs(RESULTS, exist_ok=True)
    report = {"fit_month": FIT_MONTH, "eval_months": EVAL_MONTHS,
              "flag_rule": {"se_multiple": method.FLAG_SE_MULTIPLE,
                            "floor": method.FLAG_FLOOR, "edge_cm": 520},
              "roads": {}}
    for road in ("M25", "M1"):
        fits = fit(road)
        with open(os.path.join(RESULTS, "fit_march_%s.json" % road), "w") as fh:
            json.dump(fits, fh, indent=1)
        on_chain3 = [f for f in fits.values() if f["chain_size"] >= 3]
        flagged = [f for f in on_chain3 if f["flagged"]]
        res = evaluate(road, fits)
        res["raw_interval_gap_520_touched"] = {
            "flagged": raw_interval_gap(road, fits, "flagged"),
            "all": raw_interval_gap(road, fits, "all")}
        res["fit"] = {"detectors_fitted": len(fits), "on_chains_of_3_or_more": len(on_chain3),
                      "flagged": len(flagged),
                      "flagged_detectors": sorted(
                          [(f["detector"], round(f["bias"][0], 4)) for f in flagged],
                          key=lambda x: -abs(x[1]))}
        report["roads"][road] = res
        print(road, json.dumps(res["fit"])[:400])
        for m in EVAL_MONTHS:
            s = res[m]
            print(" ", m, "pairs", s["admitted_pairs"])
            for name, _, _ in POLICIES:
                print("    %-17s %s" % (name, json.dumps(s[name])))
        print("  raw interval gap on touched:", res["raw_interval_gap_520_touched"])
    with open(os.path.join(RESULTS, "e1_out_of_sample.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
