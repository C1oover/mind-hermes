"""Minimal runtime snapshot (spec section 4). State only, no timeline."""
from __future__ import annotations
import json, os, tempfile
from dataclasses import dataclass, field, asdict


@dataclass
class Snapshot:
    model_version: str
    params_hash: str
    last_t_abs: float
    z: dict = field(default_factory=dict)
    scalars: dict = field(default_factory=dict)      # boredom, task_commitment, sleep_pressure, sleep_debt, clock_phase
    traces: dict = field(default_factory=dict)       # phasic, valence_reaction, threat, surprise, adversity, novelty_avg
    averages: dict = field(default_factory=dict)     # mood_avg, arousal_avg
    timing: dict = field(default_factory=dict)       # expected_gap, since_warm, away_min, prev_present
    habit: dict = field(default_factory=dict)
    budget: dict = field(default_factory=dict)       # impulse budgets (decay anchored at last_t_abs)
    weekly: list = field(default_factory=lambda: [0.0] * 168)
    controllers: dict = field(default_factory=dict)  # res, rate, prev
    strains: dict = field(default_factory=dict)      # aStrain, mStrain, spillUsed
    event_ring: list = field(default_factory=list)   # last ~200 events
    tool_rates: dict = field(default_factory=dict)   # per-tool success rate
    significant: list = field(default_factory=list)  # significant-event log


def save(snap: Snapshot, path: str) -> None:
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(asdict(snap), f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load(path: str, model_version: str) -> Snapshot | None:
    try:
        with open(path) as f:
            d = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if str(d.get("model_version", "")).split(".")[0] != model_version.split(".")[0]:
        return None
    return Snapshot(**d)
