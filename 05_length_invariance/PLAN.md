# Phase plan

Status markers: `[ ]` not started, `[~]` in progress, `[x]` done.

## Phase 0 — Project setup and feasibility `[x]` — 2026-09-28

New folder, guidance files copied, WebTRIS client reads patent 2's cache, 2025 site
snapshot used (the 2026 live feed moved the site text from `Name` to `Description`; the
parser accepts both). Feasibility probe positive — see README.

## Phase 1 — Prior-art gate `[~]` — **GATE FAILED for the broad claim** (2026-09-28)

Found and verified from raw text (UDOT PDF extracted with pypdf, passages grepped):

- **Azin & Yang (2020)**, *Multi-Stage Algorithm for Detection-Error Identification and
  Data Screening*, Utah DOT report UT-20.15, University of Utah. 5-min aggregated PeMS
  data. Compares the average effective vehicle length (AEVL) distribution of each
  detector with adjacent stations (K-S test), then compares AEVLs of multiple adjacent
  stations (Multiple Comparison with the Best) to single out the station "statistically
  different from AEVLs at other stations"; if the target fails, compares with upstream
  and downstream neighbours to decide which is faulty; marks detectors "that need to be
  corrected through maintenance or recalibration". Notes on-ramps affect AEVL downstream.
- **Lu, Yang & Chang (2014)**, *Algorithm for Detector-Error Screening on Basis of
  Temporal and Spatial Information*, TRR 2443:40–48 — cited by the above for comparing
  AEVL distributions of adjacent detectors. Not yet read in full.

What this takes: compare a length statistic between adjacent detectors on aggregated
data, localise the odd detector, flag it for recalibration. That was the core of the
proposed independent claim.

What is not in it (the narrow survivors):
1. Quantitative sizing and correction — the art flags only; it does not estimate a
   per-detector bias or rewrite the archived class counts.
2. Length-class shares at the bin boundaries of a classifying detector, not AEVL (AEVL
   mixes speed, occupancy and length errors). Likely argued as an obvious substitution.
3. Interval-matched comparison with a volume-balance admission gate, not distribution
   tests over time. Small step.

Decision (user, 2026-09-28): pivot, and gate new candidates by search before building.

### Pivot round 1 — three candidates, all weak or dead (2026-09-29)

1. **Smart-meter clock-offset correction from the common grid-frequency trace (CEEW,
   India).** Weak: grid-frequency (ENF) matching is established both for timestamping
   recordings and for synchronising sensor clocks ("Natural Timestamps in Powerline
   Electromagnetic Radiation"; frequency fingerprints used for time sync and phase
   identification). Applying it to meter logs reads as an obvious substitution.
2. **Absolute speed calibration of roadside detectors from the speed-limiter peak of HGVs
   (56 mph UK; 80 km/h India AIS-018).** No direct hit, but obvious over weigh-in-motion
   auto-calibration (FHWA WIM Pocket Guide Part 3; Arkansas DOT TRC1801): standard
   practice calibrates a roadside sensor against a known property of a truck class in the
   traffic stream (front-axle weight of FHWA Class 9). Swapping weight for limiter speed
   is the examiner's argument. Surviving step: extracting the HGV speed mode from
   aggregated all-vehicle speed bins by unmixing over fleet-mix variation — enabling but
   thin.
3. **Wind-turbine nacelle-direction north offset from wake-deficit bearings (open SCADA).**
   Dead: US 11,560,874, *Method for determining a yaw position offset of a wind turbine* —
   power ratio to a neighbouring turbine against yaw position, extrema from mutual wakes
   give the offset. Also US 10,138,873 (nacelle-position recalibration), and industry
   practice (vane checked against the wake-deficit direction).

Pattern: "a physical reference carried by the system" for roadside and utility sensor
QC is heavily worked. Every such trick found so far has a published or patented
counterpart.

### Pivot round 2 — any domain, physical corroboration of logical events (2026-09-29)

User opened the domain. Three candidates on the CausalInterlock pattern (physical
measurement independent of software-reported events + interlock on the input or
actuation path). All dead on triage search:

1. **Keystroke/HID injection blocked unless corroborated by physical keypress vibration.**
   Dead: NoBU, ACM AsiaCCS 2025 (doi 10.1145/3708821.3710816) — external accelerometer
   senses keypress vibration, classifies each keycode as BadUSB or human, blocks
   injected ones. Also US 9,342,687 *Detecting synthetic keystrokes*; US 10,289,846 /
   US 10,824,727 (remote-access malware: compare physical input with received events).
