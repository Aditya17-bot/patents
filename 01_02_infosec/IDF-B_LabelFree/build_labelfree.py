"""Build the IDF-B disclosure for the label-free malpractice-detection
invention, revision 7.

Layout follows IDF-B-Project1-Group05.pdf: VIT masthead table, twelve numbered
sections in plain prose, monochrome Times New Roman tables with the caption
below in bold, figures with the caption below, and the closing rule.

Every number in Section 8 Part B is read from evidence/results at build time.
"""
import json
import os
import sys

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, 'figures')
ASSETS = os.path.join(HERE, 'assets')
RES = os.path.join(os.path.dirname(HERE), 'evidence', 'results')

BODY_FONT = 'Times New Roman'
CAP_FONT = 'Arial'


# ----------------------------------------------------------------- measured
def J(name):
    with open(os.path.join(RES, name), 'r', encoding='utf-8') as f:
        return json.load(f)


SMD = J('e3_smd_commensurability.json')
SMDB = J('e3_smd_commensurability_big.json')
REP = J('e3_repeat.json')
CPL = J('e3_coupling.json')
ENV = J('e3_envelope.json')


def pc(x):
    return '%.1f %%' % (100.0 * x)


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
    """Figure caption: below the figure, centred, bold lead."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(12)
    parts = text.split('. ', 1)
    _run(p, parts[0] + '.', size=9.5, bold=True, font=CAP_FONT)
    if len(parts) > 1:
        _run(p, ' ' + parts[1], size=9.5, font=CAP_FONT)


def figure(doc, name, cap, width=6.4):
    doc.add_picture(os.path.join(FIG, name), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.space_before = Pt(8)
    doc.paragraphs[-1].paragraph_format.space_after = Pt(2)
    caption(doc, cap)


def tcaption(doc, text):
    """Table caption: below the table, centred, entirely bold, Times."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(12)
    _run(p, text, size=10.5, bold=True)
    return p


def table(doc, headers, rows, cap=None, widths=None, size=9.5,
          align_left_cols=()):
    """Monochrome Table Grid, bold centred header, no fill anywhere."""
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


def running_heads(sec):
    sec.different_first_page_header_footer = False
    h = sec.header.paragraphs[0]
    h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    h.paragraph_format.space_after = Pt(0)
    _run(h, '©VIT IPR & TTCELL', size=11, bold=True)
    f = sec.footer.paragraphs[0]
    f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    f.paragraph_format.space_before = Pt(0)
    _fld(f, ' PAGE ', '1')


def letterhead(doc):
    """The VIT IDF-B masthead block, as in the reference filing."""
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


# ----------------------------------------------------------------- sections
def sec1(doc):
    h1(doc, '1. Title of the Invention')
    para(doc,
         'A Venue-Scale Integrity-Monitoring Installation and Method for '
         'Distinguishing Coordinated Malpractice from Coincidental Anomaly at '
         'Monitored Assessment Stations, by Common-Mode-Corrected Time-Lagged '
         'Coupling of Station-Local Predictive Residuals Obtained Without '
         'Labelled Examples of Malpractice.')


def sec2(doc):
    h1(doc, '2. Field / Area of Invention')
    para(doc,
         'The present invention relates to integrity monitoring of supervised '
         'assessment and controlled-access environments, and to the automated '
         'detection of prohibited communication, prohibited device use, and '
         'coordinated collusion within such environments. More specifically, '
         'it pertains to an installation in which a sensing assembly of '
         'acoustic and further transducers is mechanically carried by each '
         'monitored station, in which a predictive model and its calibration '
         'statistics are established separately at each such station from '
         'sanctioned activity alone, and in which the resulting prediction '
         'residuals of several stations are compared with one another, after '
         'a component common to the venue has been estimated and removed, in '
         'order to resolve a time-lagged coupling between one pair of '
         'stations. The invention further relates to a station instrumented '
         'in like manner and deliberately held unoccupied, whose output '
         'supplies part of that common-mode reference, and to the physical '
         're-tasking of the sensing assemblies of an implicated pair of '
         'stations once such a coupling has been resolved.')
    para(doc,
         'The principal embodiment described herein is an examination hall of '
         'instrumented desks. The invention is not limited to that '
         'embodiment: it applies equally to professional certification and '
         'testing centres, secure interview and vetting rooms, recruitment '
         'and aptitude testing facilities, controlled-access screening areas, '
         'and any supervised environment in which unauthorised communication '
         'or device use is prohibited, in which sanctioned activity is '
         'abundant while violations are rare, and in which several monitored '
         'positions share one physical space.')


PRIOR_ROWS = [
    ('1', 'CN 106023516 A — examination monitoring method and system',
     '2016 / patent',
     'Examination-hall monitoring using infrared perimeter sensors, '
     'human-posture sensors and face-recognition cameras; behaviour compared '
     'against set values to raise a warning.',
     'Decision by comparison against preset values; requires the abnormal '
     'behaviour to be specified in advance. Hall-level, not per-station. '
     'Blind to concealed electronic devices and to covert audio. Scores each '
     'position independently, so no relation between positions is formed.'),
    ('2', 'US 9,154,748 B2 — online examination proctoring system',
     '2015 / patent',
     'Worn and fixed cameras with unpredictable prompts to sweep the room; '
     'audio capture of the test environment; evidence indexed and stored.',
     'Depends on visual evidence and on prompting the candidate. No '
     'physical-signature sensing of concealed emitters; no analysis relating '
     'one candidate to another.'),
    ('3', 'CN 111539313 A — examination cheating behaviour detection '
     'method and system', '2020 / patent',
     'Gaze tracking of the examinee together with video analysis of the '
     'region in front of the candidate to produce a cheating-behaviour '
     'result.',
     'Supervised and vision-bound; recognises behaviours it was built to '
     'recognise. Single-candidate scope; no cross-candidate relational '
     'signal.'),
    ('4', 'US 9,881,516 B1 — detecting cheating while administering '
     'online assessments', '2018 / patent',
     'Watermarked question items propagated to seed sites with web beacons, '
     'so that retrieval of an item during a test is observable.',
     'Detects item leakage on the open web, not conduct at a monitored '
     'station. Inapplicable to in-hall device use or to candidate-to-candidate '
     'coordination.'),
    ('5', 'CN 200989924 Y — detector for concealed wireless earpieces '
     'used in examination cheating', '2007 / patent',
     'Induction antenna and amplifier detecting the electromagnetic signature '
     'of a concealed earpiece, with acousto-optic indication of signal '
     'strength.',
     'Single-modality, single-purpose, and operated as a handheld sweep. No '
     'continuous per-station monitoring, no learning of ambient conditions, '
     'no relational analysis.'),
    ('6', 'US 11,917,324 B2 — anti-cheating methods in an extended '
     'reality environment', '2024 / patent',
     'Tracking of candidate hands and arms against a defined spatial boundary '
     'in an extended-reality examination, with audiovisual recording for '
     'review.',
     'Boundary rules are specified by the test giver in advance. Confined to '
     'an extended-reality environment; no physical-emission sensing and no '
     'station-to-station comparison.'),
    ('7', 'Radio-frequency signal jammers for examination halls', 'category',
     'Denial of mobile and wireless communication within the hall during the '
     'examination.',
     'Preventive rather than detective; produces no record of an attempt. May '
     'interfere with authorised systems and is ineffective against passive or '
     'non-radio methods.'),
    ('8', 'US 2019/0156689 A1 — systems and methods for online '
     'proctoring (ProctorU)', '2019 / patent application',
     'Webcam, microphone, keyboard and screen monitoring of a remote '
     'candidate; a rule combining loss of the candidate face for a threshold '
     'period, subsequent keyboard or mouse input, and subsequent submission, '
     'flags the session; the session may be suspended in software.',
     'The closest single-candidate reference on temporal rule-based '
     'detection, and is conceded as such. The anchor is the candidate’s own '
     'face-loss rather than any measured quantity independent of the '
     'candidate; there is no station-to-station relation, no venue-wide '
     'component to remove, no instrumented unoccupied position, and the '
     'response is a software session action rather than a change in the '
     'physical acquisition state of any transducer.'),
    ('9', 'Atoum, Chen, Liu, Hsu and Liu — automated online exam '
     'proctoring, IEEE Transactions on Multimedia, 19(7), 1609-1624',
     '2017 / journal',
     'Multimodal proctoring using a webcam, a worn camera and a microphone; '
     'audio and visual cues combined; evaluated on twenty-four subjects '
     'performing staged cheating types.',
     'The closest multimodal reference. Trained and evaluated on staged, '
     'labelled cheating; detection is bounded by the cheat types enacted for '
     'the corpus. Single-candidate; the microphone is used for speech and '
     'ambient cues, not for near-ultrasonic emitter signatures.'),
    ('10', 'Wollack — a nominal response model approach for detecting '
     'answer copying, Applied Psychological Measurement', '1997 / journal',
     'Item-response-theory statistic comparing a candidate response vector '
     'against a putative source, with controlled Type I error.',
     'Operates on completed answer sheets after the examination. Detects the '
     'statistical trace of copying, not the act; yields no intervention '
     'during the session and no evidence of device use.'),
    ('11', 'Belov and Wollack — graph theory approach to detect '
     'examinees involved in test collusion, Applied Psychological Measurement',
     '2021 / journal',
     'Response-similarity indices computed over examinee pairs are assembled '
     'into a graph, and connected components, cliques or near-cliques '
     'identify collusion groups.',
     'The graph construction and connected-component step is closely '
     'analogous to the dependent graph claim of the present disclosure and is '
     'acknowledged as such. It is nevertheless computed on post-hoc '
     'answer-response similarity between examinees, whereas the present '
     'invention computes it on live, time-lagged coupling between physical '
     'sensor residuals at spatially fixed stations, referenced against that '
     'same pair’s own sanctioned-activity baseline, and issues alerts during '
     'the session.'),
    ('12', 'Malhotra, Ramakrishnan, Anand, Vig, Agarwal and Shroff — '
     'LSTM-based encoder-decoder for multi-sensor anomaly detection',
     '2016 / conference',
     'A recurrent encoder-decoder trained on normal multi-sensor sequences; '
     'reconstruction error over the sequence is used as the anomaly score.',
     'General technique. No per-venue, per-station calibration under '
     'non-stationary ambient conditions, no fusion across heterogeneous '
     'physical modalities for this purpose, and no correlation of residuals '
     'across spatially separate instances.'),
    ('13', 'Hundman, Constantinou, Laporte, Colwell and Soderstrom — '
     'detecting spacecraft anomalies using LSTMs and nonparametric dynamic '
     'thresholding, KDD', '2018 / conference',
     'Prediction error from a recurrent predictor trained on normal '
     'telemetry, with an unsupervised dynamic threshold and pruning of false '
     'positives.',
     'Establishes prediction-error anomaly detection with unsupervised '
     'thresholding in a single-channel telemetry setting. Contains no '
     'teaching of multi-station deployment and none of a relational quantity '
     'between deployed instances.'),
    ('14', 'Zong, Song, Min, Cheng, Lumezanu, Cho and Chen — deep '
     'autoencoding Gaussian mixture model for unsupervised anomaly detection, '
     'ICLR', '2018 / conference',
     'Joint learning of a compressed representation and a density estimate '
     'over reconstruction features, giving an unsupervised anomaly score.',
     'Density-based rather than predictive, and single-instance. Provides no '
     'mechanism by which scores from separate deployed instances would be '
     'related to one another.'),
    ('15', 'Bardes, Ponce and LeCun — VICReg: variance-invariance-'
     'covariance regularization for self-supervised learning, ICLR',
     '2022 / conference',
     'Variance and covariance terms applied to embeddings prevent '
     'representational collapse in joint-embedding training without negative '
     'pairs.',
     'A training regulariser evaluated by downstream classification quality. '
     'Contains no teaching of using the prediction residual itself as a live '
     'detection score.'),
    ('16', 'Assran, Duval, Misra, Bojanowski, Vincent, Rabbat, LeCun and '
     'Ballas — self-supervised learning from images with a '
     'joint-embedding predictive architecture, CVPR', '2023 / conference',
     'Prediction of the embedding of masked target regions from a context '
     'region, without pixel-level reconstruction.',
     'Representation-learning method for images. The residual is a training '
     'signal, not an output; no distributed sensing deployment and no '
     'cross-instance comparison.'),
    ('17', 'LeCun — a path towards autonomous machine intelligence',
     '2022 / position paper',
     'Programmatic argument for joint-embedding predictive architectures as a '
     'basis for world models.',
     'Architectural proposal. Neither an assessment-integrity system nor a '
     'teaching of residual-based detection under per-station label-free '
     'calibration.'),
    ('18', 'Deng and Hooi — graph neural network-based anomaly detection '
     'in multivariate time series, AAAI 35(5), 4027-4035',
     '2021 / conference',
     'Learns a graph over the channels of a sensor installation from the data '
     'itself, connecting each sensor to those whose behaviour best predicts '
     'it. A forecast is made for every channel from its learned neighbours '
     'and the deviation from observation is the anomaly score; attention '
     'weights permit root-cause attribution.',
     'Discloses learned inter-channel structure, a prediction-deviation '
     'score, and per-channel attribution. The nodes are channels of one '
     'instrumented process, in which correlation between nodes is the normal '
     'and expected structure and an anomaly is a departure from it. The '
     'present invention inverts that premise. It does not disclose a coupling '
     'statistic between nodes whose predictive models are established '
     'separately at each node; nor estimation and subtraction of a venue-wide '
     'component before pairwise coupling is evaluated; nor an instrumented '
     'node held unoccupied to supply that reference.'),
    ('19', 'Zheng, Koh, Jin, Chi and others — correlation-aware '
     'spatial-temporal graph learning for multivariate time-series anomaly '
     'detection, IEEE TNNLS (arXiv:2307.08390)', '2023 / journal',
     'A correlation-learning module infers pairwise correlations between '
     'series, over which a spatial-temporal graph network is built; detection '
     'is evaluated at a configurable set of temporal delays, so a disturbance '
     'propagating between nodes can be caught at non-zero lag.',
     'The closest reference to the cross-station embodiment and acknowledged '
     'as such. Pairwise correlation learning between separately sensed series '
     'at configured non-zero delays is conceded to correspond to the '
     'time-lagged coupling step taken by itself. What is not disclosed is the '
     'arrangement that makes it meaningful: nodes that are independently '
     'occupied stations for which mutual coupling has no legitimate cause; '
     'estimation and removal of a venue-wide common component; an unoccupied '
     'instrumented node supplying part of that reference; a per-pair '
     'sanctioned-activity baseline against which coupling is judged; and a '
     'bound on inter-node timing tolerance relative to the shortest evaluated '
     'lag.'),
    ('20', 'Common-mode suppression across sensor arrays — '
     'representative: Rost and Thomas, array seismology, Reviews of '
     'Geophysics 40(3), doi 10.1029/2000RG000100; with common-average '
     'referencing in multichannel electroencephalography and common-mode '
     'rejection in differential instrumentation amplifiers',
     '2002 and earlier / review and general practice',
     'Where several like sensors observe a shared environment, a component '
     'common to all channels is estimated — by summation and '
     'beam-forming across the array, by referencing each channel to the '
     'average of all channels, or by differential measurement — and '
     'suppressed, so that the component peculiar to one channel can be '
     'resolved above it.',
     'Cited by the applicant, not against it. Common-mode suppression as a '
     'technique is conceded to be ordinary and no protection is sought for it '
     'as such. In the cited practice the array observes one field and the '
     'common component is instrument or environmental noise on a physical '
     'measurement. Here the quantity referenced across the array is the '
     'prediction residual of a model established separately at each station, '
     'the reference is formed across stations otherwise modelled '
     'independently, one of which is held unoccupied for the purpose, and the '
     'step is a precondition for a relational quantity that exists at no '
     'single station rather than an improvement to a single-station '
     'estimate.'),
    ('21', 'Tuli, Casale and Jennings — TranAD: deep transformer '
     'networks for anomaly detection in multivariate time series data, '
     'Proceedings of the VLDB Endowment 15(6)', '2022 / conference',
     'A transformer encoder-decoder trained on normal multivariate sequences, '
     'with self-conditioning on a first-pass reconstruction and an '
     'adversarial second stage that amplifies small deviations.',
     'Included so that the general prediction-error art is represented at its '
     'current state rather than at its 2018 state. Single-instance in the '
     'same sense as entries 12 to 14: no per-station calibration under '
     'non-stationary ambient conditions, no fusion across heterogeneous '
     'physical modalities, and no teaching of a relational quantity computed '
     'between separately deployed instances. The present invention is '
     'deliberately agnostic to which such predictor is used; the contribution '
     'claimed lies in the arrangement around it.'),
]


