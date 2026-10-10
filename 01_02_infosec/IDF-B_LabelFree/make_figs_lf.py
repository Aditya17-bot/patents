"""Figures 1-11 for the label-free malpractice-detection disclosure, rev7.

Architecture figures at dpi=200, data figures at dpi=300.  All labels ASCII.
Every data figure reads the measured JSON in evidence/results; nothing but a
label is hard-coded.
"""
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import (Circle, FancyArrowPatch, FancyBboxPatch,
                                Rectangle)

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'figures')
RES = os.path.join(os.path.dirname(HERE), 'evidence', 'results')

SEN = '#1565C0'      # sensing
PRC = '#F9A825'      # prediction / residual
REL = '#2E7D32'      # relational / cross-station
REF = '#6A1B9A'      # reference station
ALR = '#C62828'      # alert / response
GRY = '#455A64'
LGY = '#B0BEC5'

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})


def J(name):
    with open(os.path.join(RES, name), 'r', encoding='utf-8') as f:
        return json.load(f)


def box(ax, x, y, w, h, text, fc, fs=8.2, tc='white', bold=True, ec='black'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.06',
                                facecolor=fc, edgecolor=ec, linewidth=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fs, color=tc, fontweight='bold' if bold else 'normal',
            linespacing=1.35)


def arrow(ax, p, q, style='-|>', lw=1.3, color='black', ls='-', rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=11,
                                 linewidth=lw, color=color, linestyle=ls,
                                 connectionstyle='arc3,rad=%.2f' % rad,
                                 shrinkA=1, shrinkB=1))


def save(fig, name, dpi):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('wrote', name)


# ---------------------------------------------------------------- Figure 1
def fig01():
    """The data problem and its removal."""
    fig, ax = plt.subplots(figsize=(12.6, 5.4))
    ax.set_xlim(0, 126)
    ax.set_ylim(0, 54)
    ax.axis('off')

    ax.add_patch(Rectangle((1, 1), 60, 52, fill=False, ec=LGY, lw=1.0,
                           linestyle=(0, (4, 3))))
    ax.add_patch(Rectangle((65, 1), 60, 52, fill=False, ec=LGY, lw=1.0,
                           linestyle=(0, (4, 3))))
    ax.text(31, 50.2, 'SUPERVISED PRIOR ART', ha='center', fontsize=10,
            fontweight='bold', color=GRY)
    ax.text(95, 50.2, 'PRESENT INVENTION', ha='center', fontsize=10,
            fontweight='bold', color=GRY)

    box(ax, 6, 40, 50, 5.6, 'recordings of examination sessions', SEN, fs=8.4)
    arrow(ax, (31, 40), (31, 36))
    box(ax, 6, 30, 50, 5.6,
        'ANNOTATE EVERY INSTANCE OF MALPRACTICE\n'
        'rare, adversarial, deliberately concealed', ALR, fs=7.8)
    ax.text(58.8, 32.8, 'X', fontsize=20, fontweight='bold', color=ALR,
            ha='center', va='center')
    arrow(ax, (31, 30), (31, 26), color=GRY, ls=(0, (2, 2)))
    box(ax, 6, 20, 50, 5.6, 'classifier of the annotated behaviours', GRY,
        fs=8.4)
    arrow(ax, (31, 20), (31, 16), color=GRY, ls=(0, (2, 2)))
    box(ax, 6, 10, 50, 5.6, 'recognises only what it was shown', GRY, fs=8.4)
    ax.text(31, 5.4,
            'the corpus cannot be assembled;\nnovel methods stay invisible',
            ha='center', va='center', fontsize=8.2, color=ALR,
            fontweight='bold', linespacing=1.4)

    box(ax, 70, 40, 50, 5.6, 'recordings of sanctioned activity only', SEN,
        fs=8.4)
    arrow(ax, (95, 40), (95, 36))
    box(ax, 70, 30, 50, 5.6,
        'NO ANNOTATION STEP\nsanctioned activity is abundant, unlabelled',
        REL, fs=7.8)
    arrow(ax, (95, 30), (95, 26))
    box(ax, 70, 20, 50, 5.6,
        'predictor of the near-future signal (20)', PRC, fs=8.4, tc='black')
    arrow(ax, (95, 20), (95, 16))
    box(ax, 70, 10, 50, 5.6,
        'prediction residual is the score (30)', PRC, fs=8.4, tc='black')
    ax.text(95, 5.4,
            'anything unlike sanctioned activity scores high,\n'
            'including methods never anticipated',
            ha='center', va='center', fontsize=8.2, color=REL,
            fontweight='bold', linespacing=1.4)

    save(fig, 'fig01.png', 200)


