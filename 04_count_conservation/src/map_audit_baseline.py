"""Does the self-derived limit matter? The map audit against fixed thresholds.

map_audit.py flags a map relation when its residual exceeds a limit derived from the counts
(FLOOR_MULTIPLE x the median residual of adjacent detector pairs, from discover2). The
obvious alternative is a fixed balance tolerance - "a junction should balance to within
x % of flow" - of the kind used in manual count validation. This runs the identical
corruptions (same generator, same draws as map_audit.py) and the uncorrupted-map control,
then scores every threshold on one set of residuals:

  - the self-derived limit of each corridor;
  - fixed thresholds FIXED (% of flow), applied identically to both corridors.

The question is not whether some fixed number does as well on one corridor - one can
always be tuned after the fact - but whether any single fixed number does as well on both
corridors at once, which is what an operator without the self-derived limit would need.
Writes results/map_audit_baseline.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset, discover, evaluate
from map_audit import KINDS, corrupt, residual_pct, self_limit

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CORRIDORS = (("M25", "window_full_M25_A.json"), ("M1", "window_M1_A.json"))
FIXED = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0)


def residual_sets(manifest, trials=60, seed=0):
    c = dataset.load(manifest)
    vol, obs = c.volumes, c.observed
    truth = [t for t in discover.truth_relations(c, evaluate.fit_node_signs(c)) if len(t) >= 2]
    limit = self_limit(vol, obs)
    ctrl = [residual_pct(t, vol, obs) for t in truth]
    # same selection and same draws as map_audit.main
    clean = [t for t, r in zip(truth, ctrl) if r is not None and r <= limit]
    rng = np.random.default_rng(seed)
    corrupted = {}
    for kind in KINDS:
        res, done = [], 0
        for _ in range(trials * 5):
            if done >= trials:
                break
            i = int(rng.integers(len(clean)))
            bad = corrupt(clean[i], kind, c.shape[0], rng)
            if bad is None:
                continue
            r = residual_pct(bad, vol, obs)
            if r is None:
                continue
            done += 1
            res.append(r)
        corrupted[kind] = res
    return limit, [r for r in ctrl if r is not None], corrupted


def score(thr, ctrl, corrupted):
    det = {k: round(float(np.mean([r > thr for r in v])), 4) for k, v in corrupted.items()}
    return {"threshold_pct": round(thr, 3),
            "control_flag_rate": round(float(np.mean([r > thr for r in ctrl])), 4),
            "detection": det,
            "mean_detection": round(float(np.mean(list(det.values()))), 4)}


def main():
    out = {"fixed_thresholds": list(FIXED), "corridors": {}}
    for name, manifest in CORRIDORS:
        limit, ctrl, corrupted = residual_sets(manifest)
        res = {"self_derived": score(limit, ctrl, corrupted),
               "fixed": [score(t, ctrl, corrupted) for t in FIXED]}
        out["corridors"][name] = res
        print(name, "self", res["self_derived"], flush=True)
        for s in res["fixed"]:
            print(name, "fixed", s, flush=True)
    # for each fixed threshold: does it match the self-derived limit on both corridors?
    # "match" = detection no lower AND control flag rate no higher, on each corridor
    verdict = []
    for j, t in enumerate(FIXED):
        ok = all(out["corridors"][n]["fixed"][j]["mean_detection"]
                 >= out["corridors"][n]["self_derived"]["mean_detection"]
                 and out["corridors"][n]["fixed"][j]["control_flag_rate"]
                 <= out["corridors"][n]["self_derived"]["control_flag_rate"]
                 for n, _ in CORRIDORS)
        verdict.append({"threshold_pct": t, "matches_self_derived_on_both": ok})
    out["verdict"] = verdict
    with open(os.path.join(RESULTS, "map_audit_baseline.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(verdict)


if __name__ == "__main__":
    main()
