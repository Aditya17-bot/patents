"""Figure 7: claim tree (independent method claim 1, dependents 2 to 5, system claim 6)."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, r"C:\adi\patents\05_length_invariance\src")
import make_figs as P3                                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "patent", "figures")


def fig07():
    fig, ax = plt.subplots(figsize=(23.5, 12.4))
    ax.set_xlim(0, 47)
    ax.set_ylim(0.4, 25.2)
    ax.axis("off")
    P3.zone(ax, 0.4, 13.6, 31.2, 11.2, P3.Z_PROC, "Claim 1", "INDEPENDENT - METHOD")
    lines = [
        "in-situ sonde 100: ammonium ISE 110, controller 115 storing a calibration offset;",
        "link 130 to archive 200; carried out by data-processing system 900:",
        "(a) receive the ammonium readings A(t) at successive intervals",
        "(b) receive laboratory results L_j of samples taken at the sonde at times t_j",
        "(c) FLOOR F(t): low quantile of the readings over a window of several days before t",
        "(d) ANCHOR GAP g: from earlier samples, F(t_j) - (A(t_j) - L_j)",
        "(e) A_c(t) = A(t) - (F(t) - g), not below zero",
        "(f) A_c(t) replaces the provisional record in archive 200;",
        "     the offset F(t) - g is sent over link 130 to controller 115",
    ]
    for i, t in enumerate(lines):
        ax.text(1.0, 22.6 - i * 0.98, t, fontsize=10.6, va="center", ha="left", zorder=6,
                fontweight="bold" if t[:3] in ("(c)", "(d)") else "normal")
    P3.zone(ax, 32.6, 13.6, 14.0, 11.2, P3.Z_IN, "Claim 6", "INDEPENDENT - SYSTEM")
    ax.text(39.6, 18.6, "sonde 100 (ISE 110, controller 115),\nlink 130, archive 200,\n"
            "relay-switched sampler 440 and\nintake interlock 450, and\n"
            "data-processing system 900\n(units 310-340, 400 driving the relays)\n\n"
            "configured to carry out the\nmethod of any of claims 1 to 5",
            ha="center", va="center", fontsize=10.6, zorder=6, linespacing=1.5)
    P3.arr(ax, (32.6, 19.2), (31.6, 19.2), color=P3.Z_IN[0])
    deps = [(0.5, "Claim 2", "(of 1)", "two-tier alarm 420:\nwatch (either reading):\nrelay starts sampler 440;\nconfirmed (both): intake\ninterlock 450 by relay"),
            (12.2, "Claim 3", "(of 1 or 2)", "window 7 days, 5th\npercentile, >= 96 readings;\ng = median over the 12\nmost recent samples"),
            (23.9, "Claim 4", "(of 1 to 3)", "before the first sample:\ng from the low decile of\nlaboratory results at\nother sondes"),
            (35.6, "Claim 5", "(of 1 to 4)", "reading paired with a\nsample within 30 min;\nresults equal to the\nreading are discarded")]
    for x, head, par, t in deps:
        P3.depbox(ax, x, 1.0, 10.9, 6.6, "#566573", head + "  " + par, t)
    ax.plot([0.5, 46.5], [8.9, 8.9], color="#566573", lw=1.2, ls="--")
    ax.text(23.5, 9.4, "dependent claims 2 to 5 refine claim 1 as marked; claim 6 is the system "
            "carrying out the method", ha="center", fontsize=10, color="#566573", style="italic")
    P3.arr(ax, (16.0, 13.6), (16.0, 9.6), color=P3.Z_PROC[0])
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "fig07.png"), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("fig07.png")


if __name__ == "__main__":
    fig07()
