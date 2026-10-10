# Phase 6 — Prior art

Searched 2026-08-03. Honest finding first, because it changes the plan:

> **The broad idea — reconstructing or correcting traffic counts subject to flow
> conservation — is not novel. It is published, in this exact domain, more than once,
> and the underlying technique is a mature field in another domain entirely.**

The landscape guide named `US11093463` as nearest art. That was wrong, and in our
favour it was wrong in the easy direction: `US11093463` is not close at all. The real
prior art is elsewhere and it is much closer than the guide anticipated.

---

## 1. The killer: process-industry data reconciliation

Our method is, structurally, **data reconciliation with gross error detection**: adjust
measurements by weighted least squares so they satisfy conservation constraints, estimate
the unmeasured variables at the same time, and flag the measurements that cannot be
reconciled. This is a mature field in chemical and process engineering dating to the
1960s, with a large patent estate.

| Reference | What it does |
|---|---|
| `US5504692` — System and method for improved flow data reconciliation | Least-squares adjustment of measured flows subject to mass-balance constraints; explicitly estimates true flows from measured ones and handles unmeasured streams |
| `US10310497`, `US8781635` — Equipment condition and performance monitoring using comprehensive process model based upon mass and energy conservation | Conservation-based reconciliation used to detect faulty equipment/instruments |
| `WO2016114736A1` — Real-time data verification and data reconciliation system for petroleum refineries | Real-time reconciliation against balance constraints |
| Extensive literature on simultaneous data reconciliation and gross error detection | Bias estimation per instrument, MILP/branch-and-bound formulations, observability and redundancy analysis for unmeasured variables |

Every one of our "design decisions forced by the data" has a named counterpart here:

- our per-node scale-and-offset calibration → **systematic bias estimation**
- our infeasibility flag → **gross error detection**
- our handling of missing values → **unmeasured variable estimation / observability analysis**
- our weighted deviation objective → the standard reconciliation objective

This does not by itself destroy a traffic-specific claim, but it means an examiner has a
strong, well-documented obviousness argument: applying a known reconciliation technique
to a new measurement domain.

## 2. In-domain hits — road traffic, flow conservation

### de Souza (2019), *Freeway Loop Detector Data Reconciliation Based on Vehicle Conservation*, Procedia Computer Science

The closest single reference.

- Freeway loop detectors, vehicle conservation between stations
- Convex optimisation with explicit constraints guaranteeing physically plausible values
- Uses occupancy to bound accumulation between stations
- States that no modification is required when data from one or more lanes are missing

Distinctions that survive: it **corrects observed counts** rather than being framed as
reconstruction of missing records; its bounds come from occupancy-derived accumulation
limits rather than from the measured spread of the balance relation itself; per-detector
bias calibration is not described; irreconcilable cases are prevented by constraint
design rather than detected and reported. These are real but narrow distinctions.

### Yin, Sun, Jin, Xin (2017), *ℓ1-minimization method for link flow correction*, arXiv:1704.02052

Also very close, and it takes the one piece I had thought was our freshest angle.

- Road network link flows, **hard** flow conservation constraint
- Corrects corrupted link flows when a few sensors are bad
- Introduces "recoverability" to **analytically identify which links are robust to
  miscounts** — i.e. it already localises faulty sensors under conservation

So "flag the detector that cannot be reconciled" is published in-domain.

### Usama et al. (2022) — physics-informed neural networks on traffic networks

Decomposes a network into links and **enforces flow conservation at junctions**. Our node
construction is the same concept.

### FlowSymm (Demirci, Bullo, Swami, Singh, arXiv:2601.22317)

Network flow completion, evaluated on PEMS road traffic and Citi Bike. Physics-aware
imputation of missing flow measurements. Reported to impose conservation as a **soft**
constraint — our hard-constraint distinction survives against this one specifically.
*Flagged for manual verification: this was read from a PDF and the extraction was
partial.*

