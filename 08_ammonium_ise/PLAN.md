# PLAN — Patent NN

| Phase | Goal | Gate | Status |
|-------|------|------|--------|
| 0 | Idea + feasibility probe on open data | effect visible in raw data | |
| 1 | Prior-art search (raw text verified) | no art with the same mechanism | |
| 2 | Prototype + measured results in `results/` | every claimed number reproducible | |
| 3 | Claims (1 independent, 4–6 dependents, 1 system) | five-part structure | |
| 4 | IDF-B build (`src/make_idfb.py`) + figures | no placeholders, renders clean | |
| 5 | Review, then copy to `C:\adi\patents\IDFs\` and update STATUS.md | | |

## Phase 0 notes 2026-10-05 — water-quality sensor drift
- Idea: date and size fouling drift of a conductance sensor between service visits from a
  neighbouring station (solute carried downstream), instead of linear-in-time correction.
- USGS: field-measurements API has SC reference readings ('ReferencePrimary') at visits, but
  the published continuous SC is already drift-corrected and raw sensor data are not public:
  no ground truth for a leave-one-out test.
- NEON DP1.20288.001: Quick Start Guide says data are not corrected for sensor drift
  (prior_art_raw/neon/qsg_wq.txt); grab samples DP1.20093.001 give lab SC. But the data
  endpoint returns 403 Access Denied without an API token (account needed) as of 2026-10-05.
- Kaggle: no NEON / continuous water-quality mirror found.
- Blocked pending user decision: NEON token, or switch idea.

## Phase 1 gate 2026-10-05 — snow pillow (user's second choice): FAILED
- Johnson & Marks (2004), "The detection and correction of snow water equivalent pressure
  sensor errors", Hydrological Processes; ARS record read raw (prior_art_raw/ars_170733.txt):
  detects under/over-measurement from rates of change of SWE, density and depth, and corrects
  by density at error start x snow depth until the series intersect. That is the obvious
  pillow + depth-sensor invention. Also Meyer et al. 2012 JHM (SWE vs accumulated precip
  inconsistency at SNOTEL) and US 11,774,634 (snowpack characteristics) not yet read raw.
- Folder name 08_wq_drift kept until an idea passes; rename when one does.

## Screening round 2026-10-06 — candidate found: ammonium sonde interference correction
- Data (open, no login, OGL): EA Hydrology API water-quality sondes, quality 'Unchecked'
  (raw), ~1,940 stations; EA Water Quality Archive API (JSON-LD, Accept: application/ld+json)
  lab results. src/ea.py caches both under data/ea/.
- results/sites.json: 82 sondes running >= 1 year paired with a sampling point within 300 m.
- Conductivity drift too small to matter (probe_error.json): median |ln(sonde/lab)| 0.029, grows
  1.9 % -> 3.1 % with time since service. Some archive 0077 values equal the sonde reading
  (copied, not lab) - filter by sampling purpose / exact equality before using as truth.
- Ammonium (probe_amm.json): sonde over-reads lab by median factor ~4.5; not time-since-service.
  Over-read correlates with the sonde's own conductivity within sites (median r 0.44, 27/33
  positive) and scales across sites with conductivity: cation interference (Nikolsky-Eisenman).
- probe_interf.py, time-ordered (fit first half, score second half), 23 sites, 333 test samples:
  median abs error raw 0.68, offset-only 0.37, offset + k*SC 0.26 mg/L; p90 17.5 / 9.0 / 2.4;
  interference term beats offset at 18/23 sites. Some fitted k < 0 (unphysical): constrain k >= 0.
- Art seen (not yet read raw): sondes correct ionic strength via conductivity; K+ compensation by a
  separate K electrode (Hach US 8,691,074; ammolyser); Water Research 2020 ISE reconstruction with
  composite samples; 2026 Ionics paper K/pH/T compensation. Novelty risk: moderate (obviousness).

## Evidence round 2026-10-06 (user away, autonomous) — mechanism changed
Data: results/sites_amm.json, 71 ammonium+conductivity sondes (>= 180 d) paired with lab 0111
points within 300 m; 67 usable sites, ~1,150-1,170 matched samples (sonde within 30 min of lab).

1. Conductivity interference term (original candidate) — FAILED the evidence gate.
   - e1 (site k, one-step-ahead, rolling offset baseline): median 0.158 vs 0.161, z 1.72, 19/57 sites.
   - e2 cold start (leave-one-site-out network k): beats network median offset (z 10) but against a
     matched constant (network mean, same pool) median level (0.16 vs 0.15), tail gain only;
     station bootstrap CIs include zero; 16/67 sites better; high-SC gain comes from E01566A
     (estuarine, 30,600 uS/cm): without top 2 sites no difference. Sodium interference in saline
     water is already well known (vendor docs). Not pursued.
   - e3 lifecycle: once site lab samples exist the conductivity term adds nothing reliable.
2. Anchored floor tracking — PASSES the evidence gate (e5_anchor.py, results/e5_anchor.json):
   offset(t) = floor(t) - g, floor = 5th percentile of the sonde's own readings over the preceding
   7 days, g = median over prior lab samples of (floor - departure); corrected = reading - offset.
   Against practice (reading - median prior departure), samples with >= 1 prior lab sample (1,083):
   median 0.159 -> 0.112 mg/L N, trimmed (99 %) mean 1.04 -> 0.85, mean 106 -> 7.3 (gross faults
   absorbed), better at 571/881 (z 8.8), 54/67 sites; station bootstrap median reduction CI
   [0.022, 0.068], trimmed CI [0.011, 3.32], p90 CI includes 0.
   Mechanism checks: gain both where serviced since last lab sample (0.136->0.087, z 2.6, n 144)
   and not (z 8.5); no gain and no harm above 1 mg/L (episodes not erased); alarms at 1.0 mg/L:
   false 110 -> 90, missed 52 -> 51.
   Floor without anchoring (e4_floor.py, network background): beats network mean (z 8.2) but
   median level, 36/67 sites; sensitivity in e4_floor_*.json.
3. Prior art for the floor mechanism: Pedersen et al. 2020 (full text, prior_art_raw/lit/
   pedersen2020_watres.txt): jumps located from the maintenance logbook and removed with
   before/after means; multiplicative correction factors at composite-sample days, linearly
   interpolated between them (retrospective). Generic sensor baseline-tracking patents seen in
   search (US 5,594,667; US 2019/0034032 A1; US 6,237,394 B1) - not yet read raw.
Next: read those three raw; sensitivity of e5 (days 3/14, q 0.02/0.10, window); then figures and
IDF-B on the anchored floor mechanism. Title/CLAUDE.md need updating to the new mechanism.
- Raw check of the baseline patents (prior_art_raw/gp/baseline_patents_notes.txt): US 5,594,667 A
  computes a sensor baseline as the average of the lowest fixed percentage of points of its own
  record (grain-flow sensor) -> the floor idea alone is anticipated in principle; what remains new
  is anchoring the floor to laboratory results (floor - lab gap g) for an ammonium ISE in a river.
  Obviousness risk HIGH: US 5,594,667 + US 8,691,074 / Pedersen 2020. Honest estimate 4-5/10.
- Decision deferred to the user (2026-10-06): draft IDF-B on anchored floor tracking anyway, or
  screen again. Figures 1-2 in patent/figures show the abandoned conductivity mechanism; redraw if
  drafting proceeds.

## Status 2026-10-06 — IDF-B rev1 drafted (user chose option 1: draft anyway)
- Evidence: src/evidence.py -> results/ev_main.json, ev_rows.json, ev_sens.json. 67 sondes, 1,083
  samples with prior lab history. Method median 0.112 mg/L vs practice chosen per sonde 0.152
  (551/888, z 7.18; 52/67 sondes; station bootstrap median reduction 0.036 [0.017, 0.060]); vs last
  departure z 6.14; halves z 4.15 / 5.91; all sensitivity runs z 4.5-7.6. p90 reduction CI
  includes 0. Floor follows offset: slope 0.93, same direction 712 vs 311. Alarms: fewer false at
  0.6 and 1 mg/L; at 2 mg/L level false (67 vs 65) and more missed (37 vs 25) - stated in the IDF.
- Figures: src/figs_arch.py (1, 2), figs_data.py (3-6), figs_claims.py (7). IDF-B: src/make_idfb.py
  (refuses to build if worded comparisons stop matching results). Rebuild: src/rebuild.sh.
- Output: patent/IDF-B_Ammonium_Sonde_Floor_Anchor.docx/.pdf (17 pp, 6 claims: 1 method, 4
  dependents, 1 system); copied to C:\adi\patents\IDFs\08_Ammonium_Sonde_Floor_Anchor.*.
- Honest rating 4-5/10: obviousness over US 5,594,667 (low-quantile baseline) + US 8,691,074 /
  Pedersen 2020 (laboratory anchoring).

## Status 2026-10-06 — rev2 (weakness pass)
- e6_guard.py: service-segmented floor window = no change; offset rate-limited between services
  (cross-fitted rate unstable 0.048 vs 1.09 mg/L/d; vendor 0.31 mg/L / 73 d -> median 0.138; hold
  -> 0.153 = practice). Shows the gain is drift within service periods. Added as ablation rows.
- Two-tier alarm (claim 2): watch = max(floor-corrected, last-sample-corrected), confirmed = min.
  Watch misses fewer than median/last/per-sonde practice at 0.6/1/2 mg/L (44/36/20 vs 69/48/25);
  confirmed fewer false alarms than every baseline (78/57/43 vs 147/105/65). Trend baseline misses
  14 at 2 mg/L (with 103 false) - stated.
- Rev1 moved to C:\adi\patents\_old\08_ammonium_ise_rev1_2026-10-06; rev2 in IDFs (18 pp).
- Remaining: p90 not reduced with certainty; one agency's data; obviousness over US 5,594,667 +
  US 8,691,074. Self-rated 5/10.

# REV3 PLAN (2026-10-06) — redraft to the _shared guidance, as for patents 05/06
Guidance read in full this time: section_3k_compliance.md, physical-technical-compliance.md,
writing-guidelines.md, patent-draft-builder-SKILL.md, SKILL (2).md (section builder, Frameworks
1-4), diagram-tools.md, dataset-strategy.md; layout per IDF-B_format_reference_Tablet_Dispenser.docx
(11 sections; long Section 2 with 2.1; objectives = primary + (a)..; Tables 1-2 for prior art).

Gap audit of rev2 against the guidance:
G1 3(k)/physical: invention reads as data correction; physical effect = offset to controller and an
   alarm only. Needs actuation hardware (alarm-driven automatic sampler, intake isolation valve
   relay), named sonde hardware (ISE membrane + reference junction, ADC, microcontroller,
   SDI-12/RS-485 bus, cellular modem), apparatus-framed title, flowchart hardware nodes.
G2 Section 8 physical parameters: per-reading latency (ms), memory per sonde, decision latency
   within one 15-min interval, sonde-lab timing gap - measure, do not assert.
G3 Prior art: 10 refs (5 patents, 3 papers, 2 vendor notes) -> target >= 13 (>= 6 patents,
   >= 5 journal papers), every one read raw.
G4 High-concentration weakness: test dissolved-oxygen corroboration (sewage ammonium arrives with
   a DO drop; an offset move does not) as an episode/offset discriminator. Rule fixed before
   scoring, cross-fitted on station halves; adopt only if it holds.
G5 Writing: paragraph numbering continues 6 -> 7; Section 8 prose; banned openers/phrases;
   parallel structures; 5 protection aspects; captions stand alone.
G6 Claims: 1 independent method (hardware-anchored, ends in physical action), 4-6 dependents,
   1 system; every dependent backed by a Section 8 number.

Steps:
S1 [ ] DO download (background) + G4 experiment (e7_do.py)
S2 [ ] G2 physical metrics (e8_physical.py)
S3 [ ] G3 prior art: search + raw read, notes in prior_art_raw/
S4 [ ] Redraft make_idfb.py (G1, G5, G6); figures 1-2 with actuation hardware; data figs if G4 adopted
S5 [ ] Framework 4 self-audit (novelty / patentability / physical-technical / writing) with FIX list
S6 [ ] Publish rev3 (IDFs, STATUS, rev2 -> _old), honest rating

## REV3 status 2026-10-06
S1 [x] DO corroboration (e7_do.py): FAILED, not adopted. At the 76 samples flagged as episodes
       (floor up and DO down >= 10 pp) holding the last offset is worse than the floor (22 vs 49,
       both halves z ~ -2.3); 5 and 15 pp no better. DO drop does not identify ammonium episodes here.
S2 [x] e8_physical.py: 5.7 us per reading (one core), <= 673 readings (2.7 kB) per sonde, median
       reporting interval 15 min, lab-reading gap median 6.9 min (p90 20.8).
S3 [x] Prior art 8 patents + 8 publications, all read raw (new: US 10,918,318 B2, JP H08-304324 A,
       CN 107884535 A, Jones 2022, Wagner 2006, Kaelin 2008).
S4 [x] Redraft: apparatus title; hardware anchors (front end/ADC 116, modem 117); controller
       write-back; claim 2 two-tier alarm -> relay-started sampler 440 and intake interlock 450;
       system claim with relays; 9 + 15 numbered paragraphs; 5 protection aspects; figures 1, 2, 7.
S5 [x] Framework 4 self-audit: banned/3(k) scan clean; FIG./Figure unified; honesty fixes
       (tier trade-offs stated, inferred drift statement hedged, unmeasured mV slope replaced by N6).
S6 [x] Rev3 in IDFs (21 pp); rev2 in _old\08_ammonium_ise_rev2_2026-10-06.

## KILLED 2026-10-06 (user review: "weak, lot of assumptions, results show worse")
Decision (Claude, at the user's request to work on it or kill it): kill.
- Effect is small: median error 0.152 -> 0.112 mg/L; p90 and trimmed-mean gains not certain.
- No gain above 1 mg/L, the pollution range alarms exist for; single corrected reading misses more
  at 2 mg/L; two-tier alarm only trades misses for false alarms.
- Repairs tried and failed: DO corroboration (e7), rate-limited / held offset (e6), conductivity
  interference (e1-e3).
- Untested in the draft: sampler/intake relays (added for framing), "river returns to background"
  (assumed), drift faster than vendor figure (inferred).
- Inventive step weak: US 5,594,667 (low-quantile baseline) + US 8,691,074 / Kaelin 2008 / Pedersen
  2020 (laboratory-reference correction).
- No open data that could change this (needs Indian or second-agency ammonium sondes with lab samples).
Lesson for 09: an idea must show a clear, physically explained gain in the regime that matters
before drafting; never add hardware or claims the evidence does not test.
