# Label-Free disclosure — new independent claims, drafted against the search

Purpose. The Cell screens by counting how much prior claim language resembles yours. So
these are drafted to minimise the number of prior claims that read on them — not by adding
adjectives, but by reciting **structure and relations that no located reference recites at
all**. Every element below is either a physical thing nobody has claimed, or a relation the
E3 measurements support.

Not drafted by a registered agent. A patent agent must review before filing.

---

## What the search says is unclaimed

Located art, from the Section 3 table plus the additions in `s3_additions.md`:

| Family | What it claims | Where the nodes' correlation sits |
|---|---|---|
| ProctorU `US20190156689A1`, `US9154748B2`, `CN106023516A`, `CN111539313A`, `US11917324B2` | one candidate, one station, supervised or rule-based, software alert or session suspend | no cross-candidate relation at all |
| Wollack 1997; Belov & Wollack 2021 | similarity between completed answer vectors, graph over examinees, connected components | post-hoc, on answers, after the exam |
| GDN (AAAI 2021), CST-GL (TNNLS 2023), MTAD-GAT | learned correlation graph over the channels of **one** process, lagged delays, deviation from learned structure | correlation is the **normal** structure; anomaly = departure from it |
| Seismic arrays, EEG common-average, instrumentation CMRR | estimate and subtract the component common to an array | on **physical measurements**, one field, to clean a single-channel estimate |

Four things none of them recites:

1. **A station deliberately instrumented and held unoccupied**, whose output forms part of
   the reference. Analogues exist in other fields — a dark reference in spectroscopy, a
   dummy electrode, a reference geophone — and that class should be conceded. In an
   assessment context, on residuals, there is nothing.
2. **Predictive models established separately at each station, combined with a reference
   formed across stations.** Counter-intuitive; a skilled person shares the model. E3
   measured that sharing destroys the channel (AUROC 0.983 station-local, 0.516–0.559
   shared, zero detections in 20 trials).
3. **The inverted null**: the coordination condition is satisfied by coupling that
   **exceeds a baseline measured at that same station pair during sanctioned activity**.
   Every graph reference treats correlation as the learned norm; here the pair is its own
   control and any surviving coupling is the detection. Also label-free by construction,
   which is the disclosure's whole premise.
4. **Structural numeric relations**: a timing tolerance bounded by the shortest evaluated
   lag, and a requirement of several separate coupled events rather than one.

The combination 1 + 2 + 3 is, on the search performed, unclaimed anywhere.

---

## Independent Claim A — venue apparatus

Drafted first and deliberately as **apparatus**, because apparatus claims are searched on
structure, and there is no structure like this in the art. This is the claim with the
fewest prior claims reading on it.

> **Claim A (independent).** An examination-venue integrity installation, comprising:
>
> a plurality of candidate stations, each comprising a station body and a sensing assembly
> mechanically carried by that station body, the sensing assembly of each station
> comprising at least one acoustic transducer and at least one further transducer of a
> different physical modality;
>
> **at least one reference station comprising a station body and a sensing assembly of like
> construction to that of the candidate stations, disposed among the candidate stations
> within the venue and configured to remain unoccupied throughout a monitored session;**
>
> a time-synchronisation arrangement establishing a common time base across the sensing
> assemblies of the candidate stations and of the reference station, to within a
> predetermined timing tolerance;
>
> and a processing arrangement configured to derive, for each said station, a
> prediction-residual series from the signals of that station's sensing assembly by means
> of a predictive model and standardisation statistics **established at that station** from
> an interval of sanctioned activity, to form from the residual series of the stations,
> **including that of the reference station**, a venue-common component, to subtract that
> component from the residual series of each candidate station, and to evaluate a
> time-lagged coupling statistic between the corrected residual series of pairs of
> candidate stations over a set of lags the shortest of which is not less than twice the
> said timing tolerance.

Why it is hard to hit. An examiner searching apparatus claims must find an installation
that recites an unoccupied like-instrumented station as a structural element. Nothing in
the assessment-integrity art has one. Nothing in the graph-anomaly art has stations at all.
The seismic and EEG references have reference sensors but no candidates, no venue, no
residuals and no predictive model.

## Independent Claim B — the inverted null

