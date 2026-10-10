"""Phase D evaluation on rig logs -> results/evidence.json (the evidence base of the IDF).

    python src/evaluate.py data/rig            # real rig data
    python src/evaluate.py data/dev/rig_like   # DEV check only (simulated CSV; writes data/dev/)

Input: one CSV per run, columns
    t_s, test, f_hz, q_m3s, p_s_pa_abs, p_d_pa_abs, t_c, p_shaft_w, hf_rms
`test` is T1..T6 as in RIG_PROTOCOL.md; files are replayed in name order (T1 first).
`pump.json` in the same folder: d_imp, d_suction, d_discharge, dz, poles, npsh3_datasheet
(list of [q_m3s, npsh3_m] at the rated speed n_rated_rps).

Truth (fixed in RIG_PROTOCOL.md section 3):
  NPSH3 per T2 sweep: first step mean head <= 0.97 x mean of the first three steps.
  Acoustic onset: first step whose hf_rms mean exceeds the T1 mean by 3 sd.
Methods compared on the same samples:
  M   this method (estimator.Detector)
  B1  datasheet margin threshold NPSHa < k x NPSH3_datasheet, k = 1.1, 1.3, 1.5
  B2  frozen-baseline efficiency residual (no gate, no re-fit, no separation), same threshold rule
  B3  vibration/AE rms above T1 mean + 3 sd (the truth channel itself; shows the earliest possible)
"""
import csv
import glob
import json
import os
import sys

import numpy as np

import estimator
import physics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(folder):
    runs = []
    for f in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        with open(f, newline="") as fh:
            rows = [{k: (v if k == "test" else float(v)) for k, v in r.items()} for r in csv.DictReader(fh)]
        runs.append((os.path.basename(f), rows))
    with open(os.path.join(folder, "pump.json")) as fh:
        meta = json.load(fh)
    return runs, meta


def make_pump(meta):
    tab = np.array(meta["npsh3_datasheet"])
    n_r = meta["n_rated_rps"]

    def npsh3(q, n):
        return (n / n_r) ** 2 * float(np.interp(q * n_r / n, tab[:, 0], tab[:, 1]))
    return estimator.Pump(meta["d_imp"], meta["d_suction"], meta["d_discharge"], npsh3, meta.get("dz", 0.0))


def steps(rows, key="p_s_pa_abs", tol=500.0):
    """Split a sweep into hold steps by suction-pressure level changes."""
    out, cur = [], [rows[0]]
    for r in rows[1:]:
        if abs(r[key] - cur[0][key]) > tol:
            out.append(cur)
            cur = []
        cur.append(r)
    out.append(cur)
    return out


def main(folder):
    runs, meta = load(folder)
    pump = make_pump(meta)
    poles = meta.get("poles", 4)
    det = estimator.Detector(pump)
    frozen = None
    hf_t1 = []
    res = {"source": folder, "sweeps": [], "wear": [], "noise": {}}
    for name, rows in runs:
        test = rows[0]["test"]
        per = []
        for r in rows:
            n = r["f_hz"] * 2 / poles
            o = det.step(n, r["q_m3s"], r["p_s_pa_abs"], r["p_d_pa_abs"], r["t_c"], r["p_shaft_w"])
            fo = frozen.step(n, r["q_m3s"], r["p_s_pa_abs"], r["p_d_pa_abs"], r["t_c"], r["p_shaft_w"]) if frozen else {}
            per.append((r, o, fo))
            if test == "T1":
                hf_t1.append(r["hf_rms"])
        if test == "T1" and frozen is None and det.eta0.n >= estimator.MIN_CAL:
            import copy
            frozen = copy.deepcopy(det)
            frozen.eta0.update = lambda *a: None
            frozen.psi0.update = lambda *a: None
        if test == "T2":
            hf_lim = float(np.mean(hf_t1) + 3 * np.std(hf_t1))
            st = steps(rows)
            idx, k0 = [], 0
            for s in st:
                idx.append((k0, k0 + len(s)))
                k0 += len(s)
            heads = [np.mean([per[i][1]["head"] for i in range(a, b)]) for a, b in idx]
            npsha = [np.mean([per[i][1]["npsha"] for i in range(a, b)]) for a, b in idx]
            h_ref = float(np.mean(heads[:3]))
            k3 = next((j for j, h in enumerate(heads) if h <= 0.97 * h_ref), None)
            kac = next((j for j, (a, b) in enumerate(idx) if np.mean([rows[i]["hf_rms"] for i in range(a, b)]) > hf_lim), None)

            def first(flag):
                for j, (a, b) in enumerate(idx):
                    if any(flag(per[i]) for i in range(a, b)):
                        return j
                return None
            km = first(lambda p: p[1].get("alarm"))
            kb2 = first(lambda p: p[2].get("alarm"))
            kb1 = {str(k): first(lambda p, k=k: p[1]["R"] < k) for k in (1.1, 1.3, 1.5)}

            def at(j):
                return None if j is None else {"step": j, "npsha_m": round(float(npsha[j]), 3),
                                               "head_loss": round(1 - float(heads[j]) / h_ref, 4)}
            res["sweeps"].append({"run": name, "npsh3": at(k3), "acoustic": at(kac), "method": at(km),
                                  "frozen": at(kb2), "margin_threshold": {k: at(v) for k, v in kb1.items()}})
        if test == "T4":
            res["wear"].append({"run": name, "method_alarm_samples": int(sum(bool(p[1].get("alarm")) for p in per)),
                                "frozen_alarm_samples": int(sum(bool(p[2].get("alarm")) for p in per)),
                                "c_eta_end": per[-1][1].get("c_eta")})
    res["knee"] = det.knee()
    res["noise"]["eta_residual_sd_gated"] = float(np.std(list(det.cbuf_eta))) if det.cbuf_eta else None
    dev = os.path.abspath(folder).startswith(os.path.join(ROOT, "data", "dev"))
    out = os.path.join(ROOT, "data", "dev", "evidence_dev.json") if dev else os.path.join(ROOT, "results", "evidence.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main(sys.argv[1])
