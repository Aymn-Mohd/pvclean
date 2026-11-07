"""Writes docs/R4_SUMMARY.md from the stored results and applies the Phase R4 rule as written. Every number is computed here. Run: python src/make_r4_summary.py"""
from __future__ import annotations
import json
import os
from typing import Any
import numpy as np
from pvclean.data import repo_root, results_dir
from pvclean.stats import DRY_HIGH, DRY_LOW, cluster_spearman, dry_prediction, dry_rule

R3_MARKET = {"adelaide": "SA1_raw", "brisbane": "QLD1_raw", "seville": "ES_raw"}
NEW = ("almeria", "cordoba", "bilbao", "port_augusta", "longreach")
SPAIN = ("bilbao", "cordoba", "almeria", "seville")
NAME = {"adelaide": "Adelaide", "brisbane": "Brisbane", "seville": "Seville", "almeria": "Almería", "cordoba": "Córdoba", "bilbao": "Bilbao", "port_augusta": "Port Augusta", "longreach": "Longreach"}
MARKET = {"SA1_raw": "SA", "QLD1_raw": "QLD", "ES_raw": "ES"}
FOLD_YEAR = {"Y2": 2024, "Y3": 2025}
CONTRACTS = ("merchant", "ppa"); FOLDS = ("Y2", "Y3")


def load(name: str) -> Any:
    """One stored result file."""
    return json.load(open(os.path.join(results_dir(), name)))


def compact(rec: dict[str, Any]) -> dict[str, Any]:
    """The per-case figures of a full record."""
    t = rec["test"]["F2"]; none = np.array(t["none"]["net"]); d = rec["decomp"]["planner-ft"]
    return dict(planner_ft=rec["cmp"]["planner-ft|F2"], voc_planner=float(np.mean(np.array(t["proposed"]["net"]) - none)), voc_ft=float(np.mean(np.array(t["ft"]["net"]) - none)),
                rows_planner=float(np.mean(t["proposed"]["n_clean"])), rows_ft=float(np.mean(t["ft"]["n_clean"])), quantity=d["quantity"]["mean"], timing=d["timing"]["mean"],
                ties=int(np.sum(np.abs(np.subtract(t["proposed"]["net"], t["ft"]["net"])) < 1e-6)), kappa=rec["tuned"]["F2"]["proposed"]["params"]["kappa"])


def case_years() -> list[dict[str, Any]]:
    """All 32 case-years: the 12 of R3 and the 20 new ones, with dry spell and soiling loss."""
    rain3 = load("results_r3b_rain.json")["sites"]; rain4 = load("r4_rain.json")["sites"]
    m = load("results_matched.json")["r3"]; soil3 = load("r3_checks.json")["soil"]; s4 = load("results_r4_sites.json"); r4 = s4["r4"]; loss4 = s4["r4_meta"]["soiling_loss_pct"]
    out = []
    for site, mk in R3_MARKET.items():
        for c in CONTRACTS:
            for f in FOLDS:
                y = FOLD_YEAR[f]
                out.append(dict(compact(m[f"soil0.30|{mk}|{c}|{f}"]), site=site, market=mk, contract=c, fold=f, year=y, new=False, dry=rain3[site]["years"][str(y)]["nasa"]["longest_run_without_5mm"],
                                loss=soil3[f"{mk}|{y}"]["soiling_loss_pct"]))
    for site in NEW:
        for c in CONTRACTS:
            for f in FOLDS:
                k = f"soil0.30|{site}|{c}|{f}"
                if k in r4:
                    y = FOLD_YEAR[f]
                    out.append(dict(compact(r4[k]), site=site, market=r4[k]["market"], contract=c, fold=f, year=y, new=True, dry=rain4[site]["years"][str(y)]["longest_run_without_5mm"],
                                    loss=loss4[f"{site}|{y}"]))
    return out


def dubai() -> dict[str, Any]:
    """Generated Dubai weather: its mean longest dry spell, and planner minus FT over the 12 R1 case-years on the same price series as R3 and R4. The interval is a paired t-interval over seeds of the mean of the 12."""
    from pvclean.stats import paired
    c = load("results_chrono.json"); w = load("r3_checks.json")["r1wx"]
    keys = [f"{mk}|{k}|{f}" for mk in R3_MARKET.values() for k in CONTRACTS for f in FOLDS]
    a = np.mean([c[k]["test"]["F2"]["proposed"]["net"] for k in keys], axis=0); b = np.mean([c[k]["test"]["F2"]["ft"]["net"] for k in keys], axis=0)
    al = [f"{mk}|{k}|{f}" for mk in ("SA1_aligned", "QLD1_aligned", "ES_raw") for k in CONTRACTS for f in FOLDS]
    return dict(dry=w["longest_gap_5mm_days"], loss=w["soiling_loss_pct"], n_cases=len(keys), aligned_mean=float(np.mean([c[k]["cmp"]["planner-ft|F2"]["mean"] for k in al])), **paired(a, b))