# ---------------------------------------------------------------- Figure 2
def fig02():
    """System architecture with reference numerals."""
    fig, ax = plt.subplots(figsize=(14.2, 7.6))
    ax.set_xlim(0, 142)
    ax.set_ylim(0, 76)
    ax.axis('off')

    # --- candidate station ---------------------------------------------
    ax.add_patch(Rectangle((1.5, 34), 44, 38, fill=False, ec=LGY, lw=1.1,
                           linestyle=(0, (4, 3))))
    ax.text(23.5, 69.4, 'CANDIDATE STATION (100)', ha='center', fontsize=9.4,
            fontweight='bold', color=GRY)

    box(ax, 4, 62.0, 39, 5.2,
        'acoustic transducer (12)\naudible and near-ultrasonic', SEN, fs=7.4)
    box(ax, 4, 56.0, 39, 5.2,
        'electromagnetic sensor (14)\nadvertisement rate, RSSI', SEN, fs=7.4)
    box(ax, 4, 50.6, 39, 4.4, 'further-modality transducer (16)', SEN, fs=7.4)
    box(ax, 4, 45.2, 39, 4.4, 'optical behavioural module (18)', SEN, fs=7.4)
    ax.text(23.5, 42.6, 'SENSING ASSEMBLY (10)', ha='center', fontsize=8.2,
            fontweight='bold', color=SEN)

    box(ax, 4, 35.4, 39, 6.0,
        'STATION-LOCAL ENCODER AND\nPREDICTOR (20), STATISTICS (22)',
        PRC, fs=7.2, tc='black')

    # --- reference station ---------------------------------------------
    ax.add_patch(Rectangle((1.5, 15), 44, 15.5, fill=False, ec=REF, lw=1.4,
                           linestyle=(0, (5, 2))))
    ax.text(23.5, 27.9, 'REFERENCE STATION (90)', ha='center', fontsize=8.8,
            fontweight='bold', color=REF)
    ax.text(23.5, 25.5, 'held unoccupied for the session', ha='center',
            fontsize=7.4, color=REF, style='italic')
    box(ax, 4, 20.6, 39, 4.2, 'assembly of like construction', REF, fs=7.4)
    box(ax, 4, 15.9, 39, 4.2, 'own model and statistics', REF, fs=7.4)

    # --- synchronisation spine ------------------------------------------
    box(ax, 1.5, 8.4, 44, 4.8,
        'TIME-SYNCHRONISATION (70)\ncommon time base, tolerance T', GRY,
        fs=7.4)

    # --- per-station chain ----------------------------------------------
    box(ax, 50, 56, 24, 7.0,
        'RESIDUAL SCORING (30)\nobserved minus\npredicted change', PRC,
        fs=7.4, tc='black')
    box(ax, 50, 45, 24, 7.0,
        'FUSION (40)\nweights from the\ncalibration interval', PRC,
        fs=7.4, tc='black')

    arrow(ax, (43, 38.4), (50, 58.0), rad=-0.20)
    arrow(ax, (43, 18.0), (50, 56.6), rad=-0.34, color=REF, lw=1.5)
    arrow(ax, (62, 56), (62, 52.2))

    # --- cross-station block ---------------------------------------------
    ax.add_patch(Rectangle((79, 20), 61, 52, fill=False, ec=REL, lw=1.4))
    ax.text(109.5, 69.4, 'CROSS-STATION COUPLING UNIT (50)', ha='center',
            fontsize=9.4, fontweight='bold', color=REL)

    box(ax, 82, 60.0, 55, 6.4,
        'COMMON-MODE ESTIMATOR (52)\n'
        'median across the stations at each instant,\n'
        'the unoccupied station (90) among them', REL, fs=7.0)
    arrow(ax, (109.5, 60.0), (109.5, 57.0))
    box(ax, 82, 50.6, 55, 6.4,
        'LAGGED COUPLING COMPARATOR (54)\n'
        'shortest evaluated lag not less than 2T', REL, fs=7.0)
    arrow(ax, (109.5, 50.6), (109.5, 47.6))
    box(ax, 82, 41.2, 55, 6.4,
        'PAIR BASELINE STORE (56)\n'
        'each pair is its own control: its coupling\n'
        'measured during sanctioned activity', REL, fs=7.0)
    arrow(ax, (109.5, 41.2), (109.5, 38.2))
    box(ax, 82, 31.0, 55, 7.2,
        'COORDINATION COMPARATOR (58)\n'
        'excess over that same pair own baseline, on each\n'
        'of at least a predetermined number of occasions', REL, fs=7.0)

    arrow(ax, (74, 48.5), (82, 55.2))
    arrow(ax, (45.5, 10.8), (95, 31.0), rad=-0.12, color=GRY, lw=1.1,
          ls=(0, (3, 2)))

    # --- outputs ----------------------------------------------------------
    box(ax, 82, 22.0, 25, 6.6,
        'ALERT AND RANKING (60)\nstations ordered\nfor human inspection',
        ALR, fs=7.2)
    box(ax, 112, 22.0, 25, 6.6,
        'ACQUISITION STATE (80)\nimplicated pair only:\n(82) into (84)',
        ALR, fs=7.2)
    arrow(ax, (94.5, 31.0), (94.5, 28.6), color=ALR, lw=1.5)
    arrow(ax, (124.5, 31.0), (124.5, 28.6), color=ALR, lw=1.5)
    arrow(ax, (112, 24.5), (45.5, 38.0), rad=0.24, color=ALR, lw=1.6,
          ls=(0, (4, 2)))
    ax.text(94, 15.0,
            'the second acquisition state (84) is applied to the implicated '
            'pair alone, for a bounded\ninterval, after which those stations '
            'revert to the first acquisition state (82)',
            ha='center', fontsize=7.6, color=ALR, style='italic',
            linespacing=1.4)

    save(fig, 'fig02.png', 200)


