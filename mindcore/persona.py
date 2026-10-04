"""Personality traits from the sandbox v5. Traits modify model parameters (effective_params);
apply_persona is kept for API compatibility and returns the readout unchanged."""
import math
from copy import deepcopy

MUL_KEYS = {"speed_fast", "speed_mid", "speed_slow", "imp_gain", "lust_mul", "surprise_gain", "rumination", "giveup", "strain_gain",
            "mood_strain_gain", "tau_wake", "blunting", "habituation_strength", "mood_congruence", "hormone_congruence", "demand_gain",
            "impulse_budget", "impulse_cap", "spill_arousal", "spill_mood", "hl_phasic", "hl_surprise", "hl_adversity", "hl_commit",
            "hl_standards", "hl_bond", "hl_missing", "hl_play", "hl_mood", "hl_mood_baseline", "hl_competence", "hl_self_esteem"}
FLOOR_KEYS = {"floor_bond", "floor_comp", "floor_self", "floor_dom", "floor_mood"}
SIGNED_ADD = {"tb_arousal", "tb_mood", "tb_dom", "tb_seek", "tb_play", "tb_want", "tb_inh", "tb_bond", "tb_comp", "tb_self", "mood_baseline_offset"}
CURVES = {
    "lin": lambda x: x, "abs": abs, "ageU": lambda x: -abs(x), "pos": lambda x: max(0.0, x), "neg": lambda x: min(0.0, x),
    "cube": lambda x: x ** 3, "sq": lambda x: x * abs(x), "sat": lambda x: math.tanh(2 * x) / math.tanh(2),
}


def _t(label, group, help, fx, curve="lin"):
    return {"label": label, "group": group, "help": help, "fx": fx, "curve": curve}