def ci(x: dict[str, Any]) -> str:
    return f"{x['mean']:+.0f} [{x['lo']:+.0f}, {x['hi']:+.0f}]"


def sgn(v: float) -> str:
    return "+" if v > 0 else "0" if v == 0 else "-"


def hit(pred: str | None, mean: float) -> str:
    return "n/a" if pred is None else "yes" if ((mean > 0) if pred == "+" else (mean <= 0)) else "no"


def tally_line(means: list[float]) -> str:
    return f"{sum(v > 0 for v in means)} positive, {sum(v <= 0 for v in means)} at or below 0, of {len(means)}"


def check_counts(rows: dict[str, Any], dry: dict[str, int], main: dict[str, float]) -> dict[str, Any]:
    """Sign counts of one check: against 0, against the prediction, and against the main result."""
    k = list(rows); m = [rows[x]["planner_ft"]["mean"] for x in k]
    r = dry_rule([(dry[x], rows[x]["planner_ft"]["mean"]) for x in k])
    rn = dry_rule([(dry[x], rows[x]["planner_ft"]["mean"]) for x in k if x.split("|")[0] in NEW])
    return dict(pos=sum(v > 0 for v in m), nonpos=sum(v <= 0 for v in m), n=len(m), above=sum(rows[x]["planner_ft"]["lo"] > 0 for x in k), below=sum(rows[x]["planner_ft"]["hi"] < 0 for x in k),
                correct=r["n_correct"], predicted=r["n_predicted"], new_correct=rn["n_correct"], new_predicted=rn["n_predicted"], label=rn["verdict"], same_sign=sum((rows[x]["planner_ft"]["mean"] > 0) == (main[x] > 0) for x in k))