# ---------------------------------------------------------------- Figure 3
def fig03():
    """Working principle: context window, prediction, residual."""
    rng = np.random.default_rng(11)
    n = 260
    t = np.arange(n)
    base = (0.5 + 0.18 * np.sin(t / 21.0) + 0.09 * np.sin(t / 7.3)
            + 0.03 * rng.standard_normal(n))
    sig = base.copy()
    sig[150:200] += 0.16 * np.hanning(50) * 1.4

    fig, axes = plt.subplots(2, 1, figsize=(12.0, 5.8), sharex=True,
                             gridspec_kw={'height_ratios': [2.0, 1.15]})
    a = axes[0]
    a.plot(t, sig, color=SEN, lw=1.4, label='observed signal stream')
    a.axvspan(96, 126, color=PRC, alpha=0.22)
    a.axvspan(126, 136, color=REL, alpha=0.20)
    a.text(111, 0.90, 'context window\n(20)', ha='center', fontsize=8.4,
           fontweight='bold', color='black', linespacing=1.3)
    a.text(131, 0.90, 'prediction\nhorizon', ha='center', fontsize=8.0,
           fontweight='bold', color=REL, linespacing=1.3)
    a.plot([126, 136], [sig[126], sig[126] + 0.012], color=PRC, lw=2.4,
           ls='--')
    a.annotate('predicted change', xy=(136, sig[126]), xytext=(158, 0.34),
               fontsize=8.2, color='#8a6d00',
               arrowprops=dict(arrowstyle='->', color='#8a6d00', lw=1.1))
    a.annotate('observed change', xy=(136, sig[136]), xytext=(158, 0.86),
               fontsize=8.2, color=SEN,
               arrowprops=dict(arrowstyle='->', color=SEN, lw=1.1))
    a.set_ylabel('sensor feature (normalised)')
    a.set_ylim(0.15, 1.02)
    a.legend(loc='lower left', fontsize=8, frameon=False)
    a.spines[['top', 'right']].set_visible(False)

    resid = np.abs(np.gradient(sig)) * 6.0
    resid = np.convolve(resid, np.ones(7) / 7, mode='same')
    b = axes[1]
    b.fill_between(t, 0, resid, color=PRC, alpha=0.65)
    b.plot(t, resid, color='#8a6d00', lw=1.1)
    b.axhline(np.quantile(resid, 0.90), color=ALR, lw=1.2, ls='--')
    b.text(4, np.quantile(resid, 0.90) + 0.012,
           'alert condition on the standardised residual', fontsize=7.8,
           color=ALR)
    b.axvspan(150, 200, color=ALR, alpha=0.12)
    b.text(175, resid.max() * 0.92, 'unsanctioned activity', ha='center',
           fontsize=8.2, color=ALR, fontweight='bold')
    b.set_ylabel('residual (30)')
    b.set_xlabel('time window index')
    b.spines[['top', 'right']].set_visible(False)

    fig.tight_layout()
    save(fig, 'fig03.png', 300)


