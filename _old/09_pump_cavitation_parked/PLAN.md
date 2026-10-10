# PLAN — Patent 09: self-calibrating pump controller, cavitation from efficiency residuals

Status markers: [ ] not started, [~] in progress, [x] done. Written 2026-10-06 for the user's review.

## 0. What was checked before writing this plan (done, 2026-10-06)

- Guidance re-read: section_3k_compliance, physical-technical-compliance, writing-guidelines,
  patent-draft-builder-SKILL, SKILL (2) (Frameworks 1-4), diagram-tools, dataset-strategy, and the
  reference IDF-B layout.
- Prior art read raw (notes in prior_art_raw/gp/screen_notes_2026-10-06.txt):
  - US 6,655,922 B1 (Rockwell, 2001), claim 1: flow and pressure data + "an adaptive classifier
    system adapted to detect pump cavitation existence and extent". Generic "AI detects cavitation
    from hydraulic data" is anticipated; the title's "AI controller" cannot carry novelty alone.
  - EP 2 196 678 A1 (ABB, 2008): cavitation features from drive torque and speed estimates.
  - US 11,994,150 B2 (Schneider, 2020): updated NPSHr from functional point and end-of-line data.
  - US 11,965,513 B2 (Aramco, 2021): NPSHr-flow equation for a pump group, NPSHa margin.
  - US 8,303,260 B2 (ITT, 2006): sensorless flow from calibrated closed-valve power curve.
  - US 9,777,748 B2 (Eaton), US 7,099,852 B2 (Reliance): motor-current signature.
- Data search: no open dataset with Q, head (or both pressures), power and cavitation truth.
  Zenodo CIRA pumps: vibration + outlet pressure only. Kaggle: vibration-only or simulated.
  Grundfos set: proprietary. Celtek et al. 2026 (Sensors): data on request. Oviedo 2018: figures.

## 1. Where the novelty has to come from ("novelty inside the topic")

The topic as titled is crowded. The draft will claim a specific physical mechanism, not "AI":

N1 Margin-gated self-calibration. The healthy efficiency and head surfaces, in affinity
   coordinates (phi = Q/nD^3, psi = gH/n^2D^2, eta), are fitted and continuously re-fitted only on
   samples whose suction margin sigma = NPSHa/NPSHr_ref is above a safe ratio (cavitation physically
   impossible). Wear and deposits move the baseline; cavitation cannot enter it.
N2 Margin-signature separation. The residual r = eta/eta_0 - 1 is regressed on a margin deficit
   x = max(0, sigma_k - sigma): r = c + s x. A wear or fouling loss is c (independent of margin);
   cavitation is s (appears only as margin shrinks). Same structure that made patent 06 work
   (separate two causes by their different dependence on a physical axis).
N3 Online knee. The margin sigma_k at which s becomes significant is learned per pump, giving the
   pump's own incipient-cavitation margin instead of a datasheet NPSHr.
N4 Drive action before head loss. When the margin-dependent component crosses a limit, the
   controller lowers speed through the variable-frequency drive (NPSHr falls with n^2) or raises
   suction (tank level, booster), before the 3 % head drop that defines NPSH3.
Each must survive the deeper prior-art read in Phase A; any that does not is dropped, not reworded.

## 2. Phases, gates and kill criteria