### Broader imputation literature

IEEE T-ITS (2024) published *A Comprehensive Survey on Traffic Missing Data Imputation*.
The field is large and active — LSTM/attention hybrids, DCNN-GAN, tensor completion,
cokriging. Conservation-constrained variants appear within it. Our baselines are drawn
from this literature and are fair representatives of it.

## 3. Not close, despite the guide's suggestion

`US11093463` (Fanuc, priority 2019-04-22) — "Missing value imputation device". Claim 1 is
about choosing the number of multiple-imputation repetitions that fits a time budget. No
physical constraint, no network topology. Not relevant.

---

## 4. What is left

After the above, the following are not directly anticipated by anything found:

1. **Method-agnostic projection.** The prior art builds standalone estimators. Ours takes
   the output of *any* existing imputation method and projects it onto the feasible set,
   leaving an already-plausible estimate untouched. Measured effect: it improves every one
   of four structurally different priors.
2. **Tolerance band derived from the relation's own measured residual spread**, rather
   than from an assumed noise model or from occupancy-derived accumulation bounds. This
   was forced by measurement: exact equality measurably degraded an accurate prior
   (MAE 22.09 exact vs 21.05 banded).
3. **Topology and slip sign inferred from the balance residual itself**, so no external
   network map, junction database or naming convention is required.

Honest assessment of these three: (1) and (2) are narrow and face an obviousness attack;
(3) appears the freshest and was not found in any hit, but it is a small step.

## 4b. Prior art against the topology-discovery step — search honestly before relying on it

The strongest remaining distinction is that our method recovers the conservation
relations from the counts rather than taking a network map as input. Before leaning on
it, the obvious attack must be acknowledged:

- **SINDy** — Brunton, Proctor and Kutz, *Discovering governing equations from data by
  sparse identification of nonlinear dynamical systems*, PNAS 2016. Sparse regression to
  recover governing equations from measurements. Our step is the same family: sparse
  regression, then rounding to integer coefficients.
- Network topology inference / sparse null-space recovery is a literature in its own
  right, in sensor networks and in systems biology.

So "discover a physical relation by sparse regression" is not novel in the abstract. What
was not found anywhere is the *combination*: discovering the conservation relations from
traffic counts, selecting among them by measured residual tightness, and then using the
discovered relations as the hard constraints that reconcile the very same dataset — with
no external topology at any stage. Whether that combination is non-obvious is a genuine
question, not a settled one.

**Still to search specifically:** sparse identification applied to traffic sensor
networks; "constraint discovery" in data reconciliation (the process-industry field may
already have an equivalent, since flowsheet inference is a natural problem there); and
CPC classes around `G06F17/18` combined with `G08G1/01`.

## 5. Recommendation

**A broad claim of the form "reconstruct missing traffic counts subject to flow
conservation" is dead on arrival.** It is anticipated by de Souza (2019) and Yin et al.
(2017) and rendered obvious by the data-reconciliation estate.

Two viable paths:

- **Narrow the claim** to the combination of (1), (2) and (3) above, with the distinction
  paragraphs written against de Souza and Yin explicitly rather than hoping an examiner
  misses them. Grant is uncertain; the honest odds are not good.
- **For the academic deliverable, proceed and make this analysis the centrepiece.** The
  landscape guide itself warned that academic prior art counts in full and that the
  assignment likely rewards a defensible argument honestly made. An IDF that maps its own
  nearest art precisely, and narrows its claim in response, demonstrates more than one
  that asserts unexamined novelty.

The prototype and its measurements remain valid and useful under either path. What
changes is the breadth of what can be claimed over them.

## 5b. The class-transfer claim, searched — 2026-08-05

This was the last live thread: claims 6 and 9, class-resolved conservation detecting a
length-classifier drift that leaves the total *exactly* unchanged and is therefore
invisible to any total-flow balance. `FINDINGS.md` §16.1 recorded it as "the one feature
not found anywhere". It has now been searched properly, and the result splits in two.