TRAITS = {
    "energy": _t("Energy", "Temperament", "Sluggish to high-voltage.", [("tb_arousal", .9), ("tb_seek", .4), ("tb_play", .3), ("tau_wake", .3), ("speed_mid", .15)]),
    "extraversion": _t("Extraversion", "Temperament", "Outward activation, seeking and play.", [("tb_arousal", .35), ("tb_seek", .35), ("tb_play", .3), ("hl_missing", -.3)]),
    "playful": _t("Playful", "Temperament", "Higher, lingering PLAY drive.", [("tb_play", 1), ("tb_mood", .15), ("hl_play", .3)]),
    "mischievous": _t("Mischievous", "Temperament", "Teasing, boundary-testing.", [("tb_play", .6), ("tb_dom", .4), ("tb_seek", .3), ("imp_gain", .15), ("giveup", .4)]),
    "curiosity": _t("Curiosity", "Temperament", "Higher SEEKING, stronger novelty.", [("tb_seek", 1), ("imp_phasic_novelty", .3), ("boredom_rate", .3)]),
    "creativity": _t("Creativity", "Temperament", "Exploration and play, surprise less jarring.", [("tb_seek", .4), ("tb_play", .4), ("imp_phasic_novelty", .2), ("surprise_gain", -.25)]),
    "conscientiousness": _t("Conscientiousness", "Temperament", "Persistence and standards.", [("tb_dom", .3), ("tb_inh", .2), ("giveup", -.7), ("hl_commit", .5), ("hl_standards", .3)]),
    "rebelliousness": _t("Rebelliousness", "Temperament", "Resists structure and demands.", [("tb_dom", .5), ("tb_inh", -.2), ("hl_commit", -.5), ("giveup", .4), ("demand_gain", -.5)]),
    "patience": _t("Patience", "Temperament", "Short fuse to patient.", [("giveup", -1), ("rumination", -.5), ("hl_adversity", -.5), ("hl_commit", .3)]),
    "impulsivity": _t("Impulsivity", "Temperament", "Stronger, faster reactions, weaker brakes.", [("imp_gain", .5), ("speed_fast", .5), ("impulse_budget", .5), ("tb_inh", -.4), ("hl_phasic", .2)]),
    "warmth": _t("Warmth", "Social and affect", "Closer bond, warmer mood.", [("tb_bond", .5), ("tb_mood", .25), ("tb_want", .15), ("missing_warmth_boost", .3)]),
    "tenderness": _t("Tenderness", "Social and affect", "Soft, affiliative.", [("tb_bond", .3), ("tb_mood", .15), ("tb_dom", -.1), ("imp_val_warm", .08)]),
    "sociability": _t("Sociability", "Social and affect", "Misses the user sooner.", [("hl_missing", -.35), ("tb_seek", .2), ("tb_bond", .2), ("missing_ramp", .6)]),
    "assertiveness": _t("Assertiveness", "Social and affect", "Submissive to assertive.", [("tb_dom", 1), ("tb_inh", -.2)]),
    "formality": _t("Formality", "Social and affect", "Restrained, less play.", [("tb_play", -.5), ("tb_inh", .3), ("tb_dom", .2), ("imp_gain", -.3)]),
    "optimism": _t("Optimism", "Mood and resilience", "Pessimistic to optimistic.", [("tb_mood", .4), ("mood_baseline_offset", .25), ("rumination", -.4)]),
    "depressive_manic": _t("Depressive / manic", "Mood and resilience", "Negative: depressive, slow. Positive: manic, restless, bistable highs.",
                           [("tb_mood", 1), ("tb_arousal", .8), ("tb_dom", .5), ("tb_seek", .5), ("tb_play", .3), ("tb_want", .3), ("tau_wake", .5), ("mood_baseline_offset", .4), ("bistable", .15), ("speed_mid", .25), ("rumination", -.6)]),
    "mood_cycling": _t("Mood cycling", "Mood and resilience", "Spontaneous slow mood swings.", [("cyc_amp", .9)], "pos"),
    "menstrual_cycle": _t("Menstrual cycle", "Mood and resilience", "Optional hormone cycle strength.", [("cycle_alpha", 1), ("hormone_congruence", .2)], "pos"),
    "resilience": _t("Resilience", "Mood and resilience", "Brittle to resilient.", [("mood_strain_gain", -.8), ("strain_gain", -.6), ("hl_adversity", -.4), ("tb_self", .3)]),
    "sensitivity": _t("Sensitivity", "Mood and resilience", "Reacts more to everything.", [("imp_gain", .5), ("mood_congruence", .5), ("hormone_congruence", .4), ("surprise_gain", .3), ("habituation_strength", -.3)]),
    "shame_proneness": _t("Shame-proneness", "Mood and resilience", "Failures sink deeper and linger.", [("imp_val_standards", .15), ("hl_standards", .6), ("carry_standards_to_selfesteem", .2), ("tb_self", -.3), ("tb_mood", -.1)]),
    "emotional_stability": _t("Emotional stability", "Dynamics (timescales)", "Volatile to steady.", [("speed_fast", -.4), ("imp_gain", -.5), ("surprise_gain", -.5), ("rumination", -.7), ("tb_dom", .4), ("tb_mood", .2), ("mood_strain_gain", -.5)]),
    "moody": _t("Moody", "Dynamics (timescales)", "Quick, large mood swings that stick.", [("speed_fast", .6), ("speed_mid", .6), ("speed_slow", -.3), ("carry_valence_to_mood", .3), ("carry_phasic_to_arousal", .06), ("imp_gain", .4), ("mood_congruence", .4), ("cyc_amp", .15)]),
    "dynamicity": _t("Dynamicity", "Dynamics (timescales)", "Flat/stoic to lively.", [("speed_fast", .5), ("speed_mid", .4), ("speed_slow", .3), ("imp_gain", .6), ("carry_valence_to_mood", .2), ("carry_phasic_to_arousal", .04), ("impulse_cap", .3)]),
    "horizon": _t("Horizon: reactive vs long-term", "Dynamics (timescales)", "Reactive forgets quickly; accumulating writes reactions into slow baselines.",
                  [("speed_fast", -.5), ("speed_slow", .8), ("carry_valence_to_mood", .3), ("slow_follow_mood", .25), ("slow_follow_arousal", .2), ("spill_arousal", .5), ("spill_mood", .5)]),
    "autistic": _t("Autistic-style processing", "Cognition", "Coarse behavioural knobs, not a diagnosis model.",
                   [("surprise_gain", .4), ("hl_surprise", .7), ("habituation_strength", -.5), ("hl_commit", .6), ("giveup", -.4), ("tb_play", -.3), ("tb_inh", .2), ("imp_phasic_novelty", .2)], "pos"),
    "romanticism": _t("Romanticism", "Intimacy", "Deeper, slower-fading bond.", [("tb_bond", .6), ("hl_bond", .4), ("intensity_bond", .6), ("tb_want", .2), ("hl_missing", .3)]),
    "sensuality": _t("Sensuality", "Intimacy", "Wanting higher, erotic cues arouse more.", [("tb_want", .6), ("tb_inh", -.2), ("imp_phasic_erotic", .3)]),
    "naughty": _t("Naughty", "Intimacy", "Provocative when allowed.", [("tb_want", .7), ("tb_inh", -.6), ("lust_mul", .3), ("tb_play", .2)]),
    "prudishness": _t("Prudishness", "Intimacy", "Strong brake on erotic expression.", [("tb_inh", .9), ("tb_want", -.3), ("lust_mul", -.8)], "pos"),
    "age": _t("Age / maturity", "Intimacy", "-1 young, 0 mid-life, +1 old; U-shaped inhibition.", [("tb_inh", .9, "ageU"), ("tb_seek", -.4), ("tb_play", -.4), ("tb_dom", .4), ("mood_baseline_offset", .15), ("tau_wake", -.2)]),
    "enforced_loyalty": _t("OVERRIDE: enforced loyalty", "Overrides", "Forces bond to the top of its range.", [("floor_bond", 1), ("tb_bond", 1.5), ("hl_missing", .3)], "pos"),
    "bond_floor": _t("OVERRIDE: bond floor", "Overrides", "Bond never drops below this.", [("floor_bond", 1)], "pos"),
    "competence_floor": _t("OVERRIDE: competence floor", "Overrides", "Competence floor.", [("floor_comp", 1)], "pos"),
    "selfesteem_floor": _t("OVERRIDE: self-esteem floor", "Overrides", "Self esteem floor.", [("floor_self", 1)], "pos"),
    "dominance_floor": _t("OVERRIDE: dominance floor", "Overrides", "Dominance floor.", [("floor_dom", 1)], "pos"),
    "contentment_lock": _t("OVERRIDE: mood floor", "Overrides", "Mood and baseline floor.", [("floor_mood", 1)], "pos"),
    "uninhibited": _t("OVERRIDE: inhibition cap", "Overrides", "Caps LUST inhibition.", [("cap_inh", -.95)], "pos"),
}


