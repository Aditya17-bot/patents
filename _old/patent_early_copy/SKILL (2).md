---
name: patent-section-builder
description: >
  Builds patent Sections 6 (Working Principle), 7 (Detailed Description), and 8 (Experimental/Technical Validation) 
  using a three-step framework. Use when user uploads a revised patent document, mentions "patent sections", 
  "section 6", "section 7", "section 8", "experimental validation", "working principle", "detailed description", 
  "patent framework", "antigravity prompt", "fill patent sections", or asks to complete incomplete patent drafts. 
  Also triggers on "start patent framework", "begin framework 1", "patent skill", or "activate patent builder". 
  Supports all technical domains including IoT, AI/ML, cyber-physical systems, healthcare, quantum computing, 
  agriculture, forensics, and more. Do NOT use for trademark, copyright, or non-technical patent queries.
metadata:
  author: shlok-goenka
  version: 2.0.0
  category: patent-writing
---

# Patent Section Builder — Four-Step Framework

## Overview

This skill generates patent Sections 6, 7, and 8 through a structured four-step framework that produces ready-to-paste prompts for Antigravity. Each framework step builds on the previous, maintaining full context continuity.

**Trigger:** Activated when a user uploads a revised patent document (containing Sections 1–5 and/or 9) and requests help completing Sections 6, 7, or 8, or says "start patent framework".

---

## Critical Guidelines (Apply to ALL Frameworks)

### Writing Standards
- Technical, precise, academic tone following scientific writing conventions
- Plagiarism-free, human-like prose — no detectable AI patterns
- Avoid filler phrases: "it is worth noting", "in the realm of", "leveraging", "harnessing", "seamlessly", "robust", "cutting-edge", "state-of-the-art"
- Avoid starting consecutive paragraphs with "Furthermore", "Moreover", "Additionally"
- Use active voice where appropriate; passive voice only for formal procedural descriptions
- Vary sentence length: mix short declarative with longer compound sentences
- Every claim must be technically substantiated with specific numeric results
- Use domain-specific jargon naturally, not as decoration
- Include occasional hedging: "approximately", "within the tested range", "under field conditions"

### Physical-Technical Integration Compliance (NON-NEGOTIABLE)
- The invention must NOT be a "computer programme per se" or "algorithm with no technical effect"
- Must demonstrate **physical-technical integration**: sensors, actuators, hardware gating, physical signal interception
- Must show **technical effect beyond normal software-hardware interaction**
- Section 8 experiments must involve **real or realistic physical parameters**
- Architecture diagrams must show **hardware-software co-design**, not just software flowcharts
- Use terminology: "cyber-physical", "actuator-level", "sensor-integrated", "hardware-gated", "signal interception"
- NEVER describe the system as "fully simulation-based" — use "evaluated using field-representative sensor data"

### Anti-AI-Detection Writing Rules
Consult `references/writing-guidelines.md` for complete banned phrase list and alternatives.

---

## STEP 0: Patent Analysis (Always Do First)

Before ANY framework step, Claude must:

1. **Read the entire uploaded patent document** — all sections present
2. **Extract and internalize:** Title, domain, prior art + limitations, objectives, protection aspects, existing content
3. **Identify the core technical novelty**
4. **Map the domain** — determine appropriate datasets, architectures, and validation approaches

**Context Object (maintain across all frameworks):**
```
PATENT_CONTEXT:
  title: [extracted]
  domain: [extracted]
  core_novelty: [synthesized]
  objectives: [list from section 5]
  protection_aspects: [list from section 9]
  prior_art_gaps: [from section 3]
  physical_technical_elements: [hardware/sensor/actuator components]
```

---

## FRAMEWORK 1: Section 8 — Experimental/Technical Validation

### What Claude Does

1. **Analyze the patent thoroughly** (Step 0)
2. **Web search for suitable Kaggle dataset(s)** aligned with the patent's domain
   - Dataset must contain real-world measurements relevant to the invention
   - Prefer datasets with sensor data, time-series, spatial coordinates, physical measurements
   - Note exact Kaggle dataset URL and slug
3. **Design the experimental validation plan**
4. **Generate a single consolidated Antigravity prompt** containing everything below

### Antigravity Prompt Must Include