**The analytic half is occupied, and by a general theory rather than a near-miss.**

The claim's centrepiece is an impossibility argument: a fault lying in the null space of
the total-flow residual map cannot be detected by that map at any threshold, and enlarging
the constraint set makes it detectable. In process engineering that is not an observation,
it is a named and developed body of theory:

| Reference | What it establishes |
|---|---|
| Bagajewicz & Jiang (1998), **equivalency theory of gross errors** | two sets of gross errors are *equivalent* when they have identical effect on reconciliation; the theory characterises exactly which errors are indistinguishable and which are undetectable. Illustrated with cancelling biases that go undetected "no matter how big they are" |
| Bagajewicz (2000), **error detectability as a designed sensor-network property** | detectability is one of five formal properties of a robust sensor network, alongside precision, residual precision, availability and resilience — i.e. "which faults can this constraint set see" is a quantity the field designs against |
| Bagajewicz & Sánchez (1999c), extended to **bilinear systems** by Bagajewicz (2000) | constraint-set augmentation to force redundancy, carried explicitly from linear (flow-only) to bilinear (flow *and* composition) systems |
| Narasimhan & Jordache (2000), *Data Reconciliation and Gross Error Detection*, ch. **"Steady State Data Reconciliation for Bilinear Systems"** | the textbook treatment of component balances alongside total balances |
| Crowe et al. (1983), Crowe (1986); Sánchez & Romagnoli (1996) | projection-matrix and Q-R methods for reconciling flows *and compositions* under component balances |

Read together: "the total mass balance is blind to a bias that redistributes material
between components; the component balances see it" is the traffic instance of a textbook
result about gross-error detectability under an enlarged constraint set. The four vehicle
length classes map onto species/components one-to-one, and the length classifier maps onto
the composition analyser. An examiner who reaches this field has a clean §2(1)(ja)
obviousness argument, and combined with Yin et al. (2017) — which already supplies hard
flow conservation with sensor-fault localisation *in this domain* — it is again a
two-reference combination.

**The in-domain half is genuinely clear.** Searched Google Patents and the traffic
literature for validating classified counts against a conservation relation, and for
detecting classifier drift that way. Nothing. The vehicle-classification estate
(`US7136828B1`, `US5717390A`, `US7764808B2`, `WO2008088880A1`, and the current LiDAR/ML
toll-plaza work) is entirely about *making* the classification, never about auditing a
deployed classifier against a network-level invariant. FHWA's *Traffic Monitoring Guide*
and the state count manuals handle classification data quality by statistical reliability
assessment, not by conservation. Cheevarunothai et al. (2006) is the nearest in-domain
work and addresses loop *sensitivity* — a total-count fault — not class transfer.

So the position is: novel in the traffic domain, anticipated in general form in another.
That is the classic transposition case, and it is decided on whether the transposition
required more than routine skill.

**What is not in any of the above, and is ours by measurement rather than by argument:**
the four class relations are *looser* than the total relation, not tighter — measured mean
tolerance band 60.1 vehicles for the shortest class against 46.5 for the total (§13). The
misbin errors are anti-correlated between adjacent length bins and cancel on addition, so
the aggregate carries information the components do not. That inverts the assumption the
process-industry treatment rests on, where component balances are the finer instrument. It
is a real, non-obvious, domain-specific finding. It is also, on its own, an *unfavourable*
one: it is why class-resolved reconstruction failed (§13), and it is why the class-transfer
detector needs the false-alarm control of §5c before its sensitivity means anything.

## 5c. The false-alarm control the class test never had

Found while auditing `faults.py` for §5b. The classify test fires when **any of the four**
class relations exceeds its own 1%-false-positive threshold, so its false-alarm rate is
not 1% — it is somewhere between 1% and 4%, at a point set by how correlated the four
class residuals are, which is a property of the data and had never been measured. The
control reported against it (1.2%) was the `none` case, which is read through the **total**
relation. The capability-gap table therefore compared a class test at an unmeasured
false-alarm rate against a total-flow test at a measured 1%.

