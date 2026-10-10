"""Figures for the IDF-B on drain-onset recalibration of substrate water-content sensors.

Drawing helpers (zones with header strips, sub-boxes with italic numerals, labelled arrows, flowchart
boxes and diamonds, 2 x 2 data panels labelled (a)-(d)) are imported unchanged from the patent 05
generator, as in patent 06. Data figures read results/*.json or recompute from the cached AGC data;
no measured value is typed in. ASCII labels only.

    python src/figs.py            all figures
    python src/figs.py 3 4        only those
"""
import importlib.util
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
_spec = importlib.util.spec_from_file_location(
    "p05_make_figs", r"C:\adi\patents\05_length_invariance\src\make_figs.py")
P5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P5)
import agc                                                           # noqa: E402
from pulse_gain import pulse_rises                                   # noqa: E402
from offset_anchor import daily_plateau                              # noqa: E402
import rolling_anchor as RA                                          # noqa: E402

zone, sub, arr, poly, pbox, diamond, panel, tidy, depbox = (
    P5.zone, P5.sub, P5.arr, P5.poly, P5.pbox, P5.diamond, P5.panel, P5.tidy, P5.depbox)
Z_IN, Z_CORE, Z_RED, Z_PHY, Z_PROC, Z_OUT, DARK = (
    P5.Z_IN, P5.Z_CORE, P5.Z_RED, P5.Z_PHY, P5.Z_PROC, P5.Z_OUT, P5.DARK)
YES_C, NO_C, C = P5.YES_C, P5.NO_C, P5.C
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "patent", "figures")
SHORT = {"Reference": "Ref", "AICU": "AICU", "Automatoes": "Autom.", "Digilog": "Digilog",
         "IUACAAS": "IUACAAS", "TheAutomators": "TheAut."}