2. **Covert camera/microphone activation detected from module supply current, gated.**
   Dead: US 11,210,398 (webcam supply-current ammeter, hardware trigger, indicator immune
   to the processor); US 11,288,363 (microphone equivalent).
3. **EMI ghost-touch rejected unless the phone IMU shows a real tap impulse.** Dead:
   *Analyzing and Defending GhostTouch Attack*, IEEE TDSC 2024 (touch–IMU consistency as
   the defence, per search summary, not verified from text); US 9,619,056 family (valid
   touch event from vibro-acoustic signal); Apple "IMU for touch detection".

Pattern: first-order "corroborate the logical event with a physical one" ideas are also
taken in security. Six fresh candidates, none survived; the length-invariance idea is
the only one with a surviving narrow core AND a measured, first-hand problem behind it.

Original gate criterion: stop or narrow if a reference already uses the length-class shares of the same
traffic stream at adjacent detectors to calibrate or correct one of them.

- Coifman corpus: cross-station length comparison, "transition" of length between stations
- Cheevarunothai / Wang / Nihan: confirm they use a fixed external reference, event data
- Rendezvous / blind sensor calibration: pairwise calibration chains
- Patents: CPC G08G1/015 (classification), G08G1/042 (loops), G08G1/01, G01D18/00
- Google Patents, Espacenet; InPASS if reachable
- Every reference entering the IDF-B verified from raw text (no WebFetch quotes)

## Decision 2026-09-29: back to length invariance, claimed as a combination

User chose this over a third search round. Claim centred on what Azin & Yang (2020) do
not do: size each detector's bias per class boundary and correct the archived counts.

## Status 2026-09-30, eighth pass - restructured to the accepted cyber-security IDF-B layout

- Reference layout: `Downloads/IDF-B Cyber security Updated (1).docx`.
- IDF-B now 11 sections: 2.1 problems, 2.2 definitions; Table 1 patents (P1-P7, adds
  GB 2377027 A and US 7,684,946 B2, both read raw) and Table 2 publications (N1-N11);
  4.2 distinctions, 4.3 inventive combination, 4.4 feature mapping (F1-F9), 4.5 effects,
  4.6 applicability, 4.7 patentability summary; 6.1 claimed vs example table, 6.2, 6.3;
  [0001]-[0037] numbered paragraphs; 7.1-7.11; 8.1-8.16 with configuration, tests (V1-V11),
  admission ablation text (E4), effect summary, insights, limits + acceptance criteria;
  9 Discussion; END line. Section 12 (Note on Filing) removed.
- Claims now 8: new claim 5 (sensitivity correction sent to detector card 111, refit after);
  speed attribution is claim 6, system claims 7-8. Claim tree fig11 redrawn.
- Removed from the IDF-B, to tell the IPR cell separately: Lu, Yang & Chang (2014) unread;
  relation to patent 1 (file before it publishes); inventors in IDF-A.
- 35 pages, ~15.9k words; build checks pass.

## Status 2026-09-29, seventh pass - grounded against independent manual counts

- Source: DfT road traffic raw counts (open API roadtraffic.dft.gov.uk, no login), 12-hour
  manual classified counts by trained enumerators (verified in DfT methodology note and
  About page, `patent/prior_art_raw/dft_methodology_note.txt`, `dft_about.txt`). Cached
  in `data/dft/raw_counts_{M25,M1}_{2024,2025}.json`.
- `src/fetch_ground.py`: WebTRIS both carriageways within 8 km of each count point, count
  month only (1,340 site-months, page_size 5000, cached).
- **E11** `src/e11_ground_truth.py` -> `results/e11_ground_truth.json`: 28 detector-count
  matches (nearest fitted detector within 2 km, totals within 5 %, free-flow hours).
  Departure of recorded share from manual proxy vs bias fitted from pairs alone:
  520 cm slope 0.87 +- 0.14, r 0.77, Spearman 0.68 (p 6e-5); 660 cm 1.13 +- 0.33, r 0.56.
  Spread (MAD) 8.4 -> 4.0 points at 520, 2.5 -> 1.3 at 660 after correction. M25 strong
  (520 r 0.90, 660 r 0.84); M1 weaker (520 r 0.55, 660 none). 1160 cm unresolved.
- IDF-B: new paragraph + Figure 10 (claim tree now Figure 11); Table 2 rows; 4.2, limits,
  TRL, Section 9, 12 updated; 7.1 reference site may be fixed by a manual count. 27 pages.
- Still not grounded: individual vehicle lengths (offsets in cm), absolute common level.

## Status 2026-09-29, sixth pass - self-review (6/10 before, about 7/10 after)

