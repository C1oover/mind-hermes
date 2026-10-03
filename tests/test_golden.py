"""Golden test: Python port must reproduce the JS model (v4) on a fixed 3-day scenario.
Expected values were produced by running the JS model in node on the same inputs."""
import pytest
from mindcore.tables import DEFAULTS
from mindcore.engine import Env
from mindcore.mind import Mind

GOLD = {"299":{"mood":0.0509875113,"arousal":0.4274913293,"dominance":0.5227715142,"bond":0.45,"sleep_pressure":0.0937110255,"lust_wanting":0.1922553548,"missing_user":0.03,"mood_baseline":0.1974651888},"899":{"mood":0.1909346981,"arousal":0.6649016813,"dominance":0.4722028875,"bond":0.4956742341,"sleep_pressure":0.4098654781,"lust_wanting":0.1598389506,"missing_user":0.03,"mood_baseline":0.1940257566},"1499":{"mood":0.3818752016,"arousal":0.3771589151,"dominance":0.3893733384,"bond":0.5698258687,"sleep_pressure":0.3625844378,"lust_wanting":0.1961691026,"missing_user":0.03,"mood_baseline":0.193967356},"1799":{"mood":-0.1723931776,"arousal":0.43095127,"dominance":0.4971849713,"bond":0.5681318289,"sleep_pressure":0.1172431177,"lust_wanting":0.1937621278,"missing_user":0.03,"mood_baseline":0.1946192025},"2399":{"mood":0.1815490724,"arousal":0.6555149031,"dominance":0.4947110974,"bond":0.6121553889,"sleep_pressure":0.4613449789,"lust_wanting":0.1555390858,"missing_user":0.03,"mood_baseline":0.1969336383},"4319":{"mood":0.5223457718,"arousal":0.400159446,"dominance":0.4027801435,"bond":0.7459921944,"sleep_pressure":0.5079118064,"lust_wanting":0.2356975199,"missing_user":0.03,"mood_baseline":0.2285328557}}


def test_matches_js():
    P = dict(DEFAULTS); P["lust_gate"] = 1.0; P["cycle_alpha"] = 0.6
    env = Env(P); m = Mind(P)
    for t in range(3 * 1440):
        h = t % 1440
        pr = 1 if (540 <= h < 600 or 1140 <= h < 1260) else 0
        inp = {"present": pr, "load": .5 if pr else 0, "commit_task": .6 if pr else 0,
               "commit_rel": .3 if pr else 0, "task_demand": .4 if pr else 0}
        if pr and t % 7 == 0:
            inp["appraisal"] = {"eg": .4, "n": .3, "ew": .5, "es": .1, "ep": .2, "el": .2}
        if pr and t % 23 == 0:
            inp["events"] = [("tool_failure" if t % 46 == 0 else "tool_success", 1)]
        if t == 1500:
            inp["freeform"] = [("mood", -3)]
        m.step(t, 1, inp, env.at(t))
        if str(t) in GOLD:
            for k, v in GOLD[str(t)].items():
                assert m.out[k] == pytest.approx(v, abs=1e-8), (t, k)