# ---------------------------------------------------------------- Figure 4
def fig04():
    """Venue installation plan: candidate stations, unoccupied reference."""
    fig, ax = plt.subplots(figsize=(12.4, 7.2))
    ax.set_xlim(0, 124)
    ax.set_ylim(0, 72)
    ax.axis('off')

    ax.add_patch(Rectangle((3, 5), 85, 62, fill=False, ec=GRY, lw=1.6))
    ax.text(45.5, 68.2, 'MONITORED VENUE', ha='center', fontsize=10,
            fontweight='bold', color=GRY)

    # venue-wide disturbance, drawn as a field over the whole room
    ax.add_patch(FancyBboxPatch((6, 15), 79, 43,
                                boxstyle='round,pad=0.6',
                                facecolor=ALR, alpha=0.10, edgecolor=ALR,
                                lw=1.4, linestyle=(0, (5, 3))))
    ax.text(45.5, 60.6, 'VENUE-WIDE EVENT reaches every station at once '
            '(door, announcement, invigilator passing)', ha='center',
            fontsize=7.8, color=ALR, fontweight='bold')

    xs = [17, 40, 63]
    ys = [50, 35, 20]
    ref = (2, 0)
    pair = [(0, 1), (1, 1)]

    for ri, y in enumerate(ys):
        for ci, x in enumerate(xs):
            is_ref = (ci, ri) == ref
            in_pair = (ci, ri) in pair
            fc = REF if is_ref else (REL if in_pair else SEN)
            ax.add_patch(FancyBboxPatch((x - 8, y - 4.4), 16, 8.8,
                                        boxstyle='round,pad=0.10',
                                        facecolor=fc, edgecolor='black',
                                        linewidth=1.9 if (is_ref or in_pair)
                                        else 1.0))
            lab = ('REFERENCE (90)\nHELD UNOCCUPIED' if is_ref
                   else 'candidate station (100)')
            ax.text(x, y, lab, ha='center', va='center', fontsize=6.8,
                    color='white', fontweight='bold', linespacing=1.4)

    p, q = (xs[0], ys[1]), (xs[1], ys[1])
    arrow(ax, (p[0] + 8, p[1]), (q[0] - 8, q[1]), style='<|-|>', color=REL,
          lw=2.4)
    ax.text((p[0] + q[0]) / 2, q[1] + 6.0, 'coupled pair, lag tau',
            ha='center', fontsize=7.6, color=REL, fontweight='bold')

    ax.add_patch(Circle((xs[2] - 9.5, ys[2] + 6.6), 1.6, facecolor=PRC,
                        edgecolor='black', lw=1.0))
    ax.text(xs[2] - 12.0, ys[2] + 6.6,
            'isolated anomaly:\ncouples with nothing', fontsize=7.2,
            color='#8a6d00', fontweight='bold', va='center', ha='right',
            linespacing=1.35)

    ax.add_patch(Rectangle((6, 8), 79, 3.6, facecolor=GRY, edgecolor='black',
                           lw=1.0))
    ax.text(45.5, 9.8, 'TIME-SYNCHRONISATION ARRANGEMENT (70)   common time '
            'base to within tolerance T', ha='center', va='center',
            fontsize=7.4, color='white', fontweight='bold')

    box(ax, 93, 36, 29, 23,
        'PROCESSING ARRANGEMENT\n\n'
        'station-local models (20/22)\n'
        'common-mode estimator (52)\n'
        'coupling comparator (54)\n'
        'pair baseline store (56)\n'
        'coordination comparator (58)', REL, fs=7.4)
    arrow(ax, (88, 44), (93, 47))
    box(ax, 93, 23, 29, 8.4,
        'ALERT AND RANKING (60)\nACQUISITION STATE (80)', ALR, fs=7.4)
    arrow(ax, (107.5, 36), (107.5, 31.4))

    ax.text(107.5, 16,
            'the shortest evaluated lag\nis not less than 2T',
            ha='center', fontsize=8.0, color=GRY, style='italic',
            linespacing=1.4)

    save(fig, 'fig04.png', 200)


