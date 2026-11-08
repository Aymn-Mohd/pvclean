"""Writes docs/R6_SUMMARY.md from the stored results and applies the Phase R6 rules as written. Every number is computed here. Run: python src/make_r6_summary.py"""
from __future__ import annotations
import json
import os
import sys
from typing import Any
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_r4_summary import CONTRACTS, FOLD_YEAR, FOLDS, MARKET, NEW, R3_MARKET, ci, load
from make_r4_summary import NAME as N4
from make_r5_summary import NAME as N5, SITES as R5
from pvclean.data import repo_root, results_dir
from pvclean.stats import HEADROOM_CUT, SHARE_TARGET, ft_plain_rule, headroom_rule, nested_bootstrap, paired

NAME = {**N4, **N5}
SITES = tuple(R3_MARKET) + NEW + R5
POLS = ("fixed", "threshold", "econ", "ft", "proposed")


def records() -> dict[str, Any]:
    """Stored full records by site|contract|fold."""
    out: dict[str, Any] = {}; m = load("results_matched.json")["r3"]
    for s, mk in R3_MARKET.items():
        for c in CONTRACTS:
            for f in FOLDS:
                out[f"{s}|{c}|{f}"] = m[f"soil0.30|{mk}|{c}|{f}"]
    for k, v in load("results_r4_sites.json")["r4"].items():
        out[k.split("|", 1)[1]] = v
    for c in CONTRACTS:
        for k, v in load(f"results_r5_{c}.json")["r5"].items():
            out[k.split("|", 1)[1]] = v
    return out


def weather_facts() -> tuple[dict[str, int], dict[str, float]]:
    """Longest dry spell and soiling loss by site|year."""
    dry: dict[str, int] = {}; loss: dict[str, float] = {}
    for s, v in load("results_r3b_rain.json")["sites"].items():
        for y, r in v["years"].items():
            dry[f"{s}|{y}"] = r["nasa"]["longest_run_without_5mm"]
    for f in ("r4_rain.json", "r5_rain.json"):
        for s, v in load(f)["sites"].items():
            for y, r in v["years"].items():
                dry[f"{s}|{y}"] = r["longest_run_without_5mm"]
    for s, mk in R3_MARKET.items():
        for y in FOLD_YEAR.values():
            loss[f"{s}|{y}"] = load("r3_checks.json")["soil"][f"{mk}|{y}"]["soiling_loss_pct"]
    loss.update(load("results_r4_sites.json")["r4_meta"]["soiling_loss_pct"]); loss.update(load("results_r5_merchant.json")["r5_meta"]["soiling_loss_pct"])
    return dry, loss


def case_years() -> list[dict[str, Any]]:
    """The 56 case-years with every figure of the tables."""
    R = records(); O = load("results_r6_oracle.json")["rows"]; P = load("results_r6_plain.json")["rows"]; T = load("results_r6_seeds.json")["rows"]; dry, loss = weather_facts(); out = []
    for s in SITES:
        for c in CONTRACTS:
            for f in FOLDS:
                k = f"{s}|{c}|{f}"; r = R[k]; t = r["test"]["F2"]; o = O[k]; p = P[k]; y = FOLD_YEAR[f]
                none = np.array(t["none"]["net"]); idx = [list(range(len(none)))[i] for i in range(len(o["seeds"]))]
                nn = none[idx]; ft = np.array(t["ft"]["net"])[idx]; pl = np.array(t["proposed"]["net"])[idx]
                ov = float(np.mean(o["value"])); ou = float(np.mean(o["upper"])); fv = float(np.mean(ft - nn)); pv = float(np.mean(pl - nn))
                D = np.array([np.subtract(t["proposed"]["net"], t["ft"]["net"])] + [T[k][n]["d"] for n in sorted(T[k])])
                out.append(dict(key=k, site=s, market=r["market"], contract=c, fold=f, year=y, dry=dry[f"{s}|{y}"], loss=loss[f"{s}|{y}"], oracle=ov, upper=ou, ft=fv, planner=pv, plain=p["value"], ft_plain=p["ft_minus_plain"],
                                ft_share=fv / ov if ov > 0 else float("nan"), pl_share=pv / ov if ov > 0 else float("nan"), ft_share_up=fv / ou if ou > 0 else float("nan"), main=paired(t["proposed"]["net"], t["ft"]["net"]), nested=nested_bootstrap(D, 2000, 0),
                                ft_full=float(np.mean(np.array(t["ft"]["net"]) - none)), rows_oracle=float(np.mean(o["n_clean"])), rows_ft=float(np.mean(t["ft"]["n_clean"])), rows_plain=float(np.mean(p["n_clean"]))))
    return out


