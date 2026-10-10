"""Figures 1-11 for the IDF-B disclosure on count-derived conservation constraints.

Style follows the accepted CausalInterlock IDF-B (make_figs.py there): architecture
figures at dpi=200, data figures at dpi=300, ASCII labels, reference numerals in
parentheses. Data figures read results/*.json and the cached counts; nothing is typed in
except labels.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle, Circle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "patent", "figures")

HWC = "#1565C0"      # physical network / detectors
PRC = "#F9A825"      # processing
VAL = "#2E7D32"      # constraint / validation
ENF = "#C62828"      # output / action
GRY = "#455A64"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


def load(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return json.load(fh)


def box(ax, x, y, w, h, text, fc, fs=8.2, tc="white", bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                facecolor=fc, edgecolor="black", linewidth=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, fontweight="bold" if bold else "normal",
            linespacing=1.35)


def arrow(ax, p, q, style="-|>", lw=1.3, color="black", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=11,
                                 linewidth=lw, color=color, linestyle=ls,
                                 connectionstyle="arc3,rad=%.2f" % rad,
                                 shrinkA=1, shrinkB=1))


def save(fig, name, dpi, note):
    fig.savefig(os.path.join(OUT, name), dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print("%s  %s" % (name, note))


# ---------------------------------------------------------------- Figure 1
def fig01():
    """The road, the detectors, and the three kinds of relation recovered from counts."""
    fig, ax = plt.subplots(figsize=(13.5, 5.6))
    ax.set_xlim(0, 135)
    ax.set_ylim(0, 56)
    ax.axis("off")

    # carriageway
    ax.add_patch(Rectangle((4, 26), 127, 7, fc="#ECEFF1", ec=GRY, lw=1.0))
    ax.text(5, 23.0, "mainline carriageway", fontsize=8, color=GRY)
    ax.text(122, 23.0, "direction of flow", fontsize=8, color=GRY, ha="center")
    arrow(ax, (116, 29.5), (129, 29.5), lw=1.6, color=GRY)
    # off-slip leaving, on-slip joining
    ax.plot([52, 64], [26, 12], color=GRY, lw=6, solid_capstyle="butt", alpha=0.35)
    ax.plot([80, 92], [12, 26], color=GRY, lw=6, solid_capstyle="butt", alpha=0.35)
    ax.text(50, 9.2, "off-slip", fontsize=8, color=GRY)
    ax.text(86, 9.2, "on-slip", fontsize=8, color=GRY)

    det = [(12, 29.5, "d1"), (32, 29.5, "d2"), (48, 29.5, "d3"), (72, 29.5, "d4"),
           (96, 29.5, "d5"), (110, 29.5, "d6"), (60, 16.5, "s1"), (84, 16.5, "s2")]
    for x, y, lab in det:
        ax.add_patch(Rectangle((x - 1.6, y - 1.6), 3.2, 3.2, fc=HWC, ec="black", lw=0.8))
        ax.text(x, y + 4.6 if y > 20 else y - 4.4, lab, ha="center", fontsize=8.5,
                fontweight="bold", color=HWC)
    ax.text(4, 51.5, "Roadside detectors (110 mainline, 120 slip road) report counts per "
            "interval. No map, no site names and no coordinates are supplied.",
            fontsize=8.6, color="black")

    # relation annotations
    def brace(x0, x1, y, text, col):
        ax.plot([x0, x0, x1, x1], [y - 1.2, y, y, y - 1.2], color=col, lw=1.4)
        ax.text((x0 + x1) / 2, y + 1.2, text, ha="center", fontsize=7.8, color=col,
                fontweight="bold")
    brace(12, 32, 40, "pair: x1 - x2 = 0", VAL)
    brace(32, 48, 44.5, "pair: x2 - x3 = 0", VAL)
    brace(12, 48, 48.5, "shortcut x1 - x3: removed by ordering stage", ENF)
    ax.plot([48, 48, 72, 72], [7, 5.8, 5.8, 7], color=VAL, lw=1.4)
    ax.text(60, 2.4, "junction: x3 - x4 - s1 = 0", ha="center", fontsize=7.8, color=VAL,
            fontweight="bold")
    ax.plot([72, 72, 96, 96], [7, 5.8, 5.8, 7], color=VAL, lw=1.4)
    ax.text(84, 2.4, "junction: x4 - x5 + s2 = 0", ha="center", fontsize=7.8, color=VAL,
            fontweight="bold")
    ax.text(120, 7, "signs +1 / -1 are\nrecovered, not\nsupplied: they\nstate the "
            "direction\nof flow", fontsize=7.6, color=GRY, ha="center", style="italic")
    save(fig, "fig01.png", 200, "road schematic and recovered relations")


# ---------------------------------------------------------------- Figure 2
def route(ax, pts, color="black", ls="-", lw=1.3):
    """Orthogonal connector: straight segments, arrowhead on the last one only."""
    for (x0, y0), (x1, y1) in zip(pts[:-2], pts[1:-1]):
        ax.plot([x0, x1], [y0, y1], color=color, lw=lw, linestyle=ls,
                solid_capstyle="butt")
    arrow(ax, pts[-2], pts[-1], color=color, ls=ls, lw=lw)


def fig02():
    """Columns separated by routing channels; every connector runs in a channel."""
    fig, ax = plt.subplots(figsize=(15.0, 8.0))
    ax.set_xlim(0, 150)
    ax.set_ylim(0, 80)
    ax.axis("off")
    ax.add_patch(Rectangle((1, 1), 148, 78, fill=False, ec="#B0BEC5", lw=1.0,
                           linestyle=(0, (4, 3))))
    ax.text(2.5, 76.2, "DATA-PROCESSING SYSTEM (900)", fontsize=9.5, fontweight="bold",
            color=GRY)

    # column A: x 3-29 | channel 29-37 | B: 37-65 | channel 65-75 | C: 75-105 |
    # channel 105-113 | D: 113-146
    ax.text(16, 71, "DETECTOR NETWORK", fontsize=9, fontweight="bold", color=HWC,
            ha="center")
    box(ax, 3, 57, 26, 9, "Roadside detectors (100)\nmainline (110) and\nslip road (120)",
        HWC, 7.8)
    box(ax, 3, 45, 26, 8, "Communication link (130)\ninterval counts", HWC, 7.8)
    box(ax, 3, 31, 26, 9, "Count archive (200)\ndetector x interval,\nabsent records marked",
        HWC, 7.5)
    box(ax, 3, 17, 26, 9, "Supplied network map (610)\noptional; audited,\nnever trusted",
        GRY, 7.6)
    arrow(ax, (16, 57), (16, 53))
    arrow(ax, (16, 45), (16, 40))

    ax.text(51, 71, "CONSTRAINT RECOVERY", fontsize=9, fontweight="bold", color=PRC,
            ha="center")
    box(ax, 37, 59, 28, 7.5, "Pair stage (300)\ninteger agreement x_i = x_k", PRC, 7.6,
        "black")
    box(ax, 37, 48.5, 28, 7.5, "Ordering stage (310)\ntriangle rule: adjacency", PRC, 7.6,
        "black")
    box(ax, 37, 36, 28, 9.5, "Junction stage (320)\nslips shortlisted by correlation\n"
        "with the mainline-pair residual", PRC, 7.3, "black")
    box(ax, 37, 26, 28, 7, "Necessity test (330)", PRC, 7.6, "black")
    box(ax, 37, 16.5, 28, 7, "Self-derived limit (340)\nmultiple of adjacent-pair floor",
        PRC, 7.3, "black")
    arrow(ax, (51, 59), (51, 56))
    arrow(ax, (51, 48.5), (51, 45.5))
    arrow(ax, (51, 36), (51, 33))
    # archive -> pair stage, in channel A-B at x = 32
    route(ax, [(29, 35.5), (32, 35.5), (32, 62.75), (37, 62.75)])
    # ordering stage -> self-derived limit, dashed, in channel A-B at x = 34.5
    route(ax, [(37, 52.25), (34.5, 52.25), (34.5, 20), (37, 20)], color="#E65100",
          ls=(0, (3, 2)))

    ax.text(90, 71, "HARD CONSTRAINT SET", fontsize=9, fontweight="bold", color=VAL,
            ha="center")
    box(ax, 75, 55, 30, 11, "Relation store (400)\nsigned integer relations,\n"
        "retained under limit (340)", VAL, 7.6)
    box(ax, 75, 41, 30, 10, "Band unit (410)\ntwo-sided band from each\nrelation's own "
        "residual", VAL, 7.5)
    box(ax, 75, 22, 30, 14, "Map audit unit (600)\nmap relation over limit: flag\n"
        "repair proposer (620)\nshares >= 2 detectors", VAL, 7.4)
    arrow(ax, (90, 55), (90, 51))
    arrow(ax, (90, 36), (90, 41), color="#E65100", ls=(0, (3, 2)))
    # necessity test -> relation store, in channel B-C at x = 70
    route(ax, [(65, 29.5), (70, 29.5), (70, 60.5), (75, 60.5)])
    # supplied map -> map audit, beneath column B at y = 14
    route(ax, [(16, 17), (16, 14), (82, 14), (82, 22)])

    ax.text(129.5, 71, "RECONSTRUCTION AND ACTION", fontsize=9, fontweight="bold",
            color=ENF, ha="center")
    box(ax, 113, 57, 33, 9, "Prior estimator (500)\nany per-detector method", GRY, 7.6)
    box(ax, 113, 43, 33, 10, "Projection unit (510)\nhard two-sided inequalities,\n"
        "joint over overlapping relations", ENF, 7.4)
    box(ax, 113, 31, 15.8, 8, "Irreconcilable\nreport (520)", ENF, 7.2)
    box(ax, 130.2, 31, 15.8, 8, "Certified\ninterval (530)", ENF, 7.2)
    box(ax, 113, 17, 33, 10.5, "Fault attribution (700)\nbias fitted to the recovered\n"
        "coefficient pattern", ENF, 7.4)
    arrow(ax, (129.5, 57), (129.5, 53))
    arrow(ax, (120.9, 43), (120.9, 39))
    arrow(ax, (138.1, 43), (138.1, 39))
    # band unit -> projection unit, straight across channel C-D
    arrow(ax, (105, 48), (113, 48))
    # calibrated relations -> fault attribution, in channel C-D at x = 109
    route(ax, [(105, 43.5), (109, 43.5), (109, 22.25), (113, 22.25)])

    box(ax, 37, 3.5, 109, 8, "Outputs (800): reconstructed dataset (810) supplied to a "
        "downstream control process (820);\nmaintenance record naming a detector (830);  "
        "rewritten constraint set (840)", GRY, 7.8)
    arrow(ax, (97, 22), (97, 11.5))
    arrow(ax, (129.5, 17), (129.5, 11.5))
    save(fig, "fig02.png", 200, "system architecture")


# ---------------------------------------------------------------- Figure 3
def fig03():
    fig, axs = plt.subplots(1, 2, figsize=(13.2, 4.6))
    ax = axs[0]
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 40)
    ax.axis("off")
    ax.set_title("(a) Ordering stage (310): the triangle rule", fontsize=9.5,
                 fontweight="bold")
    pts = {"i": (8, 12), "j": (30, 12), "k": (52, 12)}
    for lab, (x, y) in pts.items():
        ax.add_patch(Circle((x, y), 2.6, fc=HWC, ec="black"))
        ax.text(x, y, lab, ha="center", va="center", color="white", fontweight="bold")
    ax.plot([10.6, 27.4], [12, 12], color=VAL, lw=2)
    ax.plot([32.6, 49.4], [12, 12], color=VAL, lw=2)
    ax.text(19, 8, "r(i,j) small", ha="center", fontsize=8, color=VAL)
    ax.text(41, 8, "r(j,k) small", ha="center", fontsize=8, color=VAL)
    arc = FancyArrowPatch((8, 14.6), (52, 14.6), connectionstyle="arc3,rad=-0.45",
                          arrowstyle="-", lw=2, color=ENF, linestyle=(0, (4, 2)))
    ax.add_patch(arc)
    ax.text(30, 29, "r(i,k) larger than both: j lies between i and k,\nso (i,k) is a "
            "shortcut and is removed", ha="center", fontsize=8, color=ENF)
    ax.text(30, 1.5, "What survives is the chain of adjacent detectors: the order of "
            "sites\nalong the road, recovered without coordinates or names.",
            ha="center", fontsize=7.8, color=GRY, style="italic")

    ax = axs[1]
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 40)
    ax.axis("off")
    ax.set_title("(b) Junction stage (320): shortlist from the residual", fontsize=9.5,
                 fontweight="bold")
    box(ax, 2, 27, 24, 8, "mainline pair (i,k)\nfails as a pair", GRY, 7.8)
    box(ax, 34, 27, 24, 8, "residual\nx_i - x_k", PRC, 8, "black")
    arrow(ax, (26, 31), (34, 31))
    box(ax, 2, 13, 24, 9, "rank every other detector\nby |corr(x_j, x_i - x_k)|",
        PRC, 7.6, "black")
    box(ax, 34, 13, 24, 9, "fit subsets of the\nshortlist; round to +/-1", PRC, 7.6,
        "black")
    arrow(ax, (46, 27), (14, 22), rad=0.1)
    arrow(ax, (26, 17.5), (34, 17.5))
    box(ax, 18, 1, 24, 8, "necessity test (330)\nevery member earns its place", VAL, 7.6)
    arrow(ax, (46, 13), (30, 9))
    save(fig, "fig03.png", 200, "ordering and junction stages")


# ---------------------------------------------------------------- Figure 4
def fig04():
    import dataset
    c = dataset.load("window_full_M25_A.json")
    nodes = load("nodes_M25_A.json")
    mk = {}
    for n in nodes["nodes"]:
        mk[n["upstream"]["marker"]] = n["upstream"]["id"]
        mk[n["downstream"]["marker"]] = n["downstream"]["id"]
        for s in n["slips"]:
            mk[s["marker"]] = s["id"]
    up, dn, sl = (c.row_of[mk[m]] for m in ("4432A", "4435A", "4435J"))
    both = c.observed[up] & c.observed[dn] & c.observed[sl]
    idx = np.where(both)[0]
    resid_pair = c.volumes[up, idx] - c.volumes[dn, idx]
    slip = c.volumes[sl, idx]
    rel = resid_pair - slip
    r_target = float(np.corrcoef(c.volumes[up, idx], slip)[0, 1])
    r_resid = float(np.corrcoef(resid_pair, slip)[0, 1])

    def rank(target, exclude):
        """Position of the slip detector when all detectors are ranked by |corr|."""
        scored = []
        for j in range(c.volumes.shape[0]):
            if j in exclude:
                continue
            b = c.observed[up] & c.observed[dn] & c.observed[j]
            if b.sum() < 400 or c.volumes[j, b].std() < 1e-9:
                continue
            scored.append((abs(float(np.corrcoef(target(b), c.volumes[j, b])[0, 1])), j))
        scored.sort(reverse=True)
        return [j for _, j in scored].index(sl) + 1, len(scored)
    rk_t = rank(lambda b: c.volumes[up, b], {up})
    rk_r = rank(lambda b: c.volumes[up, b] - c.volumes[dn, b], {up, dn})
    flow = float(c.volumes[up, idx].mean())

    fig, axs = plt.subplots(1, 2, figsize=(13.2, 4.4), gridspec_kw={"width_ratios": [1.6, 1]})
    ax = axs[0]
    w = slice(0, 288)       # three days of consecutive shared intervals
    t = np.arange(len(idx))[w] / 96.0
    ax.plot(t, resid_pair[w], color=PRC, lw=1.1, label="mainline residual x(4432A) - x(4435A)")
    ax.plot(t, slip[w], color=HWC, lw=1.0, ls="--", label="slip detector x(4435J)")
    ax.set_xlabel("days (shared intervals)")
    ax.set_ylabel("vehicles per 15 min")
    ax.legend(fontsize=7.8, loc="upper left", frameon=False)
    ax.set_title("(a) The slip flow is the residual of the mainline pair", fontsize=9.5,
                 fontweight="bold")
    ax.set_ylim(top=ax.get_ylim()[1] * 1.3)
    ax.text(0.99, 0.97, "slip ranked by |corr| with upstream mainline: %d of %d\n"
            "slip ranked by |corr| with mainline residual: %d of %d"
            % (rk_t[0], rk_t[1], rk_r[0], rk_r[1]),
            transform=ax.transAxes, ha="right", va="top", fontsize=8, color=GRY)

    ax = axs[1]
    bins = np.linspace(-120, 220, 70)
    ax.hist(resid_pair, bins=bins, color=PRC, alpha=0.65, label="pair relation")
    ax.hist(rel, bins=bins, color=VAL, alpha=0.75,
            label="recovered junction\nx(4432A) - x(4435A) - x(4435J)")
    ax.set_xlabel("residual, vehicles per 15 min")
    ax.set_ylabel("intervals")
    ax.legend(fontsize=7.6, frameon=False)
    ax.set_title("(b) Residual before and after the slip", fontsize=9.5, fontweight="bold")
    ax.text(0.98, 0.55, "median |residual|\npair %.0f (%.1f%% of flow)\njunction %.0f "
            "(%.1f%%)" % (np.median(abs(resid_pair)), 100 * np.median(abs(resid_pair)) / flow,
                          np.median(abs(rel)), 100 * np.median(abs(rel)) / flow),
            transform=ax.transAxes, ha="right", fontsize=8, color=GRY)
    fig.tight_layout()
    save(fig, "fig04.png", 300, "worked junction M25 4432A/4435A/4435J "
         "(corr target %.2f, residual %.2f)" % (r_target, r_resid))
    return {"r_target": r_target, "r_resid": r_resid, "n": int(len(idx)),
            "rank_by_target": rk_t, "rank_by_residual": rk_r,
            "pair_med": float(np.median(abs(resid_pair))), "rel_med": float(np.median(abs(rel))),
            "flow": flow}


# ---------------------------------------------------------------- Figure 5
def fig05():
    fig, ax = plt.subplots(figsize=(8.6, 11.0))
    ax.set_xlim(0, 86)
    ax.set_ylim(0, 110)
    ax.axis("off")
    steps = [
        ("S1  Receive counts indexed by detector and interval (200);\nno network map received", HWC),
        ("S2  Pair stage (300): detector pairs whose fitted coefficient\nrounds to 1 and whose "
         "residual is within the pair tolerance", PRC),
        ("S3  Ordering stage (310): remove each pair (i,k) for which some j\nagrees more tightly "
         "with both; the remainder are adjacent pairs", PRC),
        ("S4  Self-derived limit (340) = multiple x median residual\nof the adjacent pairs, "
         "measured from the counts", PRC),
        ("S5  Junction stage (320): for mainline pairs failing as pairs,\nshortlist by "
         "correlation with the pair residual; fit; round to +/-1", PRC),
        ("S6  Retain a relation only if its residual <= limit and every\nmember passes the "
         "necessity test (330)", VAL),
        ("S7  Band unit (410): two-sided band per relation from its own\nresidual spread, "
         "on observed records only", VAL),
        ("S8  Projection (510): prior (500) projected onto the intersection\nof bands as HARD "
         "inequalities, jointly over shared detectors", ENF),
        ("S9  Empty intersection: report node, interval and shortfall (520);\notherwise emit "
         "value with certified interval (530)", ENF),
        ("S10 Supply reconstructed dataset (810) to the downstream\ncontrol process (820)", GRY),
    ]
    y = 102
    for i, (txt, col) in enumerate(steps):
        box(ax, 6, y - 8, 74, 8, txt, col, 7.8, "black" if col == PRC else "white")
        if i:
            arrow(ax, (43, y + 2.4), (43, y))
        y -= 10.4
    save(fig, "fig05.png", 200, "method flowchart")


# ---------------------------------------------------------------- Figure 6
def fig06():
    fig, ax = plt.subplots(figsize=(13.2, 5.0))
    ax.set_xlim(0, 132)
    ax.set_ylim(0, 50)
    ax.axis("off")
    box(ax, 2, 32, 26, 12, "Supplied map (610)\nrelation R: detectors\nand signs", GRY, 7.8)
    box(ax, 36, 32, 28, 12, "Measure R on the counts\nmedian |residual|,\n% of flow",
        PRC, 7.8, "black")
    box(ax, 72, 32, 26, 12, "residual(R) >\nself-derived limit (340) ?", VAL, 7.8)
    box(ax, 106, 36, 24, 8, "no: R retained", GRY, 7.8)
    box(ax, 72, 12, 26, 12, "Repair proposer (620)\ntightest recovered relation\n"
        "sharing >= 2 detectors of R", VAL, 7.4)
    box(ax, 106, 12, 24, 12, "Rewrite constraint set\n(840): replace R by\nthe repair",
        ENF, 7.6)
    box(ax, 36, 12, 28, 12, "Relation store (400)\nrecovered from the\nsame counts", VAL, 7.8)
    arrow(ax, (28, 38), (36, 38))
    arrow(ax, (64, 38), (72, 38))
    arrow(ax, (98, 40), (106, 40))
    arrow(ax, (85, 32), (85, 24))
    arrow(ax, (64, 18), (72, 18))
    arrow(ax, (98, 18), (106, 18))
    ax.text(88, 27.5, "yes: flag", fontsize=8, color=ENF, fontweight="bold")
    ax.text(66, 3.5, "No threshold is taken from the map or tuned on corrupted maps: the "
            "limit is the one the recovery itself obeys.", ha="center", fontsize=7.8,
            color=GRY, style="italic")
    save(fig, "fig06.png", 200, "map audit")


# ---------------------------------------------------------------- Figure 7
def fig07():
    m25, m1 = load("discovery_v2_full_M25_A.json"), load("discovery_v2_M1_A.json")
    fig, axs = plt.subplots(1, 2, figsize=(12.6, 4.2))
    for ax, d, name in ((axs[0], m25, "M25"), (axs[1], m1, "M1")):
        sizes = sorted(d["recall_by_size"], key=int)
        rec = [d["recall_by_size"][s]["recovered"] for s in sizes]
        tot = [d["recall_by_size"][s]["of"] for s in sizes]
        x = np.arange(len(sizes))
        ax.bar(x, tot, color="#CFD8DC", edgecolor=GRY, label="surveyed relations")
        ax.bar(x, rec, color=VAL, width=0.55, label="recovered exactly, no map")
        for xi, r, t in zip(x, rec, tot):
            ax.text(xi, t + max(tot) * 0.02, "%d / %d" % (r, t), ha="center", fontsize=8.5)
        ax.set_xticks(x)
        ax.set_xticklabels(["%s detectors\n(%s)" % (s, "plain continuity" if s == "2"
                                                     else "junction with slip road")
                            for s in sizes], fontsize=8)
        ax.set_ylabel("relations")
        ax.set_title("%s: judged precision %.1f%%, limit %.2f%% of flow" %
                     (name, 100 * d["judged_precision"], d["meta"]["limit_pct"]),
                     fontsize=9.5, fontweight="bold")
        ax.legend(fontsize=7.8, frameon=False)
        ax.set_ylim(0, max(tot) * 1.15)
    fig.tight_layout()
    save(fig, "fig07.png", 300, "recovery by relation size")


# ---------------------------------------------------------------- Figure 8
def fig08():
    m25, m1 = load("discovery_v2_full_M25_A.json"), load("discovery_v2_M1_A.json")
    cfgs = [("prior_only", "prior only"), ("surveyed", "surveyed map"),
            ("recovered", "recovered, no map"), ("both", "surveyed + recovered")]
    cols = [GRY, HWC, VAL, PRC]
    fig, axs = plt.subplots(1, 2, figsize=(12.6, 4.0))
    for metric, ax, lab in (("MAE", axs[0], "MAE, vehicles per interval"),
                            ("outside", axs[1], "node-intervals outside band, %")):
        w = 0.2
        top_all = max(max(m25["configs"][k][metric], m1["configs"][k][metric])
                      for k, _ in cfgs)
        for k, ((key, name), col) in enumerate(zip(cfgs, cols)):
            vals = [m25["configs"][key][metric], m1["configs"][key][metric]]
            xs = np.arange(2) + (k - 1.5) * w
            ax.bar(xs, vals, w, color=col, label=name)
            for xv, v in zip(xs, vals):
                ax.text(xv, v + top_all * 0.015, "%.2f" % v, ha="center", fontsize=6.6,
                        va="bottom")
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["M25 clockwise, 367 detectors", "M1, 186 detectors"])
        ax.set_ylabel(lab)
        ax.set_ylim(0, top_all * 1.35)
    for ax in axs:
        ax.legend(fontsize=7.4, frameon=False, ncol=4, loc="upper center",
                  handlelength=1.2, columnspacing=1.0)
    axs[0].set_title("(a) Accuracy on withheld records", fontsize=9.5, fontweight="bold")
    axs[1].set_title("(b) Physical consistency", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig08.png", 300, "reconstruction by constraint set")


# ---------------------------------------------------------------- Figure 9
def fig09():
    a25, a1 = load("map_audit_full_M25_A.json"), load("map_audit_M1_A.json")
    kinds = ["sign_flip", "drop_member", "wrong_site", "extra_member"]
    names = ["slip sign\nreversed", "slip member\nomitted", "wrong site\nidentifier",
             "spurious member\nadded"]
    fig, axs = plt.subplots(1, 2, figsize=(12.6, 4.0), sharey=True)
    for ax, a, nm in ((axs[0], a25, "M25"), (axs[1], a1, "M1")):
        x = np.arange(len(kinds))
        det = [100 * a["kinds"][k]["detection_rate"] for k in kinds]
        rep = [100 * a["kinds"][k]["repair_rate"] for k in kinds]
        n = [a["kinds"][k]["trials"] for k in kinds]
        ax.bar(x - 0.18, det, 0.36, color=VAL, label="flagged")
        ax.bar(x + 0.18, rep, 0.36, color=HWC, label="repaired exactly")
        for xi, d, r, ni in zip(x, det, rep, n):
            ax.text(xi - 0.18, d + 1.5, "%.0f" % d, ha="center", fontsize=7.6)
            ax.text(xi + 0.18, r + 1.5, "%.0f" % r, ha="center", fontsize=7.6)
        ax.set_xticks(x)
        ax.set_xticklabels(["%s\n(n=%d)" % (nm_, ni) for nm_, ni in zip(names, n)],
                           fontsize=8)
        ax.set_ylim(0, 122)
        ctl = a["control"]
        ax.set_title("%s: uncorrupted map, %d of %d relations over the limit" %
                     (nm, ctl["false_flags"], ctl["evaluable"]), fontsize=9.2,
                     fontweight="bold")
    axs[0].set_ylabel("% of injected map errors")
    axs[0].legend(fontsize=7.8, frameon=False, loc="upper center", ncol=2)
    fig.tight_layout()
    save(fig, "fig09.png", 300, "map audit")


# ---------------------------------------------------------------- Figure 10
def fig10():
    s, r = load("faults_fpcontrol_M25_A.json"), load("faults_recovered_M25_A.json")

    def series(d, mode):
        cs = sorted([c for c in d["cases"] if c["mode"] == mode], key=lambda c: c["magnitude"])
        return [c["magnitude"] for c in cs], [100 * c["attribution_top1"] for c in cs], \
            [100 * c["detection_rate"] for c in cs]
    fig, axs = plt.subplots(1, 2, figsize=(12.6, 4.0), sharey=True)
    for ax, mode, xl in ((axs[0], "scale", "injected scale factor"),
                         (axs[1], "offset", "injected offset, vehicles per interval")):
        for d, col, nm in ((s, HWC, "surveyed map, %d relations" % s["nodes_fitted"]),
                           (r, VAL, "recovered, no map, %d relations" % r["nodes_fitted"])):
            x, a1, dt = series(d, mode)
            if mode == "scale":
                x = [100 * (v - 1) for v in x]
            ax.plot(x, a1, "o-", color=col, lw=1.4, ms=4, label=nm + ": correct detector 1st")
            ax.plot(x, dt, "s--", color=col, lw=0.9, ms=3, alpha=0.6, label=nm + ": detected")
        ax.set_xlabel(xl if mode == "offset" else "injected scale error, %")
        ax.axvline(0, color="#B0BEC5", lw=0.8)
        ax.set_ylim(0, 105)
    axs[0].set_ylabel("% of trials")
    axs[0].legend(fontsize=7, frameon=False, loc="lower left")
    axs[0].set_title("(a) Proportional miscount", fontsize=9.5, fontweight="bold")
    axs[1].set_title("(b) Constant offset", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig10.png", 300, "fault attribution, surveyed vs recovered")


# ---------------------------------------------------------------- Figure 11
def fig11():
    fig, ax = plt.subplots(figsize=(13.0, 6.2))
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 62)
    ax.axis("off")
    ind = [(6, "Claim 1 (independent)\nrelations recovered from\nthe counts; record "
               "restored\nunder them as hard constraints", VAL,
            "2 observed-only   3 union with map\n4 slip relations   5 per-network\n"
            "6, 7 constants (fallbacks)\n8 nearest-feasible   9 recurs across periods\n"
            "10 certified interval   11 irreconcilable\n12 map audit"),
           (48, "Claim 13 (independent)\nmiscounting instrument named\non recovered "
                "relations only;\nits record corrected", VAL,
            "14 substitution where the\nfault is not typed\n15 maintenance record\n"
            "16 every relation deviates\n17 constants (fallback)"),
           (90, "Claim 18 (independent)\nsystem: instruments, link,\narchive, processor; "
                "\nrestored record written back", HWC,
            "19 record correction\n20 map audit\n21 supply to traffic-control\ncomputer\n"
            "22 inductive loops")]
    for x, txt, col, deps in ind:
        box(ax, x, 36, 34, 18, txt, col, 7.8)
        box(ax, x, 4, 34, 22, deps, "#ECEFF1", 7.6, "black", bold=False)
        arrow(ax, (x + 17, 36), (x + 17, 26))
    ax.text(65, 59, "A: Claims 1-12   B: Claims 13-17   C: Claims 18-22", ha="center",
            fontsize=8.8, color=GRY, fontweight="bold")
    save(fig, "fig11.png", 200, "claim tree")


# ---------------------------------------------------------------- Figure 12
def fig12():
    d25, d1 = load("correction_M25_A.json"), load("correction_M1_A.json")
    fig, axs = plt.subplots(1, 2, figsize=(12.6, 4.0), sharey=False)
    for ax, d, nm in ((axs[0], d25, "(a) M25, recovered relations"),
                      (axs[1], d1, "(b) M1, recovered relations")):
        cs = [c for c in d["cases"] if c["mode"] != "none"]
        lab = []
        for c in cs:
            if c["mode"] == "scale":
                lab.append("%+d %%" % round(100 * (c["magnitude"] - 1)))
            elif c["mode"] == "offset":
                lab.append("%+d veh" % c["magnitude"])
            else:
                lab.append("stuck")
        x = np.arange(len(cs))
        ax.bar(x - 0.2, [c["mae_before"] for c in cs], 0.4, color="#B0BEC5",
               label="output as received (faulted)")
        ax.bar(x + 0.2, [c["mae_after"]["auto"] for c in cs], 0.4, color=VAL,
               label="output after correction")
        ax.set_yscale("log")
        ax.set_xticks(x)
        ax.set_xticklabels(lab, rotation=45, fontsize=7.5)
        ax.set_title(nm, fontsize=9.5, fontweight="bold")
    axs[0].set_ylabel("MAE of the faulty detector's output\nvs its clean record, vehicles")
    axs[0].legend(fontsize=7.5, frameon=False, loc="upper center")
    fig.tight_layout()
    save(fig, "fig12.png", 300, "detector output correction")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    fig01(); fig02(); fig03()
    w = fig04()
    with open(os.path.join(RESULTS, "idfb_fig04_example.json"), "w", encoding="utf-8") as fh:
        json.dump(w, fh, indent=1)
    fig05(); fig06(); fig07(); fig08(); fig09(); fig10(); fig11(); fig12()
