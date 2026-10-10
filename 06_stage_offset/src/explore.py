import json, sys, numpy as np, math
from summarize import load, rows_of
d = load(sys.argv[1] if len(sys.argv) > 1 else "daily_interim")
rows = rows_of(d, min_coupling=float(sys.argv[2]) if len(sys.argv) > 2 else 0.95)
by = {}
for w in rows:
    by.setdefault((w["x"], w["y"]), []).append(w)
def qerr(s_est, w):
    return abs(math.exp(w["x_visit"] * (s_est - w["s_meas"])) - 1) * 100
res = {}
def add(name, w, s):
    res.setdefault(name, []).append((qerr(s, w), abs(w["s_meas"] - w["s_prev"]) >= 0.10, abs(w["s_meas"] - w["s_prev"]) < 0.05))
for key, ws in by.items():
    ws.sort(key=lambda w: w["day"])
    for i, w in enumerate(ws):
        add("base", w, 0.0)
        add("carry", w, w["s_prev"])
        add("off", w, w["s_off"])
        for k in (0.5, 1.0, 1.5, 2.0, 3.0):
            g = abs(w["change"]) > k * w["noise"]
            add("gate%.1f" % k, w, w["s_prev"] + (w["change"] if g else 0))
            add("gate%.1f+sig" % k, w, w["s_prev"] + (w["change"] if (g and w["sse_offset"] <= w["sse_ratio"]) else 0))
        # adaptive gain from this direction's earlier visits (real time)
        past = ws[:i]
        if len(past) >= 5:
            a = np.array([p["change"] for p in past]); b = np.array([p["s_meas"] - p["s_prev"] for p in past])
            gain = float(np.clip(np.sum(a * b) / max(np.sum(a * a), 1e-9), 0, 1.2))
        else:
            gain = 0.5
        add("gain", w, w["s_prev"] + gain * w["change"])
        add("half", w, w["s_prev"] + 0.5 * w["change"])
        # conventional ratio correction with the same adaptive gain (discharge units)
        rc = math.log(w["q_ratio"] / w["q_carry"])
        if len(past) >= 5:
            a = np.array([math.log(p["q_ratio"] / p["q_carry"]) for p in past])
            b = np.array([math.log(p["q_meas"] / p["q_carry"]) for p in past])
            gr = float(np.clip(np.sum(a * b) / max(np.sum(a * a), 1e-9), 0, 1.2))
        else:
            gr = 0.5
        e = abs(math.exp(math.log(w["q_carry"] / w["q_meas"]) + gr * rc) - 1) * 100
        res.setdefault("ratio_gain", []).append((e, abs(w["s_meas"] - w["s_prev"]) >= 0.10, abs(w["s_meas"] - w["s_prev"]) < 0.05))
        # inverse-variance shrink using noise and a prior spread of true change (0.15 ft)
        tau = 0.15
        add("shrink", w, w["s_prev"] + w["change"] * tau**2 / (tau**2 + w["noise"]**2))
print("n", len(rows), "targets", len({w['x'] for w in rows}))
print("%-14s %8s %8s %8s | %8s %8s | %8s %8s" % ("method", "med", "mean", "p90", "bigmed", "bigmean", "smmed", "smmean"))
for name, v in res.items():
    e = np.array([a for a, b, c in v]); big = np.array([a for a, b, c in v if b]); sm = np.array([a for a, b, c in v if c])
    print("%-14s %8.2f %8.2f %8.1f | %8.2f %8.2f | %8.2f %8.2f" % (name, np.median(e), np.mean(e), np.percentile(e, 90), np.median(big), np.mean(big), np.median(sm), np.mean(sm)))
