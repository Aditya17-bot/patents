# Findings to date

Everything measured, with the numbers that contradict us kept in. Written 2026-08-03,
updated 2026-08-04 with Phases 8–10 and a reframed headline claim. Every figure here
traces to a file in `results/`; nothing is estimated or recalled.

---

## 1. What the invention is

Two aspects sharing one machine. The **common core** is a calibrated conservation
relation per network node, learned from the data:

1. Group detectors into **nodes** — an upstream mainline detector, a downstream mainline
   detector, and the slip-road detectors between them.
2. **Calibrate** each node's relation from intervals where every detector reported: a
   per-node scale factor and offset, because detectors disagree systematically. Slip-road
   directions come from the same fit, so no external map is needed.
3. Derive a **tolerance band** per node from the measured spread of that relation.

**First aspect — diagnose a miscounting detector** (the headline claim, see §12). Track
each node's calibrated residual over a *span* of intervals, not per interval; threshold
against that node's own empirical null; identify the culprit by fitting one bias against
the known coefficient pattern across every node it belongs to; classify the fault type by
how the bias tracks flow; report its magnitude as a number.

**Second aspect — reconstruct missing records** (see §7). Take any per-detector estimate
as a **prior** and project it onto the set of values satisfying every node relation within
its band, and non-negative. Where no such values exist, **flag** the node-interval rather
than forcing a number. Emit each value with a certified interval (§14).

Solved by Dykstra's algorithm and linear programming — closed-form steps, no neural
network, explainable, which the 2025 CRI Guidelines effectively require.

---

## 2. Data

All open, free, no registration, no payment. Verified reachable from this machine.

| Source | What | Use |
|---|---|---|
| **WebTRIS** (National Highways) | REST API, no key. 20,076 sites / 11,234 active. 15-minute volumes, vehicle-length classes, speed bins | primary evidence base |
| **DfT road traffic statistics** | Bulk CSV, Open Government Licence v3.0, whole GB network, 2000–2025 | held in reserve |
| **Open-Meteo archive** | Free, no key, any lat/long, hourly precipitation | rain analysis |

Fetched: full M25 clockwise carriageway, 494 sites, March 2025 and June 2025.

**Indian data was checked and rejected.** OpenCity's Bengaluru dataset is PDFs of signal
timings — no counts, no licence. Bengaluru Traffic Police publish violations and crashes.
data.gov.in transport holds registrations and accident aggregates. Nothing gives
directional link-level counts with topology.

Detection hardware *does* exist in India — BATCS (Bengaluru, ~169 junctions), Pune ITMS
(503 junctions), Ahmedabad (400 signals), Kanpur (1,000+ sensors), using loops, cameras
or radar. None of it is published as open data. The method needs only counts plus
topology, both of which those systems hold internally.

MnDOT's feed was tested and is unreachable. PeMS is reachable but account-gated.

---

## 3. The problem is real — measured, not assumed

M25 clockwise, March 2025, 74 sites × 2,972 intervals (`results/phase2.json`):

- **39.5%** of all records missing; **12.3%** excluding 23 detectors dead the whole month
- median detector misses only **0.91%** — most are fine, a few are catastrophic
- 232 gap runs: median 2 intervals, p90 16, max 2,666
- **every one of 2,972 intervals had at least one live detector missing** → discarding
  incomplete intervals discards the entire month
- **only 6 intervals lost all live detectors at once** → gaps hit sites independently, so
  spatial information is available to exploit

The last two facts are load-bearing and could have gone the other way. They were checked
before anything was built.

## 4. The physical law holds

Slip signs were **inferred from the balance**, never assumed from the MIDAS letter
convention.

| Node type | Median absolute residual |
|---|---|
| plain continuity (`upstream = downstream`) | **0.69% of flow** |
| with slip roads (full identity) | **1.06% of flow** |

The first is the detector noise floor, obtained free.

Absolute terms: the raw relation is off by 17.45 vehicles on a mean node flow of 592.5. A
per-node constant offset brings that to 16.41; adding a per-node scale factor brings it to
**14.84**. That is why the relation is calibrated rather than enforced at textbook zero.

---

## 5. Network construction

MIDAS site names encode the topology and were parsed, not hardcoded. The chainage
assumption was **verified geometrically**: consecutive mainline detectors are 420 m apart
(median, p90 653 m), matching MIDAS's nominal 500 m spacing.

M25 clockwise: 496 sites → 378 usable nodes; 367 live sites → **199 nodes** with a
fittable conservation relation. M25 anti-clockwise 379 nodes, M1 northbound 634.

Complication found in the data: slip markers share chainage numbers with mainline markers
(4055A and 4055J are the same place), so 91 of 115 slips are claimed by two nodes. Flagged
ambiguous and resolved from the balance rather than guessed.

---

## 6. Baselines

Four known methods, implemented properly and given every advantage. A weak baseline makes
the evidence worthless.

