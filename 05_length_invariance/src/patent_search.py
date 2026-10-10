"""Patent search on Google Patents (xhr query endpoint) for the claims of the IDF-B.

Results (id, title, priority date, snippet) are written to patent/search_2026-09-30.json.
Snippets are search-engine text and are never quoted in the IDF-B; any hit that matters
is downloaded and read in full before anything is said about it.
"""
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "patent", "search_2026-09-30.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"

QUERIES = [
    '("length class" OR "length bin" OR "length classification") (detector OR sensor) (calibrat* OR correct*) (adjacent OR neighboring OR neighbouring OR upstream OR downstream)',
    '("vehicle length distribution") (calibrat*) (detector OR sensor)',
    '("vehicle length") (offset OR bias) ("loop detector" OR "inductive loop") (calibrat*)',
    '("vehicle classification") (count*) (correct*) (bias) (detector) (adjacent OR neighboring OR upstream)',
    '("traffic sensor" OR "traffic detector") ("cross-calibration" OR "relative calibration" OR "mutual calibration")',
    '("vehicle length") ("self-calibration" OR "auto-calibration" OR "automatic calibration") (distribution) (traffic)',
    '("same vehicles") (detectors) (calibrat*) (length)',
    '("classification data") ("data quality") (adjacent OR neighboring) (stations OR sites) (vehicle length)',
    '(车长 OR 车辆长度) (标定 OR 校准 OR 修正) (相邻 OR 上游 OR 下游) (检测器 OR 线圈)',
    '(车型 OR 车辆分类) (检测器) (偏差 OR 误差) (相邻 OR 上下游) (校正 OR 标定)',
    '("weigh-in-motion" OR WIM) ("auto-calibration" OR "self-calibration") (traffic stream OR "front axle")',
    '("detector") ("length classes") ("reclassif*")',
]


def query(q, after="priority:19900101"):
    url = "q=" + urllib.parse.quote(q) + "&after=" + after + "&num=50"
    full = "https://patents.google.com/xhr/query?url=" + urllib.parse.quote(url) + "&exp="
    req = urllib.request.Request(full, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    out = []
    for cl in d.get("results", {}).get("cluster", []):
        for res in cl.get("result", []):
            p = res.get("patent", {})
            clean = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()
            out.append({"id": res.get("id", "").replace("patent/", ""),
                        "title": clean(p.get("title")), "priority": p.get("priority_date"),
                        "assignee": clean(p.get("assignee")), "snippet": clean(p.get("snippet"))[:300]})
    return d.get("results", {}).get("total_num_results"), out


def main():
    report = []
    for q in QUERIES:
        try:
            n, rows = query(q)
        except Exception as e:
            report.append({"query": q, "error": str(e)})
            print("ERR", q[:60], e)
            continue
        report.append({"query": q, "total": n, "results": rows})
        print("\n##", n, q[:110])
        for r in rows[:25]:
            print("  %-18s %s | %s | %s" % (r["id"], r["priority"], r["title"][:80], r["assignee"][:30]))
        time.sleep(2)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
