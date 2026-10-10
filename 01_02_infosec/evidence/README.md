# Evidence campaign — Label-Free Malpractice Detection disclosure

Purpose: replace Section 8, which is currently simulation on a generative model the
inventor wrote himself, with measurement on real recorded data. The 2026-09-01 audit
scored evidence 3/10 and identified E3 — a real multi-node sensor array — as the work
that moves the rating.

**Nothing here has been published anywhere and nothing may be. Any public repository,
preprint or benchmark submission before the priority date is a Section 29 disclosure and
makes Section 12 Fifth of the disclosure false.**

---

## Corpus

**Server Machine Dataset (SMD)**, from the OmniAnomaly release, **MIT licence** — no
encumbrance on a commercially intended filing. 28 server entities, 38 channels each,
28,479 samples per entity at one sample per minute, per-entity min-max normalised to
[0,1]. Train splits are anomaly-free by construction; test splits carry point labels and
per-dimension interpretation labels.

Chosen because it is the closest available public proxy for a venue of like-instrumented
stations: many entities, one common channel schema, normal-only training data. No public
corpus of replicated identical stations exists, which is exactly why the disclosure had
to simulate in the first place.

Two honest caveats, both stated in every write-up:

- SMD entities are **heterogeneous machines across three clusters**, whereas a venue is
  identical desks in one room. SMD is therefore a **pessimistic** proxy for anything that
  depends on stations resembling one another.
- SMD samples once per minute, so all lags here are in **reporting intervals**, not
  seconds. The disclosure's 1–3 s coupling lag maps to 1–3 intervals at a 1 Hz station
  reporting rate. The mechanism is rate-agnostic; the corpus fixes only the interval.

Rejected: **Exathlon** (VLDB 2021) is a better physical fit — real multi-node Spark
cluster, six anomaly types, root-cause and extended-effect ground truth, and its
resource-contention anomalies are a genuine venue-wide common-mode event — but it is
**CC BY-NC-SA 4.0**. Non-commercial licensing on evidence underpinning a commercially
intended patent is not worth the argument. Revisit only if Aditya wants it.

## Split discipline

Group-disjoint throughout. The shared model is trained on SMD groups 1 and 2 (17
entities, 417,349 windows) and **never sees group 3**. Every measurement is made on
group 3 (11 entities, 55 station pairs). Per-station control models are trained on each
held-out entity's own calibration normals — identical architecture, optimiser, epochs and
preprocessing, so the only difference between conditions is shared versus local
parameters.

Predictor is a deliberately plain one-step-ahead MLP (window 20 × 38 → 128 → 128 → 38).
Plain on purpose: the disclosure's contribution is meant to be the arrangement, not the
model, and a strong backbone would blur which is which.

---

## Results

### E3(i) — commensurability: **REFUTED**

`e3_smd.py` → `results/e3_smd_commensurability.json`

Does one shared normal-only model make residual magnitudes comparable across stations, so
that a threshold calibrated at one station holds at another? Threshold set at each
station's 99th residual percentile, applied to every other station's held-out normals,
110 ordered pairs.

| | shared | per-station |
|---|---|---|
| median realised FPR (nominal 0.0100) | 0.0095 | 0.0068 |
| within 2× nominal | 17.3 % | 22.7 % |
| within 10× nominal | 45.5 % | 53.6 % |
| p95 realised FPR | 0.795 | 0.282 |
| KS median between station pairs | 0.599 | 0.389 |
| AUROC mean on labelled test split | 0.739 | 0.797 |
| spread of mean residual across stations | **4.1×** | **2.8×** |

Sharing is worse on every commensurability metric and worse on detection. It **widens**
scale disagreement. Mechanism: a shared model fits some stations better than others, so
its residual magnitude encodes how typical that station is — a station property, not a
common scale.

**Capacity objection closed.** The obvious rebuttal is that a 128-wide model trained for 5
epochs simply lacked the capacity to fit 17 heterogeneous machines. Re-run at **384 wide,
12 epochs** — three times the width, 2.4 times the epochs, 2.7 hours of compute — with
both conditions scaled identically (`results/e3_smd_commensurability_big.json`):

| | shared | per-station |
|---|---|---|
| within 2× nominal | 14.6 % | 20.0 % |
| within 10× nominal | 32.7 % | 52.7 % |
| p95 realised FPR | 0.961 | 0.352 |
| KS median | 0.560 | 0.440 |
| AUROC mean | 0.734 | 0.776 |

More capacity makes the shared model **worse**, and widens the gap: the within-10× deficit
grows from 8.2 points to 20.0. The finding is not an artefact of an undertrained model, and
the direction is now robust to the one sensitivity that could plausibly have reversed it.

