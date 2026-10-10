# Prior art — verified entries only

Every statement below was checked against raw text on disk (`patent/prior_art_raw/`)
unless marked otherwise. WebFetch summaries are not used for any entry.

## 1. Azin & Yang (2020), UDOT report UT-20.15 — CLOSEST ART

*Multi-Stage Algorithm for Detection-Error Identification and Data Screening*, University
of Utah for Utah DOT, October 2020. `https://rosap.ntl.bts.gov/view/dot/60813`

Verified 2026-09-28 from pypdf text (see PLAN.md Phase 1). The raw PDF is **not** in
`prior_art_raw/`: ROSAP now returns Akamai 403 to scripted downloads (2026-09-29), and the
copy in a patent-2 scratchpad turned out to be an HTML error page. Re-download through a
browser before the IDF-B is finalised.

What it does (from the earlier verification): 5-min aggregated PeMS data; compares the
average effective vehicle length (AEVL) distribution of each detector with adjacent
stations (K-S test); Multiple Comparison with the Best across adjacent stations to single
out the station statistically different from the others; upstream/downstream comparison
to decide which is faulty; marks detectors that need correction through maintenance or
recalibration; notes on-ramps affect AEVL downstream.

Conceded: comparing a length statistic between adjacent detectors, localising the odd
one, flagging it for recalibration.
Not in it: per-detector, per-boundary signed bias size; correction of the archived class
counts; length-class shares of a classifying detector (AEVL is a single-loop speed
calibration quantity mixing speed, occupancy and length); interval-matched comparison with
volume-balance admission; dated attribution of a calibration change.

## 2. Lu, Yang & Chang (2014), TRR 2443:40–48, doi 10.3141/2443-05

*Algorithm for Detector-Error Screening on Basis of Temporal and Spatial Information.*
**Not read.** Closed access (Unpaywall `oa_status: closed`; SAGE 403). Needs institutional
access. Known only through its citation in entry 1 (comparison of AEVL distributions of
adjacent detectors). Do not characterise beyond that until read.

## 3. Bychkovskiy, Megerian, Estrin & Potkonjak (2003), Proc. IPSN

(Volume and pages not in the PDF; cite as IPSN 2003 only.)

*A Collaborative Approach to In-Place Sensor Calibration.* Raw: `bych.pdf`, `bych.txt`.

Verified passages:
- Abstract: "a two-phase post-deployment calibration technique ... In its first phase, the
  algorithm derives relative calibration relationships between pairs of co-located
  sensors, while in the second phase, it maximizes the consistency of the pair-wise
  calibration functions among groups of sensor nodes. The key idea in the first phase is
  to use temporal correlation of signals received at neighboring sensors when the signals
  are highly correlated (i.e. sensors are observing the same phenomenon) to derive the
  function relating their bias in amplitude."
- "To achieve true calibrated results, one must have a reference point to the ground
  truth. In typical systems, this can be achieved by manually calibrating a subset of the
  sensors in the system, and allowing the calibration to adjust the remaining sensors
  based on the calibrated subset."

Conceded: relative calibration of neighbouring sensors from pairwise relations, made
consistent over a group; absolute level needs a reference. This is the general principle
of the chain solve. It is described for a continuous sensed field (light), with the
pairwise function fitted on correlated time series; it does not concern classified vehicle
counts, class boundaries, or reclassification of an archive.

## 4. GB 2385138 A (filed and priority 2002-10-02, published 2003-08-13; Golden River Traffic Ltd), *Validation and calibration of vehicle loop detection systems*

Raw: `GB2385138A.txt` (Google Patents HTML, tags stripped).

Hardware: validation loops with switched conductors placed over the loop sensors to
simulate a passing vehicle. Background passages, verified:
- Length from a dual-loop pair depends on "an accurate knowledge of the fixed dimensions of
  the loop and the distance between loops in a pair"; vehicle path at an angle or off the
  centreline introduces errors that "will not be easily apparent from a physical
  examination of the site, especially since it is not easy with an active highway to go
  onto the road surface to check these geometric relationships."
- Wrong number of turns gives loops "differing sensitivities"; a detector threshold shift
  "will in effect 'shorten' the length of the vehicle observed."
- "irregularities in the loop installation and its condition that cannot be revealed even
  by a detailed inspection ... can generate systematic under or over reading of count,
  vehicle speed and vehicle length" (steel reinforcement near one loop, depth, feeders).
