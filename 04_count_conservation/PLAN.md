# Phase plan

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

---

## Phase 0 — Topic lock and data proof `[x]`

Confirm the topic is buildable before writing a line of the specification.

- [x] Topic 3 selected; Topics 1, 2, 4 eliminated on data availability (see `README.md`)
- [x] WebTRIS API verified reachable, no key, 11,234 active sites, 15-minute volumes
- [x] DfT bulk CSVs downloaded (`data/raw/aadf.zip`, `bydir.zip`)
- [x] MnDOT confirmed unreachable; PeMS parked as account-gated fallback
- [x] MIDAS naming convention decoded — topology is derivable from site names alone
- [x] `src/webtris.py` cached API client working

**Gate:** real 15-minute data with real gaps, obtainable free. Passed.

---

## Phase 1 — Corridor and node construction `[x]`

Turn a list of sites into a graph where the conservation identity can be written down.

- [x] Order mainline sites along the corridor by marker chainage, per direction
- [x] Validate that ordering geometrically — consecutive mainline sites are 420 m apart
      (median, M25 clockwise; p90 653 m), matching MIDAS's nominal 500 m spacing, so the
      marker number really is chainage
- [x] Emit a node list: each node = one mainline segment boundary with its incident
      upstream mainline, downstream mainline and candidate slips
- [x] Handle slip/mainline marker co-location (4055A and 4055J are the same place) with
      inclusive bounds, flagging slips claimed by two nodes as `ambiguous`

Result, M25 clockwise: 496 sites → **378 usable nodes**, 143 carrying slips, 235
plain-continuity. M25 anti-clockwise: 379 nodes. M1 northbound: 634 nodes.

**Deliverable:** `src/corridor.py`, `results/nodes_<road>_<carriageway>.json`. Done.

**Gate:** at least ~20 well-formed nodes on one corridor. Passed by a wide margin.

---

## Phase 2 — Gap characterisation and the conservation identity `[x]`

Establish that the problem is real and the constraint actually holds in the data.

- [x] Pull one full month of 15-minute data for the corridor
- [x] **Resolve slip topology from the data**: for each slip, choose its node assignment
      and its sign (entry `+` / exit `−`) by picking the combination that minimises the
      balance residual. Deriving topology from the balance rather than from an assumed
      naming convention is itself a defensible technical step, and it removes a
      hand-waved assumption an examiner could attack
- [x] Measure the true missingness: rate, run-length distribution, whether gaps are
      per-site or network-wide, whether they cluster by time of day
- [x] Measure the conservation residual on **complete** intervals:
      `upstream + entries − exits − downstream`. This is the empirical foundation of the
      whole invention — quantify how tight the identity is and what the natural noise
      floor is (detector miscount, lane closures, vehicles between detectors)
- [x] Decide the constraint form from that measurement: exact equality, or equality
      within a measured tolerance band

**Deliverable:** `results/gaps.json`, `results/conservation_residuals.json`, short
write-up in `patent/notes.md`.

Measured: **0.69% of flow** at plain-continuity nodes (the detector noise floor) and
**1.06%** at nodes carrying slips. Every one of the 2,972 intervals has at least one
absent record, so discarding incomplete intervals would discard the whole dataset; only
6 intervals lose every detector, so spatial information is nearly always available.

**Gate:** conservation residual is small and well-characterised. Passed.

---

## Phase 3 — Baselines `[x]`

Build the prior art, honestly and competently. A weak baseline makes the evidence
worthless and is easy for an examiner or evaluator to attack.

- [x] Time-of-day/day-type historical mean
- [x] Linear temporal interpolation
- [x] KNN across correlated sites, with a learned per-pair scale factor so a slip road
      can lend its shape to a mainline detector — the strongest opponent
- [x] Low-rank matrix completion by soft-thresholded SVD (the standard academic method)
- [x] Evaluation harness masking with runs resampled from the *measured* gap-length
      distribution, not uniform random cells, which would flatter interpolation
- [x] Two mask regimes reported separately, because the measured distribution mixes
      short operational dropouts with detectors that died and stayed dead for weeks

Results, 51 live sites × 2,972 intervals, 18 nodes, 10% of observed cells hidden:

| Method | MAE (operational) | MAE (all gaps) | Conservation residual, median / p90 / worst |
|---|---|---|---|
| historical mean | 47.69 | 40.45 | 5.46% / 8.58% / 9.93% |
| linear interpolation | 105.94 | 229.39 | 9.12% / 37.29% / 70.78% |
| **KNN spatial** | **22.03** | **15.65** | **1.49% / 6.38% / 9.10%** |
| soft-impute | 26.44 | 23.14 | 2.77% / 8.70% / 15.89% |

Behaviour is sane: interpolation wins the 1–4 interval bucket (MAE 32.3 vs 48.0 for the
historical mean) and collapses on long gaps. KNN is the method to beat.

The tail is where the invention's case lies. KNN's *median* conservation residual of
1.49% is already close to the 1.06% physical noise floor — but its p90 is 6.38% and its
worst node 9.10%. It has no mechanism controlling that quantity, so it cannot promise
anything about it. Beating the median alone would be a weak claim; eliminating the tail
is a categorical one.

**Deliverable:** `src/dataset.py`, `src/baselines.py`, `src/evaluate.py`,
`results/baselines_operational.json`, `results/baselines_all_gaps.json`. Done.

---

## Phase 4 — The invention `[x]`

- [x] Formulate imputation as a constrained problem: minimise weighted deviation from a
      prior subject to node conservation
- [x] Solve it by projection — Dykstra's algorithm onto the intersection of the node
      bands and the non-negative orthant. Closed-form steps, no neural network, fully
      explainable, which the 2025 CRI Guidelines' anti-black-box requirement demands
- [x] Handle the underdetermined case (least-norm correction spread across unknowns) and
      the overdetermined case (overlapping nodes solved jointly, not in sequence)
- [x] Record computation time — 8.4 s for the full month on the strongest prior

Two design decisions were **forced by measurement**, not chosen up front, and both are
dependent-claim material:

*Calibration.* The raw relation has mean absolute value 17.45 vehicles on a mean node
flow of 592.5. A per-node constant offset brings that to 16.41; a per-node scale factor
as well brings it to 14.84. So the relation enforced is the calibrated one. Enforcing a
textbook zero pushes known instrument bias into the reconstructed value — the ablation
confirms it, raising out-of-band from 1.17% to 8.54%.

*Tolerance band.* Even calibrated, the relation is good only to ~15 vehicles, the same
size as a good statistical estimator's error. The constraint is imposed as a hard
two-sided inequality with the band derived from the relation's own measured spread. Still
hard — nothing outside the band is admissible — but a physically plausible prior is left
alone.

> **Correction, recorded at Phase 5.** At 18 nodes exact equality was *worse* on accuracy
> (22.09 vs 21.05) and that was written here as the justification for the band. At 199
> nodes it is *better* (13.81 vs 14.44). The band's real justification is the guarantee:
> a zero-width intersection is empty far more often, leaving 4.02% of node-intervals
> unsatisfied against 0.93%. It buys feasibility at a ~4.5% accuracy cost.

