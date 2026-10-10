"""E3 - corroboration: dated sensitivity-change events, attributed to one detector.

If a detector's length measurement is changed (a retune, a repair, a fault), both pairs it
belongs to see a step in their share gap below 520 cm on the same day, equal in size and
opposite in sign, because the detector is the downstream member of one pair and the
upstream member of the other. Traffic cannot produce that: a change in the fleet moves
both detectors of a pair together and leaves the gap unchanged.

For every detector with both adjacent pairs available, the daily gap series of each pair
over March-June is scanned for its single largest step. An event is attributed to the
detector where:
    both pairs step on days within STEP_DAY_TOL of each other,
    each step exceeds MIN_STEP,
    the two steps are of opposite sign,
    and they cancel to within CANCEL_TOL of the larger step.
The last condition is the physical signature. As a control, the same rule is applied
with the two pairs' series taken from DIFFERENT detectors (each detector's upstream pair
matched with another detector's downstream pair); events found there are coincidences.

Output: results/e3_step_events.json
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import method
import pairs
import series

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MONTHS = ["2025-03", "2025-04", "2025-05", "2025-06"]
MIN_STEP = 0.03
STEP_DAY_TOL = 1
CANCEL_TOL = 0.3
MIN_SIDE = 5
CONTROL_OFFSETS = 20


def day_index(month, day):
    start = {"2025-03": 0, "2025-04": 31, "2025-05": 61, "2025-06": 92}[month]
    return start + day - 1


def daily_series(up, down):
    out = {}
    for m in MONTHS:
        rec = pairs.pair_record(up, down, m)
        if rec is None or not rec["admitted"]:
            continue
        for day, gaps in method.pair_gap(rec)[1].items():
            out[day_index(m, int(day))] = gaps[method.PRIMARY_EDGE]
    return out


def best_step(s):
    """Largest step in a daily series: (day of first post-step value, size, t-like score)."""
    days = sorted(s)
    xs = [s[d] for d in days]
    n = len(xs)
    if n < 2 * MIN_SIDE:
        return None
    best = None
    for k in range(MIN_SIDE, n - MIN_SIDE + 1):
        a, b = xs[:k], xs[k:]
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        va = sum((x - ma) ** 2 for x in a) / max(1, len(a) - 1)
        vb = sum((x - mb) ** 2 for x in b) / max(1, len(b) - 1)
        pooled = ((va * (len(a) - 1) + vb * (len(b) - 1)) / max(1, n - 2)) ** 0.5
        score = abs(mb - ma) / max(pooled, 1e-4) * (len(a) * len(b) / n) ** 0.5
        if best is None or score > best[2]:
            best = (days[k], mb - ma, score)
    return best


def is_event(s_up, s_down):
    """s_up: step of the pair where the detector is downstream; s_down: where upstream."""
    if s_up is None or s_down is None:
        return False
    d1, x1, _ = s_up
    d2, x2, _ = s_down
    big = max(abs(x1), abs(x2))
    return (abs(d1 - d2) <= STEP_DAY_TOL and abs(x1) > MIN_STEP and abs(x2) > MIN_STEP
            and x1 * x2 < 0 and abs(x1 + x2) < CANCEL_TOL * big)


def main():
    report = {"rule": {"min_step": MIN_STEP, "day_tol": STEP_DAY_TOL,
                       "cancel_tol": CANCEL_TOL, "min_days_each_side": MIN_SIDE},
              "roads": {}}
    for road in ("M25", "M1"):
        cands = pairs.candidates(road)
        into = {c[1]: c for c in cands}
        out_of = {c[0]: c for c in cands}
        dets = [d for d in into if d in out_of]
        steps_up, steps_down = {}, {}
        for d in dets:
            su = daily_series(into[d][0], d)
            sd = daily_series(d, out_of[d][1])
            if su and sd:
                steps_up[d] = best_step(su)
                steps_down[d] = best_step(sd)
        tested = sorted(steps_up)
        events = []
        for d in tested:
            if is_event(steps_up[d], steps_down[d]):
                day, x1, _ = steps_up[d]
                events.append({"detector": d, "day_index": day,
                               "step_upstream_pair": round(x1, 4),
                               "step_downstream_pair": round(steps_down[d][1], 4)})
        # Control: pair each detector's upstream step with another tested detector's
        # downstream step, over CONTROL_OFFSETS shifts of the detector list. Same rule;
        # any event here is coincidence, and the rate per pairing is the chance rate.
        control = 0
        trials = 0
        for shift in range(1, CONTROL_OFFSETS + 1):
            for i, d in enumerate(tested):
                other = tested[(i + shift) % len(tested)]
                if other == d:
                    continue
                trials += 1
                if is_event(steps_up[d], steps_down[other]):
                    control += 1
        report["roads"][road] = {"detectors_tested": len(tested), "events": events,
                                 "n_events": len(events), "control_events": control,
                                 "control_trials": trials,
                                 "event_rate": round(len(events) / len(tested), 4),
                                 "control_rate": round(control / trials, 5)}
        print(road, "tested", len(tested), "events", len(events),
              "control %d of %d" % (control, trials))
        for e in events:
            print("   ", e)
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "e3_step_events.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
