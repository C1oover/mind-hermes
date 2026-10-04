# Model language

Parameters, traits and derived values live in `mindcore/model/*.mind`. An optional user file
(`~/.hermes/mind-hermes/model.mind`, or the path in `MIND_HERMES_MODEL`) is loaded last and replaces definitions of the same name.

```
param bistable = 0 | min=0 label="mood bistability"
def damp(x, k=0.5) = x * exp(-k)

trait energy | label="Energy" group="Temperament" help="Sluggish to high-voltage." {
  tb_arousal += 0.9 * value
  tau_wake *= exp(0.3 * value)
  hl_play = max(hl_play, 10)
}

resolve {
  lust_gate *= lust_mul
}
```

- Assignments: `=`, `+=`, `-=`, `*=`, `/=` on parameters. Statements are separated by newlines or `;`.
- `value` is the trait setting in [-1, 1]; traits with value 0 are skipped.
- Order: traits in file order, then `min`/`max` clamps from `param` metadata, then `resolve` blocks.
- Expressions: numbers, parameter names, `+ - * /`, parentheses, calls.
- Functions: `def f(x, k=3) = expr`; builtins `exp log sqrt abs tanh pow min max clamp sig pos neg ageU cube sq sat`.
- Errors carry `file:line`. Assigning to an unknown parameter fails at load time.

`mindcore/persona_legacy.py` is the previous hard-coded implementation; `tests/test_model_equivalence.py` checks that the
model files give identical effective parameters for every trait and 300 random personas.

Not yet implemented: conditionals, user-defined state variables and readouts, and a JavaScript parser for the web UI.