def sec3(doc):
    h1(doc, '3. Prior Patents and Publications from Literature')
    para(doc,
         'The table below summarises the closest known prior art and '
         'identifies the gap addressed by the present invention. Entries 1 to '
         '9 are assessment-integrity systems. Entries 10 and 11 are the '
         'psychometric-forensics literature on collusion, which is the only '
         'prior art in that field addressing coordination between candidates. '
         'Entries 12 to 17 and 21 are general-purpose machine-learning '
         'techniques that an examiner may reasonably combine. Entries 18 to '
         '20 are the art closest to the relational step claimed here, and '
         'each of the three is treated at length because an examiner will '
         'otherwise supply them.')
    table(doc,
          ['No.', 'Reference', 'Year / type', 'Core contribution',
           'Limitation with respect to the present invention'],
          [list(r) for r in PRIOR_ROWS],
          cap='Table 1: Prior Art Considered and the Gap Addressed',
          widths=[0.30, 1.50, 0.70, 1.90, 2.30], size=7.6,
          align_left_cols=(1, 3, 4))

    para(doc,
         'The search covered patent literature through Google Patents and '
         'Espacenet, and the peer-reviewed literature in educational '
         'measurement, multimedia analytics and machine learning. The common '
         'limitation across the supervised approaches at entries 1, 3, 6, 8 '
         'and 9 is a dependence on labelled malpractice data. Genuine '
         'cheating is rare, adversarial, and deliberately concealed, so a '
         'representative labelled corpus of malpractice cannot be assembled '
         'in practice. A detector trained on such data recognises the '
         'specific cheating methods that were staged and labelled and does '
         'not generalise to novel methods.')
    para(doc,
         'The general techniques at entries 12 to 17 and 21 supply components '
         'but not the invention. Prediction-error anomaly detection is known '
         'in the abstract. What is not known, and what is claimed here, is '
         'its application as a per-station integrity score under per-station, '
         'per-session label-free calibration, fused across heterogeneous '
         'physical sensing modalities, and used as the input to a relational '
         'quantity computed between stations. Entries 10 and 11 warrant '
         'separate treatment because they address collusion directly and are '
         'the only assessment-domain prior art that does. Both belong to '
         'psychometric forensics: they infer collusion from similarity '
         'between completed answer vectors after the examination has ended. '
         'That approach detects a statistical trace of copying rather than '
         'the conduct producing it, cannot distinguish copying from shared '
         'preparation or a leaked paper, yields nothing about device use, '
         'and by construction permits no intervention while the examination '
         'is running.')
    para(doc,
         'Entries 18 and 19 require the closest attention, because they are '
         'the only located art that derives a relational quantity between '
         'separately sensed streams. Both learn a structure over nodes and '
         'score deviation from it, and entry 19 evaluates correlation at '
         'configured non-zero delays. The correspondence is conceded rather '
         'than minimised. The distinction is one of premise. In both '
         'references the nodes are channels of a single instrumented process, '
         'mutual correlation between them is the normal structure the model '
         'is built to learn, and an anomaly is a departure from that learned '
         'correlation. In the present invention the nodes are separately '
         'occupied stations at which sanctioned activity gives rise to no '
         'mutual coupling whatever, so that a coupling which persists after '
         'the venue-wide component has been removed is not a departure from '
         'the model but the detection itself. That inversion is what makes '
         'the remaining elements necessary rather than optional: predictive '
         'models established separately at each station, because a single '
         'model shared across the stations injects its own error into every '
         'stream and manufactures coupling where none exists; an estimate of '
         'the component common to the whole venue, because stations share a '
         'room and the most frequent cause of simultaneous residual elevation '
         'is an event common to it; an instrumented station held unoccupied, '
         'because that estimate needs a reference carrying no candidate; a '
         'baseline measured on each station pair during sanctioned activity, '
         'because the fixed geometry of a room produces a standing coupling '
         'that is not coordination; and a bound on inter-station timing '
         'tolerance, because a lag of one to three seconds cannot be resolved '
         'by clocks disagreeing by more than a fraction of it. None of '
         'entries 1 to 21 discloses any of those five, alone or in '
         'combination.')


def sec4(doc):
    h1(doc, '4. Summary and Background of the Invention (Gap / Novelty)')
    para(doc,
         'Examination malpractice has grown more sophisticated with the '
         'miniaturisation of electronics. Concealed micro-earpieces, '
         'smartwatches, and short-range wireless accessories are difficult to '
         'detect by inspection, and supervised detection systems face a '
         'data problem that cannot be solved by collecting more data: there '
         'is no large, representative, labelled corpus of cheating, and there '
         'will not be one, because cheating is rare and actively hidden. Any '
         'system trained to recognise cheating from labelled examples is '
         'confined to the behaviours it was shown.')
    para(doc,
         'The present invention removes that dependence. Each station is '
         'modelled from recordings of sanctioned activity, which are abundant '
         'and require no labelling. A predictive model learns to anticipate '
         'the near-future state of that station signal streams from their '
         'recent past. During a monitored session, the error between the '
         'prediction and the observation — the prediction residual '
         '— serves as the integrity-violation score. Because the model '
         'has only ever been shown sanctioned activity, activity unlike it, '
         'including methods never anticipated, produces an elevated residual. '
         'The impossible task of collecting every kind of violation is thus '
         'replaced by the routine one of observing ordinary behaviour.')
    figure(doc, 'fig01.png',
           'Figure 1. The data problem and its removal. The supervised prior '
           'art depends on an annotation step that cannot be performed at '
           'scale, because genuine malpractice is rare, adversarial and '
           'concealed; the present invention removes that step by '
           'construction, modelling sanctioned activity alone and scoring '
           'deviation from it.', width=6.1)
    para(doc,
         'Removing the labels is the precondition of the invention rather '
         'than its substance. What is claimed is the arrangement built on '
         'top of it. An installation comprises a plurality of candidate '
         'stations, each carrying its own sensing assembly and its own '
         'predictive model and calibration statistics; at least one station '
         'of like construction deliberately held unoccupied; a '
         'time-synchronisation arrangement holding all of them to a common '
         'time base within a bounded tolerance; and a processing arrangement '
         'that estimates the residual component common to the venue, removes '
         'it, and then evaluates a time-lagged coupling statistic between '
         'pairs of candidate stations against a baseline measured on that '
         'same pair during sanctioned activity. Coupling that survives all '
         'of those steps is the detection. On satisfying the coordination '
         'condition the installation re-tasks the sensing assemblies of the '
         'implicated pair alone, for a bounded interval, into a second '
         'acquisition state.')

    h2(doc, '4.1 Statement of Inventive Step (Non-Obviousness)')
    para(doc,
         'The inventive step does not reside in any single element taken '
         'alone. Anomaly detection by prediction error is known in other '
         'fields, as is self-supervised predictive representation learning, '
         'and the suppression of a component common to an array of like '
         'sensors is ordinary instrumentation practice. The invention '
         'resides in the combination of the following seven elements, and in '
         'technical effects that no element produces on its own:')
    bullets(doc, [
        ('(a)', 'a predictive model trained exclusively on sanctioned '
         'activity, so that the training corpus is abundant and the detector '
         'responds to violation methods never anticipated at design time;'),
        ('(b)', 'use of the prediction residual directly as a live integrity '
         'score, rather than as an auxiliary training signal for a downstream '
         'classifier;'),
        ('(c)', 'establishment of that model and of the statistics against '
         'which its residual is standardised separately at each station, from '
         'an interval of sanctioned activity at that same station, which '
         'calibrates the detector to local ambient conditions without any '
         'labelled data;'),
        ('(d)', 'fusion of residuals across heterogeneous physical sensing '
         'modalities, so that violation methods manifesting in different '
         'channels are covered by one score;'),
        ('(e)', 'time-lagged correlation of residual time-series between '
         'spatially proximate stations, the residual time-series of each '
         'station being generated by a model established at that station;'),
        ('(f)', 'suppression of a venue-wide common-mode residual component '
         'prior to that correlation, derived from a robust central statistic '
         'across the stations, from at least one instrumented but unoccupied '
         'reference station, or from both, so that the coordination condition '
         'responds only to coupling specific to a station pair; and'),
        ('(g)', 'maintenance of timing alignment between the residual '
         'time-series of different stations within a tolerance bounded by the '
         'shortest lag at which the correlation is evaluated, without which a '
         'pair coupling and a venue-wide event are not separable.'),
    ])
    para(doc,
         'Estimating and subtracting a component common to an array of like '
         'sensors is, as element (f) is drafted, ordinary instrumentation '
         'practice, and it is not claimed as such. Entry 20 of Section 3 sets '
         'out that practice in seismic array processing, in common-average '
         'referencing across electroencephalographic channels, and in the '
         'common-mode rejection of differential instrumentation amplifiers. '
         'What is claimed is its application to the prediction residual of a '
         'model established separately at each station rather than to a '
         'physical measurement, its formation in part from a station '
         'deliberately held unoccupied, and its use as a precondition for a '
         'relational quantity between stations rather than as an improvement '
         'to a single-station one.')
    para(doc,
         'The synergy is specifically this. Element (e) is available only in '
         'combination with element (f), and is defeated rather than assisted '
         'by the arrangement a skilled person would be expected to adopt. '
         'Collusion is a relational phenomenon; every prior system listed at '
         'entries 1 to 9 of Section 3 scores candidates in isolation and is '
         'structurally incapable of observing it, while entries 10 and 11 '
         'observe it only after the event and from the answers rather than '
         'from the conduct. A coupling computed between station residual '
         'streams is a channel that exists at no single station. That channel '
         'is not, however, available merely by computing it. Stations in a '
         'venue share an environment, so the most frequent cause of '
         'simultaneous residual elevation at neighbouring stations is not '
         'coordination but an event common to the room. Measured on eleven '
         'independently instrumented stations, a venue-wide event raises the '
         'mean pairwise coupling across all fifty-five station pairs from '
         '%.3f to %.3f, and a genuinely coupled pair — although it then '
         'carries the highest raw coupling in the venue — is identified '
         'first out of fifty-five in only one trial in ten, because the '
         'venue-wide event lifts every pair with it. Estimating and '
         'subtracting the component common to the venue restores that '
         'identification to six trials in ten and raises the ranking accuracy '
         'from %.3f to %.3f. Element (f) is a precondition of the validity of '
         'element (e), not an optimisation of it.'
         % (CPL['common_mode_suppression']['per_station|raw_median']
            ['floor_no_injection_mean_r'],
            CPL['common_mode_suppression']['per_station|raw_median']
            ['with_event_no_rejection_mean_r'],
            REP['summary']['D_both|per_station|none']['auroc_over_pairs_mean'],
            REP['summary']['D_both|per_station|raw_median']
            ['auroc_over_pairs_mean']))
    para(doc,
         'A second and less expected condition governs the same channel, and '
         'it is the reason element (c) is drafted as it is. The residual '
         'streams to be correlated must be generated by predictive models '
         'established separately at each station. Applying one model in '
         'common across the stations, which is the arrangement a person '
         'skilled in the art would naturally adopt for economy and for '
         'uniformity of scale, introduces into every stream the error '
         'peculiar to that one model, and that error is shared across the '
         'stations by construction. It appears as coupling at every station '
         'pair and cannot be removed by a reference formed from the same '
         'stations, because it is itself part of what that reference '
         'measures. The effect is not marginal. With no coordinated activity '
         'present at all, forming the reference across stations scored by a '
         'common model raises mean pairwise coupling from %.3f to %.3f, and '
         'the coupled pair is identified in none of twenty trials at any '
         'setting tested, the ranking accuracy remaining between %.3f and '
         '%.3f — that is, indistinguishable from chance. Station-local '
         'models under the same conditions reach %.3f. The arrangement '
         'claimed departs from the expedient a skilled person would adopt, '
         'and the departure is what makes the channel work.'
         % (CPL['common_mode_suppression']['shared|raw_median']
            ['floor_no_injection_mean_r'],
            CPL['common_mode_suppression']['shared|raw_median']
            ['with_event_after_rejection_mean_r'],
            min(REP['summary']['D_both|shared|%s' % r]
                ['auroc_over_pairs_mean']
                for r in ('none', 'raw_median', 'standardised_median')),
            max(REP['summary']['D_both|shared|%s' % r]
                ['auroc_over_pairs_mean']
                for r in ('none', 'raw_median', 'standardised_median')),
            REP['summary']['D_both|per_station|raw_median']
            ['auroc_over_pairs_mean']))
    para(doc,
         'Element (g) is not asserted. Measured on a coupling lag of two '
         'reporting intervals, ranking accuracy holds at %.3f, %.3f and %.3f '
         'for inter-station timing errors of zero, one half and one times '
         'that lag, falls to %.3f at one and a half times, and to %.3f at '
         'four times; identification of the coupled pair falls over the same '
         'range from %.2f to %.2f. The tolerance recited in the claims is '
         'therefore expressed as a fraction of the shortest evaluated lag '
         'rather than as an absolute interval, which makes it independent of '
         'the station reporting rate.'
         % (REP['skew_sweep']['0']['auroc_over_pairs_mean'],
            REP['skew_sweep']['1']['auroc_over_pairs_mean'],
            REP['skew_sweep']['2']['auroc_over_pairs_mean'],
            REP['skew_sweep']['3']['auroc_over_pairs_mean'],
            REP['skew_sweep']['8']['auroc_over_pairs_mean'],
            REP['skew_sweep']['0']['detection_rate_top_ranked'],
            REP['skew_sweep']['8']['detection_rate_top_ranked']))
    para(doc,
         'A further effect follows from the same architecture and is '
         'independent of the analytical content of the model. Detection '
         'operates on residuals derived from a band-limited envelope rather '
         'than on raw recordings, so the quantity leaving a station is a '
         'small number of order statistics per window from which the acoustic '
         'waveform cannot be recovered, and the volume of data leaving the '
         'venue is reduced by orders of magnitude against a video- or '
         'audio-recording installation. A last effect is a change in the '
         'physical operating state of apparatus: upon the coordination '
         'condition being satisfied, the sensing assemblies of the two '
         'implicated stations, and of no others, are switched into a second '
         'acquisition state for a bounded interval, so that the installation '
         'runs in its low-rate, low-selectivity state by default and acquires '
         'more only where a measured relation between two physically separate '
         'transducer sets has indicated it.')


