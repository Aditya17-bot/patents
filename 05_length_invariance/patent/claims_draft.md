# Claims - decisions (updated 2026-09-29, claims-strengthening pass)

The claim text of record is in `src/make_idfb.py` (`CLAIMS_A`, `CLAIMS_B`) and in the built
IDF-B, Section 10. This file keeps the reasoning.

Set: 1 independent method claim, 4 dependents (2-5), 1 independent system claim (6) with 1
dependent (7).

| Claim | What it adds | Evidence |
|---|---|---|
| 1 | receive; slip-free pairs admitted by total balance; share differences per boundary; chain biases per boundary (median or verified reference); stream CDF interpolated from class shares; offset d relative to the chain reference; **cross-boundary test: d predicts the bias at every other boundary with no fitted parameter; pass = length-offset fault, fail = other fault**; per-boundary reclassification, totals kept; archive; fault class for every unit, offset as sensitivity correction only for length-offset faults | probe, E1, E2, E8, **E9** |
| 2 | refit each period | E5 |
| 3 | dated equal-and-opposite steps | E3, E8 events |
| 4 | live correction | E1 |
| 5 | speed attribution for length-offset units | E8 speed |
| 6 | system incl. offset estimator 350 and fault classifier 360 | Section 7 |
| 7 | loop pairs per lane | Section 7 |

## Why the cross-boundary test went into claim 1

External review (ChatGPT, filtered) plus own search: the obvious-combination attack is
stronger than thought. US 6,876,949 (entry 11) alone teaches (i) a length error shifts the
vehicle population distribution and is calibrated out by matching it to a standard, and
(ii) normalising detectors against each other with the same (re-identified) vehicles.
Wall & Dailey (entry 3) teaches slip-free pairs, count balance, reference station and
archive correction (volumes). With entry 1, "offset from the length distribution via
neighbours" (old claim 1(e)) looks obvious on its own.

What none teaches, and what binned class counts allow: one offset, fixed at one boundary,
predicts the bias at every other boundary through the stream's own density, with no
fitted parameter. A unit that fails has a fault that a sensitivity retune will not cure.
E9 evidence:
- field: predicted vs solved 660 cm bias r = 0.81-0.92, 54-78 % of variance, all 8
  corridor-months; failing units persist Mar to Jun (M25 12 of 15, M1 26 of 36);
- injection (April): 660 cm boundary fault +-100 cm turns 67-99 % of passing units
  failing; 1160 cm +-150 cm only 48-58 % (weak, stated); a true 40 cm offset stays passing
  81-95 %;
- reference: moving a whole chain by a common 30 cm changes 1 of 544 unit tests (272 units, both signs), so the test
  does not depend on the unknown chain constant;
- agreement with the old principal-direction test 95-98 %; that test kept as an
  alternative embodiment only (fitted, not predicted).

## Identifiability (external review point, accepted)

The offset is relative to the chain reference (median or verified site). Claim 1(d), (f)
now say so; the description says differences between units are physical and the common
level is absolute only with a verified reference. Not a separate claim (not measured).

## Not taken from the external review

- Statements about Lu, Yang & Chang (2014): unverified (closed access); kept "not read".
- Scores out of 10: not evidence.
- Old claim 5 (principal-direction fault class): dropped, replaced by the predicted test.

Honest limits kept in the document: prediction at 660 cm runs high (slope 0.65-0.96);
1160 cm detection weak; offsets not compared with measured lengths; correcting from the
single offset is worse than per-boundary.

## Self-review changes (sixth pass)

- Claim 1(f) prediction is now first order: bias at the first boundary times the ratio of
  the CDF slopes at the two boundaries. The exact nonlinear form, with the correct sign,
  depended on the unobservable CDF shape between boundaries and fitted poorly (M1).
- Evidence for the single-offset structure is now the standardised share against a
  shuffled null (66-79 % vs <= 44 %) and r(520, 660); the raw 97-99 % is not evidence.
- Claim 3 classifies each dated change with step (f): 6 of 8 changes are offset changes.
- Held-out cross-junction validation (E10): positive on M25, weak on M1, stated as a limit.

## 2026-09-30 - claim 5 added (8 claims)

Claim 5 (new): transmit over link (130) to the detector card (111) of each detector with a
length-offset fault a sensitivity correction shortening each computed length by its
offset; refit that detector from intervals after the correction takes effect. Speed
attribution renumbered 6; system claims 7 and 8. Numeric fallbacks are supported by
Table 4 (claimed function vs example implementation) rather than extra claims.
