# Phase plan — patent 4

Status markers: `[ ]` not started, `[~]` in progress, `[x]` done.

## Phase 0 — Idea selection and setup `[x]` — 2026-10-03

Brief from the user (2026-10-03): start a new patent unattended, new folder under
`C:\adi\patents\06_stage_offset`, use all the guidance .md files, few claims, review in ~3 hours.

Selection criteria carried over from patent 3: open data with no login; a physical
invariant; a **quantitative** output (size and correct, not only flag), because flagging
by neighbour comparison is the part most often already published; open ground truth to
score against; no overlap with patents 1 and 3.

Chosen: stage-offset ("shift") estimation at a river gauging station between field
visits from a neighbouring gauge on the same river. Reasons:
- USGS publishes every field visit (measured discharge + mean gage height), so each
  estimate can be scored against an independent hydrographer measurement — stronger
  ground truth than patent 3 had.
- Topology is parsed from NLDI, not hand-picked.
- Patent search (Google Patents, 14 queries, EN + ZH) found no patent converting a
  neighbour discrepancy into a stage offset; nearest are synthetic streamflow from
  correlated gauges (US 11,238,356 B2) and multi-station forecasting ratings
  (CN 108460814 A).
- Literature: operational services compare with up/downstream stations to *question* a
  rating (Darienzo 2021, citing the French hydrometry quality plan, Puechberty et al.
  2017) — detection on a monthly step, no sizing, no automated real-time method.

Rejected alternatives considered this session: tide-gauge clock/gain/datum separation by
tidal constituents (UHSLC/IOC QC practice covers timing errors), wind-turbine and
seismometer orientation (known), smart-meter and PMU ideas (no open data), more WebTRIS
inventions (would sit too close to patents 1 and 3).

## Phase 1 — Feasibility probe `[~]`

- `src/network.py` -> `results/pairs.json`: 47 river outlets, 2,159 mainstem gauges,
  220 consecutive pairs with <= 20 % incremental drainage area.
- `src/probe.py` (hourly, IV) on 4 Platte pairs: absolute offsets from the neighbour lose
  to carrying the last measured offset forward (Platte has diversions and poor coupling,
  daily r 0.80-0.95). Led to the change-since-last-visit estimator.
- `src/probe_daily.py` (daily values, all pairs, WY2021-2026) — running.

Operational notes: the OGC field-measurements API allows 1,000 requests/hour without a
key (HTTP 429 with Retry-After); the client waits. The historical IV server is slow
(~10-30 s per 3-year series); daily values are used for the broad evaluation.

Findings that shaped the claims (2026-10-03):
- Real-time use with a neighbour whose own discharge is computed in real time is weak:
  the neighbour's own offset drifts as much as the target's (median change between its
  visits ~0.2 ft at these alluvial stations). Over all visits no gain; at visits where
  the offset changed >= 0.1 ft a modest gain. Kept as dependent claim 2, stated honestly.
- Record computation between two visits (the published record, interpolated linearly in
  time today) is where the neighbour helps clearly: leave-one-out at field visits.
- A per-station gain learned from earlier visits matters more than the unit conversion
  at the visits; stage units vs discharge-ratio units differ little at visits (similar
  stages) but stage units are stage-independent under injected offsets (CV 0.21 vs 0.57).
- Detection (flagging large changes before the visit) is weak, AUC ~0.59: not claimed.
- The "signature test" (offset vs flow-ratio model comparison) did not help; dropped.

## Phase 2 — Experiments `[x]` (partial station set, see below)

- `src/probe_daily.py` -> `results/daily.json` (published reference) and
  `results/daily_rt.json` (reference computed as in real time). Run with
  `USGS_OFFLINE=1` on the stations whose field visits are cached.
- `src/experiments.py` -> e1 interpolation (leave-one-out), e2 real time, e3 injection,
  e4 ablation, e5 detection; `src/e6_timing.py` -> e6.
- `src/fetch_visits.py` caches visits for admitted directions; it is quota-bound
  (1,000 requests/hour on the field-measurement API). Re-run it, then re-run the probes,
  experiments, figures and IDF-B to enlarge the station set; all numbers flow through.

## Phase 3 — IDF-B `[x]` draft 1 — 2026-10-03

- `src/make_figs.py` (+ `figs_data.py`) -> figures 1-5; `src/make_idfb.py` ->
  `patent/IDF-B_Stage_Offset_Neighbour_Gauge.docx` (+ .pdf via Word). Accepted 11-section
  layout, no Note on Filing, 7 claims (1 method + 4 dependents, 1 system + 1 dependent).
