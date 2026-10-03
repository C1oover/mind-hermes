# Import / export

Two JSON formats, both produced and validated by `mindcore/portable.py`.

- State (`schema: mind-hermes-state-v1`): full runtime snapshot, including parameters, persona and mind variables.
- Parameters (`schema: mind-hermes-params-v1`): numeric model parameters only. Unknown keys and non-finite numbers are rejected.

A failed import leaves the existing state untouched. Value ranges are not validated yet.
