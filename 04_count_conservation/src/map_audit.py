"""Auditing a supplied detector map against relations recovered from the counts.

Every method in the prior art takes the network map as an input and trusts it. This asks
the reverse question: given a map, can the counts say where the map is wrong, and what it
should say instead?

A map error is injected into one relation of the surveyed map, of one of four kinds met in
real asset registers:

  sign_flip     an on-slip recorded as an off-slip, or the reverse
  drop_member   a slip-road detector omitted from its junction
  wrong_site    one detector of the junction replaced by a site within six rows of it -
                a mislabelled or mis-registered site identifier
  extra_member  a detector from elsewhere wrongly attached to the junction

The audit sees only the (corrupted) map and the counts. A map relation is flagged when it
fails the same retention test that relations recovered from the counts must pass: its
median residual exceeds the limit discover2 derives from the counts themselves
(FLOOR_MULTIPLE x the median residual of adjacent detector pairs). No map-derived or
corruption-tuned threshold enters.

    flag    <=>  map_relation_residual  >  self-derived retention limit
    repair  =    the tightest recovered relation sharing >= MIN_SHARED detectors and at
                 least half the members of the flagged relation

Revision 2026-09-23. The first rule flagged when an overlapping recovered relation was
RATIO times tighter, with overlap judged as a fraction. For a two-detector map relation a
single shared detector passed that test, so the neighbouring road section was proposed as
the "repair": 22 of the 23 control flags on M25 were of that kind. The rule was replaced on
that structural finding, before the corruption trials were rerun.

The control is the same audit run on the uncorrupted map. A flag there is either a false
flag or a genuine discrepancy between the survey and the counts; both are reported.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset, discover, discover2, evaluate

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

MIN_OVERLAP = 0.5
MIN_SHARED = 2
MIN_INTERVALS = 200
KINDS = ("sign_flip", "drop_member", "wrong_site", "extra_member")


def key(rel):
    items = tuple(sorted(rel.items()))
    flip = tuple(sorted((r, -c) for r, c in rel.items()))
    return min(items, flip)


def residual_pct(rel, vol, obs):
    """Median absolute residual of a signed relation, % of the largest member's flow."""
    rows = list(rel)
    both = np.all(obs[rows], axis=0)
    if both.sum() < MIN_INTERVALS:
        return None
    r = np.zeros(int(both.sum()))
    for row, c in rel.items():
        r += c * vol[row, both]
    flow = max(float(vol[row, both].mean()) for row in rows)
    if flow < 1:
        return None
    return float(np.median(np.abs(r))) / flow * 100.0


def recovered_set(corridor, cache):
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as fh:
            return [{int(r): int(c) for r, c in rel.items()} for rel in json.load(fh)]
    found, _ = discover2.discover(corridor.volumes, corridor.observed)
    rels = [{int(r): int(c) for r, c in f["rows"].items()} for f in found]
    with open(cache, "w", encoding="utf-8") as fh:
        json.dump([{str(r): c for r, c in rel.items()} for rel in rels], fh)
    return rels


def self_limit(vol, obs):
    """Retention limit from the counts alone, exactly as discover2 derives it."""
    adjacent = discover2.ordering_stage(discover2.pair_stage(vol, obs))
    return discover2.FLOOR_MULTIPLE * float(np.median(list(adjacent.values())))


def audit_one(rel, recovered, vol, obs, res_cache, limit):
    """Return (flagged, proposed repair or None, map residual, repair residual)."""
    own = residual_pct(rel, vol, obs)
    if own is None:
        return False, None, None, None
    members = set(rel)
    best, best_res = None, None
    for cand in recovered:
        shared = len(members & set(cand))
        if shared < MIN_SHARED or shared < MIN_OVERLAP * max(len(members), len(cand)):
            continue
        k = key(cand)
        if k not in res_cache:
            res_cache[k] = residual_pct(cand, vol, obs)
        rc = res_cache[k]
        if rc is None:
            continue
        if best_res is None or rc < best_res:
            best, best_res = cand, rc
    if own > limit:
        return True, best, own, best_res
    return False, None, own, best_res


