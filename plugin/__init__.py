"""Hermes Agent plugin for the Mind ODE model.

Install this directory under ~/.hermes/plugins/mind-hermes/ and ensure the
repository root is importable (or copy mindcore alongside this plugin).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from mindcore import DEFAULTS, Env, Mind, apply_persona, default_persona, normalize_persona

PLUGIN_DIR = Path(__file__).resolve().parent
STATE_ROOT = Path(os.environ.get("MIND_HERMES_STATE_DIR", "~/.hermes/mind-hermes")).expanduser()
MAX_DT_MINUTES = 180.0

EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string", "description": "Built-in event code such as tool_success, tool_failure, threat, novelty, warmth."},
        "intensity": {"type": "number", "minimum": -1, "maximum": 1, "default": 1},
        "appraisal": {"type": "object", "description": "Optional direct appraisal map: eg, n, ew, es, ep, el, th, succ, fail."},
        "present": {"type": "number", "minimum": 0, "maximum": 1, "description": "Whether the user is present during this interval."},
        "load": {"type": "number", "minimum": 0, "maximum": 1},
        "commit_task": {"type": "number", "minimum": 0, "maximum": 1},
        "commit_rel": {"type": "number", "minimum": 0, "maximum": 1},
        "task_demand": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "additionalProperties": False,
}
PERSONA_SCHEMA = {"type": "object", "properties": {"values": {"type": "object", "description": "Trait values in [-1, 1]. Unspecified traits are preserved."}}, "required": ["values"]}


def _safe_session(session_id):
    return "".join(ch for ch in str(session_id) if ch.isalnum() or ch in "-_")[:120] or "default"


def _path(session_id):
    return STATE_ROOT / ("%s.json" % _safe_session(session_id))


def _now():
    return time.time()


def _make_runtime():
    params = dict(DEFAULTS)
    return {"params": params, "mind": Mind(params), "persona": default_persona(), "last_wall": _now(), "sim_t": 0.0}


class Store:
    def __init__(self):
        self.runtimes = {}

    def get(self, session_id):
        sid = _safe_session(session_id)
        if sid not in self.runtimes:
            self.runtimes[sid] = _make_runtime()
        return self.runtimes[sid]

    def advance(self, session_id, inp=None):
        r = self.get(session_id)
        wall = _now(); elapsed = max(0.0, min(MAX_DT_MINUTES, (wall - r["last_wall"]) / 60.0))
        r["last_wall"] = wall
        if elapsed:
            env = Env(r["params"])
            r["mind"].step(r["sim_t"], elapsed, inp or {}, env.at(r["sim_t"]))
            r["sim_t"] += elapsed
        return r

    def snapshot(self, session_id):
        r = self.get(session_id); m = r["mind"]
        return {"schema": "mind-hermes-state-v1", "saved_at": _now(), "sim_t": r["sim_t"], "last_wall": r["last_wall"],
                "params": r["params"], "persona": r["persona"], "mind": {"z": m.z, "boredom": m.boredom, "task_commitment": m.task_commitment,
                "sleep_pressure": m.sleep_pressure, "sleep_debt": m.sleep_debt, "clock_phase": m.clock_phase, "arousal_phasic": m.arousal_phasic,
                "valence_reaction": m.valence_reaction, "threat_trace": m.threat_trace, "surprise_trace": m.surprise_trace,
                "adversity_trace": m.adversity_trace, "novelty_avg": m.novelty_avg, "away_min": m.away_min, "expected_gap": m.expected_gap,
                "prev_present": m.prev_present, "since_warm": m.since_warm, "habit": m.habit, "budget": m.budget, "weekly": m.weekly,
                "asleep": m.asleep, "res": m.res, "rate": m.rate, "prev": m.prev, "aStrain": m.aStrain, "mStrain": m.mStrain,
                "spillUsed": m.spillUsed, "circ": m.circ, "mood_avg": m.mood_avg, "arousal_avg": m.arousal_avg}}

    def save(self, session_id):
        STATE_ROOT.mkdir(parents=True, exist_ok=True)
        target = _path(session_id); temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(self.snapshot(session_id), separators=(",", ":")), encoding="utf-8")
        temp.replace(target)

    def load(self, session_id):
        target = _path(session_id)
        if not target.exists():
            return self.get(session_id)
        data = json.loads(target.read_text(encoding="utf-8"))
        if data.get("schema") != "mind-hermes-state-v1":
            raise ValueError("unsupported mind state schema")
        params = dict(DEFAULTS); params.update(data.get("params", {}))
        m = Mind(params)
        for key, value in data["mind"].items():
            setattr(m, key, value)
        r = {"params": params, "mind": m, "persona": normalize_persona(data.get("persona")),
             "last_wall": float(data.get("last_wall", _now())), "sim_t": float(data.get("sim_t", 0))}
        self.runtimes[_safe_session(session_id)] = r
        return r


STORE = Store()


def _session_from(args):
    return args.get("session_id", "default") if isinstance(args, dict) else "default"


def _state_payload(session_id, advance=True):
    r = STORE.advance(session_id) if advance else STORE.get(session_id)
    raw = dict(r["mind"].out)
    shown = apply_persona(raw, r["persona"])
    return {"raw": raw, "shown": shown, "persona": r["persona"], "sim_t": r["sim_t"]}


def mind_event(**kwargs):
    session_id = kwargs.pop("session_id", "default")
    inp = {key: kwargs[key] for key in ("present", "load", "commit_task", "commit_rel", "task_demand") if key in kwargs}
    if kwargs.get("code"):
        inp["events"] = [(kwargs["code"], float(kwargs.get("intensity", 1)))]
    if kwargs.get("appraisal"):
        inp["appraisal"] = kwargs["appraisal"]
    r = STORE.advance(session_id, inp)
    STORE.save(session_id)
    return _state_payload(session_id, advance=False)


def mind_state(**kwargs):
    session_id = kwargs.get("session_id", "default")
    result = _state_payload(session_id)
    STORE.save(session_id)
    return result


def mind_persona(**kwargs):
    session_id = kwargs.get("session_id", "default")
    r = STORE.get(session_id)
    r["persona"].update(normalize_persona({**r["persona"], **kwargs.get("values", {})}))
    STORE.save(session_id)
    return {"persona": r["persona"]}


def mind_reset(**kwargs):
    session_id = kwargs.get("session_id", "default")
    STORE.runtimes[_safe_session(session_id)] = _make_runtime()
    STORE.save(session_id)
    return {"ok": True, "session_id": _safe_session(session_id)}


def pre_llm_call(session_id="default", **kwargs):
    state = _state_payload(session_id)
    shown = state["shown"]
    fields = ("mood", "arousal", "stress", "certainty", "seeking", "play", "bond", "missing_user", "sleep_pressure", "anxiety", "determination")
    compact = ", ".join("%s=%.2f" % (key, shown.get(key, 0)) for key in fields)
    return {"context": "[Mind state: %s. Use this as optional tone context; do not claim it is a diagnosis or an external fact.]" % compact}


def on_session_start(session_id="default", **kwargs):
    try:
        STORE.load(session_id)
    except Exception:
        STORE.get(session_id)


def on_session_end(session_id="default", **kwargs):
    STORE.advance(session_id)
    STORE.save(session_id)


def register(ctx):
    ctx.register_tool(name="mind_event", toolset="mind_hermes", schema=EVENT_SCHEMA, handler=mind_event,
                      description="Record a mind-model event and return raw and personality-adjusted state.")
    ctx.register_tool(name="mind_state", toolset="mind_hermes", schema={"type": "object", "properties": {}}, handler=mind_state,
                      description="Get the current mind-model state.")
    ctx.register_tool(name="mind_persona", toolset="mind_hermes", schema=PERSONA_SCHEMA, handler=mind_persona,
                      description="Set expression-layer personality trait values.")
    ctx.register_tool(name="mind_reset", toolset="mind_hermes", schema={"type": "object", "properties": {}}, handler=mind_reset,
                      description="Reset the current session's mind state.")
    ctx.register_hook("pre_llm_call", pre_llm_call)
    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("on_session_end", on_session_end)
