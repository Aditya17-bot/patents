---
name: patent-draft-builder
description: >
  Builds patent draft documents (Sections 1-5 and 9) from a user-provided patent idea.
  Use this skill whenever the user mentions "patent draft", "patent document", "patent sections 1-5",
  "write a patent", "prepare patent application", "draft patent", "patent idea", or provides a title,
  tech stack, and domain for a new invention and wants a structured patent document. Also triggers on
  "prior art search", "patentability check", "Section 3(k) compliance", "patent novelty assessment",
  or "Indian patent application". This skill handles Sections 1 through 5 and Section 9 only.
  Sections 6, 7, and 8 are intentionally left empty for the patent-section-builder skill.
  Do NOT use for trademark, copyright, design patent, or non-technical patent queries.
  Do NOT use when the user explicitly asks only for Sections 6, 7, or 8.
---

# Patent Draft Builder (Sections 1–5, 9)

## Purpose

This skill produces a professional Indian patent application draft document (.docx) covering
Sections 1, 2, 3, 4, 5, and 9. Sections 6, 7, and 8 are left empty with placeholder headings
because a separate skill (patent-section-builder) handles those sections.

The output must comply with Indian Patent Office conventions and avoid Section 3(k) rejection
(i.e., the invention must NOT be framed as a "computer programme per se" or a pure algorithm
with no technical effect beyond normal software-hardware interaction).

---

## Input Requirements

Before starting, collect these from the user. If any are missing, ask:

| Field | Description | Example |
|-------|-------------|---------|
| **Title** | Invention title (technical, descriptive) | "Quantum-Inspired Adaptive Cache Coherence..." |
| **Domain** | Technical field | Precision agriculture, IoT healthcare, etc. |
| **Tech Stack** | Key technologies involved | Sensors, FPGA, ML models, actuators, etc. |
| **Problem Statement** | What gap or limitation does this solve? | "Current systems lack real-time validation..." |
| **Core Innovation** | What is novel about the approach? | "Cyber-physical signal gating at actuator level" |
| **Physical/Hardware Elements** | Any sensors, actuators, hardware involved | GNSS receivers, flow meters, gating units |

**Critical**: The user MUST describe at least one physical/hardware component or measurable
technical effect to ensure Section 3(k) compliance. If the idea is purely software-based, guide
the user to reframe it with a cyber-physical or hardware-integrated angle before proceeding.

---

## Workflow (Follow This Exactly)

### Phase 1: Patentability Pre-Check

Before drafting anything, perform a patentability assessment:

1. **Web Search for Prior Art**
   - Run 4–6 targeted web searches using different query strategies:
     - `"[core technique] patent"` (e.g., "actuator signal gating agricultural patent")
     - `"[domain] [innovation keyword] prior art"` (e.g., "precision agriculture control enforcement prior art")
     - `"[specific technology] [application]"` on Google Scholar or IEEE
     - Search Google Patents, USPTO, EPO, and Indian Patent Office (IPAIRS)
   - For each relevant result, use `web_fetch` to read the full page and extract details.

2. **Novelty Assessment**
   Evaluate whether the invention is:
   - **Novel**: No single prior reference discloses the same combination of elements
   - **Inventive Step**: The combination is non-obvious to a person skilled in the art
   - **Not Section 3(k)**: The invention has a technical effect beyond normal software-hardware interaction

3. **Report to User**
   Present a brief patentability summary:
   - 3–5 closest prior art references found
   - Why the invention is distinguishable from each
   - Section 3(k) compliance status
   - Proceed / Revise recommendation

   If the invention appears to fall under Section 3(k) or lacks novelty, advise the user
   on how to reframe before proceeding.

### Phase 2: Section-by-Section Drafting

Once patentability is confirmed, draft each section following the structure below.

---

## Section Headings (Use Exactly as Listed — Bold, Times New Roman 13pt)

The document must use these exact section headings in this exact order:

