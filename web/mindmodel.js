/* Model language for the web UI: a port of mindcore/dsl.py + mindcore/model.py (params, functions, traits, resolve, readout).
   Works in browsers (window.MindModel) and Node (require). No eval. Parity with Python is checked by tests/test_js_parity.py. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.MindModel = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  class ModelError extends Error {
    constructor(msg, line, origin) {
      super((origin || '<model>') + (line ? ':' + line : '') + ': ' + msg);
      this.name = 'ModelError';
    }
  }

  function pyrepr(s) {
    s = String(s);
    const q = s.includes("'") && !s.includes('"') ? '"' : "'";
    let out = s.replace(/\\/g, '\\\\').replace(/\n/g, '\\n').replace(/\r/g, '\\r').replace(/\t/g, '\\t');
    if (q === "'") out = out.replace(/'/g, "\\'");
    return q + out + q;
  }

  const TOKEN = /([ \t\r]+|#[^\n]*)|(\n|;)|((?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)|("[^"\n]*")|([A-Za-z_][A-Za-z_0-9]*)|(\+=|-=|\*=|\/=|==|!=|<=|>=|[-+*\/=<>(){},|])/y;
  const KINDS = [null, 'ws', 'nl', 'num', 'str', 'name', 'op'];
  const ASSIGN = ['=', '+=', '-=', '*=', '/='];

  function tokenize(text, origin) {
    const toks = [];
    let pos = 0, line = 1;
    while (pos < text.length) {
      TOKEN.lastIndex = pos;
      const m = TOKEN.exec(text);
      if (!m) throw new ModelError('unexpected character ' + pyrepr(text[pos]), line, origin);
      let k = 1;
      while (m[k] === undefined) k++;
      const kind = KINDS[k], s = m[0];
      if (kind === 'nl') {
        toks.push(['nl', s, line]);
        if (s === '\n') line++;
      } else if (kind !== 'ws') toks.push([kind, s, line]);
      pos = TOKEN.lastIndex;
    }
    toks.push(['eof', '', line]);
    return toks;
  }

  class Parser {
    constructor(toks, origin) { this.t = toks; this.i = 0; this.origin = origin; }
    peek(k = 0) { return this.t[Math.min(this.i + k, this.t.length - 1)]; }
    next() { const t = this.t[Math.min(this.i, this.t.length - 1)]; this.i++; return t; }
    err(msg, tok) { tok = tok || this.peek(); throw new ModelError(msg, tok[2], this.origin); }
    is(tok, kind, text) { return tok[0] === kind && (text === undefined || tok[1] === text); }
    accept(kind, text) { return this.is(this.peek(), kind, text) ? this.next() : null; }
    expect(kind, text) {
      const t = this.accept(kind, text);
      if (!t) this.err('expected ' + (text || kind) + ', got ' + pyrepr(this.peek()[1] || 'end of file'));
      return t;
    }
    skipNl() { while (this.peek()[0] === 'nl') this.i++; }
    endStmt() {
      if (this.peek()[0] !== 'nl' && this.peek()[0] !== 'eof') this.err('unexpected ' + pyrepr(this.peek()[1]));
      this.skipNl();
    }
    meta() {
      const out = {};
      while (this.peek()[0] === 'name' && this.is(this.peek(1), 'op', '=')) {
        const key = this.next()[1];
        this.next();
        const [kind, s] = this.next();
        if (kind === 'str') out[key] = s.slice(1, -1);
        else if (kind === 'num') out[key] = parseFloat(s);
        else if (kind === 'name' && (s === 'true' || s === 'false')) out[key] = s === 'true';
        else this.err('bad value for ' + key);
      }
      return out;
    }
    expr() {
      if (this.is(this.peek(), 'name', 'if')) {
        this.next();
        const c = this.expr();
        this.expect('name', 'then');
        const a = this.expr();
        this.expect('name', 'else');
        return ['if', c, a, this.expr()];
      }
      let a = this.andexpr();
      while (this.accept('name', 'or')) a = ['or', a, this.andexpr()];
      return a;
    }
    andexpr() {
      let a = this.notexpr();
      while (this.accept('name', 'and')) a = ['and', a, this.notexpr()];
      return a;
    }
    notexpr() {
      if (this.accept('name', 'not')) return ['not', this.notexpr()];
      const a = this.arith();
      const t = this.peek();
      if (t[0] === 'op' && ['<', '>', '<=', '>=', '==', '!='].includes(t[1])) {
        this.next();
        return ['cmp', t[1], a, this.arith()];
      }
      return a;
    }
    arith() {
      let a = this.term();
      while (this.is(this.peek(), 'op', '+') || this.is(this.peek(), 'op', '-')) {
        const [, op, ln] = this.next();
        a = ['bin', op, a, this.term(), ln];
      }
      return a;
    }
    term() {
      let a = this.unary();
      while (this.is(this.peek(), 'op', '*') || this.is(this.peek(), 'op', '/')) {
        const [, op, ln] = this.next();
        a = ['bin', op, a, this.unary(), ln];
      }
      return a;
    }
    unary() {
      if (this.accept('op', '-')) return ['neg', this.unary()];
      this.accept('op', '+');
      return this.atom();
    }
    atom() {
      const t = this.next();
      const [kind, s, ln] = t;
      if (kind === 'num') return ['num', parseFloat(s)];
      if (kind === 'name') {
        if (this.accept('op', '(')) {
          const args = [];
          if (!this.accept('op', ')')) {
            args.push(this.expr());
            while (this.accept('op', ',')) args.push(this.expr());
            this.expect('op', ')');
          }
          return ['call', s, args, ln];
        }
        return ['var', s, ln];
      }
      if (kind === 'op' && s === '(') {
        const e = this.expr();
        this.expect('op', ')');
        return e;
      }
      return this.err('expected a value, got ' + pyrepr(s || 'end of file'), t);
    }
    stmt() {
      const nameTok = this.expect('name');
      const tok = this.next();
      if (tok[0] !== 'op' || !ASSIGN.includes(tok[1])) this.err('expected one of = += -= *= /=', tok);
      return { name: nameTok[1], op: tok[1], expr: this.expr(), line: nameTok[2], origin: this.origin };
    }
    block() {
      this.expect('op', '{');
      const out = [];
      this.skipNl();
      while (!this.accept('op', '}')) {
        out.push(this.stmt());
        if (!this.is(this.peek(), 'op', '}') && this.peek()[0] !== 'nl') this.err('unexpected ' + pyrepr(this.peek()[1]));
        this.skipNl();
      }
      return out;
    }
  }

  const WORDS = ['param', 'def', 'trait', 'resolve', 'readout', 'group'];

  function parse(text, origin) {
    origin = origin || '<model>';
    const p = new Parser(tokenize(text, origin), origin);
    const out = { params: [], defs: [], traits: [], resolve: [], readout: [] };
    let group = null;
    p.skipNl();
    while (p.peek()[0] !== 'eof') {
      const tok = p.next();
      const word = tok[1], ln = tok[2];
      if (tok[0] !== 'name' || !WORDS.includes(word)) p.err('expected param, def, trait, resolve, readout or group, got ' + pyrepr(word), tok);
      if (word === 'group') {
        group = p.expect('str')[1].slice(1, -1);
        p.endStmt();
      } else if (word === 'param') {
        const name = p.expect('name')[1];
        p.expect('op', '=');
        const e = p.expr();
        const meta = p.accept('op', '|') ? p.meta() : {};
        if (group && !('group' in meta)) meta.group = group;
        out.params.push({ name, expr: e, meta, line: ln, origin });
        p.endStmt();
      } else if (word === 'def') {
        const name = p.expect('name')[1];
        p.expect('op', '(');
        const params = [];
        if (!p.accept('op', ')')) {
          for (;;) {
            const pn = p.expect('name')[1];
            params.push([pn, p.accept('op', '=') ? p.expr() : null]);
            if (!p.accept('op', ',')) break;
          }
          p.expect('op', ')');
        }
        p.expect('op', '=');
        out.defs.push({ name, params, body: p.expr(), line: ln, origin });
        p.endStmt();
      } else if (word === 'trait') {
        const name = p.expect('name')[1];
        const meta = p.accept('op', '|') ? p.meta() : {};
        out.traits.push({ name, meta, stmts: p.block(), line: ln, origin });
        p.endStmt();
      } else {
        out[word === 'resolve' ? 'resolve' : 'readout'].push(...p.block());
        p.endStmt();
      }
    }
    return out;
  }

  const dom = (v) => { if (!Number.isFinite(v)) throw new Error('math domain error'); return v; };
  const BUILTINS = {
    exp: [1, Math.exp], log: [1, (x) => { if (x <= 0) throw new Error('math domain error'); return Math.log(x); }],
    sqrt: [1, (x) => { if (x < 0) throw new Error('math domain error'); return Math.sqrt(x); }],
    abs: [1, Math.abs], tanh: [1, Math.tanh], pow: [2, (a, b) => dom(Math.pow(a, b))],
    min: [-1, (...a) => Math.min(...a)], max: [-1, (...a) => Math.max(...a)],
    pos: [1, (x) => Math.max(0, x)], neg: [1, (x) => Math.min(0, x)], ageU: [1, (x) => -Math.abs(x)],
    cube: [1, (x) => x * x * x], sq: [1, (x) => x * Math.abs(x)],
    sat: [1, (x) => Math.tanh(2 * x) / Math.tanh(2)], sig: [1, (x) => 1 / (1 + Math.exp(-x))],
    clamp: [3, (x, a, b) => Math.max(a, Math.min(b, x))],
  };

  class Evaluator {
    constructor(funcs) { this.funcs = funcs; }
    eval(e, scope, origin, depth) {
      origin = origin || '<model>';
      depth = depth || 0;
      if (depth > 60) throw new ModelError('function call nesting too deep', null, origin);
      const k = e[0];
      const ev = (x) => this.eval(x, scope, origin, depth);
      switch (k) {
        case 'num': return e[1];
        case 'var':
          if (!(e[1] in scope)) throw new ModelError('unknown name ' + pyrepr(e[1]), e[2], origin);
          return scope[e[1]];
        case 'neg': return -ev(e[1]);
        case 'if': return ev(ev(e[1]) ? e[2] : e[3]);
        case 'or': return (ev(e[1]) || ev(e[2])) ? 1 : 0;
        case 'and': return (ev(e[1]) && ev(e[2])) ? 1 : 0;
        case 'not': return ev(e[1]) ? 0 : 1;
        case 'cmp': {
          const a = ev(e[2]), b = ev(e[3]);
          const r = { '<': a < b, '>': a > b, '<=': a <= b, '>=': a >= b, '==': a === b, '!=': a !== b }[e[1]];
          return r ? 1 : 0;
        }
        case 'bin': {
          const a = ev(e[2]), b = ev(e[3]);
          if (e[1] === '+') return a + b;
          if (e[1] === '-') return a - b;
          if (e[1] === '*') return a * b;
          if (b === 0) throw new ModelError('division by zero', e[4], origin);
          return a / b;
        }
        default: break;
      }
      const name = e[1], ln = e[3];
      const args = e[2].map(ev);
      if (Object.prototype.hasOwnProperty.call(this.funcs, name)) {
        const f = this.funcs[name];
        if (args.length > f.params.length) throw new ModelError(name + ' takes at most ' + f.params.length + ' arguments', ln, origin);
        const local = Object.create(scope);
        f.params.forEach(([pn, def], i) => {
          if (i < args.length) local[pn] = args[i];
          else if (def !== null) local[pn] = this.eval(def, local, f.origin, depth + 1);
          else throw new ModelError(name + ' is missing argument ' + pyrepr(pn), ln, origin);
        });
        return this.eval(f.body, local, f.origin, depth + 1);
      }
      if (Object.prototype.hasOwnProperty.call(BUILTINS, name)) {
        const [arity, fn] = BUILTINS[name];
        if (arity >= 0 && args.length !== arity) throw new ModelError(name + '(): wrong number of arguments', ln, origin);
        try {
          const r = fn(...args);
          if (!Number.isFinite(r) && args.every(Number.isFinite)) throw new Error('math range error');
          return r;
        } catch (exc) {
          throw new ModelError(name + '(): ' + exc.message, ln, origin);
        }
      }
      throw new ModelError('unknown function ' + pyrepr(name), ln, origin);
    }
    apply(op, cur, v, line, origin) {
      if (op === '=') return v;
      if (op === '+=') return cur + v;
      if (op === '-=') return cur - v;
      if (op === '*=') return cur * v;
      if (v === 0) throw new ModelError('division by zero', line, origin);
      return cur / v;
    }
  }

  const dict = () => Object.create(null);

  class Model {
    constructor() {
      this.params = dict(); this.meta = dict(); this.funcs = dict(); this.traits = dict();
      this.resolve = []; this.readout = dict();
      this.ev = new Evaluator(this.funcs);
    }
    add(text, origin) {
      const prog = parse(text, origin);
      for (const d of prog.defs) this.funcs[d.name] = d;
      for (const p of prog.params) {
        this.params[p.name] = this.ev.eval(p.expr, Object.create(this.params), p.origin);
        this.meta[p.name] = p.meta;
      }
      for (const t of prog.traits) this.traits[t.name] = t;
      this.resolve.push(...prog.resolve);
      for (const st of prog.readout) {
        if (st.op !== '=') throw new ModelError('readout statements must use =', st.line, st.origin);
        this.readout[st.name] = st;
      }
      return this;
    }
    validate() {
      const lists = Object.values(this.traits).map((t) => t.stmts).concat([this.resolve]);
      for (const stmts of lists) {
        for (const st of stmts) {
          if (!(st.name in this.params)) throw new ModelError('unknown parameter ' + pyrepr(st.name), st.line, st.origin);
        }
      }
      return this;
    }
    traitInfo() {
      const out = {};
      for (const [n, t] of Object.entries(this.traits)) {
        out[n] = { label: t.meta.label !== undefined ? t.meta.label : n, group: t.meta.group || '', help: t.meta.help || '' };
      }
      return out;
    }
    defaultPersona() {
      const out = {};
      for (const n of Object.keys(this.traits)) out[n] = 0;
      return out;
    }
    normalizePersona(persona) {
      const out = this.defaultPersona();
      for (const [k, v] of Object.entries(persona || {})) {
        if (k in out) {
          const x = Number(v);
          if (!Number.isNaN(x)) out[k] = Math.max(-1, Math.min(1, x));
        }
      }
      return out;
    }
    effectiveParams(base, persona) {
      const E = Object.assign(dict(), this.params, base || {});
      const per = this.normalizePersona(persona);
      for (const [name, t] of Object.entries(this.traits)) {
        const value = per[name];
        if (!value) continue;
        const scope = Object.create(E);
        scope.value = value;
        for (const st of t.stmts) E[st.name] = this.ev.apply(st.op, E[st.name], this.ev.eval(st.expr, scope, st.origin), st.line, st.origin);
      }
      for (const [k, m] of Object.entries(this.meta)) {
        if ('min' in m) E[k] = Math.max(m.min, E[k]);
        if ('max' in m) E[k] = Math.min(m.max, E[k]);
      }
      for (const st of this.resolve) E[st.name] = this.ev.apply(st.op, E[st.name], this.ev.eval(st.expr, E, st.origin), st.line, st.origin);
      return E;
    }
    evaluateReadout(inputs, params) {
      const base = Object.assign(Object.create(params), inputs);
      const out = Object.create(base);
      for (const st of Object.values(this.readout)) out[st.name] = this.ev.eval(st.expr, out, st.origin);
      const res = {};
      for (const k of Object.keys(out)) if (!k.startsWith('_')) res[k] = out[k];
      return res;
    }
    paramTable() {
      return Object.entries(this.params).map(([k, v]) => {
        const m = this.meta[k];
        return {
          key: k, label: m.label !== undefined ? m.label : k.replace(/_/g, ' '), group: m.group || 'Other', default: v,
          step: m.step !== undefined ? m.step : null, min: m.min !== undefined ? m.min : null,
          max: m.max !== undefined ? m.max : null, visible: m.visible !== undefined ? m.visible : true,
        };
      });
    }
  }

  /* files: array of [origin, text] in load order: bundled files first, then the optional user model. */
  function loadFromTexts(files) {
    const m = new Model();
    for (const [origin, text] of files) m.add(text, origin);
    return m.validate();
  }

  return { Model, ModelError, parse, tokenize, loadFromTexts, BUILTINS };
});
