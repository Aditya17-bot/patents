"""Figures for the IDF-B on stage-offset estimation at river gauging stations.

Style follows diagram-tools.md and SKILL (2).md (the drawing helpers are imported from
the patent 3 generator unchanged): zones with coloured header strips, white
sub-component boxes with italic reference numerals, a dashed boundary between the field
hardware and the processing system, labelled signal arrows, a flowchart with decision
diamonds and YES/NO branches, data figures as 2 x 2 panels labelled (a)-(d). ASCII labels.

Data figures read results/*.json; nothing measured is typed in.

    python src/make_figs.py            all figures
    python src/make_figs.py 3 4        only those
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, r"C:\adi\patents\05_length_invariance\src")
import make_figs as P3                                            # noqa: E402

RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "patent", "figures")
zone, sub, arr, poly, pbox, diamond, panel, tidy, depbox = (
    P3.zone, P3.sub, P3.arr, P3.poly, P3.pbox, P3.diamond, P3.panel, P3.tidy, P3.depbox)
Z_IN, Z_CORE, Z_RED, Z_PHY, Z_PROC, Z_OUT, DARK = (
    P3.Z_IN, P3.Z_CORE, P3.Z_RED, P3.Z_PHY, P3.Z_PROC, P3.Z_OUT, P3.DARK)
YES_C, NO_C = P3.YES_C, P3.NO_C
C = P3.C
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def load(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return json.load(fh)


def save(fig, name, dpi, note):
    fig.savefig(os.path.join(OUT, name), dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("%s  %s" % (name, note))


# ---------------------------------------------------------------- Figure 1
def fig01():
    """System architecture: two gauging stations on one river, telemetry, processing."""
    fig, ax = plt.subplots(figsize=(22, 13))
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 13)
    ax.axis("off")
    # river strip
    ax.add_patch(Rectangle((0.3, 0.35), 21.4, 0.55, facecolor="#D6EAF8", edgecolor="#5DADE2",
                           lw=1.2, zorder=1))
    ax.text(11, 0.62, "RIVER  ->  flow direction  (no significant tributary, abstraction or storage "
            "between stations 120 and 100)", ha="center", va="center", fontsize=9.5,
            color="#1B4F72", fontweight="bold", zorder=2)
    # field hardware
    zone(ax, 0.4, 1.3, 6.6, 5.2, Z_PHY, "120", "NEIGHBOURING GAUGING STATION")
    sub(ax, 0.8, 4.0, 2.8, 1.6, Z_PHY[0], 121, "Stage sensor", "pressure / radar", "")
    sub(ax, 3.9, 4.0, 2.8, 1.6, Z_PHY[0], 125, "Data logger", "+ rating", "")
    sub(ax, 0.8, 1.7, 5.9, 1.7, Z_PHY[0], 128, "Channel control", "riffle / weir / section",
        "sets the stage-discharge relation")
    zone(ax, 7.6, 1.3, 6.8, 5.2, Z_PHY, "100", "TARGET GAUGING STATION")
    sub(ax, 8.0, 4.0, 2.9, 1.6, Z_PHY[0], 110, "Stage sensor", "pressure / bubbler /", "radar")
    sub(ax, 11.2, 4.0, 2.9, 1.6, Z_PHY[0], 115, "Data logger", "applies R(h + s)", "")
    sub(ax, 8.0, 1.7, 6.1, 1.7, Z_PHY[0], 118, "Channel control", "scour, fill, weed, debris",
        "move the rating: offset s")
    zone(ax, 15.0, 1.3, 6.6, 5.2, Z_PHY, "600", "FIELD MEASUREMENT")
    sub(ax, 15.4, 4.0, 5.8, 1.6, Z_PHY[0], 610, "Discharge measurement", "ADCP / current meter",
        "+ reference gage reading")
    sub(ax, 15.4, 1.7, 5.8, 1.7, Z_PHY[0], 620, "Field-visit record", "Q_meas, GH_meas, control",
        "measured offset s_meas")
    # telemetry
    ax.plot([0.3, 21.7], [6.95, 6.95], ls=":", color="#888", lw=1.0, zorder=1)
    ax.text(0.45, 12.75, "FIELD HARDWARE (below)  /  DATA-PROCESSING SYSTEM 900 (above)",
            fontsize=8.5, color="#555", ha="left")
    # processing
    zone(ax, 0.4, 7.4, 6.6, 5.2, Z_IN, "200", "RECORD ARCHIVE")
    sub(ax, 0.8, 10.3, 5.8, 1.4, Z_IN[0], 210, "Stage and discharge series", "h(t), Q_Y(t)", "")
    sub(ax, 0.8, 8.6, 2.8, 1.4, Z_IN[0], 220, "Base rating R", "", "")
    sub(ax, 3.8, 8.6, 2.8, 1.4, Z_IN[0], 230, "Visit offsets", "s_meas", "")
    zone(ax, 7.6, 7.4, 6.8, 5.2, Z_CORE, "300", "OFFSET ESTIMATION")
    sub(ax, 8.0, 10.6, 3.0, 1.2, Z_CORE[0], 310, "Pair admission", "lag, coupling", "")
    sub(ax, 11.2, 10.6, 2.9, 1.2, Z_CORE[0], 320, "Discrepancy", "y = lnQ_Y - lnR(h)", "")
    sub(ax, 8.0, 9.1, 3.0, 1.2, Z_CORE[0], 330, "Log-slope", "x = dlnR/dh", "")
    sub(ax, 11.2, 9.1, 2.9, 1.2, Z_CORE[0], 340, "Stage-unit fit", "D = sum(xy)/sum(x^2)", "")
    sub(ax, 8.0, 7.65, 6.1, 1.15, Z_CORE[0], 350, "Offset estimator",
        "visit anchors + gain x departure of D", "")
    zone(ax, 15.0, 7.4, 6.6, 5.2, Z_RED, "400", "CORRECTION AND ACTION")
    sub(ax, 15.4, 10.3, 5.8, 1.4, Z_RED[0], 410, "Corrected discharge record", "Q = R(h + s_hat)", "")
    sub(ax, 15.4, 8.6, 2.8, 1.4, Z_RED[0], 420, "Offset command", "to logger 115", "")
    sub(ax, 18.4, 8.6, 2.8, 1.4, Z_RED[0], 430, "Visit request", "re-measure", "")
    # arrows hardware -> archive
    poly(ax, [(5.3, 5.6), (5.3, 6.45), (0.6, 6.45), (0.6, 11.0), (0.8, 11.0)], color=Z_PHY[0],
         label="Q_Y(t) via 130", lpos=(3.0, 6.45))
    poly(ax, [(12.6, 5.6), (12.6, 6.72), (6.85, 6.72), (6.85, 11.0), (6.6, 11.0)],
         color=Z_PHY[0], label="h(t) via 130", lpos=(9.6, 6.72))
    poly(ax, [(21.2, 2.55), (21.85, 2.55), (21.85, 7.18), (5.2, 7.18), (5.2, 8.55)],
         color="#7D6608", label="s_meas at each visit", lpos=(12.0, 7.18))
    arr(ax, (7.0, 10.9), (8.0, 11.2), color=Z_IN[0])
    arr(ax, (7.0, 9.3), (8.0, 9.6), color=Z_IN[0])
    arr(ax, (14.1, 9.6), (15.4, 10.9), color=Z_CORE[0], label="s_hat", lpos=(14.75, 10.55))
    poly(ax, [(16.8, 8.6), (16.8, 6.3), (13.4, 6.3), (13.4, 5.62)], color=Z_RED[0], ls="--",
         label="offset s_hat via 130", lpos=(15.1, 6.3))
    arr(ax, (19.8, 8.6), (19.8, 5.65), color=Z_RED[0], ls="--", label="field visit",
        lpos=(19.8, 6.3))
    save(fig, "fig01.png", 200, "architecture")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    import figs_arch
    import figs_data
    import figs_claims
    import figs_india
    funcs = {"1": figs_arch.fig01, "2": figs_arch.fig02, "3": figs_data.fig03, "4": figs_data.fig04,
             "5": figs_data.fig_example, "6": figs_india.fig06, "7": figs_claims.fig07}
    for w in sys.argv[1:] or sorted(funcs):
        funcs[str(int(w))]()
