import pytest

from mindcore.dsl import ModelError
from mindcore.model import Model


def val(expr, **scope):
    m = Model().add("param r = %s\n" % expr)
    return m.params["r"]


def test_if_then_else():
    assert val("if 2 > 1 then 10 else 20") == 10
    assert val("if 2 < 1 then 10 else 20") == 20
    assert val("1 + (if 1 == 1 then 2 else 3) * 2") == 5


def test_comparisons_and_logic():
    assert val("if 1 <= 1 and 2 >= 3 then 1 else 0") == 0
    assert val("if 1 != 1 or not 0 then 1 else 0") == 1
    assert val("if 3 > 2 and 2 > 1 then 1 else 0") == 1


def test_lazy_branches():
    assert val("if 1 then 5 else 1 / 0") == 5
    with pytest.raises(ModelError):
        val("if 0 then 5 else 1 / 0")


def test_conditions_in_traits_and_statements():
    m = Model().add("param a = 1\ntrait t {\n  a += if value > 0 then 2 * value else 0.5 * value\n}\n").validate()
    assert m.effective_params({"a": 1}, {"t": 1})["a"] == 3
    assert m.effective_params({"a": 1}, {"t": -1})["a"] == 0.5


def test_group_directive():
    m = Model().add('group "G1"\nparam a = 1 | label="A"\nparam b = 2 | group="G2"\n')
    assert [r["group"] for r in m.param_table()] == ["G1", "G2"]


def test_syntax_error_in_if():
    with pytest.raises(ModelError) as exc:
        val("if 1 then 2")
    assert ":1:" in str(exc.value)
