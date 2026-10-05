import json
import math
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from mindcore.model import BUNDLED, Model, get_model
from mindcore.runtime import Runtime

ROOT = Path(__file__).parent.parent
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

SNIPPETS = [
    "param a = 1 +", "param a = if 1 then 2", "param a = b", "param a = 1 / 0", "group x",
    "param a = 1\ntrait t {\n  a ** 2\n}", "param a = 1\ntrait t {\n  zz += 1\n}", "param a = foo(1)", "param a = 1 $",
    "readout { x += 1 }", "def f(x) = x\nparam a = f(1, 2)", "def f(x, y) = x\nparam a = f(1)", "param a = (1 + 2",
]


def close(a, b):
    assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12), (a, b)


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    m = get_model()
    rng = random.Random(3)
    names = list(m.traits)
    personas = [{}] + [{n: s} for n in names for s in (-1, 0.5, 1)]
    personas += [{n: rng.uniform(-1, 1) for n in rng.sample(names, rng.randint(1, 15))} for _ in range(60)]
    now = [1_760_000_000.0]
    rt = Runtime(tmp_path_factory.mktemp("rt"), "s", clock=lambda: now[0])
    readouts = []
    for i in range(14):
        now[0] += [30, 900, 7200, 40000][i % 4]
        rt.interact(["praise", "danger", "flirt", "tool_failure", "warm_moment"][i % 5], 0.7, load=0.1 * (i % 5), commit_task=i % 2)
        env = rt._env().at(rt.sim_t)
        readouts.append({"inputs": rt.mind.readout_inputs(1, env, rt.mind.circ), "params": dict(rt.mind.P)})
    req = {"personas": personas, "readouts": readouts, "snippets": SNIPPETS}
    proc = subprocess.run(["node", str(ROOT / "tests/js/parity.cjs"), str(BUNDLED)], input=json.dumps(req), capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    return req, json.loads(proc.stdout)


def test_effective_params(run):
    req, res = run
    m = get_model()
    for persona, got in zip(req["personas"], res["effective"]):
        want = m.effective_params({}, persona)
        assert want.keys() == got.keys()
        for k in want:
            close(want[k], got[k])


def test_readouts(run):
    req, res = run
    m = get_model()
    for r, got in zip(req["readouts"], res["readouts"]):
        want = m.evaluate_readout(r["inputs"], r["params"])
        assert want.keys() == got.keys()
        for k in want:
            close(want[k], got[k])


def test_ui_metadata(run):
    _, res = run
    m = get_model()
    assert res["traits"] == m.trait_info()
    want = m.param_table()
    assert [r["key"] for r in want] == [r["key"] for r in res["table"]]
    for w, g in zip(want, res["table"]):
        assert (w["label"], w["group"], w["step"], w["min"], w["max"], w["visible"]) == (g["label"], g["group"], g["step"], g["min"], g["max"], g["visible"])
        close(w["default"], g["default"])


def test_error_messages_match(run):
    req, res = run
    for snippet, got in zip(req["snippets"], res["errors"]):
        try:
            Model().add(snippet).validate()
            want = None
        except ValueError as exc:
            want = str(exc)
        assert got == want, snippet