def sec5(doc):
    h1(doc, '5. Objectives of the Invention')
    bullets(doc, [
        ('1.', 'To detect malpractice at station level without requiring any '
         'labelled example of cheating for training.'),
        ('2.', 'To detect unauthorised communication devices and covert '
         'activity through their physical signatures across one or more '
         'sensing modalities, the invention being indifferent to the '
         'particular modality employed.'),
        ('3.', 'To respond to violation methods that were not anticipated '
         'when the system was built.'),
        ('4.', 'To reduce false alarms by fusing multiple sensing modalities '
         'and by requiring corroborating evidence.'),
        ('5.', 'To distinguish coordinated malpractice between candidates '
         'from coincidental anomaly, by a time-lagged coupling between '
         'station residual streams that exists at no single station.'),
        ('6.', 'To prevent an event common to the venue from being reported '
         'as coordination, by estimating that component from the stations '
         'themselves together with at least one instrumented station held '
         'unoccupied, and removing it before any coupling is evaluated.'),
        ('7.', 'To calibrate automatically to the ambient conditions of each '
         'station and each session without labelled data, and to judge '
         'coupling against a baseline measured on that same station pair '
         'while activity was sanctioned.'),
        ('8.', 'To operate without retaining raw audio, video, or radio '
         'recordings beyond the point of feature extraction, and to emit from '
         'each station a representation from which the acoustic waveform '
         'cannot be reconstructed.'),
        ('9.', 'To bring about a physical change in the acquisition state of '
         'the implicated stations alone, bounded in time, rather than a '
         'notification only.'),
        ('10.', 'To state an honest, quantified operating envelope naming the '
         'conditions under which detection is reliable and those under which '
         'it is not.'),
    ])


def sec6(doc):
    h1(doc, '6. Working Principle (in Brief)')
    para(doc,
         'Each monitored station carries a sensing assembly whose transducers '
         'continuously produce one or more signal streams, digitised at the '
         'station and processed either by an edge processing unit there or by '
         'a venue-local aggregator receiving the derived features. In the '
         'principal embodiment these are acoustic, including near-ultrasonic '
         'energy; electromagnetic, comprising radio-frequency emissions, '
         'device-advertisement activity and signal-strength dynamics; and, '
         'where a camera is present, behavioural. The streams are divided '
         'into short overlapping windows. An encoder trained only on '
         'sanctioned sessions at that station embeds the recent window and a '
         'predictor estimates the near-future change in the signal. The '
         'squared error between predicted and observed change is the '
         'per-modality residual, standardised against statistics gathered at '
         'that station during an initial sanctioned interval of the session '
         'and combined across modalities into one integrity-violation score. '
         'A score exceeding the alert condition is logged and reported with '
         'station identifier, timestamp and severity.')
    para(doc,
         'The relational step follows. At each sampling instant the '
         'processing arrangement forms, across the residual streams of the '
         'stations of the venue and of at least one station held unoccupied, '
         'a robust central statistic representing the residual variation '
         'common to the room, and subtracts it from every station stream. A '
         'time-lagged coupling statistic is then evaluated between the '
         'corrected streams of pairs of stations, over lags no shorter than '
         'twice the tolerance to which the station clocks are aligned. That '
         'statistic is compared not against a fixed threshold but against a '
         'baseline value measured on the same pair earlier in the session, '
         'while activity was sanctioned, so that the standing coupling '
         'produced by the fixed geometry of the room is removed from the '
         'decision. Coordination is indicated when the excess over that '
         'baseline recurs on each of a predetermined number of separate '
         'occasions; an elevated residual at one station that couples with '
         'nothing is reported as an isolated individual anomaly. On '
         'coordination being indicated, the sensing assemblies of the two '
         'implicated stations alone are switched into a second acquisition '
         'state for a bounded interval.')
    figure(doc, 'fig02.png',
           'Figure 2. System architecture. Each candidate station (100) '
           'carries a sensing assembly (10) and its own encoder, predictor '
           'and standardisation statistics (20, 22); residual scoring (30) '
           'and fusion (40) yield one stream per station; the cross-station '
           'coupling unit (50) removes the venue-common component (52), '
           'evaluates lagged coupling (54) against the pair’s own baseline '
           '(56), and applies the coordination condition (58); the outputs '
           'are the ranking interface (60) and the acquisition-state '
           'controller (80).')


NUMERALS = [
    ('10', 'sensing assembly of a station'),
    ('12', 'acoustic transducer, audible and near-ultrasonic'),
    ('14', 'electromagnetic sensor'),
    ('16', 'further-modality transducer'),
    ('18', 'optical behavioural module'),
    ('20', 'station-local encoder and predictor'),
    ('22', 'station-local standardisation statistics'),
    ('24', 'acoustic analogue front end: band-pass, rectifier, low-pass'),
    ('30', 'residual scoring unit'),
    ('40', 'multi-modal fusion unit'),
    ('50', 'cross-station coupling unit'),
    ('52', 'common-mode estimator'),
    ('54', 'lagged coupling comparator'),
    ('56', 'pair baseline store'),
    ('58', 'coordination comparator'),
    ('60', 'alert and ranking interface'),
    ('70', 'time-synchronisation arrangement'),
    ('80', 'acquisition-state controller'),
    ('82', 'first acquisition state'),
    ('84', 'second acquisition state'),
    ('90', 'reference station, held unoccupied'),
    ('100', 'candidate station body'),
]


