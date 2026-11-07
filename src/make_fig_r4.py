"""Writes paper/fig_dryspell.pdf (vector, 3.5 in wide) and paper/fig_dryspell_preview.png (200 dpi) from the stored results. Run: python src/make_fig_r4.py"""
from __future__ import annotations
import os
import sys
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerTuple
from matplotlib.lines import Line2D
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_r4_summary import case_years, dubai
from make_r5_summary import case_years as r5_case_years
from pvclean.data import repo_root
from pvclean.stats import DRY_HIGH, DRY_LOW

COLOR = {"SA1_raw": "#2a78d6", "QLD1_raw": "#eb6834", "ES_raw": "#1baf7a"}
LABEL = {"SA1_raw": "SA", "QLD1_raw": "QLD", "ES_raw": "ES"}
SHAPE = {"merchant": "o", "ppa": "s"}
DODGE = {"merchant": -1.2, "ppa": 1.2}
INK = "#0b0b0b"; MUTED = "#52514e"; GRID = "#d9d8d4"; LIGHT = "#b5b4ae"


def main() -> None:
    plt.rcParams.update({"pdf.fonttype": 42, "font.size": 7, "font.family": "DejaVu Sans", "axes.linewidth": 0.5, "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                         "xtick.major.width": 0.5, "ytick.major.width": 0.5, "axes.labelcolor": INK})
    fig, ax = plt.subplots(figsize=(3.5, 2.75))
    ax.axvspan(DRY_LOW, DRY_HIGH, color="#e4e3df", lw=0, zorder=0)
    ax.axhline(0, color=MUTED, ls="--", lw=0.7, zorder=1)
    for r in case_years():
        q = r["planner_ft"]; c = COLOR[r["market"]]; xv = r["dry"] + DODGE[r["contract"]]
        ax.errorbar(xv, q["mean"], yerr=[[q["mean"] - q["lo"]], [q["hi"] - q["mean"]]], fmt="none", ecolor=c, elinewidth=0.6, capsize=0, zorder=2)
        ax.plot(xv, q["mean"], SHAPE[r["contract"]], ms=3.6, mec=c, mew=0.8, mfc="white" if r["new"] else c, zorder=3)
    for r in r5_case_years():
        q = r["planner_ft"]; c = COLOR[r["market"]]; xv = r["dry"] + DODGE[r["contract"]]
        ax.errorbar(xv, q["mean"], yerr=[[q["mean"] - q["lo"]], [q["hi"] - q["mean"]]], fmt="none", ecolor=c, elinewidth=0.6, capsize=0, zorder=2)
        ax.plot(xv, q["mean"], SHAPE[r["contract"]], ms=3.6, mec=c, mew=0.8, mfc=c, fillstyle="bottom", markerfacecoloralt="white", zorder=3)
    d = dubai()
    ax.errorbar(d["dry"], d["mean"], yerr=[[d["mean"] - d["lo"]], [d["hi"] - d["mean"]]], fmt="D", ms=4, color=INK, elinewidth=0.6, zorder=3)
    ax.annotate("Dubai (generated)", (d["dry"], d["mean"]), xytext=(0, 7), textcoords="offset points", ha="center", color=INK, fontsize=6.5)
    ax.set_xlabel("Longest dry spell (days)"); ax.set_ylabel("Planner minus FT (USD/yr)")
    ax.spines[["top", "right"]].set_visible(False); ax.set_xlim(0, max(d["dry"] + 45, 300)); ax.margins(y=0.08)
    mk = lambda **k: Line2D([], [], ls="", ms=3.6, **k)
    fig.legend(handles=[mk(marker="o", color=COLOR[k], label=LABEL[k]) for k in COLOR], loc="upper center", bbox_to_anchor=(0.55, 1.015), ncol=3, frameon=False, fontsize=6.4, handletextpad=0.1, columnspacing=1.2, labelcolor=INK)
    half = dict(mec=MUTED, mfc=MUTED, fillstyle="bottom", markerfacecoloralt="white")
    h = [(mk(marker="o", color=MUTED), mk(marker="s", color=MUTED)), (mk(marker="o", mec=MUTED, mfc="white"), mk(marker="s", mec=MUTED, mfc="white")), (mk(marker="o", **half), mk(marker="s", **half)),
         mk(marker="o", color=LIGHT), mk(marker="s", color=LIGHT)]
    fig.legend(h, ["R3 sites", "R4 sites", "R5 sites", "Merchant", "PPA"], handler_map={tuple: HandlerTuple(ndivide=None, pad=0.1)}, loc="upper center", bbox_to_anchor=(0.55, 0.965), ncol=5, frameon=False, fontsize=6.2, handletextpad=0.3, columnspacing=0.8, labelcolor=INK)
    ax.text((DRY_LOW + DRY_HIGH) / 2, 0.985, "no prediction", transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=5.8, color=MUTED)
    fig.subplots_adjust(left=0.15, right=0.985, bottom=0.135, top=0.885)
    out = os.path.join(repo_root(), "paper"); os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, "fig_dryspell.pdf")); fig.savefig(os.path.join(out, "fig_dryspell_preview.png"), dpi=200)
    print("wrote", out)


if __name__ == "__main__":
    main()