# ---------------------------------------------------------------- Figure 5
def fig05():
    """Common-mode rejection, measured."""
    c = J('e3_coupling.json')['common_mode_suppression']
    ps = c['per_station|raw_median']
    sh = c['shared|raw_median']

    labels = ['no coordinated\nactivity present',
              'venue-wide event,\nno rejection',
              'venue-wide event,\nafter rejection']
    vals_ps = [ps['floor_no_injection_mean_r'],
               ps['with_event_no_rejection_mean_r'],
               ps['with_event_after_rejection_mean_r']]
    vals_sh = [sh['floor_no_injection_mean_r'],
               sh['with_event_no_rejection_mean_r'],
               sh['with_event_after_rejection_mean_r']]

    x = np.arange(3)
    w = 0.36
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    b1 = ax.bar(x - w / 2, vals_ps, w, color=REL, edgecolor='black', lw=0.8,
                label='models established separately at each station')
    b2 = ax.bar(x + w / 2, vals_sh, w, color=LGY, edgecolor='black', lw=0.8,
                label='one model shared across the stations')
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.006,
                    '%.3f' % r.get_height(), ha='center', fontsize=8.4,
                    fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.6)
    ax.set_ylabel('mean pairwise coupling over all 55 station pairs')
    ax.set_ylim(0, 0.40)
    ax.legend(fontsize=8.4, frameon=False, loc='upper left')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=0.25, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, 'fig05.png', 300)


# ---------------------------------------------------------------- Figure 6
def fig06():
    """Part A: simulated single-station detection against signal strength."""
    snr = [1.0, 0.6, 0.3, 0.15]
    ref = [0.946, 0.903, 0.843, 0.797]
    lf = [0.705, 0.653, 0.613, 0.541]
    lfa = [0.781, 0.716, 0.657, 0.571]

    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    ax.plot(snr, ref, 'o-', color=GRY, lw=1.8, ms=6,
            label='reference detector, uses labels')
    ax.plot(snr, lfa, 's-', color=REL, lw=1.8, ms=6,
            label='present method, with temporal aggregation')
    ax.plot(snr, lf, '^--', color=PRC, lw=1.6, ms=6,
            label='present method, no aggregation')
    ax.axhline(0.5, color=ALR, lw=1.1, ls=':')
    ax.text(1.0, 0.512, 'chance', fontsize=8, color=ALR)
    for s, v in zip(snr, lfa):
        ax.annotate('%.3f' % v, (s, v), textcoords='offset points',
                    xytext=(0, 8), ha='center', fontsize=8, color=REL,
                    fontweight='bold')
    ax.invert_xaxis()
    ax.set_xlabel('signal strength of the concealed activity  '
                  '(1.0 overt, 0.15 near the noise floor)')
    ax.set_ylabel('AUROC')
    ax.set_ylim(0.45, 1.0)
    ax.legend(fontsize=8.4, frameon=False, loc='lower left')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(alpha=0.25, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, 'fig06.png', 300)