1. Title of the Invention
2. Field / Area of the Invention
3. Prior Patents and Publications from Literature
4. Summary and Background of the Invention
5. Objectives of the Invention
6. Working Principle of the Invention
7. Detailed Description of the Invention
8. Experimental Results / Technical Validation
9. WHAT ASPECT(S) OF THE INVENTION NEED(S) PROTECTION

---

## Section Content Rules

#### Section 1: Title of the Invention
- Must be a single, descriptive, technical phrase
- Should include the technical domain and the nature of the system/method
- Avoid generic terms like "system" or "method" alone — qualify them
- Pattern: `[Technical-Adjective] [Core-Mechanism] [Application-Domain] [System/Apparatus/Method]`

#### Section 2: Field / Area of the Invention
- Two sentences maximum
- First sentence: broad technical field ("The present invention relates to...")
- Second sentence: specific sub-field with technical qualifier ("More particularly, the invention pertains to...")
- Include at least one hardware or physical-process reference to anchor technical grounding

#### Section 3: Prior Patents and Publications from Literature
- **This is the most research-intensive section.**
- Perform thorough web searches (minimum 6 searches, more if needed):
  - Search Google Patents for relevant US, EP, IN patents
  - Search Google Scholar / IEEE / Elsevier for journal publications
  - Search the Indian Patent Office (IPAIRS) for Indian applications
- Build a table with exactly 5 columns:
  - `Reference` (patent number or journal name)
  - `Year`
  - `Type` (Patent or Journal)
  - `Core Contribution` (what the reference teaches)
  - `Technical Limitation w.r.t Present Invention` (what gap it leaves that your invention fills)
- Include 6–8 patents and 5–7 journal articles (13 total minimum)
- Each "Technical Limitation" must clearly show why that reference does NOT anticipate the present invention
- Use real patent numbers and real journal names wherever possible from search results
- If exact matches are not found, use the closest references and clearly state their limitations

#### Section 4: Summary and Background of the Invention
- Single paragraph, 4–6 sentences
- Structure: Context → Problem → Gap → Solution → Transformation
- Open with the domain context and current state of technology
- Identify the specific technical limitation in existing systems
- Introduce the invention as the solution
- End with how this transforms the field (e.g., "from advisory analytics to active enforcement")
- Use precise technical language — avoid marketing or vague claims

#### Section 5: Objectives of the Invention
- **Exactly 3 bullet points** (numbered 1, 2, 3)
- Each objective must begin with "To provide..." or "To enable..." or "To validate..." etc.
- Each must describe a concrete, measurable technical capability
- At least one objective must reference a physical/hardware interaction (technical grounding anchor)
- Keep each objective to a single sentence of 15–25 words

#### Sections 6, 7, 8: (Left Empty — Placeholders Only)
- Include only the section headings using the exact names from the heading list above:
  - "6. Working Principle of the Invention"
  - "7. Detailed Description of the Invention"
  - "8. Experimental Results / Technical Validation"
- Add a placeholder note under each: "[To be completed using the Patent Section Builder skill]"
- Do NOT generate any content for these sections.

#### Section 9: WHAT ASPECT(S) OF THE INVENTION NEED(S) PROTECTION
- **Exactly 5 bullet points** (numbered 1–5)
- Each point describes one specific claim-worthy technical aspect
- Focus on: architecture, method steps, hardware interactions, data flows, enforcement mechanisms
- Each point should be a concise noun phrase (8–20 words), not a full sentence
- These should map to the strongest patentable elements of the invention

---

## Writing Guidelines

### Tone and Style
- **Academic and technical**: Write as if authoring a peer-reviewed engineering paper
- **Precise terminology**: Use domain-specific technical terms, not layperson language
- **Active technical voice**: "The system intercepts..." not "It is intercepted by..."
- **No marketing language**: Avoid "revolutionary", "cutting-edge", "groundbreaking"
- **No AI-detection patterns**: Vary sentence structure, avoid repetitive transitions like
  "Furthermore", "Moreover", "Additionally" in sequence. Use natural technical prose flow.

