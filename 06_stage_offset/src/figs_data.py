"""Flowchart, data figures and claim tree (imported by make_figs.py)."""
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

import importlib.util
import os
_spec = importlib.util.spec_from_file_location(
    "p4_make_figs", os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_figs.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

zone, arr, poly, pbox, diamond, panel, tidy, depbox = (
    M.zone, M.arr, M.poly, M.pbox, M.diamond, M.panel, M.tidy, M.depbox)
Z_IN, Z_CORE, Z_RED, Z_PROC, Z_OUT = M.Z_IN, M.Z_CORE, M.Z_RED, M.Z_PROC, M.Z_OUT
YES_C, NO_C, C = M.YES_C, M.NO_C, M.C
load, save = M.load, M.save
FT = 0.3048         # metres per foot: the USGS records are in feet, the figures in metres


def fig02():
    """Flowchart of the method (claims 1 and 2)."""
    fig, ax = plt.subplots(figsize=(14, 19))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 19)
    ax.axis("off")
    bands = [(15.3, 3.5, Z_IN, "INPUT"), (9.3, 5.8, Z_CORE, "ESTIMATION"),
             (5.6, 3.5, Z_PROC, "DECISION"), (0.4, 5.0, Z_RED, "ACTION")]
    for y, h, col, lab in bands:
        ax.add_patch(FancyBboxPatch((0.2, y), 0.9, h, boxstyle="round,pad=0.04",
                                    facecolor=col[0], edgecolor=col[0], zorder=2))
        ax.text(0.65, y + h / 2, lab, rotation=90, color="white", fontsize=11,
                fontweight="bold", ha="center", va="center", zorder=3)
    X = 7.2
    steps = [
        (17.9, "S1  Receive stage h(t) from stage sensor 110 of station 100 over link 130;\n"
               "base rating R; offsets s(P), s(N) measured at field visits 600", Z_IN),
        (16.2, "S2  Receive discharge Q_Y(t) of neighbouring station 120; admit the pair:\n"
               "travel-time lag tau, coupling of daily ln Q >= threshold", Z_IN),
        (14.3, "S3  Each steady interval: y = ln Q_Y(t - tau) - ln R(h(t)),\n"
               "x = d ln R / dh at h(t)  (a stage offset moves y in proportion to x)", Z_CORE),
        (12.4, "S4  Stage-unit discrepancy of each window: D = sum(x y) / sum(x^2)\n"
               "windows after P, before and after t, before N", Z_CORE),
        (10.5, "S5  Gain g = regression of measured on estimated departures\n"
               "over the station's earlier visits (prior 0.5, limits 0 to 1.2)", Z_CORE),
    ]
    for y, t, col in steps:
        pbox(ax, X, y, 11.0, 1.25, t, col, fs=9.6)
    for (y1, _, _), (y2, _, _) in zip(steps, steps[1:]):
        arr(ax, (X, y1 - 0.66), (X, y2 + 0.66), color="#333")
    diamond(ax, X, 7.4, 6.4, 2.4, "Visit N already\nmeasured?", Z_PROC, fs=10.5)
    arr(ax, (X, 9.84), (X, 8.62), color="#333")
    pbox(ax, 4.0, 4.0, 5.6, 2.2, "S6a  Record between visits (claim 1)\n"
         "s(t) = s_lin(t) + g [D(t) - D_lin(t)]\nlinear in time between s(P), s(N)\n"
         "plus the neighbour's departure", Z_RED, fs=9.4)
    pbox(ax, 10.4, 4.0, 5.6, 2.2, "S6b  Real time (claim 2)\n"
         "s(t) = s(P) + g [D(t) - D(P)]\nfrom data before t only", Z_RED, fs=9.4)
    poly(ax, [(X - 3.2, 7.4), (4.0, 7.4), (4.0, 5.15)], color=YES_C, label="YES",
         lpos=(3.6, 6.5), lcolor=YES_C)
    poly(ax, [(X + 3.2, 7.4), (10.4, 7.4), (10.4, 5.15)], color=NO_C, label="NO",
         lpos=(10.8, 6.5), lcolor=NO_C)
    pbox(ax, X, 1.35, 11.0, 1.3, "S7  Q(t) = R(h(t) + s(t)) written to archive 410; offset in force\n"
         "sent over link 130 to data logger 115, which applies R(h + s) on site", Z_RED, fs=9.6)
    arr(ax, (4.0, 2.88), (5.2, 2.02), color="#333")
    arr(ax, (10.4, 2.88), (9.2, 2.02), color="#333")
    save(fig, "fig02.png", 200, "flowchart")


