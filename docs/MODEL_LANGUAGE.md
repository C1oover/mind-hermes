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

## Readouts

`mindcore/model/readout.mind` defines the values returned after every step (desire, anxiety, efficiency, ...):

```
readout {
  _hill = pow(desire, 3) / (pow(desire, 3) + pow(0.25, 3))
  desire_expressed = _hill * (0.2 + 0.8 * present)
}
```

Only `=` is allowed. Names starting with `_` are temporaries and are not returned. Inputs are the latent values, `arousal`, `mood`, `stress`,
`cert`, `threat_trace`, `adversity_trace`, `present`, `circ`, `light`, `H_E`, `H_P`, `moon`, and all effective parameters.
A user `model.mind` can redefine a readout or add new ones; they appear in `Mind.out`. `Mind.readout_legacy` keeps the old Python
version for `tests/test_readout_model.py`, which checks both agree over 30 simulated interactions across several days.

## Conditions and UI metadata

```
a += if value > 0 then 2 * value else 0.5 * value
```

- `if c then a else b` is lazy, so the unused branch is never evaluated. Comparisons are `< > <= >= == !=`, logic is `and or not`, and true/false are 1/0. Use parentheses to put an `if` inside arithmetic.
- `group "Name"` sets the UI group of the params below it; `param` metadata accepts `label`, `step`, `min`, `max`, `visible`.
- `Model.param_table()` returns the rows the UI needs. `tests/test_params_meta.py` checks them against the definitions still in `mind_sandbox.html`.

## Web UI parser

`web/mindmodel.js` is a JavaScript port of the parser, evaluator and model (browser global `MindModel`, or `require` in Node):

```js
const m = MindModel.loadFromTexts([["params.mind", paramsText], ["traits.mind", traitsText], ["resolve.mind", resolveText], ["readout.mind", readoutText]]);
m.paramTable();                       // rows for the parameter panel
m.traitInfo();                        // trait labels, groups, help
m.effectiveParams(base, persona);     // same as Python
m.evaluateReadout(inputs, params);    // same as Python
```

`tests/test_js_parity.py` runs Node and checks that effective parameters (about 100 personas), readouts from a simulated run, UI metadata and
error messages are identical to the Python model. The test is skipped when Node is not installed. The HTML does not use the module yet.

Not yet implemented: switching `mind_sandbox.html` to the module, user-defined state variables and dynamics (the ODE step is still Python).