Results, operational regime, 10% of observed cells hidden:

| Prior | MAE before → after | Out-of-band before → after |
|---|---|---|
| historical mean | 47.69 → **35.37** (−26%) | 43.70% → 1.21% |
| linear interpolation | 105.94 → **59.75** (−44%) | 55.76% → 1.18% |
| KNN spatial | 22.03 → **21.05** (−4.4%) | 13.47% → 1.17% |
| soft-impute | 26.44 → **23.59** (−11%) | 26.83% → 1.20% |

All-gaps regime is the same story: KNN 15.65 → 15.34, out-of-band 8.87% → 0.89%.

**Unexpected second technical effect.** The residual ~1% out-of-band is not solver
failure. An LP feasibility test showed roughly 90% of those cases are *genuinely
infeasible*: the values that were actually observed around those nodes cannot be
reconciled with conservation no matter what is filled in, by a mean shortfall of 25.6
vehicles. 233 of 2,972 intervals contain such a node. The method flags them instead of
papering over them, which localises a faulty or miscalibrated detector — a data-integrity
diagnostic no per-detector method can produce. The count is identical across all four
priors, exactly as it should be since infeasibility depends only on the observed data.

**Deliverable:** `src/constrained.py`, `src/phase4.py`,
`results/phase4_operational.json`, `results/phase4_all_gaps.json`. Done.

---

## Phase 6b — Downstream technical actions `[x]`

Decision taken: the claim stays on the reconciliation engine. Congestion prediction,
capacity planning and weather analysis are **not** claimed — they are heavily patented,
and "where to build road capacity" risks being read in India as an administrative method,
which `OpenTV` makes an absolute bar. They appear only as evidence that the reconciled
dataset changes the answers a real engineering process gives, which is what the 2025 CRI
Guidelines want the technical effect tied to.

`src/applications.py`, `src/weather.py`. Weather from the Open-Meteo archive API — free,
no key, any lat/long, so it joins to detector coordinates directly.

**1. Saturation ranking (capacity assessment input) — the usable result.**
Reconciliation materially changes which segments are flagged. Mean rank shift 7.1 places,
max 34; 20 of 51 sites move more than 5 places; **5 of the top 20 candidate bottlenecks
change identity**. Same computation, different answer, solely because of the dataset.

**2. Rain sensitivity (weather-responsive control input) — weak.**
The physical effect is recovered sensibly: flow falls 6.5% when it is raining. But the
two datasets barely disagree (0.24 percentage points mean, 3.1 max), and March 2025 was
dry — only 2.2% of intervals were wet. Too small a sample to carry weight.

**3. Forecasting — NEGATIVE RESULT, reported as such.**
Per-detector short-horizon forecasting is *worse* on the reconciled dataset, by 1.03%.
A node-flow variant, motivated in advance on the grounds that a per-detector forecaster
has no channel through which cross-detector consistency could help, is also negative at
−0.31%. Both are recorded. Forecast error is dominated by genuine traffic variability,
which is far larger than the reconciliation corrections, so the dataset difference is
swamped. Two variants were run; a third would be fishing for a favourable metric, so it
was not run.

**Consequence for the claim:** the downstream evidence is capacity-assessment ranking,
not forecasting. The disclosure must say that plainly. Claiming a forecasting benefit
would be contradicted by our own measurements.

---

## Phase 6c — Recovering the topology from the counts `[x]`

Aimed squarely at the weak axis. Every Phase 6 reference takes the network structure as
an **input**: de Souza from a known station layout, Yin et al. from a known incidence
matrix, process data reconciliation from a known flowsheet. `src/discover.py` makes it an
**output**, searching the counts for sparse relations with coefficients in {−1, 0, +1}
that hold across every interval. No site names, no coordinates, no junction database.

Rounding the fitted coefficients to integers is what makes a relation physical rather
than statistical: 0.83 is a correlation, 1 is a statement that vehicles are conserved.

**Structure recovery**, scored against the MIDAS-derived nodes the search never sees.
Two fixes raised it substantially, and it scales the right way:

| Setup | Relations found | Exact recall | Span coverage |
|---|---|---|---|
| 18 nodes, greedy pursuit | 17 | 0.389 | — |
| 18 nodes, subset enumeration | 40 | 0.556 | 0.611 |
| **199 nodes, subset enumeration** | **726** | **0.739** | **0.754** |

*Why enumeration mattered:* greedy pursuit returns one explanation per detector, and for a
mainline detector the best single explanation is almost always the next mainline detector
along, since they correlate at r ≈ 0.99. That systematically hid every relation involving
a slip road. Enumerating subsets finds those too, at trivial cost — the fits are three
columns wide.

*Why more nodes helps:* a bigger network gives each relation more redundancy, so it is
better determined. Recovery improves with scale rather than degrading, which is the
direction that matters for a real deployment.

*Span coverage* is the honest recall measure: the fraction of surveyed relations lying in
the span of the discovered ones. A surveyed relation written in a different basis is still
recovered, and constrains the reconstruction identically. Exact matching undercounts.

*Validity* — the share of discovered relations holding tighter than the 1.06% noise floor
— is 0.337. The remainder hold between the noise floor and the 4% acceptance threshold,
so the threshold is the loose knob here, not the method.

That understates it. The surveyed list is not ground truth — it is one particular
decomposition. A relation spanning several nodes with no slips between them (telescoping
continuity) is an equally valid conservation law and is counted as a false positive.
Discovered relations hold to 0.61% of flow, *below* the 1.06% measured noise floor, so
they are real laws whether or not they appear on the surveyed list.

**The decisive experiment** — reconcile using discovered relations instead of the map.
Discovery runs on the training view only, so no relation is learned from a value later
used for scoring. Run at 18 nodes first, then repeated at 199.

| Constraints used | MAE @ 18 nodes | MAE @ 199 nodes | Out-of-band @ 199 | Runtime @ 199 |
|---|---|---|---|---|
| none (KNN baseline) | 22.03 | 15.79 | 10.70% | — |
| surveyed topology | 21.05 | **14.50** | **0.93%** | 86 s |
| discovered topology | 18.52 | 15.10 | 7.13% | 210 s |
| both | 18.12 | **14.22** | 2.43% | 465 s |

**Correction.** At 18 nodes the discovered relations beat the surveyed ones (18.52 vs
21.05) and that was reported here as a finding. At 199 nodes it reverses (15.10 vs
14.50). It was a small-sample artefact and is withdrawn.

What survives:

1. **The relations can be recovered from the counts alone**, so no external map is needed
   at any stage. 147 of 199 surveyed relations recovered exactly; 75.4% span coverage.
2. **Using both constraint sets gives the lowest error of any configuration tested**
   (14.22, −9.9% against the KNN baseline) — but at 2.43% out-of-band against 0.93% for
   the surveyed set alone. It is a trade-off between accuracy and the guarantee, not a
   free improvement, and must be written that way.

---

