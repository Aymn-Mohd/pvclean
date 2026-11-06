"""Accounting of one simulated year."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class Ledger:
    """Running totals. net = revenue - cleaning, mission and inspection costs."""
    revenue: float = 0.0
    energy: float = 0.0
    cost_clean: float = 0.0
    cost_mission: float = 0.0
    cost_insp: float = 0.0
    n_clean: int = 0
    n_missions: int = 0

    def mission(self, rows: int, cfg: dict[str, Any]) -> None:
        """Books one mission of `rows` rows."""
        self.n_missions += 1; self.cost_mission += cfg["c_mission"]
        self.n_clean += rows; self.cost_clean += cfg["c_row"] * rows

    def inspection(self, n: int, cfg: dict[str, Any]) -> None:
        """Books one patrol of n rows."""
        self.cost_insp += cfg["c_mission"] + cfg["c_insp"] * n

    def summary(self) -> dict[str, Any]:
        """Annual outcomes."""
        return dict(revenue=self.revenue, energy_kwh=self.energy, cost_clean=self.cost_clean, cost_mission=self.cost_mission,
                    cost_insp=self.cost_insp, n_clean=self.n_clean, n_missions=self.n_missions)

    @property
    def net(self) -> float:
        """Revenue minus cleaning, mission and inspection costs."""
        return self.revenue - self.cost_clean - self.cost_mission - self.cost_insp
