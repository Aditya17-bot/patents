"""Architecture (Figure 1) and flowchart (Figure 2) for the anchored floor correction.

Style per diagram-tools.md: zones with coloured header strips, white sub-component boxes
with italic reference numerals, a dashed frame for the processing system, labelled signal
lanes, and a flowchart with stage bands, a decision diamond and YES/NO branches. Drawing
helpers are imported unchanged from the patent 05 generator. ASCII labels only.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

sys.path.insert(0, r"C:\adi\patents\05_length_invariance\src")
import make_figs as P3                                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "patent", "figures")
zone, arr, poly, pbox, diamond = P3.zone, P3.arr, P3.poly, P3.pbox, P3.diamond
Z_IN, Z_CORE, Z_RED, Z_PHY, Z_PROC = P3.Z_IN, P3.Z_CORE, P3.Z_RED, P3.Z_PHY, P3.Z_PROC
YES_C, NO_C = P3.YES_C, P3.NO_C
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def save(fig, name, dpi=200):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name), dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(name)


def box(ax, x, y, w, h, bd, ref, title, l1="", l2=""):
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
    # processing system
    ax.add_patch(FancyBboxPatch((0.35, 7.95), 21.3, 5.95, boxstyle="round,pad=0.05",
                                facecolor="none", edgecolor="#7F8C8D", linewidth=1.4,
                                linestyle=(0, (6, 4)), zorder=1))
    ax.text(0.55, 13.62, "DATA-PROCESSING SYSTEM  900", fontsize=10.5, fontweight="bold",
            color="#566573", ha="left", va="center")
    zone(ax, 0.6, 8.2, 6.0, 5.0, Z_IN, "200", "RECORD ARCHIVE")
    box(ax, 0.8, 8.5, 2.7, 2.6, Z_IN[0], 210, "Sonde series", "ammonium A(t)", "every 15 min")
    box(ax, 3.7, 8.5, 2.7, 2.6, Z_IN[0], 230, "Laboratory", "results L at", "sampling times")
    ax.text(3.6, 11.85, "15-minute sonde readings and\nlaboratory ammoniacal nitrogen",
            ha="center", va="center", fontsize=9.2, color="#1B4F72", linespacing=1.35)
    zone(ax, 7.6, 8.2, 6.8, 5.0, Z_CORE, "300", "OFFSET TRACKING")
    box(ax, 7.85, 8.45, 3.05, 1.25, Z_CORE[0], 310, "Floor unit", "F(t): 5th pct, 7 days")
    box(ax, 11.15, 8.45, 3.05, 1.25, Z_CORE[0], 320, "Departure", "d_j = A(t_j) - L_j")
    box(ax, 7.85, 10.05, 6.35, 1.05, Z_CORE[0], 330, "Anchor gap from earlier samples",
        "g = median_j [ F(t_j) - d_j ]   (floor above true background)")
    box(ax, 7.85, 11.35, 6.35, 1.2, Z_CORE[0], 340, "Correction",
        "A_c(t) = max(A(t) - (F(t) - g), 0)")
    arr(ax, (10.9, 9.07), (11.15, 9.07), color=Z_CORE[0])
    arr(ax, (12.7, 9.7), (12.7, 10.05), color=Z_CORE[0])
    arr(ax, (11.0, 11.1), (11.0, 11.35), color=Z_CORE[0])
    zone(ax, 15.4, 8.2, 6.0, 5.0, Z_RED, "400", "OUTPUT UNIT")
    box(ax, 15.65, 11.2, 5.5, 1.35, Z_RED[0], 410, "Corrected ammonium record", "every 15-minute reading")
    box(ax, 15.65, 9.8, 5.5, 1.15, Z_RED[0], 420, "Two-tier alarm", "watch: either reading; confirmed: both")
    box(ax, 15.65, 8.45, 5.5, 1.1, Z_RED[0], 430, "Offset in force", "F(t) - g, to the sonde controller")
    arr(ax, (6.6, 9.07), (7.85, 9.07), color=Z_IN[0], label="records", lpos=(7.22, 9.32))
    arr(ax, (14.2, 11.95), (15.65, 11.95), color=Z_CORE[0], label="A_c(t)", lpos=(14.92, 12.2))
    lane(ax, [(14.2, 11.6), (14.9, 11.6), (14.9, 10.4), (15.65, 10.4)], Z_CORE[0])
    lane(ax, [(14.2, 10.6), (14.6, 10.6), (14.6, 9.0), (15.65, 9.0)], Z_CORE[0])
    # field hardware
    ax.add_patch(Rectangle((0.35, 0.3), 21.3, 0.5, facecolor="#D6EAF8", edgecolor="#5DADE2",
                           lw=1.2, zorder=1))
    ax.text(11.0, 0.55, "RIVER   --->   flow   --->   raw-water intake downstream", ha="center", va="center",
            fontsize=9.6, color="#1B4F72", fontweight="bold", zorder=2)
    zone(ax, 0.6, 1.05, 13.8, 5.0, Z_PHY, "100", "IN-SITU WATER-QUALITY SONDE")
    box(ax, 0.85, 3.65, 3.1, 1.7, Z_PHY[0], 110, "Ammonium ISE", "NH4+ membrane,", "reference junction")
    box(ax, 4.2, 3.65, 2.9, 1.7, Z_PHY[0], 116, "Front end + ADC", "high-impedance", "input")
    box(ax, 7.35, 3.65, 3.3, 1.7, Z_PHY[0], 115, "Sonde controller", "15-min reading,", "applies F(t) - g")
    box(ax, 10.9, 3.65, 3.3, 1.7, Z_PHY[0], 117, "Cellular modem", "serial bus to", "link 130")
    box(ax, 0.85, 1.3, 4.6, 1.85, Z_PHY[0], 112, "Other sensors, wiper 114", "temperature, pH,", "conductivity")
    box(ax, 5.7, 1.3, 8.5, 1.85, Z_PHY[0], 118, "River water at the sonde",
        "ammonium falls back to a low background between pulses",
        "the ISE offset shifts at each service and drifts between them")
    arr(ax, (3.95, 4.5), (4.2, 4.5), color=Z_PHY[0])
    arr(ax, (7.1, 4.5), (7.35, 4.5), color=Z_PHY[0])
    arr(ax, (10.65, 4.5), (10.9, 4.5), color=Z_PHY[0])
    zone(ax, 15.4, 1.05, 6.0, 5.0, Z_PHY, "600", "SAMPLING, LABORATORY, INTAKE")
    box(ax, 15.6, 3.65, 2.7, 1.7, Z_PHY[0], 610, "Grab sample", "at the sonde")
    box(ax, 15.6, 1.3, 2.7, 1.85, Z_PHY[0], 620, "Laboratory", "ammoniacal N")
    box(ax, 18.5, 3.65, 2.7, 1.7, Z_PHY[0], 440, "Auto sampler", "relay-started", "(watch tier)")
    box(ax, 18.5, 1.3, 2.7, 1.85, Z_PHY[0], 450, "Intake interlock", "relay-switched", "(confirmed tier)")
    arr(ax, (16.95, 3.65), (16.95, 3.15), color=Z_PHY[0])
    ax.text(21.55, 7.0, "telemetry link 130", fontsize=9, color="#555", ha="right",
            va="center", fontstyle="italic")
    lane(ax, [(12.55, 5.35), (12.55, 6.95), (2.1, 6.95), (2.1, 8.5)], "#AF601A",
         label="A(t)", lpos=(7.1, 6.95))
    lane(ax, [(15.6, 2.2), (15.15, 2.2), (15.15, 7.35), (5.0, 7.35), (5.0, 8.5)], "#7D6608",
         label="laboratory result L", lpos=(10.4, 7.35))
    lane(ax, [(15.65, 8.75), (14.75, 8.75), (14.75, 6.3), (9.0, 6.3), (9.0, 5.35)], Z_RED[0],
         label="F(t) - g", lpos=(11.8, 6.3), ls="--")
    lane(ax, [(21.15, 10.4), (21.55, 10.4), (21.55, 5.6), (19.85, 5.6), (19.85, 5.35)], Z_RED[0],
         label="relays", lpos=(20.7, 5.6), ls="--")
    lane(ax, [(21.55, 5.6), (21.55, 2.2), (21.2, 2.2)], Z_RED[0], ls="--")
    save(fig, "fig01.png")


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
    pbox(ax, X, 17.85, W, 1.75, "S1  Receive the 15-minute ammonium reading A(t)\n"
         "of ISE 110 from sonde 100", Z_IN, fs=10)
    pbox(ax, X, 15.6, W, 1.3, "S2  Receive laboratory results L_j of grab samples\n"
         "taken at the sonde; match A(t_j) at each sampling time", Z_IN, fs=10)
    steps = [(13.75, "S3  Floor F(t): 5th percentile of A over the 7 days before t\n"
                     "(true background plus the calibration offset in force)"),
             (12.0, "S4  Anchor gap g = median over the most recent samples of\n"
                    "F(t_j) - (A(t_j) - L_j): height of the floor above background"),
             (10.25, "S5  Correct every reading:\n"
                     "A_c(t) = max(A(t) - (F(t) - g), 0)")]
    for y, t in steps:
        pbox(ax, X, y, W, 1.25, t, Z_CORE, fs=10)
    arr(ax, (X, 16.95), (X, 16.28), color="#333")
    arr(ax, (X, 14.93), (X, 14.4), color="#333")
    arr(ax, (X, 13.1), (X, 12.65), color="#333")
    arr(ax, (X, 11.35), (X, 10.9), color="#333")
    diamond(ax, X, 8.15, 4.6, 1.85, "A_c(t) or A(t) - d_last\nabove the threshold?", Z_PROC, fs=10)
    arr(ax, (X, 9.6), (X, 9.1), color="#333")
    pbox(ax, 3.45, 5.3, 4.0, 1.9, "S6a  Watch alarm 420:\nrelay starts sampler 440;\nboth above: confirmed,\nintake interlock 450", Z_RED, fs=9.4)
    pbox(ax, 8.05, 5.3, 4.0, 1.9, "S6b  No alarm;\nrelays stay open", Z_RED, fs=9.8)
    poly(ax, [(X - 2.3, 8.15), (3.45, 8.15), (3.45, 6.3)], color=YES_C, label="YES",
         lpos=(3.05, 7.3), lcolor=YES_C)
    poly(ax, [(X + 2.3, 8.15), (8.05, 8.15), (8.05, 6.3)], color=NO_C, label="NO",
         lpos=(8.45, 7.3), lcolor=NO_C)
    pbox(ax, X, 2.3, W, 1.55, "S7  Write A_c(t) to the corrected record 410; send the\n"
         "offset F(t) - g over link 130 to sonde controller 115,\nwhich reports the corrected reading on site", Z_RED, fs=10)
    arr(ax, (3.45, 4.3), (4.4, 3.12), color="#333")
    arr(ax, (8.05, 4.3), (7.1, 3.12), color="#333")
    HX, HW = 12.85, 3.3
    for y0, y1 in ((14.75, 19.2), (1.05, 3.45)):
        ax.add_patch(FancyBboxPatch((HX - HW / 2 - 0.2, y0), HW + 0.4, y1 - y0,
                                    boxstyle="round,pad=0.05", facecolor="#FEF9E7",
                                    edgecolor=Z_PHY[0], linewidth=1.5, zorder=1))
    ax.text(HX, 18.95, "FIELD HARDWARE", ha="center", va="center", fontsize=10.5,
            fontweight="bold", color=Z_PHY[0])
    pbox(ax, HX, 18.25, HW, 0.85, "Ammonium ISE 110", Z_PHY, fs=9.8)
    pbox(ax, HX, 17.15, HW, 0.95, "Sonde controller 115\n15-minute log", Z_PHY, fs=9.6)
    pbox(ax, HX, 15.6, HW, 0.95, "Grab sample 610,\nlaboratory 620", Z_PHY, fs=9.6)
    pbox(ax, HX, 2.8, HW, 0.85, "Sonde controller 115\napplies the offset", Z_PHY, fs=9.4)
    pbox(ax, HX, 1.65, HW, 0.85, "Sampler 440,\nintake interlock 450", Z_PHY, fs=9.4)
    arr(ax, (HX - HW / 2, 18.25), (R, 18.25), color=Z_PHY[0], label="A(t)", lpos=(10.6, 18.47))
    arr(ax, (HX - HW / 2, 17.15), (R, 17.15), color=Z_PHY[0], label="record", lpos=(10.6, 17.37))
    arr(ax, (HX - HW / 2, 15.6), (R, 15.6), color="#7D6608", label="L_j", lpos=(10.6, 15.82))
    arr(ax, (R, 2.8), (HX - HW / 2, 2.8), color=Z_RED[0], ls="--", label="F - g", lpos=(10.6, 3.02))
    arr(ax, (R, 1.85), (HX - HW / 2, 1.65), color=Z_RED[0], ls="--", label="relays", lpos=(10.6, 1.45))
    ax.text(12.85, 14.35, "all signals over telemetry link 130", ha="center", fontsize=9,
            style="italic", color="#666")
    ax.text(X, 0.75, "F every 15 minutes; g refreshed when a laboratory result arrives", ha="center",
            fontsize=10, style="italic", color="#444")
    save(fig, "fig02.png")


if __name__ == "__main__":
    fig01()
    fig02()
