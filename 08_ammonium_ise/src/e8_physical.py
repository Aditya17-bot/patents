"""E8: physical and timing parameters of the correction as it would run at a station.

  - reading interval of the sondes (median and share at 15 minutes)
  - time between a laboratory sampling instant and the paired sonde reading (minutes)
  - processing time per new reading: insert the reading into a sorted 7-day window, drop the
    reading that left the window, read the 5th percentile, apply the correction (one core, timed
    over the full record of every sonde)
  - memory per sonde for the window (readings x 4-byte floats)
  - decision latency: the corrected reading and alarm are available within the same reporting
    interval as the raw reading (processing time against the interval)
Output: results/e8_physical.json
"""
import bisect
import datetime as dt
import statistics as S
import time

import core
import ea
import evidence as EV


def main():
    data = EV.load()
    gaps_min, intervals, per_reading_us, window_sizes = [], [], [], []
    for k, d in data.items():
        at, av = d["at"], d["av"]
        intervals += [(at[i] - at[i - 1]).total_seconds() / 60 for i in range(1, len(at))
                      if (at[i] - at[i - 1]).total_seconds() <= 6 * 3600]
        for x in d["samples"]:
            i = bisect.bisect_left(at, x["t"])
            best = min((abs((at[j] - x["t"]).total_seconds()) / 60 for j in (i - 1, i) if 0 <= j < len(at)))
            gaps_min.append(best)
        # streaming floor: sorted window updated per reading
        win, sw, j0 = [], [], 0
        t0 = time.perf_counter()
        for i, (t, v) in enumerate(zip(at, av)):
            bisect.insort(sw, v)
            win.append((t, v))
            while win and (t - win[0][0]) > dt.timedelta(days=EV.FLOOR_DAYS):
                old = win.pop(0)[1]
                del sw[bisect.bisect_left(sw, old)]
            if len(sw) >= EV.MIN_READ:
                f = sw[int(EV.FLOOR_Q * (len(sw) - 1))]
                _ = max(v - (f - 0.0), 0.0)
        el = time.perf_counter() - t0
        per_reading_us.append(1e6 * el / len(at))
        window_sizes.append(len(sw))
    gaps_min.sort()
    intervals.sort()
    n15 = sum(1 for x in intervals if abs(x - 15) < 0.5)
    out = {"sondes": len(data),
           "reading_interval_min": {"median": S.median(intervals), "share_15min": n15 / len(intervals)},
           "lab_to_reading_gap_min": {"median": gaps_min[len(gaps_min) // 2], "p90": gaps_min[int(0.9 * len(gaps_min))],
                                      "max": gaps_min[-1], "n": len(gaps_min)},
           "processing_us_per_reading": {"median": S.median(per_reading_us), "max": max(per_reading_us)},
           "window_readings_max": max(window_sizes),
           "window_bytes_max_float32": 4 * max(window_sizes),
           "share_of_15min_interval": S.median(per_reading_us) / (15 * 60 * 1e6)}
    core.dump("e8_physical.json", out)
    print(out)


if __name__ == "__main__":
    main()
