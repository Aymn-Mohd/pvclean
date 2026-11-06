"""Write the generated tables of docs/R1_SUMMARY.md from results/results_chrono.json, results_rq1_decomp.json, price_audit.json and
results_sanity_tau.json. The hand-written header and deviation sections live in docs/R1_SUMMARY_head.md and
docs/R1_SUMMARY_tail.md; this script concatenates head + tables + tail."""
from __future__ import annotations
from typing import Any
import os, json
import numpy as np

from pvclean.data import results_dir

R = lambda f: json.load(open(os.path.join(results_dir(), f)))
MAIN = ["SA1_aligned", "QLD1_aligned", "ES_raw"]
SENS = ["SA1_raw", "QLD1_raw"]
YL = {"SA1_aligned": {"Y2": "A2 Jul23-Jun24", "Y3": "A3 Jul24-Jun25", "Y3frozen": "A3 Jul24-Jun25"},
      "QLD1_aligned": {"Y2": "A2 Jul23-Jun24", "Y3": "A3 Jul24-Jun25", "Y3frozen": "A3 Jul24-Jun25"},
      "ES_raw": {"Y2": "2024", "Y3": "2025", "Y3frozen": "2025"},
      "SA1_raw": {"Y2": "2024", "Y3": "2025", "Y3frozen": "2025"}, "QLD1_raw": {"Y2": "2024", "Y3": "2025", "Y3frozen": "2025"}}
MN = {"SA1_aligned": "SA1", "QLD1_aligned": "QLD1", "ES_raw": "ES", "SA1_raw": "SA1 raw", "QLD1_raw": "QLD1 raw"}


def ci(c: Any) -> Any:
    """A mean with its interval, as text."""
    return f"{c['mean']:+.0f} [{c['lo']:+.0f}, {c['hi']:+.0f}]"


def sign(c: Any) -> Any:
    """The sign of a mean, as text."""
    return "CI > 0" if c["lo"] > 0 else ("CI < 0" if c["hi"] < 0 else ("+" if c["mean"] > 0 else "-"))


def cmp_table(ch: Any, markets: Any, folds: Any, key: Any, label: Any, title: Any) -> Any:
    """Markdown table of one comparison."""
    L = [f"**{label}.** {title}", "", "| market | contract | test year | fold | mean [95% CI] USD/yr | sign | wins /50 |", "|---|---|---|---|---|---|---|"]
    for mk in markets:
        for c in ("merchant", "ppa"):
            for f in folds:
                r = ch[f"{mk}|{c}|{f}"]["cmp"][key]
                L.append(f"| {MN[mk]} | {c} | {YL[mk][f]} | {f} | {ci(r)} | {sign(r)} | {r['wins']} |")
    return L + [""]


def count_line(ch: Any, markets: Any, folds: Any, key: Any, label: Any) -> Any:
    """One line counting signs and intervals."""
    rows = [ch[f"{mk}|{c}|{f}"]["cmp"][key] for mk in markets for c in ("merchant", "ppa") for f in folds]
    return (f"{label}: {sum(r['mean'] > 0 for r in rows)} of {len(rows)} means > 0; {sum(r['lo'] > 0 for r in rows)} intervals wholly above 0, "
            f"{sum(r['hi'] < 0 for r in rows)} wholly below 0.")


