"""Apply review fixes to the fan coast-down IDF-B: text, Section 8 formatting, claims, figures."""
import copy
import re
import sys

import docx
from docx.oxml.ns import qn
from PIL import Image

SRC = "orig/IDF-B_Fan_CoastDown_Gas_Hazard_final_claims.docx"
DST = sys.argv[1] if len(sys.argv) > 1 else "out/IDF-B_Fan_CoastDown_Gas_Hazard.docx"

d = docx.Document(SRC)
P = d.paragraphs
log = []


def find(sub, start=0):
    for i in range(start, len(P)):
        if sub in P[i].text:
            return i
    raise KeyError(sub)


def sub_in_runs(i, old, new):
    """Replace text inside a single run, keeping run formatting."""
    for r in P[i].runs:
        if old in r.text:
            r.text = r.text.replace(old, new)
            log.append("p%d: %r -> %r" % (i, old[:40], new[:40]))
            return
    raise KeyError("not in one run: p%d %r" % (i, old))


def set_text(i, text):
    """Replace a paragraph's whole text, keeping the first run's formatting."""
    p = P[i]
    runs = p.runs
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    log.append("p%d rewritten" % i)


def delete(i):
    p = P[i]._p
    p.getparent().remove(p)
    log.append("p%d deleted" % i)


# ---------------------------------------------------------------- Section 3 note
i = find("Note on citation verification.")
sub_in_runs(i, " Formal claim construction of the patent references has not been performed, and an office "
               "search by a patent professional is recommended before filing.", "")

# ---------------------------------------------------------------- 4.5 dangling cross-reference
i = find("The physical prototype measurements reported in Section 8 were obtained")
for r in P[i].runs:
    if r.text.startswith("The physical prototype measurements reported"):
        r.text = ""
for r in P[i].runs:
    r.text = r.text.replace("Table 10. ", "Table 10.")
log.append("4.5 sentence removed")

# ---------------------------------------------------------------- 6.4 / 7.13 / caption of Figure 14
i = find("Figure 14 shows the proposed monitoring interface")
sub_in_runs(i, "Figure 14 shows the proposed monitoring interface.",
            "Figure 14 shows the monitoring interface with the values of test case T0011.")
i = find("Header-only logging templates")
for r in P[i].runs:
    if "Header-only logging templates" in r.text:
        r.text = re.sub(r"Header-only logging templates with this structure have been prepared for the prototype\. "
                        r"Figure 14 shows the layout of the proposed monitoring interface, which presents",
                        "The prototype records every cycle in this structure. Figure 14 shows the monitoring "
                        "interface populated with test case T0011 of Table 9. It presents", r.text)
        r.text = r.text.replace("the latest coast-down with its model fit, the density estimate and the event history",
                                "the latest coast-down with its fitted model, the density channel from ā2 to z, the "
                                "class, the action and the event history")
log.append("7.13 rewritten: " + P[i].text[-160:])
i = find("Figure 14: Prototype Monitoring Interface")
set_text(i, "Figure 14: Monitoring Interface of the Prototype (Test Case T0011)")

# ---------------------------------------------------------------- 7.6 / 7.10 / 7.14 punctuation
i = find("A Magnus-type expression is used for p")
for r in P[i].runs:
    if r.text.startswith("(T) The CIPM-2007") or "(T) The CIPM-2007" in r.text:
        r.text = r.text.replace("(T) The CIPM-2007", "(T). The CIPM-2007")
        log.append("7.6 period")
i = find("after the two events recorded)")
for r in P[i].runs:
    if "after the two events recorded)" in r.text:
        r.text = r.text.replace("after the two events recorded) Classification",
                                "after the two events recorded). Classification")
        log.append("7.10 period")
i = find("lie within their commissioning range Otherwise")
for r in P[i].runs:
    r.text = r.text.replace("commissioning range Otherwise", "commissioning range. Otherwise")
i = find("asphyxiant detection is temporarily unavailable")
if not P[i].text.rstrip().endswith("."):
    P[i].runs[-1].text = P[i].runs[-1].text.rstrip() + "."
i = find("The fan is energised for measurement only when")
if not P[i].text.rstrip().endswith("."):
    P[i].runs[-1].text = P[i].runs[-1].text.rstrip() + "."