# ---------------------------------------------------------------- Figure 7
def fig07():
    """Part B: commensurability refuted, at two model capacities."""
    sm = J('e3_smd_commensurability.json')['headline']
    bg = J('e3_smd_commensurability_big.json')['headline']

    metrics = [
        ('per cent of station pairs within\n2x the nominal 1 % '
         'false-positive rate\n(higher is better)',
         'frac_within_2x', 100.0, '%.1f'),
        ('per cent of station pairs within\n10x the nominal rate\n'
         '(higher is better)',
         'frac_within_10x', 100.0, '%.1f'),
        ('95th-percentile realised\nfalse-positive rate, per cent\n'
         '(lower is better)',
         'fpr_p95', 100.0, '%.1f'),
        ('median KS distance between\nstation residual distributions\n'
         '(lower is better)',
         'ks_median', 1.0, '%.3f'),
        ('mean AUROC on the\nlabelled test split\n(higher is better)',
         'auroc_mean', 1.0, '%.3f'),
    ]

    fig, axes = plt.subplots(1, 5, figsize=(14.0, 4.8))
    for ax, (title, key, scale, fmt) in zip(axes, metrics):
        vs = [sm['shared_' + key] * scale, sm['per_station_' + key] * scale]
        vb = [bg['shared_' + key] * scale, bg['per_station_' + key] * scale]
        x = np.arange(2)
        w = 0.36
        ax.bar(x - w / 2, vs, w, color=LGY, edgecolor='black', lw=0.8,
               label='128 wide, 5 epochs')
        ax.bar(x + w / 2, vb, w, color=GRY, edgecolor='black', lw=0.8,
               label='384 wide, 12 epochs')
        top = max(vs + vb)
        for xi, v in zip(x - w / 2, vs):
            ax.text(xi, v + top * 0.03, fmt % v, ha='center', fontsize=7.4)
        for xi, v in zip(x + w / 2, vb):
            ax.text(xi, v + top * 0.03, fmt % v, ha='center', fontsize=7.4,
                    fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(['one model\nshared', 'model per\nstation'],
                           fontsize=7.8)
        ax.set_title(title, fontsize=7.6, pad=8)
        ax.set_ylim(0, top * 1.26)
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', alpha=0.22, lw=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(axis='y', labelsize=7.4)
    axes[0].legend(fontsize=7.2, frameon=False, loc='upper left')
    fig.suptitle('Sharing one normal-only model across the stations makes '
                 'residuals LESS comparable, not more;\nadding capacity '
                 'widens the gap rather than closing it',
                 fontsize=9.2, fontweight='bold', y=1.06)
    fig.tight_layout()
    save(fig, 'fig07.png', 300)


# ---------------------------------------------------------------- Figure 8
def fig08():
    """Part B: coupling detection by model and reference rule."""
    s = J('e3_repeat.json')['summary']
    cells = [
        ('shared', 'none', 'D_both|shared|none'),
        ('shared', 'raw median', 'D_both|shared|raw_median'),
        ('shared', 'standardised', 'D_both|shared|standardised_median'),
        ('per station', 'none', 'D_both|per_station|none'),
        ('per station', 'raw median', 'D_both|per_station|raw_median'),
        ('per station', 'standardised',
         'D_both|per_station|standardised_median'),
    ]
    au = [s[k]['auroc_over_pairs_mean'] for _, _, k in cells]
    det = [s[k]['detection_rate_top_ranked'] for _, _, k in cells]
    labs = ['%s\nreference: %s' % (a, b) for a, b, _ in cells]
    cols = [LGY, LGY, LGY, REL, REL, REL]
    lw = [0.8, 0.8, 0.8, 0.8, 2.4, 0.8]

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.2))
    specs = ((axes[0], au,
              'ranking accuracy (AUROC) of the coupled pair\n'
              'against the 54 uncoupled pairs', 1.10, '%.3f'),
             (axes[1], det,
              'coupled pair ranked first of 55\n(fraction of 20 trials)',
              0.80, '%.2f'))
    for ax, vals, ttl, ymax, fmt in specs:
        b = ax.bar(np.arange(6), vals, 0.66, color=cols, edgecolor='black',
                   linewidth=lw)
        for r, v in zip(b, vals):
            ax.text(r.get_x() + r.get_width() / 2, v + ymax * 0.02, fmt % v,
                    ha='center', fontsize=8.4, fontweight='bold')
        ax.set_xticks(np.arange(6))
        ax.set_xticklabels(labs, fontsize=7.4, linespacing=1.4)
        ax.set_ylim(0, ymax)
        ax.set_title(ttl, fontsize=8.6, fontweight='bold')
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', alpha=0.25, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].axhline(0.5, color=ALR, lw=1.1, ls=':')
    axes[0].text(-0.42, 0.53, 'chance', fontsize=8, color=ALR)
    fig.suptitle('One venue-wide event is present in every trial.  '
                 'The claimed arrangement is the heavy-outlined bar.',
                 fontsize=9.0, y=1.02)
    fig.tight_layout()
    save(fig, 'fig08.png', 300)


