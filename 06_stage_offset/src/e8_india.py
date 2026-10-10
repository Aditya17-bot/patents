"""E8: applicability to Indian river gauging networks (CAMELS-IND, CWC gauge sites).

Source: CAMELS-IND (Mangukiya et al., ESSD 17, 461-2025, doi 10.5194/essd-17-461-2025),
daily observed streamflow of 242 Central Water Commission gauge sites, 1980-2020, as
mirrored on Kaggle (abhisingh2615/camels-ind-india-streamflow) and cached under
data/kaggle/camels_ind/. The record has discharge but no stage, so only the parts of the
method that use discharge are run here:

  1. pair finding from the CWC river path (same river string) ordered by drainage area,
     consecutive sites with incremental area <= MAX_INCR (claim 3);
  2. travel-time lag (-2..+2 days) and coupling of daily ln Q after the lag (claim 3);
  3. the noise floor of the neighbour departure: for windows of WIN_D days whose centres
     are GAP days apart, the departure of the middle window's median log ratio from the
     mean of the outer two (the discharge-unit analogue of D - D_lin over one visit
     interval). This bounds how small an offset departure the neighbour can resolve.

The same floor is computed for the admitted US directions on their published records
(which contain real offset departures, so it is an upper bound there).

Output: results/e8_india.json
"""
import csv
import datetime as dt
import json
import math
import os

import numpy as np

import network as NET
import probe_daily as PD

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CI = os.path.join(ROOT, "data", "kaggle", "camels_ind")
MAX_INCR = NET.MAX_INCR
MIN_COUPLING = 0.95
WIN_D = PD.WIN_D
STEADY_LN = 0.10        # day-to-day change of ln Q accepted as steady (no stage available)


def shift(d, n):
    return (dt.date.fromisoformat(d) + dt.timedelta(days=n)).isoformat()


def load_india():
    names = {r["gauge_id"]: r for r in csv.DictReader(open(os.path.join(CI, "attributes_csv", "camels_ind_name.csv")))}
    topo = {r["gauge_id"]: r for r in csv.DictReader(open(os.path.join(CI, "attributes_csv", "camels_ind_topo.csv")))}
    rows = list(csv.reader(open(os.path.join(CI, "streamflow_timeseries", "streamflow_observed.csv"))))
    hdr = rows[0]
    q = {g: {} for g in hdr[3:]}
    for line in rows[1:]:
        d = "%s-%02d-%02d" % (line[0], int(line[1]), int(line[2]))
        for g, v in zip(hdr[3:], line[3:]):
            if v:
                try:
                    x = float(v)
                except ValueError:
                    continue
                if x > 0:
                    q[g][d] = x
    return names, topo, q


def lag_coupling(qx, qy):
    best = None
    for lag in (-2, -1, 0, 1, 2):
        a = [(math.log(qx[d]), math.log(qy[shift(d, -lag)])) for d in qx if shift(d, -lag) in qy]
        if len(a) < 300:
            continue
        c = float(np.corrcoef(np.array(a).T)[0, 1])
        if best is None or c > best[1]:
            best = (lag, c, len(a))
    return best


def departure_floor(qx, qy, lag, gap):
    """|median log ratio of middle window - mean of the two outer windows|, windows WIN_D
    days long and gap/2 days apart, on steady days, stepping one window at a time."""
    days = sorted(d for d in qx if shift(d, -lag) in qy)
    if not days:
        return []
    y = {}
    for d in days:
        dp, dn = shift(d, -1), shift(d, 1)
        if dp in qx and dn in qx and abs(math.log(qx[d] / qx[dp])) <= STEADY_LN and \
                abs(math.log(qx[dn] / qx[d])) <= STEADY_LN:
            y[d] = math.log(qy[shift(d, -lag)]) - math.log(qx[d])

    def med(d0):
        v = [y[shift(d0, i)] for i in range(WIN_D) if shift(d0, i) in y]
        return float(np.median(v)) if len(v) >= PD.MIN_DAYS else None

    out = []
    d0 = days[0]
    end = days[-1]
    half = gap // 2
    while shift(d0, gap + WIN_D) <= end:
        a, m, b = med(d0), med(shift(d0, half)), med(shift(d0, gap))
        if a is not None and m is not None and b is not None:
            out.append(abs(m - 0.5 * (a + b)))
        d0 = shift(d0, WIN_D)
    return out


