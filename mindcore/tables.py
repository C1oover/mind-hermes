"""Parameter table, event codes and controller defaults ported from mind_sandbox.html v5."""

CODES = {
    "tool_success": {"succ": 1, "eg": .05, "es": .08},
    "tool_failure": {"fail": 1, "eg": -.4, "es": -.1, "n": .3},
    "praise": {"eg": .5, "ew": .5, "es": .3},
    "conflict": {"eg": -.5, "ew": -.7, "es": -.2, "th": .3},
    "joke": {"n": .4, "ep": .6, "ew": .3},
    "flirt": {"ew": .3, "el": .7},
    "danger": {"th": .8, "n": .6},
    "surprise": {"n": .7},
    "warm_moment": {"eg": .5, "ew": .6, "ep": .6},
}

CTRLV = ("arousal", "seeking", "play", "lust_wanting", "dominance")
CTRL_DEF = {
    "arousal": dict(comfort=.6, drain=.4, rec=300, rebound=2.5, shield=.8, deriv=6),
    "seeking": dict(comfort=.4, drain=.5, rec=240, rebound=1.2, shield=.4, deriv=3),
    "play": dict(comfort=.3, drain=.5, rec=240, rebound=1, shield=0, deriv=2),
    "lust_wanting": dict(comfort=.3, drain=.8, rec=180, rebound=1.2, shield=0, deriv=2),
    "dominance": dict(comfort=.55, drain=.3, rec=360, rebound=1, shield=.6, deriv=2),
}

DEFAULTS = {
    "speed_fast": 1, "speed_mid": 1, "speed_slow": 1, "carry_valence_to_mood": .4, "carry_phasic_to_arousal": .08,
    "carry_standards_to_selfesteem": .15, "slow_follow_mood": .35, "slow_follow_arousal": .25, "mood_avg_hl": 1440,
    "hl_phasic": 4, "hl_valence_reaction": 8, "hl_threat": 10, "hl_surprise": 20, "hl_adversity": 20,
    "hl_recent_success": 30, "hl_arousal_tonic": 60, "hl_mood": 360, "hl_dominance": 180, "hl_standards": 720,
    "hl_seeking": 90, "hl_play": 120, "hl_wanting": 45, "hl_inhibition": 120, "hl_missing": 180, "hl_commit": 15,
    "tau_boredom": 130, "hl_bond": 14400, "hl_competence": 2880, "hl_self_esteem": 20160,
    "hl_arousal_baseline": 2160, "hl_mood_baseline": 4320,
    "imp_phasic_novelty": .5, "imp_phasic_threat": .9, "imp_phasic_erotic": .4, "imp_phasic_goal": .2,
    "imp_phasic_anticipation": .3, "imp_val_goal": .15, "imp_val_warm": .1, "imp_val_standards": .1,
    "reunion_relief": .6, "impulse_cap": .8, "impulse_budget": 1.5, "appraisal_saturation": 3, "surprise_gain": .3,
    "habituation_strength": .15, "habituation_half_life": 30, "mood_congruence": .3, "hormone_congruence": .2,
    "missing_warmth_boost": .5, "intensity_bond": 1,
    "freeform_reference": 5, "hammer_scale": 1, "hammer_half_life": 30,
    "gate_floor_phasic": .1, "phasic_scale": 3, "blunting": 1.2, "rumination": .5, "giveup": .5,
    "ctl_on": 1, "demand_gain": 1.6,
    "strain_threshold": .75, "strain_gain": 1.5, "strain_hl": 720, "strain_to_baseline": .35,
    "mood_strain_threshold": .4, "mood_strain_gain": 1, "mood_strain_to_baseline": .6,
    "spill_arousal": .15, "spill_mood": .1, "spill_debt": .002, "spill_daily_cap": .6,
    "boredom_rate": .8, "reunion_keep": .4, "missing_ramp": 2, "detach_start": 4320, "detach_tau": 2880,
    "bond_baseline": .45, "circ_arousal": .7, "sleep_pressure_arousal": 1.4, "ultradian_amp": .08,
    "weather_mood": .15, "mood_baseline_offset": .25, "bistable": 0, "wanting_deprivation": .3,
    "deprivation_scale": 2880,
    "tau_wake": 1092, "tau_sleep": 252, "load_fatigue": .0015, "stress_fatigue": .0008, "light_fatigue": .3,
    "moon_sleep": .3, "clock_anchor": 15, "clock_period": 24, "phase_gain": .0015, "anchor_pull": .01,
    "sleep_threshold": -.3, "sleep_standards_boost": 1,
    "lat": 48.2, "start_doy": 278, "cloud": .4, "pressure": 1013, "weather_swing": 0, "moon_on": 1, "moon_phase0": 5,
    "cycle_alpha": 0, "cycle_length": 28, "cycle_start_day": 3,
    "tb_arousal": 0, "tb_mood": 0, "tb_dom": 0, "tb_seek": 0, "tb_play": 0, "tb_want": 0, "tb_inh": 0,
    "tb_bond": 0, "tb_comp": 0, "tb_self": 0, "imp_gain": 1, "lust_mul": 1, "cyc_amp": 0, "cyc_days": 6,
    "floor_bond": 0, "floor_comp": 0, "floor_self": 0, "floor_dom": 0, "floor_mood": 0, "cap_inh": 1,
    "lust_gate": 1,
}
for _v, _d in CTRL_DEF.items():
    for _k, _val in _d.items():
        DEFAULTS["ctl_%s_%s" % (_v, _k)] = _val
