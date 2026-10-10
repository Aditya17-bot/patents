# CLAUDE.md — Patent 08: ammonium sonde floor anchored at laboratory samples

## What this project is

Drafting a patent disclosure, with a working prototype as supporting evidence, on:

> **System and Method for Correcting the Ammonium Reading of an In-Situ River Water-Quality
> Sonde from the Floor of Its Own Record, Anchored at Laboratory Samples**

Physics / mechanism: the reading of an ammonium ion-selective electrode is the true
concentration plus a calibration offset that moves at each service and drifts between them.
River ammonium rises in pulses and falls back to a low site background between them, so a
low quantile of the sonde's own readings over several days (the floor) tracks background +
offset. At a laboratory sample the offset is known (reading minus laboratory result), which
fixes the height g of the floor above background. The offset in force is floor - g, applied
to every reading in real time. (The first candidate, a conductivity-proportional cation
interference term, failed the evidence gate: see PLAN.md.)

Target jurisdiction: **India** (Section 3(k), 2025 CRI Guidelines); claims also tuned for
US *Alice/Mayo*. Deliverable: VIT **IDF-B** in the layout of
`C:\adi\patents\_shared\IDF-B_format_reference_Tablet_Dispenser.docx`.
Generator pattern: `C:\adi\patents\06_stage_offset\src\make_idfb.py`. Phase plan in `PLAN.md`.

## Hard drafting rules

1. **Never** use business-method language (revenue, cost saving, billing, pricing, tariff,
   customer, marketing, monetise, business, commercial benefit, ROI).
2. Every claimed advantage is a **technical effect on a technical system**: accuracy of the
   ammonium record of the sonde, false pollution alarms raised by the monitoring station,
   the offset in force written to the sonde controller.
3. Every number in the IDF-B traces to a file in `results/`. Working notes may say `TBD`;
   the IDF-B has **no placeholders** — drop or reword anything unmeasured.
4. Independent claim: receive specified data → named technical transformation with its
   physical rationale → physically grounded constraint → measurably improved dataset →
   downstream technical action.
5. **Few claims**: 1 independent method, 4–6 dependents, 1 system claim.
6. No filing strategy, Section 3(k) discussion or notes to the IPR cell inside the IDF-B.

## Boundary with earlier patents

See `C:\adi\patents\IDFs\STATUS.md`. Patent 06 corrects a river gauging station's stage
offset from a neighbouring station's discharge; this one uses no neighbouring station and
no discharge. Do not claim neighbour comparison, flow ratios or stage offsets. Patents 04
and 05 are road-traffic; no overlap.

## Prior-art discipline

WebFetch summaries have fabricated quotes. Check every cited reference against its raw
text (download, extract, grep) before relying on it. Raw text in `prior_art_raw/`
(`gp/` patents via `src/gp_fetch.py`, `lit/` papers and vendor documents).

## Data

Open, free, no login, Open Government Licence (Environment Agency, England):
- Hydrology API water-quality sondes, raw (quality 'Unchecked'), 15-minute:
  `environment.data.gov.uk/hydrology/id/measures/{station}-amm-i-subdaily-mgL/readings`
  and `-cond-i-subdaily-uS`, `-temp-i-subdaily-C`.
- Water Quality Archive API (JSON-LD only, header `Accept: application/ld+json`):
  `environment.data.gov.uk/water-quality/sampling-point/{point}/observation?determinand=0111`
  (ammoniacal nitrogen as N, mg/L, laboratory).
`src/ea.py` caches every response under `data/ea/`; `EA_OFFLINE=1` forbids network access.
Some archive values equal the sonde reading (copied, not laboratory): drop exact matches.

## Code conventions

- Python 3.9, standard library plus `pypdf`, `python-docx`, numpy, matplotlib. No ML.
- Readable numerics over clever vectorisation — this code is an exhibit.

## Guidance

`C:\adi\patents\_shared\` — section_3k_compliance, physical-technical-compliance,
writing-guidelines, patent-draft-builder-SKILL, diagram-tools, dataset-strategy.

## Layout

```
README.md       idea, feasibility probe, nearest art
PLAN.md         phases, gates, current status
src/            prototype code + make_idfb.py
data/           cached downloads
results/        measured metrics — the evidence base
prior_art_raw/  raw text of cited references
patent/         IDF-B .docx/.pdf and drafting notes
```
