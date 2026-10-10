"""Client for the National Highways WebTRIS open API.

No API key, no registration. Responses are cached on disk so repeated runs of the
prototype do not re-hit the service.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request

API = "https://webtris.nationalhighways.co.uk/api/v1.0"
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "webtris")


def _get(path, cache_name, retries=3):
    os.makedirs(CACHE, exist_ok=True)
    cache_path = os.path.join(CACHE, cache_name)
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as fh:
            return json.load(fh)

    url = "%s/%s" % (API, path)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                body = resp.read().decode("utf-8")
            break
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)

    if not body.strip():
        data = {}
    else:
        data = json.loads(body)

    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return data


def sites(active_only=True):
    """All measurement sites, with the road, direction and link id parsed out.

    Site names look like:
        MIDAS site at M4/2295A2 priority 1 on link 105009001; GPS Ref: 502816;178156; Westbound
    """
    data = _get("sites", "sites.json")
    out = []
    for s in data.get("sites", []):
        if active_only and s.get("Status") != "Active":
            continue
        name = s.get("Name", "")
        out.append({
            "id": s["Id"],
            "name": name,
            "description": s.get("Description", ""),
            "lat": s.get("Latitude"),
            "lon": s.get("Longitude"),
            "kind": _match(r"^(\w+) site at", name),
            "road": _match(r"site at ([A-Za-z0-9]+)/", name),
            "marker": _match(r"site at [A-Za-z0-9]+/([A-Za-z0-9]+)", name),
            "link": _match(r"on link (\d+)", name),
            "direction": _match(r";\s*([A-Za-z-]+)\s*$", name),
        })
    return out


def daily(site_id, start, end, page_size=1000, max_pages=50):
    """15-minute interval records for one site.

    start/end are DDMMYYYY strings. Returns a list of row dicts as the API gives
    them; parsing into numbers is left to the caller so blank values stay visible.
    """
    rows = []
    for page in range(1, max_pages + 1):
        path = ("reports/Daily?sites=%s&start_date=%s&end_date=%s&page=%d&page_size=%d"
                % (site_id, start, end, page, page_size))
        cache_name = "daily_%s_%s_%s_p%d.json" % (site_id, start, end, page)
        data = _get(path, cache_name)
        batch = data.get("Rows", [])
        rows.extend(batch)
        links = data.get("Header", {}).get("links", [])
        if not any(l.get("rel") == "nextPage" for l in links) or not batch:
            break
    return rows


def _match(pattern, text):
    m = re.search(pattern, text)
    return m.group(1) if m else None


if __name__ == "__main__":
    all_sites = sites()
    print("active sites: %d" % len(all_sites))

    by_road = {}
    for s in all_sites:
        if s["road"]:
            by_road.setdefault(s["road"], []).append(s)
    top = sorted(by_road.items(), key=lambda kv: -len(kv[1]))[:12]
    print("busiest roads by site count:")
    for road, group in top:
        dirs = sorted({s["direction"] for s in group if s["direction"]})
        print("  %-6s %4d sites  directions=%s" % (road, len(group), ",".join(dirs)))