## Phase 6d — Cost and operating envelope `[x]`

`src/envelope.py`.

**Computational cost**, like for like, same machine and data. Peak memory is additional
allocation measured with `tracemalloc`, which itself inflates the timings roughly
threefold — the untraced constraint step runs in 8.4 s, reported above.

| Method | seconds (traced) | peak MB |
|---|---|---|
| historical mean | 3.66 | 1.3 |
| linear interpolation | 0.02 | 1.4 |
| KNN spatial | 22.97 | 2.9 |
| soft-impute | 15.16 | 8.7 |
| constraint step | 27.79 | **1.5** |

Honest reading: this is **not** a speed win, and the disclosure should not claim one. It
is a memory win — the constraint step peaks at 1.5 MB against soft-impute's 8.7 MB,
because it works one interval at a time rather than holding a full factorisation.

**Envelope — performance against how much data is missing:**

| Hidden | prior MAE | ours MAE | gain | out-of-band |
|---|---|---|---|---|
| 5% | 21.67 | 19.94 | **7.98%** | 1.78% |
| 10% | 22.03 | 21.05 | 4.45% | 1.17% |
| 20% | 21.70 | 20.96 | 3.41% | 1.14% |
| 40% | 24.67 | 24.62 | **0.20%** | 0.70% |

The accuracy benefit decays with missingness and is gone by 40%: more unknowns per node
means the system is underdetermined and the constraint has less determining power. **The
consistency guarantee does not decay** — out-of-band stays between 0.70% and 1.78%
throughout. So the two effects have different operating envelopes, and the disclosure
must say so rather than quoting the 5% figure alone.

**Envelope — sensitivity to the tolerance band:**

| Band scale | MAE | out-of-band | band (vehicles) |
|---|---|---|---|
| 0.0 (exact equality) | 22.09 | 4.26% | 0 |
| 0.5 | **20.68** | 1.93% | 23.3 |
| 1.0 (measured) | 21.05 | 1.17% | 46.5 |
| 2.0 | 21.30 | 13.25% | 93.1 |

MAE moves only 20.68–22.09 across a fourfold change in band width, so the band is not a
finely tuned constant propping the result up — the obvious attack. Out-of-band at scale
2.0 is definitional rather than a defect: it is scored against the scale-1.0 reference
band, so a method permitted twice that width is outside it by construction.

---

## Phase 5 — Evidence pack `[x]`

- [x] Accuracy: MAE/RMSE reduction vs. each Phase 3 baseline, per gap-length bucket
- [x] Physical consistency: conservation residual of each method's output
- [x] Robustness: 3 mask seeds on the full 367-detector / 199-node corridor
- [x] Robustness: second month (June 2025) and second corridor (M1) — Phase 10
- [x] Figures and tables generated into the IDF from `results/*.json`

Full corridor, operational regime, 10% hidden, 3 seeds:

| Prior | MAE alone | MAE constrained | Out-of-band alone → constrained |
|---|---|---|---|
| historical mean | 66.59 | 30.49 | 56.44% → 1.01% |
| linear interpolation | 92.96 | 34.75 | 58.20% → 1.02% |
| **KNN spatial** | **15.73** | **14.44** (−8.2%) | 10.90% → **0.93%** |
| soft-impute | 37.61 | 24.25 | 46.05% → 0.98% |

Seed spread on the headline figure is 14.38–14.50, so the result is not a lucky mask.

**Correction to the Phase 4 window-scale ablation.** At 18 nodes, exact equality was
*worse* than the band (22.09 vs 21.05). At 199 nodes it is *better* on accuracy
(13.81 vs 14.44) but leaves 4.02% of node-intervals unsatisfied against 0.93%, because
a zero-width intersection is empty far more often. The band's justification is therefore
the guarantee, not accuracy, and the disclosure says so.

**Deliverable:** `results/phase5_robustness_full.json`. Done.

---

## Phase 6 — Prior-art search `[~]` — **GATE FAILED for the broad claim**

- [x] Google Patents search
- [x] Verified the guide's cited nearest art (`US11093463`) — not relevant, claim 1 is
      about choosing multiple-imputation repetition counts to fit a time budget
- [x] Academic search: traffic-count imputation, physics-informed imputation,
      constrained completion, data reconciliation
- [x] Distinction analysis written against the closest references
- [ ] Espacenet and Indian Patent Advanced Search
- [ ] Full text of de Souza (2019) — 403 on ScienceDirect, summary taken from OSTI

**Result: the broad claim is anticipated.** Full analysis in `patent/prior_art.md`.

- de Souza (2019), *Freeway Loop Detector Data Reconciliation Based on Vehicle
  Conservation* — freeway loop detectors, vehicle conservation, convex optimisation with
  plausibility constraints, explicitly handles missing lanes
- Yin et al. (2017), *ℓ1-minimization method for link flow correction* — road link flows,
  **hard** conservation constraint, and analytically identifies which sensors are
  miscounting, which is the diagnostic effect I had thought was ours
- Usama et al. (2022) — PINNs enforcing flow conservation at traffic network junctions
- Process-industry **data reconciliation** (`US5504692`, `US10310497`, `WO2016114736A1`,
  60 years of literature) — weighted least squares under conservation, bias estimation,
  gross error detection, unmeasured variable estimation. Every "design decision forced by
  the data" has a named counterpart in this field

**What survives:** method-agnostic projection of any prior; tolerance band derived from
the relation's own measured residual spread; topology and slip signs inferred from the
balance itself with no external map. Narrow, and (1) and (2) face an obviousness attack.

**Gate:** failed for a broad claim; open for a narrow one. Decision needed before
drafting — see `prior_art.md` §5.

---

## Phase 7 — Invention Disclosure Form (IDF-2) `[~]`

Primary deliverable is the IDF-2, generated by `src/make_idf.py` so that every measured
number traces to `results/*.json` and none is typed by hand.

- [x] Generator written; 17 sections, every measured section wired to `results/*.json`
- [x] Title, technical field, background, objects, summary, industrial applicability
- [x] Detailed description: 9 numbered steps plus a table of design decisions forced by
      measurement, each with the alternative that was implemented and rejected
- [x] Technical Effect section — fault diagnosis, the class-transfer capability gap,
      second-corridor replication, reconstruction accuracy and consistency, certified
      bounds, operating envelope and computational cost
- [x] Novelty/inventive step with a prior-art table written *against* de Souza, Yin and
      the process-industry data-reconciliation estate rather than around them
- [x] Section 10 — results recorded **against** the invention (class-wise reconstruction,
      withdrawn discovery finding, negative forecasting result)
- [x] Draft claim set: principal claim on fault diagnosis, 9 dependent claims, and an
      ordered list of fallback positions
- [x] Business-method language scrub — automated word check over the rendered document
- [x] Section 3(k)/Ferid Allani and Alice step-two position stated explicitly
- [ ] Drawings — seven figures specified in §14, not yet drawn
- [ ] Inventor details, prior disclosure, funding — **you supply these**
- [ ] Espacenet + InPASS search — **you are doing this**

