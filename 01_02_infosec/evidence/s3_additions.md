# Section 3 additions — Label-Free disclosure

Drop-in rows for the Section 3 prior-art table, in the existing column format
`No. | Reference | Year / type | Core contribution | Limitation with respect to the present invention`,
plus the connecting-prose amendments they require.

Rationale. The table's machine-learning band (entries 12–17) contains **no graph or
inter-channel-correlation art and nothing after 2018 except two representation-learning
papers**. The cross-station coupling channel of Claims 11 and 17 is the disclosure's
strongest position, and the art closest to it is absent. An examiner will supply it. Better
to supply it first, in discloses / does-not-disclose form, and own the distinction — the
structural move the reference filing used successfully.

Entry 20 answers the audit finding that common-mode rejection is asserted as a precondition
in §4.1(f) without any instrumentation art cited against it, while carrying both cross-station
independents.

---

> **Drafting note added 2026-09-01.** Earlier drafts of these rows distinguished the prior
> art by reference to *one normal-only model shared across the stations*. The E3
> measurements (`evidence/README.md`) refuted that arrangement, and the wording above has
> been corrected to the arrangement actually supported: predictive models established
> **separately at each station**, a venue-wide common component removed before coupling is
> computed, at least one instrumented unoccupied station supplying part of that reference,
> and a bounded inter-station timing tolerance. Do not reinstate the shared-model language
> anywhere in Section 3, Section 4.1 or the claims — see `evidence/s4_claim_rewrite.md`.


## New table rows

**18**
| Reference | Deng and Hooi — graph neural network-based anomaly detection in multivariate time series, Proceedings of the AAAI Conference on Artificial Intelligence, 35(5), 4027–4035 |
|---|---|
| Year / type | 2021 / conference |
| Core contribution | Learns a graph over the channels of a sensor installation from the data itself, embedding each sensor and connecting it to the sensors whose behaviour best predicts it. A forecast is made for every channel from its learned neighbours, and the deviation between forecast and observation is the anomaly score. Graph attention weights identify which sensor deviated, permitting root-cause attribution. Evaluated on water-treatment installations. |
| Limitation with respect to the present invention | Discloses learned inter-channel structure, a prediction-deviation score, and per-channel attribution. The nodes are channels of one instrumented process, in which correlation between nodes is the normal and expected structure and an anomaly is a departure from it. The present invention inverts that premise: the nodes are separately occupied stations that are expected to be mutually uncoupled while sanctioned activity is in progress, so a lagged coupling that persists is itself the detection rather than the learned baseline. The reference does not disclose the derivation of a coupling statistic between nodes whose predictive models are established separately at each node; does not disclose estimation and subtraction of a venue-wide component before pairwise coupling is evaluated; and does not disclose an instrumented station held unoccupied to supply that reference. |

**19**
| Reference | Zheng, Koh, Jin, Chi and others — correlation-aware spatial-temporal graph learning for multivariate time-series anomaly detection, IEEE Transactions on Neural Networks and Learning Systems (arXiv:2307.08390) |
|---|---|
| Year / type | 2023 / journal |
| Core contribution | A multivariate time-series correlation learning module infers pairwise correlations between series, over which a spatial-temporal graph neural network is built; graph convolution exploits one-hop and multi-hop neighbour information. Detection is evaluated at a configurable set of temporal delays, so that a disturbance propagating between nodes can be caught earlier than at zero lag. |
| Limitation with respect to the present invention | The closest reference to the cross-station embodiment and is acknowledged as such. It discloses pairwise correlation learning between separately sensed series and explicitly evaluates correlation at a configured set of non-zero delays, which is conceded to correspond to the time-lagged coupling step of the present invention taken by itself. What it does not disclose is the arrangement in which that step becomes meaningful: the nodes are channels of a single monitored process whose mutual correlation is the modelled norm, whereas here the nodes are independently occupied stations for which mutual coupling has no legitimate cause; a venue-wide common component is neither estimated nor removed, so a disturbance reaching every node at once would present as correlation at every edge; there is no unoccupied instrumented node supplying a reference; there is no requirement that the several nodes carry physically independent transducers rather than derived quantities of one instrument; and no bound is placed on the inter-node timing tolerance within which a lag is resolvable. |

