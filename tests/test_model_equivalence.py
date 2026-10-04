import math
import random

from mindcore import persona_legacy as old
from mindcore.model import load_model
from mindcore.tables import DEFAULTS

M = load_model()


def same(a, b):
    assert a.keys() == b.keys()
    for k in a:
        assert math.isclose(a[k], b[k], rel_tol=1e-9, abs_tol=1e-12), (k, a[k], b[k])


def test_params_match_defaults():
    assert M.params == DEFAULTS


def test_trait_metadata_matches():
    assert list(M.traits) == list(old.TRAITS)
    for n, t in old.TRAITS.items():
        assert M.trait_info()[n] == {"label": t["label"], "group": t["group"], "help": t["help"]}


def test_single_traits_match_legacy():
    for name in old.TRAITS:
        for v in (-1, -0.5, 0.5, 1):
            same(M.effective_params(DEFAULTS, {name: v}), old.effective_params(DEFAULTS, {name: v}))


def test_random_personas_match_legacy():
    rng = random.Random(7)
    names = list(old.TRAITS)
    for _ in range(300):
        p = {n: rng.uniform(-1, 1) for n in rng.sample(names, rng.randint(1, 12))}
        same(M.effective_params(DEFAULTS, p), old.effective_params(DEFAULTS, p))
