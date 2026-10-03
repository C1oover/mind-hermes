from mindcore.runtime import Runtime, MAX_GAP_MIN


class Clock:
    def __init__(self, t=1_800_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def make(tmp_path, clock=None):
    return Runtime(tmp_path, "s1", clock or Clock())


def test_fresh_state_has_readout(tmp_path):
    r = make(tmp_path)
    assert "mood" in r.state()["raw"]


def test_time_advances_and_values_stay_bounded(tmp_path):
    c = Clock(); r = make(tmp_path, c)
    t0 = r.sim_t
    c.t += 3600
    r.advance()
    assert abs(r.sim_t - t0 - 60) < 1e-6
    raw = r.state()["raw"]
    assert -1 <= raw["mood"] <= 1 and 0 <= raw["arousal"] <= 1


def test_gap_is_capped_in_simulated_work(tmp_path):
    c = Clock(); r = make(tmp_path, c)
    c.t += 86400 * 30
    r.advance()
    assert r.sim_t > MAX_GAP_MIN


def test_persona_changes_shown_not_raw(tmp_path):
    r = make(tmp_path)
    raw_before = dict(r.state()["raw"])
    r.set_persona({"energy": 1})
    s = r.state()
    assert s["raw"] == raw_before
    assert s["shown"]["arousal"] >= s["raw"]["arousal"]


def test_event_changes_state(tmp_path):
    r = make(tmp_path)
    before = r.state()["raw"]["arousal"]
    after = r.interact(appraisal={"n": 1.0, "th": 1.0})["raw"]["arousal"]
    assert after != before


def test_save_load_round_trip(tmp_path):
    c = Clock(); r = make(tmp_path, c)
    r.interact(appraisal={"ew": 1.0}); r.set_persona({"warmth": .5}); r.save()
    expected = r.state()["raw"]
    r2 = make(tmp_path, c)
    got = r2.state()["raw"]
    for key in ("mood", "arousal", "bond", "sleep_pressure"):
        assert abs(got[key] - expected[key]) < 1e-9
    assert r2.persona["warmth"] == .5


def test_corrupt_state_falls_back_to_fresh(tmp_path):
    (tmp_path / "s1.json").write_text("{bad", encoding="utf-8")
    assert "mood" in make(tmp_path).state()["raw"]
