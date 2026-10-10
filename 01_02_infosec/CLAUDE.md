# patent_InfoSec — working notes

Patent drafting workspace. Indian patent disclosures in **VIT IDF-B format**.
Owner: Aditya (aditya17sep@gmail.com).

## What is in this folder

| File | What it is |
|---|---|
| `IDF-B-Project1-Group05.pdf` | **Reference filing that PASSED stage 1.** 56 pp, wearable obstacle-warning apparatus. The style/rigour target. |
| `SKILL (2).md` | `patent-section-builder` skill — Frameworks 1–4 (Sections 6/7/8, refinement, patentability audit). |
| `patent-draft-builder-SKILL.md` | `patent-draft-builder` skill — Sections 1–5 and 9. |
| `writing-guidelines.md` | Banned phrases, sentence-variation rules, numeric-specificity rules. |
| `section_3k_compliance.md` | Indian Patents Act §3(k) — what fails, what passes. |
| `physical-technical-compliance.md` | Physical-technical integration language patterns + per-domain hardware tables. |
| `dataset-strategy.md` | Kaggle search patterns per domain, quality criteria. |

## Hard rules carried over from the skills

- **Never write "Section 3(k)" into the patent body.** Compliance is baked into framing, never cited.
- The invention must read as a **cyber-physical apparatus**, never "a method implemented in software".
- No banned filler: *leveraging, robust, seamlessly, state-of-the-art, cutting-edge, it is worth noting, in the realm of*. No paragraph starting with *Furthermore / Moreover / Additionally*.
- Every claim gets a number. `BAD: "high accuracy"` / `GOOD: "97.3% ± 0.8% across 1,200 cycles"`.
- Section 6 uses `[0001]` numbering; Section 7 continues it. Section 8 is plain prose, `FIG. X` / `TABLE X`.
- Figures: matplotlib only, ASCII-safe labels, `dpi=200` architecture / `dpi=300` data, captions **below**.
- Tables: `python-docx`, blue `#1565C0` header, alternating `#E3F2FD`. Not markdown, not PNG.
- Body text Times New Roman 11pt justified; headings 13pt bold.

## Why the reference filing passed — reuse this pattern

The novelty was deliberately **not** the detector or the model. It was the **control layer inserted
between detector and actuator**: an ordinal control value, a temporal output-control state machine,
and physical actuation. The document frames the invention as an *actuation control apparatus*.

Structural moves worth copying verbatim:

