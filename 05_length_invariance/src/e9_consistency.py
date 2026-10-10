"""E9 - the cross-boundary test: does one length offset explain every boundary?

A detector that over-measures every vehicle by d cm has, at every boundary e, the share
bias F(e) - F(e - d), where F is the cumulative length distribution of the stream. Its
offset d is fixed by its bias at 520 cm; its biases at 660 cm and 1160 cm are then
predicted, with no further fitted parameter, from the stream's own class shares (F is the
PCHIP interpolation of E8 through the corridor-month median shares). A detector whose
biases at the other boundaries depart from the prediction by more than a set fraction
of its 520 cm bias has a fault that is not a length offset (for example a mis-set class
boundary), and its offset is not written as a sensitivity correction.

Unlike the principal-direction test of E8, nothing here is fitted to the bias matrix:
the direction is predicted from the counts.

A  field       March-June, both corridors, every detector on a chain of three or more:
               predicted against solved bias at 660 cm (slope through the origin,
               correlation, share of variance explained); detectors failing the test;
               agreement with the E8 principal-direction class; persistence March-June
B  injection   April, chains of four or more, every detector in turn:
               offset       every boundary moved as a length offset of +-40 cm would move it
               boundary660  only the 660 cm boundary moved, as a 660 cm threshold set
                            +-100 cm wrong would move it
               boundary1160 only the 1160 cm boundary moved, as a 1160 cm threshold set
                            +-150 cm wrong would move it
               The chain is re-solved and the test re-run. Recorded: the share of
               injected detectors passing (offset) or failing (boundary faults), and
               the class changes of the other detectors of the chain. The offset
               injection is made with the model the test assumes, so it checks only that
               the chain solve, count rounding and fleet noise do not break a true offset;
               the boundary injections are the discriminating test.
C  gauge       the test on biases re-solved with the constant of each chain moved by a
               common offset of +-30 cm applied to every detector of the chain (every
               detector's record shifted as by that offset before the solve): the share
               of detectors whose class changes

Output: results/e9_consistency.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e8_offset_model as e8
import method
import pairs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MONTHS = e8.MONTHS
EDGES = e8.EDGES
LIMIT = e8.RESIDUAL_LIMIT      # 0.3 of the 520 cm bias
FLOOR = e8.BIG                 # residual scaled by max(|b520|, 2 points)
INJ_MONTH = "2025-04"


def corridor_cdf(fits):
    shares = np.median(np.array([f["share"] for f in fits.values()]), axis=0)
    return e8.cdf_of(shares)


def predicted(F, d):
    """Share bias at each boundary of a detector over-measuring every length by d."""
    return [float(F(e - d) - F(e)) for e in EDGES]


def density_ratio(F):
    dens = [float(F.derivative()(e)) for e in EDGES]
    return [x / dens[0] for x in dens]


def test(F, bias):
    """Offset d (cm), predicted biases, residual, and whether the unit passes.

    The prediction is first order: an offset d moves the share below e by -f(e) d, so the
    bias at e is the bias at 520 cm times f(e) / f(520). It uses only the density of the
    interpolated distribution at the boundaries, and not its shape between them, which
    class counts do not determine. The offset itself, for the maintenance record, is the
    exact inversion at 520 cm."""
    d = e8.offset_cm(F, bias[0])
    if d != d:
        return {"offset_cm": None, "residual": None, "passes": False}
    ratio = density_ratio(F)
    p = [bias[0] * x for x in ratio]
    dev = max(abs(bias[k] - p[k]) for k in (1, 2))
    res = dev / max(abs(bias[0]), FLOOR)
    return {"offset_cm": d, "pred": p, "residual": res, "passes": res <= LIMIT}


# ------------------------------------------------------------------ A field
def field(road):
    out = {}
    classes = {}
    for m in MONTHS:
        fits = e8.fit_month(road, m)
        F = corridor_cdf(fits)
        st = e8.structure(fits)
        rows = {d: test(F, fits[d]["bias"]) for d in fits}
        big = [d for d in fits if abs(fits[d]["bias"][0]) > FLOOR and "pred" in rows[d]]
        obs = np.array([fits[d]["bias"][1] for d in big])
        pre = np.array([rows[d]["pred"][1] for d in big])
        slope = float(obs @ pre / (pre @ pre))
        r = float(np.corrcoef(obs, pre)[0, 1])
        r2 = 1.0 - float(((obs - pre) ** 2).sum() / (obs ** 2).sum())
        fail = [d for d in fits if not rows[d]["passes"]]
        pca_fail = {d for d in big if st["_res"][d] > LIMIT}
        agree = sum(1 for d in big if (d in pca_fail) == (not rows[d]["passes"]))
        classes[m] = {d: rows[d]["passes"] for d in fits}
        if m in ("2025-03", "2025-06"):
            out.setdefault("per_detector", {})[m] = {
                d: {"bias": [round(x, 5) for x in fits[d]["bias"]],
                    "pred": [round(x, 5) for x in rows[d]["pred"]] if "pred" in rows[d] else None,
                    "offset_cm": round(rows[d]["offset_cm"], 1) if rows[d]["offset_cm"] is not None else None,
                    "residual": round(rows[d]["residual"], 4) if rows[d]["residual"] is not None else None,
                    "passes": rows[d]["passes"]} for d in fits}
        out[m] = {"detectors": len(fits), "big": len(big),
                  "slope_660_observed_on_predicted": round(slope, 3),
                  "corr_660": round(r, 3),
                  "variance_660_explained_by_prediction": round(r2, 3),
                  "fail_all": len(fail),
                  "fail_big": sum(1 for d in big if not rows[d]["passes"]),
                  "principal_direction_fail_big": len(pca_fail),
                  "agreement_with_principal_direction_big": round(agree / len(big), 3)}
        print(road, m, json.dumps(out[m]))
    both = set(classes["2025-03"]) & set(classes["2025-06"])
    fm = {d for d in both if not classes["2025-03"][d]}
    fj = {d for d in both if not classes["2025-06"][d]}
    out["persistence"] = {"detectors_in_march_and_june": len(both), "fail_march": len(fm),
                          "fail_june": len(fj), "fail_both": len(fm & fj),
                          "pass_both": sum(1 for d in both
                                           if classes["2025-03"][d] and classes["2025-06"][d])}
    print(road, json.dumps(out["persistence"]))
    return out


# ------------------------------------------------------------------ B, C injection
def shift_series(data, delta):
    """Copy of a record with its share below each boundary lowered by delta[e]."""
    return method.correct_series(data, {"bias": delta}, "additive")


def modified(chain, targets, delta):
    new = []
    for up, down, nid, rec in chain:
        rec2 = dict(rec)
        if up in targets:
            rec2["a"] = shift_series(rec["a"], delta)
        if down in targets:
            rec2["b"] = shift_series(rec["b"], delta)
        new.append((up, down, nid, rec2))
    return new


def solve(chain):
    return {f["detector"]: f for f in method.solve_chain(chain)}


def injection(road):
    fits = e8.fit_month(road, INJ_MONTH)
    F = corridor_cdf(fits)
    kinds = {}
    for s in (+1, -1):
        # shift_series lowers the share below each boundary by delta, so a detector
        # over-measuring by d is injected with delta = -(predicted bias)
        kinds["offset %+d cm" % (40 * s)] = [-x for x in predicted(F, 40 * s)]
        kinds["boundary660 %+d cm" % (100 * s)] = [0.0, float(F(660) - F(660 - 100 * s)), 0.0]
        kinds["boundary1160 %+d cm" % (150 * s)] = [0.0, 0.0, float(F(1160) - F(1160 - 150 * s))]
    rows = {k: [] for k in kinds}
    gauge = {}
    for chain in pairs.chains(road, INJ_MONTH):
        if len(chain) + 1 < 4:
            continue
        base = solve(chain)
        bclass = {d: test(F, base[d]["bias"])["passes"] for d in base}
        for x in base:
            for k, delta in kinds.items():
                after = solve(modified(chain, {x}, delta))
                aclass = {d: test(F, after[d]["bias"])["passes"] for d in after}
                rows[k].append({"x_passes_before": bclass[x], "x_passes_after": aclass[x],
                                "others_changed": sum(1 for d in base if d != x and
                                                      aclass[d] != bclass[d]),
                                "chain_size": len(base)})
        for s in (+1, -1):
            after = solve(modified(chain, set(base), [-x for x in predicted(F, 30 * s)]))
            aclass = {d: test(F, after[d]["bias"])["passes"] for d in after}
            g = gauge.setdefault("common %+d cm" % (30 * s), [0, 0])
            g[0] += sum(1 for d in base if aclass[d] != bclass[d])
            g[1] += len(base)
    summary = {"month": INJ_MONTH}
    for k, r in rows.items():
        was = [x for x in r if x["x_passes_before"]]
        if k.startswith("offset"):
            ok = sum(1 for x in was if x["x_passes_after"])
            key = "still_pass_of_passing_before"
        else:
            ok = sum(1 for x in was if not x["x_passes_after"])
            key = "now_fail_of_passing_before"
        summary[k] = {"injections": len(r), key: "%d/%d" % (ok, len(was)),
                      "rate": round(ok / len(was), 3) if was else None,
                      "other_units_changed_per_injection": round(
                          sum(x["others_changed"] for x in r) / len(r), 4)}
    summary["common_offset_class_changes"] = {k: "%d/%d" % tuple(v) for k, v in gauge.items()}
    print(road, json.dumps(summary, indent=1))
    return summary


def main():
    report = {"limit": LIMIT, "floor": FLOOR, "roads": {}}
    for road in ("M25", "M1"):
        report["roads"][road] = {"field": field(road), "injection": injection(road)}
    with open(os.path.join(RESULTS, "e9_consistency.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
