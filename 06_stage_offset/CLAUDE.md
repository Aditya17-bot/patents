# CLAUDE.md — Patent 4

## What this project is

A software-only patent disclosure, with a working prototype as evidence, on:

> **Estimating and Correcting the Stage Offset of a River Gauging Station Between Field
> Visits from the Discharge Recorded at a Neighbouring Gauging Station on the Same River**

Physics: water is conserved along a river reach. Where no significant tributary,
abstraction or storage lies between two gauging stations, the discharge at one, delayed
by the travel time, predicts the discharge at the other up to a slowly varying flow
ratio. A gauging station converts its recorded stage to discharge through a
stage-discharge rating. When the channel control changes (scour, fill, vegetation,
debris) or the stage sensor drifts, the true relation becomes Q = R(h + s): a stage
offset s. A stage offset produces a relative discharge error equal to s times the rating
log-slope d ln R/dh, which is large at low stage and small at high stage; a change in
the flow ratio produces a relative error that does not depend on stage. That signature
lets the neighbour's record be converted into a stage offset in feet, the same quantity
the hydrographer measures at a field visit, and applied to the rating between visits.

Target jurisdiction: **India** (Section 3(k), 2025 CRI Guidelines), claims also tuned to
survive US *Alice/Mayo*. Deliverable: VIT **IDF-B** in the accepted layout (see memory
`idfb-format-reference`; generator pattern from `C:\adi\patents\05_length_invariance\src\make_idfb.py`).

## Hard drafting rules — these override normal writing instincts

1. **Never** use business-method language anywhere: *revenue, cost saving, billing,
   pricing, tariff, customer, marketing, monetise, business, commercial benefit, ROI*.
   Also avoid *water rights accounting* framed as allocation of a commodity.
2. Every claimed advantage is a **technical effect on a technical system**: accuracy of
   the discharge record computed by a gauging station, a corrected rating offset written
   to the station's data logger, a field-visit (re-measurement) trigger.
3. Every number in the IDF-B must trace to a file in `results/`. No invented figures. No
   placeholders in the IDF-B: drop or reword anything without a number.
4. Independent claim: receive specified data -> named technical transformation with its
   physical rationale -> physically grounded constraint -> dataset whose improvement is
   measurable -> downstream technical action.
5. **Few claims.** 1 independent method claim, 4–6 dependents, 1 system claim.
6. Never mention Section 3(k), patentability law, or filing strategy inside the IDF-B.
   No "Note on Filing" section.

## Boundary with the user's other filings

- Patent 1 (`C:\adi\patents\04_count_conservation`, filed, not yet published) claims total-count conservation
  in road traffic networks. This disclosure uses water conservation only to relate two
  gauges; the invention is the conversion of the discrepancy into a stage offset through
  the rating log-slope and its use on the rating. Do not claim network-wide flow
  reconstruction or imputation.
- Patent 3 (`C:\adi\patents\05_length_invariance`) claims length-class invariance between road detectors.
  No overlap in domain or quantity.

## Prior-art discipline

WebFetch summaries have fabricated quotes before. Any reference in the IDF-B prior-art
tables must be checked against its raw text (download, extract, grep) first. Raw texts
live in `patent/prior_art_raw/`.

## Data

Open, free, no login (USGS public-domain data):

- 15-min gage height (00065) and discharge (00060): `nwis.waterservices.usgs.gov/nwis/iv/`
- Field visits (measured discharge, mean gage height, control condition, rating quality):
  `api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements`
- Ratings (expanded, shift-adjusted table, rating id and start): `waterdata.usgs.gov/nwisweb/get_ratings`
- Topology (gauges on the same mainstem): NLDI `api.water.usgs.gov/nldi/`

- Indian applicability (V8): CAMELS-IND (Mangukiya et al., ESSD 17:461, 2025; open on
  Zenodo), daily observed discharge of 242 CWC gauge sites, downloaded through the
  user's Kaggle account (mirror `abhisingh2615/camels-ind-india-streamflow`, user
  permitted Kaggle use on 2026-10-03) into `data/kaggle/camels_ind/`. No stage, so only
  pair admission and departure noise can be run on it.

Client `src/usgs.py` caches every response under `data/usgs/` (gzip). Reruns never
re-hit the network. Pairs come from topology (`src/network.py`), not hand-picking.

## Code conventions

Python 3.9, standard library plus numpy, python-docx, matplotlib, pypdf. No ML
frameworks. Explicit, readable numerics: this code is an exhibit.

## Layout

```
README.md      the idea, feasibility, nearest art
PLAN.md        phases, gates, current status
src/           prototype code
data/usgs/     cached API responses
results/       measured metrics — the evidence base
patent/        IDF-B, figures, prior-art raw texts
```