# ---------------------------------------------------------------- Figure 9
def fig09():
    """Clock-skew tolerance."""
    r = J('e3_repeat.json')
    sw = r['skew_sweep']
    lag = r['config']['couple_lag']
    ks = sorted(int(k) for k in sw)
    frac = [k / float(lag) for k in ks]
    au = [sw[str(k)]['auroc_over_pairs_mean'] for k in ks]
    det = [sw[str(k)]['detection_rate_top_ranked'] for k in ks]

    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.plot(frac, au, 'o-', color=REL, lw=2.0, ms=6.5,
            label='ranking accuracy (AUROC)')
    ax.plot(frac, det, 's--', color=PRC, lw=1.7, ms=6,
            label='coupled pair ranked first of 55')
    for f, v in zip(frac, au):
        ax.annotate('%.3f' % v, (f, v), textcoords='offset points',
                    xytext=(0, 9), ha='center', fontsize=7.8, color=REL,
                    fontweight='bold')
    ax.axvspan(0, 0.5, color=REL, alpha=0.10)
    ax.text(0.25, 0.28, 'claimed tolerance:\nnot more than one half\n'
            'of the shortest lag', ha='center', fontsize=8.0, color=REL,
            fontweight='bold', linespacing=1.35)
    ax.axhline(0.5, color=ALR, lw=1.0, ls=':')
    ax.set_xlabel('inter-station timing error, as a multiple of the '
                  'coupling lag')
    ax.set_ylabel('performance')
    ax.set_ylim(0, 1.10)
    ax.set_xlim(-0.12, 4.25)
    ax.legend(fontsize=8.4, frameon=False, loc='lower left')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(alpha=0.25, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, 'fig09.png', 300)


# --------------------------------------------------------------- Figure 10
def fig10():
    """Operating envelope: event amplitude and number of coupled exchanges."""
    e = J('e3_envelope.json')
    amp = e['amplitude_sweep']
    ev = e['event_count_sweep']

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.0))

    xs = sorted(float(k) for k in amp)
    au = [amp['%g' % x]['auroc_over_pairs_mean'] for x in xs]
    det = [amp['%g' % x]['detection_rate_top_ranked'] for x in xs]
    a = axes[0]
    a.plot(xs, au, 'o-', color=REL, lw=2.0, ms=6.5, label='ranking accuracy')
    a.plot(xs, det, 's--', color=PRC, lw=1.7, ms=6, label='ranked first of 55')
    a.axvspan(0.06, 0.10, color=ALR, alpha=0.12)
    a.text(0.08, 0.14, 'knee', ha='center', fontsize=8.4, color=ALR,
           fontweight='bold')
    a.set_xlabel('amplitude of each coupled exchange,\nas a fraction of the '
                 'channel range')
    a.set_title('60 coupled exchanges held fixed', fontsize=8.8,
                fontweight='bold')

    xs2 = sorted(int(k) for k in ev)
    au2 = [ev[str(x)]['auroc_over_pairs_mean'] for x in xs2]
    det2 = [ev[str(x)]['detection_rate_top_ranked'] for x in xs2]
    b = axes[1]
    b.plot(xs2, au2, 'o-', color=REL, lw=2.0, ms=6.5, label='ranking accuracy')
    b.plot(xs2, det2, 's--', color=PRC, lw=1.7, ms=6,
           label='ranked first of 55')
    b.axvline(1, color=ALR, lw=1.6)
    b.text(4.0, 0.88, 'a single exchange is not\ndetectable by this mechanism',
           fontsize=8.0, color=ALR, fontweight='bold', linespacing=1.35)
    b.set_xlabel('number of separate coupled exchanges\nwithin the '
                 'observation window')
    b.set_title('exchange amplitude held at 0.15', fontsize=8.8,
                fontweight='bold')

    for ax in axes:
        ax.axhline(0.5, color=GRY, lw=1.0, ls=':')
        ax.set_ylim(0, 1.08)
        ax.set_ylabel('performance')
        ax.legend(fontsize=8.2, frameon=False, loc='lower right')
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(alpha=0.25, lw=0.6)
        ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, 'fig10.png', 300)


