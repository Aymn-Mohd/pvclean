"""Writes paper/fig_headroom.pdf (vector, 3.5 in wide) and paper/fig_headroom_preview.png (200 dpi) from the stored results. Run: python src/make_fig_r6.py"""
from __future__ import annotations
import os
import sys
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_r6_summary import case_years
from pvclean.data import repo_root
from pvclean.stats import HEADROOM_CUT, SHARE_TARGET

COLOR = {"SA1_raw": "#2a78d6", "QLD1_raw": "#eb6834", "ES_raw": "#1baf7a"}
LABEL = {"SA1_raw": "SA", "QLD1_raw": "QLD", "ES_raw": "ES"}
SHAPE = {"merchant": "o", "ppa": "s"}
INK = "#0b0b0b"; MUTED = "#52514e"; LINE = "#b5b4ae"; BAND = "#e4e3df"
Y_LOW, Y_HIGH = -60.0, 115.0


def main() -> None:
    plt.rcParams.update({"pdf.fonttype": 42, "font.size": 7, "font.family": "DejaVu Sans", "axes.linewidth": 0.5, "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                         "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.minor.width": 0.3, "axes.labelcolor": INK})
    C = [r for r in case_years() if r["oracle"] > 0]
    fig, ax = plt.subplots(figsize=(3.5, 2.85))
    clip = lambda v: min(max(100 * v, Y_LOW + 2), Y_HIGH - 2)
    below = 0
    for r in C:
        a, b = clip(r["ft_share"]), clip(r["pl_share"]); c = COLOR[r["market"]]; m = SHAPE[r["contract"]]
        below += (100 * r["ft_share"] < Y_LOW + 2) + (100 * r["pl_share"] < Y_LOW + 2)
        ax.plot([r["oracle"]] * 2, [a, b], color=LINE, lw=0.5, zorder=1)
        ax.plot(r["oracle"], a, m, ms=3.2, mec=c, mfc=c, mew=0.7, zorder=3)
        ax.plot(r["oracle"], b, m, ms=3.2, mec=c, mfc="white", mew=0.7, zorder=2)
    ax.set_xscale("log"); lo = min(r["oracle"] for r in C) * 0.7; hi = max(r["oracle"] for r in C) * 1.4
    ax.axvspan(lo, HEADROOM_CUT, color=BAND, lw=0, zorder=0)
    ax.axhline(100 * SHARE_TARGET, color=MUTED, ls="--", lw=0.7, zorder=1)
    ax.text(lo * 1.1, 100 * SHARE_TARGET + 2, "90%", color=MUTED, fontsize=6, va="bottom")
    ax.text(HEADROOM_CUT * 0.92, Y_HIGH - 3, "below 1,000 USD/yr", color=MUTED, fontsize=5.8, ha="right", va="top")
    ax.set_xlim(lo, hi); ax.set_ylim(Y_LOW, Y_HIGH)
    if below:
        ax.text(lo * 1.1, Y_LOW + 3, f"{int(below)} shares below {Y_LOW:.0f}% drawn at the edge", color=MUTED, fontsize=5.8, ha="left", va="bottom")
    ax.set_xlabel("Oracle value of cleaning (USD/yr)"); ax.set_ylabel("Share of oracle value captured (%)")
    ax.spines[["top", "right"]].set_visible(False)
    mk = lambda **k: Line2D([], [], ls="", ms=3.6, **k)
    h = [mk(marker="o", color=COLOR[k], label=LABEL[k]) for k in COLOR]
    h += [mk(marker="o", mec=MUTED, mfc=MUTED, label="FT"), mk(marker="o", mec=MUTED, mfc="white", label="Planner"), mk(marker="o", color=LINE, label="Merchant"), mk(marker="s", color=LINE, label="PPA")]
    fig.legend(handles=h, loc="upper center", ncol=7, frameon=False, fontsize=6, handletextpad=0.05, columnspacing=0.7, labelcolor=INK)
    fig.subplots_adjust(left=0.135, right=0.985, bottom=0.13, top=0.93)
    out = os.path.join(repo_root(), "paper"); os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, "fig_headroom.pdf")); fig.savefig(os.path.join(out, "fig_headroom_preview.png"), dpi=200)
    print("wrote", out, "points below the axis, shown at its edge:", int(below))


if __name__ == "__main__":
    main()
