# Patent Writing Guidelines — Anti-Detection & Academic Standards

## Sentence Structure Variation

### DO: Mix sentence types
- Short declarative: "The gating controller operates at 12 ms latency."
- Compound: "While the spatial normalization engine aligns positional data, the temporal synchronization module independently verifies execution windows."
- Complex with subordinate clauses: "Because the feedback verification module operates in closed-loop mode, actuation errors exceeding the 2.3% tolerance threshold are detected within a single control cycle."

### DON'T: Parallel structures across paragraphs
- BAD: "The first module processes X. The second module analyzes Y. The third module validates Z."
- GOOD: "Processing of X occurs within the intake module. Downstream, Y undergoes analysis through a dedicated evaluation pipeline. Validation of Z is performed by cross-referencing actuator feedback against the computed permission envelope."

## Vocabulary Rules

### Banned Phrases (AI-Detection Triggers)
- "It is worth noting that"
- "In the realm of"
- "Leveraging / harnessing / utilizing"
- "Plays a crucial / pivotal role"
- "This approach ensures that"
- "In order to achieve"
- "Seamlessly integrates"
- "Robust and scalable"
- "State-of-the-art" (overused — use "current" or specific method names)
- "Novel approach" (in body text — acceptable in abstract/summary only)
- "Cutting-edge"
- "Furthermore" at paragraph start (occasional use mid-sentence is fine)
- "Moreover" at paragraph start
- "Additionally" at paragraph start
- "It should be noted"

### Preferred Alternatives
| Instead of | Use |
|-----------|-----|
| leveraging | using / employing / applying |
| harnessing | capturing / directing / channeling |
| robust | fault-tolerant / resilient under [condition] |
| seamlessly | without manual intervention / transparently |
| state-of-the-art | current best-performing / [specific method name] |
| novel | proposed / introduced in this work |
| furthermore | [start with the actual content] |
| cutting-edge | recent / advanced |
| utilize | use |
| facilitate | enable / allow |

## Hedging Language (Use Sparingly but Naturally)
- "approximately 98.2% accuracy under field conditions"
- "in the range of 8–15 ms response time"
- "under typical operating conditions"
- "within the tested parameter space"
- "preliminary results indicate"
- "consistent with expected physical behavior"

## Numeric Specificity
- BAD: "The system shows high accuracy"
- GOOD: "The system achieves 97.3% spatial validation accuracy with a standard deviation of ±0.8% across 1,200 test cycles"
- BAD: "Response time is fast"
- GOOD: "Mean response time measures 11.4 ms (95th percentile: 18.2 ms) under peak load conditions"

## Paragraph Numbering Convention
- Section 6: [0001], [0002], [0003]...
- Section 7: Continues from Section 6's last number
- Section 8: Continues from Section 7's last number
- Each paragraph number corresponds to ONE technical concept or step

## Caption Writing
- Figures: "Figure N: [Descriptive title that stands alone without context]"
- Tables: "Table N: [Descriptive title]"
- Example: "Figure 3: Spatio-temporal validation accuracy across varying GNSS signal quality conditions"
- NOT: "Figure 3: Results" or "Figure 3: Graph showing accuracy"
