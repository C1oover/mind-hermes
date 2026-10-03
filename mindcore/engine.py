"""Mind engine: port of the JS sandbox model (Env + Mind). Pure Python, no Hermes imports.
Time `t` is in minutes; dt in minutes. STATUS: transcribed, NOT yet verified against JS golden trace."""
import math
from .tables import CODES, ALIAS, CTRLV, LATENT, VALUE, SIGNED

MODEL_VERSION = "1.2"
VALUESET = set(VALUE)


def sig(x):
    return 1 / (1 + math.exp(-max(-30.0, min(30.0, x))))


def clip(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def pos(x):
    return x if x > 0 else 0.0


def sgn(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


def lu(x):
    x = clip(x, .03, .97)
    return math.log(x / (1 - x))


def ls(x):
    return math.atanh(clip(x, -.97, .97))


def soft_or(a, b):
    return 1 - (1 - a) * (1 - b)


def relax(z, zt, hl, dt):
    return zt + (z - zt) * math.pow(2, -dt / hl)


def G(x, m, sd, T):
    d = ((x - m + T / 2) % T + T) % T - T / 2
    return math.exp(-d * d / (2 * sd * sd))


def ctl_p(P, v):
    return {k: P["ctl_%s_%s" % (v, k)] for k in ("comfort", "drain", "rec", "rebound", "shield", "deriv")}


class Env:
    def __init__(self, P):
        self.P = P
        self.lat = P["lat"] * math.pi / 180

    def at(self, t):
        P = self.P
        hour = (t / 60) % 24
        doy = P["start_doy"] + math.floor(t / 1440)
        dec = 23.44 * math.pi / 180 * math.sin(2 * math.pi * (doy - 81) / 365)
        sin_alt = math.sin(self.lat) * math.sin(dec) + math.cos(self.lat) * math.cos(dec) * math.cos(2 * math.pi * (hour - 12) / 24)
        cloud = clip(P["cloud"] + (.25 * math.sin(2 * math.pi * t / (1440 * 2.7)) if P["weather_swing"] > 0 else 0))
        p = P["pressure"] + P["weather_swing"] * math.sin(2 * math.pi * t / (1440 * 4))
        p3 = P["pressure"] + P["weather_swing"] * math.sin(2 * math.pi * (t - 180) / (1440 * 4))
        light = sig(8 * sin_alt) * (1 - .7 * cloud)
        x = math.tan(self.lat) * math.tan(dec)
        daylen = 24 / math.pi * math.acos(clip(-x, -1, 1))
        CL = max(20.0, P.get("cycle_length") or 28.0)
        cd = (((t / 1440 + P["cycle_start_day"]) % CL + CL) % CL) * 28 / CL
        a = P["cycle_alpha"]
        HE = .12 + .6 * G(cd, 13, 2.3, 28) + .28 * G(cd, 21, 3.5, 28)
        HP = .05 + .95 * G(cd, 21.5, 3.2, 28)
        HT = .3 + .7 * G(cd, 13.5, 1.8, 28)
        HW = G(cd, 27, 1.8, 28)
        age = (t / 1440 + P["moon_phase0"]) % 29.53
        moon = P["moon_on"] * G(age, 29.53 / 2 - 4, 2.5, 29.53)
        return {"hour": hour, "light": light, "seasonal_light": (daylen - 12) / 6, "pressure_low": sig((1013 - p) / 8),
                "pressure_drop": sig(-(p - p3) - 2), "H_E": a * (HE - .4), "H_P": a * (HP - .3), "H_T": a * (HT - .4),
                "H_W": a * HW, "moon": moon}
