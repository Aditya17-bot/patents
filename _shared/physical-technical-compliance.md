# Physical-Technical Integration Compliance Reference

## Core Patentability Principle

Under Indian patent law, inventions must demonstrate a **technical effect beyond normal software-hardware interaction**. An invention risks rejection if:
1. It is described as purely software-based with no physical hardware interaction
2. The technical effect is limited to running code on a processor
3. There are no physical sensors, actuators, or energy systems involved
4. The validation is "fully simulation-based" with "no physical sensors or energy devices required"

The invention must NOT read as a "computer programme per se" or "algorithm" — it must be framed as a **physical-technical apparatus** with measurable hardware-level effects.

**CRITICAL: Never explicitly mention this compliance requirement or its legal basis in the patent document itself. The document must naturally demonstrate physical-technical integration through its language and content — not by citing the legal test it aims to satisfy.**

## How to PASS

### Language Patterns That PASS
- "The hardware-level signal gating unit physically blocks electrical activation signals"
- "Sensor-derived actuation feedback confirms physical execution"
- "The system intercepts hydraulic control signals prior to energy transmission"
- "Real-time GNSS positioning data validates spatial boundaries of physical operations"
- "The cyber-physical enforcement layer prevents unauthorized material discharge"

### Language Patterns That FAIL
- "The algorithm processes data and generates output"
- "The software module analyzes patterns and produces recommendations"
- "The system computes optimal parameters using machine learning"
- "The neural network classifies input features"
- "The platform provides analytics and visualization"

### Remediation Strategies

If a paragraph sounds too "software-only":
1. Add the physical component it interfaces with (e.g., "transmitted to the pressure valve actuator")
2. Specify the physical signal type (electrical, hydraulic, pneumatic, optical)
3. Reference sensor hardware (GNSS receivers, flow meters, pressure transducers)
4. Describe the physical effect (blocking energy discharge, preventing material flow, interrupting circuit)
5. Use "cyber-physical" framing — the software controls physical processes, not just data

### Per-Domain Physical Elements

| Domain | Physical Components | Signal Types | Technical Effects |
|--------|-------------------|--------------|-------------------|
| Agriculture | Sprayers, pumps, valves, GNSS | Hydraulic, electrical, pneumatic | Material discharge prevention, spatial boundary enforcement |
| Healthcare | Sensors, infusion pumps, monitors | Electrical, optical, ultrasonic | Dosage control, physiological signal validation |
| IoT/Smart Systems | Actuators, relays, sensors | Electrical, wireless, thermal | Energy gating, environmental control |
| Forensics | Imaging sensors, chain-of-custody hardware | Optical, magnetic, electrical | Evidence integrity preservation, tamper detection |
| Quantum | Qubit controllers, cryogenic systems | Microwave, optical, magnetic | Quantum state manipulation, decoherence prevention |
| Energy/Carbon | Grid controllers, renewable systems | Electrical, thermal | Load balancing, carbon-aware scheduling |

## Patentability Check Criteria (Framework 4)

### Novelty Requirements
- Invention must be distinct from ALL cited prior art
- Each prior art limitation must be explicitly overcome
- Core novelty must be fundamentally different approach, not incremental
- Section 8 must show measurable performance gap vs prior art
- Every protection aspect must represent something absent from prior art

### Inventive Step Requirements
- Not obvious to a person skilled in the art
- Combination of known elements must produce unexpected technical effect
- Technical advantages must be quantitatively demonstrated

### Industrial Applicability
- Solves a real technical problem in a specific industry
- Can be manufactured or used in practice
- Description sufficient for a skilled person to reproduce

### Sufficiency of Description
- Sections 6+7 together must enable reproduction without undue experimentation
- All components must be described with enough specificity
- Operating parameters, tolerances, and interfaces must be defined

## Red Flags in Experimental Validation (Section 8)

These patterns in Section 8 will trigger patentability rejection:
- Using only synthetic/simulated data with no physical parameters
- Metrics limited to accuracy, precision, recall (pure ML metrics) without physical performance
- No reference to sensor noise, latency, or physical tolerances
- Architecture diagrams showing only software blocks
- Tables comparing only algorithmic performance

### Fix: Always Include
- Physical response time (milliseconds for actuator response)
- Sensor accuracy/tolerance ranges
- Energy consumption metrics
- Physical throughput (flow rates, signal frequencies)
- Hardware resource utilization
- Comparison with physical baselines (not just algorithmic baselines)