**Reframing decision.** The headline claim moved from reconstruction to fault diagnosis.
Reconstruction under conservation is anticipated (de Souza 2019, Yin 2017) and its
measured gain is a modest −8.2%. Fault detection *with classification and magnitude
estimation* is not anticipated by anything found, is measured at 0.0% false positives
with 91.7% correct attribution from a 162-detector line-up, and includes a fault class
that total-flow methods are provably blind to. Reconstruction is now the second aspect.

**Deliverable:** `patent/IDF-2.docx`.

**Note:** if the institution has its own IDF-2 template, the generated sections map onto
it — send the template and the generator retargets to it. `patent/patent.docx` remains
empty; a full specification is only drafted if the brief actually calls for one.

---

## Phase 8 — Vehicle-class-resolved conservation `[x]` — **NEGATIVE for reconstruction**

Hypothesis: WebTRIS reports four vehicle-length classes per interval and they sum to the
total. A car does not become a lorry, so conservation must hold within each class
independently — four constraints per node instead of one, and most useful exactly where
the method was measured weakest, in the underdetermined high-missingness regime.

It does the opposite. `src/classes.py`, `src/joint.py`, `src/phase8_classes.py`,
`src/phase8_joint.py`.

**Why.** The four class relations are *looser* than the total relation, not tighter.
Measured mean tolerance band per node: shortest class **60.1** vehicles, total **46.5**.
The length classifier misbins vehicles near a bin boundary, and those errors are
anti-correlated between adjacent bins, so they cancel when the four are added. Summing
four loose relations recovers one tight one; the total carries information the four
class relations do not.

Controlled comparison, 51-detector window, all arms starting from the same total prior
split by measured composition:

| Hidden | prior | total constraint | same solved in class space | total + class |
|---|---|---|---|---|
| 5% | 21.67 | 19.94 | 19.94 | 22.32 |
| 10% | 22.03 | 21.05 | 21.05 | 22.79 |
| 20% | 21.70 | 20.96 | 20.96 | 29.59 |
| 40% | 24.67 | 24.62 | 24.62 | **36.43** |

Column 4 is the control: a mathematically equivalent problem solved in the larger space,
reproducing column 3 exactly. So the damage in column 5 is the class constraints, not the
solver. Degradation grows with missingness — the opposite of the prediction.

**Verified along the way:** class counts sum to the total exactly in 98.66% of records
(remainder differ by 1 vehicle, rounding); detector composition varies widely across the
network (car share 0.44–0.83, longest class 0.02–0.32), so the tracer argument was
physically sound even though the result went the other way.

**Decision:** class-resolved conservation is expressly **not** claimed for reconstruction.
It is claimed for fault detection, where Phase 9 shows it detects a fault the total
relation provably cannot.

---

## Phase 9 — Synthetic fault injection `[x]` — **the strongest result in the project**

Turns the previously unverifiable diagnostic claim into a measured one. Faults of known
type, size, detector and duration are injected into real recorded data. `src/faults.py`.

**Two instrument-design failures, both recorded because they shaped the method:**

1. *Per-interval testing is the wrong instrument.* The per-interval band flags **19%** of
   clean intervals in a held-out half-month, because the relation drifts. A fault is
   persistent and one-sided where drift and noise are not, so the statistic became the
   mean residual over a span of consecutive intervals.
2. *The parametric standard error is invalid, and the threshold must be per node.* The
   residual is serially correlated, so mean/(sd/√n) came out at 179 under the null instead
   of ≈1. And node quality varies by two orders of magnitude — over a 2-day span one
   node's mean residual sits inside 1.08 vehicles on a flow of 725 while another wanders
   to 32.2 — so a single pooled threshold is set by the worst node and blinds the rest.
   Both fixed by taking each node's own empirical null from clean spans.

Full corridor, 199 nodes, calibration fitted on one half-month and every fault injected
into the disjoint other half, threshold set at 1% false positives, identification from a
line-up of all 162 multi-node detectors:

| Injected fault | Detected | Correct detector 1st | Fault type named |
|---|---|---|---|
| *no fault (control)* | **1.2%** | - | - |
| under-count 0.5% | 70.0% | 58.8% | 83% |
| under-count 1% | 80.0% | 62.5% | 92% |
| under-count 2% | 90.0% | 73.8% | 97% |
| under-count 5% | 96.2% | 81.2% | 99% |
| constant loss 2 veh/interval | 71.2% | 51.2% | 82% |
| constant loss 8 veh/interval | 87.5% | 77.5% | 97% |
| stuck at a constant | 96.2% | 78.8% | - |

**The fault magnitude is recovered, not just flagged.** Injected -1.000% reads back as -0.985%; injected -8.00 vehicles/interval reads back as -7.980. That is a diagnosis, not an alarm, and no cited reference does it.

**The capability gap.** A length-classifier drift moves counts between classes and leaves
the total *exactly* unchanged. No total-flow balance can detect it at any threshold, ever.
Measured:

| Misbooked share | Detected by class relations | Detected by total relation |
|---|---|---|
| 1% | 46.2% | 2.5% |
| 2% | 61.3% | 2.5% |
| 5% | 86.2% | 0.0% |
| 10% | 91.2% | 3.8% |

The total column sits at the false-positive floor throughout, as predicted analytically.

**Second corridor (M1, 88 nodes), nothing retuned:** control 1.2%; 1% under-count 82.5% detected / 73.8% attributed; stuck 96.2% / 87.5%; 5% misbooked class 95.0% / 81.2%. Replicates.

---

## Phase 10 — Cheap credibility `[x]`

**Per-value certified bounds** (`src/confidence.py`). Each reconstructed value is emitted
with the interval obtained by minimising and maximising that coordinate over the feasible
set — two linear programs. Any value outside it contradicts the observed data under the
calibrated relation, so it is a guarantee about the physics rather than a statistical
interval, and it holds whatever estimator produced the point value.

Full corridor, 7,571 reconstructed values: **98.2%** are bounded by the physics at all,
**96.6%** of the withheld true values fall inside their stated interval, median certified
width **43.2** vehicles per interval on a mean node flow of 706. Width by number of
absent values sharing the node: 1 → 40.5, 2 → 136.9, 3 → 223.4. Coverage below 100% is
expected, not a defect: the band is an upper quantile of the residual, so the relation
itself is violated on a matching share of intervals.

**Replication across month and corridor** (`src/generalise.py`), 3 seeds each, nothing
retuned between runs — same calibration procedure, band quantile, prior, masking, seeds:

| Corridor and month | Detectors | Nodes | Prior MAE | Ours | Gain | Outside band |
|---|---|---|---|---|---|---|
| M25 clockwise, March 2025 | 367 | 199 | 15.73 | 14.36 | −8.73% | 10.90% → **5.79%** |
| M25 clockwise, June 2025 | 373 | 209 | 17.63 | 15.87 | −9.97% | 11.29% → **5.97%** |
| M1 northbound, March 2025 | 186 | 88 | 13.66 | 12.80 | −6.26% | 11.50% → **6.11%** |

