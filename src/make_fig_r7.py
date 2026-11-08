"""Writes paper/fig_policies.pdf (vector, 3.5 in wide, two stacked panels) and paper/fig_policies_preview.png (200 dpi) from the stored results, and results/r7_fig_axes.json, which
says whether any axis had to be extended to show every value (nothing is clipped). Run: python src/make_fig_r7.py"""
from __future__ import annotations
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_r6_summary import case_years
from pvclean.data import repo_root, results_dir
from pvclean.stats import HEADROOM_CUT, SHARE_TARGET

# Validated default categorical slots 1-3 (blue, orange, aqua), each with its own marker shape as a second cue.
SERIES = [("ft_share", "FT", "#2a78d6", "o"), ("pl_share", "Planner", "#eb6834", "s"), ("plain_share", "Plain threshold", "#1baf7a", "^")]
INK = "#0b0b0b"; MUTED = "#52514e"; GRID = "#e4e3df"; BOX = "#8a8984"
DEFAULT_A = (40.0, 105.0)         # % of the oracle value
DEFAULT_B = (-600.0, 600.0)    # USD/yr


def extend(default: tuple[float, float], lo: float, hi: float, pad: float) -> tuple[tuple[float, float], bool]:
    """The default axis, widened just enough (plus pad) to show [lo, hi]."""
    a, b = default; ext = False
    if lo < a:
        a = lo - pad; ext = True
    if hi > b:
        b = hi + pad; ext = True
    return (a, b), ext


def main() -> None:
    plt.rcParams.update({"pdf.fonttype": 42, "font.size": 7, "font.family": "DejaVu Sans", "axes.linewidth": 0.5, "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                         "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.minor.width": 0.3, "axes.labelcolor": INK})
    C = case_years()
    for r in C:
        r["plain_share"] = r["plain"] / r["oracle"] if r["oracle"] > 0 else float("nan")
    Q = sorted([r for r in C if r["oracle"] >= HEADROOM_CUT], key=lambda r: r["oracle"])
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(3.5, 4.6), gridspec_kw=dict(height_ratios=[1.15, 1]))

    # (a) shares in the qualifying case-years
    ys = [100 * r[k] for r in Q for k, *_ in SERIES]
    ya, ext_a = extend(DEFAULT_A, min(ys), max(ys), 3.0)
    for k, lab, col, mk in SERIES:
        ax.plot([r["oracle"] for r in Q], [100 * r[k] for r in Q], mk, ms=3.4, mfc=col, mec="white", mew=0.4, color=col, ls="", label=lab, zorder=3)
    ax.axhline(100 * SHARE_TARGET, color=MUTED, ls="--", lw=0.7, zorder=1)
    ax.set_xscale("log"); ax.set_ylim(*ya)
    xs = [r["oracle"] for r in Q]; ax.set_xlim(min(xs) / 1.15, max(xs) * 1.15)
    ax.text(ax.get_xlim()[0] * 1.05, 100 * SHARE_TARGET + 1.5, "90%", color=MUTED, fontsize=6, va="bottom")
    ax.set_xlabel("Oracle value of cleaning (USD/yr)"); ax.set_ylabel("Share of oracle value (%)")
    ax.grid(axis="y", color=GRID, lw=0.4); ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=6, handletextpad=0.2, borderaxespad=0.2, labelcolor=INK)
    ax.set_title(f"(a) {len(Q)} case-years with oracle value at least {HEADROOM_CUT:,.0f} USD/yr", loc="left", fontsize=7, color=INK)

    # (b) paired differences, all case-years
    D = [("Planner minus FT", [r["main"]["mean"] for r in C]), ("FT minus plain threshold", [r["ft_plain"]["mean"] for r in C])]
    allv = [v for _, d in D for v in d]
    yb, ext_b = extend(DEFAULT_B, min(allv), max(allv), 0.05 * (max(allv) - min(allv)))
    rng = np.random.default_rng(0)
    for i, (lab, d) in enumerate(D):
        bx.boxplot(d, positions=[i], widths=0.45, orientation="vertical", showfliers=False, patch_artist=True, boxprops=dict(facecolor="white", edgecolor=BOX, lw=0.6),
                   medianprops=dict(color=INK, lw=0.9), whiskerprops=dict(color=BOX, lw=0.6), capprops=dict(color=BOX, lw=0.6), zorder=1)
        bx.plot(i + rng.uniform(-0.17, 0.17, len(d)), d, "o", ms=2.6, mfc=MUTED, mec="white", mew=0.3, alpha=0.9, zorder=2)
    bx.axhline(0, color=INK, lw=0.6, zorder=0)
    bx.set_xticks([0, 1], [lab for lab, _ in D]); bx.set_xlim(-0.6, 1.6); bx.set_ylim(*yb)
    bx.set_ylabel("Paired difference (USD/yr)"); bx.grid(axis="y", color=GRID, lw=0.4); bx.set_axisbelow(True)
    bx.set_title(f"(b) All {len(C)} case-years, F2 forecast, mean over 50 seeds", loc="left", fontsize=7, color=INK)
    for z in (ax, bx):
        z.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(h_pad=1.2)
    out = os.path.join(repo_root(), "paper"); os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, "fig_policies.pdf")); fig.savefig(os.path.join(out, "fig_policies_preview.png"), dpi=200)
    note = (f"panel (a) y axis {ya[0]:.1f}% to {ya[1]:.1f}% ({'extended from the default 40% to 105% to show every share; data ' + f'{min(ys):.1f}% to {max(ys):.1f}%' if ext_a else 'default 40% to 105%, every share inside'}); "
            f"panel (b) y axis {yb[0]:+.0f} to {yb[1]:+.0f} USD/yr ({'extended from the default -600 to +600 to show every value; data ' + f'{min(allv):+.0f} to {max(allv):+.0f}' if ext_b else 'default -600 to +600, every value inside'}). No value is clipped.")
    json.dump(dict(panel_a=dict(lim=ya, extended=ext_a, data=[min(ys), max(ys)]), panel_b=dict(lim=yb, extended=ext_b, data=[min(allv), max(allv)]), note=note),
              open(os.path.join(results_dir(), "r7_fig_axes.json"), "w"), indent=1)
    print("wrote", out, "|", note)


if __name__ == "__main__":
    main()
