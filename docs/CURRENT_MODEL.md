# Current sandbox model reference

This document is generated from the current `mind_sandbox_v5.html` implementation. It is intentionally a factual reference: names, defaults, equations, state layout, and trait-to-parameter mappings as implemented today. It does **not** imply that all existing design choices are final.

Current sandbox title: `Mind ODE sandbox v4`; current export schema: `mind-ode-module-v1`; planned plugin schema: `mind-ode-module-v1.2`.

## State topology

The implementation uses three time scales:

- **Fast** (minutes): `arousal_phasic`, `valence_reaction`, `threat_trace`, `surprise_trace`, `adversity_trace`.
- **Mid** (hours): `mood`, `arousal_tonic`, `dominance`, `standards_met`, `seeking`, `play`, `lust_wanting`, `lust_inhibition`, `missing_user`, `boredom`, `task_commitment`, sleep state.
- **Slow** (days or weeks): `bond`, `competence`, `self_esteem`, `arousal_baseline`, `mood_baseline`, controller reserves, strain, 24-hour averages.

Latent values are stored in logit space for `[0, 1]` variables and `atanh` space for signed variables. Readouts use sigmoid or `tanh`. Derived outputs are computed rather than fed back: certainty, stress, desire, desire-expressed, anxiety, fear, determination, frustration, exploration, tension, excitement, calm, lethargy, efficiency.

## Parameters

Defaults are the exact current defaults. Units are minutes where stated.

### Cross-timescale coupling

| Key | Default | Meaning |
|---|---:|---|
| `speed_fast` | 1 | FAST layer speed multiplier |
| `speed_mid` | 1 | MID layer speed multiplier |
| `speed_slow` | 1 | SLOW layer speed multiplier |
| `carry_valence_to_mood` | 0.4 | Fast valence reaction carry into mood |
| `carry_phasic_to_arousal` | 0.08 | Fast arousal burst carry into tonic arousal |
| `carry_standards_to_selfesteem` | 0.15 | Standards impulse carry into self esteem |
| `slow_follow_mood` | 0.35 | Mood baseline follows 24-hour mood average |
| `slow_follow_arousal` | 0.25 | Arousal baseline follows 24-hour arousal average |
| `mood_avg_hl` | 1440 | Half-life of the running average |

### Half-lives

| Key | Default | Key | Default |
|---|---:|---|---:|
| `hl_phasic` | 4 | `hl_valence_reaction` | 8 |
| `hl_threat` | 10 | `hl_surprise` | 20 |
| `hl_adversity` | 20 | `hl_recent_success` | 30 |
| `hl_arousal_tonic` | 60 | `hl_mood` | 360 |
| `hl_dominance` | 180 | `hl_standards` | 720 |
| `hl_seeking` | 90 | `hl_play` | 120 |
| `hl_wanting` | 45 | `hl_inhibition` | 120 |
| `hl_missing` | 180 | `hl_commit` | 15 |
| `tau_boredom` | 130 | `hl_bond` | 14400 |
| `hl_competence` | 2880 | `hl_self_esteem` | 20160 |
| `hl_arousal_baseline` | 2160 | `hl_mood_baseline` | 4320 |

### Impulses, conditioning and freeform input