June varies the month with the network fixed; M1 varies the network with the month fixed.
The accuracy gain ranges 6.3–10.0% and band violations are roughly halved everywhere, so
neither effect is a property of one stretch of road or one month.

**These are the de-leaked figures.** The earlier table reported 0.65–1.08% outside band;
that was produced with the calibration fitted on the full corridor including the withheld
values, so the band the reconstruction was scored against had been fitted using the very
values being reconstructed. Fixed in `constrained.training_corridor`. The honest effect is
a halving of band violations, not a tenfold reduction.

---

## Phase 11 — chronic bias: the fault present before calibration `[x]`

`src/chronic.py`, `src/chronic_absolute.py`. Full detail in `patent/FINDINGS.md` §15.

Phase 9 detects fault **onset** — it compares a node against its own past. A detector
already miscounting when the calibration was fitted has its bias absorbed into α and β,
produces no residual ever, and is structurally invisible. Since §4 of the disclosure
motivates the invention with *drifted loop sensitivity*, which is chronic, that was a hole
between the problem stated and the problem solved.

It is also where the surviving novelty is. Every FDI method found (parity space, structured
residuals, GLR, power-system bad-data identification) starts from a **known-correct** model
and asks which sensor disagrees. Here the model is fitted from the sensors under suspicion.
Decomposing the *fitted calibration offsets* over the known coefficient matrix — β = C·b,
solved for sparse b by ℓ1 LP — diagnoses the model itself and breaks the circularity.

**Baseline (nothing injected):** non-zero bias for 199 of 367 detectors; median 1.19, p90
7.18, max 43.73 veh/interval; decomposition residual median 0.00.

**Referenced experiment** (against the unfaulted corridor): magnitude recovered to
−30.027 / −15.014 / −8.007 against −30 / −15 / −8, and −0.0560 / −0.0220 against −5% /
−2%; culprit ranked 1st in 80–92% of trials.

**Reference-free experiment** — the one that counts, since a chronic fault denies you a
clean reference by definition. Corridor taken as it arrives, flagged on robust z (median
and MAD, k = 3.5) within the population of recovered biases:

| Injected | Detected | 1st over whole line-up | 1st, standing outliers set aside | Type named | Extra flagged/trial |
|---|---|---|---|---|---|
| loss 8 veh | 88.0% | **0.0%** | 88.0% | 88.0% | 0.56 |
| loss 30 veh | 92.0% | **0.0%** | 92.0% | 92.0% | 0.64 |
| under-count 2% | 84.0% | **0.0%** | 80.0% | 80.0% | 0.48 |
| under-count 5% | 88.0% | **0.0%** | 88.0% | 88.0% | 0.44 |

Nothing injected: **40 of 162** line-up detectors flagged (24.7%) — reported as an upper
bound on the alarm rate, not as false positives, since some may genuinely be miscounting
and no independent calibration record exists to settle it.

**Read the zero column.** Those 40 standing outliers are larger than anything injected and
out-rank it every time. The aspect delivers an alarm, a size, and a correct identification
**within a shortlist** — not an unqualified naming of the culprit. Stated that way in the
IDF rather than softened.

Consequences for the claim set: chronic diagnosis becomes **Claim 1**; the onset method
becomes claim 7 and is marked as the more exposed of the two; claim 1 now ends in applying
a correction and supplying corrected counts downstream, not in `outputting`.

---

## Corrections carried into this plan

- **Test-set leak fixed.** `constrained.reconstruct` calibrated α, β and the band on the
  full corridor including withheld values. Now calibrates on the view only
  (`constrained.training_corridor`). De-leaked M25 March: out-of-band **10.90% → 5.79%**,
  not → 0.93%. The Phase 10 table above is pre-fix and is superseded by the rerun.
- **Novelty claim withdrawn.** Narasimhan & Mah, AIChE J 1987 33(9):1514–1521 discloses
  fault-type discrimination *and* magnitude estimation from mass-balance residuals. The
  IDF now says so and drops that claim rather than arguing round it.

## Phase 12 — the gate was run, and it failed `[x]`

An adversarial review of IDF-2 rated it **2/10, do not file**, on two blockers both since
verified directly:

1. **Uncited art occupies the surviving distinction.** Power-system *network parameter
   error* identification (Liu/Wu/Lun 1992; Zhu/Abur 2006) diagnoses the *fitted model*,
   estimates a bias vector from it, and decomposes that over known structure — the claimed
   architecture, from 1992. We had cited only the bad-*measurement* half of power-system
   state estimation. Plus, in-domain and uncited: Vanajakshi & Rilett (TRR 1870, 2004),
   conservation-of-vehicles loop diagnostics; Cheevarunothai et al. (TRR 1945, 2006), loop
   *sensitivity* drift identified and corrected.
2. **The mechanism was misdescribed.** Verified: `rank(C)=199`, `nullity=168` (§6.3 said
   the null space was the constant-shift direction), `max|C·b−β|=7.1e-15`, non-zeros=199 =
   `rank(C)`. The system is underdetermined so the LP fits β exactly — the per-node-effects
   term is zero, and any non-conservation that is not detector bias is charged to detector
   bias anyway. The "199 of 367" figure is the LP basic-solution bound, not a finding.

IDF-2 has been corrected on both points and now states them against itself.

## Phase 13 — the last live thread, run to the end `[x]`

Two items, both gating. Both now closed.

**1. The false-alarm control the class test never had.** `faults.py` fired the classify
test when *any* of the four class relations exceeded its own 1% threshold, so its
false-alarm rate was not 1% and had never been measured; the control quoted against it
(1.2%) was the `none` case, read through the **total** relation. Measured: the four-class
test fires on **10.00%** of clean spans. `faults.class_joint_thresholds` now takes the null
of the worst-of-four statistic directly from clean spans, per node, bringing the control to
**1.25%** — exactly the total test's own control.

**The effect survives its own control**, full corridor, 199 nodes, 80 trials per case:

| Misbooked share | class, raw | class, at matched 1% | total relation |
|---|---|---|---|
| *0% (control)* | **10.00%** | **1.25%** | 1.25% |
| 1% | 43.75% | 37.50% | 2.50% |
| 2% | 71.25% | 67.50% | 0.00% |
| 5% | 86.25% | 82.50% | 3.75% |
| 10% | 90.00% | 88.75% | 3.75% |
| 40% | 97.50% | 97.50% | 0.00% |

Matching the rate costs 4–6 points below 5% misbooked and nothing above 20%. The joint
calibration draws from a dedicated generator, so all 23 non-classify rows reproduce the
published run bit for bit; the four classify rows move by up to 10 points on re-drawn
injection spans, within one standard error at n = 80. `results/faults_fpcontrol_M25_A.json`.

