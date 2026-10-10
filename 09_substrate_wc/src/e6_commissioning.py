"""E6: P1-style baseline. A one-off commissioning anchor (median plateau of each sensor's first 14 days
with an onset, then held fixed for the season), as a field-capacity calibration done once at start-up
would give, against the rolling anchor. Metric: second-half median pair gap and valve-decision
mismatch between the two corrections. Output: results/e6_commissioning.json"""
import json, os
import numpy as np
import agc
from offset_anchor import daily_plateau
import rolling_anchor as RA

ROOT = os.path.join(os.path.dirname(__file__), "..")
COMM_DAYS = 14


def main():
    P_star = json.load(open(os.path.join(ROOT, "results", "rolling_anchor.json")))["P_star"]
    S = P_star - 5
    res, gaps_c, gaps_r, mis = {}, [], [], []
    for t in agc.TEAMS:
        x, _ = agc.load(t)
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        test = x[x.index >= split]
        e_c, e_r = {}, {}
        for s in (1, 2):
            P = daily_plateau(x, s)
            comm = float(P.iloc[:COMM_DAYS].median())
            ref = RA.rolling_ref(P, days).reindex(test.index.normalize()).values
            e_c[s] = test[f"WC_slab{s}"] - comm + P_star
            e_r[s] = test[f"WC_slab{s}"] - ref + P_star
            day = (test.index.hour >= 6) & (test.index.hour < 18)
            a, b = e_c[s][day], e_r[s][day]
            ok = a.notna() & np.isfinite(b)
            mis.append(float(((a[ok] < S) != (b[ok] < S)).mean()))
        gc = float((e_c[1] - e_c[2]).abs().median())
        gr = float((e_r[1] - e_r[2]).abs().median())
        gaps_c.append(gc); gaps_r.append(gr)
        res[t] = dict(commissioning=round(gc, 2), rolling=round(gr, 2))
        print(t, res[t])
    out = dict(per_compartment=res, commissioning_days=COMM_DAYS,
               median_commissioning=round(float(np.median(gaps_c)), 2),
               median_rolling=round(float(np.median(gaps_r)), 2),
               rolling_lower_in=int(sum(r < c for r, c in zip(gaps_r, gaps_c))),
               decision_mismatch_commissioning_vs_rolling_median=round(float(np.median(mis)), 3))
    print({k: v for k, v in out.items() if k != "per_compartment"})
    json.dump(out, open(os.path.join(ROOT, "results", "e6_commissioning.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
