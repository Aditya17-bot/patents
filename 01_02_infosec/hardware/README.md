# Candidate-station interlock node — build and demonstrate

This directory contains the complete design for the hardware the patent claims, the
firmware that runs on it, and a host controller that runs **today** against recorded
data through the identical code path it will use with real transducers.

```
BOM.md                     parts, wiring, safety rules, bench measurement plan H1-H8
firmware/interlock_node.ino  ESP32 firmware: 4 channels in, gate + indicator out
host_controller.py         control law + two backends (SerialBackend / ReplayBackend)
bench_latency.py           measures the software path on real corpus input
latency_results.json       the measurements below
replay_result.csv          per-question outcome of the replay demo
```

## Run the demo now, with no hardware

```bash
python host_controller.py --replay <scratchpad>/windows_channels.csv --speed 0
python bench_latency.py
```

The replay reproduces the analysis pipeline's scheduler numbers exactly — 44.4 % / 33.3 %
advise/gate on assisted questions, 29.7 % / 10.8 % on unassisted, 80.2 % actuation
reduction — which is the check that the controller and the offline analysis implement the
same control law. When the node is plugged in, `SerialBackend` replaces `ReplayBackend`
and nothing above it changes.

## What is measured versus what is derived

**Measured on real recordings, on this machine:**

| Stage | median | p95 |
|---|---|---|
| T1 channel extraction over a 20 s window | 1.340 ms | 3.294 ms |
| T2 corroboration value (700) | 0.247 ms | 0.430 ms |
| T3 scheduler decision (800/850) | 0.0004 ms | 0.001 ms |
| **Total software path** | **1.588 ms** | **3.724 ms** |

The control-cycle budget is 2500 ms, so the software consumes **0.06 %** of it. The
latency budget is essentially all transducer and actuation — which is the useful finding:
nothing in the control law needs optimising, and a slower, cheaper node MCU is viable.

**Derived from datasheets and standard bounds — these are the numbers the build replaces:**

| Path element | Derived | Basis |
|---|---|---|
| photodiode edge → MCU | 0.005 ms | BPW34 rise < 1 µs, 200 Hz sampling |
| display panel response | 8.3 ms | one refresh at 120 Hz |
| node frame → host | 20.0 ms | `REPORT_HZ = 50` |
| gate command → switch | 0.001 ms | TS3USB221A t_pd, ns scale |
| USB full-speed frame | 1.0 ms | worst-case HID poll interval |
| **Derived transducer total** | **29.3 ms** | |

**Projected sense-to-gate latency: 30.9 ms**, against the 200 ms responsiveness bound the
reference filing used — 169 ms of margin. Every one of these five rows becomes a bench
measurement the day the node exists.

## Why the build is what unblocks the patent

The disclosure's distinguishing elements over the closest art (`US20190156689A1`, ProctorU,
which flags a behavioural sequence and then suspends the session *in software*) are:

1. a **physically measured** question-onset anchor rather than a software event;
2. attribution of an acoustic emission to the seated candidate by structure-borne
   coincidence, so a neighbour's speech cannot implicate them;
3. an intervention that **physically interrupts the input path** rather than asking the
   application to stop accepting input.

None of the three can be evidenced from public datasets, because no public dataset carries
synchronised photodiode, desk-contact, and keystroke channels from one candidate station.
Every number currently in Section 8 comes from a proxy corpus standing in for a different
sensor. That is the gap, and roughly ₹1,150 of parts closes it.

Run **H2 first** (own whisper versus a confederate at 1 m, piezo/mic coincidence). It is the
riskiest claim in the document. If structure-borne coupling of whispering does not separate
cleanly, the attribution unit should be re-framed around contact events — typing impulses,
leaning, hand placement — and the claims rewritten *before* filing rather than after.