- historical mean by time-of-day and day type
- linear temporal interpolation
- **KNN spatial** with a learned per-pair scale factor — the strongest opponent
- soft-impute matrix completion by thresholded SVD

Masking uses the **measured gap-length distribution**, not uniform random cells — uniform
masking would leave a live neighbour either side of nearly every hole and flatter
interpolation enormously. Two regimes are reported separately because the measured
distribution mixes short operational dropouts with detectors dead for weeks.

---

## 7. Main result — full corridor, 199 nodes, 10% of observed cells hidden

`results/phase4_operational.json`, `results/discovery_full.json`

**All figures below are the de-leaked ones**, 3 seeds, mean [min–max]. The calibration and
band are fitted on the visible data only (`constrained.training_corridor`); consistency is
scored against the relation fitted on everything, which is the right reference for asking
whether a value is physically plausible. The pre-fix figures — out-of-band ~0.9% — were
produced with the band fitted using the withheld values themselves and are withdrawn.

| Prior | MAE before → after | Out-of-band before → after |
|---|---|---|
| historical mean | 66.59 → 30.42 (−54%) | 56.44% → 21.43% |
| linear interpolation | 92.96 → 34.88 (−62%) | 58.20% → 21.96% |
| KNN spatial | 15.73 → **14.36** (−8.7%) | 10.90% → **5.79%** |
| soft-impute | 37.61 → 24.41 (−35%) | 46.05% → 17.99% |

Each prior is paired against its own constrained version, so the difference is
attributable to the constraint alone.

Two things changed materially when the leak was removed. The accuracy gains survive
essentially unchanged. The consistency guarantee does not: out-of-band falls by roughly
half rather than to under 1%, and for the weak priors it stays above 17%. **"No competing
method controls the out-of-band quantity at all" is still true; "the constraint drives it
to ~1%" is not, and is withdrawn.**

### Ablations — full corridor, 3 seeds (`results/phase5_robustness_full.json`)

| Variant | MAE | Out-of-band |
|---|---|---|
| calibrated relation, measured band (as claimed) | 14.36 [14.26–14.41] | 5.79% [5.46–6.11] |
| exact equality, no band | **13.83** [13.75–13.95] | **4.02%** [3.96–4.10] |
| textbook zero, no calibration | 14.67 [14.24–14.90] | 6.58% [6.45–6.65] |
| offset calibration only | 14.38 [14.23–14.56] | 6.56% [6.36–6.73] |
| uniform instead of flow weighting | 14.35 [14.26–14.41] | 5.78% [5.44–6.10] |

**Calibration is confirmed.** Dropping it costs accuracy (14.67 vs 14.36) and raises band
violations (6.58% vs 5.79%). Scale-and-offset beats offset-only on both. This survives the
leak fix intact and is the one design decision the ablations do support.

**The band is not confirmed on either metric, and the previous justification for it is
withdrawn.** Exact equality is better on MAE (13.83 vs 14.36) *and* on band violations
(4.02% vs 5.79%), with non-overlapping seed ranges. The earlier text claimed the reverse
on feasibility; that comparison was made under the leak, where the constraining relation
and the scoring relation were the same object and the band's slack therefore cost nothing.
With them properly separated, slack admissible under the fitted relation can fall outside
the reference, while exact equality pins the solution to the centre and lands near the
reference centre.

What the band is still claimed for is the two things an equality constraint cannot give:
a feasible set **with interior**, without which the per-value certified intervals of §14
have zero width and certify nothing; and a criterion for declaring an interval
irreconcilable instead of forcing a solution through a relation the observations have
already broken. Whether that trade is worth making **has not been measured** — the obvious
experiment is to run §14's certified bounds under exact equality and confirm they collapse.

**Flow-proportional weighting is dropped** — indistinguishable from uniform (14.36 vs
14.35). It does not appear in the claims.

---

## 8. Second technical effect: irreconcilable data

> **Superseded by the leak fix — not yet rerun.** The figures in this section were
> computed over the ~0.93% out-of-band population produced by the leaked evaluation. The
> de-leaked population is 5.79%, six times larger, so the 90% infeasibility share below
> does **not** transfer to it and must not be quoted. Rerunning the LP feasibility test
> against the corrected population is outstanding. Retained here so the earlier number is
> not silently deleted.

The residual ~1% out-of-band was not solver failure. An LP feasibility test showed **~90%
of those cases are genuinely infeasible** — the values that were *observed* around those
nodes cannot satisfy conservation whatever is filled in, by a mean shortfall of 25.6
vehicles. 233 of 2,972 intervals contain one.

The method flags them rather than papering over them, localising a faulty or
miscalibrated detector.

Internal check: the flagged count is **identical across all four priors**, as it must be,
since infeasibility depends only on observed data.

---

## 9. Recovering the topology from the counts alone

Every prior-art reference takes network structure as an **input**. `src/discover.py` makes
it an **output**: sparse relations with coefficients in {−1, 0, +1} holding across every
interval, found with no site names, no coordinates, no map. Rounding to integers is what
makes a relation physical rather than statistical — 0.83 is a correlation, 1 is a
statement that vehicles are conserved.

