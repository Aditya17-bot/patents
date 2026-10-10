"""Data facts quoted in the IDF-B: period, samples, sensors, and the agreement of the 5-min pulse log with
the daily irrigation meter (after the midnight-reset handling in agc.py). Output: results/data_check.json"""
import json, os
import numpy as np
import agc

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    out, first, last, n5, pulses = {}, [], [], 0, 0
    for t in agc.TEAMS:
        x, daily = agc.load(t)
        s = x.irr.groupby(x.index.normalize()).sum()
        j = daily.join(s.rename("sum"), how="inner").dropna()
        wc = x[["WC_slab1", "WC_slab2"]].notna().all(axis=1)
        out[t] = dict(days=int(x.index.normalize().nunique()), samples=int(len(x)),
                      samples_with_both_wc=int(wc.sum()), pulses=int((x.irr > 0).sum()),
                      pulse_over_meter=round(float(j["sum"].sum() / j.Irr.sum()), 3),
                      corr_daily=round(float(np.corrcoef(j.Irr, j["sum"])[0, 1]), 3),
                      irr_mean_l_m2_day=round(float(daily.Irr.mean()), 2),
                      drain_mean_l_m2_day=round(float(daily.Drain.mean()), 2),
                      pulse_volume_median_l_m2=round(float(x.irr[x.irr > 0].median()), 2),
                      wc_median_1=round(float(x.WC_slab1.median()), 1),
                      wc_median_2=round(float(x.WC_slab2.median()), 1))
        first.append(x.index.min()); last.append(x.index.max())
        n5 += int(wc.sum()); pulses += out[t]["pulses"]
    res = dict(per_compartment=out, compartments=len(agc.TEAMS), sensors=2 * len(agc.TEAMS),
               period=[str(min(first).date()), str(max(last).date())], samples_both_wc=n5, pulses=pulses,
               pulse_over_meter_range=[min(v["pulse_over_meter"] for v in out.values()),
                                       max(v["pulse_over_meter"] for v in out.values())],
               corr_daily_min=min(v["corr_daily"] for v in out.values()))
    print(json.dumps({k: v for k, v in res.items() if k != "per_compartment"}))
    json.dump(res, open(os.path.join(ROOT, "results", "data_check.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
