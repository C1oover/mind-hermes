import pytest
from mindcore.engine import Env
from mindcore.mind import Mind
from mindcore.runtime import Runtime, PRESENCE_GRACE_MIN


def test_idle_advance_matches_manual_one_minute_stepping(tmp_path):
    now = [1_800_000_000.0]
    r = Runtime(tmp_path, "eq", lambda: now[0])
    ref = Mind(dict(r.params))
    env = Env(r.params)
    start, last_seen = r.sim_t, r.last_seen
    ref.readout(1, env.at(start), ref.circ)
    now[0] += 120 * 60
    r.advance()
    for i in range(120):
        t = start + i
        ref.step(t, 1.0, {"present": 1 if (t - last_seen) < PRESENCE_GRACE_MIN else 0}, env.at(t))
    for key in ("mood", "arousal", "sleep_pressure", "bond", "dominance"):
        assert r.mind.out[key] == pytest.approx(ref.out[key], abs=1e-9), key
