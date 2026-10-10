"""Probe: unmix HGV speed distribution from aggregate WebTRIS bins at night (free flow)."""
import os, json, glob, collections
import numpy as np
from scipy.optimize import nnls
SRC = r"C:\adi\patents\04_count_conservation\data\webtris"
SB = ["0 - 10 mph","11 - 15 mph","16 - 20 mph","21 - 25 mph","26 - 30 mph","31 - 35 mph","36 - 40 mph",
      "41 - 45 mph","46 - 50 mph","51 - 55 mph","56 - 60 mph","61 - 70 mph","71 - 80 mph","80+ mph"]
LB = ["0 - 520 cm","521 - 660 cm","661 - 1160 cm","1160+ cm"]
rows = collections.defaultdict(list)
names = {}
for f in glob.glob(os.path.join(SRC, "daily_*.json")):
    sid = os.path.basename(f).split("_")[1]
    d = json.load(open(f))
    for r in d.get("Rows", []):
        if r["Total Volume"] in ("", None): continue
        hh = int(r["Time Period Ending"][:2])
        if not (0 <= hh < 5): continue
        try:
            s = np.array([float(r[k]) for k in SB]); l = np.array([float(r[k]) for k in LB])
        except ValueError:
            continue
        if s.sum() < 5 or abs(s.sum() - l.sum()) > 0.05 * s.sum() + 1: continue
        rows[sid].append((s, l)); names[sid] = r["Site Name"]
out = []
for sid, rr in rows.items():
    if len(rr) < 400: continue
    S = np.array([x[0] for x in rr]); L = np.array([x[1] for x in rr])
    car = L[:, 0] + L[:, 1]; hgv = L[:, 3]; mid = L[:, 2]
    A = np.column_stack([car, mid, hgv])
    H = []
    for j in range(len(SB)):
        coef, _ = nnls(A, S[:, j]); H.append(coef)
    H = np.array(H)                         # bins x {car, mid, hgv}
    h = H[:, 2] / H[:, 2].sum(); c = H[:, 0] / H[:, 0].sum()
    hgv_share = hgv.sum() / L.sum()
    out.append((sid, names[sid], len(rr), hgv_share, h[8], h[9], h[10], h[11], c[10], c[11], c[12]))
out.sort(key=lambda x: x[1])
print(len(out), "sites")
print("site name n hgvshare | HGV: 46-50 51-55 56-60 61-70 | car: 56-60 61-70 71-80")
for o in out: print("%s %-14s %5d %.2f | %.2f %.2f %.2f %.2f | %.2f %.2f %.2f" % (o[0], o[1][:14], *o[2:]))
r = np.array([o[6] / (o[5] + o[6] + 1e-9) for o in out])
print("HGV fraction above 55.5 mph among 51-60: median %.2f p10 %.2f p90 %.2f" % (np.median(r), np.percentile(r, 10), np.percentile(r, 90)))
json.dump([list(map(lambda v: v if isinstance(v, str) else float(v), o)) for o in out], open("probe.json", "w"), indent=0)