Defects found and fixed:
- Sign: code solved b = F(e) - F(e - d) while claim/description say b = F(e - d) - F(e)
  (d = over-measurement). Code fixed (E8, E9). With the correct sign the exact nonlinear
  prediction at 660 cm is poor (M1 R2 about 0): it depends on the CDF shape between class
  boundaries, which counts do not fix. The test now uses the first-order prediction
  b(e) = b(520) f(e)/f(520) (density at the boundaries only): slope 0.73-0.95,
  R2 0.60-0.82. Claim 1(f) reworded to the slope ratio.
- "One offset explains 97-99 %" was not evidence: shuffled null gives 94-96 %. Replaced by
  standardised share 66-79 % vs shuffled <= 44 %, and r(520, 660) = 0.79-0.89. The 1160 cm
  link is weak (r 0.11-0.45); stated.
- "verified physical parameter" overclaim removed; Figure 2 caption; Table 6 PCA column
  removed; speed attribution stated as an upper bound (real speed change confounds).
- E10 `src/e10_checks.py` -> `results/e10_checks.json`: null test; failure drivers
  (failing units have small offsets, so not an interpolation artefact); interpolation
  sensitivity (offsets x0.89-1.13, classes agree 90-100 %); events (6 of 8 dated changes
  pass as offset changes of 32-65 cm, 2 are >30-point faults); held-out cross-junction
  pairs (M25 7.7-8.6 -> 4.4-4.9, all improve, shuffled control 11.1-11.3; M1 only
  9.9-10.9 -> 8.6-9.7, 4 of 8-9 improve).
- Claim 3 now also classifies the dated change with step (f).

Still open / next levers:
- Absolute level across chains not established (M1 junction). Candidate: link chains
  across junctions with slip-road class counts (validation only; near patent-1 territory).
- Ground truth: co-located WIM / camera classifier or probe-vehicle site.
- Lu, Yang & Chang (2014) unread; Azin & Yang raw PDF.
- Claim 1 is long (a-h); consider moving (g) correction to a dependent claim for breadth.

## Status 2026-09-29, fifth pass - claims strengthened after external review and search

- New verified art: US 6,876,949 B2 (entry 11, closest on stream-based length
  calibration), Dailey & Wall WA-RD 633.1 (entry 3), Lee & Coifman 2012 (entry 4).
  Dropped US 6,337,640 and US 7,764,197. Table A now 15 entries.
- **E9** `src/e9_consistency.py` -> `results/e9_consistency.json`: parameter-free
  cross-boundary test. Field r 0.81-0.92; injected 660 cm fault detected 67-99 %,
  1160 cm 48-58 %; true offset kept 81-95 %; common 30 cm chain shift changes 1 of 544 unit tests.
- Claims: 1 (adds (f) cross-boundary test; offset relative to chain reference; offset
  written only for length-offset faults), 2 refit, 3 dated step, 4 live, 5 speed
  attribution, 6 system (+360), 7 loops. New Table 7; old Tables 7-9 now 8-10; Figure 7(d)
  is the test; claim tree redrawn. 25 pages.
- Still open: Lu, Yang & Chang (2014) full text; Azin & Yang raw PDF via a browser.

## Status 2026-09-29, fourth pass — inventive step strengthened (self-review 5/10)

Self-review (no web) found: inventive step thin (3.5/10); "68-92 %" reduction stated as all
admitted pairs but was pairs touching a corrected detector (all pairs: 57-79 %); "sensitivity
correction" only a label. Fixed:

- **E8** `src/e8_offset_model.py` -> `results/e8_offset_model.json`. One length offset per
  unit explains 97.2-98.8 % of the detectors x boundaries bias variance in all 8
  corridor-months; fitted 660/520 ratio 0.15-0.19 vs 0.18-0.22 predicted from the stream's
  own length CDF (PCHIP through class shares; prediction 0.01-0.05 high every month). Offsets
  |d| median 31-36 cm, p90 72-100 cm. Fault class (residual > 0.3): M1 15-23 units/month,
  14 of 15 persist Mar->Jun. Speed attribution: speed explains median 4-8 cm of ~33 cm ->
  mostly detection-threshold error. Negative: correcting from the single offset is worse at
  660/1160 than per-boundary -> record still corrected per boundary.
- Claims now: 1 (adds step (e): stream CDF from chain's class shares, offset d in cm; (g)
  writes d as sensitivity correction), 2 refit, 3 dated step (split statistic spelt out),
  4 live, 5 fault class, 6 speed attribution, 7 system (+350), 8 loops. Attendance mark ->
  description only.
- New Figure 7 (offset model) and Table 6; figures renumbered to 10; both pair populations
  reported everywhere.

