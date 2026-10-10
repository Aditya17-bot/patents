# Candidate-station interlock node — bill of materials and build

Everything below is off-the-shelf and hobby-grade. Total ≈ **₹1,150** for one station.
Nothing here is exotic; the point of the build is not sophistication, it is *reduction to
practice* — putting the claimed transducers physically in the loop so the measurements in
Section 8 describe the apparatus rather than a stand-in for it.

## Parts

| Ref | Part | Purpose | Typical price (INR) |
|---|---|---|---|
| 210 | BPW34 PIN photodiode + OPA333 / LM358 transimpedance stage | Question-onset anchor. Watches a small high-contrast patch on the display. | 60 + 40 |
| 400 | 27 mm piezo disc (contact type), bonded to desk underside | Structure-borne channel. | 30 |
| 401 | JFET preamp (2N5457) or TL072 non-inverting stage, gain ~40 dB | Piezo is high-impedance; it needs a buffer before any ADC. | 40 |
| 402 | Electret microphone module (MAX9814 with AGC disabled) | Airborne channel. Attribution comes from the **coincidence** of 400 and 402, not from either alone. | 180 |
| 410 | MPU-6050 six-axis IMU, I²C at 0x68 | Desk/chassis motion. Same part family as the reference filing used. | 90 |
| 920 | TS3USB221A analog USB switch **or** Omron G6K-2F-Y DPDT signal relay | In-line gate on the keyboard's D+/D− pair. | 120 |
| 930 | Common-cathode RGB LED + 3×220 Ω | Desk indicator for the ADVISE stage (910). | 20 |
| — | ESP32-WROOM devkit (or Arduino Nano; ESP32 preferred for the second core and faster ADC) | Node controller. | 350 |
| — | Perfboard, USB-A breakout pair, headers, hookup wire | — | 200 |

Substitutions that do not change the claim: any PIN photodiode with rise time < 1 µs; any
six-axis IMU sampling ≥ 100 Hz; any analog switch or signal relay rated for USB 2.0
full-speed signalling.

## Wiring

```
   display bezel                      desk underside
   ┌──────────────┐                   ┌──────────────┐
   │ BPW34 (210)  │                   │ piezo  (400) │
   └──────┬───────┘                   └──────┬───────┘
          │ transimpedance                   │ JFET preamp (401)
          ▼                                  ▼
      ADC1_CH0                           ADC1_CH3
          │                                  │
          │      ┌───────────────┐           │
          └─────►│               │◄──────────┘
                 │    ESP32      │◄──── I2C ──── MPU-6050 (410)
   MAX9814 ─────►│   (node MCU)  │◄──── ADC ──── electret (402)
     (402)       │               │
                 │               ├──── GPIO ───► RGB LED (910/930)
                 │               ├──── GPIO ───► TS3USB221A /OE  (920)
                 └───────┬───────┘
                         │ USB CDC serial @ 921600
                         ▼
                    host controller

   keyboard ──D+/D──►┌─────────────┐──D+/D──► exam terminal
                     │ TS3USB221A  │
                     │    (920)    │  /OE driven by MCU
                     └─────────────┘
```

## Two design rules that are not optional

**The gate fails closed (keyboard working).** `TS3USB221A` `/OE` is pulled low by a 10 kΩ
resistor so the switch passes signal whenever the MCU is unpowered, held in reset, or
crashed. Opening the input path is the *active* state and requires a live MCU asserting it.
A student is never locked out by a hardware fault. This is stated as a claim limitation, not
just an implementation detail.

**The gate is watchdog-bounded.** Firmware arms a hardware watchdog before every gate
assertion; if the host controller stops sending heartbeats the gate releases within
`GATE_MAX_MS`. An unattended failure cannot hold a candidate's keyboard open indefinitely.

## Display patch for the onset anchor (210)

The exam application renders a 40 × 40 px patch in a screen corner that inverts on every
question transition. The photodiode sits over it behind an opaque shroud. This is the
standard psychophysics/EEG technique for recovering true stimulus-onset timing, and it is
what makes T0 a *measured physical event* rather than a software log line — which is exactly
the distinction the current draft cannot yet claim, because the eye-tracking corpus gave us
only the `StartMedia` log marker.

Anchor accuracy is then bounded by panel response, not by software scheduling: ~8.3 ms at
120 Hz, ~16.7 ms at 60 Hz, plus LCD pixel transition (typ. 1–5 ms).

## What each transducer must be shown to do

These are the bench measurements that convert the current prophetic description into
evidence. Predictions are derived from datasheets and standard engineering bounds and are
labelled as **derived**, not measured — the whole point of building is to replace them.

| # | Measurement | Derived expectation | Why it matters to the claim |
|---|---|---|---|
| H1 | Photodiode edge vs. software render callback, 500 transitions | offset stable to within one refresh period; jitter < 2 ms | Establishes T0 as physical |
| H2 | Piezo/mic coincidence: candidate's own whisper vs. a confederate whispering at 1 m | own-speech structure-borne SNR ≥ 10 dB above neighbour's | The attribution claim (420) stands or falls here |
| H3 | Piezo response to typing impulses | clear per-keystroke transient, > 20 dB above desk noise floor | Gives a second, independent commit-time anchor |
| H4 | Gate assertion → keyboard report ceases, 200 trials | < 2 ms (USB full-speed frame 1 ms + switch t_pd ≈ ns) | The physical technical effect itself |
| H5 | Gate release → enumeration restored | < 100 ms typical for HID re-enumeration | Proportionality of the intervention |
| H6 | Fail-safe: cut MCU power mid-gate | path closes, keyboard restored | Safety limitation above |
| H7 | Watchdog: stop host heartbeat mid-gate | release within `GATE_MAX_MS` | Safety limitation above |
| H8 | IMU seated noise floor at the desk | compare against MotionSense seated p50 0.178 m/s², p99 1.832 m/s² | Confirms the desk sensor sees what the proxy predicted |

H2 is the one to run first. It is the riskiest claim in the whole disclosure — if the
candidate's own whisper does not separate from a neighbour's by a usable margin, the
attribution unit needs re-framing around contact events (typing, leaning, hand placement)
rather than vocalisation, and the claim set should be rewritten *before* filing, not after.
