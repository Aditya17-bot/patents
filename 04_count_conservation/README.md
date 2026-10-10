# Patent project — Topic 3 (flow-conservation-constrained traffic imputation)

## Chosen topic

**A Method for Reconstructing Missing Traffic-Count Records in a Historical Volume
Dataset Using Direction-of-Flow Conservation Constraints at Network Nodes.**

Topic 3 from the landscape guide. Chosen over Topics 1, 2 and 4 on one criterion the
guide does not rank on: *whether the input data actually exists publicly, free, and
without gatekeeping.*

| Topic | Technical strength | Public free data reality |
|---|---|---|
| 1 — NRW apportionment | strong | needs DMA bulk-inflow totalizers + per-customer billing + logged supply hours. Not published anywhere. Dead. |
| 2 — transformer overload | strong | needs consumer→transformer mapping from DISCOM GIS. Not public. Dead. |
| 4 — meter-data integrity | strong | needs feeder aggregate energy *and* the individual consumers under that feeder. No open dataset pairs them. Dead. |
| **3 — traffic imputation** | **strong** | **two fully open, no-login, no-payment sources verified live (below).** |
| 5 — accident hotspots | moderate | data fine (MoRTH), but the guide flags heavy academic prior art. |

Topic 3 also has the property the guide calls out as the best possible position: the
physical constraint (flow conservation at a node) is *simultaneously* the inventive step
and the Section 3(k) / Alice technical-effect anchor. It is not "apply ML to data".

## Data sources — verified reachable 2026-08-03

### Primary: National Highways WebTRIS (England)

- REST API, no key, no registration, no payment: `https://webtris.nationalhighways.co.uk/api/v1.0/`
- `/sites` → 20,076 MIDAS/TMU sites, 11,234 currently Active, with lat/long, carriageway
  direction, and link id parsed from the site name.
- `/reports/Daily?sites=<id>&start_date=DDMMYYYY&end_date=DDMMYYYY&page=&page_size=`
  → **15-minute** interval records: `Total Volume`, volume split by vehicle length class
  (0–520cm / 521–660 / 661–1160 / 1160+), speed-bin histogram, `Avg mph`.
- Contains genuine missing/blank intervals — the imputation problem is real, not synthetic.
- Motorway corridors carry mainline sites plus on-slip and off-slip sites, so
  `upstream_mainline + on_slip − off_slip = downstream_mainline` is an exact,
  same-timestamp conservation identity. This is the strongest possible form of the
  constraint.

### Secondary: DfT road traffic statistics (Great Britain, whole network)

- Bulk CSV, Open Government Licence v3.0, no login: already downloaded to `data/raw/`.
  - `aadf.zip` (18.6 MB → 150 MB CSV) — AADF per junction-to-junction link.
  - `bydir.zip` (31.6 MB) — **AADF by direction of travel**, with `count_point_id`,
    `road_name`, `start_junction_road_name`, `end_junction_road_name`, `direction_of_travel`,
    `link_length_km`, `easting`/`northing`, per-vehicle-class counts, years 2000–2025, plus
    `estimation_method` flagging which rows DfT itself estimated rather than counted.
- Gives the *network-node* version of the constraint (junction inflow = outflow) across a
  whole national road network, and gives a second, independent evaluation setting.

### Indian data — checked, and not usable as the evidence base

The method is jurisdiction-neutral and the filing target is India, so Indian data was
investigated for the worked example. It does not exist at the required granularity:

- **OpenCity "Bengaluru City Traffic Signal Data"** — ~120 junctions, but the resources
  are **PDF files of signal timings only**. No vehicle counts, no approach volumes, no
  turning movements. Licence field says "No License Provided".
- **Bengaluru Traffic Police datasets** on OpenCity — violations and crash records, not
  link-level volumes.
- **data.gov.in transport sector** — registered-vehicle totals, accident statistics,
  state-level aggregates. Nothing giving directional link-level counts with the network
  topology needed to write a conservation identity.

Conclusion: the evidence base stays WebTRIS. The India-facing content is in the framing
— Indian jurisdiction, Section 3(k) drafting, and applicability to Indian networks —
rather than in a second dataset. Worth stating plainly in the disclosure: the method
needs only counts and topology, both of which Indian authorities hold internally even
though they do not publish them.

Both WebTRIS and DfT were fetched successfully from this machine; MnDOT's feed
(`data.dot.state.mn.us`) was tested and is **not reachable** — do not rely on it.
PeMS is reachable but requires an account, so it is a fallback only.

## Plan

1. **Corridor extraction** — pick one motorway corridor from WebTRIS, classify sites into
   mainline / on-slip / off-slip, order them by chainage, build the node list where the
   conservation identity holds.
2. **Gap characterisation** — measure the real missingness pattern (rate, run lengths,
   whether gaps are per-site or network-wide).
3. **Baselines** — temporal mean-by-time-of-day, linear interpolation, KNN across sites,
   matrix/tensor completion. These are the prior art the claim must beat.
4. **The invention** — imputation solved as a constrained problem where node-level
   inflow/outflow balance is a *hard* constraint on the imputed values, not a penalty.
5. **Evidence** — MAE/RMSE reduction vs. each baseline, plus a conservation-residual
   metric showing the baselines produce physically inconsistent datasets and this does not.
   The 2025 CRI Guidelines require the technical effect to be *evidenced*, not asserted.
6. **Drafting** — specification with an explicit "Technical Effect" paragraph, independent
   claim built to the guide's five-part structure, dependent claims narrowing the
   constraint and the data types. Scrub every business-method word.

## Layout

```
data/raw/      bulk DfT downloads (gitignored — large)
data/webtris/  cached WebTRIS API responses
src/           fetch + prototype code
patent/        specification and claims drafts
```