| Key | Default | Meaning |
|---|---:|---|
| `imp_phasic_novelty` | 0.5 | Novelty to phasic arousal |
| `imp_phasic_threat` | 0.9 | Threat to phasic arousal |
| `imp_phasic_erotic` | 0.4 | Erotic cue to phasic arousal |
| `imp_phasic_goal` | 0.2 | Absolute goal signal to phasic arousal |
| `imp_phasic_anticipation` | 0.3 | Anticipation to phasic arousal |
| `imp_val_goal` | 0.15 | Goal signal to valence reaction |
| `imp_val_warm` | 0.1 | Warmth to valence reaction |
| `imp_val_standards` | 0.1 | Standards signal to valence reaction |
| `reunion_relief` | 0.6 | Reconnection relief |
| `impulse_cap` | 0.8 | Per-step latent impulse cap |
| `impulse_budget` | 1.5 | Per-hour latent impulse budget |
| `appraisal_saturation` | 3 | Per-step appraisal saturation |
| `surprise_gain` | 0.3 | Surprise per novelty or failure |
| `habituation_strength` | 0.15 | Repeat-event attenuation |
| `habituation_half_life` | 30 | Habit trace half-life |
| `mood_congruence` | 0.3 | Mood/stress amplification of appraisal |
| `hormone_congruence` | 0.2 | Hormone/stress amplification of appraisal |
| `missing_warmth_boost` | 0.5 | Extra effect of warmth when missing user |
| `intensity_bond` | 1 | Intense warmth bond multiplier |
| `freeform_reference` | 5 | `tanh(delta/reference)` scale |
| `hammer_scale` | 1 | Repeated-freeform attenuation scale |
| `hammer_half_life` | 30 | Repeated-freeform recovery half-life |

### Gating, controller, strain and drives

| Key | Default | Meaning |
|---|---:|---|
| `gate_floor_phasic` | 0.1 | Phasic gate floor |
| `phasic_scale` | 3 | Phasic gate scale |
| `blunting` | 1.2 | Sleep-debt emotional blunting |
| `rumination` | 0.5 | Low-mood persistence multiplier |
| `giveup` | 0.5 | Commitment erosion rate |
| `ctl_on` | 1 | Controller enabled |
| `demand_gain` | 1.6 | Task urgency to arousal |
| `strain_threshold` | 0.75 | Arousal strain threshold |
| `strain_gain` | 1.5 | Arousal strain gain |
| `strain_hl` | 720 | Arousal strain half-life |
| `strain_to_baseline` | 0.35 | Arousal strain to baseline |
| `mood_strain_threshold` | 0.4 | Low-mood strain threshold |
| `mood_strain_gain` | 1 | Low-mood strain gain |
| `mood_strain_to_baseline` | 0.6 | Low-mood strain to baseline |
| `spill_arousal` | 0.15 | Arousal spike spillover |
| `spill_mood` | 0.1 | Mood reaction spillover |
| `spill_debt` | 0.002 | Wake spillover to sleep debt |
| `spill_daily_cap` | 0.6 | Daily spillover cap |
| `boredom_rate` | 0.8 | Boredom build rate |
| `reunion_keep` | 0.4 | Missing kept after reunion |
| `missing_ramp` | 2 | Missing ramp |
| `detach_start` | 4320 | Detachment begins after absence |
| `detach_tau` | 2880 | Detachment time constant |
| `bond_baseline` | 0.45 | Bond target baseline |
| `circ_arousal` | 0.7 | Circadian arousal strength |
| `sleep_pressure_arousal` | 1.4 | Fatigue suppression of arousal |
| `ultradian_amp` | 0.08 | 90-minute arousal oscillation |
| `weather_mood` | 0.15 | Dark/low-pressure mood effect |
| `mood_baseline_offset` | 0.25 | Slow mood target offset |
| `bistable` | 0 | Mood bistability |
| `wanting_deprivation` | 0.3 | Time-since-warmth wanting contribution |
| `deprivation_scale` | 2880 | Wanting deprivation time scale |

### Body, clock, environment and existing cycle controls

