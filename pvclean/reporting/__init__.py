"""Rebuilds paper macros, tables, figures and the phase summaries from stored results."""
from __future__ import annotations
import json
import os
from pvclean.data import repo_root, results_dir


def build_all(out: str | None = None, results_out: str | None = None, figures: bool = True, refresh_inputs: bool = False, summaries: bool = False, docs: str | None = None) -> list[str]:
    """Runs the generators in order. Later generators replace table_fore.tex and table_exact.tex of the first. Returns a line per step."""
    from . import numbers_main, numbers_pes, numbers_v10
    res = results_dir().rstrip("/") + "/"
    out = (out or os.path.join(repo_root(), "papers", "e1_pes")).rstrip("/") + "/"
    res_out = (results_out or res).rstrip("/") + "/"
    os.makedirs(out, exist_ok=True); os.makedirs(res_out, exist_ok=True)
    log = []
    inp_path = res + "macro_inputs.json"
    if refresh_inputs:
        from .inputs import compute
        json.dump(compute(json.load(open(res + "results.json"))["config"]), open(res_out + "macro_inputs.json", "w"), indent=1)
        inp_path = res_out + "macro_inputs.json"
        log.append(f"wrote {inp_path}")
    numbers_main.build(res, out, json.load(open(inp_path))); log.append(f"wrote {out}numbers.tex, tables and figures")
    numbers_v10.build(res, out, res_out); log.append(f"wrote {out}numbers_v10.tex")
    numbers_pes.build(res, out, res_out); log.append(f"wrote {out}numbers_pes.tex")
    if figures:
        from . import figures_r2
        figures_r2.build(res, os.path.join(res_out, "figures")); log.append("wrote R2 figures")
    if summaries:
        from . import claims_registry, summary_r1, summary_r2, summary_r3
        records = os.path.join(repo_root(), "docs", "records")
        docs = docs or records
        os.makedirs(docs, exist_ok=True)
        summary_r1.build(records, docs); summary_r2.build(res.rstrip("/"), docs); summary_r3.build(res.rstrip("/"), docs); claims_registry.build(os.path.join(repo_root(), "papers", "e1_pes") + "/", docs)
        log.append(f"wrote summaries in {docs}")
    return log