def sec7(doc):
    h1(doc, '7. Detailed Description of the Invention')
    para(doc,
         'Reference numerals used throughout the description and the figures '
         'are indexed below. They identify the parts of one embodiment and '
         'are not limitations upon the claims.', )
    half = (len(NUMERALS) + 1) // 2
    rows = []
    for i in range(half):
        a = NUMERALS[i]
        b = NUMERALS[i + half] if i + half < len(NUMERALS) else ('', '')
        rows.append([a[0], a[1], b[0], b[1]])
    table(doc, ['No.', 'Part', 'No.', 'Part'], rows,
          cap='Table 2: Index of Reference Numerals',
          widths=[0.5, 2.85, 0.5, 2.85], size=8.6, align_left_cols=(1, 3))

    para(doc,
         'In the principal embodiment the acoustic transducer (12) captures '
         'sound across a wide band including the near-ultrasonic frequencies '
         'used by some covert audio links, and the electromagnetic sensor '
         '(14) monitors bands associated with consumer devices, capturing '
         'radio emissions, device-advertisement rates and received-'
         'signal-strength behaviour. An optional module (18) derives gaze, '
         'blink, head-pose and fixation features from a camera. Further '
         'transducers (16) of other physical modalities may be substituted or '
         'added; the invention is not restricted to any of them, for the '
         'reasons set out at Section 7.1. In a representative embodiment the '
         'derived features of all modalities are reported at a common low '
         'frame rate and grouped into overlapping context windows of '
         'approximately seven seconds.',
         lead='Sensing.')
    para(doc,
         'The output of the acoustic transducer is not digitised as a '
         'waveform. An analogue front end (24) band-passes it to the voice '
         'and near-ultrasonic bands of interest, rectifies it, and low-pass '
         'filters the result, so that what is digitised is the envelope. From '
         'each reporting window only order statistics of that envelope are '
         'retained, in a representative embodiment its peak and its '
         'root-mean-square. Two consequences follow, and the second is the '
         'important one. The data rate leaving the station falls by three '
         'orders of magnitude against waveform capture. And the retained '
         'representation cannot be inverted: the envelope stage discards '
         'phase, and a peak and a root-mean-square are order statistics over '
         'the whole window, so the mapping from waveform to retained '
         'representation is many-to-one and no inverse exists. That is a '
         'property of the signal chain rather than a policy undertaking, and '
         'it holds at any sampling rate.',
         lead='Non-reconstructability of the acoustic representation.')
    para(doc,
         'A separate lightweight encoder is provided for each modality at '
         'each station. From a context window the encoder produces a compact '
         'embedding, and a predictor estimates the change in the signal over '
         'a short future horizon. Training minimises the error of that '
         'prediction on sanctioned sessions alone, while a variance-and-'
         'covariance regularisation on the embedding prevents the degenerate '
         'solution in which the encoder maps every input to the same point. '
         'No labelled malpractice is used at any stage. The parameters of the '
         'model (20) and the statistics (22) against which its residual is '
         'standardised are established at the station whose signals they '
         'serve, and are not transferred between stations. Section 8 sets out '
         'the measurement that requires this: a model shared across stations '
         'is worse at every commensurability metric tested and destroys the '
         'relational channel entirely.',
         lead='Model, established station by station.')
    para(doc,
         'At inference the prediction error for each modality is the anomaly '
         'score. Scores are standardised using statistics gathered from '
         'sanctioned calibration data at that station only, then combined '
         'across modalities. Fusing modalities is beneficial because '
         'different violation methods manifest in different channels. The '
         'residual may in addition be aggregated by a causal rolling '
         'statistic over a longer span within the session, which raises '
         'sensitivity to faint but sustained activity and uses no future '
         'information.',
         lead='Scoring and fusion.')
    figure(doc, 'fig03.png',
           'Figure 3. Working principle at one station. The encoder embeds '
           'the recent context window and the predictor estimates the '
           'near-future change; the discrepancy against the observed change '
           'is the residual (30), which serves as the integrity-violation '
           'score.', width=6.0)
    para(doc,
         'A single station cannot distinguish an individual brief anomaly '
         'from coordinated activity. The processing arrangement therefore '
         'compares the residual time-series of proximate stations. Collusion '
         'couples two stations in time — one candidate signals, the '
         'other responds after a short lag — producing residual '
         'elevations that are correlated at that lag. An isolated anomaly '
         'correlates with nothing. A lagged cross-correlation of proximate-'
         'station residuals, evaluated per modality and combined, therefore '
         'separates coordination from coincidence, and the quantity so '
         'obtained is absent from any single-station analysis.',
         lead='Cross-station coupling.')
    para(doc,
         'Stations within a venue share an environment, so residual '
         'elevations arise simultaneously at proximate stations for reasons '
         'unrelated to coordination: an invigilator passing between desks, a '
         'door opening, a dropped object, a public-address announcement, a '
         'venue-wide radio disturbance. Such common-mode events satisfy a '
         'naive coordination condition and are the principal source of false '
         'coordination alarms. The processing arrangement estimates, at each '
         'sampling instant, a component representing residual variation '
         'shared across the stations, and subtracts it from each station '
         'residual before any coupling statistic is computed. The estimate is '
         'formed as a robust central statistic across the stations — in '
         'the best-performing embodiment tested, the plain median at each '
         'instant — and includes the residual of at least one station '
         '(90) instrumented in like manner and held unoccupied throughout the '
         'session. The unoccupied station is not a refinement. A reference '
         'formed only from occupied stations carries whatever the candidates '
         'at those stations are doing; a station carrying no candidate '
         'observes the room and nothing else, which is precisely the quantity '
         'to be removed.',
         lead='Common-mode rejection and the unoccupied reference station.')
    figure(doc, 'fig04.png',
           'Figure 4. Venue installation. Candidate stations (100) and at '
           'least one like-instrumented reference station (90) held '
           'unoccupied share a common time base (70) to within a tolerance T; '
           'a venue-wide event reaches every station at once and is removed '
           'by the common-mode estimator, while the coupling of one pair at a '
           'lag survives it and an isolated anomaly couples with nothing.')
    para(doc,
         'A coupling statistic evaluated against a fixed threshold would '
         'report the standing coupling produced by the fixed geometry of the '
         'room — two adjacent desks share a wall, a light fitting and a '
         'draught, and their residuals are not independent even when both '
         'candidates behave. For each pair of stations the processing '
         'arrangement therefore measures, during an interval of the session '
         'in which activity is sanctioned, a baseline value of the same '
         'coupling statistic computed on the same corrected residual streams '
         'of the same pair. Coordination is indicated only when the coupling '
         'later exceeds that pair’s own baseline by a predetermined margin. '
         'Each pair is thus its own control, which removes seating distance, '
         'room geometry and any fixed shared exposure from the decision '
         'without any labelled datum. The condition is further required to be '
         'satisfied on each of at least a predetermined number of separate '
         'occasions within the session, because the coupling statistic is a '
         'correlation estimate and a single exchange does not move it: '
         'measurement reported at Section 8 puts the usable range at about '
         'twenty separate exchanges and upward.',
         lead='The inverted null: each pair is its own control.')
    para(doc,
         'The lag to be resolved is short. Clock disagreement between '
         'stations both smears a genuine coupling and manufactures a spurious '
         'one, so a time-synchronisation arrangement (70) holds the streams '
         'to a common time base within a predetermined tolerance, and the set '
         'of lags at which coupling is evaluated is bounded below at twice '
         'that tolerance. Expressed as a fraction of the coupling lag the '
         'requirement is independent of the reporting rate: measurement '
         'reported at Section 8 shows ranking accuracy above 0.95 while the '
         'timing error remains within about one and a half times the shortest '
         'evaluated lag, and collapse beyond three times it. For a coupling '
         'lag of one to three seconds that admits network time '
         'synchronisation over the venue local area network and requires no '
         'pulse-per-second distribution.',
         lead='Timing.')
    para(doc,
         'Ambient acoustic and electromagnetic conditions differ between '
         'halls, between rooms of a hall and between mornings and afternoons. '
         'The statistics used for standardisation are therefore established '
         'from an initial interval of each session, at each station, and '
         'then held fixed for the remainder of that session, or re-established '
         'at intervals where the ambient conditions are known to drift. No '
         'labelled data is required, which is what makes the calibration '
         'deployable at scale.',
         lead='Per-station, per-session calibration.')
    para(doc,
         'Every claim of this disclosure that ends in a notification is a '
         'weaker claim than one that ends in a physical act, and the '
         'installation accordingly acts. Each sensing assembly is operable in '
         'a first acquisition state (82) and a second acquisition state (84), '
         'the two differing in at least one of sampling rate, the number of '
         'transducers enabled, and the directional selectivity of '
         'acquisition. The installation runs in the first state throughout. '
         'On the coordination condition being satisfied in respect of a pair, '
         'the acquisition-state controller (80) switches the sensing '
         'assemblies of the two implicated stations, and of no other station, '
         'into the second state for a bounded interval, after which they '
         'revert unless the condition is satisfied again. The response is '
         'deliberately confined to gathering better evidence on the '
         'implicated pair. Confining it to that pair and bounding it in time '
         'is also the privacy answer: the venue is monitored at the lower '
         'rate by default, and closer acquisition is applied only where a '
         'measured relation between two physically separate transducer sets '
         'has warranted it.',
         lead='Graduated physical response.')

    h2(doc, '7.1 Alternative Embodiments')
    para(doc,
         'The following alternatives are contemplated and are to be read as '
         'within the scope of the invention. They are recited so that the '
         'disclosure supports claim language broader than the principal '
         'embodiment.')
    bullets(doc, [
        ('(a) Sensing modalities.', 'The sensing assembly may comprise any '
         'one or more of: acoustic sensing including near-ultrasonic bands; '
         'electromagnetic and radio-frequency sensing including '
         'device-advertisement capture and received-signal-strength dynamics; '
         'mechanical vibration or accelerometric sensing of the desk or seat '
         'surface; magnetic-field sensing; pressure, strain, or load sensing '
         'in the seat or writing surface; thermal or infrared sensing; '
         'millimetre-wave or radar-based micro-motion sensing; capacitive '
         'proximity sensing; and optical sensing of candidate behaviour. The '
         'method is indifferent to which physical quantity is sensed, because '
         'the detector learns the temporal predictability of whatever stream '
         'it is given.'),
        ('(b) Physical form factor.', 'The sensing assembly may be embedded '
         'within a purpose-built desk body; provided as a retrofit sensing '
         'pod clamped or adhered to an existing desk; integrated into a '
         'partition, seat back, or candidate device holder; or mounted '
         'overhead on a per-station basis. Retrofit embodiments are '
         'commercially significant because they do not require replacement of '
         'existing furniture. The reference station is of like construction '
         'in every case.'),
        ('(c) The reference station.', 'One reference station per hall '
         'suffices in a small room. Two or more at spaced positions are '
         'contemplated where the venue is large enough that a disturbance '
         'does not reach all stations equally, in which case the reference '
         'applied to a candidate station may be formed with greater weight on '
         'the nearer reference. A reference station may alternatively be a '
         'candidate station recorded as unoccupied for that session by the '
         'seating plan, at the cost of relying on that record.'),
        ('(d) Processing topology.', 'Inference may be performed entirely at '
         'an edge processing unit at the station; at a venue-local '
         'aggregation server receiving feature streams from many stations and '
         'performing scoring, fusion, common-mode estimation and coupling '
         'centrally; at a remote server; or in any hybrid division of these. '
         'In privacy-preserving embodiments raw acoustic, optical and radio '
         'signals are reduced to features at the point of acquisition and '
         'only derived features or residual values are transmitted beyond the '
         'venue.'),
        ('(e) Model and residual variants.', 'The predictive model may employ '
         'convolutional, recurrent, or attention-based encoders; a single '
         'joint encoder across modalities or one per modality; prediction of '
         'raw future samples, of future feature statistics, or of the future '
         'embedding. The residual may be computed as squared error, absolute '
         'error, cosine distance in embedding space, or negative '
         'log-likelihood under a predictive distribution. Fusion may be by '
         'mean, maximum, weighted sum with weights set from sanctioned-only '
         'variance, or a learned combiner trained without malpractice '
         'labels.'),
        ('(f) Coupling variants.', 'Cross-station coupling may be measured by '
         'time-lagged cross-correlation, mutual information, coherence, or '
         'event-coincidence statistics over sliding windows. Coupling results '
         'across a venue may be assembled into a graph in which stations are '
         'nodes and supra-threshold proximate pairs are edges; connected '
         'components identify collusion groups involving more than two '
         'candidates, and the graph may be presented to an invigilator as a '
         'live hall map.'),
        ('(g) The second acquisition state.', 'The second state may raise the '
         'sampling rate of one or more transducers, enable a transducer held '
         'inactive in the first state, narrow the directional selectivity of '
         'an acoustic array toward the implicated station, or extend the '
         'retained window of derived features. It may be applied for a fixed '
         'interval, for an interval that extends while the coordination '
         'condition continues to be satisfied, or until an invigilator '
         'acknowledges the indication.'),
        ('(h) Contemplated further development.', 'In a further contemplated '
         'embodiment the predictive model is additionally trained against '
         'corrupted or temporally shuffled future signals as explicit '
         'negative examples, such that a plausible future is scored as more '
         'probable than an implausible one, sharpening the residual used as '
         'the integrity score. This variant is disclosed to preserve it for '
         'possible later claiming; it is deliberately not recited among the '
         'claims of Section 10, as it has not been reduced to practice.'),
        ('(i) Application environments.', 'Beyond examination halls the same '
         'installation applies to professional certification and licensing '
         'test centres, secure interview and vetting rooms, recruitment and '
         'aptitude testing facilities, defence and public-service selection '
         'examinations, controlled-access screening areas, and multi-seat '
         'remote-proctoring installations. In each case the enabling '
         'condition is the same: sanctioned activity is abundant and cheaply '
         'recorded, violations are rare, concealed and unlabellable, and '
         'several monitored positions share one space.'),
    ])


