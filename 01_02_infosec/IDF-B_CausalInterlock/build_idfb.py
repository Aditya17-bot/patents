"""Build the IDF-B disclosure for the causal emission-response interlock.

Layout follows IDF-B_LabelFree_Malpractice_Detection_rev6: twelve numbered
sections, plain prose (no bracketed paragraph numbering), styled tables and
figures with captions below.
"""
import os
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, 'figures')
ASSETS = os.path.join(HERE, 'assets')

BODY_FONT = 'Times New Roman'
TBL_FONT = 'Arial'
HDR_FILL = '1565C0'
ALT_FILL = 'E3F2FD'


# ----------------------------------------------------------------- helpers
def _run(p, text, size=11, bold=False, italic=False, font=BODY_FONT,
         color=None):
    r = p.add_run(text)
    r.font.name = font
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    if color:
        r.font.color.rgb = color
    rpr = r._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rpr.append(rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
        rf.set(qn(a), font)
    return r


def _outline(par, lvl):
    pr = par._p.get_or_add_pPr()
    ol = OxmlElement('w:outlineLvl')
    ol.set(qn('w:val'), str(lvl))
    pr.append(ol)


def h1(doc, text):
    p = doc.add_paragraph()
    _outline(p, 0)
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    _run(p, text, size=13, bold=True)


def h2(doc, text):
    p = doc.add_paragraph()
    _outline(p, 1)
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    _run(p, text, size=11.5, bold=True)


def para(doc, text, lead=None, indent=0.0, size=11, italic=False):
    """A justified body paragraph.  `lead` is set in bold before the text."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.line_spacing = 1.14
    if indent:
        p.paragraph_format.left_indent = Inches(indent)
    if lead:
        _run(p, lead + ' ', size=size, bold=True)
    _run(p, text, size=size, italic=italic)
    return p


def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(12)
    parts = text.split('. ', 1)
    _run(p, parts[0] + '.', size=9.5, bold=True, font=TBL_FONT)
    if len(parts) > 1:
        _run(p, ' ' + parts[1], size=9.5, font=TBL_FONT)


def figure(doc, name, cap, width=6.4):
    doc.add_picture(os.path.join(FIG, name), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.space_before = Pt(8)
    doc.paragraphs[-1].paragraph_format.space_after = Pt(2)
    caption(doc, cap)


def shade(cell, fill):
    cell._tc.get_or_add_tcPr().append(
        parse_xml('<w:shd %s w:fill="%s"/>' % (nsdecls('w'), fill)))


def tcaption(doc, text):
    """Table caption: centred, bold, below the table, as in the IDF-B model."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(12)
    _run(p, text, size=10.5, bold=True)
    return p


def table(doc, headers, rows, cap=None, widths=None, size=9.5,
          align_left_cols=()):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = 'Table Grid'
    t.autofit = False

    trpr = t.rows[0]._tr.get_or_add_trPr()
    trpr.append(OxmlElement('w:tblHeader'))
    for i, htxt in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ''
        pp = c.paragraphs[0]
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pp.paragraph_format.space_after = Pt(2)
        pp.paragraph_format.keep_with_next = True
        _run(pp, htxt, size=size, bold=True)

    last = len(rows)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            c = t.rows[ri + 1].cells[ci]
            c.text = ''
            pp = c.paragraphs[0]
            pp.alignment = (WD_ALIGN_PARAGRAPH.LEFT if ci in align_left_cols
                            else WD_ALIGN_PARAGRAPH.CENTER)
            pp.paragraph_format.space_after = Pt(2)
            if ri + 1 == last:
                pp.paragraph_format.keep_with_next = True
            _run(pp, str(val), size=size)

    if widths:
        for ri in range(len(t.rows)):
            for ci, w in enumerate(widths):
                t.rows[ri].cells[ci].width = Inches(w)

    if cap:
        tcaption(doc, cap)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def bullets(doc, items, indent=0.28):
    for it in items:
        if isinstance(it, tuple):
            para(doc, it[1], lead=it[0], indent=indent, size=10.5)
        else:
            para(doc, it, indent=indent, size=10.5)


def _fld(par, instr, placeholder=''):
    """Insert a Word field code, e.g. PAGE or TOC."""
    r = par.add_run()
    fc = OxmlElement('w:fldChar')
    fc.set(qn('w:fldCharType'), 'begin')
    fc.set(qn('w:dirty'), 'true')
    r._r.append(fc)
    r = par.add_run()
    r.font.name = BODY_FONT
    r.font.size = Pt(11)
    it = OxmlElement('w:instrText')
    it.set(qn('xml:space'), 'preserve')
    it.text = instr
    r._r.append(it)
    r = par.add_run()
    fc = OxmlElement('w:fldChar')
    fc.set(qn('w:fldCharType'), 'separate')
    r._r.append(fc)
    if placeholder:
        _run(par, placeholder, size=11)
    r = par.add_run()
    fc = OxmlElement('w:fldChar')
    fc.set(qn('w:fldCharType'), 'end')
    r._r.append(fc)


def _border_bottom(par, color='CFD8DC'):
    pr = par._p.get_or_add_pPr()
    bd = OxmlElement('w:pBdr')
    bt = OxmlElement('w:bottom')
    bt.set(qn('w:val'), 'single')
    bt.set(qn('w:sz'), '6')
    bt.set(qn('w:space'), '2')
    bt.set(qn('w:color'), color)
    bd.append(bt)
    pr.append(bd)


def _bar(container, left, right, italic_right=True):
    """A borderless two-column strip: left text, right text."""
    grey = RGBColor(0x60, 0x6C, 0x76)
    t = container.add_table(rows=1, cols=2, width=Inches(6.7))
    t.autofit = False
    t.columns[0].width = Inches(4.3)
    t.columns[1].width = Inches(2.4)
    t.rows[0].cells[0].width = Inches(4.3)
    t.rows[0].cells[1].width = Inches(2.4)
    for cell in t.rows[0].cells:
        tcpr = cell._tc.get_or_add_tcPr()
        mar = OxmlElement('w:tcMar')
        for side in ('top', 'left', 'bottom', 'right'):
            e = OxmlElement('w:' + side)
            e.set(qn('w:w'), '0')
            e.set(qn('w:type'), 'dxa')
            mar.append(e)
        tcpr.append(mar)
    pl = t.rows[0].cells[0].paragraphs[0]
    pr = t.rows[0].cells[1].paragraphs[0]
    pr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for p in (pl, pr):
        p.paragraph_format.space_after = Pt(0)
    if isinstance(left, str):
        _run(pl, left, size=8.5, font=TBL_FONT, color=grey)
    else:
        left(pl)
    if isinstance(right, str):
        _run(pr, right, size=8.5, font=TBL_FONT, italic=italic_right, color=grey)
    else:
        right(pr)
    return t, pl, pr


def running_heads(sec):
    """The VIT copyright line at the top right of every page, folio below."""
    sec.different_first_page_header_footer = False

    h = sec.header.paragraphs[0]
    h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    h.paragraph_format.space_after = Pt(0)
    _run(h, '\u00a9VIT IPR & TTCELL', size=11, bold=True)

    f = sec.footer.paragraphs[0]
    f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    f.paragraph_format.space_before = Pt(0)
    _fld(f, ' PAGE ', '1')


def letterhead(doc):
    """The IDF-B masthead block, as in the VIT reference filing: logo and form
    name at the left, the three registry rows at the right, then straight into
    Section 1. No title page and no contents list."""
    t = doc.add_table(rows=3, cols=3)
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False

    left = t.cell(0, 0).merge(t.cell(2, 0))
    left.text = ''
    left.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = left.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(os.path.join(ASSETS, 'vit_logo.png'),
                            width=Inches(1.55))
    _run(p, '  Invention Disclosure Format (IDF)-B', size=9, bold=True)

    for ri, lab in enumerate(('Document No.', 'Issue No/Date', 'Amd. No/Date')):
        c = t.cell(ri, 1)
        c.text = ''
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        pp = c.paragraphs[0]
        pp.paragraph_format.space_before = Pt(3)
        pp.paragraph_format.space_after = Pt(3)
        _run(pp, lab, size=10, bold=True)
        blank = t.cell(ri, 2)
        blank.text = ''
        blank.paragraphs[0].paragraph_format.space_after = Pt(3)

    for ri in range(3):
        t.rows[ri].height = Inches(0.3)
        for ci, w in enumerate((3.05, 1.25, 1.45)):
            t.rows[ri].cells[ci].width = Inches(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)


# ----------------------------------------------------------------- document
def build():
    doc = Document()
    st = doc.styles['Normal']
    st.font.name = BODY_FONT
    st.font.size = Pt(11)
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Inches(0.9)
    sec.top_margin = sec.bottom_margin = Inches(0.85)

    running_heads(sec)
    letterhead(doc)

    # ============================================================== 1
    h1(doc, '1. Title of the Invention')
    para(doc,
         'A Cyber-Physical Apparatus and Method for Detecting Externally Assisted '
         'Malpractice at a Monitored Assessment Station, in which a Photometrically '
         'Measured Question-Onset Anchor, a Covert Acoustic Emission Attributed to the '
         'Seated Candidate by Structure-Borne Coupling, and an Answer-Commit Input-Dynamics '
         'Discontinuity are Interlocked Against a Bounded External-Assistance Latency Band, '
         'and in which Graduated Enforcement Acts Upon the Candidate Input Path Under a '
         'Dual-Channel Actuation Interlock.')

    # ============================================================== 2
    h1(doc, '2. Field / Area of Invention')
    para(doc,
         'The present invention relates to integrity monitoring of supervised assessment '
         'stations, and specifically to the detection of malpractice in which a candidate '
         'obtains an answer from a source outside the station during the examination. More '
         'particularly, it pertains to an apparatus in which transducers disposed at an '
         'individual candidate station measure the instant at which a question is physically '
         'presented on the display, the instant at which a covert acoustic emission is '
         'produced by the seated candidate, and the instant at which an answer is committed '
         'through the input devices, and in which a control arrangement decides whether those '
         'three instants stand in the causal relation that external assistance necessarily '
         'imposes upon them. The invention further relates to the graduated actuation that '
         'follows such a decision, including an in-line unit that physically interrupts the '
         'candidate input path under an interlock condition requiring corroboration from two '
         'physically independent sensing modalities.')
    para(doc,
         'The principal embodiment described herein is a computer-based examination desk. '
         'The invention is not limited to that embodiment: it applies to professional '
         'certification and licensing test centres, secure interview and vetting rooms, '
         'recruitment and aptitude testing facilities, and any supervised environment in '
         'which a task is presented at a known instant, a response is committed through an '
         'instrumented input device, and covert assistance from outside the station is '
         'prohibited.')

    # ============================================================== 3
    h1(doc, '3. Prior Patents and Publications from Literature')
    para(doc,
         'The following table summarises the closest known prior art and identifies the gap '
         'addressed by the present invention. Entries 1 to 7 are assessment-integrity '
         'systems. Entries 8 and 9 are input-path isolation hardware, which supplies the '
         'enforcement component and is expressly conceded. Entries 10 to 12 are the '
         'behavioural and psychometric literature on detecting assisted responding. Entries '
         '13 to 17 are general techniques an examiner may reasonably combine, and each is '
         'addressed directly.')

    pa = [
        ['1', 'US 2019/0156689 A1 — systems and methods for detecting '
              'cheating in online proctoring (ProctorU)', '2019 / patent',
         'Webcam, microphone, keyboard and screen capture. Flags a behavioural sequence: '
         'loss of face for a threshold interval, then resumed keyboard or mouse input, then '
         'answer submission. The session is suspended when the sequence is observed.',
         'The closest reference. Its anchor is the candidate’s own face-loss, an '
         'appearance, rather than a measured display transition, so the sequence carries no '
         'external timing reference. There is no bounded latency band, no attribution of '
         'sound to the seated candidate, and no test separating composition from '
         'transcription. The intervention is a software session suspend: nothing in the '
         'physical input path is interrupted.'],
        ['2', 'US 2017/0263142 A1 — anti-cheating system using eyewear',
         '2016 / patent',
         'Smart glasses display a portion of each question; an iris check gates whether the '
         'display is enabled.',
         'A single gating check on a wearable display. No multi-channel fusion, no timing '
         'relation between events, no escalation state machine, and no enforcement action '
         'upon the candidate’s input devices.'],
        ['3', 'US 9,881,516 B1 — detecting cheating while administering online '
              'assessments', '2018 / patent',
         'Watermarked items seeded to external sites with web beacons, so retrieval of an '
         'item during a test becomes observable.',
         'Detects item leakage on the open web rather than conduct at the station. Silent on '
         'in-room assistance, on sensing, and on intervention.'],
        ['4', 'US 9,154,748 B2 — online examination proctoring system',
         '2015 / patent',
         'Worn and fixed cameras with unpredictable room-sweep prompts; audio capture; '
         'evidence indexed for later review.',
         'Evidence-gathering platform art. Audio is captured but never attributed to a '
         'particular speaker, and review is post-hoc.'],
        ['5', 'US 2012/0135388 A1 — online proctoring with biometric anomaly '
              'detection', '2012 / patent',
         'Continuous biometric identity confirmation during a remote examination, flagging '
         'departures from the enrolled biometric.',
         'Enrolment is used to answer who is present, not to distinguish composing an answer '
         'from transcribing a dictated one. No timing interlock, no actuation.'],
        ['6', 'US 2011/0177484 A1 — secure remote testing with dual capture',
         '2011 / patent',
         'Two camera views of the candidate and workspace, recorded for adjudication.',
         'Platform art, conceded. Adds viewpoints, not a decision rule and not an '
         'intervention.'],
        ['7', 'US 9,601,024 B2 — monitoring of test-taker activity',
         '2017 / patent',
         'Activity monitoring during a computerised test with rule-based flagging.',
         'Rules are specified in advance against observable behaviours. No physical onset '
         'reference and no graduated, rate-limited enforcement.'],
        ['8', 'CN 110414225 B; US 10,515,234; US 10,970,423 — in-line USB data '
              'diodes and peripheral isolation', '2019–2021 / patents',
         'Hardware placed in series with a USB peripheral that permits, blocks or restricts '
         'the data path under an external control signal.',
         'Supplies the enforcement component and is conceded as known. What is not disclosed '
         'is the arrangement that decides when such a unit should act: no sensing, no '
         'corroboration value, no interlock condition governing the control signal.'],
        ['9', 'US 9,734,358 B2 and secure KVM isolation practice',
         '2017 / patent + category',
         'Isolation of keyboard and video paths between security domains, with unidirectional '
         'data enforcement.',
         'Static policy enforcement between domains. The gate state is configured, not '
         'derived from live measurement of the operator.'],
        ['10', 'Kundu et al. — keystroke dynamics against LLM-assisted writing '
               '(arXiv:2406.15335)', '2024 / preprint',
         'TypeNet-family keystroke models distinguish text written unaided from text produced '
         'with a large-language-model assistant. Reported condition-specific accuracy 74.98 % '
         'to 85.72 %.',
         'The published quantitative benchmark for this problem, and software-only. One '
         'modality, no sensor at the desk, no attribution of any acoustic event, no real-time '
         'intervention. It answers whether a passage was assisted, after the fact.'],
        ['11', 'Mehta et al. — follow-up study on paraphrasing conditions '
               '(arXiv:2511.12468)', '2025 / preprint',
         '130 participants; detection degrades as the assisted text is paraphrased before '
         'entry.',
         'Same architecture and the same gap. Establishes that a single input-dynamics '
         'channel is fragile in isolation, which is the reason the present invention refuses '
         'to actuate on one channel.'],
        ['12', 'Preknowledge and answer-copying detection from response times '
               '(Balta & Dogan 2024; and the joint response-time / accuracy literature)',
         '2021–2024 / journals',
         'Item-response and response-time joint models identify examinees whose speed and '
         'accuracy pattern indicates prior knowledge of items or copying.',
         'Cohort-level and offline. Operates on completed response vectors, produces a '
         'statistical flag after the session, and by construction permits no intervention '
         'during it. No sensor, no attribution, no actuation.'],
        ['13', 'Killourhy & Maxion — comparing anomaly detectors for keystroke '
               'dynamics', '2009 / conference',
         'Benchmark corpus and evaluation protocol for keystroke-timing biometrics; '
         'Manhattan-scaled, Mahalanobis and Euclidean detectors against an enrolled profile.',
         'A component of the present invention and used here as the measurement basis for the '
         'discontinuity channel. It teaches verifying identity from typing rhythm. It does '
         'not teach using the deviation as evidence that the candidate is transcribing a '
         'dictated answer, nor tying that deviation to an acoustic event and a display '
         'transition.'],
        ['14', 'Photodiode marking of stimulus onset in psychophysics and '
               'electroencephalography', 'category',
         'A photodiode placed over a patch of the display recovers true stimulus-onset timing '
         'independently of the rendering software.',
         'Standard laboratory instrumentation, conceded as known in its own field. It has not '
         'been applied as an integrity reference at an examination station, nor used as the '
         'origin of a latency band that gates a physical intervention.'],
        ['15', 'Contact and structure-borne pickup for own-voice detection',
         'category',
         'Contact transducers pick up vocalisation conducted through a solid body while '
         'rejecting airborne sound from other sources; used in headsets and hearing devices.',
         'The physical principle is known. Applying it at the desk so that a whisper can be '
         'assigned to the seated candidate rather than to a neighbour, and making that '
         'attribution a precondition of enforcement, is not disclosed.'],
        ['16', 'Dual-channel and two-out-of-two interlocks in safety-instrumented '
               'systems (IEC 61508 practice)', 'category',
         'Actuation of a hazardous or irreversible output is conditioned on agreement between '
         'independent sensing channels.',
         'Established practice in process safety. It is not applied in assessment-integrity '
         'systems, where the actuation in the prior art is a software flag and the question '
         'of channel independence therefore never arises.'],
        ['17', 'Rate limiting, debouncing and hysteresis in control systems',
         'category',
         'Persistence counters, cooldowns and minimum intervals suppress chattering outputs '
         'in feedback controllers.',
         'General technique. Not disclosed as a mechanism whose parameters are set from '
         'measured detector statistics, and not disclosed in combination with an interlock '
         'over independent sensing modalities in this field.'],
    ]
    table(doc, ['#', 'Reference', 'Year / type', 'Core contribution',
                'Limitation with respect to the present invention'],
          pa, widths=[0.30, 1.45, 0.72, 2.06, 2.37], size=8.4,
          align_left_cols=(1, 3, 4))

    para(doc,
         'The search covered patent literature through Google Patents and Espacenet and the '
         'peer-reviewed and preprint literature in educational measurement, biometrics and '
         'multimodal sensing. Across the assessment-integrity entries the common structure is '
         'the same: a detector observes an appearance — a face leaving frame, a hand '
         'crossing a boundary, an unusual typing rhythm — and a threshold on that '
         'appearance produces a flag. Two consequences follow. Detection is bounded by the '
         'appearances anticipated when the system was built, and the flag is at best '
         'circumstantial, because ordinary conduct produces every one of those appearances '
         'routinely.')
    para(doc,
         'The present invention proceeds from a different premise. Externally assisted '
         'answering is not primarily an appearance; it is a closed causal loop with someone '
         'outside the station, and that loop leaves a timing signature that ordinary conduct '
         'cannot produce. The question must be presented before it can be communicated; the '
         'communication must be produced by the seated candidate and not by a neighbour; the '
         'answer cannot be committed sooner than a helper could have supplied it, nor so much '
         'later that no causal link remains; and an answer received from outside is entered '
         'with the input dynamics of transcription rather than of composition. No reference '
         'located by the inventor measures the origin of that loop as a physical event, '
         'attributes its acoustic element to the seated candidate, bounds its latency, tests '
         'its commit for transcription, or conditions a physical interruption of the input '
         'path on two independent modalities agreeing. Entries 8, 9, 13, 14, 15, 16 and 17 '
         'each supply one component of that arrangement and are conceded as such; what is '
         'claimed is the arrangement.')

    # ============================================================== 4
    h1(doc, '4. Summary and Background of the Invention (Gap / Novelty)')
    para(doc,
         'Examination malpractice conducted with an accomplice outside the room has become '
         'the difficult case. The candidate reads the question, murmurs it into a concealed '
         'microphone, receives the answer through a concealed earpiece, and types it. Nothing '
         'in that sequence looks anomalous frame by frame. The candidate faces the screen '
         'throughout, produces no visible device, and types an answer at an ordinary speed. '
         'Detectors built on appearance are therefore working against the grain of the '
         'behaviour they are asked to find, and the published quantitative benchmark for the '
         'single most informative appearance — keystroke dynamics against '
         'machine-assisted writing — sits at 74.98 % to 85.72 % under favourable, '
         'condition-specific evaluation, with degradation when the assisted text is '
         'paraphrased before entry.')
    para(doc,
         'The invention detects the loop rather than the appearance. Three instants are '
         'recovered at the station. A photodiode over a patch of the display panel gives T0, '
         'the instant at which the question actually became visible, measured from emitted '
         'light rather than read from a software event that the examined machine itself '
         'generates. A transducer in contact with the desk gives T1, the instant of a covert '
         'vocal emission, and gives it only when the emission is coupled through the desk '
         'structure, which the candidate’s own speech is and a neighbour’s speech '
         'across an air gap is not. The input devices give T2, the instant at which the '
         'answer was committed. The apparatus then asks whether T2 minus T1 falls inside a '
         'bounded external-assistance latency band and whether the commit dynamics depart '
         'from the candidate’s enrolled profile in the direction characteristic of '
         'transcription. Only when the relation holds is a corroboration value raised, and '
         'only then may enforcement advance.')
    figure(doc, 'fig01.png',
           'Figure 1. The causal relation the interlock tests, and the four grounds on which '
           'it refuses. The apparatus does not ask whether the candidate looks suspicious; it '
           'asks whether three physically measured instants stand in the relation that '
           'external assistance imposes upon them.')
    para(doc,
         'Enforcement is the second half of the invention and, on the evidence of Section 8, '
         'the more substantial half. The output is not a flag. It is a graduated ladder that '
         'ends in an in-line unit physically opening the keyboard data lines, and every rung '
         'of that ladder is rate-limited by a persistence counter, a per-candidate cooldown '
         'and a global session interval that no escalation may bypass. Above the ladder sits '
         'a dual-channel interlock: the two most consequential rungs cannot be reached unless '
         'two physically independent sensing modalities have exceeded threshold within the '
         'same control cycle. No single modality may ever open a candidate’s input path.')
    para(doc,
         'The proposed system comprises: a station-associated sensing assembly comprising a '
         'photometric onset sensor at the display panel, a desk-contact transducer, a desk '
         'inertial unit, an imaging sensor and an input-device interface; a processing unit '
         'deriving per-channel quantities and an ordinal corroboration value from them; a '
         'causal latency interlock evaluating the relation between the measured instants; a '
         'graduated enforcement scheduler; an in-line gating unit disposed in series with the '
         'candidate input path; and an evidence record store.')
    figure(doc, 'fig02.png',
           'Figure 2. System architecture. Physical sensing at the candidate station (100) '
           'supplies the channel-derivation stage; the causal latency interlock (600) and the '
           'corroboration value unit (700) decide eligibility; the graduated enforcement '
           'scheduler (800) and the dual-channel interlock (850) decide whether, and at what '
           'severity, any actuator is permitted to operate.')

    h2(doc, '4.1 Statement of Inventive Step (Non-Obviousness)')
    para(doc,
         'The inventive step does not reside in any element taken alone. Photodiode onset '
         'marking is standard laboratory instrumentation. Contact transducers that favour '
         'own-voice over airborne sound are used in headsets. Keystroke-timing comparison '
         'against an enrolled profile is a mature biometric. In-line USB isolators are sold '
         'as commodity hardware. The invention resides in the following combination, and in '
         'technical effects that no element produces on its own:')
    bullets(doc, [
        ('(a)', 'derivation of the question-onset instant T0 from light emitted by the '
                'display panel itself, rather than from a rendering event reported by the '
                'machine under examination, so that the origin of the timing analysis is a '
                'physical measurement of the panel rather than a report from the '
                'software stack. The effect of this element is not discriminative power. It '
                'is that the anchor is independent of the reported event: where the examined '
                'machine delays or misreports its own rendering, the anchor still marks the '
                'instant at which light actually reached the candidate, and where the machine '
                'suppresses the transition altogether the apparatus obtains no anchor and '
                'records that it has none, rather than accepting a false one. Independence '
                'from the reported event is what is claimed; independence from the machine is '
                'not, since in the principal embodiment the patch is rendered by that machine. '
                'The element further permits an attributed emission to be assigned to one '
                'identified assessment item rather than to the session at large;'),
        ('(b)', 'attribution of a covert acoustic emission to the seated candidate by '
                'requiring coincidence between a structure-borne desk channel and an airborne '
                'channel, so that speech from an adjacent candidate cannot implicate the one '
                'at the instrumented station;'),
        ('(c)', 'evaluation of two bounded intervals rather than one: the interval '
                'between the measured presentation instant and the attributed emission '
                'against a bounded consultation interval, whose lower bound is the shortest '
                'time in which the displayed item could have been apprehended and whose '
                'upper bound is the presentation of the succeeding item; and the interval '
                'between that emission and the answer commit against a bounded '
                'external-assistance latency band, so that an emission too early to be a '
                'reading of the item then displayed, a commit too fast for any helper to '
                'have replied, and a commit too late to bear a causal relation, are each '
                'rejected on stated grounds;'),
        ('(d)', 'a test of the commit itself against an enrolled input-dynamics profile of '
                'the same candidate, directed not at identity but at the distinction between '
                'composing an answer and transcribing one received from elsewhere;'),
        ('(e)', 'application of one desk inertial measurement at two separate points in the '
                'decision — lowering the confidence threshold demanded of the imaging '
                'channel while raising the weight given to the acoustic channel — so '
                'that a single physical quantity governs the reliability of two other '
                'channels rather than acting as a third detector;'),
        ('(f)', 'a graduated enforcement scheduler in which advance between severities '
                'requires persistence across consecutive control cycles and is bounded by a '
                'per-candidate cooldown and a global session interval that escalation may '
                'shorten but never eliminate; and'),
        ('(g)', 'a dual-channel interlock under which the severities that act physically upon '
                'the candidate input path are unreachable unless two physically independent '
                'sensing modalities have exceeded threshold within the same control cycle.'),
    ])
    para(doc,
         'The synergy runs as follows. Element (c) is meaningful only because of elements (a) '
         'and (b). A latency band measured from a software-reported onset is a band measured '
         'against a clock the examined machine controls, and a latency band measured from an '
         'unattributed sound is a band that any conversation in the room can enter. Removing '
         'either measurement does not degrade the interlock; it makes the interlock '
         'meaningless, because the quantity it thresholds no longer denotes what the claim '
         'says it denotes. The dependency is structural rather than rhetorical: without T0 '
         'the first of the two intervals of element (c) cannot be formed at all, and the '
         'second ceases to be referable to any particular item. Element (d) is what prevents the band from being satisfied by '
         'coincidence: an unassisted candidate who happens to clear their throat and then '
         'answer within the band is separated from an assisted one by the manner of the '
         'commit, not by its timing.')
    para(doc,
         'Element (e) is a second-order use of a measurement, and it is the element least '
         'likely to be arrived at by combination. The obvious use of a desk inertial unit is '
         'as an additional detector whose output joins a fusion. Here it is not a detector at '
         'all. Physical motion of the desk degrades gaze estimation and simultaneously '
         'improves the case that a structure-borne signal originated at this desk, so the '
         'same measurement is applied with opposite sign to two other channels. Section 8 '
         'reports that qualifying a gaze departure by inertial corroboration lifts '
         'trial-level separation from 0.562 to 0.659 by itself, which is the measured '
         'consequence of the coupling and not of an extra input.')
    para(doc,
         'Elements (f) and (g) supply the technical effect that distinguishes this disclosure '
         'from every reference in Section 3 that ends in a flag. Once the output of an '
         'integrity system is a physical interruption of a candidate’s keyboard, a false '
         'positive is no longer a line in a report; it is an act performed upon a person '
         'sitting an examination. Requiring two channels to agree rather than either alone '
         'reduces false hardware gating on the recorded corpus from 30.58 to 9.31 events per '
         'hour, a fall of 69.6 %, and the unassisted gate rate from 29.7 % to 10.8 %, at a '
         'cost of one quarter of true gates; Section 8.6 states the respect in which that '
         'replay falls short of the two-transducer condition the claim recites. That trade is the invention taking a deliberate '
         'position: the apparatus would rather miss an assisted candidate than open the input '
         'path of an unassisted one.')
    para(doc,
         'A further technical effect follows from the same architecture. Because every '
         'decision is anchored to a physically measured onset and recorded with the '
         'per-channel quantities that produced it, each actuation carries a self-contained '
         'evidence record naming the instants, the channels and the rule that fired. The '
         'output is auditable by construction rather than by retention of video.')

    # ============================================================== 5
    h1(doc, '5. Objectives of the Invention')
    bullets(doc, [
        ('1.', 'To establish the question-onset instant at a candidate station as a physical '
               'measurement of emitted light, independent of any event reported by the '
               'machine under examination.'),
        ('2.', 'To attribute a covert acoustic emission to the seated candidate rather than '
               'to a neighbour, by requiring coincidence between structure-borne and airborne '
               'channels.'),
        ('3.', 'To detect externally assisted answering from the causal relation between '
               'presentation, emission and commit, rather than from the appearance of any '
               'one of them.'),
        ('4.', 'To distinguish an answer composed by the candidate from an answer transcribed '
               'from an external source, by reference to that candidate’s own enrolled '
               'input dynamics.'),
        ('5.', 'To use a single desk inertial measurement to govern the reliability of two '
               'other sensing channels, so that the apparatus degrades gracefully under '
               'physical disturbance instead of failing silently.'),
        ('6.', 'To intervene physically and proportionately during the session, through a '
               'graduated ladder ending in interruption of the candidate input path, rather '
               'than to produce a report after it.'),
        ('7.', 'To make actuation upon that input path impossible on the evidence of a single '
               'sensing modality, and to bound the rate of every actuation by persistence, '
               'cooldown and a global interval.'),
        ('8.', 'To fail safe: to leave the candidate’s input path working whenever the '
               'controller is unpowered, reset or unresponsive, and to release any asserted '
               'gate automatically in the absence of a live decision.'),
        ('9.', 'To state an honest, quantified operating envelope, including the conditions '
               'under which the apparatus should not be relied upon.'),
    ])

    # ============================================================== 6
    h1(doc, '6. Working Principle (in Brief)')
    para(doc,
         'A photodiode is fixed over a small high-contrast patch rendered in a corner of the '
         'display panel, which inverts at every question transition. The edge detected by the '
         'photodiode is the onset anchor T0, timestamped on the same monotonic clock as every '
         'other channel at the station. A piezoelectric transducer bonded to the underside of '
         'the desk and an electret microphone in the desk housing are sampled continuously; '
         'an emission is registered as T1 only where both channels exceed threshold within a '
         'short coincidence window, since vocalisation by the seated candidate couples into '
         'the desk structure through contact while a neighbour’s speech reaches the '
         'microphone without doing so. The input-device interface timestamps the answer '
         'commit as T2 and derives the timing dynamics of the keystrokes preceding it.')
    para(doc,
         'Within each control cycle the apparatus evaluates three conditions. The '
         'consultation-band comparator asks whether T1 minus T0 lies within a bounded '
         'interval whose lower limit is the shortest time in which the displayed item could '
         'have been apprehended and vocalised, and whose upper limit is the presentation '
         'instant of the succeeding item; an emission arriving sooner is activity carried '
         'over from the preceding item, and one arriving later belongs to a different item. '
         'The '
         'assistance-band comparator asks whether T2 minus T1 lies within a bounded interval '
         'whose lower limit is the shortest time in which an external helper could have '
         'responded and whose upper limit is the longest interval over which a causal '
         'relation is asserted. The discontinuity comparator asks whether the timing dynamics '
         'of the commit depart from the candidate’s enrolled profile in the direction '
         'characteristic of transcription. Ocular channels derived from the imaging sensor '
         '— the geometry of departures from the display and of returns to it, the '
         'scanpath and the pupil response — contribute corroborating quantities, and the '
         'desk inertial unit qualifies them: a gaze departure counts only where the desk was '
         'measurably disturbed at the same time, and the acoustic channel is weighted upward '
         'under the same condition.')
    para(doc,
         'The corroboration value unit combines the qualified quantities into an ordinal value '
         'and the eligibility comparator decides whether the cycle is eligible for any '
         'output at all. Eligibility is not actuation. The graduated enforcement scheduler '
         'then decides whether an eligible cycle may advance the enforcement state, requiring '
         'the same severity to be earned on consecutive cycles, respecting a per-candidate '
         'cooldown and a global session interval, and consulting the dual-channel interlock '
         'before permitting any severity that acts upon the input path. Where the interlock '
         'is satisfied, the in-line gating unit opens the keyboard data lines for a bounded '
         'interval; where it is not, the ladder stops at an indication to the candidate or an '
         'entry on the invigilator console. Every cycle, whether or not it actuated, is '
         'written to the evidence record store with the instants and channel quantities that '
         'produced it.')

    # ============================================================== 7
    h1(doc, '7. Detailed Description of the Invention')
    para(doc,
         'The station assembly (100) carries the elements set out below. Figure 3 shows '
         'their physical arrangement at one desk and the two acoustic paths that the '
         'attribution test distinguishes. Reference numerals are used consistently '
         'throughout this document and are collected in Table 1.')

    table(doc, ['Ref', 'Element', 'Ref', 'Element'], [
        ['100', 'candidate station / desk assembly', '600', 'causal latency interlock'],
        ['200', 'display panel', '610', 'assistance-band comparator'],
        ['205', 'rendered onset patch region', '615', 'consultation-band comparator'],
        ['210', 'photometric onset sensor', '620', 'discontinuity comparator'],
        ['300', 'imaging sensor', '700', 'corroboration value unit'],
        ['310', 'gaze estimator', '710', 'eligibility comparator'],
        ['320', 'scanpath unit', '800', 'graduated enforcement scheduler'],
        ['330', 'pupillometry unit', '810', 'persistence counter'],
        ['400', 'desk-contact transducer', '820', 'per-candidate cooldown'],
        ['401', 'transducer preamplifier', '830', 'global session interval'],
        ['402', 'airborne microphone', '840', 'escalation comparator'],
        ['403', 'band-pass and envelope stage', '850', 'dual-channel actuation interlock'],
        ['410', 'desk inertial unit', '910', 'desk indicator / haptic'],
        ['420', 'emission attribution unit', '920', 'in-line gating unit'],
        ['430', 'reliability-transfer unit', '930', 'session hold latch'],
        ['500', 'input-device interface', '950', 'evidence record store'],
        ['510', 'enrolled profile store', '', ''],
    ], cap='Table 1: Reference Numerals Used in the Description and the Figures',
        widths=[0.55, 2.55, 0.55, 2.55], size=9.5, align_left_cols=(1, 3))


    para(doc,
         'A photodiode (210) with a transimpedance stage is mounted against the bezel of the '
         'display panel (200), behind an opaque shroud, over a patch region (205) that the '
         'examination application inverts on every question transition. The detector runs against a '
         'slowly adapting baseline so that ambient light drift and backlight modulation do '
         'not generate false anchors, and a holdoff interval suppresses multiple anchors from '
         'a single transition. The resulting anchor is emitted immediately rather than at the '
         'next reporting boundary, so its latency is bounded by the sampling period and not '
         'by the frame rate. The significance of this element is not its precision but its '
         'independence: the timing origin of the entire analysis is a measurement of photons '
         'that reached the candidate, and it remains valid if the software on the examined '
         'machine misreports, delays or fabricates its own rendering events.',
         lead='Photometric onset sensing (210).')

    para(doc,
         'A contact piezoelectric transducer (400) is bonded to the underside of the desk and '
         'buffered by a high-impedance preamplifier; an electret microphone (402) is mounted '
         'in the desk housing. The emission attribution unit (420) registers an emission '
         'instant T1 only where both channels exceed their respective thresholds within a '
         'coincidence window. The physical basis is that speech produced by the seated '
         'candidate reaches the desk by structural conduction through contact between the '
         'candidate and the desk, whereas speech from an adjacent station reaches the '
         'microphone through air without exciting the desk structure. The claim asserted is '
         'therefore not that the apparatus recognises words — it does not, and no audio '
         'need be retained — but that it can decline to attribute a sound to a candidate '
         'who did not produce it.',
         lead='Desk-contact emission attribution (400, 402, 420).')

    para(doc,
         'Coincidence of two threshold crossings is by itself defeated by a concurrence the '
         'apparatus must be built to reject: the candidate strikes the desk or types while a '
         'neighbour speaks, so that the contact channel and the airborne channel cross their '
         'thresholds in the same window for unrelated reasons. Band-limiting the two channels '
         'to the range of voice fundamental and first-formant frequencies does not dispose of '
         'it, because a mechanical impulse is broadband and deposits energy in that range as '
         'well. The unit therefore requires the two channels to be consistent and not merely '
         'concurrent: the band-limited envelopes of the contact and airborne channels must '
         'correlate above a threshold across the coincidence window before an emission instant '
         'is registered. A common source modulates both channels together, since it is one '
         'utterance reaching two transducers by two paths; two unrelated sources do not, since '
         'a keystroke transient and a neighbour’s syllable have no reason to share an '
         'envelope. This is the discriminating mechanism where the simple coincidence test is '
         'ambiguous, and it is what the attribution claim rests on when the station is busy '
         'rather than quiet.',
         lead='Concurrent but unrelated sources.')

    para(doc,
         'Each of the three analog channels is compared against a baseline adapted over a time '
         'constant long compared with the events it must detect, so that a threshold is a '
         'departure from the station’s present condition rather than from a value fixed at '
         'installation. Ambient illumination and backlight level drift over a session; desk '
         'and room noise floors differ between halls and rise as a hall fills. A fixed '
         'threshold is therefore wrong at some point in every deployment, in one direction or '
         'the other, and the apparatus is not calibrated per venue before use. Adaptation is '
         'deliberately slow relative to the coincidence window, so that the baseline tracks '
         'the condition of the station without absorbing the event being detected.',
         lead='Adaptive baselines on all three analog channels.')

    para(doc,
         'A six-axis inertial unit (410) fixed to the desk supplies a combined motion '
         'magnitude, computed as the Euclidean combination of the linear acceleration '
         'magnitude with the angular rate magnitude scaled by a fixed coupling coefficient. '
         'The reliability-transfer unit (430) applies this single quantity at two points. The '
         'confidence threshold demanded of the imaging channel is reduced as motion rises, '
         'because a physically disturbed camera or a moving head degrades gaze estimation and '
         'a fixed threshold would silently discard true departures; and the weight given to '
         'the acoustic channel is raised under the same condition, because desk motion is '
         'corroborating evidence that a structure-borne signal originated at this desk. The '
         'threshold adjustment is bounded below by a floor and the motion term is saturated '
         'at a maximum, so that a single impulse — a dropped object, a knocked desk '
         '— cannot drive the imaging threshold arbitrarily low.',
         lead='Inertial reliability transfer (410, 430).')

    para(doc,
         'Ocular quantities are derived from the imaging sensor (300): the gaze estimator '
         '(310) supplies departures from and returns to the display region; the scanpath unit '
         '(320) supplies the geometry of the trajectory; the pupillometry unit (330) supplies '
         'the pupil response. The quantities that matter to this invention are those that '
         'describe consulting a fixed external source rather than merely looking away: the '
         'angular concentration of exit bearings, the position and dispersion of the landing '
         'point on return, the count of bounded departure-and-return pairs, and the periodic '
         'structure of the away signal within the assistance band. A departure is admitted '
         'only where the inertial channel corroborates that the candidate physically moved, '
         'which is the qualification described above.',
         lead='Ocular channels (300, 310, 320, 330).')

    figure(doc, 'fig03.png',
           'Figure 3. Physical arrangement of one instrumented station, in side elevation. '
           'The candidate\u2019s own vocalisation reaches the contact transducer (400) through '
           'the desk structure and the microphone (402) through the air; a neighbour\u2019s '
           'speech reaches (402) alone, and the coincidence requirement is what refuses to '
           'attribute it to the seated candidate.', width=6.5)

    para(doc,
         'The input-device interface (500) timestamps the answer commit as T2 and derives '
         'per-key hold intervals and inter-key intervals for the keystrokes preceding it. The '
         'enrolled profile store (510) holds statistics of the same quantities gathered from '
         'the candidate during an enrolment interval of ordinary, unassisted work. The '
         'discontinuity comparator (620) computes a scaled distance between the commit '
         'dynamics and the enrolled profile. The purpose is not identification. Transcribing '
         'a dictated string and composing an answer are different motor tasks, and they '
         'produce different timing distributions in the same person; the comparator is '
         'directed at that difference.',
         lead='Input dynamics and the enrolled profile (500, 510, 620).')

    para(doc,
         'Each acoustic channel passes through an analog stage before it is digitised. That '
         'stage band-passes the signal to the range of voice fundamental and first-formant '
         'frequencies, approximately 80 Hz to 1 kHz, and then rectifies and low-pass filters '
         'it to produce an envelope. It is the envelope, not the waveform, that reaches the '
         'converter, so the sampling rate at the node is set by the envelope bandwidth and '
         'not by the bandwidth of speech; 200 Hz is ample for an envelope whose own content '
         'lies below about 50 Hz, and the anti-aliasing requirement is met by the low-pass '
         'stage that forms it. This is why the node can be a commodity microcontroller: at no '
         'point does it hold a speech waveform.',
         lead='Analog envelope front end (401, 402).')

    para(doc,
         'What leaves the station node is therefore not an acoustic signal, and could not be '
         'reconstructed into one. Within each analysis window the node reduces each acoustic '
         'channel to a peak magnitude and a root-mean-square magnitude, and emits only those '
         'statistics, a scalar motion magnitude and the derived instants. Two properties make '
         'the reduction irreversible, and neither is a retention policy. First, the analog '
         'stage has already discarded phase: an envelope detector is insensitive to the phase '
         'relations among the components it passes, and phase is not recoverable from '
         'magnitude alone. Second, the peak and mean-square of a window are two order '
         'statistics of every sample in it; the mapping is many-to-one over an enormous '
         'preimage, and no inverse exists rather than none being permitted. Intelligibility '
         'requires the spectral detail and the temporal fine structure that both stages '
         'remove. The protection is a property of what the apparatus computes, and it holds '
         'whether or not the recipient is trusted, and whether or not the emitted statistics '
         'are later stored.',
         lead='Non-reconstructability of the acoustic representation.')

    para(doc,
         'Two intervals are evaluated, and the onset anchor is what makes the first of them '
         'computable at all. The consultation-band comparator (615) evaluates T1 minus T0. '
         'Its lower bound is a minimum item-apprehension interval: a candidate cannot have '
         'read an item and begun to vocalise it inside that interval, so an emission '
         'arriving sooner is residual activity carried over from the preceding item rather '
         'than a consultation about the present one. Its upper bound is the presentation '
         'instant derived for the succeeding item, which is what binds an attributed '
         'emission to one identified question rather than to the session at large. In the '
         'described embodiment the lower bound is set at 1.0 s and may be varied between '
         '0.5 s and 2.0 s without departing from the invention; Section 8.2 reports the '
         'measurement on which that default is set, and Section 9.3 lists its confirmation '
         'on physically acquired data among the predictions the planned trial would test. '
         'The assistance-band comparator (610) then evaluates whether T2 minus T1 lies '
         'within a bounded assistance interval. Its lower bound is the shortest time in '
         'which a helper outside the station could have heard the emission, resolved the '
         'item and returned an answer, and the candidate could have begun to commit it; '
         'its upper bound is the longest interval over which a causal relation between '
         'that emission and that commit is asserted. In the described embodiment the '
         'lower bound is set at 2.0 s and the upper bound at 30 s, the lower permitted to '
         'vary between 1.0 s and 4.0 s and the upper between 15 s and 60 s without '
         'departing from the invention; Section 8.2 states the proxy measurement from '
         'which those defaults are taken and how little weight it will bear. '
         'Removing the onset anchor removes '
         'both tests: the first interval cannot be formed, and the second is no longer '
         'referable to any particular item. The corroboration value unit '
         '(700) combines the interlock outcome with the qualified ocular quantities and the '
         'weighted acoustic quantity into an ordinal corroboration value, and the eligibility '
         'comparator (710) determines whether the cycle is eligible for output. The value is '
         'ordinal by construction. Its function is to order cycles by strength of evidence so '
         'that the scheduler may act on the strongest; no protection is sought for the '
         'combination as a mathematical method in the abstract, and the value has no meaning '
         'in this apparatus except as the input to a physical actuation decision.',
         lead='Causal latency interlock and corroboration value (600, 615, 610, 700, 710).')

    para(doc,
         'The scheduler (800) holds a per-candidate enforcement state over the severities '
         'observe, advise, notify, gate and hold. Advance requires the same severity to be '
         'earned on n consecutive control cycles, counted by the persistence counter (810). A '
         'per-candidate cooldown (820) bars repeat actuation upon the same candidate within a '
         'fixed interval, and a global session interval (830) bars actuation anywhere in the '
         'room within a fixed interval of the last one, so that the total rate of intervention '
         'in a hall is bounded independently of how many candidates are flagged at once. The '
         'escalation comparator (840) permits a sustained and rising corroboration value to '
         'shorten those intervals by a bounded fraction; it may never eliminate them.',
         lead='Graduated enforcement scheduler (800, 810, 820, 830, 840).')

    para(doc,
         'The two severities that act physically upon the candidate — gate and hold '
         '— are conditioned on the dual-channel interlock (850). The interlock is '
         'satisfied only where two physically independent sensing modalities have each '
         'exceeded their own threshold within the same control cycle; independence is a '
         'property of the transducers, so that two quantities derived from the same camera do '
         'not constitute two channels. The severities that act only informationally remain '
         'available on a single modality. The design position is explicit: an indication to '
         'the candidate may be wrong, and an interruption of their keyboard should not be.',
         lead='Dual-channel actuation interlock (850).')

    para(doc,
         'The desk indicator (910) provides a private visual or haptic indication to the '
         'candidate alone. The in-line gating unit (920) is disposed in series with the '
         'candidate keyboard and comprises an analog switch or signal relay in the data pair, '
         'whose enable input is driven by the controller. Two properties are enforced in '
         'hardware rather than in software. The enable input is held in the passing state by '
         'a pull-down resistor, so that the candidate’s input path works whenever the '
         'controller is unpowered, held in reset or unresponsive: opening the path is the '
         'active state and requires a live controller to assert it. And every assertion is '
         'watchdog-bounded, releasing automatically if the decision layer stops refreshing '
         'it, so that no failure can hold a candidate’s keyboard open. The session hold '
         'latch (930) requires human release. The evidence record store (950) receives every '
         'control cycle with its instants, channel quantities, interlock outcome and '
         'scheduler decision.',
         lead='Actuators and the evidence record (910, 920, 930, 950).')

    figure(doc, 'fig04.png',
           'Figure 4. The in-line gating unit (920). The data pair is opened while bus power '
           'and ground pass through, so the device is not power-cycled. Two properties are '
           'held in the circuit rather than in software: a pull-down biases the enable input '
           'toward continuity, and every assertion is released by a watchdog when the '
           'controller stops refreshing it.', width=6.4)

    figure(doc, 'fig05.png',
           'Figure 5. The enforcement ladder and the conditions governing advance along it. '
           'The severities that act physically upon the candidate input path are unreachable '
           'on the evidence of one sensing modality, and no escalation may eliminate the '
           'global session interval.')

    h2(doc, '7.1 Alternative Embodiments')
    para(doc,
         'The following alternatives are contemplated and are to be read as within the scope '
         'of the invention. They are recited so that the disclosure supports claim language '
         'broader than the principal embodiment.')
    bullets(doc, [
        ('(a) Onset anchoring.', 'The onset instant may be recovered by a photodiode over a '
         'rendered patch; by a photodiode or phototransistor observing panel backlight '
         'modulation; by an ambient-light sensor differencing two regions of the panel; by an '
         'optical tap on the video interface; or by a line-level tap on the display signal '
         'itself. What is required is that the instant be derived from a physical quantity '
         'emitted by the display rather than from an event reported by the machine under '
         'examination.'),
        ('(b) Emission attribution.', 'Coincidence may be evaluated between a contact '
         'piezoelectric transducer and an airborne microphone; between two contact '
         'transducers at different points of the desk with a time-difference constraint; '
         'between a contact transducer and a throat or bone-conduction sensor; or between a '
         'contact transducer and a capacitive or load sensor confirming that the candidate is '
         'in contact with the desk. Attribution may also be strengthened by a microphone '
         'array steering a null toward adjacent stations.'),
        ('(c) Commit-dynamics channel.', 'The input-dynamics channel may be derived from '
         'keystroke hold and inter-key intervals; from pointer velocity, curvature and '
         'dwell; from touch-surface pressure and contact area; from stylus dynamics; or from '
         'any combination. The comparison against the enrolled profile may use a scaled '
         'Manhattan distance, a Mahalanobis distance, a likelihood under a fitted density, or '
         'a learned scoring function trained without any example of assisted responding.'),
        ('(d) Latency band.', 'The bounds of the assistance band may be fixed; set per '
         'examination from the item type; adapted per candidate from the distribution of '
         'unassisted commit intervals observed during enrolment; or expressed as a '
         'probability under a fitted latency model with the comparator thresholding that '
         'probability. Multiple bands may be evaluated in parallel for different modes of '
         'assistance.'),
        ('(e) Reliability transfer.', 'The quantity transferred from the inertial unit may '
         'adjust a threshold, a weight, a prior, or the admissibility of an event. The same '
         'construction may be applied with other governing quantities: ambient illumination '
         'governing the imaging channel, or ambient acoustic level governing the emission '
         'channel.'),
        ('(f) Enforcement actuators.', 'The severity that acts upon the input path may open '
         'the keyboard data lines by an analog switch or a signal relay; may suspend '
         'enumeration of the input device; may interpose a hardware filter that passes '
         'navigation but not character entry; or may act upon the display rather than the '
         'input, by blanking or watermarking the item. The private indication may be visual, '
         'haptic or thermal. In every case the fail-safe and watchdog properties recited '
         'above apply.'),
        ('(g) Processing topology.', 'The channel derivation may be performed at a node '
         'controller at the station, at a room-local aggregator, or divided between them, '
         'with the enforcement scheduler at either. In privacy-preserving embodiments the '
         'imaging and acoustic streams are reduced to derived quantities at the point of '
         'acquisition and no raw audio or video leaves the station.'),
        ('(h) Contemplated further development.', 'In a further contemplated embodiment the '
         'apparatus estimates the direction of arrival of the airborne component and '
         'maintains a per-station acoustic map of the room, so that an emission may be '
         'assigned to a specific neighbouring station rather than merely refused. This '
         'variant is disclosed here to preserve it for possible later claiming and is '
         'deliberately not recited among the claims of Section 10, as it has not been reduced '
         'to practice.'),
        ('(i) Application environments.', 'Beyond examination halls, the same apparatus '
         'applies to professional certification and licensing test centres, secure interview '
         'and vetting rooms, recruitment and aptitude testing facilities, defence and '
         'public-service selection examinations, and supervised remote-proctoring '
         'installations at candidate premises where the station hardware can be provided.'),
    ])

    # ============================================================== 8
    h1(doc, '8. Validation — Part A: Study on Recorded Human Data')
    para(doc,
         'The control layer was evaluated on recorded human data rather than on simulation. '
         'Four public corpora of human recordings were used, each standing in for one '
         'transducer of the contemplated station, together with a control-law implementation '
         'that consumes those recordings through the same code path it will use with live '
         'transducers. Detection quality is reported as AUC, the area under the '
         'receiver-operating curve, where 1.0 is perfect ordering and 0.5 is chance, and as '
         'EER, the equal-error rate.')
    para(doc,
         'The nature and the limits of this evidence are stated at the outset. No corpus '
         'exists that carries synchronised photodiode, desk-contact, inertial and keystroke '
         'channels from one candidate station, because such a corpus can only be produced by '
         'the apparatus described here. Every figure below therefore measures a mechanism of '
         'the invention on real human recordings of the physical quantity concerned, and no '
         'figure below measures the assembled apparatus. What Section 8 establishes is that '
         'each mechanism does what the specification says it does, on human data, at stated '
         'sample sizes. What it does not establish is field performance. Section 9 specifies '
         'the build and the trial that would. Table 2 summarises what follows: every row is a '
         'measurement on recorded human data of the physical quantity concerned, and no row '
         'is a measurement of the assembled apparatus.')

    table(doc, ['Mechanism', 'Evidence base', 'Headline measurement', 'Section'], [
        ['Ocular corroboration channels (310, 320, 330)',
         'eye-tracking corpus; 11 candidates, 100 recordings, 3,213 windows',
         'window AUC 0.594 to 0.733 per channel, 0.780 fused', '8.2'],
        ['Consultation-band lower bound (615)', 'the same corpus; 2,091 departures',
         '7 events (0.335 %) begin within 1,000 ms of the onset anchor', '8.2'],
        ['Reliability transfer (430), as a decision rule',
         'the same corpus; head-pose quantity, not an inertial sensor',
         'trial AUC 0.562 to 0.659 from one measurement applied at two points', '8.3'],
        ['Input-dynamics discontinuity (510, 620)',
         'keystroke benchmark; 51 subjects, published protocol',
         'equal-error rate 9.60 %, AUC 0.954', '8.4'],
        ['Persistence counter (810)', 'the same corpus',
         '9.60 % at n = 1 falling to 5.07 % at n = 5', '8.4'],
        ['Desk inertial channel (410)', 'human motion corpus; 24 subjects at 50 Hz',
         'seated noise floor 0.178 m/s\u00b2 median, 1.832 m/s\u00b2 at p99', '8.5'],
        ['Two-channel agreement rule (850), not the claimed two-transducer '
         'interlock',
         'replay of 3,213 cycles; both channels from one instrument',
         'false gating 30.58/h to 9.31/h, a fall of 69.6 %', '8.6'],
        ['Enforcement scheduler (800 to 840)', 'the same replay',
         '419 eligible cycles held to 83 actuations, a reduction of 80.2 %', '8.6'],
        ['Control path (600, 700, 800)', 'recorded corpus timed on a commodity host',
         'software path 1.588 ms median, 0.06 % of the cycle budget', '8.7'],
    ], cap='Table 2: What Section 8 Establishes, Mechanism by Mechanism',
        widths=[1.70, 1.82, 2.10, 0.58], size=8.8, align_left_cols=(0, 1, 2))

    h2(doc, '8.1 Corpora and what each stands in for')
    table(doc, ['Corpus', 'Contents', 'Channel it stands in for', 'What it cannot supply'],
          [['Academic-reading eye-tracking corpus (Tobii / iMotions exports)',
            '150 recordings, 60.04 Hz gaze and pupil, labelled assisted / unassisted per '
            'trial, with stimulus onset and offset markers',
            'Imaging sensor (300) and the ocular channels (310, 320, 330); the stimulus '
            'marker stands in for the onset anchor T0',
            'The onset marker is a software log line, not a photometric measurement. This is '
            'the substitution the build removes.'],
           ['Keystroke-dynamics benchmark corpus',
            '51 subjects, 8 sessions of 50 repetitions, 31 timing features per repetition, '
            'published evaluation protocol',
            'Input-device interface (500), enrolled profile store (510) and the discontinuity '
            'comparator (620)',
            'Impostor repetitions stand in for transcription. A different person typing is '
            'not the same as the same person transcribing.'],
           ['Inertial corpus, 50 Hz tri-axial accelerometer and gyroscope',
            '24 subjects across sitting, standing, walking, stairs and jogging',
            'Desk inertial unit (410) and the reliability-transfer unit (430), in real '
            'physical units',
            'The sensor is body-worn, not desk-mounted. It bounds the seated noise floor; it '
            'does not measure desk coupling.'],
           ['Pointer-dynamics corpus',
            '1,033 windows of speed and curvature statistics from ordinary daily use',
            'Second input-dynamics channel under Section 7.1(c)',
            'Unlabelled for assistance; used to characterise ordinary variation only.']],
          cap='Table 3: Recorded Human Corpora and the Station Channel Each Stands In For',
          widths=[1.35, 1.85, 1.75, 1.85], size=8.8, align_left_cols=(0, 1, 2, 3))

    para(doc,
         'One methodological finding governs everything that follows and is reported first '
         'because it bounds the rest. The eye-tracking corpus was exported under three '
         'incompatible schemas, and detection performance is not comparable across them: '
         'restricted to the 55-column export the window-level AUC is 0.705, on the 46-column '
         'export it is 0.498, and on the 118-column export it is 0.292. A figure computed by '
         'pooling all three is partly a measurement of export protocol rather than of '
         'candidate behaviour. All ocular figures in this section are accordingly restricted '
         'to the 55-column protocol: 100 recordings, 11 candidates, 63 assisted and 37 '
         'unassisted trials, 3,213 observation windows of 20 s at a 2.5 s hop. Evaluation is '
         'by participant-disjoint five-fold cross-validation, so no candidate contributes to '
         'both the training and the evaluation of any fold. The consequence is a small '
         'evaluation: eleven candidates cannot resolve fine differences between '
         'configurations, and the ocular figures below are reported as a range across '
         'configurations rather than as a selected best.')

    h2(doc, '8.2 Ocular corroboration channels')
    para(doc,
         'Six channels were derived from the imaging corpus and evaluated singly and in '
         'combination. The causal-loop channel, which describes the geometry of consulting a '
         'fixed external source — the angular concentration of exit bearings, the '
         'landing position and dispersion on return, the count of bounded '
         'departure-and-return pairs, and periodic structure in the away signal within the '
         'assistance band — reaches 0.723 and is among the strongest single channels. '
         'The fused configuration reaches 0.780 at window level, with question-level figures '
         'between 0.695 and 0.775 depending on how windows are aggregated.')
    figure(doc, 'fig06.png',
           'Figure 6. Ocular corroboration channels on the 55-column protocol, 11 candidates, '
           'participant-disjoint five-fold cross-validation. (a) window-level AUC of each '
           'channel taken singly, against the fused configuration; (b) the AUC lost when each '
           'channel is removed from the fused configuration.',
           width=6.5)
    para(doc,
         'Removing any single channel costs between 0.048 and 0.084 AUC, so no channel is '
         'redundant and none dominates. That pattern supports the fusion recited in the '
         'claims, and it equally bounds what fusion delivers: six channels together reach '
         '0.780, which is a useful ordering of candidates and is not an adjudication of any '
         'one of them. Two negative results are reported because they constrain the claims. '
         'Question-onset phase structure — whether behaviour differs systematically as a '
         'function of elapsed time since presentation — was tested and rejected, at AUC '
         '0.485 to 0.519, and is not claimed. And the contribution of an ocular enrolment '
         'baseline is unstable: under the fused model an enrolment-deviation term reduces AUC '
         'from 0.780 to 0.713 and taken alone reaches only 0.585, while under a separate '
         'held-out construction it raises window AUC from 0.673 to 0.712. Because the '
         'direction of the effect depends on the construction, and because only 6 of the 11 '
         'candidates carry a usable unassisted baseline, ocular enrolment is not claimed. '
         'Enrolment is claimed where its benefit is stable and measured, which is the '
         'input-dynamics channel of Section 8.4.')

    para(doc,
         'The same corpus fixes where the lower bound of the consultation interval (615) may '
         'be placed. Across 2,091 gaze departures in the 55-column protocol, 7 — '
         '0.335 % — begin within 1,000 ms of the stimulus onset marker that stands in '
         'for the anchor T0, and those few fall disproportionately in unassisted recordings: '
         '0.62 % of unassisted departures against 0.21 % of assisted ones, which is the '
         'signature of activity carried over from the preceding item rather than of a '
         'consultation about the present one. The first departure of a trial has a fifth '
         'percentile of 997 ms in assisted recordings against 0 ms in unassisted ones, and a '
         'first percentile over all departures of 2,381 ms assisted against 1,295 ms '
         'unassisted. A lower bound of one second therefore discards almost no departure '
         'that could be a consultation while excluding the class of events arriving too '
         'early to be a reading of the item then displayed. Seven events is a small number. '
         'The bound is accordingly stated in Section 7 as a default with a permitted range, '
         'subject to confirmation on physically acquired data, and not as a measured '
         'optimum. A gaze departure is a proxy for an acoustic emission here, and the '
         'substitution is recorded as such.',
         lead='Where the consultation bound may be set.')

    para(doc,
         'The assistance band of Section 7 is on weaker ground and the difference is stated '
         'rather than smoothed over. No corpus available here contains an attributed acoustic '
         'emission, so the interval T2 minus T1 has never been observed. What the eye-tracking '
         'corpus does supply is the duration of each departure from the display, which '
         'brackets an external consultation and therefore bounds how long one takes. Assisted '
         'departures are the longer: median 816 ms against 741 ms, but separating in the upper '
         'tail, 1,899 ms against 1,440 ms at the seventy-fifth percentile, 4,500 ms against '
         '2,987 ms at the ninetieth and 6,651 ms against 4,562 ms at the ninety-fifth. Taking '
         '2 s to 30 s as the band, 24.1 % of assisted departures fall inside it against 16.4 % '
         'of unassisted ones, an enrichment of 1.47 times. That is a weak separation and it is '
         'a bound on consultation duration rather than a measurement of helper latency. The '
         'defaults of Section 7 are accordingly presented as derived starting values with a '
         'permitted range, to be replaced by the distribution the staged trial of Section 9.2 '
         'would produce. Until then the assistance band is the least evidenced numeric '
         'parameter in the disclosure, and it should not be quoted as a measured quantity.',
         lead='Where the assistance band may be set, and how weakly.')

    h2(doc, '8.3 Reliability transfer: one measurement applied at two points')
    para(doc,
         'One matter must be settled before this subsection is read, because it governs what '
         'the result means. The eye-tracking corpus contains no inertial sensor. The motion '
         'quantity used here is derived from the eye tracker’s own camera-relative eye '
         'position and range channels — it is a head-pose quantity, not an accelerometer '
         'reading, and it comes from the same instrument as the gaze channel it qualifies. '
         'What follows is therefore a test of the coupling as a decision rule, on human data, '
         'between two quantities that are statistically distinct but not physically '
         'independent. It is not a measurement of the desk inertial unit (410), which is '
         'characterised separately at Section 8.5 on a corpus that has no gaze channel. The '
         'two have never been observed together, because no corpus carries both.')
    para(doc,
         'The coupling recited at element (e) of Section 4.1 was evaluated independently of '
         'the fused model. Gaze departures were qualified by requiring the head-pose channel '
         'to show that the candidate physically moved at the same time, with the '
         'qualification threshold set at the ninetieth percentile of departure-associated '
         'motion peaks in unassisted trials. Qualified-departure count alone lifts '
         'trial-level AUC from 0.562 to 0.659, an improvement of 0.097 obtained without '
         'adding any new sensing channel to the decision — the inertial measurement was '
         'already present, and the gain comes from applying it to the admissibility of the '
         'ocular channel rather than as a detector in its own right. This is the measured '
         'form of the argument that the two-point application is not an obvious combination: '
         'used as a third detector, the same signal contributes far less.')
    para(doc,
         'The finding also corrects an error that a threshold alone would have concealed. In '
         'the raw corpus the fraction of samples away from the display region is 38 % to 49 % '
         'even in unassisted trials, which is not glancing behaviour but tracker dropout. '
         'Requiring inertial corroboration separates a departure that the candidate physically '
         'made from a gap in the eye-tracker record, and it is what makes the ocular '
         'departure channel usable at all.')

    h2(doc, '8.4 Input-dynamics discontinuity and the persistence counter')
    para(doc,
         'The discontinuity comparator (620) was evaluated on the keystroke benchmark under '
         'its published protocol: the enrolled profile is built from the first four sessions '
         'of a subject, genuine trials are that subject’s later sessions, and the '
         'contrasting set is drawn from other subjects’ first five repetitions. Three '
         'scaled-distance detectors were compared.')
    table(doc, ['Detector', 'EER, mean across 51 subjects', 'EER, median', 'AUC'],
          [['Manhattan scaled', '9.60 % (SD 6.87)', '8.00 %', '0.954 (SD 0.049)'],
           ['Mahalanobis', '11.12 % (SD 6.29)', '10.45 %', '0.945 (SD 0.045)'],
           ['Euclidean', '17.05 % (SD 9.42)', '15.55 %', '0.879 (SD 0.097)'],
           ['Manhattan scaled, stricter contrast set drawn from all sessions',
            '14.22 %', '—', '—']],
          cap='Table 4: Discontinuity Detectors Against the Enrolled Profile (510)',
          widths=[2.6, 1.65, 1.1, 1.45], size=9.5, align_left_cols=(0,))
    para(doc,
         'The persistence counter (810) is a parameter of the enforcement scheduler, and the '
         'value it should take is a measurement rather than a preference. Requiring the '
         'departure to hold across consecutive commit events, with the events grouped so that '
         'a run always concerns the same contrasting party, gives an equal-error rate of '
         '9.60 % at n = 1, 7.22 % at n = 2, 5.38 % at n = 3 and 5.07 % at n = 5. The curve is '
         'the justification for requiring persistence before advancing a severity, and it '
         'also shows where the benefit stops: past n = 3 the return is small and the latency '
         'cost is not.')
    figure(doc, 'fig07.png',
           'Figure 7. Input-dynamics discontinuity against the enrolled profile. (a) three '
           'scaled-distance detectors, 51 subjects; (b) equal-error rate as a function of the '
           'number of consecutive commit events required, which is the measured basis for the '
           'persistence counter (810).',
           width=6.5)
    para(doc,
         'Physical timing scales recovered from the same corpus fix the units the comparator '
         'works in: median key hold 86.1 ms, with a fifth-to-ninety-fifth percentile range of '
         '49.3 to 144.8 ms, and median down-to-down interval 191.1 ms. One limitation is '
         'stated plainly. In this corpus the contrasting set is a different person typing the '
         'same string, which is not the same thing as the same person transcribing a dictated '
         'answer. The corpus establishes that a scaled distance from an enrolled profile '
         'separates typing that did not come from the enrolled motor pattern, and that '
         'persistence sharpens that separation as the scheduler assumes. It does not '
         'establish the magnitude of the transcription effect, which the trial of Section 9 '
         'is specified to measure.')

    h2(doc, '8.5 Inertial channel in physical units')
    para(doc,
         'The desk inertial channel was characterised on a 50 Hz human motion corpus so that '
         'the thresholds recited in the specification are expressed in real units rather than '
         'in arbitrary ones. The seated noise floor has a median combined magnitude of '
         '0.178 m/s², a ninety-fifth percentile of 0.966 m/s² and a '
         'ninety-ninth percentile of 1.832 m/s². Separation of seated from walking is '
         'essentially complete at AUC 0.9995 and from standing is partial at 0.792, which is '
         'the expected ordering and confirms the channel is measuring gross posture change '
         'rather than noise.')
    table(doc, ['Property', 'Measured value', 'What it fixes in the specification'],
          [['Seated combined magnitude, median / p95 / p99',
            '0.178 / 0.966 / 1.832 m/s²',
            'The threshold above which desk motion qualifies a gaze departure, and the scale '
            'of the weight applied to the acoustic channel'],
           ['Onset confirmation latency, N = 1 to N = 8 samples at 50 Hz',
            '20 ms to 160 ms',
            'The delay the reliability transfer adds to the control cycle'],
           ['False-onset rate over the same range', '1.000 % falling to 0.598 %',
            'The cost of confirming motion before qualifying a departure'],
           ['Saturation behaviour under a 8.90 m/s² impulse, fifty times the seated '
            'median',
            'unsaturated adjustment would reach 0.066; the bound holds the threshold at 0.450 '
            'against its floor of 0.35',
            'Confirms that a single impulse cannot drive the imaging threshold arbitrarily '
            'low, which is the safety property recited in Section 7']],
          cap='Table 5: Desk Inertial Channel Characterised in Physical Units',
          widths=[2.05, 1.85, 2.9], size=9.3, align_left_cols=(0, 1, 2))

    h2(doc, '8.6 Enforcement discipline')
    para(doc,
         'The scheduler was evaluated by replaying the recorded corpus through the '
         'control-law implementation, question by question, at the control-cycle rate, with '
         'each channel rank-calibrated against unassisted cycles so that the thresholds are '
         'expressed as quantiles rather than as raw scores. One hundred questions were '
         'replayed, 63 assisted and 37 unassisted, producing 3,213 control cycles. Each '
         'mechanism of Section 7 was then switched off in turn.')
    table(doc, ['Mechanism', 'Configuration', 'True gate rate, assisted',
                'Gate rate, unassisted', 'False gates per hour', 'Actuations'],
          [['Dual-channel interlock (850)', 'any single modality may gate', '44.4 %',
            '29.7 %', '30.58', '83'],
           ['', 'interlock armed', '33.3 %', '10.8 %', '9.31', '83'],
           ['Persistence counter (810)', 'n = 1', '58.7 % advise', '37.8 % advise',
            '45.21 advise', '131'],
           ['', 'n = 2 (default)', '44.4 % advise', '29.7 % advise', '30.58 advise', '83'],
           ['', 'n = 4', '33.3 % advise', '24.3 % advise', '15.96 advise', '53'],
           ['Escalation comparator (840)', 'disabled', '—', '—', '—', '80'],
           ['', 'enabled', '—', '—', '—', '83']],
          cap='Table 6: Enforcement Ablations on 3,213 Replayed Control Cycles',
          widths=[1.5, 1.55, 1.05, 1.0, 1.05, 0.75], size=8.8, align_left_cols=(0, 1))
    para(doc,
         'The first and fourth data rows carry identical figures because they describe the '
         'same baseline configuration under two different ablations. With the interlock '
         'disarmed, the gate severity becomes reachable on exactly the evidence that reaches '
         'the advise severity, so the gate rates and the advise rates coincide; arming the '
         'interlock is what separates them. The repetition is a property of the ablation, not '
         'a transcription error.', size=9.5, italic=True)
    para(doc,
         'What this subsection measures, and what it does not, must be stated first. The two '
         'quantities the interlock was armed with are both derived from the eye-tracking '
         'corpus, and therefore from a single instrument: one is the ocular score, the other '
         'the head-pose score of Section 8.3. Section 7 and the claims require the two '
         'modalities of an interlock to be transducers responsive to different physical '
         'quantities, and two scores from one camera do not satisfy that requirement. The '
         'ablation below is accordingly a measurement of the interlock as a decision rule '
         'operating on two decorrelated scores, and it is not a measurement of the '
         'two-transducer interlock the claims recite. The claimed configuration cannot be '
         'measured on any corpus that exists; it is measurement H2 together with H8 of '
         'Section 9.2, on the assembled node. Every figure below should be read subject to '
         'that limitation, and the reduction in false gating should not be quoted without it.')
    para(doc,
         'Three conclusions follow, and one non-conclusion. Requiring two channels to agree '
         'rather than either alone cuts false hardware gating by 69.6 % and the unassisted '
         'gate rate by 63.6 %, at a cost of one quarter of true gates — a large effect for '
         'a rule that adds no sensor and no computation, though obtained under the limitation '
         'stated above. The persistence counter trades sensitivity for quiet along a smooth '
         'curve, cutting false advisories by 64.7 % between n = 1 and n = 4 while true '
         'advisories fall from 58.7 % to 33.3 %. The scheduler as a whole reduces 419 eligible '
         'cycles to 83 actuations, a reduction of 80.2 %; for scale, the global session '
         'interval by itself would have left room for 1,297 actuations over the same replayed '
         'time, so the reduction is achieved by the persistence counter and the cooldowns '
         'rather than by the room-level interval. The non-conclusion is the escalation '
         'comparator, which '
         'on this corpus produces 83 actuations against 80 with it disabled. Its effect is '
         'negligible here and is reported as such; it is retained in the claims as a '
         'dependent feature because it bounds behaviour under sustained evidence, not because '
         'this corpus demonstrates a benefit.')
    figure(doc, 'fig08.png',
           'Figure 8. Enforcement discipline measured by replay of the recorded corpus. '
           '(a) the effect of the dual-channel interlock on true and false gating; (b) the '
           'persistence counter trading sensitivity against alert burden; (c) the reduction '
           'from eligible cycles to permitted actuations.',
           width=6.6)

    h2(doc, '8.7 Control-path latency')
    para(doc,
         'The software half of the perception-to-actuation path was timed directly, using the '
         'recorded corpus as input, on a commodity host. Channel extraction over one 20 s '
         'observation window takes 1.340 ms at the median and 3.294 ms at the ninety-fifth '
         'percentile; computation of the corroboration value takes 0.247 ms and 0.430 ms; the '
         'scheduler decision takes 0.4 µs. The total software path is 1.588 ms at the '
         'median and 3.724 ms at the ninety-fifth percentile, which is 0.06 % of the 2,500 ms '
         'control-cycle budget.')
    para(doc,
         'The transducer and actuation half is bounded from datasheet figures and standard '
         'interface limits and is labelled derived throughout: display panel response 8.3 ms '
         'at 120 Hz, node reporting interval 20.0 ms, USB full-speed frame 1.0 ms, photodiode '
         'edge to controller 0.005 ms, and gate command to switch 0.001 ms, giving 29.3 ms. '
         'The projected sense-to-gate latency is therefore 30.9 ms against the 200 ms '
         'responsiveness bound, leaving 169 ms of margin. The five derived rows are precisely '
         'what the build of Section 9 replaces with measurements; the useful conclusion from '
         'the measured half is that the control law is not the constraint, and a slower and '
         'cheaper node controller remains viable.')
    figure(doc, 'fig09.png',
           'Figure 9. Sense-to-gate latency budget, separating the measured software path from '
           'the derived transducer and actuation path. The hatched segments are the bench '
           'measurements the contemplated build would supply.',
           width=6.6)

    h2(doc, '8.8 Operating envelope and what is not established')
    para(doc,
         'The ocular corroboration channel reaches AUC 0.70 to 0.78 across configurations on '
         'eleven candidates. That is materially below the 74.98 % to 85.72 % condition-specific '
         'accuracy reported for keystroke dynamics against machine-assisted writing, and no '
         'claim is made in this disclosure that the ocular channel exceeds it. The comparison '
         'is in any case not like for like: the published benchmark answers whether a passage '
         'was assisted, offline, from one modality, whereas the ocular channel here is one '
         'corroborating input to a live actuation decision that no single modality may carry. '
         'The two figures in this disclosure that stand comparison with published work are the '
         'input-dynamics discontinuity, at 9.60 % equal-error and 0.954 AUC falling to 5.07 % '
         'under persistence, and the enforcement discipline, which has no published '
         'counterpart because the prior art does not actuate.')
    para(doc,
         'The apparatus is accordingly specified to operate as a graduated intervention and '
         'evidence system rather than as an adjudicator. An indication to the candidate is a '
         'low-cost, reversible action appropriate to moderate evidence. Interruption of the '
         'input path is a high-cost action reserved for cycles that satisfy the causal '
         'interlock and carry corroboration from two independent modalities and have persisted '
         'across consecutive cycles and fall within the permitted actuation rate. It is not '
         'asserted, and no claim should be construed to assert, that any actuation of this '
         'apparatus constitutes proof of malpractice.')
    para(doc,
         'Four limitations bound Section 8 and are stated without qualification. The ocular '
         'evaluation rests on eleven candidates from a single corpus recorded for a different '
         'purpose, and its onset marker is a software log line rather than a photometric '
         'measurement. The keystroke evaluation uses a different person’s typing as the '
         'contrast, which is a proxy for transcription and not transcription. The inertial '
         'evaluation uses a body-worn sensor to bound a desk-mounted one. And two elements of '
         'the apparatus — the acoustic emission-attribution unit (420) and the in-line '
         'gating unit (920) — are described and specified but have not been physically '
         'built or measured. That is the largest honest gap in this disclosure, it is the '
         'reason the readiness assessment at Section 11 is what it is, and Section 9 is the '
         'plan that closes it.')

    # ============================================================== 9
    h1(doc, '9. Contemplated Prototype and Planned Physical Validation')
    para(doc,
         'No physical prototype has been constructed as at the date of this disclosure, and '
         'no measurement on the contemplated transducers is reported anywhere in this '
         'document. This section is prospective. It is included to satisfy sufficiency by '
         'describing, in terms an ordinarily skilled person could follow, a specific hardware '
         'embodiment by which the invention may be reduced to practice, and to define in '
         'advance the experiment that would move the invention from its present readiness '
         'level to the next. Nothing in this section is a report of results obtained.')
    para(doc,
         'Two components of the embodiment do exist in a form that shortens the build and '
         'they are described here for completeness, with their status stated exactly. Node '
         'firmware has been written for the contemplated controller, implementing the '
         'adaptive-baseline onset detector, the coincidence accumulators, the inertial '
         'combination, the host protocol, the fail-safe gate polarity and the gate watchdog. '
         'A host-side control-law implementation has been written with two interchangeable '
         'back ends behind one interface: a replay back end that consumes recorded data and a '
         'serial back end that will consume live frames from the node. The replay back end '
         'reproduces the scheduler figures of Section 8.6 exactly, which verifies that the '
         'controller and the offline analysis implement the same control law. Neither fact is '
         'a physical measurement, and neither is offered as one; what they establish is that '
         'the software half of the system is written and self-consistent, and that connecting '
         'the transducers is a substitution of one back end for another rather than a rewrite.')

    h2(doc, '9.1 Contemplated station hardware')
    para(doc,
         'Representative components are set out below. They are recited as one enabling '
         'embodiment and are not limitations on the claims, which are drafted to be '
         'indifferent to the particular part. The parts are ordinary and readily obtained, '
         'which is deliberate: the object of the build is to place the claimed transducers '
         'physically into the decision loop, and a part chosen for the properties recited in '
         'the rationale column below is sufficient for that purpose.')
    table(doc, ['Ref', 'Representative component', 'Function', 'Rationale'],
          [['210', 'PIN photodiode with a transimpedance stage (BPW34 with OPA333 or LM358)',
            'Question-onset anchor T0 from a patch on the display panel',
            'Rise time under one microsecond, so the anchor is limited by panel response '
            'rather than by the sensor. Any photodiode of comparable rise time substitutes.'],
           ['400 / 401', '27 mm contact piezoelectric disc bonded to the desk underside, with '
            'a JFET or FET-input buffer at about 40 dB',
            'Structure-borne channel for emission attribution',
            'The piezo is a high-impedance source and needs buffering before any converter. '
            'Bonding location is on the underside so the element is not visible or accessible '
            'to the candidate.'],
           ['402', 'Electret microphone module with automatic gain disabled',
            'Airborne channel for emission attribution',
            'Attribution comes from coincidence between 400 and 402. Automatic gain must be '
            'disabled or the coincidence relation between the two channels is not preserved.'],
           ['403', 'Band-pass and envelope stage on each acoustic channel: 80 Hz to 1 kHz '
            'active band-pass, precision rectifier, low-pass at about 50 Hz',
            'Forms the envelope that is digitised, on both acoustic channels alike',
            'The converter never sees a speech waveform, so the node sampling rate is set by '
            'the envelope and not by speech bandwidth, and anti-aliasing is satisfied by the '
            'low-pass stage. Both channels must use identical stages or the envelope '
            'comparison between them is not meaningful.'],
           ['410', 'Six-axis inertial measurement unit on I²C, 100 Hz or above',
            'Desk motion for the reliability-transfer unit (430)',
            'Sampling rate must exceed the confirmation requirement of Section 8.5. Any '
            'six-axis part at 100 Hz or above substitutes.'],
           ['920', 'Analog USB switch or DPDT signal relay in the keyboard data pair',
            'In-line gating unit',
            'Rated for the signalling rate in use. The enable input must be held in the '
            'passing state by a pull-down so that the path is closed whenever the controller '
            'is unpowered.'],
           ['910 / 930', 'Common-cathode RGB indicator with series resistors',
            'Private indication to the candidate',
            'Visible to the seated candidate and not to neighbouring stations.'],
           ['—', 'Node controller with two or more analog inputs, I²C and a USB '
            'device interface',
            'Channel sampling, timestamping and gate drive',
            'A dual-core part is preferred so that sampling is not disturbed by host '
            'communication, but the measured control-path latency of Section 8.7 shows this '
            'is not a constraint.'],
           ['—', 'Perfboard, USB breakout pair, headers and wiring', 'Assembly',
            '—']],
          cap='Table 7: Contemplated Station Hardware',
          widths=[0.5, 1.75, 1.5, 2.55], size=8.8, align_left_cols=(1, 2, 3))

    para(doc,
         'Two properties of the build are design rules rather than implementation choices, '
         'and both are recited as claim limitations. The enable input of the gating unit is '
         'held in the passing state by a pull-down resistor, so the candidate’s keyboard '
         'works whenever the controller is unpowered, held in reset or hung; opening the input '
         'path is the active state and requires a live controller to assert it. And the '
         'firmware arms a watchdog before every gate assertion, releasing the gate if the '
         'decision layer stops refreshing it, so no unattended failure can hold a '
         'candidate’s keyboard open. Both properties are cheap to implement and directly '
         'demonstrable on the bench, and both exist because the consequence of a fault in this '
         'apparatus falls on a person sitting an examination.',
         lead='Non-optional design rules.')
    para(doc,
         'The examination application renders a small high-contrast patch in a corner of the '
         'display that inverts on every question transition, and the photodiode sits over it '
         'behind an opaque shroud. This is the standard technique for recovering true '
         'stimulus-onset timing in psychophysics and electroencephalography, and it is what '
         'converts T0 from a log line into a measured physical event. Anchor accuracy is then '
         'bounded by panel response rather than by software scheduling: about 8.3 ms at 120 Hz '
         'or 16.7 ms at 60 Hz, plus pixel transition time of typically 1 to 5 ms.',
         lead='The display patch.')

    h2(doc, '9.2 Smallest configuration that exercises the claims, and the planned '
              'protocol')
    para(doc,
         'One instrumented station and one confederate position exercise every claimed '
         'mechanism except the room-level global interval, which requires a second station. '
         'Two stations and one host are therefore the smallest configuration that exercises '
         'the claim set. The configuration is deliberately small: it is sufficient to '
         'demonstrate mechanism and insufficient to estimate operational performance.')
    para(doc,
         'Enrolment data would first be recorded from consenting volunteers performing '
         'ordinary unassisted work at the instrumented station, that data alone forming the '
         'enrolled profiles and the calibration set. Assisted episodes would then be staged '
         'with independently logged ground-truth timestamps, comprising a whispered question '
         'to a confederate with the answer returned through an earpiece, at varied helper '
         'latencies inside and outside the contemplated band, and with a neighbouring '
         'confederate speaking at similar volume as the attribution control. Ground truth '
         'would be used for evaluation only and never for calibration. Any trial would be '
         'conducted with consenting volunteers and not during a live institutional '
         'examination. Each measurement in Table 8 replaces a derived quantity of Section 8.7 '
         'or an element of Section 7 that has not been measured.')
    table(doc, ['#', 'Bench measurement', 'Derived expectation to be replaced',
                'Claim element it evidences'],
          [['H1', 'Photodiode edge against the software render callback, 500 transitions',
            'Offset stable within one refresh period; jitter under 2 ms',
            'Element (a): that T0 is a physical measurement independent of the examined '
            'machine'],
           ['H2', 'Coincidence of the contact and airborne channels for the candidate’s '
            'own whisper against a confederate whispering at 1 m',
            'Own-speech structure-borne level at least 10 dB above the neighbour’s',
            'Element (b): the attribution claim stands or falls here'],
           ['H3', 'Contact-channel response to typing impulses',
            'A clear per-keystroke transient more than 20 dB above the desk noise floor',
            'A second, independent commit-time anchor under Section 7.1(c)'],
           ['H4', 'Gate assertion to cessation of keyboard reports, 200 trials',
            'Under 2 ms, being one USB frame plus switch propagation',
            'The physical technical effect of the enforcement claim'],
           ['H5', 'Gate release to restoration of the input device',
            'Under 100 ms for re-enumeration',
            'Proportionality and reversibility of the intervention'],
           ['H6', 'Controller power removed during an asserted gate',
            'Path closes; keyboard restored',
            'The fail-safe limitation of Section 7 and of the claims'],
           ['H7', 'Host heartbeat stopped during an asserted gate',
            'Gate releases within the watchdog bound',
            'The watchdog limitation of Section 7 and of the claims'],
           ['H8', 'Desk inertial noise floor while seated',
            'Comparable to the seated median of 0.178 m/s² and p99 of 1.832 m/s² '
            'measured in Section 8.5',
            'That the desk sensor sees what the proxy corpus predicted']],
          cap='Table 8: Planned Bench Measurements',
          widths=[0.35, 2.05, 2.1, 1.85], size=8.7, align_left_cols=(1, 2, 3))

    para(doc,
         'H2 is the measurement to run first, and the reason is stated candidly: it is the '
         'riskiest element of the disclosure. If the candidate’s own whisper does not '
         'separate from a neighbour’s by a usable margin, the attribution unit must be '
         're-framed around contact events — typing impulses, leaning, hand placement on '
         'the desk — rather than around vocalisation, and the claim set should be '
         'rewritten before filing rather than defended after an objection.')

    h2(doc, '9.3 Predictions the trial would test, and its limits')
    para(doc,
         'The trial is specified so that it can fail. Four predictions follow from the '
         'architecture and each is falsifiable. First, the interval between the photometric '
         'onset and the attributed emission, and between that emission and the commit, should '
         'separate staged assisted episodes from unassisted work, and no attributed emission '
         'relating to a displayed item should arrive within the consultation bound of one '
         'second set at Section 7; if the intervals do not separate on physically acquired '
         'data, or if genuine consultations are found inside that bound, the causal interlock '
         'is not supported outside the proxy corpora and the bound must be re-derived. Second, a confederate speaking at a neighbouring position should '
         'fail to produce an attributed emission at the instrumented station; if it does '
         'produce one, element (b) fails and with it the claims that depend on attribution. '
         'Third, commit dynamics during transcription of a dictated answer should depart from '
         'the enrolled profile in the same direction and of an order comparable to the '
         'separation reported in Section 8.4; if transcription by the enrolled person is '
         'indistinguishable from composition by that person, the discontinuity comparator is '
         'not supported and the corpus figure was a proxy artefact. Fourth, the gate should '
         'assert and release within the bounds of H4 to H7; if it does not, the enforcement '
         'claims require narrowing.')
    para(doc,
         'Even if every prediction were confirmed, such a trial would establish only that the '
         'mechanisms operate on physically acquired data at one instrumented station. Three '
         'limitations would bound it. The environment would be a controlled room rather than a '
         'populated examination hall, lacking crowd acoustics, invigilator movement and the '
         'structural coupling of a hall full of occupied desks. The number of participants '
         'would be small, and the ocular and input-dynamics figures would carry wide intervals. '
         'And assisted episodes would be staged by informed volunteers rather than performed '
         'adversarially by candidates with an incentive to evade detection; in particular, no '
         'staged trial measures what happens when a candidate learns that whispering is what '
         'triggers the gate. Performance in an operational hall should be expected to fall '
         'below both the figures of Section 8 and any figures such a trial produced, and this '
         'disclosure does not assert otherwise.')

    # ============================================================== 10
    h1(doc, '10. Aspects of the Invention Requiring Protection (Claims)')
    para(doc,
         'The following elements are considered novel and inventive and are proposed for '
         'protection. Claims 1, 13, 19 and 20 are independent. Every independent claim '
         'terminates in the interruption of a physical data path by a switching element; '
         'none may be satisfied by producing a report, an alert or a display. The set is '
         'drafted on three '
         'principles. First, the independent system claims are distinguished by runtime '
         'operations of the deployed apparatus — derivation of the onset instant from '
         'emitted light, attribution by coincidence between physically distinct transducers, '
         'evaluation of a bounded latency relation, and conditioning of a physical actuation '
         'on two independent modalities — all of which are inspectable properties of the '
         'running system rather than characteristics of a training process. Second, the '
         'safety limitations of the gating unit are drawn into the independent enforcement '
         'claim rather than left as optional refinements, because an actuation claim that does '
         'not recite them describes an apparatus the inventor would not deploy. Third, no '
         'claim is directed to a computer-readable medium, to a set of instructions, or to a '
         'data structure as such. The subject matter claimed is the apparatus and its '
         'operation: a sensor receiving light emitted by a panel, two acoustic transducers '
         'differing in the physical path by which sound reaches them, an inertial sensor, and '
         'a switching element in series with a data path. A medium claim would add nothing '
         'that Claims 19 and 20 do not already reach, and would invite the objection the '
         'remainder of the set is drafted to avoid.')

    figure(doc, 'fig10.png',
           'Figure 10. Structure of the claim set. Four independent claims carry the '
           'apparatus, the enforcement arrangement and the two methods, each terminating in '
           'interruption of a physical data path; the dependents refine each of them, and two '
           'deployment claims refer back to the system claims.', width=6.4)

    h2(doc, 'A. System claims \u2014 causal latency interlock at a monitored station')
    para(doc,
         'An integrity-monitoring system for a monitored assessment station, comprising: a '
         'display panel arranged to present assessment items to a candidate at the station; a '
         'photometric sensor disposed to receive light emitted by a region of said display '
         'panel and to produce an onset signal; an acoustic sensing arrangement comprising a '
         'first transducer mechanically coupled to a work surface of the station and a second '
         'transducer responsive to airborne sound at the station; an input-device interface '
         'receiving input events from at least one input device of the station; a processing '
         'unit coupled to the display panel, the photometric sensor, the acoustic sensing '
         'arrangement and the input-device interface; and an actuator arrangement comprising a '
         'gating unit disposed in series with a data path of said input device; wherein the '
         'processing unit is configured to: derive, from a '
         'transition of the onset signal, a presentation instant T0 for an assessment item, '
         'said instant being derived from light emitted by the display panel and '
         'independently of any item-presentation event reported by a machine executing the '
         'assessment; derive an emission instant T1 attributed to the candidate seated at the '
         'station, said instant being registered only where the first transducer and the '
         'second transducer each exceed a respective threshold within a coincidence window '
         'and a measure of correlation between the band-limited envelopes of the two '
         'transducers across said window exceeds a consistency threshold, whereby neither an '
         'acoustic emission originating at another station and not coupled through said work '
         'surface, nor a concurrence of a mechanical impulse at said work surface with an '
         'unrelated airborne emission, produces an attributed emission instant; derive, from the '
         'input-device interface, a commit instant T2 at which a response to said assessment '
         'item is committed; determine whether an interval between T0 and T1 lies within a '
         'bounded consultation interval, the lower bound of said consultation interval being '
         'not less than a minimum item-apprehension interval and the upper bound thereof '
         'being not later than a presentation instant derived for a succeeding assessment '
         'item, whereby the attributed emission is bound to one identified assessment item; '
         'determine whether an interval between T1 and T2 lies within a bounded assistance '
         'interval having a lower bound and an upper bound; derive a corroboration value at '
         'least from both said determinations; and, when the corroboration value satisfies an '
         'eligibility condition, cause the gating unit to interrupt said data path.',
         lead='Claim 1 (independent).')
    bullets(doc, [
        ('Claim 2.', 'The system of Claim 1, wherein the photometric sensor is disposed over '
         'a region of the display panel in which the assessment application renders a patch '
         'whose luminance changes upon each transition between assessment items, and wherein '
         'the processing unit detects said transition against an adaptive baseline with a '
         'holdoff interval between successive presentation instants.'),
        ('Claim 3.', 'The system of Claim 1, wherein the coincidence window has a duration '
         'greater than the difference in propagation delay between the structure-borne path '
         'to the first transducer and the airborne path to the second transducer over the '
         'dimensions of the station, and shorter than the shortest interval separating '
         'distinct utterances; wherein each of the first and second transducers is '
         'band-limited to a range of voice fundamental and first-formant frequencies before '
         'the respective threshold is applied, such that neither transducer alone can register '
         'an emission instant; wherein each acoustic channel is band-limited and rectified by '
         'an analog stage preceding digitisation, such that the quantity digitised is an '
         'envelope and the sampling rate at the processing unit is determined by the '
         'bandwidth of that envelope rather than by the bandwidth of speech; and wherein each '
         'said threshold is maintained relative to a '
         'baseline adapted over a time constant long compared with said coincidence window, '
         'such that drift in the ambient level at the station does not alter the coincidence '
         'condition.'),
        ('Claim 4.', 'The system of Claim 1, further comprising an enrolled profile store '
         'holding statistics of input-event timing of the candidate gathered during an '
         'enrolment interval, wherein the processing unit computes a discontinuity measure '
         'between input-event timing preceding T2 and said statistics, and includes said '
         'measure in the corroboration value.'),
        ('Claim 5.', 'The system of Claim 4, wherein the discontinuity measure is a scaled '
         'distance between a vector of hold intervals and inter-event intervals and '
         'corresponding statistics of the enrolled profile, the scaling being derived from '
         'dispersion of the enrolled profile.'),
        ('Claim 6.', 'The system of Claim 1, further comprising an inertial sensor coupled to '
         'the station and an imaging sensor directed at the candidate, wherein the processing '
         'unit derives a motion magnitude from the inertial sensor and applies said magnitude '
         'both to reduce a confidence threshold applied to a quantity derived from the imaging '
         'sensor and to increase a weight applied to a quantity derived from the acoustic '
         'sensing arrangement.'),
        ('Claim 7.', 'The system of Claim 6, wherein the reduction of said confidence '
         'threshold is bounded below by a floor value and the motion magnitude is saturated at '
         'a maximum value, such that a single impulse applied to the station cannot reduce the '
         'confidence threshold below said floor.'),
        ('Claim 8.', 'The system of Claim 6, wherein a departure of gaze from a region '
         'associated with the display panel is admitted to the corroboration value only where '
         'the motion magnitude exceeds a qualification threshold within a corresponding '
         'interval.'),
        ('Claim 9.', 'The system of Claim 6, wherein the corroboration value is further '
         'derived from one or more quantities, derived from said imaging sensor, describing a '
         'geometry of departures from and '
         'returns to a region associated with the display panel, said quantities comprising an '
         'angular concentration of departure bearings, a dispersion of return landing '
         'positions, and a count of departure-and-return pairs of bounded duration.'),
        ('Claim 10.', 'The system of Claim 1, wherein the bounds of the consultation '
         'interval and of the assistance interval are each established per candidate by '
         'displacing a default bound by a statistic of the distribution of commit intervals '
         'observed from that candidate during an enrolment interval of unassisted work, no '
         'attributed emission instant arising during such an interval.'),
        ('Claim 11.', 'The system of Claim 1, further comprising an evidence record store '
         'receiving, for each control cycle, the instants T0, T1 and T2, the quantities from '
         'which the corroboration value was derived, and the output produced, whereby each '
         'output carries a self-contained record of the measurements that produced it.'),
        ('Claim 12.', 'The system of Claim 1, further comprising a node controller disposed '
         'at the station, wherein the processing unit reduces each acoustic channel, within '
         'each of a succession of analysis windows, to a peak magnitude and a '
         'root-mean-square magnitude of the envelope formed by the analog stage, and wherein '
         'the quantities passed beyond said node controller consist of said magnitudes, a '
         'scalar motion magnitude, the instants derived in Claim 1 and quantities derived '
         'from an imaging sensor, whereby the phase relations and the temporal fine structure '
         'on which the intelligibility of speech depends are absent from every quantity that '
         'leaves the node controller and cannot be recovered from those that do; and wherein '
         'no acoustic waveform and no image frame is retained beyond derivation of said '
         'quantities.'),
    ])

    h2(doc, 'B. System claims — graduated enforcement under a dual-channel interlock')
    para(doc,
         'An enforcement system for a monitored assessment station at which a candidate is '
         'seated, comprising: a plurality of sensing modalities disposed at the station, each '
         'comprising a transducer responsive to a different physical quantity from that of '
         'every other said modality; a processing unit deriving a per-modality quantity from '
         'each and '
         'combining said quantities into an ordinal corroboration value; a gating '
         'unit disposed in series with a data path of an input device of the station and '
         'having an enable input; and an indicator disposed to be perceptible to the candidate '
         'at the station; wherein the processing unit is configured to: maintain an '
         'enforcement state over an ordered plurality of severities, at least one severity '
         'causing operation of the indicator and at least one further severity causing the '
         'gating unit to interrupt said data path; treat a control cycle as eligible where the '
         'corroboration value satisfies an eligibility condition; advance the enforcement '
         'state only where the control cycle is eligible on each of n consecutive control '
         'cycles, n being an integer not less than two; withhold '
         'advancement where an interval since a previous actuation upon the same candidate is '
         'less than a cooldown interval, or where an interval since a previous actuation at '
         'any station of the venue is less than a global interval; and permit any severity '
         'that acts upon said data path or that withholds the assessment session, including '
         'the highest severity of the ordered plurality, only where at least two of said '
         'sensing modalities have each exceeded a respective threshold within the same control '
         'cycle, no such severity being reachable upon the evidence of one modality alone; '
         'and wherein the enable input of the gating unit is biased toward a state in which '
         'said data path is continuous, such that the data path is continuous whenever the '
         'processing unit is unpowered or not asserting said input, and wherein an assertion '
         'of said input is released automatically in the absence of a periodic refresh from '
         'the processing unit.',
         lead='Claim 13 (independent).')
    bullets(doc, [
        ('Claim 14.', 'The system of Claim 13, wherein the ordered plurality of severities '
         'comprises, in order: recording without output; a private indication to the '
         'candidate; a notification to an invigilator; interruption of the input data path for '
         'a bounded interval; and a session hold requiring release by a human operator.'),
        ('Claim 15.', 'The system of Claim 13, further comprising an escalation comparator '
         'configured, upon a sustained increase in the corroboration value, to reduce the '
         'cooldown interval and the global interval by a bounded fraction, said comparator '
         'being incapable of reducing either interval to zero.'),
        ('Claim 16.', 'The system of Claim 13, wherein one of said sensing modalities '
         'comprises a transducer mechanically coupled to a work surface of the station and '
         'another comprises an imaging sensor directed at the candidate, such that the two '
         'quantities compared by the interlock originate in a mechanical measurement and an '
         'optical measurement respectively.'),
        ('Claim 17.', 'The system of Claim 13, wherein one of said sensing modalities '
         'comprises an input-device interface and the per-modality quantity derived therefrom '
         'is a discontinuity measure between input-event timing preceding a commit and '
         'statistics of the same quantities gathered from the candidate during an enrolment '
         'interval, and wherein n is not greater than eight.'),
        ('Claim 18.', 'The system of Claim 13, wherein the gating unit comprises an analog '
         'switch or a signal relay disposed in a data pair of the input device, and wherein '
         'interruption of the data path is effected by opening said data pair.'),
    ])

    h2(doc, 'C. Method claims')
    para(doc,
         'A method for detecting externally assisted responding at a monitored assessment '
         'station, comprising: receiving, at a photometric sensor disposed to receive light '
         'emitted by a display panel of the station, an onset signal, and deriving from a '
         'transition thereof a presentation instant T0 for an assessment item independently of '
         'any item-presentation event reported by a machine executing the assessment; '
         'acquiring signals from a transducer mechanically coupled to a work surface of the '
         'station and from an airborne acoustic transducer, and deriving an emission instant '
         'T1 only where both exceed a respective threshold within a coincidence window and a '
         'measure of correlation between the band-limited envelopes of the two transducers '
         'across said window exceeds a consistency threshold; '
         'deriving from an input-device interface a commit instant T2 at which a response to '
         'said item is committed; determining whether an interval between T0 and T1 lies '
         'within a bounded consultation interval whose lower bound is not less than a minimum '
         'item-apprehension interval and whose upper bound is not later than a presentation '
         'instant derived for a succeeding item; determining whether an interval between T1 '
         'and T2 lies within a bounded assistance interval; deriving a corroboration '
         'value at least from both said determinations; and, when the corroboration value '
         'satisfies an eligibility condition, interrupting a data path of an input device of '
         'the station by means of a gating unit disposed in series therewith.',
         lead='Claim 19 (independent).')
    para(doc,
         'A method of graduated enforcement at a monitored assessment station, comprising: '
         'deriving a per-modality quantity from each of a plurality of sensing modalities '
         'disposed at a station at which a candidate is seated, each said modality comprising '
         'a transducer responsive to a different physical quantity from that of every other '
         'said modality; maintaining an '
         'enforcement state over an ordered plurality of severities; advancing said state only '
         'upon satisfaction of an eligibility condition on each of n consecutive control '
         'cycles, n being an integer not less than two, and only where a per-candidate '
         'cooldown interval and a venue-wide global '
         'interval have both elapsed; permitting any severity that acts upon a data path of an '
         'input device of the station or that withholds the assessment session, including the '
         'highest severity of the ordered plurality, only where at least two of said '
         'modalities have each exceeded a respective threshold within the same control cycle; '
         'interrupting said '
         'data path by de-asserting an enable input of a gating unit disposed in series '
         'therewith, said input being biased toward continuity of the path; releasing said '
         'interruption automatically in the absence of a periodic refresh; and recording each '
         'control cycle with the quantities and the decision that produced it.',
         lead='Claim 20 (independent).')
    bullets(doc, [
        ('Claim 21.', 'The method of Claim 19, further comprising computing a discontinuity '
         'measure between input-event timing preceding T2 and statistics of the same '
         'quantities gathered from the candidate during an enrolment interval, and including '
         'said measure in the corroboration value.'),
        ('Claim 22.', 'The method of Claim 19, further comprising acquiring a signal from an '
         'imaging sensor directed at the candidate and a signal from an inertial sensor '
         'coupled to the station, deriving a motion magnitude from the latter, and applying '
         'said magnitude both to reduce a confidence threshold applied to a quantity derived '
         'from said imaging sensor and to increase a weight applied to an acoustic-derived '
         'quantity.'),
        ('Claim 23.', 'The method of Claim 19, further comprising reducing each '
         'acoustic channel, within each of a succession of analysis windows, to scalar '
         'envelope statistics comprising a peak magnitude and a root-mean-square magnitude of '
         'an envelope formed by an analog band-pass and rectifying stage, and passing only '
         'said statistics, a scalar motion magnitude and the derived instants beyond a node '
         'controller disposed at the station, whereby the phase relations and the temporal '
         'fine structure on which the intelligibility of speech depends are absent from every '
         'quantity so passed and cannot be recovered from those that are; and wherein no '
         'acoustic waveform and no image frame is retained beyond derivation of the '
         'quantities used.'),
    ])

    h2(doc, 'D. Deployment claims')
    bullets(doc, [
        ('Claim 24.', 'The system of Claim 13, wherein the per-modality quantities are '
         'derived at a node controller disposed at the station and the enforcement state is '
         'maintained at a host serving a plurality of such stations within the venue, said '
         'host maintaining the global interval across all of them, and wherein the gating unit '
         'is driven by the node controller and not by said host.'),
        ('Claim 25.', 'The system of Claim 1 or Claim 13, wherein the station is one of a '
         'plurality of stations of an examination hall, a professional certification or '
         'licensing test centre, a secure interview or vetting room, a recruitment or aptitude '
         'testing facility, or a defence or public-service selection examination, and the '
         'global interval is maintained across said plurality.'),
    ])
    para(doc,
         'The embodiment described at Section 7.1(h) — direction-of-arrival estimation '
         'assigning an emission to a specific neighbouring station — is deliberately '
         'excluded from the claim set, as it has not been reduced to practice. It is '
         'disclosed in the specification so that priority is preserved should it be claimed in '
         'a later continuation or subsequent application.',
         lead='Note on scope.')

    # ============================================================== 11
    h1(doc, '11. Technology Readiness Level (TRL)')
    para(doc,
         'The invention has been formulated as a specific architecture (Sections 6 and 7) and '
         'its control layer has been validated on recorded human data across four corpora, '
         'with per-mechanism ablations and a directly measured control-path latency '
         '(Section 8). Node firmware and a host-side control-law implementation exist and the '
         'latter has been verified against the offline analysis by replay. No physical '
         'prototype has been constructed, no measurement on the contemplated transducers has '
         'been made, and the acoustic attribution unit and the in-line gating unit remain '
         'described rather than built. Readiness is therefore assessed at TRL 3 — '
         'experimental proof of concept. Successful completion of the bench measurements and '
         'the staged trial described at Section 9 would support an assessment of TRL 4, and '
         'no higher.')
    trl = doc.add_table(rows=4, cols=9)
    trl.style = 'Table Grid'
    trl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for lo, hi, lab in ((0, 2, 'Research'), (3, 5, 'Development'),
                        (6, 8, 'Deployment')):
        m = trl.rows[0].cells[lo].merge(trl.rows[0].cells[hi])
        m.text = ''
        pp = m.paragraphs[0]
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(pp, lab, size=9.5, bold=True)
    trl = trl  # rows 1..3 hold the ladder
    names = ['Basic principles observed', 'Technology concept formulated',
             'Experimental proof of concept', 'Technology validated in lab',
             'Validated in relevant environment', 'Demonstrated in relevant environment',
             'Prototype in operational environment', 'System complete and qualified',
             'Proven in operational environment']
    for i in range(9):
        c = trl.rows[1].cells[i]
        c.text = ''
        pp = c.paragraphs[0]
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(pp, 'TRL %d' % (i + 1), size=9, bold=True)
        c2 = trl.rows[2].cells[i]
        c2.text = ''
        pp = c2.paragraphs[0]
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(pp, names[i], size=7.8)
        c3 = trl.rows[3].cells[i]
        c3.text = ''
        pp = c3.paragraphs[0]
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(pp, '\u2713' if i < 3 else '', size=12, bold=True)
        c.width = c2.width = c3.width = Inches(0.71)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    _run(p, 'Current TRL: Level 3 — Experimental Proof of Concept.', size=11,
         bold=True)

    # ============================================================== 12
    h1(doc, '12. Note on Filing')
    para(doc, 'Seven matters are flagged for the IPR & TT Cell.')
    para(doc,
         'subject-matter eligibility, the primary anticipated objection. The invention is a '
         'computer-related invention and an objection under the exclusion in the Patents Act, '
         '1970 covering a mathematical method, a business method, a computer programme per se '
         'and algorithms should be expected before any objection on novelty or inventive step. '
         'The objection is anticipated and the following response is proposed. The independent '
         'claims are directed to a system comprising a photometric sensor receiving light '
         'emitted by a display panel, a transducer mechanically coupled to a work surface, an '
         'inertial sensor, and a gating unit disposed in series with the data path of an input '
         'device; the technical effect is not confined to the execution of a program on a '
         'general-purpose computer. That effect consists in (i) derivation of a timing '
         'reference from a measured physical emission rather than from a reported software '
         'event, so that a misreported or delayed rendering event does not corrupt the '
         'reference and a suppressed transition yields no reference at all rather than '
         'a false one. The argument must be put in those terms and not as independence '
         'from the examined machine, since in the principal embodiment that machine '
         'renders the patch, and an examiner who reads Section 9.1 will notice; (ii) '
         'discrimination of the physical origin of an acoustic emission by the presence or '
         'absence of structural coupling, so that a sound is attributed to one seat and not '
         'another; (iii) a change in the electrical continuity of a data path effected by a '
         'physical switching element, which is a change in the state of hardware and not an '
         'output of a program; and (iv) a fail-safe bias and watchdog release governing that '
         'switching element, which are properties of the circuit that hold when the program is '
         'not running at all. Press (iii) first. It is the effect the prior art in this field '
         'does not produce at all: a change in the electrical continuity of a physical '
         'data path, outside the computer, which no characterisation of the contribution '
         'as instructions can reach. Press (ii) second. Do not lead with (iv), attractive '
         'as it is, because the fail-safe bias and the watchdog are conceded prior art at '
         'entries 8 and 16 of Section 3, and a Controller applying the '
         'substance-of-the-contribution test will answer that the circuit property relied '
         'upon exists in the prior-art gate without this invention. (iv) answers the '
         'narrow question whether the claim contains anything but instructions; it does '
         'not answer the question the Controller actually asks.',
         lead='First:')
    para(doc,
         'the drafting consequence. The complete specification should recite the hardware '
         'limitations of the independent claims substantively rather than nominally, and each '
         'technical effect above should appear in the description as ordinary engineering '
         'exposition — naming the transducers, the physical quantities, the circuit '
         'states — rather than as argument. A registered patent agent should verify this '
         'alignment against the current Guidelines for Examination of Computer Related '
         'Inventions before filing, and should confirm that the enforcement claim of Claim 13 '
         'is drafted so that the switching element and its bias are unambiguously apparatus '
         'limitations.',
         lead='Second:')
    para(doc,
         'a co-pending internal disclosure of the same inventor. A separate disclosure by this '
         'inventor addresses label-free detection of malpractice by self-supervised predictive '
         'residual analysis and cross-station correlation. The two are complementary rather '
         'than overlapping and the boundary should be recorded now rather than argued later. '
         'That disclosure claims how a per-station anomaly score is produced without labelled '
         'malpractice, and its output is an alert. The present disclosure claims a timing '
         'relation between three physically measured instants and a graduated physical '
         'intervention conditioned on independent corroboration; it does not claim any method '
         'of producing an anomaly score, and its corroboration value could in principle be '
         'supplied by the other disclosure’s residual. Neither claim set anticipates the '
         'other on the inventor’s reading, but the agent should review both together, '
         'since common inventorship and an overlapping field make a double-patenting or '
         'obviousness-type objection foreseeable if they are filed independently and without '
         'cross-reference.',
         lead='Third:')
    para(doc,
         'claim breadth and the weakest positions. The inventor regards Claim 13 and '
         'Claim 20, into which the interlock and the fail-safe properties are drawn as '
         'positive limitations, as the strongest position, and would prefer narrowing of '
         'Claim 1 to any concession on those. Claim 1 has already been narrowed on that '
         'principle. Attribution by coincidence between a work-surface-coupled transducer and '
         'an airborne transducer was moved out of the dependent claims and into Claim 1 '
         'itself, because it is the element that distinguishes this apparatus from every '
         'acoustic proctoring reference located, and a Claim 1 that merely asserted an '
         'emission to be attributed without reciting the structure effecting the attribution '
         'invited both an anticipation objection and an objection on sufficiency. On the same '
         'principle Claim 1 now recites two bounded intervals rather than one, so that the '
         'photometric anchor T0 performs work in the claim — it bounds the emission from '
         'below and binds it to one identified item — rather than appearing only as an '
         'ordering condition that an examiner could read out as non-functional. Two exposures '
         'are recorded here rather than left for the examiner. Claim 2 recites a rendered '
         'patch and a photodiode, which is standard practice in psychophysics instrumentation '
         'and is defensible only in the combination, not alone. Claim 18 recites an analog '
         'switch in a data pair, which is entry 8 of Section 3 and should be conceded if '
         'pressed; the substance is in the condition governing it, not in the switch. If the '
         'agent prunes for fee purposes, the inventor regards Claims 3, 6, 7, 8, 12, 14 and '
         '16 as the dependents most worth keeping. Claim 3 deliberately carries four '
         'separable limitations — the bounds on the coincidence window, the band-limiting, '
         'the envelope-consistency requirement and the adapted baseline — because an '
         'internal disclosure is not a filed claim set; the agent should split it into '
         'separate dependents at drafting, and the envelope-consistency limitation is the one '
         'of the four worth its own claim, since it is what answers the concurrence of a '
         'keystroke with a neighbour’s speech. No claim to a computer-readable medium is '
         'included, and none should be added: the agent is asked to resist the reflex of '
         'adding one at drafting.',
         lead='Fourth:')
    para(doc,
         'state of reduction to practice. The invention stands at TRL 3. Section 8 reports '
         'measurements on recorded human corpora that stand in for the contemplated '
         'transducers, and states in each case what the substitution costs. Section 9 is '
         'prospective throughout and reports no measurement on the contemplated hardware. Two '
         'claimed elements — acoustic attribution and the in-line gate — have not '
         'been built. Nothing in this disclosure should be represented to any external party '
         'as a measurement of the assembled apparatus, and the sample sizes and the negative '
         'results in Section 8 should travel with any figure quoted from it. For the Cell'"'"'s '
         'internal costing only, and not for the specification: the component set of '
         'Table 7 is of the order of INR 1,150 per station exclusive of enclosure and '
         'labour, and the two-station configuration of Section 9.2 of the order of INR 2,500. '
         'Cost figures were removed from the body of this disclosure because they are '
         'commercial rather than technical, they date the document, and an applicant'"'"'s own '
         'statement that a build is cheap and ordinary is quotable against it on inventive '
         'step.',
         lead='Fifth:')
    para(doc,
         'this note is internal and must not enter the filed specification, and neither may '
         'Sections 8, 9 and 12. A specification that argues its own patentability, names the '
         'exclusion it seeks to avoid, or characterises its own validation as preliminary '
         'invites the examiner to adopt the applicant’s characterisation and can be read '
         'as an admission. The candour in this document is owed to the Cell and to the '
         'drafting agent, and it belongs here rather than in a filed instrument. No part of '
         'this work has been publicly disclosed; no preprint, demonstration or public '
         'repository exists, and none should be made until a priority date is secured. If the '
         'prototype of Section 9 is built, any demonstration should be deferred or conducted '
         'under a written confidentiality undertaking.',
         lead='Sixth:')
    para(doc,
         'unity of invention. Claim 1 and Claim 13 are separate independent system claims and '
         'an objection that they lack a single general inventive concept is foreseeable. The '
         'position taken here is that they share one, and the claims were amended so that they '
         'plainly do: a corroboration value derived from transducers responsive to different '
         'physical quantities governs the interruption of the candidate input path by a '
         'switching element in series with it, and both independent system claims now recite '
         'that value, that switching element and that interruption. Claim 1 constrains how the value is earned, and Claim 13 '
         'constrains what the value is permitted to do. Should the objection nevertheless be '
         'pressed, the inventor’s preference is to prosecute Claim 13 in the parent and file '
         'Claim 1 as a divisional rather than the reverse, because the enforcement claim '
         'carries the hardware limitations that answer the eligibility objection recorded '
         'above.',
         lead='Seventh:')

    endp = doc.add_paragraph()
    endp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    endp.paragraph_format.space_before = Pt(18)
    _run(endp, '————— END OF THE DOCUMENT —————', size=11, bold=True)

    cp = doc.core_properties
    cp.author = 'VIT IPR & TT Cell'
    cp.last_modified_by = 'VIT IPR & TT Cell'
    cp.title = 'Causal Emission-Response Interlock - IDF-B'
    cp.comments = ''
    cp.category = ''
    cp.keywords = ''

    out = os.path.join(HERE, 'IDF-B_Causal_Emission_Response_Interlock.docx')
    doc.save(out)
    print('wrote', out)


if __name__ == '__main__':
    build()