def load(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return json.load(fh)


def save(fig, name, dpi, note):
    fig.savefig(os.path.join(OUT, name), dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("%s  %s" % (name, note))


# ---------------------------------------------------------------- Figure 1
def fig01():
    """Architecture: irrigation section hardware (bottom), processing system (top). Right-angle arrows only."""
    fig, ax = plt.subplots(figsize=(22, 13.6))
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 13.6)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.35, 7.6), 21.3, 5.8, boxstyle="round,pad=0.05", facecolor="none",
                                edgecolor="#7F8C8D", linewidth=1.4, linestyle=(0, (6, 4)), zorder=1))
    ax.text(0.55, 13.12, "DATA-PROCESSING SYSTEM  900  (climate / irrigation computer)", fontsize=10.5,
            fontweight="bold", color="#566573", ha="left", va="center")
    # 200 signal input: two boxes side by side
    zone(ax, 0.6, 7.8, 6.0, 5.0, Z_IN, "200", "SIGNAL INPUT")
    sub(ax, 0.85, 8.3, 2.6, 2.6, Z_IN[0], 210, "WC readings", "sensors 110, 120", "every 5 min")
    sub(ax, 3.75, 8.3, 2.6, 2.6, Z_IN[0], 220, "Pulse log", "from meter 530", "L/m2 per pulse")
    # 300 recalibration
    zone(ax, 7.6, 7.8, 6.8, 5.0, Z_CORE, "300", "DRAIN-ONSET RECALIBRATION")
    sub(ax, 7.85, 11.0, 3.05, 1.15, Z_CORE[0], 310, "Pulse response", "rise of WC per pulse")
    sub(ax, 11.15, 11.0, 3.05, 1.15, Z_CORE[0], 320, "Drain onset", "rise < 0.3 x morning rise")
    sub(ax, 7.85, 9.55, 3.05, 1.15, Z_CORE[0], 340, "Common scale", "optional: WC* = P* - D")
    sub(ax, 11.15, 9.55, 3.05, 1.15, Z_CORE[0], 330, "Rolling reference", "median plateau, past 14 d")
    sub(ax, 7.85, 8.05, 6.35, 1.15, Z_CORE[0], 350, "Drain deficit",
        "D = P_s(d) - WC  (gain only if two routes agree)")
    arr(ax, (10.9, 11.57), (11.15, 11.57), color=Z_CORE[0])
    arr(ax, (12.68, 11.0), (12.68, 10.7), color=Z_CORE[0])
    arr(ax, (12.68, 9.55), (12.68, 9.2), color=Z_CORE[0])
    arr(ax, (9.38, 9.55), (9.38, 9.2), color=Z_CORE[0])
    # 400 control
    zone(ax, 15.4, 7.8, 6.0, 5.0, Z_RED, "400", "IRRIGATION CONTROL")
    sub(ax, 15.65, 10.6, 5.5, 1.35, Z_RED[0], 410, "Valve decision", "pulse if D > set-point d")
    sub(ax, 15.65, 8.1, 2.65, 1.35, Z_RED[0], 420, "Valve command", "to unit 510")
    sub(ax, 18.5, 8.1, 2.65, 1.35, Z_RED[0], 430, "Delivery alarm", "dripper check")
    # internal signal lanes (right angles only)
    poly(ax, [(2.15, 10.9), (2.15, 11.75), (7.85, 11.75)], color=Z_IN[0], label="WC(t)", lpos=(4.9, 11.75))
    poly(ax, [(6.35, 9.6), (7.1, 9.6), (7.1, 11.2), (7.85, 11.2)], color=Z_IN[0], label="volume",
         lpos=(7.1, 10.3))
    poly(ax, [(14.2, 8.62), (14.9, 8.62), (14.9, 11.27), (15.65, 11.27)], color=Z_CORE[0], label="D(t)",
         lpos=(14.9, 10.0))
    arr(ax, (16.98, 10.6), (16.98, 9.45), color=Z_RED[0])
    # hardware band
    zone(ax, 0.6, 0.9, 13.8, 5.6, Z_PHY, "100", "IRRIGATION SECTION (greenhouse gutter)")
    for i, (x0, ref) in enumerate(((0.95, 110), (7.75, 120))):
        ax.add_patch(Rectangle((x0, 2.0), 6.2, 1.25, facecolor="#F5CBA7", edgecolor="#A04000", lw=1.5, zorder=4))
        ax.text(x0 + 3.1, 2.62, "rockwool slab 150  (one slab type)", ha="center", va="center", fontsize=9.2, zorder=5)
        sub(ax, x0 + 0.3, 3.6, 2.9, 1.25, Z_PHY[0], ref, "WC sensor", "dielectric, pins in slab")
        sub(ax, x0 + 3.4, 3.6, 2.5, 1.25, Z_PHY[0], 160 + i, "Plants + drippers", "on the slab")
        arr(ax, (x0 + 1.75, 3.6), (x0 + 1.75, 3.25), color=Z_PHY[0])
        arr(ax, (x0 + 4.65, 3.6), (x0 + 4.65, 3.25), color=Z_PHY[0])
    ax.add_patch(Rectangle((0.95, 1.2), 13.0, 0.5, facecolor="#D6EAF8", edgecolor="#5DADE2", lw=1.2, zorder=3))
    ax.text(7.45, 1.45, "gutter 170: drain -> drain meter 540, drain EC probe 550", ha="center", va="center",
            fontsize=9.3, color="#1B4F72", fontweight="bold", zorder=4)
    zone(ax, 15.4, 0.9, 6.0, 5.6, Z_PHY, "500", "DOSING HARDWARE")
    sub(ax, 15.65, 3.95, 2.65, 1.35, Z_PHY[0], 530, "Dose meter", "L per pulse")
    sub(ax, 15.65, 1.9, 2.65, 1.35, Z_PHY[0], 540, "Drain meter", "L per day")
    sub(ax, 18.5, 1.9, 2.65, 3.4, Z_PHY[0], 510, "Valve / pump", "on/off pulses", "to drippers")
    poly(ax, [(19.8, 1.9), (19.8, 1.05), (14.9, 1.05), (14.9, 5.6), (12.4, 5.6), (12.4, 4.85)],
         color="#1E8449", label="nutrient solution", lpos=(13.65, 5.6))
    # field lanes to the processing system (right angles, no crossings)
    poly(ax, [(2.15, 4.85), (2.15, 8.3)], color="#B9770E", label="WC 110", lpos=(2.15, 6.95))
    poly(ax, [(9.0, 4.85), (9.0, 7.2), (3.0, 7.2), (3.0, 8.3)], color="#AF601A", label="WC 120", lpos=(6.0, 7.2))
    poly(ax, [(16.98, 5.3), (16.98, 7.42), (5.05, 7.42), (5.05, 8.3)], color="#7D6608",
         label="pulse volumes", lpos=(11.4, 7.42))
    poly(ax, [(17.6, 8.1), (17.6, 7.05), (19.8, 7.05), (19.8, 5.3)], color=Z_RED[0], ls="--",
         label="valve command", lpos=(18.7, 7.05))
    save(fig, "fig01.png", 200, "architecture")