**A. DATASET INSTALLATION (Mandatory — must come first)**
- Kaggle MCP instructions: search, download, unzip, load, explore
- Column identification for mapping to patent components
- Feature engineering instructions for any missing physical parameters

**B. ARCHITECTURE DIAGRAMS (2 diagrams: Figure 1 and Figure 2)**

Generate BOTH diagrams directly in Python using **matplotlib only** (no Mermaid, no Figma, no external CLI tools).
Save at `dpi=200, bbox_inches='tight', facecolor='white'`. Use only ASCII-safe characters in all labels —
NO Unicode math symbols (use `alpha`, `sigma`, `theta`, `psi`, `Delta`, `Sum`, `||`, `^2` etc. written out in plain ASCII).

**VISUAL STYLE — match this exactly (based on patent sample reference):**

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

# Zone boxes: colored header strip (solid fill = zone border color) + light fill body
def zone(ax, x, y, w, h, bd_color, bg_color, zone_num, zone_title):
    # Outer zone body
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
        facecolor=bg_color, edgecolor=bd_color, linewidth=2.5, zorder=2))
    # Solid colored header strip (top 0.55 units)
    ax.add_patch(FancyBboxPatch((x, y+h-0.55), w, 0.55, boxstyle="round,pad=0.02",
        facecolor=bd_color, edgecolor=bd_color, linewidth=0, zorder=3))
    ax.text(x+0.18, y+h-0.28, f"{zone_num}  {zone_title}",
        fontsize=10.5, fontweight='bold', color='white', va='center', ha='left', zorder=4)

# Sub-component boxes: white fill, colored border, italic reference numeral top-left
def sub(ax, x, y, w, h, bd_color, ref_num, title, line1='', line2=''):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04",
        facecolor='white', edgecolor=bd_color, linewidth=1.5, zorder=5))
    ax.text(x+0.15, y+h-0.14, str(ref_num), fontsize=8, color='#777',
        va='top', ha='left', zorder=6, fontstyle='italic')
    n = bool(line1) + bool(line2)
    ty = y + h/2 + (0.12 if n else 0)
    ax.text(x+w/2, ty, title, fontsize=9.5, fontweight='bold',
        color='#1A1A1A', va='center', ha='center', zorder=6)
    if line1:
        ax.text(x+w/2, ty-0.28, line1, fontsize=8, color='#555',
            va='center', ha='center', zorder=6, fontstyle='italic')
    if line2:
        ax.text(x+w/2, ty-0.52, line2, fontsize=8, color='#555',
            va='center', ha='center', zorder=6)
```

**Zone color scheme (use consistently):**
| Zone | Border | Background |
|------|--------|------------|
| Proprietary IP / Input | `#2980B9` | `#EBF4FB` |
| Quantum Processor / Core | `#7D3C98` | `#F4ECFB` |
| FPGA / Regulatory | `#C0392B` | `#FDEDEC` |
| Sensor / Physical | `#D68910` | `#FEF9E7` |
| Classical Co-Processor | `#1E8449` | `#EAFAF1` |
| Output / Attestation | `#717D7E` | `#F2F3F4` |
| Final output box (700) | `#2C3E50` fill | white text |

**Arrow styling:**
```python
# Use ax.annotate with arrowstyle='->' for all arrows
ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
    arrowprops=dict(arrowstyle='->', color=arrow_color, lw=1.8,
                    connectionstyle='arc3,rad=0'))
# Arrow labels: small bold text with white background bbox
ax.text(midx, midy+0.18, 'Label text', fontsize=7.5, color=arrow_color,
    ha='center', fontweight='bold', bbox=dict(fc='white', ec='none', pad=1))
```

**Figure 1 — System-Level Cyber-Physical Architecture:**
- Layout: 22×13 inch canvas, `ax.set_xlim(0, 22)`, `ax.set_ylim(0, 13)`
- Top row: 3 zones side-by-side (Proprietary IP | Quantum Processor | FPGA/Regulatory)
- Bottom row: 3 zones side-by-side (Sensor Array | Classical Co-Processor | Output & Attestation)
- Far right: dark final output box (700 Regulatory Filing Package)
- Each zone contains 2–3 white sub-component boxes with reference numerals
- Cross-zone arrows labeled with signal names (e.g., 'Hamiltonian Parameters', 'Quantum Readout')
- Feedback loops drawn as annotated curved arrows with `connectionstyle='arc3,rad=0.3'`
- Light dashed outer border around entire diagram
- Reference numerals table at bottom (3 columns, fontsize 7.2)

