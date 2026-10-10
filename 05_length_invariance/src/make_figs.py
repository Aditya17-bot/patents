"""Figures for the IDF-B disclosure on length-invariance recalibration.

Style follows the drafting guidance in this folder (diagram-tools.md, SKILL (2).md):
architecture drawn as zones with coloured header strips and white sub-component boxes
carrying italic reference numerals, a dashed boundary between the roadside hardware and
the data-processing system, labelled signal arrows, a flowchart with stage bands,
decision diamonds and YES/NO branches, and data figures as 2 x 2 panels labelled (a)-(d).
ASCII labels only. Architecture at dpi=200, data at dpi=300, white background.

Data figures read results/*.json and the cached series; nothing measured is typed in.
The length distributions of Figure 1 are a labelled schematic.

    python src/make_figs.py            all figures
    python src/make_figs.py 2 5        only those
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "patent", "figures")

# zone palette (SKILL (2).md)
Z_IN = ("#2980B9", "#EBF4FB")      # input / archive
Z_CORE = ("#7D3C98", "#F4ECFB")    # core solution
Z_RED = ("#C0392B", "#FDEDEC")     # correction
Z_PHY = ("#D68910", "#FEF9E7")     # sensor / physical
Z_PROC = ("#1E8449", "#EAFAF1")    # admission / processing
Z_OUT = ("#717D7E", "#F2F3F4")     # output
DARK = "#2C3E50"
YES_C, NO_C = "#1E8449", "#CB4335"
# data palette
C = ["#2196F3", "#E91E63", "#4CAF50", "#FF9800", "#9C27B0", "#00BCD4"]
ROAD_C = {"M25": C[0], "M1": C[1]}
RAW_C = "#90A4AE"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def load(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return json.load(fh)


def save(fig, name, dpi, note):
    fig.savefig(os.path.join(OUT, name), dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("%s  %s" % (name, note))


# ------------------------------------------------------------------ drawing helpers
def zone(ax, x, y, w, h, colors, num, title):
    bd, bg = colors
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06", facecolor=bg,
                                edgecolor=bd, linewidth=2.5, zorder=2))
    ax.add_patch(FancyBboxPatch((x, y + h - 0.55), w, 0.55, boxstyle="round,pad=0.02",
                                facecolor=bd, edgecolor=bd, linewidth=0, zorder=3))
    ax.text(x + 0.18, y + h - 0.28, "%s  %s" % (num, title), fontsize=10.5,
            fontweight="bold", color="white", va="center", ha="left", zorder=4)


def sub(ax, x, y, w, h, bd, ref, title, line1="", line2=""):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04", facecolor="white",
                                edgecolor=bd, linewidth=1.5, zorder=5))
    ax.text(x + 0.12, y + h - 0.1, str(ref), fontsize=8, color="#777", va="top",
            ha="left", zorder=6, fontstyle="italic")
    n = bool(line1) + bool(line2)
    ty = y + h / 2 + (0.14 * n)
    ax.text(x + w / 2, ty, title, fontsize=9.5, fontweight="bold", color="#1A1A1A",
            va="center", ha="center", zorder=6)
    if line1:
        ax.text(x + w / 2, ty - 0.3, line1, fontsize=8, color="#555", va="center",
                ha="center", zorder=6, fontstyle="italic")
    if line2:
        ax.text(x + w / 2, ty - 0.56, line2, fontsize=8, color="#555", va="center",
                ha="center", zorder=6)


def arr(ax, p, q, color="#333", lw=1.8, ls="-", rad=0.0, label=None, lpos=None,
        lcolor=None, z=7, shrink_a=0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=15, linewidth=lw,
                                 color=color, linestyle=ls, joinstyle="miter",
                                 capstyle="butt",
                                 connectionstyle="arc3,rad=%.2f" % rad, shrinkA=shrink_a,
                                 shrinkB=1.5, zorder=z))
    if label:
        mx, my = lpos if lpos else ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.2)
        ax.text(mx, my, label, fontsize=7.8, color=lcolor or color, ha="center",
                va="center", fontweight="bold", zorder=8,
                bbox=dict(fc="white", ec="none", pad=1.2))


def poly(ax, pts, color="#333", lw=1.8, ls="-", label=None, lpos=None, lcolor=None):
    xs = [q[0] for q in pts[:-1]]
    ys = [q[1] for q in pts[:-1]]
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=7, solid_joinstyle="miter",
            solid_capstyle="butt", dash_joinstyle="miter")
    arr(ax, pts[-2], pts[-1], color=color, lw=lw, ls=ls)
    if label:
        ax.text(lpos[0], lpos[1], label, fontsize=7.8, color=lcolor or color, ha="center",
                va="center", fontweight="bold", zorder=8,
                bbox=dict(fc="white", ec="none", pad=1.2))


def pbox(ax, x, y, w, h, text, colors, fs=9.2, bold=False):
    bd, bg = colors
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.08",
                                facecolor=bg, edgecolor=bd, linewidth=1.6, zorder=5))
    ax.text(x, y, text, fontsize=fs, ha="center", va="center", zorder=6,
            fontweight="bold" if bold else "normal", color="#1A1A1A", linespacing=1.3)


def diamond(ax, x, y, w, h, text, colors, fs=8.8):
    bd, bg = colors
    ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                         closed=True, facecolor=bg, edgecolor=bd, linewidth=1.8, zorder=5))
    ax.text(x, y, text, fontsize=fs, ha="center", va="center", zorder=6,
            color="#1A1A1A", linespacing=1.25)


def panel(ax, letter):
    ax.text(-0.08, 1.06, "(%s)" % letter, transform=ax.transAxes, fontsize=13,
            fontweight="bold", va="bottom", ha="left")


def tidy(ax):
    ax.grid(True, alpha=0.15, linestyle="--")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ---------------------------------------------------------------- Figure 1
def fig01():
    """Roadside hardware and the principle: same vehicles, same length shares."""
    fig = plt.figure(figsize=(16, 10.5))
    ax = fig.add_axes([0.02, 0.44, 0.96, 0.55])
    ax.set_xlim(0, 32)
    ax.set_ylim(0, 13)
    ax.axis("off")
    # carriageway, three lanes
    ax.add_patch(Rectangle((0.5, 5.0), 31, 4.5, fc="#ECEFF1", ec="#455A64", lw=1.2))
    for yl in (6.5, 8.0):
        ax.plot([0.5, 31.5], [yl, yl], color="white", lw=2, ls=(0, (6, 5)))
    ax.text(0.7, 9.8, "mainline carriageway (3 lanes), direction of travel ->",
            fontsize=10, color="#455A64")
    # on-slip joining between d3 and d4
    ax.add_patch(Polygon([(13.2, 1.2), (14.6, 1.2), (17.6, 5.0), (15.9, 5.0)], closed=True,
                         fc="#CFD8DC", ec="#455A64", lw=1.0))
    ax.text(12.3, 0.5, "on-slip road (120): vehicles join here", fontsize=9.5,
            color="#455A64")
    xs = [3.0, 7.5, 12.0, 20.0, 24.5, 29.0]
    for i, x in enumerate(xs):
        bad = (i == 4)
        col = "#C0392B" if bad else "#D68910"
        for yl in (5.75, 7.25, 8.75):                 # a loop pair in every lane
            ax.add_patch(Rectangle((x - 0.75, yl - 0.35), 0.6, 0.7, fc="none", ec=col, lw=1.6))
            ax.add_patch(Rectangle((x + 0.15, yl - 0.35), 0.6, 0.7, fc="none", ec=col, lw=1.6))
        # roadside outstation with detector card
        ax.add_patch(Rectangle((x - 0.8, 10.4), 1.6, 1.0, fc=col, ec="black", lw=0.8))
        ax.text(x, 10.9, "d%d" % (i + 1), ha="center", va="center", fontsize=10,
                color="white", fontweight="bold")
        ax.plot([x, x], [9.5, 10.4], color=col, lw=1.2)
        ax.plot([x, x], [11.4, 12.0], color="#2980B9", lw=1.2)
    ax.plot([xs[0], xs[-1] + 1.5], [12.0, 12.0], color="#2980B9", lw=1.8)
    ax.text(xs[-1] + 1.6, 12.0, "link (130)\nto archive (200)", fontsize=9, color="#2980B9",
            va="center")
    ax.text(xs[0] - 1.9, 10.9, "detector\nsites (110)", fontsize=9, color="#D68910",
            va="center", ha="center")
    # pairs
    for a, b in ((0, 1), (1, 2), (3, 4), (4, 5)):
        ax.annotate("", xy=(xs[b] - 0.9, 4.2), xytext=(xs[a] + 0.9, 4.2),
                    arrowprops=dict(arrowstyle="<->", color="#1E8449", lw=1.6))
        ax.text((xs[a] + xs[b]) / 2, 3.6, "admitted pair", ha="center", fontsize=9,
                color="#1E8449", fontweight="bold")
    ax.annotate("", xy=(xs[3] - 0.9, 4.2), xytext=(xs[2] + 0.9, 4.2),
                arrowprops=dict(arrowstyle="<->", color="#CB4335", lw=1.2, ls="--"))
    ax.text((xs[2] + xs[3]) / 2, 4.55, "not a pair: vehicles join between", fontsize=9,
            color="#CB4335", ha="center", bbox=dict(fc="white", ec="none", pad=1.0))
    ax.text(7.5, 2.4, "chain 1: d1 - d2 - d3", ha="center", fontsize=10.5, color="#1E8449",
            fontweight="bold")
    ax.text(24.5, 2.4, "chain 2: d4 - d5 - d6", ha="center", fontsize=10.5,
            color="#1E8449", fontweight="bold")
    ax.text(24.5, 1.2, "d5 reads every vehicle long: its share below 520 cm is lower\n"
            "than at BOTH neighbours, by the same amount", ha="center", fontsize=9.5,
            color="#C0392B")

    bx = fig.add_axes([0.07, 0.06, 0.88, 0.32])
    L = np.linspace(250, 1450, 900)

    def dens(shift):
        car = np.exp(-0.5 * ((L - shift - 450) / 45) ** 2) * 0.80
        van = np.exp(-0.5 * ((L - shift - 560) / 50) ** 2) * 0.22
        hgv = np.exp(-0.5 * ((L - shift - 1250) / 120) ** 2) * 0.28
        return car + van + hgv
    bx.plot(L, dens(0), color="#D68910", lw=2.2, label="d4, d6: lengths as measured "
            "(the same vehicles)")
    bx.fill_between(L, dens(0), color="#D68910", alpha=0.15)
    bx.plot(L, dens(45), color="#C0392B", lw=2.2, ls="--",
            label="d5: every length read 45 cm long")
    for e in (520, 660, 1160):
        bx.axvline(e, color="#455A64", lw=1.0, ls=":")
        bx.text(e + 8, 0.86, "boundary %d cm" % e, fontsize=9, color="#455A64")
    bx.fill_between(L, dens(0), dens(45), where=(L > 480) & (L < 565), color="#C0392B",
                    alpha=0.25)
    bx.annotate("vehicles moved from the class below\n520 cm into the class above",
                xy=(535, 0.45), xytext=(700, 0.55), fontsize=9.5, color="#C0392B",
                arrowprops=dict(arrowstyle="->", color="#C0392B"))
    bx.set_xlabel("vehicle length, cm  (schematic distributions)")
    bx.set_yticks([])
    bx.set_xlim(250, 1450)
    bx.legend(fontsize=9.5, frameon=False, loc="upper right")
    for s in ("top", "right", "left"):
        bx.spines[s].set_visible(False)
    save(fig, "fig01.png", 200, "roadside hardware and principle")


# ---------------------------------------------------------------- Figure 2
def fig02():
    fig, ax = plt.subplots(figsize=(23, 15.5))
    ax.set_xlim(0, 23)
    ax.set_ylim(-3.2, 14)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.05, -3.1), 22.9, 17.0, boxstyle="round,pad=0.05",
                                fill=False, ec="#B0BEC5", lw=1.2, ls="--"))

    # physical layer, full height at left
    zone(ax, 0.3, 0.9, 4.9, 12.3, Z_PHY, "100", "ROADSIDE HARDWARE")
    sub(ax, 0.6, 9.4, 4.3, 2.6, Z_PHY[0], 110, "Detector site", "pair of inductive loops",
        "in every lane")
    sub(ax, 0.6, 6.3, 4.3, 2.6, Z_PHY[0], 111, "Detector card", "length of each vehicle",
        "count per class, 15 min")
    sub(ax, 0.6, 3.2, 4.3, 2.6, Z_PHY[0], 112, "Neighbouring sites", "same carriageway,",
        "a few hundred metres apart")
    sub(ax, 0.6, 1.2, 4.3, 1.6, Z_PHY[0], 120, "Slip roads", "", "")
    arr(ax, (2.75, 9.4), (2.75, 8.9), color=Z_PHY[0])
    ax.plot([5.75, 5.75], [-2.2, 13.6], color="#455A64", lw=1.6, ls=(0, (8, 5)))
    ax.text(5.55, 13.75, "ROADSIDE", ha="right", fontsize=10, color="#455A64",
            fontweight="bold")
    ax.text(5.95, 13.75, "DATA-PROCESSING SYSTEM (900)", ha="left", fontsize=10,
            color="#455A64", fontweight="bold")

    # top row: archive, admission, chain solution
    zone(ax, 6.3, 7.4, 5.2, 5.8, Z_IN, "130-200", "LINK AND ARCHIVE")
    sub(ax, 6.6, 10.6, 4.6, 1.9, Z_IN[0], 130, "Communication link", "15-min records")
    sub(ax, 6.6, 8.0, 4.6, 2.1, Z_IN[0], 200, "Count archive", "class counts, totals,",
        "mean speed per interval")
    zone(ax, 12.0, 7.4, 5.2, 5.8, Z_PROC, "300-310", "PAIR ADMISSION")
    sub(ax, 12.3, 10.6, 4.6, 1.9, Z_PROC[0], 300, "Pair-admission unit",
        "no slip road; totals within 3 %")
    sub(ax, 12.3, 8.0, 4.6, 2.1, Z_PROC[0], 310, "Share-difference unit",
        "g_i(e) = S_i(e) - S_(i+1)(e)", "e = 520, 660, 1160 cm")
    zone(ax, 17.7, 7.4, 5.0, 5.8, Z_CORE, "320-360", "CHAIN SOLUTION")
    sub(ax, 18.0, 11.2, 4.4, 1.3, Z_CORE[0], 320, "Chain solver",
        "b_i - b_(i+1) = g_i ; median = 0")
    sub(ax, 18.0, 9.55, 4.4, 1.35, Z_CORE[0], "350/360", "Offset estimator",
        "one length offset d (cm) per unit;", "residual -> fault class")
    sub(ax, 18.0, 7.9, 4.4, 1.35, Z_CORE[0], "330/340", "Step-event detector",
        "equal and opposite steps;", "refit scheduler")

    # bottom row: reclassification, outputs, final action
    zone(ax, 17.7, 0.9, 5.0, 5.6, Z_RED, "400", "RECLASSIFICATION")
    sub(ax, 18.0, 3.5, 4.4, 2.2, Z_RED[0], 400, "Reclassification unit",
        "move b(e) x N vehicles", "across each boundary e")
    sub(ax, 18.0, 1.2, 4.4, 1.8, Z_RED[0], 405, "Interval total kept", "N unchanged")
    zone(ax, 12.0, 0.9, 5.2, 5.6, Z_OUT, "800", "OUTPUTS")
    sub(ax, 12.3, 4.1, 4.6, 1.6, Z_OUT[0], 810, "Corrected dataset", "written to archive")
    sub(ax, 12.3, 2.45, 4.6, 1.1, Z_OUT[0], 820, "Traffic-management process")
    sub(ax, 12.3, 1.1, 4.6, 1.2, Z_OUT[0], 830, "Maintenance record")
    ax.add_patch(FancyBboxPatch((6.6, 1.6), 4.6, 3.6, boxstyle="round,pad=0.08",
                                facecolor=DARK, edgecolor=DARK, zorder=5))
    ax.text(8.9, 3.4, "840  SENSITIVITY CORRECTION\nOF DETECTOR UNIT\n\nlength offset (cm) and\n"
            "fault class; dated change;\nmark for site retune", ha="center", va="center",
            color="white", fontsize=9.6, fontweight="bold", zorder=6, linespacing=1.3)

    # signal arrows
    arr(ax, (4.9, 11.5), (6.6, 11.5), color=Z_PHY[0], label="class counts",
        lpos=(5.9, 11.9))
    arr(ax, (8.9, 10.6), (8.9, 10.1), color=Z_IN[0])
    poly(ax, [(11.2, 9.3), (11.85, 9.3), (11.85, 11.55), (12.3, 11.55)], color=Z_IN[0],
         label="records", lpos=(11.85, 10.45))
    arr(ax, (14.6, 10.6), (14.6, 10.1), color=Z_PROC[0], label="admitted pairs",
        lpos=(15.95, 10.35))
    poly(ax, [(16.9, 9.7), (17.45, 9.7), (17.45, 11.85), (18.0, 11.85)], color=Z_PROC[0],
         label="g(e)", lpos=(17.45, 10.8))
    arr(ax, (16.9, 8.5), (18.0, 8.5), color=Z_PROC[0], label="daily g(e)",
        lpos=(17.45, 8.05))
    arr(ax, (20.2, 11.2), (20.2, 10.9), color=Z_CORE[0])
    poly(ax, [(22.4, 10.2), (22.55, 10.2), (22.55, 5.7)], color=Z_CORE[0],
         label="b(e), d (cm),\nfault class", lpos=(21.55, 6.95))
    arr(ax, (19.4, 7.9), (19.4, 5.7), color=Z_CORE[0], ls="--", label="refit date",
        lpos=(19.4, 6.95))
    arr(ax, (18.0, 4.6), (16.9, 4.6), color=Z_RED[0], label="corrected counts",
        lpos=(17.45, 5.2))
    arr(ax, (14.6, 4.1), (14.6, 3.55), color=Z_OUT[0])
    ax.text(14.85, 3.83, "supplied", fontsize=7.8, color=Z_OUT[0], fontweight="bold",
            va="center", zorder=8)
    poly(ax, [(18.0, 3.8), (17.45, 3.8), (17.45, 1.7), (16.9, 1.7)], color=Z_RED[0],
         label="offsets,\nfault class", lpos=(17.45, 2.75))
    poly(ax, [(12.3, 4.9), (11.6, 4.9), (11.6, 7.7), (10.6, 7.7), (10.6, 8.0)],
         color=Z_OUT[0], label="write back", lpos=(11.6, 6.3))
    arr(ax, (12.3, 1.9), (11.2, 1.9), color=Z_OUT[0])
    poly(ax, [(6.6, 3.4), (5.2, 3.4), (5.2, 7.6), (4.9, 7.6)], color=DARK, ls="--",
         label="retune on site", lpos=(5.75, 5.3), lcolor=DARK)

    # reference numerals, three columns
    refs = [("100", "roadside hardware"), ("110", "detector site, loop pairs"),
            ("111", "detector card"), ("112", "neighbouring sites"), ("120", "slip road"),
            ("130", "communication link"), ("200", "count archive"),
            ("300", "pair-admission unit"), ("310", "share-difference unit"),
            ("320", "chain solver"), ("330", "step-event detector"),
            ("340", "refit scheduler"), ("350", "offset estimator"),
            ("360", "fault classifier"), ("400", "reclassification unit"),
            ("405", "interval total kept"), ("810", "corrected dataset"),
            ("820", "traffic-management process"), ("830", "maintenance record"),
            ("840", "sensitivity correction"), ("900", "data-processing system")]
    per = (len(refs) + 2) // 3
    for i, (n, t) in enumerate(refs):
        col, row = divmod(i, per)
        ax.text(0.6 + 7.6 * col, -0.3 - 0.36 * row, "%s  %s" % (n, t), fontsize=7.6,
                color="#333", va="center")
    save(fig, "fig02.png", 200, "architecture")


# ---------------------------------------------------------------- Figure 3
def fig03():
    fig, ax = plt.subplots(figsize=(15, 23))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 23)
    ax.axis("off")
    bands = [(19.6, 22.8, "ACQUISITION", Z_PHY), (13.0, 19.4, "ADMISSION", Z_PROC),
             (8.4, 12.8, "CHAIN SOLUTION", Z_CORE), (4.6, 8.2, "CORRECTION", Z_RED),
             (0.3, 4.4, "OUTPUT", Z_OUT)]
    for y0, y1, lab, col in bands:
        ax.add_patch(FancyBboxPatch((0.2, y0), 0.9, y1 - y0, boxstyle="round,pad=0.04",
                                    facecolor=col[0], edgecolor=col[0], zorder=2))
        ax.text(0.65, (y0 + y1) / 2, lab, rotation=90, ha="center", va="center",
                color="white", fontsize=11, fontweight="bold", zorder=3)
        ax.add_patch(Rectangle((1.2, y0), 13.6, y1 - y0, fc=col[1], ec="none", alpha=0.45,
                               zorder=1))
    X = 5.6
    pbox(ax, X, 22.0, 7.4, 1.1, "S1  Loop pairs (110) and detector card (111) measure each\n"
         "vehicle's length and count it by class per 15 min", Z_PHY, bold=True)
    pbox(ax, X, 20.4, 7.4, 0.9, "S2  Records sent over link (130) to count archive (200)",
         Z_PHY)
    arr(ax, (X, 21.45), (X, 20.85))
    diamond(ax, X, 18.4, 5.2, 2.0, "Slip road between\nconsecutive sites?", Z_PROC)
    arr(ax, (X, 19.95), (X, 19.4))
    pbox(ax, 11.8, 18.4, 3.6, 0.9, "not a pair", Z_RED)
    arr(ax, (X + 2.6, 18.4), (10.0, 18.4), color=NO_C, label="YES", lpos=(9.1, 18.75),
        lcolor=NO_C)
    pbox(ax, X, 16.4, 7.4, 1.0, "S3  Matched intervals: both reported, mean speed\n"
         "> 50 mph at both, >= 100 vehicles", Z_PROC)
    arr(ax, (X, 17.4), (X, 16.9), color=YES_C, label="NO", lpos=(X + 0.45, 17.15),
        lcolor=YES_C)
    diamond(ax, X, 14.4, 5.6, 2.0, "Totals within 3 % over\n>= 500 intervals?", Z_PROC)
    arr(ax, (X, 15.9), (X, 15.4))
    pbox(ax, 11.8, 14.4, 3.6, 1.0, "excluded: not the\nsame vehicles", Z_RED)
    arr(ax, (X + 2.8, 14.4), (10.0, 14.4), color=NO_C, label="NO", lpos=(9.1, 14.75),
        lcolor=NO_C)
    pbox(ax, X, 12.1, 7.4, 1.0, "S4  Admitted pair: share difference g_i(e) below\n"
         "520, 660 and 1160 cm over matched intervals", Z_CORE)
    arr(ax, (X, 13.4), (X, 12.6), color=YES_C, label="YES", lpos=(X + 0.5, 13.0),
        lcolor=YES_C)
    diamond(ax, X, 10.55, 5.2, 1.5, "Chain of >= 2\nadmitted pairs?", Z_CORE)
    arr(ax, (X, 11.6), (X, 11.3))
    pbox(ax, 11.8, 10.55, 3.6, 0.9, "detector not\ncorrected", Z_RED)
    arr(ax, (X + 2.6, 10.55), (10.0, 10.55), color=NO_C, label="NO", lpos=(9.1, 10.9),
        lcolor=NO_C)
    pbox(ax, X, 8.9, 7.4, 0.9, "S5  Solve b_i(e) - b_(i+1)(e) = g_i(e); median of chain = 0",
         Z_CORE, bold=True)
    arr(ax, (X, 9.8), (X, 9.35), color=YES_C, label="YES", lpos=(X + 0.5, 9.58),
        lcolor=YES_C)
    pbox(ax, X, 7.3, 7.4, 1.0, "S6  Every later interval of each detector: move\n"
         "b(e) x N vehicles across each boundary e; N unchanged", Z_RED, bold=True)
    arr(ax, (X, 8.45), (X, 7.8))
    pbox(ax, X, 5.5, 7.4, 1.0, "S7  Corrected counts written to archive (200) and\n"
         "supplied to traffic-management process (820)", Z_RED)
    arr(ax, (X, 6.8), (X, 6.0))
    pbox(ax, X, 3.85, 7.4, 0.95, "S8  Each unit's biases -> one length offset d (cm) through\n"
         "the stream's length CDF; speed bias separates spacing from threshold", Z_OUT,
         bold=True)
    arr(ax, (X, 5.0), (X, 4.35))
    diamond(ax, X, 2.2, 5.6, 1.3, "biases at all boundaries fit\none offset d within limit?",
            Z_OUT, fs=8.4)
    arr(ax, (X, 3.37), (X, 2.87))
    pbox(ax, 11.8, 2.2, 3.6, 1.0, "record d (cm), class\n'length offset' (830)",
         (DARK, "#D5D8DC"), bold=True)
    arr(ax, (X + 2.8, 2.2), (10.0, 2.2), color=YES_C, label="YES", lpos=(9.1, 2.55),
        lcolor=YES_C)
    pbox(ax, X, 0.72, 7.4, 0.62, "S9  record class 'other fault' and biases (830); inspect site",
         Z_OUT)
    arr(ax, (X, 1.55), (X, 1.05), color=NO_C, label="NO", lpos=(X + 0.45, 1.3),
        lcolor=NO_C)

    # refit engine panel at right
    zone(ax, 9.7, 4.75, 5.0, 4.85, Z_CORE, "330/340", "REFIT ENGINE")
    pbox(ax, 12.2, 8.3, 4.4, 0.9, "daily g of the detector's\ntwo pairs", Z_CORE, fs=8.6)
    diamond(ax, 12.2, 6.5, 4.2, 1.7, "equal and opposite\nsteps within 1 day?", Z_CORE,
            fs=8.3)
    arr(ax, (12.2, 7.85), (12.2, 7.35))
    poly(ax, [(10.1, 6.5), (9.6, 6.5), (9.6, 8.9), (9.3, 8.9)], color=YES_C, ls="--")
    ax.text(12.2, 5.12, "YES: date the change in record (830);\nrefit from that day (to S5)",
            ha="center", va="center", fontsize=8.3, color=YES_C, fontweight="bold",
            zorder=8)
    # dashed loop around the monthly refit
    ax.add_patch(FancyBboxPatch((1.5, 6.2), 8.0, 6.6, boxstyle="round,pad=0.1", fill=False,
                                ec=Z_CORE[0], lw=1.4, ls="--", zorder=4))
    ax.text(9.35, 6.42, "S4-S6 repeated each period (claim 2)", ha="right",
            fontsize=8.5, color=Z_CORE[0], fontweight="bold", zorder=8)
    save(fig, "fig03.png", 200, "method flowchart")


# ---------------------------------------------------------------- Figure 4
def fig04():
    """Disagreement between adjacent detectors that see the same vehicles."""
    probe = load("probe.json")["roads"]
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    # (a) distribution of |gap| below 520 cm, March
    ax = axs[0, 0]
    bins = np.linspace(0, 42, 29)
    for road in ("M25", "M1"):
        g = [100 * abs(v["2025-03"]["gap520"]) for v in probe[road]["pairs"].values()
             if "2025-03" in v]
        ax.hist(g, bins=bins, color=ROAD_C[road], alpha=0.55, edgecolor="white",
                linewidth=1.2, label="%s (%d pairs, median %.1f)" % (
                    road, len(g), 100 * probe[road]["abs_gap520_median"]))
    ax.set_xlabel("|difference in share below 520 cm| between adjacent detectors, points")
    ax.set_ylabel("pairs")
    ax.legend(frameon=False, fontsize=9.5)
    panel(ax, "a")
    tidy(ax)
    # (b) persistence: March vs June per pair, admitted in both
    ax = axs[0, 1]
    for road in ("M25", "M1"):
        pts = [(100 * v["2025-03"]["gap520"], 100 * v["2025-06"]["gap520"])
               for v in probe[road]["pairs"].values()
               if "2025-03" in v and "2025-06" in v and v["2025-03"]["admitted"]
               and v["2025-06"]["admitted"]]
        x, y = np.array(pts).T
        r = np.corrcoef(x, y)[0, 1]
        ax.scatter(x, y, s=18, color=ROAD_C[road], alpha=0.65, edgecolor="white",
                   linewidth=0.5, label="%s: r = %.3f, R^2 = %.2f" % (road, r, r * r))
    lim = [-40, 40]
    ax.plot(lim, lim, color="#455A64", lw=1, ls="--")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("pair difference in March 2025, points")
    ax.set_ylabel("same pair in June 2025, points")
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    panel(ax, "b")
    tidy(ax)
    # (c) difference against volume ratio: the admission gate
    ax = axs[1, 0]
    for road in ("M25", "M1"):
        v = [x["2025-03"] for x in probe[road]["pairs"].values() if "2025-03" in x]
        ax.scatter([100 * (p["ratio"] - 1) for p in v], [100 * abs(p["gap520"]) for p in v],
                   s=18, color=ROAD_C[road], alpha=0.6, edgecolor="white", linewidth=0.5,
                   label=road)
    ax.axvspan(-3, 3, color=C[2], alpha=0.12, label="admitted: totals within 3 %")
    ax.set_xlim(-30, 30)
    ax.set_xlabel("upstream total / downstream total - 1, %")
    ax.set_ylabel("|difference below 520 cm|, points")
    ax.legend(frameon=False, fontsize=9.5)
    panel(ax, "c")
    tidy(ax)
    # (d) fitted bias at 520 cm, chains of 3 or more
    ax = axs[1, 1]
    for road in ("M25", "M1"):
        f = load("fit_march_%s.json" % road)
        b = np.sort([100 * abs(v["bias"][0]) for v in f.values() if v["chain_size"] >= 3])
        y = np.arange(1, len(b) + 1) / len(b)
        ax.plot(b, y, color=ROAD_C[road], lw=2.2, label="%s (%d detectors)" % (road, len(b)))
    for t in (1, 5):
        ax.axvline(t, color="#455A64", lw=1, ls=":")
        ax.text(t + 0.3, 0.05, "%d pt" % t, fontsize=9, color="#455A64")
    ax.set_xlim(0, 30)
    ax.set_xlabel("|fitted bias at 520 cm|, points (March 2025)")
    ax.set_ylabel("cumulative share of detectors")
    ax.legend(frameon=False, fontsize=9.5, loc="lower right")
    panel(ax, "d")
    tidy(ax)
    fig.tight_layout(h_pad=3, w_pad=3)
    save(fig, "fig04.png", 300, "disagreement")


# ---------------------------------------------------------------- Figure 5
def fig05():
    """Correction of months the fit did not see."""
    import e5_refit
    import method
    import pairs
    e1, e5 = load("e1_out_of_sample.json"), load("e5_refit.json")
    months = ["2025-04", "2025-05", "2025-06"]
    mlab = ["Apr", "May", "Jun"]
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    # (a) one chain, May, corrected with April fit
    ax = axs[0, 0]
    fits = e5_refit.fit("M25", "2025-04")
    chain = max(pairs.chains("M25", "2025-05"), key=len)
    dets = [chain[0][0]] + [p[1] for p in chain]
    raw, cor = [], []
    for i, d in enumerate(dets):
        rec = chain[i][3] if i < len(chain) else chain[i - 1][3]
        data = rec["a"] if i < len(chain) else rec["b"]
        raw.append(100 * method.shares(data, rec["keys"])[0])
        f = fits.get(d)
        cor.append(100 * method.shares(method.correct_series(data, f, "additive"),
                                       rec["keys"])[0] if f else np.nan)
    x = np.arange(len(dets))
    ax.plot(x, raw, "o-", color=RAW_C, lw=1.8, ms=6, label="May 2025, as recorded")
    ax.plot(x, cor, "o-", color=C[2], lw=2.2, ms=6,
            label="May 2025, corrected with April biases")
    ax.fill_between(x, raw, cor, color=C[2], alpha=0.15)
    ax.set_xticks(x)
    ax.set_xticklabels(dets, rotation=60, fontsize=8)
    ax.set_xlabel("detector (WebTRIS site id), in order along the M25")
    ax.set_ylabel("share of vehicles below 520 cm, %")
    ax.set_ylim(36, 78)
    ax.legend(frameon=False, fontsize=9.5, loc="lower left")
    ax.annotate("range %.1f -> %.1f points" % (np.nanmax(raw) - np.nanmin(raw),
                                               np.nanmax(cor) - np.nanmin(cor)),
                xy=(0.98, 0.95), xycoords="axes fraction", ha="right", fontsize=10,
                color=C[2], fontweight="bold")
    panel(ax, "a")
    tidy(ax)
    # (b) mean |gap| raw, fixed fit, rolling fit, both roads
    ax = axs[0, 1]
    w = 0.13
    xs = np.arange(len(months))
    k = 0
    for road in ("M25", "M1"):
        r = e5["roads"][road]
        for kind, col, lab in (("raw", RAW_C, "as recorded"),
                               ("fixed", C[3], "March fit"),
                               ("rolling", C[2], "fit on month before")):
            if kind == "raw":
                vals = [100 * r["fixed"][m]["raw_mean_abs_gap_520"] for m in months]
            else:
                vals = [100 * r[kind][m]["corrected_mean_abs_gap_520"] for m in months]
            pos = xs + (k - 2.5) * w
            ax.bar(pos, vals, w, color=col, edgecolor="white", linewidth=1.2,
                   hatch=None if road == "M25" else "//",
                   label="%s, %s" % (road, lab))
            for p, v in zip(pos, vals):
                ax.text(p, v + 0.12, "%.1f" % v if kind == "raw" else "%.2f" % v,
                        ha="center", va="bottom", fontsize=7.2,
                        rotation=0 if kind == "raw" else 90)
            k += 1
    ax.set_xticks(xs)
    ax.set_xticklabels(mlab)
    ax.set_ylabel("mean |difference below 520 cm|, points")
    ax.legend(frameon=False, fontsize=8.2, ncol=2, loc="upper center")
    ax.set_ylim(0, 11.5)
    panel(ax, "b")
    tidy(ax)
    # (c) constant-share vs proportional correction
    ax = axs[1, 0]
    for road, mk in (("M25", "o"), ("M1", "s")):
        add = [100 * e1["roads"][road][m]["all/additive"]["mean_abs_gap_touched"][0]
               for m in months]
        rat = [100 * e1["roads"][road][m]["all/ratio"]["mean_abs_gap_touched"][0]
               for m in months]
        ax.plot(mlab, add, mk + "-", color=ROAD_C[road], lw=2.2, ms=8,
                label="%s, constant-share (claimed)" % road)
        ax.plot(mlab, rat, mk + "--", color=ROAD_C[road], lw=1.6, ms=7, alpha=0.7,
                label="%s, proportional (7.1 ii)" % road)
        ax.fill_between(mlab, add, rat, color=ROAD_C[road], alpha=0.15)
    ax.set_ylabel("mean |difference below 520 cm| after correction, points")
    ax.set_xlabel("month corrected (biases fitted on March)")
    ax.legend(frameon=False, fontsize=9)
    panel(ax, "c")
    tidy(ax)
    # (d) all three boundaries, April
    ax = axs[1, 1]
    edges = ["520 cm", "660 cm", "1160 cm"]
    xs = np.arange(3)
    w = 0.2
    for j, road in enumerate(("M25", "M1")):
        a = e1["roads"][road]["2025-04"]["all/additive"]
        raw = [100 * v for v in a["mean_abs_gap_touched_raw"]]
        cor = [100 * v for v in a["mean_abs_gap_touched"]]
        p1 = xs + (2 * j - 1.5) * w
        p2 = xs + (2 * j - 0.5) * w
        ax.bar(p1, raw, w, color=RAW_C, edgecolor="white", linewidth=1.2,
               hatch=None if road == "M25" else "//", label="%s as recorded" % road)
        ax.bar(p2, cor, w, color=ROAD_C[road], edgecolor="white", linewidth=1.2,
               label="%s corrected" % road)
        for p, rv, cv in zip(p2, raw, cor):
            ax.text(p, cv + 0.1, "-%.0f%%" % (100 * (1 - cv / rv)), ha="center",
                    fontsize=8.5, color=ROAD_C[road], fontweight="bold")
    ax.set_yscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels(edges)
    ax.set_xlabel("class boundary (April 2025, biases fitted on March)")
    ax.set_ylabel("mean |difference in share below boundary|, points (log)")
    ax.legend(frameon=False, fontsize=9)
    panel(ax, "d")
    tidy(ax)
    fig.tight_layout(h_pad=3, w_pad=3)
    save(fig, "fig05.png", 300, "correction out of sample")


def chain_example():
    """Numbers quoted for Figure 5(a), saved separately so the text can cite them."""
    import e5_refit
    import method
    import pairs
    fits = e5_refit.fit("M25", "2025-04")
    chain = max(pairs.chains("M25", "2025-05"), key=len)
    dets = [chain[0][0]] + [p[1] for p in chain]
    raw, cor = [], []
    for i, d in enumerate(dets):
        rec = chain[i][3] if i < len(chain) else chain[i - 1][3]
        data = rec["a"] if i < len(chain) else rec["b"]
        raw.append(100 * method.shares(data, rec["keys"])[0])
        f = fits.get(d)
        if f:
            cor.append(100 * method.shares(method.correct_series(data, f, "additive"),
                                           rec["keys"])[0])
    return {"road": "M25", "month": "2025-05", "fit_month": "2025-04", "detectors": dets,
            "fitted": len(cor), "raw_range_pct": round(max(raw) - min(raw), 2),
            "corrected_range_pct": round(max(cor) - min(cor), 2)}


# ---------------------------------------------------------------- Figure 6
def fig06():
    """Known faults injected into real detectors."""
    d = load("e2_injection.json")
    sizes = d["sizes"]
    xs = [100 * s for s in sizes]
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    ax = axs[0, 0]
    for road, mk in (("M25", "o"), ("M1", "s")):
        for shape, ls in (("additive", "-"), ("ratio", ":")):
            loc = [100 * d["roads"][road]["%s %+.2f" % (shape, s)]["localised"]
                   for s in sizes]
            ax.plot(xs, loc, mk + ls, color=ROAD_C[road], lw=2 if ls == "-" else 1.4, ms=7,
                    label="%s, %s shape" % (road, "constant" if shape == "additive"
                                            else "proportional"))
    ax.set_ylim(70, 100)
    ax.set_xlabel("injected change in share below 520 cm, points")
    ax.set_ylabel("injected detector shows largest change on chain, %")
    ax.legend(frameon=False, fontsize=9)
    panel(ax, "a")
    tidy(ax)
    ax = axs[0, 1]
    for road, mk in (("M25", "o"), ("M1", "s")):
        med = [100 * d["roads"][road]["additive %+.2f" % s]["median_size_error"]
               for s in sizes]
        p90 = [100 * d["roads"][road]["additive %+.2f" % s]["p90_size_error"]
               for s in sizes]
        ax.plot(xs, med, mk + "-", color=ROAD_C[road], lw=2, ms=7, label="%s median" % road)
        ax.plot(xs, p90, mk + "--", color=ROAD_C[road], lw=1.6, ms=7,
                label="%s 90th percentile" % road)
    ax.plot(xs, [abs(x) / 2 for x in xs], color="#455A64", lw=1, ls=":",
            label="half the injection")
    ax.set_xlabel("injected change in share below 520 cm, points")
    ax.set_ylabel("|fitted - injected| bias, points")
    ax.legend(frameon=False, fontsize=9)
    panel(ax, "b")
    tidy(ax)
    keys = ["4", "5", "6", "7+"]
    xs2 = np.arange(len(keys))
    for idx, (metric, lab, letter) in enumerate((
            ("localised", "injected detector shows largest change, %", "c"),
            ("p90_size_error_over_injection", "90th percentile |size error| / injection, %",
             "d"))):
        ax = axs[1, idx]
        for j, road in enumerate(("M25", "M1")):
            v = [100 * d["roads"][road]["by_chain_size"][k][metric] for k in keys]
            pos = xs2 + (j - 0.5) * 0.36
            ax.bar(pos, v, 0.36, color=ROAD_C[road], edgecolor="white", linewidth=1.2,
                   label=road)
            for p, val in zip(pos, v):
                ax.text(p, val + 1, "%.0f%%" % val, ha="center", fontsize=9)
        ax.set_xticks(xs2)
        ax.set_xticklabels(keys)
        ax.set_xlabel("detectors on the chain")
        ax.set_ylabel(lab)
        ax.legend(frameon=False, fontsize=9.5)
        if metric == "localised":
            ax.set_ylim(0, 110)
        panel(ax, letter)
        tidy(ax)
    fig.tight_layout(h_pad=3, w_pad=3)
    save(fig, "fig06.png", 300, "injected faults")


# ---------------------------------------------------------------- Figure 7
def fig07():
    """One length offset per detector unit: structure, prediction, size, persistence."""
    d = load("e8_offset_model.json")
    big = d["big_threshold"]
    lim_res = d["residual_limit"]
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    # (a) bias at 660 against bias at 520, March, every fitted unit
    ax = axs[0, 0]
    for road, mk in (("M25", "o"), ("M1", "s")):
        pdm = d["roads"][road]["per_detector"]["2025-03"]
        x = np.array([100 * v["bias"][0] for v in pdm.values()])
        y = np.array([100 * v["bias"][1] for v in pdm.values()])
        st = d["roads"][road]["structure"]["2025-03"]
        ax.scatter(x, y, s=20, marker=mk, color=ROAD_C[road], alpha=0.6, edgecolor="white",
                   linewidth=0.5, label="%s units, March" % road)
        xs = np.array([-40, 40])
        ax.plot(xs, st["loadings"][1] * xs, color=ROAD_C[road], lw=1.8,
                label="%s fitted ratio %.2f" % (road, st["loadings"][1]))
        ax.plot(xs, st["cdf_density_ratio"][1] * xs, color=ROAD_C[road], lw=1.2, ls="--",
                label="%s ratio predicted from length density %.2f"
                % (road, st["cdf_density_ratio"][1]))
    ax.axhline(0, color="#B0BEC5", lw=0.8)
    ax.axvline(0, color="#B0BEC5", lw=0.8)
    ax.set_xlim(-40, 40)
    ax.set_ylim(-9, 9)
    ax.set_xlabel("unit bias below 520 cm, points (March 2025)")
    ax.set_ylabel("unit bias below 660 cm, points")
    ax.legend(frameon=False, fontsize=8.3, loc="upper left")
    panel(ax, "a")
    tidy(ax)
    # (b) ratio 660/520: fitted against predicted, every corridor-month
    ax = axs[0, 1]
    labels, obs, pred = [], [], []
    for road in ("M25", "M1"):
        for m, lab in (("2025-03", "Mar"), ("2025-04", "Apr"), ("2025-05", "May"),
                       ("2025-06", "Jun")):
            st = d["roads"][road]["structure"][m]
            labels.append("%s\n%s" % (road, lab))
            obs.append(st["loadings"][1])
            pred.append(st["cdf_density_ratio"][1])
    xs = np.arange(len(labels))
    ax.bar(xs - 0.2, obs, 0.4, color=C[4], edgecolor="white", linewidth=1.2,
           label="fitted from unit biases")
    ax.bar(xs + 0.2, pred, 0.4, color=C[5], edgecolor="white", linewidth=1.2,
           label="predicted: length density at 660 / at 520")
    for x0, o, p_ in zip(xs, obs, pred):
        ax.text(x0 - 0.2, o + 0.004, "%.2f" % o, ha="center", fontsize=8)
        ax.text(x0 + 0.2, p_ + 0.004, "%.2f" % p_, ha="center", fontsize=8)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 0.3)
    ax.set_ylabel("ratio of bias at 660 cm to bias at 520 cm")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    panel(ax, "b")
    tidy(ax)
    # (c) offset in cm, and the part a speed (loop-spacing) error could explain
    ax = axs[1, 0]
    bins = np.linspace(0, 160, 33)
    for road in ("M25", "M1"):
        pdm = d["roads"][road]["per_detector"]["2025-03"]
        sel = [v for v in pdm.values() if abs(v["bias"][0]) > big and v["offset_cm"] is not None]
        off = [abs(v["offset_cm"]) for v in sel]
        spd = [abs(720.0 * (np.exp(v["speed_bias"]) - 1.0)) for v in sel]
        ax.hist(off, bins=bins, color=ROAD_C[road], alpha=0.5, edgecolor="white",
                linewidth=1.0, label="%s length offset (median %.0f cm)" % (road, np.median(off)))
        ax.hist(spd, bins=bins, histtype="step", color=ROAD_C[road], lw=2.0, ls="--",
                label="%s part explained by speed bias (median %.0f cm)" % (road, np.median(spd)))
    ax.set_xlabel("|length offset| of unit, cm (units with |bias at 520 cm| > %d points)"
                  % round(100 * big))
    ax.set_ylabel("detector units")
    ax.legend(frameon=False, fontsize=8.8)
    panel(ax, "c")
    tidy(ax)
    # (d) the cross-boundary test: bias at 660 cm predicted from the unit's offset alone
    ax = axs[1, 1]
    e9 = load("e9_consistency.json")
    for road, mk in (("M25", "o"), ("M1", "s")):
        pdm = e9["roads"][road]["field"]["per_detector"]["2025-03"]
        ok = [v for v in pdm.values() if v["pred"] is not None and v["passes"]]
        bad = [v for v in pdm.values() if v["pred"] is not None and not v["passes"]]
        ax.scatter([100 * v["pred"][1] for v in ok], [100 * v["bias"][1] for v in ok], s=22,
                   marker=mk, color=ROAD_C[road], alpha=0.6, edgecolor="white", linewidth=0.5,
                   label="%s, passes: one offset (%d units)" % (road, len(ok)))
        ax.scatter([100 * v["pred"][1] for v in bad], [100 * v["bias"][1] for v in bad], s=46,
                   marker=mk, facecolor="none", edgecolor="#C0392B", linewidth=1.4,
                   label="%s, fails: fault of another kind (%d)" % (road, len(bad)))
    ax.plot([-9, 9], [-9, 9], color="#455A64", lw=1.0, ls="--",
            label="observed = predicted (no fitted parameter)")
    ax.axhline(0, color="#B0BEC5", lw=0.8)
    ax.axvline(0, color="#B0BEC5", lw=0.8)
    ax.set_xlim(-9, 9)
    ax.set_ylim(-9, 9)
    ax.set_xlabel("bias below 660 cm predicted from the unit's offset d, points (March 2025)")
    ax.set_ylabel("bias below 660 cm solved along the chain, points")
    ax.legend(frameon=False, fontsize=8.6, loc="upper left")
    panel(ax, "d")
    tidy(ax)
    fig.tight_layout(h_pad=3, w_pad=3)
    save(fig, "fig07.png", 300, "single length offset per unit")


# ---------------------------------------------------------------- Figure 8
def _broken(days, vals):
    xs, ys = [], []
    for i, (dd, v) in enumerate(zip(days, vals)):
        if i and dd - days[i - 1] > 1:
            xs.append(np.nan)
            ys.append(np.nan)
        xs.append(dd)
        ys.append(v)
    return xs, ys


def fig08():
    """Dated changes in length measurement: equal and opposite steps."""
    import e3_steps
    import pairs
    e3 = load("e3_step_events.json")
    events = e3["roads"]
    series_of = {}
    continuity = []
    for road in ("M25", "M1"):
        cands = pairs.candidates(road)
        into = {c[1]: c for c in cands}
        out_of = {c[0]: c for c in cands}
        for ev in events[road]["events"]:
            dd = ev["detector"]
            su = e3_steps.daily_series(into[dd][0], dd)
            sd = e3_steps.daily_series(dd, out_of[dd][1])
            series_of[(road, dd)] = (into[dd][0], out_of[dd][1], su, sd, ev)
            window = range(ev["day_index"] - 5, ev["day_index"] + 5)
            continuity.append({
                "road": road, "detector": dd,
                "both_pairs_all_days": all(k in su and k in sd for k in window),
                "missing_upstream_pair": [k - ev["day_index"] for k in window if k not in su],
                "missing_downstream_pair": [k - ev["day_index"] for k in window
                                            if k not in sd]})
    full = [c for c in continuity if c["both_pairs_all_days"]]
    full.sort(key=lambda c: -(abs(series_of[(c["road"], c["detector"])][4]
                                  ["step_upstream_pair"])))
    shown = full[:2]
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    for ax, c, letter in zip((axs[0, 0], axs[0, 1]), shown, "ab"):
        up, down, su, sd, ev = series_of[(c["road"], c["detector"])]
        dd = c["detector"]
        for s, col, lab in (
                (su, C[0], "pair %s -> %s (detector downstream): step %+.1f"
                 % (up, dd, 100 * ev["step_upstream_pair"])),
                (sd, C[1], "pair %s -> %s (detector upstream): step %+.1f"
                 % (dd, down, 100 * ev["step_downstream_pair"]))):
            days = sorted(s)
            x, y = _broken(days, [100 * s[k] for k in days])
            ax.plot(x, y, "o-", ms=3, lw=1.2, color=col, label=lab)
        ax.axvline(ev["day_index"] - 0.5, color="#455A64", ls="--", lw=1.2)
        ax.text(ev["day_index"] - 1.5, 0.02, "step day", transform=ax.get_xaxis_transform(),
                ha="right", fontsize=9, color="#455A64")
        ax.set_xticks([0, 31, 61, 92, 121])
        ax.set_xticklabels(["1 Mar", "1 Apr", "1 May", "1 Jun", "30 Jun"])
        ax.set_ylabel("daily difference below 520 cm, points")
        ax.set_title("%s, detector %s" % (c["road"], dd), fontsize=11, fontweight="bold")
        ax.legend(frameon=False, fontsize=9, loc="best")
        panel(ax, letter)
        tidy(ax)
    # (c) step in one pair against step in the other: equal and opposite
    ax = axs[1, 0]
    allev = []
    for road, mk in (("M25", "o"), ("M1", "s")):
        ev = events[road]["events"]
        ax.scatter([100 * e["step_upstream_pair"] for e in ev],
                   [100 * e["step_downstream_pair"] for e in ev], s=90, marker=mk,
                   color=ROAD_C[road], edgecolor="white", linewidth=1.2, zorder=5,
                   label="%s (%d events)" % (road, len(ev)))
        allev += [(road, e) for e in ev]
    # large steps labelled beside the point; small ones listed in a column with leaders
    small = sorted([(r, e) for r, e in allev if abs(e["step_upstream_pair"]) < 0.2],
                   key=lambda z: -z[1]["step_downstream_pair"])
    for r, e in allev:
        if abs(e["step_upstream_pair"]) >= 0.2:
            ax.annotate("%s %s" % (r, e["detector"]), (100 * e["step_upstream_pair"],
                                                      100 * e["step_downstream_pair"]),
                        textcoords="offset points", xytext=(12, -4), fontsize=9)
    for k, (r, e) in enumerate(small):
        ax.annotate("%s %s  (%+.1f / %+.1f)" % (r, e["detector"],
                                                100 * e["step_upstream_pair"],
                                                100 * e["step_downstream_pair"]),
                    (100 * e["step_upstream_pair"], 100 * e["step_downstream_pair"]),
                    xytext=(14, 38 - 6.5 * k), textcoords="data", fontsize=8.8,
                    va="center", arrowprops=dict(arrowstyle="-", color="#90A4AE", lw=0.7))
    lim = [-45, 50]
    ax.plot(lim, [-v for v in lim], color="#455A64", lw=1.2, ls="--",
            label="equal and opposite")
    ax.axhline(0, color="#B0BEC5", lw=0.8)
    ax.axvline(0, color="#B0BEC5", lw=0.8)
    ax.set_xlabel("step in the pair where the detector is downstream, points")
    ax.set_ylabel("step in the pair where it is upstream, points")
    ax.legend(frameon=False, fontsize=9.5, loc="lower left")
    panel(ax, "c")
    tidy(ax)
    # (d) event rate against the control
    ax = axs[1, 1]
    labels, vals, cols, notes = [], [], [], []
    for road in ("M25", "M1"):
        r = events[road]
        labels += ["%s\ndetectors" % road, "%s\ncontrol" % road]
        vals += [100 * r["n_events"] / r["detectors_tested"],
                 100 * r["control_events"] / r["control_trials"]]
        cols += [ROAD_C[road], RAW_C]
        notes += ["%d / %d" % (r["n_events"], r["detectors_tested"]),
                  "%d / %d" % (r["control_events"], r["control_trials"])]
    ax.bar(labels, vals, color=cols, edgecolor="white", linewidth=1.2)
    for i, (v, n) in enumerate(zip(vals, notes)):
        ax.text(i, v + 0.1, n, ha="center", fontsize=10, fontweight="bold")
    ax.set_ylabel("share showing the signature, %")
    ax.set_ylim(0, max(vals) * 1.3)
    panel(ax, "d")
    tidy(ax)
    fig.tight_layout(h_pad=3, w_pad=3)
    save(fig, "fig08.png", 300, "dated changes")
    return {"shown": [(c["road"], c["detector"]) for c in shown],
            "continuity_5_days_either_side": continuity}


# ---------------------------------------------------------------- Figure 9
def fig09():
    """Admission conditions and the attendance mark."""
    e4 = load("e4_ablation.json")
    fl = load("flag_rules.json")
    months = ["2025-04", "2025-05", "2025-06"]
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    variants = [("claimed", C[2]), ("no volume gate", C[1]),
                ("loose volume gate 10%", C[3]), ("no free-flow condition", C[4])]
    for ax, road, letter in ((axs[0, 0], "M25", "a"), (axs[0, 1], "M1", "b")):
        xs = np.arange(3)
        w = 0.2
        for j, (name, col) in enumerate(variants):
            v = [100 * e4["variants"][name][road]["scores"][m]["corrected_mean_abs_gap_520"]
                 for m in months]
            pos = xs + (j - 1.5) * w
            ax.bar(pos, v, w, color=col, edgecolor="white", linewidth=1.2, label=name)
            for p, val in zip(pos, v):
                ax.text(p, val * 1.01, "%.2f" % val, ha="center", va="bottom", fontsize=7.5,
                        rotation=90)
        ax.set_ylim(0, 1.22 * max(100 * e4["variants"][n][road]["scores"][m]
                                  ["corrected_mean_abs_gap_520"]
                                  for n, _ in variants for m in months))
        ax.set_xticks(xs)
        ax.set_xticklabels(["Apr", "May", "Jun"])
        ax.set_ylabel("corrected mean |difference below 520 cm|, points")
        ax.set_title("%s: fit on March with one condition relaxed" % road, fontsize=11,
                     fontweight="bold")
        ax.legend(frameon=False, fontsize=9)
        panel(ax, letter)
        tidy(ax)
    ax = axs[1, 0]
    tols = ["0.01", "0.02", "0.03", "0.05"]
    tx = [100 * float(t) for t in tols]
    for road, mk in (("M25", "o"), ("M1", "s")):
        c = fl[road]["march_counts"]
        n = c["0.01"]["detectors"]
        for rule, ls in (("median", "-"), ("local", "--")):
            y = [100 * c[t][rule] / n for t in tols]
            ax.plot(tx, y, mk + ls, color=ROAD_C[road], lw=2 if ls == "-" else 1.5, ms=7,
                    label="%s, %s rule" % (road, rule))
    ax.set_xlabel("tolerance, points")
    ax.set_ylabel("fitted detectors marked in March, %")
    ax.legend(frameon=False, fontsize=9)
    panel(ax, "c")
    tidy(ax)
    ax = axs[1, 1]
    for road, mk in (("M25", "o"), ("M1", "s")):
        for rule, col in (("median", C[2]), ("local", C[3])):
            pts = []
            for t in ("0.02", "0.03", "0.05"):
                r = fl[road]["injection"]["%s T=%s" % (rule, t)]
                a, b = r["newly_flagged"].split("/")
                pts.append((r["other_flips_per_injection"], 100 * int(a) / int(b), t))
            ax.plot([p[0] for p in pts], [p[1] for p in pts], mk + "-", color=col, ms=8,
                    lw=1.6, label="%s, %s rule" % (road, rule))
            for p in pts:
                ax.annotate("%.0f pt" % (100 * float(p[2])), (p[0], p[1]),
                            textcoords="offset points", xytext=(6, -10), fontsize=8)
    ax.set_xlabel("marks of other detectors changed per injected fault")
    ax.set_ylabel("injected faults newly marked, %")
    ax.legend(frameon=False, fontsize=9)
    panel(ax, "d")
    tidy(ax)
    fig.tight_layout(h_pad=3, w_pad=3)
    save(fig, "fig09.png", 300, "conditions and attendance mark")


def fig10():
    """Ground truth: fitted biases against independent manual classified counts."""
    d = load("e11_ground_truth.json")["pooled"]
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    for col, (key, edge, what) in enumerate((("b520", 520, "cars and motorcycles (vans as covariate)"),
                                             ("b660", 660, "cars, motorcycles and vans"))):
        st = d[key]
        pts = st["points"]
        fitb = st["fit_raw_deviation_on_bias"]
        ax = axs[0, col]
        for road, mk in (("M25", "o"), ("M1", "s")):
            sel = [q for q in pts if q["road"] == road]
            ax.scatter([q["bias_pts"] for q in sel], [q["dev_raw_pts"] for q in sel], s=60,
                       marker=mk, color=ROAD_C[road], alpha=0.8, edgecolor="white",
                       linewidth=0.8, label="%s detector at a manual count (%d)" % (road, len(sel)))
        lo = min(q["bias_pts"] for q in pts) - 2
        hi = max(q["bias_pts"] for q in pts) + 2
        xs = np.array([lo, hi])
        ax.plot(xs, fitb["alpha_pts"] + xs, color="#455A64", ls="--", lw=1.2,
                label="slope 1: fitted bias is the real error")
        ax.plot(xs, fitb["alpha_pts"] + fitb["beta"] * xs, color="#C0392B", lw=1.8,
                label="fitted: slope %.2f +- %.2f, r = %.2f" % (fitb["beta"], fitb["beta_se"],
                                                               fitb["r"]))
        ax.set_xlabel("bias below %d cm fitted from detector pairs only, points" % edge)
        ax.set_ylabel("recorded share below %d cm less the manual-count share, points" % edge)
        ax.set_title("below %d cm; manual proxy: %s" % (edge, what), fontsize=10.5)
        ax.legend(frameon=False, fontsize=9, loc="upper left")
        panel(ax, "ab"[col])
        tidy(ax)
        ax = axs[1, col]
        raw = np.array([q["dev_raw_pts"] for q in pts])
        cor = np.array([q["dev_corrected_pts"] for q in pts])
        raw = raw - np.median(raw)
        cor = cor - np.median(cor)
        order = np.argsort(raw)
        ys = np.arange(len(pts))
        for y, i in zip(ys, order):
            ax.plot([raw[i], cor[i]], [y, y], color="#B0BEC5", lw=1.0, zorder=1)
        ax.scatter(raw[order], ys, s=34, color="#90A4AE", zorder=2,
                   label="recorded (spread %.1f points, MAD)" % st["mad_raw_pts"])
        ax.scatter(cor[order], ys, s=34, color=C[1], zorder=3,
                   label="corrected (spread %.1f points, MAD)" % st["mad_corrected_pts"])
        ax.axvline(0, color="#455A64", lw=0.8)
        ax.set_yticks([])
        ax.set_xlabel("departure from the manual count below %d cm, about the median, points" % edge)
        ax.set_ylabel("detector-count pairs (%d)" % len(pts))
        ax.legend(frameon=False, fontsize=9.5, loc="lower right")
        panel(ax, "cd"[col])
        tidy(ax)
    fig.tight_layout(h_pad=3, w_pad=3)
    save(fig, "fig10.png", 300, "ground truth against manual counts")


# ---------------------------------------------------------------- Figure 10
def depbox(ax, x, y, w, h, bd, head, text):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", facecolor="white",
                                edgecolor=bd, linewidth=1.6, zorder=5))
    ax.add_patch(FancyBboxPatch((x, y + h - 0.8), w, 0.8, boxstyle="round,pad=0.02",
                                facecolor=bd, edgecolor=bd, linewidth=0, zorder=6))
    ax.text(x + w / 2, y + h - 0.4, head, ha="center", va="center", fontsize=10,
            fontweight="bold", color="white", zorder=7)
    ax.text(x + w / 2, y + (h - 0.8) / 2, text, ha="center", va="center", fontsize=9.3,
            zorder=7, linespacing=1.35)


def fig11():
    fig, ax = plt.subplots(figsize=(17, 7.0))
    ax.set_xlim(0, 34)
    ax.set_ylim(0, 13.6)
    ax.axis("off")
    zone(ax, 0.4, 7.4, 21.6, 5.8, Z_PROC, "Claim 1", "INDEPENDENT - METHOD")
    ax.text(11.2, 10.05, "detectors (110) -> link (130) -> slip-free pairs admitted by total balance\n"
            "-> share difference per boundary -> signed bias per detector per boundary,\n"
            "chain reference fixed -> LENGTH OFFSET (cm) from the stream's own length\n"
            "distribution -> CROSS-BOUNDARY TEST: offset predicts the other boundaries\n"
            "-> reclassification, totals kept -> archive (200); fault class + offset (830)",
            ha="center", va="center", fontsize=10.3, zorder=6, linespacing=1.45)
    zone(ax, 23.2, 7.4, 10.4, 5.8, Z_IN, "Claim 7", "INDEPENDENT - SYSTEM")
    ax.text(28.4, 10.05, "count archive (200), pair admission\n(300), share difference (310), chain\n"
            "solver (320), offset estimator (350),\nfault classifier (360), reclassification\n"
            "unit (400), maintenance record (830)", ha="center", va="center", fontsize=10.3,
            zorder=6, linespacing=1.45)
    deps = [(0.7, "Claim 2", "refit each\nperiod; apply\nto the next"),
            (4.95, "Claim 3", "equal and\nopposite steps:\ndate the change,\nrefit from it"),
            (9.2, "Claim 4", "live correction\nsupplied to\ntraffic\nmanagement"),
            (13.45, "Claim 5", "sensitivity\ncorrection sent\nto the detector\ncard (111)"),
            (17.7, "Claim 6", "speed bias splits\nloop spacing\nfrom threshold\nerror")]
    for x, head, t in deps:
        depbox(ax, x, 0.6, 3.9, 4.8, Z_PROC[0], head, t)
        arr(ax, (x + 1.95, 7.4), (x + 1.95, 5.5), color=Z_PROC[0])
    depbox(ax, 26.3, 0.6, 4.2, 4.8, Z_IN[0], "Claim 8",
           "each detector a\npair of inductive\nloops in every lane")
    arr(ax, (28.4, 7.4), (28.4, 5.5), color=Z_IN[0])
    save(fig, "fig11.png", 200, "claim tree")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
    notes = {}
    for w in which:
        r = globals()["fig%02d" % int(w)]()
        if int(w) == 5:
            notes["fig05"] = chain_example()
        elif r is not None:
            notes["fig%02d" % int(w)] = r
    if notes:
        path = os.path.join(RESULTS, "idfb_fig_notes.json")
        old = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                old = json.load(fh)
        old.update(notes)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(old, fh, indent=1)
