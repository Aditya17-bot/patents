"""E9: detection of an injected dripper fault by the delivery alarm (claim 5).

The data hold no recorded dripper fault, so a fault is injected into the real weekly series of
results/dripper_ratio.json. The weekly ratio of the two slabs of a section is
    r = (f1 / u1) / (f2 / u2)                       (dripper_ratio.py)
where f is the share of the dosed water that reaches the slab. A dripper line of slab s partly closed so
that it passes a fraction k of its former flow scales f_s by k, so from the fault week on r is multiplied
by k (fault on slab 1) or divided by k (fault on slab 2). This is the first-order effect only: it leaves
out any change in the plants' uptake of the under-watered slab, which would grow the departure further
as the slab dries.

Rule (as e7_delivery.py): alarm in week i when the ratio departs from the median of weeks i-5..i-2 by more
than L in weeks i and i-1. A fault starting in week i0 is detected if an alarm is raised in weeks
i0+1..i0+3 (two to four weeks of fault). Every start week with four clean weeks before it and three after
it, every compartment, both slabs. The same windows without injection give the chance of an alarm
that is not caused by the fault. Output: results/e9_dripper_fault.json
"""
import json
import os

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
KS = (0.9, 0.8, 0.7, 0.6, 0.5)
LS = (0.2, 0.3)
HORIZON = 3


def alarms(w, L):
    """Weeks i (index) on which the rule of e7_delivery.py raises the alarm."""
    out = []
    for i in range(5, len(w)):
        base = np.median(w[i - 5:i - 1])
        if abs(w[i] - base) > L and abs(w[i - 1] - base) > L:
            out.append(i)
    return out


def main():
    dr = json.load(open(os.path.join(ROOT, "results", "dripper_ratio.json")))
    out = dict(ks=KS, limits=LS, horizon_weeks=HORIZON, by_limit={})
    for L in LS:
        rows = {}
        chance, m = 0, 0
        for team, v in dr.items():
            w0 = np.array(v["weekly"], float)
            a0 = alarms(w0, L)
            for i0 in range(5, len(w0) - HORIZON):
                m += 1
                chance += any(i0 + 1 <= i <= i0 + HORIZON for i in a0)
        rows["no_fault"] = dict(windows=m, with_alarm=chance, rate=round(chance / m, 3))
        print("L", L, "no fault", rows["no_fault"])
        for k in KS:
            hit, n, delay = 0, 0, []
            for team, v in dr.items():
                w0 = np.array(v["weekly"], float)
                for i0 in range(5, len(w0) - HORIZON):
                    for slab in (1, 2):
                        w = w0.copy()
                        w[i0:] = w[i0:] * k if slab == 1 else w[i0:] / k
                        a = [i for i in alarms(w, L) if i0 + 1 <= i <= i0 + HORIZON]
                        n += 1
                        if a:
                            hit += 1
                            delay.append(a[0] - i0 + 1)
            rows[str(k)] = dict(closed_pct=round(100 * (1 - k)), cases=n, detected=hit,
                                rate=round(hit / n, 3),
                                median_weeks_to_alarm=float(np.median(delay)) if delay else None)
            print("L", L, "k", k, rows[str(k)])
        out["by_limit"][str(L)] = rows
    json.dump(out, open(os.path.join(ROOT, "results", "e9_dripper_fault.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
