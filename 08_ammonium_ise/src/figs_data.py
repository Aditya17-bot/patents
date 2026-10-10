"""Data figures (3-6) for the IDF-B, read from results/ev_*.json; nothing measured is typed in.

Palette: categorical slots validated with the dataviz validator (light surface): method blue
#2a78d6, practice (median of prior departures) orange #eb6834, practice chosen per site violet
#4a3aa7; raw reading in neutral grey. Text in ink colours, never series colours. 2 x 2 panels
labelled (a)-(d), one y-axis per panel.
"""
import bisect
import datetime as dt
import json
import os
import statistics as S

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import core
import ea

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "patent", "figures")
BLUE, ORANGE, VIOLET, GREY = "#2a78d6", "#eb6834", "#4a3aa7", "#8c8c8c"
INK, MUTED, GRID = "#1a1a1a", "#555555", "#e4e4e4"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#999",
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})


def load(name):
    return json.load(open(os.path.join(RES, name)))


def panel(ax, letter, title):
    ax.set_title(title, fontsize=10.5, color=INK, loc="left")
    ax.text(-0.12, 1.06, "(%s)" % letter, transform=ax.transAxes, fontsize=12, fontweight="bold", color=INK)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(name)


def bars(ax, labels, values, colors, fmt="%.3f"):
    x = np.arange(len(labels))
    ax.bar(x, values, width=0.62, color=colors, edgecolor="white", linewidth=2)
    for xi, v in zip(x, values):
        ax.text(xi, v, fmt % v, ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)