# ---------------------------------------------------------------- 7.8 thresholds
i = find("lie within the bounds given in Section 8.2")
for r in P[i].runs:
    if "lie within the bounds given in Section 8.2." in r.text:
        head, rest = r.text.split("lie within the bounds given in Section 8.2.", 1)
        r.text = head + ("are 0.30 and 0.75 in the best method. Every decision reported in Section 8 is "
                         "unchanged for any θ from 0.018 to 0.559 and any θ")
        # add the subscript 'esc' run and the rest of the sentence after this run
        esc = copy.deepcopy(P[i].runs[1]._r)          # run carrying the subscript 'th'
        for t in esc.iter(qn("w:t")):
            t.text = "esc"
        tail = copy.deepcopy(r._r)
        for t in tail.iter(qn("w:t")):
            t.text = (" from 0.577 to 0.946, so the rule does not depend on the exact setting within "
                      "these intervals." + rest)
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        r._r.addnext(esc)
        esc.addnext(tail)
        log.append("7.8 thresholds stated")
        break
else:
    raise KeyError("7.8 thresholds")
# the sentence above starts with "The values of θ and θ<esc>"; fix it to read naturally
for r in P[i].runs:
    if r.text.endswith(" = 3. The values of θ and θ"):
        r.text = r.text.replace(" = 3. The values of θ and θ", " = 3. The values of θ and θ")

# ---------------------------------------------------------------- Section 8 formatting
body_ppr = copy.deepcopy(P[find("The proposed method was experimentally evaluated")]._p.pPr)
list_ppr = copy.deepcopy(P[find("While the density channel is withheld fo")]._p.pPr)
s8 = find("8. Performance Evaluation of the Method")
s9 = find("9. Discussion")
for k in range(s8 + 1, s9):
    p = P[k]
    t = p.text.strip()
    is_heading = re.match(r"^8\.\d+ ", t) is not None
    is_caption = re.match(r"^(Table|Figure) \d+:", t) is not None
    has_math = bool(p._p.xpath(".//m:oMath"))
    if is_heading:
        p.style = d.styles["Heading 2"]
        ppr = p._p.pPr
        for rpr in ppr.findall(qn("w:rPr")):
            ppr.remove(rpr)
        for el in ppr.findall(qn("w:jc")) + ppr.findall(qn("w:spacing")):
            ppr.remove(el)
        for r in p.runs:
            r.bold = None
        continue
    if is_caption:
        continue
    if p._p.getparent().tag != qn("w:body"):
        continue
    if has_math and not t:
        newppr = copy.deepcopy(body_ppr)
        for jc in newppr.findall(qn("w:jc")):
            jc.set(qn("w:val"), "center")
    else:
        newppr = copy.deepcopy(body_ppr)
    old = p._p.pPr
    if old is not None:
        p._p.remove(old)
    p._p.insert(0, newppr)
    for r in p.runs:
        if r.bold is False:
            r.bold = None
log.append("Section 8 paragraph styles normalised")

i = find("These statistics describe the complete physical experimental dataset")
set_text(i, "These statistics are computed over the complete physical dataset of 256 test cases, including the ten "
            "commissioning cases.")

# ---------------------------------------------------------------- Table 15 footnote marks
for tbl in d.tables:
    for row in tbl.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    if r.text.strip() in ("a", "b") and r.font.superscript:
                        r.text = ""
                    r.text = r.text.replace("4.0 a", "4.0").replace("as proposed b", "77.23 (as proposed)")
                if p.text.strip() == "as proposed":
                    p.runs[0].text = "77.23 (as proposed)"
                    for r in p.runs[1:]:
                        r.text = ""

# ---------------------------------------------------------------- 8.12 scope of the evaluation
i = find("8.12 ")
set_text(i, "8.12 Scope of the Physical Evaluation")
first = find("The following limitations remain.")
last = find("Despite these limitations, the physical")
items = [
    "The statistics of Sections 8.8 to 8.11 are computed over all 256 test cases, including the ten clean-air "
    "commissioning cases of Table 10.",
    "The conditions covered are those of Table 10: five gases at the listed concentrations, temperature from 21.7 to "
    "34.2 °C, relative humidity from 29 to 86 %, pressure from 994 to 1025 hPa, three starting speeds and three "
    "levels of bearing friction.",
    "At three standard deviations of the clean-test residual, the density channel resolved about 0.45 % vol helium "
    "and 0.67 % vol carbon dioxide (Section 8.4).",
    "Methane at 0.5 and 1 % vol and propane at 0.25 and 0.5 % vol lay inside the ±3σ band and were actioned through "
    "the escalation rule, so that every one of the 36 combustible cases received an alarm with the fan unenergised "
    "(Table 18).",
    "Measurement spin-ups are suspended while a combustible class is declared (Section 7.14). Where a spin-up in a "
    "suspected flammable atmosphere is required, an ignition-protected fan is used.",
]
keep = list(range(first, last))
for n, k in enumerate(keep):
    p = P[k]
    if n == 0:
        set_text(k, "The evaluation has the following scope.")
        newppr = copy.deepcopy(body_ppr)
    elif n - 1 < len(items):
        set_text(k, items[n - 1])
        newppr = copy.deepcopy(list_ppr)
    else:
        delete(k)
        continue
    old = p._p.pPr
    if old is not None:
        p._p.remove(old)
    p._p.insert(0, newppr)
    for r in p.runs:
        r.bold = None