- §2.2 **Definitions** — every coined quantity defined by the sensor inputs it derives from *and*
  the actuator behaviour it determines ("Its function is ordinal… no protection is sought for the
  combination as a mathematical method in the abstract").
- Numbered **equations** + **reference numerals** (400, 700, 810…) used consistently across body
  text, figures and the parameter table.
- §3 prior-art table: state what the reference **discloses** first, then what it does **not**
  disclose. Expressly concede that the platform/components are not the point of novelty.
- §3.1 "Scope of Prior-Art Searching Still Required" — assert no final novelty determination.
- §4.3 Non-obviousness argued as **N specific consequences of the arrangement** that do not follow
  from the elements taken separately.
- §4.4 feature-vs-closest-art tick/cross matrix. §4.5 technical effects. §4.7 §3(k) position.
- §8.2 parameter table: default + permitted range + **the physical actuation behaviour it controls**.
- §8.10 "Scope and Limitations of the Reported Validation" — states honestly what was not tested.

## Current invention (chosen 2026-08-25)

**Causal Emission–Response Interlock** — desk-mounted cyber-physical examination-integrity node.

Kernel: cheating is detected as a **closed causal loop with an outside helper**, not as an appearance.

- photodiode on the display panel gives a *physical* question-onset anchor `T0` (not a software API event)
- desk-contact piezo attributes covert vocal emission to the **seated** candidate by structure-borne
  coupling (neighbour speech does not couple across the desk gap) → `T1`
- answer-commit `T2` must fall in a bounded external-assistance latency band **and** show
  input-dynamics discontinuity against the enrolled keystroke/mouse profile (transcribing, not composing)
- **one** desk inertial measurement applied at **two** points: lowers the vision detector confidence
  threshold under motion, and raises the acoustic attribution weight
- graduated enforcement ladder ending in an in-line HID unit physically opening the keyboard data
  lines; **dual-channel interlock** — no single modality may ever actuate hardware

Constraints from the user: must **not** reuse the framework of the earlier JEPA-based cheating
patent; must produce better results. Benchmark to beat: keystroke-only LLM-assist detection tops out
at **74.98–85.72 %** (arXiv 2406.15335).

### Reference numerals allocated

```
100 candidate station / desk assembly
200 display panel          210 photometric onset sensor
300 imaging sensor         310 gaze estimator      320 scanpath   330 pupillometry
400 desk-contact transducer  410 inertial unit     420 emission attribution unit
                             430 reliability-transfer unit
500 input-dynamics unit      510 enrolled profile store
600 causal latency interlock 610 assistance-band comparator  620 discontinuity comparator
700 corroboration value unit 710 eligibility comparator
800 graduated enforcement scheduler
    810 persistence counter  820 per-candidate cooldown  830 global session interval
    840 escalation comparator 850 dual-channel interlock
900 actuators: 910 desk indicator/haptic  920 in-line HID gating unit  930 session hold latch
950 evidence record store
```

## Datasets

Kaggle CLI installed and authenticated (`~/.kaggle/kaggle.json`). Working copies live in the session
scratchpad under `ds/` — re-download with `kaggle datasets download -d <ref> -p <dir> --unzip`.

| Ref | Role |
|---|---|
| `jennylandes/eye-tracking-dataset-academic-reading` | **Primary.** Real Tobii/iMotions exam recordings, labelled `Schummeln` (97) / `Nicht_Schummeln` (53), 16 participants, 5 questions. |
| `carnegiecylab/keystroke-dynamics-benchmark-data-set` | CMU DSL, 51 subjects × 400 reps × 31 timing features → enrolled profile + transcription discontinuity. |
| `malekzadeh/motionsense-dataset` | 50 Hz tri-axial accel + gyro, 24 subjects → desk inertial channel, real physical units. |
| `shreyp135/mouse-dynamics-dailyusage-data` | 1033 windows, speed/curvature → second input-dynamics channel. |
| `aneelapervez/yolo-exam-cheating` | Vision detector channel, exam-hall class inventory. Not yet pulled. |

### Eye-tracking export quirks (already solved in `et_load.py`)

- Three different header schemas across the 150 files (55 / 118 / 46 columns). `SlideEvent` is absent
  from the 46-column `*_edit.csv` files — guard for it.
- Numeric columns are **locale-mangled**: dots inserted as thousand separators into the digit string
  (`326.690.673.828.125` → `3.26690673828125` mm pupil). Recovery = strip dots, then place the decimal
  at the position that lands the value inside a per-column physical range.
- `Timestamp` is mangled the same way. Decode monotonically, then rescale so the median inter-sample
  step equals `ET_PERIOD_MS = 16.6546` (60.04 Hz). Trial duration then comes out at 69–93 s.
- `StartMedia` / `EndMedia` markers give the true stimulus onset/offset = the `T0` anchor.
- Tobii validity codes: `0` = valid, `4` = invalid.

## Scripts (in scratchpad, move into repo when stable)

```
et_load.py      loader, locale repair, clock reconstruction, T0 anchor
et_features.py  per-trial channel features        -> trial_features.csv, departure_events.csv
et_windows.py   20 s / 2.5 s sliding windows, all channels, protocol tag
                                                  -> windows.csv (4377 windows, 45 cols)
et_model.py     enrolment baseline + fusion + participant-disjoint CV
                                                  -> model_results.json, model_out.txt
channels.py     independent ocular / inertial / pupil scores for the interlock
                                                  -> windows_channels.csv, channel_results.json
scheduler.py    enforcement state machine + parameter sweeps
                                                  -> scheduler_trials.csv, scheduler_results.json
ks_layer.py     keystroke discontinuity, CMU DSL  -> ks_results.json
ms_layer.py     inertial channel, MotionSense     -> ms_results.json, ms_sit.npy
et_features.py  per-trial features (superseded by et_windows.py)
et_eval.py      early trial-level evaluation (superseded by et_model.py)
```

Run order: `et_windows.py` -> `channels.py` -> `scheduler.py`. `et_model.py`, `ks_layer.py` and
`ms_layer.py` are independent. `et_model.py` takes ~25 min; run it with `run_in_background` and
`python -u` (it buffers otherwise and you will see nothing).

```
```

`et_model.py` takes ~10 min — run it with `run_in_background`.

## STATUS as of 2026-08-26 — pipeline fixed, results honest, ready for a scope decision

All five blockers from 2026-08-25 are resolved. What changed:

1. **Causal-loop channel rebuilt** (`et_windows.py`). The old `d_ret` was dominated by trial
   length. Replaced with the geometry of consulting a fixed external source: exit-bearing
   concentration (`exit_R`), return-landing position and dispersion (`land_*`, `ret_disp_*`),
   bounded departure/return pairs (`pair_*`), and away-signal autocorrelation in the assistance
   band (`acf_*`). **The kernel went from AUC 0.443, the worst channel, to 0.723, among the best.**
2. **Head-motion qualification added** — the "one measurement, two placements" claim. A gaze
   departure counts only if the inertial channel corroborates that the candidate physically moved
   (`HEAD_QUAL = 0.5663`, the p90 of unassisted departure head-motion peaks). Validated
   independently: qualified-departure count alone lifts trial AUC **0.562 -> 0.659**.
3. **Protocol confound found and removed.** The corpus holds three incompatible export schemas and
   performance *reverses* across them: 55-col AUC 0.705, 46-col 0.498 (chance), 118-col **0.292**
   (inverted). The pooled number was partly detecting recording protocol. All ocular validation is
   now restricted to the 55-column protocol: 100 recordings, 11 candidates, 63 assisted / 37
   unassisted. `windows.csv` carries a `proto` column; never pool them again.
4. **Enrolment deviation dropped from the ocular model** — it measurably hurt (0.780 -> 0.713),
   because only 6 of 11 candidates had a usable baseline and the rest were fed zeros. Enrolment is
   retained as a mechanism where it demonstrably works: the keystroke layer.
5. **Question-onset phase structure tested and REJECTED** (AUC 0.485-0.519). Do not claim it.

### Where the numbers stand

**Ocular corroboration** (55-col protocol, participant-disjoint 5-fold CV):

| Channel | window AUC |
|---|---|
| C3 head motion (410) | 0.733 |
| **C2 causal loop (600)** | **0.723** |
| C1 gaze departure (310) | 0.710 |
| C5 scanpath (320) | 0.654 |
| C2b source geometry (620) | 0.642 |
| C4 pupillometry (330) | 0.594 |

Leave-one-channel-out costs −0.048 to −0.084 for every channel, so the fusion argument holds.
Best configurations cluster at **window AUC 0.70–0.78, question-level 0.65–0.78**. Model selection
across 16 configurations did not separate them reliably — 11 candidates cannot resolve it. Report
the range, not a cherry-picked best.

**Keystroke discontinuity** (`ks_layer.py`, CMU DSL, 51 subjects, published protocol) — the strong
layer, and the one with enrolment working as designed:

| Detector | EER | AUC |
|---|---|---|
| Manhattan scaled | **14.21 %** | **0.915** |
| Mahalanobis | 15.68 % | 0.905 |
| Euclidean | 23.43 % | 0.808 |

Persistence over consecutive commit events: EER **14.21 % (k=1) -> 8.39 % (k=8)**. This is the
measured justification for the persistence counter (810) — it is not a heuristic.
Physical timing scale: key hold 86.1 ms median (49.3–144.8 ms p5–p95), down-down 191.1 ms.

**Inertial channel** (`ms_layer.py`, MotionSense, 24 subjects, 50 Hz) — real physical units:
seated noise floor 0.178 m/s² median, p99 1.832 m/s²; seated vs walking AUC 1.000, vs standing
0.792; onset latency 20–160 ms for N = 1–8 sample confirmation with false-onset rate 1.00 % ->
0.598 %. Saturation works: an 8.90 m/s² impulse (50x seated median) would drive the threshold to
0.066, far below its 0.35 floor, but `M_max` holds it at 0.450.

**Enforcement discipline** (`scheduler.py`, rank-calibrated control values) — the real contribution:

- **Dual-channel interlock (850) is the strongest design element.** False hardware gate
  **30.58/h -> 9.31/h (−69.6 %)** and unassisted gate rate 29.7 % -> 10.8 % (−63.6 %), for a
  25 % cost in true gates (44.4 % -> 33.3 %). No single modality can open the input path.
- Persistence counter (810), n=1 -> n=4: false advise **45.2/h -> 16.0/h (−64.7 %)**, true advise
  58.7 % -> 33.3 %, actuations 131 -> 53.
- Scheduler holds 419 eligible cycles down to 83 actuations (**80.2 % reduction**) where the global
  interval alone would permit 1297.
- **Escalation override (840) is negligible on this corpus** (83 vs 80 actuations). Say so; do not
  claim a benefit that is not there.

### The scope decision that is now due

The ocular classifier tops out near AUC 0.75. It will not beat a published benchmark and should not
be sold as doing so. The defensible framing — and the one the reference filing used successfully —
is that novelty lives in the **control layer**, evidenced by:

- the keystroke discontinuity channel at EER 8.39 %,
- the inertial qualification coupling (0.562 -> 0.659 from one measurement placed twice),
- the interlock cutting false hardware actuation by 69.6 %,
- the scheduler's 80.2 % actuation reduction.

That is a complete, physically grounded, reproducible evidence base — larger than the reference
filing's (7 clips, 471 frames). Write Section 8 around actuation discipline and per-channel
technical effects, not around a classification score.

### Corrected keystroke numbers (supersede the table above)

Two protocol bugs in `ks_layer.py` were found and fixed (impostor set pulled 40 attempts per
foreign subject instead of 5; persistence blocks chunked by row position instead of by adversary).
Corrected, under the published Killourhy & Maxion protocol:

| Detector | EER mean | EER median | AUC |
|---|---|---|---|
| Manhattan scaled | **9.60 %** (SD 6.87) | 8.00 % | **0.954** |
| Mahalanobis | 11.12 % | 10.45 % | 0.945 |
| Euclidean | 17.05 % | 15.55 % | 0.879 |

Persistence: 9.60 % (k=1) → 7.22 % (k=2) → 5.38 % (k=3) → 5.07 % (k=5). Stricter all-session
impostor variant: 14.22 %. **Do not quote the old 14.21 / 8.39 figures.**

## DELIVERED 2026-08-26 — `IDF-B_CausalInterlock/`

Full IDF-B disclosure, built to match `IDF-B_LabelFree_Malpractice_Detection_rev6` (the user's
other filing) rather than the older Group05 format: twelve numbered sections, plain prose with no
`[0001]` numbering, TRL grid, internal filing note.

```
IDF-B_CausalInterlock/
  IDF-B_Causal_Emission_Response_Interlock.docx   30 pp, 10 figures, 8 tables, 25 claims
  preview.pdf                                     Word-exported, for visual check
  make_figs.py                                    fig01..fig10, reads the saved JSON/CSV outputs
  build_idfb.py                                   full document text + python-docx layout
  assets/vit_logo.png                             masthead logo, lifted from the reference PDF
  figures/fig01..fig10.png
```

### Presentation pass, 2026-08-27

Figure files are now named in **document order** (`fig01.png` = Figure 1). Do not reintroduce the
old `figure_N.png` names — they were numbered in creation order and did not match the captions.

Added in this pass, all in `make_figs.py` / `build_idfb.py`:

- **Cover page** — disclosure-record table + a real Word `TOC` field. Headings carry `w:outlineLvl`
  (0 for `h1`, 1 for `h2`); without it the field reports "No table of contents entries found".
- **Running head and folio** — built as a borderless two-cell table in the header/footer, not with
  tab stops: the inherited Header-style centre tab at 3.25" swallows a right tab and the two
  strings collide. `sec.different_first_page_header_footer = True` keeps the cover clean.
- **Figure 3** (NEW) station side elevation — every part carries only its reference numeral, with a
  key beneath, which is patent convention and the only layout that does not overlap. Shows the two
  acoustic paths and the crossed desk gap. This is the "how the hardware works" figure.
- **Figure 4** (NEW) in-line gating unit — switched data pair, VBUS/GND passing through, pull-down
  on `/OE`, retriggerable watchdog, plus a three-row state table. Evidences claims 13 and 20.
- **Figure 10** (NEW) claim dependency map at the head of §10.
- **Figure 1 rebuilt** — the accepted geometry above, four *mini timelines* below showing the shape
  of each rejection. Replaced a floating text list that read as a legend.
- **Figure 9 rebuilt** — per-element log-scale bars plus the total against the 200 ms bound. The
  old single 30.9 ms bar on a 0–200 axis was unreadable.
- **Table 1** reference-numeral index (§7) and **Table 2** evidence summary (§8). Old Tables 1–6
  therefore became 3–8.

Export with Word COM: open normally, `Fields.Update()`, `TablesOfContents(1).Update()`,
`Repaginate()`, then `ExportAsFixedFormat($p, 17)`. Opening read-only makes `SaveAs` throw.
Set `$w.UserName = "VIT IPR & TT Cell"` before opening or the save stamps the machine owner into
`docProps`. If Aditya has the .docx open the build fails with `PermissionError`; build to a temp
directory instead (`import build_idfb as b; b.HERE = <tmp>; b.build()` — `FIG` is resolved at
import so the figures still come from the repo).

### Table style, 2026-08-27 — matches `IDF-B-Project1-Group05.pdf`

Aditya asked for the reference filing's table look. **No colour anywhere in tables.** The rules:

- Body font **Times New Roman**, not Arial. Header row **bold, centred, black on white** — no fill.
  Body rows no fill, no alternating shading. Black `Table Grid` borders.
- Caption goes **below** the table, centred, **entirely bold**, in the form `Table N: Title Case`.
  Reference captions are short titles, so descriptive detail that used to live in the caption was
  moved into the body prose (INR 1,150 into §9.1, the Table 2 framing sentence into the §8 lead,
  the Table 8 note into §9.2). Figure captions were left alone — Arial, bold lead, below.
- First row carries `w:tblHeader` so the header repeats when a table splits across pages.
- The §11 TRL grid is monochrome too: plain cells, bold labels, `✓` ticks in TRL 1-3.
- Page header is `©VIT IPR & TTCELL`, bold, right-aligned, **on every page including the cover**
  (`different_first_page_header_footer = False`). Footer is a bare centred `PAGE` field.
- Cover carries no inventor name or email; `core_properties.author` is set to `VIT IPR & TT Cell`.

Table point sizes were raised roughly 1 pt when the font changed, since Times reads smaller than
Arial at the same nominal size. Page count held at 29.

Section map: 1 title · 2 field · 3 prior art (17 entries) · 4 + 4.1 inventive step (a)–(g) ·
5 objectives · 6 working principle · 7 detailed description + 7.1 alternatives (a)–(i) ·
8 validation on recorded human data (8.1–8.8) · 9 contemplated prototype + bench plan H1–H8 ·
10 claims (independents 1, 13, 19, 20, 24) · 11 **TRL 3** · 12 note on filing.

Figure order: 1 causal timing kernel · 2 architecture · 3 station side elevation · 4 in-line gating
unit · 5 enforcement ladder · 6 ocular channels · 7 keystroke discontinuity · 8 enforcement
discipline · 9 latency budget · 10 claim map. File names match (`fig01.png` … `fig10.png`).

Decisions baked in, keep them:

- Scope framing is the control layer, per the reference filing. The ocular classifier is presented
  as **one corroborating input**, never as beating the 74.98–85.72 % benchmark; §8.8 says so.
- Independent claims 13 and 20 carry the fail-safe bias and the watchdog release as **positive
  limitations**. §12 flags these as the strongest §3(k) answer (a circuit property that holds when
  no program is running).
- §12 "Third" records the **co-pending label-free disclosure** of the same inventor and draws the
  boundary: that one claims how a score is produced, this one claims a timing relation plus
  physical intervention. Agent must review both together.
- Negative results are stated, not buried: onset phase structure rejected (0.485–0.519), ocular
  enrolment unstable across constructions and therefore not claimed, escalation comparator (840)
  negligible on this corpus.
- Section 3(k) is never named in the body — only in §12, which the note itself says must not
  enter the filed specification.

### Hardening pass, 2026-08-28 — masthead, claim surgery, cost removal

Aditya asked for the document to open like `IDF-B-Project1-Group05.pdf` and for a weakness audit.
Rated 7/10 before this pass, 8/10 after. What changed, all of it deliberate — do not revert:

**Front matter.** The custom title page and the Word TOC field are gone. The document now opens
with the VIT masthead table exactly as the reference filing does: logo + `Invention Disclosure
Format (IDF)-B` in a merged left cell, `Document No.` / `Issue No/Date` / `Amd. No/Date` at the
right, then straight into §1. Logo extracted from page 1 of the reference PDF, kept at
`assets/vit_logo.png`. Closing line `----- END OF THE DOCUMENT -----` added, also from the
reference. `cover()` was replaced by `letterhead()`. 29 pp -> 28 pp.

**The defect that mattered: T0 did no work in Claim 1.** The photometric anchor is sold as the
primary novelty in §4.1, §5, §6 and §12, but Claim 1 recited it only as the ordering condition
`T1 following T0`, and §7 said the same. An examiner reads that out as non-functional and Claim 1
collapses toward ProctorU. Fixed by adding a **second bounded interval**: the
**consultation-band comparator (615)**, evaluating `T1 - T0`, lower bound a minimum
item-apprehension interval, upper bound the presentation instant of the succeeding item. T0 now
bounds the emission from below *and* binds it to one identified item — neither is computable
without it, and ProctorU's face-loss anchor cannot supply either.

The lower bound is **measured, not asserted** (new paragraph in §8.2, new row in Table 2):
across 2,091 gaze departures on the 55-column protocol, **7 (0.335 %)** begin within 1,000 ms of
the onset marker, and those few skew unassisted (0.62 % vs 0.21 %), which is what carry-over from
the preceding item looks like. First-departure p5: 997 ms assisted vs 0 ms unassisted. Default
1.0 s, permitted range 0.5-2.0 s, stated in §7 as a default subject to confirmation. Seven events
is small and the text says so.

**Other claim fixes.**
- Attribution by structure-borne/airborne coincidence **moved from dependent Claim 3 into Claim 1**.
  §12 calls attribution the distinguishing element; leaving it in a dependent while Claim 1 merely
  asserted "attributed to the candidate" was an anticipation *and* a sufficiency exposure. Claim 3
  repurposed to the coincidence-window duration bounds and voice-band limiting.
- Claim 1's actuator was `produce an output` — i.e. a flag, which is what §4.1 attacks in the prior
  art. Now `a physical output` from `at least one transducer disposed to act upon the candidate or
  upon a data path`.
- **Claim 13 now defines the corroboration value** (Claim 15 referenced it with no antecedent basis).
- **Claim 17 made self-contained** (it depended on 13 but cited "the discontinuity measure of
  Claim 4", which hangs off Claim 1 — improper cross-chain dependency).
- **`n >= 2` recited in Claims 13 and 20.** `n = 1` deleted the persistence limitation entirely.
- Claim 10 now covers both bands. Claim 12 antecedents repointed.
- **CRM claim deleted.** The old Claim 24 ("non-transitory computer-readable medium") is the one
  claim in the set that Indian practice routinely refuses outright, and it contradicted the entire
  framing strategy. §10's lead-in now carries a **third drafting principle** saying so
  affirmatively, and §12 Fourth instructs the agent not to add one back at drafting.
- Old Claims 26 + 27 merged into one deployment claim.
- **27 claims -> 25 claims; independents are 1, 13, 19, 20.** Numbering 1-23 is unchanged, so every
  claim reference in §12 still resolves.

**Self-inflicted admissions cut.** §4.1 opened by conceding five prior-art elements in one breath,
including *"Two-out-of-two interlocks are ordinary practice in process safety"* — a roadmap to
combining Claim 13 with IEC 61508 art, written by the applicant. Cut from §4.1; the concession
survives where it belongs, in §3 entry 16, in discloses/does-not-disclose form. §9.1's *"the purpose
of the build is not sophistication"* also cut.

**Costs removed from the body.** Table 7 lost its Price column; the `INR 1,150` sentence and §9.2's
`two to three thousand rupees` are gone. Commercial, not technical; dates the document; and an
applicant's own statement that a build is cheap and ordinary is quotable on inventive step. The
figures survive in **§12 Fifth**, explicitly marked for the Cell's internal costing and not for the
specification. §9.2 retitled away from "Minimum viable configuration".

**Numerals and figures.** Allocated **205 rendered onset patch region** (it was described and claimed
but unnumbered) and **615 consultation-band comparator**; both added to Table 1. Figure 1 rebuilt —
the accepted timeline now shows both bands, and there are **five** rejection panels, the new first
one being `T1 - T0 TOO EARLY`. Figure 2's interlock column names both comparators. Figure 3 labels
the patch `(205)`. Figure 10 redrawn for four independents with Group D shown unfilled and marked
"no independent claim".

**Second hardening pass, same day** — prompted by an external (ChatGPT) review that turned out to
describe a *different* invention entirely (IoT + cloud + noise mapping + ML model menu). Seven of its
ten points had no counterpart here and were rejected; adding a cloud tier in particular would have
damaged the eligibility and privacy positions. Three were real:

- **Privacy became a positive limitation.** Claims 12 and 23 previously said only that no waveform is
  retained — a policy promise. The firmware already supports far more: the node samples at 200 Hz and
  emits only peak and RMS per acoustic channel at `REPORT_HZ = 50`, i.e. two scalars per 20 ms.
  Intelligible speech needs ~8 kHz sampling, so the emitted representation is two to three orders of
  magnitude short of reconstructability. That is information-theoretic, not policy. New §7 paragraph
  *Non-reconstructability of the acoustic representation*.
- **Concurrent unrelated sources — a real hole.** The candidate types or knocks the desk while a
  neighbour whispers: both channels cross threshold in the same window for unrelated reasons and
  attribution false-fires. Band-limiting does not fix it — a mechanical impulse is broadband. Claim 3
  now requires the band-limited **envelopes to correlate** across the window, not merely to co-occur.
  One utterance reaching two transducers modulates both together; a keystroke and a syllable do not.
  This is what keeps attribution alive in a busy hall, and it gives H2 a second thing to measure.
- **Adaptive baselines claimed on all three analog channels** (firmware already had them:
  `PHOTO_ALPHA`, `Adaptive photoBase/piezoBase/micBase`). Only the photometric one was claimed before.
  Described as an adapted threshold, never as ML.

Also added **§12 Seventh, unity of invention**: Claims 1 and 13 are separate independents and an
examiner may object they share no single general inventive concept. Position taken — they share one
(a corroboration value from physically independent transducers governing a physical actuation; 1
constrains how it is earned, 13 what it may do). If pressed, **prosecute Claim 13 in the parent and
file Claim 1 as a divisional**, since 13 carries the hardware limitations answering eligibility.

Everything folded into existing claims, so **still 25 claims, no renumbering**, every cross-reference
resolves. 28 pp -> 30 pp. §12 Fourth now tells the agent Claim 3 deliberately carries four separable
limitations and should be split at drafting, envelope-consistency being the one worth its own claim.

Build-script fix: the masthead logo path resolved from `HERE` at call time rather than import time,
which broke the documented build-to-temp workaround when Aditya has the .docx open. Now `ASSETS` is
resolved at import, same as `FIG`.

**What was NOT changed, and why.** Heading wording still matches `rev6` rather than Group05
(`5. Objectives` vs `5. Objective(s)` etc.) — consistency across the inventor's two filings is worth
more than reference-exactness. TRL held at 3.

**Still the top substantive risk:** element (b), structure-borne attribution, carries Claims 1, 3 and
19 and has zero measured data. Bench test **H2** before filing, unchanged from the plan below.

### Next steps

1. Aditya reviews the .docx; the drafting agent reviews §12 with the label-free disclosure beside it.
2. Run bench measurement **H2** first (own whisper vs confederate at 1 m). It is the riskiest claim;
   if structure-borne separation fails, re-frame (420) around contact events before filing.
3. H1 and H4–H7 next: they convert the five DERIVED rows of §8.7 into measurements and evidence the
   enforcement claims.
4. Only then revise §8, §9 and §11 upward to TRL 4.

## AUDIT PASS 2026-08-28 (evening) — all findings fixable without bench data are FIXED

A hostile pre-filing audit scored the document 4/10 and found things two earlier reviews missed.
Everything below has been applied. 31 pp, still 25 claims, no renumbering.

**Evidence honesty — the big one.** `et_windows.py:97` derives `head_v` from `ET_CameraLeftX/Y`, and
`channels.py:32` builds `INERTIAL` entirely from `ET_CameraLeft*` / `ET_Distance*`. **The "inertial"
channel in the ocular experiments is the eye tracker.** So §8.6's dual-channel interlock ablation
(-69.6 % false gating) was run on two quantities from ONE instrument — exactly what §7 and Claim 16
declare insufficient. §8.3 and §8.6 now open by saying so; Table 2 rows relabelled ("Two-channel
agreement rule (850), not the claimed two-transducer interlock"); §4.1(g) reworded; §8.8's
"strongest single design element" removed. The number stays, correctly described.

**The assistance band had no number anywhere in 30 pages** — the limitation in the title of the
invention. Now defaults 2.0 s / 30 s, permitted 1.0-4.0 s and 15-60 s, with new §8.2 support from
assisted-vs-unassisted departure durations (p75 1,899 vs 1,440 ms; p90 4,500 vs 2,987; p95 6,651 vs
4,562; a 2-30 s window holds 24.1 % of assisted departures against 16.4 %, enrichment 1.47x). Stated
as weak, proxy-derived, and to be replaced by the staged trial.

**Nyquist contradiction closed.** §7 said 200 Hz sampling; Claim 3 required voice-band limiting
(85-900 Hz). Resolved by disclosing the analog front end that was implicit all along: band-pass
80 Hz - 1 kHz, rectify, low-pass ~50 Hz, digitise the ENVELOPE. New numeral **403**, new Table 7 row,
Claim 3 rebalanced onto it.

**Non-reconstructability re-argued structurally.** The old ratio argument was arithmetically wrong
(100 values/s vs 8 kHz is 80x, not "two to three orders of magnitude"). Replaced in §7 and in Claims
12 and 23 by the real reason: the envelope stage discards phase, and peak+RMS are two order
statistics over the whole window — many-to-one, no inverse. Holds at any rate.

**Claim fixes.** Claim 1: actuator disjunct "act upon the candidate" DELETED (it let Claim 1 read on
an LED, fatal under §3(k)); now mandatorily interrupts the data path; envelope-consistency pulled up
from Claim 3 so the *whereby* is no longer contradicted by §7; "coupled to the foregoing" replaced.
Claim 19 same treatment. Claim 9 -> depends on Claim 6 (Claim 1 has no imaging sensor). Claim 22 made
self-contained. Claim 10 was logically impossible (no T1 exists during unassisted enrolment) — now
tracks §7.1(d). Claim 12 no longer cites non-parent claims. Claims 13 and 20: "a candidate" given
antecedent basis; transducer independence pulled up from Claim 16; **interlock extended to cover the
session hold**, which previously escaped it. Claim 16 repurposed (mechanical + optical). Claim 17
recites n <= 8 instead of how n was chosen. Claim 23 single parent. Claim 24 made limiting. Claim 25
no longer mixes categories.

**§12 First reordered.** Lead with argument (iii), the physical data-path interruption. Do NOT lead
with (iv) — the fail-safe bias and watchdog are conceded prior art at entries 8 and 16, so a
Controller applying the substance-of-the-contribution test answers it in one line. Argument (i)
corrected: T0 is independent of the *reported event*, not of the machine — the machine renders the
patch (§9.1) and an examiner will notice.

**Also:** Table 6 note explaining why two rows share figures (interlock disarmed makes gate rate ==
advise rate — real, not a typo); §8.6's "against 1,297" reworded (it is a capacity ceiling, not an
actuation count); Table 1 caption no longer claims numerals appear in the claims; Figure 10 and its
caption updated.

**Unity is now stronger, not weaker:** both independent system claims recite the same switching
element and the same interruption, so the shared special technical feature is concrete. §12 Seventh
updated.

**Still open, needs bench work:** the assistance band is derived not measured, and H2 (structure-borne
attribution) remains unrun. Those cap the score; nothing else in the audit is outstanding.

## CORRECTION 2026-08-28 — the interlock evidence does not measure the claimed interlock

A hostile audit found this and it is confirmed in the source. **Do not quote the 69.6 % figure as a
measurement of the dual-channel interlock until this is resolved.**

`et_windows.py:97` computes `head_v` from `ET_CameraLeftX` / `ET_CameraLeftY` — the eye tracker's own
camera-relative eye position. `channels.py:32` then defines
`INERTIAL = ['head_rms','head_p95','head_mean','head_lead_ms','dist_sd','dist_mean']`, every one of
which derives from `ET_CameraLeft*` or `ET_Distance*`. The "inertial" channel in the ocular
experiments **is the eye tracker**. There is no second transducer in that corpus.

Consequences, all of which must be fixed in the document:

- §8.6's dual-channel interlock ablation (false gating 30.58/h -> 9.31/h, -69.6 %) was run with two
  quantities derived from **one sensor**. That is exactly the configuration §7 and Claim 16 declare
  insufficient: *"two quantities derived from the same camera do not constitute two channels."*
  The number is real as a *score-decorrelation* result; it is not a measurement of the claimed
  interlock.
- §8.3's "one measurement applied at two points" (0.562 -> 0.659) is head-pose coupling, not inertial
  coupling. `ms_layer.py` (MotionSense) is the only real inertial evidence and it is a separate corpus
  that was never joined to the ocular data.
- §4.1(g), §8.8 ("stands comparison with published work"), Table 2 row "Dual-channel actuation
  interlock (850)", and the STATUS section above all inherit the error.

Honest reframing available without new work: describe §8.6 as an ablation of the *decision rule* on
recorded human data, state plainly that both inputs came from one sensor, and say the transducer
independence Claim 16 requires is evidenced only by H2/H8 once the node exists. Do not delete the
result — restate what it measures.

## Prior art already located (verified against patent-office records)

| Ref | What it discloses | Gap to exploit |
|---|---|---|
| `US20190156689A1` (ProctorU, filed 2019-01-25) | **Closest.** Webcam/mic/keyboard/screen; flags "loss of face ≥10 s **then** mouse/keyboard input **then** submission"; suspends the session. | Anchor is the candidate's own face-loss, not a measured display transition. No latency-band gating, no audio attribution, no composition-vs-transcription test. Enforcement is a **software** session suspend — no physical interruption of the HID path. |
| `US20170263142A1` (Zereshkian & Messinger, 2016) | Smart glasses show the second half of each question; iris check gates display. | No fusion, no timing logic, no escalation state machine, no enforcement action. |
| `US9881516B1`, `US20120135388A1`, `US9154748B2`, `US20110177484A1`, `US9601024B2` | Assorted online-proctoring platforms, biometric anomaly flagging, dual-camera. | Platform art — concede it, do not claim it. |
| `CN110414225B`, `US10515234`, `US10970423`, `US9734358` | In-line USB/HID data-diode and KVM isolation hardware. | Concede the HID gating component as known; claim the **arrangement** that drives it. |
| arXiv 2406.15335 (Kundu et al. 2024) | Keystroke dynamics vs LLM-assisted writing, TypeNet. **74.98–85.72 %** condition-specific. | Software-only, no sensor, no real-time intervention. **This is the number to beat.** |
| arXiv 2511.12468 (Mehta et al. 2025) | Follow-up, 130 participants, paraphrasing conditions. | Same gap. |
| Psychometric RT literature (Balta & Dogan 2024; PubMed 33994559) | Preknowledge detection from response-time/accuracy joint models, some with fixation counts. | Cohort-level, offline, post-hoc flagging. No sensor anchor, no attribution, no actuation. |

## Conventions

- Scratchpad for all temp work: `C:\Users\rober\AppData\Local\Temp\claude\C--adi-patent-InfoSec\<session>\scratchpad`.
- Python is 3.9, `pypdf` available, `fitz` is not, `poppler` is not — extract PDF text with pypdf and
  write to a file with `encoding='utf-8'` (console is cp1252 and will raise on `\u25cf`).
- In Python, `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` before printing dataset text.

## AUDIT 2026-09-01 — `IDF-B_LabelFree_Malpractice_Detection_rev6_FINAL` reviewed, rated 6/10

Second disclosure, same inventor. 23 claims (independents 1, 11, 16, 17, 23), 6 figures, 7 tables,
TRL 3, §8 is **simulation only** on a generative model authored by the inventor. Both copies in the
repo root are byte-identical (md5 `679d841f912077cf899769d97d24939c`).

Core idea, and it is a good one: one normal-only predictive model applied across all stations makes
their residual time-series *commensurable*, which creates a cross-station coupling channel that
provably does not exist at any single station. §4.1(e) depends on (a)+(c) — that synergy argument is
sound. Common-mode rejection (f) is drawn positively into both cross-station independents.

### Scores
novelty 8 · inventive step as argued 6.5 · **§3(k) 4** · claim drafting 5.5 · **evidence 3** ·
sufficiency/writing 9. Grant chance as filed: low. After Tier-1 fixes: good, **on Claims 11/17, not
Claim 1**.

### The five defects that decide it

1. **No physical actuation anywhere.** Claim 1 output is "transmit an alert"; Claim 11 "indicate".
   Sensing assembly + processing unit + communication module = generic computer with sensors. Under
   the 2025 CRI Guidelines step-wise test the contribution reads as "a better anomaly score", i.e.
   the algorithm. CausalInterlock survives §3(k) because it opens the keyboard data lines; this has
   no equivalent.
2. **Common-mode rejection is standard instrumentation** — common-average referencing, differential
   measurement, seismic array processing, first-PC removal. §3 cites no instrumentation art and
   §4.1 asserts it as a precondition without defending non-obviousness. It carries both cross-station
   independents, so if it falls they fall.
3. **Product-by-process inside system claims.** "trained exclusively on … no labelled instance of
   malpractice" is not structurally detectable in a deployed system. §12 Second half-sees this;
   Claim 1 still leans on it.
4. **Claim 23 is a CRM claim.** Deleted from CausalInterlock on 2026-08-28 for the same reason.
   Delete here; add the affirmative drafting principle to §10.
5. **§3 entry 8 "base disclosure"** reads like the inventor's own earlier work. If ever publicly
   disclosed it is §29 art and §12 Fifth ("no public disclosure") is wrong. Resolve first.

### Fix plan (Tier 1 = do or do not file)

- Pull **Claim 12's instrumented unoccupied reference station up into Claim 11** as a mandatory
  element — real transducer, no prior-art counterpart, claim inoperable without it. Best available
  §3(k) answer in the existing spec.
- Pull **Claim 15's time-synchronisation arrangement up into Claim 11** with a numeric tolerance
  (≤50 ms alignment against 1–3 s coupling lags). §9 already argues its necessity.
- Delete Claim 23. Add ProctorU `US20190156689A1` to §3 (already in the CausalInterlock table;
  closer to Claim 1 than several cited entries). Add instrumentation common-mode art in
  discloses/does-not-disclose form and own the distinction.
- Tier 2: give Claim 1 a runtime-inspectable distinction (per-session venue calibration, not the
  training negative); prune field-of-use Claims 21/22; split "Claim 1 or Claim 11" multiple
  dependency in 20/22; reconcile the acoustic band (Claim 3 says >15 kHz, §9 says 18–45 kHz, §8
  stops at 24 kHz); keep Claim 14 but make conceding it costless.
- Tier 3, self-inflicted admissions to cut, same class as the ones removed from CausalInterlock
  §4.1: §8.1's *"not usable as a per-window accusation device"* and Table 4's 11 %/29 % detection
  rates — move to §12 internal, keep §8 on the session-level triage mode actually claimed. Same for
  the §8 sentence conceding the inventor authored both signal generators.

### Evidence plan — the highest-value work, Kaggle available

E1 real physical acoustic anomaly corpus (MIMII / DCASE-style), train normal-only, score anomalies →
first measured row for Claims 1, 9, 16. E2 `jennylandes/eye-tracking-dataset-academic-reading`,
**55-column protocol only, never pool protocols**: train on `Nicht_Schummeln`, score `Schummeln` →
Claim 8 on real humans, label-free by construction. E3 the one that matters — any real multi-node
sensor array (multi-node WiFi RSSI/CSI, multi-sensor hall, multi-microphone room) to show, as three
separate results, that (i) one normal-only model yields commensurable residuals across nodes,
(ii) an injected venue-wide event is removed by common-mode subtraction, (iii) an injected lagged
pair coupling survives it. E3 evidences Claims 11/12/17 and turns Figure 5 from a drawing into a
result. If E3 lands the document rates ~8.

### Format
Opens with two plain paragraphs; needs the Group05 **masthead table** and the exact
`----- END OF THE DOCUMENT -----` line. Tables need the Group05 monochrome treatment. Retarget
`IDF-B_CausalInterlock/build_idfb.py`, which already implements all of it, rather than restyling.

### Cross-filing risk — settle before either is filed
Same inventor, same domain, overlapping sensors (Label-Free Claim 5 = desk accelerometric,
Claim 8 = gaze/blink/head-pose). Whichever files first is citable against the other under
§13(1)(b) / §29. The CausalInterlock §12 Third boundary holds **only while Label-Free recites no
timing relation between an onset anchor and a response**. It currently does not — keep it so, and
review both claim sets side by side before filing either.

## E3 EVIDENCE RUN 2026-09-01 — cross-station channel MEASURED on real data; the
## disclosure's central synergy argument is REFUTED by it

Work lives in `evidence/`. Full write-up in `evidence/README.md`; do not re-derive from
the JSON. Corpus is the **Server Machine Dataset (SMD)**, MIT licence, 28 entities x 38
channels, sparse-cloned from `NetManAIOps/OmniAnomaly`. Group-disjoint: shared model
trained on groups 1+2 (17 entities, 417,349 windows), every measurement on group 3
(11 entities, 55 station pairs). Exathlon was evaluated and **rejected** — better physical
fit but CC BY-NC-SA 4.0, non-commercial, not worth it under a commercially intended
filing. SMD lags are in REPORTING INTERVALS (1 sample/min), not seconds.

**E3(i) commensurability — REFUTED.** One shared normal-only model does NOT make residual
magnitudes comparable across stations. Threshold transfer, 110 ordered pairs, nominal FPR
0.0100: within 2x nominal 17.3 % shared vs 22.7 % per-station; KS median 0.599 vs 0.389;
AUROC 0.739 vs 0.797; spread of mean residual across stations **4.1x shared vs 2.8x
per-station**. Sharing WIDENS scale disagreement. Mechanism: a shared model fits some
stations better than others, so residual magnitude encodes how typical the station is.

**E3(ii)+(iii) coupling channel — CONFIRMED, in the configuration the disclosure argues
against.** 20 trials, resampled pairs and injections, scenario D (coupled pair at lag 2
plus a simultaneous venue-wide event), detection = coupled pair ranked first of 55:

| model | reference rule | detection | AUROC | z median |
|---|---|---|---|---|
| shared | any of the three | 0.00 | 0.516-0.559 | 0.01-0.19 |
| per-station | none | 0.10 | 0.632 | 0.57 |
| **per-station** | **raw across-station median** | **0.60** | **0.983** | **4.42** |
| per-station | standardised median | 0.55 | 0.920 | 3.28 |

The shared model is **at chance** (AUROC ~0.53), zero detections in 20 trials. Common-mode
rejection is **necessary and its effect is now measured**: AUROC 0.632 -> 0.983, detection
0.10 -> 0.60. The extra per-venue calibration step is NOT needed and slightly hurts
(0.983 -> 0.920) — plain median of per-station residuals is the best rule tested.

**Why sharing poisons it.** With NO injection, median rejection under the shared model
RAISES mean pair correlation 0.0738 -> 0.1381. The shared model's errors are correlated
across stations because they are the same model's errors; it manufactures a cross-station
common component out of its own deficiencies, and a reference formed from the stations
carrying it cannot remove it.

**Clock-skew tolerance, measured not asserted** (per-station + raw median, lag 2, 20 trials
per point): skew +-0 AUROC 0.992 / detection 0.75; +-2 (1x lag) 0.981 / 0.60; +-3 (1.5x)
0.954 / 0.35; +-4 (2x) 0.939 / 0.30; +-8 (4x) 0.726 / 0.15. Monotone. As a fraction of the
coupling lag it is rate-agnostic: AUROC holds above 0.95 to about 1.5x lag. For a 1-3 s lag
that is roughly one second, and the proposed <=50 ms sync sits at ~2 % of lag. **This is
the numeric tolerance the audit's Tier-1 item needed.**

The skew sweep inside `e3_coupling.py` is VOID — run on the shared cell, which was not
detecting. Use `e3_repeat.py`'s sweep. Kept in the JSON so the error is on the record.

**Operating envelope** (per-station + raw median, scenario D, 20 trials/point). Amplitude
as a fraction of the [0,1] channel range, 60 events: 0.02 -> AUROC 0.514, 0.06 -> 0.673,
0.10 -> 0.866, 0.15 -> 0.953, 0.25 -> 0.999. Sharp knee between 0.06 and 0.10. Number of
coupled exchanges, amplitude 0.15: 10 -> 0.759, 20 -> 0.852, 40 -> 0.929, 60 -> 0.953,
90 -> 0.992. The second axis matters more operationally — the channel is a correlation
estimate, so **a single exchange is not detectable by this mechanism and the document must
not imply it is**. Useful from about twenty exchanges, strong beyond forty.

### What must change in the document

1. **Rewrite §4.1(a)+(c)+(e).** "one common normal-only model … residual time-series are
   numerically comparable by construction" is contradicted in DIRECTION, on a public
   MIT corpus, in under five minutes of compute. Do not file it.
2. **Promote §4.1(f).** Common-mode rejection is the load-bearing element and the only one
   with measured support. Pair it with the concession rewrite in `evidence/s3_additions.md`.
3. **Claim 11: recite per-station calibration + the across-station common-mode reference.
   Do NOT recite that the model is shared.**
4. **Instrumented unoccupied reference station gets STRONGER** — with stations
   independently modelled the reference must come from somewhere principled. Tier-1 move
   unchanged, now with a measured reason, not only a §3(k) one.
5. **§8's simulated cross-station figures are suspect** (acoustic 0.468, EM 0.739,
   behavioural 0.650, combined 0.810) — produced under the shared-model assumption.

### Rewrite drafted — `evidence/s4_claim_rewrite.md`

Replacement §4.1 synergy paragraph, amended element list (a)-(g) with the new (g) timing
element, and rewritten Claim 11 pulling Claim 12's instrumented unoccupied reference
station and Claim 15's synchronisation arrangement up as MANDATORY elements (the audit's
Tier-1 plan), with the timing tolerance now carrying a measured number. Claims 12 and 15
repurposed, plus a new dependent on the exchange count.

