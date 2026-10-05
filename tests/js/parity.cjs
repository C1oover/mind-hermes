// Reads {personas, readouts, snippets} as JSON on stdin; prints the JS model's answers as JSON. Used by tests/test_js_parity.py.
const fs = require('fs');
const path = require('path');
const { loadFromTexts, Model } = require('../../web/mindmodel.js');
const dir = process.argv[2];
const files = ['params.mind', 'traits.mind', 'resolve.mind', 'readout.mind'].map((f) => [f, fs.readFileSync(path.join(dir, f), 'utf8')]);
const m = loadFromTexts(files);
const req = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = {
  effective: req.personas.map((p) => Object.assign({}, m.effectiveParams({}, p))),
  readouts: req.readouts.map((r) => m.evaluateReadout(r.inputs, r.params)),
  table: m.paramTable(),
  traits: m.traitInfo(),
  errors: req.snippets.map((s) => { try { new Model().add(s).validate(); return null; } catch (e) { return String(e.message); } }),
};
process.stdout.write(JSON.stringify(out));