Phase A — Deep prior-art read (Claude, ~3 h)                                    [x]
  DONE 2026-10-06, report prior_art_raw/PHASE_A_REPORT.md. Gate A PASS: 13 patents + 10 papers
  raw-read; nothing does N1+N2. N1 alone near-obvious (US 7,112,037 baseline "assuming adequate
  NPSHa" + US 6,954,713 NPSHa calc); N4 alone known (Danfoss lowers speed on detection);
  US 11,994,150 reads any head deficit as wear (the confound N2 removes). Core = N2 with N1;
  N3, N4 dependent. Acoustic emission detects inception earlier than hydraulics (Mousmoulis) —
  state as a limit; the advantage claimed is hydraulic-only wear/cavitation separation.
  - Kallesoe C.S. (Aalborg University/Grundfos) model-based fault detection and isolation in
    centrifugal pumps (residuals from pump models, includes cavitation?) — highest risk to N2.
  - Patents: KSB, Grundfos, Sulzer, Xylem, Wilo, Danfoss, ABB on "efficiency deviation" or
    "performance curve deviation" cavitation; Chinese patents (离心泵 汽蚀 效率 残差 自校准).
  - Papers: efficiency/head-drop based incipient cavitation; NPSH3 vs incipient (ISO 9906,
    Gulich "Centrifugal Pumps" chapter on cavitation, if an open copy exists).
  GATE A: N1 and N2 not anticipated together. Kill or re-scope if a single reference does both.

Phase B — Prototype and development simulator (Claude, ~1 day)                 [x]
  DONE 2026-10-06: src/physics.py (IAPWS-IF97 vapour pressure, Kell density, NPSHa, head,
  efficiency, affinity coefficients), src/estimator.py (N1 gate R>=2, RLS baseline, c/d split,
  knee), src/controller.py (PROBE margin-step test, LIMIT, Modbus register), src/simulator.py and
  src/dev_run.py (DEV ONLY, output data/dev/, never evidence). Gate B PASS: all paths run.
  New feature N5 from the build: on a candidate alarm the drive lowers speed until R >= 2 and the
  residual's recovery decides cavitation (recovers) vs wear (does not) — physical discrimination
  in the loop. Lab sheet: RIG_PROTOCOL.md.
  - src/physics.py: IAPWS water vapour pressure, NPSHa, affinity coordinates, efficiency.
  - src/estimator.py: margin-gated recursive fit of the healthy surface (explainable: affinity
    polynomial or monotone spline with forgetting factor), residual, c + s x separation, knee.
  - src/simulator.py: development-only pump model (affinity laws, NPSHr ~ n^2, head-drop curve
    below NPSH3, slow wear) to test code paths and pick nothing that the rig data will judge.
    Simulator output never goes into Section 8.
  - src/controller.py: speed-command logic with dwell/hysteresis; Modbus/Profinet message format
    for the drive.
  GATE B: code runs end to end on simulator; every constant written down before rig data arrive.

Phase C — Laboratory evidence (needs the user; VIT fluid-mechanics lab or similar)     [ ]
  Rig: centrifugal pump on a closed loop or open sump with a suction throttling valve (or vacuum on
  the tank) and a discharge valve; VFD-driven motor.
  Sensors (with ranges to note in the IDF):
    - absolute pressure transducer at suction, gauge pressure transducer at discharge
    - electromagnetic or turbine flow meter
    - water temperature (PT100) at suction
    - power: VFD power/torque/speed readout and, ideally, a three-phase power analyser
    - accelerometer on the casing (>= 10 kHz band) and, if possible, a hydrophone or acoustic
      emission sensor: independent truth for incipient cavitation; a transparent inlet section or
      stroboscope helps but is optional
    - logger at >= 1 Hz for hydraulics, >= 25 kHz bursts for vibration/acoustics
  Test matrix (about 1-2 lab days):
    T1 healthy map: 3 speeds x 6-8 flows at high suction margin (calibration region)
    T2 NPSH sweeps (ISO 9906 style): at each speed and 3-4 flows, lower suction pressure in steps
       until beyond the 3 % head drop; hold each step 60-120 s
    T3 slow ramps: continuous suction-pressure ramp at fixed flow (tests detection lead in time)
    T4 emulated degradation without cavitation: partly closed suction strainer bypass or a
       recirculation/bypass valve, or a worn/trimmed impeller if the lab has one — tests that wear
       does not raise a cavitation alarm and that the baseline re-calibrates
    T5 closed loop: run the controller on the drive during T3 ramps (speed command recorded)
  Truth: NPSH3 from the 3 % head drop (standard); incipient onset from the acoustic/vibration
  high-frequency band (or visual); no-cavitation periods from T1/T4.
  Fallback if no rig: the user requests the Celtek et al. 2026 dataset and/or the Oviedo group data
  by e-mail; if neither arrives, Phase C fails and the patent is not drafted.
  GATE C: real data in data/ with a written log of each run.
  FOUND 2026-10-06: Zenodo 18500146 (Pardo Vigil, Gonzalez, Fernandez Oro et al., Univ. Oviedo,
  2026), data/zenodo_18500146/: H vs NPSH sweeps at 20/25/30/35 Hz, non-cavitating H and
  efficiency curves, acoustic spectra (incipient truth) at Q = 45/104/180 m3/h. Manually read
  curve points, no time series, no shaft power during sweeps, no wear runs. Licence conflict:
  Zenodo page says CC-BY-4.0, readme says CC BY-NC-SA — confirm before use. Can test: head-
  residual detection point vs NPSH3 and vs acoustic onset, per-pump knee vs NPSHr, n^2 scaling.
  Cannot test: N2 wear separation, N5 probe, efficiency residual. Not enough alone for Gate C.

Phase D — Evaluation (Claude, ~1 day)                                            [ ]
  Questions, each with a fair baseline:
    E1 Detection lead: margin (m of NPSHa) and time (s during T3) at which the method flags, against
       NPSH3 (3 % head drop) and against the acoustic onset.
    E2 Baselines on the same runs: datasheet-curve efficiency residual (no self-calibration);
       NPSHa/NPSHr threshold (US 11,965,513 style); drive torque/speed features (EP 2 196 678 style);
       vibration RMS threshold.
    E3 Wear rejection (T4): false cavitation alarms with and without N1/N2.
    E4 Closed loop (T5): head loss avoided, time below NPSH3 avoided, speed reduction needed.
    E5 Sensitivity: safe-margin ratio, window length, sensor noise (from the logged noise).
    E6 Physical metrics: sensor ranges and accuracy, sampling rates, computation per sample (us),
       command latency to the drive (ms).
  GATE D (kill criteria): method must flag before NPSH3 at most sweeps AND earlier than the margin
  threshold or the torque/speed baseline at a stated majority of sweeps, AND raise no more false
  alarms than the baselines during T4. If not, stop and report; do not draft.

  READY 2026-10-06: src/evaluate.py reads rig CSVs (format in its docstring) and writes
  results/evidence.json; tested on simulator CSVs (src/dev_rig_like.py -> data/dev/, DEV ONLY).
  KEY RISK seen in dev: with an accurate datasheet and no wear, a plain margin threshold at
  1.5 x NPSH3 alarms about as early as the method (~1 % loss). The method can only win where
  (i) the real NPSH3 differs from the datasheet (knee learned per pump), and (ii) wear is present
  (frozen baseline / Schneider-style reading fails). The rig must therefore include T4 at low
  margin and, if possible, a second impeller or a pump whose NPSH3 differs from its datasheet.
  Gate D compares against the best k of B1, not the worst.

Phase E — IDF-B (Claude, ~1 day)                                                  [ ]
  - Layout of the reference IDF-B; generator like 08 rev3 (numbers read from results/, build refuses
    if worded comparisons stop matching).
  - Title (apparatus form), Field with hardware anchors, 2.1 problem, 2.2 definitions; >= 13 raw-read
    references (>= 6 patents, >= 5 journal papers); Sections 6 (8-12 numbered paragraphs) and 7
    (15-25), Section 8 prose with rig figures; 5 protection aspects; claims 1 + 4-6 + system.
  - Figures: architecture (pump, VFD, sensors, controller, fieldbus) and flowchart in the
    diagram-tools style; data figures from rig data only (2 x 2 panels, validated palette).
  - Physical-technical framing: transducers, flow meter, VFD speed command as the physical action.

Phase F — Framework 4 audit and honest rating (Claude)                           [ ]
  - Novelty per reference, inventive step, claim support, sufficiency, physical-technical tests,
    writing audit with exact fixes; rating stated plainly; kill if the evidence is weak.

## 3. What the user needs to decide or provide

1. Is a centrifugal pump test rig with a suction throttling valve (or vacuum tank), VFD, suction and
   discharge transducers, flow meter and power readout available at VIT (fluid mechanics / mechanical
   lab)? If yes: who runs it, and can an accelerometer or hydrophone be added?
2. If no rig: are you willing to e-mail the authors of Celtek et al. 2026 (Sensors 26, 5596) and the
   Oviedo group (Proceedings 2018, 2, 1410) to request their data?
3. Keep "AI" in the title? Recommendation: no — say "self-calibrating" and "margin-conditioned
   residual"; the generic AI claim is anticipated (US 6,655,922 B1) and the 2025 CRI Guidelines
   penalise black boxes.

Decisions (user, 2026-10-06): "AI" dropped from the title; Phase A started. Rig/data question
still open.

## 4. Timeline (if a rig is available)

Day 1: Phase A + start Phase B (Claude). Day 2: Phase B done, rig protocol sheet for the lab.
Lab days (user): Phase C. Next 2 days: Phases D-F. Decision points at Gates A, C and D.
