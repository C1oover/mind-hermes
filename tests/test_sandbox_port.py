import time

from mindcore.persona import TRAITS, effective_params
from mindcore.runtime import Runtime
from mindcore.tables import DEFAULTS


def test_runtime_event_and_persona(tmp_path):
    r = Runtime(tmp_path, "t", clock=lambda: 1_700_000_000.0)
    out = r.interact("praise", 1.0, load=0.2)
    assert 0.0 <= out["raw"]["arousal"] <= 1.0
    assert -1.0 <= out["raw"]["mood"] <= 1.0
    r.set_persona({"playful": 1.0, "depressive_manic": -1.0})
    assert r.params["tb_play"] > 0 and r.params["tb_mood"] < 0
    r.save()
    r2 = Runtime(tmp_path, "t", clock=lambda: 1_700_000_600.0)
    assert r2.persona["playful"] == 1.0
    assert r2.advance() > 0


def test_traits_and_overrides():
    assert len(TRAITS) == 39
    p = effective_params(DEFAULTS, {"contentment_lock": 1.0, "uninhibited": 1.0, "prudishness": 1.0})
    assert p["floor_mood"] == 1.0 and p["cap_inh"] < 0.1 and p["lust_gate"] < 1.0