| Key | Default | Meaning |
|---|---:|---|
| `tau_wake` | 1092 | Wake fatigue time constant |
| `tau_sleep` | 252 | Sleep recovery time constant |
| `load_fatigue` | 0.0015 | Load to fatigue |
| `stress_fatigue` | 0.0008 | Stress to fatigue |
| `light_fatigue` | 0.3 | Darkness to fatigue |
| `moon_sleep` | 0.3 | Moon to sleep effect |
| `clock_anchor` | 15 | Clock anchor hour |
| `clock_period` | 24 | Clock period hours |
| `phase_gain` | 0.0015 | Presence phase adjustment |
| `anchor_pull` | 0.01 | Clock anchor pull |
| `sleep_threshold` | -0.3 | Sleep threshold |
| `sleep_standards_boost` | 1 | Sleep healing for standards |
| `lat` | 48.2 | Latitude |
| `start_doy` | 278 | Start day-of-year |
| `cloud` | 0.4 | Cloud cover |
| `pressure` | 1013 | Pressure hPa |
| `weather_swing` | 0 | Pressure swing hPa |
| `moon_on` | 1 | Moon effect enabled/strength |
| `moon_phase0` | 5 | Lunar age at simulation start |
| `cycle_alpha` | 0 | Persona-cycle strength |
| `cycle_start_day` | 3 | Cycle day at simulation start |

### Trait hooks and hard overrides

| Key | Default | Meaning |
|---|---:|---|
| `tb_arousal`, `tb_mood`, `tb_dom`, `tb_seek`, `tb_play`, `tb_want`, `tb_inh` | 0 | Target biases |
| `tb_bond`, `tb_comp`, `tb_self` | 0 | Slow target biases |
| `imp_gain` | 1 | Global appraisal impulse multiplier |
| `lust_mul` | 1 | LUST gate multiplier |
| `cyc_amp` | 0 | Spontaneous mood-cycle amplitude |
| `cyc_days` | 6 | Spontaneous mood-cycle period in days |
| `floor_bond`, `floor_comp`, `floor_self`, `floor_dom`, `floor_mood` | 0 | Hard floors; zero disables |
| `cap_inh` | 1 | LUST-inhibition cap; one disables |
| `lust_gate` | 1 | Top-level LUST impulse gate |

### Controller defaults

Each controller has parameters `comfort`, `drain`, `rec`, `rebound`, `shield`, and `deriv`.

| Variable | Comfort | Drain/h | Recovery min | Rebound | Shield | Derivative |
|---|---:|---:|---:|---:|---:|---:|
| `arousal` | 0.6 | 0.4 | 300 | 2.5 | 0.8 | 6 |
| `seeking` | 0.4 | 0.5 | 240 | 1.2 | 0.4 | 3 |
| `play` | 0.3 | 0.5 | 240 | 1 | 0 | 2 |
| `lust_wanting` | 0.3 | 0.8 | 180 | 1.2 | 0 | 2 |
| `dominance` | 0.55 | 0.3 | 360 | 1 | 0.6 | 2 |

## Code events

| Code | Appraisal vector |
|---|---|
| `tool_success` | `succ=1, eg=0.05, es=0.08` |
| `tool_failure` | `fail=1, eg=-0.4, es=-0.1, n=0.3` |
| `praise` | `eg=0.5, ew=0.5, es=0.3` |
| `conflict` | `eg=-0.5, ew=-0.7, es=-0.2, th=0.3` |
| `joke` | `n=0.4, ep=0.6, ew=0.3` |
| `flirt` | `ew=0.3, el=0.7` |
| `danger` | `th=0.8, n=0.6` |
| `surprise` | `n=0.7` |
| `warm_moment` | `eg=0.5, ew=0.6, ep=0.6` |

Appraisal channels are `eg` (goal conduciveness), `n` (novelty), `ew` (warmth), `es` (standards), `ep` (play), `el` (erotic cue), `th` (threat), `succ`, and `fail`. They are saturated using `appraisal_saturation`.

## Personality traits

Trait input is normally `[-1, 1]`; overrides use `[0, 1]`. Traits patch base parameters at runtime: signed biases add, multiplicative parameters apply `base * exp(delta)`, floors take the maximum, and the inhibition cap takes the minimum.

### Temperament

