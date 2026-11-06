"""Phase R2 figures from results/trace_merchant_default.json and results/results_robot.json: results/figures/fig_mission.pdf and
fig_robot_sweep.pdf. Vector PDFs with embedded fonts. Contract colours are Okabe-Ito; line style and marker carry the same identity."""
from __future__ import annotations
from typing import Any
import json, os
import numpy as np
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D

F = "figures"
INK, MUTED, GRID, IDLE = "#222222", "#666666", "#dddddd", "#e8e8e6"
CLEAN, CLOSED = "#0072B2", "#D55E00"
STYLE = {"fixed": ("#0072B2", "-", "o"), "merchant": ("#D55E00", "--", "s"), "ppa": ("#009E73", "-.", "^"), "capped": ("#CC79A7", ":", "D")}
NAME = {"fixed": "Fixed tariff", "merchant": "Merchant", "ppa": "PPA", "capped": "Capped export"}
plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "text.color": INK, "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "hatch.linewidth": 0.6,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6})


def fig_mission(T: Any) -> Any:
    """Writes fig_mission.pdf from the mission trace."""
    n = T["plant"]["n_rows"]; pitch = T["plant"]["row_pitch_m"]; night = T["night"]
    cleaned, closed = set(night["rows"]), set(night["closed_rows"])
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(7.16, 4.5), height_ratios=[1.0, 1.0], gridspec_kw=dict(hspace=0.5))
    for r in range(1, n + 1):
        x = r * pitch
        fc, ec, h = (CLEAN, CLEAN, None) if r in cleaned else ("white", CLOSED, "////") if r in closed else (IDLE, "#b0b0ac", None)
        ax.add_patch(Rectangle((x - 3.5, 0), 7, 1, facecolor=fc, edgecolor=ec, hatch=h, lw=0.6))
    ax.plot([0, night["stops"][-1]["row"] * pitch], [-0.32, -0.32], color=INK, lw=1.1, zorder=3)
    ax.plot([0, night["stops"][-1]["row"] * pitch], [-0.48, -0.48], color=INK, lw=1.0, ls=(0, (4, 2)), zorder=3)
    ax.plot([s["row"] * pitch for s in night["stops"]], [-0.32] * len(night["stops"]), "o", ms=3.2, mfc="white", mec=INK, mew=0.7, zorder=4)
    ax.annotate("", (night["stops"][-1]["row"] * pitch + 13, -0.32), (night["stops"][-1]["row"] * pitch, -0.32), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
    ax.annotate("", (-6, -0.48), (6, -0.48), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
    ax.plot([0], [-0.4], marker="P", ms=8, color=INK, ls="none", zorder=5, clip_on=False)
    ax.text(0, -0.6, "Dock", ha="center", va="top", fontsize=7)
    for s, ha in ((night["stops"][0], "left"), (night["stops"][len(night["stops"]) // 2], "center"), (night["stops"][-1], "center")):
        ax.text(s["row"] * pitch, -0.26, f"{s['arrive_min']:.0f} min", ha=ha, va="bottom", fontsize=6.5)
    ax.text(night["stops"][-1]["row"] * pitch + 18, -0.48, f"back at dock: {night['end_min']:.0f} of {T['robot']['night_min']:.0f} min", va="center", fontsize=7)
    ax.set_xlim(-14, (n + 1) * pitch); ax.set_ylim(-0.8, 1.08); ax.set_yticks([])
    ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False)
    ax.xaxis.tick_top(); ax.set_xticks([r * pitch for r in (1, 5, 10, 15, 20, 25, 30, 35, 40)], [1, 5, 10, 15, 20, 25, 30, 35, 40]); ax.tick_params(axis="x", length=0, pad=1)
    ax.set_title(f"(a) Night before {night['date']}: {len(cleaned)} rows cleaned (row numbers above; 10 m pitch, row length schematic)", loc="left", fontsize=8, pad=14)
    key = [Patch(facecolor=CLEAN, edgecolor=CLEAN, label="Cleaned"), Patch(facecolor="white", edgecolor=CLOSED, hatch="////", label="Closed (crop access)"),
           Patch(facecolor=IDLE, edgecolor="#b0b0ac", label="Open, not cleaned"),
           Line2D([], [], color=INK, lw=1.1, marker="o", ms=3.2, mfc="white", mew=0.7, label="Outbound, stops"), Line2D([], [], color=INK, lw=1.0, ls=(0, (4, 2)), label="Return")]
    ax.legend(handles=key, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.02), frameon=False, fontsize=7, handlelength=1.8, columnspacing=1.2)

    W = T["week"]
    for i, w in enumerate(W):
        rows = set(w["mission"]["rows"]) if w["mission"] else set(); shut = set(w["closed_rows"])
        for r in range(1, n + 1):
            fc, ec, h = (CLEAN, CLEAN, None) if r in rows else ("white", CLOSED, "////") if r in shut else (IDLE, "white", None)
            bx.add_patch(Rectangle((r - 0.5, i + 0.12), 1, 0.76, facecolor=fc, edgecolor=ec, hatch=h, lw=0.3))
        lab = f"{len(rows)} rows, {w['mission']['end_min']:.0f} min" if w["mission"] else "no mission"
        bx.text(n + 1, i + 0.5, lab, va="center", fontsize=7)
    k = [w["day"] for w in W].index(night["day"])
    bx.add_patch(Rectangle((0.3, k + 0.02), n + 0.4, 0.96, fill=False, edgecolor=INK, lw=0.9))
    bx.set_xlim(0.3, n + 7.5); bx.set_ylim(len(W), 0)
    bx.set_yticks([i + 0.5 for i in range(len(W))], [w["date"][5:] for w in W]); bx.tick_params(axis="y", length=0)
    bx.set_xticks([1, 5, 10, 15, 20, 25, 30, 35, 40]); bx.set_xlabel("Row number", x=0.43)
    bx.spines["left"].set_visible(False); bx.spines["bottom"].set_visible(False)
    bx.set_title("(b) Seven nights around it (box: the night in (a)), labelled by the production day that follows", loc="left", fontsize=8)
    fig.savefig(os.path.join(F, "fig_mission.pdf"), bbox_inches="tight")
    plt.close(fig)


LEVELS = {"night": ("Night (min)", ["240", "360", "480"]), "service": ("Service (min/row)", ["40", "25", "15"]),
          "speed": ("Speed (m/s)", ["0.25", "0.5", "1.0"]), "battery": ("Battery (rows)", ["6", "10", "none"]),
          "availability": ("Availability", ["0.8", "0.9", "1.0"])}


def fig_sweep(D: Any) -> Any:
    """Writes fig_robot_sweep.pdf from the sweep."""
    fac = D["_meta"]["factors"]; contracts = list(STYLE)
    fig, axs = plt.subplots(2, 5, figsize=(7.16, 3.3), sharey="row", height_ratios=[2.2, 1], gridspec_kw=dict(wspace=0.12, hspace=0.16))
    for j, (f, settings) in enumerate(fac.items()):
        top, low = axs[0, j], axs[1, j]
        d_idx = settings.index("default")
        for a in (top, low):
            a.axvline(d_idx, color=GRID, lw=3, zorder=0)
            a.set_xlim(-0.4, 2.4); a.set_xticks(range(3))
            a.grid(axis="y", color=GRID, lw=0.4); a.set_axisbelow(True)
        top.axhline(0, color=MUTED, lw=0.7)
        low.axhline(90, color=INK, lw=0.7, ls=(0, (2, 2)))
        for i, c in enumerate(contracts):
            col, ls, mk = STYLE[c]
            off = (i - 1.5) * 0.09
            x = np.arange(3) + off
            m = [D[f"{s}|{c}"]["metrics"]["planner_bestbase"] for s in settings]
            mean = np.array([v["mean"] for v in m])
            top.errorbar(x, mean, yerr=[mean - [v["lo"] for v in m], [v["hi"] for v in m] - mean], color=col, ls=ls, marker=mk, ms=3.2, lw=1.0, elinewidth=0.7, capsize=0)
            base = D[f"default|{c}"]["metrics"]["value_of_cleaning"]["mean"]
            low.plot(np.arange(3), [100 * D[f"{s}|{c}"]["metrics"]["value_of_cleaning"]["mean"] / base for s in settings], color=col, ls=ls, marker=mk, ms=2.8, lw=0.9)
        top.set_title(LEVELS[f][0], fontsize=7.5, pad=3)
        top.tick_params(labelbottom=False)
        low.set_xticklabels(LEVELS[f][1], fontsize=7)
        low.set_ylim(87, 103); low.set_yticks([90, 100])
    axs[0, 0].set_ylabel("Planner minus best\nbaseline (USD/yr)")
    axs[1, 0].set_ylabel("Value of cleaning\n(% of default)")
    axs[1, 4].text(2.4, 90.7, "90%", ha="right", va="bottom", fontsize=6.5)
    fig.text(0.51, -0.02, "Each panel runs from least to most capable robot; the wide grey band marks the default. Bars: 95% t-interval over 50 seeds.", ha="center", fontsize=7, color=MUTED)
    h = [Line2D([], [], color=STYLE[c][0], ls=STYLE[c][1], marker=STYLE[c][2], ms=3.2, lw=1.0, label=NAME[c]) for c in contracts]
    fig.legend(handles=h, ncol=4, loc="lower center", bbox_to_anchor=(0.51, 0.93), frameon=False, fontsize=7.5, handlelength=2.6)
    fig.savefig(os.path.join(F, "fig_robot_sweep.pdf"), bbox_inches="tight")
    plt.close(fig)


def build(R: str, out: str) -> None:
    """R: results directory. out: directory for the two figures."""
    global F
    F = out
    os.makedirs(F, exist_ok=True)
    fig_mission(json.load(open(os.path.join(R, "trace_merchant_default.json"))))
    fig_sweep(json.load(open(os.path.join(R, "results_robot.json"))))