def _rows(d, min_c):
    return [w for r in d["results"] if r.get("rows") and r.get("coupling", 0) >= min_c
            for w in r["rows"]]


def fig03():
    """Physics and sensitivity: rating log-slope, injected offsets, departures."""
    import core
    import usgs
    d = load("daily.json")
    e1 = load("e1_interpolation.json")
    e3 = load("e3_injection.json")
    mc = e1["meta"]["min_coupling"]
    rows = _rows(d, mc)
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    ex = max((r for r in d["results"] if r.get("rows") and r.get("coupling", 0) >= mc),
             key=lambda r: len(r["rows"]))
    rat = core.Rating(usgs.rating(ex["x"], "exsa")["table"])
    g = np.linspace(rat.gmin + 0.3, rat.gmax - 0.3, 400)
    sl = rat.slope(g, dg=0.25)   # smoothed over +-0.25 ft for display (table is rounded)
    ax = axs[0, 0]
    ax.plot(g * FT, sl / FT, color=C[0], lw=2)
    ax.fill_between(g * FT, 0, sl / FT, color=C[0], alpha=0.15)
    ax.set_xlabel("effective stage g = h + s (m)")
    ax.set_ylabel("rating log-slope x = d ln R / dh  (1/m)")
    lo, hi = float(np.nanmax(sl[:40])), float(np.nanmin(sl[-40:]))
    ax.set_title("Base rating of station %s: a 0.03 m offset moves discharge\n"
                 "by %.0f %% near the bottom of the rating and %.0f %% near the top"
                 % (ex["x"], 100 * (math.exp(0.1 * lo) - 1), 100 * (math.exp(0.1 * hi) - 1)),
                 fontsize=10.5)
    panel(ax, "a")
    tidy(ax)
    ax = axs[0, 1]
    sel = [w for w in rows if "0.10" in w.get("inj", {})]
    xs = np.array([w["x_T_med"] / FT for w in sel])
    ax.scatter(xs, [FT * w["inj"]["0.10"] for w in sel], s=14, color=C[0], alpha=0.6,
               label="stage units (m): this method, CV %.2f" % e3["0.10"]["stage_units_cv"])
    ax.scatter(xs, [w["inj"]["ratio_0.10"] for w in sel], s=14, color=C[1], alpha=0.5,
               label="discharge ratio (ln units), CV %.2f" % e3["0.10"]["ratio_change_cv"])
    ax.axhline(0.10 * FT, color="#333", ls="--", lw=1)
    ax.set_xscale("log")
    ax.set_xlabel("median rating log-slope in the window (1/m)")
    ax.set_ylabel("response to a 0.030 m injected stage offset")
    ax.set_title("Injected offset: the stage-unit response does not depend on stage", fontsize=10.5)
    ax.legend(fontsize=9)
    panel(ax, "b")
    tidy(ax)
    ax = axs[1, 0]
    for inj, col in (("0.10", C[0]), ("0.30", C[3])):
        v = [FT * w["inj"][inj] for w in rows if inj in w.get("inj", {})]
        ax.hist(np.clip(v, -0.015, 0.18), bins=np.linspace(-0.015, 0.18, 66), color=col, alpha=0.6,
                edgecolor="white", linewidth=1.2,
                label="injected %.3f m: median %.3f m" % (FT * float(inj), FT * e3[inj]["median_ft"]))
        ax.axvline(FT * float(inj), color=col, ls="--")
    ax.set_xlim(-0.015, 0.18)
    ax.set_xlabel("recovered offset change (m)")
    ax.set_ylabel("visit intervals")
    ax.legend(fontsize=9)
    ax.set_title("Recovery of stage offsets injected into real records (n = %d)" % e3["0.10"]["n"],
                 fontsize=10.5)
    panel(ax, "c")
    tidy(ax)
    ax = axs[1, 1]
    rec = e1["records"]
    a = np.array([FT * q["gain"] * q["dev"] for q in rec])
    b = np.array([FT * q["true_dev"] for q in rec])
    ax.scatter(a, b, s=12, color=C[4], alpha=0.35, label="field visit")
    # mean measured departure in bins of the estimate (deciles of the non-zero estimates)
    qs = np.percentile(a, np.linspace(0, 100, 11))
    bx, by = [], []
    for lo_, hi_ in zip(qs[:-1], qs[1:]):
        m = (a >= lo_) & (a <= hi_)
        if m.sum() >= 10:
            bx.append(float(np.mean(a[m])))
            by.append(float(np.mean(b[m])))
    ax.plot(bx, by, color="#1A1A1A", lw=2.2, marker="o", ms=6, label="mean per decile of the estimate")
    ax.legend(fontsize=9, loc="upper left")
    lim = float(np.percentile(np.abs(np.concatenate([a, b])), 98))
    ax.plot([-lim, lim], [-lim, lim], color="#333", ls="--", lw=1)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel("estimated departure g [s_raw(t) - s_lin(t)] (m)")
    ax.set_ylabel("measured offset minus linear interpolation (m)")
    ax.set_title("Departure from time interpolation at %d field visits (r = %.2f)"
                 % (e1["published"]["n"], e1["published"]["r_dev"]), fontsize=10.5)
    panel(ax, "d")
    tidy(ax)
    fig.tight_layout()
    save(fig, "fig03.png", 300, "physics and sensitivity")


