# Patent 09 — Pump cavitation from NPSH-margin-conditioned efficiency residuals

## Idea

Healthy pump efficiency in affinity coordinates is fitted only on samples with a large suction
margin (NPSHa/NPSHr), so wear moves the baseline and cavitation cannot enter it. The efficiency
residual is split into a margin-independent part (wear, fouling) and a part that grows as the
margin shrinks (cavitation). The VFD lowers speed before the 3 % head drop (NPSH3). Full plan in
`PLAN.md`.

## Feasibility probe

Not run. No open dataset has flow, head, power and cavitation truth together (searched
2026-10-06). Needs a laboratory NPSH rig or author data on request (PLAN.md Phase C).

## Nearest prior art

US 6,655,922 B1 (adaptive classifier on flow and pressure for cavitation), EP 2 196 678 A1
(drive torque/speed features), US 11,994,150 B2 and US 11,965,513 B2 (NPSHr curves and margin),
US 8,303,260 B2 (calibrated power curve). Notes: `prior_art_raw/gp/screen_notes_2026-10-06.txt`.