| Setup | Found | Exact recall | Span coverage |
|---|---|---|---|
| 18 nodes, greedy pursuit | 17 | 0.389 | — |
| 18 nodes, subset enumeration | 40 | 0.556 | 0.611 |
| **199 nodes, subset enumeration** | **726** | **0.739** | **0.754** |

Greedy pursuit hid every slip-road relation, because for a mainline detector the best
single explanation is the next mainline detector along (r ≈ 0.99). Subset enumeration
finds them. Recovery **improves with network size** — more redundancy per relation.

### Reconciliation using discovered relations — full corridor

Discovery runs on the training view only, so nothing is learned from values later scored.

> **Out-of-band column superseded by the leak fix — not yet rerun.** These runs predate
> `constrained.training_corridor`, so their out-of-band figures are inflated in the
> method's favour exactly as the 0.93% in §7 was. The MAE column is unaffected in ordering
> and the accuracy conclusions below stand; the feasibility comparison between constraint
> sets does not, and is outstanding.

| Constraints | MAE | Out-of-band | Runtime |
|---|---|---|---|
| none (KNN) | 15.79 | 10.70% | — |
| surveyed (199) | 14.50 | **0.93%** | 85.8 s |
| discovered (692) | 15.10 | 7.13% | 209.7 s |
| **both (891)** | **14.22** | 2.43% | 465.0 s |

**Correction to an earlier claim.** On the 51-site window, discovered relations beat
surveyed ones on accuracy (18.52 vs 21.05) and I reported that as a finding. **It does not
hold at scale** — at 199 nodes the surveyed topology wins (14.50 vs 15.10). It was a
small-sample artefact. What survives is that combining both is best on accuracy (14.22,
−9.9% against the baseline), at the cost of feasibility (2.43% vs 0.93%).

So the honest position is a **trade-off**, not a free win: best accuracy from both sets,
best guarantee from the surveyed set alone.

---

## 10. Cost and operating envelope

`results/cost.json`, `results/envelope.json`. Peak memory measured with `tracemalloc`,
which itself inflates timings ~3× — the untraced constraint step runs in 8.4 s.

| Method | seconds (traced) | peak MB |
|---|---|---|
| historical mean | 3.66 | 1.3 |
| linear interpolation | 0.02 | 1.4 |
| KNN spatial | 22.97 | 2.9 |
| soft-impute | 15.16 | 8.7 |
| constraint step | 27.79 | **1.5** |

**Not a speed win — do not claim one.** It is a memory win: 1.5 MB against soft-impute's
8.7 MB, because it works one interval at a time rather than holding a factorisation.

### Against missingness

| Hidden | prior MAE | ours MAE | gain | out-of-band |
|---|---|---|---|---|
| 5% | 21.67 | 19.94 | **7.98%** | 1.78% |
| 10% | 22.03 | 21.05 | 4.45% | 1.17% |
| 20% | 21.70 | 20.96 | 3.41% | 1.14% |
| 40% | 24.67 | 24.62 | **0.20%** | 0.70% |

The accuracy benefit **decays to nothing by 40% missing** — more unknowns per node means
the system is underdetermined. The **consistency guarantee does not decay**. The two
effects have different operating envelopes and the disclosure must say so.

### Against band width

| Band scale | MAE | out-of-band |
|---|---|---|
| 0.0 (exact) | 22.09 | 4.26% |
| 0.5 | **20.68** | 1.93% |
| 1.0 (measured) | 21.05 | 1.17% |
| 2.0 | 21.30 | 13.25% |

MAE moves only 20.68–22.09 across a fourfold change in band width, so the band is not a
finely tuned constant propping up the result. Out-of-band at scale 2.0 is definitional —
scored against the scale-1.0 reference band.

---

## 11. Downstream technical actions

Congestion prediction, capacity planning and weather analysis are **not claimed** — they
are heavily patented, and "where to build road capacity" risks being read in India as an
administrative method, which `OpenTV` makes an absolute bar. They appear only as evidence
that the reconciled dataset changes the answers a real engineering process gives.

**Saturation ranking — works.** Mean rank shift 7.1 places, max 34; 20 of 51 sites move
more than 5 places; **5 of the top 20 candidate bottlenecks change identity.** Same
computation, different answer, solely because of the dataset.

**Rain sensitivity — weak.** The physical effect recovers sensibly (flow falls 6.5% when
raining), but the two datasets differ by only 0.24 percentage points on average, and March
2025 was dry — 2.2% of intervals wet. Too small a sample.

**Forecasting — NEGATIVE.** Per-detector short-horizon forecasting is *worse* on the
reconciled dataset (−1.03%). A node-flow variant, motivated in advance because a
per-detector forecaster has no channel through which cross-detector consistency could
help, is also negative (−0.31%). Forecast error is dominated by genuine traffic
variability, far larger than the reconciliation corrections. Two variants were run; a
third would be fishing.

