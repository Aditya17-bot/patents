# CLAUDE.md — Patent NN: <short title>

## What this project is

Drafting a patent disclosure, with a working prototype as supporting evidence, on:

> **<Full title of the invention>**

Physics / mechanism: <the physical invariant or effect the invention relies on, in 3–5 sentences>.

Target jurisdiction: **India** (Section 3(k), 2025 CRI Guidelines); claims also tuned for
US *Alice/Mayo*. Deliverable: VIT **IDF-B** in the layout of
`C:\adi\patents\_shared\IDF-B_format_reference_Tablet_Dispenser.docx`.
Generator pattern: `C:\adi\patents\06_stage_offset\src\make_idfb.py`. Phase plan in `PLAN.md`.

## Hard drafting rules

1. **Never** use business-method language (revenue, cost saving, billing, pricing, tariff,
   customer, marketing, monetise, business, commercial benefit, ROI).
2. Every claimed advantage is a **technical effect on a technical system**.
3. Every number in the IDF-B traces to a file in `results/`. Working notes may say `TBD`;
   the IDF-B has **no placeholders** — drop or reword anything unmeasured.
4. Independent claim: receive specified data → named technical transformation with its
   physical rationale → physically grounded constraint → measurably improved dataset →
   downstream technical action.
5. **Few claims**: 1 independent method, 4–6 dependents, 1 system claim.
6. No filing strategy, Section 3(k) discussion or notes to the IPR cell inside the IDF-B.

## Boundary with earlier patents

See `C:\adi\patents\IDFs\STATUS.md`. <State what this patent must not claim.>

## Prior-art discipline

WebFetch summaries have fabricated quotes. Check every cited reference against its raw
text (download, extract, grep) before relying on it. Keep raw text in `prior_art_raw/`.

## Data

Open, free, no login. Flag any source that needs payment or a login before adding it.
Cache every download to `data/`; reruns must not re-hit the network.

## Code conventions

- Python 3.9, standard library plus `pypdf`, `python-docx`, numpy/scipy/pandas where needed.
  No ML black boxes.
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
