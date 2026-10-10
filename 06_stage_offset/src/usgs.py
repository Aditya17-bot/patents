"""USGS open water-data client with a disk cache. No key, no login.

Sources (all public):
  - Instantaneous values (15-min gage height 00065, discharge 00060):
      https://waterservices.usgs.gov/nwis/iv/
  - Field measurements (measured discharge and mean gage height per field visit):
      https://api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements/items
  - Monitoring-location metadata (drainage area, coordinates):
      https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations/items
  - Stage-discharge ratings (base rating table, offset, rating start):
      https://waterdata.usgs.gov/nwisweb/get_ratings
  - River topology (gauges up/down the same mainstem):
      https://api.water.usgs.gov/nldi/

Every response is cached under data/usgs/; reruns never re-hit the network.
"""
import datetime as dt
import gzip
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "usgs")
UA = "patent4-research/1.0 (python urllib)"


def _get(url, kind, binary=False, tries=8):
    os.makedirs(os.path.join(CACHE, kind), exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()[:20]
    path = os.path.join(CACHE, kind, key + ".gz")
    if os.path.exists(path):
        with gzip.open(path, "rb") as f:
            raw = f.read()
    elif os.environ.get("USGS_OFFLINE"):
        raise RuntimeError("not cached (offline): " + url)
    else:
        err = None
        waited = 0
        i = 0
        while True:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                           "Accept-Encoding": "identity"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    raw = r.read()
                break
            except urllib.error.HTTPError as e:  # 429: hourly request quota of the open API
                err = e
                if e.code == 429 and waited < 3600:
                    ra = int(e.headers.get("Retry-After") or 60)
                    time.sleep(ra + 2)
                    waited += ra + 2
                    continue
                i += 1
            except Exception as e:  # network hiccup or 503
                err = e
                i += 1
            if i >= tries:
                raise RuntimeError("fetch failed %s: %s" % (url, err))
            time.sleep(4 * i)
        with gzip.open(path, "wb") as f:
            f.write(raw)
        with open(os.path.join(CACHE, kind, "index.tsv"), "a", encoding="utf-8") as f:
            f.write(key + "\t" + url + "\n")
    return raw if binary else raw.decode("utf-8", "replace")


def _parse_t(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def iv(site, param, start, end):
    """Instantaneous values as a list of (utc datetime, float, qualifiers).

    RDB (tab-separated) is used: half the size of JSON from the historical IV server.
    Only the first (primary) time series of the parameter is kept."""
    q = urllib.parse.urlencode({"format": "rdb", "sites": site, "parameterCd": param,
                                "startDT": start, "endDT": end, "siteStatus": "all"})
    txt = _get("https://nwis.waterservices.usgs.gov/nwis/iv/?" + q, "iv")
    out, head, col = [], None, None
    tz_off = {"EST": -5, "EDT": -4, "CST": -6, "CDT": -5, "MST": -7, "MDT": -6, "PST": -8,
              "PDT": -7, "AKST": -9, "AKDT": -8, "HST": -10, "UTC": 0, "GMT": 0}
    for ln in txt.splitlines():
        if ln.startswith("#") or not ln:
            continue
        p = ln.split("	")
        if head is None:
            head = p
            vcols = [i for i, h in enumerate(head) if h.endswith("_" + param)]
            if not vcols:
                return []
            col = vcols[0]
            continue
        if p[0] == "5s":
            continue
        if len(p) <= col + 1 or p[0] != "USGS":
            continue
        try:
            x = float(p[col])
        except ValueError:
            continue
        t = dt.datetime.strptime(p[2], "%Y-%m-%d %H:%M")
        off = tz_off.get(p[3], 0)
        t = (t - dt.timedelta(hours=off)).replace(tzinfo=dt.timezone.utc)
        out.append((t, x, tuple(p[col + 1].split(","))))
    out.sort(key=lambda r: r[0])
    return out


def _ogc(collection, params):
    feats = []
    params = dict(params, f="json", limit=10000)
    url = ("https://api.waterdata.usgs.gov/ogcapi/v0/collections/%s/items?" % collection
           + urllib.parse.urlencode(params))
    while url:
        d = json.loads(_get(url, collection))
        feats += d.get("features", [])
        url = None
        for ln in d.get("links", []):
            if ln.get("rel") == "next":
                url = ln["href"]
    return feats


def field_visits(site):
    """Field visits with a measured discharge: list of dicts sorted by time."""
    feats = _ogc("field-measurements", {"monitoring_location_id": "USGS-" + site})
    by = {}
    for f in feats:
        p = f["properties"]
        v = by.setdefault(p["field_visit_id"], {"visit": p["field_visit_id"]})
        try:
            val = float(p["value"])
        except (TypeError, ValueError):
            continue
        if p["reading_type"] == "Discharge" and p["parameter_code"] == "00060":
            v["q"] = val
            v["time"] = _parse_t(p["time"])
            v["rated"] = p.get("measurement_rated")
            v["control"] = p.get("control_condition")
        elif p["reading_type"] == "MeanGageHeight" and p["parameter_code"] == "00065":
            v["gh"] = val
            v.setdefault("time_gh", _parse_t(p["time"]))
            if p.get("control_condition"):
                v.setdefault("control", p.get("control_condition"))
    out = [v for v in by.values() if "q" in v and "gh" in v]
    out.sort(key=lambda v: v["time"])
    return out


def location(site):
    feats = _ogc("monitoring-locations", {"id": "USGS-" + site})
    return feats[0]["properties"] if feats else {}


def rating(site, file_type="base"):
    """Parse a NWIS rating file: header fields plus the (stage, shift, discharge) table."""
    q = urllib.parse.urlencode({"site_no": site, "file_type": file_type})
    txt = _get("https://waterdata.usgs.gov/nwisweb/get_ratings?" + q, "ratings")
    head, rows = {}, []
    lines = txt.splitlines()
    i = 0
    for i, ln in enumerate(lines):
        if ln.startswith("#"):
            s = ln[3:].strip() if ln.startswith("# //") else ln[1:].strip()
            if s.startswith("RATING ID"):
                head["rating_id"] = s.split('"')[1].strip()
                head["rating_remarks_line"] = s
            elif s.startswith("RATING OFFSET1"):
                head["offset"] = float(s.split("=")[1])
            elif s.startswith("RATING_DATETIME BEGIN") and "begin" not in head:
                head["begin"] = s.split("BEGIN=")[1].split()[0]
            elif s.startswith("RATING REMARKS"):
                head["remarks"] = s.split("=", 1)[1].strip().strip('"')
            elif s.startswith("STATION NAME"):
                head["name"] = s.split('"')[1].strip()
            elif s.startswith("RETRIEVED"):
                head["retrieved"] = s.split(":", 1)[1].strip()
            continue
        if ln.startswith("INDEP"):
            break
    for ln in lines[i + 2:]:
        p = ln.split("\t")
        if len(p) < 3:
            continue
        try:
            rows.append((float(p[0]), float(p[1] or 0.0), float(p[2])))
        except ValueError:
            continue
    head["table"] = rows
    return head


def nldi(site, mode="UM", distance=400):
    """Gauges on the same mainstem: mode UM (upstream main) or DM (downstream main)."""
    url = ("https://api.water.usgs.gov/nldi/linked-data/nwissite/USGS-%s/navigation/%s/nwissite?distance=%d"
           % (site, mode, distance))
    d = json.loads(_get(url, "nldi"))
    out = []
    for f in d.get("features", []):
        p = f["properties"]
        out.append({"site": p["identifier"].replace("USGS-", ""), "name": p.get("name"),
                    "comid": p.get("comid"), "mainstem": p.get("mainstem"),
                    "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1]})
    return out


def flowline_measure(site):
    """Position of a gauge along its NHD flowline network (for ordering), via NLDI feature."""
    url = "https://api.water.usgs.gov/nldi/linked-data/nwissite/USGS-%s?f=json" % site
    d = json.loads(_get(url, "nldi"))
    f = d["features"][0]
    return f["properties"]


def dv(sites, start, end, params=("00060", "00065"), stats=("00001", "00002", "00003")):
    """Daily values for several sites: {site: {param: {stat: {date: (value, code)}}}}.

    Only the first time series of each parameter/statistic at a site is kept."""
    out = {}
    for i in range(0, len(sites), 5):
        chunk = sites[i:i + 5]
        q = urllib.parse.urlencode({"format": "rdb", "sites": ",".join(chunk),
                                    "parameterCd": ",".join(params), "statCd": ",".join(stats),
                                    "startDT": start, "endDT": end, "siteStatus": "all"})
        txt = _get("https://waterservices.usgs.gov/nwis/dv/?" + q, "dv")
        head = None
        cols = {}
        for ln in txt.splitlines():
            if ln.startswith("#") or not ln:
                if ln.startswith("# Data provided for site"):
                    head = None
                continue
            p = ln.split("\t")
            if p[0] == "agency_cd":
                head = p
                cols = {}
                for j, h in enumerate(head):
                    parts = h.split("_")
                    if len(parts) == 3 and parts[1] in params and parts[2] in stats:
                        key = (parts[1], parts[2])
                        if key not in cols:
                            cols[key] = j
                continue
            if head is None or p[0] != "USGS":
                continue
            site = p[1]
            d = p[2]
            for (par, st), j in cols.items():
                if j < len(p) and p[j] not in ("", "Ice", "Eqp", "Bkw", "Dis", "Ssn", "Mnt", "***"):
                    try:
                        val = float(p[j])
                    except ValueError:
                        continue
                    code = p[j + 1] if j + 1 < len(p) else ""
                    out.setdefault(site, {}).setdefault(par, {}).setdefault(st, {})[d] = (val, code)
    return out
