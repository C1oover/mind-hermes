"""Hermes-independent runtime: wall-clock time, substepping, persistence, persona.

Sim time t is in minutes since local midnight of the day the state was created,
so Env.at(t) sees the real local hour of day. STATUS: written against mind.py and
engine.py as read from the repository; unverified until CI passes.
"""
import datetime
import json
import time
from pathlib import Path

from .engine import Env
from .mind import Mind
from .persona import apply_persona, default_persona, normalize_persona
from .tables import DEFAULTS

SCHEMA = "mind-hermes-state-v1"
MAX_GAP_MIN = 2880.0
SUBSTEP_MIN = 5.0
PRESENCE_GRACE_MIN = 5.0
EVENT_DT_MIN = 0.05
INPUT_KEYS = ("load", "commit_task", "commit_rel", "task_demand")
MIND_FIELDS = ("z", "boredom", "task_commitment", "sleep_pressure", "sleep_debt", "clock_phase", "arousal_phasic",
               "valence_reaction", "threat_trace", "surprise_trace", "adversity_trace", "novelty_avg", "away_min",
               "expected_gap", "prev_present", "since_warm", "habit", "budget", "weekly", "asleep", "res", "rate",
               "prev", "aStrain", "mStrain", "spillUsed", "circ", "mood_avg", "arousal_avg")


def safe_id(session_id):
    return "".join(ch for ch in str(session_id) if ch.isalnum() or ch in "-_")[:120] or "default"


def local_midnight(wall):
    d = datetime.datetime.fromtimestamp(wall)
    return d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp(), d.timetuple().tm_yday


class Runtime:
    def __init__(self, root, session_id="default", clock=time.time):
        self.root = Path(root).expanduser()
        self.sid = safe_id(session_id)
        self.clock = clock
        self.path = self.root / (self.sid + ".json")
        if not self.load():
            self.reset()

    def reset(self):
        now = self.clock()
        self.t0, doy = local_midnight(now)
        self.params = dict(DEFAULTS)
        self.params["start_doy"] = doy
        self.mind = Mind(self.params)
        self.persona = default_persona()
        self.sim_t = (now - self.t0) / 60.0
        self.last_seen = self.sim_t
        self._ensure_out()

    def _env(self):
        return Env(self.params)

    def _ensure_out(self):
        if not self.mind.out:
            present = 1 if (self.sim_t - self.last_seen) < PRESENCE_GRACE_MIN else 0
            self.mind.readout(present, self._env().at(self.sim_t), self.mind.circ)

    def advance(self):
        """Simulate idle time up to now; the user counts as present for a short grace period."""
        target = (self.clock() - self.t0) / 60.0
        t = max(self.sim_t, target - MAX_GAP_MIN)
        env = self._env()
        while target - t > 1e-9:
            dt = min(SUBSTEP_MIN, target - t)
            present = 1 if (t - self.last_seen) < PRESENCE_GRACE_MIN else 0
            self.mind.step(t, dt, {"present": present}, env.at(t))
            t += dt
        self.sim_t = max(self.sim_t, target)
        self._ensure_out()
        return self.sim_t

    def interact(self, code=None, intensity=1.0, appraisal=None, **inputs):
        """Advance to now, mark the user present, apply one short step carrying the event."""
        self.advance()
        self.last_seen = self.sim_t
        inp = {"present": 1}
        for key in INPUT_KEYS:
            if key in inputs and inputs[key] is not None:
                inp[key] = inputs[key]
        if code:
            inp["events"] = [(code, float(intensity))]
        if appraisal:
            inp["appraisal"] = dict(appraisal)
        self.mind.step(self.sim_t, EVENT_DT_MIN, inp, self._env().at(self.sim_t))
        self.sim_t += EVENT_DT_MIN
        return self.state()

    def state(self):
        raw = dict(self.mind.out)
        return {"raw": raw, "shown": apply_persona(raw, self.persona), "persona": dict(self.persona), "sim_t": self.sim_t}

    def set_persona(self, values):
        merged = dict(self.persona)
        merged.update(values or {})
        self.persona = normalize_persona(merged)
        return dict(self.persona)

    def snapshot(self):
        return {"schema": SCHEMA, "saved_at": self.clock(), "t0": self.t0, "sim_t": self.sim_t, "last_seen": self.last_seen,
                "params": self.params, "persona": self.persona, "mind": {k: getattr(self.mind, k) for k in MIND_FIELDS}}

    def save(self):
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.snapshot(), separators=(",", ":")), encoding="utf-8")
        tmp.replace(self.path)

    def load(self):
        if not self.path.exists():
            return False
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("schema") != SCHEMA:
                return False
            params = dict(DEFAULTS)
            params.update(data.get("params", {}))
            mind = Mind(params)
            for key in MIND_FIELDS:
                if key in data["mind"]:
                    setattr(mind, key, data["mind"][key])
            self.params, self.mind = params, mind
            self.t0 = float(data["t0"]); self.sim_t = float(data["sim_t"]); self.last_seen = float(data["last_seen"])
            self.persona = normalize_persona(data.get("persona"))
        except (OSError, ValueError, KeyError, TypeError):
            return False
        self._ensure_out()
        return True
