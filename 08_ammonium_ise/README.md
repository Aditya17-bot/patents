# Patent 08 — ammonium sonde floor anchored at laboratory samples

Final mechanism (IDF-B in `patent/`): offset in force = 7-day 5th-percentile floor of the sonde's own
ammonium record minus a gap g fixed at earlier laboratory samples; corrected reading = reading - offset.
Evidence in `results/ev_main.json`; see PLAN.md for the full log, including the conductivity
interference idea below, which failed the evidence gate.

---

# Patent 08 — ammonium sonde interference correction from the sonde's own conductivity

## Idea

An ammonium ion-selective electrode (ISE) in a river water-quality sonde also responds to
sodium and potassium (Nikolsky-Eisenman). The sonde turns the electrode potential into a
concentration as if only ammonium were present, so it over-reads by a term proportional to
the interfering cations. Those cations are a fairly stable share of the dissolved ions at a
site, and the sonde's conductivity cell measures the dissolved ions continuously. So:

    corrected ammonium = reading - b - k * conductivity,   k >= 0

with k and b fitted per site from the routine laboratory samples already taken there.
Current practice applies one correction value (or one that drifts in time) from those samples.

## Feasibility (Environment Agency, England; open, no login)

- Raw sonde data (quality 'Unchecked') from the EA Hydrology API; laboratory ammoniacal
  nitrogen (determinand 0111) from the EA Water Quality Archive API.
- Probe on 23 sites (`src/probe_interf.py`, first half fits, second half scores): median absolute
  error raw 0.68, single offset 0.37, offset + conductivity term 0.26 mg/L N; 90th percentile
  17.5 / 9.0 / 2.4.
- The over-read is not drift: it does not grow with time since service (`results/probe_amm.json`).

## Nearest art (raw text in `prior_art_raw/`)

- US 8,691,074 B2: correction value = ISE reading minus a reference-method result, applied to
  future readings (constant). No conductivity.
- CN 118914491 A: sludge-build-up compensation for ISEs and sample-based slope/offset
  interpolated between calibrations. No conductivity-based interference term.
- Pedersen et al., Water Research 2020: ISE jumps and drift corrected with composite samples.
- Capella et al., Sensors 2020: redundant ISEs and an expert system to reject interference.
- 2026 preprint (Research Square): K+ ISE, pH and temperature compensation of an NH4+ ISE.
- Vendors (In-Situ, YSI): conductivity used to derive ammonia (temperature, ionic strength),
  potassium compensation with an extra K+ electrode.

See `PLAN.md` for gates and status.
