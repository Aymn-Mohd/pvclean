"""POST HOC sanity checks of the surprising R5 result: Whyalla 2024 against Port Augusta 2024, merchant, on nearly the same rain. Writes results/r5_sanity.json and paper/fig_r5_sanity_trace.png.
Run: python src/r5_sanity.py"""
from __future__ import annotations
import io
import json
import os
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pvclean import model
from pvclean.config import load_protocol
from pvclean.data import data_path, repo_root, results_dir
from pvclean.sites import site_config
from pvclean.stats import paired
from pvclean.studies import r4
from pvclean.studies.matched import CAL
from pvclean.studies.runner import Runner, job, record_job

YEAR, FOLD, C = 2024, "Y2", "merchant"
SITES = ("whyalla", "port_augusta")
RETUNE = dict(train1005=[1005, 1006, 1007, 1008, 1009], train1010=[1010, 1011, 1012, 1013, 1014], train1015=[1015, 1016, 1017, 1018, 1019])


def overs(site: str) -> tuple[dict, dict]:
    """Test and training overrides, as chrono.run_fold builds them."""
    ex = dict(real_value=r4.market_of(site), fc_mode="roll", roll_min_hist=1, **r4.site_over(site, YEAR))
    return dict(ex, real_years=(CAL.index(YEAR),)), dict(ex, real_years=(CAL.index(YEAR) - 1,))


