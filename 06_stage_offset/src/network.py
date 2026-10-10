"""Find pairs of stream gauges on the same river mainstem, from topology, not by hand.

Each outlet gauge is navigated upstream along its mainstem with NLDI. Every gauge found
is checked for 15-minute discharge (00060) and gage height (00065) over the study
period and for its drainage area. Consecutive gauges (ordered by drainage area) form a
pair when the downstream drainage area exceeds the upstream one by at most MAX_INCR.

Output: results/pairs.json
"""
import json
import os
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import usgs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "pairs.json")

START, END = "2023-10-01", "2026-09-30"  # water years 2024-2026
MAX_INCR = 0.20                          # incremental drainage area <= 20 % of upstream

# Outlet gauges of large rivers across the conterminous US; NLDI supplies everything
# upstream on the same mainstem.
OUTLETS = [
    "06805500",  # Platte R at Louisville NE
    "06892350",  # Kansas R at DeSoto KS
    "07263450",  # Arkansas R at Murray Dam nr Little Rock AR
    "08116650",  # Brazos R nr Rosharon TX
    "08162000",  # Colorado R at Wharton TX
    "08475000",  # Rio Grande nr Brownsville TX
    "06934500",  # Missouri R at Hermann MO
    "03611500",  # Ohio R at Metropolis IL
    "01578310",  # Susquehanna R at Conowingo MD
    "01463500",  # Delaware R at Trenton NJ
    "01646500",  # Potomac R nr Washington DC
    "02035000",  # James R at Cartersville VA
    "11447650",  # Sacramento R at Freeport CA
    "11303500",  # San Joaquin R nr Vernalis CA
    "13269000",  # Snake R at Weiser ID
    "06329500",  # Yellowstone R nr Sidney MT
    "05082500",  # Red R of the North at Grand Forks ND
    "05330000",  # Minnesota R nr Jordan MN
    "05407000",  # Wisconsin R at Muscoda WI
    "05465500",  # Iowa R at Wapello IA
    "05490500",  # Des Moines R at Keosauqua IA
    "05586100",  # Illinois R at Valley City IL
    "03377500",  # Wabash R at Mt Carmel IL
    "06485500",  # Big Sioux R at Akron IA
    "06478500",  # James R nr Scotland SD
    "01184000",  # Connecticut R at Thompsonville CT
    "02489500",  # Pearl R nr Bogalusa LA
    "08066500",  # Trinity R at Romayor TX
    "08176500",  # Guadalupe R at Victoria TX
    "14191000",  # Willamette R at Salem OR
    "07355500",  # Red R at Alexandria LA
    "02226000",  # Altamaha R at Doctortown GA
    "02105769",  # Cape Fear R at Lock 1 nr Kelly NC
    "03234500",  # Scioto R at Higby OH
    "04193500",  # Maumee R at Waterville OH
    "12510500",  # Yakima R at Kiona WA
    "09380000",  # Colorado R at Lees Ferry AZ
    "06775900",  # Dismal R? (Loup system) -- harmless if absent
    "06793000",  # Loup R nr Genoa NE
    "06800500",  # Elkhorn R at Waterloo NE
    "06818000",  # Missouri R at St Joseph MO
    "07144100",  # Little Arkansas R nr Sedgwick KS
    "07331000",  # Washita R nr Dickson OK
    "07228000",  # Canadian R nr Calvin OK
    "07160000",  # Cimarron R nr Ripley OK
    "06853500",  # Republican R nr Hardy NE
    "06887500",  # Kansas R at Wamego KS
]


def site_rdb(sites, extra):
    q = dict({"format": "rdb", "sites": ",".join(sites), "siteStatus": "all"}, **extra)
    txt = usgs._get("https://waterservices.usgs.gov/nwis/site/?" + urllib.parse.urlencode(q), "site")
    rows, head = [], None
    for ln in txt.splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        p = ln.split("\t")
        if head is None:
            head = p
            continue
        if p[0].endswith("s") and len(p[0]) < 4:
            continue  # format row
        rows.append(dict(zip(head, p)))
    return rows


def main():
    mainstem = {}
    def nav(o):
        try:
            return o, usgs.nldi(o, "UM", 3000)
        except Exception as e:
            print("nldi fail", o, e)
            return o, []
    with ThreadPoolExecutor(6) as ex:
        for o, lst in ex.map(nav, OUTLETS):
            ids = {r["site"] for r in lst if r["site"].isdigit() and len(r["site"]) == 8}
            ids.add(o)
            mainstem[o] = sorted(ids)
    allsites = sorted({s for v in mainstem.values() for s in v})
    print("gauges on mainstems:", len(allsites))

    info, series = {}, {}
    for i in range(0, len(allsites), 80):
        chunk = allsites[i:i + 80]
        for r in site_rdb(chunk, {"siteOutput": "expanded"}):
            try:
                da = float(r.get("drain_area_va") or "nan")
            except ValueError:
                da = float("nan")
            info[r["site_no"]] = {"name": r.get("station_nm"), "da": da,
                                  "lat": float(r.get("dec_lat_va") or 0), "lon": float(r.get("dec_long_va") or 0),
                                  "state": r.get("state_cd"), "huc": r.get("huc_cd")}
        for r in site_rdb(chunk, {"seriesCatalogOutput": "true", "outputDataTypeCd": "iv"}):
            if r.get("parm_cd") in ("00060", "00065"):
                series.setdefault(r["site_no"], {})[r["parm_cd"]] = (r.get("begin_date", ""), r.get("end_date", ""))

    def ok(s):
        sr = series.get(s, {})
        if "00060" not in sr or "00065" not in sr:
            return False
        return all(sr[p][0] <= START and sr[p][1] >= "2026-09-01" for p in ("00060", "00065"))

    pairs, seen = [], set()
    for o, ids in mainstem.items():
        good = [s for s in ids if s in info and info[s]["da"] == info[s]["da"] and ok(s)]
        good.sort(key=lambda s: info[s]["da"])
        for a, b in zip(good, good[1:]):
            if (a, b) in seen:
                continue
            ra = info[b]["da"] / info[a]["da"] - 1.0
            if 0.0 <= ra <= MAX_INCR:
                seen.add((a, b))
                pairs.append({"up": a, "down": b, "incr": round(ra, 4), "outlet": o,
                              "up_name": info[a]["name"], "down_name": info[b]["name"],
                              "up_da": info[a]["da"], "down_da": info[b]["da"]})
    print("pairs:", len(pairs))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"start": START, "end": END, "max_incr": MAX_INCR, "n_mainstem_gauges": len(allsites),
               "pairs": pairs, "info": {s: info[s] for s in info}}, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