Fixed in two places. `faults.py` now runs `("classify", 0.0)` — share zero moves no
vehicles, so clean data goes through the identical four-class pathway and yields that
pathway's own control — and `class_joint_thresholds` takes the null of the worst-of-four
statistic directly from clean spans, per node, so the combined test can be held to 1% and
compared like for like. Results in §5d.

## 5d. The capability gap, measured against its own control

Full corridor, M25 clockwise, 199 nodes, 40 detectors, 2-day spans, 80 trials per case,
calibration fitted on one half-month and every fault injected into the disjoint other half.
`results/faults_fpcontrol_M25_A.json`.

The concern was justified. **The four-class test fires on 10.00% of clean spans**, not the
1% each of its four thresholds was individually set to. The previously published
capability-gap table therefore credited it with sensitivity it had partly bought by firing
eight times more often than the test it was being compared against.

Holding it to the same 1% per node as the total-flow test:

| Misbooked share | class relations, raw | class relations, at matched 1% | total relation |
|---|---|---|---|
| *0% (control)* | **10.00%** | **1.25%** | 1.25% |
| 1% | 43.75% | 37.50% | 2.50% |
| 2% | 71.25% | 67.50% | 0.00% |
| 5% | 86.25% | 82.50% | 3.75% |
| 10% | 90.00% | 88.75% | 3.75% |
| 20% | 95.00% | 95.00% | 2.50% |
| 40% | 97.50% | 97.50% | 0.00% |

Calibration brings the control to 1.25%, which is exactly the total-flow test's own control,
so the two columns are now the same test at the same false-alarm rate on the same spans.

**The effect survives.** It costs 4–6 points at the smallest misbooked shares and nothing
above 20%. At 5% misbooked the class relations detect 82.5% and the total relation 3.75%,
both controlled at 1.25%. The total column sits at its false-positive floor throughout,
which is the analytically predicted behaviour and is now demonstrated rather than merely
predicted.

*Isolation of the change.* The joint calibration draws its spans from a dedicated generator
so the shared stream is untouched, and **every one of the 23 non-classify rows reproduces
the published run bit for bit**. The four classify rows shift by up to 10 points
(0.4625→0.4375, 0.6125→0.7125, 0.9125→0.9000, 0.9375→0.9500) because inserting the control
case ahead of them re-draws their injection spans; at n = 80 one standard error is about
5.5 points, so those are resampling noise, not an effect. Reported rather than smoothed.

**What this does and does not buy.** It converts claims 6 and 9 from unevidenced to
evidenced — the sensitivity figures now mean what they say, and the impossibility argument
is backed by a controlled measurement. It does nothing to §5b: the general form of the
argument remains occupied by gross-error detectability theory, and this experiment is
evidence for a claim whose novelty is contested, not evidence of novelty.

## 6. Searches still worth running

- Espacenet and Indian Patent Advanced Search (not yet queried; the above is Google
  Patents plus academic search)
- CPC class `G08G1/065`, `G08G1/01` cross-referenced with data-quality/imputation terms
- Direct full-text read of de Souza (2019) — currently behind a 403 on ScienceDirect, so
  the summary above is from the OSTI record

---

## 7. The §4b searches, run — 2026-09-22

§4b named three searches as gating the one surviving distinction (topology and slip signs
inferred from the balance residual itself, no external map). All three are now run, plus a
patent-estate sweep. **The distinction holds.** The finding in one line: *everyone takes
the incidence matrix as an input.*