def default_persona():
    return {k: 0.0 for k in TRAITS}


def normalize_persona(persona=None):
    result = default_persona()
    for key, value in (persona or {}).items():
        if key in result:
            try:
                result[key] = max(-1.0, min(1.0, float(value)))
            except (TypeError, ValueError):
                pass
    return result


def persona_patch(persona):
    out = {}
    for name, t in TRAITS.items():
        raw = max(-1.0, min(1.0, float(persona.get(name, 0) or 0)))
        if not raw:
            continue
        for fx in t["fx"]:
            k, gain = fx[0], fx[1]
            curve = fx[2] if len(fx) > 2 else t["curve"]
            v = CURVES[curve](raw) * gain
            if not v:
                continue
            if k in FLOOR_KEYS:
                out[k] = max(out.get(k, 0.0), max(0.0, v))
            else:
                out[k] = out.get(k, 0.0) + v
    return out


def effective_params(base, persona):
    E = dict(base)
    for k, v in persona_patch(normalize_persona(persona)).items():
        if k not in E:
            continue
        if k in FLOOR_KEYS:
            E[k] = max(E[k], v)
        elif k in MUL_KEYS:
            E[k] = E[k] * math.exp(v)
        elif k == "cap_inh":
            E[k] = max(.03, min(E[k], 1 + v))
        elif k in SIGNED_ADD:
            E[k] = E[k] + v
        else:
            E[k] = max(0.0, E[k] + v)
    E["lust_gate"] = base.get("lust_gate", 1) * E.get("lust_mul", 1)
    return E


def apply_persona(readout, persona=None):
    """Traits now act on the dynamics, so the readout is returned unchanged."""
    return deepcopy(readout)
