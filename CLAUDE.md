# CLAUDE.md — Patents hub

All patent work lives here. Start Claude Code from `C:\adi\patents` for anything
cross-patent; start it inside a project folder when working on one patent.

## Layout

```
IDFs\          final Word + PDF of every IDF-B, one pair each, numbered NN_Title
               STATUS.md lists each one with its status
_shared\       drafting guidance (.md), landscape guide PDF, IDF-B format reference docx
_template\     skeleton for a new patent — copy it, do not edit it in place
_old\          superseded copies (early patent folder, old Downloads revisions, 09_pump_cavitation_parked)
01_02_infosec\         01 LabelFree Malpractice Detection + 02 Causal Emission Response Interlock
04_count_conservation\ 04 Count-Derived Conservation Constraints (filed)
05_length_invariance\  05 Length-Invariance Recalibration
06_stage_offset\       06 Stage Offset from Neighbour Gauge
07_fan_coastdown\      07 Fan Coast-Down Gas Hazard
08_ammonium_ise\       08 Ammonium Sonde Floor Anchor (KILLED, kept for record)
09_substrate_wc\       09 Substrate water-content sensor self-calibration (greenhouse irrigation, in progress)
_screening\            screening logs for candidate topics
```

03 Cloud Security Risk Scoring has no working folder — only its IDF in `IDFs\`.

## Starting a new patent

1. Copy `_template` to `NN_short_name` (next number: 10).
2. Copy the drafting-guidance `.md` files from `_shared\` (writing-guidelines, section_3k_compliance,
   physical-technical-compliance, patent-draft-builder-SKILL, `SKILL (2).md` as
   patent-section-builder-SKILL, diagram-tools, dataset-strategy) into `NN_short_name\guidance\`
   and apply them while drafting (user rules above win on conflict).
3. Fill in its `CLAUDE.md` (title, physics, jurisdiction, boundary with earlier patents).
4. Build the IDF-B into `NN_short_name\patent\`.
5. When final, copy the Word + PDF into `IDFs\NN_Title.docx/.pdf` and add a line to
   `IDFs\STATUS.md`. Superseded revisions go to `_old\`, not Downloads.
   Never copy the Word/PDF to Downloads unless the user asks for it.

## Rules that apply to every patent

- Every project keeps a `HANDOVER.md` (where work stopped, results, next steps). Update it at the end of
  each work block; a new session reads it first.
- Do not gate topics on novelty: pick a workable idea, start, find the novelty at claim level.

- No business-method language anywhere (revenue, cost saving, billing, pricing, customer,
  marketing, monetise, business, commercial benefit, ROI).
- Every number in an IDF-B traces to a file in that project's `results\`. No placeholders
  in the IDF-B — drop or reword unmeasured statements.
- No filing strategy, Section 3(k) discussion or notes to the IPR cell inside the IDF-B.
- Prior art: verify against raw text (download, extract, grep), never WebFetch summaries.
- Few claims: 1 independent method, 4–6 dependents, 1 system claim.
- Layout follows `_shared\IDF-B_format_reference_Tablet_Dispenser.docx` (11 sections).
