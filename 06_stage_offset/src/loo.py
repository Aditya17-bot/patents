"""Leave-one-out interpolation of the offset between field visits (record computation).

For three consecutive visits P, T, N at a target, the offset at T is estimated without
T's measurement: (a) linear interpolation in time between s(P) and s(N) (current practice
for the approved record), (b) the same plus the neighbour's departure from linearity,
converted to stage units: s_hat = s_lin + g * (D_T - D_lin)."""
import datetime as dt, json, math, sys
import numpy as np
from summarize import load, rows_of

def days(a, b):
    return (dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days

def run(name, min_c=0.95, out=None):
    d = load(name)
    rows = rows_of(d, min_coupling=min_c)
    by = {}
    for w in rows:
        by.setdefault((w["x"], w["y"]), []).append(w)
    rec = []
    for key, ws in by.items():
        ws.sort(key=lambda w: w["day"])
        hist = []
        for i in range(len(ws) - 1):
            a, b = ws[i], ws[i + 1]
            if b["prev_day"] != a["day"]:
                continue
            tP, tT, tN = a["prev_day"], a["day"], b["day"]
            f = days(tT, tP) / max(days(tN, tP), 1)
            sP, sT, sN = a["s_prev"], a["s_meas"], b["s_meas"]
            s_lin = sP + (sN - sP) * f
            DP, DN = a["dP"], b["dT"]
            DT = 0.5 * (a["dT"] + b["dP"])
            dev = DT - (DP + (DN - DP) * f)
            true_dev = sT - s_lin
            if len(hist) >= 5:
                A = np.array([h[0] for h in hist]); B = np.array([h[1] for h in hist])
                g = float(np.clip(np.sum(A * B) / max(np.sum(A * A), 1e-9), 0, 1.2))
            else:
                g = 0.5
            s_hat = s_lin + g * dev
            x = a["x_visit"]
            e_lin = abs(math.exp(x * (s_lin - sT)) - 1) * 100
            e_hat = abs(math.exp(x * (s_hat - sT)) - 1) * 100
            rec.append({"x": key[0], "y": key[1], "day": tT, "e_lin": e_lin, "e_hat": e_hat,
                        "dev": dev, "true_dev": true_dev, "g": g, "s_lin": s_lin, "s_hat": s_hat, "s_meas": sT})
            hist.append((dev, true_dev))
    el = np.array([r["e_lin"] for r in rec]); eh = np.array([r["e_hat"] for r in rec])
    big = np.array([abs(r["true_dev"]) >= 0.1 for r in rec])
    r = np.corrcoef([q["dev"] for q in rec], [q["true_dev"] for q in rec])[0, 1]
    print(name, "n", len(rec), "targets", len({q['x'] for q in rec}), "r(dev,true)", round(r, 3))
    for lab, m in (("all", np.ones(len(rec), bool)), ("|true dev|>=0.1", big)):
        print("  %-16s lin med %.2f mean %.2f p90 %.1f | nbr med %.2f mean %.2f p90 %.1f | improved %.0f%%" % (
            lab, np.median(el[m]), np.mean(el[m]), np.percentile(el[m], 90), np.median(eh[m]), np.mean(eh[m]),
            np.percentile(eh[m], 90), 100 * np.mean(eh[m] < el[m])))
    if out:
        json.dump(rec, open(out, "w"), indent=0)
    return rec

if __name__ == "__main__":
    run(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.95)