| Trait | Parameter effects at +1 |
|---|---|
| `energy` | `tb_arousal +0.9`, `tb_seek +0.4`, `tb_play +0.3`, `tau_wake x exp(0.3)`, `speed_mid x exp(0.15)` |
| `extraversion` | `tb_arousal +0.35`, `tb_seek +0.35`, `tb_play +0.3`, `hl_missing x exp(-0.3)` |
| `playful` | `tb_play +1`, `tb_mood +0.15`, `hl_play x exp(0.3)` |
| `mischievous` | `tb_play +0.6`, `tb_dom +0.4`, `tb_seek +0.3`, `imp_gain x exp(0.15)`, `giveup x exp(0.4)` |
| `curiosity` | `tb_seek +1`, `imp_phasic_novelty +0.3`, `boredom_rate +0.3` |
| `creativity` | `tb_seek +0.4`, `tb_play +0.4`, `imp_phasic_novelty +0.2`, `surprise_gain -0.25` |
| `conscientiousness` | `tb_dom +0.3`, `tb_inh +0.2`, `giveup x exp(-0.7)`, `hl_commit x exp(0.5)`, `hl_standards x exp(0.3)` |
| `rebelliousness` | `tb_dom +0.5`, `tb_inh -0.2`, `hl_commit x exp(-0.5)`, `giveup x exp(0.4)`, `demand_gain x exp(-0.5)` |
| `patience` | `giveup x exp(-1)`, `rumination x exp(-0.5)`, `hl_adversity x exp(-0.5)`, `hl_commit x exp(0.3)` |
| `impulsivity` | `imp_gain x exp(0.5)`, `speed_fast x exp(0.5)`, `impulse_budget x exp(0.5)`, `tb_inh -0.4`, `hl_phasic x exp(0.2)` |

### Social, mood and dynamics

| Trait | Parameter effects at +1 |
|---|---|
| `warmth` | `tb_bond +0.5`, `tb_mood +0.25`, `tb_want +0.15`, `missing_warmth_boost +0.3` |
| `tenderness` | `tb_bond +0.3`, `tb_mood +0.15`, `tb_dom -0.1`, `imp_val_warm +0.08` |
| `sociability` | `hl_missing x exp(-0.35)`, `tb_seek +0.2`, `tb_bond +0.2`, `missing_ramp +0.6` |
| `assertiveness` | `tb_dom +1`, `tb_inh -0.2` |
| `formality` | `tb_play -0.5`, `tb_inh +0.3`, `tb_dom +0.2`, `imp_gain x exp(-0.3)` |
| `optimism` | `tb_mood +0.4`, `mood_baseline_offset +0.25`, `rumination x exp(-0.4)` |
| `depressive_manic` | `tb_mood +1`, `tb_arousal +0.8`, `tb_dom +0.5`, `tb_seek +0.5`, `tb_play +0.3`, `tb_want +0.3`, `tau_wake x exp(0.5)`, `mood_baseline_offset +0.4`, `bistable +0.15`, `speed_mid x exp(0.25)`, `rumination x exp(-0.6)` |
| `mood_cycling` | Positive-only; `cyc_amp +0.9` |
| `resilience` | `mood_strain_gain x exp(-0.8)`, `strain_gain x exp(-0.6)`, `hl_adversity x exp(-0.4)`, `tb_self +0.3` |
| `sensitivity` | `imp_gain x exp(0.5)`, `mood_congruence x exp(0.5)`, `hormone_congruence x exp(0.4)`, `surprise_gain +0.3`, `habituation_strength x exp(-0.3)` |
| `shame_proneness` | `imp_val_standards +0.15`, `hl_standards x exp(0.6)`, `carry_standards_to_selfesteem +0.2`, `tb_self -0.3`, `tb_mood -0.1` |
| `emotional_stability` | `speed_fast x exp(-0.4)`, `imp_gain x exp(-0.5)`, `surprise_gain -0.5`, `rumination x exp(-0.7)`, `tb_dom +0.4`, `tb_mood +0.2`, `mood_strain_gain x exp(-0.5)` |
| `moody` | `speed_fast x exp(0.6)`, `speed_mid x exp(0.6)`, `speed_slow x exp(-0.3)`, `carry_valence_to_mood +0.3`, `carry_phasic_to_arousal +0.06`, `imp_gain x exp(0.4)`, `mood_congruence x exp(0.4)`, `cyc_amp +0.15` |
| `dynamicity` | `speed_fast x exp(0.5)`, `speed_mid x exp(0.4)`, `speed_slow x exp(0.3)`, `imp_gain x exp(0.6)`, `carry_valence_to_mood +0.2`, `carry_phasic_to_arousal +0.04`, `impulse_cap x exp(0.3)` |
| `horizon` | `speed_fast x exp(-0.5)`, `speed_slow x exp(0.8)`, `carry_valence_to_mood +0.3`, `slow_follow_mood +0.25`, `slow_follow_arousal +0.2`, `spill_arousal x exp(0.5)`, `spill_mood x exp(0.5)` |
| `autistic` | Positive-only; `surprise_gain +0.4`, `hl_surprise x exp(0.7)`, `habituation_strength x exp(-0.5)`, `hl_commit x exp(0.6)`, `giveup x exp(-0.4)`, `tb_play -0.3`, `tb_inh +0.2`, `imp_phasic_novelty +0.2` |