**(a) Sparse identification / physics-informed methods on traffic sensor networks.**
The PINN and PDE-discovery line is real and active — Usama et al., TRAFFIC-PDE-LEARN
(arXiv:2505.00904), and the domain-decomposition PINN work (arXiv:2605.08028). What they
discover is the *governing PDE of traffic dynamics*; what they assume is the network.
Flow conservation is enforced "at junctions" by decomposing a network into individual
links — the link set is given. Castillo et al.'s state-of-the-art review of sensor
location and flow observability (J. Sensors, 2015) is explicit: the observability problem
is posed *through equations associated with network topology incidence matrices*. The
incidence matrix is the input to that literature, never its output.

**(b) Constraint discovery in data reconciliation.** This was the dangerous one, since the
process industry has occupied every other distinction. It does not occupy this one.
Reconciliation is defined on *a given network*: "modifying measured or estimated
quantities in order to balance the mass flows in a given network". Where the field does
speak of unknowns, they are unmeasured *flows*, not the constraint structure — the flow
vector is split into informed and unknown quantities, with the balance equations
themselves fixed throughout. Component balances need composition *known* in advance.
Flowsheet inference, hypothesised in §4b as a natural problem for the field, was not
found as a solved or posed one.

**(c) Topology inference from detector counts, in-domain.** Counts are used for OD-demand
estimation and static traffic assignment via modularity partitioning
(arXiv:2211.13514) — on a known network, and the literature notes inductive loops give no
route information at all. Map-inference work that does recover topology
(*Inferring and Improving Street Maps*, CACM; Road Network Fusion, arXiv:1802.02351)
recovers it from **GPS traces and imagery**, not from counts. No work was found that
recovers connectivity from count data alone.

**(d) Patent estate.** `G08G1/01` cross-referenced with structure-from-counts returns
detector hardware (US3126522A, EP0523844A1, DE3521655A1) and enforcement systems, none
relevant. The single near hit, **US6850840B1** *Method for describing and generating road
networks*, was read to claim 1 and **ruled out**: it takes pre-existing nodal points and
links as input and inserts contour points to better approximate road geometry, from
position-determination data. Claim 1's limitation is *"forcing at least one link to
approximate a real course of a road between two nodal points in accordance with at least
one contour point if the distance between the two nodal points exceeds a predetermined
distance."* Geometry refinement on a known network, from GPS. Not structure discovery, and
no count data.

**Consequence.** Survivor (3) in §4 survives its own adversarial search and is the element
to build the claim on. Two cautions carried forward, not resolved:

- SINDy (Brunton/Proctor/Kutz, PNAS 2016) still makes "recover a relation by sparse
  regression" old in the abstract, so the claim must rest on the *combination* — discovery
  from counts, selection by measured residual tightness, and reuse of the discovered
  relations as the hard constraints reconciling the same dataset — not on the regression.
- Absence of evidence from four searches is not proof of absence. Espacenet and InPASS
  remain unrun, and de Souza (2019) is still unread in full text.

**Still outstanding:** Espacenet; Indian Patent Advanced Search; de Souza (2019) full text.

## 8. Deep search, 2026-09-24 (after v2 of the IDF-B)

New art, not yet in the IDF-B Section 3 table:

- **LV power-grid topology identification from smart-meter energy data by energy
  conservation + (constrained / weighted) least squares or Lasso** — e.g. "Low-voltage
  distribution network topology identification based on constrained least square and graph
  theory" (Soft Computing, 2022, doi 10.1007/s00500-022-07151-3); layer-by-layer stepwise
  regression on energy conservation; Lasso user-ownership (Energies 17(7):1762, 2024).
  Analogous field, directly pertinent: recovers which meters belong to which parent from
  conservation, integer (0/1) membership. Distinctions: parent/child roles known (meter
  types), 0/1 membership not ±1 direction, tree not chain, no ordering stage.
- **Connectivity-model error detection and correction from meter data** — US 9,816,836 B2
  (Oracle, prio 2014-11-10) and US 11,916,380 B2 (Landis+Gyr, prio 2017-08-07): flag wrong
  meter-to-transformer mappings and propose/auto-apply the corrected mapping. Voltage
  correlation, not conservation. Occupies the *concept* of claim 12 (map audit + repair).
