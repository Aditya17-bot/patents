"""Figure 6: applicability to Indian gauging networks (E8) and station-level uncertainty (E9)."""
import importlib.util
import json
import os
import struct

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_spec = importlib.util.spec_from_file_location(
    "p4_make_figs", os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_figs.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
panel, tidy, C, load, save = M.panel, M.tidy, M.C, M.load, M.save

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHP = os.path.join(ROOT, "data", "kaggle", "camels_ind", "shapefiles_catchment", "catchments.shp")


def read_polygons(path):
    """Minimal ESRI shapefile reader for polygon records (type 5): list of rings."""
    b = open(path, "rb").read()
    pos = 100
    rings = []
    while pos + 8 <= len(b):
        clen = struct.unpack(">i", b[pos + 4:pos + 8])[0] * 2
        rec = b[pos + 8:pos + 8 + clen]
        pos += 8 + clen
        if len(rec) < 44 or struct.unpack("<i", rec[:4])[0] != 5:
            continue
        nparts, npts = struct.unpack("<2i", rec[36:44])
        parts = list(struct.unpack("<%di" % nparts, rec[44:44 + 4 * nparts])) + [npts]
        off = 44 + 4 * nparts
        pts = np.frombuffer(rec[off:off + 16 * npts], dtype="<f8").reshape(-1, 2)
        for i in range(nparts):
            rings.append(pts[parts[i]:parts[i + 1]])
    return rings


# label positions (lon, lat) per river, chosen so that the labels do not overlap
LABEL_AT = {"Godavari/Pranhita/Wardha": (72.6, 20.5), "Brahmani": (82.6, 24.7),
            "Mahanadi/Seonath": (78.4, 23.4), "Tapi": (72.4, 24.4)}
LABEL_AT_SITE = {"Perur": (74.4, 16.1), "Polavaram": (82.6, 15.7)}


def fig06():
    e8 = load("e8_india.json")
    e9 = load("e9_bootstrap.json")
    coup = load("coupling.json")
    fig, axs = plt.subplots(2, 2, figsize=(16, 13))
    # (a) map of CWC catchments and admitted pairs
    ax = axs[0, 0]
    for ring in read_polygons(SHP):
        ax.fill(ring[:, 0], ring[:, 1], facecolor="#EEF2F3", edgecolor="#AAB7B8", lw=0.4, zorder=1)
    cols = {}
    pal = [C[0], C[1], C[2], C[3], C[4], C[5]]
    for r in e8["admitted"]:
        key = tuple(sorted((r["x"], r["y"])))
        if key in cols:
            continue
        col = pal[len(cols) % len(pal)]
        cols[key] = col
        ax.plot([r["lon"], r["lon_y"]], [r["lat"], r["lat_y"]], color=col, lw=2.6, zorder=3)
        ax.scatter([r["lon"], r["lon_y"]], [r["lat"], r["lat_y"]], color=col, s=55, zorder=4,
                   edgecolor="white", linewidth=1.0)
        mlon, mlat = 0.5 * (r["lon"] + r["lon_y"]), 0.5 * (r["lat"] + r["lat_y"])
        at = (LABEL_AT_SITE.get(r["x_name"]) or LABEL_AT_SITE.get(r["y_name"])
              or LABEL_AT.get(r["river"]) or (mlon + 0.5, mlat + 0.5))
        ax.annotate("%s - %s (r = %.3f)" % (r["y_name"], r["x_name"], r["coupling"]),
                    (mlon, mlat), xytext=at, textcoords="data", fontsize=8.6,
                    color=col, fontweight="bold", zorder=5, ha="left",
                    va="center", arrowprops=dict(arrowstyle="-", color=col, lw=0.9),
                    bbox=dict(fc="white", ec=col, alpha=0.92, pad=2, lw=0.6))
    ax.set_xlabel("longitude (deg E)")
    ax.set_ylabel("latitude (deg N)")
    ax.set_aspect("equal")
    ax.set_title("CWC gauge sites (CAMELS-IND): %d of %d same-river pairs admitted\n"
                 "(area increment <= 20 %%, coupling >= 0.95)"
                 % (e8["admitted_pairs"], e8["same_river_consecutive_pairs"]), fontsize=10.5, pad=12)
    panel(ax, "a")
    # (b) coupling against incremental area
    ax = axs[0, 1]
    us_incr = [r[2] for r in coup]
    us_c = [r[5] for r in coup]
    lo = 0.002
    ax.scatter([max(v, lo) for v in us_incr], us_c, s=22, color=C[0], alpha=0.6,
               label="US directions (%d)" % len(coup))
    ci = e8["candidates_coupling"]
    ax.scatter([max(r["incr"], lo) for r in ci], [r["coupling"] for r in ci], s=26, color=C[3],
               alpha=0.85, marker="D", label="India same-river pairs (%d)" % len(ci))
    ax.fill_between([lo * 0.8, 0.20], 0.95, 1.0, color="#ABEBC6", alpha=0.45, zorder=0)
    ax.axhline(0.95, color="#1E8449", ls="--", lw=1.2)
    ax.axvline(0.20, color="#1E8449", ls="--", lw=1.2)
    ax.text(0.0024, 0.66, "admitted region (shaded):\nincrement <= 20 %, coupling >= 0.95",
            color="#1E8449", fontsize=9, fontweight="bold")
    ax.set_xscale("log")
    ax.set_xlim(lo * 0.8, 30)
    ax.set_xlabel("incremental drainage area between the stations (fraction)")
    ax.set_ylabel("coupling: correlation of daily ln Q after the lag")
    ax.set_ylim(min(0.5, min(us_c + [r["coupling"] for r in ci])), 1.0)
    ax.legend(fontsize=9, loc="lower left")
    ax.set_title("Pair admission (claim 3) on both networks", fontsize=10.5)
    tidy(ax)
    panel(ax, "b")
    # (c) departure noise floor
    ax = axs[1, 0]
    bins = np.linspace(0, 0.5, 41)
    ind = [r for r in e8["admitted"]]
    ax.bar([0], [0], color="white")
    fl_in = e8["india_floor"]
    fl_us = e8["us_floor_upper"]
    # recompute histograms from per-direction medians is not enough; show summary bars
    labels = ["India (CWC)\nmedian", "India (CWC)\n90th pct", "US (published)\nmedian",
              "US (published)\n90th pct"]
    vals = [fl_in["median"], fl_in["p90"], fl_us["median"], fl_us["p90"]]
    colors = [C[3], C[3], C[0], C[0]]
    p = ax.bar(range(4), [100 * v for v in vals], color=colors, edgecolor="white", linewidth=1.2)
    for rect, v in zip(p, vals):
        ax.text(rect.get_x() + rect.get_width() / 2, 100 * v + 0.6, "%.1f %%" % (100 * v),
                ha="center", fontsize=9.5)
    ax.set_xticks(range(4))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("|departure| of the neighbour's log ratio (% of discharge)")
    ax.set_title("Noise floor of the neighbour departure over one %d-day visit interval\n"
                 "(%d Indian and %d US window triples)" % (e8["gap_days"], fl_in["n"], fl_us["n"]),
                 fontsize=10.5)
    tidy(ax)
    panel(ax, "c")
    # (d) station-cluster bootstrap
    ax = axs[1, 1]
    rows = [("e1_all", "Record, all visits"), ("e1_open_water", "Record, open water"),
            ("e1_big", "Record, departure >= 0.03 m"),
            ("e1_vs_practice", "Record, all, vs practice per station"),
            ("e1_ip_all", "Record, all, rebuilt neighbour record"),
            ("e1_rt_all", "Record, real-time ref., all"),
            ("e2_rt_all", "Real time, all visits"), ("e2_rt_big", "Real time, change >= 0.03 m")]
    for i, (k, lab) in enumerate(rows):
        v = e9[k]
        y = len(rows) - 1 - i
        col = C[0] if v["ci95"][0] > 0 else "#95A5A6"
        ax.plot(v["ci95"], [y, y], color=col, lw=3)
        ax.scatter([v["reduction_pts"]], [y], color=col, s=60, zorder=3)
        ax.text(max(v["ci95"]) + 0.25, y, "%.1f  [%.1f, %.1f]   %d/%d stations"
                % (v["reduction_pts"], v["ci95"][0], v["ci95"][1], v["stations_better"],
                   v["stations_with_5plus"]), va="center", fontsize=8.8)
    ax.axvline(0, color="#333", lw=1)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([lab for _, lab in rows][::-1], fontsize=9)
    ax.set_xlabel("reduction of mean absolute discharge error (percentage points), 95 % interval")
    ax.set_xlim(-1.5, 19)
    ax.set_title("Resampling whole stations (%d draws)" % e9["B"], fontsize=10.5)
    tidy(ax)
    panel(ax, "d")
    fig.tight_layout()
    save(fig, "fig06.png", 300, "india and robustness")