def _bars(ax, groups, title):
    labs = list(groups)
    w = 0.36
    for j, (key, col, name) in enumerate((("baseline", C[1], "baseline"),
                                          ("method", C[0], "this method"))):
        vals = [groups[g][key]["mean"] for g in labs]
        p = ax.bar(np.arange(len(labs)) + (j - 0.5) * w, vals, w, color=col, edgecolor="white",
                   linewidth=1.2, label=name)
        for rect, v in zip(p, vals):
            ax.text(rect.get_x() + rect.get_width() / 2, v + 0.3, "%.1f" % v, ha="center",
                    fontsize=8.5)
    ax.set_xticks(np.arange(len(labs)))
    ax.set_xticklabels(labs, fontsize=9)
    ax.set_ylabel("mean absolute discharge error (%)")
    ax.set_title(title, fontsize=10.5)
    ax.legend(fontsize=9)
    tidy(ax)


def fig04():
    """Accuracy at field visits."""
    e1 = load("e1_interpolation.json")
    e2 = load("e2_realtime.json")
    e4 = load("e4_ablation.json")
    rec = e1["records"]
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    ax = axs[0, 0]
    for k, col, lab in (("e_lin", C[1], "linear time interpolation (current practice)"),
                        ("e_hat", C[0], "with neighbour departure (this method)")):
        v = np.sort([max(q[k], 0.01) for q in rec])
        ax.plot(v, np.arange(1, len(v) + 1) / len(v), color=col, lw=2.2, label=lab)
    ax.set_xscale("log")
    ax.set_xlabel("absolute discharge error at the field visit (%)")
    ax.set_ylabel("cumulative share of visits")
    ax.set_title("Record between visits: %d visits at %d stations"
                 % (e1["published"]["n"], e1["published"]["targets"]), fontsize=10.5)
    ax.legend(fontsize=9)
    panel(ax, "a")
    tidy(ax)
    _bars(axs[0, 1], {"all visits": e1["published"]["all"],
                      "open water": e1["published"]["open_water"],
                      "departure\n>= 0.03 m": e1["published"]["big"],
                      "all, real-time\nreference": e1["realtime"]["all"]},
          "Record between visits; baseline = linear time interpolation")
    panel(axs[0, 1], "b")
    _bars(axs[1, 0], {"all visits,\nreal-time ref.": e2["realtime"]["all"],
                      "open water,\nreal-time ref.": e2["realtime"]["open_water"],
                      "change >= 0.03 m,\nreal-time ref.": e2["realtime"]["big"],
                      "all visits,\nfinal ref.": e2["published"]["all"]},
          "Real time; baseline = last measured offset carried forward")
    panel(axs[1, 0], "c")
    ax = axs[1, 1]
    labs = ["linear_time", "practice_per_station", "no_ratio_term", "ratio_units", "stage_units_no_gain",
            "stage_units_gain"]
    names = ["linear in\ntime", "practice chosen\nper station", "no flow-\nratio term", "ratio\nunits",
             "stage units,\ng = 1", "stage units,\ngain (claim 5)"]
    for j, (grp, col, lab) in enumerate(((e4["all"], C[2], "all visits"),
                                         (e4["open_water"], C[4], "open water"),
                                         (e4["big"], C[3], "departure >= 0.03 m"))):
        vals = [grp[k]["mean"] for k in labs]
        p = ax.bar(np.arange(len(labs)) + (j - 1) * 0.27, vals, 0.27, color=col, edgecolor="white",
                   linewidth=1.2, label=lab)
        for rect, v in zip(p, vals):
            ax.text(rect.get_x() + rect.get_width() / 2, v + 0.3, "%.0f" % v, ha="center",
                    fontsize=7.5)
    ax.set_xticks(np.arange(len(labs)))
    ax.set_xticklabels(names, fontsize=8.5)
    ax.set_ylabel("mean absolute discharge error (%)")
    ax.set_title("Baselines and ablation on the same visits", fontsize=10.5)
    ax.legend(fontsize=9)
    tidy(ax)
    panel(ax, "d")
    fig.tight_layout()
    save(fig, "fig04.png", 300, "accuracy")


