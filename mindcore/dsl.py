"""Tiny model language: params, functions, traits and resolve blocks. No eval/exec."""
import math
import re
from collections import ChainMap


class ModelError(ValueError):
    def __init__(self, msg, line=None, origin=None):
        super().__init__("%s%s: %s" % (origin or "<model>", ":%d" % line if line else "", msg))


TOKEN = re.compile(
    r'(?P<ws>[ \t\r]+|\#[^\n]*)|(?P<nl>\n|;)|(?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)'
    r'|(?P<str>"[^"\n]*")|(?P<name>[A-Za-z_][A-Za-z_0-9]*)|(?P<op>\+=|-=|\*=|/=|==|!=|<=|>=|[-+*/=<>(){},|])')
ASSIGN = ("=", "+=", "-=", "*=", "/=")


def tokenize(text, origin):
    toks, pos, line = [], 0, 1
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:
            raise ModelError("unexpected character %r" % text[pos], line, origin)
        kind, s = m.lastgroup, m.group()
        if kind == "nl":
            toks.append(("nl", s, line))
            line += s == "\n"
        elif kind != "ws":
            toks.append((kind, s, line))
        pos = m.end()
    toks.append(("eof", "", line))
    return toks


class UserFunc:
    def __init__(self, name, params, body, line, origin):
        self.name, self.params, self.body, self.line, self.origin = name, params, body, line, origin


