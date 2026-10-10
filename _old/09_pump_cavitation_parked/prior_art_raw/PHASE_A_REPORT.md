# Phase A — deep prior-art read (2026-10-06)

All statements below are checked against raw text in `gp/` (Google Patents full text) or `lit/`
(PDF/HTML extracted to .txt). Where only an abstract was obtainable it is marked [abstract only].
Search log: `gp/_queries.txt` plus browser screens (about 350 patents screened by full-text term
counts for cavitation / NPSH / efficiency / suction / baseline-learn-calibrate; about 45 opened).

## Gate A verdict: PASS, with a narrower core than planned

No single reference fits a healthy efficiency (or head) baseline only on samples with a large
measured NPSH margin AND splits the residual into a margin-independent part (wear) and a
margin-dependent part (cavitation). N1 alone is close to obvious (see 7,112,037 + 6,954,713).
N4 alone is known (Danfoss). The inventive core must be N2 (margin-signature separation) with N1
as its precondition; N3 and N4 become dependent claims.

## Closest references and what each discloses (raw-verified)

| # | Reference | What it discloses | What it lacks |
|---|-----------|-------------------|---------------|
| P1 | US 6,655,922 B1 (Rockwell, 2001) | Flow + pressure data, "adaptive classifier system adapted to detect pump cavitation existence and extent" (claim 1), neural network (claim 2) | No efficiency surface, no margin gating, no wear separation |
| P2 | US 7,112,037 B2 (ITT, 2002) | Automatic characterisation of torque and speed at a set point on start-up; later test line compared; data "taken during system or suction changes" rejected by slope test; baseline presumed valid "assuming adequate Net Positive Suction Head Available" | NPSH margin never measured or used as gate; degradation only, no cavitation/wear split |
| P3 | US 6,954,713 B2 (Fisher-Rosemount, 2002) | Stored characteristic curve; NPSHa computed and compared with NPSHr (claim 1); generic pump model "updated or calibrated with actual pump data" | Threshold comparison only; no residual dependence on margin; no wear handling |
| P4 | US 11,994,150 B2 (Schneider, 2020) + Ejjabraoui & Ineza, Springer chapter (2024) [abstract] | Head difference between current head (suction + discharge pressure) and theoretical head from end-of-line characteristics → adapted NPSHr used in real time (claim 1); chapter: "correcting the net-positive suction head required for the change in pump characteristics resulting from mechanical wear" | Treats every head deficit as wear; a cavitation head drop would be misread as wear — the confound this patent removes |
| P5 | US 11,965,513 B2 (Aramco, 2021) | Single NPSHr–flow equation for a pump group, NPSH margin, shut-down when NPSHa < NPSHr + margin | Fixed datasheet NPSHr; no residual |
| P6 | EP 2 196 678 A1 / CN 101750258 B (ABB, 2008) | Cavitation features from frequency-converter torque and speed estimates | No suction pressure, no margin |
| P7 | US 6,487,903 B2 (2001) | NPSHa from suction pressure and temperature vs NPSHr at measured speed; dynamic pressure below a % of the non-cavitating value (claim 1) | Fixed reference; no wear separation |
| P8 | US 11,920,600 B2 (2017) | Statistical difference in specific energy → wear as probable cause; cavitation detected as a separate event; NPSH as monitored variable | Rule-based pre-diagnosis; no margin-conditioned residual |
| P9 | US 11,852,148 B2 / US 12,209,590 B2 (2019) | Pump curve, NPSHA/NPSHR display, trend vs "acceptable baseline operation", cavitation warning near curve end | Generic baseline; no gating, no separation |
| P10 | US 20200388140 A1 (2019) | Suction/discharge pressure + flow, signatures, cavitation as out-of-limit condition, shut-down command | Signature matching only |
| P11 | CN 106368960 B (2016) | Automated NPSH3 bench test: inlet valve stepped until head falls 3 % | Off-line test-stand procedure, not in-service |
| P12 | US 9,777,748 B2, US 7,099,852 B2 | Motor-current signature bands for cavitation | Different signal |
| P13 | US 8,303,260 B2 (ITT, 2006) | Sensorless flow from calibrated closed-valve power curve | No cavitation separation |

