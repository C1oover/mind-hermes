import math

import pytest

from mindcore.dsl import ModelError
from mindcore.model import Model, get_model
from mindcore.runtime import Runtime

CODES = ["praise", "tool_failure", "danger", "flirt", "warm_moment", "joke", "conflict", "surprise", "tool_success"]


def test_readouts_match_legacy_over_simulated_days(tmp_path):
    now = [1_760_000_000.0]
    rt = Runtime(tmp_path, "s", clock=lambda: now[0])
    gaps = [30, 600, 3600, 40000, 90, 7200, 20000, 300, 86400, 45]
    checked = 0
    for i in range(30):
        now[0] += gaps[i % len(gaps)]
        rt.interact(CODES[i % len(CODES)], 0.5 + (i % 3) * 0.3, load=0.2 * (i % 4), commit_task=i % 2)
        env = rt._env().at(rt.sim_t)
        new = rt.mind.out
        rt.mind.readout_legacy(1, env, rt.mind.circ)
        old = dict(rt.mind.out)
        rt.mind.readout(1, env, rt.mind.circ)
        assert rt.mind.out.keys() == old.keys()
        for k in old:
            assert math.isclose(rt.mind.out[k], old[k], rel_tol=1e-9, abs_tol=1e-12), (k, rt.mind.out[k], old[k])
        checked += 1
    assert checked == 30 and "desire_expressed" in rt.mind.out


def test_user_readout_override_and_new_output():
    m = Model().add("param a = 1\nreadout {\n  x = a * 2\n  _t = x + 1\n  y = _t * 3\n}\n")
    assert m.evaluate_readout({}, m.params) == {"x": 2.0, "y": 9.0}
    m.add("readout {\n  x = a * 10\n}\n", "user.mind")
    assert m.evaluate_readout({}, m.params) == {"x": 10.0, "y": 33.0}


def test_readout_requires_plain_assignment():
    with pytest.raises(ModelError):
        Model().add("param a = 1\nreadout {\n  x += 1\n}\n")


def test_bundled_model_has_readouts():
    assert "efficiency" in get_model().readout
