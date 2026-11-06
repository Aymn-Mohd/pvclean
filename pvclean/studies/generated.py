"""Generated-market studies: tune every policy on the train seeds, evaluate on the test seeds."""
from __future__ import annotations
import time
from typing import Any
import numpy as np
from pvclean import model
from pvclean.config import CONFIG, STORED_CONFIG_KEYS
from pvclean.sites import site_params
from pvclean.stats import paired_short as paired, paired_summary
from .runner import Runner
from .study import Study


def price_stats(rn: Runner, over: dict[str, Any]) -> dict[str, float]:
    """Share of negative hours and capture ratio of a price model."""
    cfg = model.merged(over)
    a, d, cp = [], [], []
    for s in rn.test:
        w = model.weather(s, cfg); sp = model.spot_prices(s, cfg); dy = w["pdc"] > 0.05
        a.append((sp < 0).mean()); d.append((sp[dy] < 0).mean())
        cp.append((np.maximum(sp, 0) * w["pdc"]).sum() / w["pdc"].sum() / sp.mean())
    return dict(neg_all=float(np.mean(a)), neg_day=float(np.mean(d)), capture=float(np.mean(cp)))


def best_of(ev: dict[str, Any], baselines: list[str]) -> str:
    """The baseline with the best test mean, as the first generated-market studies chose it."""
    return max(baselines, key=lambda p: ev[p]["inc_net"][0])


def rq(S: Study) -> dict[str, Any]:
    """RQ1 policies, RQ3 row information, cost and soiling sensitivity, and the price regime sweep (results.json)."""
    P = S.params; t0 = time.time()
    results: dict[str, Any] = {"config": {k: CONFIG[k] for k in STORED_CONFIG_KEYS}, "train_seeds": S.protocol.train, "test_seeds": S.protocol.test, "expo": {}}
    for h in sorted(set(P["het_sweep"] + P["het_fig"])):
        e = model.exposure(CONFIG, hetero=h)
        results["expo"][str(h)] = dict(cv=float(e.std() / e.mean()), maxmin=float(e.max() / e.min()), lo=float(e.min()), hi=float(e.max()))
    with S.runner_pool() as rn:
        base = rn.baselines; rq1: dict[str, Any] = {}; transfer: dict[str, Any] = {}; best_fixed = None
        for c in rn.contracts:
            best = rn.tune_params(c, policies=P["rq1_policies"])
            if c == "fixed":
                best_fixed = best
            else:
                pols = P["core_policies"]
                evt = rn.evaluate_summary(c, {p: best_fixed[p] for p in pols}, policies=pols)
                transfer[c] = {p: dict(params=evt[p]["params"], inc_net=evt[p]["inc_net"], n_clean=evt[p]["n_clean"], inc_net_seeds=evt[p]["inc_net_seeds"]) for p in pols}
            ev = rn.evaluate_summary(c, best)
            bb = best_of(ev, base)
            ev["_best_baseline"] = bb
            for tag, other in (("_paired_vs_best", bb), ("_paired_vs_econ", "econ"), ("_paired_noval", "proposed_noval"), ("_paired_nobatch", "proposed_nobatch")):
                ev[tag] = paired(ev["proposed"]["inc_net_seeds"], ev[other]["inc_net_seeds"])
            rq1[c] = ev
            print(c, "done", round(time.time() - t0), "s", flush=True)
        results["rq1"] = rq1; results["transfer"] = transfer
        rq3: dict[str, Any] = {}
        for c in P["rq3_contracts"]:
            par = rq1[c]["proposed"]["params"]
            for het in P["het_sweep"]:
                for info, sig, pe in (P["regimes_full"] if het in P["het_fig"] else P["regimes_cv"]):
                    ev = rn.evaluate_summary(c, {"proposed": par}, cfg_over={"patrol_every": pe}, info=info, sigma=sig, hetero=het, policies=["proposed"])
                    rq3[f"{c}|h{het}|{info}|s{sig}|p{pe}"] = ev["proposed"]
        results["rq3"] = rq3
        sens: dict[str, Any] = {}
        for c in P["sens_contracts"]:
            for crow in P["crow"]:
                for sm in P["soil"]:
                    over = {"c_row": crow, "soil_mean": sm}; pols = P["core_policies"]
                    best = rn.tune_params(c, cfg_over=over, policies=pols)
                    ev = rn.evaluate_summary(c, best, cfg_over=over, policies=pols)
                    bb = best_of(ev, base)
                    sens[f"{c}|c{crow}|s{sm}"] = dict(best_baseline=bb, proposed=ev["proposed"]["inc_net"], baseline=ev[bb]["inc_net"],
                                                      paired=paired(ev["proposed"]["inc_net_seeds"], ev[bb]["inc_net_seeds"]),
                                                      n_clean_prop=ev["proposed"]["n_clean"], n_clean_base=ev[bb]["n_clean"])
        results["sens"] = sens
        pr: dict[str, Any] = {}
        for c in P["price_contracts"]:
            for sc in P["price_scales"]:
                over = {"price_depress_scale": sc}; pols = P["noval_policies"]
                best = rn.tune_params(c, cfg_over=over, policies=pols)
                ev = rn.evaluate_summary(c, best, cfg_over=over, policies=pols)
                bb = best_of(ev, base)
                pr[f"{c}|k{sc}"] = dict(stats=price_stats(rn, over), best_baseline=bb, proposed=ev["proposed"]["inc_net"], baseline=ev[bb]["inc_net"],
                                        vs_best=paired(ev["proposed"]["inc_net_seeds"], ev[bb]["inc_net_seeds"]),
                                        vs_noval=paired(ev["proposed"]["inc_net_seeds"], ev["proposed_noval"]["inc_net_seeds"]),
                                        vs_econ=paired(ev["proposed"]["inc_net_seeds"], ev["econ"]["inc_net_seeds"]), revenue_none=ev["proposed"]["revenue_none"])
        results["price"] = pr
    results["runtime_s"] = time.time() - t0
    return results