- Conventional validation: test vehicles and drivers ("at least 10 vehicles and drivers
  are required"), or a secondary sensor system brought to site, or the trailer apparatus
  parked over the loops in the lane under test.

Use: background for the technical problem (length bias is a per-installation property;
finding it conventionally needs site access). Not a reference against the method.

## 5. EP 2790165 A1 (priority 2013-04-09, withdrawn), *Quality determination in data acquisition*

Raw: `EP2790165A1.txt`.

Presence-pulse ("atomic data stream") level; models of signal sequences taking sensor
topology and environment into account; error classification and correction; a detector
parameter recommendation module recommending "sensitivity" and "measurement time"
settings from a detector reliability model; truck detection by CNN from pulse lengths and
headways. Uses "logical-topological correlation between neighbouring loops and sections".

Distinct: microscopic pulse data, black-box models, error rates. No comparison of
length-class shares between detectors observing the same vehicles; no per-boundary bias.
Conceded in general: recommending a detector sensitivity setting as the output of a data
quality process.

## 6. Nihan, Wang & Cheevarunothai (December 2006), WSDOT WA-RD 647.1

*Improving Dual-Loop Truck (and Speed) Data: Quick Detection of Malfunctioning Loops and
Calculation of Required Adjustments.* Raw: `wsdot_647_1.pdf`, `wsdot_647_1.txt`
(66 pages). The TRR 1945 paper (Cheevarunothai, Wang & Nihan 2006) is its journal
version and is not archived; cite the report.

Verified passages:
- "The algorithm identifies dual-loop sensitivity problems using individual vehicle
  information extracted from high-resolution loop event data and corrects dual-loop
  sensitivities through a two-step procedure: 1) remove the sensitivity discrepancy
  between the two single loops and 2) adjust their sensitivities to the appropriate level."
- "the SV-length distribution reported by Wang and Nihan (2004) was used as the
  ground-truth vehicle length distribution for SVs."
- "Features of vehicle length distribution can be used to set the two single loop
  sensitivities to the correct sensitivity level."

Conceded: setting loop sensitivity from the vehicle-length distribution. Distinct:
event data, external reference, one station at a time. IDF-B entry 2.

## 7. Wu & Coifman (2014), Transportation Research Part C

*Improved vehicle classification from dual-loop detectors in congested traffic.* Raw:
`wu_coifman_2014b.pdf`, `.txt` (author preprint, ceg.osu.edu). Verified: "the dual loop
approach works well in free flow traffic ... This approach implicitly assumes that vehicle
acceleration is negligible, but unfortunately at low speeds this assumption is invalid and
length-based classification performance degrades in congestion." Basis of the free-flow
condition. IDF-B entry 6.

## Added 2026-09-29 (second pass, for the md-guided IDF-B), all verified from raw text

- **Minge et al. (Nov 2012), MnDOT 2012-33, FHWA Pooled Fund TPF-5(192)** — `minge_2012_mndot.pdf/.txt`.
  4.1 "it is recommended that a probe vehicle process be used as the primary calibration
  method ... one or more vehicles of known speed and length are driven through the subject
  site ... the detector is adjusted to match the known values after the run." 2.4.2 causes
  of length-based error.
- **Coifman & Kim (2009), Transportation Research Part C** — author draft
  `coifman_kim_2009.pdf/.txt`. Single-loop speed estimation and length classification;
  recalibrates speed via on-time ratios of successive vehicles. Volume/pages not in draft.
- **Balzano & Nowak (2007), Proc. IPSN (April 25-27, 2007)** — `balzano_nowak_2007.pdf/.txt`.
  Blind gain calibration; "The component of the offset in the signal subspace is generally
  unidentifiable".
- **Lu, Varaiya, Horowitz & Palen**, *Faulty loop data analysis/correction and loop fault
  detection*, California PATH — `lu_horowitz_loop_fault.pdf/.txt`. Undated manuscript; PDF
  metadata creation date 2008-02-15. Review; flow-ratio test upstream/downstream; on-time tests.
- **US 11,461,692 B2** (CLR Analytics, filed 2018-04-17, pub 2022-10-04) — `US11461692_fpo.txt`.
  Single-loop classification from signatures (KNN); notes re-calibration needed between stations.
- **US 6,999,886 B2** (Inductive Signature Technologies, filed 2003-09-17, pub 2006-02-14) —
  `US6999886_fpo.txt`. Single-loop card synthesises second output to mimic a speed trap.
