"""Cached NEON API downloads. Token read from C:\adi\patents\_secrets\neon_token.txt."""
import json, os, re, sys, urllib.request

TOKEN = open(r"C:\adi\patents\_secrets\neon_token.txt").read().strip()
CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "neon")


def _get(url, path):
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={"X-API-Token": TOKEN})
        with urllib.request.urlopen(req, timeout=120) as r, open(path + ".part", "wb") as f:
            f.write(r.read())
        os.replace(path + ".part", path)
    return path


def month_files(dp, site, month, pattern):
    """Download files of one product-site-month whose name matches pattern; return local paths."""
    d = os.path.join(CACHE, dp, site, month)
    os.makedirs(d, exist_ok=True)
    idx = _get(f"https://data.neonscience.org/api/v0/data/{dp}/{site}/{month}", os.path.join(d, "index.json"))
    files = json.load(open(idx, encoding="utf-8"))["data"]["files"]
    out = []
    for f in files:
        if re.search(pattern, f["name"]):
            out.append(_get(f["url"], os.path.join(d, f["name"])))
    return out


def available_months(dp, site):
    path = os.path.join(CACHE, dp + "_product.json")
    _get(f"https://data.neonscience.org/api/v0/products/{dp}", path)
    for s in (json.load(open(path, encoding="utf-8"))["data"]["siteCodes"] or []):
        if s["siteCode"] == site:
            return s["availableMonths"]
    return []


if __name__ == "__main__":
    dp, site, month, pat = sys.argv[1:5]
    for p in month_files(dp, site, month, pat):
        print(p)
