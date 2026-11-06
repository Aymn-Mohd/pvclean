"""The quantity and timing decomposition of the difference between two policies."""
from __future__ import annotations
from typing import Any, Sequence
import numpy as np
from .intervals import paired


def decomp(A: dict[str, Any], B: dict[str, Any], vref: Sequence[float]) -> dict[str, Any]:
    """A minus B per seed. quantity = d_energy x v_ref, timing = d_revenue - quantity, with v_ref the policy-independent production-weighted mean contract value
    of the seed-year. Each part is the mean with a 95% paired t-interval; the residual of the accounting identity is reported."""
    A = {k: np.asarray(v, float) for k, v in A.items() if k != "params"}
    B = {k: np.asarray(v, float) for k, v in B.items() if k != "params"}
    v = np.asarray(vref, float)
    d_rev = A["revenue"] - B["revenue"]; d_e = A["energy_kwh"] - B["energy_kwh"]
    qty = d_e * v
    parts = dict(d_net=A["net"] - B["net"], d_revenue=d_rev, d_energy_mwh=d_e / 1000.0,
                 d_clean_cost=A["cost_clean"] - B["cost_clean"], d_mission_cost=A["cost_mission"] - B["cost_mission"],
                 d_row_cleanings=A["n_clean"] - B["n_clean"], d_missions=A["n_missions"] - B["n_missions"],
                 quantity=qty, timing=d_rev - qty)
    resid = parts["d_net"] - (d_rev - parts["d_clean_cost"] - parts["d_mission_cost"] - (A["cost_insp"] - B["cost_insp"]))
    out = {k: paired(x, np.zeros_like(x)) for k, x in parts.items()}
    out["identity_max_abs_residual"] = float(np.abs(resid).max())
    out["v_ref_mean"] = float(v.mean())
    return out