**The framing to keep:** the refutation hands back a STRONGER inventive-step argument than
it destroys. Sharing one model across stations is the obvious expedient a skilled person
would adopt for economy and uniform scale. The invention now teaches AWAY from it and gives
the measured reason. Teaching away from the obvious beats claiming the obvious as insight.

### Section 3 additions drafted — `evidence/s3_additions.md`

Entries 18 GDN (Deng & Hooi, AAAI 2021, 35(5) 4027-4035), 19 **CST-GL** (Zheng, Koh, Jin,
Chi et al., TNNLS 2023, arXiv 2307.08390), 20 common-mode instrumentation art (Rost &
Thomas, Rev. Geophys. 40(3), doi 10.1029/2000RG000100, plus EEG common-average referencing
and instrumentation-amplifier CMRR), 21 TranAD (VLDB 2022). All in discloses /
does-not-disclose form.

**CST-GL is the threat.** Its `--delays [0,6,30,60,120,180,360]` is lagged inter-node
correlation on a learned pairwise-correlation graph, published 2023. Concede it. The
distinction that survives — and it is real — is the **inverted null**: in CST-GL and GDN
the nodes are channels of one process, mutual correlation is the normal structure the
model learns, and an anomaly is a departure from it; here the nodes are independently
occupied stations for which coupling has no legitimate cause, so surviving coupling IS the
detection. Write that into §4.1. CST-GL has **no LICENSE file** — read for ideas, never
vendor the code.

