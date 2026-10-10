# Laboratory protocol — patent 09 evidence (Phase C)

One to two lab days on a centrifugal pump NPSH test rig. Everything logged goes to `data/rig/`
exactly as recorded (no editing); a run log line per run in `data/rig/RUNLOG.csv`.

## 1. Rig and sensors (note make, model, range, accuracy of each in RUNLOG header)

| Quantity | Sensor | Minimum spec |
|----------|--------|--------------|
| Suction pressure (absolute) | absolute transducer at suction flange (2 D upstream) | 0–2 bar abs, 0.1 % FS |
| Discharge pressure | gauge or absolute transducer at discharge flange | 0–6 bar, 0.1 % FS |
| Flow | electromagnetic or turbine flowmeter | 0.5 % of reading |
| Water temperature | PT100 in suction pipe or tank | 0.1 K |
| Shaft power | torque-speed sensor, or VFD power/torque readout, or 3-phase power analyser (motor efficiency then from motor data) | 1 % |
| Speed | VFD output frequency and/or tacho | 0.1 % |
| Cavitation reference (truth) | accelerometer on casing near eye (>= 10 kHz band) and, if available, hydrophone or acoustic-emission sensor; optional transparent inlet / stroboscope | — |
| Suction control | throttle valve on suction line or vacuum pump on closed tank | NPSHa down to below NPSH3 |
| Wear emulation | bypass/recirculation valve from discharge to suction (internal-leakage analogue) or a second, trimmed/worn impeller | 1–5 % efficiency loss |
| Drive | VFD with Modbus/analogue frequency setpoint | needed only for T5 |

Logging: hydraulics at >= 1 Hz (1 s means), vibration/AE bursts of 2 s at >= 25 kHz every 10 s.
Record pipe diameters at both taps, tap heights, impeller diameter, motor poles, pump datasheet
NPSH3 curve (photo of datasheet page into `data/rig/`).

## 2. Test matrix

| Test | What | Purpose |
|------|------|---------|
| T1 healthy map | 3 speeds (e.g. 100, 90, 80 %) x 6–8 flows (50–120 % BEP), full suction pressure, 3 min each | calibration region; noise of each sensor |
| T2 NPSH sweeps | at each speed x 3 flows: lower suction pressure in steps (about 0.1 m NPSH near the knee), hold 90 s per step, continue past 3 % head drop | NPSH3 truth, knee, detection margin |
| T3 slow ramps | 2–3 continuous suction-pressure ramps at fixed speed/flow (about 0.5 m NPSH per minute) | detection lead in time |
| T4 wear without cavitation | at full suction pressure open bypass valve in 3 steps (hold 5 min each); repeat with suction pressure just above the knee (from T2) | no false cavitation alarm; probe classifies as wear |
| T5 closed loop | run `src/controller.py` on the drive (or operator applies the logged speed command by hand within 2 s) during T3 ramps | speed command, head loss avoided |
| T6 repeat | repeat one T2 sweep at the end of the day | repeatability |

## 3. Truth definitions (written before data, not changed after)

- NPSH3: suction head at which head falls 3 % below its mean over the first three steps of the
  sweep (ISO 9906 practice).
- Acoustic onset: first step at which high-frequency band rms (accelerometer 5–10 kHz or AE)
  exceeds its T1 mean by 3 standard deviations.
- Cavitation-free periods: all of T1, and T4 at full suction pressure.

## 4. What Claude needs back

The raw logger files, RUNLOG.csv, sensor data sheets, rig photo, datasheet NPSH3 curve.