**The disclosure must not claim a forecasting benefit.** Our own measurements contradict
it.

---

## 12. Fault diagnosis - detect, localise, classify, quantify

`src/faults.py`. The strongest result in the project, and the reason the headline claim
moved here from reconstruction.

Faults of known type, size, detector and duration injected into real recorded data.
Calibration fitted on one half-month, every fault injected into the disjoint other half,
so the calibration cannot absorb the fault. Threshold set per node at 1% false positives
from that node's own clean spans. Identification from a line-up of all 162 detectors
belonging to more than one node.

Two instrument-design failures on the way, both kept because they shaped the method:

1. **Per-interval testing is the wrong instrument.** The per-interval band flags **19% of
   clean intervals** in a held-out half-month, because the relation drifts slowly. A
   fault is persistent and one-sided where drift is not, so the statistic became the mean
   residual over a span.
2. **The parametric standard error is invalid, and the threshold must be per node.** The
   residual is serially correlated, so mean/(sd/root-n) came out at **179** under the null
   instead of about 1. And node quality varies by two orders of magnitude - over a 2-day
   span one node stays inside 1.08 vehicles on a flow of 725 while another wanders to
   32.2 - so a pooled threshold is set by the worst node and blinds the rest.

Full corridor, 199 nodes (`results/faults_full_M25_A.json`):

| Injected fault | Detected | Correct detector 1st | Type named |
|---|---|---|---|
| *no fault (control)* | **1.2%** | - | - |
| under-count 0.5% | 70.0% | 58.8% | 83% |
| under-count 1% | 80.0% | 62.5% | 92% |
| under-count 2% | 90.0% | 73.8% | 97% |
| under-count 5% | 96.2% | 81.2% | 99% |
| constant loss 2 veh/interval | 71.2% | 51.2% | 82% |
| constant loss 8 veh/interval | 87.5% | 77.5% | 97% |
| stuck at a constant | 96.2% | 78.8% | - |

**The magnitude is recovered, not just flagged.** Injected -1.000% reads back as -0.985%; injected -8.00 vehicles/interval reads back as -7.980. Diagnosis, not an alarm.

**A capability gap, not a tuning advantage.** A length-classifier drift moves counts
between classes and leaves the total *exactly* unchanged, so no total-flow balance can
detect it at any threshold, ever:

| Misbooked share | Class relations | Total relation |
|---|---|---|
| 1% | 46.2% | 2.5% |
| 2% | 61.3% | 2.5% |
| 5% | 86.2% | 0.0% |
| 10% | 91.2% | 3.8% |

The total column sits at the false-positive floor throughout, as predicted analytically.

> **Superseded — the table above was not a controlled comparison.** The class test fires
> when *any* of the four class relations exceeds its own 1% threshold, so its false-alarm
> rate is not 1%; it was never measured, and the control quoted against it (1.2%) is the
> `none` case, which is read through the **total** relation. Measured now
> (`results/faults_fpcontrol_M25_A.json`): the four-class test fires on **10.00%** of clean
> spans. Held to the same 1% per node as the total test — by taking the null of the
> worst-of-four statistic directly from clean spans, `faults.class_joint_thresholds` — the
> control drops to **1.25%**, which is exactly the total test's own control, and the
> comparison becomes like for like:
>
> | Misbooked share | class, raw | class, at matched 1% | total relation |
> |---|---|---|---|
> | *0% (control)* | **10.00%** | **1.25%** | 1.25% |
> | 1% | 43.75% | 37.50% | 2.50% |
> | 2% | 71.25% | 67.50% | 0.00% |
> | 5% | 86.25% | 82.50% | 3.75% |
> | 10% | 90.00% | 88.75% | 3.75% |
> | 20% | 95.00% | 95.00% | 2.50% |
> | 40% | 97.50% | 97.50% | 0.00% |
>
> **The effect survives its control.** Matching the false-alarm rate costs 4–6 points below
> 5% misbooked and nothing above 20%. All 23 non-classify rows reproduce the earlier run
> bit for bit, so the calibration is isolated; the four classify rows move by up to 10
> points on re-drawn injection spans, which at n = 80 is within one standard error (≈5.5
> points) and is resampling noise. Full detail in `prior_art.md` §5c–5d.

**Second corridor (M1, 88 nodes), nothing retuned** (`results/faults_M1_A.json`):
control 1.2%; 1% under-count 82.5% detected / 73.8% attributed; stuck 96.2% / 87.5%; 5% misbooked class 95.0% / 81.2%. Replicates.

How attribution works: a detector enters each node's relation with a *known* coefficient
(+1 upstream, -(1+alpha) downstream, the fitted sign as a slip). A bias prints that
coefficient pattern across every node the detector belongs to. One bias value is fitted
by weighted least squares to the whole pattern, and the candidate explaining the most
weighted deviation wins. An innocent neighbour can explain the one node it shares with
the culprit but is contradicted by its other, clean nodes. Only works for detectors in
two or more nodes - stated as the method's limit, not hidden.

