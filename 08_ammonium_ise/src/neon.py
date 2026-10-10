"""NEON open-data client with a disk cache. No key, no login.

Sources (all public, https://data.neonscience.org/api/v0/):
  - DP1.20288.001 Water quality: in-situ multisonde, 1-min at wadeable streams, NOT corrected
    for sensor drift (Quick Start Guide, prior_art_raw/neon/qsg_wq.txt).
  - DP1.20093.001 Chemical properties of surface water: grab samples, laboratory and field
    specific conductance.
  - Maintenance records of the sondes (cleaning, swap, calibration).

Every response is cached under data/neon/; reruns never re-hit the network.
"""
import csv
import gzip
import hashlib
import io
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "neon")
API = "https://data.neonscience.org/api/v0"
UA = "patent8-research/1.0 (python urllib)"


def _get(url, kind, tries=6):
    os.makedirs(os.path.join(CACHE, kind), exist_ok=True)
    key = hashlib.sha1(url.split("?")[0].encode() if "X-Amz" in url else url.encode()).hexdigest()[:20]
    path = os.path.join(CACHE, kind, key + ".gz")
    if os.path.exists(path):
        with gzip.open(path, "rb") as f:
            return f.read()
    if os.environ.get("NEON_OFFLINE"):
        raise RuntimeError("not cached (offline): " + url)
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as r:
                raw = r.read()
            break
        except Exception as e:          # throttling (429) or a network hiccup
            err = e
            time.sleep(5 * (i + 1))
    else:
        raise RuntimeError("fetch failed %s: %s" % (url, err))
    with gzip.open(path, "wb") as f:
        f.write(raw)
    with open(os.path.join(CACHE, kind, "index.tsv"), "a", encoding="utf-8") as f:
        f.write(key + "\t" + url.split("?")[0] + "\n")
    return raw


def months(dp, site):
    d = json.loads(_get("%s/products/%s" % (API, dp), "meta"))["data"]
    for s in d["siteCodes"]:
        if s["siteCode"] == site:
            return s["availableMonths"]
    return []


def files(dp, site, month, package="basic"):
    url = "%s/data/%s/%s/%s?package=%s" % (API, dp, site, month, package)
    d = json.loads(_get(url, "filelists"))["data"]
    return d["files"]


def table(dp, site, month, pattern, package="basic"):
    """Rows (dicts) of every CSV in the month whose name contains `pattern`."""
    out = []
    for f in files(dp, site, month, package):
        if pattern in f["name"] and f["name"].endswith(".csv"):
            raw = _get(f["url"], "csv_" + dp)
            out += list(csv.DictReader(io.StringIO(raw.decode("utf-8", "replace"))))
    return out


def file_names(dp, site, month, package="basic"):
    return [f["name"] for f in files(dp, site, month, package)]
