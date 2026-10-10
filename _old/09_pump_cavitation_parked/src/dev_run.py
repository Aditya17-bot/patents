"""DEVELOPMENT-ONLY scenario runs on simulator.py. Writes data/dev/dev_summary.json (not results/).

S1 commissioning: random flow/speed at high suction margin until the detector is armed.
S2 NPSH sweeps: fixed speed and flow, tank pressure lowered in 60 s steps past the 3 % head drop.
S3 wear: (a) slow wear at high margin; (b) wear step while margin sits just below the gate
   with no cavitation; (c) frozen-baseline comparison.
S4 closed loop: slow tank-pressure ramp with and without the controller.
"""
import copy
import json
import os

import numpy as np

import controller
import estimator
import simulator as sim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "dev")


def commission(seed=1, n_s=3000):
    pump = sim.SimPump(seed)
    det = estimator.Detector(sim.pump_def())
    rng = np.random.default_rng(seed + 100)
    f, qf = 50.0, 1.0
    for k in range(n_s):
        if k % 60 == 0:
            f = rng.uniform(40, 50)
            qf = rng.uniform(0.6, 1.2)
        n = controller.hz_to_rps(f)
        q = sim.Q_B * qf * n / sim.N0
        meas, _ = pump.measure(n, q, 1.0e5)
        det.step(*meas)
    return pump, det


def sweep(pump, det, f=50.0, qf=1.0, p0=1.0e5, dp=2.5e3, hold=60, frozen=None):
    n = controller.hz_to_rps(f)
    q = sim.Q_B * qf
    rows = []
    p = p0
    while True:
        for _ in range(hold):
            meas, tr = pump.measure(n, q, p)
            o = det.step(*meas)
            fr = frozen.step(*meas) if frozen else None
            rows.append((p, tr["loss"], tr["R_true"], o["R"], o.get("alarm", False),
                         bool(fr and fr.get("alarm"))))
        if tr["loss"] > 0.035 or p < 5e3:
            break
        p -= dp
    first = next((r for r in rows if r[4]), None)
    return {"f": f, "qf": qf, "alarm_loss": first[1] if first else None,
            "alarm_R_true": first[2] if first else None, "alarm_R_meas": first[3] if first else None,
            "R_true_at_npsh3": next((r[2] for r in rows if r[1] >= 0.03), None),
            "knee": det.knee()}


def margin_threshold_alarm(f, qf, ratio):
    """Datasheet baseline: alarm when NPSHa < ratio x datasheet NPSH3. Returns true R and loss."""
    r_true = ratio / sim.TRUE_FACTOR
    loss = 0.03 * ((sim.R_ON - r_true) / (sim.R_ON - 1)) ** 2 if r_true < sim.R_ON else 0.0
    return {"ratio": ratio, "R_true": r_true, "loss_at_alarm": loss}


def frozen_copy(det):
    """Baseline frozen at commissioning: gate disabled (no self-calibration)."""
    fr = copy.deepcopy(det)
    fr.eta0.update = lambda *a: None
    fr.psi0.update = lambda *a: None
    return fr


def wear_tests(seed=3):
    pump, det = commission(seed)
    fr = frozen_copy(det)
    n = controller.hz_to_rps(50)
    q = sim.Q_B
    alarms = {"adaptive_high": 0, "frozen_high": 0}
    for k in range(6000):                       # (a) wear 0 -> 4 % at high margin
        pump.wear = 0.04 * k / 6000
        meas, _ = pump.measure(n, q, 1.0e5)
        alarms["adaptive_high"] += det.step(*meas)["alarm"]
        alarms["frozen_high"] += fr.step(*meas)["alarm"]
    # (b) margin just below gate, no cavitation; wear step of 2 % at k = 300; controller probes
    p_low = None
    for p in np.arange(1.0e5, 0, -500.0):
        meas, tr = pump.measure(n, q, p)
        if det.pump.npsh3_ref(q, n) * estimator.R_SAFE > tr["npsha"]:
            p_low = p - 500.0
            break
    ctl = controller.Controller()
    f_cmd = 50.0
    loss_max = 0.0
    for k in range(900):
        if k == 300:
            pump.wear += 0.02
        n = controller.hz_to_rps(f_cmd)
        meas, tr = pump.measure(n, sim.Q_B * n / sim.N0, p_low)
        o = det.step(*meas)
        loss_max = max(loss_max, tr["loss"])
        f_cmd = ctl.step(50.0, o)
        if ctl.rebase:
            det.rebase(*ctl.rebase)
            ctl.rebase = None
    return {"high_margin_alarm_samples": alarms, "low_margin_step": {
        "p_tank": p_low, "events": ctl.events, "true_loss_max": loss_max}}


def closed_loop(seed=5, use_ctl=True):
    pump, det = commission(seed)
    ctl = controller.Controller()
    f_cmd = 50.0
    t_over3 = t_over1 = 0
    f_min = 50.0
    kn = None
    for k in range(4000):
        p = max(1.0e5 - 25.0 * k, 1.0e4)       # 25 Pa/s ramp down, then hold
        n = controller.hz_to_rps(f_cmd)
        q = sim.Q_B * n / sim.N0                 # flow follows speed on a friction-dominated system
        meas, tr = pump.measure(n, q, p)
        o = det.step(*meas)
        if k % 60 == 0:
            kn = det.knee()
            kn = kn[0] if kn and kn[1] > 0 else None
        if use_ctl:
            f_cmd = ctl.step(50.0, o, kn)
        f_min = min(f_min, f_cmd)
        t_over3 += tr["loss"] >= 0.03
        t_over1 += tr["loss"] >= 0.01
    return {"controller": use_ctl, "s_loss_ge_3pct": int(t_over3), "s_loss_ge_1pct": int(t_over1),
            "f_min_hz": round(f_min, 2), "events": ctl.events[:6], "knee": det.knee()}


def main():
    os.makedirs(OUT, exist_ok=True)
    res = {"NOTE": "DEVELOPMENT SIMULATOR OUTPUT - NOT EVIDENCE"}
    pump, det = commission()
    res["armed_after_commissioning"] = det.eta0.n >= estimator.MIN_CAL
    sw = []
    for f, qf in [(50, 1.0), (50, 0.7), (50, 1.2), (42, 1.0)]:
        p2, d2 = commission(seed=int(f * 10 + qf * 10))
        sw.append(sweep(p2, d2, f, qf, frozen=frozen_copy(d2)))
    res["sweeps"] = sw
    res["margin_threshold"] = [margin_threshold_alarm(50, 1.0, r) for r in (1.1, 1.3, 1.5)]
    res["wear"] = wear_tests()
    res["closed_loop"] = [closed_loop(use_ctl=False), closed_loop(use_ctl=True)]
    with open(os.path.join(OUT, "dev_summary.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