Fault typing: cut the span into busier and quieter halves. A proportional miscount scales
with flow; a constant offset does not. Whichever model fits better names the type.

---

## 13. Vehicle-class conservation - negative for reconstruction

`src/classes.py`, `src/joint.py`. Hypothesis: cars do not become lorries, so conservation
must hold per vehicle length class - four constraints per node instead of one, helping
most exactly where the method is weakest.

**It does the opposite, and the reason is physical.** The class relations are *looser*
than the total relation: mean band 60.1 vehicles for the shortest class alone against
46.5 for the total. The length classifier misbins vehicles at bin boundaries, those
errors are anti-correlated between adjacent bins, and they cancel when the four are added.

Controlled comparison, all arms from the same total prior split by measured composition:

| Hidden | prior | total constraint | same, solved in class space | total + class |
|---|---|---|---|---|
| 5% | 21.67 | 19.94 | 19.94 | 22.32 |
| 10% | 22.03 | 21.05 | 21.05 | 22.79 |
| 20% | 21.70 | 20.96 | 20.96 | 29.59 |
| 40% | 24.67 | 24.62 | 24.62 | **36.43** |

Column 4 is the control - a mathematically equivalent problem in the larger space,
reproducing column 3 **exactly**. So the damage in column 5 is the class constraints, not
the solver. Degradation grows with missingness, the opposite of the prediction.

Verified on the way: classes sum to the total exactly in 98.66% of records (remainder off
by 1 vehicle, rounding); composition varies widely across detectors (car share 0.44-0.83,
longest class 0.02-0.32), so the reasoning was sound even though the result went the other
way.

**Decision:** not claimed for reconstruction; claimed for fault detection, where section
12 shows it sees what the total relation provably cannot.

---

## 14. Certified bounds per reconstructed value

`src/confidence.py`. Each reconstructed value carries the interval obtained by minimising
and maximising that coordinate over the feasible set - two linear programs. Anything
outside it contradicts the observed data under the calibrated relation, so it is a
guarantee about the physics rather than a statistical interval, and it holds whatever
estimator produced the point value.

Full corridor, 7,514 reconstructed values over 400 intervals. De-leaked — the bounds are
computed from the relation fitted on the visible data only, so the certificate never uses
the value it certifies:

- **98.15%** are bounded by the physics at all
- **96.71%** of withheld true values fall inside their stated interval
- median certified width **43.4** vehicles per interval on a mean node flow of 706
- width by unknowns sharing the node: 1 → 41.0 (n=6,627), 2 → 138.7 (n=720), 3 → 237.8 (n=28)

These barely moved under the leak fix (98.2/96.6/43.2 before), unlike the out-of-band
figures in §7. That is expected and is worth stating: the certified interval is derived
from the same relation that constrains the reconstruction, so fitting that relation on less
data widens the interval slightly and coverage is essentially unchanged. It is the *scoring
against an independently fitted reference* that the leak was corrupting.

Coverage below 100% is expected, not a defect: the band is an upper quantile of the
residual, so the relation itself is violated on a matching share of intervals.

**This is now the strongest measured result on the reconstruction aspect** — and, per
§7, the only one the ablations still support in preference to an exact equality
constraint, since an equality constraint yields intervals of zero width.

### Replication across month and corridor (`results/generalisation.json`)

3 seeds each, nothing retuned — same calibration procedure, band quantile, prior, masking
and seeds throughout.

| Corridor and month | Detectors | Nodes | Prior MAE | Ours | Gain | Outside band |
|---|---|---|---|---|---|---|
| M25 clockwise, March 2025 | 367 | 199 | 15.73 | 14.36 | −8.73% | 10.90% → **5.79%** |
| M25 clockwise, June 2025 | 373 | 209 | 17.63 | 15.87 | −9.97% | 11.29% → **5.97%** |
| M1 northbound, March 2025 | 186 | 88 | 13.66 | 12.80 | −6.26% | 11.50% → **6.11%** |

June varies the month with the network fixed; M1 varies the network with the month fixed.
Gain ranges 6.3–10.0% and band violations are roughly halved everywhere. Neither effect is
a property of one stretch of road or one month.

**De-leaked.** The previous version of this table read 0.65–1.08% outside band. It was
produced with the calibration fitted on the full corridor, withheld values included, so
the band the reconstruction was scored against had itself been fitted using the values
being reconstructed. Fixed in `constrained.training_corridor`; §16.1 records the
correction. The real effect is a halving of band violations, not a tenfold reduction, and
every figure of the form "→ 0.9%" elsewhere in this document is superseded by its rerun.

---

## 15. Chronic bias — a fault that was there before anyone looked

`src/chronic.py`, `src/chronic_absolute.py`. Full corridor, 199 nodes, 367 detectors,
162 in the multi-node line-up.