# ---------------------------------------------------------------- Figure 2
def fig02():
    fig, ax = plt.subplots(figsize=(15, 19.0))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 19.0)
    ax.axis("off")
    bands = [(15.3, 3.5, Z_IN, "INPUT"), (8.6, 6.4, Z_CORE, "RECALIBRATION"),
             (6.2, 2.1, Z_PROC, "DECISION"), (2.6, 3.3, Z_RED, "ACTION")]
    for y, h, col, lab in bands:
        ax.add_patch(FancyBboxPatch((0.2, y), 0.8, h, boxstyle="round,pad=0.04", facecolor=col[0],
                                    edgecolor=col[0], zorder=2))
        ax.text(0.6, y + h / 2, lab, rotation=90, color="white", fontsize=11.5, fontweight="bold",
                ha="center", va="center", zorder=3)
    X, W = 5.95, 8.1
    pbox(ax, X, 17.8, W, 1.25, "S1  Every 5 min: WC reading of each slab sensor 110, 120\n"
         "and the volume of each irrigation pulse (dose meter 530)", Z_IN, fs=10)
    pbox(ax, X, 16.1, W, 1.25, "S2  Rise of each sensor per pulse =\nmax(WC over 3 intervals from the pulse) - WC before", Z_IN, fs=10)
    steps = [(14.2, "S3  Drain onset of the day: first pulse after the 4 first pulses\n"
                    "whose rise < 0.3 x median rise of those 4 (slab now drains)"),
             (12.45, "S4  Daily plateau P_s(day) = median WC in 30 min after the onset;\n"
                     "reference P_s(d) = median of P_s over days d-14 .. d-1 (>= 3 days)"),
             (10.7, "S5  Drain deficit D = P_s(d) - WC of each sensor (offset cancels);\n"
                    "optional common scale WC* = P* - D"),
             (9.15, "S6  Optional gain: rise-per-litre ratio and decline ratio of the sensors;\n"
                    "apply only if they agree within 10 %")]
    for y, t in steps:
        pbox(ax, X, y, W, 1.2, t, Z_CORE, fs=9.8)
    for y0, y1 in ((17.17, 16.73), (15.47, 14.81), (13.6, 13.06), (11.85, 11.31), (10.1, 9.76)):
        arr(ax, (X, y0), (X, y1), color="#333")
    diamond(ax, X, 7.25, 4.6, 1.75, "D above\nset-point?", Z_PROC, fs=10.5)
    arr(ax, (X, 8.55), (X, 8.13), color="#333")
    LX, RX = 3.45, 8.45
    pbox(ax, LX, 4.55, 4.0, 1.4, "S7b  Keep valve closed\n(deficit within set-point)", Z_RED, fs=9.8)
    pbox(ax, RX, 4.55, 4.0, 1.4, "S7a  Open valve 510:\none pulse to the section", Z_RED, fs=9.8)
    poly(ax, [(X - 2.3, 7.25), (LX, 7.25), (LX, 5.25)], color=NO_C, label="NO", lpos=(LX - 0.45, 6.3), lcolor=NO_C)
    poly(ax, [(X + 2.3, 7.25), (RX, 7.25), (RX, 5.25)], color=YES_C, label="YES", lpos=(RX + 0.5, 6.3), lcolor=YES_C)
    # both branches return to S1 at the next sampling interval
    ax.plot([LX, LX, RX, RX], [3.85, 3.25, 3.25, 3.85], color="#333", lw=1.8, zorder=7)
    poly(ax, [(X, 3.25), (X, 2.85), (1.35, 2.85), (1.35, 17.8), (X - W / 2, 17.8)], color="#555", ls="--",
         label="next sampling interval", lpos=(3.6, 2.85))
    # weekly task, independent of the 5-min loop
    ax.add_patch(FancyBboxPatch((X - W / 2, 0.55), W, 1.4, boxstyle="round,pad=0.08", facecolor=Z_RED[1],
                                edgecolor=Z_RED[0], linewidth=1.6, linestyle=(0, (5, 3)), zorder=5))
    ax.text(X, 1.25, "S8  Weekly, in parallel: delivery ratio (rise per litre / daily decline) of each\n"
            "slab against the other slabs of the section; delivery alarm 430 on drift",
            ha="center", va="center", fontsize=9.8, zorder=6, linespacing=1.3)
    # hardware panel
    HX, HW = 12.85, 3.3
    for y0, y1 in ((15.3, 18.8), (3.55, 5.55)):
        ax.add_patch(FancyBboxPatch((HX - HW / 2 - 0.2, y0), HW + 0.4, y1 - y0, boxstyle="round,pad=0.05",
                                    facecolor="#FEF9E7", edgecolor=Z_PHY[0], linewidth=1.5, zorder=1))
    ax.text(HX, 18.55, "SECTION HARDWARE", ha="center", va="center", fontsize=10.5, fontweight="bold", color=Z_PHY[0])
    pbox(ax, HX, 17.8, HW, 0.8, "WC sensors 110, 120", Z_PHY, fs=9.8)
    pbox(ax, HX, 16.1, HW, 0.9, "Dose meter 530\n(pulse volume)", Z_PHY, fs=9.6)
    pbox(ax, HX, 4.55, HW, 1.1, "Irrigation valve /\npump 510", Z_PHY, fs=9.8)
    arr(ax, (HX - HW / 2, 17.8), (X + W / 2, 17.8), color=Z_PHY[0], label="WC(t)", lpos=(10.6, 18.05))
    arr(ax, (HX - HW / 2, 16.1), (X + W / 2, 16.1), color="#7D6608", label="volume", lpos=(10.6, 16.35))
    arr(ax, (RX + 2.0, 4.55), (HX - HW / 2, 4.55), color=Z_RED[0], ls="--", label="command", lpos=(10.85, 4.8))
    save(fig, "fig02.png", 200, "flowchart")


