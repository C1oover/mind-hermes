import json

import pytest

from mindcore.portable import (ImportErrorInvalid, export_params, export_state, import_params, import_state)
from mindcore.runtime import Runtime


def make(tmp_path, name):
    return Runtime(tmp_path / name, "s", lambda: 1_800_000_000.0)


def test_state_round_trip_between_runtimes(tmp_path):
    a = make(tmp_path, "a")
    a.interact(appraisal={"ew": 1.0})
    a.set_persona({"warmth": .4})
    b = make(tmp_path, "b")
    import_state(b, export_state(a))
    for key in ("mood", "arousal", "bond"):
        assert b.state()["raw"][key] == pytest.approx(a.state()["raw"][key], abs=1e-9)
    assert b.persona["warmth"] == .4


def test_bad_state_import_leaves_runtime_unchanged(tmp_path):
    a = make(tmp_path, "a")
    before = a.state()["raw"]["mood"]
    for bad in ("{nope", json.dumps({"schema": "other"}), json.dumps({"schema": "mind-hermes-state-v1"})):
        with pytest.raises(ImportErrorInvalid):
            import_state(a, bad)
    assert a.state()["raw"]["mood"] == before


def test_params_round_trip_and_validation(tmp_path):
    a = make(tmp_path, "a")
    key = sorted(a.params)[0]
    doc = json.loads(export_params(a))
    doc["params"][key] = a.params[key]
    assert key in import_params(a, json.dumps(doc))
    for bad in ({"zzz_unknown": 1}, {key: "x"}, {key: True}, {key: float("nan")}):
        with pytest.raises(ImportErrorInvalid):
            import_params(a, json.dumps({"schema": "mind-hermes-params-v1", "params": bad}))
