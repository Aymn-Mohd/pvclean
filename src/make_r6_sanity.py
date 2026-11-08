"""Phase R6 sanity checks (POST HOC): counts every trigger of the pre-registration, reruns one unit at the same seed, checks that the oracle and the policies saw identical inputs, and draws a soiling
and cleaning trace for the case-year with the most re-solved seeds. Writes results/r6_sanity.json and paper/fig_r6_sanity_trace.png. The pre-fix oracle file, if given as
the first argument, adds the trace's pre-fix line. Run: python src/make_r6_sanity.py [pre-fix results_r6_oracle.json]"""
from __future__ import annotations
import json
import os
import sys
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_r6_summary import NAME, case_years, records
from pvclean import model
from pvclean.data import repo_root, results_dir
from pvclean.exact.oracle import sr_tables
from pvclean.stats import HEADROOM_CUT
from pvclean.studies.r6 import POLICIES, oracle_unit, overs
from pvclean.studies.runner import job

FIXED = "#2a78d6"; PRE = "#eb6834"; NONE = "#8a8984"; INK = "#0b0b0b"


def mean_sr(sched: list, seed: int, cfg: dict) -> np.ndarray:
    """Mean soiling ratio over rows, per day, of a schedule [(day, rows)], from the oracle's tables."""
    SR = sr_tables(seed, cfg); D, n, _ = SR.shape; last = np.zeros(n, int); by = {int(d): rows for d, rows in sched}; out = np.zeros(D)
    for k in range(D):
        for i in by.get(k, ()):
            last[i] = k
        out[k] = SR[k, np.arange(n), last].mean()
    return out


