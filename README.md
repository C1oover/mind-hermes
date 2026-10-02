# mind-hermes

Biomimetic mind engine (multi-timescale ODE state model with traits) and a Hermes Agent plugin.

Status: design draft, not publishable.

- `docs/SPEC.md`: interface spec v1.2 and architecture
- `mindcore/`: pure Python engine (port of the JS sandbox `mind_sandbox_v5.html`); no Hermes imports
- `sandbox/`: JS designer (to be added)

Build order: mindcore + snapshot + golden traces, world providers, adapter/renderer/tools, appraisers, scheduler, sampling, bridge.
