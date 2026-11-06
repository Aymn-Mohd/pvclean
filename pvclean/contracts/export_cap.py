"""Fixed tariff with an export cap."""
from __future__ import annotations
from .fixed import FixedTariff


class ExportCap(FixedTariff):
    """The tariff, with plant export limited to export_cap_frac of inverter capacity."""
    name = "capped"
    capped = True
