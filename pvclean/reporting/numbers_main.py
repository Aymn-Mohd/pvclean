"""Figures, LaTeX tables and numbers.tex macros from stored results.
No number in the paper is typed by hand."""
from __future__ import annotations
from typing import Any


def build(RES: str, OUT: str, I: dict[str, Any]) -> None:
    """RES: results directory with a trailing slash. OUT: paper directory with a trailing slash. I: the numbers of macro_inputs.json."""
    import json
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import stats
    from pvclean import model as sim

    R = json.load(open(RES + "results.json"))
    BLUE = ["#9ec5f4", "#3987e5", "#184f95"]      # ordinal ramp (low, mid, high)
    C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
    INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e2dc"

    plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.edgecolor": MUTED,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                         "grid.color": GRID, "grid.linewidth": 0.5, "lines.linewidth": 1.5,
                         "legend.frameon": False, "savefig.bbox": "tight", "pdf.fonttype": 42})


    def ci95(x):
        x = np.asarray(x, float)
        return x.mean(), stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


    macros = {}


    def M(name, val):
        macros[name] = val


    def usd(x):
        return f"{x:,.0f}"


    HET_FIG = [0.5, 1.0, 1.5]
    HET_SWEEP = [0.0, 0.5, 1.0, 1.5, 2.0]
    EXPO = R["expo"]
    cv = lambda h: EXPO[str(h)]["cv"]
    mm = lambda h: EXPO[str(h)]["maxmin"]

    # ------------------------------------------------------------------ setup numbers
    cfg = dict(sim.CONFIG, **R["config"])
    M("NRows", f"{cfg['n_rows']}"); M("RowKwp", f"{cfg['row_kwp']:.0f}")
    M("PlantMwp", f"{cfg['n_rows'] * cfg['row_kwp'] / 1000:.1f}")
    M("NTest", str(len(R["test_seeds"]))); M("NTrain", str(len(R["train_seeds"])))
    M("SoilMeanPct", f"{cfg['soil_mean'] * 100:.2f}")
    M("CRow", f"{cfg['c_row']:.0f}"); M("CMission", f"{cfg['c_mission']:.0f}"); M("CInsp", f"{cfg['c_insp']:.2f}")
    M("Tariff", f"{cfg['tariff']:.2f}"); M("PPA", f"{cfg['ppa']:.2f}")
    M("CapPct", f"{cfg['export_cap_frac'] * 100:.0f}")
    M("RuntimeS", f"{R['runtime_s']:.0f}")
    M("ExpoCVDef", f"{cv(1.0):.2f}"); M("ExpoMaxMinDef", f"{mm(1.0):.1f}")
    M("ExpoCVLo", f"{cv(0.5):.2f}"); M("ExpoCVHi", f"{cv(1.5):.2f}")
    M("ExpoMaxMinHi", f"{mm(1.5):.1f}"); M("ExpoCVTop", f"{cv(2.0):.2f}"); M("ExpoMaxMinTop", f"{mm(2.0):.1f}")

    caps, negs, negall, rdays, yld = [], [], [], [], []
    for s in R["test_seeds"]:
        w = sim.weather(s); sp = sim.spot_prices(s); day = w["pdc"] > 0.05
        caps.append((np.maximum(sp, 0) * w["pdc"]).sum() / w["pdc"].sum() / sp.mean())
        negs.append((sp[day] < 0).mean()); negall.append((sp < 0).mean())
        rdays.append((w["rain"] >= 1).sum()); yld.append(w["pdc"].sum())
    M("CaptureRatio", f"{np.mean(caps):.2f}"); M("NegDaylightPct", f"{np.mean(negs) * 100:.1f}")
    M("NegAllPct", f"{np.mean(negall) * 100:.1f}")
    M("RainDays", f"{np.mean(rdays):.1f}"); M("YieldDC", usd(np.mean(yld)))
    M("SpotMean", f"{np.mean([sim.spot_prices(s).mean() for s in R['test_seeds']]):.3f}")

    # ------------------------------------------------------------------ RQ1 table
    names = {"fixed": "Fixed interval", "threshold": "Loss threshold", "econ": "Economic, constant price",
             "proposed": "Proposed", "proposed_noval": "  without contract valuation",
             "proposed_nobatch": "  without mission batching"}
    cnames = {"fixed": "Fixed tariff", "merchant": "Merchant", "ppa": "PPA, negative-price clause",
              "capped": "Fixed tariff, export cap"}
    cols = ["fixed", "merchant", "ppa", "capped"]
    lines = []
    for p in ["fixed", "threshold", "econ", "proposed", "proposed_noval", "proposed_nobatch"]:
        cells = []
        for c in cols:
            v = R["rq1"][c][p]
            cells.append(f"{usd(v['inc_net'][0])} ({v['n_clean'][0]:.0f})")
        lab = names[p].strip()
        lab = ("\\quad " + lab) if names[p].startswith("  ") else lab
        lines.append(lab + " & " + " & ".join(cells) + r" \\")
        if p == "proposed":
            cells = []
            for c in cols:
                pv = R["rq1"][c]["_paired_vs_best"]
                cells.append(f"{pv['mean']:+.0f} $\\pm$ {pv['ci']:.0f}")
            lines.append(r"\quad gain over best baseline & " + " & ".join(cells) + r" \\")
            pcells = []
            for c in cols:
                ev_ = R["rq1"][c]
                d_ = np.array(ev_["proposed"]["inc_net_seeds"]) - np.array(ev_[ev_["_best_baseline"]]["inc_net_seeds"])
                pw = stats.wilcoxon(d_).pvalue
                pcells.append("$<$0.001" if pw < 0.001 else f"{pw:.3f}")
            lines.append(r"\quad Wilcoxon $p$ vs best baseline & " + " & ".join(pcells) + r" \\")
    tab = r"""\begin{table*}[!t]
\centering
\caption{Incremental net maintenance value over no robot cleaning, mean of %s test years, USD per year for the %s MWp plant (robot cleanings per year in brackets). The gain row is the paired mean difference to the best tuned baseline with its 95\%% confidence half-width.}
\label{tab:rq1}
\begin{tabular}{lcccc}
\toprule
Policy & %s \\
\midrule
%s
\bottomrule
\end{tabular}
\end{table*}
""" % (macros["NTest"], macros["PlantMwp"], " & ".join(cnames[c] for c in cols), "\n".join(lines))
    open(OUT + "table_rq1.tex", "w").write(tab)

    for c, tag in zip(cols, ["Fix", "Mer", "Ppa", "Cap"]):
        ev = R["rq1"][c]
        for k, nm in [("_paired_vs_best", "Best"), ("_paired_vs_econ", "Econ"), ("_paired_noval", "Noval"),
                      ("_paired_nobatch", "Nobatch")]:
            M(f"Gain{nm}{tag}", f"{ev[k]['mean']:.0f}"); M(f"Gain{nm}{tag}CI", f"{ev[k]['ci']:.0f}")
            M(f"Wins{nm}{tag}", str(ev[k]["wins"]))
        bb = ev["_best_baseline"]
        M(f"BestBase{tag}", names[bb].split(",")[0].lower())
        M(f"IncBest{tag}", usd(ev[bb]["inc_net"][0]))
        M(f"IncProp{tag}", usd(ev["proposed"]["inc_net"][0]))
        M(f"GainPct{tag}", f"{ev['_paired_vs_best']['mean'] / ev[bb]['inc_net'][0] * 100:.1f}")
        M(f"RevNone{tag}", usd(ev["proposed"]["revenue_none"][0]))
        M(f"EnergyRec{tag}", f"{ev['proposed']['energy_rec_mwh'][0]:.0f}")
        M(f"CleanProp{tag}", f"{ev['proposed']['n_clean'][0]:.0f}")
        M(f"CleanFixed{tag}", f"{ev['fixed']['n_clean'][0]:.0f}")
        M(f"CleanNoval{tag}", f"{ev['proposed_noval']['n_clean'][0]:.0f}")
        M(f"TFixed{tag}", str(ev["fixed"]["params"]["T"]))
        M(f"Theta{tag}", f"{ev['threshold']['params']['theta'] * 100:.0f}")
    pf = R["rq1"]["fixed"]["proposed"]
    M("EnergyLossNonePct", f"{pf['energy_rec_mwh'][0] / (pf['energy_none_mwh'][0] + pf['energy_rec_mwh'][0]) * 100:.0f}")
    M("IncMin", usd(min(R["rq1"][c]["proposed"]["inc_net"][0] for c in cols)))
    M("IncMax", usd(max(R["rq1"][c]["proposed"]["inc_net"][0] for c in cols)))

    for c, tag in zip(["merchant", "ppa", "capped"], ["Mer", "Ppa", "Cap"]):
        t = R["transfer"][c]
        for p, nm in [("fixed", "Fixed"), ("threshold", "Thr"), ("econ", "Econ"), ("proposed", "Prop")]:
            loss = R["rq1"][c][p]["inc_net"][0] - t[p]["inc_net"][0]
            M(f"Tr{nm}{tag}", usd(loss))
        bt = max(["fixed", "threshold", "econ"], key=lambda p: t[p]["inc_net"][0])
        d = np.array(t["proposed"]["inc_net_seeds"]) - np.array(t[bt]["inc_net_seeds"])
        m, h = ci95(d)
        M(f"TrGain{tag}", f"{m:.0f}"); M(f"TrGain{tag}CI", f"{h:.0f}")

    # ------------------------------------------------------------------ RQ3: value of information
    regimes = [("site", "0.0", "7", "Station"), ("mobile", "0.005", "7", r"$\sigma$=0.5"),
               ("mobile", "0.01", "7", r"$\sigma$=1"), ("mobile", "0.02", "7", r"$\sigma$=2"),
               ("mobile", "0.04", "7", r"$\sigma$=4"), ("mobile", "0.01", "28", r"$\sigma$=1, 28 d"),
               ("perfect", "0.0", "7", "Perfect")]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.3), sharey=True)
    for ax, c, title in zip(axes, ["fixed", "merchant"], ["Fixed tariff", "Merchant"]):
        for het, col in zip(HET_FIG, BLUE):
            base = np.array(R["rq3"][f"{c}|h{het}|site|s0.0|p7"]["inc_net_seeds"])
            ms, hs = [], []
            for info, sg, pe, _ in regimes:
                v = np.array(R["rq3"][f"{c}|h{het}|{info}|s{sg}|p{pe}"]["inc_net_seeds"])
                m, h = ci95(v - base) if info != "site" else (0.0, 0.0)
                ms.append(m); hs.append(h)
            x = np.arange(len(regimes))
            ax.errorbar(x, ms, yerr=hs, color=col, marker="o", ms=4, capsize=2, lw=1.5,
                        label=f"Row CV {cv(het):.2f}")
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_xticks(x); ax.set_xticklabels([r[3] for r in regimes], rotation=30, ha="right")
        ax.set_title(title, fontsize=8, color=INK)
    axes[0].set_ylabel("Net value vs station (USD/yr)")
    axes[1].legend(loc="lower left", fontsize=7)
    fig.savefig(OUT + "fig_voi.pdf")
    plt.close(fig)

    ht = {0.5: "Lo", 1.0: "Def", 1.5: "Hi"}
    for c, tag in [("fixed", "Fix"), ("merchant", "Mer")]:
        for het in HET_FIG:
            base = np.array(R["rq3"][f"{c}|h{het}|site|s0.0|p7"]["inc_net_seeds"])
            v = np.array(R["rq3"][f"{c}|h{het}|perfect|s0.0|p7"]["inc_net_seeds"])
            m, h = ci95(v - base)
            M(f"Voi{tag}{ht[het]}", usd(m)); M(f"Voi{tag}{ht[het]}CI", f"{h:.0f}")
            vm = np.array(R["rq3"][f"{c}|h{het}|mobile|s0.01|p7"]["inc_net_seeds"])
            m2, h2 = ci95(vm - base)
            M(f"Mob{tag}{ht[het]}", usd(m2)); M(f"Mob{tag}{ht[het]}CI", f"{h2:.0f}")
        M(f"MobClean{tag}", f"{R['rq3'][f'{c}|h1.0|mobile|s0.04|p7']['n_clean'][0]:.0f}")
        M(f"SiteClean{tag}", f"{R['rq3'][f'{c}|h1.0|site|s0.0|p7']['n_clean'][0]:.0f}")
    insp_w = R["rq3"]["fixed|h1.0|mobile|s0.01|p7"]["insp_cost"][0]
    insp_m = R["rq3"]["fixed|h1.0|mobile|s0.01|p28"]["insp_cost"][0]
    M("InspWeekly", usd(insp_w)); M("InspMonthly", usd(insp_m))
    visits = 365 / 7 * cfg["n_rows"]
    M("RowVisitsYr", usd(visits))

    # value of perfect information against row CV
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    voi = {}
    for c, tag, col in [("fixed", "Fix", C1), ("merchant", "Mer", C2)]:
        xs, ms, hs, first = [], [], [], None
        for het in HET_SWEEP:
            base = np.array(R["rq3"][f"{c}|h{het}|site|s0.0|p7"]["inc_net_seeds"])
            v = np.array(R["rq3"][f"{c}|h{het}|perfect|s0.0|p7"]["inc_net_seeds"])
            m, h = ci95(v - base)
            xs.append(cv(het)); ms.append(m); hs.append(h)
            if first is None and m - h > 0:
                first = cv(het)
        voi[tag] = (xs, ms, hs)
        M(f"VoiSigCV{tag}", f"{first:.2f}" if first is not None else "none")
        M(f"VoiTop{tag}", usd(ms[-1])); M(f"VoiTop{tag}CI", f"{hs[-1]:.0f}")
        ax.errorbar(xs, ms, yerr=hs, color=col, marker="o", ms=4, capsize=2,
                    label="Fixed tariff" if tag == "Fix" else "Merchant")
    ax.axhline(insp_w, color=MUTED, ls="--", lw=1.0); ax.axhline(insp_m, color=MUTED, ls=":", lw=1.0)
    ax.text(0.01, insp_w * 1.03, "weekly patrol cost", fontsize=6.5, color=MUTED, va="bottom")
    ax.text(0.01, insp_m * 1.06, "monthly patrol cost", fontsize=6.5, color=MUTED, va="bottom")
    ax.axvline(cv(1.0), color=MUTED, lw=0.8, ls="-.")
    ax.text(cv(1.0) + 0.006, insp_w * 0.55, "2x string spread\n(Micheli et al.)", fontsize=6.5, color=MUTED)
    ax.set_xlabel("Row exposure CV"); ax.set_ylabel("Value of perfect info (USD/yr)")
    ax.set_ylim(-150, insp_w * 1.25)
    ax.legend(loc="center left", fontsize=7)
    fig.savefig(OUT + "fig_cv.pdf")
    plt.close(fig)
    voimax = max(max(voi["Fix"][1]), max(voi["Mer"][1]))
    M("VoiMax", usd(voimax))
    M("BreakEvenInsp", f"{voimax / visits:.2f}")
    M("BreakEvenRatio", f"{insp_w / voimax:.0f}")

    # ------------------------------------------------------------------ sensitivity (cost x soiling rate)
    soil_keys = ["0.0015", "0.003", "0.0045"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.2), sharey=True)
    crows = [2.0, 4.0, 8.0, 12.0]
    sig = {"fixed": 0, "merchant": 0}
    for ax, c, title in zip(axes, ["fixed", "merchant"], ["Fixed tariff", "Merchant"]):
        for sm, col in zip(soil_keys, BLUE):
            ms = [R["sens"][f"{c}|c{cr}|s{sm}"]["paired"]["mean"] for cr in crows]
            hs = [R["sens"][f"{c}|c{cr}|s{sm}"]["paired"]["ci"] for cr in crows]
            sig[c] += sum(m - h > 0 for m, h in zip(ms, hs))
            ax.errorbar(np.array(crows) + (float(sm) - 0.003) * 60, ms, yerr=hs, color=col, marker="o", ms=4,
                        capsize=2, label=f"{float(sm) * 100:.2f} %/day")
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_xticks(crows); ax.set_xlabel("Cleaning cost per row (USD)")
        ax.set_title(title, fontsize=8, color=INK)
    axes[0].set_ylabel("Gain over best baseline (USD/yr)")
    axes[0].legend(title="Mean soiling rate", fontsize=7, title_fontsize=7, loc="upper left")
    fig.savefig(OUT + "fig_sens.pdf")
    plt.close(fig)
    M("SensSigFix", str(sig["fixed"])); M("SensSigMer", str(sig["merchant"]))
    M("SensN", str(len(crows) * len(soil_keys)))
    allm = [v["paired"]["mean"] for v in R["sens"].values()]
    M("SensMin", f"{min(allm):.0f}"); M("SensMax", f"{max(allm):.0f}")
    neg_sig = [k for k, v in R["sens"].items() if v["paired"]["mean"] + v["paired"]["ci"] < 0]
    M("SensNegSig", str(len(neg_sig)))
    hi = R["sens"]["merchant|c12.0|s0.0045"]["paired"]
    M("SensMerHi", f"{hi['mean']:.0f}"); M("SensMerHiCI", f"{hi['ci']:.0f}")
    doha = [R["sens"][f"{c}|c{cr}|s0.0045"]["paired"] for c in ("fixed", "merchant") for cr in (4.0,)]
    M("DohaFix", f"{doha[0]['mean']:.0f}"); M("DohaFixCI", f"{doha[0]['ci']:.0f}")
    M("DohaMer", f"{doha[1]['mean']:.0f}"); M("DohaMerCI", f"{doha[1]['ci']:.0f}")
    M("DohaIncFix", usd(R["sens"]["fixed|c4.0|s0.0045"]["proposed"][0]))
    M("DohaIncMer", usd(R["sens"]["merchant|c4.0|s0.0045"]["proposed"][0]))

    # ------------------------------------------------------------------ market regime sweep
    scales = [0.0, 1.0, 1.5, 2.0, 3.0]
    nm_ = {0.0: "Zero", 1.0: "Base", 1.5: "Qld", 2.0: "Mid", 3.0: "Sa"}
    fig, ax = plt.subplots(figsize=(3.5, 2.45))
    for c, tag, col in [("merchant", "Mer", C1), ("ppa", "Ppa", C2)]:
        xs = [R["price"][f"{c}|k{k}"]["stats"]["neg_all"] * 100 for k in scales]
        gb = [R["price"][f"{c}|k{k}"]["vs_best"]["mean"] for k in scales]
        gbc = [R["price"][f"{c}|k{k}"]["vs_best"]["ci"] for k in scales]
        gv = [R["price"][f"{c}|k{k}"]["vs_noval"]["mean"] for k in scales]
        gvc = [R["price"][f"{c}|k{k}"]["vs_noval"]["ci"] for k in scales]
        lab = "Merchant" if tag == "Mer" else "PPA clause"
        dx = -0.4 if tag == "Mer" else 0.4
        ax.errorbar(np.array(xs) + dx, gb, yerr=gbc, color=col, marker="o", ms=4, capsize=2, label=f"{lab}, vs best baseline")
        ax.errorbar(np.array(xs) + dx, gv, yerr=gvc, color=col, marker="s", ms=3.5, capsize=2, ls="--", label=f"{lab}, vs no valuation")
        for k in scales:
            r = R["price"][f"{c}|k{k}"]
            M(f"Pr{nm_[k]}Gain{tag}", f"{r['vs_best']['mean']:.0f}"); M(f"Pr{nm_[k]}Gain{tag}CI", f"{r['vs_best']['ci']:.0f}")
            M(f"Pr{nm_[k]}Noval{tag}", f"{r['vs_noval']['mean']:.0f}"); M(f"Pr{nm_[k]}Noval{tag}CI", f"{r['vs_noval']['ci']:.0f}")
            M(f"Pr{nm_[k]}Wins{tag}", str(r["vs_best"]["wins"]))
            M(f"Pr{nm_[k]}Inc{tag}", usd(r["proposed"][0]))
            M(f"Pr{nm_[k]}Pct{tag}", f"{r['vs_best']['mean'] / r['baseline'][0] * 100:.1f}")
    for k in scales:
        st = R["price"][f"merchant|k{k}"]["stats"]
        M(f"Pr{nm_[k]}Neg", f"{st['neg_all'] * 100:.1f}"); M(f"Pr{nm_[k]}NegDay", f"{st['neg_day'] * 100:.0f}")
        M(f"Pr{nm_[k]}Cap", f"{st['capture']:.2f}")
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.axvline(10.4, color=MUTED, lw=0.8, ls="-."); ax.axvline(31.3, color=MUTED, lw=0.8, ls="-.")
    ax.set_xlim(-1.5, 36); ax.set_xlabel("Hours with negative price (%); dash-dot: QLD 10.4, SA 31.3 (AEMO Q1 2026)", fontsize=6.5)
    ax.set_ylabel("Planner gain (USD/yr)")
    ax.legend(fontsize=6.3, loc="upper center", bbox_to_anchor=(0.5, -0.33), ncol=2, columnspacing=1.0, handlelength=2.2)
    fig.savefig(OUT + "fig_price.pdf")
    plt.close(fig)
    M("ExcessDefPct", f"{cv(1.0)**2/8*100:.1f}"); M("ExcessHiPct", f"{cv(1.5)**2/8*100:.1f}")

    # ------------------------------------------------------------------ example year (merchant, seed 0)
    clim, vexp, pbar = sim.planner_inputs("merchant")
    par = R["rq1"]["merchant"]["proposed"]["params"]
    r = sim.simulate("proposed", par, "merchant", 0, clim=clim, vexp=vexp, pbar=pbar, record=True)
    tr = r["trace"]
    w = sim.weather(0)
    ex = sim.exposure(sim.CONFIG)
    hi_row, lo_row = int(np.argmax(ex)), int(np.argmin(ex))
    fig, axes = plt.subplots(2, 1, figsize=(3.5, 3.6), gridspec_kw={"height_ratios": [1.3, 1]})
    ax = axes[0]
    d = np.arange(365)
    ax.plot(d, tr[:, hi_row] * 100, color=C1, lw=1.0, label=f"Row {hi_row + 1} (exposure {ex[hi_row]:.2f})")
    ax.plot(d, tr[:, lo_row] * 100, color=C2, lw=1.0, label=f"Row {lo_row + 1} (exposure {ex[lo_row]:.2f})")
    for rd in np.where(w["rain"] >= 5)[0]:
        ax.axvline(rd, color=MUTED, lw=0.6, ls=":")
    ax.set_ylabel("Soiling ratio (%)"); ax.set_xlabel("Day of year")
    ax.legend(fontsize=6.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0.2)
    ax = axes[1]
    cs = sim.clear_sky()
    for mo, col, lab in [(3, C1, "April"), (6, C2, "July"), (11, C3, "December")]:
        sel = cs["month"] == mo
        prof = [vexp[sel & (cs["hour"] == h)].mean() * 1000 for h in range(24)]
        ax.plot(range(24), prof, color=col, label=lab)
    ax.set_xlabel("Hour of day"); ax.set_ylabel("Expected value (USD/MWh)")
    ax.set_xticks([0, 6, 12, 18, 23])
    ax.legend(fontsize=6.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, borderaxespad=0.2)
    fig.tight_layout(h_pad=1.2)
    fig.savefig(OUT + "fig_example.pdf")
    plt.close(fig)
    M("ExHiRow", str(hi_row + 1)); M("ExLoRow", str(lo_row + 1))
    M("PbarMer", f"{pbar * 1000:.1f}")
    apr_noon = vexp[(cs["month"] == 3) & (cs["hour"] == 12)].mean() * 1000
    jul_noon = vexp[(cs["month"] == 6) & (cs["hour"] == 12)].mean() * 1000
    M("AprNoon", f"{apr_noon:.0f}"); M("JulNoon", f"{jul_noon:.0f}")

    # ------------------------------------------------------------------ extra robustness (rain scale, manual-scale cost)
    import json as _json
    X = _json.load(open(RES + "results_extra.json"))
    for c, tag in [("fixed", "Fix"), ("merchant", "Mer")]:
        for rs, nm in [(2.0, "Two"), (3.0, "Three")]:
            r = X["rain"][f"{c}|r{rs}"]
            M(f"Rain{nm}Gain{tag}", f"{r['paired']['mean']:.0f}"); M(f"Rain{nm}Gain{tag}CI", f"{r['paired']['ci']:.0f}")
        for cr, nm in [(24.0, "Mid"), (48.0, "Man")]:
            r = X["cost"][f"{c}|c{cr}"]
            M(f"Cost{nm}Gain{tag}", f"{r['paired']['mean']:.0f}"); M(f"Cost{nm}Gain{tag}CI", f"{r['paired']['ci']:.0f}")
            M(f"Cost{nm}Inc{tag}", usd(r["proposed"][0]))
    M("RainDaysTwo", f"{X['rain']['fixed|r2.0']['rain_days']:.0f}"); M("RainDaysThree", f"{X['rain']['fixed|r3.0']['rain_days']:.0f}")

    # ------------------------------------------------------------------ real AEMO price replay
    RR = _json.load(open(RES + "results_real.json"))
    RO = _json.load(open(RES + "results_oracle.json"))
    RL = _json.load(open(RES + "results_roll.json"))
    def _pool(folds):
        P = {p: np.concatenate([x[p]["inc_net_seeds"] for x in folds]) for p in folds[0]}
        bb = max(["fixed", "threshold", "econ"], key=lambda p: P[p].mean())
        d = P["proposed"] - P[bb]
        m, h = ci95(d)
        return m, h, P["proposed"].mean()
    rows = []
    for mk, mt in [("SA1", "Sa"), ("QLD1", "Qld")]:
        for c, ct in [("merchant", "Mer"), ("ppa", "Ppa")]:
            a = _pool(RR[f"{mk}|aligned|None"][c]); o = _pool(RO[f"{mk}|{c}"]); r = _pool(RL[f"{mk}|{c}"])
            for nm, v in (("Loyo", a), ("Orac", o), ("Roll", r)):
                M(f"Real{mt}{ct}{nm}", f"{v[0]:.0f}"); M(f"Real{mt}{ct}{nm}CI", f"{v[1]:.0f}")
            M(f"Real{mt}{ct}Inc", usd(a[2]))
            sg = lambda v: f"{v[0]:+.0f} $\\pm$ {v[1]:.0f}".replace("-", "$-$")
            rows.append(f"{'S. Australia' if mk == 'SA1' else 'Queensland'}, {'merchant' if c == 'merchant' else 'PPA'} & {usd(a[2])} & {sg(a)} & {sg(r)} & {sg(o)} \\\\")
    # ---- Spain (OMIE) replay: same protocol
    SP = _json.load(open(RES + "results_spain.json"))
    sgf = lambda m, h: f"{m:+.0f} $\\pm$ {h:.0f}".replace("-", "$-$")
    orac_all = [v[0] for v in []]
    for c, ct in [("merchant", "Mer"), ("ppa", "Ppa")]:
        for nm, key in (("Loyo", "loyo"), ("Roll", "roll"), ("Orac", "oracle")):
            M(f"RealEs{ct}{nm}", f"{SP[key][c]['paired']['mean']:.0f}"); M(f"RealEs{ct}{nm}CI", f"{SP[key][c]['paired']['ci']:.0f}")
        M(f"RealEs{ct}Inc", usd(SP["loyo"][c]["proposed"]))
        rows.append(f"Spain, {'merchant' if c == 'merchant' else 'PPA'} & {usd(SP['loyo'][c]['proposed'])} & {sgf(SP['loyo'][c]['paired']['mean'], SP['loyo'][c]['paired']['ci'])} & {sgf(SP['roll'][c]['paired']['mean'], SP['roll'][c]['paired']['ci'])} & {sgf(SP['oracle'][c]['paired']['mean'], SP['oracle'][c]['paired']['ci'])} \\\\")
    M("RealEsMerFoldOne", f"{SP['loyo']['merchant']['per_fold'][0]:.0f}")
    allor = [_pool(RO[f"{mk}|{c}"])[0] for mk in ("SA1", "QLD1") for c in ("merchant", "ppa")] + [SP["oracle"][c]["paired"]["mean"] for c in ("merchant", "ppa")]
    M("RealOracMin", f"{min(allor):.0f}"); M("RealOracMax", f"{max(allor):.0f}")
    es = I["es"]
    M("EsNeg", f"{es['neg'] * 100:.0f}"); M("EsNegLo", f"{min(es['neg_y']) * 100:.0f}"); M("EsNegHi", f"{max(es['neg_y']) * 100:.0f}")
    M("EsZero", f"{es['zero'] * 100:.0f}")
    M("EsPriceJump", f"{(es['jump'] - 1) * 100:.0f}")
    M("EsMean", f"{es['mean'] * 1000:.0f}")
    for mk, mt in [("SA1", "Sa"), ("QLD1", "Qld")]:
        a_ = I[mk]
        M(f"Aemo{mt}Neg", f"{a_['neg'] * 100:.0f}"); M(f"Aemo{mt}NegDay", f"{a_['neg_day'] * 100:.0f}")
        M(f"Aemo{mt}NegLo", f"{min(a_['neg_y']) * 100:.0f}"); M(f"Aemo{mt}NegHi", f"{max(a_['neg_y']) * 100:.0f}")
    treal = r"""\begin{table}[!t]
\centering
\caption{Replay of AEMO 2023 to 2025 prices (South Australia, Queensland) and OMIE 2023 to 2025 prices (Spain) with generated weather. Value of the proposed planner (USD per year) and its gain over the best tuned baseline (USD per year, 95\% interval) when prices are learned from the two other years, the previous year, or the test year itself. Fifty weather years per price year.}
\label{tab:real}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{lcccc}
\toprule
Market, contract & Value & Other yrs & Prev. yr & Test yr \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    open(OUT + "table_real.tex", "w").write(treal)


    # ------------------------------------------------------------------ real Dubai weather (NASA POWER) and NREL soiling fit
    WX = _json.load(open(RES + "results_wx.json"))
    for c, ct in [("fixed", "Fix"), ("merchant", "Mer"), ("ppa", "Ppa")]:
        M(f"Wx{ct}Gain", f"{WX[c]['paired']['mean']:.0f}"); M(f"Wx{ct}GainCI", f"{WX[c]['paired']['ci']:.0f}")
        M(f"Wx{ct}Syn", f"{WX[c]['synthetic']['paired']['mean']:.0f}"); M(f"Wx{ct}SynCI", f"{WX[c]['synthetic']['paired']['ci']:.0f}")
    M("WxIncMer", usd(WX["merchant"]["proposed"][0])); M("WxIncFix", usd(WX["fixed"]["proposed"][0])); M("WxIncPpa", usd(WX["ppa"]["proposed"][0]))
    cfg_s = dict(sim.CONFIG)
    syn_y = np.mean([sim.weather(s_, cfg_s)["pdc"].sum() for s_ in range(24)])
    real_y = I["wx"]["real_yield"]
    M("WxYieldReal", f"{real_y:,.0f}".replace(",", "{,}")); M("WxYieldSyn", f"{syn_y:,.0f}".replace(",", "{,}"))
    rd1 = I["wx"]["rain_days_1mm"]; rd5 = I["wx"]["rain_days_5mm"]
    M("WxRainDays", f"{np.mean(rd1):.1f}"); M("WxRainDaysFive", f"{np.mean(rd5):.1f}"); M("WxRainMin", f"{min(rd1)}"); M("WxRainMax", f"{max(rd1)}")
    M("WxNYears", "24")

    NR = _json.load(open(RES + "results_nrel.json"))
    for tag, nm in [("med", "Med"), ("p90", "Pn"), ("def_amp", "Def")]:
        for c, ct in [("fixed", "Fix"), ("merchant", "Mer")]:
            r = NR[f"{tag}|{c}"]
            M(f"Nrel{nm}Gain{ct}", f"{r['paired']['mean']:.0f}"); M(f"Nrel{nm}Gain{ct}CI", f"{r['paired']['ci']:.0f}")
            M(f"Nrel{nm}Inc{ct}", usd(r["proposed"][0]))
    n_ = I["nrel"]
    M("NrelSites", str(n_["sites"])); M("NrelSiteMonths", f"{n_['site_months']:,}".replace(",", "{,}"))
    M("NrelMedian", f"{n_['median']:.2f}"); M("NrelQOne", f"{n_['q1']:.2f}"); M("NrelQThree", f"{n_['q3']:.2f}")
    M("NrelSiteMedian", f"{n_['site_median']:.2f}"); M("NrelSitePn", f"{n_['site_p90']:.2f}"); M("NrelSiteMax", f"{n_['site_max']:.2f}")
    M("NrelAmp", f"{(n_['prof_max'] - n_['prof_min']) / (n_['prof_max'] + n_['prof_min']):.2f}"); M("NrelPeak", {"Sep": "September", "Oct": "October", "Aug": "August"}.get(n_["prof_peak"], n_["prof_peak"]))


    # ------------------------------------------------------------------ forecast hierarchy (EXP-02) and exact benchmark (EXP-01)
    FC = _json.load(open(RES + "results_forecast.json"))
    mname = {"SA1_aligned": "SA", "QLD1_aligned": "QLD", "ES_raw": "ES"}
    frows = []; allf = {m: [] for m in ("clim", "roll", "dayahead", "perfect")}
    fsg = lambda v: f"{v:+.0f}".replace("-", "$-$")
    for key, v in FC.items():
        mk, c = key.split("|")
        cells = []
        for m in ("clim", "roll", "dayahead", "perfect"):
            pf = v[m]["per_fold"]; allf[m] += pf
            cells.append(f"{fsg(v[m]['gain'])} [{fsg(min(pf))},{fsg(max(pf))}]")
        frows.append(f"{mname[mk]}, {'merchant' if c == 'merchant' else 'PPA'} & " + " & ".join(cells) + " \\\\")
    tfore = r"""\begin{table*}[!t]
