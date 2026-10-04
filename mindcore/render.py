"""Configurable text rendering of the mind state for LLM context.

The shipped default (render_default.json) is used when the user has no config.
Override any key with a JSON file:

  1. path in env MIND_HERMES_RENDER_CONFIG, else
  2. <state_dir>/render.json

Only the keys present in the file override the defaults. Invalid files or
format strings fall back to the defaults instead of raising.

Modes: "auto" (dynamic, words only, shows just what stands out), "words", "numeric".
"""
import json
import os
from pathlib import Path

DEFAULT_FILE = Path(__file__).with_name("render_default.json")

ENV_VAR = "MIND_HERMES_RENDER_CONFIG"

DEFAULT_CONFIG = {
    # Wrapper around the rendered items. Placeholders: {state}
    "template": "[Mind state: {state}. Optional tone context only; not a diagnosis or an external fact.]",
    # Per item. Placeholders: {key} {label} {value} {word}
    "item_format": "{label}={value:.2f}",
    # Used instead of item_format when mode == "words".
    "word_item_format": "{label}: {word}",
    "separator": ", ",
    # "numeric", "words" or "auto"
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
    # mode "auto": {key: [[upper_bound, phrase, salience], ...]}. Empty phrase = unremarkable.
    # Only phrases with salience >= min_salience are shown, strongest first, capped at max_items.
    "traits": {},
    "max_items": 5,
    "min_salience": 0.3,
}


def _valid_bands(b):
    try:
        return [[float(x), str(w)] for x, w in b]
    except (TypeError, ValueError):
        return None


def _valid_traits(t):
    out = {}
    for k, bands in t.items():
        try:
            out[str(k)] = sorted([float(a), str(p), float(sal)] for a, p, sal in bands)
        except (TypeError, ValueError):
            continue
    return out


def merge_config(user, base=None):
    cfg = json.loads(json.dumps(base or DEFAULT_CONFIG))
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
        elif key == "traits" and isinstance(val, dict):
            cfg[key] = _valid_traits(val)
        elif key == "max_items" and isinstance(val, int) and not isinstance(val, bool):
            cfg[key] = max(0, val)
        elif key == "min_salience" and isinstance(val, (int, float)) and not isinstance(val, bool):
            cfg[key] = float(val)
        elif key == "field_bands" and isinstance(val, dict):
            out = {}
            for k, v in val.items():
                bands = _valid_bands(v)
                if bands:
                    out[str(k)] = sorted(bands)
            cfg[key] = out
    if cfg["mode"] not in ("numeric", "words", "auto"):
        cfg["mode"] = DEFAULT_CONFIG["mode"]
    if cfg["source"] not in ("shown", "raw"):
        cfg["source"] = DEFAULT_CONFIG["source"]
    return cfg


def default_config():
    """Shipped default (render_default.json) layered over the code defaults."""
    try:
        return merge_config(json.loads(DEFAULT_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return merge_config(None)


def load_config(state_dir=None, path=None):
    base = default_config()
    candidates = [path, os.environ.get(ENV_VAR)]
    if state_dir:
        candidates.append(Path(state_dir).expanduser() / "render.json")
    for cand in candidates:
        if not cand:
            continue
        p = Path(cand).expanduser()
        if p.is_file():
            try:
                return merge_config(json.loads(p.read_text(encoding="utf-8")), base)
            except (OSError, ValueError):
                break
    return base


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
    if cfg["mode"] == "auto":
        picked = []
        for key, bands in cfg["traits"].items():
            if key not in values:
                continue
            try:
                v = float(values[key])
            except (TypeError, ValueError):
                continue
            for bound, phrase, sal in bands:
                if v <= bound:
                    if phrase and sal >= cfg["min_salience"]:
                        picked.append((sal, phrase))
                    break
        picked.sort(key=lambda t: -t[0])
        text = cfg["separator"].join(p for _, p in picked[:cfg["max_items"]]) or cfg["empty"]
        return _fmt(cfg["template"], DEFAULT_CONFIG["template"], state=text)
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