### Repo assessment (asked 2026-09-01)

`imperial-qore/TranAD` BSD-3 — use as backbone; kills the §8 admission that the inventor
authored both signal generators. `laurab222/TSAD` — evaluation harness + SMD/SWaT/WADI
loaders; verify its licence before reuse. `2er0/mTADS` MPL-2.0 (GutenTAG) — third-party
generator for ablations real data cannot cover; still synthetic, does not move evidence
alone. `huankoh/CST-GL` — prior art, not a tool.

### Still open

- **Capacity objection CLOSED 2026-09-01.** Re-ran at 384 wide / 12 epochs, both conditions
  scaled identically, 2.7 h compute (`results/e3_smd_commensurability_big.json`). Shared got
  WORSE: within-10x nominal 32.7 % vs per-station 52.7 % (deficit grew from 8.2 to 20.0
  points), p95 FPR 0.961 vs 0.352, KS median 0.560 vs 0.440, AUROC 0.734 vs 0.776. E3(i) is
  not an artefact of an undertrained model. Quote it as final.
- Injection is synthetic; no public corpus has real cross-station coupling. Say so beside
  every number.
- SMD entities are heterogeneous machines across three clusters; a venue is identical desks
  in one room. SMD is a PESSIMISTIC proxy. State it.
- **SWaT / WADI access request to iTrust has NOT been submitted** — weeks of lead time,
  Aditya must submit it.