def quickstart(S: Study) -> dict[str, Any]:
    """A small run at one site: tune each policy, test it and print its value of cleaning. `params.site` names the site; `params.over` adds overrides."""
    P = S.params; pols = P["policies"]; over = dict(site_params(P["site"]), **P.get("over", {})); out: dict[str, Any] = {"site": P["site"], "contracts": {}}
    with S.runner_pool() as rn:
        for c in P["contracts"]:
            best = rn.tune(c, over, pols)
            ev = rn.evaluate(c, {p: best[p]["params"] for p in pols}, over, {}, pols)
            out["contracts"][c] = {p: dict(params=best[p]["params"], value_of_cleaning=float(np.mean(ev[p]["inc_net"])), row_cleanings=float(np.mean(ev[p]["n_clean"]))) for p in pols}
            for p in pols:
                r = out["contracts"][c][p]
                print(f"{c:9s} {p:10s} value of cleaning {r['value_of_cleaning']:9.1f} USD, {r['row_cleanings']:6.1f} row cleanings, params {r['params']}", flush=True)
    return out


def ft_synthetic(S: Study) -> dict[str, Any]:
    """FT in the generated-market study, with all paired comparisons on identical seeds (results_ft_synthetic.json)."""
    pols = S.params["policies"]; out = {}
    with S.runner_pool() as rn:
        for c in rn.contracts:
            best = rn.tune_params(c, policies=pols)
            ev = rn.evaluate_summary(c, best, policies=pols)
            bb = best_of(ev, rn.baselines)
            res: dict[str, Any] = {p: dict(params=ev[p]["params"], seeds=ev[p]["inc_net_seeds"], inc=ev[p]["inc_net"], n_clean=ev[p]["n_clean"]) for p in pols}
            res["best_baseline"] = bb
            res["stats"] = {"proposed_vs_best_baseline": paired_summary(res["proposed"]["seeds"], res[bb]["seeds"]), "ft_vs_best_baseline": paired_summary(res["ft"]["seeds"], res[bb]["seeds"]),
                            "proposed_vs_ft": paired_summary(res["proposed"]["seeds"], res["ft"]["seeds"]), "proposed_vs_econ": paired_summary(res["proposed"]["seeds"], res["econ"]["seeds"])}
            out[c] = res
    return out


