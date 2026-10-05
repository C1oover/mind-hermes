import json
import math
from pathlib import Path

from mindcore.model import get_model, load_model
from mindcore.tables import DEFAULTS

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "html_param_defs.json").read_text())


def test_param_table_matches_original_ui_definitions():
    table = load_model().param_table()
    assert [r["key"] for r in table] == [row[0] for row in FIXTURE]
    for r, (key, label, default, step, group) in zip(table, FIXTURE):
        assert (r["label"], r["group"]) == (label, group), key
        assert math.isclose(r["default"], default, abs_tol=1e-12), key
        assert (r["step"] or 0.01) == step, key


def test_defaults_unchanged_and_every_param_has_label():
    m = load_model()
    assert m.params == DEFAULTS
    assert all(r["label"] and r["group"] for r in m.param_table())
    assert get_model().param_table()[0]["key"] == "speed_fast"
