"""E7: delivery alarm noise floor. Rule: alarm when the weekly delivery ratio departs from the median of
its previous 4 weeks by more than L in 2 consecutive weeks. No dripper fault is recorded in the data, so
every alarm on it is counted as a false alarm (an upper bound). A delivery change larger than L sustained
for 2 weeks would raise the alarm. Output: results/e7_delivery.json"""
import json, os
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    dr = json.load(open(os.path.join(ROOT, "results", "dripper_ratio.json")))
    out = {}
    for L in (0.15, 0.2, 0.3):
        alarms, weeks, per = 0, 0, {}
        for t, v in dr.items():
            w = np.array(v["weekly"])
            a = 0
            for i in range(5, len(w)):
                base = np.median(w[i - 5:i - 1])
                if abs(w[i] - base) > L and abs(w[i - 1] - base) > L:
                    a += 1
            n = max(0, len(w) - 5)
            per[t] = a; alarms += a; weeks += n
        out[str(L)] = dict(alarm_weeks=alarms, section_weeks=weeks, rate=round(alarms / weeks, 3), per_compartment=per)
        print(L, out[str(L)])
    json.dump(out, open(os.path.join(ROOT, "results", "e7_delivery.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
