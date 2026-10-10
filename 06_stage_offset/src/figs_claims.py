"""Figure 7: claim tree (independent method claim 1, dependents 2 to 6, system claim 7)."""
import importlib.util
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_spec = importlib.util.spec_from_file_location(
    "p4_make_figs", os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_figs.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def fig07():
    fig, ax = plt.subplots(figsize=(23.5, 12.4))
    ax.set_xlim(0, 47)
    ax.set_ylim(0.4, 25.2)
    ax.axis("off")
    # independent method claim
    M.zone(ax, 0.4, 13.6, 31.2, 11.2, M.Z_PROC, "Claim 1", "INDEPENDENT - METHOD")
    lines = [
        "gauging station 100: stage sensor 110 above control 118; data logger 115 applying R(h + s);",
        "link 130 to archive 200; carried out by data-processing system 900 between two field visits:",
        "(a) receive stage h and the offsets measured at the two visits (current meter or ADCP)",
        "(b) receive neighbour 120 record finalised with its own visits; delay it by the travel-time lag",
        "(c) y = ln Q_Y - ln R(h),  x = d ln R/dh,  so that  y = c + s x",
        "(d) FLOW RATIO c FIXED AT EACH VISIT from the offset measured there; interpolated between",
        "(e) WINDOW OFFSET in metres: stage offset fitted to y - c against x",
        "(f) s = interpolated offset + weight x (window offset - interpolated offset)",
        "(g) Q = R(h + s) for every interval replaces the logger's record in archive 200",
    ]
    for i, t in enumerate(lines):
        ax.text(1.0, 22.6 - i * 0.98, t, fontsize=10.6, va="center", ha="left", zorder=6,
                fontweight="bold" if t[:3] in ("(d)", "(e)") else "normal")
    # system claim
    M.zone(ax, 32.6, 13.6, 14.0, 11.2, M.Z_IN, "Claim 7", "INDEPENDENT - SYSTEM")
    ax.text(39.6, 18.6, "gauging station 100 (sensor 110,\nlogger 115), link 130, archive 200\n"
            "and data-processing system 900\n(units 320, 330, 340, 350, 400)\n\n"
            "configured to carry out the\nmethod of any of claims 1 to 6",
            ha="center", va="center", fontsize=10.6, zorder=6, linespacing=1.5)
    M.arr(ax, (32.6, 19.2), (31.6, 19.2), color=M.Z_IN[0])
    # dependents
    deps = [(0.5, "Claim 2", "(of 1)", "real time, before the\nnext visit: flow ratio\nfixed at the last visit;\n"
             "offset sent over link\n130 to logger 115,\nwhich applies it"),
            (9.85, "Claim 3", "(of 1 or 2)", "pair admission:\nsame mainstem,\narea increment <= 20 %;\n"
             "lag -2..+2 d from daily\nchanges; coupling\n>= 0.95"),
            (19.2, "Claim 4", "(of 1 or 2)", "daily intervals,\nsteady <= 0.076 m;\n21-day windows,\n"
             ">= 8 steady days;\nlinear in time"),
            (28.55, "Claim 5", "(of 1 or 2)", "least squares\nsum x (y - c) / sum x^2;\nweight = gain learned\n"
             "from earlier visits,\n0.5 until 5 visits,\nbounded 0..1.2"),
            (37.9, "Claim 6", "(of 1)", "neighbour record\nrebuilt from its stage\nand base rating, offsets\n"
             "interpolated between\nits own visits")]
    for x, head, par, t in deps:
        M.depbox(ax, x, 1.0, 8.6, 6.6, "#566573", head + "  " + par, t)
    ax.plot([0.5, 46.5], [8.9, 8.9], color="#566573", lw=1.2, ls="--")
    ax.text(23.5, 9.4, "dependent claims 2 to 6 refine claim 1 as marked; claim 7 is the system "
            "carrying out the method", ha="center", fontsize=10, color="#566573", style="italic")
    M.arr(ax, (16.0, 13.6), (16.0, 9.6), color=M.Z_PROC[0])
    M.save(fig, "fig07.png", 200, "claim tree")


if __name__ == "__main__":
    fig07()