def main() -> None:
    res = results_dir(); lines: list[str] = []; out: dict = dict(year=YEAR, contract=C)
    rec = {"whyalla": json.load(open(os.path.join(res, "results_r5_merchant.json")))["r5"][f"soil0.30|whyalla|{C}|{FOLD}"], "port_augusta": json.load(open(os.path.join(res, "results_r4_sites.json")))["r4"][f"soil0.30|port_augusta|{C}|{FOLD}"]}
    # same seed
    worst = 0.0
    for s, v in rec.items():
        te, tr = overs(s)
        for p in ("ft", "proposed"):
            for seed in (0, 1, 2):
                worst = max(worst, abs(job((p, v["tuned"]["F2"][p]["params"], C, seed, "site", 0.01, 1.0, dict(te, _inp=dict(tr))))[1]["net"] - v["test"]["F2"][p]["net"][seed]))
    out["same_seed_max_abs_diff_usd"] = worst
    lines.append(f"Same seed: fresh runs of planner and FT at both sites, seeds 0 to 2, differ from the stored net by at most {worst:.2e} USD.")
    # inputs: rain from the raw files; the two sites really are two tables; dust is shared
    raw = pd.concat([pd.read_csv(io.StringIO(open(data_path("raw", "nasa_power", f"whyalla_{y}.csv")).read().split("-END HEADER-\n")[1])) for y in (YEAR - 1, YEAR, YEAR + 1)])
    t = pd.to_datetime(dict(year=raw.YEAR, month=raw.MO, day=raw.DY, hour=raw.HR)).dt.tz_localize("UTC").dt.tz_convert("Etc/GMT-10")
    daily = raw.PRECTOTCORR.groupby(t.dt.strftime("%Y-%m-%d").values).sum()
    daily = daily[[k.startswith(str(YEAR)) and not k.endswith("02-29") for k in daily.index]].values
    b = {s: model.site_year(YEAR, model.merged(site_config(s))) for s in SITES}
    rd = float(np.max(np.abs(daily - b["whyalla"]["rain"])))
    d0 = [model.dust(0, model.merged(overs(s)[0])) for s in SITES]
    big = {s: set(np.flatnonzero(b[s]["rain"] >= 5).tolist()) for s in SITES}
    out["rain_vs_raw_file_max_abs_mm"] = rd
    lines.append(f"Inputs: Whyalla's rain rebuilt from the raw files differs from the model's by at most {rd:.2e} mm. Dust and row noise of seed 0 are equal at both sites: {bool(np.array_equal(d0[0][0], d0[1][0]) and np.array_equal(d0[0][1], d0[1][1]))}. Rain and production are separate tables: daily rain correlation {np.corrcoef(b['whyalla']['rain'], b['port_augusta']['rain'])[0, 1]:.2f}, days >= 5 mm {len(big['whyalla'])} and {len(big['port_augusta'])}, of which {len(big['whyalla'] & big['port_augusta'])} are shared, DC yield {b['whyalla']['pdc'].sum():.0f} and {b['port_augusta']['pdc'].sum():.0f} kWh/kWp.")
    # every planner grid point on the test year, and the training mean that chose among them
    P = load_protocol(); grid = P.grids["proposed"]; T: dict = {}
    with Runner(P) as rn:
        for s, v in rec.items():
            te, tr = overs(s); ft = v["tuned"]["F2"]["ft"]["params"]; rows = []
            for par in grid:
                ev = rn.evaluate(C, dict(proposed=par, ft=ft), te, tr, ["proposed", "ft"])
                trn = rn.map(record_job, [("proposed", par, C, x, "site", 0.01, 1.0, tr) for x in rn.train])
                rows.append(dict(params=par, train_mean=float(np.mean([r["net"] for r in trn])), planner_ft=paired(ev["proposed"]["net"], ev["ft"]["net"]), rows=float(np.mean(ev["proposed"]["n_clean"]))))
            T[s] = dict(chosen=v["tuned"]["F2"]["proposed"]["params"], ft=ft, grid=rows)
            m = [r["planner_ft"]["mean"] for r in rows]; tm = [r["train_mean"] for r in rows]
            lines.append(f"{s}, every point of the R3 planner grid on {YEAR}: planner minus FT runs from {min(m):+.0f} to {max(m):+.0f}, positive at {sum(x > 0 for x in m)} of {len(m)} points. Chosen: beta {T[s]['chosen']['beta']:g}, kappa {T[s]['chosen']['kappa']:g}, with {rec[s]['cmp']['planner-ft|F2']['mean']:+.0f}. Training means span {max(tm) - min(tm):.0f} USD, and the top two differ by {sorted(tm)[-1] - sorted(tm)[-2]:.1f} USD.")
        # other train seeds
        R: dict = {}
        for name, seeds in RETUNE.items():
            q = rn.with_(train=seeds)
            for s in SITES:
                R[f"{s}|{name}"] = r4.row(r4.run_case(q, s, C, FOLD, "POST HOC"))
        out["retune"] = {k: dict(planner_ft=v["planner_ft"], params=v["params"]["proposed"], ft=v["params"]["ft"]) for k, v in R.items()}
        for s in SITES:
            lines.append(f"{s}, tuning repeated on three other train-seed sets: " + ", ".join(f"{R[f'{s}|{n}']['planner_ft']['mean']:+.0f} (kappa {R[f'{s}|{n}']['params']['proposed']['kappa']:g})" for n in RETUNE) + ".")
    out["grid"] = T
    # traces
    fig, axes = plt.subplots(2, 1, figsize=(6.5, 4), sharex=True, sharey=True)
    for ax, s in zip(axes, SITES):
        te, tr = overs(s); v = rec[s]
        for name, p, par, col in (("no cleaning", "none", {}, "#8a8984"), ("FT", "ft", v["tuned"]["F2"]["ft"]["params"], "#eb6834"), ("planner", "proposed", v["tuned"]["F2"]["proposed"]["params"], "#2a78d6")):
            r = job((p, par, C, 0, "site", 0.01, 1.0, dict(te, _inp=dict(tr), mission_log=True)))[1]
            ax.plot(np.array(r["sr_log"]).mean(axis=1), lw=1, label=name, color=col)
        ax.set_ylabel(f"{s}\nmean row soiling ratio"); ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, ncol=3); axes[1].set_xlabel(f"day of {YEAR}, merchant, seed 0")
    os.makedirs(os.path.join(repo_root(), "paper"), exist_ok=True); fig.tight_layout(); fig.savefig(os.path.join(repo_root(), "paper", "fig_r5_sanity_trace.png"), dpi=200)
    out["lines"] = lines
    json.dump(out, open(os.path.join(res, "r5_sanity.json"), "w"), indent=1, default=float)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
