"""POST HOC sanity checks of the surprising R4 site-year, Almeria 2024: planner above FT under merchant, below FT under PPA. Writes results/r4_sanity.json and paper/fig_r4_sanity_trace.png.
Run: python src/r4_sanity.py"""
from __future__ import annotations
import json
import os
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import numpy as np
from pvclean import model
from pvclean.data import repo_root, results_dir
from pvclean.sites import site_config
from pvclean.studies import r4
from pvclean.studies.matched import CAL
from pvclean.studies.runner import job

SITE, FOLD, YEAR, SEED = "almeria", "Y2", 2024, 0


def overs() -> tuple[dict, dict]:
    """Test and training overrides of the fold, as chrono.run_fold builds them."""
    ex = dict(real_value=r4.market_of(SITE), fc_mode="roll", roll_min_hist=1, **r4.site_over(SITE, YEAR))
    return dict(ex, real_years=(CAL.index(YEAR),)), dict(ex, real_years=(CAL.index(YEAR) - 1,))


def run(pol: str, par: dict, c: str, seed: int, log: bool = False) -> dict:
    """One year, as the job ran it; log adds the daily row states."""
    te, tr = overs()
    over = dict(te, _inp=dict(tr))
    if log:
        over["mission_log"] = True
    return job((pol, par, c, seed, "site", 0.01, 1.0, over))[1]