**2. Prior art on the class-transfer claim — the gate failed.** Full detail in
`prior_art.md` §5b. In the traffic domain it is clear: nothing in the literature or the
vehicle-classification patent estate audits a deployed classifier against a network
conservation relation. In general form it is occupied, by a developed theory rather than a
near-miss — Bagajewicz & Jiang's **equivalency theory of gross errors** and Bagajewicz's
**error detectability** as a designed sensor-network property, extended to **bilinear**
(flow *and* composition) systems in 2000; Narasimhan & Jordache's textbook chapter on
bilinear reconciliation; Crowe's projection methods for component balances. "The total
balance is blind to a bias that redistributes material between components; the component
balances see it" is the traffic instance of a textbook result. Vehicle length classes map
onto species one-to-one, the length classifier onto the composition analyser.

**Consequence:** claims 6 and 9 are now *evidenced* but not *novel in general form*. The
one element found nowhere is the inverted-tightness finding — class relations measurably
looser than the total (60.1 vs 46.5 vehicles) because misbin errors anti-correlate between
adjacent bins and cancel on addition, inverting the assumption the process-industry
treatment rests on. That is narrow, and it is a fix to a problem the approach creates.

## Phase 14 — the §4b searches, run `[x]` — 2026-09-22

The three searches §4b named as gating the one surviving distinction, plus a patent-estate
sweep. **Survivor (3) holds.** One line: *everyone takes the incidence matrix as an input.*
Full detail in `patent/prior_art.md` §7.

- [x] Sparse identification / PINN on traffic sensor networks — discovers the governing
      PDE, assumes the network. Castillo (2015) poses observability *through network
      topology incidence matrices*.
- [x] Constraint discovery in data reconciliation — the dangerous one; does not occupy it.
      Reconciliation is defined on "a given network"; its unknowns are unmeasured flows,
      never the constraint structure.
- [x] Topology inference from detector counts in-domain — counts feed OD estimation and
      assignment on known networks. Map inference recovers topology from GPS and imagery,
      not counts.
- [x] Patent estate, `G08G1/01` × structure-from-counts. Single near hit `US6850840B1`
      read to claim 1 and **ruled out** — takes pre-existing nodes and links as input,
      refines geometry from position data.

**Consequence — claim restructure proposed, not yet applied.** `patent/claim_restructure.md`.
Survivor (3) is currently dependent claim 5, hanging off a claim 1 that Phase 12 rates as
met by Liu/Wu/Lun 1992. The proposal promotes it to an independent claim drawn to the
*combination* — discovery from counts, selection by measured residual tightness, reuse as
the hard constraints on the same dataset — not to the sparse regression, which SINDy makes
old in the abstract. Effect claimed as a **capability, not an accuracy gain**, because
§10.2 records discovered relations as not outperforming the surveyed topology.

**Next action:** review `patent/claim_restructure.md` wording, then wire into
`src/make_idf.py` (edit the generator, never the .docx, so numbers keep tracing to
`results/`). Claim text sits at `make_idf.py:1290` (claim 1), `:1338` (claim 5),
`:1339` (claim 6).

**Deliverable confirmed 2026-09-22:** VIT IDF-B format, with an actual filing as the goal.

## Phase 15 — the survivor re-examined, and rebuilt `[~]` — 2026-09-23

**The old recovery figure was hollow.** `discover.py` on the full M25 recovered 146 of 156
plain mainline pairs and **1 of 43** slip-road relations. "147/199 recovered" was mostly
"consecutive mainline detectors agree". Cause: candidates shortlisted by correlation with
the target; slips correlate weakly with mainline and never enter the pool. The 1.06%
"noise floor" used for precision was also map-derived (Phase 2 slip-node median).

**`src/discover2.py`** — three stages, no map: pair stage; ordering stage (triangle rule
drops shortcut pairs → adjacency chain = site order along the road); junction stage
(slip candidates shortlisted by correlation with the *residual* of the mainline pair,
rounded to ±1, every member must be necessary). Retention floor = median residual of the
adjacent pairs — from the counts. `src/discovery_v2_eval.py`, `src/map_audit.py`.

| | M25 (367 sites) | M1 (186 sites, replication) |
|---|---|---|
| self-derived floor | 0.902% | 1.181% |
| slip relations recovered exactly | **20+1 of 43** (was 1) | 7 of 11 |
| plain pairs recovered | 118 of 156 (was 146) | 55 of 75 |
| judged precision (exact + implied by map, of judgeable) | **71.6%** | **70.5%** |
| relations on sites the survey never covers | 136 | 92 |
| MAE / outside band: surveyed | 14.41 / 5.46% | 13.07 / 7.68% |
| MAE / outside band: recovered only | 14.47 / 6.89% | 12.72 / 8.66% |
| MAE / outside band: both | **14.09** / 5.57% | **12.29** / 7.35% |

All leak-fixed (discovery on training view). `results/discovery_v2_*.json`.

**Map audit** (new capability, candidate independent claim): corrupt one map relation,
flag if a recovered relation sharing ≥half its detectors holds <0.5× its residual.

| | M25 detect / repair | M1 detect / repair |
|---|---|---|
| sign flip | 86.7% / 40.0% | 55.3% / 25.5% |
| slip omitted | 98.3% / 16.7% | 84.2% / 5.3% |
| wrong site (±6 rows) | 78.3% / 36.7% | 76.7% / 28.3% |
| extra member | 76.7% / 70.0% | 83.3% / 71.7% |
| **false flags, clean map** | **11.6% (23/199)** | **12.5% (11/88)** |

False-flag rate too high to claim as is — flagged clean relations may be genuine survey
errors (unchecked) or loose nodes. `results/map_audit_*.json`.

**Superseded:** `discovery_strict.py` (retention test on v1 barely filtered: kept 651/726).

### Phase 15b (2026-09-23) — map-audit rule fixed; fault attribution with no map

**Map-audit false flags diagnosed.** 22 of 23 v1 control flags were a rule bug: for a
two-detector map relation, one shared detector met the "half overlap" test, so the
neighbouring road section was proposed as the "repair". New rule (structural, set before
rerunning corruptions): flag ⇔ map relation's residual > discover2's self-derived limit
(2 × median adjacent-pair residual; M25 1.804%, M1 2.363%); repair must share ≥ 2
detectors. Corruptions now drawn only from relations that pass the control (otherwise an
already failing relation counts as detected for free). v1 results kept as
`map_audit_*_v1rule.json`.

| Corruption | M25 detect / repair | M1 detect / repair |
|---|---|---|
| sign flip | 100 / 45.0 (n 60) | 100 / 44.8 (n 29) |
| drop member | 100 / 55.2 (n 58) | 100 / 79.3 (n 29) |
| wrong site | 60.0 / 8.3 (n 60) | 61.7 / 6.7 (n 60) |
| extra member | 100 / 76.7 (n 60) | 100 / 81.7 (n 60) |
| control: surveyed relations over the limit | 21 / 199 (10.6%) | 16 / 88 (18.2%) |

The control flags are relations that genuinely fail conservation on the counts (up to
27.5%), not matching artefacts. Several come in adjacent pairs sharing one detector
(4470A: 27.5% and 20.6%; 5602A: 18.1% and 9.45%; 4361A; 5738A) — the signature of one
faulty detector, not a map error. Candidate refinement (not built): a detector common to
two adjacent flagged relations is reported as a detector fault; an isolated flag as a map
discrepancy. Do not call the control flags "false flags" in the spec — call them
"surveyed relations inconsistent with the counts".

