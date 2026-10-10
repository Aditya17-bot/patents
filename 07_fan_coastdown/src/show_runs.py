import docx, sys
d = docx.Document('orig/IDF-B_Fan_CoastDown_Gas_Hazard_final_claims.docx')
keys = sys.argv[1:]
for i, p in enumerate(d.paragraphs):
    t = p.text
    if any(k in t for k in keys):
        print(i, p.style.name, len(p.runs), [r.text[:40] for r in p.runs][:12])