### Section 3(k) Compliance (Critical — Internal Only)
Every draft must satisfy ALL of the following:
- At least one physical sensor, actuator, or hardware component is named
- The invention produces a measurable technical effect (e.g., physical signal blocking, sensor feedback)
- The system is framed as a cyber-physical apparatus, NOT a software algorithm
- Terms like "computer programme per se", "simulation-based", or "no physical hardware required"
  must NEVER appear

**CRITICAL: Section 3(k) must NEVER be explicitly mentioned anywhere in the generated patent
document.** Do not reference "Section 3(k)", "3(k) compliance", "Indian Patents Act Section 3(k)",
or any variation in the title, field description, summary, objectives, or claim aspects.
Section 3(k) awareness is an internal drafting guideline — it governs HOW you write, but the
patent document itself must read as a natural technical disclosure without any defensive legal
references to patentability exclusions. The compliance must be baked into the framing, not
stated explicitly.

### Plagiarism Prevention
- Never copy phrases from prior art references — always paraphrase
- Use original technical phrasing for all descriptions
- Vary sentence structure across sections

---

## Document Generation

After drafting all sections, generate a `.docx` file using Python (python-docx).
Read `/mnt/skills/public/docx/SKILL.md` for the document creation instructions.

### MANDATORY Typography Specifications

Apply these specifications to EVERY element of the generated document:

**Headings (Section titles 1–9):**
- Font: Times New Roman
- Size: 13pt
- Style: Bold
- Alignment: Left

**Body text (all content inside sections):**
- Font: Times New Roman
- Size: 11pt
- Style: Regular
- Alignment: Justified (WD_ALIGN_PARAGRAPH.JUSTIFY)

**Table content:**
- Font: Times New Roman
- Size: 10pt (header row 10.5pt bold)
- Alignment: Left for body cells, Center for header cells

**Implementation using python-docx:**
```python
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def add_section_heading(doc, number, title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(f"{number}. {title}")
    run.bold = True
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    # Force font via XML for full compatibility
    r = run._r
    rPr = r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), 'Times New Roman')
    rFonts.set(qn('w:hAnsi'), 'Times New Roman')
    rPr.append(rFonts)
    return p

def add_body_paragraph(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)
    r = run._r
    rPr = r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), 'Times New Roman')
    rFonts.set(qn('w:hAnsi'), 'Times New Roman')
    rPr.append(rFonts)
    return p
```

**Additional document settings:**
- A4 page size (11906 x 16838 DXA)
- 1-inch margins all around
- A properly formatted table for Section 3 with borders and header row shading (#1565C0 header)
- Numbered lists for Section 5 (3 items) and Section 9 (5 items)
- Placeholder text for Sections 6, 7, 8

Save the final document to `/mnt/user-data/outputs/` and present it to the user.

---

## Quality Checklist (Verify Before Delivering)

Before presenting the document, verify:
- [ ] Section headings match the exact 9-heading list above (bold, Times New Roman 13pt)
- [ ] All body text is Times New Roman 11pt, justified alignment
- [ ] Section 1: Title is technical, specific, and domain-qualified
- [ ] Section 2: Exactly 2 sentences, includes hardware/physical reference
- [ ] Section 3: Table has 13+ entries (6+ patents, 5+ journals), all 5 columns filled
- [ ] Section 4: Single paragraph, 4–6 sentences, context→problem→solution flow
- [ ] Section 5: Exactly 3 numbered objectives, each with a physical/technical anchor
- [ ] Sections 6, 7, 8: Only headings and placeholder text — no generated content
- [ ] Section 9: Exactly 5 numbered claim aspects, heading in ALL CAPS as specified
- [ ] No Section 3(k) violations anywhere in the document (enforced silently — never mention 3(k) in the document text)
- [ ] Technical, academic tone throughout — no AI-pattern language
- [ ] All prior art references sourced from actual web search results