| # | Literature | What it discloses (raw) | What it lacks |
|---|------------|-------------------------|---------------|
| L1 | Kallesøe, Izadi-Zamanabadi, Rasmussen, Cocquempot (2004), AAU full text | Head and torque models fH(Q,ω), fT(Q,ω); five faults incl. leakage (wear) and "performance degradation due to cavitation", isolated by structural analysis; observer sensitivity to cavitation "very low"; cavitation modelled as linear term | No NPSH or inlet pressure in the isolation; no margin gating |
| L2 | Kallesøe, Cocquempot, Izadi-Zamanabadi, IEEE TCST 14 (2006) [abstract only] | Adaptive observer + ARR fault detection on pump | Same |
| L3 | Samanipour, Poshtan, Sadeghi, Turk. J. EECS 25 (2017) [abstract only] | Pressure deviation from pump performance curve as residual; SOM network; "capable of detecting incipient cavitation" | Fixed curve; no wear; no margin |
| L4 | Ahonen, Tamminen, Ahola, Kestilä, Insight 53 (2011) [bibliographic only; full text behind bot check] and IEEE TIE (2011) [abstract] | Frequency-converter estimation of pump state; normal-state speed/torque compared with new data for cavitation (secondary description) | Needs full text — flagged |
| L5 | Han et al., Sensors 24 (2024), PMC11175120, full text | Test rig; NPSH1 % = inception, NPSH3 % = fully developed; vibration + stator current detection; data "unavailable due to privacy" | Hydraulic residual not used |
| L6 | Mousmoulis et al., Eur. J. Mech. B/Fluids, DOI 10.1016/j.euromechflu.2018.10.015, Lancaster e-print, full text | AE + accelerometer + visualisation; literature: high-frequency noise maximum "far before the 3% total head drop" | Acoustic only |
| L7 | Liu et al., AIP Advances 14 (2024) [abstract] | Vibration rms + kurtosis + BP network for cavitation states | Vibration |
| L8 | Kim et al., Sensors (2026), PMC13517267, full text | Physics-informed health indices, model trained on one healthy baseline day, residual attribution | AODD pump, no cavitation/NPSH |
| L9 | Turunen, Aalto MSc thesis (2022), full text | CNN on VFD torque: cavitation hard to separate from normal (78.4 % weighted accuracy) | Torque only |
| L10 | Danfoss Drives web page (CBM cavitation), full text | Current-signature cavitation detection in the VFD; "motor speed is automatically lowered within predefined limits when cavitation is detected" | N4 generic action known |

## Addendum — N5 margin-step discrimination test (screened 2026-10-06, 107 patents)

N5: on a candidate alarm the drive lowers speed until the suction margin ratio is restored; recovery
of the efficiency residual = cavitation, no recovery = margin-independent loss (wear).
- US 10,711,787 B1 (2014), claim 3: controller "automatically reduce a speed of an impeller ... when
  a cavitation event is detected" — speed reduction as remedy known (also Danfoss L10).
- US 12,092,116 B2 (2018, fire apparatus): active "deadhead health test" (closed discharge at set
  speed) for wear-ring health; cavitation from a separate cavitation sensor. Active test known for
  wear, but not a margin step used to discriminate wear from cavitation.
- US 10,844,854 B2 (2017): accelerometer RMS over threshold and time; no hydraulic discrimination.
- US 9,341,055 B2: wellbore suction pressure monitoring; no discrimination test.
Verdict: no reference uses a commanded margin step and residual recovery to separate wear from
cavitation. N5 is a strong dependent claim (or part of the independent claim) because it is a
physical action of the drive that produces the diagnostic itself.

## Consequences for the plan

1. Independent claim core: margin-gated healthy surface (N1) + regression of the residual on the
   margin deficit with a margin-independent term c and a margin slope s (N2) + drive action keyed
   to s (not to c). Novel over each reference; obviousness argument: P2+P3 give a baseline taken at
   adequate NPSHa, but none teaches that the residual's dependence on the margin separates wear from
   cavitation; P4 teaches the opposite inference (head deficit -> wear -> raise NPSHr).
2. N3 (per-pump knee) and N4 (speed reduction by n^2 law to restore margin) are dependent claims.
3. Honest limit to state in the IDF: acoustic emission detects inception earlier than any
   hydraulic method (L6). The claimed method's advantage is hydraulic-only operation that separates
   wear, not earliest possible detection. Evaluation must compare against acoustic onset honestly.
4. Open items: full text of Ahonen 2011 (Insight) and Kallesøe thesis (AAU, Cloudflare) — user can
   download manually; Schiavello & Visser 2009 (TAMU, 403) for NPSH margin physics.