# ---------------------------------------------------------------- Figure 3
EXAMPLE_TEAM = "IUACAAS"


def example_day(x):
    """Second-half day on which both sensors show a drain onset (first one found)."""
    days = np.sort(x.index.normalize().unique())
    split = days[len(days) // 2]
    P1, P2 = daily_plateau(x, 1), daily_plateau(x, 2)
    both = [d for d in P1.index if d in P2.index and d >= split]
    return both[0], P1, P2


def fig03():
    x, _ = agc.load(EXAMPLE_TEAM)
    day, P1, P2 = example_day(x)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    a = axes[0, 0]
    seg = x[day + pd.Timedelta("4h"):day + pd.Timedelta("20h")]
    for s, col in ((1, C[0]), (2, C[1])):
        a.plot(seg.index, seg[f"WC_slab{s}"], color=col, lw=1.8, label="sensor %d" % s)
        P = (P1 if s == 1 else P2)[day]
        a.axhline(P, color=col, ls=":", lw=1.2)
        a.text(seg.index[-1], P + 0.4, "plateau %.1f" % P, color=col, ha="right", fontsize=9)
    pul = seg[seg.irr > 0]
    a.vlines(pul.index, a.get_ylim()[0], a.get_ylim()[0] + 1.0, color="#1E8449", lw=1.2, label="pulse")
    a.set_ylabel("WC reading (%)")
    a.set_title("One day, %s, %s: same slab type, offset readings" % (EXAMPLE_TEAM, day.date()), fontsize=11)
    a.legend(frameon=False, fontsize=9, loc="center right")
    panel(a, "a"); tidy(a)
    a = axes[0, 1]
    for s, col in ((1, C[0]), (2, C[1])):
        p = pulse_rises(x, s)
        p = p[(p.t >= day) & (p.t < day + pd.Timedelta("1D")) & (p.vol > 0)]
        a.plot(np.arange(len(p)) + 1, p.rise.values, "o-", color=col, label="sensor %d" % s)
        a.fill_between(np.arange(len(p)) + 1, 0, p.rise.values, color=col, alpha=0.15)
    a.set_xlabel("pulse number of the day")
    a.set_ylabel("rise of the reading per pulse (WC %)")
    a.set_title("Pulse response collapses when the slab starts to drain", fontsize=11)
    a.legend(frameon=False, fontsize=9)
    panel(a, "b"); tidy(a)
    a = axes[1, 0]
    days = np.sort(x.index.normalize().unique())
    for s, col, P in ((1, C[0], P1), (2, C[1], P2)):
        a.plot(P.index, P.values, ".", color=col, alpha=0.6, label="daily plateau, sensor %d" % s)
        ref = RA.rolling_ref(P, days)
        a.plot(ref.index, ref.values, "-", color=col, lw=2, label="rolling reference, sensor %d" % s)
    a.set_ylabel("WC reading at drain onset (%)")
    a.set_title("Plateau per sensor over the season, %s" % EXAMPLE_TEAM, fontsize=11)
    a.legend(frameon=False, fontsize=8.5)
    panel(a, "c"); tidy(a)
    a = axes[1, 1]
    ch = []
    for t in agc.TEAMS:
        xx, _ = agc.load(t)
        for s in (1, 2):
            P = daily_plateau(xx, s)
            d = P.diff()[P.index.to_series().diff().dt.days == 1]
            ch.extend(d.dropna().values)
    ch = np.array(ch)
    a.hist(np.clip(ch, -10, 10), bins=60, color=C[2], edgecolor="white", linewidth=1.2)
    med = float(np.median(np.abs(ch)))
    a.axvline(0, color="#333", lw=1)
    a.text(0.97, 0.92, "consecutive days: %d\nmedian |change| %.2f WC %%" % (len(ch), med),
           transform=a.transAxes, ha="right", va="top", fontsize=10)
    a.set_xlabel("plateau change from the previous day (WC %, clipped at +-10)")
    a.set_ylabel("sensor-days")
    a.set_title("The drain-onset plateau is stable from day to day", fontsize=11)
    panel(a, "d"); tidy(a)
    fig.tight_layout()
    refs = {s: float(RA.rolling_ref(P, days).get(day)) for s, P in ((1, P1), (2, P2))}
    json.dump(dict(team=EXAMPLE_TEAM, day=str(day.date()), n_changes=int(len(ch)), median_abs_change=med,
                   ref1=refs[1], ref2=refs[2]),
              open(os.path.join(RESULTS, "fig03_example.json"), "w"), indent=1)
    save(fig, "fig03.png", 300, "physics")


# ---------------------------------------------------------------- Figure 4
def fig04():
    ra, ex, cr = load("rolling_anchor.json"), load("experiments.json"), load("control_replay.json")
    oa = load("offset_anchor.json")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    a = axes[0, 0]
    teams = agc.TEAMS
    xs = np.arange(len(teams))
    vals = [[ra["teams"][t]["raw"] for t in teams], [oa[t]["wc_gap_offset_median"] for t in teams],
            [ra["teams"][t]["rolling"] for t in teams]]
    for i, (v, lab) in enumerate(zip(vals, ("raw", "fixed anchor (first half)", "rolling anchor"))):
        b = a.bar(xs + (i - 1) * 0.27, v, 0.27, color=C[[1, 3, 0][i]], edgecolor="white", linewidth=1.2, label=lab)
        for r, val in zip(b, v):
            a.text(r.get_x() + r.get_width() / 2, val + 0.2, "%.1f" % val, ha="center", fontsize=8)
    a.set_xticks(xs); a.set_xticklabels([SHORT[t] for t in teams])
    a.set_ylabel("median |WC1 - WC2|, second half (WC %)")
    a.set_title("Paired sensors in one compartment, held-out half", fontsize=11)
    a.legend(frameon=False, fontsize=9)
    panel(a, "a"); tidy(a)
    a = axes[0, 1]
    t = "AICU"
    x, _ = agc.load(t)
    days = np.sort(x.index.normalize().unique())
    e = {}
    for s in (1, 2):
        ref = RA.rolling_ref(daily_plateau(x, s), days).reindex(x.index.normalize()).values
        e[s] = x[f"WC_slab{s}"] - ref
    g_raw = (x.WC_slab1 - x.WC_slab2).abs().groupby(x.index.normalize()).median()
    g_cor = (e[1] - e[2]).abs().groupby(x.index.normalize()).median()
    a.plot(g_raw.index, g_raw.values, color=C[1], lw=1.6, label="raw")
    a.fill_between(g_raw.index, 0, g_raw.values, color=C[1], alpha=0.15)
    a.plot(g_cor.index, g_cor.values, color=C[0], lw=1.6, label="rolling anchor")
    a.fill_between(g_cor.index, 0, g_cor.values, color=C[0], alpha=0.15)
    a.set_ylabel("daily median |WC1 - WC2| (WC %)")
    a.set_title("Daily pair gap over the season, %s" % t, fontsize=11)
    a.legend(frameon=False, fontsize=9)
    panel(a, "b"); tidy(a)
    a = axes[1, 0]
    grid = ex["E1_sensitivity"]
    Ws, ths = sorted({g["W"] for g in grid}), sorted({g["thr"] for g in grid})
    M = np.array([[next(g["gap_median"] for g in grid if g["W"] == w and g["thr"] == th) for th in ths] for w in Ws])
    im = a.imshow(M, cmap="Blues_r", vmin=0, vmax=ex["E1_raw_gap_median"])
    for i in range(len(Ws)):
        for j in range(len(ths)):
            a.text(j, i, "%.2f" % M[i, j], ha="center", va="center", fontsize=11, fontweight="bold")
    a.set_xticks(range(len(ths))); a.set_xticklabels(["%.1f" % v for v in ths])
    a.set_yticks(range(len(Ws))); a.set_yticklabels(["%d d" % v for v in Ws])
    a.set_xlabel("drain-onset threshold (fraction of morning rise)")
    a.set_ylabel("rolling window")
    a.set_title("Median pair gap over compartments (raw: %.2f WC %%)" % ex["E1_raw_gap_median"], fontsize=11)
    fig.colorbar(im, ax=a, fraction=0.046)
    panel(a, "c")
    a = axes[1, 1]
    keys = list(cr["sensors"].keys())
    mm = [cr["sensors"][k]["mismatch"] * 100 for k in keys]
    fs = [cr["sensors"][k]["full_slab_irr"] * 100 for k in keys]
    xs = np.arange(len(keys))
    a.bar(xs - 0.2, mm, 0.4, color=C[4], edgecolor="white", linewidth=1.2, label="valve decision differs")
    a.bar(xs + 0.2, fs, 0.4, color=C[3], edgecolor="white", linewidth=1.2, label="pulse into a draining slab")
    a.set_xticks(xs)
    a.set_xticklabels(["%s-%s" % (SHORT[k.rsplit("_", 1)[0]], k.rsplit("_", 1)[1]) for k in keys], rotation=45, ha="right")
    a.set_ylabel("share of daytime 5-min samples (%)")
    a.set_title("Set-point rule on raw vs corrected reading (D > 5, i.e. WC* < P* - 5)", fontsize=11)
    a.legend(frameon=False, fontsize=9)
    panel(a, "d"); tidy(a)
    fig.tight_layout()
    save(fig, "fig04.png", 300, "main results")


# ---------------------------------------------------------------- Figure 5
def fig05():
    so, db, dr, ex = load("scale_offset.json"), load("dryback.json"), load("dripper_ratio.json"), load("experiments.json")
    teams = agc.TEAMS
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    a = axes[0, 0]
    gr = [so[t]["G_first_half"] for t in teams]
    gd = [so[t]["G_decl_first_half"] for t in teams]
    lim = (0.6, 2.0)
    xx = np.linspace(*lim, 50)
    a.fill_between(xx, xx * 0.9, xx * 1.1, color=C[2], alpha=0.15, label="+-10 % agreement band")
    a.plot(xx, xx, color="#333", lw=1)
    for t, u, v in zip(teams, gr, gd):
        ok = so[t]["routes_agree"]
        a.plot(u, v, "o", ms=10, color=C[0] if ok else C[1])
        a.text(u + 0.02, v + 0.03, SHORT[t], fontsize=9)
    a.set_xlim(*lim); a.set_ylim(*lim)
    a.set_xlabel("relative gain from pre-drain rise per litre")
    a.set_ylabel("relative gain from daily decline")
    a.set_title("Two physical routes to the sensor gain ratio (first half)", fontsize=11)
    a.legend(frameon=False, fontsize=9, loc="upper left")
    panel(a, "a"); tidy(a)
    a = axes[0, 1]
    xs = np.arange(len(teams))
    sets = [("gap_raw", "raw", C[1]), ("gap_scale_ungated", "gain always applied", C[3]),
            ("gap_scale_gated", "gain applied only if routes agree", C[0])]
    for i, (k, lab, col) in enumerate(sets):
        v = [db[t][k] * 100 for t in teams]
        a.bar(xs + (i - 1) * 0.27, v, 0.27, color=col, edgecolor="white", linewidth=1.2, label=lab)
    a.set_xticks(xs); a.set_xticklabels([SHORT[t] for t in teams])
    a.set_ylabel("median relative pair gap of daily dry-back (%)")
    a.set_title("Overnight dry-back agreement, second half", fontsize=11)
    a.legend(frameon=False, fontsize=9)
    panel(a, "b"); tidy(a)
    a = axes[1, 0]
    for i, t in enumerate(teams):
        w = dr[t]["weekly"]
        a.plot(np.arange(len(w)) + 1, w, "-o", ms=4, color=C[i % len(C)], label=SHORT[t])
    a.axhline(1, color="#333", lw=1)
    a.set_xlabel("week of the season")
    a.set_ylabel("delivery ratio slab 1 / slab 2 (gain-free)")
    a.set_title("Water delivered per unit demand, slab against slab", fontsize=11)
    a.legend(frameon=False, fontsize=8.5, ncol=3)
    panel(a, "c"); tidy(a)
    a = axes[1, 1]
    cov = ex["E3_coverage"]
    labs, v = [], []
    for t in teams:
        for s in ("1", "2"):
            labs.append("%s-%s" % (SHORT[t], s)); v.append(cov[t][s]["coverage"] * 100)
    b = a.bar(np.arange(len(v)), v, color=C[5], edgecolor="white", linewidth=1.2)
    for r, val in zip(b, v):
        a.text(r.get_x() + r.get_width() / 2, val + 1, "%.0f" % val, ha="center", fontsize=8)
    a.set_xticks(np.arange(len(v))); a.set_xticklabels(labs, rotation=45, ha="right")
    a.set_ylabel("irrigated days with a detected drain onset (%)")
    a.set_title("How often the anchor is refreshed", fontsize=11)
    panel(a, "d"); tidy(a)
    fig.tight_layout()
    save(fig, "fig05.png", 300, "scale and delivery")


# ---------------------------------------------------------------- Figure 6
def fig06():
    fig, ax = plt.subplots(figsize=(23.5, 12.4))
    ax.set_xlim(0, 47)
    ax.set_ylim(0.4, 25.2)
    ax.axis("off")
    zone(ax, 0.4, 13.6, 31.2, 11.2, Z_PROC, "Claim 1", "INDEPENDENT - METHOD")
    lines = [
        "irrigation section 100: slabs 150 of one substrate type, >= 2 dielectric WC sensors 110, 120,",
        "valve / pump 510 dosing pulses through drippers, dose meter 530; carried out by system 900:",
        "(a) deliver pulses via valve 510; receive WC readings and the volume of each pulse",
        "(b) RESPONSE of each reading to each pulse (rise per pulse)",
        "(c) COLLAPSE of the response vs the same day's earlier pulses = DRAIN ONSET of the slab",
        "(d) SENSOR-SPECIFIC daily PLATEAU reading after its own slab's drain onset",
        "(e) ROLLING REFERENCE in a reference memory, from past days' plateaus only",
        "(f) DRAIN DEFICIT = reference - reading (sensor offset cancels)",
        "(g) valve 510 opened for a pulse when the section's deficit exceeds a set-point, else held",
    ]
    for i, t in enumerate(lines):
        ax.text(1.0, 22.6 - i * 0.98, t, fontsize=10.6, va="center", ha="left", zorder=6,
                fontweight="bold" if t[:3] in ("(c)", "(d)", "(e)", "(f)") else "normal")
    zone(ax, 32.6, 13.6, 14.0, 11.2, Z_IN, "Claim 7", "INDEPENDENT - SYSTEM")
    ax.text(39.6, 18.6, "section 100 (slabs 150, sensors\n110, 120, valve 510, meter 530);\n"
            "system 900: sensor input 210,\npulse-volume input 220,\nonset units 310, 320,\n"
            "reference memory 330,\ndeficit unit 350,\nvalve output 410, 420 -> 510", ha="center", va="center",
            fontsize=10.6, zorder=6, linespacing=1.5)
    arr(ax, (32.6, 19.2), (31.6, 19.2), color=Z_IN[0])
    deps = [(0.5, "Claim 2", "(of 1)", "common scale:\nWC* = P* - D, P* =\nmedian plateau over a\ncommissioning period"),
            (9.75, "Claim 3", "(of 1 or 2)", "fraction 0.2-0.4 (0.3) of\nfirst 4 pulses; 30-min\nplateau; window 7-28 d\n(14 d), >= 3 days"),
            (19.0, "Claim 4", "(of 1 to 3)", "gain by filling route\nand by uptake route;\napplied only if they\nagree (gate)"),
            (28.25, "Claim 5", "(of 1 to 4)", "gain-free delivery\nratio slab vs slab;\ndripper alarm 430\non drift"),
            (37.5, "Claim 6", "(of 1 to 5)", "drain EC probe 550:\ndeficit at first drained\npulse checked; sensor\ncheck signal 440")]
    for x, head, par, t in deps:
        depbox(ax, x, 1.0, 8.95, 6.6, "#566573", head + "  " + par, t)
    ax.plot([0.5, 46.5], [8.9, 8.9], color="#566573", lw=1.2, ls="--")
    ax.text(23.5, 9.4, "dependent claims 2 to 6 refine claim 1 as marked; claim 7 is the system carrying out the method",
            ha="center", fontsize=10, color="#566573", style="italic")
    arr(ax, (16.0, 13.6), (16.0, 9.6), color=Z_PROC[0])
    save(fig, "fig06.png", 200, "claim tree")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    funcs = {"1": fig01, "2": fig02, "3": fig03, "4": fig04, "5": fig05, "6": fig06}
    for w in sys.argv[1:] or sorted(funcs):
        funcs[str(int(w))]()
