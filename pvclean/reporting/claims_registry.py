"""EXP-09: list every number macro used in paper/main.tex with its value and defining file."""
from __future__ import annotations
import json
import os
import re
from pvclean.data import results_dir


def build(P: str, DOCS: str) -> None:
    """P: paper directory with a trailing slash. DOCS: output directory."""
    defs = {}
    for f in ("numbers.tex", "numbers_v10.tex", "numbers_pes.tex"):
        for m in re.finditer(r"\\newcommand\{\\(\w+)\}\{(.*)\}", open(P + f).read()):
            defs[m.group(1)] = (m.group(2), f)
    names = json.load(open(os.path.join(results_dir(), "claims_macros.json")))   # macro names only: the manuscript is not in this repository
    used = sorted(set(names["used"]) & set(defs))
    missing = names["missing"]
    out = ["# Claims registry (EXP-09)", "", "Every numeric macro used by the manuscript, its value and the file that defines it. Both files are generated from `results/*.json` by `src/make_outputs.py` / `src/make_outputs_v10.py`; none is typed by hand except where `make_outputs_v10.py` marks a transcribed GPU_HOST summary.", "", "| macro | value | defined in |", "|---|---|---|"]
    out += [f"| `\\{m}` | {defs[m][0]} | {defs[m][1]} |" for m in used]
    if missing: out += ["", "Undefined capitalised commands in main.tex (check): " + ", ".join(missing)]
    open(os.path.join(DOCS, "CLAIMS_REGISTRY.md"), "w").write("\n".join(out) + "\n")