- **US 6,337,640 B2** (Diamond Consulting Services, filed 1999-03-31, pub 2002-01-08) —
  `US6337640_fpo.txt`. Figure-of-eight axle-counting loop.
- **US 7,764,197 B2** (United Toll Systems, filed 2008-01-28, pub 2010-07-27) —
  `US7764197_fpo.txt`. Multilane loop sampling synchronisation.
- WSDOT 647.1 extra verified facts: ALEDA "is executable on a laptop computer"; "WSDOT's Loop
  maintenance staff can utilize the ALEDA system at loop stations"; before/after comparisons
  around known sensitivity tune-ups.
- Jia et al. (2001) PeMS g-factor PDF has an undecodable font; not used.

## IDF-B Table A numbering (current)

1 Azin & Yang (section 1 here); 2 WSDOT 647.1 (section 6); 3 Minge 2012; 4 Coifman & Kim
2009; 5 Wu & Coifman 2014 (section 7); 6 Lu, Varaiya, Horowitz & Palen; 7 Bychkovskiy 2003
(section 3); 8 Balzano & Nowak 2007; 9 GB 2385138 A (section 4); 10 EP 2790165 A1
(section 5); 11 US 11,461,692 B2; 12 US 6,999,886 B2; 13 US 6,337,640 B2; 14 US 7,764,197 B2.
Lu, Yang & Chang (2014) is mentioned only as cited by entry 1; flagged unread in Section 12.

## Patent searches run (Google Patents xhr, 2026-09-29)

- `("vehicle length") (adjacent OR neighboring OR neighbouring OR upstream) (detector OR sensor) (calibrat*) ("length class" OR "length bin" OR "classification") (downstream)` — 61 results, none on point.
- `("effective vehicle length") (adjacent OR upstream OR neighboring) (detector) (calibrat* OR correct*)` — 49, none on point.
- `("vehicle length") ("loop detector" OR "inductive loop") (sensitivity) (calibrat*) (adjacent OR upstream OR neighbouring OR neighboring)` — 33; GB2385138A and EP2790165A1 read (entries 4, 5).
- `(("vehicle classification" OR "length classification") (detector) ("same vehicles" OR "same traffic") (upstream downstream) (bias OR offset OR error) (correct*))` — 2, neither on point.
- Chinese-language query on vehicle length / adjacent / detector / calibration — noise.

## Added 2026-09-29 (claims-strengthening pass), all verified from raw text

- **US 6,876,949 B2** (Inductive Signature Technologies, filed 2003-03-07, pub 2005-04-05;
  divisional US 6,988,052 B2 pub 2006-01-17, same specification): `US6876949_fpo.txt`,
  `US6988052_fpo.txt`. NEW CLOSEST ART on calibration from the stream. Verified:
  "common vehicular traffic is used as passive probes using vehicle re-identification
  techniques"; coefficients "derived by using linear algebra to solve multiple simultaneous
  equations"; "compare a local population distribution table with a standard population
  distribution table, and to calibrate an output of a vehicle detector based on the result";
  inductive lengths calibrated so "the mean CVIL for each detector's local population
  distribution table was shifted to the arbitrarily chosen standard mean of 19.0 feet";
  a 6 m instead of 4 m loop spacing "can be exposed and quantified" by matching the local
  distribution to the standard. Conceded: a length error shifts the population
  distribution and can be calibrated out; same-vehicle normalisation of several detectors.
  Distinct: per-vehicle signatures / re-identification / standard table; multiplicative
  scaling; no class counts, no pair admission, no chain, no cross-boundary test, no
  class-count correction. IDF-B entry 11.
- **Dailey & Wall, WSDOT WA-RD 633.1 (Jan 2006)**: `wsdot_633_1.pdf/.txt`. Describes the
  Wall & Dailey (TRR 1855, 2003) archived-data correction. Verified: "The reference station
  candidates are limited to pairs of stations that have no on- or off-ramps between the
  mainline sensor locations"; "if vehicle counts are balanced, the data are valid"; find a
  reference station, compare adjacent stations, "the bias in the station is calculated,
  and a correction time series is applied"; the corrected station becomes the next
  reference. Total volumes only. IDF-B entry 3. (Also relevant to patent 1.)
