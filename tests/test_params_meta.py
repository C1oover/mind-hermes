import ast
import math
import re
from pathlib import Path

from mindcore.model import get_model, load_model
from mindcore.tables import DEFAULTS


def html_rows():
    html = (Path(__file__).parent.parent / "mind_sandbox.html").read_text(encoding="utf-8")
    rows = {}
    for g, arr in re.findall(r"def\('([^']+)',(\[\[.*?\]\])\);", html):
        for r in ast.literal_eval(arr):
            rows[r[0]] = (g, r[1], r[2], r[3] if len(r) > 3 else None)
    return rows


def test_param_table_matches_html_definitions():
    table = {r["key"]: r for r in load_model().param_table()}
    rows = html_rows()
    assert len(rows) > 100
    for k, (g, label, d, step) in rows.items():
        r = table[k]
        assert (r["group"], r["label"]) == (g, label), k
        assert math.isclose(r["default"], d, abs_tol=1e-12) and r["step"] == step, k


def test_defaults_unchanged_and_every_param_has_label():
    m = load_model()
    assert m.params == DEFAULTS
    assert all(r["label"] and r["group"] for r in m.param_table())
    assert get_model().param_table()[0]["key"] == "speed_fast"
