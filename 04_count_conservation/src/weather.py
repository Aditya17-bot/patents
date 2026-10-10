"""Historical weather for the corridor, from the Open-Meteo archive API.

Free, no key, no registration, and it accepts any latitude/longitude, so it joins to
detector sites directly by their coordinates. Sites are snapped to a coarse grid before
querying, because a corridor has hundreds of detectors but rainfall does not vary
meaningfully between two detectors 400 m apart.
"""

import json
import os
import time
import urllib.error
import urllib.request

API = "https://archive-api.open-meteo.com/v1/archive"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "weather")

GRID = 0.25  # degrees; about 25 km, far finer than a rain band


def snap(lat, lon):
    return (round(lat / GRID) * GRID, round(lon / GRID) * GRID)


def hourly(lat, lon, start, end, retries=3):
    """Hourly precipitation, wind and visibility for one grid cell.

    start/end are ISO dates. Returns {iso_hour: {"precip": mm, "wind": kph, "vis": m}}.
    """
    glat, glon = snap(lat, lon)
    os.makedirs(CACHE, exist_ok=True)
    name = "w_%.2f_%.2f_%s_%s.json" % (glat, glon, start, end)
    path = os.path.join(CACHE, name)

    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    url = ("%s?latitude=%.4f&longitude=%.4f&start_date=%s&end_date=%s"
           "&hourly=precipitation,wind_speed_10m,visibility&timezone=UTC"
           % (API, glat, glon, start, end))
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            break
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)

    h = raw.get("hourly", {})
    out = {}
    for i, t in enumerate(h.get("time", [])):
        out[t] = {
            "precip": h.get("precipitation", [None] * (i + 1))[i],
            "wind": h.get("wind_speed_10m", [None] * (i + 1))[i],
            "vis": h.get("visibility", [None] * (i + 1))[i],
        }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    return out


def precipitation_by_interval(corridor, sites_meta, start, end):
    """Precipitation in mm aligned to the corridor's 15-minute columns, per site.

    Returns rain[row][column] = mm in that hour. The hourly figure is held across the
    four intervals inside the hour.
    """
    import numpy as np

    rain = np.zeros(corridor.shape)
    cache = {}
    for i, sid in enumerate(corridor.site_ids):
        meta = sites_meta.get(sid)
        if not meta or meta.get("lat") is None:
            continue
        cell = snap(meta["lat"], meta["lon"])
        if cell not in cache:
            cache[cell] = hourly(meta["lat"], meta["lon"], start, end)
        series = cache[cell]
        for j, (date, slot) in enumerate(corridor.keys):
            hour = "%sT%02d:00" % (date, slot // 4)
            rec = series.get(hour)
            if rec and rec["precip"] is not None:
                rain[i, j] = rec["precip"]
    return rain
