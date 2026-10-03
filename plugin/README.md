# Mind Hermes plugin

Install the repository or copy `plugin/` and `mindcore/` into a Hermes plugin directory:

```text
~/.hermes/plugins/mind-hermes/
  plugin.yaml
  __init__.py
  mindcore/
```

The plugin registers four tools: `mind_event`, `mind_state`, `mind_persona`, and `mind_reset`. It also injects a compact, personality-adjusted state summary through Hermes's `pre_llm_call` hook.

State is written atomically per Hermes session to `~/.hermes/mind-hermes/` by default. Set `MIND_HERMES_STATE_DIR` to change that location.

## Design

- The raw model is advanced by wall-clock elapsed time, capped at 180 minutes in one call to prevent an unbounded jump after a long outage.
- The plugin persists raw state and persona separately.
- Personality is expression-only: it changes the displayed/prompt-injected readout and never becomes feedback into the core controller.
- The injected state is optional tone context, not a diagnosis or an assertion about the user.
