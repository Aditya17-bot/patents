"""Phase 1 — build a corridor graph on which the conservation identity can be written.

A MIDAS site name carries everything needed:

    MIDAS site at M25/4055A priority 1 on link 199123501; GPS Ref: ...; Clockwise
                      ^^^^^ marker: number = chainage, letter = role

Roles observed in the feed: A and B are the two mainline carriageways; J and K are slip
roads associated with the A carriageway; L and M are slip roads associated with the B
carriageway. Which of J/K is an entry and which is an exit is *not* assumed here — it is
left for Phase 2 to determine from the volume balance itself, so the topology is derived
from data rather than from folklore about the naming scheme.

A node is the boundary between two consecutive mainline sites, together with every slip
site whose chainage falls between them. The identity to be tested at each node is

    upstream_mainline + sum(entry slips) - sum(exit slips) = downstream_mainline
"""

import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import webtris

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

# Which marker letters belong to which carriageway.
MAINLINE = {"A": "A", "B": "B"}
SLIPS = {"J": "A", "K": "A", "L": "B", "M": "B"}


def parse_marker(marker):
    """'4055A' -> (4055, 'A'). Returns (None, None) if it does not fit the scheme."""
    if not marker:
        return None, None
    m = re.match(r"^(\d+)([A-Z])(\d*)$", marker)
    if not m:
        return None, None
    return int(m.group(1)), m.group(2)


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def corridor_sites(road, carriageway):
    """Sites on one carriageway of one road, chainage-ordered, roles attached."""
    out = []
    for s in webtris.sites():
        if s["road"] != road:
            continue
        number, letter = parse_marker(s["marker"])
        if number is None:
            continue
        if letter in MAINLINE and MAINLINE[letter] == carriageway:
            role = "mainline"
        elif letter in SLIPS and SLIPS[letter] == carriageway:
            role = "slip"
        else:
            continue
        if s["lat"] is None or s["lon"] is None:
            continue
        out.append(dict(s, chainage=number, letter=letter, role=role))
    out.sort(key=lambda x: (x["chainage"], x["letter"]))
    return out


def chainage_is_ordered(sites, max_gap_m=3000):
    """Check that consecutive mainline chainage numbers are geographically adjacent.

    If the marker number really is chainage, consecutive mainline sites should be a few
    hundred metres apart (MIDAS spacing is nominally 500 m). Large jumps mean the
    ordering assumption is wrong somewhere and the node list cannot be trusted.
    """
    mains = [s for s in sites if s["role"] == "mainline"]
    gaps = []
    for a, b in zip(mains, mains[1:]):
        gaps.append(haversine_m(a["lat"], a["lon"], b["lat"], b["lon"]))
    if not gaps:
        return {"n": 0}
    gaps_sorted = sorted(gaps)
    return {
        "n_mainline": len(mains),
        "n_gaps": len(gaps),
        "median_m": round(gaps_sorted[len(gaps) // 2], 1),
        "p90_m": round(gaps_sorted[int(len(gaps) * 0.9)], 1),
        "max_m": round(gaps_sorted[-1], 1),
        "over_threshold": sum(1 for g in gaps if g > max_gap_m),
        "threshold_m": max_gap_m,
    }


def build_nodes(sites, max_span_m=3000):
    """One node per consecutive mainline pair, carrying the slips that sit between them.

    Slip markers usually share their chainage number with an adjacent mainline marker
    (4055A and 4055J are the same physical location), so a co-located slip is a
    *candidate* for the node on either side of it and the bounds are inclusive. Which
    side it truly belongs to, and whether it adds or removes vehicles, is resolved in
    Phase 2 by choosing the assignment that closes the balance. Slips carried by more
    than one node are flagged ambiguous so that resolution step knows what to test.

    Nodes whose mainline pair is further apart than max_span_m are dropped: a long span
    usually means an intervening junction whose slips are not instrumented, and the
    identity would not close there for reasons that have nothing to do with the method.
    """
    mains = [s for s in sites if s["role"] == "mainline"]
    slips = [s for s in sites if s["role"] == "slip"]

    claims = {}
    for s in slips:
        claims[s["id"]] = 0

    nodes = []
    for up, down in zip(mains, mains[1:]):
        span = haversine_m(up["lat"], up["lon"], down["lat"], down["lon"])
        between = [s for s in slips
                   if up["chainage"] <= s["chainage"] <= down["chainage"]]
        for s in between:
            claims[s["id"]] += 1
        nodes.append({
            "node_id": "%s_%s_%s" % (up["road"], up["marker"], down["marker"]),
            "road": up["road"],
            "direction": up["direction"],
            "upstream": {"id": up["id"], "marker": up["marker"]},
            "downstream": {"id": down["id"], "marker": down["marker"]},
            "slips": [{"id": s["id"], "marker": s["marker"], "letter": s["letter"],
                       "dist_to_upstream_m": round(
                           haversine_m(up["lat"], up["lon"], s["lat"], s["lon"]), 1),
                       "dist_to_downstream_m": round(
                           haversine_m(down["lat"], down["lon"], s["lat"], s["lon"]), 1)}
                      for s in between],
            "span_m": round(span, 1),
            "usable": span <= max_span_m,
        })

    for n in nodes:
        for s in n["slips"]:
            s["ambiguous"] = claims[s["id"]] > 1
    return nodes


def summarise(nodes):
    usable = [n for n in nodes if n["usable"]]
    with_slips = [n for n in usable if n["slips"]]
    slip_ids = {s["id"] for n in usable for s in n["slips"]}
    ambiguous = {s["id"] for n in usable for s in n["slips"] if s["ambiguous"]}
    return {
        "nodes_total": len(nodes),
        "nodes_usable": len(usable),
        "nodes_with_slips": len(with_slips),
        "nodes_plain_continuity": len(usable) - len(with_slips),
        "slips_assigned": len(slip_ids),
        "slips_ambiguous": len(ambiguous),
        "slip_letters": sorted({s["letter"] for n in usable for s in n["slips"]}),
    }


def main(road="M25", carriageway="A"):
    sites = corridor_sites(road, carriageway)
    order = chainage_is_ordered(sites)
    nodes = build_nodes(sites)
    summary = summarise(nodes)

    print("%s carriageway %s" % (road, carriageway))
    print("  sites: %d (%d mainline, %d slip)"
          % (len(sites),
             sum(1 for s in sites if s["role"] == "mainline"),
             sum(1 for s in sites if s["role"] == "slip")))
    print("  chainage ordering check: %s" % json.dumps(order))
    print("  nodes: %s" % json.dumps(summary))

    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, "nodes_%s_%s.json" % (road, carriageway))
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"road": road, "carriageway": carriageway,
                   "ordering_check": order, "summary": summary,
                   "sites": sites, "nodes": nodes}, fh, indent=1)
    print("  wrote %s" % out)
    return nodes


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0] if args else "M25", args[1] if len(args) > 1 else "A")
