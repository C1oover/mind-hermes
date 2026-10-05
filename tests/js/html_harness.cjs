// Runs the script part of mind_sandbox.html (everything before the UI code) in a VM and prints parameter/persona/simulation results as JSON.
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const code = html.slice(html.indexOf('<script>') + 8, html.indexOf('let EP=null'));
const ctx = vm.createContext({ console, Math, Date, Float32Array, Float64Array, Object, Array, Set, Map, JSON, Number, String, parseFloat, isFinite, performance: { now: () => Date.now() } });
vm.runInContext(code + '\n;globalThis.__api={effectiveParams,defaultParams,defaultPersona,simulate,defaultCfg,PARAM_DEFS,PERSONA_KEYS,TRAITS};', ctx);
const A = ctx.__api;
const keys = A.PERSONA_KEYS;
const personas = [{}];
for (const k of keys) for (const v of [-1, 1]) personas.push({ [k]: v });
let s = 7;
const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
for (let i = 0; i < 12; i++) { const p = {}; for (const k of keys) if (rnd() < 0.3) p[k] = rnd() * 2 - 1; personas.push(p); }
const P = A.defaultParams();
const summary = (r) => {
  const o = { W: r.W, N: r.N };
  for (const k in r.series) { const a = Array.from(r.series[k]); o[k] = [a[a.length - 1], a.reduce((x, y) => x + y, 0)]; }
  return o;
};
const out = {
  defs: A.PARAM_DEFS, traits: keys, persona0: A.defaultPersona(),
  params: personas.map((p) => A.effectiveParams(P, p)),
  sim: personas.filter((_, i) => i % 9 === 0).map((p) => summary(A.simulate(A.defaultCfg(), A.effectiveParams(P, p), 5))),
};
process.stdout.write(JSON.stringify(out));
