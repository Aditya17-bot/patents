# CLAUDE.md — Patent 3

## What this project is

Drafting a software-only patent disclosure, with a working prototype as supporting
evidence, on:

> **A Method for Recalibrating Vehicle-Length Measurement in a Chain of Roadside
> Vehicle Detectors Using the Invariance of Vehicle Length Between Adjacent Detectors**

Physics: a vehicle's length does not change between two detectors a few hundred metres
apart. Where no slip road joins or leaves between them, both detectors see the same
vehicles, so their shares of vehicles in each length class must agree. A persistent
difference can only be measurement error. Each detector sits in two adjacent pairs, so
solving along the chain localises the faulty detector and sizes its length offset.

Target jurisdiction: **India** (Section 3(k), 2025 CRI Guidelines), claim also tuned to
survive US *Alice/Mayo*. Deliverable: VIT **IDF-B**, same format as the user's accepted
IDF-Bs (`C:\adi\patents\04_count_conservation\patent\IDF-B_Count_Derived_Conservation_Constraints.docx`,
generator `C:\adi\patents\04_count_conservation\src\make_idfb.py`). Phase plan in `PLAN.md`.

## Hard drafting rules — these override normal writing instincts

1. **Never** use business-method language anywhere in the spec, claims, or supporting
   docs: *revenue, cost saving, billing, pricing, tariff, customer, marketing, monetise,
   business, commercial benefit, ROI*. `OpenTV Inc. v. Controller of Patents`
   (2023:DHC:3305) makes the Indian business-method bar **absolute**.
2. Every claimed advantage is a **technical effect on a technical system**: accuracy of
   the length-class count dataset, consistency between adjacent detectors, a sensitivity
   correction applied to a physical detector unit. Not "helps planners decide".
3. The 2025 CRI Guidelines require the technical effect to be **disclosed and
   evidenced**. Every number in the IDF-B must trace to a file in `results/`. No invented
   figures. In working notes, write `TBD` for anything unmeasured; in the IDF-B itself
   there are **no placeholders at all** — drop or reword a statement that has no number.
4. Independent claim follows the five-part structure: receive specified data → named
   technical transformation with its physical rationale → physically grounded constraint
   → dataset whose improvement is measurable → downstream technical action.
5. **Few claims.** Target: 1 independent method claim, 4–6 dependents, 1 system claim.
   One mechanism, argued well, beats eighteen claims defended thinly.

## Boundary with patent 1 (filed; not yet published)

Patent 1 (`C:\adi\patents\04_count_conservation`) claims conservation of **total** vehicle counts: map-free
relation recovery, reconstruction, and correction of a miscounting instrument (its
Claim 13). This invention must not claim anything derived from total-count conservation
residuals. Total counts are used here only as an **admission gate** (the pair sees the
same vehicles); the invention is the use of **length-class shares** as the invariant.
Patent 1's disclosure is not prior art to this one until it publishes. File this one
before then.

## Prior-art discipline

WebFetch summaries have fabricated quotes from papers and patents (twice, in patent 1).
Any reference that enters the IDF-B prior-art table must be checked against its raw text
(curl or download, extract, grep) before any statement about it is relied on.

## Data

Open, free, no login. Never add a source that needs payment or a login without flagging
it first.

- **WebTRIS** — `https://webtris.nationalhighways.co.uk/api/v1.0/`, no key. 15-minute
  records per site: `Total Volume`, four length bins (`0 - 520 cm`, `521 - 660 cm`,
  `661 - 1160 cm`, `1160+ cm`), speed bins, `Avg mph`. Client `src/webtris.py` caches to
  `data/webtris/`, and reads patent 2's cache (`C:\adi\patents\04_count_conservation\data\webtris`,
  M25/M1 March–June 2025) before touching the network.

MIDAS site names encode topology — parse, do not hardcode:

```
MIDAS site at M25/4055A priority 1 on link 199123501; GPS Ref: 555982;175115; Clockwise
                   ^^^^ ^                                                     ^^^^^^^^^
                   |    marker suffix: A/B = mainline carriageway             direction
                   |                   J,K = slip roads on the A side
                   |                   L,M = slip roads on the B side
                   marker number = chainage, so it orders sites along the road
```

## Code conventions

- Python 3.9, standard library plus `pypdf`, `python-docx`, numpy/scipy/pandas where
  genuinely needed. No ML frameworks — a black box is a liability under the 2025 CRI
  Guidelines.
- Cache every API response to disk. Reruns must not re-hit WebTRIS.
- Prefer explicit, readable numerics over clever vectorisation — this code is an exhibit.

## Guidance files in this folder

`section_3k_compliance.md`, `physical-technical-compliance.md`, `writing-guidelines.md`,
`patent-draft-builder-SKILL.md`, `SKILL (2).md`, `diagram-tools.md`,
`dataset-strategy.md` — copied from patent 2, general drafting guidance.

## Layout

```
README.md      the idea, the feasibility probe, nearest art
PLAN.md        phases, gates, current status
CLAUDE.md      this file
src/           prototype code
data/webtris/  cached API responses (new fetches only; old ones read from patent 2)
results/       measured metrics — the evidence base
patent/        IDF-B and drafting notes
```
