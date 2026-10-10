# Patent 03 Cloud Security Risk Scoring — review 2026-10-06: KILLED
- Section 8: every result "[TO BE MEASURED]" (Tables 2, 4; Figs 3-5); TRL 2. Needs a bench host with
  TPM 2.0, BMC, SmartNIC TCAM and labelled compromises; no open dataset has these together.
- Prior art not cited: Keylime (raw README, keylime_readme.txt here): "The Verifier continuously verifies
  the integrity state of the machine"; "Users can create their own customized actions that will trigger
  when a machine fails its attested measurements."
- Remaining elements generic: HPC anomaly detection (CloudShield, cited), exponential staleness
  weighting, confidence = decayed/nominal weight.
- Rule breaks in the draft: placeholders; Section 5A "guarantees legal defensibility"/"non-overlap";
  "return on investment", "costs throughput"; 7 protection aspects.