Section 12 detects the **onset** of a fault: it fits each node on a clean stretch and
notices when the residual moves. A drifted loop is usually a chronic condition, not an
event. If the detector was already miscounting when the calibration was fitted, its bias
is absorbed into that node's α and β, the residual never moves, and the method is
**structurally blind** to it — and the corrupted calibration is then used to judge every
other detector at that node.

That blind spot is where the remaining novelty is. Every FDI method found — parity space,
structured residuals, GLR, power-system bad-data identification — starts from a **known,
correct** system model and asks which sensor disagrees with it. Here the model is fitted
from the very sensors under suspicion, which is circular unless something breaks it.

**The mechanism.** A per-detector bias cannot hide in the calibration without leaving a
trace, because each detector enters the nodes it belongs to with *different* coefficients:
+1 upstream, −(1+α) downstream, fitted sign as a slip. So β = C·b across the network, with
C known. Solve for a **sparse** b by ℓ1 linear program. Sparsity is what makes it a
detector rather than a re-parameterisation: every detector carries some small offset — that
is what the calibration is for — and a fault is an *outlier* in that population.

Proportional vs constant is separated by decomposing at **two flow levels**, not two times
(a chronic fault gives you no two times). Critically that second decomposition uses the
**rigid** relation with the downstream coefficient pinned at 1, because the free α of the
calibrated form is exactly what lets a percentage miscount vanish.

**Identifiability limit, stated up front:** a bias common to every detector leaves every
node balance unchanged, so the null-space component of b is not recoverable. What is
recoverable is what distinguishes a detector from its neighbours — which is where a fault
lives.

**Baseline, nothing injected:** non-zero bias for 199 of 367 detectors; median |offset|
1.19, p90 7.18, max 43.73 vehicles/interval; decomposition reproduces the fitted node
offsets to a median residual of 0.00.

**Experiment A — referenced against the unfaulted corridor** (`chronic.py`). Answers "can
the decomposition see a chronic bias at all". More favourable than deployment, because it
is handed a clean reference a real deployment does not have. 25 detectors faulted in turn,
fault applied to the **whole record before any fitting**:

| Injected chronic fault | True | Recovered (median) | 1st | Top 3 |
|---|---|---|---|---|
| loss 30 veh/interval | −30.0 | **−30.027** | 92.0% | 92.0% |
| loss 15 veh/interval | −15.0 | **−15.014** | 92.0% | 92.0% |
| loss 8 veh/interval | −8.0 | **−8.007** | 88.0% | 88.0% |
| gain 8 veh/interval | +8.0 | **+7.990** | 92.0% | 92.0% |
| gain 15 veh/interval | +15.0 | **+14.981** | 92.0% | 92.0% |
| gain 30 veh/interval | +30.0 | **+30.028** | 92.0% | 92.0% |
| under-count 5% | −0.0500 | **−0.0560** | 88.0% | 92.0% |
| under-count 2% | −0.0200 | **−0.0220** | 80.0% | 88.0% |
| over-count 2% | +0.0200 | **+0.0209** | 84.0% | 92.0% |
| over-count 5% | +0.0500 | **+0.0518** | 84.0% | 88.0% |

**Experiment B — reference-free, and the one that counts** (`chronic_absolute.py`).
Experiment A still leans on a clean reference, and a chronic fault by definition denies you
one; requiring it readmits the onset assumption through the side door. Here the corridor is
taken as it arrives, decomposed once, and a detector is flagged when its recovered bias is
an outlier *within the population of recovered biases* — robust z on median and MAD,
k = 3.5. Nothing is differenced against anything. Fault type is named without being told,
by comparing both components on a common vehicles/interval scale.

Nothing injected: **40 of 162** detectors flagged (24.7%). Robust scale 0.69 veh (constant
component), 1.47 veh (proportional). Those 40 are **not** reported as false alarms — this
is real road data and some may genuinely be miscounting, which is the premise of the whole
exercise. The figure bounds the alarm rate from above. They are excluded from the
injection pool so no fault is credited to a detector already singled out.

| Injected chronic fault | Detected | 1st over whole line-up | 1st, standing outliers set aside | Type named | Extra flagged/trial |
|---|---|---|---|---|---|
| loss 30 veh/interval | 92.0% | **0.0%** | 92.0% | 92.0% | 0.64 |
| loss 15 veh/interval | 92.0% | **0.0%** | 92.0% | 92.0% | 0.64 |
| loss 8 veh/interval | 88.0% | **0.0%** | 88.0% | 88.0% | 0.56 |
| gain 8 veh/interval | 88.0% | **0.0%** | 88.0% | 88.0% | 0.40 |
| gain 15 veh/interval | 92.0% | **0.0%** | 92.0% | 92.0% | 0.40 |
| gain 30 veh/interval | 92.0% | **0.0%** | 92.0% | 92.0% | 0.40 |
| under-count 5% | 88.0% | **0.0%** | 88.0% | 88.0% | 0.44 |
| under-count 2% | 84.0% | **0.0%** | 80.0% | 80.0% | 0.48 |
| over-count 2% | 84.0% | **0.0%** | 84.0% | 84.0% | 0.36 |
| over-count 5% | 88.0% | **0.0%** | 88.0% | 88.0% | 0.64 |

