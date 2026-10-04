"""Configurable text rendering of the mind state for LLM context.

All snippets (wrapper template, per-item format, labels, value-to-word bands)
live in DEFAULT_CONFIG and can be overridden with a JSON file:

  1. path in env MIND_HERMES_RENDER_CONFIG, else
  2. <state_dir>/render.json

Only the keys present in the file override the defaults. Invalid files or
format strings fall back to the defaults instead of raising.
"""
import json
import os
from pathlib import Path

ENV_VAR = "MIND_HERMES_RENDER_CONFIG"

DEFAULT_CONFIG = {
    # Wrapper around the rendered items. Placeholders: {state}
    "template": "[Mind state: {state}. Optional tone context only; not a diagnosis or an external fact.]",
    # Per item. Placeholders: {key} {label} {value} {word}
    "item_format": "{label}={value:.2f}",
    # Used instead of item_format when mode == "words".
    "word_item_format": "{label}: {word}",
    "separator": ", ",
    # "numeric" or "words"
    "mode": "numeric",
    # "shown" (persona-adjusted) or "raw"
    "source": "shown",
    "fields": ["mood", "arousal", "stress", "certainty", "seeking", "play", "bond",
               "missing_user", "sleep_pressure", "anxiety", "determination"],
    # Optional display names per field key.
    "labels": {},
    # [[upper_bound, word], ...] sorted ascending; first bound >= value wins.
    "bands": [[-0.5, "very low"], [-0.15, "low"], [0.15, "neutral"], [0.5, "elevated"], [1e9, "high"]],
    # Per-field band overrides, same shape as bands.
    "field_bands": {},
    # Text used when no fields are available.
    "empty": "no data",
}


def _valid_bands(b):
    try:
        return [[float(x), str(w)] for x, w in b]
    except (TypeError, ValueError):
        return None


def merge_config(user):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if not isinstance(user, dict):
        return cfg
    for key, val in user.items():
        if key not in cfg:
            continue
        base = cfg[key]
        if isinstance(base, str) and isinstance(val, str):
            cfg[key] = val
        elif key == "fields" and isinstance(val, list):
            cfg[key] = [str(v) for v in val]
        elif key == "labels" and isinstance(val, dict):
            cfg[key] = {str(k): str(v) for k, v in val.items()}
        elif key == "bands":
            bands = _valid_bands(val)
            if bands:
                cfg[key] = sorted(bands)
        elif key == "field_bands" and isinstance(val, dict):
            out = {}
            for k, v in val.items():
                bands = _valid_bands(v)
                if bands:
                    out[str(k)] = sorted(bands)
            cfg[key] = out
    if cfg["mode"] not in ("numeric", "words"):
        cfg["mode"] = DEFAULT_CONFIG["mode"]
    if cfg["source"] not in ("shown", "raw"):
        cfg["source"] = DEFAULT_CONFIG["source"]
    return cfg


def load_config(state_dir=None, path=None):
    candidates = [path, os.environ.get(ENV_VAR)]
    if state_dir:
        candidates.append(Path(state_dir).expanduser() / "render.json")
    for cand in candidates:
        if not cand:
            continue
        p = Path(cand).expanduser()
        if p.is_file():
            try:
                return merge_config(json.loads(p.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                break
    return merge_config(None)


def word_for(value, bands):
    for bound, word in bands:
        if value <= bound:
            return word
    return bands[-1][1] if bands else ""


def _fmt(template, fallback, **kw):
    try:
        return template.format(**kw)
    except (KeyError, IndexError, ValueError):
        return fallback.format(**kw)


def render(state, config=None):
    """Render a Runtime.state() dict (or a plain value dict) to a context string."""
    cfg = config or merge_config(None)
    values = state.get(cfg["source"], state) if isinstance(state, dict) and cfg["source"] in state else state
    items = []
    word_mode = cfg["mode"] == "words"
    item_fmt = cfg["word_item_format"] if word_mode else cfg["item_format"]
    fallback = DEFAULT_CONFIG["word_item_format"] if word_mode else DEFAULT_CONFIG["item_format"]
    for key in cfg["fields"]:
        raw = values.get(key, 0.0)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = 0.0
        bands = cfg["field_bands"].get(key, cfg["bands"])
        items.append(_fmt(item_fmt, fallback, key=key, label=cfg["labels"].get(key, key),
                          value=value, word=word_for(value, bands)))
    text = cfg["separator"].join(items) if items else cfg["empty"]
    return _fmt(cfg["template"], DEFAULT_CONFIG["template"], state=text)
