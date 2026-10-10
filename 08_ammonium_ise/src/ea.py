"""Environment Agency (England) open-data client with a disk cache. No key, no login.

Sources (Open Government Licence):
  - Hydrology API, water-quality sondes (raw, quality 'Unchecked'), 15-min readings:
      https://environment.data.gov.uk/hydrology/id/measures/{measure}/readings
  - Water Quality Archive API, spot samples with laboratory results:
      https://environment.data.gov.uk/water-quality/sampling-point/{point}/observation
    (JSON-LD only: Accept: application/ld+json)

Every response is cached under data/ea/; reruns never re-hit the network.
"""
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "ea")
HYD = "https://environment.data.gov.uk/hydrology"
WQ = "https://environment.data.gov.uk/water-quality"
UA = "patent8-research/1.0 (python urllib)"


def _get(url, kind, accept="application/json", tries=6):
    os.makedirs(os.path.join(CACHE, kind), exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()[:20]
    path = os.path.join(CACHE, kind, key + ".gz")
    if os.path.exists(path):
        with gzip.open(path, "rb") as f:
            return json.loads(f.read())
    if os.environ.get("EA_OFFLINE"):
        raise RuntimeError("not cached (offline): " + url)
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=300) as r:
                raw = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code in (400, 404, 422):
                raw = json.dumps({"error": e.code}).encode()
                break
            err = e
        except Exception as e:          # network hiccup
            err = e
        time.sleep(5 * (i + 1))
    else:
        raise RuntimeError("fetch failed %s: %s" % (url, err))
    with gzip.open(path, "wb") as f:
        f.write(raw)
    with open(os.path.join(CACHE, kind, "index.tsv"), "a", encoding="utf-8") as f:
        f.write(key + "\t" + url + "\n")
    return json.loads(raw)


def _items(d):
    it = d.get("items", [])
    return it if isinstance(it, list) else [it]


def sonde_stations(prop="conductivity"):
    d = _get("%s/id/stations.json?observedProperty=%s&_limit=5000" % (HYD, prop), "stations")
    return _items(d)


def readings(measure, start, end):
    """Readings of a hydrology measure as [(utc datetime, value, quality)], start/end ISO dates."""
    out = []
    y0, y1 = int(start[:4]), int(end[:4])
    for y in range(y0, y1 + 1):            # one request per calendar year keeps responses small
        a = max(start, "%d-01-01" % y)
        b = min(end, "%d-12-31" % y)
        url = ("%s/id/measures/%s/readings.json?mineq-date=%s&maxeq-date=%s&_limit=200000"
               % (HYD, measure, a, b))
        for r in _items(_get(url, "readings")):
            v = r.get("value")
            if v is None:
                continue
            t = dt.datetime.fromisoformat(r["dateTime"].replace("Z", ""))
            out.append((t, float(v), r.get("quality")))
    out.sort(key=lambda r: r[0])
    return out


def points_near(lat, lon, radius_km):
    url = "%s/sampling-point?latitude=%.6f&longitude=%.6f&radius=%s&limit=50" % (WQ, lat, lon, radius_km)
    return _get(url, "points", accept="application/ld+json").get("member", [])


def samples(point, determinand):
    """Lab results of one determinand at a sampling point:
    [(time, value, unit, below_detection_limit, sampling_purpose_code)]."""
    out, skip = [], 0
    while True:
        url = ("%s/sampling-point/%s/observation?determinand=%s&limit=250&skip=%d"
               % (WQ, point, determinand, skip))
        d = _get(url, "samples", accept="application/ld+json")
        m = d.get("member", [])
        for o in m:
            r = o.get("hasResult") or {}
            v = r.get("numericValue")
            if v is None:
                continue
            simple = str(o.get("hasSimpleResult") or "")
            try:
                purpose = o["hasSample"]["isResultOf"]["samplingPurpose"]["notation"]
            except (KeyError, TypeError):
                purpose = ""
            out.append((dt.datetime.fromisoformat(o["phenomenonTime"]), float(v),
                        o.get("hasUnit"), simple.startswith("<"), purpose))
        skip += len(m)
        if len(m) < 250 or skip >= d.get("totalItems", 0):
            break
    out.sort(key=lambda r: r[0])
    return out


def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))