def main():
    names, topo, q = load_india()
    by = {}
    for g, r in names.items():
        if q.get(g):
            by.setdefault(r["cwc_river"], []).append(g)
    daily = json.load(open(os.path.join(ROOT, "results", "daily.json")))
    gaps = sorted(w["gap_days"] for r in daily["results"] if r.get("rows") and r.get("coupling", 0) >= MIN_COUPLING
                  for w in r["rows"])
    GAP = gaps[len(gaps) // 2]
    pairs, admitted = [], []
    for riv, gs in by.items():
        gs = sorted(gs, key=lambda g: float(topo[g]["cwc_area"]))
        for a, b in zip(gs, gs[1:]):
            incr = float(topo[b]["cwc_area"]) / float(topo[a]["cwc_area"]) - 1.0
            pairs.append((riv, a, b, incr))
            if incr > MAX_INCR:
                continue
            for x, y in ((b, a), (a, b)):
                lc = lag_coupling(q[x], q[y])
                if lc is None:
                    continue
                rec = {"river": riv, "basin": names[x]["river_basin"], "x": x, "y": y,
                       "x_name": names[x]["cwc_site_name"], "y_name": names[y]["cwc_site_name"],
                       "x_area": float(topo[x]["cwc_area"]), "y_area": float(topo[y]["cwc_area"]),
                       "incr": round(incr, 4), "lag": lc[0], "coupling": round(lc[1], 4), "days": lc[2],
                       "lat": float(topo[x]["cwc_lat"]), "lon": float(topo[x]["cwc_lon"]),
                       "lat_y": float(topo[y]["cwc_lat"]), "lon_y": float(topo[y]["cwc_lon"])}
                if lc[1] >= MIN_COUPLING:
                    fl = departure_floor(q[x], q[y], lc[0], GAP)
                    rec["floor_n"] = len(fl)
                    rec["floor_median"] = round(float(np.median(fl)), 4) if fl else None
                    rec["floor_p90"] = round(float(np.percentile(fl, 90)), 4) if fl else None
                    rec["floor_all"] = [round(v, 5) for v in fl]
                    admitted.append(rec)
                else:
                    rec["floor_n"] = 0
                pairs_rec = rec
            # keep only admitted detail; candidate counts are below
    all_floor = [v for r in admitted for v in r["floor_all"]]

    # same statistic on the admitted US directions (published records: an upper bound)
    import usgs
    P = json.load(open(os.path.join(ROOT, "results", "pairs.json")))
    coup = json.load(open(os.path.join(ROOT, "results", "coupling.json")))
    sites = sorted({s for p in P["pairs"] for s in (p["up"], p["down"])})
    DV = usgs.dv(sites, PD.START, PD.END, stats=("00003",))
    us_floor = []
    for x, y, incr, lag, lr, c in coup:
        if c < MIN_COUPLING:
            continue
        qx = {d: v for d, v in PD.series(DV, x, "00060").items() if v > 0}
        qy = {d: v for d, v in PD.series(DV, y, "00060").items() if v > 0}
        us_floor += departure_floor(qx, qy, lag, GAP)
    out = {"source": "CAMELS-IND (Mangukiya et al. 2025, ESSD 17:461), CWC observed daily streamflow 1980-2020; "
                     "Kaggle mirror abhisingh2615/camels-ind-india-streamflow",
           "stations_with_flow": sum(1 for g in q if q[g]),
           "same_river_consecutive_pairs": len(pairs),
           "pairs_incr_ok": sum(1 for p in pairs if p[3] <= MAX_INCR),
           "admitted_directions": len(admitted),
           "admitted_pairs": len({tuple(sorted((r["x"], r["y"]))) for r in admitted}),
           "rivers": sorted({r["river"] for r in admitted}),
           "basins": sorted({r["basin"] for r in admitted}),
           "gap_days": GAP, "win_d": WIN_D, "steady_ln": STEADY_LN,
           "india_floor": {"n": len(all_floor), "median": round(float(np.median(all_floor)), 4),
                           "p90": round(float(np.percentile(all_floor, 90)), 4)},
           "us_floor_upper": {"n": len(us_floor), "median": round(float(np.median(us_floor)), 4),
                              "p90": round(float(np.percentile(us_floor, 90)), 4)},
           "admitted": [{k: v for k, v in r.items() if k != "floor_all"} for r in admitted],
           "candidates": [{"river": p[0], "a": p[1], "b": p[2], "incr": round(p[3], 4)} for p in pairs]}
    # coupling of every candidate direction with incr <= MAX_INCR, for the figure
    cand = []
    for riv, a, b, incr in pairs:
        lc = lag_coupling(q[b], q[a])
        if lc:
            cand.append({"incr": round(incr, 4), "coupling": round(lc[1], 4)})
    out["candidates_coupling"] = cand
    json.dump(out, open(os.path.join(ROOT, "results", "e8_india.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("admitted", "candidates", "candidates_coupling")}, indent=1))
    for r in out["admitted"]:
        print(r["river"], r["x_name"], "<-", r["y_name"], r["incr"], r["lag"], r["coupling"], r["floor_median"])


if __name__ == "__main__":
    main()
