"""Message types for the engine interface (spec section 2)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional

Source = Literal["observed", "forecast", "computed"]
EventType = Literal["code", "free", "appraisal", "tool_outcome", "contact_bid_sent", "contact_bid_answered"]

CODES = ("tool_success", "tool_failure", "praise", "conflict", "joke", "flirt", "danger", "surprise", "warm_moment")


@dataclass
class Event:
    t_abs: float                      # epoch seconds, UTC
    type: EventType
    name: str = ""
    value: float = 1.0
    data: dict = field(default_factory=dict)  # appraisal vector / tool_outcome payload


@dataclass
class Input:
    t_abs: float
    present: bool = False
    load: float = 0.0
    commit_task: float = 0.0
    commit_rel: float = 0.0
    task_demand: float = 0.0
    events: list[Event] = field(default_factory=list)


@dataclass
class WorldValue:
    value: float | str | None = None
    source: Source = "computed"
    age_s: float = 0.0


@dataclass
class Bid:
    reason: str
    strength: float
    earliest_abs: float
    expires_abs: float
