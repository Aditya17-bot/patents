# Patent 09 screening — round 1 (2026-10-06)
Gate: (1) open raw data + independent truth, (2) large error under current practice in the data,
(3) physical mechanism, (4) raw-text prior-art check, (5) feasibility probe. Stop at first failure.

| Candidate | Failed at | Why |
|---|---|---|
| Ice-affected discharge from stage + freezing degree-days (USGS winter visits as truth) | 4 | Holtschlag & Grewal 1998 (J. Hydrol. Eng.): real-time ice-affected flow from stage, air temperature and open-water rating by extended Kalman filter; Melcher & Walker 1992 (USGS WSP 2378) compare 17 methods |
| Ozone analyzer zero offset from night-time NO titration (EPA AirData O3 + NO) | 1, 4 | truth (AQS one-point QC zero checks) needs an AQS API key (account); low-cost sensor literature already baseline-corrects O3 (e.g. paired electrochemical sensor studies) |
| Tipping-bucket undercatch vs co-located check gauge (UK EA) | 4 (known) | dynamic calibration of TBRs is established |
| Pyranometer closure / thermal offset (NREL, BSRN) | 4 (known) | BSRN QC closure tests |
| Soil-temperature probe depth from diurnal damping (USCRN) | 1 | no independent truth |
| RH sensor drift from saturation in rain/fog | 1, 4 | no truth; saturation checks are standard QC |
| Reservoir capacity loss from water balance | 1 | truth (resurveys) too sparse; storage computed from the same table |
| Dam turbine/gate outflow vs downstream gauge (USBR RISE / USACE CWMS) | 2 (not probed) | few sites; plant flow calibration (index testing) is practice |
| Groundwater logger vs manual dips (EA / India-WRIS) | 1 (unverified) | EA dips availability unverified; India-WRIS needs registration |
| EIA-930 tie-line reconciliation | 4 | de Chalendar & Benson 2019 physics-based reconciliation |
| Single-loop speed (g-factor) vs dual loops | 4 | heavily published (Wang & Nihan; Coifman) |
| WQ sonde drift (NEON), snow pillow, ammonium ISE | earlier rounds | see memory patent8-idea-gate |

Unlocks that need the user (free accounts the user would create; Claude cannot create accounts):
EPA AQS API key (QC checks as truth), NEON API token (raw sondes + lab chemistry), India-WRIS
registration (CWC/CGWB Indian data). A VIT laboratory rig would give physical ground truth directly.

# Round 2 (2026-10-06)
| Candidate | Failed at | Why |
|---|---|---|
| Aquatic-vegetation rating shifts driven by growing degree-days since last scouring flood (USGS visits) | 4 | Perret, Renard & Le Coz 2021 (WRR): temporal rating curve with plant growth/decay and reconfiguration, Bayesian; plus Darienzo 2021 segmentation |
| DO sensor gain anchored at high-flow saturation (EA sondes, field DO 9901 as truth) | 2 | probe (08_ammonium_ise/results/probe_do.json): 60 sites, 1,466 field checks, median abs error 4.0 % sat (within instrument tolerance); p90 26 % but not growing with time since service (not drift) |
| Rating hysteresis from gauge-height change during measurement (Jones formula calibrated on gaugings) | 4 (known) | Petersen-Overleir 2006 and Jones-formula literature |
| NDIR CO2 automatic baseline (lowest reading = 400 ppm) | 4 (known) | standard ABC in commercial NDIR sensors - same floor logic as killed 08 |
| PV/met logger clock offset from solar noon | 4 (known) | pvanalytics time-shift detection |
| Cyber-physical attack detection by process invariants (HAI/SWaT) | 4 (crowded) | large literature and patents |
Conclusion: public sensor-correction space with open truth is largely mined; blind rounds have low yield.

# Round 3 (2026-10-06, after 09 pump cavitation parked for lack of open data)
User asked for an open-data topic "like before". Downloaded and probed real data for each.
| Candidate | Failed at | Why (evidence in _screening/<folder>) |
|---|---|---|
| ZeMA hydraulic rig (UCI 447): physics-based leakage/accumulator separation | 2 | ML already 0.35 % error on all four conditions (dataset docs); accumulator precharge signal in PS1 transients tiny (zema/) |
| MetroPT-3 metro APU (UCI 791): night leak-down rate as leak measure | 5 | daily leak-down rate shows no rise before any of 4 reported air leaks; seasonal drift only (metropt/segments.pkl) |
| Rating shift from baseflow-recession shape (USGS) | 4 | Darienzo/Le Coz 2021: stage-recession shift detection incl. real-time indicator |
| 3W hydrate in production line vs PCK scaling, subcooling-margin gated (Petrobras 3W v2, 14 + 36 real) | 3/5 | only topside/tree temperatures; generic hydrate curve puts nearly all real hydrate events outside the envelope; frozen/negative sensors in several instances (3w/) |
| 3W hydrate in service line (57 real) via gas-lift choke equation | 1 | upstream GL-choke pressure absent in almost all instances |
| HGV speed-limiter peak (56 mph) as absolute speed reference (WebTRIS) | 1 | WebTRIS speed bins empty for MIDAS, TMU and A-road sites, 2019-2025 (only Avg mph); also judged near-obvious over WIM front-axle calibration in 05 PLAN |
Conclusion: third round, no survivor.
