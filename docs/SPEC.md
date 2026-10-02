# Mind module for Hermes: interface spec v1.2 and architecture

Sandbox = `mind_sandbox_v5.html` (model + designer). Target = Hermes Agent plugin, latest upstream.

## 1. Principles
- Engine (`mindcore`) is pure Python, no Hermes imports. Same model as the JS sandbox.
- Derived variables are computed on read, never stored.
- Impulses are asynchronous, LLM-controlled, freeform, saturated with tanh (no hard ranges); `freeform_reference` is the magnitude guide.
- Time is absolute UTC (epoch seconds) everywhere; engine steps in minutes. Gaps are fast-forwarded with `present=0` at a coarser step (5-15 min).
- One agent (possibly several concurrent instances), one user, persona only (no user modeling). One engine behind a lock; `present` = any session active.
- Every hard feature (sampling, max_tokens, thinking, proactive, cycle display) is opt-in, default off.
- Determinism is not a contract; seed only drives small jitter; golden tests use fixed seed with tolerance.

## 2. Messages (schema `mind-ode-module-v1.2`)
| Message | Direction | Content |
|---|---|---|
| designer | sandbox -> engine | model_version, params (diff), persona (traits), traits_table, seed |
| world | providers -> engine, renderer | optional fields with `source` (observed/forecast/computed) and `age_s` |
| input | adapter -> engine | t_abs, present, load, commit_task, commit_rel, task_demand, events[] |
| state | engine -> adapter | readout vector (~45 keys), asleep, away_min, world_used |
| snapshot | engine <-> store | minimal runtime state |
| bid | engine -> scheduler | reason, strength, earliest_abs, expires_abs |
| module-log | engine -> sandbox | events with absolute time + sparse state samples |

### world fields
- time: t_abs, tz, utc_offset_min, local_min, weekday, date, is_holiday
- place: lat, lon, name (perturbed)
- sky: sun_alt_deg, daylen_h, cloud, precip, temp_c, pressure_hpa, pressure_trend_3h
- moon: age_d
- cycle: anchor_date, length, day, phase (persona's own cycle only)
Missing field => engine computes it, `source: computed`.

### events (all carry t_abs)
- `code` {name, value}: tool_success, tool_failure, praise, conflict, joke, flirt, danger, surprise, warm_moment
- `free` {name, value}: impulse on a named variable, tanh against reference, hammer budget applies
- `appraisal` {eg, n, ew, es, ep, el, th, succ, fail}
- `tool_outcome` {tool, ok, expected_p, dur_ms}: aggregated per turn; signal = prediction error vs learned per-tool rate, scaled by `tool_outcome_weight` (~0.1-0.2)
- `contact_bid_sent`, `contact_bid_answered`

## 3. Rules
- Inputs clamped; unknown events ignored and logged.
- Floors/caps enforced inside the step.
- Major version bump invalidates snapshots; minor adds keys.

## 4. Snapshot (state only)
- latent z map; boredom, task_commitment, sleep_pressure, sleep_debt, clock_phase
- traces: phasic, valence_reaction, threat, surprise, adversity; novelty_avg
- mood_avg, arousal_avg, expected_gap, since_warm, away_min, prev_present
- habit counters and impulse budgets with decay timestamps
- weekly[168], controller reserves/rates/prev, strains, spill_used
- last_t_abs, model_version, params_hash

Kept beyond state: (1) ring buffer of last ~200 events, (2) per-tool success-rate table, (3) optional rotated append-only log (off by default), (4) significant-event log.
Writes are atomic (temp + rename), on timer and session end. Missing file => fresh start.

## 5. Significant events
Entries {t_abs, kind, variable, delta, cause, gist, state_digest}; written on band crossing, large impulse, floor/cap activation. `cause` from the short appraiser's gist. Renderer shows top 1-2; tool `mind_why(variable)` returns more.

## 6. World providers (modular)
WorldProvider interface; clock, geo, weather, cycle modules. Default weather: Open-Meteo (no key; non-commercial; attribution; history endpoint for gap filling). Cache TTL 15-30 min; failure => computed fallback. Privacy: one stable per-install offset of ~2-5 km from an install id. Config file first, env vars as overrides.

## 7. Components
mindcore, world, adapter, appraiser (short+long), renderer, tools (mind_impulse, mind_event, mind_state, mind_why, mind_world), scheduler, store, bridge.

## 8. Hermes integration (verify against upstream)
- pre_llm_call: once per turn before tool loop; injected into user message at call time, not persisted. State block.
- System prompt section: persona, reading guide, impulse scale guide, appraiser protocol.
- post_tool_call / post_llm_call: outcome and appraisal triggers.
- register_tool: impulse and info tools.
- Subagents: hooks see parent_session_id; behaviour per `hooks.granularity`.

## 9. Hook granularity (setting)
`hooks.granularity`: `turn` (default) | `turn_plus_delegation` | `tool_call` | `all`. Related: `hooks.include_subagents`, `hooks.min_interval_s`, `hooks.tool_filter`. Note: mid-loop block refresh may not be possible with pre_llm_call alone; verify upstream.

## 10. Rendering
Full compact block every turn (no delta rendering: injection is ephemeral). World line + state line with bucketed labels and hysteresis + top live reasons. `render.length_hint` soft (default on); `sampling.max_tokens` hard (default off); `render.cycle` off|phase|detail.

## 11. Appraiser
Short: background, non-trivial turns. Mode `context`: send exact main-call messages + short instruction ("appraise only the last turn; JSON only"), structured output, temp 0, ~80 tokens, never written to history. Mode `compact`: digest prompt. Output: appraisal vector, <=2 freeform impulses, one-line gist; clamped. `appraiser.thinking`: off|low|on. Long: on idle/finalize/nightly; input = gists + ledger + summaries; output = impulses on slow variables and expected_gap corrections; traits never auto-edited. Model: main by default; optional `appraiser.task`.

## 12. Proactive contact
Engine projects forward with present=0 for threshold crossings -> earliest bid; one timer; cron can wake it. Fire-time gates: re-evaluate, quiet hours, agent asleep, min interval, daily cap, unanswered-bid backoff. Delivery: main-model generation from persona+state+reason; silent => nothing; message appended to session. Targets: configurable list [{platform, chat_id}], empty by default.

## 13. Sampling (experimental, off)
temperature (seeking+play up, fatigue down, clamp +-0.3), optional top_p, optional max_tokens; only provider-accepted fields sent.

## 14. Sandbox TODO
Env accepts world override; cycle_len + anchor date; moon age from absolute date; tool_outcome + weight; appraisal event; cycle controls under traits; absolute-time inputs; export traits_table, model_version, golden trace.

## 15. Build order
1. mindcore port + snapshot + golden traces 2. world 3. adapter/renderer/tools 4. appraisers 5. scheduler/proactive 6. sampling, bridge
