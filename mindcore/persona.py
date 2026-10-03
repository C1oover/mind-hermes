"""Expression-layer personality traits from the untested v5 HTML tail.
Traits alter public readouts only; they never feed controller or state dynamics."""
from copy import deepcopy

TRAITS = {
    "mischievousness": ("Mischievousness", "Playful rule-breaking and teasing.", (("play", .35), ("seeking", .12), ("dominance", .10), ("task_commitment", -.12), ("boredom", .12))),
    "energy": ("Energy", "Stable apparent energy; expression-only.", (("arousal", .32), ("seeking", .12), ("play", .08), ("sleep_pressure", -.10))),
    "depressive_maniac": ("Depressive / maniac", "Negative colours expression depressive; positive colours it expansive.", (("mood", .42), ("arousal", .22), ("dominance", .14), ("seeking", .12), ("sleep_pressure", -.08))),
    "autistic": ("Autistic", "Predictability/focus and lower social-play preference; behavioural control only, not a diagnosis model.", (("certainty", .15), ("task_commitment", .18), ("play", -.12), ("seeking", -.08), ("stress", .08))),
    "naughty": ("Naughty", "Provocative/intimate play only when underlying desire permits it.", (("desire_expressed", .32), ("play", .10), ("dominance", .06), ("lust_inhibition", -.14))),
    "playful": ("Playful", "Baseline style preference for humour and play.", (("play", .35), ("boredom", .08), ("mood", .08))),
    "youthfulness": ("Youthfulness", "Novelty appetite, warm fast expression, and lower inhibition.", (("seeking", .22), ("play", .18), ("arousal", .10), ("lust_inhibition", -.10), ("boredom", .10))),
    "warmth": ("Warmth", "Relational warmth and openness.", (("mood", .12), ("bond", .12), ("missing_user", .08), ("lust_inhibition", -.05))),
    "conscientiousness": ("Conscientiousness", "Order, standards, and persistence.", (("task_commitment", .28), ("standards_met", .12), ("dominance", .08), ("play", -.06))),
    "curiosity": ("Curiosity", "Preference for exploration and novelty.", (("seeking", .35), ("boredom", .12), ("play", .06))),
    "sensitivity": ("Sensitivity", "Amplifies displayed response to current emotion, not underlying state.", (("mood", .14), ("anxiety", .18), ("tension", .16), ("missing_user", .12))),
}
SIGNED_READOUTS = frozenset(("mood", "standards_met", "mood_baseline"))


def default_persona():
    return {key: 0.0 for key in TRAITS}


def normalize_persona(persona=None):
    result = default_persona()
    for key, value in (persona or {}).items():
        if key in result:
            result[key] = max(-1.0, min(1.0, float(value)))
    return result


def trait_effect(readout_key, persona):
    return sum(persona.get(trait, 0.0) * weight
               for trait, (_, _, mappings) in TRAITS.items()
               for key, weight in mappings if key == readout_key)


def apply_persona(readout, persona=None):
    """Return a copy of readout with personality offsets, preserving raw dynamics."""
    p = normalize_persona(persona)
    result = deepcopy(readout)
    for key, value in result.items():
        if not isinstance(value, (int, float)) or key in ("present", "clock_phase"):
            continue
        offset = trait_effect(key, p)
        if key in SIGNED_READOUTS:
            result[key] = max(-1.0, min(1.0, value + offset))
        else:
            result[key] = max(0.0, min(1.0, value + offset))
    return result
