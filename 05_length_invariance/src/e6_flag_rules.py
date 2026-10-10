"""E6 - which rule should mark a detector for attendance in the maintenance record?

E1 found that correcting every fitted detector is at least as good as correcting only the
marked ones, so the mark serves the maintenance record alone. Two rules are compared:

    median   |bias at 520 cm| above the tolerance and above three standard errors, the
             bias being relative to the chain's median (method.solve_chain)
    local    an interior detector whose two pairs both disagree by more than the
             tolerance, with the signs that place that detector, not its neighbours, as
             the source; gauge-free, but cannot mark the two ends of a chain

Reported: detectors marked in March at tolerances of 1, 2, 3 and 5 points; and, on April
chains of four or more with the injection of e2_injection.py (constant shift of -10, -5,
+5, +10 points), how many previously unmarked injected detectors become marked, and how
many marks of OTHER detectors change per injection.

Output: results/flag_rules.json. Run time is about an hour; the chain is re-solved for
every injection and rule.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_injection as e2
import method
import pairs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
TOLS = [0.01, 0.02, 0.03, 0.05]


def gaps_of(chain):
    return [method.pair_gap(p[3])[0][0] for p in chain]


def median_flags(chain, T):
    fits = method.solve_chain(chain)
    return [abs(f["bias"][0]) > T and abs(f["bias"][0]) > 3 * f["se"][0] for f in fits]


def local_flags(chain, T):
    g = gaps_of(chain)
    n = len(g) + 1
    out = [False] * n
    for i in range(1, n - 1):
        gl, gr = g[i - 1], g[i]
        out[i] = (-gl > T and gr > T) or (gl > T and -gr > T)
    return out


def main():
    rep = {}
    for road in ("M25", "M1"):
        chains3 = [c for c in pairs.chains(road, "2025-03") if len(c) + 1 >= 3]
        counts = {}
        for T in TOLS:
            nm = sum(sum(median_flags(c, T)) for c in chains3)
            nl = sum(sum(local_flags(c, T)) for c in chains3)
            ndet = sum(len(c) + 1 for c in chains3)
            counts["%.2f" % T] = {"detectors": ndet, "median": nm, "local": nl}
        print(road, "March", counts)
        inj = {}
        chains4 = [c for c in pairs.chains(road, "2025-04") if len(c) + 1 >= 4]
        for T in (0.02, 0.03, 0.05):
            for rule, fn in (("median", median_flags), ("local", local_flags)):
                flips = n = det = 0
                detectable = 0
                for c in chains4:
                    base = fn(c, T)
                    dets = [c[0][0]] + [p[1] for p in c]
                    for xi, x in enumerate(dets):
                        for delta in (-0.10, -0.05, 0.05, 0.10):
                            c2, _ = e2.modified_chain(c, x, delta, "additive")
                            after = fn(c2, T)
                            n += 1
                            flips += sum(1 for j in range(len(dets))
                                         if j != xi and after[j] != base[j])
                            if not base[xi]:
                                detectable += 1
                                det += after[xi]
                inj["%s T=%.2f" % (rule, T)] = {
                    "injections": n, "other_flips_per_injection": round(flips / n, 3),
                    "newly_flagged": "%d/%d" % (det, detectable)}
                print(road, rule, T, inj["%s T=%.2f" % (rule, T)])
        rep[road] = {"march_counts": counts, "injection": inj}
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "flag_rules.json"), "w") as fh:
        json.dump(rep, fh, indent=1)


if __name__ == "__main__":
    main()
