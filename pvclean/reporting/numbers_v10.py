"""v10 tables and number macros. Reads results/*.json (v9 results that were re-run bit-identically in EXP-01, plus v10 results).
Writes paper/numbers_v10.tex, paper/table_fore.tex (replacement), paper/table_exact.tex (replacement)."""
from __future__ import annotations


def build(R: str, OUT: str, RES_OUT: str) -> None:
    """R: results directory with a trailing slash. OUT: paper directory. RES_OUT: where macros_v10.json goes."""
    import json, os
    import numpy as np
    from pvclean import stats as evaluation

    M = {}                                   # macro name -> string

    def fmt(x, d=0, sign=False):
        s = f"{abs(x):,.{d}f}".replace(",", "{,}") if abs(x) >= 10000 else f"{abs(x):.{d}f}"
        if x < 0 and float(s.replace("{,}", "")) != 0: return "$-$" + s
        return ("+" if sign else "") + s

    # ------------------------------------------------------------------ real-market replay (F0..F4, ft)
    rep = json.load(open(R + "results_replay.json"))
    CASES = [("SA1_aligned", "merchant", "SA, merchant"), ("SA1_aligned", "ppa", "SA, PPA"), ("QLD1_aligned", "merchant", "QLD, merchant"),
             ("QLD1_aligned", "ppa", "QLD, PPA"), ("ES_raw", "merchant", "ES, merchant"), ("ES_raw", "ppa", "ES, PPA")]
    BASE = ["fixed", "threshold", "econ"]
    rows = []; summ = {}
    for mk, c, label in CASES:
        folds = [rep[f"{mk}|{c}|{k}"] for k in range(3)]
        pooled = {b: np.concatenate([np.array(f["F0"][b]["seeds"]) for f in folds]) for b in BASE}
        bb = max(BASE, key=lambda b: pooled[b].mean())
        cell = {}
        for pol in ("proposed", "ft"):
            for sc in ("F0", "F2", "F3", "F4"):
                if sc == "F4" and pol == "ft": pass
                d = {k: np.array(folds[k][sc][pol]["seeds"]) - np.array(folds[k]["F0"][bb]["seeds"]) for k in range(3)}
                cell[(pol, sc)] = evaluation.year_stratified(d, n_boot=4000)
        dpf = {sc: evaluation.year_stratified({k: np.array(folds[k][sc]["proposed"]["seeds"]) - np.array(folds[k][sc]["ft"]["seeds"]) for k in range(3)}, n_boot=4000)
               for sc in ("F0", "F2", "F3", "F4")}
        d1 = {k: np.array(folds[k]["F1"]["proposed"]["seeds"]) - np.array(folds[k]["F1"]["ft"]["seeds"]) for k in (1, 2)}
        dpf["F1"] = evaluation.year_stratified(d1, n_boot=4000)
        summ[(mk, c)] = dict(label=label, bb=bb, cell=cell, dpf=dpf)

    def cellstr(cl, ci=True):
        return f"{fmt(cl['mean'], 0, True)} [{fmt(cl['lo'], 0)},{fmt(cl['hi'], 0)}]"

    tab = ["\\begin{table*}[!t]", "\\centering",
           "\\caption{Gain over the best tuned baseline (USD per year; mean over the three price years, with the 95\\% interval from resampling the 50 weather and dust replicates inside each year) for the contract-aware planner and for the forecast-matched threshold (FT), by price forecast. F0 is the profile of the two other price years (not causal for the 2023 and 2024 folds), F2 the mean of the previous 28 days, F3 adds the operating day (a published day-ahead product in Spain only, a next-day-known proxy for the Australian regions) and F4 is the oracle. SA, QLD and ES are South Australia, Queensland and Spain.}",
           "\\label{tab:fore}", "\\scriptsize", "\\setlength{\\tabcolsep}{2.2pt}",
           "\\begin{tabular}{lccccccc}", "\\toprule",
           " & \\multicolumn{4}{c}{Contract-aware planner} & \\multicolumn{3}{c}{FT threshold} \\\\ \\cmidrule(lr){2-5}\\cmidrule(lr){6-8}",
           "Market, contract & F0 & F2 & F3 & F4 (oracle) & F0 & F2 & F3 \\\\", "\\midrule"]
    for (mk, c), s in summ.items():
        cl = s["cell"]
        tab.append(f"{s['label']} & {cellstr(cl[('proposed','F0')])} & {cellstr(cl[('proposed','F2')])} & {cellstr(cl[('proposed','F3')])} & {fmt(cl[('proposed','F4')]['mean'],0,True)} & {cellstr(cl[('ft','F0')])} & {cellstr(cl[('ft','F2')])} & {cellstr(cl[('ft','F3')])} \\\\")
    tab += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    open(OUT + "table_fore.tex", "w").write("\n".join(tab) + "\n")

    # counts for the text
    n_ft_beats_F0 = sum(s["dpf"]["F0"]["mean"] < 0 for s in summ.values())          # ft better than proposed under F0
    n_ft_beats_F1 = sum(s["dpf"]["F1"]["mean"] < 0 for s in summ.values())
    n_prop_beats_F2 = sum(s["dpf"]["F2"]["lo"] > 0 for s in summ.values())
    n_prop_beats_F3 = sum(s["dpf"]["F3"]["lo"] > 0 for s in summ.values())
    M["FtBeatsPropFzero"] = n_ft_beats_F0; M["FtBeatsPropFone"] = n_ft_beats_F1
    M["PropBeatsFtFtwo"] = n_prop_beats_F2; M["PropBeatsFtFthree"] = n_prop_beats_F3
    f2d = [s["dpf"]["F2"]["mean"] for s in summ.values()]; f3d = [s["dpf"]["F3"]["mean"] for s in summ.values()]
    M["PropMinusFtTwoLo"] = fmt(min(f2d), 0, True); M["PropMinusFtTwoHi"] = fmt(max(f2d), 0, True)
    M["PropMinusFtThreeLo"] = fmt(min(f3d), 0, True); M["PropMinusFtThreeHi"] = fmt(max(f3d), 0, True)
    M["PropFzeroLoss"] = sum(s["cell"][("proposed", "F0")]["hi"] < 0 for s in summ.values())
    M["PropFtwoPos"] = sum(s["cell"][("proposed", "F2")]["lo"] > 0 for s in summ.values())
    M["PropFthreePos"] = sum(s["cell"][("proposed", "F3")]["lo"] > 0 for s in summ.values())
    g2 = [s["cell"][("proposed", "F2")]["mean"] for s in summ.values()]; g3 = [s["cell"][("proposed", "F3")]["mean"] for s in summ.values()]
    M["RollLo"] = fmt(min(g2), 0, True); M["RollHi"] = fmt(max(g2), 0, True); M["DayLo"] = fmt(min(g3), 0, True); M["DayHi"] = fmt(max(g3), 0, True)
    yp2 = sum(v for s in summ.values() for v in [s["cell"][("proposed", "F2")]["years_positive"]]); M["RollYearsPos"] = yp2
    ft2 = [s["cell"][("ft", "F2")] for s in summ.values()]; M["FtTwoBelowBase"] = sum(c["hi"] < 0 for c in ft2)
    M["EsMerFzeroLoss"] = fmt(summ[("ES_raw", "merchant")]["cell"][("proposed", "F0")]["mean"], 0)

    # ------------------------------------------------------------------ generated markets: ft
    ftj = json.load(open(R + "results_ft_synthetic.json"))
    for c, tag in [("fixed", "Fix"), ("merchant", "Mer"), ("ppa", "Ppa"), ("capped", "Cap")]:
        st = ftj[c]["stats"]
        M["FtGain" + tag] = fmt(st["ft_vs_best_baseline"]["mean"], 0, True)
        M["FtGainLo" + tag] = fmt(st["ft_vs_best_baseline"]["boot_lo"], 0); M["FtGainHi" + tag] = fmt(st["ft_vs_best_baseline"]["boot_hi"], 0)
        M["PropMinusFt" + tag] = fmt(st["proposed_vs_ft"]["mean"], 0, True)
        M["PropMinusFtLo" + tag] = fmt(st["proposed_vs_ft"]["boot_lo"], 0); M["PropMinusFtHi" + tag] = fmt(st["proposed_vs_ft"]["boot_hi"], 0)
        M["PropMinusEcon" + tag] = fmt(st["proposed_vs_econ"]["mean"], 0, True)

    # ------------------------------------------------------------------ exact benchmark with corrected horizon
    ex = json.load(open(R + "results_exact.json")); mp = json.load(open(R + "results_matched.json"))
    hz_path = R + "results_horizon.json"
    hz = None
    if os.path.exists(hz_path):
        h = json.load(open(hz_path))
        if len(h) >= 680:
            hz = {}
            for x in h:
                hz.setdefault(f"{x['contract']}|{int(x['crow'])}", {}).setdefault(x["arm"], []).append(x["gain"])
            hz = {k: {a: float(np.mean(v)) for a, v in d.items()} for k, d in hz.items()}
            hzsrc = "computed from results_horizon.json (680 runs)"
    if hz is None:
        t = json.load(open(R + "horizon_summary_transcribed.json")); hz = t["mean_gain"]; hzsrc = "transcribed from <gpu-host> OPTIMISATION_DIAGNOSTICS.md"
    SET = [("fixed", 4.0), ("fixed", 12.0), ("merchant", 4.0), ("merchant", 12.0)]
    texact = ["\\begin{table}[!t]", "\\centering",
              "\\caption{Exact benchmark, 20 instances of 6 rows and 60 days: clairvoyant optimum (USD over no cleaning) and share of it reached by the receding-horizon MILP (14 days; 30 days with a 30-day tail) and by the tuned policies. Settings: contract, cleaning cost per row (USD).}",
              "\\label{tab:exact}", "\\scriptsize", "\\setlength{\\tabcolsep}{2.3pt}", "\\begin{tabular}{lcccccccc}", "\\toprule",
              "Setting & Clairv. & MILP 14 & MILP 30+30 & Fixed & Thr. & Econ & FT & Prop. \\\\", "\\midrule"]
    pct = {}
    for c, cr in SET:
        k = f"{c}|c{cr}"; kk = f"{c}|{int(cr)}"
        opt = float(np.mean([e["opt"] for e in ex[k]["exact"]]))
        vals = [hz[kk]["H14"], hz[kk]["H30+T30"]]
        site = {p: float(np.mean(ex[k]["site"][p]["seeds"])) for p in ("fixed", "threshold", "econ")}
        ftv = float(np.mean(mp["part_b"][k]["ft"]["seeds"])); prv = float(np.mean(ex[k]["site"]["proposed"]["seeds"]))
        row = [opt] + vals + [site["fixed"], site["threshold"], site["econ"], ftv, prv]
        pct[kk] = [100 * v / opt for v in row[1:]]
        texact.append(f"{c.capitalize()}, {int(cr)} & {opt:.0f} & " + " & ".join(f"{p:.0f}" for p in pct[kk]) + " \\\\")
    texact += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    open(OUT + "table_exact.tex", "w").write("\n".join(texact) + "\n")
    _o = sorted(p[0] for p in pct.values())[1:]  # elsewhere = all but the merchant/12 case
    M["MilpFourteenLo"] = f"{min(_o):.0f}"; M["MilpFourteenHi"] = f"{max(p[0] for p in pct.values()):.0f}"
    M["MilpLongLo"] = f"{min(p[1] for p in pct.values()):.0f}"; M["MilpLongHi"] = f"{max(p[1] for p in pct.values()):.0f}"
    M["MilpFourteenMerTwelve"] = f"{pct['merchant|12'][0]:.0f}"; M["MilpLongMerTwelve"] = f"{pct['merchant|12'][1]:.0f}"
    M["MilpFourteenMerTwelveUsd"] = f"{hz['merchant|12']['H14']:.1f}"; M["MilpLongMerTwelveUsd"] = f"{hz['merchant|12']['H30+T30']:.1f}"
    for kk, tag in [("fixed|4", "FixLo"), ("fixed|12", "FixHi"), ("merchant|4", "MerLo"), ("merchant|12", "MerHi")]:
        M["FtPct" + tag] = f"{pct[kk][5]:.0f}"; M["PropPct" + tag] = f"{pct[kk][6]:.0f}"; M["MilpLongPct" + tag] = f"{pct[kk][1]:.0f}"
    # ft vs proposed on small instances
    for k, tag in [("fixed|c4.0", "FixLo"), ("fixed|c12.0", "FixHi"), ("merchant|c4.0", "MerLo"), ("merchant|c12.0", "MerHi")]:
        a, b = np.array(mp["part_b"][k]["proposed"]["seeds"]), np.array(mp["part_b"][k]["ft"]["seeds"])
        s = evaluation.paired_summary(a, b)
        M["SmallPropMinusFt" + tag] = fmt(s["mean"], 0, True); M["SmallPropMinusFtLo" + tag] = fmt(s["boot_lo"], 0); M["SmallPropMinusFtHi" + tag] = fmt(s["boot_hi"], 0)
    n_ft_better_small = sum(np.mean(mp["part_b"][k]["ft"]["seeds"]) > np.mean(mp["part_b"][k]["proposed"]["seeds"]) +
                            0 for k in mp["part_b"] if evaluation.paired_summary(mp["part_b"][k]["proposed"]["seeds"], mp["part_b"][k]["ft"]["seeds"])["boot_hi"] < 0)
    M["SmallFtBetterSettings"] = n_ft_better_small

    # ------------------------------------------------------------------ forecast error vs decision value (EXP-07)
    fa = json.load(open(R + "results_forecast_audit.json"))
    mae = {}
    for m in fa["metrics"]:
        mae[(m["market"], m["contract"], m["year"], m["scenario"])] = m
    xs = []; ys = []; ordok = 0; ordn = 0
    for (mk, c), s in summ.items():
        for k in range(3):
            sc = ["F0", "F2", "F3"]
            gains = [float(np.mean(np.array(rep[f"{mk}|{c}|{k}"][q]["proposed"]["seeds"]))) for q in sc]
            errs = [mae[(mk, c, k, q)]["mae_prod_w"] for q in sc]
            xs += errs; ys += gains
            ordn += 1; ordok += int(np.argsort(errs).tolist() == np.argsort([-g for g in gains]).tolist())
    rho, p = evaluation.spearman(xs, ys)
    M["LeakChecks"] = f"{fa['leakage']['checks']:,}".replace(",", "{,}")
    assert fa["leakage"]["failures"] == 0
    M["MaeGainRho"] = f"{rho:.2f}"; M["MaeGainP"] = f"{p:.3f}"; M["MaeRankAgree"] = ordok; M["MaeRankN"] = ordn
    # ES merchant F0 vs F2 MAE ratio and SA merchant
    M["SaMerMaeFzero"] = f"{np.mean([mae[('SA1_aligned','merchant',k,'F0')]['mae_prod_w'] for k in range(3)]):.4f}"
    M["SaMerMaeFtwo"] = f"{np.mean([mae[('SA1_aligned','merchant',k,'F2')]['mae_prod_w'] for k in range(3)]):.4f}"

    with open(OUT + "numbers_v10.tex", "w") as f:
        f.write("% Auto-generated by src/make_outputs_v10.py. Do not edit.\n")
        for k, v in sorted(M.items()):
            assert k.isalpha(), k
            f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    json.dump({k: str(v) for k, v in M.items()}, open(RES_OUT + "macros_v10.json", "w"), indent=1)
