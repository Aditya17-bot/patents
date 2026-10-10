# Patent 4 — stage-offset estimation for river gauging stations from a neighbouring gauge

## The idea

A river gauging station records stage (water level) with a sensor and converts it to
discharge with a stage-discharge rating. The rating drifts: bed scour or fill, weed
growth, debris on the control, and stage-sensor drift all move the true relation to
Q = R(h + s), a **stage offset** s. Hydrographers measure s only at field visits, every
6-8 weeks; between visits the station keeps applying the last offset (real time) and the
record is later interpolated in time (USGS standards, Sauer 2002, section 8.4.4).

Water is conserved along a reach. A second gauging station on the same river, with no
significant tributary between them, sees the same water delayed by the travel time. The
log discrepancy between the neighbour's discharge and the target's base-rating discharge,

    y(t) = ln Q_Y(t - tau) - ln R(h(t))  ~=  c + s * x(t),   x(t) = d ln R/dh at h(t),

has two parts with different signatures: a flow ratio c that does not depend on stage,
and a stage offset whose effect scales with the rating log-slope x(t) — large at low
flow, small at high flow. The method fits the change of the discrepancy since the last
field visit in **stage units** (least squares on x), so the result is an offset in feet:
the quantity the hydrographer measures and the quantity the station's data logger
applies. The change is applied only when it exceeds its own noise and the offset
signature fits better than a flow-ratio change.

Inputs are records every station already produces: stage, discharge, the rating, and the
field visits. No new instrument at the site.

## Ground truth

Every USGS field visit publishes the measured discharge and the mean gage height, so the
offset the hydrographer would apply is s_meas = R^-1(Q_meas) - GH_meas. Each estimate is
made from data available before the visit and scored against that visit's measurement.

## Nearest art found (verified from raw text where noted)

- Sauer (2002) USGS WRIR 01-4044 — shifts defined from discharge measurements and
  interpolated linearly in time; reference gauges used only to estimate *missing*
  discharge (hydrographic comparison, mathematical translation, routing). Raw PDF read.
- Darienzo (2021) PhD thesis, Univ. Grenoble Alpes — automatic shift detection from
  gaugings (segmentation), stage recessions, sediment transport proxy; notes that
  operational services examine regressions with upstream/downstream stations on a
  monthly step to *question* ratings, and that no automated real-time method exists.
  Raw PDF read.
- US 11,238,356 B2 — synthetic streamflow for a malfunctioning streamgage from correlated
  streamgages (clustering + regression); replaces discharge, no stage offset.
- CN 108460814 A — multi-station linked rating for flood forecasting (target stage and
  discharge as a function of upstream stations); forecasting, not offset estimation.
- Mansanarez et al. (2019) WRR (HAL hal-02609391, raw PDF read) — stage-period-discharge
  model: rating parameters change at known dates, estimated from gaugings.
- Puechberty et al. (2017), Charte qualite de l'hydrometrie (HAL hal-02606950, raw PDF
  read) — superpose upstream/downstream hydrographs; a gap after a flood prompts
  questioning both ratings; monthly linear correlation between stations (6.2.2-6.2.3).
  Closest non-patent art: detection by comparison, no sizing in stage units.
- CN 103106248 A — station stage reported, conversion model selected, discharge reported.

## Data

USGS public-domain data, no key, no login (see CLAUDE.md). Pairs of gauges from NLDI
mainstem navigation of 47 large rivers: 2,159 gauges, 220 consecutive pairs with
<= 20 % incremental drainage area.

## Results (draft 1, 2026-10-03; partial station set, see PLAN.md)

Leave-one-out at field visits (record between two visits; neighbour's final record),
coupling >= 0.95: see `results/e1_interpolation.json`. Real time (`e2_realtime.json`),
injected offsets (`e3_injection.json`), ablation (`e4_ablation.json`), detection
(`e5_detection.json`, weak, not claimed), timing (`e6_timing.json`), 15-minute check
(`e7_iv.json`). The IDF-B prints every number from these files.

## Reproduce

```
python src/network.py                 # pairs from river topology
python src/coupling.py                # lag and coupling per direction (admission)
python src/probe_daily.py daily       # (after caching) per-visit evaluation, published reference
Y_MODE=realtime python src/probe_daily.py daily_rt
IV_MODE=1 python src/probe_daily.py daily_iv
python src/experiments.py; python src/e6_timing.py; python src/e7_iv.py
python src/make_figs.py; python src/make_idfb.py
```
`src/fetch_visits.py` caches field visits within the API quota; `USGS_OFFLINE=1` runs
the probes on cached data only.