**Fault attribution on recovered topology** (`faults_recovered_M25_A.json`, discover2 on
train half only, 392 relations, 238 eligible detectors vs 162 with the survey; 40 tested,
3 repeats → 120 trials vs 80). Detection ≥ survey in almost every case; top-1 attribution
higher for large faults (scale 0.8: 89.2 vs 82.5; offset ±30: 89.9/89.2 vs 83.8/85.0;
stuck 87.5 vs 78.8; classify 0.4: 91.7 vs 80.0), lower for small offsets (±2: 27.5/36.7
vs 51.2/53.8; −4: 58.3 vs 71.2). No-fault alarm rate 5.0% vs 1.2% — more relations per
detector at 1% each. Detector sets differ, so not a paired comparison.

### Phase 16 (2026-09-23) — IDF-B built

`patent/IDF-B_Count_Derived_Conservation_Constraints.docx` (20 pages), generator
`src/make_idfb.py` (imports layout helpers from the accepted CausalInterlock
`build_idfb.py`; refuses to build if a results file is missing), figures
`src/make_idfb_figs.py` → `patent/figures/fig01-11.png`. 25 claims, 4 independent:
1 recovery + hard-constrained reconstruction + supply to control; 11 map audit + rewrite
constraint set; 17 system; 21 fault attribution on recovered relations. Old chronic/onset
claims dropped (met by entries 5, 6). New evidence files: `idfb_fig04_example.json`
(slip ranks 17/356 by target corr, 1/355 by residual corr), `v1_slip_recall_M25_A.json`
(v1 method: 1/43 slip junctions).

### Phase 17 (2026-09-24) — strict review acted on

Independent Opus review scored v1 of the IDF-B 4/10 (inventive step 3/10: IPCA network
topology identification, arXiv:1506.00438, missed by our searches). Acted on, in order:
text fixes (RMSE reported, prior art + IPCA/OMP/ARACNE, claims redrafted: 17 claims,
independents 1/12/15 written in full; irreconcilability and fault attribution demoted),
then tests:
- `ablation_ranking.json`: only the ranking changed. Target-ranking 0/43 (M25), 0/13
  (M1) slip junctions; residual-ranking 21/43, 7/13. Element (b) now evidenced.
- `stability_split_half.json`: split-half admission test REJECTED — worse MAE and RMSE
  on both corridors (M1 RMSE 36.12 → 42.05). RMSE regression cause still unknown.
- `baseline_structure.json`: IPCA 0 relations in span / read off on both corridors, even
  on favourable subsets with 2000+ complete intervals (implementation verified 10/10 on
  synthetic). Cause measured: counts near low-rank (1st PC 90.8 %, 10 dims = 99 %);
  conservation directions not the quietest. OMP given our limit: 4/43, 0/13 slip
  junctions, precision 89.6 %/100 %.
