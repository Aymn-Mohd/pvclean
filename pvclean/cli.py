"""Command line: python -m pvclean run <config.yaml> | tune <config.yaml> | report | download <source>."""
from __future__ import annotations
import argparse
import json
import sys
from pvclean.data import data_dir


def main(argv: list[str] | None = None) -> int:
    """Parses arguments and runs one command. Returns the exit status."""
    ap = argparse.ArgumentParser(prog="pvclean", description="Runs studies, tunes policies, rebuilds paper outputs and downloads data.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a study config")
    r.add_argument("config"); r.add_argument("--out", help="output directory (default runs/<study>/)"); r.add_argument("--workers", type=int)
    t = sub.add_parser("tune", help="tune policies on the train seeds of a study and print the parameters")
    t.add_argument("config"); t.add_argument("--contract", default="merchant"); t.add_argument("--policies", nargs="*"); t.add_argument("--workers", type=int)
    p = sub.add_parser("report", help="rebuild paper macros, tables and figures from stored results")
    p.add_argument("--out", help="paper output directory (default papers/e1_pes)"); p.add_argument("--results-out", help="directory for macros_*.json (default results/)")
    p.add_argument("--no-figures", action="store_true", help="skip the R2 figures"); p.add_argument("--refresh-inputs", action="store_true", help="recompute results/macro_inputs.json from the data cache")
    p.add_argument("--summaries", action="store_true", help="also rewrite docs/records/R*_SUMMARY.md")
    d = sub.add_parser("download", help="fetch data into the cache, one attempt per URL")
    d.add_argument("source"); d.add_argument("--limit", type=int); d.add_argument("--sites", nargs="*", help="only these sites; a failed site is dropped and the next one continues")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        from pvclean.studies import run_study
        path, secs = run_study(a.config, a.out, a.workers)
        print(f"wrote {path} in {secs:.1f} s")
    elif a.cmd == "tune":
        from pvclean.studies import load_study
        S = load_study(a.config, workers=a.workers)
        pols = a.policies or [p_ for p_ in ("fixed", "threshold", "econ", "ft", "proposed")]
        with S.runner_pool() as rn:
            print(json.dumps(rn.tune(a.contract, S.params.get("over", {}), pols), indent=1))
    elif a.cmd == "report":
        from pvclean.reporting import build_all
        for line in build_all(out=a.out, results_out=a.results_out, figures=not a.no_figures, refresh_inputs=a.refresh_inputs, summaries=a.summaries):
            print(line)
    else:
        from pvclean.download import download
        res = download(a.source, a.limit, a.sites)
        print(f"{a.source}: {res['status']}; {len(res['files'])} files in {data_dir()}")
        return 0 if res["status"] == "ok" else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