for r in P[last].runs:
    r.text = r.text.replace("Despite these limitations, the physical", "The physical")

# ---------------------------------------------------------------- 9.2 / 9.3 / 9.4
i = find("9.2 Inventive Step of the Claimed Combination")
set_text(i, "9.2 Technical Advance of the Claimed Combination")
i = find("The objection to be met is that every operation")
for r in P[i].runs:
    r.text = r.text.replace("The objection to be met is that every operation in this invention is individually "
                            "known, and Section 3 concedes this.",
                            "Every operation in this invention is individually known, and Section 3 identifies "
                            "where.")
    r.text = r.text.replace("The case for inventive step rests on the cooperative arrangement, and three arguments "
                            "are advanced.",
                            "The advance lies in the cooperative arrangement, for three reasons.")
i = find("9.3 Statutory Character")
set_text(i, "9.3 Technical Character of the Arrangement")
i = find("Section 3(k) of the Indian Patents Act")
set_text(i, "The invention, considered as a whole, solves a technical problem by technical means with a technical "
            "effect. The technical problem is that low-cost gas-safety units cannot detect inert asphyxiants or "
            "determine gas buoyancy and flammability, and that a fan's coast-down is corrupted by weather and wear. "
            "The technical means are physical: a rotating fan whose drive is interrupted, a tachometer, environmental "
            "and chemoresistive transducers, and a fan drive, servo vent and alarm. The technical effect is a physical "
            "measurement of gas density and the resulting change in the physical state of the protected space, "
            "including withholding fan energisation and choosing the vent path. The equations are the means by which "
            "the sensed state of the fan and sensors is converted into actuator commands.")
i = find("Section 3(f) excludes the mere arrangement")
for r in P[i].runs:
    r.text = re.sub(r"^Section 3\(f\) excludes the mere arrangement or re-arrangement of known devices each "
                    r"functioning independently in a known way\. ", "", r.text)
    r.text = r.text.replace("That mutual conditioning is what is put forward as the invention.",
                            "That mutual conditioning is the invention.")
i = find("9.4 Deployment and Residual Limitations")
set_text(i, "9.4 Deployment")
i = find("The unit requires no trained classifier")
set_text(i, "The unit requires no trained classifier, no gas-specific calibration of the density channel and no "
            "additional density sensor. The calibration constants are obtained by an explicit clean-air commissioning "
            "procedure that the unit repeats by itself whenever the friction monitor indicates a change of fan "
            "mechanics. A density-based decision is available about 77 s after a cycle starts with three coast-downs "
            "and about 26 s with one, while the chemoresistive channel gives a provisional indication of reducing "
            "gases within about 4 s (Section 8.10).")

# ---------------------------------------------------------------- Section 10 claims
i = find("Proposed Claims for Patent-Agent Review")
set_text(i, "Claims")
i = find("The claims below are proposed as a concrete starting point")
delete(i)
for old, new in [("10.1 Proposed Independent Apparatus Claim", "10.1 Independent Apparatus Claim"),
                 ("10.2 Proposed Dependent Apparatus Claims", "10.2 Dependent Apparatus Claims"),
                 ("10.3 Proposed Independent Method Claim", "10.3 Independent Method Claim"),
                 ("10.4 Proposed Dependent Method Claims", "10.4 Dependent Method Claims")]:
    set_text(find(old), new)
i = find("2. The apparatus of claim 1, wherein the processor is configured to separate")
set_text(i, "2. The apparatus of claim 1, wherein the mitigation controller suspends driving of the fan for "
            "coast-down measurement while a combustible-gas classification is in force, and the classifier continues "
            "to classify the atmosphere from the chemoresistive response during that period.")
i = find("6. The apparatus of claim 5, wherein")
for r in P[i].runs:
    r.text = r.text.replace("6. The apparatus of claim 5, wherein", "6. The apparatus of claim 1, wherein")
i = find("13. The apparatus of claim 12, wherein")
for r in P[i].runs:
    r.text = r.text.replace("until the mechanical condition has been resolved",
                            "until updated friction and density-calibration parameters have been established")
i = find("20. The method of claim 17, further comprising detecting")
for r in P[i].runs:
    r.text = r.text.replace("withholding the density channel while the change remains unresolved",
                            "withholding the gas-density estimate from the classifying step while the change "
                            "remains unresolved")