def tables() -> Any:
    """The generated R1 tables."""
    ch = R("results_chrono.json"); dc = R("results_rq1_decomp.json"); au = R("price_audit.json"); st = R("results_sanity_tau.json")
    v = ch["_verdict_H_R1"]
    L = ["## 1. H-R1 verdict (MAIN)", "",
         f"**MAIN.** Verdict: **{v['verdict']}**. Planner minus FT under F2 has mean > 0 in {v['mean_pos']} of {v['n']} case-years "
         f"(rule for SUPPORTED: >= 10) and {v['ci_wholly_below']} interval lies wholly below 0 (rule: none); "
         f"{v['mean_nonpos']} of {v['n']} means are <= 0 (NOT SUPPORTED needs >= 6), so the rule gives PARTIAL. "
         f"{v['ci_wholly_above']} of {v['n']} intervals lie wholly above 0.", ""]
    L += cmp_table(ch, MAIN, ("Y2", "Y3"), "planner-ft|F2", "MAIN",
                   "Planner minus FT, F2, net value per seed (USD/yr), mean and 95% t-interval over the 50 test seeds; conditional on that price year.")
    L += ["## 2. Secondary comparisons", ""]
    L += cmp_table(ch, MAIN, ("Y2", "Y3"), "planner-bestbase|F2", "DESCRIPTIVE",
                   "Planner minus the training-selected best conventional baseline (fixed, threshold, econ), F2.")
    L += [count_line(ch, MAIN, ("Y2", "Y3"), "planner-bestbase|F2", "DESCRIPTIVE"), "",
          "| market | contract | best baseline per fold (training mean) |", "|---|---|---|"]
    for mk in MAIN + SENS:
        for c in ("merchant", "ppa"):
            L.append(f"| {MN[mk]} | {c} | " + ", ".join(f"{f}: {ch[f'{mk}|{c}|{f}']['best_baseline']}" for f in ("Y2", "Y3", "Y3frozen")) + " |")
    L += [""]
    L += cmp_table(ch, MAIN, ("Y2", "Y3"), "ft-bestbase|F2", "DESCRIPTIVE", "FT minus the training-selected best baseline, F2.")
    L += [count_line(ch, MAIN, ("Y2", "Y3"), "ft-bestbase|F2", "DESCRIPTIVE"), ""]
    L += cmp_table(ch, MAIN, ("Y3frozen",), "planner-ft|F2", "DESCRIPTIVE",
                   "Year 3 secondary: year-1 parameters and planner inputs frozen; planner minus FT, F2.")
    s2 = ch["_verdict_secondary_Y3frozen"]
    L += [f"With Y3frozen in place of Y3 the same rule would give {s2['verdict']} ({s2['mean_pos']}/12 positive, {s2['ci_wholly_below']} wholly below 0) (DESCRIPTIVE).", ""]
    L += ["## 3. Forecast sensitivity (SENSITIVITY)", "",
          "**SENSITIVITY.** Planner minus FT per forecast; each policy re-tuned under that forecast. CLIM = causal climatology "
          "(month x hour profile of the prior years); F3 = ES day-ahead, Australia proxy (realised operating-day 5-min prices); F4 = oracle (not deployable).", "",
          "| market | contract | test year | F2 | CLIM | F3 | F4 |", "|---|---|---|---|---|---|---|"]
    for mk in MAIN:
        for c in ("merchant", "ppa"):
            for f in ("Y2", "Y3"):
                cm = ch[f"{mk}|{c}|{f}"]["cmp"]
                L.append(f"| {MN[mk]} | {c} | {YL[mk][f]} | " + " | ".join(ci(cm[f"planner-ft|{n}"]) for n in ("F2", "CLIM", "F3", "F4")) + " |")
    L += [""]
    sv = ch["_sensitivity_raw_calendar"]
    L += cmp_table(ch, SENS, ("Y2", "Y3"), "planner-ft|F2", "SENSITIVITY",
                   "Australia, raw calendar years (2023 train; 2024, 2025 test), no season alignment; planner minus FT, F2.")
    L += [f"Raw-calendar sensitivity: {sv['mean_pos']} of {sv['n']} means > 0, {sv['ci_wholly_below']} wholly below 0, {sv['ci_wholly_above']} wholly above 0 (SENSITIVITY; the 12-case rule does not apply).", ""]
    L += cmp_table(ch, SENS, ("Y2", "Y3"), "planner-bestbase|F2", "SENSITIVITY", "Australia raw calendar: planner minus the training-selected best baseline, F2.")

    L += ["## 4. Price audit (ANALYSIS)", "",
          "**ANALYSIS.** Old = hourly-mean valuation (v9/v10 rule: merchant max(mean, 0), PPA paid iff mean >= 0) on the same contiguous R1 years; "
          "new = interval-level (merchant mean of max(p, 0); PPA paid share of intervals). Uncleaned-plant revenue is the mean over the 50 test seeds' weather (USD/yr).", "",
          "| market | year | merchant rev old | new | change | PPA rev old | new | change | PPA zero-pay h old | unpaid h new | h with any neg. interval | neg. hour share old | neg. interval share new |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in au["rows"]:
        L.append(f"| {MN[r['market']]} | {r['label']} | {r['merchant_rev_uncleaned_old']:,.0f} | {r['merchant_rev_uncleaned_new']:,.0f} | {r['merchant_rev_change_pct']:+.2f}% | "
                 f"{r['ppa_rev_uncleaned_old']:,.0f} | {r['ppa_rev_uncleaned_new']:,.0f} | {r['ppa_rev_change_pct']:+.2f}% | {r['ppa_zero_hours_old']} | "
                 f"{r['ppa_unpaid_hours_new']:.0f} | {r['hours_any_negative_interval']} | {100 * r['neg_hour_share_old']:.2f}% | {100 * r['neg_interval_share_new']:.2f}% |")
    L += [""]

    def drow(name, d):
        g = lambda k, s=0: f"{d[k]['mean']:+.{s}f} ± {d[k]['ci']:.{s}f}"
        return (f"| {name} | {g('d_net')} | {g('d_revenue')} | {g('d_energy_mwh', 2)} | {g('d_clean_cost')} | {g('d_mission_cost')} | "
                f"{g('quantity')} | {g('timing')} |")
    hdr = ["| case | d net | d revenue | d energy MWh | d (cleanings x c_row) | d (missions x c_mission) | quantity | timing |", "|---|---|---|---|---|---|---|---|"]
    L += ["## 5. Decompositions (ANALYSIS)", "",
          "**ANALYSIS.** Per seed A minus B, mean ± 95% paired half-width over 50 seeds (USD/yr unless stated). quantity = d energy x v_ref with v_ref the "
          "policy-independent production-weighted mean contract value of the seed-year; timing = d revenue - quantity; d net = d revenue - d cleaning cost - "
          "d mission cost (identity residual 0 in every case). Under the flat-tariff contracts (fixed, capped) timing is 0 by construction.", "",
          f"RQ1 rerun reproduces results/results.json rq1 inc_net: max |diff| = {dc['rq1_reproduction']['max_abs_diff']:.1e} (tolerance 1e-6), OK = {dc['rq1_reproduction']['ok']}.", "",
          "**ANALYSIS.** Generated markets (RQ1, 4 contracts, 50 test seeds). Best baseline selected by training mean.", ""] + hdr
    for c, r in dc["rq1"].items():
        L.append(drow(f"{c}: planner - FT", r["decomp"]["planner-ft"]))
        L.append(drow(f"{c}: planner - {r['best_baseline_train']}", r["decomp"]["planner-bestbase"]))
    L += ["", "Training-selected best baseline vs the test-selected one stored in results.json: " +
          ", ".join(f"{c} {r['best_baseline_train']} (stored {r['best_baseline_stored_test_selected']})" for c, r in dc["rq1"].items()) + ".", "",
          "**ANALYSIS.** R1 case-years, F2, planner minus FT.", ""] + hdr
    for k, r in dc["r1"].items():
        mk, c, f = k.split("|")
        L.append(drow(f"{MN[mk]} {c} {YL[mk][f]} ({f})", r["decomp"]["planner-ft"]))
    L += ["", "**ANALYSIS.** R1 case-years, F2, planner minus the training-selected best baseline.", ""] + hdr
    for k, r in dc["r1"].items():
        mk, c, f = k.split("|")
        L.append(drow(f"{MN[mk]} {c} {YL[mk][f]} ({f}) vs {r['best_baseline']}", r["decomp"]["planner-bestbase"]))
    L += [""]

    L += ["## 6. Tuned parameters per year (DESCRIPTIVE)", "",
          "**DESCRIPTIVE.** F2 parameters selected on the training years (Y2: year 1; Y3: years 1+2; Y3frozen reuses Y2's).", "",
          "| market | contract | fold | fixed T | threshold theta | econ b | FT (Hb, b, antic) | planner (beta, kappa) |", "|---|---|---|---|---|---|---|---|"]
    for mk in MAIN + SENS:
        for c in ("merchant", "ppa"):
            for f in ("Y2", "Y3"):
                t = ch[f"{mk}|{c}|{f}"]["tuned"]["F2"]; P = lambda p: t[p]["params"]
                L.append(f"| {MN[mk]} | {c} | {f} | {P('fixed')['T']} | {P('threshold')['theta']} | {P('econ')['b']} | "
                         f"({P('ft')['Hb']}, {P('ft')['b']}, {P('ft')['antic']}) | ({P('proposed')['beta']}, {P('proposed')['kappa']}) |")
    L += ["", "**DESCRIPTIVE.** Mean row cleanings per year at test, F2.", "", "| market | contract | fold | fixed | threshold | econ | FT | planner |", "|---|---|---|---|---|---|---|---|"]
    for mk in MAIN + SENS:
        for c in ("merchant", "ppa"):
            for f in ("Y2", "Y3"):
                t = ch[f"{mk}|{c}|{f}"]["test"]["F2"]
                L.append(f"| {MN[mk]} | {c} | {f} | " + " | ".join(f"{np.mean(t[p]['n_clean']):.0f}" for p in ("fixed", "threshold", "econ", "ft", "proposed")) + " |")
    L += [""]

    L += ["## 7. Single-row sanity check (ANALYSIS)", "",
          "**ANALYSIS.** One row, constant price (0.06 USD/kWh), constant daily output, linear value-loss growth L(t) = a t, no rain, no access windows, "
          f"c_mission = 0, c_row = {st['c_row']:.0f} USD, perfect state information. tau* = sqrt(2c/a). The planner's index cleans at the first whole day t with "
          "a t (t+1)/2 >= c (the 'discrete rule'), which lies in [tau* - 1/2, tau* + 1/2). Test: tests/test_sanity_tau.py.", "",
          "| a (USD/day^2) | tau* (days) | discrete rule | measured mean interval | cleanings | rel. error |", "|---|---|---|---|---|---|"]
    for r in st["cases"]:
        L.append(f"| {r['a']:.4f} | {r['tau_star']:.2f} | {r['tau_discrete_rule']} | {r['measured_mean']:.2f} | {r['n_cleanings']} | {100 * r['rel_err']:+.1f}% |")
    return L + [""]


def exists(f: Any) -> Any:
    """True if a stored result exists."""
    return os.path.exists(os.path.join(results_dir(), f))


def r1b_tables() -> Any:
    """Phase R1b sections; each is written only once its results file exists."""
    L = []
    if exists("price_audit.json"):
        au = R("price_audit.json")
        L += ["## R1b.1 Price-audit headline (ANALYSIS)", "",
              "**ANALYSIS.** Per market, summed over its three years: uncleaned-plant merchant revenue and PPA zero-payment hours, old "
              "(hourly-mean valuation) against new (interval-level). Detail per year in section 4.", "",
              "| market | merchant rev old (3 yr) | new | change | PPA zero-pay h old (3 yr) | unpaid h new | change |", "|---|---|---|---|---|---|---|"]
        for mk in MAIN + SENS:
            rr = [r for r in au["rows"] if r["market"] == mk]
            mo = sum(r["merchant_rev_uncleaned_old"] for r in rr); mn = sum(r["merchant_rev_uncleaned_new"] for r in rr)
            ho = sum(r["ppa_zero_hours_old"] for r in rr); hn = sum(r["ppa_unpaid_hours_new"] for r in rr)
            L.append(f"| {MN[mk]} | {mo:,.0f} | {mn:,.0f} | {100 * (mn / mo - 1):+.2f}% | {ho:,} | {hn:,.0f} | {100 * (hn / ho - 1):+.1f}% |")
        L += [""]
    if exists("claims_recheck.json"):
        cc = R("claims_recheck.json")
        L += ["## R1b.2 Recheck of the paper's sensitivity claims (ANALYSIS)", "",
              "**ANALYSIS.** Planner minus the best baseline exactly as stored and cited (best baseline selected on the test mean), per seed. "
              "t = 95% paired t-interval; Wilcoxon = two-sided signed-rank p; 'paper' = what main.tex / supplement.tex say about significance "
              "(blank: no statement). Price-dip and cost settings were rerun with per-seed storage and reproduce the stored means to "
              f"{cc['max_repro_abs_diff']:.1e} USD (tolerance 1e-6). Last column: the same comparison with the training-selected best baseline.", "",
              "| setting | best baseline | mean [95% t] USD/yr | excludes 0 | Wilcoxon p | wins / n | paper | agrees | train-selected bb: mean ± ci |",
              "|---|---|---|---|---|---|---|---|---|"]
        for r in cc["rows"]:
            ts = r.get("train_selected")
            tsx = f"{r['bb_train']}: {ts['mean']:+.0f} ± {ts['ci']:.0f}" if ts else "n/a (not stored)"
            ag = "" if r["paper_agrees"] is None else ("yes" if r["paper_agrees"] else "**NO**")
            L.append(f"| {r['key']} | {r['best_baseline']} | {r['mean']:+.0f} [{r['lo']:+.0f}, {r['hi']:+.0f}] | {'yes' if r['excludes_0'] else 'no'} | "
                     f"{r['wilcoxon_p']:.3g} | {r['wins']}/{r['n']} | {r['paper_says'] or ''} | {ag} | {tsx} |")
        L += [""]
    if exists("results_robust.json"):
        rb = R("results_robust.json")
        VN = {"a_noaccess": "(a) no access windows", "b_bias+25": "(b) station bias +25%", "b_bias-25": "(b) station bias -25%",
              "c_eff098": "(c) cleaning to SR 0.98", "d_continuous": "(d) continuous 3 years (yrs 2-3)"}
        L += ["## R1b.3 Robustness (SENSITIVITY, pre-registered)", "",
              "**SENSITIVITY.** Generated markets, 50 test seeds, every variant retuned on the train seeds. Mean [95% t-interval] USD/yr; "
              "best baseline selected by training mean. Rule (pre-registered): ROBUST if the sign of the paired mean matches the default and, "
              "where the default interval excludes 0, the variant's interval does not lie wholly on the other side of 0.", ""]
        for cmp_, nm in (("planner-bestbase", "Planner minus best baseline (primary)"), ("planner-ft", "Planner minus FT")):
            L += [f"**SENSITIVITY.** {nm}.", "", "| variant | " + " | ".join(rx_c for rx_c in ("fixed", "merchant", "ppa", "capped")) + " |", "|---|---|---|---|---|"]
            L.append("| default (RQ1 rerun) | " + " | ".join(ci(rb["_default"][c]["cmp"][cmp_]) + f" ({rb['_default'][c]['best_baseline']})" for c in ("fixed", "merchant", "ppa", "capped")) + " |")
            for v in VN:
                L.append(f"| {VN[v]} | " + " | ".join(f"{ci(rb[f'{v}|{c}']['cmp'][cmp_])} ({rb[f'{v}|{c}']['best_baseline']}) **{rb[f'{v}|{c}']['verdict'][cmp_]}**"
                                                       for c in ("fixed", "merchant", "ppa", "capped")) + " |")
            nr = sum(rb[f"{v}|{c}"]["verdict"][cmp_] == "ROBUST" for v in VN for c in ("fixed", "merchant", "ppa", "capped"))
            L += ["", f"{nm}: ROBUST in {nr} of {4 * len(VN)} variant-contract cells.", ""]
    if exists("failure_diag.json"):
        fd = R("failure_diag.json"); A, B = fd["a"], fd["b"]; ca, cb = fd["checks"]["a"], fd["checks"]["b"]
        L += ["## R1b.4 Failure diagnostics (DESCRIPTIVE)", "",
              "**DESCRIPTIVE.** One median-difference seed per case (planner minus FT net closest to the median); the rerun with per-day logging "
              "reproduces the stored per-seed nets exactly. Figures: `results/figures/r1b_diag_es_merchant_2024.pdf`, "
              "`results/figures/r1b_diag_exact_merchant_c4.pdf`; numbers in `results/failure_diag.json`. The all-seed checks test whether the "
              "median seed's pattern is typical; they do not establish cause.", "",
              f"**(a) R1 Spain merchant 2024, F2, seed {A['seed']}** (planner - FT {A['seed_diff']:+.0f} USD/yr; median {A['median_diff']:+.0f}).",
              f"1. The gap opens before day 120. The planner sweeps the whole plant on days 36-40 and 89-91, while FT first cleans on day 134. "
              f"The planner is about -280 USD behind at day 100 and -117 at day 120. It is briefly ahead between about days 160 and 235, then "
              f"loses again in days 236-266 (extra late-summer sweeps) and ends at -43.",
              f"2. The early sweeps coincide with the early-2024 price collapse. Between days 40 and 110 the realised daily value falls from about 75 to "
              f"near 0 USD/MWh, and the causal F2 forecast lags above it. FT's 14-day net benefit stays below 0 through this period. The planner's "
              f"renewal index g tau - A - c crosses 0 as tau grows, because g still carries the lagged, higher forecast.",
              f"3. The day 36-40 sweep is followed by rain of 9.4, 10.6 and 17.5 mm on days 46, 53 and 59. Rain of 5 mm or more is a free 90% "
              f"cleaning, but the rain gate looks only 2 days ahead.",
              f"4. All 50 seeds: the cumulative planner - FT is below 0 at day 120 in {ca['seeds_cum120_below0']} of 50 (mean {ca['mean_cum_day120']:+.0f}, "
              f"final {ca['mean_final']:+.0f}); the planner cleans {ca['mean_pl_rows_before_120']:.0f} rows before day 120 against FT's "
              f"{ca['mean_ft_rows_before_120']:.0f}, and {ca['mean_pl_rows_rain5_within14d']:.0f} against {ca['mean_ft_rows_rain5_within14d']:.0f} rows "
              f"within 14 days before a >= 5 mm rain.",
              f"5. So, on average, the year's loss to FT is already accrued by day 120. Over the rest of the year the planner regains "
              f"{ca['mean_final'] - ca['mean_cum_day120']:+.0f} USD.", "",
              f"**(b) Exact benchmark, merchant, 4 USD/row, seed {B['seed']}** (planner - FT {B['seed_diff']:+.1f} USD; median {B['median_diff']:+.1f}; "
              f"J* = {B['jstar']:.1f}, planner {B['planner_gain']:.1f}, FT {B['ft_gain']:.1f} USD over no cleaning).",
              f"1. The planner cleans all 6 rows twice: days 146-147, just before the odd rows' access window (days 150-154), and again on days 167 and 170. "
              f"J* cleans once (odd rows day 148, even rows day 152), and FT also once (days 149 and 151).",
              f"2. The pre-window sweep is the access-anticipation term (Phi += g L): it cleans 2-4 days earlier than J*, costing about -40 USD by day 148, "
              f"which is recovered by day 152.",
              f"3. The second sweep, 10-13 days before the window ends (day 180, no terminal value), accounts for the final loss (about -25 USD). Phi = g tau - A "
              f"has no notion of the remaining horizon, whereas FT's benefit sum is truncated at the window end.",
              f"4. All 20 seeds: the planner cleans {cb['mean_pl_rows_day160plus']:.1f} rows on days 160-179 against {cb['mean_ft_rows_day160plus']:.1f} (FT) "
              f"and {cb['mean_jstar_rows_day160plus']:.2f} (J*), and {cb['mean_pl_rows']:.1f} rows in total against {cb['mean_ft_rows']:.1f} and "
              f"{cb['mean_jstar_rows']:.1f}.",
              f"5. The planner's 64% of J* in table_exact for this setting is consistent with an end-of-window effect: a stationary renewal index "
              f"is applied to a 60-day instance with no terminal value. Its size was not separated from other causes.", ""]
    if exists("audit_counts.json"):
        ac = R("audit_counts.json"); n = ac["nlr"]; mp = ac["mae_pairs"]; lc = ac["leakage_checks"]
        L += ["## R1b.5 Provenance (ANALYSIS)", "",
              f"**ANALYSIS.** `src/provenance_r1b.py`; details in `data/provenance/NLR.md` and `results/audit_counts.json`.", "",
              "| quantity | reproduced | paper |", "|---|---|---|",
              f"| NREL sites with monthly rates | {n['sites_with_monthly_rates']} (of {n['sites_in_table']}; {n['sites_without_monthly_rates']} low-soiling sites have none) | 146 |",
              f"| median loss rate, site-months | {n['median_site_month_pct_day']:.4f} %/day | 0.10 |",
              f"| largest site mean | {n['site_mean_max']:.4f} %/day | 0.30 |",
              f"| forecast-error / value pairs | {mp['n']} (Spearman rho {mp['spearman_rho']:.3f}, p {mp['spearman_p']:.3f}) | 54, -0.11, 0.408 |",
              f"| no-lookahead checks | {lc['n']:,} = {lc['arithmetic']}; 0 failures stored | 23,562 |", "",
              "Caveats (see NLR.md): the 0.10 %/day 'median' is over site-months of the 146 measurably soiling sites, not over sites and not over all "
              "255; the NREL sensitivity runs use the median and 90th percentile of site means (0.11 and 0.19 %/day).", ""]
    return L


def build(HEADS: str, DOCS: str) -> None:
    """HEADS: directory with the hand-written head and tail. DOCS: output directory."""
    head = open(os.path.join(HEADS, "R1_SUMMARY_head.md")).read()
    tail = open(os.path.join(HEADS, "R1_SUMMARY_tail.md")).read()
    open(os.path.join(DOCS, "R1_SUMMARY.md"), "w").write(head + "\n" + "\n".join(tables() + r1b_tables()) + "\n" + tail)