- E1 (real acoustic anomaly corpus) and E2 (eye-tracking, 55-column protocol ONLY, never
  pool protocols) not started.
- **§3 entry 8 RESOLVED 2026-09-01.** Aditya confirms the base disclosure is his own work and
  was **never publicly disclosed**. So it is NOT prior art (nothing published or publicly
  used anticipates), and §12 Fifth is correct as written. **But it must come OUT of the §3
  table**: type `prior / disclosure` plus a limitation column conceding desk-embedded
  acoustic + EM sensing is an *applicant admission* that manufactures prior art against
  Claims 3 and 4 which does not otherwise exist. Delete entry 8, renumber 9-17 (§12 Second's
  "entries 12 to 17" becomes 11 to 16 before the new rows land), and record the development
  history in §12 internal instead. Full wording in `evidence/s3_additions.md`.
  **Sub-question CLOSED 2026-09-01: no application was ever filed on the base disclosure.**
  So there is no §13(1)(b) prior-claiming exposure from it either. Entry 8 is simply not
  prior art in any form and must not appear in §3.

## DELIVERED 2026-09-01 — `IDF-B_LabelFree/` rev7, rated 8/10

Full rewrite of the label-free disclosure, folding in the 2026-09-01 audit (Tier 1-3) and the E3
measurement campaign. **30 pp, 29 claims, 11 figures, 13 tables, TRL 3.**

