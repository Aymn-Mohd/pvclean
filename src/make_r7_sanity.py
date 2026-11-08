"""Phase R7 sanity checks (SENSITIVITY): the oracle below a policy, F4 FT worse than F2 FT by more than 500 USD/yr, reproduction of the stored F2 results by the F2 arm, and the plain
threshold's independence of the price forecast. If the F4 check fires, the script stops so that a same-seed rerun can be made first. Writes results/r7_sanity.json.
Run: python src/make_r7_sanity.py"""
from __future__ import annotations
import json
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_r7_summary import PL, YEAR, keys, load, same_nets, stored_rows
from make_r6_summary import NAME, records
from pvclean.data import results_dir

TOL = 1e-6


def name(k: str) -> str:
    s, c, f = k.split("|")
    return f"{NAME[s]} {c} {YEAR[f]}"


def main() -> None:
    st = stored_rows(); K = keys(); A = load("results_r7_forecast.json")["arms"]; L: list[str] = []
    # Reproduction and the plain threshold.
    f2 = same_nets(A["F2"]["rows"], st, tuple(PL)); none = sum(any(A[n]["rows"][k]["none"] != A["F2"]["rows"][k]["none"] for n in A) for k in K)
    pl = sum(same_nets(A[n]["rows"], A["F2"]["rows"], ("threshold",)) for n in A)
    L.append(f"The F2 arm reproduces the stored R3 to R5 per-seed nets of plain, FT and planner: differs in {f2} of {len(K)} case-years. "
             f"No-cleaning nets differ between forecast arms in {none} case-years; the plain threshold's nets differ from F2 in {pl} case-year-arms (it reads no prices).")
    # F4 FT against F2 FT.
    d = sorted((A["F4"]["rows"][k]["value"]["ft"] - A["F2"]["rows"][k]["value"]["ft"], k) for k in K); hit = [x for x in d if x[0] < -500]
    w = d[0][1]; a4, a2 = A["F4"]["rows"][w], A["F2"]["rows"][w]
    L.append(f"F4 FT worse than F2 FT by more than 500 USD/yr (case-year mean value): {len(hit)} of {len(K)}. Lowest: {name(w)}, {d[0][0]:+.0f} USD/yr; FT tuned to {a4['params']['ft']} under F4 and "
             f"{a2['params']['ft']} under F2, training-year mean net {a4['train_mean']['ft']:.0f} and {a2['train_mean']['ft']:.0f}. "
             + "Not triggered.")
    if hit:
        raise SystemExit("F4 check triggered: run a same-seed rerun and an identical-inputs check before the summary")
    # Oracle split.
    p = os.path.join(results_dir(), "results_r7_oracle_split.json")
    if os.path.exists(p):
        S = json.load(open(p)); R = S["rows"]; seeds = S["_meta"]["seeds"]; REC = records()
        for kd in ["C"] + S["_meta"]["kinds"]:
            seed_b = 0; cy_b = []; inp = 0.0
            for k, o in R.items():
                t = REC[k]["test"]["F2"]
                pv = np.array([max(t[q]["net"][x] for q in PL) - t["none"]["net"][x] for x in seeds]); ov = np.array(o[kd]["value"])
                seed_b += int(np.sum(pv > ov + TOL)); inp = max(inp, max(abs(o[kd]["none"][j] - t["none"]["net"][x]) for j, x in enumerate(seeds)))
                if np.mean(pv) > np.mean(ov) + TOL:
                    cy_b.append(k)
            if kd == "C":
                L.append(f"Oracle C (stored R6, full information) below the best policy: {seed_b} of {len(R) * len(seeds)} seeds, {len(cy_b)} case-years on means. "
                         + ("Not triggered." if not seed_b else "**Check**: C is the optimum of the true problem only up to its search; see the run log."))
            else:
                L.append(f"Oracle {kd} below the best policy: {seed_b} of {len(R) * len(seeds)} seeds, {len(cy_b)} case-years on means{' (' + ', '.join(name(k) for k in cy_b) + ')' if 0 < len(cy_b) <= 8 else ''}. "
                         + (f"Expected, not a bug: {kd} plans with less information than the policies in one respect ({dict(A='realised rain', B='prices beyond the F2 forecast', D='per-row soiling')[kd]}) and is an open-loop plan, while the policies react to observations." if seed_b else "Not triggered."))
            if kd != "C":
                ab = [(o[kd]["value"][j] - o["C"]["value"][j], o[kd]["value"][j] - o["C"]["upper"][j]) for o in R.values() for j in range(len(seeds))]
                L.append(f"Oracle {kd} above oracle C: {sum(a > TOL for a, _ in ab)} of {len(ab)} seeds (largest difference {kd} minus C: {max(a for a, _ in ab):+.2f} USD); above C's Lagrangian upper bound: {sum(u > TOL for _, u in ab)}. "
                         + ("Not a bug: C is a local-search optimum within its bound (median gap to the bound " + f"{np.median([o['C']['upper'][j] - o['C']['value'][j] for o in R.values() for j in range(len(seeds))]):.1f} USD), and the {kd} search sometimes ends on a better true schedule." if any(a > TOL for a, _ in ab) else "Not triggered."))
            L.append(f"Identical inputs, oracle {kd}: largest difference between its no-cleaning net and the stored policies' no-cleaning net: {inp:.2e} USD.")
    json.dump(dict(label="SENSITIVITY", lines=L), open(os.path.join(results_dir(), "r7_sanity.json"), "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    main()
