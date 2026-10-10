"""E7 - how long the method takes, and how many interval records it handles.

On one desktop processor, for each corridor and April 2025:
    fit       admission of pairs, share differences and chain solution for the month
              (reading the cached per-site series is included)
    correct   reclassification of every interval record of every fitted detector for
              the month, reported per record in microseconds

The fifteen-minute reporting interval is 900 s; the per-record time is the latency the
correction adds to a record in live use (claim 4).

Output: results/e7_timing.json
"""
import json
import os
import platform
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import method
import pairs
import series

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MONTH = "2025-04"


def main():
    report = {"month": MONTH, "processor": platform.processor(),
              "python": platform.python_version(), "roads": {}}
    for road in ("M25", "M1"):
        t0 = time.perf_counter()
        fits = {}
        n_pairs = 0
        for chain in pairs.chains(road, MONTH):
            n_pairs += len(chain)
            for f in method.solve_chain(chain):
                if f["chain_size"] >= 3:
                    fits[f["detector"]] = f
        t_fit = time.perf_counter() - t0

        data = {d: series.load(d, MONTH) for d in fits}
        n_rec = sum(len(v) for v in data.values())
        t0 = time.perf_counter()
        for d, recs in data.items():
            method.correct_series(recs, fits[d], "additive")
        t_cor = time.perf_counter() - t0
        report["roads"][road] = {
            "admitted_pairs": n_pairs, "fitted_detectors": len(fits),
            "fit_seconds": round(t_fit, 1), "records_corrected": n_rec,
            "correct_seconds": round(t_cor, 3),
            "microseconds_per_record": round(1e6 * t_cor / n_rec, 2)}
        print(road, report["roads"][road])
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "e7_timing.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