- Build checks pass: no placeholders, business vocabulary or banned phrases; 100 % of
  numbered paragraphs name a physical element; every table referenced has a caption.

## Status 2026-10-03 14:10 IST — draft 1 on the full admitted set

- Visits fetched for all 98 sites of the 107 directions with coupling >= 0.90; 77 directions
  admitted at 0.95, 68 scored. `src/rebuild.sh` reruns everything offline.
- E1 record between visits (neighbour's final record): 1,214 visits, 56 stations; mean
  error 15.2 -> 13.0 %, p90 33.3 -> 27.0 %; departures >= 0.1 ft (560): mean 27.1 -> 21.1 %,
  better at 356/504 (z 9.27). Open water only (no ice, Apr-Nov), >= 0.1 ft: 19.2 -> 16.1 %
  (z 7.74). Ice visits (82): 59.9 -> 38.4 % (ice estimation from neighbours is known, N1).
- Real-time reference: all visits level; >= 0.1 ft changes 22.1 -> 19.1 % (z 4.13, E2).
- E3 injection 0.10 ft -> median 0.098 ft; stage-unit CV 0.31 vs discharge-ratio CV 0.84.
- E4 ablation: stage vs ratio units similar at visits (536/1042); gain matters overall.
- E5 detection AUC 0.58-0.66: weak, not claimed. E6: 0.096 ms per station-day.
- E7 15-minute subset (89 visits, 18 stations): 9.1 -> 8.1 % (daily 8.5 %).
- IDF-B 19 pages, 7 claims; copies in Downloads.

## Status 2026-10-03 (second pass) — improvements after user review request

- Figures redrawn: architecture (signal lanes, no arrows across zone bodies), flowchart
  (hardware column, fixed overlaps), Fig 3 smoothed rating slope + decile trend line,
  new Fig 6 (India map, admission scatter, noise floor, station bootstrap), claim tree.
- E8 India (`src/e8_india.py`, CAMELS-IND via Kaggle): 6 same-river CWC pairs admitted
  (Godavari, Mahanadi, Brahmani-Baitarani, Tapi); departure noise median 8.6 % vs US
  3.9 % (upper bound). No stage in the open Indian record.
- E9 (`src/e9_bootstrap.py`): station-cluster bootstrap. Record between visits, departure
  >= 0.1 ft: 5.9 points [3.9, 8.1], 32/38 stations improve; real time all visits CI
  includes zero. Gain prior/warm-up sensitivity: mean error 13.0-13.7 %.
- New claim 6: neighbour's final record as reference, station by station (fallback that
  the strongest evidence supports). 8 claims total.

## Status 2026-10-04 (third pass) — external review, scores raised

An independent reviewer agent rated draft 2: disclosure 6.5, published application 5,
grant India 3.5, US 3. Its findings, checked and acted on:
- Gain look-ahead leak (left-out visit's truth entered the gain through the visit before
  it): fixed in `experiments.usable()` — a departure enters the gain only once its
  following visit is past.
- Physics: D = sum(xy)/sum(x^2) has no flow-ratio term, so D = s + c sum(x)/sum(x^2).
  New estimator: flow ratio c fixed at each visit from the measured offset, interpolated,
  window offset sum x(y - c)/sum x^2 (`experiments.ratio_at_visit/offset_given_ratio`;
  probe_daily now stores window sums `wT`, `wP`).
- Error metric now exact: |R(GH + s)/Q_meas - 1| (was linearised).
- Practice baselines added (Kennedy 1983 / USGS 2019 deck): whole change at the largest
  flood (step) and prorated up to it (ramp); probe_daily stores `peak_day`.
- Results (leak-free, exact): record, all visits 17.0 -> 13.7 % (z 4.04, CI 1.6-5.2);
  open water 11.7 -> 10.6 % (z 3.28, CI 0.4-1.7); >= 0.03 m: 31.3 -> 22.6 %, vs flood
  step 29.3 % (CI 2.0-11.5). Stage vs ratio units z 4.32 (each slope tercile z > 2.3);
  with vs without flow-ratio term z 3.74. Real time (real-time ref.): mean 15.6 -> 14.0 %
  (CI 0.1-3.2), median 6.9 -> 7.5 %. Holds on two station halves, coupling 0.90-0.97,
  windows 14-28 d, steady 0.15-0.35 ft.
- Prior art: Kennedy 1983 (TWRI 3-A13) and USGS 2019 deck added (N5, N6), raw texts in
  prior_art_raw; Google Patents files re-fetched via browser (abstract + claim 1).
