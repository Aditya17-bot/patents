# Framework 4 audit — IDF-B 09 (rev1, 2026-10-06)

Built by `src/make_idfb.py`; 20 pages; checker passed (no business words, banned phrases or
placeholders; 23 numbered paragraphs, 100 % name hardware; Tables 1-9, Figures 1-6).

## Novelty (per reference)
| Ref | Overcome by | Status |
|---|---|---|
| P1 US 7,133,749 (+US 7,574,284) | continuous daily anchor from production pulses; onset by collapse of rise vs same day's first pulses; common constant across sensors; gated gain; delivery ratio | OVERLAPPING on "field capacity anchors the sensor" — closest art |
| P2 US 8,862,277 | no cross-sensor correction; deficiency test not gain-free | NOVEL |
| P3 US 9,775,308 | corrects reading, not dose | NOVEL |
| P4-P6 sensor devices | in-place correction, no device change | NOVEL |
| P7 EP 3 016 492 B1 | claim 1 read raw: irrigation output from stored data and readings as reported; no calibration in text | NOVEL |
| N1-N6 | used as read | NOVEL |
Verdict: NEEDS STRENGTHENING at inventive step vs P1 + N5 (an examiner may combine "field capacity
as reference" with "several sensors per section"). The answer is the measured difference between a
fixed and a rolling anchor (2.05 vs 1.44 WC %) and the scale-free onset rule.

## Patentability
- Industrial applicability: PASS (greenhouse irrigation computers, valve output).
- Inventive step: AT RISK (see above); strongest elements are (d)+(e) together.
- Claim support: claims 1-4, 6 supported by Section 8; claim 5 (delivery alarm) has no measured
  detection rate (stated as limitation).
- Sufficiency: PASS (constants, rules, worked example [0017]).
- Experimental support: PARTIAL — no independent truth of slab water (no slab weights); evidence is
  pair agreement of physically identical slabs + decision replay.

## Physical-technical
Test 1 PASS (sensors, valve/pump, meters, gutter); Test 2 PASS (valve actuation on corrected reading,
but shown by replay, not in a greenhouse); Test 3 PASS; Test 4 100 % of numbered paragraphs.

## Writing
No banned phrases (checker). Risk LOW-MODERATE: some long sentences in 4.5 and 8.6.

## Honest rating
Moderate. Real problem with large measured effect (pair gap 7.35 -> 1.44 WC %, 8/12 sensors change
valve decisions on >20 % of intervals), clean open data, but closest art P1 is near and there is no
slab-weight truth. Two things would raise it: (1) the 4TU v2 gutter-weight data as truth (acceptance
criterion 1 in 8.10); (2) reading EP 3 016 492 claims raw.

## Rev1b additions (same day)
- P1-style one-off commissioning anchor (first 14 onset days, fixed): median pair gap
  2.46 vs rolling 1.44 WC %; rolling lower in 4/6 (level Automatoes,
  worse Digilog); valve decisions differ on median 49 % of intervals.
  Added to 4.2, 8.4, Table 9 -> inventive-step argument vs P1 now measured.
- Delivery alarm: false-alarm bound 0/95 section-weeks at L = 0.3,
  3 at L = 0.2; detection rate still unmeasured (no faults in data).
- EP 3 016 492 B1 claims read raw. Remaining open item: slab-weight truth (4TU offline all day 2026-10-06).
Rating unchanged: moderate, closer to good if 4TU slab weights confirm the corrected level.

## Rev2 (2026-10-06, review of two user-raised problems)
Problem 1 "evidence is sensor agreement, not accuracy": E8 (`src/e8_drain_cup.py`, `results/e8_drain_cup.json`)
uses the drain EC probe (EC_drain_PC, separate instrument) as drain truth. Label sound: fires after 11-50 % of
pulses, <= 6.3 % on metered-zero-drain days, <= 1.3 % in quiet periods. Reading at first drained pulse minus
anchor (held-out half, 737 sensor-days): raw vs P* 4.88 WC % (0/12 sensors within 1), one-off commissioning
(P1-style) 4.77 (1/12), rolling 1.10 (10/12). Accuracy at the drain point vs independent instrument; dry-back
size in litres still unverified (needs slab weights). Null result reported in 8.11: pre-pulse reading
predicts which pulse drains weakly for all anchors (AUC 0.53-0.55).
Problem 2 "same plateau for all slabs": claim 1 rewritten to steer on drain deficit D = P_s(d) - WC (own slab's
drain onset); offset cancels, no common-plateau assumption. Valve decisions identical to old rule (D > d is
WC* < P* - d), so all replay numbers stand. P* moved to dependent claim 2 (display / set-points as WC).
New claim 6: drain EC probe check + sensor check signal 440. Claims now 1 + 5 + 1 (system = claim 7).
Inventive step vs P1 now stronger: P1-style one-off anchor misses physical drain by 4.77 WC % median.
Rating: moderate -> moderate-good.

## Rev2b (2026-10-07)
- Claim 5 detection rate now measured on injected faults (E9, `src/e9_dripper_fault.py`,
  `results/e9_dripper_fault.json`): partial closure of one slab's dripper line injected into the measured weekly
  delivery ratios (ratio x k, first order). L = 0.3: 64 / 90 / 98 % of 30 / 40 / 50 % closures alarmed within
  2-4 weeks, 0 of 77 fault-free windows; 10 % closures not separable (4 %). L = 0.2: 86 % of 30 % closures,
  9 % chance alarms. Labelled as injected in 8.6, 8.11, Table 7 (V5) and Table 10. IDF-B 23 pages.
- Guidance .md set (writing guidelines, 3(k), physical-technical, section builders) re-checked against the
  IDF-B: zero hits for every listed banned phrase; 100 % of numbered paragraphs name a physical element.
- Slab weights: 4TU still in maintenance 2026-10-07. Wayback copy of the v2 record shows the same abstract as
  v1 and one file (ndownloader 24757220, 7z), not archived; v1 ReadMe lists no weighing. The earlier note
  "v2 adds gutter weighing" is unverified and probably wrong.
Rating: moderate-good (unchanged; claim 5 no longer untested).
- V9 (E10, `src/e10_litres_to_drain.py`, `results/e10_litres_to_drain.json`): litres dosed from the first pulse
  to the first probe-detected drained pulse (dose meter + drain EC probe, no slab sensor, no drain meter) vs
  morning drain deficit, held-out half, 749 sensor-days / 80 days. Pooled Spearman: rolling 0.49, one-off
  commissioning 0.26, raw P* 0.21; day-bootstrap 95 % CI of rolling - raw 0.21..0.35, rolling - commissioning
  0.16..0.32. Within-sensor weaker (median 0.32, 0.05..0.63). Litre route to relative gain within 15 % of rise
  route in 4/6, same side of 1 in 5/6. In 4.5, 8.8 (renamed "... and the Dose Meter (V8, V9)"), Table 7,
  Table 10, 8.11, Discussion. First evidence on the deficit away from the drain point that is not sensor
  agreement. Rating: moderate-good, nearer good; slab weights would still settle the litre scale.

## Rev3 (2026-10-07, user feedback on claims / prior art)
- Claim 1 rewritten as the explicit chain: pulses -> response per pulse -> collapse = drain onset -> sensor-specific
  plateau -> rolling reference in a reference memory -> drain deficit -> valve. No numbers in claim 1.
- Claim 3: ranges supported by the sensitivity test (fraction 0.2-0.4, window 7-28 d) plus preferred values.
- Claim 4: filling route vs uptake route, gain applied only on agreement, "whereby" a one-route distortion is not applied.
- Claim 7: architecture (sensor input 210, pulse-volume input 220, units 310/320, reference memory 330, deficit 350,
  valve output 410/420 -> 510).
- Prior art: P2 family (US 8,751,052) discloses an ADAPTIVE field-capacity mode (~10-day time constant) — the
  closest art to the rolling reference; previously undescribed. Added P8 US 11,930,744, P9 US 8,961,068.
  4.2 rewritten: each class (one-off drainage calibration, adaptive drainage calibration, dynamic irrigation,
  sensor construction, gain) distinguished by teaching AND by measured effect on the same data.
- E11 (`src/e11_p2_anchor.py`): P2-type anchor (FC from fast-fall end after last pulse, same 14-day median):
  1.75 WC % from physical drain, 4/12 within 1, vs drain onset 1.10, 10/12; litres Spearman 0.43 vs 0.49
  (CI of difference 0.03..0.10); pair gap similar (1.33 vs 1.44) — any self-anchor removes offsets.
  Table 9 now 4 anchors; Table 10 row; V10 in Table 7.
- Not doable: closed-loop greenhouse run (no rig); second facility / sensor / coir (no open data found:
  Kaggle, Zenodo searched 2026-10-07).
Rating: moderate-good -> good-minus (P2 adaptive mode is closer art than thought, but measured effect separates).
