"""Phase R1b stage 5 (DESCRIPTIVE): failure diagnostics for one median-difference seed.
  (a) R1 Spain merchant 2024 (ES_raw|merchant|Y2), F2: planner vs FT (the one interval wholly below 0 in H-R1).
  (b) exact benchmark, merchant, c_row = 4 USD (6 rows, days 120-180): planner vs FT, with the clairvoyant J* schedule.
The seed is the one whose planner-minus-FT net is closest to the median over the test seeds (ties: lowest seed). The run is repeated
with cfg diag=True (decisions unaffected) and must reproduce the stored per-seed nets exactly. Per day: forecast value (mean of the
forecast over the policy's horizon) and realised daily mean value, the planner's estimated loss A (sum over rows), the planner index
max_i Phi_i and FT's trigger max_i NB_i over open rows, cleanings, rain and access windows, and the cumulative paired net value.
Writes results/figures/r1b_diag_es_merchant_2024.pdf, results/figures/r1b_diag_exact_merchant_c4.pdf and results/failure_diag.json."""
from __future__ import annotations
from typing import Any
from pvclean import model
from pvclean.exact import row_tables, schedule_value, solve
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .study import Study

# reference categorical palette, fixed order (dataviz skill references/palette.md): planner, FT, clairvoyant
C_PL, C_FT, C_JS = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID, ACCESS = "#0b0b0b", "#52514e", "#e4e3df", "#ecebe7"


def median_seed(seeds: Any, d: Any) -> Any:
    """The seed closest to the median difference; ties go to the lowest seed."""
    d = np.asarray(d, float); med = np.median(d)
    i = min(range(len(d)), key=lambda k: (abs(d[k] - med), seeds[k]))
    return seeds[i], float(d[i]), float(med)


def run_policy(pol: Any, par: Any, contract: Any, seed: Any, cfg: Any, inp: Any) -> Any:
    """One year with daily diagnostics."""
    c, v, p = inp
    return model.simulate(pol, par, contract, seed, cfg=dict(cfg, diag=True), clim=c, vexp=v, pbar=p)


def series(r: Any, key: Any, red: Any) -> Any:
    """A daily series reduced over open rows."""
    return np.array([red(x[key][x["avail"]]) if key in x and x["avail"].any() else np.nan for x in r["diag"]])


def summarise(name: Any, pl: Any, ft: Any, days: Any, extra: Any = None) -> Any:
    """Summary of one case and its cumulative paired net."""
    dpl = np.array([x["net_day"] for x in pl["diag"]]); dft = np.array([x["net_day"] for x in ft["diag"]])
    cum = np.cumsum(dpl - dft)
    w = 30 if len(days) > 90 else 10
    roll = cum[w:] - cum[:-w]
    lo = int(np.argmin(roll)); hi = int(np.argmax(roll))
    clean = lambda r: [(x["day"], len(x["rows"])) for x in r["diag"] if x["rows"]]
    black = np.array([(~x["avail"]).any() for x in pl["diag"]])
    out = dict(case=name, final_paired=float(cum[-1]), planner_net=pl["net"], ft_net=ft["net"],
               planner_cleanings=pl["n_clean"], planner_missions=pl["n_missions"], ft_cleanings=ft["n_clean"], ft_missions=ft["n_missions"],
               worst_window=dict(days=[int(days[lo]), int(days[lo + w])], change=float(roll[lo])),
               best_window=dict(days=[int(days[hi]), int(days[hi + w])], change=float(roll[hi])),
               rain_days_ge1=int(sum(x["rain"] >= 1 for x in pl["diag"])), rain_days_ge5=int(sum(x["rain"] >= 5 for x in pl["diag"])),
               access_days=int(black.sum()),
               planner_missions_by_day=clean(pl), ft_missions_by_day=clean(ft),
               planner_rain_gated_days=int(sum(x.get("rain_soon", False) for x in pl["diag"])))
    out.update(extra or {})
    return out, cum


