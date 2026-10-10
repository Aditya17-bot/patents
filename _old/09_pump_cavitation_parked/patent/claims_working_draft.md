# Working claim draft (NOT the IDF; numbers and wording fixed only after rig evidence)

Structure per hub rules: 1 independent method, 5 dependents, 1 system.

1. A method of operating a centrifugal pump driven by a variable-frequency drive, comprising:
   (a) measuring, during operation, the rotational speed, the flow rate, the absolute pressure at
       the pump suction, the pressure at the pump discharge, the liquid temperature and the shaft
       power of the pump;
   (b) computing, for each operating point, the flow coefficient, the hydraulic efficiency and a
       suction margin ratio equal to the net positive suction head available, obtained from the
       suction pressure and the vapour pressure at the measured temperature, divided by a reference
       net positive suction head scaled with the square of the speed;
   (c) fitting a healthy efficiency curve as a function of the flow coefficient only from operating
       points whose suction margin ratio is at or above a cavitation-free ratio, and re-fitting it
       during operation from such points, so that a margin-independent efficiency loss enters the
       curve and a cavitation loss does not;
   (d) separating the efficiency residual relative to the healthy curve into a margin-independent
       component, estimated from recent operating points at or above the cavitation-free ratio, and
       a margin-dependent component present only below that ratio; and
   (e) when the margin-dependent component falls below a threshold set from the residual noise of
       the cavitation-free points, transmitting to the drive a speed command that raises the
       suction margin ratio, the margin-independent component not raising the command.

2. Claim 1, wherein on the margin-dependent component crossing the threshold the drive first
   lowers the speed until the suction margin ratio reaches the cavitation-free ratio, and the loss
   is classified as cavitation when the residual recovers and as a margin-independent loss when it
   does not, the latter resetting the margin-independent component without a cavitation command.
   [N5]
3. Claim 1, wherein the pairs of suction margin ratio and margin-dependent component are fitted
   with a hinge function, the hinge ratio being stored as the pump's own onset ratio of
   performance-affecting cavitation and used, with a buffer, as the lower limit of the margin
   ratio held by the speed command. [N3]
4. Claim 1, wherein the head coefficient residual is separated in the same manner and the
   command requires both residuals below their thresholds. [only if rig shows it helps]
5. Claim 1, wherein the speed command is n_new = n x sqrt(R / R_target), rate-limited and bounded
   below by a minimum fraction of the process setpoint, written as a frequency setpoint register
   of the drive. [N4 specific form]
6. Claim 1, wherein calibration points are further restricted to steady operation, the flow
   coefficient varying by less than a set fraction over a window. [only if rig shows needed]

7. A pump system comprising a centrifugal pump, a variable-frequency drive, an absolute pressure
   transducer at the suction, a pressure transducer at the discharge, a flowmeter, a temperature
   sensor, a shaft-power measurement (drive torque-speed estimate or power meter), and a
   controller connected to the drive by a fieldbus and configured to perform the method of claim 1.

Notes
- Distinguish in Section 4: US 7,112,037 (baseline assumed at adequate NPSHa, no measured gate,
  no split); US 11,994,150 (head deficit always read as wear, raises NPSHr — the opposite
  inference); Kallesoe 2004 (structural isolation without margin); US 6,655,922 (generic
  classifier); Danfoss / US 10,711,787 (speed reduction after detection, no discrimination).
- Section 8 limits to state: acoustic emission sees inception earlier (Mousmoulis); method needs
  the pump to visit high-margin points to calibrate; a wear step that occurs while margin stays
  below the gate is resolved only by the claim-2 test (needs a short speed reduction).
