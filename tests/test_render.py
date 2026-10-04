import json

from mindcore.render import DEFAULT_CONFIG, default_config, load_config, merge_config, render, word_for

STATE = {"shown": {"mood": 0.6, "arousal": -0.3, "stress": 0.0}, "raw": {"mood": -0.9}}


def test_default_matches_legacy_format():
    cfg = merge_config({"fields": ["mood", "arousal"]})
    assert render(STATE, cfg) == "[Mind state: mood=0.60, arousal=-0.30. Optional tone context only; not a diagnosis or an external fact.]"


def test_custom_template_and_labels():
    cfg = merge_config({"template": "MIND<{state}>", "item_format": "{label}:{value:.1f}", "separator": "|",
                        "fields": ["mood"], "labels": {"mood": "Mood"}})
    assert render(STATE, cfg) == "MIND<Mood:0.6>"


def test_words_mode_and_field_bands():
    cfg = merge_config({"mode": "words", "fields": ["mood", "stress"],
                        "field_bands": {"stress": [[0.5, "calm"], [9, "tense"]]}})
    out = render(STATE, cfg)
    assert "mood: high" in out and "stress: calm" in out


def test_raw_source():
    cfg = merge_config({"source": "raw", "fields": ["mood"]})
    assert "mood=-0.90" in render(STATE, cfg)


def test_bad_format_and_values_fall_back():
    cfg = merge_config({"item_format": "{nope}", "template": "{missing}", "mode": "bogus", "fields": ["mood"]})
    assert cfg["mode"] == DEFAULT_CONFIG["mode"]
    assert "mood=0.60" in render(STATE, cfg)


def test_load_config_from_state_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("MIND_HERMES_RENDER_CONFIG", raising=False)
    (tmp_path / "render.json").write_text(json.dumps({"separator": " ; "}))
    assert load_config(tmp_path)["separator"] == " ; "
    (tmp_path / "render.json").write_text("{bad")
    assert load_config(tmp_path)["separator"] == default_config()["separator"]


def test_word_for_edges():
    bands = [[0.0, "neg"], [1.0, "pos"]]
    assert word_for(-5, bands) == "neg" and word_for(5, bands) == "pos"


def test_default_json_is_auto_and_digestible():
    cfg = load_config("/nonexistent")
    assert cfg["mode"] == "auto" and cfg["traits"]
    calm = render({"shown": {"mood": 0.0, "arousal": 0.5, "stress": 0.1}}, cfg)
    assert "settled" in calm and not any(c.isdigit() for c in calm)


def test_auto_picks_salient_sorted_and_capped():
    cfg = load_config("/nonexistent")
    cfg["max_items"] = 2
    out = render({"shown": {"mood": -0.9, "stress": 0.9, "anxiety": 0.7, "play": 0.9, "sleep_pressure": 0.6}}, cfg)
    assert out.index("very low mood") < out.index("heavy stress") or "heavy stress" in out
    assert out.count(",") == 1 and "playful" not in out


def test_user_file_overrides_default_layer(tmp_path, monkeypatch):
    monkeypatch.delenv("MIND_HERMES_RENDER_CONFIG", raising=False)
    (tmp_path / "render.json").write_text(json.dumps({"template": "<{state}>", "max_items": 1}))
    cfg = load_config(tmp_path)
    assert cfg["mode"] == "auto" and render({"shown": {"mood": -0.9, "stress": 0.9}}, cfg) == "<very low mood>"