def plot(path: Any, title: Any, pl: Any, ft: Any, cum: Any, js_sched: Any = None, js_cum: Any = None) -> Any:
    """Writes the five-panel diagnostic figure."""
    days = np.array([x["day"] for x in pl["diag"]])
    plt.rcParams.update({"font.size": 7, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(5, 1, figsize=(7.0, 8.2), sharex=True, gridspec_kw=dict(hspace=0.35))
    black = np.array([(~x["avail"]).any() for x in pl["diag"]])
    for a in ax:
        a.grid(axis="y", color=GRID, lw=0.6); a.set_axisbelow(True)
        for d in days[black]:
            a.axvspan(d - 0.5, d + 0.5, color=ACCESS, lw=0)
    # 1 forecast value
    a = ax[0]
    a.plot(days, [x["v_day"] * 1000 for x in pl["diag"]], color=MUTED, lw=0.8, label="realised daily mean value")
    a.plot(days, [x.get("vhat", np.nan) * 1000 for x in pl["diag"]], color=C_PL, lw=2, label="planner forecast (7-day horizon mean)")
    a.plot(days, [x.get("vhat", np.nan) * 1000 for x in ft["diag"]], color=C_FT, lw=2, ls="--", label="FT forecast (Hb-day horizon mean)")
    a.set_ylabel("value\n(USD/MWh)"); a.legend(fontsize=6, frameon=False, ncol=3, loc="upper left")
    # 2 estimated loss
    a = ax[1]
    a.plot(days, [x["A"].sum() if "A" in x else np.nan for x in pl["diag"]], color=C_PL, lw=2)
    a.set_ylabel("planner est.\nloss A, sum (USD)")
    # 3 index and trigger
    a = ax[2]
    a.plot(days, series(pl, "phi", np.max), color=C_PL, lw=2, label="planner max Φ (open rows)")
    a.plot(days, series(ft, "nb", np.max), color=C_FT, lw=2, ls="--", label="FT max NB (open rows); cleans if ≥ 0")
    a.axhline(0, color=MUTED, lw=0.8)
    a.set_ylabel("USD"); a.legend(fontsize=6, frameon=False, ncol=2, loc="upper left")
    # 4 cleanings and rain
    a = ax[3]
    n_pl = [len(x["rows"]) for x in pl["diag"]]; n_ft = [len(x["rows"]) for x in ft["diag"]]
    a.vlines(days - 0.2, 0, n_pl, color=C_PL, lw=2, label="planner rows cleaned")
    a.vlines(days + 0.2, 0, n_ft, color=C_FT, lw=2, label="FT rows cleaned")
    if js_sched is not None:
        jd = [d for d, rows in js_sched for _ in rows]
        a.plot(sorted(set(jd)), [-0.6] * len(set(jd)), "^", ms=5, color=C_JS, label="clairvoyant J* mission")
    rd = [(x["day"], x["rain"]) for x in pl["diag"] if x["rain"] >= 1]
    for k, (d, mm) in enumerate(rd):
        a.annotate(f"{mm:.0f}", (d, max(n_pl + n_ft) + 0.3 + 0.9 * (k % 2)), fontsize=5.5, color=MUTED, ha="center")
        a.axvline(d, color=MUTED, lw=0.6, ls=":")
    a.set_ylabel("rows / mission"); a.legend(fontsize=6, frameon=False, ncol=3, loc="lower left", bbox_to_anchor=(0, 1.0))
    a.set_ylim(-1.2, max(n_pl + n_ft) + 2.4)
    # 5 cumulative paired net
    a = ax[4]
    a.plot(days, cum, color=INK, lw=2, label="planner − FT")
    if js_cum is not None:
        a.plot(days, js_cum, color=C_JS, lw=2, ls="-.", label="planner − clairvoyant J*")
    a.axhline(0, color=MUTED, lw=0.8)
    a.set_ylabel("cumulative paired\nnet (USD)"); a.set_xlabel("day of simulated year (shaded: crop-access window; dotted: rain ≥ 1 mm, labelled in mm)")
    a.legend(fontsize=6, frameon=False, loc="lower left")
    fig.suptitle(title, fontsize=8, x=0.01, ha="left")
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)


def run(S: Study) -> dict:
    """Both diagnostic cases and the checks over all seeds (failure_diag.json, 2 figures)."""
    FIG = S.out_path("figures"); os.makedirs(FIG, exist_ok=True)
    out = {}
    # ---------------- (a) R1 Spain merchant 2024, F2
    ch = S.stored("results_chrono.json")["ES_raw|merchant|Y2"]
    t = ch["test"]["F2"]; seeds = list(range(len(t["proposed"]["net"])))
    s, dval, med = median_seed(seeds, np.array(t["proposed"]["net"]) - np.array(t["ft"]["net"]))
    ex = dict(real_value="ES_raw", fc_mode="roll", roll_min_hist=1)
    cte = dict(model.CONFIG, **ex, real_years=(1,)); ctr = dict(model.CONFIG, **ex, real_years=(0,))
    inp = model.planner_inputs("merchant", ctr)
    pl = run_policy("proposed", t["proposed"]["params"], "merchant", s, cte, inp)
    ft = run_policy("ft", t["ft"]["params"], "merchant", s, cte, inp)
    assert pl["net"] == t["proposed"]["net"][s] and ft["net"] == t["ft"]["net"][s], "diag rerun does not reproduce stored nets"
    days = np.array([x["day"] for x in pl["diag"]])
    sa, cum = summarise("ES merchant 2024 F2", pl, ft, days, dict(seed=s, seed_diff=dval, median_diff=med, params=dict(planner=t["proposed"]["params"], ft=t["ft"]["params"])))
    out["a"] = sa
    plot(os.path.join(FIG, "r1b_diag_es_merchant_2024.pdf"),
         f"(a) R1, Spain merchant 2024, F2 - seed {s} (planner − FT {dval:+.0f} USD/yr; median over 50 seeds {med:+.0f})", pl, ft, cum)
    # ---------------- (b) exact benchmark, merchant, c_row 4
    ex_ = S.stored("results_exact.json")["merchant|c4.0"]
    mp = S.stored("results_matched.json")["part_b"]["merchant|c4.0"]
    seeds = sorted(e["seed"] for e in ex_["exact"])
    dpf = np.array(ex_["site"]["proposed"]["seeds"]) - np.array(mp["ft"]["seeds"])
    s, dval, med = median_seed(seeds, dpf)
    cfg = dict(model.CONFIG, n_rows=6, night_min=100.0, d0=120, d1=180, c_row=4.0)
    inp = model.planner_inputs("merchant", cfg)
    pl = run_policy("proposed", ex_["site"]["proposed"]["params"], "merchant", s, cfg, inp)
    ft = run_policy("ft", mp["ft"]["params"], "merchant", s, cfg, inp)
    none = model.simulate("none", {}, "merchant", s, cfg=cfg)["net"]
    assert pl["net"] - none == ex_["site"]["proposed"]["seeds"][s] and ft["net"] - none == mp["ft"]["seeds"][s]
    Rev = row_tables(s, "merchant", cfg)
    res, sched = solve(Rev, cfg, 120)
    jstar = schedule_value(Rev, sched, cfg) - schedule_value(Rev, [], cfg)
    # daily net of the J* schedule on the same revenue table
    last = np.full(cfg["n_rows"], cfg["d0"]); byday = dict(sched); js_day = []
    for d in range(cfg["d0"], cfg["d1"]):
        cost = 0.0
        if byday.get(d):
            for r_ in byday[d]: last[r_] = d
            cost = cfg["c_mission"] + cfg["c_row"] * len(byday[d])
        js_day.append(sum(Rev[i, last[i] - cfg["d0"], d - cfg["d0"]] for i in range(cfg["n_rows"])) - cost)
    plan_check = schedule_value(Rev, pl["sched"], cfg) - schedule_value(Rev, [], cfg)
    days = np.array([x["day"] for x in pl["diag"]])
    sb, cum = summarise("exact merchant c4", pl, ft, days,
                        dict(seed=s, seed_diff=dval, median_diff=med, jstar=jstar, jstar_status=int(res.status), jstar_sched=sched,
                             planner_gain=pl["net"] - none, ft_gain=ft["net"] - none, planner_gain_on_rev_table=plan_check,
                             params=dict(planner=ex_["site"]["proposed"]["params"], ft=mp["ft"]["params"])))
    cum_js = np.cumsum(np.array([x["net_day"] for x in pl["diag"]]) - np.array(js_day))
    sb["final_planner_minus_jstar"] = float(cum_js[-1])
    out["b"] = sb
    plot(os.path.join(FIG, "r1b_diag_exact_merchant_c4.pdf"),
         f"(b) Exact benchmark, merchant, 4 USD/row, 6 rows, days 120-180 - seed {s} (planner − FT {dval:+.1f} USD; median over 20 {med:+.1f})",
         pl, ft, cum, js_sched=sched, js_cum=cum_js)
    # ---------------- checks over all seeds (is the median seed's pattern typical?)
    t = ch["test"]["F2"]; ca = []
    inp_a = model.planner_inputs("merchant", ctr)
    for s_ in range(len(t["proposed"]["net"])):
        a_ = run_policy("proposed", t["proposed"]["params"], "merchant", s_, cte, inp_a); f_ = run_policy("ft", t["ft"]["params"], "merchant", s_, cte, inp_a)
        c_ = np.cumsum(np.array([x["net_day"] for x in a_["diag"]]) - np.array([x["net_day"] for x in f_["diag"]]))
        early = lambda r: sum(len(x["rows"]) for x in r["diag"] if x["day"] < 120)
        wasted = lambda r: sum(len(x["rows"]) for x in r["diag"] if x["rows"] and any(y["rain"] >= 5 for y in r["diag"][x["day"] + 1:x["day"] + 15]))
        ca.append(dict(seed=s_, cum_day120=float(c_[119]), final=float(c_[-1]), pl_rows_before_120=early(a_), ft_rows_before_120=early(f_),
                       pl_rows_rain5_within14d=wasted(a_), ft_rows_rain5_within14d=wasted(f_)))
    cb = []
    for s_ in seeds:
        a_ = run_policy("proposed", ex_["site"]["proposed"]["params"], "merchant", s_, cfg, inp); f_ = run_policy("ft", mp["ft"]["params"], "merchant", s_, cfg, inp)
        Rv = row_tables(s_, "merchant", cfg); _, sc_ = solve(Rv, cfg, 120)
        late = lambda sch: sum(len(r) for d, r in sch if d >= 160)
        cb.append(dict(seed=s_, pl_rows_day160plus=late(a_["sched"]), ft_rows_day160plus=late(f_["sched"]), jstar_rows_day160plus=late(sc_),
                       pl_rows=a_["n_clean"], ft_rows=f_["n_clean"], jstar_rows=sum(len(r) for _, r in sc_)))
    S = lambda L, k: float(np.mean([x[k] for x in L]))
    out["checks"] = dict(
        a=dict(per_seed=ca, mean_cum_day120=S(ca, "cum_day120"), mean_final=S(ca, "final"), seeds_cum120_below0=sum(x["cum_day120"] < 0 for x in ca),
               mean_pl_rows_before_120=S(ca, "pl_rows_before_120"), mean_ft_rows_before_120=S(ca, "ft_rows_before_120"),
               mean_pl_rows_rain5_within14d=S(ca, "pl_rows_rain5_within14d"), mean_ft_rows_rain5_within14d=S(ca, "ft_rows_rain5_within14d")),
        b=dict(per_seed=cb, **{f"mean_{k}": S(cb, k) for k in ("pl_rows_day160plus", "ft_rows_day160plus", "jstar_rows_day160plus", "pl_rows", "ft_rows", "jstar_rows")}))
    return dict(label="DESCRIPTIVE", **out)