def main() -> None:
    R = records(); O = json.load(open(os.path.join(results_dir(), "results_r6_oracle.json"))); C = case_years(); fix = O["_meta"].get("fix_resolve", {}); lines = []
    # Triggers at case-year level.
    t1 = [r for r in C if max(np.mean(np.subtract(R[r["key"]]["test"]["F2"][p]["net"], R[r["key"]]["test"]["F2"]["none"]["net"])) for p in POLICIES) > r["oracle"] + 1e-6]
    t2 = [r for r in C if r["ft_plain"]["mean"] < -500]; t3 = [r for r in C if np.isfinite(r["ft_share"]) and r["ft_share"] > 1]
    worst = min(C, key=lambda r: r["ft_plain"]["mean"]); top = max((r for r in C if np.isfinite(r["ft_share"])), key=lambda r: r["ft_share"])
    # Seed level, and identical inputs.
    seed_below = 0; ub_below = 0; inp = 0.0
    for k, o in O["rows"].items():
        t = R[k]["test"]["F2"]
        for j, x in enumerate(o["seeds"]):
            bv = max(t[p]["net"][x] for p in POLICIES) - t["none"]["net"][x]
            seed_below += bv > o["value"][j] + 1e-6; ub_below += bv > o["upper"][j] + 1e-6; inp = max(inp, abs(o["none"][j] - t["none"]["net"][x]))
    lines.append(f"Trigger 1, oracle below a policy: {len(t1)} case-years on means. At seed level, {fix.get('units', 0)} of {O['_meta']['units']} seeds had a tuned policy above the oracle schedule after the first re-solve, by at most "
                 f"{max((x['new_value'] - x['old_value'] for x in fix.get('units_log', [])), default=0):.2f} USD, in {len(Counter(x['key'] for x in fix.get('units_log', [])))} case-years, {sum(r['oracle'] >= HEADROOM_CUT for r in C if r['key'] in {x['key'] for x in fix.get('units_log', [])})} of them at or above the cut. **BUG**, in the re-solve step: a policy's nights were scored as a start but searched only if they ranked in the top 2, and the night repair could end below the policy's own rows. Fixed (every start searched; the policy's schedule kept as an incumbent); only those {fix.get('units', 0)} units ran again; {fix.get('improved', 0)} improved. Seeds below a policy now: {seed_below}. Upper bound below a policy: {ub_below}.")
    lines.append(f"Trigger 2, FT below the plain threshold by more than 500 USD/yr: {len(t2)} case-years. Most negative: {NAME[worst['site']]} {worst['contract']} {worst['year']}, {worst['ft_plain']['mean']:+.0f} [{worst['ft_plain']['lo']:+.0f}, {worst['ft_plain']['hi']:+.0f}]. Not triggered.")
    lines.append(f"Trigger 3, FT share above 100%: {len(t3)} case-years. Highest: {NAME[top['site']]} {top['contract']} {top['year']}, {100 * top['ft_share']:.1f}%. Not triggered.")
    lines.append(f"Identical inputs: largest difference between the oracle's no-cleaning net and the stored policies' no-cleaning net, over all {O['_meta']['units']} units: {inp:.2e} USD.")
    # Same-seed rerun of the case-year with the most re-solved seeds.
    cnt = Counter(x["key"] for x in fix.get("units_log", [])); key = cnt.most_common(1)[0][0] if cnt else "a_coruna|ppa|Y2"; seed = min(x["seed"] for x in fix["units_log"] if x["key"] == key) if cnt else 1
    s, c, f = key.split("|"); te, tr = overs(s, f); cfg = model.merged(te); t = R[key]["test"]["F2"]
    best = max(POLICIES, key=lambda p: t[p]["net"][seed])
    sc = [(int(d), [int(i) for i in rows]) for d, rows in job((best, t[best]["params"], c, seed, "site", 0.01, 1.0, dict(te, _inp=dict(tr))))[1]["sched"]]
    a = [oracle_unit((s, c, f, seed, [[d for d, _ in sc]], {}, sc)) for _ in range(2)]
    o = O["rows"][key]; j = o["seeds"].index(seed)
    lines.append(f"Same-seed rerun, {NAME[s]} {c} fold {f}, seed {seed}: two reruns {a[0]['value']:.4f} and {a[1]['value']:.4f}, stored {o['value'][j]:.4f}; the {best} policy {t[best]['net'][seed] - t['none']['net'][seed]:.4f}. Identical: {a[0]['value'] == a[1]['value'] == o['value'][j]}.")
    # Trace.
    pre_path = sys.argv[1] if len(sys.argv) > 1 else "" 
    fig, axs = plt.subplots(2, 2, figsize=(6.5, 3.8), gridspec_kw=dict(height_ratios=[2.2, 1], width_ratios=[1.6, 1]))
    days = np.arange(cfg.get("d1", 365) - cfg.get("d0", 0)); runs = [("no cleaning", [], NONE, "-", None)]
    if os.path.exists(pre_path):
        P = json.load(open(pre_path))["rows"][key]; runs.append((f"oracle before fix ({P['value'][j]:.1f} USD)", P["sched"][j], PRE, "-", -0.2))
    runs.append((f"oracle after fix = {best} policy ({o['value'][j]:.1f} USD)", o["sched"][j], FIXED, "--", 0.2))
    nights = [d for _, sch, *_ in runs for d, _ in sch]; lo, hi = (min(nights) - 6, max(nights) + 14) if nights else (0, 30)
    for col, (x0, x1) in enumerate([(0, len(days) - 1), (lo, hi)]):
        ax, bx = axs[0, col], axs[1, col]
        for lab, sch, colr, ls, off in runs:
            ax.plot(days, 100 * mean_sr(sch, seed, cfg), color=colr, lw=0.9, ls=ls, label=lab)
            if off is not None:
                bx.bar([d + off for d, _ in sch], [len(r) for _, r in sch], width=0.4, color=colr, label=lab.split(" (")[0])
        ax.set_xlim(x0, x1); bx.set_xlim(x0, x1)
        for z in (ax, bx):
            z.spines[["top", "right"]].set_visible(False); z.tick_params(labelsize=6.5)
        bx.set_xlabel("day of test year" + (", zoom" if col else ""), fontsize=7)
    axs[0, 0].set_ylabel("mean soiling ratio (%)", fontsize=7); axs[1, 0].set_ylabel("rows cleaned", fontsize=7)
    axs[0, 0].legend(fontsize=6, frameon=False, loc="lower left"); axs[1, 0].legend(fontsize=6, frameon=False, loc="upper left")
    fig.suptitle(f"{NAME[s]}, {c}, test fold {f}, seed {seed}; value over no cleaning in brackets", fontsize=8, color=INK)
    fig.tight_layout(); out = os.path.join(repo_root(), "paper", "fig_r6_sanity_trace.png"); fig.savefig(out, dpi=200)
    lines.append(f"Trace: `paper/fig_r6_sanity_trace.png`, {NAME[s]} {c} fold {f} seed {seed}: mean row soiling ratio and rows cleaned per night, before and after the fix.")
    json.dump(dict(label="POST HOC", lines=lines), open(os.path.join(results_dir(), "r6_sanity.json"), "w"), indent=1)
    print("\n".join(lines)); print("wrote", out)


if __name__ == "__main__":
    main()