def main() -> None:
    C = case_years(); new = [r for r in C if r["new"]]; D = dubai()
    key = lambda r: f"{r['site']}|{r['contract']}|{r['fold']}"
    dry = {key(r): r["dry"] for r in C}; mean = {key(r): r["planner_ft"]["mean"] for r in C}
    V = dry_rule([(r["dry"], r["planner_ft"]["mean"]) for r in new])
    x = [r["dry"] for r in C]; l = [r["loss"] for r in C]; y = [r["planner_ft"]["mean"] for r in C]; g = [r["site"] for r in C]
    S1 = cluster_spearman(x, y, g, 2000, 0); S2 = cluster_spearman(l, y, g, 2000, 0)
    o: list[str] = []; w = o.append
    w("# E1 Phase R4: new matched sites and the dry-spell prediction\n")
    w(f"Labels: **MAIN** is the pre-registered prediction test; **DESCRIPTIVE** is pre-registered but decides nothing; **POST HOC** and **SENSITIVITY** were listed in the pre-registration and run after the test, and decide nothing. Pre-registration: `docs/records/decisions.md`, \"Phase R4\". Generated by `src/make_r4_summary.py`. Money is USD/yr, mean over 50 seeds with the 95% t-interval. Rule thresholds: {DRY_HIGH} and {DRY_LOW} days.\n")
    w("## Summary\n")
    w(f"- **R4 verdict: {V['verdict']}.** {V['n_correct']} of {V['n_predicted']} predicted case-years have the predicted sign ({100 * V['share_correct']:.0f}%). Predicted above 0: {V['n_predicted_pos']}. Predicted at or below 0: {V['n_predicted_nonpos']}. No prediction: {V['n_no_prediction']}.")
    w(f"- **Spearman rho over {S1['n']} case-years (DESCRIPTIVE):** dry spell {S1['rho']:+.2f} [{S1['lo']:+.2f}, {S1['hi']:+.2f}]; soiling loss without cleaning {S2['rho']:+.2f} [{S2['lo']:+.2f}, {S2['hi']:+.2f}]. Cluster bootstrap by site, {S1['clusters']} sites.")
    w(f"- **All {sum(1 for r in new if dry_prediction(r['dry']) and hit(dry_prediction(r['dry']), r['planner_ft']['mean']) == 'no')} misses are PPA case-years predicted above 0** (POST HOC reading; section 1).\n")
    w("## 1. Prediction test (MAIN)\n")
    w("Planner minus FT, forecast F2, soiling 0.30%/day. Wins = seeds of 50 where the planner is strictly better; ties = seeds with equal net.\n")
    w("| site | market | contract | year | longest dry spell (days) | predicted | mean [95% CI] | actual sign | match | wins | ties |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for r in new:
        p = dry_prediction(r["dry"]); q = r["planner_ft"]
        w(f"| {NAME[r['site']]} | {MARKET[r['market']]} | {r['contract']} | {r['year']} | {r['dry']} | {p or 'none'} | {ci(q)} | {sgn(q['mean'])} | {hit(p, q['mean'])} | {q['wins']}/{q['n']} | {r['ties']} |")
    w(f"\nRule: {V['n_correct']} of {V['n_predicted']} = {100 * V['share_correct']:.1f}% with the predicted sign; sides {V['n_predicted_pos']} and {V['n_predicted_nonpos']}. **Verdict: {V['verdict']}.**\n")
    pr = [r for r in new if dry_prediction(r["dry"])]
    good = lambda r: hit(dry_prediction(r["dry"]), r["planner_ft"]["mean"]) == "yes"
    spans = lambda r: r["planner_ft"]["lo"] <= 0 <= r["planner_ft"]["hi"]
    g_s = sum(good(r) and spans(r) for r in pr); b_s = sum(not good(r) and spans(r) for r in pr); n = len(pr)
    w(f"How firm the label is: {g_s} correct and {b_s} wrong case-years have an interval that spans 0. Moving all of them against the prediction gives {V['n_correct'] - g_s} of {n} ({100 * (V['n_correct'] - g_s) / n:.0f}%); moving all of them for it gives {V['n_correct'] + b_s} of {n} ({100 * (V['n_correct'] + b_s) / n:.0f}%). The at-or-below-0 side is one site, Bilbao. {sum(r['dry'] == DRY_HIGH - 1 for r in new)} case-years sit one day under the {DRY_HIGH}-day threshold and get no prediction.\n")
    w("R3 itself does not fit the rule perfectly. The same rule on the 12 R3 case-years, from which the thresholds were drawn: " + (lambda v: f"{v['n_correct']} of {v['n_predicted']}.\n")(dry_rule([(r["dry"], r["planner_ft"]["mean"]) for r in C if not r["new"]])))
    w("### By contract (POST HOC)\n")
    w("Not pre-registered. Added after seeing the table above.\n")
    w("| contract | predicted above 0: correct | predicted at or below 0: correct | all predicted | Spearman rho, dry spell, all 32 case-years split by contract |\n|---|---|---|---|---|")
    for c in CONTRACTS:
        a = [r for r in pr if r["contract"] == c]; up = [r for r in a if dry_prediction(r["dry"]) == "+"]; dn = [r for r in a if dry_prediction(r["dry"]) != "+"]; al = [r for r in C if r["contract"] == c]
        q = cluster_spearman([r["dry"] for r in al], [r["planner_ft"]["mean"] for r in al], [r["site"] for r in al], 2000, 0)
        w(f"| {c} | {sum(map(good, up))} / {len(up)} | {sum(map(good, dn))} / {len(dn)} | {sum(map(good, a))} / {len(a)} | {q['rho']:+.2f} [{q['lo']:+.2f}, {q['hi']:+.2f}], n = {q['n']} |")
    w("")
    w("## 2. Per case-year detail (DESCRIPTIVE)\n")
    w("Soiling loss: energy without cleaning against a dust-free run. Value of cleaning: policy minus no cleaning. Quantity and timing: the R1 split of planner minus FT revenue.\n")
    w("| site | contract | year | dry spell | soiling loss % | value of cleaning, planner | value of cleaning, FT | rows, planner | rows, FT | quantity | timing | kappa |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in C:
        w(f"| {NAME[r['site']]}{'' if r['new'] else ' (R3)'} | {r['contract']} | {r['year']} | {r['dry']} | {r['loss']:.1f} | {r['voc_planner']:+.0f} | {r['voc_ft']:+.0f} | {r['rows_planner']:.0f} | {r['rows_ft']:.0f} | {r['quantity']:+.0f} | {r['timing']:+.0f} | {r['kappa']:g} |")
    w("\n## 3. Rank correlation over all case-years (DESCRIPTIVE)\n")
    w("| predictor | Spearman rho | 95% CI | case-years | sites | B | dropped resamples |\n|---|---|---|---|---|---|---|")
    for n, s in (("longest dry spell", S1), ("soiling loss without cleaning", S2)):
        w(f"| {n} | {s['rho']:+.3f} | [{s['lo']:+.3f}, {s['hi']:+.3f}] | {s['n']} | {s['clusters']} | {s['B']} | {s['dropped']} |")
    w("\nThe 32 case-years hold only 16 site-years, because merchant and PPA share weather. The interval resamples whole sites.\n")
    w("## 4. Within Spain (DESCRIPTIVE)\n")
    w("Same prices, different weather.\n")
    w("| site | year | dry spell | soiling loss % | merchant | PPA |\n|---|---|---|---|---|---|")
    for s in SPAIN:
        for yv in FOLD_YEAR.values():
            a = {r["contract"]: r for r in C if r["site"] == s and r["year"] == yv}
            if a:
                w(f"| {NAME[s]} | {yv} | {a['merchant']['dry']} | {a['merchant']['loss']:.1f} | {ci(a['merchant']['planner_ft'])} | {ci(a['ppa']['planner_ft'])} |")
    sp = [r for r in C if r["market"] == "ES_raw"]
    w(f"\nSpanish case-years: {tally_line([r['planner_ft']['mean'] for r in sp])}. Spearman rho of dry spell and planner minus FT inside Spain, without an interval because there are {len({r['site'] for r in sp})} sites: {cluster_spearman([r['dry'] for r in sp], [r['planner_ft']['mean'] for r in sp], [r['site'] for r in sp], 2000, 0)['rho']:+.2f}.\n")
    w("## 5. Checks after the test (POST HOC)\n")
    K = load("results_r4_kappa.json"); H = load("results_r4_shift.json"); L = load("results_r4_lowsoil.json")
    w("None of these changes the verdict. Correct = case-years with the sign the dry-spell rule predicts, over predicted case-years. The all count includes the R3 sites, from which the thresholds were drawn; the new-sites count is the fair one. The rule column shows what the rule would say on that check; it is not a verdict. Same sign = same side of 0 as the main result.\n")
    w("| check | case-years | mean > 0 | mean <= 0 | CI > 0 | CI < 0 | correct / predicted, all | correct / predicted, new sites | rule on new sites, not a verdict | same sign as main |\n|---|---|---|---|---|---|---|---|---|---|")
    for n, rows in (("wider kappa grid", K["rows"]), ("dust season moved half a year", H["rows"]), ("soiling 0.11%/day", L["rows"])):
        c = check_counts(rows, dry, mean)
        w(f"| {n} | {c['n']} | {c['pos']} | {c['nonpos']} | {c['above']} | {c['below']} | {c['correct']} / {c['predicted']} | {c['new_correct']} / {c['new_predicted']} | {c['label']} | {c['same_sign']} / {c['n']} |")
    w(f"\nKappa: the planner's parameters moved in {K['_meta']['planner_params_moved']} of {len(K['rows'])} case-years, and kappa is at the grid top in {K['_meta']['kappa_at_grid_top']}. Bilbao on the wider grid: {', '.join(ci(K['rows'][f'bilbao|{c}|{f}']['planner_ft']) for c in CONTRACTS for f in FOLDS)} (merchant 2024, merchant 2025, PPA 2024, PPA 2025).\n")
    w("| site | contract | year | main | wider kappa | season moved | 0.11%/day |\n|---|---|---|---|---|---|---|")
    for r in C:
        k = key(r); f = lambda d: ci(d[k]["planner_ft"]) if k in d else "not run"
        w(f"| {NAME[r['site']]} | {r['contract']} | {r['year']} | {ci(r['planner_ft'])} | {f(K['rows'])} | {f(H['rows'])} | {f(L['rows'])} |")
    w("\n## 6. Sensitivity to cost and tuning seeds (SENSITIVITY)\n")
    Q = load("results_r4_cost.json"); T = load("results_r4_seeds.json")
    w("| check | case-years | mean > 0 | mean <= 0 | CI > 0 | CI < 0 | correct / predicted, all | correct / predicted, new sites | rule on new sites, not a verdict | same sign as main |\n|---|---|---|---|---|---|---|---|---|---|")
    for n, rows in [(f"costs {a}", v["rows"]) for a, v in Q["arms"].items()] + [(f"tuning seeds {a}", v["rows"]) for a, v in T["sets"].items()]:
        c = check_counts(rows, dry, mean)
        w(f"| {n} | {c['n']} | {c['pos']} | {c['nonpos']} | {c['above']} | {c['below']} | {c['correct']} / {c['predicted']} | {c['new_correct']} / {c['new_predicted']} | {c['label']} | {c['same_sign']} / {c['n']} |")
    w("\n## 7. Generated Dubai weather (DESCRIPTIVE)\n")
    w(f"Mean longest dry spell {D['dry']:.0f} days, soiling loss {D['loss']:.1f}%. Mean planner minus FT over its {D['n_cases']} R1 case-years on the same price series as R3 and R4: {ci(D)}. On R1's aligned Australian series the mean is {D['aligned_mean']:+.0f}.")
    extra = os.path.join(results_dir(), "r4_sanity.json")
    if os.path.exists(extra):
        s = json.load(open(extra))
        w("\n## 8. Sanity checks (POST HOC)\n")
        for line in s["lines"]:
            w(f"- {line}")
    path = os.path.join(repo_root(), "docs", "R4_SUMMARY.md")
    with open(path, "w") as f:
        f.write("\n".join(o) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    main()
