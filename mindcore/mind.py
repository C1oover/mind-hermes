"""Mind class: line-by-line port of the v4 JS model. Time in minutes."""
import math
from .tables import CODES, ALIAS, CTRLV, LATENT, VALUE, SIGNED
from .engine import (VALUESET, sig, clip, pos, sgn, lu, ls, soft_or, relax, ctl_p)

_TRACE_KEYS = ("eg", "n", "ew", "es", "ep", "el", "th", "succ", "fail")


class Mind:
    def __init__(self, P):
        self.P = P
        self.z = {"mood": ls(.1), "arousal_tonic": lu(.45), "dominance": lu(.5), "standards_met": 0.0, "seeking": lu(.3),
                  "play": lu(.2), "lust_wanting": lu(.15), "lust_inhibition": lu(.2), "missing_user": lu(.03),
                  "bond": lu(P["bond_baseline"]), "competence": lu(.5), "self_esteem": lu(.5),
                  "arousal_baseline": lu(.5), "mood_baseline": ls(.2), "recent_success": 0.0}
        self.boredom = .1; self.task_commitment = .03; self.sleep_pressure = .3; self.sleep_debt = .3
        self.clock_phase = P["clock_anchor"]
        self.arousal_phasic = 0.0; self.valence_reaction = 0.0; self.threat_trace = 0.0
        self.surprise_trace = 0.0; self.adversity_trace = 0.0
        self.novelty_avg = .3; self.away_min = 0.0; self.expected_gap = 600.0; self.prev_present = 0; self.since_warm = 0.0
        self.habit = {"n": 0.0, "ew": 0.0, "ep": 0.0, "succ": 0.0, "fail": 0.0}
        self.budget = {}; self.weekly = [0.0] * 168; self.out = {}; self.asleep = False
        self.res = {v: 1.0 for v in CTRLV}; self.rate = {v: 0.0 for v in CTRLV}; self.prev = {v: .4 for v in CTRLV}
        self.aStrain = 0.0; self.mStrain = 0.0; self.spillUsed = 0.0; self.circ = 0.0
        self.mood_avg = 0.0; self.arousal_avg = .5

    def value(self, k):
        if k in VALUESET:
            return getattr(self, k)
        z = self.z[k]
        return math.tanh(z) if k in SIGNED else sig(z)

    def effective(self):
        P = self.P
        A = self.value("arousal_baseline"); D = self.sleep_debt
        gp = P["gate_floor_phasic"] + (1 - P["gate_floor_phasic"]) * math.pow(A, 1.5)
        gv = .4 + .6 * A
        bl = 1 / (1 + P["blunting"] * pos(D - .4))
        sc = P["phasic_scale"]
        return (sig(self.z["arousal_tonic"] + gp * sc * math.tanh(self.arousal_phasic / sc)),
                math.tanh(bl * (self.z["mood"] + gv * self.valence_reaction)))

    def certainty(self):
        return sig(1 - 4 * math.tanh(self.surprise_trace))

    def stress(self):
        return soft_or(4 * pos(.5 - self.value("dominance")) * pos(.5 - self.certainty()), math.tanh(2 * self.threat_trace))

    def apply_freeform(self, name, delta):
        P = self.P
        name = ALIAS.get(name, name)
        is_v = name in VALUESET
        if not is_v and name not in self.z:
            return
        f = math.tanh(delta / P["freeform_reference"])
        used = self.budget.get(name, 0.0)
        f = f / (1 + used / P["hammer_scale"])
        self.budget[name] = used + abs(f)
        sg = name in SIGNED
        x = getattr(self, name) if is_v else (math.tanh(self.z[name]) if sg else sig(self.z[name]))
        lo = -1 if sg else 0
        x2 = x + f * (1 - x) if f > 0 else x + f * (x - lo)
        if is_v:
            setattr(self, name, clip(x2))
        else:
            self.z[name] = ls(x2) if sg else lu(x2)

    def step(self, t, dt, inp, env):
        P = self.P; z = self.z
        dec = lambda h: math.pow(2, -dt / h)
        hF = lambda k: P[k] / P["speed_fast"]
        hM = lambda k: P[k] / P["speed_mid"]
        hS = lambda k: P[k] / P["speed_slow"]
        present = inp.get("present") or 0
        load = inp.get("load") or 0
        g_in = inp.get("commit_task") or 0
        gR_in = inp.get("commit_rel") or 0
        demand = inp.get("task_demand") or 0
        a = {k: 0.0 for k in _TRACE_KEYS}
        for k, v in (inp.get("appraisal") or {}).items():
            a[k] = a.get(k, 0.0) + v
        for code, inten in (inp.get("events") or []):
            v = CODES.get(code)
            if v:
                for k, w in v.items():
                    a[k] += w * inten
        a["el"] *= P["lust_gate"]
        sat = P["appraisal_saturation"]
        for k in a:
            a[k] = sat * math.tanh(a[k] / sat)
        for k in self.budget:
            self.budget[k] *= math.pow(2, -dt / (60 if k.startswith("imp_") else P["hammer_half_life"]))
        self.spillUsed *= dec(1440)
        x = {}
        for k in LATENT:
            x[k] = self.value(k)
        for k in VALUE:
            x[k] = getattr(self, k)
        S = self.sleep_pressure; D = self.sleep_debt; A = x["arousal_baseline"]
        C = math.cos(2 * math.pi * (env["hour"] - self.clock_phase) / 24); self.circ = C
        reunion = 0.0
        if present and not self.prev_present and self.away_min > 30:
            if self.away_min > 60:
                self.expected_gap = .8 * self.expected_gap + .2 * self.away_min
            reunion = x["missing_user"]
            z["missing_user"] = lu(x["missing_user"] * P["reunion_keep"])
        self.prev_present = present
        self.away_min = 0.0 if present else self.away_min + dt
        b = int(math.floor(t / 60)) % 168; b2 = (b + 1) % 168
        anticipation = pos(self.weekly[b2] - self.weekly[b])
        overdue = 0.0 if present else pos(self.weekly[b] - present)
        self.weekly[b] += (present - self.weekly[b]) * min(1, dt / 240)
        self.since_warm = 0.0 if a["ew"] > .2 else self.since_warm + dt
        for ch in self.habit:
            self.habit[ch] *= dec(P["habituation_half_life"])
        for ch in ("n", "ew", "ep", "succ", "fail"):
            v = a[ch]
            if v:
                a[ch] = v / (1 + P["habituation_strength"] * self.habit[ch])
                self.habit[ch] += abs(v)
        stress = self.stress(); certainty = self.certainty()
        arousal, mood = self.effective()
        self.mood_avg += (mood - self.mood_avg) * (1 - dec(P["mood_avg_hl"]))
        self.arousal_avg += (arousal - self.arousal_avg) * (1 - dec(P["mood_avg_hl"]))
        kc = P["mood_congruence"] * (S + stress) + P["hormone_congruence"] * env["H_W"]
        gpos = max(.3, 1 - kc); gneg = 1 + kc + P["mood_congruence"] * pos(-mood)
        for k in ("eg", "es"):
            a[k] *= gpos if a[k] > 0 else gneg
        a["ew"] = a["ew"] * gpos * (1 + x["missing_user"] * P["missing_warmth_boost"]) if a["ew"] > 0 else a["ew"] * gneg
        # fast layer
        dph = P["imp_phasic_novelty"] * a["n"] + P["imp_phasic_threat"] * a["th"] + P["imp_phasic_erotic"] * a["el"] + P["imp_phasic_goal"] * abs(a["eg"])
        self.arousal_phasic = self.arousal_phasic * dec(hF("hl_phasic")) + dph + dt * P["imp_phasic_anticipation"] * anticipation
        dvr = P["imp_val_goal"] * a["eg"] + P["imp_val_warm"] * a["ew"] + P["imp_val_standards"] * a["es"] + P["reunion_relief"] * reunion
        self.valence_reaction = self.valence_reaction * dec(hF("hl_valence_reaction")) + dvr + dt * (.15 * anticipation - .1 * overdue)
        self.threat_trace = self.threat_trace * dec(hF("hl_threat")) + a["th"]
        self.adversity_trace = self.adversity_trace * dec(hF("hl_adversity")) + pos(-a["eg"])
        self.surprise_trace = self.surprise_trace * dec(hF("hl_surprise")) + P["surprise_gain"] * clip(a["n"] + .5 * a["fail"], 0, 1)

        def hr(k, xv):
            return max(.1, 1 - xv * xv) if k in SIGNED else max(.1, 4 * xv * (1 - xv))
        z["recent_success"] = relax(z["recent_success"], 0, hF("hl_recent_success"), dt) + hr("recent_success", x["recent_success"]) * (.25 * a["succ"] - .7 * a["fail"])
        rs = sig(z["recent_success"])
        ctl = {}
        for v in CTRLV:
            c = ctl_p(P, v)
            u = arousal if v == "arousal" else x[v]
            excess = pos(u - c["comfort"]); raw = (u - self.prev[v]) / dt
            self.rate[v] += (raw - self.rate[v]) * min(1, dt / 5); self.prev[v] = u
            R = self.res[v] - c["drain"] * excess * dt / 60
            R += (1 - R) * (1 - dec(c["rec"])) * (.3 + .7 * (1 - u)) * (2.5 if self.asleep else 1)
            R = clip(R); self.res[v] = R
            shield = min(.9, c["shield"] * self.task_commitment * (.5 + x["dominance"]))
            ctl[v] = P["ctl_on"] * (-(c["rebound"] * (1 - R) * (1 - R) * (1 - shield)) - c["deriv"] * self.rate[v])
        self.aStrain = clip(self.aStrain * dec(P["strain_hl"]) + P["ctl_on"] * P["strain_gain"] * pos(arousal - P["strain_threshold"]) * dt / 60)
        self.mStrain = clip(self.mStrain * dec(1440) + P["ctl_on"] * P["mood_strain_gain"] * pos(-mood - P["mood_strain_threshold"]) * dt / 60)
        # mid layer
        sl = env["seasonal_light"]; light = env["light"]; W_L = env["pressure_low"]; W_d = env["pressure_drop"]
        H_E = env["H_E"]; H_P = env["H_P"]; H_T = env["H_T"]; H_W = env["H_W"]
        ultra = P["ultradian_amp"] * math.cos(2 * math.pi * t / 90)
        za = (z["arousal_baseline"] + P["circ_arousal"] * C - P["sleep_pressure_arousal"] * (S - .3) + .4 * (x["seeking"] - .3)
              + .4 * x["missing_user"] + .5 * stress + .3 * W_d - .5 * H_P + .3 * H_W + .5 * present * (.5 + load)
              + .3 * anticipation + ultra + P["ctl_on"] * P["demand_gain"] * demand * self.task_commitment + ctl["arousal"])
        z["arousal_tonic"] = relax(z["arousal_tonic"], za, hM("hl_arousal_tonic") * (1 + P["rumination"] * pos(-mood)), dt) + P["carry_phasic_to_arousal"] * dph
        zm = (.7 * z["mood_baseline"] - .5 * x["boredom"] - .6 * pos(S - .6) + .3 * x["standards_met"] + .4 * (rs - .5)
              - .5 * x["missing_user"] - P["weather_mood"] * (.5 * (1 - light) + .3 * W_L + .2 * W_d))
        z["mood"] = relax(z["mood"], zm, hM("hl_mood"), dt) + P["carry_valence_to_mood"] * dvr
        domT = clip(.5 + .5 * (x["competence"] - .5) + .35 * (rs - .5) + .2 * x["standards_met"] - .3 * (S - .3)
                    - .25 * math.tanh(self.surprise_trace) + .15 * H_T, .03, .97)
        z["dominance"] = relax(z["dominance"], lu(domT) + ctl["dominance"], hM("hl_dominance"), dt)
        hls = hM("hl_standards") * (1 + .5 * pos(-mood) * (1 - present)) / (1 + P["sleep_standards_boost"] * (1 if self.asleep else 0))
        z["standards_met"] = relax(z["standards_met"], ls(.8 * (x["self_esteem"] - .5)), hls, dt)
        g = self.task_commitment
        g += (1 - dec(hF("hl_commit"))) * (g_in - g) - dt / 60 * P["giveup"] * self.adversity_trace * (1 - x["dominance"]) * g
        self.task_commitment = g = clip(g)
        gR = gR_in * (.5 + x["bond"]); gateA = .4 + .6 * A
        seekT = clip((.3 + .5 * x["boredom"] + .3 * x["missing_user"] + .15 * x["play"] + .2 * anticipation) * (1 - .6 * S) * (1 - .8 * stress) * (1 - .5 * g) * gateA, .03, .97)
        playT = clip((.15 + .5 * pos(mood) * (1 - stress) * (1 - S) + .2 * gR) * (1 - .4 * g) * gateA, .03, .97)
        wantT = clip(.2 + .5 * x["bond"] * pos(mood) + .7 * gR + P["wanting_deprivation"] * (1 - math.exp(-self.since_warm / P["deprivation_scale"]))
                     + .25 * H_E + .15 * H_T - .3 * H_P - .3 * S, .03, .97)
        inhT = clip(.05 + .3 * g + .5 * stress + .25 * S + .5 * gR * (1 - x["dominance"]) * (1 - x["competence"]) + .2 * H_W + .2 * math.tanh(self.threat_trace), .03, .97)
        z["seeking"] = relax(z["seeking"], lu(seekT) + ctl["seeking"], hM("hl_seeking"), dt)
        z["play"] = relax(z["play"], lu(playT) + ctl["play"], hM("hl_play"), dt)
        z["lust_wanting"] = relax(z["lust_wanting"], lu(wantT) + ctl["lust_wanting"], hM("hl_wanting"), dt)
        z["lust_inhibition"] = relax(z["lust_inhibition"], lu(inhT), hM("hl_inhibition"), dt)
        w = .2 if self.asleep else 1
        o = self.boredom
        u = P["boredom_rate"] * (1 - self.novelty_avg) * (1 - g) * (1 - S) * w
        oS = u / (u + 1)
        o = oS + (o - oS) * math.exp(-dt * (u + 1) / hM("tau_boredom"))
        o = o * (1 - .8 * clip(a["n"], 0, 1)) * math.exp(-.02 * dt * x["seeking"])
        self.boredom = clip(o)
        self.novelty_avg += (a["n"] - self.novelty_avg) * min(1, dt / 30)
        ratio = 0.0 if present else pos((self.away_min - self.expected_gap) / self.expected_gap)
        missT = clip(x["bond"] * (1 - math.exp(-ratio / P["missing_ramp"])) * math.exp(-pos(self.away_min - P["detach_start"]) / P["detach_tau"]) + .15 * x["bond"] * overdue, 0, .97)
        z["missing_user"] = relax(z["missing_user"], lu(missT), hM("hl_missing"), dt)
        imp = {"seeking": P["imp_phasic_novelty"] * a["n"] * (1 - stress), "play": .4 * a["ep"],
               "lust_wanting": .8 * a["el"] + .05 * pos(a["ew"]), "lust_inhibition": .5 * a["th"],
               "dominance": .05 * a["succ"] - .3 * a["fail"] - .8 * a["th"] * (1 - x["dominance"]), "standards_met": .5 * a["es"]}
        for k, val in imp.items():
            dz = clip(hr(k, x[k]) * val, -P["impulse_cap"], P["impulse_cap"])
            used = self.budget.get("imp_" + k, 0.0)
            allow = max(0.0, P["impulse_budget"] - used)
            dzc = clip(dz, -allow, allow)
            z[k] += dzc
            if k == "standards_met":
                z["self_esteem"] += P["carry_standards_to_selfesteem"] * dzc
            self.budget["imp_" + k] = used + abs(dzc)
        # slow layer
        At = clip(.55 - .5 * (D - .3) + .15 * sl + .12 * H_E - .1 * H_W + .1 * (x["bond"] - P["bond_baseline"]) + .1 * x["mood_baseline"]
                  + P["strain_to_baseline"] * self.aStrain + P["slow_follow_arousal"] * (self.arousal_avg - .5), .03, .97)
        z["arousal_baseline"] = relax(z["arousal_baseline"], lu(At), hS("hl_arousal_baseline"), dt)
        mbT = math.tanh(P["mood_baseline_offset"] + .6 * (x["bond"] - P["bond_baseline"]) + .8 * (x["competence"] - .5) + .5 * (x["self_esteem"] - .5)
                        - .6 * pos(D - .5) + .35 * sl + .25 * H_E - .3 * H_W - P["mood_strain_to_baseline"] * self.mStrain + P["slow_follow_mood"] * self.mood_avg)
        z["mood_baseline"] = relax(z["mood_baseline"], ls(mbT), hS("hl_mood_baseline"), dt) + dt * P["bistable"] * x["mood_baseline"] * (1 - x["mood_baseline"] ** 2) / 1440
        inten = math.tanh(pos(self.arousal_phasic) / P["phasic_scale"])
        z["bond"] = relax(z["bond"], lu(P["bond_baseline"]), hS("hl_bond"), dt) + hr("bond", x["bond"]) * (.05 * pos(a["ew"]) - .06 * pos(-a["ew"])) * (1 + P["intensity_bond"] * inten)
        z["competence"] = relax(z["competence"], 0, hS("hl_competence"), dt) + hr("competence", x["competence"]) * (.6 + .8 * math.tanh(self.surprise_trace)) * (.03 * a["succ"] - .1 * a["fail"])
        z["self_esteem"] = relax(z["self_esteem"], lu(.5 + .25 * x["standards_met"] + .2 * (x["competence"] - .5) + .2 * (x["bond"] - P["bond_baseline"])), hS("hl_self_esteem"), dt)
        # spillover with daily cap
        excA = arousal - x["arousal_tonic"]
        excM = mood - math.tanh(z["mood"] / (1 + P["blunting"] * pos(D - .4)))
        fac = max(0.0, 1 - self.spillUsed / P["spill_daily_cap"])
        dA = P["spill_arousal"] * dt * sgn(excA) * pos(abs(excA) - .2) * fac
        dM = P["spill_mood"] * dt * sgn(excM) * pos(abs(excM) - .25) * (.5 + arousal) * fac
        z["arousal_baseline"] += dA; z["mood_baseline"] += dM; self.spillUsed += abs(dA) + abs(dM)
        self.sleep_debt = clip(D + (S - D) * min(1, dt / 2160) + P["spill_debt"] * dt * pos(S - .85) * (1 - D))
        self.asleep = (not present) and C < P["sleep_threshold"] - .1 * env["moon"]
        if self.asleep:
            S *= math.exp(-dt / (P["tau_sleep"] * (1 + P["moon_sleep"] * env["moon"])))
        else:
            S += (1 - S) * (1 - math.exp(-dt * (1 + P["light_fatigue"] * (1 - light)) / P["tau_wake"])) + dt * (P["load_fatigue"] * load + P["stress_fatigue"] * stress) * (1 - S)
        self.sleep_pressure = clip(S)
        ph = self.clock_phase
        if present:
            ph -= P["phase_gain"] * dt * math.sin(2 * math.pi * ((((env["hour"] - (ph - 10)) % 24) + 24) % 24) / 24)
        ph += P["anchor_pull"] * dt / 60 * (P["clock_anchor"] - ph) + (P["clock_period"] - 24) / 1440 * dt
        self.clock_phase = ph
        for n, d in (inp.get("freeform") or []):
            self.apply_freeform(n, d)
        self.readout(present, env, C)

    def readout(self, present, env, C):
        x = {}
        for k in LATENT:
            x[k] = self.value(k)
        for k in VALUE:
            x[k] = getattr(self, k)
        arousal, mood = self.effective(); stress = self.stress(); cert = self.certainty()
        want = x["lust_wanting"]; inh = x["lust_inhibition"]
        desire = want * (1 - inh) * (.4 + .6 * arousal)
        hill = desire ** 3 / (desire ** 3 + .25 ** 3)
        anx = min(1, (.7 * pos(.5 - x["dominance"]) + .7 * pos(.5 - cert) + .3 * pos(-mood)) * min(1, 1.6 * arousal))
        g = x["task_commitment"]; adv = self.adversity_trace
        self.out = {"mood": mood, "arousal": arousal, "dominance": x["dominance"], "certainty": cert, "stress": stress,
                    "standards_met": x["standards_met"], "task_commitment": g, "seeking": x["seeking"], "play": x["play"],
                    "lust_wanting": want, "lust_inhibition": inh, "desire": desire, "desire_expressed": hill * (.2 + .8 * present),
                    "boredom": x["boredom"], "missing_user": x["missing_user"], "bond": x["bond"], "competence": x["competence"],
                    "self_esteem": x["self_esteem"], "sleep_pressure": x["sleep_pressure"], "sleep_debt": x["sleep_debt"],
                    "arousal_baseline": x["arousal_baseline"], "mood_baseline": x["mood_baseline"], "anxiety": anx,
                    "fear": anx * min(1, 3 * self.threat_trace), "determination": g * (1 - x["sleep_pressure"]) * min(1, .3 + 3 * adv),
                    "frustration": g * min(1, 3 * adv) * x["dominance"],
                    "exploration": x["seeking"] * x["dominance"] * (1 - stress) * (1 - x["sleep_pressure"]) * (1 - .6 * g),
                    "tension": arousal * pos(-mood), "excitement": arousal * pos(mood), "calm": (1 - arousal) * pos(mood),
                    "lethargy": (1 - arousal) * pos(-mood), "efficiency": math.exp(-(arousal - .55) ** 2 / (2 * .04)) * (1 - .5 * x["sleep_pressure"]),
                    "res_arousal": self.res["arousal"], "res_seeking": self.res["seeking"], "res_play": self.res["play"],
                    "res_wanting": self.res["lust_wanting"], "res_dominance": self.res["dominance"],
                    "strain_arousal": self.aStrain, "strain_mood": self.mStrain, "circadian": (C + 1) / 2, "light": env["light"],
                    "cycle_estrogen": env["H_E"], "cycle_progesterone": env["H_P"], "moon": env["moon"], "present": present,
                    "clock_phase": self.clock_phase}
