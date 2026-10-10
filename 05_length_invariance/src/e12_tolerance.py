"""E12 - how many detector units exceed a published length-measurement tolerance?

The FHWA Weigh-in-Motion Pocket Guide, Part 3 (FHWA-PL-18-015, 2018), gives the LTPP
performance requirement for vehicle length as +-1.5 ft or 3 % of the vehicle's overall
length, whichever is longer. For a vehicle near the 520 cm class boundary that is 1.5 ft,
45.72 cm. The offsets of E8 (relative to each chain's median reference) are compared with
it, for units with a bias at 520 cm above 2 points and for all fitted units.

Output: results/e12_tolerance.json
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
TOL_CM = 1.5 * 30.48


def main():
    e8 = json.load(open(os.path.join(RESULTS, "e8_offset_model.json")))
    out = {"tolerance_cm": round(TOL_CM, 2), "roads": {}}
    for road, r in e8["roads"].items():
        out["roads"][road] = {}
        for m, pdm in r["per_detector"].items():
            allu = [abs(v["offset_cm"]) for v in pdm.values() if v["offset_cm"] is not None]
            big = [abs(v["offset_cm"]) for v in pdm.values()
                   if v["offset_cm"] is not None and abs(v["bias"][0]) > e8["big_threshold"]]
            out["roads"][road][m] = {
                "units": len(allu), "units_over_tolerance": sum(x > TOL_CM for x in allu),
                "big_units": len(big), "big_over_tolerance": sum(x > TOL_CM for x in big)}
    print(json.dumps(out, indent=1))
    with open(os.path.join(RESULTS, "e12_tolerance.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
