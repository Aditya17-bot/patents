# Section 3(k) Compliance Reference
## Indian Patents Act — Computer-Related Inventions

---

## What Section 3(k) Says

Under the Indian Patents Act 1970, Section 3(k) states that the following are NOT patentable:

> "a mathematical or business method or a computer programme per se or algorithms"

The key phrase is **"per se"** — meaning a computer program BY ITSELF, in isolation, with no technical effect beyond what software normally does when run on standard hardware.

The Indian Patent Office (IPO) Guidelines for Computer Related Inventions (CRI Guidelines, revised 2017) clarify that an invention involving a computer program IS patentable if it produces a **technical effect** or has a **technical contribution** beyond the normal physical interactions between the program and the computer.

---

## What IS Rejectable Under 3(k)

The following framings WILL trigger a Section 3(k) rejection:

| Framing | Why It Fails |
|---------|--------------|
| "A method implemented in software for..." | Pure software method — no hardware anchor |
| "A computer program that calculates..." | Programme per se — no technical effect |
| "An algorithm for optimizing..." | Mathematical method / algorithm per se |
| "A system comprising a processor configured to run..." | Processor alone is not sufficient hardware differentiation |
| "A business method for managing..." | Business method exclusion |
| No physical sensor, actuator, or measurement device mentioned | No technical effect beyond software |
| "Fully simulation-based" or "no physical hardware required" | Confirms programme per se |

---

## What IS Patentable (How to Frame Correctly)

An invention passes Section 3(k) scrutiny if it meets **at least one** of the following:

1. **Produces a technical effect** — e.g., physical signal blocking, energy interception, sensor-driven actuation, hardware-level gating
2. **Has technical contribution** — the combination of hardware + software produces an effect not achievable by either alone
3. **Is a cyber-physical apparatus** — the invention is described as a system integrating computational elements with physical hardware components
4. **Involves industrial applicability** — solves a real-world engineering problem with measurable physical outcomes

---

## Compliant Framing Patterns (Use These)

### Titles
- "... Apparatus for ..." (apparatus = physical device)
- "... Cyber-Physical System for ..."
- "... Hardware-Integrated Method for ..."
- "A [Technical-Domain] Device Comprising ..."

### Field / Area (Section 2)
Always include at least one of:
- "...integrated with physical sensor arrays..."
- "...implemented on embedded FPGA hardware..."
- "...employing actuator-level signal interception..."
- "...utilizing quantum processor hardware operating at [X] mK..."

### Summary / Background (Section 4)
- Frame the invention as a **system** or **apparatus**, not a program or algorithm
- Name at least one physical component early: sensor, actuator, transducer, relay, QPU, FPGA
- Describe the **physical effect** the invention produces

### Objectives (Section 5)
Every objective must describe a **technical capability**, not a software feature:
- GOOD: "To provide a hardware-gated actuator enforcement mechanism that physically intercepts..."
- BAD: "To provide a software module that detects..."

### Protection Aspects (Section 9)
At least 3 of the 5 aspects must reference hardware components or physical interactions:
- "Cyber-physical apparatus comprising [named hardware]..."
- "Method of [physical process] using [named hardware]..."
- "Embedded firmware module for [measurable validation]..."

---

## Banned Phrases — NEVER Use in Patent Document

These phrases will invite 3(k) scrutiny or signal non-compliance:

| Banned Phrase | Use Instead |
|---------------|-------------|
| "computer programme" | "apparatus", "system", "cyber-physical device" |
| "algorithm for" | "method implemented in [hardware] for" |
| "software module" | "firmware module", "embedded control unit" |
| "simulation-based" | "evaluated using field-representative sensor data" |
| "virtual" | "hardware-validated", "physically implemented" |
| "no physical hardware required" | [never use — delete entirely] |
| "mathematical method" | "computational procedure executed by [hardware]" |
| "business method" | [reframe entirely around technical apparatus] |
| "program per se" | [never use] |

---

## Mandatory Hardware Anchors (At Least One Required Per Section)

The following hardware components, when named explicitly, anchor the invention outside 3(k):

**Sensing hardware:**
- Physical sensors (UV-Vis spectrometer, NMR sensor, GC-MS, GNSS receiver, accelerometer, LiDAR)
- Analog-to-digital converters (ADC), signal conditioning units

**Processing hardware:**
- FPGA (Field-Programmable Gate Array) — explicitly named
- NISQ Quantum Processor / QPU operating at cryogenic temperature
- ASICs, DSP chips, microcontrollers with specific part characteristics

**Actuation / enforcement hardware:**
- Relays, solenoid valves, flow control gates, signal gating units
- Servo motors, actuators, pump controllers

**Security / attestation hardware:**
- TPM (Trusted Platform Module) — TPM 2.0 specification
- HSM (Hardware Security Module)
- Tamper-evident enclosures (FIPS 140-2 Level 3 rated)

**Communication hardware:**
- Physical bus interfaces (SPI, I2C, CAN bus)
- RF transceivers, LoRa modules, cellular modems

---

## The 3(k) Compliance Test — Run Before Finalizing Any Section

Ask these 5 questions about every section drafted. ALL must be YES:

```
□ 1. Is the invention described as an apparatus/system/device — not a program or algorithm?
□ 2. Is at least one physical hardware component named explicitly?
□ 3. Does the invention produce a measurable physical effect (not just data output)?
□ 4. Would the invention fail to function if the hardware were removed?
□ 5. Is the word "per se" (or any equivalent) absent from the document?
```

If ANY answer is NO — revise before proceeding.

---

## Examiner Red Flags to Avoid

Indian Patent Office examiners specifically look for:

1. **"System comprising a processor and memory"** alone — not sufficient, processor is generic
2. **Flowcharts showing only software steps** — must show hardware interaction nodes
3. **Claims that read as pure method steps** without hardware anchoring language
4. **Section 8 (Experimental Results) showing only simulation data** — must include physical parameter measurements (latency in ms, sensor readings, physical signal levels)
5. **Architecture diagrams with only software blocks** — must show hardware-software co-design

---

## IPO CRI Guidelines Quick Reference (2017 Revision)

The revised 2017 guidelines established a **three-stage test** for CRI patentability:

**Stage 1 — Proper Claim Construction:**
Read the claim as a whole. Identify what is actually being claimed.

**Stage 2 — Determine if the Claimed Subject Matter Falls Under Excluded Categories:**
- Is it a mathematical method? → 3(k) applies
- Is it a business method? → 3(k) applies
- Is it a computer program per se? → 3(k) applies
- Is it an algorithm? → 3(k) applies

**Stage 3 — Check for Technical Effect / Technical Contribution:**
If the claimed subject matter involves a computer program but ALSO produces a technical effect beyond normal hardware-software interaction → NOT excluded under 3(k)

**Technical effects that overcome 3(k):**
- Higher speed
- Reduced memory usage with physical consequence
- More efficient computer operation
- **Physical-world effects** (preferred — strongest argument)

---

## CRITICAL INTERNAL RULE

**Section 3(k) must NEVER be explicitly mentioned anywhere in the generated patent document.**

Do not write:
- "This invention complies with Section 3(k)..."
- "To avoid Section 3(k) rejection..."
- "Per the Indian Patents Act Section 3(k)..."

Section 3(k) awareness governs HOW you draft — it must be invisible in the output.
The compliance is baked into the apparatus framing, hardware anchoring, and technical effect language.
The patent document must read as a natural technical disclosure, not a defensive legal response.