### E3(ii) and E3(iii) — coupling channel: **CONFIRMED, in the opposite configuration**

`e3_coupling.py` (single trial, factorial) and `e3_repeat.py` (20 trials, resampled pairs
and injections) → `results/e3_coupling.json`, `results/e3_repeat.json`

Perturbations are injected into the **raw channel signal before the predictor**, never
into the residual. Scenario D is the operating case: one genuinely coupled station pair
at lag 2 intervals, plus a simultaneous venue-wide event reaching all 11 stations.
Detection = the coupled pair ranked first of 55. AUROC ranks the coupled pair against the
54 uncoupled ones.

**20 trials, scenario D:**

| model | reference rule | detection | AUROC | z median |
|---|---|---|---|---|
| shared | none | 0.00 | 0.532 | 0.01 |
| shared | raw median | 0.00 | 0.516 | 0.18 |
| shared | standardised median | 0.00 | 0.559 | 0.19 |
| per-station | none | 0.10 | 0.632 | 0.57 |
| **per-station** | **raw median** | **0.60** | **0.983** | **4.42** |
| per-station | standardised median | 0.55 | 0.920 | 3.28 |

Coupled pair only, no venue event: per-station + raw median 0.65 / **0.977** / 4.13.

Three things fall out.

1. **The shared model is at chance.** AUROC 0.51–0.61 across every rule and both
   scenarios, zero detections in 20 trials. It does not merely fail to help — it removes
   the channel.
2. **Common-mode rejection is necessary, and the size of its effect is now measured.**
   Per-station, no rejection → raw median rejection: AUROC **0.632 → 0.983**, detection
   **0.10 → 0.60**, z **0.57 → 4.42**. Without it the coupled pair has the highest raw
   correlation in the venue and is still not top-ranked, because the venue-wide event
   lifts every pair with it.
3. **The extra calibration step is not needed and slightly hurts** (0.983 → 0.920). The
   plain across-station median of per-station residuals is the best rule tested.

**Why the shared model poisons the channel.** With no injection at all, applying median
rejection under the shared model *raises* mean pair correlation from 0.0738 to 0.1381.
The shared model's prediction errors are correlated across stations because they are the
same model's errors. It manufactures a cross-station common component out of its own
deficiencies, and a reference formed from the stations carrying that component cannot
remove it.

Venue-wide event suppression, mean r over all 55 pairs:

| | floor, no injection | with event, no rejection | after raw-median rejection |
|---|---|---|---|
| per-station | 0.0607 | 0.3339 | 0.0225 |
| shared | 0.0738 | 0.1609 | 0.1321 |

### Clock-skew tolerance — **measured, not asserted**

20 trials per point, per-station + raw median, scenario D, coupling lag 2 intervals.

| inter-station skew | detection | z median | AUROC |
|---|---|---|---|
| ±0 | 0.75 | 3.93 | 0.992 |
| ±1 (0.5 × lag) | 0.65 | 3.49 | 0.987 |
| ±2 (1 × lag) | 0.60 | 3.37 | 0.981 |
| ±3 (1.5 × lag) | 0.35 | 2.69 | 0.954 |
| ±4 (2 × lag) | 0.30 | 1.88 | 0.939 |
| ±6 (3 × lag) | 0.15 | 1.25 | 0.828 |
| ±8 (4 × lag) | 0.15 | 0.80 | 0.726 |

Monotone. Expressed as a fraction of the coupling lag the sweep is rate-agnostic: AUROC
holds above 0.95 while skew stays within about 1.5 × the lag, and collapses beyond 3 ×.
For the disclosure's 1–3 s lag that puts the useful envelope near or below one second,
and the proposed ≤50 ms synchronisation sits at roughly 2 % of the lag — comfortably
inside, with the margin now derived from data rather than asserted.

The first skew sweep in `e3_coupling.py` is **void**: it was run on the shared cell, which
the factorial then showed was not detecting at all, so it measured degradation of a
non-signal. It is retained in the JSON only so the error is on the record.

### Operating envelope

`e3_envelope.py` → `results/e3_envelope.json`. Per-station models, raw across-station
median reference, scenario D, 20 resampled trials per point. Turns the single operating
point into something Section 8.1 can quote.

**Event amplitude**, as a fraction of the [0,1] channel range, 60 events fixed:

| amplitude | 0.02 | 0.04 | 0.06 | 0.10 | 0.15 | 0.25 |
|---|---|---|---|---|---|---|
| detection | 0.05 | 0.05 | 0.10 | 0.50 | 0.75 | 0.95 |
| AUROC | 0.514 | 0.574 | 0.673 | 0.866 | 0.953 | 0.999 |
| z median | 0.32 | 0.41 | 0.64 | 2.60 | 6.52 | 10.76 |