Open: RMSE regression cause; sparse/rotated PCA variant (Table 7 #6); correction step of
claim 9 not implemented; inventor details.

### Phase 18 (2026-09-24) — deep-search review acted on (India 5/10 → target 7)

All six items from the deep-search verdict, in order:
1. **Grid art cited.** IDF-B §3 entries 17-20: LV topology by conservation LS/Lasso
   (Soft Computing 2022; Energies 2024; CN111628494B), US 11,205,901, mismapping
   US 9,816,836 / US 11,916,380, Graph WaveNet. Each distinguished.
2. **Grid baseline run** (`src/baseline_grid.py`, `results/baseline_grid.json`): bounded LS,
   every detector tried as parent, 0/1 and signed, pools 12/30. Best: 6/43 slip junctions
   M25, 0/13 M1 (ours 21/43, 7/13).
3. **RMSE regression SOLVED.** `src/rmse_diagnosis.py`: 81 of 50,373 withheld M1 cells,
   each moved >200 veh, carried more than the whole rise. Cause: when Dykstra stalled on a
   satisfiable interval, restart from `_minimum_slack` LP vertex, which has no cost on the
   unknowns and zeroes them. Fix: `constrained._nearest_feasible` (weighted-L1 nearest
   feasible point, LP); `constrained.FALLBACK = "nearest"`. Now RMSE falls under every
   constraint set on both corridors: M25 recovered 31.30 vs prior 32.00 (was 33.65), M1
   26.39 vs 29.09 (was 36.12); MAE improves too (M1 recovered 11.88, was 12.72). Old
   results kept as `*_vertexfallback.json`. New dependent claim 9.
4. **Detector correction implemented and measured** (`src/correction.py`,
   `results/correction_{M25,M1}_A.json`): detect → attribute top-1 (whoever it is) →
   correct (model inversion; substitution from relations where untyped, e.g. stuck).
   End-to-end, wrong corrections charged: net error removed 54-83% M25, 68-92% M1.
   Now independent Claim 12. Not measured: carrying correction forward past the span.
5. **Map-audit fixed-threshold baseline** (`src/map_audit_baseline.py`): no fixed
   tolerance matches the self-derived limit on both corridors, but a fixed 2% is nearly as
   good. Map audit demoted to dependent Claims 11, 16.
6. **Sparse baselines** (`src/baseline_sparse.py`): varimax-rotated IPCA 4/43 M25 but
   **5/13 on M1** (ours 7/13) — strongest baseline, stated plainly; relaxed Lasso 0/0.
Also: June 2025 M25 replication of recovery + reconstruction (`discovery_v2_june_M25_A.json`).

Claims now 18: indep 1 (reconstruction), 12 (detector correction), 15 (system).
IDF-B rebuilt (26 pp), fig11 redrawn, fig12 added.

### Phase 19 (2026-09-24) — real faults on unmodified counts; claim-directed search

`src/real_faults.py`: relations recovered on the first half of March (no map), second half
scanned in 2-day spans; report = every relation of the named detector deviates (>=2).
Reports: M25 14 (10 detectors), M1 16 (10); first-half scan 0/0 (in-sample, optimistic).
`src/real_faults_followup.py`, one admission rule for both groups (>=90% present in
reference half): **5/18 named detectors dead (a month >=95% absent) in Apr-Jun vs 7/80
controls, Fisher one-sided p = 0.041**. Bracketing weak (1/13 confirmed; span median
dilutes short faults). Bin-sum integrity weak (3/14, 2/16). June sign persistence 7/9
(p 0.09). WebTRIS Status useless (dead site still "Active"). Worked examples
(`real_fault_examples.json`): M1/4669A ratio to 4680A 0.97-0.99 → 0.92/0.88/0.88/0.85
(20-23 Mar) → silent from 25 Mar, 100% absent Apr-Jun; M25/5814A 1.2-2.5% low on 24/26/27
Mar while partners agree <0.5%, absent 0.5/5.0/11.3% Apr/May/Jun. M25/4963K report is
probably a road change (diversion), stated as such. IDF-B §8.6a + Table 6b.

Claim-directed search: new close art, cited as IDF-B entries 21-22:
- Yang, Yang & Fan (2019) TR-B 122:20-39 — per-sensor bias by GMM from nodal balance,
  corrects counts; network GIVEN. Anticipates Claim 12's correction concept on a known map.
- US 9,053,519 (TaKaDu, prio 2012) — picks +/- signs of water meters from data; zone
  membership from GIS. Concedes "signs from data".
- Lu/Varaiya/Horowitz/Palen PATH review (folded into 21); EP1659550A2 (node-edge model
  stored, not derived) — not closer. WebFetch fabricated quotes again: verify from raw text.

### Phase 20 (2026-09-24) — Yang-Yang-Fan baseline; real-fault study over four months

`src/yf_compare.py`: entry 21 (Yang, Yang & Fan 2019, static GMM, surveyed map, theta
bounded 0.5-1.5, undetermined sensors barred from naming - both in its favour) vs ours on
surveyed map vs ours on recovered relations; identical injected faults, 40 detectors,
3 spans each. Named correctly: entry 21 2-36 %, ours (map) 83-96 %, ours (no map)
89-98 %. Entry 21 net error removed negative for offsets/stuck (multiplicative model) and
~0-8 % for +/-5 % on M25. `yf_sanity.py`: over two weeks entry 21 recovers a 10 % fault
to median 0.012 in ratio - implementation sound; it needs long windows. Coverage similar
(249/111 determined vs 238/109 in >=2 recovered relations). First unbounded attempt
collapsed theta to ~0.06 - fixed before scoring.

`src/fetch_months.py` (Apr-Jun manifests, 6-thread prefetch), `src/real_faults_months.py`:
March-June x M25/M1, same rule each month; outcome = dead (month >=95 % absent) in next 3
months; admission >=90 % present in reference half, both groups; 40 controls per run.
**13/40 reported vs 18/320 controls, Fisher p = 2.85e-6; per detector 12/37 vs 12/238,
p = 5.3e-6.** Chance scan: 1 report over all 8 runs. IDF-B §8.6 Table 6c, §8.6a Table 6b.

### Phase 21 (2026-09-25) — second external review (items 18-27) acted on

Experiments (all on the claimed configuration, relations recovered, no map):
- `recurrence.py`: March relations re-found in Apr/May/Jun. Recur in all 3: exact 82 %
  (M25) / 77 % (M1); outside-map 50 % / 20 %; unmapped-site 48 % / 38 %. Recurrence
  separates physical from chance relations -> new Claim 9 (replaces unmeasured archive claim).
- `harm_test.py`: removing outside-map relations improves touched detectors slightly
  (M25 RMSE 23.6->20.6). NOT in IDF-B (user: omit slightly-worse results; no claim rests on it).
- `recurrence_filter.py` (June vs May): M25 better (MAE 15.59->15.45, RMSE 30.68->29.72),
  M1 neutral/slightly worse. NOT in IDF-B; Claim 9 claims no accuracy gain.
- `confidence.py ... recovered`: certified intervals on recovered relations: bounded 99.8 /
  99.3 %, coverage 96.5 / 95.2 % (surveyed 96.7 / 94.9). In IDF-B Table 6d (Claim 10).
- `irreconcilable_test.py`: clean flag rate 48 %, faulted 56-83 % -> weak. NOT in IDF-B;
  Claim 11 described as solver behaviour only, not a fault indicator.
- Map audit vs fixed threshold paragraph removed (dependent use only).
Claims restructured to 22: independents 1 (restore record), 13 (correct miscounting
instrument; "only the retained relations, no map"), 18 (system; ends in restored archive).
Fallbacks: 6, 7 (recovery constants), 16 (every-relation rule), 17 (span/quantile).
Traffic-control computer -> dependent 21. Certified/irreconcilable moved to 10/11.
Section 2: instrument-level technical problem paragraph. Divisional recommendation for
Claims 13-17. CRI 2025 Guidelines: final notified July 2025 (PIB); reviewer's "29 Apr 2026"
not confirmed; guideline PDF not retrievable (IP India serves HTML).

### Next (resume here)
0. User review of the IDF-B claims. Open: inventor details (TBD in §12).
1. (done 15b) 2. (done 15b)
3. 28 true pairs lost to the ordering stage — check whether the survey skips a site.
4. Claim architecture for approval (proposal): Ind. 1 recovery + hard-constrained
   validation (discover2 stages recited); Ind. 2 map audit; Ind. 3 system; old chronic
   and onset claims → fallbacks/dependents. Downstream actions: substitute reconstructed
   values into control feed, maintenance instruction for flagged detector, rewrite
   constraint set.
5. Build IDF-B in the format of
   `C:di\patent_InfoSec\IDF-B_CausalInterlock\` (reuse `build_idfb.py` helpers +
   `make_figs.py` style: 12 sections, reference numerals, claim-tree figure). Deliverable
   `patent/IDF-B_*.docx`, generator `src/make_idfb.py`, numbers from `results/`.

---

## Still outstanding

1. ~~CPC `G05B23/02`, `G01D18/00`, `G01D3/08`~~ — run; the FDI art is fatal to the onset
   claim and the parameter-error art is fatal to the chronic claim.
2. ~~**Blind / self-calibration of sensor networks**~~ — searched. Balzano & Nowak (IPSN
   2007) and the blind-drift-calibration line recover per-sensor gains and offsets from
   redundancy with no reference sensor. No patent found, but academic art counts in full.
   Moot in any case, given (1).
3. ~~Class-transfer false-alarm control~~ — done, Phase 13 above. The result is good and
   the claim is dead anyway on §5b.
3. End-to-end onset pipeline: classify whichever detector attribution ranked first, not the
   injected one. Corridor-wide false-alarm rate per span.
4. Replicate Phase 11 on M1.
5. Drawings (nine figures specified in IDF §14).
6. Espacenet + InPASS — user is doing these.

---

## What you need to do

Nothing is blocked right now — Phase 1 proceeds on defaults. But four decisions will
shape the output, and the earlier they land the less rework there is.

1. **Assignment specifics.** Deadline, mark weighting, required format (is it a full
   specification, a provisional, or a report *about* a patent?), page or word limit, and
   whether a prototype/evidence section is actually credited. This changes how much of
   Phases 3–5 is worth building.
2. **Corridor choice.** Default is the M25 — 992 sites, dense slip coverage, ring road so
   the topology closes on itself. Say if you want a different road or a specific junction
   range.
3. **Do you want an India-facing worked example too?** The method is
   jurisdiction-neutral, but an Indian dataset in the examples reads better to an Indian
   examiner. Bengaluru OpenCity traffic volumes are the candidate; quality is much lower
   than WebTRIS, so this would be a secondary illustration, not the evidence base.
4. **Confirm the `.docx` is the final deliverable** and whether there is a prescribed
   template or form (e.g. Form 2 complete/provisional specification format) to follow.

Things only you can supply: the assignment brief itself, if there is one. Drop it into
this folder and I will draft to it.
