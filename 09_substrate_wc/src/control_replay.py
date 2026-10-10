"""Step 3: downstream effect on irrigation valve decisions (replay, second half of the season).

Rule replayed on every 5-min daytime sample (06:00-18:00): open the irrigation valve for a pulse when
WC < S, with S = P* - 5 (P* = common slab-type drain-onset plateau from rolling_anchor).
Reference decision: offset-corrected reading (rolling drain-onset anchor). Raw decision: sensor as read.
Reported per sensor:
  mismatch      share of daytime samples where raw and corrected decisions differ
  full_slab_irr share of daytime samples where the raw reading calls for a pulse while the corrected
                reading is at or above P* - 1 (slab at drainage plateau: the pulse would pass to drain)
  starved       share where raw says 'no pulse' while corrected is below S - 3 (slab drying unseen)
"""
import json, os
import numpy as np
import pandas as pd
import agc
from offset_anchor import daily_plateau
from rolling_anchor import rolling_ref

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    P_star = json.load(open(os.path.join(ROOT, "results", "rolling_anchor.json")))["P_star"]
    S = P_star - 5
    res = dict(P_star=P_star, setpoint=round(S, 2), sensors={})
    for team in agc.TEAMS:
        x, _ = agc.load(team)
        days = np.sort(x.index.normalize().unique())
        split = days[len(days) // 2]
        test = x[(x.index >= split)]
        test = test[(test.index.hour >= 6) & (test.index.hour < 18)]
        day = test.index.normalize()
        for s in (1, 2):
            raw = test[f"WC_slab{s}"]
            P = rolling_ref(daily_plateau(x, s), days).reindex(day).values
            cor = raw - P + P_star
            ok = raw.notna() & np.isfinite(cor)
            raw, cor = raw[ok], cor[ok]
            d_raw, d_cor = raw < S, cor < S
            res["sensors"][f"{team}_{s}"] = dict(
                n=int(ok.sum()), offset_mean=round(float((raw - cor).mean()), 2),
                mismatch=round(float((d_raw != d_cor).mean()), 3),
                full_slab_irr=round(float((d_raw & (cor >= P_star - 1)).mean()), 3),
                starved=round(float((~d_raw & (cor < S - 3)).mean()), 3))
            print(team, s, res["sensors"][f"{team}_{s}"])
    v = res["sensors"].values()
    res["median_over_sensors"] = {k: round(float(np.median([r[k] for r in v])), 3)
                                  for k in ("mismatch", "full_slab_irr", "starved")}
    res["sensors_with_mismatch_over_20pct"] = int(sum(r["mismatch"] > 0.2 for r in v))
    print(res["median_over_sensors"], "sensors >20% mismatch:", res["sensors_with_mismatch_over_20pct"])
    json.dump(res, open(os.path.join(ROOT, "results", "control_replay.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