class _Parser:
    def __init__(self, toks, origin):
        self.t, self.i, self.origin = toks, 0, origin

    def peek(self, k=0):
        return self.t[min(self.i + k, len(self.t) - 1)]

    def next(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def err(self, msg, tok=None):
        tok = tok or self.peek()
        raise ModelError(msg, tok[2], self.origin)

    def accept(self, kind, text=None):
        tok = self.peek()
        if tok[0] == kind and (text is None or tok[1] == text):
            return self.next()
        return None

    def expect(self, kind, text=None):
        tok = self.accept(kind, text)
        if not tok:
            self.err("expected %s, got %r" % (text or kind, self.peek()[1] or "end of file"))
        return tok

    def skip_nl(self):
        while self.peek()[0] == "nl":
            self.i += 1

    def end_stmt(self):
        if self.peek()[0] not in ("nl", "eof"):
            self.err("unexpected %r" % self.peek()[1])
        self.skip_nl()

    def meta(self):
        out = {}
        while self.peek()[0] == "name" and self.peek(1)[:2] == ("op", "="):
            key = self.next()[1]
            self.next()
            kind, s, _ = self.next()
            if kind == "str":
                out[key] = s[1:-1]
            elif kind == "num":
                out[key] = float(s)
            elif kind == "name" and s in ("true", "false"):
                out[key] = s == "true"
            else:
                self.err("bad value for %s" % key)
        return out

    def expr(self):
        if self.peek()[:2] == ("name", "if"):
            self.next()
            c = self.expr()
            self.expect("name", "then")
            a = self.expr()
            self.expect("name", "else")
            return ("if", c, a, self.expr())
        a = self.andexpr()
        while self.accept("name", "or"):
            a = ("or", a, self.andexpr())
        return a

    def andexpr(self):
        a = self.notexpr()
        while self.accept("name", "and"):
            a = ("and", a, self.notexpr())
        return a

    def notexpr(self):
        if self.accept("name", "not"):
            return ("not", self.notexpr())
        a = self.arith()
        if self.peek()[0] == "op" and self.peek()[1] in ("<", ">", "<=", ">=", "==", "!="):
            op = self.next()[1]
            return ("cmp", op, a, self.arith())
        return a

    def arith(self):
        a = self.term()
        while self.peek()[:2] in (("op", "+"), ("op", "-")):
            _, op, ln = self.next()
            a = ("bin", op, a, self.term(), ln)
        return a

    def term(self):
        a = self.unary()
        while self.peek()[:2] in (("op", "*"), ("op", "/")):
            _, op, ln = self.next()
            a = ("bin", op, a, self.unary(), ln)
        return a

    def unary(self):
        if self.accept("op", "-"):
            return ("neg", self.unary())
        self.accept("op", "+")
        return self.atom()

    def atom(self):
        kind, s, ln = self.next()
        if kind == "num":
            return ("num", float(s))
        if kind == "name":
            if self.accept("op", "("):
                args = []
                if not self.accept("op", ")"):
                    args.append(self.expr())
                    while self.accept("op", ","):
                        args.append(self.expr())
                    self.expect("op", ")")
                return ("call", s, args, ln)
            return ("var", s, ln)
        if (kind, s) == ("op", "("):
            e = self.expr()
            self.expect("op", ")")
            return e
        self.err("expected a value, got %r" % (s or "end of file"), (kind, s, ln))

    def stmt(self):
        _, name, ln = self.expect("name")
        tok = self.next()
        if tok[0] != "op" or tok[1] not in ASSIGN:
            self.err("expected one of = += -= *= /=", tok)
        return (name, tok[1], self.expr(), ln, self.origin)

    def block(self):
        self.expect("op", "{")
        out = []
        self.skip_nl()
        while not self.accept("op", "}"):
            out.append(self.stmt())
            if self.peek()[:2] != ("op", "}"):
                if self.peek()[0] != "nl":
                    self.err("unexpected %r" % self.peek()[1])
            self.skip_nl()
        return out


def parse(text, origin="<model>"):
    p = _Parser(tokenize(text, origin), origin)
    out = {"params": [], "defs": [], "traits": [], "resolve": [], "readout": []}
    group = None
    p.skip_nl()
    while p.peek()[0] != "eof":
        tok = p.next()
        word, ln = tok[1], tok[2]
        if tok[0] != "name" or word not in ("param", "def", "trait", "resolve", "readout", "group"):
            p.err("expected param, def, trait, resolve, readout or group, got %r" % word, tok)
        if word == "group":
            group = p.expect("str")[1][1:-1]
            p.end_stmt()
        elif word == "param":
            name = p.expect("name")[1]
            p.expect("op", "=")
            e = p.expr()
            meta = p.meta() if p.accept("op", "|") else {}
            if group and "group" not in meta:
                meta["group"] = group
            out["params"].append((name, e, meta, ln, origin))
            p.end_stmt()
        elif word == "def":
            name = p.expect("name")[1]
            p.expect("op", "(")
            params = []
            if not p.accept("op", ")"):
                while True:
                    pn = p.expect("name")[1]
                    params.append((pn, p.expr() if p.accept("op", "=") else None))
                    if not p.accept("op", ","):
                        break
                p.expect("op", ")")
            p.expect("op", "=")
            out["defs"].append(UserFunc(name, params, p.expr(), ln, origin))
            p.end_stmt()
        elif word == "trait":
            name = p.expect("name")[1]
            meta = p.meta() if p.accept("op", "|") else {}
            out["traits"].append({"name": name, "meta": meta, "stmts": p.block(), "line": ln, "origin": origin})
            p.end_stmt()
        else:
            out["resolve" if word == "resolve" else "readout"].extend(p.block())
            p.end_stmt()
    return out


def _sat(x):
    return math.tanh(2 * x) / math.tanh(2)


BUILTINS = {
    "exp": math.exp, "log": math.log, "sqrt": math.sqrt, "abs": abs, "tanh": math.tanh, "pow": math.pow,
    "min": min, "max": max, "pos": lambda x: max(0.0, x), "neg": lambda x: min(0.0, x),
    "ageU": lambda x: -abs(x), "cube": lambda x: x ** 3, "sq": lambda x: x * abs(x), "sat": _sat,
    "sig": lambda x: 1 / (1 + math.exp(-x)), "clamp": lambda x, a, b: max(a, min(b, x)),
}


class Evaluator:
    def __init__(self, funcs):
        self.funcs = funcs

    def eval(self, e, scope, origin="<model>", depth=0):
        if depth > 60:
            raise ModelError("function call nesting too deep", None, origin)
        k = e[0]
        if k == "num":
            return e[1]
        if k == "var":
            if e[1] not in scope:
                raise ModelError("unknown name %r" % e[1], e[2], origin)
            return scope[e[1]]
        if k == "neg":
            return -self.eval(e[1], scope, origin, depth)
        if k == "if":
            return self.eval(e[2] if self.eval(e[1], scope, origin, depth) else e[3], scope, origin, depth)
        if k == "or":
            return 1.0 if (self.eval(e[1], scope, origin, depth) or self.eval(e[2], scope, origin, depth)) else 0.0
        if k == "and":
            return 1.0 if (self.eval(e[1], scope, origin, depth) and self.eval(e[2], scope, origin, depth)) else 0.0
        if k == "not":
            return 0.0 if self.eval(e[1], scope, origin, depth) else 1.0
        if k == "cmp":
            a, b = self.eval(e[2], scope, origin, depth), self.eval(e[3], scope, origin, depth)
            return 1.0 if {"<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b, "==": a == b, "!=": a != b}[e[1]] else 0.0
        if k == "bin":
            a, b = self.eval(e[2], scope, origin, depth), self.eval(e[3], scope, origin, depth)
            if e[1] == "+":
                return a + b
            if e[1] == "-":
                return a - b
            if e[1] == "*":
                return a * b
            if b == 0:
                raise ModelError("division by zero", e[4], origin)
            return a / b
        name, args, ln = e[1], [self.eval(a, scope, origin, depth) for a in e[2]], e[3]
        if name in self.funcs:
            f = self.funcs[name]
            if len(args) > len(f.params):
                raise ModelError("%s takes at most %d arguments" % (name, len(f.params)), ln, origin)
            local = {}
            for i, (pn, default) in enumerate(f.params):
                if i < len(args):
                    local[pn] = args[i]
                elif default is not None:
                    local[pn] = self.eval(default, ChainMap(local, scope), f.origin, depth + 1)
                else:
                    raise ModelError("%s is missing argument %r" % (name, pn), ln, origin)
            return self.eval(f.body, ChainMap(local, scope), f.origin, depth + 1)
        if name in BUILTINS:
            try:
                return BUILTINS[name](*args)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ModelError("%s(): %s" % (name, exc), ln, origin)
        raise ModelError("unknown function %r" % name, ln, origin)

    def apply(self, op, cur, v, line, origin):
        if op == "=":
            return v
        if op == "+=":
            return cur + v
        if op == "-=":
            return cur - v
        if op == "*=":
            return cur * v
        if v == 0:
            raise ModelError("division by zero", line, origin)
        return cur / v