def sec8(doc):
    h1(doc, '8. Validation')
    para(doc,
         'This section reports two bodies of work of different evidential '
         'weight, and they are kept apart deliberately. Part A is a '
         'parametric simulation of station-level signals, in which both the '
         'sanctioned and the violation signals were produced by a generative '
         'model. It establishes internal consistency and nothing more. Part B '
         'is a measurement campaign on a public, real, multi-node sensor '
         'corpus under a licence permitting commercial use, and it is the '
         'evidence on which the cross-station claims rest. No measurement on '
         'a physical prototype of this invention is reported anywhere in this '
         'document; Section 9 sets out prospectively the experiment that '
         'would produce one. Detection quality is reported throughout as '
         'AUROC, where 1.0 is perfect ranking and 0.5 is chance.')

    h2(doc, '8.1 Part A — Simulation of the Single-Station Detector')
    para(doc,
         'Before the method was evaluated the simulation was audited to '
         'confirm that no single sensor feature trivially separates '
         'sanctioned from violation activity; the largest single-feature '
         'separation was small, at a Cohen’s d of 0.16, so any detection must '
         'arise from learned temporal structure rather than from one obvious '
         'cue. A supervised reference detector trained from scratch on the '
         'same data, but permitted to use the labels, establishes the best '
         'achievable performance and serves as a ceiling. The apparent '
         'tension between a single-feature separation of 0.16 and a '
         'supervised ceiling of 0.946 is expected and is itself informative: '
         'the separating information is multivariate and temporal, '
         'distributed across features and across time, and invisible to any '
         'test applied to one feature at one instant.')
    para(doc,
         'The simulation generated twenty-two engineered feature streams per '
         'station: eight acoustic features, being log band energy in six '
         'bands spanning 0–500 Hz, 500 Hz–2 kHz, 2–8 kHz, '
         '8–14 kHz, 14–18 kHz and 18–24 kHz together with '
         'spectral flatness and spectral flux; six electromagnetic features, '
         'being the mean and variance of received signal strength, the '
         'advertisement rate, the count of distinct advertising addresses, '
         'the probe-request rate and channel utilisation; and eight '
         'behavioural features. Streams were segmented into context windows '
         'of thirty frames, yielding 17,000 context windows per modality, and '
         'the model was trained for forty epochs on sanctioned windows only, '
         'with embedding spread held between 0.94 and 0.97 by the '
         'variance-covariance regularisation. All figures derive from a '
         'single training run per configuration; no across-seed variance '
         'estimate exists, and no figure below should be read as carrying '
         'more precision than that supports.',
         lead='Scope of the simulation.')
    table(doc,
          ['Signal strength (SNR)', 'Reference detector (uses labels)',
           'Present method (uses no labels)', 'Interpretation'],
          [['1.0 (overt)', '0.946', '0.705 / 0.781',
            'Recovers about three quarters of the label-using reference with '
            'no labelled malpractice; temporal aggregation raises the figure '
            'to 0.781.'],
           ['0.6 (moderate)', '0.903', '0.653 / 0.716',
            'Detection remains clearly above chance as concealment '
            'increases.'],
           ['0.3 (faint)', '0.843', '0.613 / 0.657',
            'Weak but non-trivial detection of subtle activity.'],
           ['0.15 (near noise floor)', '0.797', '0.541 / 0.571',
            'Approaches chance; defines the lower limit of the operating '
            'envelope.']],
          cap='Table 3: Simulated Single-Station Detection Against Signal '
              'Strength',
          widths=[1.0, 1.25, 1.25, 3.0], size=8.6, align_left_cols=(3,))
    figure(doc, 'fig06.png',
           'Figure 5. Simulated single-station detection across signal '
           'strength, against a label-using reference detector. The second '
           'trace for the present method includes causal temporal '
           'aggregation within the session.', width=5.6)
    para(doc,
         'Two observations follow. The method recovers a substantial fraction '
         'of the label-using reference while using no labelled malpractice, '
         'which is the central claim of the single-station embodiment. And '
         'detection degrades gracefully and monotonically as concealment '
         'increases, approaching chance only near the noise floor. Fusion of '
         'modalities was confirmed to exceed the best single modality. In an '
         'ablated run trained without the variance-covariance regularisation '
         'the embedding spread fell from the healthy 0.94–0.97 range to '
         'approximately 0.09, the signature of representational collapse, and '
         'fused detection fell at every signal strength, to 0.633 against '
         '0.705 at signal strength 1.0 and to 0.571 against 0.613 at 0.3. The '
         'regularisation recited in Section 7 is therefore not incidental: '
         'without it the encoder degenerates toward a near-constant '
         'embedding and the residual loses discriminative content.')
    para(doc,
         'The sanctioned signals and the violation signals of Part A were '
         'both produced by a parametric generative model. The simulation '
         'establishes that a model trained on sanctioned activity alone '
         'recovers a violation signal that a label-using model also recovers, '
         'at a quantified fraction of its performance. It does not establish '
         'external validity, because the statistical structure of real '
         'examination-hall acoustics and radio traffic is not known to match '
         'the generator. The figures are offered as evidence of mechanism, '
         'not as predicted field performance. Part A additionally contained a '
         'simulated cross-station evaluation. Those cross-station figures '
         'have been withdrawn from this disclosure and are not relied upon '
         'anywhere in it, for the reason given at Section 8.3: they were '
         'produced under an assumption about the arrangement that the '
         'measurements of Part B contradict.',
         lead='What Part A does and does not establish.')

    h2(doc, '8.2 Part B — Measurement on a Real Multi-Node Sensor '
            'Corpus')
    para(doc,
         'No public corpus exists of many like-instrumented examination '
         'desks, which is why the disclosure had to simulate in the first '
         'place. The closest available proxy of the right shape is the '
         'Server Machine Dataset, released under the MIT licence with the '
         'OmniAnomaly work: 28 entities, 38 channels each, 28,479 samples per '
         'entity at one sample per minute, per-entity normalised to the unit '
         'interval, with anomaly-free training splits by construction. It '
         'supplies what is needed — many separately instrumented nodes '
         'reporting on a common channel schema, with normal-only data for '
         'each. Two limitations are stated wherever a number from it is '
         'quoted. The entities are heterogeneous machines across three '
         'clusters, whereas a venue is identical desks in one room, which '
         'makes the corpus a pessimistic proxy for anything depending on '
         'stations resembling one another. And the sampling interval is one '
         'minute, so every lag below is expressed in reporting intervals, not '
         'seconds; the mechanism is rate-agnostic and the corpus fixes only '
         'the interval.',
         lead='Corpus.')
    para(doc,
         'The split is group-disjoint throughout. A model trained on groups 1 '
         'and 2 — 17 entities, 417,349 windows — never sees group '
         '3, and every measurement is made on group 3, which is 11 stations '
         'and therefore 55 station pairs. The station-local control models '
         'are trained on each held-out station’s own calibration normals, with '
         'identical architecture, optimiser, epochs and preprocessing, so '
         'that the only difference between the two conditions is shared '
         'against local parameters. The predictor is a deliberately plain '
         'one-step-ahead multilayer perceptron over a window of 20 samples; '
         'plain on purpose, because the contribution claimed is the '
         'arrangement and a strong backbone would blur which is which. '
         'Perturbations representing a coupled exchange and a venue-wide '
         'event are injected into the raw channel signal before the '
         'predictor, never into the residual. Those perturbations are '
         'synthetic, because no public corpus carries real cross-station '
         'coupling; that limitation is repeated at Section 8.3 and is not '
         'minimised.',
         lead='Protocol.')

    para(doc,
         'The first question is whether one normal-only model applied across '
         'the stations makes their residual magnitudes comparable, so that a '
         'threshold calibrated at one station holds at another. A threshold '
         'was set at each station 99th residual percentile and applied to '
         'every other station held-out normals, over 110 ordered pairs. It '
         'does not. Sharing widens scale disagreement on every metric '
         'measured, and is also worse at detection on the labelled test '
         'split.',
         lead='Residual comparability under a shared model.')
    hd = SMD['headline']
    hb = SMDB['headline']
    table(doc,
          ['Quantity (nominal false-positive rate 1 %)',
           'One model shared', 'Model per station',
           'Shared, 3x width', 'Per station, 3x width'],
          [['station pairs within 2x nominal',
            pc(hd['shared_frac_within_2x']),
            pc(hd['per_station_frac_within_2x']),
            pc(hb['shared_frac_within_2x']),
            pc(hb['per_station_frac_within_2x'])],
           ['station pairs within 10x nominal',
            pc(hd['shared_frac_within_10x']),
            pc(hd['per_station_frac_within_10x']),
            pc(hb['shared_frac_within_10x']),
            pc(hb['per_station_frac_within_10x'])],
           ['95th-percentile realised false-positive rate',
            pc(hd['shared_fpr_p95']), pc(hd['per_station_fpr_p95']),
            pc(hb['shared_fpr_p95']), pc(hb['per_station_fpr_p95'])],
           ['median KS distance between station residuals',
            '%.3f' % hd['shared_ks_median'],
            '%.3f' % hd['per_station_ks_median'],
            '%.3f' % hb['shared_ks_median'],
            '%.3f' % hb['per_station_ks_median']],
           ['mean AUROC on the labelled test split',
            '%.3f' % hd['shared_auroc_mean'],
            '%.3f' % hd['per_station_auroc_mean'],
            '%.3f' % hb['shared_auroc_mean'],
            '%.3f' % hb['per_station_auroc_mean']]],
          cap='Table 4: Residual Comparability Across 11 Held-Out Stations, '
              'at Two Model Capacities',
          widths=[2.35, 1.02, 1.05, 1.02, 1.06], size=8.6,
          align_left_cols=(0,))
    figure(doc, 'fig07.png',
           'Figure 6. Residual comparability across stations. Sharing one '
           'normal-only model is worse on every metric, and adding capacity '
           'widens the deficit rather than closing it.', width=6.5)
    para(doc,
         'The obvious rebuttal is capacity: that a model of %d units trained '
         'for %d epochs simply lacked the capacity to fit 17 heterogeneous '
         'machines. The right-hand columns close that objection. Re-run at '
         '%d units and %d epochs, with both conditions scaled identically, '
         'the shared model gets worse and the gap widens — the deficit '
         'in station pairs within ten times nominal grows from %.1f points to '
         '%.1f. The mechanism is straightforward once stated: a shared model '
         'fits some stations better than others, so its residual magnitude '
         'encodes how typical that station is. That is a station property, '
         'not a common scale.'
         % (SMD['config']['hidden'], SMD['config']['epochs'],
            SMDB['config']['hidden'], SMDB['config']['epochs'],
            100 * (hd['per_station_frac_within_10x']
                   - hd['shared_frac_within_10x']),
            100 * (hb['per_station_frac_within_10x']
                   - hb['shared_frac_within_10x'])))

    para(doc,
         'The second question is whether a coupled station pair can be '
         'identified while a venue-wide event is also present. This is the '
         'operating case. One station pair was coupled at a lag of two '
         'reporting intervals and a simultaneous event was applied to all 11 '
         'stations. Identification is the strict test of whether the coupled '
         'pair ranks first out of 55; the AUROC column ranks it against the '
         '54 uncoupled pairs. Twenty trials, with the pairs and the '
         'injections resampled each trial and the predictors held fixed.',
         lead='Identification of a coupled pair under a venue-wide event.')
    s = REP['summary']
    order = [('one model shared', 'none', 'D_both|shared|none'),
             ('one model shared', 'median across stations',
              'D_both|shared|raw_median'),
             ('one model shared', 'standardised median',
              'D_both|shared|standardised_median'),
             ('model per station', 'none', 'D_both|per_station|none'),
             ('model per station', 'median across stations',
              'D_both|per_station|raw_median'),
             ('model per station', 'standardised median',
              'D_both|per_station|standardised_median')]
    table(doc,
          ['Residual model', 'Common-mode reference',
           'Coupled pair ranked first of 55', 'AUROC over pairs',
           'Median z of the coupled pair'],
          [[a, b, '%.2f' % s[k]['detection_rate_top_ranked'],
            '%.3f' % s[k]['auroc_over_pairs_mean'],
            '%.2f' % s[k]['z_median']] for a, b, k in order],
          cap='Table 5: Identification of a Coupled Station Pair in the '
              'Presence of a Venue-Wide Event, 20 Trials',
          widths=[1.35, 1.55, 1.25, 1.0, 1.35], size=8.8,
          align_left_cols=(0, 1))
    figure(doc, 'fig08.png',
           'Figure 7. Identification of the coupled pair by residual model '
           'and common-mode reference rule. The claimed arrangement is the '
           'heavy-outlined bar; the shared-model conditions are at chance and '
           'return no identification in twenty trials.', width=6.3)
    para(doc,
         'Three findings fall out and all three bear directly on the claims. '
         'The shared-model conditions are at chance, at an AUROC of %.3f to '
         '%.3f across every reference rule, with no identification in twenty '
         'trials; sharing does not merely fail to help, it removes the '
         'channel. Common-mode rejection is necessary, and the size of its '
         'effect is now measured rather than asserted: with station-local '
         'models, moving from no reference to the plain across-station median '
         'takes AUROC from %.3f to %.3f and identification from %.2f to %.2f. '
         'And the additional per-station standardisation of the reference is '
         'not needed and slightly hurts, at %.3f against %.3f, so Claim 12 '
         'recites the plain median.'
         % (min(s['D_both|shared|%s' % r]['auroc_over_pairs_mean']
                for r in ('none', 'raw_median', 'standardised_median')),
            max(s['D_both|shared|%s' % r]['auroc_over_pairs_mean']
                for r in ('none', 'raw_median', 'standardised_median')),
            s['D_both|per_station|none']['auroc_over_pairs_mean'],
            s['D_both|per_station|raw_median']['auroc_over_pairs_mean'],
            s['D_both|per_station|none']['detection_rate_top_ranked'],
            s['D_both|per_station|raw_median']['detection_rate_top_ranked'],
            s['D_both|per_station|standardised_median']
            ['auroc_over_pairs_mean'],
            s['D_both|per_station|raw_median']['auroc_over_pairs_mean']))

    cm = CPL['common_mode_suppression']
    table(doc,
          ['Residual model', 'No coordinated activity present',
           'Venue-wide event, no rejection',
           'Venue-wide event, after rejection'],
          [['model per station',
            '%.4f' % cm['per_station|raw_median']['floor_no_injection_mean_r'],
            '%.4f' % cm['per_station|raw_median']
            ['with_event_no_rejection_mean_r'],
            '%.4f' % cm['per_station|raw_median']
            ['with_event_after_rejection_mean_r']],
           ['one model shared',
            '%.4f' % cm['shared|raw_median']['floor_no_injection_mean_r'],
            '%.4f' % cm['shared|raw_median']
            ['with_event_no_rejection_mean_r'],
            '%.4f' % cm['shared|raw_median']
            ['with_event_after_rejection_mean_r']]],
          cap='Table 6: Mean Pairwise Coupling Over All 55 Station Pairs, '
              'Before and After Common-Mode Rejection',
          widths=[1.45, 1.75, 1.65, 1.65], size=8.8, align_left_cols=(0,))
    figure(doc, 'fig05.png',
           'Figure 8. Suppression of a venue-wide event. With station-local '
           'models the event is removed to below the uninjected floor; with '
           'one shared model the reference cannot remove a component the '
           'shared model itself contributes to every station.', width=5.6)
    para(doc,
         'The last row of Table 6 explains why the shared model poisons the '
         'channel, and the explanation is mechanical rather than statistical. '
         'The prediction errors of one model applied to many stations are '
         'correlated across those stations because they are the errors of '
         'one and the same model. The shared model manufactures a '
         'cross-station common '
         'component out of its own deficiencies, and a reference formed from '
         'the stations carrying that component cannot remove it. With no '
         'injection at all, applying median rejection under the shared model '
         'raises mean pairwise coupling from %.4f to %.4f — it adds '
         'coupling where there was none.'
         % (cm['shared|raw_median']['floor_no_injection_mean_r'],
            cm['shared|raw_median']['with_event_after_rejection_mean_r']))

    para(doc,
         'The tolerance recited in the claims is measured, not asserted. '
         'Station clocks were deliberately skewed and the identification '
         'repeated, twenty trials per point, at a coupling lag of two '
         'reporting intervals.',
         lead='Tolerance to inter-station timing error.')
    sk = REP['skew_sweep']
    lag = float(REP['config']['couple_lag'])
    table(doc,
          ['Timing error (reporting intervals)',
           'As a multiple of the coupling lag',
           'Coupled pair ranked first of 55', 'AUROC over pairs',
           'Median z'],
          [[k, '%.1fx' % (int(k) / lag),
            '%.2f' % sk[k]['detection_rate_top_ranked'],
            '%.3f' % sk[k]['auroc_over_pairs_mean'],
            '%.2f' % sk[k]['z_median']]
           for k in sorted(sk, key=int)],
          cap='Table 7: Tolerance to Inter-Station Timing Error',
          widths=[1.45, 1.5, 1.4, 1.05, 0.95], size=8.8)
    figure(doc, 'fig09.png',
           'Figure 9. Tolerance to inter-station timing error, expressed as a '
           'multiple of the coupling lag and therefore independent of the '
           'station reporting rate. The shaded band is the tolerance recited '
           'at Claim 14.', width=5.6)
    para(doc,
         'The degradation is monotone and, expressed as a fraction of the '
         'coupling lag, rate-agnostic: ranking accuracy holds above 0.95 '
         'while the error stays within about one and a half times the lag and '
         'collapses beyond three times it. For the one-to-three-second '
         'coupling lag of the principal embodiment that places the useful '
         'envelope near or below one second, and puts an alignment of '
         'fifty milliseconds — which ordinary network time '
         'synchronisation over a local area network attains — at roughly '
         'two per cent of the lag, comfortably inside it. An earlier skew '
         'sweep, run before the factorial of Table 5 had established which '
         'cell was detecting, was performed on the shared-model condition and '
         'therefore measured the degradation of a non-signal. It is void, is '
         'not reported here, and is retained in the working record only so '
         'that the error stands on it.')

    para(doc,
         'Ranking accuracy alone does not say when the channel is usable. Two '
         'sweeps bound it, both with station-local models, the plain median '
         'reference and a venue-wide event present, twenty resampled trials '
         'per point.',
         lead='Operating envelope of the coupling channel.')
    amp = ENV['amplitude_sweep']
    table(doc,
          ['Amplitude of each exchange, as a fraction of the channel range']
          + ['%g' % float(k) for k in sorted(amp, key=float)],
          [['coupled pair ranked first of 55']
           + ['%.2f' % amp[k]['detection_rate_top_ranked']
              for k in sorted(amp, key=float)],
           ['AUROC over pairs']
           + ['%.3f' % amp[k]['auroc_over_pairs_mean']
              for k in sorted(amp, key=float)]],
          cap='Table 8: Operating Envelope Against Exchange Amplitude, '
              'at 60 Exchanges',
          widths=[2.3, 0.68, 0.68, 0.68, 0.68, 0.68, 0.68], size=8.4,
          align_left_cols=(0,))
    ev = ENV['event_count_sweep']
    table(doc,
          ['Number of separate coupled exchanges in the observation window']
          + [k for k in sorted(ev, key=int)],
          [['coupled pair ranked first of 55']
           + ['%.2f' % ev[k]['detection_rate_top_ranked']
              for k in sorted(ev, key=int)],
           ['AUROC over pairs']
           + ['%.3f' % ev[k]['auroc_over_pairs_mean']
              for k in sorted(ev, key=int)]],
          cap='Table 9: Operating Envelope Against the Number of Coupled '
              'Exchanges, at Amplitude 0.15',
          widths=[2.6, 0.78, 0.78, 0.78, 0.78, 0.78], size=8.4,
          align_left_cols=(0,))
    figure(doc, 'fig10.png',
           'Figure 10. Operating envelope of the coupling channel. There is a '
           'sharp knee in amplitude between 0.06 and 0.10 of the channel '
           'range, and the channel needs repeated exchanges rather than one '
           'large exchange.', width=6.3)
    para(doc,
         'Both axes are monotone and the second is the more operationally '
         'meaningful. The coupling statistic is a correlation estimate, so it '
         'requires repeated exchanges rather than one dramatic one: a single '
         'exchange is not detectable by this mechanism, and nothing in this '
         'disclosure should be read as implying that it is. The channel '
         'becomes useful from roughly twenty separate exchanges and is strong '
         'beyond forty, which is the measurement behind the recitation of a '
         'predetermined number of separate occasions at Claim 17 and of a '
         'figure of not fewer than twenty at Claim 18. In amplitude there is '
         'a sharp knee: below about six per cent of the channel range the '
         'channel is dead, and at and above fifteen per cent identification '
         'is close to certain.')

    h2(doc, '8.3 What the Measurements Establish, and What They Do Not')
    para(doc,
         'Part B is a measurement on real recorded multi-node sensor data '
         'under a permissive licence, and it establishes four things about '
         'the arrangement claimed: that residuals from one shared model are '
         'not comparable across nodes and become less so with capacity; that '
         'a venue-wide disturbance defeats pairwise coupling unless a common '
         'component is estimated and removed; that removing it restores '
         'identification, from %.2f to %.2f of trials; and that the tolerance '
         'to timing error scales with the coupling lag. Four limitations bound '
         'it, and each is stated wherever the numbers are used. The corpus is '
         'server telemetry, not desks in a hall, so it is a proxy of the '
         'right shape and the wrong physics; no acoustic transducer, no '
         'electromagnetic sensor and no candidate was involved. The entities '
         'are heterogeneous machines, which makes the proxy pessimistic. The '
         'coupled exchange and the venue-wide event are synthetic injections, '
         'because no public corpus carries real cross-station coupling. And '
         'identification is a strict top-one-of-fifty-five criterion at 55 '
         'pairs; a hall of a hundred desks has about five thousand pairs, and '
         'the false-alarm rate per pair-hour at that scale has not been '
         'measured by anyone, including the inventor.'
         % (s['D_both|per_station|none']['detection_rate_top_ranked'],
            s['D_both|per_station|raw_median']['detection_rate_top_ranked']))
    para(doc,
         'An earlier revision of this disclosure argued the opposite of what '
         'Part B measures. It asserted that scoring every station with one '
         'common normal-only model rendered the residual time-series '
         '"numerically comparable by construction", and that this '
         'commensurability was what made the cross-station channel available. '
         'That assertion is contradicted in direction by Table 4 and Table 5. '
         'It has been removed from Section 4.1 and from the claims, and it '
         'must not be reinstated. The simulated cross-station figures of Part '
         'A were produced under the same assumption and have been withdrawn '
         'with it. The correction strengthens the position rather than '
         'weakening it: sharing one model across stations is the obvious '
         'expedient a skilled person would adopt for economy and for '
         'uniformity of scale, and the invention now teaches away from it and '
         'gives the measured reason.',
         lead='A withdrawn assertion, recorded rather than deleted.')

    h2(doc, '8.4 Operating Envelope and Alert Burden')
    para(doc,
         'Ranking performance does not by itself state how many alerts an '
         'invigilator would receive, and Objective 10 undertakes to state the '
         'conditions under which detection is reliable. The operating points '
         'below are derived from the single-station ranking performance of '
         'Table 3 under an equal-variance Gaussian assumption on the score '
         'distributions, by which the discriminability index is the square '
         'root of two times the inverse normal of the AUROC. They are '
         'analytic projections rather than separately measured quantities, '
         'and are to be replaced by measured values once score distributions '
         'are logged. They are stated for the best single-station '
         'configuration, an AUROC of 0.781 with temporal aggregation, at the '
         'overt signal strength.')
    table(doc,
          ['Stations referred per 300-station hall', 'Fraction of the hall',
           'Expected fraction of violating candidates recovered'],
          [['1', '0.3 %', 'approx. 5 %'],
           ['5', '1.7 %', 'approx. 15 %'],
           ['10', '3.3 %', 'approx. 23 %'],
           ['20', '6.7 %', 'approx. 34 %']],
          cap='Table 10: Session-Level Alert Budget at the Simulated '
              'Single-Station Operating Point',
          widths=[2.1, 1.5, 2.6], size=9.0)
    para(doc,
         'The system is intended to operate at session level as a '
         'prioritisation aid, not at window level as an adjudicator. '
         'Residuals are aggregated over the whole of a candidate session, '
         'candidates are ranked by aggregated score, and a fixed alert budget '
         'of the highest-ranked stations is referred for human attention, per '
         'Claims 7, 10 and 26. Within a realistic invigilation budget the '
         'installation concentrates finite human attention on the stations '
         'most likely to warrant it, at a recovery rate materially above the '
         'uniform-random baseline that unaided invigilation approximates, and '
         'it does so without any labelled malpractice data. It is not '
         'asserted, and no claim should be construed to assert, that an '
         'indication generated by the installation constitutes proof of '
         'malpractice. The output is an ordering of stations for human '
         'inspection, and, where the coordination condition is satisfied, a '
         'bounded change in the acquisition state of two of them.')


