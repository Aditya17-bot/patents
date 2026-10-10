# CLAUDE.md — Patent project

## What this project is

Drafting a software-only patent application, with a working prototype as supporting
evidence, on:

> **A Method for Reconstructing Missing Traffic-Count Records in a Historical Volume
> Dataset Using Direction-of-Flow Conservation Constraints at Network Nodes**

Target jurisdiction: **India** (Section 3(k), 2025 CRI Guidelines), with the claim also
tuned to survive US *Alice/Mayo*. India is the stricter test, so optimise for India.

Source brief: `Patentable Software-Only Inventions in Water, Electricity, and Traffic
Analytics_ Landscape and Drafting Guide.pdf` (Topic 3). Decision rationale and the
public-data survey are in `README.md`. Phase plan is in `PLAN.md`.

## Hard drafting rules — these override normal writing instincts

1. **Never** use business-method language anywhere in the spec, claims, or supporting
   docs: *revenue, cost saving, billing, pricing, tariff, customer, marketing, monetise,
   business, commercial benefit, ROI*. In India, `OpenTV Inc. v. Controller of Patents`
   (2023:DHC:3305) makes the business-method bar **absolute** — no technical-effect
   escape hatch. One stray sentence about saving money can sink the application.
2. Every claimed advantage must be a **technical effect on a technical system**, stated
   as: improved accuracy/integrity of a dataset, reduced computation or memory,
   improved consistency of a downstream control dataset. Not "helps planners decide".
3. The 2025 CRI Guidelines require the technical effect to be **disclosed and
   evidenced**, not asserted. Every claim of improvement in the spec must trace to a
   number the prototype actually produced. No invented figures, ever. If a result is not
   yet measured, write `TBD` rather than a plausible-looking number.
4. Independent claim follows the five-part structure:
   receive specified data → specific named technical transformation with its physical
   rationale → apply the physically-grounded constraint → produce a dataset whose
   improvement is measurable → downstream technical action or quantified system-level
   improvement.
5. The constraint is a **hard constraint**, not a regularisation penalty. That distinction
   is the inventive step and must survive into the claim wording.

## Data

Both sources are open, free, no registration. Never add a source that needs payment or
a login without flagging it first.

- **WebTRIS** — `https://webtris.nationalhighways.co.uk/api/v1.0/`, no key.
  15-minute volumes per site. Client: `src/webtris.py` (caches to `data/webtris/`).
- **DfT bulk CSV** — Open Government Licence v3.0, already in `data/raw/`
  (`aadf.zip`, `bydir.zip`). Read straight from the zip; do not unpack the 150 MB CSV.

MIDAS site names encode the topology — parse, do not hardcode:

```
MIDAS site at M25/4055A priority 1 on link 199123501; GPS Ref: 555982;175115; Clockwise
                   ^^^^ ^                                                     ^^^^^^^^^
                   |    marker suffix: A/B = mainline carriageway             direction
                   |                   J,K = slip roads on the A side
                   |                   L,M = slip roads on the B side
                   marker number = chainage, so it orders sites along the road
```

## Code conventions

- Python 3.9, standard library plus `pypdf`, `python-docx`, and numpy/scipy/pandas where
  genuinely needed. No heavyweight ML frameworks — a black-box model is a liability
  under the 2025 CRI Guidelines, which explicitly require AI/ML claims not to be black
  boxes.
- Cache every API response to disk. Reruns must not re-hit WebTRIS.
- Keep raw data out of version control; `data/` is generated.
- Prefer explicit, readable numerics over clever vectorisation — this code is an exhibit
  and may be read by an examiner or an evaluator.

## Layout

```
README.md      topic decision + data survey
PLAN.md        phases, gates, current status
CLAUDE.md      this file
src/           prototype code
data/raw/      DfT bulk downloads
data/webtris/  cached API responses
results/       measured metrics — the evidence base for the spec
patent/        patent.docx (final deliverable) + drafting notes
```