def extra(S: Study) -> dict[str, Any]:
    """Rain-day scale and manual-scale cleaning cost (results_extra.json)."""
    P = S.params; pols = P["policies"]; out: dict[str, Any] = {"rain": {}, "cost": {}}
    with S.runner_pool() as rn:
        def rec(ev: dict[str, Any]) -> dict[str, Any]:
            bb = best_of(ev, rn.baselines)
            return dict(best_baseline=bb, proposed=ev["proposed"]["inc_net"], baseline=ev[bb]["inc_net"], paired=paired(ev["proposed"]["inc_net_seeds"], ev[bb]["inc_net_seeds"]),
                        none_energy=ev["proposed"]["energy_none_mwh"])
        for c in P["contracts"]:
            for rs in P["rain_scales"]:
                over = {"rain_scale": rs}
                best = rn.tune_params(c, cfg_over=over, policies=pols)
                r = rec(rn.evaluate_summary(c, best, cfg_over=over, policies=pols))
                cfg = model.merged(over)
                r["rain_days"] = float(np.mean([(model.weather(s, cfg)["rain"] >= 1).sum() for s in rn.test]))
                out["rain"][f"{c}|r{rs}"] = r
            for crow in P["crow"]:
                over = {"c_row": crow}
                best = rn.tune_params(c, cfg_over=over, policies=pols)
                out["cost"][f"{c}|c{crow}"] = rec(rn.evaluate_summary(c, best, cfg_over=over, policies=pols))
    return out


def rec_full(ev: dict[str, Any], pols: list[str], baselines: list[str]) -> dict[str, Any]:
    """Record of one cell with per-seed values."""
    bb = best_of(ev, baselines)
    return dict(best_baseline=bb, proposed=ev["proposed"]["inc_net"], baseline=ev[bb]["inc_net"], paired=paired(ev["proposed"]["inc_net_seeds"], ev[bb]["inc_net_seeds"]),
                noval=paired(ev["proposed"]["inc_net_seeds"], ev["proposed_noval"]["inc_net_seeds"]), none_energy=ev["proposed"]["energy_none_mwh"], n_clean=ev["proposed"]["n_clean"],
                params={p: ev[p]["params"] for p in pols}, seeds={p: ev[p]["inc_net_seeds"] for p in pols})


def nrel(S: Study) -> dict[str, Any]:
    """NREL-calibrated soiling sweep (results_nrel.json)."""
    pols = S.params["policies"]; out = {}
    with S.runner_pool() as rn:
        for tag, over in S.params["cells"].items():
            for c in S.params["contracts"]:
                best = rn.tune_params(c, cfg_over=over, policies=pols)
                out[f"{tag}|{c}"] = rec_full(rn.evaluate_summary(c, best, cfg_over=over, policies=pols), pols, rn.baselines)
                out[f"{tag}|{c}"]["over"] = over
    return out


def wx(S: Study) -> dict[str, Any]:
    """Real Dubai weather: 16 held-out weather years x 3 dust draws (results_wx.json)."""
    P = S.params; pols = P["policies"]
    otr = {"wx_years": tuple(range(*P["train_years"]))}; ote = {"wx_years": tuple(range(*P["test_years"]))}; out = {}
    with S.runner_pool() as rn:
        for c in P["contracts"]:
            best = rn.tune_params(c, cfg_over=otr, policies=pols)
            out[c] = rec_full(rn.evaluate_real(c, best, ote, otr, pols), pols, rn.baselines)
            best_s = rn.tune_params(c, policies=pols)      # the same held-out seeds on the generated weather
            out[c]["synthetic"] = rec_full(rn.evaluate_summary(c, best_s, policies=pols), pols, rn.baselines)
    return out