def pct(x: float) -> str:
    return f"{100 * x:.1f}%" if np.isfinite(x) else "undefined"


def med(v: list[float]) -> str:
    v = [x for x in v if np.isfinite(x)]
    return f"median {100 * np.median(v):.1f}%, range {100 * min(v):.1f}% to {100 * max(v):.1f}%"


def side(x: dict[str, Any]) -> str:
    return "above" if x["lo"] > 0 else "below" if x["hi"] < 0 else "spans"


def main() -> None:
    C = case_years(); om = load("results_r6_oracle.json"); pm = load("results_r6_plain.json")["_meta"]; sm = load("results_r6_seeds.json")["_meta"]
    A = [r for r in C if r["oracle"] >= HEADROOM_CUT]; Lo = [r for r in C if r["oracle"] < HEADROOM_CUT]
    VA = headroom_rule([r["ft_share"] for r in A]); VAU = headroom_rule([r["ft_share_up"] for r in A]); VP = headroom_rule([r["pl_share"] for r in A])
    B = [r for r in C if r["contract"] == "merchant" and r["ft_full"] >= HEADROOM_CUT]; BP = [r for r in C if r["contract"] == "ppa" and r["ft_full"] >= HEADROOM_CUT]
    VB = ft_plain_rule([r["ft_plain"] for r in B]); VBP = ft_plain_rule([r["ft_plain"] for r in BP])
    cnt = lambda key: {k: sum(side(r[key]) == k for r in C) for k in ("above", "below", "spans")}
    M, Nn = cnt("main"), cnt("nested"); moved = sum(side(r["main"]) != side(r["nested"]) for r in C)
    gaps = [100 * (r["upper"] - r["oracle"]) / r["oracle"] for r in C if r["oracle"] > 0]; gapsA = [100 * (r["upper"] - r["oracle"]) / r["oracle"] for r in A]
    O = om["rows"]; mdiff = max(max(v["table_diff"]) for v in O.values()); viol = sum(sum(v["violations"]) for v in O.values())
    o: list[str] = []; w = o.append
    w("# E1 Phase R6: headroom, the value of price-awareness and tuning-inclusive intervals\n")
    w(f"Labels: **MAIN** decides a hypothesis; **DESCRIPTIVE** is pre-registered and decides nothing; **POST HOC** was added after the test. Pre-registration: `docs/records/decisions.md`, \"Phase R6\". Generated by `src/make_r6_summary.py`. Money is USD/yr; value = policy minus no cleaning, mean over seeds. Oracle seeds per case-year: {len(om['_meta']['seeds'])}.\n")
    w("## Summary\n")
    w(f"- **H-R6a: {VA['verdict']}.** FT reaches {pct(SHARE_TARGET)} of the oracle value in {VA['hold']} of {VA['n']} case-years at or above {HEADROOM_CUT:.0f} USD/yr ({pct(VA['share_holding'])}). FT share: {med([r['ft_share'] for r in A])}. Planner share: {med([r['pl_share'] for r in A])}.")
    w(f"- **H-R6b: {VB['verdict']}.** FT minus plain threshold is positive in {VB['mean_pos']} of {VB['n']} merchant case-years, with {VB['ci_wholly_below']} intervals wholly below 0. Median {np.median([r['ft_plain']['mean'] for r in B]):+.0f} USD/yr. PPA (DESCRIPTIVE): {VBP['mean_pos']} of {VBP['n']}, median {np.median([r['ft_plain']['mean'] for r in BP]):+.0f}.")
    w(f"- **Tuning-inclusive intervals (DESCRIPTIVE):** {Nn['above']} above 0, {Nn['below']} below 0, {Nn['spans']} span 0, against {M['above']}, {M['below']} and {M['spans']} for the main intervals.")
    w(f"- **Oracle quality:** every schedule is feasible ({viol} violations) and replayed in the simulator. Bound gap at or above the cut: median {np.median(gapsA):.2f}%, largest {max(gapsA):.2f}%.\n")
    w("## 1. H-R6a, headroom (MAIN)\n")
    w("Share = mean policy value / mean oracle value, 50 seeds, on the feasible oracle schedule. Share against the upper bound is the same ratio with the bound, so it is a floor.\n")
    w("| site | contract | year | oracle value | upper bound | FT value | FT share | FT share vs bound | reaches target | planner share |\n|---|---|---|---|---|---|---|---|---|---|")
    for r in A:
        w(f"| {NAME[r['site']]} | {r['contract']} | {r['year']} | {r['oracle']:.0f} | {r['upper']:.0f} | {r['ft']:.0f} | {pct(r['ft_share'])} | {pct(r['ft_share_up'])} | {'yes' if r['ft_share'] >= SHARE_TARGET else 'no'} | {pct(r['pl_share'])} |")
    w(f"\nRule: {VA['hold']} of {VA['n']} = {pct(VA['share_holding'])}. **Verdict: {VA['verdict']}.**\n")
    w(f"Against the upper bound (DESCRIPTIVE): {VAU['hold']} of {VAU['n']}; the rule would say {VAU['verdict']}. Planner (DESCRIPTIVE): {VP['hold']} of {VP['n']} reach the target.\n")
    w(f"Below the cut (DESCRIPTIVE), {len(Lo)} case-years. FT share: {med([r['ft_share'] for r in Lo]) if Lo else 'none'}. Planner share: {med([r['pl_share'] for r in Lo]) if Lo else 'none'}.\n")
    w("## 2. H-R6b, FT against the plain threshold (MAIN)\n")
    w("Merchant case-years with FT value at or above the cut. The comparison is paired over 50 seeds. FT differs from the plain threshold in more than prices: see note 5 of the pre-registration.\n")
    w("| site | year | FT value | plain value | FT minus plain [95% CI] | side |\n|---|---|---|---|---|---|")
    for r in B:
        w(f"| {NAME[r['site']]} | {r['year']} | {r['ft_full']:.0f} | {r['plain']:.0f} | {ci(r['ft_plain'])} | {side(r['ft_plain'])} |")
    w(f"\nRule: mean positive in {VB['mean_pos']} of {VB['n']}; at or below 0 in {VB['mean_nonpos']}; {VB['ci_wholly_below']} wholly below 0, {VB['ci_wholly_above']} wholly above. **Verdict: {VB['verdict']}.**\n")
    w("### PPA (DESCRIPTIVE)\n")
    w("| site | year | FT value | plain value | FT minus plain [95% CI] | side |\n|---|---|---|---|---|---|")
    for r in BP:
        w(f"| {NAME[r['site']]} | {r['year']} | {r['ft_full']:.0f} | {r['plain']:.0f} | {ci(r['ft_plain'])} | {side(r['ft_plain'])} |")
    w(f"\nMean positive in {VBP['mean_pos']} of {VBP['n']}, {VBP['ci_wholly_below']} wholly below 0, {VBP['ci_wholly_above']} wholly above. The rule would say {VBP['verdict']}; this is not a verdict.\n")
    w("## 3. Tuning-inclusive intervals (DESCRIPTIVE)\n")
    w("Planner minus FT, 4 tuning-seed sets, nested bootstrap, B = 2000, numpy default_rng(0) per case-year, percentile 95%. The sets share their test replicates, and 4 sets give the set level little to draw on.\n")
    w(f"| interval | above 0 | below 0 | spans 0 |\n|---|---|---|---|\n| main | {M['above']} | {M['below']} | {M['spans']} |\n| tuning-inclusive | {Nn['above']} | {Nn['below']} | {Nn['spans']} |\n")
    w(f"{moved} of {len(C)} case-years change side. Reruns match the stored R3 and R4 means to within {sm['max_abs_diff_vs_stored']:.2e} USD.\n")
    w("## 4. Every case-year (DESCRIPTIVE)\n")
    w("| site | contract | year | dry spell | soiling loss % | oracle | FT | planner | plain | FT share | planner share | FT minus plain | planner minus FT, main | planner minus FT, tuning-inclusive |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in C:
        w(f"| {NAME[r['site']]} | {r['contract']} | {r['year']} | {r['dry']} | {r['loss']:.1f} | {r['oracle']:.0f} | {r['ft']:.0f} | {r['planner']:.0f} | {r['plain']:.0f} | {pct(r['ft_share'])} | {pct(r['pl_share'])} | {ci(r['ft_plain'])} | {ci(r['main'])} | {ci(r['nested'])} |")
    w("\n## 5. Oracle checks (DESCRIPTIVE)\n")
    w(f"Units: {om['_meta']['units']}. Solved again from a tuned policy's mission nights: {om['_meta']['solved_again']}. Violations of robot constraints: {viol}. Largest difference between the path tables and the simulator's ledger: {mdiff:.2e} USD. Bound gap, all case-years with a positive oracle value: median {np.median(gaps):.2f}%, largest {max(gaps):.2f}%. Plain threshold matches the stored records: {pm['all_match_stored']}.")
    extra = os.path.join(results_dir(), "r6_sanity.json")
    if os.path.exists(extra):
        w("\n## 6. Sanity checks (POST HOC)\n")
        for x in json.load(open(extra))["lines"]:
            w(f"- {x}")
    path = os.path.join(repo_root(), "docs", "R6_SUMMARY.md")
    with open(path, "w") as f:
        f.write("\n".join(o) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    main()
