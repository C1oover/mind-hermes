from mindcore.persona import apply_persona, default_persona, effective_params, normalize_persona
from mindcore.tables import DEFAULTS


def test_defaults_and_bounds():
    assert all(value == 0 for value in default_persona().values())
    assert normalize_persona({"energy": 9, "unknown": .4})["energy"] == 1
    assert "unknown" not in normalize_persona({"unknown": .4})


def test_traits_change_params_not_readout():
    raw = {"mood": .2, "arousal": .4, "present": 1}
    assert apply_persona(raw, {"energy": .5}) == raw
    assert apply_persona(raw, {"energy": .5}) is not raw
    assert effective_params(DEFAULTS, {"energy": 1})["tb_arousal"] > DEFAULTS["tb_arousal"]
    assert effective_params(DEFAULTS, default_persona())["tb_arousal"] == DEFAULTS["tb_arousal"]
