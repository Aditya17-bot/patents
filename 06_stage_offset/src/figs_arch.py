"""Architecture (Figure 1) and flowchart (Figure 2), redrawn with routed signal lanes.

Style per diagram-tools.md / SKILL (2).md: zones with coloured header strips, white
sub-component boxes with italic reference numerals, a dashed frame for the processing
system, labelled signal arrows on separate lanes so that no arrow crosses a zone header,
and a flowchart with stage bands, a decision diamond, YES/NO branches and the hardware
it exchanges signals with. ASCII labels only.
"""
import importlib.util
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

_spec = importlib.util.spec_from_file_location(
    "p4_make_figs", os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_figs.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

zone, sub, arr, poly, pbox, diamond = M.zone, M.sub, M.arr, M.poly, M.pbox, M.diamond
Z_IN, Z_CORE, Z_RED, Z_PHY, Z_PROC, Z_OUT, DARK = M.Z_IN, M.Z_CORE, M.Z_RED, M.Z_PHY, M.Z_PROC, M.Z_OUT, M.DARK
YES_C, NO_C = M.YES_C, M.NO_C
save = M.save


def box(ax, x, y, w, h, bd, ref, title, l1="", l2=""):
    """Sub-component box with numeral, bold title and up to two description lines."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04", facecolor="white",
                                edgecolor=bd, linewidth=1.6, zorder=5))
    ax.text(x + 0.1, y + h - 0.08, str(ref), fontsize=8.5, color="#666", va="top", ha="left",
            zorder=6, fontstyle="italic")
    n = bool(l1) + bool(l2)
    ty = y + h / 2 + 0.16 * n
    ax.text(x + w / 2, ty, title, fontsize=10, fontweight="bold", color="#1A1A1A",
            va="center", ha="center", zorder=6)
    if l1:
        ax.text(x + w / 2, ty - 0.33, l1, fontsize=8.6, color="#444", va="center", ha="center",
                zorder=6, fontstyle="italic")
    if l2:
        ax.text(x + w / 2, ty - 0.62, l2, fontsize=8.6, color="#444", va="center", ha="center",
                zorder=6)


def lane(ax, pts, color, label=None, lpos=None, ls="-"):
    poly(ax, pts, color=color, lw=2.0, ls=ls, label=label, lpos=lpos, lcolor=color)


def fig01():
    fig, ax = plt.subplots(figsize=(22, 14.2))
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 14.2)
    ax.axis("off")
    # ------------------------------------------------ processing system (top band)
    ax.add_patch(FancyBboxPatch((0.35, 7.95), 21.3, 5.95, boxstyle="round,pad=0.05",
                                facecolor="none", edgecolor="#7F8C8D", linewidth=1.4,
                                linestyle=(0, (6, 4)), zorder=1))
    ax.text(0.55, 13.62, "DATA-PROCESSING SYSTEM  900", fontsize=10.5, fontweight="bold",
            color="#566573", ha="left", va="center")
    zone(ax, 0.6, 8.2, 6.0, 5.0, Z_IN, "200", "RECORD ARCHIVE")
    box(ax, 0.8, 8.5, 1.8, 2.6, Z_IN[0], 210, "Series", "h(t), Q_Y(t)", "15 min / daily")
    box(ax, 2.8, 8.5, 1.75, 2.6, Z_IN[0], 220, "Rating", "base R(g)", "stage -> Q")
    box(ax, 4.75, 8.5, 1.65, 2.6, Z_IN[0], 230, "Offsets", "measured", "at visits")
    ax.text(3.6, 11.85, "15-minute stage, neighbour discharge,\nrating and field-visit offsets",
            ha="center", va="center", fontsize=9.2, color="#1B4F72", linespacing=1.35)

    zone(ax, 7.6, 8.2, 6.8, 5.0, Z_CORE, "300", "OFFSET ESTIMATION")
    box(ax, 7.85, 8.45, 2.0, 1.25, Z_CORE[0], 310, "Pair admission", "lag, coupling")
    box(ax, 10.05, 8.45, 2.0, 1.25, Z_CORE[0], 320, "Discrepancy", "y = ln Q_Y - ln R(h)")
    box(ax, 12.25, 8.45, 1.95, 1.25, Z_CORE[0], 330, "Log-slope", "x = d ln R / dh")
    box(ax, 7.85, 10.05, 6.35, 1.05, Z_CORE[0], 340, "Stage-unit fit per window",
        "s = sum x (y - c) / sum(x^2),  c fixed at the visits  (m)")
    box(ax, 7.85, 11.35, 6.35, 1.2, Z_CORE[0], 350, "Offset estimator",
        "s(t) = s_lin(t) + g [s_raw(t) - s_lin(t)],  g from earlier visits")
    arr(ax, (9.85, 9.07), (10.05, 9.07), color=Z_CORE[0])
    arr(ax, (11.05, 9.7), (11.05, 10.05), color=Z_CORE[0])
    arr(ax, (13.2, 9.7), (13.2, 10.05), color=Z_CORE[0])
    arr(ax, (11.0, 11.1), (11.0, 11.35), color=Z_CORE[0])

    zone(ax, 15.4, 8.2, 6.0, 5.0, Z_RED, "400", "CORRECTION UNIT")
    box(ax, 15.65, 10.9, 5.5, 1.65, Z_RED[0], 410, "Corrected discharge record",
        "Q(t) = R(h(t) + s(t))", "every 15-minute stage value")
    box(ax, 15.65, 8.5, 5.5, 1.9, Z_RED[0], 420, "Offset command",
        "offset in force, for the logger", "replaces the last measured offset")
    # internal flows
    arr(ax, (6.6, 9.07), (7.85, 9.07), color=Z_IN[0], label="records", lpos=(7.22, 9.32))
    arr(ax, (14.2, 11.95), (15.65, 11.95), color=Z_CORE[0], label="s(t)", lpos=(14.92, 12.2))
    lane(ax, [(14.2, 11.6), (14.9, 11.6), (14.9, 9.45), (15.65, 9.45)], Z_CORE[0])

    # ------------------------------------------------ field hardware (bottom band)
    ax.add_patch(Rectangle((0.35, 0.3), 21.3, 0.5, facecolor="#D6EAF8", edgecolor="#5DADE2",
                           lw=1.2, zorder=1))
    ax.text(11.0, 0.55, "RIVER   --->   flow   (no significant tributary, abstraction or storage "
            "between stations 120 and 100)", ha="center", va="center", fontsize=9.6,
            color="#1B4F72", fontweight="bold", zorder=2)
    zone(ax, 0.6, 1.05, 6.0, 5.0, Z_PHY, "120", "NEIGHBOURING STATION")
    box(ax, 0.8, 3.65, 2.6, 1.7, Z_PHY[0], 121, "Stage sensor", "pressure / radar")
    box(ax, 3.7, 3.65, 2.7, 1.7, Z_PHY[0], 125, "Data logger", "Q_Y = R_Y(h_Y + s_Y)")
    box(ax, 0.8, 1.3, 5.6, 1.95, Z_PHY[0], 128, "Channel control", "riffle, weir or section")
    zone(ax, 7.6, 1.05, 6.8, 5.0, Z_PHY, "100", "TARGET GAUGING STATION")
    box(ax, 7.85, 3.65, 2.9, 1.7, Z_PHY[0], 110, "Stage sensor", "transducer / bubbler", "/ radar")
    box(ax, 11.0, 3.65, 3.2, 1.7, Z_PHY[0], 115, "Data logger", "applies R(h + s)")
    box(ax, 7.85, 1.3, 6.35, 1.95, Z_PHY[0], 118, "Channel control",
        "scour, fill, weed, debris, ice", "move the relation: offset s")
    zone(ax, 15.4, 1.05, 6.0, 5.0, Z_PHY, "600", "FIELD VISIT")
    box(ax, 15.65, 3.65, 5.5, 1.7, Z_PHY[0], 620, "Field-visit record",
        "Q_meas, GH_meas -> s_meas")
    box(ax, 15.65, 1.3, 5.5, 1.95, Z_PHY[0], 610, "Discharge measurement",
        "ADCP or current meter,", "reference gauge reading")
    arr(ax, (18.4, 3.25), (18.4, 3.65), color=Z_PHY[0])
    arr(ax, (3.4, 4.5), (3.7, 4.5), color=Z_PHY[0])
    arr(ax, (10.75, 4.5), (11.0, 4.5), color=Z_PHY[0])

    # ------------------------------------------------ telemetry lanes (link 130)
    ax.text(21.55, 7.0, "telemetry link 130", fontsize=9, color="#555", ha="right",
            va="center", fontstyle="italic")
    lane(ax, [(5.05, 5.35), (5.05, 6.55), (1.7, 6.55), (1.7, 8.5)], "#B9770E",
         label="Q_Y(t)", lpos=(3.4, 6.55))
    lane(ax, [(12.6, 5.35), (12.6, 6.95), (2.6, 6.95), (2.6, 8.5)], "#AF601A",
         label="h(t)", lpos=(7.1, 6.95))
    lane(ax, [(18.4, 5.35), (18.4, 7.35), (5.6, 7.35), (5.6, 8.5)], "#7D6608",
         label="s_meas at each visit", lpos=(11.4, 7.35))
    lane(ax, [(15.65, 8.85), (15.05, 8.85), (15.05, 6.2), (13.6, 6.2), (13.6, 5.35)], Z_RED[0],
         label="offset s(t)", lpos=(14.3, 6.2), ls="--")
    save(fig, "fig01.png", 200, "architecture")


def fig02():
    fig, ax = plt.subplots(figsize=(15, 19.5))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 19.5)
    ax.axis("off")
    bands = [(14.75, 4.45, Z_IN, "INPUT"), (9.45, 5.1, Z_CORE, "ESTIMATION"),
             (7.0, 2.25, Z_PROC, "DECISION"), (0.9, 5.9, Z_RED, "ACTION")]
    for y, h, col, lab in bands:
        ax.add_patch(FancyBboxPatch((0.2, y), 0.8, h, boxstyle="round,pad=0.04",
                                    facecolor=col[0], edgecolor=col[0], zorder=2))
        ax.text(0.6, y + h / 2, lab, rotation=90, color="white", fontsize=11.5,
                fontweight="bold", ha="center", va="center", zorder=3)
    X, W = 5.75, 8.5
    R = X + W / 2
    pbox(ax, X, 17.85, W, 1.75, "S1  Receive the stage h(t) recorded at station 100,\n"
         "the base rating R, and the offsets s(P), s(N)\nmeasured at the field visits", Z_IN, fs=10)
    pbox(ax, X, 15.6, W, 1.3, "S2  Receive discharge Q_Y(t) of neighbour 120; find lag tau;\n"
         "admit if coupling >= 0.95 and area increment <= 20 %", Z_IN, fs=10)
    steps = [(13.75, "S3  Each steady day:  y = ln Q_Y(t - tau) - ln R(h(t))\n"
                     "x = d ln R / dh at h(t)   (offset s moves y by s x)"),
             (12.0, "S4  Flow ratio c fixed at visits P and N from their measured offsets;\n"
                    "offset of the window at t:  s_raw = sum x (y - c) / sum(x^2)"),
             (10.25, "S5  Gain g = regression of measured on estimated departures\n"
                     "over the station's earlier visits (prior 0.5, limits 0 to 1.2)")]
    for y, t in steps:
        pbox(ax, X, y, W, 1.25, t, Z_CORE, fs=10)
    arr(ax, (X, 16.95), (X, 16.28), color="#333")
    arr(ax, (X, 14.93), (X, 14.4), color="#333")
    arr(ax, (X, 13.1), (X, 12.65), color="#333")
    arr(ax, (X, 11.35), (X, 10.9), color="#333")
    diamond(ax, X, 8.15, 4.6, 1.85, "Visit N already\nmeasured?", Z_PROC, fs=10.5)
    arr(ax, (X, 9.6), (X, 9.1), color="#333")
    pbox(ax, 3.45, 5.3, 4.0, 1.9, "S6a  Record between visits\n(claim 1)\n"
         "s(t) = s_lin(t)\n + g [s_raw(t) - s_lin(t)]", Z_RED, fs=9.6)
    pbox(ax, 8.05, 5.3, 4.0, 1.9, "S6b  Real time (claim 2)\n"
         "s(t) = s(P) + g [s_raw(t) - s(P)]\nc from visit P; data before t", Z_RED, fs=9.6)
    poly(ax, [(X - 2.3, 8.15), (3.45, 8.15), (3.45, 6.3)], color=YES_C, label="YES",
         lpos=(3.05, 7.3), lcolor=YES_C)
    poly(ax, [(X + 2.3, 8.15), (8.05, 8.15), (8.05, 6.3)], color=NO_C, label="NO",
         lpos=(8.45, 7.3), lcolor=NO_C)
    pbox(ax, X, 2.3, W, 1.55, "S7  Write Q(t) = R(h(t) + s(t)) for every stage value to the\n"
         "corrected record 410; send the offset in force over link 130\n"
         "to data logger 115, which applies R(h + s) on site", Z_RED, fs=10)
    arr(ax, (3.45, 4.3), (4.4, 3.12), color="#333")
    arr(ax, (8.05, 4.3), (7.1, 3.12), color="#333")
    # field hardware: inputs (top panel) and the logger (bottom panel)
    HX, HW = 12.85, 3.3
    for y0, y1 in ((14.75, 19.2), (1.2, 3.4)):
        ax.add_patch(FancyBboxPatch((HX - HW / 2 - 0.2, y0), HW + 0.4, y1 - y0,
                                    boxstyle="round,pad=0.05", facecolor="#FEF9E7",
                                    edgecolor=Z_PHY[0], linewidth=1.5, zorder=1))
    ax.text(HX, 18.95, "FIELD HARDWARE", ha="center", va="center", fontsize=10.5,
            fontweight="bold", color=Z_PHY[0])
    pbox(ax, HX, 18.25, HW, 0.85, "Stage sensor 110", Z_PHY, fs=9.8)
    pbox(ax, HX, 17.15, HW, 0.95, "Field visit 600\nQ_meas, GH_meas", Z_PHY, fs=9.6)
    pbox(ax, HX, 15.6, HW, 0.95, "Neighbouring\nstation 120", Z_PHY, fs=9.6)
    pbox(ax, HX, 2.3, HW, 1.25, "Data logger 115\napplies R(h + s)", Z_PHY, fs=9.8)
    arr(ax, (HX - HW / 2, 18.25), (R, 18.25), color=Z_PHY[0], label="h(t)", lpos=(10.6, 18.47))
    arr(ax, (HX - HW / 2, 17.15), (R, 17.15), color="#7D6608", label="s_meas", lpos=(10.6, 17.37))
    arr(ax, (HX - HW / 2, 15.6), (R, 15.6), color=Z_PHY[0], label="Q_Y(t)", lpos=(10.6, 15.82))
    arr(ax, (R, 2.3), (HX - HW / 2, 2.3), color=Z_RED[0], ls="--", label="offset s(t)",
        lpos=(10.6, 2.55))
    ax.text(12.85, 14.35, "all signals over telemetry link 130", ha="center", fontsize=9,
            style="italic", color="#666")
    ax.text(X, 0.75, "repeated each day; a new field visit becomes P", ha="center",
            fontsize=10, style="italic", color="#444")
    save(fig, "fig02.png", 200, "flowchart")