\centering
\caption{Gain of the contract-aware planner over the best tuned baseline (USD per year) by price information, with the range over the three price years in brackets. SA, QLD and ES are South Australia, Queensland and Spain. Climatology is the profile of the two other years, rolling is the mean of the previous 28 days, day-ahead adds the next 24 h, and perfect foresight is not deployable.}
\label{tab:fore}
\scriptsize
\setlength{\tabcolsep}{2.5pt}
\begin{tabular}{lcccc}
\toprule
Market, contract & Climatology & Rolling & Day-ahead & Perfect \\
\midrule
""" + "\n".join(frows) + r"""
\bottomrule
\end{tabular}
\end{table*}
"""
    open(OUT + "table_fore.tex", "w").write(tfore)
    M("ForeRollPos", str(sum(x > 0 for x in allf["roll"]))); M("ForeN", str(len(allf["roll"])))
    M("ForeClimNeg", str(sum(x < 0 for x in allf["clim"]))); M("ForeDayPos", str(sum(x > 0 for x in allf["dayahead"])))
    M("ForeRollLo", f"{min(v['roll']['gain'] for v in FC.values()):.0f}"); M("ForeRollHi", f"{max(v['roll']['gain'] for v in FC.values()):.0f}")
    M("ForeDayLo", f"{min(v['dayahead']['gain'] for v in FC.values()):.0f}"); M("ForeDayHi", f"{max(v['dayahead']['gain'] for v in FC.values()):.0f}")
    M("ForePerfLo", f"{min(v['perfect']['gain'] for v in FC.values()):.0f}"); M("ForePerfHi", f"{max(v['perfect']['gain'] for v in FC.values()):.0f}")
    _sa = FC["SA1_aligned|merchant"]["roll"]["per_fold"]
    M("RealSaMerRollRange", f"{fsg(min(_sa))} to {fsg(max(_sa))} USD per year")
    M("ForeRollCasesPos", str(sum(v["roll"]["gain"] > 0 for v in FC.values())))
    EX = _json.load(open(RES + "results_exact.json"))
    MP = _json.load(open(RES + "results_mpc.json"))
    erows = []; maxgap = 0; nlt = 0; infos = []; opts = []; mpcp = []
    for key, v in EX.items():
        contract, cr = key.split("|"); opt = np.mean([e["opt"] for e in v["exact"]])
        maxgap = max(maxgap, np.nanmax([e["gap"] for e in v["exact"]]))
        mpc = np.mean([e["mpc"] for e in MP[key]]); prop = np.mean(v["site"]["proposed"]["seeds"])
        pc = lambda t, p: f"{100 * np.mean(v[t][p]['seeds']) / opt:.0f}"
        erows.append(f"{'Fixed' if contract == 'fixed' else 'Merchant'}, {cr[1:].replace('.0', '')} & {opt:.0f} & {100 * mpc / opt:.0f} & {pc('site', 'fixed')} & {pc('site', 'threshold')} & {pc('site', 'econ')} & {pc('site', 'proposed')} & {pc('matched', 'proposed')} \\\\")
        tag = ("Fix" if contract == "fixed" else "Mer") + ("Lo" if cr == "c4.0" else "Hi")
        M(f"Ex{tag}Opt", f"{opt:.0f}"); M(f"Ex{tag}Prop", pc("site", "proposed"))
        M(f"Ex{tag}Regret", f"{opt - prop:.0f}")
        M(f"Ex{tag}Info", f"{opt - mpc:.0f}"); M(f"Ex{tag}OptReg", f"{mpc - prop:.0f}".replace("-", "-")); M(f"Ex{tag}Mpc", f"{100 * mpc / opt:.0f}")
        infos.append(opt - mpc); opts.append(mpc - prop); mpcp.append(100 * mpc / opt); nlt += (mpc - prop) < (opt - mpc)
    M("ExInfoLo", f"{min(infos):.0f}"); M("ExInfoHi", f"{max(infos):.0f}")
    M("ExOptLo", f"{min(opts):.0f}"); M("ExOptHi", f"{max(opts):.0f}")
    M("ExMpcLo", f"{min(mpcp):.0f}"); M("ExMpcHi", f"{max(mpcp):.0f}"); M("ExOptLtInfo", str(nlt))
    M("ExMaxGap", f"{maxgap * 100:.2f}"); M("ExNInst", "20")
    texact = r"""\begin{table}[!t]
\centering
\caption{Exact benchmark on 20 instances of 6 rows and 60 summer days. Clairvoyant optimum (USD per instance, value over no cleaning), and the share of it reached by the information-matched optimiser (receding horizon, same information as the planner), the tuned policies, and the planner with perfect state and value information. Settings are contract and cleaning cost per row (USD).}
\label{tab:exact}
\scriptsize
\setlength{\tabcolsep}{2.5pt}
\begin{tabular}{lccccccc}
\toprule
Setting & Clairv. & Matched & Fixed & Thr. & Econ & Prop. & Prop., perfect \\
\midrule
""" + "\n".join(erows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    open(OUT + "table_exact.tex", "w").write(texact)

    # ------------------------------------------------------------------ write numbers.tex
    with open(OUT + "numbers.tex", "w") as f:
        f.write("% Auto-generated by src/make_outputs.py from results/results.json. Do not edit.\n")
        for k, v in sorted(macros.items()):
            assert k.isalpha(), k
            if isinstance(v, str) and v.startswith("-") and v[1:2].isdigit():
                v = "$-$" + v[1:]
            f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