**The zero column is the most important number in this section.** Ranked against the whole
line-up the injected detector is *never* first — the 40 standing outliers are larger than
anything injected here and stay larger. Set them aside and the injected detector is first
in 80–92% of trials. So what this delivers on this corridor is **an alarm, a size, and a
correct identification within a shortlist** — not an unqualified naming of the culprit.
Collateral cost is low: 0.36–0.64 additional detectors flagged per trial out of 162.

**Not measured:** multiple simultaneous chronic faults; whether the 40 standing selections
are genuine (no independent calibration records exist for these detectors, so both
readings fit the data); replication on M1.

---

## 16. Prior art - the gate failed for a broad claim

Full detail in `prior_art.md`. Summary:

- **de Souza (2019)**, *Freeway Loop Detector Data Reconciliation Based on Vehicle
  Conservation* — freeway loop detectors, vehicle conservation, convex optimisation with
  plausibility constraints, handles missing lanes. Closest single reference.
- **Yin et al. (2017)**, *ℓ1-minimization method for link flow correction* — road link
  flows, **hard** conservation constraint, and analytically identifies which sensors
  miscount. Takes the fault-localisation effect.
- **Usama et al. (2022)** — PINNs enforcing flow conservation at traffic junctions.
- **Process-industry data reconciliation** (`US5504692`, `US10310497`, `WO2016114736A1`,
  60 years of literature) — weighted least squares under conservation, bias estimation,
  gross error detection, unmeasured variable estimation. Every one of our "design
  decisions forced by the data" has a named counterpart there.
- **SINDy** (Brunton et al., PNAS 2016) and **SID** (arXiv 2305.19525, conservation laws
  as sparse invariants) — against the discovery step.
- Also: `US9177215`, `US5396234`, `US11574539`.
- `US11093463`, named by the landscape guide as nearest art, is **not relevant** — it
  concerns choosing multiple-imputation repetition counts to fit a time budget.

**A broad claim is dead on arrival.** What survives, narrowly:

1. method-agnostic projection of any prior onto the feasible set
2. tolerance band derived from the relation's own measured residual spread
3. topology and signs inferred from the balance itself, no external map at any stage

(1) and (2) face an obviousness attack. (3) is the freshest but is a small step, and
sparse conservation-law discovery is itself a known technique in the abstract.

**Outstanding:** Espacenet and Indian InPASS (need interactive sessions); CPC classes
`G08G1/065`, `G08G1/01`, `G06F17/18`; whether process-industry data reconciliation already
has flowsheet inference, which would be the nearest hit to (3) if it exists.

### 16.1 The reference that killed the classification claim — confirmed, not recalled

The pivot from reconstruction to fault diagnosis moved the claim out of one crowded field
and into another that had **not been searched**. Confirmed by web search:

> **Narasimhan & Mah (1987)**, *Generalized likelihood ratio method for gross error
> identification*, AIChE Journal **33**(9):1514–1521 — identifies gross errors caused by
> *biases in measuring instruments*, process leaks and controller failure, by testing
> modelled hypotheses against the residuals of process mass-balance constraints.

That is fault-type discrimination **plus magnitude estimation** from conservation-constraint
residuals, published in 1987. The claim in the earlier IDF that "the cited art detects and
localises; none classifies the kind of fault or states its size" is **false**. It has been
struck and replaced with an express statement that a claim of that scope is not available.

The distinction that survives is narrower and is now what the case rests on: GLR, parity
space, structured residuals and power-system bad-data identification **all begin from a
system model that is surveyed and assumed correct** — a flowsheet, an admittance matrix —
and ask which sensor disagrees with it. Section 15 diagnoses the *fitted model itself*,
which is the only route to a bias present when that model was estimated.

**Nearest known art to that, and NOT YET SEARCHED:** blind / self-calibration of sensor
networks (Balzano & Nowak and successors) — recovery of unknown per-sensor gains and
offsets from redundancy in the sensed field with no reference sensor. Intended distinction:
there the redundancy is a smoothness or subspace assumption about the field, here it is an
exact conservation relation whose coefficients are themselves recovered from the data, and
the object is to single out an outlier rather than to calibrate everything. A targeted
search on sparse decomposition of calibration parameters found only array/imaging geometric
calibration, which is a different problem — **not conclusive**. This is the single largest
open risk.

**Two searches remain the gate, both capable of ending the application:** CPC `G05B23/02`,
`G01D18/00`, `G01D3/08` (FDI and gross-error detection); and the patent art on blind sensor
calibration.

---

## 17. Honest overall position

**Reframed since the first draft.** The headline claim moved from reconstruction to fault
diagnosis, on the evidence:

