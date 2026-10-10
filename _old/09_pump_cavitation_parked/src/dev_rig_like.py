"""DEVELOPMENT-ONLY: write simulator output in the rig CSV format to data/dev/rig_like/
so that evaluate.py can be tested before rig data exist. Never evidence."""
import csv
import json
import os

import numpy as np

import simulator as sim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "dev", "rig_like")
COLS = ["t_s", "test", "f_hz", "q_m3s", "p_s_pa_abs", "p_d_pa_abs", "t_c", "p_shaft_w", "hf_rms"]


def write(name, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    pump = sim.SimPump(7)
    rng = np.random.default_rng(8)
    t = 0

    def rec(test, f, qf, p):
        nonlocal t
        n = f / 2
        q = sim.Q_B * qf * n / sim.N0
        (n_, qm, ps, pd, tc, pw), tr = pump.measure(n, q, p)
        hf = 1.0 + rng.normal(0, 0.05) + (2.0 * (2.3 - tr["R_true"]) if tr["R_true"] < 2.3 else 0.0)
        t += 1
        return [t, test, f, qm, ps, pd, tc, pw, hf]

    rows = []
    for f in (50, 45, 40):
        for qf in (0.6, 0.8, 1.0, 1.1, 1.2):
            rows += [rec("T1", f, qf, 1.0e5) for _ in range(180)]
    write("01_T1.csv", rows)
    for j, (f, qf) in enumerate([(50, 1.0), (50, 0.8), (45, 1.0)]):
        rows, p = [], 1.0e5
        while p > 2.0e4:
            rows += [rec("T2", f, qf, p) for _ in range(90)]
            p -= 2.5e3
        write("02_T2_%d.csv" % j, rows)
    rows = []
    for w in (0.0, 0.01, 0.02, 0.03):
        pump.wear = w
        rows += [rec("T4", 50, 1.0, 1.0e5) for _ in range(300)]
    write("03_T4.csv", rows)
    meta = {"d_imp": sim.D_IMP, "d_suction": sim.D_S, "d_discharge": sim.D_D, "dz": 0.0, "poles": 4,
            "n_rated_rps": sim.N0,
            "npsh3_datasheet": [[q, sim.npsh3_datasheet(q, sim.N0)] for q in np.linspace(0, 0.04, 9)]}
    with open(os.path.join(OUT, "pump.json"), "w") as fh:
        json.dump(meta, fh, indent=1)


if __name__ == "__main__":
    main()
