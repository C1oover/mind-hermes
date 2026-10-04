import pytest

from mindcore.dsl import ModelError
from mindcore.model import Model


def build(text):
    return Model().add(text, "t.mind").validate()


def test_all_assignment_operators():
    m = build('param a = 2\nparam b = 3\ntrait t | label="T" {\n  a += 1 * value\n  b *= 2\n  a -= 0.5\n  b /= 4\n}\n')
    out = m.effective_params({"a": 2, "b": 3}, {"t": 1})
    assert out["a"] == 2.5 and out["b"] == 1.5


def test_plain_assignment_and_precedence():
    m = build("param a = 1\nparam b = 0\ntrait t {\n  b = 2 + 3 * -value\n  a = (a + 1) * 4\n}\n")
    out = m.effective_params({"a": 1, "b": 0}, {"t": 1})
    assert out["b"] == -1 and out["a"] == 8


def test_functions_with_defaults():
    m = build("def f(x, k=3) = x * k\nparam a = f(2)\nparam c = f(2, 5)\n")
    assert m.params["a"] == 6 and m.params["c"] == 10


def test_min_max_clamp_and_resolve():
    m = build("param a = 1 | min=0\nparam g = 2\ntrait t {\n  a -= 5 * value\n}\nresolve {\n  g *= 3\n}\n")
    out = m.effective_params({"a": 1, "g": 2}, {"t": 1})
    assert out["a"] == 0 and out["g"] == 6


def test_zero_valued_traits_skipped():
    m = build("param a = 1\ntrait t {\n  a += 5\n}\n")
    assert m.effective_params({"a": 1}, {"t": 0})["a"] == 1


def test_user_override_replaces_definition():
    m = build("param a = 1\ntrait t {\n  a += 1\n}\n")
    m.add("trait t {\n  a += 10\n}\n", "user.mind")
    assert m.effective_params({"a": 1}, {"t": 1})["a"] == 11


@pytest.mark.parametrize("text,line", [("param a = 1\nparam b = (\n", 2), ("param a = 1\ntrait t {\n  zz += 1\n}\n", 3),
                                        ("param a = 1 / 0\n", 1), ("param a = nope\n", 1), ("param a = 1 $\n", 1)])
def test_errors_have_line_numbers(text, line):
    with pytest.raises(ModelError) as exc:
        build(text)
    assert ":%d:" % line in str(exc.value)