- Reconstruction under conservation is anticipated twice in-domain and its measured gain
  over the strongest baseline is **-8.2%**, decaying to nothing at 40% missing.
- Fault detection *with classification and magnitude estimation* is not anticipated by
  anything found, runs at **0.0% false positives** with **91.7%** correct attribution from
  a 162-detector line-up, recovers the fault size to within a few percent, and includes a
  fault class total-flow methods are provably blind to.

**Strong:** the technical-effect anchor is about as good as software analytics gets - a
physical law, measured evidence on two corridors and two months, no business-method
exposure, not a black box. The fault-diagnosis result is quantitative and reproducible,
and the class-transfer blindness is an analytic impossibility argument backed by
measurement, which is a rare thing to have.

**Weak:** novelty on the reconstruction aspect. That core is published in-domain twice and
is a mature technique in another field. Several individually attractive results turned out
to be small-sample artefacts (discovered-vs-surveyed topology) or negatives (class-wise
reconstruction, downstream forecasting), and all are reported as such.

**Untested:** the classification and sizing step against process-industry gross-error
literature, which is where the nearest hit would be if it exists. Espacenet and InPASS
searches are outstanding.

### Corrections to the above, recorded rather than quietly edited

1. **The classification-and-sizing novelty claim is withdrawn.** Narasimhan & Mah (1987)
   discloses it (§16.1). The bullet above claiming it "is not anticipated by anything
   found" was written before that field was searched, and was wrong.
2. **A test-set leak was found and fixed.** `constrained.reconstruct` was calibrating α, β
   and the tolerance band on the *full* corridor, including the very values it was then
   scored on reconstructing. It now calibrates on the view only
   (`constrained.training_corridor`). The de-leaked out-of-band figure on M25 March is
   **10.90% → 5.79%**, not 10.90% → 0.93%. Every headline reconstruction number in §7 and
   §14 must be republished from the reruns; the corrected values are lower.
3. **The principal claim has moved again**, to the chronic case (§15), because that is
   where the surviving distinction from the FDI art is. The onset method is now a second
   independent claim and is treated as the more exposed of the two.

**As a project deliverable:** strong. Real measurements, negatives reported, prior art
mapped rather than assumed, two claims withdrawn on the evidence, a leak found and
corrected against our own interest, and the reference-free chronic experiment reported
with its worst column (0.0% rank-1 over the full line-up) intact.

**As a grantable patent: 2 out of 10 — do not file.** The gate was run and it failed.
Two independent blockers, both verified:

1. **The surviving distinction is occupied.** Power-system **network parameter error
   identification** — Liu, Wu & Lun, *IEEE TPWRS* 7(1):81–89 (1992); Zhu & Abur, *IEEE
   TPWRS* 21(2):586–592 (2006) — treats the *fitted model* as the object under suspicion,
   estimates a bias vector from it, and decomposes that vector over known network
   structure to name the erroneous element. That is the claimed architecture, in a
   conservation-governed network, from 1992. This project cited only the *bad-measurement*
   half of power-system state estimation, which is the half that does assume a surveyed
   admittance matrix. Combined with Yin et al. (2017), already cited, which supplies ℓ1
   minimisation under hard flow conservation *in this domain*, it is a two-reference
   obviousness combination. Also uncited and in-domain: **Vanajakshi & Rilett**, *TRR*
   1870 (2004), conservation-of-vehicles loop-detector diagnostics for non-catastrophic
   malfunction; and **Cheevarunothai et al.**, *TRR* 1945 (2006), identification and
   correction of loop *sensitivity* drift — the exact fault mechanism §4 is built on.

2. **The mechanism does not do what §6.3 described. Verified directly:**
   `rank(C) = 199`, `nullity = 168` (not 1), `max|C·b − β| = 7.1e-15`, non-zeros = 199.
   The system is underdetermined, so the LP fits β *exactly* — the `(genuine per-node
   effects)` term is identically zero, and every non-conservation that is not detector
   bias is attributed to detector bias. The support of 199 is `rank(C)`, the LP basic
   solution bound, not a discovery about how many detectors carry a bias. What the
   procedure computes is the minimum-ℓ1 representation of β in the row space of C.
   The IDF has been corrected to say all of this.

There is no third pivot. The one feature not found in any search is **claim 6 + claim 9,
the class-transfer fault** — conservation evaluated per vehicle length class, with an
analytic impossibility argument for total-flow methods. Small, currently without a
false-alarm control, but genuinely unlocated in the art.

**As an academic project report: 8/10 and rising.** The measurement discipline is the
asset — real data, baselines given every advantage, a masking protocol justified rather
than assumed, ablations reported when they came out wrong, a test-set leak found and
corrected against our own interest with every affected number republished, two novelty
claims withdrawn on evidence, and the worst column in the project (0.0% rank-1 over the
full line-up) printed rather than buried. The route to 9–10 is to write up the gate we
set, ran and failed — including the rank/nullity diagnosis of why our own method
underperforms. A project that explains its own failure is worth more than one that
reports a pass.
