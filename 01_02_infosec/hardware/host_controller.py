"""Host controller for the candidate-station interlock node (100).

One control path, two backends:

    SerialBackend   talks to the ESP32 over USB CDC.  Real transducers.
    ReplayBackend   replays recorded corpus data through the identical path.

Everything above the backend - corroboration value, eligibility, the four-stage
scheduler (800), the dual-channel interlock (850) - is the same object in both
cases.  That is the point: when the hardware arrives, only the backend changes,
so the software is already exercised and only the transducer physics is new.

Run the replay demo:
    python host_controller.py --replay ../../<scratchpad>/windows_channels.csv
    python host_controller.py --replay <csv> --speed 0     # as fast as possible
    python host_controller.py --serial COM5                # real node
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Iterator, Optional

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- control law

HOP_S = 2.5

PARAMS = dict(tau=0.90, n_persist=2, t_cooldown=15.0, t_gap=6.0,
              epsilon=0.05, tau_gate=0.90, tau_a=0.85, tau_b=0.85)

OBSERVE, ADVISE, GATE, HOLD = 0, 1, 2, 3
STAGE_NAME = {OBSERVE: 'OBSERVE', ADVISE: 'ADVISE', GATE: 'GATE', HOLD: 'HOLD'}


@dataclass
class Cycle:
    """One control cycle: the corroboration value plus the two independent channels."""
    t_s: float
    A: float
    ocular: float
    inertial: float
    m_total: float = 0.0          # Equation 1, m/s^2
    since_onset_s: float = 0.0    # time since the last photometric anchor (210)
    tag: str = ''


@dataclass
class Actuation:
    t_s: float
    level: int
    A: float
    escalated: bool
    decide_ms: float


class Scheduler:
    """Stages 810/820/830/840/850. Identical logic to scratchpad/scheduler.py."""

    def __init__(self, p=None):
        self.p = dict(PARAMS if p is None else p)
        self.reset()

    def reset(self):
        self.run = 0
        self.last_act = -1e9
        self.last_state_act = -1e9
        self.a_at_last = -1e9
        self.stage = OBSERVE
        self.events: list[Actuation] = []
        self.raw_eligible = 0

    def step(self, c: Cycle) -> Optional[Actuation]:
        t0 = time.perf_counter()
        p = self.p
        if c.A < p['tau']:
            self.run = 0
            return None
        self.run += 1
        self.raw_eligible += 1
        if self.run < p['n_persist']:                                   # 810
            return None
        escalated = (c.A - self.a_at_last) >= p['epsilon']              # 840
        if (c.t_s - self.last_state_act) < p['t_cooldown'] and not escalated:   # 820
            return None
        if (c.t_s - self.last_act) < p['t_gap']:                        # 830
            return None
        two = (c.ocular >= p['tau_a']) and (c.inertial >= p['tau_b'])   # 850
        lvl = GATE if (c.A >= p['tau_gate'] and two) else ADVISE
        if lvl >= GATE and sum(1 for e in self.events if e.level >= GATE) >= 2:
            lvl = HOLD
        self.stage = max(self.stage, lvl)
        ev = Actuation(c.t_s, lvl, c.A, escalated,
                       (time.perf_counter() - t0) * 1000.0)
        self.events.append(ev)
        self.last_act = self.last_state_act = c.t_s
        self.a_at_last = c.A
        return ev


# ---------------------------------------------------------------- backends

class Backend:
    def cycles(self) -> Iterator[Cycle]:
        raise NotImplementedError

    def actuate(self, level: int) -> float:
        """Drive the actuators. Returns the measured command latency in ms."""
        return 0.0

    def close(self):
        pass


class ReplayBackend(Backend):
    """Replays recorded control cycles.  Real corpus values, no transducers."""

    def __init__(self, csv, speed=1.0, only=None):
        df = pd.read_csv(csv)
        need = {'A', 'ocular', 'inertial', 't_rel_s', 'fname', 'label'}
        missing = need - set(df.columns)
        if missing:
            raise SystemExit('replay csv missing columns: %s' % sorted(missing))
        un = df[df.label == 0]
        for c in ('A', 'ocular', 'inertial'):
            ref = np.sort(un[c].to_numpy(float))
            df[c] = np.searchsorted(ref, df[c].to_numpy(float), side='right') / len(ref)
        self.df = df
        self.speed = speed
        self.only = only
        self.gate_cmds = 0

    def questions(self):
        for (f, lab), g in self.df.groupby(['fname', 'label']):
            if self.only and f != self.only:
                continue
            yield f, lab, g.sort_values('t_rel_s')

    def cycles_for(self, g) -> Iterator[Cycle]:
        prev = None
        for _, r in g.iterrows():
            if self.speed > 0 and prev is not None:
                dt = (r['t_rel_s'] - prev) / self.speed
                if dt > 0:
                    time.sleep(min(dt, 0.25))
            prev = r['t_rel_s']
            yield Cycle(t_s=float(r['t_rel_s']), A=float(r['A']),
                        ocular=float(r['ocular']), inertial=float(r['inertial']),
                        m_total=float(r.get('head_rms', 0.0)),
                        since_onset_s=float(r['t_rel_s']))

    def actuate(self, level):
        t0 = time.perf_counter()
        if level >= GATE:
            self.gate_cmds += 1
        return (time.perf_counter() - t0) * 1000.0


class SerialBackend(Backend):
    """Live node.  Frames arrive at REPORT_HZ; cycles are emitted every HOP_S."""

    def __init__(self, port, baud=921600, scorer=None):
        try:
            import serial
        except ImportError:
            raise SystemExit('pyserial not installed:  pip install pyserial')
        self.ser = serial.Serial(port, baud, timeout=1.0)
        self.scorer = scorer
        self.buf: list[dict] = []
        self.t_start = time.perf_counter()
        self.last_hb = 0.0
        time.sleep(2.0)                      # board reset on port open
        self.ser.reset_input_buffer()

    def _read_frame(self) -> Optional[dict]:
        raw = self.ser.readline().decode('ascii', 'replace').strip()
        if not raw or raw.startswith('#'):
            if raw:
                print('  node: %s' % raw)
            return None
        parts = raw.split()
        if parts[0] == 'O':                                     # onset anchor (210)
            print('  onset anchor seq=%s t=%s us' % (parts[1], parts[2]))
            return None
        if parts[0] != 'F' or len(parts) != 9:
            return None
        return dict(us=int(parts[1]), since_onset_ms=int(parts[2]),
                    pz_pk=float(parts[3]), pz_rms=float(parts[4]),
                    mic_pk=float(parts[5]), mic_rms=float(parts[6]),
                    m_total=float(parts[7]), gate=int(parts[8]))

    def cycles(self) -> Iterator[Cycle]:
        """Aggregate node frames into one control cycle per HOP_S."""
        window_start = time.perf_counter()
        while True:
            f = self._read_frame()
            now = time.perf_counter()
            if now - self.last_hb > 0.5:
                self.ser.write(b'H')                            # watchdog heartbeat
                self.last_hb = now
            if f:
                self.buf.append(f)
            if now - window_start < HOP_S:
                continue
            window_start = now
            if not self.buf:
                continue
            b, self.buf = self.buf, []
            # Attribution (420): airborne energy counts only when the structure-borne
            # channel corroborates it in the same frame.  A neighbour's speech reaches
            # the microphone but not the desk.
            attributed = float(np.mean([1.0 if (x['mic_pk'] > 3.0 and x['pz_pk'] > 3.0)
                                        else 0.0 for x in b]))
            m = float(np.mean([x['m_total'] for x in b]))
            feats = dict(attributed=attributed, m_total=m,
                         pz_pk=float(np.max([x['pz_pk'] for x in b])),
                         mic_pk=float(np.max([x['mic_pk'] for x in b])),
                         since_onset_s=b[-1]['since_onset_ms'] / 1000.0)
            if self.scorer is None:
                raise SystemExit('SerialBackend needs a scorer; see fit_scorer()')
            A, oc, ine = self.scorer(feats)
            yield Cycle(t_s=now - self.t_start, A=A, ocular=oc, inertial=ine,
                        m_total=m, since_onset_s=feats['since_onset_s'])

    def actuate(self, level):
        t0 = time.perf_counter()
        if level >= GATE:
            self.ser.write(b'G1')
        elif level == ADVISE:
            self.ser.write(b'A1')
        self.ser.flush()
        return (time.perf_counter() - t0) * 1000.0

    def release(self):
        self.ser.write(b'G0A0')
        self.ser.flush()

    def close(self):
        try:
            self.release()
        finally:
            self.ser.close()


# ---------------------------------------------------------------- runner

def run_replay(csv, speed, limit=None, verbose=False):
    be = ReplayBackend(csv, speed=speed)
    sched = Scheduler()
    rows, decide_ms = [], []
    n = 0
    for fname, label, g in be.questions():
        sched.reset()
        t_wall = time.perf_counter()
        acts = []
        for c in be.cycles_for(g):
            t0 = time.perf_counter()
            ev = sched.step(c)
            decide_ms.append((time.perf_counter() - t0) * 1000.0)
            if ev:
                cmd = be.actuate(ev.level)
                acts.append(ev)
                if verbose:
                    print('    %-6s t=%6.1fs A=%.2f oc=%.2f in=%.2f  cmd %.3f ms'
                          % (STAGE_NAME[ev.level], c.t_s, c.A, c.ocular,
                             c.inertial, cmd))
        rows.append(dict(fname=fname, label=int(label), stage=sched.stage,
                         n_cycles=len(g), raw_eligible=sched.raw_eligible,
                         n_events=len(acts),
                         n_gate=sum(1 for a in acts if a.level >= GATE),
                         t_first=acts[0].t_s if acts else np.nan,
                         t_first_gate=next((a.t_s for a in acts
                                            if a.level >= GATE), np.nan),
                         dur_s=float(g.t_rel_s.max() - g.t_rel_s.min()),
                         wall_s=time.perf_counter() - t_wall))
        n += 1
        if limit and n >= limit:
            break
    return pd.DataFrame(rows), np.array(decide_ms)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--replay', help='windows_channels.csv from the analysis pipeline')
    ap.add_argument('--serial', help='node serial port, e.g. COM5 or /dev/ttyUSB0')
    ap.add_argument('--speed', type=float, default=0.0,
                    help='replay speed multiplier; 0 = no wall-clock pacing')
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--out', default='replay_result.csv')
    a = ap.parse_args()

    if a.serial:
        be = SerialBackend(a.serial)
        sched = Scheduler()
        print('node connected on %s; ctrl-c to stop' % a.serial)
        try:
            for c in be.cycles():
                ev = sched.step(c)
                print('  t=%6.1fs A=%.2f M=%.2f m/s^2 %s'
                      % (c.t_s, c.A, c.m_total,
                         STAGE_NAME[ev.level] if ev else ''))
                if ev:
                    be.actuate(ev.level)
        except KeyboardInterrupt:
            pass
        finally:
            be.close()
        return

    if not a.replay:
        ap.error('give --replay <csv> or --serial <port>')
    r, dms = run_replay(a.replay, a.speed, a.limit, a.verbose)
    r.to_csv(a.out, index=False)

    asst, hon = r[r.label == 1], r[r.label == 0]
    hh = hon.dur_s.sum() / 3600.0
    print('\nreplayed %d questions (%d assisted / %d unassisted), %d control cycles'
          % (len(r), len(asst), len(hon), int(r.n_cycles.sum())))
    print('  assisted    advise %5.1f%%   gate %5.1f%%   median t_gate %5.1f s'
          % (100 * (asst.stage >= ADVISE).mean(), 100 * (asst.stage >= GATE).mean(),
             asst.t_first_gate.median()))
    print('  unassisted  advise %5.1f%%   gate %5.1f%%   false gate %.2f/h'
          % (100 * (hon.stage >= ADVISE).mean(), 100 * (hon.stage >= GATE).mean(),
             hon.n_gate.sum() / hh if hh else float('nan')))
    print('  discipline  %d eligible cycles -> %d actuations (%.1f%% reduction)'
          % (r.raw_eligible.sum(), r.n_events.sum(),
             100 * (1 - r.n_events.sum() / max(1, r.raw_eligible.sum()))))
    print('\ncontrol-law decision latency, measured on this machine:')
    print('  median %.4f ms   p95 %.4f ms   max %.4f ms   over %d decisions'
          % (np.median(dms), np.percentile(dms, 95), dms.max(), len(dms)))
    print('  budget per control cycle is %.0f ms, so the control law uses %.4f%% of it'
          % (HOP_S * 1000, 100 * np.median(dms) / (HOP_S * 1000)))
    print('\nwrote %s' % a.out)


if __name__ == '__main__':
    main()