The characterising relation, claimed on its own so that it survives even if Claim A is
narrowed on the structure.

> **Claim B (independent).** A system for detecting coordinated malpractice between
> candidates at an examination venue, comprising a plurality of monitored stations each
> associated with a sensing assembly, and a processing arrangement configured to:
>
> generate for each station a prediction-residual series by means of a predictive model
> trained on sanctioned activity, the model and its standardisation statistics being
> established separately for each said station;
>
> subtract from the residual series of each station a venue-common component derived from
> the residual series of a plurality of the said stations;
>
> **establish, for each pair of stations and during an interval of the session in which
> activity is sanctioned, a baseline value of a time-lagged coupling statistic between the
> corrected residual series of that pair;**
>
> evaluate the said coupling statistic for that pair during a subsequent interval of the
> session; and
>
> **indicate coordinated malpractice for a pair only when the coupling statistic for that
> pair exceeds the baseline value established for that same pair by a predetermined margin,
> on each of at least a predetermined number of separate occasions within the session.**

Two things are doing work here and both are supported. The pair being **its own control**
removes the room's fixed geometry, the pair's seating distance and any standing coupling
from the decision, which is what makes the condition label-free rather than threshold-set.
The **repetition requirement** is not a formality: E3 measured the coupling statistic as an
estimate that needs repeated exchanges — ranking accuracy 0.759 at ten coupled events,
0.852 at twenty, 0.929 at forty, 0.992 at ninety. A single exchange is not detectable by
this mechanism, and a claim that implied otherwise would be unsupported.

## Independent Claim C — physical response

Every claim in the present set ends in an alert. This one does not, and it is the reason to
draft it. The response is deliberately modest and real — reconfiguring acquisition to
gather better evidence on the implicated pair — rather than an invented actuator.

> **Claim C (independent).** An examination-venue integrity installation comprising a
> plurality of candidate stations each carrying a sensing assembly operable in a first
> acquisition state and in a second acquisition state, the second acquisition state
> differing from the first in at least one of sampling rate, number of transducers enabled,
> and directional selectivity of acquisition; at least one like-instrumented station held
> unoccupied within the venue; and a processing arrangement configured to derive
> station-local prediction residuals, to remove a venue-common component formed using the
> residual of the said unoccupied station, to evaluate a time-lagged coupling statistic
> between pairs of candidate stations, and, upon the coupling statistic for a pair
> satisfying a coordination condition, **to switch the sensing assemblies of the two
> stations of that pair, and of no other station, from the first acquisition state into the
> second acquisition state for a bounded interval.**

Why this matters beyond drafting neatness. The contribution stops being "a better score"
and becomes a change in the physical operating state of apparatus, brought about by a
measured relation between two physically separate transducer sets. That the change is
confined to the implicated pair and bounded in time is also the privacy answer: the
installation runs in the low-rate state by default and only the pair under suspicion is
sampled harder.

**Do not import the CausalInterlock enforcement here.** That disclosure interrupts the
keyboard data path. Keeping the two filings apart matters — see the cross-filing note in
`CLAUDE.md`. Re-tasking acquisition is a different technical effect and keeps the boundary
clean.

## Independent Claim D — method

> **Claim D (independent).** A method of distinguishing coordinated malpractice from
> coincidental anomaly at an examination venue having a plurality of instrumented
> candidate stations and at least one like-instrumented station held unoccupied, the method
> comprising: establishing at each station, from an interval of sanctioned activity at that
> station, a predictive model and standardisation statistics for that station; generating
> at each station a standardised prediction-residual series; forming a venue-common
> component from the residual series of a plurality of the stations and of the said
> unoccupied station and subtracting it from each candidate station's residual series;
> evaluating a time-lagged coupling statistic between pairs of corrected residual series
> over lags exceeding the timing tolerance to which the stations are synchronised;
> attributing an elevated residual at a single station, unaccompanied by coupling to any
> other station, to an individual anomaly; and attributing coupling between a station pair,
> persisting over a plurality of separate occasions and exceeding that pair's own
> sanctioned-activity baseline, to coordination between the candidates at those stations.

The final two steps are the discrimination the whole disclosure exists to perform, and no
located reference performs it: the art either scores individuals and never relates them, or
relates them after the fact from their answers.

---