def corrupt(rel, kind, n_sites, rng):
    rel = dict(rel)
    rows = list(rel)
    if kind == "sign_flip":
        slips = rows[2:]
        if not slips:
            return None
        r = slips[rng.integers(len(slips))]
        rel[r] = -rel[r]
    elif kind == "drop_member":
        if len(rows) < 3:
            return None
        r = rows[2 + rng.integers(len(rows) - 2)]
        del rel[r]
    elif kind == "wrong_site":
        # a nearby site, not a random one: a mislabel confuses neighbours
        r = rows[rng.integers(len(rows))]
        others = [s for s in range(max(0, r - 6), min(n_sites, r + 7)) if s not in rel]
        if not others:
            return None
        new = others[rng.integers(len(others))]
        rel[new] = rel.pop(r)
    elif kind == "extra_member":
        others = [s for s in range(n_sites) if s not in rel]
        new = others[rng.integers(len(others))]
        rel[new] = int(rng.choice((-1, 1)))
    return rel


def main(manifest="window_full_M25_A.json", trials=60, seed=0):
    c = dataset.load(manifest)
    vol, obs = c.volumes, c.observed
    n = c.shape[0]
    fitted = evaluate.fit_node_signs(c)
    truth = [t for t in discover.truth_relations(c, fitted) if len(t) >= 2]
    tag = manifest.replace("window_", "").replace(".json", "")
    recovered = recovered_set(c, os.path.join(RESULTS, "recovered2_%s.json" % tag))
    print("%s: %d sites, %d map relations, %d recovered relations"
          % (tag, n, len(truth), len(recovered)), flush=True)

    limit = self_limit(vol, obs)
    print("self-derived retention limit %.3f%% of flow" % limit, flush=True)
    res_cache = {}
    # control: the uncorrupted map
    control = [audit_one(t, recovered, vol, obs, res_cache, limit) for t in truth]
    evaluable = [a for a in control if a[2] is not None]
    false_flags = sum(1 for a in evaluable if a[0])
    print("control: %d of %d map relations flagged (false flags)"
          % (false_flags, len(evaluable)), flush=True)

    # corrupt only relations that pass on the clean map, otherwise a relation that already
    # fails would count as detected whatever was done to it
    clean = [t for t, a in zip(truth, control) if a[2] is not None and not a[0]]
    print("corruptions drawn from %d relations that pass the control" % len(clean), flush=True)
    rng = np.random.default_rng(seed)
    flagged_ctrl = [{"relation": {c.site_ids[r]: v for r, v in t.items()},
                     "residual_pct": round(a[2], 3)}
                    for t, a in zip(truth, control) if a[0]]
    out = {"manifest": manifest, "rule": "residual > self-derived limit",
           "limit_pct": round(limit, 3), "min_shared": MIN_SHARED, "min_overlap": MIN_OVERLAP,
           "map_relations": len(truth), "corruption_pool": len(clean), "recovered_relations": len(recovered),
           "control": {"evaluable": len(evaluable), "false_flags": false_flags,
                       "false_flag_rate": round(false_flags / len(evaluable), 4),
                       "flagged": flagged_ctrl},
           "kinds": {}}
    for kind in KINDS:
        det = rep = done = 0
        for _ in range(trials * 5):
            if done >= trials:
                break
            i = int(rng.integers(len(clean)))
            bad = corrupt(clean[i], kind, n, rng)
            if bad is None or residual_pct(bad, vol, obs) is None:
                continue
            done += 1
            flagged, repair, _, _ = audit_one(bad, recovered, vol, obs, res_cache, limit)
            if flagged:
                det += 1
                if repair is not None and key(repair) == key(clean[i]):
                    rep += 1
        out["kinds"][kind] = {"trials": done, "detected": det, "repaired_exact": rep,
                              "detection_rate": round(det / done, 4) if done else None,
                              "repair_rate": round(rep / done, 4) if done else None}
        print("  %-13s trials %3d  detected %5.1f%%  repaired exactly %5.1f%%"
              % (kind, done, 100 * det / max(done, 1), 100 * rep / max(done, 1)),
              flush=True)

    with open(os.path.join(RESULTS, "map_audit_%s.json" % tag), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote results/map_audit_%s.json" % tag, flush=True)


if __name__ == "__main__":
    main(*(sys.argv[1:2] or ["window_full_M25_A.json"]))
