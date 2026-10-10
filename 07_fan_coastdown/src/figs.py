"""Redrawn schematic figures for the fan coast-down gas-hazard IDF-B (Figures 1, 3, 4, 12, 14)."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figs")
os.makedirs(OUT, exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"

INK = "#1f2a36"
GREY = "#566573"
C_SENSE = ("#2c5d9e", "#edf3fb")
C_PROC = ("#6c4a9e", "#f3eefa")
C_DEC = ("#24785a", "#ebf6f0")
C_ACT = ("#a8741a", "#fbf3e4")
C_RED = ("#b03a2e", "#fbecea")
C_GREY = ("#5d6d7e", "#f2f4f6")


def box(ax, x, y, w, h, col, text, fs=10.5, bold=False, lw=1.6, r=0.12):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=%g" % r,
                                fc=col[1], ec=col[0], lw=lw, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
            fontweight="bold" if bold else "normal", zorder=4, linespacing=1.35)


def zone(ax, x, y, w, h, col, title):
    ax.add_patch(Rectangle((x, y), w, h, fc=col[1], ec=col[0], lw=1.0, alpha=0.45, zorder=1))
    ax.text(x + 0.15, y + h - 0.12, title, ha="left", va="top", fontsize=10.5,
            fontweight="bold", color=col[0], zorder=2)


def arr(ax, p, q, color=GREY, lw=1.5, ls="-", label=None, lpos=0.5, loff=(0, 0.12), lfs=8.8,
        ha="center"):
    ax.annotate("", xy=q, xytext=p, zorder=5,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, ls=ls,
                                shrinkA=0, shrinkB=0, mutation_scale=13))
    if label:
        lx = p[0] + (q[0] - p[0]) * lpos + loff[0]
        ly = p[1] + (q[1] - p[1]) * lpos + loff[1]
        ax.text(lx, ly, label, ha=ha, va="bottom", fontsize=lfs, color=color, zorder=6,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def line(ax, pts, color=GREY, lw=1.5, ls="-"):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=5, solid_capstyle="butt")


def poly_arrow(ax, pts, color=GREY, lw=1.5, ls="-", label=None, li=0, loff=(0, 0.1), lfs=8.8):
    line(ax, pts[:-1], color, lw, ls)
    arr(ax, pts[-2], pts[-1], color, lw, ls)
    if label:
        (x0, y0), (x1, y1) = pts[li], pts[li + 1]
        ax.text((x0 + x1) / 2 + loff[0], (y0 + y1) / 2 + loff[1], label, ha="center", va="bottom",
                fontsize=lfs, color=color, zorder=6,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def canvas(w, h, xmax, ymax):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches="tight", pad_inches=0.08,
                facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- Figure 1: architecture
def fig01():
    fig, ax = canvas(15, 10.6, 15, 10.6)
    W, H = 2.35, 0.95
    xs = [0.75, 3.55, 6.35, 9.15, 11.95]
    cx = [x + W / 2 for x in xs]
    zone(ax, 0.45, 8.55, 14.2, 1.95, C_SENSE, "SENSING LAYER (100)")
    zone(ax, 0.45, 5.35, 14.2, 2.85, C_PROC, "PROCESSING LAYER (200)")
    zone(ax, 0.45, 2.6, 14.2, 2.4, C_DEC, "DECISION LAYER (300)")
    zone(ax, 0.45, 0.15, 14.2, 2.1, C_ACT, "ACTUATION AND RECORDING LAYER (400, 500)")
    # ESP32 bracket
    ax.plot([14.85, 14.95, 14.95, 14.85], [7.95, 7.95, 2.8, 2.8], color=INK, lw=1.3)
    ax.text(15.05, 5.37, "110 ESP32 microcontroller\n(hosts layers 200 and 300)", rotation=90,
            ha="left", va="center", fontsize=10, color=INK)

    ys = 8.75
    sense = ["101 Axial fan\n(sensing element\nand actuator)", "102 Tachometer\n(edge per blade\npassage)",
             "103 Fan supply-\nvoltage monitor", "104 BME280\nT, RH, P", "105 MQ-series\nchemoresistor"]
    for x, t in zip(xs, sense):
        box(ax, x, ys, W, 1.25, C_SENSE, t, fs=10)
    arr(ax, (xs[0] + W, ys + 0.62), (xs[1], ys + 0.62), label="rotor", loff=(0, 0.04), lfs=8.5)

    # processing row: 201 202 203 | 204 205  (two rows to keep arrows orthogonal)
    yp = 6.95
    proc = [(xs[0], "201 Revolution timer\nT_k, RPM_k, ω_k, t_k"),
            (xs[1], "202 Coast-down fitter\nfree: a0, a1, a2\nlocked a1: a0, a2"),
            (xs[2], "203 Density estimator\nρ̂ = ā2 / K"),
            (xs[3], "204 Thermodynamic\nreference ρ_ref(T, RH, P)"),
            (xs[4], "205 MQ normaliser\ns = −ln(Rs / R0,eff)")]
    for x, t in proc:
        box(ax, x, yp - 0.5, W, 1.0 if "202" not in t else 1.0, C_PROC, t, fs=9.6)
    # sensing -> processing
    poly_arrow(ax, [(cx[1] - 0.4, ys), (cx[1] - 0.4, 8.42), (cx[0], 8.42), (cx[0], yp + 0.5)],
               label="edge times", li=1, loff=(0, 0.03), lfs=8.3)
    poly_arrow(ax, [(cx[2], ys), (cx[2], 8.3), (cx[1] + 0.55, 8.3), (cx[1] + 0.55, yp + 0.5)],
               label="drive-off check", li=1, loff=(0, 0.03), lfs=8.3)
    arr(ax, (cx[3], ys), (cx[3], yp + 0.5))
    arr(ax, (cx[4], ys), (cx[4], yp + 0.5))
    poly_arrow(ax, [(cx[3] + 0.6, ys), (cx[3] + 0.6, 8.36), (cx[4] - 0.6, 8.36), (cx[4] - 0.6, yp + 0.5)],
               label="T, RH", li=1, loff=(0, 0.03), lfs=8.3)
    arr(ax, (xs[0] + W, yp), (xs[1], yp), label="(t_k, ω_k)", loff=(0, 0.05), lfs=8.3)
    arr(ax, (xs[1] + W, yp), (xs[2], yp), label="ā2", loff=(0, 0.05), lfs=8.3)

    # decision row
    yd = 3.55
    dec = [(xs[0], "302 Friction monitor\nand recommissioning\n(a0, a1 vs commissioning)", C_DEC),
           (xs[2] - 0.4, "301 Residual former\nr = 100(ρ̂/ρ_ref − 1)\nz = r / σ_r", C_DEC),
           (xs[3] + 0.2, "303 Two-axis classifier\n(z, s) → hazard class", C_DEC),
           (xs[4] + 0.2, "304 Mitigation\nselector (Table 8)", C_DEC)]
    pos = {}
    for x, t, c in dec:
        w = W if "304" not in t else W - 0.2
        box(ax, x, yd - 0.55, w, 1.1, c, t, fs=9.6)
        pos[t[:3]] = (x, w)
    # 202 -> 302 (a0, a1)
    poly_arrow(ax, [(cx[1] - 0.5, yp - 0.5), (cx[1] - 0.5, 5.6), (cx[0], 5.6), (cx[0], yd + 0.55)],
               label="a0, a1 (free fit)", li=1, loff=(0.3, -0.3), lfs=8.3)
    # 203 -> 301, 204 -> 301
    x301, w301 = pos["301"]
    arr(ax, (cx[2], yp - 0.5), (cx[2], yd + 0.55), label="ρ̂", lpos=0.25, loff=(0.18, 0), lfs=9)
    poly_arrow(ax, [(cx[3], yp - 0.5), (cx[3], 5.2), (x301 + w301 - 0.25, 5.2), (x301 + w301 - 0.25, yd + 0.55)],
               label="ρ_ref", li=1, loff=(0, 0.03), lfs=9)
    # 205 -> 303
    x303, w303 = pos["303"]
    poly_arrow(ax, [(cx[4], yp - 0.5), (cx[4], 4.75), (x303 + w303 - 0.4, 4.75), (x303 + w303 - 0.4, yd + 0.55)],
               label="s", li=1, loff=(0, 0.03), lfs=9)
    # 301 -> 303
    arr(ax, (x301 + w301, yd), (x303, yd), label="z", loff=(0, 0.05), lfs=9)
    # 302 -> 301 gate (withhold)
    x302, w302 = pos["302"]
    arr(ax, (x302 + w302, yd), (x301, yd), color=C_RED[0], label="withhold z\nwhen wear flagged",
        loff=(0, 0.05), lfs=8.3)
    # 302 -> 202/203 recommission (dashed, up)
    poly_arrow(ax, [(cx[0] - 0.6, yd + 0.55), (cx[0] - 0.6, 6.12), (xs[1] + 0.3, 6.12), (xs[1] + 0.3, yp - 0.5)],
               color=C_RED[0], ls="--", label="re-lock a1, new K", li=1, loff=(0, -0.33), lfs=8.3)
    # 303 -> 304
    x304, w304 = pos["304"]
    arr(ax, (x303 + w303, yd), (x304, yd), label="class", loff=(0, 0.05), lfs=8.5)

    # actuation row
    ya = 0.4
    act = ["401 Fan drive\n(spin-up, cut-off,\ninhibit, 60 / 100 %)", "402 Vent servo\n(high / low path,\n0°, 45°, 90°)",
           "403 Buzzer and\nred / green LEDs", "404 Local display\n(16 × 2)", "501 Log and\ninterface"]
    for x, t in zip(xs, act):
        box(ax, x, ya, W, 1.25, C_ACT, t, fs=9.6)
    # 304 -> 401..404 through a bus
    bus_y = 2.05
    line(ax, [(x304 + w304 / 2, yd - 0.55), (x304 + w304 / 2, 2.35)], color=C_ACT[0])
    line(ax, [(cx[0], 2.35), (x304 + w304 / 2, 2.35)], color=C_ACT[0])
    for c in cx[:4]:
        arr(ax, (c, 2.35), (c, ya + 1.25), color=C_ACT[0])
    ax.text(cx[2] + 1.4, 2.4, "class-specific action", fontsize=8.5, color=C_ACT[0], va="bottom",
            ha="center")
    # every unit -> 501 (record)
    poly_arrow(ax, [(x304 + w304 - 0.3, yd - 0.55), (x304 + w304 - 0.3, 2.0), (cx[4] + 0.6, 2.0), (cx[4] + 0.6, ya + 1.25)],
               color=GREY, ls=":", label="record", li=0, loff=(0.38, -0.2), lfs=8.3)
    # 401 -> 101 drive (dashed, left margin)
    poly_arrow(ax, [(xs[0], ya + 0.62), (0.25, ya + 0.62), (0.25, ys + 0.62), (xs[0], ys + 0.62)],
               color=C_RED[0], ls="--")
    ax.text(0.12, 5.0, "fan supply: spin-up, cut-off for coast-down, held off when inhibited",
            rotation=90, ha="center", va="center", fontsize=8.8, color=C_RED[0])
    save(fig, "fig01.png")


# ---------------------------------------------------------------- Figure 3: signal pathway
def fig03():
    fig, ax = canvas(14, 8.2, 14, 8.2)
    left = [("101 Axial fan rotor\n(sensing element)", None),
            ("102 Optical tachometer\nor fan Hall output", "edge pulses"),
            ("103 Fan supply-\nvoltage divider", "analogue"),
            ("104 BME280\nT, RH, P", "digital (I²C)"),
            ("105 MQ-series element\nheater + load resistor R_L", "analogue V_out")]
    per = [None, "Capture timer (MCPWM)\n/ pulse counter (PCNT)", "ADC channel", "I²C bus", "ADC channel"]
    right = [("401 Motor-driver stage\n(PWM drive, cut-off, inhibit)", "PWM"),
             ("402 Vent servo(s)\n(high / low path)", "PWM"),
             ("403 Buzzer and\nred / green LEDs", "GPIO"),
             ("404 16 × 2 character\ndisplay", "I²C"),
             ("501 Log and\ninterface", "serial / Wi-Fi")]
    ys = [6.55, 5.15, 3.75, 2.35, 0.95]
    bw, bh = 3.4, 1.0
    # controller
    ax.add_patch(FancyBboxPatch((5.0, 0.55), 3.9, 7.0, boxstyle="round,pad=0,rounding_size=0.15",
                                fc="white", ec=INK, lw=2.2, zorder=2))
    ax.text(6.95, 7.25, "110 ESP32 microcontroller", ha="center", va="center", fontsize=11.5,
            fontweight="bold", color=INK)
    for i, ((t, lab), y) in enumerate(zip(left, ys)):
        box(ax, 0.3, y, bw, bh, C_SENSE, t, fs=10)
        if per[i]:
            box(ax, 5.3, y + 0.1, 3.3, 0.8, C_GREY, per[i], fs=9.6)
            arr(ax, (0.3 + bw, y + bh / 2), (5.3, y + 0.5), label=lab, loff=(0, 0.06), lfs=8.6)
    arr(ax, (0.3 + bw / 2, ys[0]), (0.3 + bw / 2, ys[1] + bh), label=" blade passages", lpos=0.5,
        loff=(0.95, -0.12), lfs=8.6)
    box(ax, 5.3, 6.4, 3.3, 0.6, C_PROC, "Layers 200–300: timing, fit, ρ̂, ρ_ref,\nr, z, s, class, action",
        fs=8.6)
    for (t, lab), y in zip(right, ys):
        box(ax, 10.3, y, bw, bh, C_ACT, t, fs=10)
        arr(ax, (8.9, y + bh / 2), (10.3, y + bh / 2), label=lab, loff=(0, 0.06), lfs=8.6)
    poly_arrow(ax, [(12.0, ys[0] + bh), (12.0, 7.9), (2.0, 7.9), (2.0, ys[0] + bh)], color=C_RED[0],
               ls="--", label="fan supply: energised for spin-up, removed at cut-off, held off when inhibited",
               li=1, loff=(0, 0.04), lfs=9)
    save(fig, "fig03.png")


# ---------------------------------------------------------------- Figure 4: pipeline
def fig04():
    fig, ax = canvas(15, 9.7, 15, 9.7)
    bw, bh = 2.45, 1.15
    xs = [0.3, 3.25, 6.2, 9.15, 12.1]
    rows = [7.45, 4.55, 1.65]
    steps = [
        ["S1 Initialise; load K,\na1,lock, a0,ref, σa0,\nσa1, R0, σr", "S2 Read BME280\nT, RH, P", "S3 Read MQ\nRs = RL(Vc/Vout − 1)",
         "S4 Spin up fan\nand let it stabilise", "S5 Remove drive\n(coast-down starts)"],
        ["S10 Repeat S4–S9\nthree times;\naverage a2 → ā2", "S9 Free fit: a0, a1, a2;\nrefit with a1 locked\n→ a0, a2",
         "S8 Keep revolutions\nwith t_k ≥ 0.3 s", "S7 RPM = 60 / T_k\nω = 2π / T_k", "S6 Time each\nrevolution T_k"],
        ["S11 ρ̂ = ā2 / K", "S12 ρ_ref(T, RH, P);\nr, z = r / σr", "S13 Friction check\n(a0, a1 vs\ncommissioning)",
         "S14 Classify (z, s)\n(Equation 14)", "S15 Apply action,\nrecord cycle, repeat"]]
    titles = ["Acquisition", "Coast-down processing", "Compensation, fusion and decision"]
    for r, (y, row, ttl) in enumerate(zip(rows, steps, titles)):
        ax.text(7.5, y + bh + 0.3, ttl, ha="center", va="bottom", fontsize=11.5, fontweight="bold",
                color=GREY)
        for x, t in zip(xs, row):
            col = C_SENSE if r == 0 else (C_PROC if r == 1 else C_DEC)
            box(ax, x, y, bw, bh, col, t, fs=9.6)
        for i in range(4):
            if r == 1:
                arr(ax, (xs[i + 1], y + bh / 2), (xs[i] + bw, y + bh / 2))
            else:
                arr(ax, (xs[i] + bw, y + bh / 2), (xs[i + 1], y + bh / 2))
    arr(ax, (xs[4] + bw / 2, rows[0]), (xs[4] + bw / 2, rows[1] + bh))
    arr(ax, (xs[0] + bw / 2, rows[1]), (xs[0] + bw / 2, rows[2] + bh))
    # repeat loop S10 -> S4
    poly_arrow(ax, [(xs[0] + 0.5, rows[1] + bh), (xs[0] + 0.5, 6.75), (xs[3] + bw / 2, 6.75), (xs[3] + bw / 2, rows[0])],
               color=C_PROC[0], ls="--", label="repeat until three coast-downs", li=1, loff=(0, 0.03), lfs=8.6)
    # S13 wear branch
    box(ax, xs[2] - 0.15, 0.05, bw + 0.3, 0.8, C_RED, "wear: withhold z, acquire 4 clean\ncoast-downs, re-lock a1, new K", fs=8.6)
    arr(ax, (xs[2] + bw / 2, rows[2]), (xs[2] + bw / 2, 0.85), color=C_RED[0], label="wear", lpos=0.45,
        loff=(0.33, -0.1), lfs=8.6)
    # S15 loops back to S2
    poly_arrow(ax, [(xs[4] + bw, rows[2] + bh / 2), (14.85, rows[2] + bh / 2), (14.85, 9.5), (xs[1] + bw / 2, 9.5),
                    (xs[1] + bw / 2, rows[0] + bh)], color=GREY, ls="--", label="next cycle", li=2, loff=(0, 0.03), lfs=8.6)
    save(fig, "fig04.png")


# ---------------------------------------------------------------- Figure 12: decision logic
def fig12():
    fig, ax = canvas(15, 10.2, 15, 10.2)
    box(ax, 4.6, 9.0, 5.8, 0.95, C_SENSE, "Inputs: z (density residual), s (MQ response),\nwear state from 302", fs=10.2, bold=True)
    box(ax, 5.3, 7.45, 4.4, 0.95, C_PROC, "Density channel valid?\n(drive-off check, fit quality, no wear flag)", fs=9.8)
    arr(ax, (7.5, 9.0), (7.5, 8.4))
    box(ax, 0.3, 7.45, 3.9, 0.95, C_RED, "No: evaluate with z = 0;\nrecommission (4 clean coast-downs)", fs=9.4)
    arr(ax, (5.3, 7.92), (4.2, 7.92), label="no", loff=(0, 0.04), lfs=9)
    poly_arrow(ax, [(2.25, 7.45), (2.25, 6.7), (5.3, 6.7)], color=C_RED[0], ls="--")
    box(ax, 5.3, 5.95, 4.4, 0.95, C_PROC, "s ≥ θ ?\n(reducing or combustible gas indicated)", fs=9.8)
    arr(ax, (7.5, 7.45), (7.5, 6.9), label="yes", lpos=0.4, loff=(0.25, -0.08), lfs=9)
    # left branch: s < theta
    box(ax, 1.6, 4.3, 3.2, 0.9, C_PROC, "|z| ≥ 3 ?", fs=10)
    poly_arrow(ax, [(5.3, 6.15), (3.2, 6.15), (3.2, 5.2)], label="no", li=0, loff=(0.5, 0.03), lfs=9)
    # right branch: s >= theta
    box(ax, 10.2, 4.3, 3.2, 0.9, C_PROC, "sign and size of z", fs=10)
    poly_arrow(ax, [(9.7, 6.42), (11.8, 6.42), (11.8, 5.2)], label="yes", li=0, loff=(0.5, 0.03), lfs=9)
    # leaves
    W, H, y = 2.75, 1.45, 1.95
    leaves = [(0.15, C_GREY, "CLEAN\nfan normal duty,\nvent 0°"),
              (3.05, C_DEC, "ASPHYXIANT\nfan ON 100 %,\nvent 90°, alarm"),
              (6.15, C_PROC, "LIGHT_COMB\nfan NOT energised,\nHIGH vent, alarm"),
              (9.05, C_SENSE, "HEAVY_COMB\nfan NOT energised,\nLOW vent, alarm"),
              (11.95, C_ACT, "s ≥ θ_esc ?")]
    for x, c, t in leaves[:4]:
        box(ax, x, y, W, H, c, t, fs=9.6)
    box(ax, 11.95, y + 0.25, W, 0.95, C_ACT, "s ≥ θ_esc ?", fs=10)
    poly_arrow(ax, [(2.4, 4.3), (2.4, 3.8), (1.5, 3.8), (1.5, y + H)], label="no", li=1, loff=(0, 0.03), lfs=9)
    poly_arrow(ax, [(3.4, 4.3), (3.4, 3.8), (4.4, 3.8), (4.4, y + H)], label="yes", li=1, loff=(0, 0.03), lfs=9)
    poly_arrow(ax, [(10.9, 4.3), (10.9, 3.75), (7.5, 3.75), (7.5, y + H)], label="z ≤ −3", li=1, loff=(0, 0.03), lfs=9)
    arr(ax, (11.4, 4.3), (11.4, y + H - 0.0), label="z ≥ +3", lpos=0.45, loff=(-0.05, -0.1), lfs=9)
    poly_arrow(ax, [(12.4, 4.3), (12.4, 3.75), (13.3, 3.75), (13.3, y + 0.25 + 0.95)], label="|z| < 3", li=1,
               loff=(0.15, 0.03), lfs=9)
    box(ax, 12.6, 0.05, 2.25, 1.25, C_ACT, "VOC_NUISANCE\nfan 60 %, vent 45°,\nnotify", fs=9.4)
    box(ax, 6.15, 0.05, 5.7, 1.25, C_RED, "ESCALATED: unresolved strong response\ntreated as HEAVY_COMB: fan NOT energised,\nLOW vent, alarm", fs=9.4)
    arr(ax, (13.72, y + 0.25), (13.72, 1.3), label="no", lpos=0.5, loff=(0.25, -0.1), lfs=9)
    poly_arrow(ax, [(12.25, y + 0.25), (12.25, 1.62), (11.4, 1.62), (11.4, 1.3)], color=C_RED[0], label="yes", li=0,
               loff=(0.3, -0.1), lfs=9)
    ax.text(0.2, 0.55, "Measurement spin-ups are suspended\nwhile a combustible class is declared.",
            fontsize=9.2, color=C_RED[0], ha="left", va="center", style="italic")
    save(fig, "fig12.png")


# ---------------------------------------------------------------- Figure 14: monitoring interface
def coast(a0=1.5626, a1=0.014370, a2=1.4837e-3, rpm0=2520.0, rpm_end=160.0):
    w = rpm0 * 2 * np.pi / 60
    t, dt, ts, ws = 0.0, 0.001, [0.0], [w]
    while w > rpm_end * 2 * np.pi / 60:
        w -= (a0 + a1 * w + a2 * w * w) * dt
        t += dt
        ts.append(t)
        ws.append(w)
    return np.array(ts), np.array(ws) * 60 / (2 * np.pi)


def fig14():
    fig = plt.figure(figsize=(15, 9.2))
    fig.patch.set_facecolor("white")
    bg = fig.add_axes([0, 0, 1, 1])
    bg.axis("off")
    bg.add_patch(Rectangle((0, 0.925), 1, 0.075, fc="#1f3b5c", ec="none", transform=bg.transAxes))
    bg.text(0.015, 0.962, "Gas-hazard unit 110  |  monitoring interface (501)", color="white", fontsize=15,
            fontweight="bold", va="center", transform=bg.transAxes)
    bg.text(0.985, 0.962, "density channel: VALID   wear flag: none   cycle: T0011", color="white",
            fontsize=11, va="center", ha="right", transform=bg.transAxes)

    def tile(x, y, w, h, title, value, sub, col):
        bg.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.008", fc=col[1],
                                    ec=col[0], lw=1.3, transform=bg.transAxes))
        bg.text(x + 0.01, y + h - 0.025, title, fontsize=10, color=GREY, va="top", transform=bg.transAxes)
        bg.text(x + 0.01, y + h * 0.42, value, fontsize=17, color=INK, fontweight="bold", va="center",
                transform=bg.transAxes)
        bg.text(x + 0.01, y + 0.018, sub, fontsize=9, color=GREY, va="bottom", transform=bg.transAxes)

    tw, th, ty = 0.152, 0.13, 0.775
    tiles = [("Temperature (104)", "23.23 °C", "BME280, 1 Hz", C_SENSE),
             ("Relative humidity (104)", "41.4 %", "BME280, 1 Hz", C_SENSE),
             ("Pressure (104)", "1010.3 hPa", "BME280, 1 Hz", C_SENSE),
             ("MQ resistance (105)", "21.45 kΩ", "s = −0.010", C_SENSE),
             ("Hazard class (303)", "CLEAN", "|z| < 3, s < θ", C_DEC),
             ("Action (304)", "normal duty", "vent 0°, no alarm", C_DEC)]
    for i, (a, b, c, col) in enumerate(tiles):
        tile(0.012 + i * (tw + 0.012), ty, tw, th, a, b, c, col)

    ax = fig.add_axes([0.055, 0.1, 0.44, 0.58])
    t, rpm = coast()
    ax.plot(t, rpm, color=C_RED[0], lw=2.2, label="fitted model, dω/dt = −(a0 + a1ω + a2ω²)")
    ax.axvspan(0, 0.3, color=C_RED[1])
    ax.set_xlabel("Time since cut-off (s)")
    ax.set_ylabel("Fan speed (RPM)")
    ax.set_title("Latest coast-down (202), 3 of 3 accepted", fontsize=11.5, loc="left")
    ax.grid(color="#e3e7ec")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=9.5)
    ax.text(0.98, 0.55, "a0 = 1.5626 rad/s²\na1 = 0.014370 s⁻¹\na2 = 1.4837 × 10⁻³ rad⁻¹\nRMSE 0.0773 rad/s",
            transform=ax.transAxes, ha="right", fontsize=9.6, bbox=dict(fc="white", ec="#c9d1da"))

    x0 = 0.53
    bg.add_patch(FancyBboxPatch((x0, 0.38), 0.455, 0.355, boxstyle="round,pad=0,rounding_size=0.008", fc="white",
                                ec="#c9d1da", lw=1.2, transform=bg.transAxes))
    bg.text(x0 + 0.012, 0.715, "Density channel (203, 204, 301)", fontsize=11.5, color=INK, va="top",
            transform=bg.transAxes)
    rows = [("ā2 (mean of 3 coast-downs)", "1.4955 × 10⁻³ rad⁻¹"),
            ("ρ̂ = ā2 / K", "1.18214 kg/m³"),
            ("ρ_ref (T, RH, P)", "1.18225 kg/m³"),
            ("r = 100(ρ̂ / ρ_ref − 1)", "−0.009 %"),
            ("z = r / σ_r", "−0.06  (threshold ±3)"),
            ("Friction a0, a1 vs commissioning", "within k_w σ")]
    for i, (k, v) in enumerate(rows):
        yy = 0.66 - i * 0.045
        bg.text(x0 + 0.015, yy, k, fontsize=10.5, color=GREY, va="center", transform=bg.transAxes)
        bg.text(x0 + 0.44, yy, v, fontsize=10.5, color=INK, va="center", ha="right", fontweight="bold",
                transform=bg.transAxes)

    bg.add_patch(FancyBboxPatch((x0, 0.03), 0.455, 0.325, boxstyle="round,pad=0,rounding_size=0.008", fc="white",
                                ec="#c9d1da", lw=1.2, transform=bg.transAxes))
    bg.text(x0 + 0.012, 0.335, "Event history (501)", fontsize=11.5, color=INK, va="top", transform=bg.transAxes)
    ev = [("T0059", "z +15.11, s −0.014", "ASPHYXIANT", "fan 100 %, vent 90°, alarm", C_DEC[0]),
          ("T0077", "z −13.80, s −0.040", "ASPHYXIANT", "fan 100 %, vent 90°, alarm", C_DEC[0]),
          ("T0119", "z −7.15, s +1.696", "LIGHT_COMB", "fan off, high vent, alarm", C_RED[0]),
          ("T0137", "z +3.20, s +2.073", "HEAVY_COMB", "fan off, low vent, alarm", C_RED[0]),
          ("T0095", "z −1.10, s +0.966", "ESCALATED", "fan off, low vent, alarm", C_RED[0]),
          ("T0011", "z −0.06, s −0.010", "CLEAN", "normal duty, vent 0°", GREY)]
    for i, (a, b, c, d, col) in enumerate(ev):
        yy = 0.29 - i * 0.043
        bg.text(x0 + 0.015, yy, a, fontsize=9.8, color=GREY, va="center", transform=bg.transAxes)
        bg.text(x0 + 0.065, yy, b, fontsize=9.8, color=INK, va="center", transform=bg.transAxes)
        bg.text(x0 + 0.215, yy, c, fontsize=9.8, color=col, fontweight="bold", va="center", transform=bg.transAxes)
        bg.text(x0 + 0.315, yy, d, fontsize=9.2, color=GREY, va="center", transform=bg.transAxes)
    save(fig, "fig14.png")


if __name__ == "__main__":
    fig01()
    fig03()
    fig04()
    fig12()
    fig14()
