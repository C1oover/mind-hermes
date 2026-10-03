from mindcore.persona import default_persona, normalize_persona, trait_effect, apply_persona


def test_defaults_and_bounds():
    assert all(value == 0 for value in default_persona().values())
    assert normalize_persona({"energy": 9, "unknown": .4})["energy"] == 1


def test_traits_apply_only_to_readout_copy():
    raw = {"mood": .2, "arousal": .4, "present": 1, "clock_phase": 15}
    shown = apply_persona(raw, {"energy": .5})
    assert raw == {"mood": .2, "arousal": .4, "present": 1, "clock_phase": 15}
    assert abs(shown["arousal"] - .56) < 1e-12
    assert shown["present"] == 1 and shown["clock_phase"] == 15


def test_signed_clamp():
    assert apply_persona({"mood": .99}, {"depressive_maniac": 1})["mood"] == 1
