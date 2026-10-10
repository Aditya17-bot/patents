# CLAUDE.md — Patent 09: Drain-onset recalibration of substrate water-content sensors

**Read `HANDOVER.md` first** — it says where work stopped and what to do next.

## What this project is

Drafting a patent disclosure, with a working prototype as supporting evidence, on (IDF-B rev2 title):

> **System and Method for Recalibrating Substrate Water-Content Sensors from the Drain Onset of their
> Slabs and Controlling the Irrigation Valve on the Corrected Reading**

Physics / mechanism: a rockwool slab stores each irrigation pulse until it reaches its drainage plateau;
then pulses pass to drain and the WC rise per pulse collapses. That collapse (relative to the same day's
first pulses, so independent of sensor scale/offset) marks the drain onset of each sensor's own slab. The
reading just after it is the daily plateau; a rolling reference from past days' plateaus tracks drift.
Control acts on the **drain deficit** D = reference plateau - reading (offset cancels; no assumption that
all slabs drain at one water content). Optional common scale WC* = P* - D (claim 2). Gain corrected only
when two physical routes agree (claim 4). Drain EC probe in the gutter = independent drain check (claim 6).
Physical action: irrigation valve / pump opened when D exceeds a set-point.
Raw problem size: paired GroSens sensors in one compartment disagree by up to ~15 WC %.
(Original idea was a metered water balance; abandoned as truth because the daily drain meter batches.)

Target jurisdiction: **India** (Section 3(k), 2025 CRI Guidelines); claims also tuned for US *Alice/Mayo*.
Deliverable: VIT **IDF-B** in the layout of `C:\adi\patents\_shared\IDF-B_format_reference_Tablet_Dispenser.docx`.
Generator pattern: `C:\adi\patents\06_stage_offset\src\make_idfb.py`. Phase plan in `PLAN.md`.
TRL 4 (open real data, no hardware). VIT provides nothing — no rig.

## Hard drafting rules

1. **Never** use business-method language (revenue, cost saving, billing, pricing, tariff, customer,
   marketing, monetise, business, commercial benefit, ROI). Do not cite the AGC "Economics.pdf".
2. Every claimed advantage is a **technical effect on a technical system** (water, drain, root-zone EC).
3. Every number in the IDF-B traces to a file in `results/`. Working notes may say `TBD`; the IDF-B has
   **no placeholders**.
4. Independent claim: receive specified data → named technical transformation with its physical
   rationale → physically grounded constraint → measurably improved dataset → downstream technical action.
5. **Few claims**: 1 independent method, 4–6 dependents, 1 system claim.
6. No filing strategy, Section 3(k) discussion or notes to the IPR cell inside the IDF-B.

## Boundary with earlier patents

04 (count conservation, traffic), 05 (length invariance, traffic), 06 (river stage offset), 07 (fan
coast-down), 08 (ammonium sonde, killed). Do not claim generic conservation constraints on counts (04) or
neighbour-gauge offsets (06); this one is specific to substrate slabs, dosed pulses and drain.

## Prior-art discipline

WebFetch summaries have fabricated quotes. Check every cited reference against raw text (download,
extract, grep). Keep raw text in `prior_art_raw/`. Prior art shapes the claims; it is not a gate on the
topic (user rule, 2026-10-06).

## Data

- `data/agc/` — Autonomous Greenhouse Challenge 2nd edition (WUR 2019-20), Kaggle mirror
  `piantic/autonomous-greenhouse-challengeagc-2nd-2019` (= 4TU v1). 6 compartments (Reference + 5 teams):
  5-min climate + Cum_irr, GrodanSens (2 slab sensors each: WC, EC, T), daily Irr / Drain (L/m2).
- 4TU v2 (doi 10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7): one 7z file (ndownloader 24757220).
  Earlier belief that it adds gutter weighing is unverified — archived v2 abstract equals v1, v1 has no
  weighing. 4TU in maintenance 2026-10-06/07; public API (no key): `https://data.4tu.nl/v2/articles?search_for=...`.
  Fetch when back into `data/agc_v2/` and check before relying on it.
- Guidance: `guidance/*.md` (writing, 3(k), physical-technical, section builders); user rules here win.
- Drain EC (`EC_drain_PC`, 5 min, in GreenhouseClimate.csv) is used as an independent drain detector (E8).
- `data/neon/` — NEON STER soil water (side study). Token: `C:\adi\patents\_secrets\neon_token.txt`.
- Kaggle CLI (user's account) is allowed.

## Code conventions

- Python 3.9, numpy/pandas/scipy, `pypdf`, `python-docx`. No ML black boxes. Readable numerics.
- Run scripts as `python src\x.py` from `09_substrate_wc` (not `-I`; they import each other).
