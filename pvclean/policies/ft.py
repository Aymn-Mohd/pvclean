"""FT: forecast-matched price-aware economic threshold."""
from __future__ import annotations
import numpy as np
from pvclean.core.robot import pack
from .base import Decision, Policy, State


class ForecastThreshold(Policy):
    """Same station estimate, production climatology, contract-aware gain, price forecast, rain gate, packing and access as the planner. A row is cleaned when its forecast
    net benefit over the next Hb days is non-negative: NB_i = sum_h [P_i(clean) - P_i(est_i)] v_h - c_row - c_mission / b."""
    name = "ft"

    def decide(self, s: State) -> Decision:
        cfg, d, p = s.cfg, s.d, self.params
        out = Decision(wanted=np.zeros(s.n, bool))
        rain_soon = s.rain_soon()
        if not rain_soon:
            Hb = p["Hb"]
            hh = (np.arange(d * 24, d * 24 + Hb * 24) % 8760 if s.wrap else
                  np.arange(d * 24, min(d * 24 + Hb * 24, 8760, cfg.get("d1", 365) * 24)))
            if len(hh):
                ndays = len(hh) / 24.0
                gain = s.gain(s.clim[hh])
                vf = s.forecast(hh)
                gtot = (gain * vf[None, :]).sum(1)
                nb = gtot - cfg["c_row"] - cfg["c_mission"] / p["b"]
                out.reason = "access_anticipation" if not ((nb >= 0) & s.avail).any() else "forecast_net_benefit"
                if p.get("antic"):
                    c = s.closing_soon()
                    if c is not None:
                        L, soon = c
                        nb = nb + np.where(soon, gtot / ndays * L, 0.0)
                out.wanted = nb >= 0
                due = np.where(out.wanted & s.avail)[0]
                due = due[np.argsort(-nb[due])]
                out.rows = pack(list(due), cfg)
                if s.dg is not None:
                    s.dg.update(vhat=float(vf.mean()), nb=nb.copy())
        if s.dg is not None:
            s.dg["rain_soon"] = bool(rain_soon)
        return out
