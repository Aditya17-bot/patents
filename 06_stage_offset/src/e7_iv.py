"""E7: the same left-out-visit test with the base rating applied to every 15-minute stage
(hourly means) instead of to the daily mean stage, on the directions whose 15-minute
records are cached, compared with the daily-mean version on the same visits."""
import json
import os

import numpy as np

import experiments as EX

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
iv = EX.interpolation(EX.load("daily_iv"))
dv = EX.interpolation(EX.load("daily"))
key = lambda q: (q["x"], q["y"], q["day"])
dvk = {key(q): q for q in dv}
common = [(q, dvk[key(q)]) for q in iv if key(q) in dvk]
out = {"n_iv": len(iv), "n_common": len(common),
       "targets": len({q["x"] for q, _ in common}),
       "iv": {"linear": EX.summ([q["e_lin"] for q, _ in common]),
              "method": EX.summ([q["e_hat"] for q, _ in common]),
              "paired": EX.paired([q["e_lin"] for q, _ in common], [q["e_hat"] for q, _ in common])},
       "daily": {"linear": EX.summ([d["e_lin"] for _, d in common]),
                 "method": EX.summ([d["e_hat"] for _, d in common]),
                 "paired": EX.paired([d["e_lin"] for _, d in common], [d["e_hat"] for _, d in common])}}
if common:
    out["r_dev_iv"] = round(float(np.corrcoef([q["dev"] for q, _ in common], [q["true_dev"] for q, _ in common])[0, 1]), 3)
    out["r_dev_daily"] = round(float(np.corrcoef([d["dev"] for _, d in common], [d["true_dev"] for _, d in common])[0, 1]), 3)
json.dump(out, open(os.path.join(ROOT, "results", "e7_iv.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