def sec9(doc):
    h1(doc, '9. Contemplated Prototype and Planned Physical Validation')
    para(doc,
         'No physical prototype has been constructed as at the date of this '
         'disclosure, and no measurement on the transducers of this invention '
         'is reported anywhere in this document. This section is prospective. '
         'It is included to satisfy sufficiency by describing, in terms an '
         'ordinarily skilled person could follow, a specific hardware '
         'embodiment by which the invention may be reduced to practice, and '
         'to define in advance the experiment that would move it from its '
         'present readiness level to TRL 4. Nothing here is to be read as a '
         'report of results obtained.')
    para(doc,
         'Five nodes exercise every claimed mechanism: four candidate '
         'stations, two of which form the coupled pair while a third carries '
         'an isolated individual anomaly as a distractor, and one node '
         'instrumented identically and held unoccupied. The unoccupied node '
         'is not an optional extra in this build; it is the element on which '
         'Claims 11, 19 and 24 turn. One venue-local aggregator serves all '
         'five.',
         lead='Minimum configuration.')
    table(doc,
          ['Function', 'Representative component', 'Rationale'],
          [['Acoustic sensing, audible and near-ultrasonic',
            'Knowles SPH0641LU4H-1 PDM MEMS microphone, rated 100 Hz to '
            '80 kHz, on a breakout such as the RAK18032 module',
            'Operated in ultrasonic mode with a PDM clock of 3.072 MHz or '
            'above, this part reaches the 18 to 45 kHz band in which covert '
            'audio links operate. Ordinary voice microphones roll off near '
            '20 kHz and would not capture that band at all.'],
           ['Acoustic analogue front end (24)',
            'Band-pass 80 Hz to 1 kHz for the voice band and a second path '
            'for the near-ultrasonic band, precision rectifier, low-pass at '
            'approximately 50 Hz',
            'Digitising the envelope rather than the waveform is what makes '
            'the retained representation non-invertible, and it removes the '
            'Nyquist requirement that waveform capture in a 45 kHz band would '
            'otherwise impose on every station.'],
           ['Electromagnetic sensing, 2.4 GHz ISM band',
            'ESP32-S3 module in IEEE 802.11 promiscuous mode with concurrent '
            'BLE scanning',
            'Captures management-frame rate, advertisement rate and per-frame '
            'received-signal-strength without decrypting payloads, which '
            'preserves the property recited at Section 7.1(d).'],
           ['Broadband radio-frequency energy (optional)',
            'RTL-SDR receiver (RTL2832U with R820T2 tuner), or an nRF24L01+ '
            'operated as a carrier-detect channel scanner',
            'Extends coverage beyond the ISM band to cellular uplink and to '
            'emitters that do not advertise.'],
           ['Behavioural sensing (optional)',
            'Camera module such as a Raspberry Pi Camera Module 3 or an '
            'ESP32-CAM, features extracted at the aggregator',
            'Supplies the optional third modality of Claim 8. Raw frames are '
            'discarded after feature extraction.'],
           ['Second acquisition state (84)',
            'Firmware-selectable PDM clock and reporting rate; a second '
            'microphone enabled only in the second state; optionally a '
            'two-element endfire array per station',
            'Provides the physical state change of Claim 19 without '
            'additional apparatus beyond a second transducer per station.'],
           ['Inter-station time synchronisation (70)',
            'SNTP discipline over the venue local area network',
            'Table 7 puts the required alignment at a fraction of the '
            'coupling lag, which for a one-to-three-second lag is hundreds of '
            'milliseconds. Ordinary network time synchronisation meets that '
            'with margin; no pulse-per-second distribution and no satellite '
            'discipline are required.'],
           ['Common-mode reference (90)',
            'At least one node of identical construction per hall or per '
            'zone, held unoccupied',
            'Supplies the part of the venue-common estimate that carries no '
            'candidate. Claims 11, 19 and 24 recite it as a structural '
            'element.'],
           ['Aggregation and inference',
            'Single-board computer such as a Raspberry Pi 5 (8 GB), or a '
            'laptop host',
            'Executes the per-station encoders and predictors, residual '
            'scoring, standardisation, fusion, common-mode estimation, '
            'coupling and the coordination condition.'],
           ['Staged-violation instruments (evaluation only)',
            'A spare smartphone at reduced transmit power; a Bluetooth '
            'earpiece; a paired phone and speaker generating a '
            'near-ultrasonic link',
            'Used only to generate ground-truth episodes for evaluation. '
            'These devices are never used in training, which preserves the '
            'label-free property of the method under test.']],
          cap='Table 11: Contemplated Station Hardware',
          widths=[1.5, 2.15, 2.55], size=8.2, align_left_cols=(0, 1, 2))

    para(doc,
         'Sanctioned-session data would first be recorded from consenting '
         'volunteers performing written work under ordinary conditions, that '
         'data alone forming the training corpus and the calibration set at '
         'each node. Violation episodes would then be staged with '
         'independently logged ground-truth timestamps. Ground truth would be '
         'used for evaluation only and never for training. The bench '
         'programme below is ordered so that the tests carrying the most '
         'claim weight run first.',
         lead='Planned protocol.')
    table(doc,
          ['', 'Test', 'What it validates', 'Why it is needed'],
          [['B1', 'Residual series generated from real node audio and '
            'accelerometry, normal-only training at each node',
            'The residual chain on real transducers',
            'Nothing in Section 8 Part B used a microphone.'],
           ['B2', 'Station-local against shared model on the five real nodes',
            'The Table 4 and Table 5 findings, on hardware',
            'Turns a proxy result into a component result.'],
           ['B3', 'Staged venue-wide event (door, announcement, chair scrape) '
            'across all five nodes; suppression measured with and without the '
            'unoccupied node in the reference',
            'Claim 11 and Claim 19 reference element',
            'The only test that shows the unoccupied station earns its place '
            'as a structural limitation.'],
           ['B4', 'Two confederates exchanging whispers or taps at a '
            'controlled lag; the coupled pair against the other five pairs',
            'Claims 11, 17 and 24',
            'First real coupling, replacing synthetic injection.'],
           ['B5', 'Per-pair sanctioned-activity baseline measured, and its '
            'stability across a session',
            'The inverted null of Claim 17',
            'The baseline must be stable within a session or the claim '
            'fails.'],
           ['B6', 'Node clocks deliberately skewed; the degradation curve of '
            'Table 7 reproduced', 'Claim 14',
            'Confirms the measured tolerance envelope on hardware.'],
           ['B7', 'A two-to-three-hour sanctioned session with no '
            'coordination; false-alarm rate per pair-hour',
            'Every cross-station claim',
            'The number that does not yet exist, and the first thing a '
            'sceptical reader asks. A hall of a hundred desks is about five '
            'thousand pairs.'],
           ['B8', 'Acquisition-state switch exercised end to end; latency '
            'from condition satisfied to state changed, and confinement to '
            'the implicated pair', 'Claims 19 to 21',
            'Confirms that the physical response occurs, is bounded, and '
            'reaches no other station.']],
          cap='Table 12: Bench Programme for the Contemplated Prototype',
          widths=[0.35, 2.0, 1.55, 2.3], size=8.2, align_left_cols=(1, 2, 3))

    para(doc,
         'The trial is specified so that it can fail. Residuals should rise '
         'during staged violation episodes and return to baseline during '
         'sanctioned activity, without the model having been shown any '
         'violation example; if they do not separate on real signals, the '
         'single-station claim is not supported outside simulation. Residual '
         'elevations at two colluding proximate stations should be time-locked '
         'after common-mode subtraction, while an isolated staged anomaly '
         'should produce no corresponding elevation at its neighbour; if '
         'coupling is observed equally for innocent adjacent pairs after '
         'subtraction and after each pair’s own baseline is applied, the '
         'cross-station claims fail. Removing the unoccupied node from the '
         'reference should measurably degrade suppression in B3; if it does '
         'not, the reference station is not earning its place as a claim '
         'element and should be demoted to a dependent. And per-station, '
         'per-session calibration from an initial sanctioned interval should '
         'suffice to bring the residual distribution to a usable operating '
         'point; if the distribution drifts materially within a session, the '
         'held-fixed variant of Claim 2 is insufficient and its re-established '
         'variant is required.',
         lead='Predictions the trial would test.')
    para(doc,
         'Even if every prediction were confirmed, such a trial would '
         'establish only that the arrangement operates on physically acquired '
         'sensor data and that the coupling channel is observable in '
         'practice. The environment would be a controlled room rather than a '
         'populated examination hall, lacking the dense ambient radio '
         'population, crowd acoustics and invigilator movement of operational '
         'conditions. The number of stations and participants would be small, '
         'and five nodes give ten pairs where a hall gives thousands. '
         'Violation episodes would be staged by informed volunteers rather '
         'than performed adversarially by candidates with an incentive to '
         'evade detection. Performance in an operational hall should be '
         'expected to fall below both the simulated figures of Part A and any '
         'figures such a trial produced, and this disclosure does not assert '
         'otherwise.',
         lead='Limits of what such a trial would establish.')