**Figure 2 — Control/Optimization Pipeline (Flowchart):**
- Layout: 14×22 inch canvas, vertical top-to-bottom flow
- Left-side stage bands using `FancyBboxPatch` per stage (Setup / Stage 2 / VQE Loop / Validation / Cert & Filing)
- Stage band colors match zone palette; label rotated 90 degrees inside band
- Process boxes: `FancyBboxPatch` rounded rect, zone color scheme
- Decision diamonds: `plt.Polygon` with 4 points `[top, right, bottom, left]`
- YES/NO branch labels beside arrows in green (#1E8449) and red (#CB4335)
- Dashed `FancyBboxPatch` outline around the VQE optimization loop sub-section
- Right-side panel for feedback engine (Adversarial Optimization Engine) with its own header strip
- Feedback arrows use curved `connectionstyle='arc3,rad=0.3'` and dashed `linestyle='--'`
- Reference numerals + 3-line caption at bottom

**Figure caption placement: BELOW the figure**
**Figure explanation: max 5 lines, immediately below caption**

**C. DATA-DRIVEN FIGURES (5 figures: Figure 3 through Figure 7)**

MANDATORY DESIGN RULES for every figure:
- 2×2 multi-panel layout: `fig, axes = plt.subplots(2, 2, figsize=(16, 12))`
- Panel labels: (a), (b), (c), (d) in top-left of each subplot
- Rich color palettes — NOT default matplotlib:
  ```python
  colors = ['#2196F3', '#E91E63', '#4CAF50', '#FF9800', '#9C27B0', '#00BCD4']
  ```
- `fill_between` shading under lines with alpha=0.15
- Data annotations: percentages on bars, peak values on lines, R² on scatter
- `edgecolor='white'`, `linewidth=1.2` on bar charts
- Subtle grid: `ax.grid(True, alpha=0.15, linestyle='--')`
- Spine removal: top and right spines off
- Save: `dpi=300, bbox_inches='tight', facecolor='white'`
- **ALL data from datasets — ZERO hardcoded values**

Figure assignments (Claude designs specific panels based on patent domain):
- Figure 3: Validation performance (accuracy, compliance distribution, adherence, coverage)
- Figure 4: Signal gating analysis (response times, decision outcomes, violation breakdown, efficiency)
- Figure 5: Permission envelope dynamics (adaptive bounds, violation rates, tightness vs detection, cumulative)
- Figure 6: Closed-loop verification (commanded vs actual, error distribution, feedback latency, compliance rates)
- Figure 7: Prior art benchmarking (capability comparison, response time log-scale, radar coverage, composite scores)
- Each figure gets a caption + 2-sentence explanation

**D. TABLES (3 tables — as Word-formatted .docx, NOT markdown or PNG)**

Generate tables using `python-docx`:
```python
pip install python-docx
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
```

Table styling requirements:
- Blue header row (#1565C0 background, white bold text)
- Alternating row colors (#E3F2FD / white)
- Clean borders (#B0BEC5, 0.5pt)
- Cell padding for readability
- Font: 10pt body, 10.5pt header
- Auto-fit to page width
- Output as `.docx` file — user copies table directly into patent Word doc

Table 1: System Performance Metrics Summary (all values computed from dataset)
Table 2: Comparative Capability Matrix vs. Prior Art
Table 3: Dimension-wise Constraint Validation Results

Each table gets a caption + 1–2 sentence explanation.

**E. SECTION 8 TEXT FORMAT**
- NO [00XX] paragraph numbering — Section 8 uses regular prose
- Brief 2-sentence explanations per figure/table (detailed explanations go in Section 7)
- Structure: opening paragraph → figures with captions → tables with captions → closing paragraph
- Physical-technical integration compliance throughout
- Captions use "FIG. X" and "TABLE X" format for patent style

### Per-Patent Customization Points
User may modify in-chat: number of diagrams/graphs/tables, dataset preference, domain-specific visualization types. These apply to current chat only.

---

## FRAMEWORK 2: Sections 6 & 7 — Working Principle and Detailed Description

### What Claude Does

1. **Receive Section 8 output** from user (pasted from Antigravity)
2. **Cross-reference with original patent** (Sections 1–5, 9)
3. **Generate Antigravity prompt** for Sections 6 and 7 that references specific Section 8 results

### Key Rules
- **Section 6 (Working Principle):** [000X] numbering. 8–12 paragraphs. High-level operational flow. No figure references.
- **Section 7 (Detailed Description):** Continues numbering from Section 6. 15–25 paragraphs. Deep component-level detail. References Section 8 FIG./TABLE with specific numeric results.
- Both must maintain physical-technical integration compliance — hardware references throughout
- Weave in actual numbers from Section 8 (latencies, detection rates, R² values, etc.)
- Every patent objective (Section 5) must be addressed
- Every protection aspect (Section 9) must have dedicated technical detail in Section 7

---

## FRAMEWORK 3: Refinement and Validation

### What Claude Does

1. **Receive pasted Sections 6 & 7** from user
2. **Validate against all guidelines:**
   - Physical-technical integration — flag any "pure software" paragraphs
   - Technical consistency with Section 8 results
   - Objective coverage (Section 5) and protection aspect coverage (Section 9)
   - AI-detection risk — sentence start patterns, parallel structures, banned phrases
   - Paragraph numbering correctness
   - Figure/table reference completeness
3. **Produce validation report** with scorecard
4. **Deliver refined sections** with specific fixes applied

### Validation Checklist
```
□ Every objective (Section 5) addressed in at least one paragraph
□ Every protection aspect (Section 9) has supporting detail
□ No paragraph describes purely algorithmic process without physical tie-in
□ Section 8 results referenced in Section 7 with specific numbers
□ Paragraph numbering sequential and correct
□ No 3+ consecutive paragraphs starting with same structure
□ No banned phrases present
□ Physical components mentioned in >60% of paragraphs
□ All FIG. and TABLE panels referenced in Section 7
□ Hedging language used appropriately
```

---

## FRAMEWORK 4: Patentability Check

### What Claude Does

1. **Receive the complete finalized patent document** (all sections)
2. **Perform a comprehensive patentability audit** across three dimensions:
   - Novelty assessment
   - Patentability assessment
   - Physical-technical integration compliance (deep check)
3. **Perform writing quality audit**
4. **Deliver a detailed patentability report**

### Dimension 1: Novelty Check

Claude must verify:
- The invention is **distinct from every prior art reference** listed in Section 3
- For each prior art entry, confirm that the patent document explicitly identifies a **technical limitation** that the present invention overcomes
- Check that the core novelty claim is **not merely an incremental improvement** but introduces a fundamentally different technical approach
- Verify that Section 8 experimental results demonstrate **measurable performance differences** vs. prior art (not just theoretical claims)
- Cross-check Section 9 (Aspects Needing Protection) — each aspect must represent something NOT found in any cited prior art

Output format:
```
NOVELTY CHECK:
[For each prior art reference in Section 3:]
  - Reference: [name/number]
  - Cited limitation: [what Section 3 says]
  - How invention overcomes it: [from Sections 6/7/8]
  - Novelty status: NOVEL / OVERLAPPING / AT RISK
  
Overall novelty verdict: [NOVEL / NEEDS STRENGTHENING / AT RISK]
Specific concerns: [if any]
```

### Dimension 2: Patentability Assessment

Claude must verify:
- The invention has **industrial applicability** — it solves a real technical problem
- The invention involves an **inventive step** — it is not obvious to a person skilled in the art
- The claims (Section 9) are **clear, specific, and technically supported** by Sections 6/7/8
- The description is **sufficient for reproduction** — a skilled person could build the system from Sections 6 and 7
- The experimental validation (Section 8) provides **sufficient evidence** for the claimed advantages

Output format:
```
PATENTABILITY CHECK:
  Industrial applicability: [PASS/FAIL + evidence]
  Inventive step: [PASS/FAIL + reasoning]
  Claim clarity (Section 9): [PASS/FAIL + per-claim assessment]
  Sufficiency of description: [PASS/FAIL + any gaps]
  Experimental support: [PASS/FAIL + coverage analysis]
  
Overall patentability verdict: [PATENTABLE / NEEDS REVISION / NOT PATENTABLE]
```

### Dimension 3: Physical-Technical Integration Deep Check

This is the MOST CRITICAL check. Claude must:

**Per-paragraph scan of Sections 6, 7, and 8:**
- Flag any paragraph that describes a purely algorithmic/software process without physical tie-in
- Flag any paragraph that could be interpreted as "computer programme per se"
- Flag any use of "simulation-based", "software module", "algorithm" without accompanying physical effect
- Flag any architecture description that shows only software blocks without hardware

**Specific physical-technical integration tests:**
```
TEST 1: Physical Hardware Presence
  - Does Section 6 describe physical sensors and actuators? [YES/NO]
  - Does Section 7 detail hardware components (relays, valves, transducers)? [YES/NO]
  - Does Section 8 measure physical parameters (latency in ms, flow rates, spatial tolerance)? [YES/NO]

TEST 2: Technical Effect Beyond Software
  - Does the invention produce a physical effect (blocking energy, preventing discharge)? [YES/NO]
  - Is the technical effect different from normal software-hardware interaction? [YES/NO]
  - Would the invention work without the specific hardware described? [YES/NO — must be NO]

TEST 3: Not "Computer Programme Per Se"
  - Can any section be read as describing only an algorithm? [flag paragraphs]
  - Is the system described as "fully simulation-based"? [must be NO]
  - Are "no physical sensors or energy devices required" anywhere? [must be NO]

TEST 4: Language Compliance
  - Count of paragraphs referencing physical hardware: [N out of total]
  - Percentage of paragraphs with physical tie-in: [must be >60%]
  - List of paragraphs with weakest physical connection: [paragraph numbers]
```

Output format:
```
PHYSICAL-TECHNICAL INTEGRATION CHECK:
  Test 1 (Physical Hardware): [PASS/FAIL]
  Test 2 (Technical Effect): [PASS/FAIL]
  Test 3 (Not Programme Per Se): [PASS/FAIL]
  Test 4 (Language Compliance): [X% physical tie-in]
  
  Flagged paragraphs: [list with specific concerns]
  Suggested fixes: [for each flagged paragraph]
  
  Overall integration verdict: [PASS / NEEDS REVISION / FAIL]
```

### Dimension 4: Writing Quality & AI-Detection Audit

Claude must scan for:
- **Banned phrases** (see `references/writing-guidelines.md`) — list any found with paragraph numbers
- **Repetitive sentence structures** — flag 3+ consecutive paragraphs with same opening pattern
- **Parallel constructions** — flag overly symmetrical paragraph pairs
- **Vague claims** — flag any assertion without a specific numeric or technical backing
- **Tone consistency** — verify academic technical tone throughout, no informal language

Output format:
```
WRITING QUALITY AUDIT:
  Banned phrases found: [list with locations]
  Sentence pattern issues: [specific paragraphs]
  Vague claims: [paragraphs lacking specificity]
  AI-detection risk level: LOW / MODERATE / HIGH
  
  Specific fixes recommended: [list]
```

### Mandatory Fix Delivery (CRITICAL)

For EVERY issue flagged in ANY dimension above, Claude MUST provide exact replacement text. No vague suggestions — provide copy-paste-ready fixes.

**Format for each fix:**
```
FIX #[N]: [paragraph number] — [issue category] — [CRITICAL or RECOMMENDED]
  CURRENT:  "[exact sentence(s) from the document that need changing]"
  REPLACE:  "[exact rewritten sentence(s) ready to paste]"
  REASON:   [one-line explanation of why this change is needed]
```

**Examples:**
```
FIX #1: [0023] — Weak physical tie-in (patentability risk) — CRITICAL
  CURRENT:  "Each compliance record is serialized with a cryptographic timestamp to support tamper-evident audit trails."
  REPLACE:  "Each compliance record—encoding the relay state, actuator channel identifier, and sensor-derived feedback residual—is serialized with a cryptographic timestamp to support tamper-evident audit trails traceable to specific physical actuation events."
  REASON:   Original sentence describes only data processing with no physical reference. Fix ties the record to relay hardware and sensor measurements.

FIX #2: [0015] — AI-detection pattern (5 consecutive "The [X]..." starts) — RECOMMENDED
  CURRENT:  "The temporal synchronization module compares each pending command's requested execution timestamp..."
  REPLACE:  "Comparison of each pending command's requested execution timestamp against the crop-specific operational window is performed by the temporal synchronization module."
  REASON:   Paragraphs [0011]–[0015] all started with "The [component]..." — restructured to break detectable pattern.

FIX #3: [0016] — Missing figure reference (FIG. 3(d) unreferenced) — CRITICAL
  CURRENT:  "The processor outputs a per-dimension pass/fail vector that feeds directly into the gating decision logic."
  REPLACE:  "FIG. 3, panel (d) synthesizes these rates into a radar visualization of multi-dimensional envelope coverage, confirming near-complete spatial coverage with temporal enforcement representing the most operationally variable dimension. The processor outputs a per-dimension pass/fail vector that feeds directly into the gating decision logic."
  REASON:   FIG. 3(d) was generated in Section 8 but never referenced in Section 7.

FIX #4: [Section 8, para 3] — Banned phrase detected — CRITICAL
  CURRENT:  "It is worth noting that the system achieves 87% detection."
  REPLACE:  "The system achieves 87% detection across the combined evaluation window."
  REASON:   "It is worth noting" is a banned AI-detectable filler phrase.
```

**Rules:**
- Only provide fixes for GENUINE issues — do NOT manufacture problems or force changes
- If a section is technically correct, compliant, and well-written, say so and move on
- There is NO compulsion to produce fixes — a clean document with zero issues is the ideal outcome
- Every flagged issue gets a numbered fix — no exceptions for actual problems
- CURRENT text must be an EXACT quote from the document (copy-paste match)
- REPLACE text must be drop-in ready — user replaces directly in Word
- Each fix marked as CRITICAL (must apply before filing) or RECOMMENDED (improves quality)
- Fixes grouped by dimension: physical-technical fixes first, then novelty, then writing
- If no issues found in a dimension, explicitly state "No fixes required"
- If overall verdict is READY with zero issues, state this clearly and do NOT invent fixes just to appear thorough

### Final Patentability Report

```
╔══════════════════════════════════════════╗
║      PATENTABILITY REPORT SUMMARY       ║
╠══════════════════════════════════════════╣
║ Novelty:              [NOVEL / AT RISK] ║
║ Patentability:        [PASS / FAIL]     ║
║ Physical-Technical:   [PASS / FAIL]     ║
║ Writing Quality:      [PASS / NEEDS FIX]║
╠══════════════════════════════════════════╣
║ OVERALL VERDICT:      [READY / REVISE]  ║
╚══════════════════════════════════════════╝

Total fixes provided: [N]
Critical (must fix): [N]
Recommended (optional): [N]
```

---

## Context Maintenance Protocol

**Between frameworks, Claude must:**
1. Summarize what was produced in the completed framework
2. Carry forward the PATENT_CONTEXT object with updated fields
3. When starting a new framework, reference what the previous framework produced
4. Per-chat modifications apply ONLY to current generation — do not alter base skill

---

## How to Trigger This Skill

**In any new chat, say one of:**
- "Start patent framework"
- "Activate patent builder"
- "Fill patent sections 6, 7, and 8"
- "Begin framework 1 for my patent"
- "Run patentability check"

Then upload your revised patent document.

**To move between frameworks:**
- "Move to framework 2" / "Start framework 2"
- "Framework 3" / "Refine sections 6 and 7"
- "Framework 4" / "Run patentability check" / "Check patentability"

---

## Quick Reference

| Framework | Input | Output | Purpose |
|-----------|-------|--------|---------|
| 1 | Revised patent doc | Antigravity prompt for Section 8 | Experimental validation (figures, tables, text) |
| 2 | Section 8 output + patent doc | Antigravity prompt for Sections 6 & 7 | Working principle & detailed description |
| 3 | Sections 6 & 7 content | Refined content + validation report | Quality assurance and compliance |
| 4 | Complete patent document | Patentability report | Novelty, patentability, physical-technical integration, writing audit |