- **Lee & Coifman (2012), J. Transp. Eng. 138(7):871-881**: author draft
  `coifman_Sensitivity.pdf/.txt`. Verified abstract: sensitivity assessed from "the daily
  median on-time"; correction "via a multiplicative correction factor" and an alarm to
  dispatch a technician; transposed to dual-loop spacing; assumes passenger-vehicle
  effective length and free-flow speed. Summarises Chen & May (1987) on-time ratio to the
  station average and Coifman (1999) upstream vs downstream loop of a dual loop. Entry 4.
- Downloaded, read, not used: Coifman `amps` (1999), `classStEval` (2013), `EventVald`
  (2004), `LaneMapping` (2006), `LeeAndCoifman2015a_0` (LIDAR validation of classification
  stations; attendance-based, like Minge).
- Dropped from Table A (irrelevant): US 6,337,640 B2, US 7,764,197 B2.
- Seen in search, not added (total-flow bias, patent-1 territory): UC Davis NCST
  "Networked sensor data error estimation" (GMM systematic error of flow sensors) and
  "Bias estimation of spatiotemporal traffic sensor data" (physics-informed deep learning).
- Lu, Yang & Chang (2014): still unread. A search snippet (not raw text) says it compares
  AEVL between lanes and stations with multiple comparisons with the best, the same family
  as entry 1.

## IDF-B Table A numbering (from the claims pass; supersedes the numbering above)

1 Azin & Yang; 2 WSDOT 647.1; 3 Dailey & Wall WA-RD 633.1; 4 Lee & Coifman 2012; 5 Minge
2012; 6 Coifman & Kim 2009; 7 Wu & Coifman 2014; 8 Lu, Varaiya, Horowitz & Palen;
9 Bychkovskiy 2003; 10 Balzano & Nowak 2007; 11 US 6,876,949 B2; 12 GB 2385138 A;
13 EP 2790165 A1; 14 US 11,461,692 B2; 15 US 6,999,886 B2.

## Deep search 2026-09-30 (for the publication / grant assessment)

Verified from raw text:
- **FHWA WIM Pocket Guide Part 3, FHWA-PL-18-015 (June 2018)** - `fhwa_wim_guide_part3.txt`.
  Auto-calibration routines ("For systems that use an auto-calibration routine, check the WIM
  manufacturer's guidelines"); drift monitoring by "Class 9 average front axle weight and
  front axle weight distribution"; LTPP "vehicle length measurement requirement of +-1.5 feet
  or 3 percent of the vehicle's overall length, whichever is longer". IDF-B entry 16
  (conceded: stream-statistic calibration check at one site, for weight).
- **US 7,684,946 B2** (Mettler-Toledo, 2010) - `US7684946B2.txt`: WIM auto-calibration from
  WIM vs static weights of the same vehicles. Not close; not in Table A.
- **GB 2377027 A** (Golden River, 2002) - `GB2377027A.txt`: roadside station accuracy with an
  instrumented probe vehicle. Attendance-based; not in Table A.
- **US 11,119,209 B2** (Houston Radar) - uses a vehicle length distribution only to reject
  implausible radar events. Not relevant.
- US 2017/0140645 A1 (Univ. Oklahoma, magnetic signatures), US 11,313,950 B2 (Image Sensing
  Systems, ML radar classification), US 11,080,995 B2 - not relevant.
- TMG 2022 Appendix C (QC criteria compendium): only "VTrans relies largely on auto
  calibration" at WIM sites; no neighbour comparison. Not used.
- Google Patents xhr, 12 queries incl. Chinese, saved in `patent/search_2026-09-30.json`
  (`src/patent_search.py`): nothing on class-share comparison between same-vehicle
  detectors, chain solution per boundary, offset from the stream's class shares,
  cross-boundary test or total-preserving reclassification.
- Lu, Yang & Chang 2014: Semantic Scholar confirms CLOSED access; still unread.
- Azin & Yang raw PDF: ROSAP still blocks scripts; Chrome PDF viewer not readable by tools.

Legal (verified): Section 11A text (`ik_11a.txt`, Indian Kanoon); CRI Guidelines 2025
official final (`cri2025.txt`): Ferid Allani (2019), Microsoft v Asst. Controller, Raytheon
v Controller (15 Sept 2023, novel hardware not required), Example 16 (data-engineering
pipeline incl. "dynamic cross-sensor calibration"; needs pipeline, technical rationale and
validation methodology disclosed).