## Dependents worth keeping, and why

Each is a fallback position if an independent is narrowed.

- the venue-common component is a **median** across stations at each sampling instant —
  measured best of three rules (0.983, against 0.920 for a per-station-standardised median
  and 0.632 for none)
- the timing tolerance does not exceed **one half** of the shortest evaluated lag —
  measured 0.987 at that setting, 0.981 at one times, 0.954 at one and a half times
- the reference station's sensing assembly is **identical in construction** to the
  candidate stations'
- **two or more** unoccupied reference stations at spaced positions
- the acoustic transducer's output is reduced to an **envelope** before digitisation, so
  that what leaves the station cannot be reconstructed into speech
- coupling statistics assembled into a **graph**, connected components identifying groups
  of more than two — concede this one first if pressed; Belov & Wollack 2021 is close
- per-modality coupling statistics combined by weights from the sanctioned interval

## What to drop

- **The CRM claim (present Claim 23).** Routinely refused in Indian practice, and it
  contradicts the framing. Deleted from CausalInterlock on 2026-08-28 for the same reason.
- **"trained exclusively on … no labelled instance of malpractice"** as a limitation inside
  a system claim. It is a product-by-process recitation not detectable in a deployed
  system. Keep the label-free property as a described advantage; make the claim recite the
  runtime-inspectable thing instead — per-station, per-session calibration from a sanctioned
  interval.
- **The shared-model language everywhere.** Refuted by E3. See `s4_claim_rewrite.md`.

---

# Reaching TRL 4

Present rating is TRL 3, experimental proof of concept, and that is honest. **The E3 work
does not by itself confer TRL 4.** TRL 4 is component or breadboard validation in a
laboratory environment; E3 validated the signal-processing arrangement on a public server
-telemetry corpus, which is a proxy of the right shape and the wrong physics. No acoustic
transducer, no electromagnetic sensing, no desk, no candidate was involved. Relabelling
without a build would not survive a question from the Cell.

What TRL 4 requires is a breadboard of the actual components on a bench, producing measured
numbers from real hardware.

## Minimum build

Five nodes: four candidate stations and **one held unoccupied** — the unoccupied node is
not optional, it is the element Claims A, C and D turn on. Per node: the Knowles
SPH0641LU4H-1 MEMS microphone already specified in Section 9, an ESP32-S3, and an
accelerometer for the second modality. One Raspberry Pi 5 aggregator.

Synchronisation is the cheap surprise. E3 measured the tolerance as roughly half the
shortest evaluated lag; with a coupling lag of one to three seconds that is a tolerance of
hundreds of milliseconds, which plain SNTP over the local network meets with room to spare.
No 1PPS hardware, no GPS discipline.

## Bench tests

| | Test | Validates | Why it is needed |
|---|---|---|---|
| B1 | residual series generated from real node audio and accelerometry, normal-only training per node | the residual chain on real transducers | nothing in E3 used a microphone |
| B2 | station-local versus shared model, on the five real nodes | the E3(i) refutation, on hardware | turns a proxy result into a component result |
| B3 | staged venue-wide event (door, announcement, chair scrape) across all five nodes; suppression measured with and without the unoccupied node in the reference | Claim A and Claim C's reference element | the only test that shows the unoccupied station earns its place |
| B4 | two confederates exchanging whispers or taps at controlled lag; coupled pair against the other five pairs | Claims A, B, D | first real coupling, replacing injection |
| B5 | per-pair sanctioned-activity baseline measured and its stability over a session | Claim B's inverted null | the baseline must be stable or the claim fails |
| B6 | node clocks deliberately skewed; degradation curve reproduced | the timing tolerance dependent | confirms the measured envelope on hardware |
| B7 | **two to three hour sanctioned session, no coordination, false-alarm rate per pair-hour** | everything | the number that does not exist yet, and the first thing a sceptical reader asks |

B3, B4 and B7 are the ones that matter. B7 in particular: E3 used eleven stations and
fifty-five pairs; a real hall of a hundred desks is about five thousand pairs, and the
false-alarm rate per pair has never been measured. Do not write a TRL 4 claim without it.

Passing B1 to B7 supports **TRL 4** and no more. TRL 5 needs a real hall during a real
examination, which is a different approval problem.
