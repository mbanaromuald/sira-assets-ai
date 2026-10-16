import os, tempfile
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
from core import db, agents
from core.finance import schedule, simulate
from core.matching import run_matching, summary
from core.maintenance import analyse

def test_finance():
    s = schedule(1_200_000, 4, "lineaire"); assert abs(s[12] - 900_000) < 1 and s[-1] == 0
    d = schedule(1_000_000, 5, "degressif"); assert d[-1] == 0 and abs(d[12] - 650_000) < 1
    assert simulate(1e6, 5, "lineaire").dotation.sum() == 1_000_000

def test_pipeline():
    db.init_db(); a = db.load("actifs"); assert len(a) == 320
    res = run_matching(db.sample_inventory(), a); s = summary(res)
    assert s["taux_auto"] > 85 and s["parfait"] > 150
    r = analyse(db.load("v_actifs"), db.load("maintenance")); assert "recommandation" in r
    assert agents.ask("VNC totale des serveurs de la zone Ouest")["df"] is not None
    assert agents.ask("véhicules dont les réparations dépassent 60%")["agent"].startswith("Agent Maintenance")

def test_sql_guard():
    import pytest
    with pytest.raises(ValueError): agents.safe_sql("DROP TABLE actifs")

def test_partial_count_scope():
    a = db.load("actifs"); f = db.sample_inventory(); f = f[f.agence == "Yaoundé Bastos"]
    full, part = summary(run_matching(f, a, scope=False)), summary(run_matching(f, a, scope=True))
    assert part["absents"] < full["absents"] / 5