CLAIMS = [
    ('A. System claims — single-station label-free detection', None),
    ('Claim 1 (independent).',
     'An integrity-monitoring system for a monitored assessment station, '
     'comprising: a sensing assembly mechanically carried by a station body '
     'and comprising at least one acoustic transducer and at least one '
     'further transducer of a different physical modality, arranged to '
     'produce respective signal streams; a processing unit coupled to the '
     'sensing assembly; and a communication module; wherein the processing '
     'unit is configured to: form, from each said signal stream, context '
     'windows of predetermined duration; compute for each context window, by '
     'a predictive model established from signal streams recorded during '
     'sanctioned activity at that station, a predicted change of the stream '
     'over a prediction horizon of predetermined duration and a prediction '
     'residual between the predicted change and the observed change; '
     'establish, at that station and during an initial interval of each '
     'monitored session, standardisation statistics for the said residual, '
     'and standardise the residual against those statistics for the '
     'remainder of that session; derive an integrity-violation score from the '
     'standardised residuals of the said streams; and cause the '
     'communication module to transmit an alert identifying the station when '
     'the said score satisfies a predetermined alert condition.'),
    ('Claim 2.',
     'The system of Claim 1, wherein the standardisation statistics are held '
     'fixed for the remainder of the monitored session after the initial '
     'interval, or are re-established at predetermined intervals during the '
     'session.'),
    ('Claim 3.',
     'The system of Claim 1, wherein the acoustic transducer is arranged to '
     'capture acoustic energy including a near-ultrasonic band above 15 kHz.'),
    ('Claim 4.',
     'The system of Claim 3, wherein the said further transducer is an '
     'electromagnetic sensor capturing at least device-advertisement activity '
     'and received-signal-strength dynamics, the acoustic and electromagnetic '
     'sensors being disposed within or upon a desk body constituting the '
     'station.'),
    ('Claim 5.',
     'The system of Claim 1, wherein the said further transducer comprises '
     'one or more of: a mechanical vibration or accelerometric sensor; a '
     'magnetic-field sensor; a pressure, strain, or load sensor; a thermal or '
     'infrared sensor; a millimetre-wave or radar-based micro-motion sensor; '
     'a capacitive proximity sensor; and an optical sensor of candidate '
     'behaviour.'),
    ('Claim 6.',
     'The system of Claim 1, wherein a prediction residual is computed and '
     'standardised for each of a plurality of sensing modalities and the '
     'standardised residuals are fused into a combined integrity-violation '
     'score by a weighted combination, the weights being determined, without '
     'any labelled data, from statistics of those residuals over the '
     'sanctioned calibration interval at that station.'),
    ('Claim 7.',
     'The system of Claim 1, wherein the integrity-violation score is further '
     'aggregated by a causal rolling statistic over an extended interval '
     'within the monitored session, the aggregated score being used in place '
     'of the instantaneous score for evaluation of the alert condition.'),
    ('Claim 8.',
     'The system of Claim 6, further comprising an optical behavioural '
     'sensing module deriving gaze direction, blink rate, head pose and '
     'fixation features, a prediction residual of which is included in the '
     'said weighted combination.'),
    ('Claim 9.',
     'The system of Claim 1, wherein the predictive model comprises, for each '
     'sensing modality, an encoder producing an embedding of the context '
     'window and a predictor operating upon that embedding, the encoder and '
     'predictor having been trained jointly under an objective comprising a '
     'prediction-error term and a variance-and-covariance regularisation term '
     'applied to the embedding, the said regularisation term preventing '
     'collapse of the embedding to a constant.'),
    ('Claim 10.',
     'The system of Claim 1, wherein the processing unit aggregates the '
     'integrity-violation score over the whole of the monitored session for '
     'each of a plurality of stations, ranks the stations by aggregated '
     'score, and causes the communication module to identify to an '
     'invigilator a predetermined number of highest-ranked stations for human '
     'inspection.'),

    ('B. System claims — venue installation and cross-station '
     'coordination', None),
    ('Claim 11 (independent).',
     'An examination-venue integrity installation, comprising: a plurality of '
     'candidate stations, each comprising a station body and a sensing '
     'assembly mechanically carried by that station body, the sensing '
     'assembly of each candidate station comprising at least one acoustic '
     'transducer and at least one further transducer of a different physical '
     'modality; at least one reference station comprising a station body and '
     'a sensing assembly of like construction to that of the candidate '
     'stations, disposed among the candidate stations within the venue and '
     'configured to remain unoccupied throughout a monitored session; a '
     'time-synchronisation arrangement establishing a common time base across '
     'the sensing assemblies of the candidate stations and of the reference '
     'station to within a predetermined timing tolerance; and a processing '
     'arrangement configured to: derive, for each said station, a '
     'prediction-residual time-series from the signals of the sensing '
     'assembly of that station by means of a predictive model and '
     'standardisation '
     'statistics established at that station from an interval of sanctioned '
     'activity at that station; form, from the residual time-series of the '
     'candidate stations and from the residual time-series of the said '
     'reference station, a venue-common component representing residual '
     'variation shared across the venue, and subtract that component from the '
     'residual time-series of each candidate station; evaluate a time-lagged '
     'coupling statistic between the corrected residual time-series of pairs '
     'of candidate stations, over a set of lags the shortest of which is not '
     'less than twice the said timing tolerance; indicate coordinated '
     'malpractice in respect of a pair when the said statistic satisfies a '
     'predetermined coordination condition; and indicate an isolated '
     'individual anomaly when an elevated residual at one candidate station '
     'is unaccompanied by a coupling, satisfying that condition, to any other '
     'candidate station.'),
    ('Claim 12.',
     'The installation of Claim 11, wherein the venue-common component is a '
     'median taken across the residual time-series of the said candidate '
     'stations and of the said reference station at each sampling instant.'),
    ('Claim 13.',
     'The installation of Claim 11, wherein the sensing assembly of the '
     'reference station is identical in construction and configuration to '
     'that of the candidate stations, and wherein two or more such reference '
     'stations are disposed at spaced positions within the venue.'),
    ('Claim 14.',
     'The installation of Claim 11, wherein the said timing tolerance does '
     'not exceed one half of the shortest lag at which the coupling statistic '
     'is evaluated.'),
    ('Claim 15.',
     'The installation of Claim 11, wherein the coupling statistic is '
     'computed separately for each of a plurality of sensing modalities and '
     'thereafter combined, the contribution of each modality being weighted '
     'according to statistics of its residual over the sanctioned calibration '
     'interval.'),
    ('Claim 16.',
     'The installation of Claim 11, wherein coupling statistics computed '
     'across the plurality of candidate stations are assembled into a graph '
     'in which candidate stations constitute nodes and station pairs '
     'satisfying the coordination condition constitute edges, and wherein '
     'connected components of that graph identify collusion groups comprising '
     'more than two candidates.'),
    ('Claim 17 (independent).',
     'A system for distinguishing coordinated malpractice from coincidental '
     'anomaly at a monitored venue, comprising a plurality of monitored '
     'stations each associated with a sensing assembly comprising at least '
     'two transducers of different physical modality, and a processing '
     'arrangement configured to: generate, for each station, a '
     'prediction-residual time-series by means of a predictive model and '
     'standardisation statistics established separately for that station from '
     'an interval of sanctioned activity at that station; subtract from the '
     'residual time-series of each station a venue-common component derived '
     'from the residual time-series of a plurality of the said stations; '
     'establish, for each pair of stations and during an interval of the '
     'session in which activity is sanctioned, a baseline value of a '
     'time-lagged coupling statistic between the corrected residual '
     'time-series of that pair; evaluate the said coupling statistic for that '
     'pair during a subsequent interval of the session; and indicate '
     'coordinated malpractice in respect of a pair only when the coupling '
     'statistic for that pair exceeds the baseline value established for that '
     'same pair by a predetermined margin, on each of at least a '
     'predetermined number of separate occasions within the session.'),
    ('Claim 18.',
     'The system of Claim 17, wherein the said predetermined number of '
     'separate occasions is not fewer than twenty.'),
    ('Claim 19 (independent).',
     'An examination-venue integrity installation, comprising: a plurality of '
     'candidate stations, each carrying a sensing assembly comprising at '
     'least one acoustic transducer and at least one further transducer of a '
     'different physical modality, the said sensing assembly being operable '
     'in a first acquisition state and in a second acquisition state; at '
     'least one '
     'reference station carrying a sensing assembly of like construction and '
     'held unoccupied within the venue throughout a monitored session; and a '
     'processing arrangement configured to derive, for each said station, a '
     'prediction-residual time-series by means of a predictive model and '
     'standardisation statistics established at that station; to subtract '
     'from the residual time-series of each candidate station a venue-common '
     'component formed using at least the residual time-series of the said '
     'reference station; to evaluate a time-lagged coupling statistic between '
     'the corrected residual time-series of pairs of candidate stations; and, '
     'upon the coupling statistic for a pair satisfying a predetermined '
     'coordination condition, to switch the sensing assemblies of the two '
     'candidate stations of that pair, and of no other candidate station, '
     'from the first acquisition state into the second acquisition state for '
     'a bounded interval.'),
    ('Claim 20.',
     'The installation of Claim 19, wherein the second acquisition state '
     'differs from the first in at least one of: the sampling rate of at '
     'least one transducer; the number of transducers enabled; and the '
     'directional selectivity of acquisition.'),
    ('Claim 21.',
     'The installation of Claim 19, wherein the said bounded interval does '
     'not exceed a predetermined maximum, and wherein upon its expiry the '
     'sensing assemblies of the said two candidate stations revert to the '
     'first acquisition state unless the coordination condition is again '
     'satisfied in respect of that pair.'),
    ('Claim 22.',
     'The installation of Claim 19, wherein the output of the acoustic '
     'transducer of each sensing assembly is band-limited and rectified to an '
     'envelope prior to digitisation, and wherein only order statistics of '
     'that envelope over each reporting window are retained and transmitted, '
     'whereby the retained representation is not invertible to the acoustic '
     'waveform from which it was derived.'),

    ('C. Method claims', None),
    ('Claim 23 (independent).',
     'A method for label-free detection of malpractice at a monitored '
     'assessment station, comprising: acquiring one or more sensor signal '
     'streams from a sensing assembly mechanically carried by that station; '
     'forming, from each said stream, context windows of predetermined '
     'duration; generating, by a predictive model trained exclusively on '
     'signal streams recorded during sanctioned activity at that station and '
     'containing no labelled instance of malpractice, a predicted change of '
     'the stream over a prediction horizon of predetermined duration for each '
     'context window; computing a prediction residual between the predicted '
     'change and the observed change; establishing standardisation statistics '
     'at that station from an initial sanctioned interval of the monitored '
     'session and standardising the residual against them; deriving an '
     'integrity-violation score from the standardised residual; and issuing '
     'an alert when the said score satisfies a predetermined alert condition; '
     'wherein no labelled example of malpractice is employed at any stage of '
     'the method, including the training of the said model.'),
    ('Claim 24 (independent).',
     'A method of distinguishing coordinated malpractice from coincidental '
     'anomaly at a monitored venue having a plurality of instrumented '
     'candidate stations and at least one station instrumented in like manner '
     'and held unoccupied, the method comprising: establishing at each said '
     'station, from an interval of sanctioned activity at that station, a '
     'predictive model and standardisation statistics for that station; '
     'generating at each said station a standardised prediction-residual '
     'time-series; forming a venue-common component from the residual '
     'time-series of a plurality of the candidate stations and of the said '
     'unoccupied station, and subtracting it from the residual time-series of '
     'each candidate station; evaluating a time-lagged coupling statistic '
     'between the corrected residual time-series of pairs of candidate '
     'stations, over lags exceeding the timing tolerance to which the said '
     'stations are synchronised; attributing an elevated residual at a single '
     'candidate station, unaccompanied by coupling to any other candidate '
     'station, to an individual anomaly; and attributing coupling between a '
     'pair of candidate stations, persisting over a plurality of separate '
     'occasions and exceeding a baseline value of the same statistic measured '
     'on that same pair during sanctioned activity, to coordination between '
     'the candidates at those stations.'),
    ('Claim 25.',
     'The method of Claim 23, wherein the predictive model comprises an '
     'encoder and a predictor trained jointly under an objective comprising a '
     'prediction-error term and a variance-and-covariance regularisation term '
     'applied to the embedding.'),
    ('Claim 26.',
     'The method of Claim 23, further comprising aggregating the '
     'integrity-violation score over the whole of the monitored session for '
     'each of a plurality of stations, ranking the stations by aggregated '
     'score, and referring a predetermined number of highest-ranked stations '
     'for human inspection.'),

    ('D. Deployment and application claims', None),
    ('Claim 27.',
     'The installation of Claim 11, wherein the said processing arrangement '
     'is embodied at an edge processing unit located at each station, at a '
     'venue-local aggregation server receiving derived features from a '
     'plurality of stations, at a remote server, or in any combination '
     'thereof; and wherein raw acoustic, optical and radio signals are '
     'reduced to derived features at the point of acquisition such that only '
     'derived features or residual values are transmitted beyond the venue.'),
    ('Claim 28.',
     'The installation of Claim 11, deployed in an examination hall, a '
     'professional certification or licensing test centre, a secure interview '
     'or vetting room, a recruitment or aptitude testing facility, a defence '
     'or public-service selection examination, a controlled-access screening '
     'area, or a multi-seat remote-proctoring installation.'),
    ('Claim 29.',
     'The method of Claim 24, performed in any environment recited in '
     'Claim 28.'),
]


def sec10(doc):
    h1(doc, '10. Aspects of the Invention Requiring Protection (Claims)')
    para(doc,
         'The following elements are considered novel and inventive and are '
         'proposed for protection. Claims 1, 11, 17, 19, 23 and 24 are '
         'independent. The set is drafted on three principles.')
    para(doc,
         'The label-free training of the model is a process characteristic, '
         'and process characteristics carry their full weight in method '
         'claims but are not inspectable in a deployed system. The method '
         'claims of Part C therefore recite it as an active limitation, while '
         'the system and installation claims are distinguished instead by '
         'runtime properties of the working apparatus — per-station and '
         'per-session calibration, an instrumented station held unoccupied, '
         'a bounded timing tolerance, a per-pair baseline, and a change of '
         'acquisition state — each of which can be observed in the '
         'installation as it runs.',
         lead='First.')
    para(doc,
         'Common-mode rejection, the unoccupied reference station and the '
         'bound on timing tolerance are recited as positive elements of the '
         'independent installation claims rather than as optional '
         'refinements. Section 8 measures a coordination condition evaluated '
         'without them at chance or near it; a claim that made them optional '
         'would extend to an arrangement that the measurements of Section 8 '
         'place at chance.',
         lead='Second.')
    para(doc,
         'No claim to a computer-readable medium is included. Such a claim is '
         'routinely refused in Indian practice, and it would contradict the '
         'framing of the entire set, which is directed to an installation of '
         'physical transducers at fixed positions in a room and to the '
         'physical acts performed upon them. This omission is deliberate and '
         'should not be reversed at drafting.',
         lead='Third.')
    for lead, body in CLAIMS:
        if body is None:
            h2(doc, lead)
        else:
            para(doc, body, lead=lead)
    figure(doc, 'fig11.png',
           'Figure 11. Claim dependency map. Four groups of apparatus claims '
           'with their dependents, together with the method and deployment '
           'claims; the annotation beneath each group records how strong the '
           'inventor takes that group to be.', width=6.5)
    para(doc,
         'The embodiment described at Section 7.1(h) — training against '
         'corrupted or temporally shuffled futures as explicit negative '
         'examples — is deliberately excluded from the claim set above, '
         'as it has not been reduced to practice. It is nevertheless '
         'disclosed in the specification so that priority is preserved should '
         'it be claimed in a later continuation or subsequent application.',
         lead='Note on scope.')