**20**
| Reference | Common-mode suppression across sensor arrays — representative: Rost and Thomas, array seismology: methods and applications, Reviews of Geophysics, 40(3) (doi 10.1029/2000RG000100); together with common-average referencing in multichannel electroencephalography and common-mode rejection in differential instrumentation amplifiers |
|---|---|
| Year / type | 2002 and earlier / review and general practice |
| Core contribution | Where several like sensors observe a shared environment, a component common to all channels is estimated — by summation and beam-forming across the array, by referencing each channel to the average of all channels, or by differential measurement — and suppressed, so that the component peculiar to one channel or to one direction of arrival can be resolved above it. Long-established practice across seismology, electrophysiology and analog instrumentation. |
| Limitation with respect to the present invention | Cited by the applicant, not against it. Common-mode suppression as a technique is conceded to be ordinary and no protection is sought for it as such. In every cited practice the array observes one field and the common component is instrument or environmental noise on a physical measurement. Here the quantity referenced across the array is not a measurement but the **prediction residual of a model established separately at each station**, and the reference is formed across stations that are otherwise modelled independently, one of which is held unoccupied for the purpose. The suppression step is applied not to improve the estimate of a single-station quantity but as a precondition for a relational quantity, the pairwise coupling between stations, that does not exist at any single station. Neither the cited practice nor the assessment-integrity art at entries 1 to 11 teaches that combination. |

**21**
| Reference | Tuli, Casale and Jennings — TranAD: deep transformer networks for anomaly detection in multivariate time series data, Proceedings of the VLDB Endowment, 15(6) |
|---|---|
| Year / type | 2022 / conference |
| Core contribution | A transformer encoder-decoder trained on normal multivariate sequences, with self-conditioning on a first-pass reconstruction and an adversarial second stage that amplifies small deviations. Reports anomaly scores from reconstruction error on nine public multivariate corpora. |
| Limitation with respect to the present invention | Included so that the general prediction-error art is represented at its current state rather than at its 2018 state. Single-instance and offline in the same sense as entries 12 to 14: no per-venue calibration under non-stationary ambient conditions, no fusion across heterogeneous physical modalities, and no teaching of a relational quantity computed between separately deployed instances. The present invention is deliberately agnostic to which such predictor is used; the contribution claimed lies in the arrangement around it. |

---

## Connecting-prose amendments

**In the paragraph following the table** (currently begins *"The general techniques at entries 12 to 17 supply components but not the invention"*), extend the band and add the graph paragraph:

> The general techniques at entries 12 to 17 and 21 supply components but not the invention.
> […existing sentence retained…]
>
> Entries 18 and 19 require separate treatment, because they are the only prior art that
> derives a relational quantity between separately sensed streams and they are therefore the
> closest art to the cross-station claims. Both learn a structure over nodes and score
> deviation from it, and entry 19 evaluates correlation at configured non-zero delays. The
> correspondence is conceded rather than minimised. The distinction is one of premise. In
> both references the nodes are channels of a single instrumented process, mutual correlation
> between them is the normal structure that the model is built to learn, and an anomaly is a
> departure from that learned correlation. In the present invention the nodes are separately
> occupied stations at which sanctioned activity gives rise to no mutual coupling whatever, so
> that a coupling which persists after the venue-wide component has been removed is not a
> departure from the model but the detection itself. That inversion is what makes the further
> elements necessary rather than optional: a common normal-only model applied station by
> station, because residuals scored by separate station-specific models are not comparable and
> cannot be correlated; an estimate of the component common to the whole venue, because
> stations share a room and the most frequent cause of simultaneous residual elevation is an
> event common to it; an instrumented station held unoccupied, because that estimate needs a
> reference that carries no candidate; and a bound on inter-station timing tolerance, because
> a lag of one to three seconds cannot be resolved by clocks that disagree by more than a
> fraction of it. None of entries 1 to 21 discloses any of those four, alone or in
> combination.