def fig_claims():
    """Claim tree."""
    fig, ax = plt.subplots(figsize=(17, 7.0))
    ax.set_xlim(0, 34)
    ax.set_ylim(0, 13.6)
    ax.axis("off")
    zone(ax, 0.4, 7.4, 21.6, 5.8, Z_PROC, "Claim 1", "INDEPENDENT - METHOD")
    ax.text(11.2, 10.05,
            "stage h(t) from sensor (110) via link (130); base rating R; offsets measured\n"
            "at visits P and N -> neighbouring station (120) discharge, travel-time lag ->\n"
            "per interval y = ln Q_Y - ln R(h), x = d ln R/dh -> STAGE-UNIT discrepancy D\n"
            "per window -> offset = linear in time between visits + gain x departure of D\n"
            "(gain from earlier visits) -> Q = R(h + s) to archive (410); offset to logger (115)",
            ha="center", va="center", fontsize=10.3, zorder=6, linespacing=1.45)
    zone(ax, 26.2, 7.4, 7.4, 5.8, Z_IN, "Claim 7", "INDEPENDENT - SYSTEM")
    ax.text(28.4, 10.05, "record archive (200), pair admission\n(310), discrepancy unit (320),\n"
            "log-slope unit (330), stage-unit fit\n(340), offset estimator (350),\n"
            "correction unit (400)", ha="center", va="center", fontsize=10.3, zorder=6,
            linespacing=1.45)
    deps = [(0.7, "Claim 2", "real time: last\nvisit offset +\ngain x change\nof D since it"),
            (6.0, "Claim 3", "pair admission:\nlag from daily\nchanges, coupling\nthreshold"),
            (11.3, "Claim 4", "steady intervals,\nwindow length,\nminimum days"),
            (16.6, "Claim 5", "gain: prior until\nenough visits,\nbounded")]
    for x, head, t in deps:
        depbox(ax, x, 0.6, 4.6, 4.8, Z_PROC[0], head, t)
        arr(ax, (x + 2.3, 7.4), (x + 2.3, 5.5), color=Z_PROC[0])
    depbox(ax, 26.3, 0.6, 4.2, 4.8, Z_IN[0], "Claim 7",
           "with the stations:\nstage sensor and\ndata logger that\napplies R(h + s)")
    arr(ax, (28.4, 7.4), (28.4, 5.5), color=Z_IN[0])
    save(fig, "fig07.png", 200, "claim tree")


