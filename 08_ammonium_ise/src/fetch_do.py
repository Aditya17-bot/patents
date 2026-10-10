"""Cache dissolved-oxygen saturation (do-i-subdaily-pct) for every paired ammonium sonde."""
import json
import os
from concurrent.futures import ThreadPoolExecutor

import core
import ea


def one(s):
    try:
        r = ea.readings(s["station"] + "-do-i-subdaily-pct", s["opened"], s["closed"])
        return s["station"], len(r)
    except Exception as e:
        return s["station"], "error %s" % e


if __name__ == "__main__":
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(one, core.load_sites()))
    core.dump("do_fetch.json", res)
    print(sum(1 for _, n in res if isinstance(n, int) and n > 1000), "sites with DO of", len(res))
