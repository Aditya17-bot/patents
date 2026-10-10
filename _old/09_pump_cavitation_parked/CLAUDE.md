# CLAUDE.md — Patent 09: pump cavitation from hydraulic-efficiency residuals

## What this project is

Drafting a patent disclosure, with a working prototype and laboratory evidence, on (working title,
from the user's topic):

> **Self-Calibrating Pump Controller for Early Cavitation Detection from Hydraulic-Efficiency
> Residuals Conditioned on the Net Positive Suction Head Margin**

Physics / mechanism: a centrifugal pump's hydraulic efficiency eta = rho g Q H / P follows a fixed
surface in affinity coordinates (flow coefficient Q/nD^3, head coefficient gH/n^2D^2) while it is
healthy. Cavitation lowers head and efficiency only when the suction margin NPSHa/NPSHr shrinks
(NPSHa = (p_suction - p_vapour(T))/rho g + v^2/2g; NPSHr scales with speed squared by the affinity
law), so its residual depends on the margin; wear lowers efficiency at every margin. The healthy
surface is re-fitted continuously only on operating points whose margin is large enough that
cavitation is physically impossible, so wear moves the baseline and cavitation does not. The
margin-dependent part of the residual is the cavitation signal; the controller lowers speed (or acts
on suction) before the 3 % head drop that defines NPSH3.

Target jurisdiction: **India** (Section 3(k), 2025 CRI Guidelines); claims also tuned for US
*Alice/Mayo*. Deliverable: VIT **IDF-B** in the layout of
`C:\adi\patents\_shared\IDF-B_format_reference_Tablet_Dispenser.docx`.
Generator pattern: `C:\adi\patents\08_ammonium_ise\src\make_idfb.py` (rev3 structure). Plan in `PLAN.md`.

## Hard drafting rules (from the hub and _shared guidance)

1. Never use business-method language (revenue, cost, billing, pricing, customer, market,
   business, commercial, ROI) — including "costs"/"costly" in prose.
2. Every claimed advantage is a technical effect on the pump: detection before head loss, avoided
   cavitation operation, speed command to the drive, wear tracked without false cavitation alarms.
3. Every number in the IDF-B traces to `results/`. No placeholders, no "[TO BE MEASURED]" (this is
   what killed patent 03). Simulated data never appears as evidence (patent 07's problem); a
   physics simulator may be used only for development and is labelled as such in working notes.
4. Independent claim: receive measurements -> named transformation with physical rationale ->
   physically grounded constraint (margin-gated calibration) -> measurable improvement -> drive
   command. Few claims: 1 independent method, 4-6 dependents, 1 system.
5. No filing strategy, Section 3(k) discussion, "guarantees legal defensibility" or notes to the
   IPR cell inside the IDF-B.
6. Do not overstate: every limitation and every result that goes the wrong way is stated (patent
   08 lesson). Never add hardware or claims that the evidence does not test.

## Boundary with earlier patents

All other hub patents are hydrology, traffic, water quality or infosec; no overlap. Patent 02
(causal emission response interlock) is infosec; no overlap.

## Prior-art discipline

Raw text only (`prior_art_raw/`). Already read: US 6,655,922 B1 (adaptive classifier on flow and
pressure — generic AI detection is taken), EP 2 196 678 A1, US 11,994,150 B2, US 11,965,513 B2,
US 8,303,260 B2, US 9,777,748 B2, US 7,099,852 B2. Must still read: Kallesoe (Aalborg/Grundfos)
model-based fault detection for centrifugal pumps; KSB/Grundfos/Sulzer/Xylem/Danfoss patents on
efficiency or performance-curve deviation; Chinese patents.

## Data

No open dataset has flow, head or both pressures, power and cavitation truth (searched 2026-10-06,
see `prior_art_raw/gp/screen_notes_2026-10-06.txt`). Evidence must come from a laboratory NPSH test
rig (preferably at VIT) or from datasets obtained from authors on request by the user.

## Code conventions

Python 3.9, numpy, matplotlib, python-docx. Explainable estimators only (affinity-law structured
regression, splines, Gaussian process at most); no black-box networks.

## Layout

```
README.md       idea, feasibility, nearest art
PLAN.md         phases, gates, current status
src/            prototype code + make_idfb.py
data/           rig data (raw files as logged), downloads
results/        measured metrics — the evidence base
prior_art_raw/  raw text of cited references
patent/         IDF-B .docx/.pdf and figures
```