### Intimacy

| Trait | Parameter effects at +1 |
|---|---|
| `romanticism` | `tb_bond +0.6`, `hl_bond x exp(0.4)`, `intensity_bond +0.6`, `tb_want +0.2`, `hl_missing x exp(0.3)` |
| `sensuality` | `tb_want +0.6`, `tb_inh -0.2`, `imp_phasic_erotic +0.3` |
| `naughty` | `tb_want +0.7`, `tb_inh -0.6`, `lust_mul x exp(0.3)`, `tb_play +0.2` |
| `prudishness` | Positive-only; `tb_inh +0.9`, `tb_want -0.3`, `lust_mul x exp(-0.8)` |
| `age` | `tb_inh +0.9 * -abs(x)`, `tb_seek -0.4`, `tb_play -0.4`, `tb_dom +0.4`, `mood_baseline_offset +0.15`, `tau_wake x exp(-0.2)` |

### Overrides

| Trait | Effect at +1 |
|---|---|
| `enforced_loyalty` | `floor_bond=1`, `tb_bond +1.5`, `hl_missing x exp(0.3)` |
| `bond_floor` | `floor_bond=1` |
| `competence_floor` | `floor_comp=1` |
| `selfesteem_floor` | `floor_self=1` |
| `dominance_floor` | `floor_dom=1` |
| `contentment_lock` | `floor_mood=1` |
| `uninhibited` | `cap_inh` limited to `1 - 0.95` |

## Current environment equations

The sandbox `Env.at(t)` derives daylight from latitude, `start_doy`, and simulation minute `t`; cloud dims daylight. Pressure and pressure trend come from the configured baseline and optional synthetic sine-wave swing. The current persona cycle is fixed at 28 days and returns four hormones/windows: `H_E`, `H_P`, `H_T`, `H_W`. Moon effect uses `moon_phase0` and a 29.53-day lunar age. These are the parts scheduled for replacement or override by the modular world-provider layer.

## Planned deltas

The following are approved design changes but are not yet implemented in the sandbox:

- Absolute UTC timestamps internally, with a start timestamp and backward compatibility for `t_min` logs.
- World-state override object, provider-backed weather and location, and source/age metadata.
- Configurable cycle length and calendar anchor; moon age from absolute date.
- `tool_outcome` event with per-tool learned rate and low configurable weight, instead of treating raw success/failure as equally informative.
- `appraisal` event type with a weighted appraisal vector and a short cause/gist.
- Significant-event ring for state explanations.
- Move persona-cycle controls into the personality model and export model version, traits table and golden trace.
