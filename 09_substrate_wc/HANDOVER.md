# HANDOVER — Patent 09 (update at the end of every work block)

Last updated: 2026-10-07, session 3b. **IDF-B rev3 built (24 pp), copied to IDFs (Downloads only when user asks).** Added E9
(claim 5 detection on injected dripper faults) and E10/V9 (morning deficit vs metered litres to drain).
4TU still in maintenance 2026-10-07 (checked twice).

## Session 3b (2026-10-07, user feedback: claims, prior art, validation) — rev3, 24 pp

- Claims: claim 1 = explicit chain (pulses -> response -> collapse = drain onset -> sensor-specific plateau ->
  rolling reference in reference memory -> drain deficit -> valve), no numbers. Claim 3 = tested ranges
  (fraction 0.2-0.4, window 7-28 d) + preferred values; build asserts ranges match experiments E1. Claim 4 =
  filling vs uptake route, gate, "whereby". Claim 7 = architecture (210, 220, 310, 320, 330 memory, 350, 410/420).
  Table 4 step letters and Figure 6 updated.
- Prior art: P2 family US 8,751,052 has an ADAPTIVE field-capacity mode (~10-day time constant) — closest art to
  the rolling reference. Added P8 US 11,930,744, P9 US 8,961,068 (raw text in prior_art_raw, notes_2026-10-07.md).
  4.2 rewritten: teaching + measured effect per class. E11 `src/e11_p2_anchor.py`: P2-type anchor 1.75 WC % from
  physical drain (4/12 within 1) vs drain onset 1.10 (10/12); litres 0.43 vs 0.49 (CI diff 0.03..0.10); pair gap
  similar (any self-anchor removes offsets). Table 9 has 4 anchors; V10 in Table 7; Table 10 row.
- Not doable here: closed-loop greenhouse run (no rig); second facility / sensor model / coir (no open data —
  Kaggle and Zenodo searched). Tell user these need a partner greenhouse.
- Pending user decision: trim five self-weakening statements (8.4 Digilog/constants, 8.7 meter balance,
  8.8 onset delay, 8.11 AUC) — proposed, not yet approved.
- Outputs copied to IDFs only. NEVER copy to Downloads unless the user asks.

## Session 3 (2026-10-07)

- Guidance .md files from Downloads (writing-guidelines, section_3k_compliance, physical-technical-compliance,
  patent-draft-builder-SKILL, patent-section-builder-SKILL (= `SKILL (2).md`), diagram-tools, dataset-strategy)
  copied to `guidance/`. Same files already sat flat in `_shared/`. Hub CLAUDE.md step 2 now says: copy them into
  every new patent folder's `guidance/`. IDF-B re-scanned against every list in them: zero hits.
- Slab weights: the "4TU v2 adds gutter weighing" note is UNVERIFIED and probably wrong. Wayback copy of the v2
  record page (12764777/2) has the same abstract as v1 and one file `ndownloader/files/24757220` (7z, not in
  Wayback); v1 ReadMe lists no weighing. When 4TU is back: download that 7z into `data/agc_v2/` and look, but
  expect no weights. No other mirror found (Kaggle, Zenodo searched).
- E9 `src/e9_dripper_fault.py` -> `results/e9_dripper_fault.json`: closure of one slab's dripper line injected
  into the measured weekly delivery ratio (ratio x k). L = 0.3: 64/90/98 % of 30/40/50 % closures alarmed in
  2-4 weeks, 0/77 fault-free windows; L = 0.2: 86 % of 30 %, 9 % chance alarms. Labelled "injected" in 8.6, 8.11.
- E10 `src/e10_litres_to_drain.py` -> `results/e10_litres_to_drain.json` (V9, in 8.8): litres dosed from first
  pulse to first probe-drained pulse vs morning drain deficit. Pooled Spearman rolling 0.49 / commissioning 0.26 /
  raw P* 0.21; bootstrap CI of rolling-raw 0.21..0.35. Within-sensor median 0.32. Litre-route gain within 15 %
  of rise route 4/6. Build asserts guard the wording of both.

## Start here next

1. Check 4TU (`curl -s "https://data.4tu.nl/v2/articles?search_for=autonomous%20greenhouse"`; "maintenance" in
   HTML = down). If up: fetch file 24757220 (7z) of article 12764777 v2 into `data/agc_v2/`, list contents. If
   gutter weights exist, do the old step: `src/e11_slab_weight.py` (held-out half; weighed loss vs D x gain;
   weighed water at drain onset over the season). If not, record that and drop the item.
2. Otherwise: await user review of rev2b; submit through the IPR cell.

## Where we are

Topic: in-situ recalibration of rockwool slab water-content (WC) sensors from the **drain onset** of their own
slab (collapse of the per-pulse rise under routine pulses), rolling reference from past days only, irrigation
valve actuated on the **drain deficit** D = P_s(d) - WC (sensor offset cancels; no assumption that slabs share
one plateau). Common constant P* is optional (claim 2, display). Data: Wageningen Autonomous Greenhouse
Challenge 2nd ed. (Kaggle mirror; 6 compartments x 2 GroSens sensors, 2019-12-16 to 2020-05-30).

