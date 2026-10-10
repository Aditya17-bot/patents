"""Figures 1-7 for the causal emission-response interlock disclosure.

Architecture figures at dpi=200, data figures at dpi=300.  All labels ASCII.
Data figures read the saved analysis outputs; nothing is hard-coded except
labels.
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

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figures')
SCRATCH = os.environ.get(
    'PATENT_SCRATCH',
    r'C:\Users\rober\AppData\Local\Temp\claude\C--adi-patent-InfoSec'
    r'\46f3d2b0-9227-41c2-805a-1a3b15973f2c\scratchpad')
HW = r'C:\adi\patents\01_02_infosec\hardware'

HWC = '#1565C0'      # hardware / sensing
PRC = '#F9A825'      # processing
VAL = '#2E7D32'      # corroboration / validation
ENF = '#C62828'      # enforcement
GRY = '#455A64'

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})


def box(ax, x, y, w, h, text, fc, fs=8.2, tc='white', bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.06',
                                facecolor=fc, edgecolor='black', linewidth=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fs, color=tc, fontweight='bold' if bold else 'normal',
            linespacing=1.35)


def arrow(ax, p, q, style='-|>', lw=1.3, color='black', ls='-', rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=11,
                                 linewidth=lw, color=color, linestyle=ls,
                                 connectionstyle='arc3,rad=%.2f' % rad,
                                 shrinkA=1, shrinkB=1))


# ---------------------------------------------------------------- Figure 1
def fig02():
    fig, ax = plt.subplots(figsize=(14.4, 7.8))
    ax.set_xlim(0, 144)
    ax.set_ylim(0, 78)
    ax.axis('off')

    ax.add_patch(Rectangle((1, 1), 142, 76, fill=False, ec='#B0BEC5', lw=1.0,
                           linestyle=(0, (4, 3))))
    ax.text(2.5, 74.2, 'CANDIDATE STATION / DESK ASSEMBLY (100)', fontsize=9.5,
            fontweight='bold', color=GRY)

    ax.text(16.5, 69.0, 'PHYSICAL SENSING', fontsize=9, fontweight='bold', color=HWC, ha='center')
    box(ax, 3, 59, 27, 7.6, 'Display panel (200) with\nphotometric onset sensor (210)', HWC, 7.7)
    box(ax, 3, 49.5, 27, 7.6, 'Imaging sensor (300)\ngaze / scanpath / pupil', HWC, 7.7)
    box(ax, 3, 40, 27, 7.6, 'Desk-contact transducer (400)\nstructure-borne pickup', HWC, 7.7)
    box(ax, 3, 30.5, 27, 7.6, 'Desk inertial unit (410)\ntri-axial accel + gyro', HWC, 7.7)
    box(ax, 3, 21, 27, 7.6, 'Input device stream (500)\nkeystroke / pointer timing', HWC, 7.7)

    ax.text(50, 69.0, 'CHANNEL DERIVATION', fontsize=9, fontweight='bold', color=PRC, ha='center')
    box(ax, 37, 59, 26, 7.6, 'Onset anchor T0\n(physical, not an API event)', PRC, 7.7, 'black')
    box(ax, 37, 49.5, 26, 7.6, 'Gaze estimator (310)\nscanpath (320) pupil (330)', PRC, 7.7, 'black')
    box(ax, 37, 40, 26, 7.6, 'Emission attribution (420)\nT1, seated candidate only', PRC, 7.7, 'black')
    box(ax, 37, 28.5, 26, 9.6, 'Reliability transfer (430)\none inertial measurement,\n'
                               'two placements: it weights (420)\nand thresholds (310)', PRC, 7.4, 'black')
    box(ax, 37, 19, 26, 7.6, 'Enrolled profile store (510)\ncommit time T2', PRC, 7.7, 'black')

    for ys, yd in ((59, 59), (49.5, 49.5), (40, 40), (30.5, 28.5 + 1.0), (21, 19)):
        arrow(ax, (30, ys + 3.8), (37, yd + 3.8))

    arrow(ax, (41.5, 38.1), (41.5, 40.0), color='#E65100', lw=1.7, ls=(0, (3, 2)))
    arrow(ax, (58.5, 38.1), (58.5, 49.5), color='#E65100', lw=1.7, ls=(0, (3, 2)),
          rad=0.42)

    ax.text(84.5, 69.0, 'CAUSAL LATENCY INTERLOCK (600)', fontsize=9,
            fontweight='bold', color=VAL, ha='center')
    box(ax, 69, 53, 31, 13.0,
        'Causal band comparators (615, 610)\nT1 - T0 inside the consultation interval ?\n'
        'T2 - T1 inside the assistance band ?', VAL, 7.5)
    box(ax, 69, 37, 31, 13.0,
        'Discontinuity comparator (620)\ncommit dynamics against the\nenrolled profile: transcribing ?', VAL, 8.0)
    box(ax, 69, 21, 31, 13.0,
        'Corroboration value unit (700)\nordinal value A\neligibility comparator (710)', VAL, 8.0)

    arrow(ax, (63, 62.8), (69, 61.5))
    arrow(ax, (63, 43.8), (69, 46.5))
    arrow(ax, (63, 33.3), (69, 44.5))
    arrow(ax, (63, 22.8), (69, 42.0))
    arrow(ax, (84.5, 53), (84.5, 50.4))
    arrow(ax, (84.5, 37), (84.5, 34.4))

    ax.text(122.5, 69.0, 'ENFORCEMENT', fontsize=9, fontweight='bold', color=ENF,
            ha='center')
    box(ax, 106, 45, 33, 21.0,
        'Graduated enforcement scheduler (800)\n\npersistence counter (810)\n'
        'per-candidate cooldown (820)\nglobal session interval (830)\n'
        'escalation comparator (840)', ENF, 7.8)
    box(ax, 106, 34, 33, 8.6,
        'DUAL-CHANNEL INTERLOCK (850)\ntwo physically independent modalities\n'
        'required before any actuation', '#8E0000', 7.8)
    arrow(ax, (122.5, 45), (122.5, 42.6), lw=1.7)

    box(ax, 106, 24.5, 15.6, 7.2, 'Desk indicator\n/ haptic (910)', GRY, 7.5)
    box(ax, 123.4, 24.5, 15.6, 7.2, 'In-line HID\ngating unit (920)', GRY, 7.5)
    box(ax, 106, 15.5, 33, 7.2, 'Session hold latch (930)\nEvidence record store (950)', GRY, 7.5)

    arrow(ax, (100, 28.0), (106, 30.0), lw=1.5)
    arrow(ax, (113.8, 34), (113.8, 31.7), lw=1.5)
    arrow(ax, (131.2, 34), (131.2, 31.7), lw=1.5)
    arrow(ax, (122.5, 24.5), (122.5, 22.7), lw=1.2)

    ax.text(87, 8.0,
            'The gating unit (920) is fail-closed: the candidate input path is passing whenever the '
            'controller is unpowered\nor unresponsive, and every gate assertion is watchdog-bounded. '
            'Opening the path is the active, refreshed state.',
            fontsize=7.4, ha='center', va='center', color=GRY, style='italic',
            linespacing=1.6,
            bbox=dict(boxstyle='round,pad=0.5', fc='#FFF3E0', ec='#FFB74D', lw=0.9))

    fig.savefig(os.path.join(OUT, 'fig02.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig02  system architecture')


# ---------------------------------------------------------------- Figure 1
def fig01():
    """Causal timing kernel: the accepted geometry and the four rejections."""
    fig, ax = plt.subplots(figsize=(13.2, 7.6))
    ax.set_xlim(0, 132)
    ax.set_ylim(0, 76)
    ax.axis('off')

    ax.add_patch(FancyBboxPatch((4, 36.5), 124, 37.5,
                                boxstyle='round,pad=0.4', facecolor='#F4FBF4',
                                edgecolor='#A5D6A7', lw=1.0))
    ax.text(7.5, 71.4, 'ACCEPTED GEOMETRY', fontsize=10.5, fontweight='bold',
            color=VAL, va='center')
    ax.text(35.0, 71.4, 'the relation that external assistance necessarily imposes',
            fontsize=8.6, color=GRY, va='center', style='italic')

    ax.plot([10, 122], [52, 52], color='black', lw=1.6, zorder=3)
    ax.annotate('', xy=(124.6, 52), xytext=(122, 52),
                arrowprops=dict(arrowstyle='-|>', color='black', lw=1.6))
    ax.text(125.4, 52, 'time', fontsize=8.4, va='center', color='black')

    band_lo, band_hi = 70.0, 104.0
    ax.add_patch(Rectangle((band_lo, 51.1), band_hi - band_lo, 1.8,
                           facecolor='#C8E6C9', edgecolor=VAL, lw=1.2, zorder=2))
    for bx in (band_lo, band_hi):
        ax.plot([bx, bx], [52.9, 61.0], color=VAL, lw=0.9, ls=':', zorder=1)
    ax.annotate('', xy=(band_hi, 61.0), xytext=(band_lo, 61.0),
                arrowprops=dict(arrowstyle='<|-|>', color=VAL, lw=1.6))
    ax.text((band_lo + band_hi) / 2, 67.4,
            'BOUNDED EXTERNAL-ASSISTANCE LATENCY BAND (610)',
            ha='center', fontsize=9.2, fontweight='bold', color=VAL)
    ax.text((band_lo + band_hi) / 2, 65.6,
            'the shortest interval in which a helper could hear, resolve and answer,\n'
            'and the longest over which a causal relation is still asserted',
            ha='center', va='top', fontsize=7.9, color=GRY, linespacing=1.5)

    cons_lo, cons_hi = 20.0, 42.0
    ax.add_patch(Rectangle((cons_lo, 51.1), cons_hi - cons_lo, 1.8,
                           facecolor='#BBDEFB', edgecolor=HWC, lw=1.2, zorder=2))
    ax.annotate('', xy=(cons_hi, 57.0), xytext=(cons_lo, 57.0),
                arrowprops=dict(arrowstyle='<|-|>', color=HWC, lw=1.5))
    ax.text(31, 63.9, 'BOUNDED CONSULTATION INTERVAL (615)',
            ha='center', fontsize=9.0, fontweight='bold', color=HWC)
    ax.text(31, 58.0,
            'lower bound: the shortest time in which the item could\n'
            'have been read and vocalised; upper bound: the next\n'
            'presentation instant, which binds the emission to one item',
            ha='center', va='bottom', fontsize=7.6, color=GRY, linespacing=1.5)

    for x, lab, sub, col in [
            (20, 'T0', 'question onset\nphotometric (210)', HWC),
            (42, 'T1', 'attributed covert\nemission (420)', '#00695C'),
            (88, 'T2', 'answer commit\ninput devices (500)', PRC)]:
        ax.plot([x, x], [50.9, 53.1], color=col, lw=3.2, zorder=4)
        ax.text(x, 53.7, lab, ha='center', va='bottom', fontsize=12,
                fontweight='bold', color=col)
        ax.text(x, 50.2, sub, ha='center', va='top', fontsize=8.0, color=GRY,
                linespacing=1.45)

    ax.add_patch(FancyBboxPatch((7.5, 38.6), 55.5, 8.0,
                                boxstyle='round,pad=0.28', facecolor='#E3F2FD',
                                edgecolor=HWC, lw=1.0))
    ax.text(9.4, 45.2, 'Why T0 is measured, and what it does', fontsize=8.4,
            fontweight='bold', color=HWC, va='center')
    ax.text(9.4, 41.7,
            'A software render event fires before the panel emits light, and the examined\n'
            'machine can delay or falsify it. The photodiode (210) times the photons that\n'
            'reached the candidate, bounds the emission from below, and binds it to one item.',
            fontsize=7.1, color=GRY, va='center', linespacing=1.6)

    ax.text(67.5, 45.9, 'ON ACCEPTANCE', fontsize=8.4, fontweight='bold',
            color=VAL, va='center')
    chips = [('corroboration\nvalue (700)', VAL), ('eligibility\ncomparator (710)', VAL),
             ('enforcement\nscheduler (800)', ENF)]
    for i, (t, c) in enumerate(chips):
        cx = 67.5 + i * 19.6
        box(ax, cx, 38.4, 16.0, 5.8, t, c, 7.4)
        if i:
            arrow(ax, (cx - 3.6, 41.3), (cx, 41.3), lw=1.2)

    ax.plot([4, 128], [34.0, 34.0], color='#CFD8DC', lw=1.2)
    ax.text(7.5, 31.4, 'REJECTED', fontsize=10.5, fontweight='bold', color=ENF,
            va='center')
    ax.text(24.0, 31.4,
            'five separable grounds; the one that fired is written to the evidence '
            'record store (950) with the cycle',
            fontsize=8.6, color=GRY, va='center', style='italic')

    panels = [
        (dict(t0=0.05, t1=0.24, t2=0.88, band=(0.36, 0.64),
              bandlab='consultation window'),
         'T1 - T0\nTOO EARLY',
         'the emission arrived before\nthe item could be read: it is\n'
         'carried over from the last one'),
        (dict(t0=0.08, t1=0.34, t2=0.46, band=(0.58, 0.90)),
         'T2 - T1\nTOO SHORT',
         'the answer was committed\nbefore any helper could\nhave replied to it'),
        (dict(t0=0.06, t1=0.26, t2=0.95, band=(0.42, 0.74)),
         'T2 - T1\nTOO LONG',
         'no causal link remains; the\ncommit is unrelated to the\nemission'),
        (dict(t0=0.08, t1=None, t2=0.68, band=(0.50, 0.86)),
         'EMISSION\nNOT ATTRIBUTED',
         'airborne only, no\nstructure-borne coupling:\na neighbour spoke'),
        (dict(t0=0.08, t1=0.32, t2=0.68, band=(0.50, 0.86), composed=True),
         'COMMIT DYNAMICS\nMATCH (510)',
         'the timing is the candidate\ncomposing, not transcribing\na received answer'),
    ]
    W = 23.0
    x0s = [4.0 + i * (W + 2.25) for i in range(5)]
    for (geo, title, why), x0 in zip(panels, x0s):
        ax.add_patch(FancyBboxPatch((x0, 4.6), W, 23.6,
                                    boxstyle='round,pad=0.3', facecolor='#FFF8F8',
                                    edgecolor='#EF9A9A', lw=1.0))
        ax.add_patch(Circle((x0 + 2.7, 25.2), 1.6, facecolor=ENF,
                            edgecolor='none', zorder=5))
        ax.text(x0 + 2.7, 25.2, 'X', ha='center', va='center', color='white',
                fontsize=9.0, fontweight='bold', zorder=6)
        ax.text(x0 + 5.6, 25.2, title, fontsize=7.5, fontweight='bold',
                color=ENF, va='center', linespacing=1.4)

        ax.plot([x0 + 2.0, x0 + W - 2.0], [16.4, 16.4], color='black', lw=1.1)

        def px(f, _x0=x0):
            return _x0 + 2.0 + f * (W - 4.0)

        bl, bh = geo['band']
        ok = geo.get('composed', False)
        bc = '#C8E6C9' if ok else '#FFCDD2'
        be = VAL if ok else '#E57373'
        ax.add_patch(Rectangle((px(bl), 15.7), px(bh) - px(bl), 1.4,
                               facecolor=bc, edgecolor=be, lw=1.0, zorder=2))
        if geo.get('bandlab'):
            ax.text((px(bl) + px(bh)) / 2, 14.7, geo['bandlab'], ha='center',
                    va='top', fontsize=6.7, color=ENF, style='italic')

        ax.plot([px(geo['t0'])] * 2, [15.4, 17.4], color=HWC, lw=2.4, zorder=4)
        ax.text(px(geo['t0']), 17.8, 'T0', ha='center', fontsize=7.4,
                fontweight='bold', color=HWC)
        if geo['t1'] is None:
            ax.plot([px(0.34)] * 2, [15.4, 17.4], color='#9E9E9E', lw=2.0,
                    ls=(0, (1.6, 1.4)), zorder=4)
            ax.text(px(0.34), 17.8, 'T1?', ha='center', fontsize=7.4,
                    fontweight='bold', color='#9E9E9E')
            ax.text(px(0.34), 14.7, 'airborne only', ha='center', va='top',
                    fontsize=6.9, color='#9E9E9E', style='italic')
        else:
            ax.plot([px(geo['t1'])] * 2, [15.4, 17.4], color='#00695C', lw=2.4,
                    zorder=4)
            ax.text(px(geo['t1']), 17.8, 'T1', ha='center', fontsize=7.4,
                    fontweight='bold', color='#00695C')
        t2c = PRC if ok else ENF
        ax.plot([px(geo['t2'])] * 2, [15.4, 17.4], color=t2c, lw=2.4, zorder=4)
        ax.text(px(geo['t2']), 17.8, 'T2', ha='center', fontsize=7.4,
                fontweight='bold', color=t2c)
        if ok:
            ax.text(px(geo['t2']) + 1.0, 14.7, 'in band, but\nmatches (510)',
                    ha='center', va='top', fontsize=6.7, color=ENF,
                    style='italic', linespacing=1.4)

        ax.text(x0 + W / 2, 8.4, why, ha='center', va='center', fontsize=7.0,
                color=GRY, linespacing=1.55)

    fig.savefig(os.path.join(OUT, 'fig01.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig01  causal timing kernel')


# ---------------------------------------------------------------- Figure 3
def fig03():
    """Physical arrangement of the instrumented station, in side elevation."""
    fig, ax = plt.subplots(figsize=(13.4, 8.4))
    ax.set_xlim(0, 134)
    ax.set_ylim(0, 84)
    ax.axis('off')

    DESK = '#D7CCC8'
    DESK_E = '#8D6E63'
    BODY = '#B0BEC5'
    SB = '#004D40'
    AB = '#00897B'
    FAR = '#BDBDBD'

    def num(x, y, t, col=GRY, fs=7.6, ha='center', halo=True):
        bb = dict(boxstyle='round,pad=0.16', fc='white', ec='none', alpha=0.85)
        ax.text(x, y, t, fontsize=fs, fontweight='bold', color=col, ha=ha,
                va='center', zorder=8, bbox=bb if halo else None)

    # ---------------------------------------------------------- the room
    ax.plot([4, 130], [30, 30], color='#90A4AE', lw=1.4)
    ax.add_patch(Rectangle((14, 54), 66, 2.8, facecolor=DESK, edgecolor=DESK_E,
                           lw=1.2, zorder=3))
    ax.add_patch(Rectangle((16, 30), 4, 24, facecolor=DESK, edgecolor=DESK_E, lw=1.2))
    ax.add_patch(Rectangle((74, 30), 4, 24, facecolor=DESK, edgecolor=DESK_E, lw=1.2))
    num(15.5, 58.4, '(100)', DESK_E, 8.0, 'left')

    # ---------------------------------------------------------- candidate
    ax.add_patch(Circle((86, 68), 4.2, facecolor=BODY, edgecolor=GRY, lw=1.1))
    ax.add_patch(FancyBboxPatch((80.5, 56.5), 11, 11.0, boxstyle='round,pad=0.4',
                                facecolor=BODY, edgecolor=GRY, lw=1.1))
    ax.plot([80.5, 73.0], [63.5, 57.6], color=GRY, lw=2.8, solid_capstyle='round')
    ax.add_patch(Rectangle((81, 48), 11, 2.2, facecolor='#CFD8DC', edgecolor=GRY, lw=1.0))
    ax.add_patch(Rectangle((92, 30), 3, 26, facecolor='#CFD8DC', edgecolor=GRY, lw=1.0))
    ax.text(86, 74.4, 'SEATED CANDIDATE', fontsize=8.2, fontweight='bold',
            color=GRY, ha='center')

    # ---------------------------------------------------------- display panel
    ax.add_patch(Rectangle((20, 56.8), 22, 16, facecolor='#263238',
                           edgecolor='black', lw=1.3, zorder=4))
    ax.add_patch(Rectangle((21.2, 58.0), 19.6, 13.6, facecolor='#37474F',
                           edgecolor='none', zorder=5))
    ax.add_patch(Rectangle((40.0, 66.2), 1.6, 3.4, facecolor='white',
                           edgecolor='#FFB300', lw=1.4, zorder=6))
    ax.add_patch(Rectangle((43.0, 66.0), 3.6, 3.8, facecolor=HWC,
                           edgecolor='black', lw=1.1, zorder=6))
    ax.add_patch(Rectangle((42.4, 65.4), 4.8, 5.0, facecolor='none',
                           edgecolor='#455A64', lw=1.4, zorder=7))
    ax.plot([41.6, 43.0], [67.9, 67.9], color='#FFB300', lw=1.6, zorder=6)
    num(31, 59.6, '(200)', 'white', 8.0, halo=False)
    num(47.4, 71.8, '(210)', HWC, 7.8, 'left')
    num(38.6, 67.9, '(205)', '#E65100', 7.0, 'right')
    ax.add_patch(Rectangle((27.6, 72.8), 4.6, 2.4, facecolor=HWC,
                           edgecolor='black', lw=1.1, zorder=6))
    num(29.9, 77.2, '(300)', HWC, 7.8)

    # ---------------------------------------------------------- desk-top parts
    ax.add_patch(Rectangle((47.0, 56.8), 4.0, 3.0, facecolor='#455A64',
                           edgecolor='black', lw=1.0, zorder=5))
    num(48.2, 63.4, '(402)', AB, 7.6)
    ax.add_patch(Rectangle((53.0, 56.8), 3.4, 2.6, facecolor='#ECEFF1',
                           edgecolor=GRY, lw=1.0, zorder=5))
    ax.add_patch(Circle((54.7, 58.1), 0.8, facecolor='#FFB300', edgecolor=GRY,
                        lw=0.7, zorder=6))
    num(55.6, 61.2, '(910)', '#F57F17', 7.6)
    ax.add_patch(Rectangle((58.0, 56.8), 14.0, 2.0, facecolor='#ECEFF1',
                           edgecolor=GRY, lw=1.1, zorder=5))
    num(65.0, 60.6, '(500)', GRY, 7.6)

    # ---------------------------------------------------------- under the desk
    ax.add_patch(Circle((34.0, 52.8), 1.6, facecolor=SB, edgecolor='black',
                        lw=1.0, zorder=4))
    ax.add_patch(Rectangle((37.4, 51.6), 3.4, 2.2, facecolor=SB,
                           edgecolor='black', lw=1.0, zorder=4))
    ax.add_patch(Rectangle((45.0, 51.4), 4.2, 2.4, facecolor=HWC,
                           edgecolor='black', lw=1.0, zorder=4))
    num(34.0, 49.4, '(400)', SB, 7.4)
    num(39.1, 49.4, '(401)', SB, 7.4)
    num(47.1, 49.4, '(410)', HWC, 7.4)

    box(ax, 20, 32, 15, 12.0, 'HOST\nMACHINE\nunder\nexamination', '#37474F', 7.6)
    box(ax, 38, 32, 14, 6.0, 'NODE\nCONTROLLER', GRY, 7.6)
    box(ax, 56, 42, 13, 6.0, 'GATING\nUNIT (920)', ENF, 7.6)

    ax.plot([66, 66], [56.8, 48.0], color=ENF, lw=1.8, solid_capstyle='round', zorder=2)
    ax.plot([56, 35], [45.0, 41.0], color=ENF, lw=1.8, solid_capstyle='round', zorder=2)
    arrow(ax, (52, 35.4), (56, 43.6), lw=1.3, color=ENF, ls=(0, (3, 2)))
    ax.text(53.4, 38.6, 'gate\ncommand', fontsize=6.9, color=ENF, ha='left',
            va='center', style='italic', linespacing=1.4)

    ax.plot([24, 52], [50.0, 50.0], color='#B0BEC5', lw=0.9, ls=(0, (2.5, 2.0)),
            zorder=1)
    for sx, sy in ((44.8, 66.0), (29.9, 72.8), (49.0, 56.8), (54.7, 56.8),
                   (34.0, 51.2), (47.1, 51.4)):
        ax.plot([sx, sx], [sy, 50.0], color='#B0BEC5', lw=0.8,
                ls=(0, (2.5, 2.0)), zorder=1)
    ax.plot([45, 45], [50.0, 38.0], color='#B0BEC5', lw=0.9,
            ls=(0, (2.5, 2.0)), zorder=1)

    # ---------------------------------------------------------- acoustic paths
    ax.annotate('', xy=(49.6, 60.4), xytext=(82.2, 66.4),
                arrowprops=dict(arrowstyle='-|>', color=AB, lw=1.5,
                                ls=(0, (3.5, 2.0)),
                                connectionstyle='arc3,rad=0.20'))
    ax.add_patch(Circle((72.8, 56.8), 0.9, facecolor=SB, edgecolor='none',
                        zorder=6))
    ax.annotate('', xy=(36.0, 55.4), xytext=(71.6, 55.4),
                arrowprops=dict(arrowstyle='-|>', color=SB, lw=2.4),
                zorder=6)
    ax.plot([34.0, 34.0], [54.0, 54.4], color=SB, lw=1.6, zorder=6)

    # ---------------------------------------------------------- neighbour
    ax.add_patch(Rectangle((104, 54), 26, 2.8, facecolor='#F5F5F5',
                           edgecolor=FAR, lw=1.1))
    ax.add_patch(Rectangle((106, 30), 3, 24, facecolor='#F5F5F5', edgecolor=FAR, lw=1.1))
    ax.add_patch(Circle((118, 66), 3.6, facecolor='#F5F5F5', edgecolor=FAR, lw=1.1))
    ax.add_patch(FancyBboxPatch((113.5, 55.5), 9, 9.5, boxstyle='round,pad=0.4',
                                facecolor='#F5F5F5', edgecolor=FAR, lw=1.1))
    ax.text(118, 72.0, 'NEIGHBOURING\nCANDIDATE', fontsize=7.4, color='#9E9E9E',
            ha='center', fontweight='bold', linespacing=1.4)
    ax.annotate('', xy=(50.6, 60.2), xytext=(114.4, 64.6),
                arrowprops=dict(arrowstyle='-|>', color=FAR, lw=1.3,
                                ls=(0, (3.5, 2.0)),
                                connectionstyle='arc3,rad=0.13'))
    ax.plot([81, 103], [55.4, 55.4], color=FAR, lw=1.2, ls=':')
    ax.add_patch(Circle((101, 48.6), 2.3, facecolor='white', edgecolor=ENF,
                        lw=1.6, zorder=6))
    ax.text(101, 48.6, 'X', ha='center', va='center', color=ENF, fontsize=9.5,
            fontweight='bold', zorder=7)
    ax.text(101, 44.0, 'no structural path\nacross the desk gap', fontsize=7.2,
            color=ENF, ha='center', fontweight='bold', linespacing=1.4)

    # ---------------------------------------------------------- key
    ax.plot([4, 130], [23.0, 23.0], color='#CFD8DC', lw=1.1)
    ax.text(4, 25.4,
            'An emission instant T1 is registered only where the contact channel (400) and the '
            'airborne channel (402) both exceed their thresholds inside the\ncoincidence window. '
            'A sound that reaches only (402) is not attributed to the seated candidate.',
            fontsize=7.8, color=GRY, va='center', linespacing=1.6)

    key = [
        ('(100)', 'desk / work surface'),
        ('(200)', 'display panel'),
        ('(210)', 'photometric onset sensor over the patch'),
        ('(300)', 'imaging sensor: gaze, scanpath, pupil'),
        ('(400/401)', 'contact piezo transducer, preamplifier'),
        ('(402)', 'airborne microphone in the housing'),
        ('(410)', 'six-axis desk inertial unit'),
        ('(500)', 'candidate keyboard'),
        ('(910)', 'desk indicator, this candidate only'),
        ('(920)', 'in-line gating unit, in the data pair'),
        ('(205)', 'onset patch, inverted at each item'),
        ('NC / HOST', 'node controller; examined machine'),
    ]
    cols = [5.0, 43.0, 82.0]
    for i, (n, d) in enumerate(key):
        c, r = divmod(i, 6)
        x = cols[c]
        y = 19.4 - r * 3.1
        ax.text(x, y, n, fontsize=7.3, fontweight='bold', color=GRY, va='center')
        ax.text(x + 9.2, y, d, fontsize=7.3, color='#37474F', va='center')

    paths = [(SB, '-', 2.2, 'structure-borne path through the desk, to (400)'),
             (AB, (0, (3.5, 2.0)), 1.5, 'airborne path from the seated candidate, to (402)'),
             (FAR, (0, (3.5, 2.0)), 1.3, "neighbour's airborne path: reaches (402), never (400)")]
    ax.text(82.0, 19.4 + 3.1, 'ACOUSTIC PATHS', fontsize=7.4, fontweight='bold',
            color=GRY, va='center')
    for i, (c, ls, lw, d) in enumerate(paths):
        y = 19.4 - i * 3.1
        ax.plot([82.0, 89.0], [y, y], color=c, lw=lw, ls=ls)
        ax.annotate('', xy=(90.4, y), xytext=(89.0, y),
                    arrowprops=dict(arrowstyle='-|>', color=c, lw=lw))
        ax.text(91.6, y, d, fontsize=7.3, color='#37474F', va='center')

    fig.savefig(os.path.join(OUT, 'fig03.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig03  station physical arrangement')


# ---------------------------------------------------------------- Figure 4
def fig04():
    """In-line gating unit: signal path, fail-safe bias and watchdog release."""
    fig, ax = plt.subplots(figsize=(13.0, 7.6))
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 86)
    ax.axis('off')

    ax.add_patch(FancyBboxPatch((28, 40), 64, 42, boxstyle='round,pad=0.5',
                                facecolor='#FFF5F5', edgecolor=ENF, lw=1.6))
    ax.text(60, 79.0, 'IN-LINE GATING UNIT (920)', fontsize=10.2,
            fontweight='bold', color=ENF, ha='center')
    ax.text(60, 76.2, 'disposed in series with the candidate keyboard',
            fontsize=8.0, color=GRY, ha='center', style='italic')

    box(ax, 2, 54, 22, 10.0, 'CANDIDATE\nKEYBOARD (500)', HWC, 8.4)
    box(ax, 100, 54, 26, 10.0, 'HOST MACHINE\nunder examination', '#37474F', 8.4)

    for y, lab, col in ((70.0, 'VBUS', '#EF6C00'), (44.0, 'GND', '#424242')):
        ax.plot([24, 100], [y, y], color=col, lw=1.6)
        ax.text(78 if y > 60 else 58, y + 1.2, lab + '  -  not interrupted',
                fontsize=7.4, color=col, ha='center', fontweight='bold')

    ax.add_patch(Rectangle((42, 54.4), 20, 10.2, facecolor='none',
                           edgecolor=GRY, lw=1.1, ls=(0, (3, 2))))
    ax.text(52, 66.0, 'analog switch / signal relay', fontsize=7.6, color=GRY,
            ha='center', fontweight='bold')
    for y, lab in ((61.5, 'D+'), (57.0, 'D-')):
        ax.plot([24, 46], [y, y], color=HWC, lw=1.8)
        ax.plot([58, 100], [y, y], color=HWC, lw=1.8)
        ax.text(26.5, y + 1.3, lab, fontsize=7.6, color=HWC, fontweight='bold')
        ax.plot([46, 56.6], [y, y + 2.6], color='black', lw=1.6)
        ax.add_patch(Circle((46, y), 0.55, facecolor='black', edgecolor='none', zorder=4))
        ax.add_patch(Circle((58, y), 0.55, facecolor='black', edgecolor='none', zorder=4))

    ax.plot([52, 52], [54.4, 51.0], color='black', lw=1.4)
    ax.plot([38, 70], [51.0, 51.0], color='black', lw=1.4)
    ax.text(50.4, 52.3, '/OE', fontsize=7.8, fontweight='bold', color='black',
            ha='right')
    ax.text(52, 47.6, 'shown in the OPEN (gated) state', fontsize=7.4,
            color=ENF, ha='center', style='italic')

    ax.plot([38, 38], [51.0, 49.4], color='black', lw=1.4)
    ax.add_patch(Rectangle((36.8, 46.2), 2.4, 3.2, facecolor='white',
                           edgecolor='black', lw=1.3, zorder=4))
    ax.plot([38, 38], [46.2, 44.0], color='black', lw=1.4)
    ax.text(35.4, 47.8, 'R', fontsize=8.0, fontweight='bold', ha='right', va='center')
    ax.text(30.0, 41.6, 'pull-down: biases the path to PASSING', fontsize=7.4,
            color='#2E7D32', fontweight='bold', ha='left')

    box(ax, 70, 46.6, 20, 8.8, 'RETRIGGERABLE\nWATCHDOG', '#8E0000', 7.8)
    ax.text(93.0, 51.0, 'releases the gate\nif the refresh stops', fontsize=7.4,
            color='#8E0000', va='center', fontweight='bold', linespacing=1.4)

    box(ax, 70, 26.0, 20, 8.8, 'NODE\nCONTROLLER', GRY, 7.8)
    ax.annotate('', xy=(80, 46.6), xytext=(80, 34.8),
                arrowprops=dict(arrowstyle='-|>', color=GRY, lw=1.5))
    ax.text(81.6, 40.6, 'assert + periodic refresh', fontsize=7.4, color=GRY,
            fontweight='bold', va='center')

    hdr = ['CONDITION', 'ENABLE INPUT', 'CANDIDATE DATA PATH']
    rows = [('controller unpowered, in reset or hung',
             'held low by R', 'CONTINUOUS  (passes)', '#2E7D32'),
            ('controller asserting and refreshing',
             'driven and retriggered', 'INTERRUPTED  (gated)', ENF),
            ('controller stops refreshing',
             'watchdog times out', 'CONTINUOUS  (passes)', '#2E7D32')]
    cx = [4.0, 54.0, 88.0]
    ax.add_patch(Rectangle((2, 17.6), 126, 3.6, facecolor=HWC, edgecolor='none'))
    for c, h in zip(cx, hdr):
        ax.text(c, 19.4, h, fontsize=7.8, fontweight='bold', color='white',
                va='center')
    for i, (a, b, c, col) in enumerate(rows):
        y = 15.0 - i * 3.6
        if i % 2 == 0:
            ax.add_patch(Rectangle((2, y - 1.8), 126, 3.6, facecolor='#E3F2FD',
                                   edgecolor='none'))
        ax.text(cx[0], y, a, fontsize=7.6, color='#212121', va='center')
        ax.text(cx[1], y, b, fontsize=7.6, color=GRY, va='center')
        ax.text(cx[2], y, c, fontsize=7.6, color=col, va='center', fontweight='bold')
    ax.plot([2, 128], [17.6, 17.6], color=GRY, lw=0.8)
    ax.plot([2, 128], [5.4, 5.4], color=GRY, lw=0.8)

    ax.text(65, 2.4,
            'Opening the candidate input path is the active, refreshed state. Both properties are '
            'circuit conditions and hold when no program is executing.',
            fontsize=7.8, color=GRY, ha='center', va='center', style='italic')

    fig.savefig(os.path.join(OUT, 'fig04.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig04  in-line gating unit')


# ---------------------------------------------------------------- Figure 3
def fig05():
    fig, ax = plt.subplots(figsize=(12.4, 6.2))
    ax.set_xlim(0, 124)
    ax.set_ylim(0, 62)
    ax.axis('off')

    ax.text(2, 58.5, 'GRADUATED ENFORCEMENT LADDER', fontsize=10,
            fontweight='bold', color=GRY)
    rungs = [('A0  observe', 'no output; the cycle is recorded to (950) only', '#90A4AE'),
             ('A1  advise', 'desk indicator / haptic (910) to the candidate alone', '#F9A825'),
             ('A2  notify', 'invigilator console entry with the cycle evidence', '#FB8C00'),
             ('A3  gate', 'in-line HID unit (920) physically opens the keyboard data lines', '#C62828'),
             ('A4  hold', 'session hold latch (930); human release required', '#7B1FA2')]
    for i, (t, d, c) in enumerate(rungs):
        y = 49 - i * 8.4
        box(ax, 2, y, 17, 6.4, t, c, 8.4)
        ax.text(21.4, y + 3.2, d, fontsize=7.9, color=GRY, va='center')
        if i:
            arrow(ax, (10.5, y + 6.4 + 2.0), (10.5, y + 6.4 + 0.2), lw=1.3)

    ax.plot([73, 73], [3, 56], color='#CFD8DC', lw=1.1)

    ax.text(76, 58.5, 'THE ADVANCE CONDITION', fontsize=10, fontweight='bold',
            color=GRY)
    box(ax, 76, 46, 45, 8.4,
        'persistence counter (810): the same rung must be\n'
        'earned on n consecutive control cycles', ENF, 8.0)
    box(ax, 76, 35.5, 45, 8.4,
        'per-candidate cooldown (820) and global session\n'
        'interval (830): neither may be bypassed', ENF, 8.0)
    box(ax, 76, 25, 45, 8.4,
        'escalation comparator (840): a sustained rise may\n'
        'shorten, but never eliminate, the interval', ENF, 8.0)
    box(ax, 76, 11.5, 45, 11.4,
        'DUAL-CHANNEL INTERLOCK (850)\n\n'
        'A0-A2 may be reached on one modality.\n'
        'A3 and A4 require two physically independent\n'
        'modalities to have exceeded threshold in the\n'
        'same cycle. No single modality may ever open\n'
        'the candidate input path.', '#8E0000', 8.0)
    for y in (46, 35.5, 25):
        arrow(ax, (98.5, y), (98.5, y - 2.1), lw=1.3)

    ax.text(98.5, 6.0,
            'Measured effect of (850) on the recorded corpus:\n'
            'false gate 30.58/h to 9.31/h (-69.6%), unassisted gate rate '
            '29.7% to 10.8%,\nat a cost of 25% of true gates (44.4% to 33.3%).',
            ha='center', va='center', fontsize=7.8, color=GRY, linespacing=1.5,
            bbox=dict(boxstyle='round,pad=0.45', fc='#FFEBEE', ec=ENF, lw=0.9))

    ax.annotate('', xy=(76, 52.2), xytext=(63, 52.2),
                arrowprops=dict(arrowstyle='-|>', color=GRY, lw=1.5))
    ax.text(69.5, 54.6, 'every advance\nmust satisfy', ha='center', fontsize=7.9,
            color=GRY, fontweight='bold', linespacing=1.4)
    ax.add_patch(Rectangle((0.4, 14.2), 19.2, 16.8, facecolor='none',
                           edgecolor='#8E0000', lw=1.4, ls=(0, (3.5, 2.2)),
                           zorder=5))
    ax.annotate('', xy=(76, 17.2), xytext=(19.6, 22.6),
                arrowprops=dict(arrowstyle='-|>', color='#8E0000', lw=1.4,
                                ls=(0, (3.5, 2.2)),
                                connectionstyle='arc3,rad=-0.16'))

    fig.savefig(os.path.join(OUT, 'fig05.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig05  enforcement ladder')


# ---------------------------------------------------------------- Figure 4
def fig06():
    m = json.load(open(os.path.join(SCRATCH, 'model_results.json')))
    order = [('C3 head motion (410)', 0.084), ('C2 causal loop (600)', 0.062),
             ('C1 gaze departure (310)', 0.071), ('C5 scanpath (320)', 0.083),
             ('C2b source geometry (620)', 0.066), ('C4 pupillometry (330)', 0.048)]
    labs = [k.replace(' (', '\n(') for k, _ in order]
    auc = [m['ALL CANDIDATES | ' + k]['auc'] for k, _ in order]
    loco = [d for _, d in order]
    fused = m['ALL CANDIDATES | absolute only']['auc']

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 4.6),
                                 gridspec_kw={'width_ratios': [1.55, 1]})
    x = np.arange(len(order))
    b = a1.bar(x, auc, color=[VAL if v >= 0.70 else PRC if v >= 0.64 else '#B0BEC5'
                              for v in auc], edgecolor='black', linewidth=0.7)
    a1.axhline(fused, color=ENF, ls='--', lw=1.4)
    a1.text(len(order) - 0.45, fused + 0.006,
            'fused, all channels  %.3f' % fused, ha='right', fontsize=8.2,
            color=ENF, fontweight='bold')
    a1.axhline(0.5, color='black', lw=0.9)
    a1.text(-0.45, 0.505, 'chance', fontsize=7.6, color='black')
    for r, v in zip(b, auc):
        a1.text(r.get_x() + r.get_width() / 2, v + 0.006, '%.3f' % v,
                ha='center', fontsize=8.2, fontweight='bold')
    a1.set_xticks(x)
    a1.set_xticklabels(labs, fontsize=7.0)
    a1.set_ylim(0.48, 0.82)
    a1.set_ylabel('window AUC', fontsize=9)
    a1.set_title('(a) Corroborating channels, taken singly',
                 fontsize=9.6, fontweight='bold')
    a1.grid(axis='y', alpha=0.25, lw=0.6)
    a1.set_axisbelow(True)

    a2.barh(x, loco, color=ENF, edgecolor='black', linewidth=0.7)
    for i, v in enumerate(loco):
        a2.text(v + 0.0015, i, '-%.3f' % v, va='center', fontsize=8.2,
                fontweight='bold', color=ENF)
    a2.set_yticks(x)
    a2.set_yticklabels(labs, fontsize=7.7)
    a2.invert_yaxis()
    a2.set_xlim(0, 0.105)
    a2.set_xlabel('AUC lost when the channel is removed', fontsize=8.6)
    a2.set_title('(b) Leave-one-channel-out', fontsize=9.6, fontweight='bold')
    a2.grid(axis='x', alpha=0.25, lw=0.6)
    a2.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig06.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('fig06  ocular channels')


# ---------------------------------------------------------------- Figure 5
def fig07():
    k = json.load(open(os.path.join(SCRATCH, 'ks_results.json')))
    ks = [1, 2, 3, 5]
    eer = [k['persist_k%d' % i]['eer_mean'] * 100 for i in ks]
    sd = [k['persist_k%d' % i]['eer_sd'] * 100 for i in ks]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.0, 4.4),
                                 gridspec_kw={'width_ratios': [1, 1.12]})
    det = [('Manhattan\nscaled', k['manhattan_scaled']), ('Mahalanobis', k['mahalanobis']),
           ('Euclidean', k['euclidean'])]
    x = np.arange(3)
    w = 0.36
    a1.bar(x - w / 2, [d[1]['eer_mean'] * 100 for d in det], w, label='EER (%)',
           color=ENF, edgecolor='black', lw=0.7)
    a1.bar(x + w / 2, [d[1]['auc_mean'] * 100 for d in det], w, label='AUC (x100)',
           color=VAL, edgecolor='black', lw=0.7)
    for i, d in enumerate(det):
        a1.text(i - w / 2, d[1]['eer_mean'] * 100 + 1.6, '%.2f' % (d[1]['eer_mean'] * 100),
                ha='center', fontsize=8.1, fontweight='bold')
        a1.text(i + w / 2, d[1]['auc_mean'] * 100 + 1.6, '%.3f' % d[1]['auc_mean'],
                ha='center', fontsize=8.1, fontweight='bold')
    a1.set_xticks(x)
    a1.set_xticklabels([d[0] for d in det], fontsize=8.4)
    a1.set_ylim(0, 132)
    a1.legend(fontsize=8, frameon=False, loc='upper left', ncol=2)
    a1.set_title('(a) Discontinuity detector against the enrolled\nprofile (510), 51 subjects',
                 fontsize=9.4, fontweight='bold')
    a1.grid(axis='y', alpha=0.25, lw=0.6)
    a1.set_axisbelow(True)

    a2.errorbar(ks, eer, yerr=sd, marker='o', ms=7, lw=1.9, color=ENF,
                capsize=4, mfc='white', mew=1.8)
    for kk, v in zip(ks, eer):
        a2.annotate('%.2f%%' % v, (kk, v), textcoords='offset points',
                    xytext=(9, 9), fontsize=8.4, fontweight='bold', color=ENF)
    a2.set_xticks(ks)
    a2.set_xlabel('n, consecutive commit events required (810)', fontsize=8.8)
    a2.set_ylabel('equal-error rate (%)', fontsize=8.8)
    a2.set_ylim(0, 19)
    a2.set_xlim(0.55, 5.75)
    a2.set_title('(b) Why the persistence counter is a measurement,\nnot a heuristic',
                 fontsize=9.4, fontweight='bold')
    a2.grid(alpha=0.25, lw=0.6)
    a2.set_axisbelow(True)
    a2.text(2.55, 15.6, 'error bars are the across-subject SD;\n'
                        'the fall from n=1 to n=3 is 4.2 points',
            fontsize=7.6, color=GRY, linespacing=1.4)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig07.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('fig07  input-dynamics discontinuity')


# ---------------------------------------------------------------- Figure 6
def fig08():
    s = json.load(open(os.path.join(SCRATCH, 'scheduler_results.json')))
    on, off = s['default'], s['interlock_interlock']

    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(13.0, 4.3),
                                     gridspec_kw={'width_ratios': [1.05, 1.05, 1]})

    lab = ['false gate\nper hour', 'unassisted\ngate rate (%)', 'assisted\ngate rate (%)']
    voff = [off['false_gate_per_hour'], off['gate_rate_unassisted'] * 100,
            off['gate_rate_assisted'] * 100]
    von = [on['false_gate_per_hour'], on['gate_rate_unassisted'] * 100,
           on['gate_rate_assisted'] * 100]
    x = np.arange(3)
    w = 0.36
    a1.bar(x - w / 2, voff, w, label='any single modality may gate', color='#B0BEC5',
           edgecolor='black', lw=0.7)
    a1.bar(x + w / 2, von, w, label='dual-channel interlock (850) armed', color=ENF,
           edgecolor='black', lw=0.7)
    for i in range(3):
        a1.text(i - w / 2, voff[i] + 0.7, '%.1f' % voff[i], ha='center', fontsize=8.1,
                fontweight='bold')
        a1.text(i + w / 2, von[i] + 0.7, '%.1f' % von[i], ha='center', fontsize=8.1,
                fontweight='bold', color=ENF)
    a1.set_xticks(x)
    a1.set_xticklabels(lab, fontsize=8.0)
    a1.set_ylim(0, 56)
    a1.legend(fontsize=7.6, frameon=False, loc='upper left')
    a1.set_title('(a) Effect of the dual-channel interlock', fontsize=9.4, fontweight='bold')
    a1.grid(axis='y', alpha=0.25, lw=0.6)
    a1.set_axisbelow(True)

    ns = [1, 2, 3, 4]
    fa = [s['n_persist_%d' % n]['false_advise_per_hour'] for n in ns]
    ta = [s['n_persist_%d' % n]['advise_rate_assisted'] * 100 for n in ns]
    a2.plot(ns, fa, marker='o', ms=6.5, lw=1.9, color=ENF, mfc='white', mew=1.7,
            label='false advise / hour')
    a2.plot(ns, ta, marker='s', ms=6.5, lw=1.9, color=VAL, mfc='white', mew=1.7,
            label='true advise rate (%)')
    for n, v in zip(ns, fa):
        a2.annotate('%.1f' % v, (n, v), textcoords='offset points', xytext=(0, 9),
                    ha='center', fontsize=8.0, color=ENF, fontweight='bold')
    for n, v in zip(ns, ta):
        a2.annotate('%.1f' % v, (n, v), textcoords='offset points', xytext=(0, -14),
                    ha='center', fontsize=8.0, color=VAL, fontweight='bold')
    a2.set_xticks(ns)
    a2.set_xlabel('n, persistence counter (810)', fontsize=8.8)
    a2.set_ylim(0, 66)
    a2.legend(fontsize=7.8, frameon=False)
    a2.set_title('(b) Persistence trades sensitivity for quiet', fontsize=9.4,
                 fontweight='bold')
    a2.grid(alpha=0.25, lw=0.6)
    a2.set_axisbelow(True)

    vals = [on['ceiling_global_only'], on['raw_eligible_total'], on['actuations_total']]
    names = ['global interval (830)\nalone would permit',
             'cycles the corroboration\nvalue found eligible',
             'actuations the full\nscheduler emitted']
    bb = a3.bar(range(3), vals, color=['#CFD8DC', PRC, ENF], edgecolor='black', lw=0.7)
    for r, v in zip(bb, vals):
        a3.text(r.get_x() + r.get_width() / 2, v + 22, '%d' % v, ha='center',
                fontsize=9.0, fontweight='bold')
    a3.set_xticks(range(3))
    a3.set_xticklabels(names, fontsize=6.9)
    a3.set_ylim(0, 1480)
    a3.set_ylabel('control cycles', fontsize=8.8)
    a3.set_title('(c) Actuation discipline: %.1f%% reduction' % on['reduction_pct'],
                 fontsize=9.4, fontweight='bold')
    a3.grid(axis='y', alpha=0.25, lw=0.6)
    a3.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig08.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('fig08  enforcement discipline')


# ---------------------------------------------------------------- Figure 9
def fig09():
    """Sense-to-gate latency: per-element magnitudes and the total against bound."""
    L = json.load(open(os.path.join(HW, 'latency_results.json')))
    rows = [
        ('node frame to host  (REPORT_HZ = 50)', 20.0, 'derived'),
        ('display panel response  (one refresh at 120 Hz)', 8.3, 'derived'),
        ('channel extraction over a 20 s window', L['T1_channel_extraction_ms']['median'], 'measured'),
        ('USB full-speed frame', 1.0, 'derived'),
        ('corroboration value (700)', L['T2_corroboration_value_ms']['median'], 'measured'),
        ('photodiode edge to controller', 0.005, 'derived'),
        ('gate command to switch', 0.001, 'derived'),
        ('scheduler decision (800 / 850)', L['T3_scheduler_decision_ms']['median'], 'measured'),
    ]
    meas = sum(v for _, v, k in rows if k == 'measured')
    der = sum(v for _, v, k in rows if k == 'derived')
    total = meas + der

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.0, 4.6),
                                 gridspec_kw={'width_ratios': [1.42, 1.0]})

    ypos = np.arange(len(rows))[::-1]
    for (lab, v, kind), y in zip(rows, ypos):
        c = HWC if kind == 'measured' else '#E57373'
        a1.barh(y, v, height=0.62, color=c, edgecolor='black', lw=0.7,
                hatch=None if kind == 'measured' else '//')
        a1.text(v * 1.32, y, '%.4g ms' % v, va='center', fontsize=7.6,
                fontweight='bold', color=c)
    a1.set_yticks(ypos)
    a1.set_yticklabels([r[0] for r in rows], fontsize=7.4)
    a1.set_xscale('log')
    a1.set_xlim(1e-4, 900)
    a1.set_xlabel('milliseconds (logarithmic)', fontsize=8.4)
    a1.set_title('(a) elements of the sense-to-gate path', fontsize=9.0,
                 fontweight='bold')
    a1.grid(axis='x', alpha=0.25, lw=0.6)
    a1.set_axisbelow(True)
    for s in ('top', 'right'):
        a1.spines[s].set_visible(False)
    a1.legend(handles=[
        plt.Rectangle((0, 0), 1, 1, fc=HWC, ec='black', lw=0.7),
        plt.Rectangle((0, 0), 1, 1, fc='#E57373', ec='black', lw=0.7, hatch='//')],
        labels=['measured on this machine', 'derived from datasheets'],
        loc='lower right', fontsize=7.4, framealpha=0.95)

    a2.barh(0, meas, height=0.40, color=HWC, edgecolor='black', lw=0.8)
    a2.barh(0, der, left=meas, height=0.40, color='#E57373', edgecolor='black',
            lw=0.8, hatch='//')
    a2.barh(0, 200 - total, left=total, height=0.40, color='#ECEFF1',
            edgecolor='#B0BEC5', lw=0.8)
    a2.plot([200, 200], [-0.40, 0.40], color='black', lw=2.4)
    a2.text(198, 0.48, 'responsiveness bound  200 ms', ha='right', fontsize=8.2,
            fontweight='bold')
    a2.annotate('projected sense-to-gate\n%.1f ms' % total,
                xy=(total, 0.20), xytext=(46, 1.02),
                arrowprops=dict(arrowstyle='-|>', color='black', lw=1.1),
                fontsize=8.4, fontweight='bold', color='black', linespacing=1.4)
    a2.text((total + 200) / 2, 0.0, 'margin  %.0f ms' % (200 - total),
            ha='center', va='center', fontsize=8.2, color=GRY, fontweight='bold')
    a2.annotate('measured software path %.3f ms\n= %.2f %% of the 2,500 ms control-cycle budget'
                % (meas, 100 * meas / 2500.0),
                xy=(meas / 2, -0.20), xytext=(14, -0.92),
                arrowprops=dict(arrowstyle='-|>', color=HWC, lw=1.1),
                fontsize=7.8, color=HWC, fontweight='bold', linespacing=1.5)
    a2.set_xlim(-4, 224)
    a2.set_ylim(-1.5, 1.5)
    a2.set_yticks([])
    a2.set_xlabel('milliseconds from question onset to actuation', fontsize=8.4)
    a2.set_title('(b) the same total against the responsiveness bound',
                 fontsize=9.0, fontweight='bold')
    for s in ('top', 'right', 'left'):
        a2.spines[s].set_visible(False)
    a2.grid(axis='x', alpha=0.25, lw=0.6)
    a2.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig09.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('fig09  latency budget')


# ---------------------------------------------------------------- Figure 10
def fig10():
    """Claim structure: five independents and what depends on each."""
    fig, ax = plt.subplots(figsize=(13.0, 4.4))
    ax.set_xlim(0, 130)
    ax.set_ylim(-2.0, 44)
    ax.axis('off')

    groups = [
        (2.0, 34.0, 'A', '#0D47A1', 'Claim 1',
         'system: causal latency interlock', [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 4),
        (38.0, 26.0, 'B', '#8E0000', 'Claim 13',
         'system: graduated enforcement', [14, 15, 16, 17, 18], 3),
        (66.0, 34.0, 'C', '#1B5E20', 'Claim 19   |   Claim 20',
         'methods: interlock   |   enforcement', [21, 22, 23], 3),
        (102.0, 26.0, 'D', '#4527A0', 'no independent claim',
         'refer back to Claim 1 / Claim 13', [24, 25], 2),
    ]
    for gi, (x0, w, tag, col, title, sub, deps, per) in enumerate(groups):
        rows = (len(deps) + per - 1) // per
        bot = 15.2 - (rows - 1) * 5.6 - 2.0
        h = 34.6 - bot
        ax.add_patch(FancyBboxPatch((x0, bot), w, h,
                                    boxstyle='round,pad=0.4', facecolor='#FAFAFA',
                                    edgecolor='#CFD8DC', lw=1.1))
        ax.text(x0 + 1.6, 37.0, 'GROUP ' + tag, fontsize=8.2, fontweight='bold',
                color=col)
        if tag == 'D':
            ax.add_patch(FancyBboxPatch((x0 + 1.6, 26.8), w - 3.2, 6.6,
                                        boxstyle='round,pad=0.2', facecolor='white',
                                        edgecolor=col, lw=1.2, linestyle=(0, (3, 2))))
            ax.text(x0 + w / 2, 30.1, title, ha='center', va='center',
                    fontsize=8.0, fontweight='bold', color=col, style='italic')
        else:
            box(ax, x0 + 1.6, 26.8, w - 3.2, 6.6, title, col, 8.4)
        ax.text(x0 + w / 2, 24.6, sub, fontsize=7.4, color=GRY, ha='center',
                style='italic')
        ax.text(x0 + w / 2, 21.6,
                'claims' if tag == 'D' else 'dependent claims',
                fontsize=7.2, color='#90A4AE', ha='center')
        for i, d in enumerate(deps):
            r, c = divmod(i, per)
            cw = (w - 3.2 - (per - 1) * 1.2) / per
            cx = x0 + 1.6 + c * (cw + 1.2)
            cy = 15.2 - r * 5.6
            ax.add_patch(FancyBboxPatch((cx, cy), cw, 4.2,
                                        boxstyle='round,pad=0.16',
                                        facecolor='white', edgecolor=col, lw=1.1))
            ax.text(cx + cw / 2, cy + 2.1, str(d), ha='center', va='center',
                    fontsize=8.6, fontweight='bold', color=col)

    ax.text(65.0, -0.8,
            'Independent claims are shaded: Claims 1, 13, 19 and 20, each terminating in '
            'interruption of a physical data path. Claim 24 refers to Claim 13; Claim 25 to '
            'Claim 1 or Claim 13. No claim is directed to a computer-readable medium.',
            fontsize=7.6, color=GRY, ha='center', va='center')

    fig.savefig(os.path.join(OUT, 'fig10.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10  claim structure')




if __name__ == "__main__":
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07,
              fig08, fig09, fig10):
        f()
    print("done ->", OUT)