```
IDF-B_LabelFree/
  IDF-B_LabelFree_Malpractice_Detection_rev7.docx
  preview.pdf                  Word-exported
  build_labelfree.py           full text + python-docx layout; reads evidence/results at build time
  make_figs_lf.py              fig01..fig11, all data figures read the measured JSON
  assets/vit_logo.png
  figures/fig01..fig11.png
```

Format is the **Group05 reference filing** look, same machinery as `IDF-B_CausalInterlock`:
VIT masthead table (no title page, no TOC), `©VIT IPR & TTCELL` header on every page, centred
`PAGE` footer, monochrome Times New Roman tables with **bold caption below** in the form
`Table N: Title Case`, figure captions below in Arial, closing `----- END OF THE DOCUMENT -----`.
Twelve numbered sections, plain prose (no `[0001]`), matching rev6 and CausalInterlock.

### What changed from rev6 — do not revert any of it

**§3.** Entry 8 (the inventor's own unpublished base disclosure) **deleted** — listing it was an
applicant admission manufacturing prior art against Claims 3 and 4. ProctorU `US20190156689A1`
inserted as the new entry 8, so entries 12-17 keep their old numbers and every cross-reference
still resolves. Four new entries: **18 GDN**, **19 CST-GL**, **20 common-mode instrumentation art
(conceded by the applicant)**, **21 TranAD**. New closing paragraph owns the **inverted null** —
in GDN/CST-GL the nodes are channels of one process and correlation is the learned norm; here the
nodes are independently occupied stations and surviving coupling *is* the detection.

**§4.1 rewritten.** The shared-model synergy argument is **gone**. Elements are now (a)-(g) with
(c) per-station, (e) station-local models, (f) common-mode with the concession, (g) the new timing
element. Two measured paragraphs replace the old assertion, plus the teaching-away framing: a
skilled person *would* share one model, and sharing destroys the channel.

**§7** gained: the analogue envelope front end (24) and the non-reconstructability argument
(envelope discards phase; peak + RMS are order statistics, many-to-one, no inverse); station-local
models with the reason; the unoccupied reference station (90); the timing bound; the **inverted
null** (each pair its own control); and the **graduated physical response** — two acquisition
states, implicated pair only, bounded interval.

**§8 split into Part A and Part B.** Part A is the old simulation, single-station only. Part B is
the E3 campaign on SMD, with Tables 4-9 and Figures 6-10 generated from `evidence/results/*.json`
at build time. **The simulated cross-station figures (acoustic 0.468, EM 0.739, behavioural 0.650,
combined 0.810) are WITHDRAWN** — produced under the refuted shared-model assumption. §8.3 records
the withdrawal openly rather than deleting it; §12 Fourth instructs the agent not to restore it.
The void skew sweep is disclosed as void. §8.1's *"not usable as a per-window accusation device"*
and the 11 %/29 % window rates are out of §8 (Tier-3), replaced by the session-level budget only.

**§9** is now a **five-node** build — four candidate stations and one held unoccupied — with the
analogue front end and the second-acquisition-state hardware added to Table 11, **all prices
removed** (they live in §12 Ninth), SNTP justified by the measured tolerance (no 1PPS, no GPS),
and bench programme **B1-B8** in Table 12. B3 (does the unoccupied node earn its place), B4 (first
real coupling), B7 (false-alarm rate per pair-hour) are the ones that matter.

**§10, 23 claims -> 29.** Independents **1, 11, 17, 19, 23, 24**.

- **CRM claim deleted**; §10 carries the affirmative third drafting principle saying so.
- **Claim 11** is now the venue *apparatus*: unoccupied reference station, time-synchronisation
  arrangement and station-local models pulled up as **mandatory** elements (audit Tier-1), shortest
  lag `>= 2T`. Claim 12 repurposed to the plain median (measured best of three rules), Claim 14 to
  `T <= half the shortest lag` (measured 0.987 there).
- **Claim 17** is the inverted null, standing alone so it survives if 11 is narrowed on structure.
  Claim 18 recites **not fewer than twenty** separate occasions — measured, and it also stops the
  spec implying a single exchange is detectable.
- **Claim 19** is the physical response and is the best §3(k) answer this filing has.
  Claims 20-22 hang off it; Claim 22 is envelope-before-digitisation as a **positive** limitation.
- Claim 1's product-by-process softened to runtime-inspectable per-station, per-session
  calibration. Multiple dependency ("Claim 1 or Claim 11") split. Claim 19 recites its transducers
  explicitly so Claims 20 and 22 have antecedent basis.

**§12 has nine heads.** Eligibility ordered to lead with the acquisition-state switch, then the
unoccupied station, then calibration, then data reduction. Second gives a concession ladder and a
**defensible ten-claim core (11, 12, 13, 14, 17, 18, 19, 20, 22, 24)**. Fourth records the
withdrawn assertion and forbids reinstating shared-model language. Fifth records the base-disclosure
history and why it is *not* in §3. Seventh is unity — prosecute 11 and 19 in the parent, file 17 as
a divisional. **Eighth is the cross-filing boundary with CausalInterlock**, and flags that both
disclosures now recite acoustic-envelope reduction: the agent must decide which filing carries the
broader recitation, and filing order is citable under §§13(1)(b)/29.

### Rating, 2026-09-01 — 8/10 (rev6 was 6/10)

| | rev6 | rev7 | why |
|---|---|---|---|
| novelty | 8 | 8.5 | inverted null + unoccupied node have no counterpart in the located art |
| inventive step as argued | 6.5 | 8 | teaching-away, backed by measurement, beats an asserted synergy |
| §3(k) | 4 | 6.5 | acquisition-state switch + unoccupied station + analogue front end |
| claim drafting | 5.5 | 7.5 | CRM gone, antecedents fixed, numeric limits tied to measurements |
| evidence | 3 | 7 | real MIT corpus, group-disjoint, capacity objection closed, negatives reported |
| sufficiency / writing | 9 | 9 | unchanged strength |

**What still caps it at 8, in order:**

1. **No hardware.** Every acoustic and electromagnetic number in the document is simulated or from
   a proxy corpus. B1, B3, B4 and B7 are the difference between 8 and 9.
2. **Synthetic injection.** The coupled exchange and the venue-wide event in Part B are constructed.
   Stated everywhere, but it is the first thing a hostile reader attacks.
3. **§3(k) is answered, not settled.** Re-tasking acquisition is a real change of apparatus state,
   but an examiner may characterise it as changing a setting. CausalInterlock opening the keyboard
   data lines is a stronger answer, and this filing has no equivalent. Claims 1 and 17 both still
   end in an indication.
4. **Six independents, 29 claims.** Unity objection is near-certain; §12 Seventh has the answer but
   it will cost prosecution time and fees.
5. **False-alarm rate per pair-hour has never been measured** at any scale. 55 pairs in Part B; a
   hall of 100 desks is ~5,000. Do not write a TRL 4 claim without B7.

Grant chance as filed: **good on Claims 11, 19 and 24; low on Claim 1.**

### Build notes

`build_labelfree.py` and `make_figs_lf.py` read `evidence/results/*.json`, so re-running either
after a new evidence run updates the numbers in the tables, the figures **and the prose of §4.1 and
§8.2** — the measured values are interpolated, not typed. Export with Word COM exactly as for
CausalInterlock (`Fields.Update()`, `Repaginate()`, `ExportAsFixedFormat($p, 17)`, `$w.UserName`
set first). If Aditya has the .docx open, build to a temp directory (`import build_labelfree as b;
b.HERE = <tmp>; b.build()` — `FIG`, `ASSETS` and `RES` resolve at import).

**Gotcha for future sessions:** the Bash tool collapses `\\` to `\` inside heredocs, so a Python
heredoc containing `\n` writes a real newline into the file and breaks the source. Use the Write
tool or a script file for any patch containing backslashes.

Apostrophes in the build script are **U+2019**, not ASCII `'`, so they sit inside single-quoted
Python string literals without escaping. Keep it that way.
