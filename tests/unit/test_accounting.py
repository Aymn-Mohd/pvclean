from pvclean import model
from pvclean.core.accounting import Ledger


def test_net_and_summary():
    l = Ledger(); l.revenue = 100.0
    l.mission(3, model.CONFIG); l.inspection(40, model.CONFIG)
    assert l.n_clean == 3 and l.n_missions == 1 and l.cost_clean == 12.0 and l.cost_mission == 10.0 and l.cost_insp == 20.0
    assert l.net == 58.0 and set(l.summary()) == {"revenue", "energy_kwh", "cost_clean", "cost_mission", "cost_insp", "n_clean", "n_missions"}
