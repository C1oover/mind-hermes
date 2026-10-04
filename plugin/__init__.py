"""Hermes Agent plugin: thin wrapper over mindcore.runtime.Runtime."""
import os

from mindcore.render import load_config, render
from mindcore.runtime import Runtime, safe_id

STATE_DIR = os.environ.get("MIND_HERMES_STATE_DIR", "~/.hermes/mind-hermes")
RUNTIMES = {}
EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string", "description": "Built-in event code (see mindcore/tables.py CODES)."},
        "intensity": {"type": "number", "minimum": -1, "maximum": 1, "default": 1},
        "appraisal": {"type": "object", "description": "Direct appraisal values: eg, n, ew, es, ep, el, th, succ, fail."},
        "load": {"type": "number", "minimum": 0, "maximum": 1},
        "commit_task": {"type": "number", "minimum": 0, "maximum": 1},
        "commit_rel": {"type": "number", "minimum": 0, "maximum": 1},
        "task_demand": {"type": "number", "minimum": 0, "maximum": 1},
    },
}
PERSONA_SCHEMA = {"type": "object", "properties": {"values": {"type": "object", "description": "Trait values in [-1, 1]; omitted traits are kept."}}, "required": ["values"]}
EMPTY = {"type": "object", "properties": {}}


def runtime(session_id="default"):
    sid = safe_id(session_id)
    if sid not in RUNTIMES:
        RUNTIMES[sid] = Runtime(STATE_DIR, sid)
    return RUNTIMES[sid]


def mind_event(session_id="default", **kw):
    r = runtime(session_id)
    out = r.interact(kw.get("code"), kw.get("intensity", 1.0), kw.get("appraisal"), **{k: kw.get(k) for k in ("load", "commit_task", "commit_rel", "task_demand")})
    r.save()
    return out


def mind_state(session_id="default", **kw):
    r = runtime(session_id)
    r.advance()
    r.save()
    return r.state()


def mind_persona(session_id="default", values=None, **kw):
    r = runtime(session_id)
    out = r.set_persona(values)
    r.save()
    return {"persona": out}


def mind_reset(session_id="default", **kw):
    r = runtime(session_id)
    r.reset()
    r.save()
    return {"ok": True}


def pre_llm_call(session_id="default", **kw):
    r = runtime(session_id)
    state = r.interact()
    r.save()
    return {"context": render(state, load_config(STATE_DIR))}


def on_session_start(session_id="default", **kw):
    runtime(session_id)


def on_session_end(session_id="default", **kw):
    r = runtime(session_id)
    r.advance()
    r.save()


def register(ctx):
    ctx.register_tool(name="mind_event", toolset="mind_hermes", schema=EVENT_SCHEMA, handler=mind_event, description="Record a mind-model event; returns raw and persona-adjusted state.")
    ctx.register_tool(name="mind_state", toolset="mind_hermes", schema=EMPTY, handler=mind_state, description="Get the current mind state.")
    ctx.register_tool(name="mind_persona", toolset="mind_hermes", schema=PERSONA_SCHEMA, handler=mind_persona, description="Set expression-layer persona traits.")
    ctx.register_tool(name="mind_reset", toolset="mind_hermes", schema=EMPTY, handler=mind_reset, description="Reset this session's mind state.")
    ctx.register_hook("pre_llm_call", pre_llm_call)
    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("on_session_end", on_session_end)
