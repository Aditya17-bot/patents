# Proposed claim restructure — 2026-09-22

## The problem

The claim set puts the surviving distinction in a dependent position under a parent the
project's own analysis rates as met.

| Claim | Directed to | Art position |
|---|---|---|
| 1 (independent) | chronic bias decomposition | **met** — power-system network *parameter error* identification, Liu/Wu/Lun 1992, Zhu/Abur 2006 (Phase 12) |
| 6 (independent) | fault onset from residuals | **met** — Narasimhan & Mah 1987; §12 already concedes "not available however it is worded" |
| 9 (dep. on 6) | class-transfer fault | **met in general form** — Bagajewicz equivalency theory, bilinear reconciliation (§5b) |
| **5 (dep. on 1)** | **nodes and slip signs from counts alone, no network map** | **not found** — §7 searches (a)–(d) |
| 10–12 (dep.) | certified bounds on hard-constrained reconstruction | narrow; §10.4 records the band as unsupported on accuracy |

Claim 5 is the one element that survived four adversarial searches. It currently depends
on claim 1. If claim 1 falls, claim 5 falls with it — so the strongest asset is carried by
the weakest parent.

## The move

Promote the count-derived constraint structure to an independent claim, drawn to the
*combination* searched in §7 — discovery from counts, selection by measured residual
tightness, and reuse of the discovered relations as the hard constraints on the same
dataset. Not to the sparse regression, which SINDy makes old in the abstract.

## Proposed new independent claim

> A computer-implemented method of validating a dataset of vehicle counts produced by a
> network of vehicle-counting detectors of undocumented topology, comprising:
>
> receiving a dataset of vehicle counts indexed by detector and by measurement interval,
> and receiving no network map;
>
> selecting, by a measure of correlation between detector count series, a shortlist of
> candidate detector subsets;
>
> fitting, for each candidate subset, coefficients of a linear relation among the counts
> of that subset, and rounding the fitted coefficients to the nearest integers within a
> tolerance, whereby a candidate relation expresses conservation of vehicles among the
> detectors of that subset with signed coefficients denoting direction of flow;
>
> retaining a candidate relation as a validated conservation relation only if the measured
> spread of its residual is small relative to the flow recorded at its detectors, and
> discarding it otherwise;
>
> deriving, for each retained relation, a two-sided tolerance band from the measured spread
> of that relation's own residual;
>
> and thereafter imposing the retained relations upon the same received dataset as hard
> two-sided inequality constraints of the said bands, so as to reconstruct an absent record
> by projecting a prior estimate onto their intersection, and reporting as irreconcilable
> any node and interval for which the said intersection is empty;
>
> whereby the constraint set against which the dataset is validated is derived from that
> dataset itself, and the validation is performed without receipt of a network map, a
> junction database or a detector naming convention.

Five-part structure per the drafting rules: receive specified data → named transformation
with physical rationale (integer-rounded signed coefficients = conservation with direction
of flow) → hard constraint (two-sided bands as hard inequalities, not a penalty) →
dataset whose improvement is measurable → downstream technical action (reconstruction;
irreconcilable-node reporting).

## Measured support, and its limit

Traces to §11.4 and `results/discovery*.json`:

- **147 of 199** surveyed relations (73.9%) recovered exactly, no map supplied
- **75.4%** of surveyed relations lie in the span of the recovered set
- Greedy matching-pursuit was implemented first and **replaced after measurement** — the
  best single explanation for a mainline detector is always the next mainline detector, so
  slip-road relations were never surfaced. A design decision forced by measurement.

**Stated against the claim, per §10.2:** discovered relations do **not** outperform the
surveyed topology. The earlier 18-node result (MAE 18.52 vs 21.05) reversed at 199 nodes
and is withdrawn as a small-sample artefact. So the technical effect claimed is a
**capability, not an accuracy gain**: the dataset's integrity can be checked on a detector
network whose topology is undocumented, which no cited method can do. Combining recovered
with surveyed relations gives the lowest error of any configuration tested, at the cost of
a weaker consistency guarantee — a trade-off, claimed as one.

## Consequent renumbering

- New claim 1 — above.
- Claim 1 (chronic) becomes an independent claim in second position, retained as the first
  fallback, unchanged in substance.
- Claim 6 (onset) unchanged, still marked the more exposed.
- Claims 10–12 become dependent on the new claim 1 as well as on the old ones, since the
  reconstruction they certify is what the new claim 1 already recites.
- Claim 5 is absorbed into new claim 1 and deleted as a dependent.

## Not resolved

Espacenet and InPASS unrun. de Souza (2019) still unread in full text. Absence of evidence
across four searches is not proof of absence.