- Claims restructured: 2 independent methods (record; logger before next visit), system
  claim with the station hardware, 9 claims. Title 14 words. SI units throughout.
  Ice and the truth-selected subset no longer headline. Build refuses if a worded
  comparison stops matching the numbers.

## Status 2026-10-04 (rounds 3-4) — reviewer scores and responses

Reviewer agent scores (disclosure / published / grant IN / grant US):
round 1 6.5/5/3.5/3; round 2 8.0/6.5/4.5/4.0; round 3 8.5/7.0/5.0/4.5.
Round 3 -> 4 changes:
- Practice baselines: per-rise split (Kennedy, rises >= 0.5 ft) and practice chosen per
  station from earlier visits only (`e_prac`): method 17.0 -> 13.7 % over all visits
  (z 3.79, CI 1.6-5.4), open water z 2.79.
- Neighbour record rebuilt from its own visits (`Y_MODE=interp`, daily_ip): 19.9 -> 15.8 %
  (z 3.43, CI 1.7-6.7). Claim scope restricted to a neighbour record finalised with its own
  visits; chaining claim and chaining language dropped.
- V4 injection rerun with the claimed estimator; synthetic flow-ratio test in two forms
  (linear ramp: by construction; step at largest flood: term smaller at 66 % of visits).
- Real time: neighbour finalised to date (`Y_MODE=rtfinal`, daily_rtf) mean 15.6 -> 13.75 %,
  sign test not significant. Noise gating tried, not adopted (only a searched setting
  reached significance). Real time kept as dependent claims 2 and 4.
- Claims: 1 system (self-contained, station hardware, record replaced), 2 system + logger
  offset, 3 method, 4 method + logger offset, 5-10 dependents.

## Status 2026-10-04 (rounds 5-6) — near the ceiling on this data

Scores: round 4 8.5/7.5/5.5/4.5; round 5 8.5/8.0/5.5/4.5; round 6 8.5/8.5/6.0/4.5
(disclosure / published / grant IN / grant US).
- Claims (11): 1 system (self-contained), 2 system + logger offset (neighbour record as
  computed to date), 3 method, 4 method + logger offset, 5 admission, 6 days/windows,
  7 least squares + through-origin gain, 8 gain prior/bounds, 9 linear interpolation and
  windows, 10 neighbour rebuilt from its own visits, 11 sensors/link/15-min sampling.
- Generic fit in claims 1/3 supported by median and x^2-weighted-median fits
  (experiments.FITS): 13.6 / 14.3 % vs least squares 13.7 % over all visits; vs per-station
  practice z 4.62 / 3.77.
- Reviewer's view of the ceiling with US records: published ~8.5 (8.5-9 with attorney
  polish), India grant ~6, US grant ~4.5-5. Remaining levers need new data: Indian stage +
  gaugings (India-WRIS; registration status not verified) or a prospective logger trial.

## Open items for review

- Figure 5 now shows the direction with the most scored visits (06799315/06799350).
- Prior art: read Mansanarez et al. 2019 (WRR) and the French hydrometry quality plan
  (Puechberty et al. 2017) in full; more patent queries (virtual gauging, reference
  station shift). Only references read in full are in Tables 1-2.
- Filing note (not for the IDF-B): independent of patents 1 and 3; inventors in IDF-A.

## Status 2026-10-05 — rev2, claims narrowed to the evidence kernel
- Claims cut from 11 to 7, as the hub rule asks: 1 independent method (record between visits;
  steps a-g without pair admission, steadiness filter or learned gain; step f uses a generic
  weight, so g = 1 is covered), dependents 2 (logger offset before next visit),
  3 (admission constants), 4 (days, steadiness, windows, linear interpolation),
  5 (least squares + learned gain), 6 (neighbour rebuilt from its visits); 7 system
  carrying out claims 1-6.
- N7 (Vlah 2024) row and 4.2 distinction reworded: N7 does anchor the donor relation at
  field visits; the distinction is the stage-signature separation, offset in metres, and
  keeping the target's stage record. N7 column added to Table 3.
- 4.7 Patentability Summary removed; its sentence on independent ADCP/current-meter
  evidence folded into 6.2. Headings match the reference IDF-B; 8.6a/b/c -> 8.7/8.8/8.9,
  later subsections 8.10-8.12. Figure kept with its caption (keep_with_next on images).
- Figures 2, 4, 7 regenerated for the new claim numbers. 24 pages.
- rev1 (11 claims) and the old generator are in `C:\adi\patents\_old\06_stage_offset_rev1_2026-10-04`.