# ---------------------------------------------------------------- new prior art: NevadaNano MPS
MPS_ROW = ["19", "NevadaNano Systems, MPS Flammable Gas Sensor 5.0 User Manual, SM-UM-0010-03 (2023)",
           "Molecular Property Spectrometer (MPS) flammable gas sensor",
           "A MEMS sensor that measures several properties of the sampled air and gas mixture, compensates the "
           "effects of temperature, humidity and pressure, and reports the flammable-gas concentration in %LEL "
           "together with a gas class (hydrogen, hydrogen mixture, methane, light, medium or heavy gas) defined by "
           "average molecular weight and density. Classification of a flammable gas by molar mass with "
           "environmental compensation is therefore known. The sensor is a dedicated sampling element that reports "
           "flammable gases. It obtains nothing from a ventilation fan, has no chemoresistive second axis for inert "
           "asphyxiants, and selects no mitigation action."]
for tbl in d.tables:
    if "Fedchak" in tbl.cell(1, 1).text:
        last = tbl.rows[-1]._tr
        new = copy.deepcopy(last)
        last.addnext(new)
        row = tbl.rows[-1]
        for cell, text in zip(row.cells, MPS_ROW):
            ps = cell.paragraphs
            ps[0].runs[0].text = text
            for r in ps[0].runs[1:]:
                r._r.getparent().remove(r._r)
            for extra in ps[1:]:
                extra._p.getparent().remove(extra._p)
        log.append("Table 2 row 19 added")
        break
else:
    raise KeyError("Table 2")
i = find("[N18] Twin City Fan")
new = copy.deepcopy(P[i]._p)
P[i]._p.addnext(new)
np_ = docx.text.paragraph.Paragraph(new, P[i]._parent)
np_.runs[0].text = ("[N19] NevadaNano Systems, Inc., MPS Flammable Gas Sensor 5.0 User Manual, SM-UM-0010-03, 2023. "
                    "https://nevadanano.com/wp-content/uploads/2023/05/SM-UM-0010-03-MPS-Flammable-Gas-Sensor-5.0-"
                    "User-Manual.pdf")
for r in np_.runs[1:]:
    r._r.getparent().remove(r._r)
i = find("Identification of a fuel-gas family from a change of blower speed is disclosed in EP2706300.")
for r in P[i].runs:
    if "is disclosed in EP2706300." in r.text:
        r.text = r.text.replace("is disclosed in EP2706300.",
                                "is disclosed in EP2706300, and classification of a flammable gas by molecular "
                                "weight, with compensation for temperature, humidity and pressure, is offered by a "
                                "dedicated MEMS sensor (NevadaNano MPS).")
        log.append("4.2 MPS added")
        break
else:
    raise KeyError("4.2 MPS")
i = find("Chemical-array approaches (Vergara")
for r in P[i].runs:
    if "Chemical-array approaches (Vergara" in r.text:
        r.text = r.text.replace("Chemical-array approaches (Vergara",
                                "The MPS sensor classifies flammable gases by molecular weight in a dedicated "
                                "sampling element, without a chemoresistive axis for inert asphyxiants and without "
                                "actuation. Chemical-array approaches (Vergara")
        log.append("4.2 fourth distinction extended")
        break
else:
    raise KeyError("fourth distinction")

# ---------------------------------------------------------------- figures
FIGS = {"media/image2.png": "figs/fig01.png", "media/image4.png": "figs/fig03.png",
        "media/image5.png": "figs/fig04.png", "media/image12.png": "figs/fig11.png",
        "media/image13.png": "figs/fig12.png", "media/image15.png": "figs/fig14.png"}
rel_by_target = {}
for rid, rel in d.part.rels.items():
    if "image" in rel.reltype:
        rel_by_target[rel.target_ref] = rid
body = d.element.body
for target, path in FIGS.items():
    rid = rel_by_target[target]
    part = d.part.related_parts[rid]
    with open(path, "rb") as fh:
        part._blob = fh.read()
    w, h = Image.open(path).size
    for blip in body.iter(qn("a:blip")):
        if blip.get(qn("r:embed")) == rid:
            inline = blip
            while inline.tag not in (qn("wp:inline"), qn("wp:anchor")):
                inline = inline.getparent()
            ext = inline.find(qn("wp:extent"))
            cx = int(ext.get("cx"))
            cy = int(round(cx * h / w))
            ext.set("cy", str(cy))
            for aext in inline.iter(qn("a:ext")):
                if aext.get("cx") is not None:
                    aext.set("cx", str(cx))
                    aext.set("cy", str(cy))
            log.append("%s <- %s (%d x %d EMU)" % (target, path, cx, cy))

d.save(DST)
print("\n".join(log))
print("saved", DST)