**In §4.1(f)**, the common-mode element currently asserts the precondition without conceding
the technique. Replace the opening of that element with a concession in the same register as
the §3 entry 20 row:

> Estimating and subtracting a component common to an array of like sensors is ordinary
> instrumentation practice and is not claimed as such. What is claimed is its application to
> the prediction residual of a model shared across the stations rather than to a physical
> measurement, and as a precondition for a relational quantity between stations rather than
> as an improvement to a single-station one.

Reason: the audit finding stands — element (f) carries both cross-station independents, and an
unconceded assertion that a standard technique is a precondition invites the examiner to answer
it with the first instrumentation textbook to hand. Conceding it costs nothing, because the
element that does the work is what the reference is formed **from**, not the act of forming it.

---

## Not added, and why

- **mTADS / GutenTAG** (synthetic multivariate anomaly benchmark suites) — a data generator, not
  a detection teaching. Belongs in §8 as the provenance of any synthetic ablation, not in §3.
- **TSAD benchmark toolkits** — evaluation harnesses. Same reasoning.
- **Exathlon** (VLDB 2021) — a benchmark corpus. Same reasoning, and its CC BY-NC-SA 4.0 licence
  makes it unattractive to lean on for a commercially intended filing.

---

## Entry 8 — REMOVE FROM THE TABLE (resolved 2026-09-01)

Aditya has confirmed that entry 8, *"Multi-sensor examination desk with acoustic and
electromagnetic signatures (base disclosure)"*, is **his own earlier work and was never
publicly disclosed**.

Two consequences, and they point the same way.

**It is not prior art.** Under section 2(1)(l) an invention is new unless anticipated by
publication or public use. Work that was never made available to the public anticipates
nothing, and one's own undisclosed work is not citable against oneself. Section 12 Fifth
of the disclosure ("no public disclosure") is therefore correct as written.

**Leaving it in Section 3 manufactures prior art that does not otherwise exist.** The
table's type column currently reads `prior / disclosure`, and the limitation column
concedes that the base disclosure teaches desk-embedded acoustic and electromagnetic
sensors with decisions taken by thresholds or learned models. That is an **applicant
admission**, made in the applicant's own specification, characterising the applicant's own
unpublished work as prior. Admitted prior art is available against the applicant in a way
that unpublished work never is. The entry gives away, for nothing, the two sensing
modalities that Claims 3 and 4 depend on.

**Action.** Delete entry 8 from the Section 3 table and renumber entries 9 to 17 (and the
new 18 to 21) accordingly. Every cross-reference to the entry numbers in the prose after
the table, in Section 4.1, and in Section 12 Second must be repointed — Section 12 Second
currently refers to "entries 12 to 17", which becomes 11 to 16 before the new rows are
added.

Record the development history where it belongs, in **Section 12 (internal, not filed)**:

> The subject matter of this disclosure develops earlier unpublished work of the same
> inventor on a multi-sensor examination desk carrying acoustic and electromagnetic
> sensing. That earlier work has not been published, exhibited, demonstrated outside the
> institution, or otherwise made available to the public, and no application has been filed
> in respect of it. It is accordingly not prior art and is not listed in Section 3. It is
> recorded here so that the Cell has the development history, and so that any decision to
> disclose or publish it is taken with knowledge of the effect on this application.

**Still to confirm with the inventor**, because "not disclosed" and "not filed" are
different questions with different consequences: whether any patent application was ever
filed on the base disclosure. An earlier application, even one not yet published, is
citable under section 13(1)(b) as prior claiming and is relevant under section 29. If one
exists the strategy changes; if none does, the position above holds unchanged.

**And a checklist worth walking**, because the things that count as public disclosure are
broader than people expect and a single slip destroys novelty worldwide with no grace
period in most jurisdictions: a conference paper, poster or abstract; a project exhibition,
demo day or open house; a thesis or project report deposited in a library or institutional
repository; a public code repository; a preprint; a video; a product demonstration to
anyone outside a confidentiality obligation; a funding application that becomes public.
Internal submission to the VIT IPR and TT Cell is not disclosure — that is a confidential
institutional channel.
