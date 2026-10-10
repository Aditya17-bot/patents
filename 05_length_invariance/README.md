# Patent 3 — length-invariance recalibration of roadside vehicle detectors

## The idea

A vehicle's length does not change between two detectors a few hundred metres apart.
Where no slip road joins or leaves the carriageway between two consecutive detectors,
both see the same vehicles, so both must report the same share of vehicles in each
length class. A persistent difference can only be measurement error at one of them.

Each detector belongs to two adjacent pairs (upstream and downstream), so solving along
a chain of detectors separates the one faulty detector from its agreeing neighbours and
sizes its error. The output is a corrected length-class count record and a sensitivity
correction for the detector unit.

Inputs: only the 15-minute length-bin counts already archived nationally. No per-vehicle
event data. No external reference length distribution — the reference is the same
traffic stream measured at the next detector.

## Why this is a real problem — feasibility probe

`src/probe.py` -> `results/probe.json` (rebuilt 2026-09-29; the 2026-09-28 scratch probe
pooled both roads and is superseded). WebTRIS carriageway A, March 2025, consecutive
mainline pairs with no slip road between them, intervals where both sites reported and
average speed > 50 mph, no volume gate:

| Measure | M25 | M1 |
|---|---|---|
| Pairs | 112 | 256 |
| Up/down total-volume ratio, median | 1.0010 | 1.0008 |
| \|gap\| in share below 520 cm, median | 5.0 pts | 5.8 pts |
| same, 90th percentile | 18.2 pts | 20.1 pts |
| same, maximum | 38.9 pts (volume ratio 0.73: lost lane, not calibration) | 40.8 pts |
| Relative gap in 1160+ cm share, median | 2.9 % | 3.7 % |
| Correlation of gap with speed ratio | -0.07 | -0.08 |
| Correlation of per-pair gap, March vs Apr / May / Jun (balanced pairs) | 0.992 / 0.991 / 0.987 | 0.973 / 0.902 / 0.748 |

The gaps are persistent per detector, not noise; the M1 decay is explained by dated
changes at single detectors (E3).

## Nearest art found in triage (to be verified from raw text in Phase 1)

- **Cheevarunothai, Wang & Nihan (2006)**, TRR 1945; WSDOT report 647.1 — identify and
  correct dual-loop sensitivity problems. Needs per-vehicle **event data** and a fixed
  **external** ground-truth short-vehicle length distribution (Wang & Nihan 2004); one
  station at a time. Checked in the raw WSDOT PDF text.
- **Coifman group** (Wu & Coifman 2014; Coifman & Kim 2009) — length-based classification
  from single and dual loops, event data.
- **Jia et al. (2001), PeMS g-factor** — effective vehicle length for single-loop speed.
- Sensor-network **rendezvous / blind calibration** — calibrate sensors that observe the
  same quantity against each other. The obviousness risk: examiner combines this with
  Cheevarunothai.
- Patent 1 (`C:\adi\patents\04_count_conservation`) — total-count conservation. Not prior art until published;
  must not be claimed over.

## Data

WebTRIS only, open, no key. Reuses patent 2's cache (M25/M1, March–June 2025).
