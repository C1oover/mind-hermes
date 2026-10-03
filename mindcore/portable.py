"""Import/export of full state and of parameters only, as validated JSON text."""
import json
import numbers

from .runtime import SCHEMA
from .tables import DEFAULTS

MAX_BYTES = 2_000_000
PARAMS_SCHEMA = "mind-hermes-params-v1"


class ImportErrorInvalid(ValueError):
    pass


def export_state(rt):
    return json.dumps(rt.snapshot(), indent=2)


def import_state(rt, text):
    """Replace the runtime's state with an exported snapshot. Leaves rt unchanged on any error."""
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise ImportErrorInvalid("file too large")
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise ImportErrorInvalid("not valid JSON") from exc
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ImportErrorInvalid("wrong or missing schema")
    if not all(k in data for k in ("t0", "sim_t", "last_seen", "mind")):
        raise ImportErrorInvalid("missing fields")
    backup = rt.path.read_text(encoding="utf-8") if rt.path.exists() else None
    rt.root.mkdir(parents=True, exist_ok=True)
    rt.path.write_text(text, encoding="utf-8")
    if not rt.load():
        if backup is None:
            rt.path.unlink()
        else:
            rt.path.write_text(backup, encoding="utf-8")
            rt.load()
        raise ImportErrorInvalid("state could not be loaded")
    rt.save()
    return rt.state()


def export_params(rt):
    return json.dumps({"schema": PARAMS_SCHEMA, "params": rt.params}, indent=2)


def import_params(rt, text):
    """Apply known numeric parameters; unknown keys and non-numbers are rejected, not ignored."""
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise ImportErrorInvalid("file too large")
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise ImportErrorInvalid("not valid JSON") from exc
    if not isinstance(data, dict) or data.get("schema") != PARAMS_SCHEMA or not isinstance(data.get("params"), dict):
        raise ImportErrorInvalid("wrong or missing schema")
    new = data["params"]
    for key, val in new.items():
        if key not in DEFAULTS:
            raise ImportErrorInvalid("unknown parameter: %s" % key)
        if isinstance(val, bool) or not isinstance(val, numbers.Real) or val != val or abs(val) == float("inf"):
            raise ImportErrorInvalid("parameter %s must be a finite number" % key)
    rt.params.update(new)
    rt.save()
    return sorted(new)
