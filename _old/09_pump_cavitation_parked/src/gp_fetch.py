"""Fetch a Google Patents page and keep its raw abstract, first claim and description text.

    python src/gp_fetch.py EP2656059B1 US20120234696A1 ...

Writes prior_art_raw/gp/<number>.txt (title, abstract, claims, description), so every
statement about a patent is checked against its own text, not a search summary.
"""
import html
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "prior_art_raw", "gp")


def text(fragment):
    t = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def fetch(num):
    path = os.path.join(OUT, num + ".txt")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    url = "https://patents.google.com/patent/%s/en" % num
    raw = None
    for i in range(6):                  # the site answers 503 when queried too fast
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                                         timeout=120).read().decode("utf-8", "replace")
            break
        except Exception:
            time.sleep(20 * (i + 1))
    if raw is None:
        raise RuntimeError("could not fetch " + url)
    title = re.search(r"<title>(.*?)</title>", raw, re.S)
    abst = re.search(r'<section itemprop="abstract".*?</section>', raw, re.S)
    claims = re.search(r'<section itemprop="claims".*?</section>', raw, re.S)
    desc = re.search(r'<section itemprop="description".*?</section>', raw, re.S)
    out = "TITLE: %s\nURL: %s\n\nABSTRACT: %s\n\nCLAIMS: %s\n\nDESCRIPTION: %s\n" % (
        text(title.group(1)) if title else "", url, text(abst.group(0)) if abst else "",
        text(claims.group(0)) if claims else "", text(desc.group(0)) if desc else "")
    os.makedirs(OUT, exist_ok=True)
    open(path, "w", encoding="utf-8").write(out)
    return out


if __name__ == "__main__":
    for n in sys.argv[1:]:
        t = fetch(n)
        a = t.split("ABSTRACT:")[1].split("CLAIMS:")[0].strip()
        c = t.split("CLAIMS:")[1].split("DESCRIPTION:")[0].strip()
        print("==", n, t.splitlines()[0][:120])
        print("  ABSTRACT:", a[:700])
        print("  CLAIM 1:", c[:900])