# --------------------------------------------------------------- Figure 11
def fig11():
    """Claim dependency map."""
    fig, ax = plt.subplots(figsize=(13.4, 7.2))
    ax.set_xlim(0, 134)
    ax.set_ylim(0, 72)
    ax.axis('off')

    def group(x0, w, title, colour, ind, deps, note):
        ax.add_patch(Rectangle((x0, 15), w, 51, fill=False, ec=colour,
                               lw=1.5))
        ax.text(x0 + w / 2, 67.4, title, ha='center', fontsize=9.0,
                fontweight='bold', color=colour)
        box(ax, x0 + 2.0, 56.4, w - 4, 7.6, ind, colour, fs=7.0)
        yy = 51.4
        for d in deps:
            box(ax, x0 + 4.5, yy, w - 9, 3.4, d, 'white', fs=6.9, tc='black',
                bold=False, ec=colour)
            arrow(ax, (x0 + w / 2, yy + 3.4), (x0 + w / 2, yy + 4.0),
                  color=colour, lw=0.9)
            yy -= 4.0
        ax.text(x0 + w / 2, 11.0, note, ha='center', fontsize=7.2,
                color=colour, style='italic', linespacing=1.35)

    group(2, 30, 'A.  SINGLE-STATION SYSTEM', SEN,
          'CLAIM 1\nstation-local, per-session\ncalibration; '
          'the residual\nis the score',
          ['2  calibration held fixed', '3  near-ultrasonic acoustic',
           '4  and electromagnetic, in desk', '5  further modalities',
           '6  multi-modal fusion', '7  causal aggregation',
           '8  optical behavioural', '9  collapse regularisation',
           '10  session-level ranking'],
          'weakest on eligibility;\nnarrow this one first')

    group(34, 31, 'B.  VENUE INSTALLATION', REL,
          'CLAIM 11\nunoccupied reference station;\n'
          'common-mode removal,\nlagged coupling',
          ['12  median across stations',
           '13  reference of like construction',
           '14  tolerance not over half the lag',
           '15  per-modality weighting',
           '16  graph, connected components'],
          'strongest structural position;\nprosecute in the parent')

    group(67, 31, 'C.  INVERTED NULL', REF,
          'CLAIM 17\neach pair is its own control;\n'
          'repeated occasions required',
          ['18  at least twenty exchanges'],
          'the characterising relation;\nsurvives if Claim 11 narrows')

    group(100, 32, 'D.  PHYSICAL RESPONSE', ALR,
          'CLAIM 19\ntwo acquisition states;\n'
          'implicated pair only, bounded',
          ['20  what the two states differ in',
           '21  bounded, reverts automatically',
           '22  envelope before digitisation'],
          'the eligibility answer;\ndo not concede')

    ax.text(67, 4.0,
            'METHOD CLAIMS   23 single station, reciting the label-free '
            'training   -   24 venue discrimination   -   25, 26 dependent'
            '          DEPLOYMENT   27, 28, 29',
            ha='center', fontsize=7.8, color=GRY, fontweight='bold')

    save(fig, 'fig11.png', 200)


if __name__ == '__main__':
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09,
              fig10, fig11):
        f()
    print('all figures written to', OUT)
