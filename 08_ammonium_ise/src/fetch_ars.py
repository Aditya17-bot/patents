"""Raw text of the ARS record of Johnson & Marks (2004), for the prior-art gate."""
import re
import urllib.request

URL = "https://www.ars.usda.gov/research/publications/publication/?seqNo115=170733"
t = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"}),
                           timeout=90).read().decode("utf-8", "replace")
open(r"prior_art_raw\ars_170733.html", "w", encoding="utf-8").write(t)
txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
open(r"prior_art_raw\ars_170733.txt", "w", encoding="utf-8").write(txt)
i = txt.find("Technical Abstract")
print(txt[i:i + 2500] if i >= 0 else txt[:2500])
print(re.findall(r'href="([^"]+\.pdf)"', t)[:5])