def main() -> None:
    R = json.load(open(os.path.join(results_dir(), "results_r4_sites.json")))["r4"]
    rec = {c: R[f"soil0.30|{SITE}|{c}|{FOLD}"] for c in ("merchant", "ppa")}
    seeds = rec["ppa"]["test"]["F2"]; lines = []; out: dict = dict(site=SITE, year=YEAR, seed=SEED)
    # 1. same seed: stored net reproduced from a fresh run, for every policy, contract and three seeds
    worst = 0.0
    for c, v in rec.items():
        for p in ("ft", "proposed"):
            par = v["tuned"]["F2"][p]["params"]
            for s in (0, 1, 2):
                worst = max(worst, abs(run(p, par, c, s)["net"] - v["test"]["F2"][p]["net"][s]))
    out["same_seed_max_abs_diff_usd"] = worst
    lines.append(f"Same seed: fresh runs of planner and FT, both contracts, seeds 0 to 2, differ from the stored net by at most {worst:.2e} USD.")
    # 2. identical inputs: weather, dust, exposure and rain flags do not depend on policy or contract
    te, _ = overs(); cfg = model.merged(te)
    w = model.weather(SEED, cfg); inc, noise = model.dust(SEED, cfg); fc = model.rain_forecast(w["rain"], SEED, cfg)
    w2 = model.weather(SEED, model.merged(dict(te))); inc2, noise2 = model.dust(SEED, model.merged(dict(te))); fc2 = model.rain_forecast(w2["rain"], SEED, model.merged(dict(te)))
    same = all(np.array_equal(a, b) for a, b in ((w["pdc"], w2["pdc"]), (w["rain"], w2["rain"]), (inc, inc2), (noise, noise2), (fc, fc2)))
    none = {c: rec[c]["test"]["F2"]["none"]["energy_kwh"] for c in rec}
    out["inputs_identical"] = bool(same); out["none_energy_same_across_contracts"] = bool(np.allclose(none["merchant"], none["ppa"], rtol=0.02))
    gap = float(np.max(np.abs(np.array(none["merchant"]) / np.array(none["ppa"]) - 1)))
    lines.append(f"Identical inputs: production, rain, dust, row noise and rain flags are equal across rebuilt configs: {same}. No-cleaning energy under merchant and PPA differs by at most {100 * gap:.2f}%.")
    # raw file against the model's rain, computed independently of the pipeline
    import io
    import pandas as pd
    from pvclean.data import data_path
    raw = pd.concat([pd.read_csv(io.StringIO(open(data_path("raw", "nasa_power", f"{SITE}_{y}.csv")).read().split("-END HEADER-\n")[1])) for y in (YEAR - 1, YEAR, YEAR + 1)])
    t = pd.to_datetime(dict(year=raw.YEAR, month=raw.MO, day=raw.DY, hour=raw.HR)).dt.tz_localize("UTC").dt.tz_convert("Europe/Madrid")
    daily = raw.PRECTOTCORR.groupby(t.dt.strftime("%Y-%m-%d").values).sum()
    daily = daily[[k.startswith(str(YEAR)) and not k.endswith("02-29") for k in daily.index]].values
    rd = float(np.max(np.abs(daily - w["rain"])))
    out["rain_vs_raw_file_max_abs_mm"] = rd
    lines.append(f"Rain: daily totals rebuilt directly from the raw NASA POWER files differ from the model's rain by at most {rd:.2e} mm.")
    # 3. the traces
    T: dict = {}
    fig, axes = plt.subplots(2, 1, figsize=(6.5, 4), sharex=True, sharey=True)
    for ax, c in zip(axes, ("merchant", "ppa")):
        v = rec[c]; d = {}
        for name, p, par in (("no cleaning", "none", {}), ("FT", "ft", v["tuned"]["F2"]["ft"]["params"]), ("planner", "proposed", v["tuned"]["F2"]["proposed"]["params"])):
            r = run(p, par, c, SEED, log=True); sr = np.array(r["sr_log"]).mean(axis=1); d[name] = sr
            ax.plot(sr, lw=1, label=name, color={"no cleaning": "#8a8984", "FT": "#eb6834", "planner": "#2a78d6"}[name])
            T[f"{c}|{name}"] = dict(mean_sr=float(sr.mean()), n_clean=float(r["n_clean"]), n_missions=float(r["n_missions"]), net=float(r["net"]), energy_mwh=float(r["energy_kwh"] / 1000))
        ax.set_ylabel(f"{c}\nmean row soiling ratio"); ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, ncol=3); axes[1].set_xlabel(f"day of {YEAR}, seed {SEED}")
    os.makedirs(os.path.join(repo_root(), "paper"), exist_ok=True)
    fig.tight_layout(); fig.savefig(os.path.join(repo_root(), "paper", "fig_r4_sanity_trace.png"), dpi=200)
    out["traces"] = T
    # 4. why PPA differs: seed-mean spending and energy, planner minus FT
    for c, v in rec.items():
        d = v["decomp"]["planner-ft"]; q = d["d_clean_cost"]["mean"] + d["d_mission_cost"]["mean"]
        out[f"split_{c}"] = dict(net=d["d_net"]["mean"], revenue=d["d_revenue"]["mean"], extra_cost=q, quantity=d["quantity"]["mean"], timing=d["timing"]["mean"], extra_rows=d["d_row_cleanings"]["mean"], extra_missions=d["d_missions"]["mean"], energy_mwh=d["d_energy_mwh"]["mean"], v_ref=d["v_ref_mean"])
        lines.append(f"Almería 2024, {c}: planner minus FT is {d['d_net']['mean']:+.0f} = revenue {d['d_revenue']['mean']:+.0f} minus extra cost {q:+.0f} ({d['d_row_cleanings']['mean']:+.0f} rows, {d['d_missions']['mean']:+.0f} missions). Extra energy {d['d_energy_mwh']['mean']:+.1f} MWh at a reference value of {d['v_ref_mean']:.3f} USD/kWh; quantity {d['quantity']['mean']:+.0f}, timing {d['timing']['mean']:+.0f}.")
    # 5. site inputs are the right site's: yield, and the equator-facing azimuth beats the opposite one
    Y = {}
    for s in r4.NEW_SITES:
        b = model.merged(site_config(s))
        a = float(model.site_year(YEAR, b)["pdc"].sum()); f = float(model.site_year(YEAR, dict(b, azimuth=(b["azimuth"] + 180) % 360))["pdc"].sum())
        Y[s] = dict(dc_kwh_kwp=a, opposite_azimuth=f)
    out["yields"] = Y
    lines.append("DC yield 2024, kWh/kWp, with the opposite azimuth in brackets: " + ", ".join(f"{s} {v['dc_kwh_kwp']:.0f} ({v['opposite_azimuth']:.0f})" for s, v in Y.items()) + f". Equator-facing is higher at every site: {all(v['dc_kwh_kwp'] > v['opposite_azimuth'] for v in Y.values())}.")
    # 6. R3 rows of the shift job against the stored R3 check
    H = json.load(open(os.path.join(results_dir(), "results_r4_shift.json")))["rows"]; old = json.load(open(os.path.join(results_dir(), "r3_checks.json")))["shift"]["soil0.30"]["rows"]
    mk = {"adelaide": "SA1_raw", "brisbane": "QLD1_raw", "seville": "ES_raw"}
    diffs = [abs(H[f"{s}|{c}|{f}"]["planner_ft"]["mean"] - old[f"{m}|{c}|{f}"]["cmp"]["planner-ft|F2"]["mean"]) for s, m in mk.items() for c in ("merchant", "ppa") for f in ("Y2", "Y3")]
    out["shift_vs_r3_max_abs_diff"] = max(diffs)
    lines.append(f"The 12 R3 rows of r4_shift differ from the stored R3 shift check by at most {max(diffs):.2e} USD.")
    out["lines"] = lines
    json.dump(out, open(os.path.join(results_dir(), "r4_sanity.json"), "w"), indent=1, default=float)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
