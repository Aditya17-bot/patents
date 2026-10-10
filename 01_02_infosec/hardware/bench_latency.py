"""End-to-end control-loop latency, measured.

This is a real measurement, not a projection: it times the software half of the
perception-to-actuation path on this machine, using the recorded corpus as input.
The transducer half (photodiode edge, piezo/mic acquisition, USB gate assertion)
is bounded separately in hardware/BOM.md and becomes measurable when the node is
built - those rows are marked DERIVED here and must be replaced with bench values.

Stages timed:
  T1  channel extraction over one 20 s observation window   (et_windows.window_feats)
  T2  corroboration value from the fitted model             (700)
  T3  scheduler decision                                    (800/850)
"""
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.environ.get(
    'PATENT_SCRATCH',
    r'C:\Users\rober\AppData\Local\Temp\claude\C--adi-patent-InfoSec'
    r'\46f3d2b0-9227-41c2-805a-1a3b15973f2c\scratchpad')
sys.path.insert(0, SCRATCH)
sys.path.insert(0, HERE)

from et_load import trials                      # noqa: E402
from et_windows import streams, window_feats, WIN_MS, HOP_MS   # noqa: E402
from host_controller import Scheduler, Cycle, HOP_S            # noqa: E402


def pct(a):
    return dict(median=float(np.median(a)), p95=float(np.percentile(a, 95)),
                p99=float(np.percentile(a, 99)), max=float(np.max(a)),
                n=int(len(a)))


def main():
    t_feat, t_score, t_dec = [], [], []

    # --- T1 channel extraction, timed over real recordings
    tr_all = [t for t in trials()]
    picked = 0
    for tr in tr_all:
        try:
            S = streams(tr)
        except Exception:
            continue
        if S is None:
            continue
        t = S['t']
        start = t[0]
        while start + WIN_MS <= t[-1] + 1:
            i0 = int(np.searchsorted(t, start))
            i1 = int(np.searchsorted(t, start + WIN_MS))
            t0 = time.perf_counter()
            f = window_feats(S, i0, i1)
            if f is not None:
                t_feat.append((time.perf_counter() - t0) * 1000.0)
            start += HOP_MS
        picked += 1
        if picked >= 12:                     # enough windows for a stable estimate
            break

    # --- T2 corroboration value: fit once, then time inference only
    w = pd.read_csv(os.path.join(SCRATCH, 'windows.csv'))
    w = w[w.proto == 55].reset_index(drop=True)
    META = {'fname', 'label', 'pid', 'qid', 'win', 't_rel_s', 'proto', 'enrolled'}
    RAW = [c for c in w.columns if c not in META and w[c].dtype != object]
    from sklearn.ensemble import GradientBoostingClassifier
    X = np.nan_to_num(w[RAW].to_numpy(float), nan=0.0, posinf=8.0, neginf=-8.0)
    m = GradientBoostingClassifier(n_estimators=150, max_depth=3,
                                   learning_rate=0.08, subsample=0.85,
                                   random_state=0).fit(X, w.label.values)
    for i in range(min(2000, len(X))):
        row = X[i:i + 1]
        t0 = time.perf_counter()
        m.predict_proba(row)
        t_score.append((time.perf_counter() - t0) * 1000.0)

    # --- T3 scheduler decision
    sched = Scheduler()
    rs = np.random.RandomState(0)
    for i in range(5000):
        c = Cycle(t_s=i * HOP_S, A=float(rs.rand()),
                  ocular=float(rs.rand()), inertial=float(rs.rand()))
        t0 = time.perf_counter()
        sched.step(c)
        t_dec.append((time.perf_counter() - t0) * 1000.0)

    res = {'T1_channel_extraction_ms': pct(t_feat),
           'T2_corroboration_value_ms': pct(t_score),
           'T3_scheduler_decision_ms': pct(t_dec)}
    tot_med = (res['T1_channel_extraction_ms']['median'] +
               res['T2_corroboration_value_ms']['median'] +
               res['T3_scheduler_decision_ms']['median'])
    tot_p95 = (res['T1_channel_extraction_ms']['p95'] +
               res['T2_corroboration_value_ms']['p95'] +
               res['T3_scheduler_decision_ms']['p95'])
    res['software_path_total_ms'] = dict(median=tot_med, p95=tot_p95)
    res['control_cycle_budget_ms'] = HOP_S * 1000
    res['budget_used_pct'] = 100 * tot_med / (HOP_S * 1000)

    print('MEASURED software path (this machine, real corpus input)')
    print('  %-28s %9s %9s %9s %9s' % ('stage', 'median', 'p95', 'p99', 'max'))
    for k in ('T1_channel_extraction_ms', 'T2_corroboration_value_ms',
              'T3_scheduler_decision_ms'):
        v = res[k]
        print('  %-28s %8.3f  %8.3f  %8.3f  %8.3f   (n=%d)'
              % (k.replace('_ms', ''), v['median'], v['p95'], v['p99'],
                 v['max'], v['n']))
    print('  %-28s %8.3f  %8.3f' % ('TOTAL software path', tot_med, tot_p95))
    print('\n  control-cycle budget %.0f ms -> software uses %.2f%% (median)'
          % (HOP_S * 1000, res['budget_used_pct']))

    print('\nDERIVED transducer bounds (replace with bench measurements once built)')
    derived = {
        'photodiode_edge_to_mcu_ms': (0.005, 'BPW34 rise <1us + 200Hz sampling'),
        'display_panel_response_ms': (8.3, 'one refresh period at 120 Hz'),
        'node_frame_to_host_ms': (20.0, 'REPORT_HZ = 50'),
        'gate_command_to_switch_ms': (0.001, 'TS3USB221A t_pd, ns scale'),
        'usb_full_speed_frame_ms': (1.0, 'worst-case HID poll interval'),
    }
    for k, (v, why) in derived.items():
        print('  %-32s %8.3f ms   (%s)' % (k, v, why))
    hw = sum(v for v, _ in derived.values())
    print('  %-32s %8.3f ms' % ('DERIVED transducer total', hw))
    print('\n  projected sense-to-gate latency = software %.3f + transducers %.3f'
          ' = %.1f ms' % (tot_med, hw, tot_med + hw))
    print('  the 200 ms responsiveness bound used by the reference filing leaves'
          ' %.0f ms of margin' % (200 - (tot_med + hw)))
    res['derived_transducer_ms'] = {k: v for k, (v, _) in derived.items()}
    res['projected_sense_to_gate_ms'] = tot_med + hw

    with open(os.path.join(HERE, 'latency_results.json'), 'w') as fh:
        json.dump(res, fh, indent=1)
    print('\nwrote latency_results.json')


if __name__ == '__main__':
    main()
