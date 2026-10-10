"""Pair each long-running EA conductivity sonde with a co-located Water Quality Archive point.

A sonde station qualifies when it ran for at least MIN_DAYS. Its partner is the nearest
sampling point within MAX_KM; the pair is kept when the point holds at least MIN_SAMPLES
laboratory conductivity results (determinand 0077, conductivity at 25 C) inside the
sonde's period. Output: results/sites.json
"""
import datetime as dt
import json
import os
from concurrent.futures import ThreadPoolExecutor

import ea

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "sites.json")
MIN_DAYS, MAX_KM, MIN_SAMPLES = 365, 0.3, 8
DET = "0077"                       # conductivity at 25 C, uS/cm


def period(s):
    a = dt.date.fromisoformat(s["dateOpened"][:10]) if s.get("dateOpened") else None
    b = dt.date.fromisoformat(s["dateClosed"][:10]) if s.get("dateClosed") else dt.date(2026, 9, 30)
    return a, b


def one(s):
    a, b = period(s)
    try:
        pts = ea.points_near(s["lat"], s["long"], MAX_KM)
    except Exception as e:
        return None
    best = None
    for p in pts:
        wkt = p.get("geometry", {}).get("asWKT", "")
        best = p if best is None else best
    if not pts:
        return None
    rows = []
    for p in pts[:3]:                   # nearest few points; the API orders by distance
        try:
            sm = [x for x in ea.samples(p["notation"], DET) if a <= x[0].date() <= b]
        except Exception:
            continue
        rows.append((len(sm), p["notation"], p.get("altLabel")))
    rows.sort(reverse=True)
    if not rows or rows[0][0] < MIN_SAMPLES:
        return None
    return {"station": s["notation"], "label": s.get("label"), "lat": s["lat"], "lon": s["long"],
            "opened": str(a), "closed": str(b), "point": rows[0][1], "point_label": rows[0][2],
            "n_samples": rows[0][0]}


def main():
    st = [s for s in ea.sonde_stations("conductivity") if s.get("dateOpened")]
    st = [s for s in st if (period(s)[1] - period(s)[0]).days >= MIN_DAYS]
    print("sondes running >= %d days: %d" % (MIN_DAYS, len(st)))
    with ThreadPoolExecutor(6) as ex:
        out = [r for r in ex.map(one, st) if r]
    out.sort(key=lambda r: -r["n_samples"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print("paired sites:", len(out), "samples:", sum(r["n_samples"] for r in out))
    for r in out[:15]:
        print(r["station"], r["label"], r["opened"], r["closed"], r["point"], r["n_samples"])


if __name__ == "__main__":
    main()