def fig_example():
    """Offset trajectory at one station: measured visits, linear interpolation, this method."""
    import datetime as dt
    import core
    import probe_daily as pdl
    import usgs
    e1 = load("e1_interpolation.json")
    rec = e1["records"]
    by = {}
    for q in rec:
        by.setdefault((q["x"], q["y"]), []).append(q)
    # the direction with the most scored visits (not chosen for its result)
    key = max(by, key=lambda k: (len(by[k]), k))
    x, y = key
    gain = by[key][-1]["gain"]
    P = __import__("json").load(open(M.os.path.join(M.RESULTS, "pairs.json")))
    sites = sorted({s for p in P["pairs"] for s in (p["up"], p["down"])})
    DV = usgs.dv(sites, pdl.START, pdl.END, stats=("00003",))
    hx, qx, qy = pdl.series(DV, x, "00065"), pdl.series(DV, x, "00060"), pdl.series(DV, y, "00060")
    lag, _ = pdl.lag_days(qx, qy)
    rat = pdl.load_rating(x)
    vis = pdl.visits_with_offset(x, rat, rat.begin or dt.datetime(2020, 10, 1, tzinfo=dt.timezone.utc))
    vis = [v for v in vis if v["day"] >= pdl.START]
    ydx = {}
    for d in sorted(hx):
        dp, dn = pdl.shift_day(d, -1), pdl.shift_day(d, 1)
        if dp not in hx or dn not in hx or abs(hx[d] - hx[dp]) > pdl.STEADY_FT or abs(hx[dn] - hx[d]) > pdl.STEADY_FT:
            continue
        q = qy.get(pdl.shift_day(d, -lag))
        sl = float(rat.slope(hx[d]))
        lr = float(rat.lnq(hx[d]))
        if q and q > 0 and np.isfinite(sl) and sl > 0 and np.isfinite(lr):
            ydx[d] = (math.log(q) - lr, sl)

    import experiments as EX

    def W_(d_from, d_to):
        """Window statistics [n, sum x, sum y, sum x^2, sum x y] over [d_from, d_to)."""
        w = [0, 0.0, 0.0, 0.0, 0.0]
        for i in range(max(pdl.daydiff(d_to, d_from), 0)):
            o = ydx.get(pdl.shift_day(d_from, i))
            if o:
                w = EX.w_add(w, [1, o[1], o[0], o[1] ** 2, o[0] * o[1]])
        return w if w[0] >= pdl.MIN_DAYS else None

    W = pdl.WIN_D
    days, s_lin, s_hat = [], [], []
    for a, b in zip(vis, vis[1:]):
        if a["day"] == b["day"]:
            continue
        wA = W_(pdl.shift_day(a["day"], 1), pdl.shift_day(a["day"], W + 1))
        wB = W_(pdl.shift_day(b["day"], -W), b["day"])
        n = pdl.daydiff(b["day"], a["day"])
        for i in range(0, n, 3):
            d = pdl.shift_day(a["day"], i)
            f = i / n
            sl_ = a["s_meas"] + f * (b["s_meas"] - a["s_meas"])
            wt = W_(pdl.shift_day(d, -W), pdl.shift_day(d, W + 1))
            est = sl_
            if wA and wB and wt:
                cA, cB = EX.ratio_at_visit(wA, a["s_meas"]), EX.ratio_at_visit(wB, b["s_meas"])
                est = sl_ + gain * (EX.offset_given_ratio(wt, cA + f * (cB - cA)) - sl_)
            days.append(dt.date.fromisoformat(d))
            s_lin.append(FT * sl_)
            s_hat.append(FT * est)
    fig, axs = plt.subplots(2, 1, figsize=(16, 10), sharex=True,
                            gridspec_kw={"height_ratios": [2, 1]})
    ax = axs[0]
    ax.plot(days, s_lin, color=C[1], lw=1.8, label="linear interpolation in time (current practice)")
    ax.plot(days, s_hat, color=C[0], lw=1.8, label="with neighbour departure, gain %.2f (this method)" % gain)
    vd = [dt.date.fromisoformat(v["day"]) for v in vis]
    ax.scatter(vd, [FT * v["s_meas"] for v in vis], color="#111", s=28, zorder=5, label="offset measured at field visit")
    ax.set_ylabel("stage offset s (m)")
    ax.set_title("Station %s with neighbour %s: offset between field visits (the direction with the "
                 "most scored visits)" % (x, y), fontsize=11)
    ax.legend(fontsize=9)
    panel(ax, "a")
    tidy(ax)
    ax = axs[1]
    hd = sorted(hx)
    ax.plot([dt.date.fromisoformat(d) for d in hd], [FT * hx[d] for d in hd], color=C[5], lw=1.0)
    ax.fill_between([dt.date.fromisoformat(d) for d in hd], FT * min(hx.values()), [FT * hx[d] for d in hd],
                    color=C[5], alpha=0.15)
    ax.set_ylabel("daily mean stage h (m)")
    lo = min(days)
    hi = max(days)
    ax.set_xlim(lo, hi)
    panel(ax, "b")
    tidy(ax)
    fig.tight_layout()
    save(fig, "fig05.png", 300, "example trajectory %s/%s" % (x, y))
    json_path = M.os.path.join(M.RESULTS, "fig05_example.json")
    __import__("json").dump({"x": x, "y": y, "gain": gain, "n": len(by[key]),
                             "e_lin_mean": float(np.mean([q["e_lin"] for q in by[key]])),
                             "e_hat_mean": float(np.mean([q["e_hat"] for q in by[key]]))},
                            open(json_path, "w"))
    return {"x": x, "y": y, "gain": gain}