def sec11(doc):
    h1(doc, '11. Technology Readiness Level (TRL)')
    para(doc,
         'The invention has been formulated as a specific architecture at '
         'Sections 6 and 7, validated as a self-supervised method on a '
         'parametric simulation of station-level signals at Section 8.1, and '
         'validated as a signal-processing arrangement on a public corpus of '
         'real multi-node sensor recordings at Section 8.2. No physical '
         'prototype has been constructed and no laboratory trial on the '
         'transducers of this invention has been performed; the hardware '
         'embodiment and the bench programme that would constitute such a '
         'trial are specified prospectively at Section 9. Readiness is '
         'therefore assessed at TRL 3, experimental proof of concept, as '
         'marked below. The measurements of Section 8.2 do not by themselves '
         'confer TRL 4: they validated the arrangement on a corpus of the '
         'right shape and the wrong physics, with no acoustic transducer, no '
         'electromagnetic sensing, no desk and no candidate involved. '
         'Successful completion of tests B1 to B8 would support an assessment '
         'of TRL 4, and no higher.')
    t = doc.add_table(rows=4, cols=9)
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    bands = ['Research'] * 3 + ['Development'] * 3 + ['Deployment'] * 3
    lvls = ['TRL %d' % i for i in range(1, 10)]
    desc = ['Basic principles observed', 'Technology concept formulated',
            'Experimental proof of concept', 'Technology validated in lab',
            'Validated in relevant environment',
            'Demonstrated in relevant environment',
            'Prototype in operational environment',
            'System complete and qualified',
            'Proven in operational environment']
    ticks = ['✔'] * 3 + [''] * 6
    for ri, row in enumerate((bands, lvls, desc, ticks)):
        for ci, val in enumerate(row):
            c = t.rows[ri].cells[ci]
            c.text = ''
            pp = c.paragraphs[0]
            pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pp.paragraph_format.space_after = Pt(2)
            _run(pp, val, size=8.0, bold=(ri in (0, 1, 3)))
        for ci in range(9):
            t.rows[ri].cells[ci].width = Inches(0.7)
    tcaption(doc, 'Table 13: Technology Readiness Level Assessment')
    para(doc, 'Current TRL: Level 3 — Experimental Proof of Concept.')


def sec12(doc):
    h1(doc, '12. Note on Filing')
    para(doc,
         'Nine matters are flagged for the IPR & TT Cell and for the drafting '
         'agent. This note is internal. Section 12 in its entirety, and the '
         'candid statements of limitation in Sections 8 and 9, are written '
         'for the Cell and not for the Controller.')

    para(doc,
         'Subject-matter eligibility is the primary anticipated objection, '
         'and it should be expected before any objection on novelty or '
         'inventive step. The response is prepared and is ordered '
         'deliberately. The strongest argument, and the one to press first, '
         'is that the installation brings about a change in the physical '
         'operating state of apparatus: upon a measured relation between the '
         'outputs of two physically separate transducer sets satisfying the '
         'coordination condition, the sensing assemblies of those two '
         'stations, and of no others, are switched into a second acquisition '
         'state for a bounded interval. That is an effect upon the operation '
         'of the apparatus itself and is independent of the analytical '
         'content of any model. Second, the installation recites a physical '
         'element with no counterpart in the cited art: a station of like '
         'construction deliberately held unoccupied, whose transducer output '
         'forms part of the reference. Third, the detection is of a physical '
         'condition — acoustic and electromagnetic energy emitted by '
         'concealed devices — from transducer measurements, and the '
         'detector is calibrated automatically to the ambient physical '
         'conditions of a specific station without labelled data. Fourth, the '
         'acoustic signal chain reduces the waveform to an envelope and then '
         'to order statistics before anything leaves the station, which '
         'reduces the data leaving the venue by orders of magnitude and does '
         'so as a property of the circuit rather than of the software.',
         lead='First: subject-matter eligibility.')
    para(doc,
         'The Delhi High Court in Ferid Allani v. Union of India (W.P.(C) '
         '7/2014, decision dated 12 December 2019) held that the exclusion '
         'attaches only to a computer programme per se, and that an invention '
         'exhibiting a technical effect or a technical contribution falls '
         'outside it; the same reasoning has since been applied in Blackberry '
         'Limited v. Controller of Patents and Designs and in Microsoft '
         'Technology Licensing LLC v. Assistant Controller of Patents and '
         'Designs. The Revised Guidelines for Examination of Computer Related '
         'Inventions, 2025, issued by the Controller General on 29 July 2025 '
         'and superseding the 2017 Guidelines, set out a step-wise assessment '
         'methodology, add a dedicated part addressing inventions in '
         'artificial intelligence and machine learning, and confirm that '
         'system and method claims are both allowable in independent format '
         'where fully supported by the specification. The complete '
         'specification should be drafted so that the hardware limitations of '
         'Claims 11, 17, 19 and 24 are substantive rather than nominal, and '
         'so that each technical effect above appears in the description as '
         'ordinary technical writing and not as argument. A registered patent '
         'agent should verify this alignment before filing.')
    para(doc,
         'The claim language has been drafted by the inventor, broad at the '
         'independent level and progressively narrowed through the '
         'dependents. Twenty-nine claims is more than official fees comfortably '
         'accommodate, and the agent will prune. The inventor’s ranking is as '
         'follows. Claims 11, 19 and 24 are the position; do not concede '
         'them. Claims 12, 13, 14, 17, 18, 20 and 22 are the dependents worth '
         'keeping, each being a measured or structural fallback if an '
         'independent is narrowed. Claim 1 is the weakest on eligibility and '
         'is the first to narrow if the set must shrink; its dependents 3, 4, '
         '6 and 9 are worth more than the claim they hang from. Claim 16, the '
         'graph and connected-component embodiment, corresponds closely to '
         'entry 11 of Section 3 and differs only in the quantity from which '
         'the edges are derived; it is the weakest of the cross-station '
         'dependents and is the one to concede if pressed. A defensible '
         'ten-claim core would be 11, 12, 13, 14, 17, 18, 19, 20, 22 and 24.',
         lead='Second: claim breadth and the order of concession.')
    para(doc,
         'The invention stands at TRL 3. Section 8.1 reports simulation on a '
         'generative model, with its sample-size and single-run limits '
         'stated. Section 8.2 reports measurement on a real public corpus, '
         'but that corpus is server telemetry rather than instrumented desks, '
         'and the coupled exchange and the venue-wide event within it are '
         'synthetic injections. Section 9 is prospective throughout and '
         'reports no measurement. No experimental result on the transducers '
         'of this invention is asserted anywhere in this disclosure, and '
         'nothing in it should be represented to any external party as such.',
         lead='Third: state of reduction to practice.')
    para(doc,
         'An earlier revision argued that one normal-only model shared across '
         'the stations made their residuals commensurable and that this was '
         'the source of the cross-station channel. Measurement on a public '
         'MIT-licensed corpus contradicts that in direction, on the '
         'inventor’s own mechanism, in a few minutes of compute. The assertion '
         'and the simulated cross-station figures produced under it have been '
         'withdrawn from Sections 4.1, 7, 8 and 10. The drafting agent must '
         'not reinstate shared-model language anywhere, and must not restore '
         'the withdrawn simulated cross-station figures alongside the '
         'measured ones. The correction is recorded here rather than '
         'concealed, because the position it leaves is stronger: the '
         'invention now teaches away from the expedient a skilled person '
         'would adopt, and gives the measured reason for doing so.',
         lead='Fourth: a withdrawn assertion, and an instruction.')
    para(doc,
         'The subject matter of this disclosure develops earlier unpublished '
         'work of the same inventor on a multi-sensor examination desk '
         'carrying acoustic and electromagnetic sensing. That earlier work '
         'has not been published, exhibited, demonstrated outside the '
         'institution, or otherwise made available to the public, and no '
         'application has been filed in respect of it. It is accordingly not '
         'prior art — neither under section 2(1)(l) nor, no application '
         'existing, under section 13(1)(b) — and it is deliberately not '
         'listed in Section 3. It was listed in an earlier revision, and that '
         'was an error: characterising one’s own unpublished work as prior, in '
         'one’s own specification, is an applicant admission that manufactures '
         'prior art which does not otherwise exist, and it would have given '
         'away for nothing the two sensing modalities on which Claims 3 and 4 '
         'depend. It is recorded here so that the Cell has the development '
         'history and so that any decision to publish it is taken knowing the '
         'effect on this application.',
         lead='Fifth: development history, and why it is not in Section 3.')
    para(doc,
         'No part of this work has been publicly disclosed. No preprint, '
         'conference submission, demonstration, or public repository exists, '
         'and none will be made until a priority date is secured, since '
         'public disclosure prior to filing would prejudice novelty in '
         'jurisdictions without a grace period. The evidence campaign of '
         'Section 8.2 was run privately and its code and results are '
         'unpublished; they must remain so. The things that count as public '
         'disclosure are broader than is generally expected, and one slip '
         'destroys novelty in most jurisdictions with no remedy: a conference '
         'paper, poster or abstract; a project exhibition, demonstration day '
         'or open house; a thesis or project report deposited in a library or '
         'institutional repository; a public code repository; a preprint; a '
         'video; a demonstration to anyone outside a confidentiality '
         'obligation; a funding application that becomes public. Internal '
         'submission to the VIT IPR & TT Cell is not disclosure. If a '
         'prototype is built under Section 9, any demonstration should be '
         'deferred or conducted under a written confidentiality undertaking.',
         lead='Sixth: absence of public disclosure.')
    para(doc,
         'Six independent claims will attract an objection that they lack a '
         'single general inventive concept. The position to take is that they '
         'share one: a relational quantity between the prediction residuals '
         'of stations modelled independently of one another, made meaningful '
         'by removing a component common to the venue, part of which is '
         'measured at a station carrying no candidate. Claim 11 constrains '
         'the structure that earns that quantity, Claim 17 constrains the '
         'reference against which it is judged, Claim 19 constrains what it '
         'may do, and Claims 23 and 24 are the corresponding methods. If the '
         'objection is pressed, prosecute Claims 11 and 19 in the parent and '
         'file Claim 17 as a divisional, because 11 and 19 carry the physical '
         'limitations that answer the eligibility objection recorded above. '
         'Claim 1 is a different invention in substance and can be surrendered '
         'or filed separately without damaging the rest.',
         lead='Seventh: unity of invention.')
    para(doc,
         'The same inventor has a co-pending disclosure directed to a '
         'desk-mounted examination-integrity node that anchors a timing '
         'relation to a photometrically measured display transition and '
         'physically interrupts a keyboard data path. The two must be read '
         'side by side before either is filed, and the boundary is this: that '
         'disclosure claims a timing relation between an onset anchor and a '
         'response at one station, together with interruption of a data path; '
         'this one claims a relation between two stations, together with a '
         'change in the acquisition state of transducers. Neither should be '
         'allowed to drift into the other. Two specific points of contact '
         'need watching. Both disclosures now recite reduction of an acoustic '
         'signal to an envelope before digitisation, here at Claim 22 and '
         'there as a privacy limitation; the recitations should be kept '
         'distinct in scope, and the agent should decide which filing carries '
         'the broader one. And whichever application is filed first is '
         'citable against the other under sections 13(1)(b) and 29, so the '
         'filing order is a decision to be taken deliberately rather than by '
         'accident of readiness.',
         lead='Eighth: the co-pending disclosure of the same inventor.')
    para(doc,
         'This note must not enter the filed specification. A specification '
         'that argues its own patentability, names the exclusion it seeks to '
         'avoid, or characterises its own validation as preliminary invites '
         'the examiner to adopt the applicant characterisation and can be '
         'read as an admission. The complete specification should instead '
         'demonstrate the technical effects through the ordinary work of the '
         'description — naming the transducers, the signals they carry, '
         'the physical quantities measured, and the operations performed upon '
         'them — and leave the legal characterisation to prosecution. '
         'Component costs for the Section 9 build have been kept out of the '
         'body for the same reason: an applicant’s own statement that a build '
         'is inexpensive and ordinary is quotable against inventive step. At '
         'Indian retail prices current at the date of this disclosure the '
         'five-node configuration of Section 9 is of the order of twenty-five '
         'to thirty-five thousand rupees exclusive of enclosures, cabling and '
         'labour; that figure is for the Cell’s internal costing and belongs '
         'nowhere else.',
         lead='Ninth: this note is internal.')


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
    for f in (sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9, sec10,
              sec11, sec12):
        f(doc)

    endp = doc.add_paragraph()
    endp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    endp.paragraph_format.space_before = Pt(18)
    _run(endp, '————— END OF THE DOCUMENT '
         '—————', size=11, bold=True)

    cp = doc.core_properties
    cp.author = 'VIT IPR & TT Cell'
    cp.last_modified_by = 'VIT IPR & TT Cell'
    cp.title = 'Label-Free Malpractice and Collusion Detection - IDF-B'
    cp.comments = ''
    cp.category = ''
    cp.keywords = ''

    out = os.path.join(
        HERE, 'IDF-B_LabelFree_Malpractice_Detection_rev7.docx')
    doc.save(out)
    print('wrote', out)


if __name__ == '__main__':
    build()
