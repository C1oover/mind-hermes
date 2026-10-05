import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from mindcore.model import get_model

ROOT = Path(__file__).parent.parent
spec = importlib.util.spec_from_file_location("build_html", ROOT / "tools" / "build_html.py")
build_html = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_html)
HAS_NODE = shutil.which("node") is not None


def harness():
    proc = subprocess.run(["node", str(ROOT / "tests/js/html_harness.cjs"), str(ROOT / "mind_sandbox.html")], capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_html_embeds_current_model():
    text = (ROOT / "mind_sandbox.html").read_text(encoding="utf-8")
    assert build_html.build(text) == text, "run: python tools/build_html.py"


@pytest.mark.skipif(not HAS_NODE, reason="node not installed")
def test_html_script_runs_and_matches_model():
    out = harness()
    m = get_model()
    assert [d[0] for d in out["defs"]] == list(m.params)
    assert out["traits"] == list(m.traits)
    assert out["sim"] and out["sim"][0]["W"] > 0


@pytest.mark.skipif(not HAS_NODE, reason="node not installed")
def test_html_trait_effect_text():
    fx = harness()["fx"]
    assert all(fx[n] for n in get_model().traits)
    assert fx["energy"][0] == "tb_arousal += 0.9 * value"