- **US 11,205,901 B2** (Depsys/Kraken, prio 2017-09-12): power network topology from
  metering data via current sensitivity coefficients; parent meter at slack node assumed.
- **Graph WaveNet** (IJCAI 2019) and successors: adjacency of traffic sensors learned from
  data with no road network — soft, weighted, black-box; not conservation relations.
- **Reaction-network identification**: integer stoichiometry inferred from time series
  (arXiv:1412.6346; PLOS One 2026 logistic regression) — integer-coefficient conservation
  structure from data, other domain.
- de Souza (2019) read in full: station layout with mainline/on-ramp/off-ramp types is an
  INPUT; bounds from occupancy. Characterisation in Section 3 holds.
- US law: Electric Power Group v. Alstom (Fed. Cir. 2016) — collecting/analysing grid
  measurement data is abstract; In re Stanford (Fed. Cir. 2021) — more accurate
  computation is not a technological improvement. India: Kroll v. Controller (Del HC,
  1 Jul 2025) refusal for lack of technical effect; Raytheon (2023) — no novel hardware
  needed; 2025 CRI Guidelines — math inside a technical process with measurable effect OK.


## 9. Claim-directed search, 2026-09-24 (verified from primary text)

- **Yang, Yang & Fan (2019), "Networked sensor data error estimation", Transportation
  Research Part B 122:20-39.** GMM estimate of a multiplicative bias per sensor from nodal
  flow balance on a given node-link adjacency matrix; hypothesis test on sensor health;
  corrected counts. Follow-up: H. Yang, PhD dissertation, UC Davis 2022 (ROSAP dot 73744).
  Closest art to Claim 12. Distinction: network given; ours recovered.
- **US 9,053,519 B2 (TaKaDu, priority 2012-02-13).** For a DMA whose boundary meters come
  from GIS, chooses +/- direction of each meter in the mass balance from meter data by
  plausibility of the consumption curve. Concedes signs-from-data. Distinction: membership
  and order not recovered; selection by plausibility, not closure within self-derived noise.
- **Lu, Varaiya, Horowitz, Palen, "Faulty loop data analysis/correction and loop fault
  detection" (PATH review).** Upstream/downstream flow ratios, known layout. Same class as
  entry 3.
- **EP1659550A2.** Toll data checked against a stored node-edge model (Kirchhoff). Topology
  stored, not derived. Not closer.
- **India:** Microsoft v. Asst. Controller, 2024 SCC OnLine Mad 285 (sensor-data invention,
  refusal set aside) — favourable. Kroll v. Controller (Delhi HC, 1 Jul 2025) — refused, P2P
  keyword search, "no technical advancement to the hardware".


## 10. Espacenet and InPASS, 2026-09-25 (IDF-B Table A)

Espacenet full text: "traffic detector flow conservation" 83; "traffic detector topology
conservation counts" 1 (CN103489316A, detector placement on given network); "traffic
detector fault correction flow balance" 9 (none); "missing traffic data flow conservation"
86 -> **CN102169630A** (2011, Shanghai): faulty fixed traffic-data device identified via
cross-sectional flow conservation, data completed from history + adjacent loops; layout
given. IDF-B entry 23. Abstract read on the Espacenet page.
InPASS (published + granted): abstract "traffic conservation" 2774 (latest 25 screened,
none); abstract "detector topology" 6 (all screened; 5684/DELNP/2008 mobile-terminal
maps, none); IPC G08G AND "conservation", IPC G08G 1 AND "detector": screened by user,
none relevant. abstract "sensor fault correction flow" 38,076 (OR semantics, unscreenable,
not logged).
Correction: FlowSymm (arXiv 2601.22317, entry 15) enforces conservation EXACTLY on a given
graph (divergence-free completion), not as a soft term. IDF-B entry 15 corrected.
