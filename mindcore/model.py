"""Model definition from .mind files (params, traits, resolve). Bundled files plus an optional user file override."""
import os
from collections import ChainMap
from pathlib import Path

from .dsl import Evaluator, ModelError, parse

BUNDLED = Path(__file__).parent / "model"
FILES = ("params.mind", "traits.mind", "resolve.mind", "readout.mind")


class Model:
    def __init__(self):
        self.params, self.meta, self.funcs, self.traits, self.resolve, self.readout = {}, {}, {}, {}, [], {}
        self.ev = Evaluator(self.funcs)

    def add(self, text, origin="<model>"):
        prog = parse(text, origin)
        for d in prog["defs"]:
            self.funcs[d.name] = d
        for name, expr, meta, line, org in prog["params"]:
            self.params[name] = self.ev.eval(expr, ChainMap({}, self.params), org)
            self.meta[name] = meta
        for t in prog["traits"]:
            self.traits[t["name"]] = t
        self.resolve.extend(prog["resolve"])
        for st in prog["readout"]:
            if st[1] != "=":
                raise ModelError("readout statements must use =", st[3], st[4])
            self.readout[st[0]] = st
        return self

    def validate(self):
        for stmts in [t["stmts"] for t in self.traits.values()] + [self.resolve]:
            for name, _op, _e, line, origin in stmts:
                if name not in self.params:
                    raise ModelError("unknown parameter %r" % name, line, origin)
        return self

    def trait_info(self):
        return {n: {"label": t["meta"].get("label", n), "group": t["meta"].get("group", ""), "help": t["meta"].get("help", "")}
                for n, t in self.traits.items()}

    def default_persona(self):
        return {n: 0.0 for n in self.traits}

    def normalize_persona(self, persona=None):
        out = self.default_persona()
        for k, v in (persona or {}).items():
            if k in out:
                try:
                    out[k] = max(-1.0, min(1.0, float(v)))
                except (TypeError, ValueError):
                    pass
        return out

    def effective_params(self, base, persona):
        E = dict(self.params)
        E.update(base)
        persona = self.normalize_persona(persona)
        for name, t in self.traits.items():
            value = persona[name]
            if not value:
                continue
            scope = ChainMap({"value": value}, E)
            for nm, op, expr, line, origin in t["stmts"]:
                E[nm] = self.ev.apply(op, E[nm], self.ev.eval(expr, scope, origin), line, origin)
        for k, m in self.meta.items():
            if "min" in m:
                E[k] = max(m["min"], E[k])
            if "max" in m:
                E[k] = min(m["max"], E[k])
        for nm, op, expr, line, origin in self.resolve:
            E[nm] = self.ev.apply(op, E[nm], self.ev.eval(expr, E, origin), line, origin)
        return E


def _evaluate_readout(self, inputs, params):
    """Run the readout block: names starting with _ are temporaries, everything else is returned."""
    out = {}
    scope = ChainMap(out, inputs, params)
    for name, _op, expr, _line, origin in self.readout.values():
        out[name] = self.ev.eval(expr, scope, origin)
    return {k: v for k, v in out.items() if not k.startswith("_")}


Model.evaluate_readout = _evaluate_readout


def load_model(user_path=None):
    m = Model()
    for f in FILES:
        p = BUNDLED / f
        if p.exists():
            m.add(p.read_text(encoding="utf-8"), str(f))
    if user_path and Path(user_path).exists():
        m.add(Path(user_path).read_text(encoding="utf-8"), str(user_path))
    return m.validate()


def user_model_path():
    env = os.environ.get("MIND_HERMES_MODEL")
    return Path(env).expanduser() if env else Path.home() / ".hermes" / "mind-hermes" / "model.mind"


_cache = None


def get_model():
    global _cache
    if _cache is None:
        _cache = load_model(user_model_path())
    return _cache


def reload_model():
    global _cache
    _cache = None
    return get_model()