Sharp knee between 0.06 and 0.10. Below 0.06 of channel range the channel is dead; at and
above 0.15 it is close to certain.

**Number of coupled exchanges** in the observation window, amplitude 0.15 fixed:

| events | 10 | 20 | 40 | 60 | 90 |
|---|---|---|---|---|---|
| detection | 0.10 | 0.45 | 0.70 | 0.75 | 0.90 |
| AUROC | 0.759 | 0.852 | 0.929 | 0.953 | 0.992 |
| z median | 1.04 | 2.24 | 4.47 | 6.52 | 8.32 |

Also monotone, and it is the more operationally meaningful axis: the channel is a
correlation estimate, so it needs repeated exchanges rather than one dramatic one. A
single exchange is not detectable by this mechanism and the disclosure must not imply it
is. Useful from roughly twenty exchanges, strong beyond forty.

---

## What this does to the disclosure

**Rewrite §4.1(a)+(c)+(e).** The claimed synergy — that the cross-station coupling channel
exists *because* one normal-only model is shared, making residuals "numerically comparable
by construction" — is contradicted in direction, not merely unsupported. Filing it invites
refutation by the applicant's own mechanism, on a public MIT-licensed corpus, in under
five minutes of compute.

**Promote §4.1(f).** Common-mode rejection is now the load-bearing element and the only one
with measured support. It converts a miss into a detection.

**Claim 11 should recite per-station calibration and the across-station common-mode
reference, and should not recite that the model is shared.** A shared-model limitation is a
limitation this evidence argues against.

**The instrumented unoccupied reference station gets stronger.** With stations
independently modelled, the reference has to come from somewhere principled. The Tier-1
move the audit already chose now has a measured reason behind it, not only a
Section 3(k) one.

**The time-synchronisation limitation can now carry a number derived from measurement.**
Tier-1 item, previously asserted.

**Treat §8's simulated cross-station figures as suspect** (acoustic 0.468, EM 0.739,
behavioural 0.650, combined 0.810). They were produced under the shared-model assumption
on the inventor's own generator, and that assumption is the one just refuted.

**Section 3 additions** are drafted in `s3_additions.md`: GDN (AAAI 2021), CST-GL
(TNNLS 2023), common-mode instrumentation art (Rost & Thomas 2002, EEG common-average
referencing, instrumentation-amplifier CMRR) and TranAD (VLDB 2022), each in
discloses / does-not-disclose form, plus the §4.1(f) concession rewrite.

---

## Reproducing

```
kaggle-free; data is a sparse git clone
  git clone --depth 1 --filter=blob:none --sparse \
      https://github.com/NetManAIOps/OmniAnomaly.git omni
  cd omni && git sparse-checkout set ServerMachineDataset

export SMD_DIR=<...>/omni/ServerMachineDataset      # or edit the default in e3_smd.py

python -u e3_smd.py        # E3(i)   ~3 min, writes results/ + shared/local model caches
python -u e3_coupling.py   # factorial, single trial   ~3 min
python -u e3_repeat.py     # 20 trials + skew sweep    ~4 min
python -u e3_envelope.py   # amplitude / event-count envelope
```

`e3_coupling.py` writes `results/shared_model.pt` and `results/local_models.pt`; the later
scripts load them, so every trial uses identical predictors and only the injection varies.
Delete the caches to retrain. `E3_HID`, `E3_EPOCHS`, `E3_W`, `E3_TAG` and `E3_TRIALS`
override the defaults for sensitivity runs.

## Still open

- **Amplitude sensitivity of the E3(i) refutation.** The shared model was 128-wide, 5
  epochs, on 417k windows. A fair objection is that it was too small to fit 17
  heterogeneous machines. Re-run with `E3_HID=384 E3_EPOCHS=12 E3_TAG=_big` before the
  finding is quoted as final. The direction is unlikely to reverse — sharing widened
  residual spread rather than narrowing it — but the objection should be closed.
- **Detection rate is a strict top-1-of-55 metric.** 0.60 at the operating point. Whether
  persistence across windows lifts it is untested; do not claim it.
- **Injection is synthetic.** Real cross-station coupling is not available in any public
  corpus. The venue-wide and pair-coupled events are constructed, and the write-up must
  say so wherever a number is quoted.
- **E1** (real physical acoustic anomaly corpus, normal-only) and **E2**
  (`jennylandes/eye-tracking-dataset-academic-reading`, 55-column protocol only, never
  pool protocols) are not started.
