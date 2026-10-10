"""Pair EA sondes that carry both an ammonium ISE and a conductivity cell with a co-located
Water Quality Archive point holding laboratory ammoniacal-nitrogen results.

A sonde qualifies when it ran for at least MIN_DAYS and reports ammonium (amm-i-subdaily-mgL)
and conductivity (cond-i-subdaily-uS). Its partner is the sampling point within MAX_KM (the
nearest three are tried) with the most determinand-0111 results inside the sonde's period;
the pair is kept with at least MIN_SAMPLES. Output: results/sites_amm.json
"""
import datetime as dt
import json
import os
from concurrent.futures import ThreadPoolExecutor

import ea

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "sites_amm.json")
MIN_DAYS, MAX_KM, MIN_SAMPLES = 180, 0.3, 8
DET = "0111"                       # ammoniacal nitrogen as N, mg/L


def period(s):
    a = dt.date.fromisoformat(s["dateOpened"][:10])
    b = dt.date.fromisoformat(s["dateClosed"][:10]) if s.get("dateClosed") else dt.date(2026, 9, 30)
    return a, b


def measures(s):
    return {m["@id"].rsplit("/", 1)[1].replace(s["notation"] + "-", "") for m in s.get("measures", [])
            if isinstance(m, dict) and "@id" in m}


def one(s):
    a, b = period(s)
    try:
        pts = ea.points_near(s["lat"], s["long"], MAX_KM)
    except Exception:
        return None
    rows = []
    for p in pts[:3]:
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
    st = [s for s in ea.sonde_stations("ammonium") if s.get("dateOpened")]
    print("ammonium sonde stations:", len(st))
    st = [s for s in st if (period(s)[1] - period(s)[0]).days >= MIN_DAYS]
    st = [s for s in st if {"amm-i-subdaily-mgL", "cond-i-subdaily-uS"} <= measures(s)]
    print("running >= %d days with ammonium and conductivity: %d" % (MIN_DAYS, len(st)))
    with ThreadPoolExecutor(6) as ex:
        out = [r for r in ex.map(one, st) if r]
    out.sort(key=lambda r: -r["n_samples"])
    json.dump(out, open(OUT, "w"), indent=1)
    print("paired sites:", len(out), "lab samples in sonde periods:", sum(r["n_samples"] for r in out))


if __name__ == "__main__":
    main()