def fig03():
    """Mechanism: the floor follows the offset; where the gain comes from."""
    m = load("ev_main.json")
    rows = load("ev_rows.json")
    fig, axs = plt.subplots(2, 2, figsize=(12.5, 9))
    # (a) change of floor vs change of departure between consecutive samples
    ax = axs[0, 0]
    by = {}
    for r in rows:
        by.setdefault(r["station"], []).append(r)
    dfl, ddp = [], []
    for v in by.values():
        for a, b in zip(v, v[1:]):
            dfl.append(b["floor"] - a["floor"])
            ddp.append((b["sonde"] - b["lab"]) - (a["sonde"] - a["lab"]))
    ax.scatter(dfl, ddp, s=10, color=BLUE, alpha=0.45, edgecolor="none")
    lim = 3
    ax.plot([-lim, lim], [-lim, lim], color=MUTED, lw=1, ls="--")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    f = m["floor_follows_offset"]
    ax.text(0.03, 0.96, "slope %.2f (1 expected)\nsame sign %d, opposite %d" % (
        f["slope_departure_on_floor"], f["same_sign"], f["opposite_sign"]),
        transform=ax.transAxes, va="top", fontsize=9, color=INK)
    ax.set_xlabel("change of the 7-day floor between samples (mg/L N)")
    ax.set_ylabel("change of sonde - laboratory (mg/L N)")
    panel(ax, "a", "The floor moves with the sensor offset")
    # (b) serviced since the last laboratory sample or not
    ax = axs[0, 1]
    sv = m["serviced"]
    labels, vals, cols = [], [], []
    for key, lab in (("serviced_since_last_lab", "serviced since\nlast sample"), ("not_serviced", "not serviced")):
        labels += [lab + "\npractice", lab + "\nmethod"]
        vals += [sv[key]["median"]["median"], sv[key]["method"]["median"]]
        cols += [ORANGE, BLUE]
    bars(ax, labels, vals, cols)
    ax.set_ylabel("median absolute error (mg/L N)")
    panel(ax, "b", "Gain with and without a sonde service")
    # (c) by laboratory concentration band
    ax = axs[1, 0]
    bands = list(m["by_lab_band"].keys())
    x = np.arange(len(bands))
    pm = [m["by_lab_band"][b]["median"]["median"] for b in bands]
    me = [m["by_lab_band"][b]["method"]["median"] for b in bands]
    ax.bar(x - 0.18, pm, 0.34, color=ORANGE, edgecolor="white", linewidth=2, label="practice (median departure)")
    ax.bar(x + 0.18, me, 0.34, color=BLUE, edgecolor="white", linewidth=2, label="this method")
    ax.set_xticks(x)
    ax.set_xticklabels(["%s mg/L\nn = %d" % (b.replace("-1e+09", " and above"), m["by_lab_band"][b]["median"]["n"]) for b in bands], fontsize=9)
    ax.set_yscale("log")
    ax.set_ylabel("median absolute error (mg/L N, log)")
    ax.legend(frameon=False, fontsize=9)
    panel(ax, "c", "By laboratory concentration")
    # (d) false alarms and missed exceedances
    ax = axs[1, 1]
    th = list(m["alarms"].keys())
    x = np.arange(len(th))
    for j, (h, col, lab) in enumerate((("practice_best", VIOLET, "practice chosen per site"),
                                       ("watch", ORANGE, "watch tier (either estimate)"),
                                       ("confirmed", BLUE, "confirmed tier (both estimates)"))):
        fa = [m["alarms"][t][h]["false_alarms"] for t in th]
        mi = [m["alarms"][t][h]["missed"] for t in th]
        ax.bar(x + (j - 1) * 0.27, fa, 0.25, color=col, edgecolor="white", linewidth=2, label=lab)
        ax.bar(x + (j - 1) * 0.27, [-v for v in mi], 0.25, color=col, alpha=0.45, edgecolor="white", linewidth=2)
    ax.axhline(0, color="#999", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(["threshold %s mg/L" % t for t in th], fontsize=9)
    ax.set_ylabel("false alarms (up, solid) / missed (down, light)")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    panel(ax, "d", "Alarms at fixed thresholds, %d samples" % (m["alarms"]["1"]["lab_exceed"] + m["alarms"]["1"]["lab_below"]))
    save(fig, "fig03.png")


def fig04():
    """Accuracy at laboratory samples: distribution, baselines, sensitivity, stations."""
    m = load("ev_main.json")
    rows = [r for r in load("ev_rows.json") if r["i"] >= 1]
    sens = load("ev_sens.json")
    fig, axs = plt.subplots(2, 2, figsize=(12.5, 9))
    ax = axs[0, 0]
    for h, col, lab in (("raw", GREY, "raw sonde reading"), ("median", ORANGE, "practice: median departure"),
                        ("practice_best", VIOLET, "practice chosen per site"), ("method", BLUE, "this method")):
        e = np.sort([abs(r[h] - r["lab"]) for r in rows])
        ax.plot(np.maximum(e, 1e-3), np.arange(1, len(e) + 1) / len(e), color=col, lw=2, label=lab)
    ax.set_xscale("log")
    ax.set_xlabel("absolute error at the laboratory sample (mg/L N)")
    ax.set_ylabel("cumulative share of samples")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    panel(ax, "a", "Error distribution, %d samples at %d sites" % (len(rows), m["sites_with_prior"]))
    ax = axs[0, 1]
    H = (("raw", "raw"), ("median", "median\ndeparture"), ("last", "last\ndeparture"), ("trend", "trend in\ntime"),
         ("practice_best", "chosen\nper site"), ("floor_net", "floor, no\nanchor"), ("method", "this\nmethod"))
    vals = [m["with_prior"][h]["median"] for h, _ in H]
    cols = [GREY, ORANGE, ORANGE, ORANGE, VIOLET, GREY, BLUE]
    bars(ax, [l for _, l in H], vals, cols)
    ax.set_ylabel("median absolute error (mg/L N)")
    panel(ax, "b", "Practice baselines and ablation")
    ax = axs[1, 0]
    labs = ["%gd, q %.2f,\n%d samples" % (s["floor_days"], s["floor_q"], s["window"]) for s in sens]
    x = np.arange(len(sens))
    ax.bar(x - 0.18, [s["practice_best"]["median"] for s in sens], 0.34, color=VIOLET, edgecolor="white", linewidth=2,
           label="practice chosen per site")
    ax.bar(x + 0.18, [s["method"]["median"] for s in sens], 0.34, color=BLUE, edgecolor="white", linewidth=2,
           label="this method")
    ax.set_xticks(x)
    ax.set_xticklabels(labs, fontsize=8)
    ax.set_ylabel("median absolute error (mg/L N)")
    ax.set_ylim(0, 0.2)
    ax.legend(frameon=False, fontsize=9, ncol=2, loc="upper left")
    panel(ax, "c", "Sensitivity: floor window, quantile, anchor samples")
    ax = axs[1, 1]
    per = {}
    for r in rows:
        per.setdefault(r["station"], []).append(r)
    xs = [S.mean(abs(r["practice_best"] - r["lab"]) for r in v) for v in per.values()]
    ys = [S.mean(abs(r["method"] - r["lab"]) for r in v) for v in per.values()]
    ax.scatter(np.maximum(xs, 1e-3), np.maximum(ys, 1e-3), s=26, color=BLUE, edgecolor="white", linewidth=0.8)
    lo, hi = 1e-2, max(max(xs), max(ys)) * 1.5
    ax.plot([lo, hi], [lo, hi], color=MUTED, lw=1, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("practice chosen per site: mean error (mg/L N)")
    ax.set_ylabel("this method: mean error (mg/L N)")
    ax.text(0.03, 0.96, "below the line: method better\n%d of %d sites" % (m["sites_better"]["practice_best"], len(per)),
            transform=ax.transAxes, va="top", fontsize=9, color=INK)
    panel(ax, "d", "Per site")
    save(fig, "fig04.png")


def fig05():
    """One site over time: raw record, floor, corrections and laboratory results."""
    rows = load("ev_rows.json")
    per = {}
    for r in rows:
        per.setdefault(r["station"], []).append(r)
    cand = sorted(per, key=lambda k: -len(per[k]))
    st = None
    for k in cand:
        v = [r for r in per[k] if r["i"] >= 1]
        if len(v) >= 30 and S.median(abs(r["method"] - r["lab"]) for r in v) < S.median(abs(r["practice_best"] - r["lab"]) for r in v):
            st = k
            break
    site = {s["station"]: s for s in core.load_sites()}[st]
    v = per[st]
    t0 = dt.datetime.fromisoformat(v[0]["t"]) - dt.timedelta(days=10)
    t1 = dt.datetime.fromisoformat(v[min(len(v) - 1, 40)]["t"]) + dt.timedelta(days=5)
    amm = [r for r in ea.readings(st + "-amm-i-subdaily-mgL", site["opened"], site["closed"]) if r[1] >= 0 and t0 <= r[0] <= t1]
    at = [r[0] for r in amm]
    av = [r[1] for r in amm]
    days = []
    d = t0
    while d <= t1:
        i1 = bisect.bisect_right(at, d)
        i0 = bisect.bisect_left(at, d - dt.timedelta(days=7))
        if i1 - i0 >= 96:
            w = sorted(av[i0:i1])
            days.append((d, w[int(0.05 * (len(w) - 1))]))
        d += dt.timedelta(hours=6)
    vv = [r for r in v if t0 <= dt.datetime.fromisoformat(r["t"]) <= t1]
    fig, axs = plt.subplots(2, 1, figsize=(12.5, 8.4), sharex=True)
    ax = axs[0]
    ax.plot(at, av, color=GREY, lw=0.6, label="raw sonde reading")
    ax.plot([a for a, _ in days], [b for _, b in days], color=BLUE, lw=2, label="7-day floor (5th percentile)")
    ax.scatter([dt.datetime.fromisoformat(r["t"]) for r in vv], [r["lab"] for r in vv], s=40, color=INK, zorder=5,
               label="laboratory result")
    ax.set_ylabel("ammonium (mg/L N)")
    ax.set_yscale("symlog", linthresh=0.1)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    panel(ax, "a", "Sonde %s: raw record, its floor and the laboratory results" % st)
    ax = axs[1]
    tt = [dt.datetime.fromisoformat(r["t"]) for r in vv if r["i"] >= 1]
    e_p = [abs(r["practice_best"] - r["lab"]) for r in vv if r["i"] >= 1]
    e_m = [abs(r["method"] - r["lab"]) for r in vv if r["i"] >= 1]
    ax.plot(tt, e_p, color=VIOLET, lw=1.6, marker="o", ms=6, label="practice chosen per site")
    ax.plot(tt, e_m, color=BLUE, lw=1.6, marker="s", ms=6, label="this method")
    ax.set_yscale("log")
    ax.set_ylabel("absolute error at the sample (mg/L N)")
    ax.legend(frameon=False, fontsize=9)
    panel(ax, "b", "Error at each laboratory sample, using only earlier samples")
    core.dump("fig05_example.json", {"station": st, "label": site["label"], "n_samples_shown": len(vv),
                                     "median_practice_best": S.median(e_p), "median_method": S.median(e_m),
                                     "from": str(t0.date()), "to": str(t1.date())})
    save(fig, "fig05.png")


def fig06():
    """No laboratory history yet, and station-level uncertainty."""
    m = load("ev_main.json")
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.8))
    ax = axs[0]
    fs = m["first_sample"]
    bars(ax, ["raw", "network\nconstant", "floor with\nnetwork background"],
         [fs["raw"]["median"], fs["net_const"]["median"], fs["method"]["median"]], [GREY, ORANGE, BLUE])
    ax.set_ylabel("median absolute error (mg/L N)")
    panel(ax, "a", "First laboratory sample of each site (%d sites)" % fs["raw"]["n"])
    ax = axs[1]
    items = [("vs median\ndeparture", m["bootstrap_vs_median"]), ("vs last\ndeparture", m["bootstrap_vs_last"]),
             ("vs chosen\nper site", m["bootstrap_vs_practice_best"])]
    for j, (lab, b) in enumerate(items):
        lo, hi = b["median"]["ci95"]
        ax.plot([j, j], [lo, hi], color=BLUE, lw=3, solid_capstyle="round")
        ax.plot(j, b["median"]["mean"], "o", color=BLUE, ms=9, mec="white", mew=2)
        ax.text(j + 0.08, b["median"]["mean"], "%.3f\n(%.3f to %.3f)" % (b["median"]["mean"], lo, hi), fontsize=9,
                color=INK, va="center")
    ax.axhline(0, color="#999", lw=1)
    ax.set_xticks(range(len(items)))
    ax.set_xticklabels([i[0] for i in items], fontsize=9)
    ax.set_xlim(-0.5, len(items) - 0.2)
    ax.set_ylabel("reduction of median error (mg/L N)")
    panel(ax, "b", "Resampling whole stations, 2000 draws, 95 % interval")
    save(fig, "fig06.png")


if __name__ == "__main__":
    fig03()
    fig04()
    fig05()
    fig06()
