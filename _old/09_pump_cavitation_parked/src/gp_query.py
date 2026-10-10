"""Google Patents search (xhr/query) -> list of publication number, priority date, title.

    python src/gp_query.py "<query string in Google Patents syntax>" [num]

Appends every query and its hits to prior_art_raw/gp/_queries.txt (search log for the IDF).
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "prior_art_raw", "gp", "_queries.txt")


def query(q, num=40):
    u = "https://patents.google.com/xhr/query?url=" + urllib.parse.quote("q=%s&num=%d" % (q, num)) + "&exp="
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
    out = []
    for c in json.loads(r)["results"]["cluster"]:
        for x in c["result"]:
            p = x["patent"]
            out.append((p["publication_number"], p.get("priority_date", ""), html.unescape(re.sub("<[^>]+>", "", p["title"]))))
    return out


if __name__ == "__main__":
    q = sys.argv[1]
    hits = query(q, int(sys.argv[2]) if len(sys.argv) > 2 else 40)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n### " + q + "\n")
        for h in hits:
            line = "%s  %s  %s" % h
            f.write(line + "\n")
            print(line[:150])