## Status 2026-09-29, third pass — IDF-B redrafted to the md guidance files

Deliverables: `patent/IDF-B_Length_Invariance_Recalibration.docx` and `.pdf` (20 pages,
A4). Built by `src/make_idfb.py` from `results/*.json`; figures by `src/make_figs.py`.

Applied from the guidance files (writing-guidelines, section_3k_compliance,
physical-technical-compliance, SKILL (2), diagram-tools, patent-draft-builder):
- two-sentence field; five-column prior-art table with 14 verified entries (8 publications,
  6 patents); single lead summary paragraph; exactly 3 objectives; [0001]-[0031] numbering
  in Sections 6-7; "Figure N:" / "Table N:" captions each with a short explanation;
  blue-header tables with alternating rows; 5 protection aspects before the claims;
- no mention of patentability law anywhere in the text (Section 12 "technical character");
  claim 1 anchored to the data-processing system (900) and link (130), not
  "computer-implemented";
- figures redrawn: zone-style architecture with roadside/processing boundary and a
  hardware feedback path (840 -> detector card), flowchart with stage bands, decision
  diamonds and refit engine, physical site schematic, 2x2 data panels (a)-(d), claim tree;
- build refuses on business words, banned phrases, placeholders, banned paragraph
  openers, or < 60 % physical tie-in in Sections 6-7 (currently 94 %).

New measurements: E7 `e7_timing.py` -> `e7_timing.json` (fit 8.2 s / 16.4 s per
corridor-month; 6.4-6.6 us per 15-min record reclassified). Probe now stores per-pair
values (Figure 4). Figure notes `idfb_fig_notes.json` (chain example, event continuity).

Still open before filing: Lu, Yang & Chang (2014) full text (closed access); Azin & Yang
raw PDF to `patent/prior_art_raw/` (ROSAP blocks scripts); user review.

## Status at end of second session 2026-09-29 — IDF-B drafted

Deliverable: `patent/IDF-B_Length_Invariance_Recalibration.docx` (+ `.pdf`, 17 pages),
built by `src/make_idfb.py` from `results/*.json` (refuses to build if a file is missing;
scans for placeholders and business vocabulary). Figures `src/make_figs.py`. Claim
reasoning `patent/claims_draft.md`. Verified prior art `patent/prior_art.md`, raw texts in
`patent/prior_art_raw/`.

Claims: 1 method (independent), 2 refit, 3 dated step, 4 live correction, 5 attendance
mark (3 daily SE + tolerance), 6 system (independent), 7 loop pairs.

New this session:
- **E5** `e5_refit.py` -> `e5_refit.json`. Refit on month before halves June residual:
  M25 0.92 -> 0.46 pts, M1 2.65 -> 1.43; pairs worse 2 -> 0, 14 -> 8.
- **E6** `e6_flag_rules.py` -> `flag_rules.json` (run as scratch, identical code). Local
  both-neighbour rule: fewer other-mark flips, far fewer injected faults caught. Median
  rule kept; no flag claim beyond claim 5. Correcting ALL fitted detectors beats
  correcting flagged only (E1), so the flag is maintenance-only — item 1 of the old list.
- **E2** now reports by chain length: p90 size error 27-72 % of injection; median gauge
  limits absolute size on short chains (item 2: accepted and stated, Section 8.5).
- **Probe** rebuilt as `src/probe.py` -> `results/probe.json` (was missing).
- E3 continuity: 3 of 8 events have both pairs reporting ±5 days; 4 have both pairs
  missing the same days (detector offline around the step); M1 2602 dated by one pair.
- Prior art verified from raw text: Bychkovskiy 2003 (neighbour calibration — conceded
  for chain solve), GB2385138A (background: length bias from loop installation), EP2790165A1,
  WSDOT WA-RD 647.1 (sensitivity from length distribution — conceded), Wu & Coifman 2014.

Open, before filing:
1. **Lu, Yang & Chang (2014) TRR 2443** — closed access (SAGE 403, Unpaywall closed).
   Needs VIT library access; read in full, check it does not size/correct.
2. **Azin & Yang raw PDF** — ROSAP blocks scripted download (Akamai 403). Save via
   browser to `patent/prior_art_raw/` so the closest-art row has text on disk.
3. User review of the IDF-B; inventor details go in IDF-A (IPR cell).

<details><summary>Previous status block (first session 2026-09-29)</summary>

## Status at end of session 2026-09-29 — where to resume

Done and measured (all in `results/`, code in `src/`):