Deliverable: `patent/IDF-B_Substrate_WC_Drain_Onset_Recalibration.docx/.pdf` (rev2b, 23 pages); copies in
`C:\adi\patents\IDFs\09_Substrate_WC_Drain_Onset_Recalibration.*` (refresh after rebuilds; never copy to Downloads unless the user asks);
STATUS.md row 09 updated (rev2b, moderate-good).
Claims (rev2): 1 method (drain deficit) + 5 dependents (2 common scale P*, 3 constants, 4 gated gain + dry-back,
5 delivery-ratio alarm, 6 drain EC probe check -> sensor check signal 440) + 1 system (7).
Audit: `patent/framework4_audit_2026-10-06.md` (rev2 section at the end).
Rebuild everything: `bash src/rebuild.sh` (from `src`). Figures use right-angle arrows only (user rule).

## Session 2 (rev2): two user-raised problems, both addressed

- "Evidence = sensor agreement, not accuracy": E8 `src/e8_drain_cup.py` -> `results/e8_drain_cup.json`.
  Drain EC probe (EC_drain_PC, separate instrument) as drain truth: a pulse is drained if the probe steps
  >= 0.15 dS/m within 15 min. Label sound: fires after 11-50 % of pulses, <= 6.3 % on metered-zero-drain
  days, <= 1.3 % in quiet periods. Reading at first drained pulse minus anchor (held-out half, 737
  sensor-days): raw vs P* 4.88, one-off commissioning (P1-style) 4.77, rolling 1.10 WC %; within 1 WC %:
  0 / 1 / 10 of 12 sensors. IDF-B Section 8.8 + Table 9. Strengthens inventive step vs US 7,133,749.
  Honest nulls in 8.11: pre-pulse reading predicts which pulse drains weakly (AUC ~0.54, all anchors);
  collapse rule finds onset 0-275 min later than the probe (reading differs only 0.30 WC %, plateau flat).
- "Same plateau for all slabs": claim 1 rewritten onto the drain deficit; replay decisions identical
  (D > d == WC* < P* - d), so all earlier numbers stand. Figures 1, 2, 4, 6 relabelled.

## Key results (all in `results/`)

- Pair gap |WC1-WC2|, held-out half, median of 6 compartments: raw 7.35, fixed 2.05, rolling 1.44 WC %
  (`rolling_anchor.json`); 427/473 compartment-days lower, z = 17.52 (`experiments.json` E2); 9 settings 0.96-1.58.
- One-off commissioning anchor: 2.46 vs rolling 1.44 WC %, rolling lower 4/6 (`e6_commissioning.json`).
- Drain-probe check: see above (`e8_drain_cup.json`).
- Valve replay (`control_replay.json`): 8/12 sensors > 20 % different decisions; median 16 % pulses into a draining slab.
- Gain (`scale_offset.json`, `dryback.json`): routes agree 4/6; dry-back gap 12.9 raw, 11.9 gated, 15.0 % ungated.
- Delivery ratio (`dripper_ratio.json`, `e7_delivery.json`): false alarms 0/95 at L = 0.3; detection on injected closures in `e9_dripper_fault.json` (90 % of 40 % closures).
- Litres to drain vs morning deficit (`e10_litres_to_drain.json`): pooled Spearman rolling 0.49, commissioning 0.26, raw 0.21.
- Loader: Cum_irr midnight reset fixed; pulse sum / meter 0.999-1.010. Daily meter balance unusable as truth.

## Weak points / next steps (in order)

1. **Slab-weight truth** — probably not in 4TU v2 (see Session 3). V9 is the litre check meanwhile.
2. Plateau falls over the season (Fig 3(c)): real slab change vs drift unknown; the valve decision on D does not
   depend on it; slab weights would settle it.
3. Claim 5 detection measured only on injected faults (E9); physical closure test is the acceptance item.
4. Then await user review; submit through the IPR cell (IDF-A by the cell).

## User rules (also in memory)

- Do not gate topics on novelty; find novelty at claim level. Never "no idea has passed".
- Open data only, TRL 4, VIT gives nothing. Kaggle CLI allowed.
- Keep this file current; the user clears sessions and starts fresh agents. "Keep continuing until all parts are over".
- Numbers are not skipped. IDF-B: no placeholders, no business words; the checker in `make_idfb.py` enforces
  this (note: banned "per se" also matches "per sensor" — reword).

## Files

- Analysis: `src/agc.py` (loader), `pulse_gain.py`, `holdout.py`, `uptake_balance.py`, `pair_agreement.py`,
  `offset_anchor.py`, `rolling_anchor.py`, `dripper_ratio.py`, `scale_offset.py`, `dryback.py`,
  `control_replay.py`, `experiments.py`, `e6_commissioning.py`, `e7_delivery.py`, `e8_drain_cup.py`,
  `e9_dripper_fault.py`, `e10_litres_to_drain.py`, `data_check.py`.
- Drafting guidance: `guidance/*.md` (user's rules; user rules in CLAUDE.md win on conflict, e.g. right-angle arrows).
- Drafting: `src/figs.py` (Figures 1-6), `src/make_idfb.py` (IDF-B + checker), `src/rebuild.sh`.
- Prior art: `prior_art_raw/notes_2026-10-06.md` + raw .txt of every cited reference.
- Side study (not core): `src/neon.py`, `probe_rain_storage.py`, `probe_night_conservation.py`.
- Dead agriculture ideas: `C:\adi\patents\_screening\agri_round1_2026-10-06.md`.