- **E1** `evaluate_e1.py` -> `e1_out_of_sample.json`. Fit March, score Apr-Jun. Touched
  pairs, mean |gap| below 520 cm, flagged/additive: M25 7.9/8.0/8.1 -> 0.63/0.69/0.85
  pts; M1 9.7/9.2/8.9 -> 1.1/1.7/2.9 pts. Pairs made worse by >1 pt: M25 3/83, 3/81,
  2/71; M1 6/158, 10/154, 15/157. **Additive beats ratio** everywhere (ratio was the
  physics guess; measured and rejected). M1 decays by June -> biases change over time.
- **Bias spread** (March, chains >= 3): |b520| q25/50/75/90 = 0.4/2.5/6.1/12.7 pts (M25),
  0.4/2.8/7.3/12.1 (M1); median day-to-day SE ~0.1 pt. ~65 % of detectors exceed the
  1-pt floor — the flag floor needs a decision.
- **E3** `e3_steps.py` -> `e3_step_events.json`. Dated sensitivity-change events: both
  pairs of one detector step on the same day, equal and opposite. 8 events (M25 2 of 90
  detectors tested, M1 6 of 145); control 0 of 4,700 mismatched pairings. Examples
  M1/2602 (~13-15 May, -0.41/+0.46), M25/5986 (late March, -0.087/+0.087). Strongest
  corroboration that gaps are detector properties.
- **E2** `e2_injection.py` -> `e2_injection.json`. Injected faults localised 82-96 %,
  median size error ~0; p90 size error about half the injection and 0.2-0.85 other
  flags flip per injection (median gauge moves on short chains). Cluster gauge tried and
  **worse** (`e2_injection_clustergauge.json`); median kept.
- **E4** `e4_ablation.py` -> `e4_ablation.json`. Volume gate and free-flow condition make
  **little measurable difference** to E1 scores (M1 no-gate slightly worse May/Jun:
  1.77 vs 1.47, 2.89 vs 2.65 pts; M25 unchanged). Do not argue either as an accuracy
  feature; keep the gate only as the physical precondition (same vehicles).

Caveat to state in the IDF-B: E1 measures agreement between neighbours, which is
gauge-free; absolute accuracy of the consensus is not established (no ground truth).

Next, in order:
1. Decide flag floor (1 pt flags ~65 %); consider flag only where E3-type local evidence
   or both neighbours disagree in the same direction.
2. False-flag behaviour of the median gauge on short chains — accept and state, or fix.
3. Read Lu, Yang & Chang (2014) TRR 2443 in full (raw text).
4. Draft claims: 1 independent (receive -> slip-free pairs -> matched shares -> chain
   biases per boundary -> correct archive preserving totals -> maintenance record),
   dependents: additive model, periodic refit, dated equal-and-opposite step events,
   system claim.
5. IDF-B from `C:di\patent 2\src\make_idfb.py` helpers.

</details>

## Phase 2 — Data layer `[x]`

`src/series.py`: parse cached daily reports into per-site, per-month arrays (length bins,
total, speed) and cache the parsed form, so experiments do not re-read 11k JSON files.
`src/pairs.py`: slip-free adjacent pairs, matched intervals, admission by volume balance.

## Phase 3 — The method `[x]`

Share-below-boundary at each of three edges (520, 660, 1160 cm). Per pair, gap per edge.
Per slip-free segment, per-detector bias per edge by least absolute deviations on the
pairwise gaps, gauge fixed by zero median over the segment. Flag by threshold from the
reference-period spread. Correct counts by moving vehicles across each edge by the bias.
Output a sensitivity correction record.

## Phase 4 — Evidence `[x]` (E1-E6; ground-truth comparison not possible on open data)

- E1 out-of-sample: fit on March, correct April–June, measure reduction in adjacent-pair
  share discrepancy against the uncorrected record
- E2 synthetic injection: known offsets added to healthy detectors; detection,
  localisation, magnitude error, false alarms
- E3 baselines: fixed external reference distribution (Cheevarunothai-style); per-pair
  flag without chain localisation; total-count checks (blind to length offsets by
  construction)
- E4 lane-loss discrimination (volume deficit + share pattern) — dependent claim only if
  it measures cleanly
- E5 corroboration: step changes in a detector's gap series (maintenance events)
- E6 replication on a second month pair / corridor

## Phase 5 — Claims `[x]` — 2026-09-29

1 independent method claim, 4–6 dependents, 1 system claim. Five-part structure.

## Phase 6 — IDF-B `[~]` — redrafted to md guidance 2026-09-29, awaiting review

Reuse `C:\adi\patents\04_count_conservation\src\make_idfb.py` helpers and figure style. No placeholders.
