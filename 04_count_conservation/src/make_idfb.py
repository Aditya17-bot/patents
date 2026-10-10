"""Build the IDF-B disclosure for count-derived conservation constraints.

Format: the inventor's accepted CausalInterlock IDF-B (twelve numbered sections, masthead,
styled tables, captioned figures, claim groups A-D with a claim-tree figure). Its layout
helpers are imported from that generator unchanged, so the two documents cannot drift
apart in style.

Every measured number is read from results/*.json at build time. A figure with no results
file behind it is written as TBD. Nothing here describes an effect on anything other than
a technical system (CLAUDE.md, drafting rule 1).
"""
import json
import os
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
REF = r"C:\adi\patents\01_02_infosec\IDF-B_CausalInterlock"
sys.path.insert(0, REF)
import build_idfb as B                                            # noqa: E402

B.FIG = os.path.join(ROOT, "patent", "figures")
OUT = os.path.join(ROOT, "patent", "IDF-B_Count_Derived_Conservation_Constraints.docx")

h1, h2, para, figure, table, bullets, _run = (B.h1, B.h2, B.para, B.figure, B.table,
                                              B.bullets, B._run)
TBD = "TBD"


def load(name):
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def case(d, mode, mag):
    for c in (d or {}).get("cases", []):
        if c["mode"] == mode and abs(c["magnitude"] - mag) < 1e-9:
            return c
    return None


def pct(x, nd=1):
    return ("%." + str(nd) + "f %%") % (100.0 * x)


def sci(p):
    """p-value for print: 0.041, or 2.9 x 10^-6 below 0.001."""
    if p >= 0.001:
        return "%.3f" % p
    m, e = ("%.1e" % p).split("e")
    return "%s × 10^%d" % (m, int(e))


def net_removed(e):
    """Share of total absolute error removed, after charging wrong corrections."""
    before = e["trials"] * e["mae_before"]
    after = (e["trials"] * e["mae_after"]["auto"]
             + e["innocent_corrections"] * e["innocent_mae_introduced"])
    return 1.0 - after / before if before else 0.0


YF_CASES = (("scale", 0.95), ("scale", 1.05), ("offset", -15.0), ("offset", 15.0),
            ("stuck", 0.0))


def yf_case(d, mode, mag):
    for c in d["cases"]:
        if c["mode"] == mode and abs(c["magnitude"] - mag) < 1e-9:
            return c
    return None


def yf_range_of(ds):
    ours = [yf_case(d, m, g)["ours_recovered"]["named_correctly"] for d in ds
            for m, g in YF_CASES]
    theirs = [yf_case(d, m, g)["yf_surveyed"]["named_correctly"] for d in ds
              for m, g in YF_CASES]
    return min(ours), max(ours), min(theirs), max(theirs)


def claim(doc, n, text, independent=False):
    lead = "Claim %d%s." % (n, " (independent)" if independent else "")
    para(doc, text, lead=lead, indent=0.28, size=10.5)


def build():
    v25 = load("discovery_v2_full_M25_A.json")
    v1 = load("discovery_v2_M1_A.json")
    a25 = load("map_audit_full_M25_A.json")
    a1 = load("map_audit_M1_A.json")
    fs = load("faults_fpcontrol_M25_A.json")
    fr = load("faults_recovered_M25_A.json")
    conf = load("confidence_full_M25_A.json")
    cr25, cr1 = load("confidence_recovered_M25_A.json"), load("confidence_recovered_M1_A.json")
    cs1 = load("confidence_surveyed_M1_A.json")
    irr = load("irreconcilable_test.json")
    harm = load("harm_test.json")
    recur = load("recurrence.json")
    rfilt = load("recurrence_filter.json")
    missing = [n for n, o in (("certified M25", cr25), ("certified M1", cr1),
                              ("certified surveyed M1", cs1), ("irreconcilable", irr),
                              ("harm test", harm), ("recurrence", recur),
                              ("recurrence filter", rfilt)) if o is None]
    if missing:
        raise SystemExit("results absent, refusing to build with invented figures: %s"
                         % ", ".join(missing))
    gen = load("generalisation.json")
    ex = load("idfb_fig04_example.json")
    old = load("v1_slip_recall_M25_A.json")
    missing = [n for n, o in (("discovery_v2 M25", v25), ("discovery_v2 M1", v1),
                              ("map_audit M25", a25), ("map_audit M1", a1),
                              ("faults surveyed", fs), ("faults recovered", fr),
                              ("confidence", conf), ("fig04 example", ex),
                              ("v1 slip recall", old)) if o is None]
    if missing:
        raise SystemExit("results absent, refusing to build with invented figures: %s"
                         % ", ".join(missing))

    abl = load("ablation_ranking.json")
    base = load("baseline_structure.json")
    grid = load("baseline_grid.json")
    sparse = load("baseline_sparse.json")
    cor25, cor1 = load("correction_M25_A.json"), load("correction_M1_A.json")
    mab = load("map_audit_baseline.json")
    jun = load("discovery_v2_june_M25_A.json")
    rf25, rf1 = load("real_faults_full_M25_A.json"), load("real_faults_M1_A.json")
    rfu, rfx = load("real_faults_followup.json"), load("real_fault_examples.json")
    rfm = load("real_faults_months.json")
    yf1, yf25 = load("yf_compare_M1_A.json"), load("yf_compare_full_M25_A.json")
    yfs = load("yf_sanity_M1_A.json")
    missing = [n for n, o in (("real faults M25", rf25), ("real faults M1", rf1),
                              ("real faults follow-up", rfu),
                              ("real fault examples", rfx), ("four-month study", rfm),
                              ("Yang-Fan M1", yf1), ("Yang-Fan M25", yf25),
                              ("Yang-Fan sanity", yfs)) if o is None]
    if missing:
        raise SystemExit("results absent, refusing to build with invented figures: %s"
                         % ", ".join(missing))
    diag = load("rmse_diagnosis_M1_A_vertexfallback.json")
    old25 = load("discovery_v2_full_M25_A_vertexfallback.json")
    old1 = load("discovery_v2_M1_A_vertexfallback.json")
    missing = [n for n, o in (("grid baseline", grid), ("sparse baseline", sparse),
                              ("correction M25", cor25), ("correction M1", cor1),
                              ("map audit baseline", mab), ("rmse diagnosis", diag),
                              ("v2 M25 vertex fallback", old25),
                              ("v2 M1 vertex fallback", old1)) if o is None]
    if missing:
        raise SystemExit("results absent, refusing to build with invented figures: %s"
                         % ", ".join(missing))
    if abl:
        a_m25, a_m1 = abl["corridors"]["M25"], abl["corridors"]["M1"]
        abl_sentence = (
            "In a controlled comparison in which only the ranking is changed and every "
            "other stage and constant is held fixed, ranking against the detector's own "
            "counts recovers %d of %d surveyed slip-road junctions on the reference "
            "corridor and %d of %d on the replication corridor; ranking against the "
            "mainline-pair residual recovers %d and %d (Section 8.2)."
            % (a_m25["target"]["slip_recovered"], a_m25["slip_total"],
               a_m1["target"]["slip_recovered"], a_m1["slip_total"],
               a_m25["residual"]["slip_recovered"], a_m1["residual"]["slip_recovered"]))
    else:
        abl_sentence = ("The controlled comparison in which only the ranking is changed "
                        "is TBD.")
    stab = load("stability_split_half.json")
    c25, c1 = v25["configs"], v1["configs"]

    def yf_range():
        return yf_range_of((yf25, yf1))
    rs25, rs1 = v25["recall_by_size"], v1["recall_by_size"]
    slips25 = sum(rs25[s]["recovered"] for s in rs25 if s != "2")
    slipt25 = sum(rs25[s]["of"] for s in rs25 if s != "2")
    slips1 = sum(rs1[s]["recovered"] for s in rs1 if s != "2")
    slipt1 = sum(rs1[s]["of"] for s in rs1 if s != "2")
    k25, k1 = a25["kinds"], a1["kinds"]
    ctl25, ctl1 = a25["control"], a1["control"]

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = B.BODY_FONT
    st.font.size = Pt(11)
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Inches(0.9)
    sec.top_margin = sec.bottom_margin = Inches(0.85)
    B.running_heads(sec)
    B.letterhead(doc)

    # ============================================================== 1
    h1(doc, "1. Title of the Invention")
    para(doc,
         "A Method and System for Recovering Road-Network Flow-Conservation Relations "
         "from Detector Counts Alone and Imposing them as Hard Constraints to Reconstruct "
         "Missing Traffic Counts and Correct a Miscounting Detector.")

    # ============================================================== 2
    h1(doc, "2. Field / Area of Invention")
    para(doc,
         "The present invention relates to the processing of measurement data produced by "
         "networks of fixed roadside vehicle-counting detectors, such as inductive-loop "
         "detectors on a motorway carriageway and its entry and exit slip roads. More "
         "particularly, it pertains to a method in which the conservation relations that "
         "hold between the counts of such detectors, namely which detectors are joined by "
         "a junction and whether each slip road adds vehicles to the carriageway or removes "
         "them, are recovered from the recorded counts themselves, without any network map, "
         "junction register, site naming convention or coordinates, and in which the "
         "recovered relations are then imposed as hard two-sided inequality constraints on "
         "the same dataset. The constraints are used to reconstruct records the detectors "
         "failed to report, to identify a detector that is miscounting and correct its "
         "output, and to test a supplied network map for errors.")
    para(doc,
         "The principal embodiment described herein is a motorway corridor instrumented "
         "with mainline and slip-road loop detectors reporting fifteen-minute counts. The "
         "invention is not limited to that embodiment. It applies to any detector network "
         "in which a vehicle entering a section must leave it again, including urban "
         "arterial networks, tunnel and bridge approaches, and managed-motorway schemes, "
         "and to archives of counts recorded by such networks in the past as well as to "
         "live feeds.")
    para(doc,
         "The technical problem is one of the measuring instruments and the record they "
         "produce. Roadside detectors fail to report in some intervals, through loop "
         "failure or loss of the communication link; they drift, counting a steady "
         "fraction too many or too few vehicles; they stick at a constant; and the metadata "
         "that says how they are connected, where it exists at all, cannot be trusted "
         "(Section 4). The record the instruments produce is then incomplete and "
         "internally inconsistent: more vehicles leave a stretch of road than enter it. "
         "The invention addresses that problem by technical means. It recovers, from the "
         "instruments' own counts, the physical conservation relations that connect them, "
         "and uses those relations to restore the absent records and to correct the "
         "records of an instrument that is miscounting, so that the stored record of the "
         "instruments again obeys the conservation of vehicles. The mathematics serves "
         "that process and is not claimed on its own.")

    # ============================================================== 3
    h1(doc, "3. Prior Patents and Publications from Literature")
    para(doc,
         "The following table summarises the closest known prior art and identifies the gap "
         "addressed by the present invention. Entries 1 to 3 are in-domain traffic-count "
         "reconciliation. Entries 4 to 7 are data reconciliation and fault identification "
         "in other measurement domains, which an examiner will reasonably combine. Entries "
         "8 to 13 are methods that recover structure from data, and entry 8 is the closest "
         "art to the invention as a whole. Entries 14 to 16 are the remaining patent "
         "references located, each addressed directly. Entries 17 to 20 were located by a "
         "later search of the electricity-distribution and learned-traffic-graph "
         "literature; entry 17 is the closest analogue outside traffic and is run on the "
         "same counts in Section 8.2. Entries 21 and 22 were located by a search directed "
         "at the claims themselves: entry 21 is the closest art to Claim 13, entry 22 to "
         "the signed coefficients of Claim 1. Entry 23 was located in Espacenet "
         "(Table A).")
    pa = [
        ["1", "de Souza (2019), Freeway Loop Detector Data Reconciliation Based on Vehicle "
              "Conservation", "2019 / thesis",
         "Convex optimisation correcting freeway loop counts subject to vehicle "
         "conservation between stations, with occupancy-derived bounds.",
         "The station layout is an input. Conservation is imposed between stations the "
         "analyst has already placed in order; nothing in it establishes which detectors "
         "are joined, in what order, or with what sign."],
        ["2", "Yin, Sun, Jin, Xin (2017), l1-minimisation method for link flow correction",
         "2017 / journal",
         "Hard flow conservation on network link flows with an analytic account of which "
         "links are recoverable.",
         "Operates on a given link-node incidence matrix. Conceded as disclosing hard "
         "conservation constraints in this domain; what it does not do is produce the "
         "incidence matrix."],
        ["3", "Vanajakshi and Rilett (2004), TRR 1870; Cheevarunothai, Wang and Nihan "
              "(2006), TRR 1945", "2004-2006 / journal",
         "Conservation of vehicles across adjacent loop detectors to diagnose systematic "
         "error, and identification of drifted loop sensitivity.",
         "Adjacent detectors are identified by the analyst. Conceded as disclosing "
         "conservation-based diagnosis of a miscounting loop on a known layout."],
        ["4", "Process data reconciliation: US 5,504,692; US 10,310,497; WO 2016/114736 A1",
         "patents",
         "Weighted least-squares adjustment of measured flows subject to mass balance, "
         "with gross error detection.",
         "Defined on a given flowsheet. The balance equations are fixed throughout; the "
         "unknowns are unmeasured flows, not the constraint structure."],
        ["5", "Narasimhan and Mah (1987), AIChE J. 33(9):1514; Bagajewicz and Jiang (1998), "
              "equivalency of gross errors", "1987-1998 / journal",
         "Detection, localisation, type discrimination and magnitude estimation of gross "
         "errors from mass-balance residuals.",
         "Conceded in full for a known model. Every method in this line asks which sensor "
         "disagrees with a surveyed model; none recovers the model from the sensors."],
        ["6", "Liu, Wu and Lun (1992), IEEE Trans. Power Syst. 7(1):81; Zhu and Abur (2006), "
              "21(2):586", "1992-2006 / journal",
         "Identification of network parameter errors in power-system state estimation.",
         "Suspects a parameter of a known admittance matrix. The branch set, which is the "
         "analogue of the junction set here, is given."],
        ["7", "Balzano and Nowak (2007), blind calibration of sensor networks; Dorffer et "
              "al. (arXiv:1805.11999)", "2007-2018 / conf.",
         "Recovery of per-sensor gain and offset without a calibrated reference.",
         "Exploits smoothness or subspace structure of the sensed field, not an exact "
         "integer conservation relation, and recovers no connectivity."],
        ["8", "Narasimhan and Shah (2008), Control Eng. Practice 16, IPCA; Rajeswaran and "
              "Narasimhan (2015), network topology identification using PCA "
              "(arXiv:1506.00438); Learning conserved networks from flows (arXiv:1905.08716)",
         "2008-2019 / journal",
         "Recovery of the constraint matrix of a flow-conserving network, and of the "
         "measurement-noise covariance, from flow data alone; graph-theoretic recovery of "
         "the incidence matrix.",
         "The closest art: it recovers conservation structure from measurements, and the "
         "general statement that this cannot be done is not made here. It operates on a "
         "matrix of simultaneously observed flows and returns a real-valued basis of the "
         "constraint space. In its published form it does not return individual relations with coefficients of "
         "+1 or -1 naming the detectors of one junction, and it is not described for "
         "records absent in different intervals at different detectors. Whether it "
         "succeeds on the data of Section 8 is %s."
         % ("measured in Section 8.2" if load("baseline_structure.json")
            else "not yet measured (Table 7)")],
        ["9", "Mallat and Zhang (1993), matching pursuit; Pati, Rezaiifar and "
              "Krishnaprasad (1993), orthogonal matching pursuit; Efron et al. (2004), LARS",
         "1993-2004 / journal",
         "Greedy selection of the regressor most correlated with the current residual.",
         "Conceded as the general principle behind ranking candidates against a residual. "
         "The contribution claimed is the residual chosen: that of a pair of mainline "
         "detectors bracketing one junction, which is supplied by the ordering stage. "
         "Run on the same data, it recovers few slip-road junctions (Table 3b)."],
        ["10", "Margolin et al. (2006), ARACNE, BMC Bioinformatics 7(Suppl 1):S7",
         "2006 / journal",
         "Removes the weakest edge of every triangle in a gene co-expression network "
         "(data-processing inequality).",
         "Conceded as the same pattern as the ordering stage, applied to mutual "
         "information between genes. Not applied to count agreement between detectors, "
         "nor used to supply adjacent pairs for a junction search."],
        ["11", "Brunton, Proctor and Kutz (2016), SINDy, PNAS", "2016 / journal",
         "Sparse regression recovering governing equations from measurements.",
         "Makes recovery of a relation by sparse regression old in the abstract, and is "
         "conceded as such. Its candidate library is chosen by the analyst; it contains "
         "no mechanism for finding a weakly varying term hidden behind a dominant one, "
         "which is the problem the junction stage of Section 7 solves."],
        ["12", "TRAFFIC-PDE-LEARN (arXiv:2505.00904); Castillo et al. (2015), J. Sensors, "
              "flow observability review", "2015-2025 / journal",
         "Discovery of the governing equation of traffic dynamics; observability posed "
         "through the network incidence matrix.",
         "The incidence matrix is the input to this literature and never its output."],
        ["13", "Inferring and Improving Street Maps (CACM); Road Network Fusion "
               "(arXiv:1802.02351)", "2018-2020 / journal",
         "Recovery of road topology.",
         "From GPS traces and imagery. No work located recovers connectivity from counts, "
         "and inductive loops carry no route information at all."],
        ["14", "US 6,850,840 B1, method for describing and generating road networks",
         "2005 / patent",
         "Inserts contour points between known nodal points from position data.",
         "Geometry refinement on a given network, from GPS. Read to claim 1 and ruled "
         "out."],
        ["15", "FlowSymm (Demirci, Bullo, Swami, Singh, arXiv:2601.22317)", "2026 / preprint",
         "Completes missing edge flows while exactly respecting local conservation: a "
         "minimum-norm divergence-free completion on the given graph, refined by "
         "attention-selected symmetry actions; tested on traffic, power and bike flows.",
         "Conceded as exact conservation in flow completion. The graph, and so every "
         "conservation relation, is given; nothing recovers it, and conservation is exact "
         "equality rather than calibrated two-sided bands measured from the counts."],
        ["16", "US 11,093,463 B2, missing value imputation device", "2021 / patent",
         "Selects the number of multiple-imputation repetitions to fit a time budget.",
         "No physical constraint and no network. Not relevant."],
        ["17", "Low-voltage topology identification by energy conservation: constrained "
               "least squares with graph theory, Soft Computing (2022), doi "
               "10.1007/s00500-022-07151-3; regression with knowledge reasoning, Energies "
               "17(7):1762 (2024); CN111628494B", "2022-2024 / journal, patent",
         "Recovers which smart meters sit under a transformer or branch from the identity "
         "parent energy = sum of children, fitted by bounded least squares or Lasso on "
         "meter data; coefficients read as 0/1 membership.",
         "Closest analogue: conservation-based structure recovery from meter data. The "
         "parent meter is known and each fit asks only which meters belong to it; "
         "coefficients state membership, not direction, so a relation in which one "
         "member adds flow and another removes it is not the form fitted; meters are "
         "not ordered. Run on the counts with every detector tried as parent, it "
         "recovers few slip-road junctions (Table 3b)."],
        ["18", "US 11,205,901 B2, topology of a distribution network from metering data",
         "2021 / patent",
         "Sensitivity coefficients between meter currents and voltages identify the "
         "connection of meters, with the head-end meter at the slack node.",
         "Uses voltage-current sensitivity, not an integer conservation relation, and a "
         "known reference meter. No reconstruction under the recovered structure."],
        ["19", "US 9,816,836 B2 (meter-to-transformer mismapping); US 11,916,380 B2 "
               "(correcting a meter's recorded location)", "2017-2024 / patents",
         "Detect that a meter is recorded against the wrong transformer, and propose the "
         "correct one, from measured data.",
         "Concede the concept of checking a network register against measurements. They "
         "work by voltage correlation, not by conservation, and recover no relations. "
         "This is why the map audit of the present disclosure is claimed only as a "
         "dependent use (Claims 12 and 20)."],
        ["20", "Wu et al. (2019), Graph WaveNet, IJCAI", "2019 / conf.",
         "Learns an adaptive adjacency between traffic sensors from data, with no road "
         "graph supplied.",
         "A dense, real-valued, learned dependency used inside a neural forecaster: not a "
         "conservation relation, not signed, not explainable, and not imposed as a "
         "constraint. Defeats any broad statement that traffic connectivity has never "
         "been inferred from sensor data, and no such statement is made."],
        ["21", "Yang, Yang and Fan (2019), Networked sensor data error estimation, "
               "Transportation Research Part B 122:20-39; Yang (2022), dissertation, UC "
               "Davis; Lu, Varaiya, Horowitz and Palen, faulty loop data analysis / "
               "correction and loop fault detection (California PATH review)",
         "2008-2022 / journal",
         "Estimates a multiplicative bias per traffic sensor from nodal flow balance by "
         "the generalised method of moments, tests sensor health, and corrects the "
         "observed counts using the estimated bias.",
         "Closest art to Claim 13, conceded for a known network: the node-link adjacency "
         "matrix is an input. The correction here is made on relations recovered from the "
         "counts, the faulty detector is named from the pattern over its several "
         "recovered relations, and the fault is typed proportional or constant before it "
         "is inverted."],
        ["22", "US 9,053,519 B2 (TaKaDu), analysing GIS data to improve monitoring of "
               "water distribution networks", "2015 / patent (priority 2012)",
         "For a metered zone whose boundary meters are known from GIS, chooses the +/- "
         "direction of each meter's flow in the zone's mass balance from the meter data, "
         "by the plausibility of the resulting consumption curve.",
         "Concedes that the sign of a flow term in a conservation sum can be chosen from "
         "data. The zone and its members are given by GIS; the signs are selected for a "
         "plausible net consumption, not for closure within a noise limit measured from "
         "the data; nothing is ordered or recovered, and no reconstruction under the "
         "result is described."],
        ["23", "CN102169630A (B), quality control method of road continuous traffic "
               "flow data", "2011 / patent",
         "Identifies a faulty fixed traffic-data acquisition device by a pattern test "
         "built on cross-sectional flow conservation, then completes invalid and missing "
         "data from same-period history and adjacent loop data.",
         "Conservation-based fault identification and repair on a known arrangement of "
         "sections and adjacent loops, in the class of entry 3. The spatial relation "
         "between devices is an input; nothing recovers which devices are joined, in what "
         "order or with what sign, and the repair is by history and neighbours, not by "
         "inverting a fault fitted across recovered relations."],
    ]
    table(doc, ["#", "Reference", "Year / type", "Core contribution",
                "Limitation with respect to the present invention"],
          pa, widths=[0.30, 1.45, 0.72, 2.06, 2.37], size=8.4, align_left_cols=(1, 3, 4))
    para(doc,
         "Searches in the two patent databases an examiner will use were run on 25 "
         "September 2026 and are logged in Table A. Espacenet (worldwide, European Patent "
         "Office) was searched on full text; InPASS (Indian Patent Office) on abstract and "
         "on international patent classification G08G, which covers traffic-control "
         "systems including vehicle counting. One further relevant document was found, "
         "entry 23.")
    table(doc, ["#", "Database", "Query", "Documents", "Outcome"], [
        ["1", "Espacenet", 'full text: "traffic detector flow conservation"', "83",
         "traffic-state estimation, detector placement and signal control; nothing "
         "closer than entries 1 to 3"],
        ["2", "Espacenet", 'full text: "traffic detector topology conservation counts"',
         "1", "CN103489316A: detector placement on a given road network; not relevant"],
        ["3", "Espacenet", 'full text: "traffic detector fault correction flow balance"',
         "9", "none in the field"],
        ["4", "Espacenet", 'full text: "missing traffic data flow conservation"', "86",
         "CN102169630A, entry 23; the remainder estimation and completion by learning"],
        ["5", "InPASS", 'abstract: "traffic conservation" (published and granted)', "2774",
         "most recent 25 screened; traffic signal control and monitoring; none relevant"],
        ["6", "InPASS", 'abstract: "detector topology" (published and granted)', "6",
         "all screened; 5684/DELNP/2008 maps traffic from mobile-terminal positions; "
         "none relevant"],
        ["7", "InPASS", 'IPC G08G AND abstract: "conservation"', "-",
         "screened by the inventor; none relevant"],
        ["8", "InPASS", 'IPC G08G 1 AND abstract: "detector"', "-",
         "screened by the inventor; none relevant"],
    ], cap="Table A: Patent Database Search Log, 25 September 2026",
        widths=[0.3, 0.8, 2.3, 0.75, 2.75], size=8.2, align_left_cols=(2, 4))
    para(doc,
         "The search covered Google Patents, the transport, process-systems and "
         "power-systems literature, and a patent-estate sweep of CPC G08G1/01 against "
         "structure recovery from counts. In entries 1 to 7 the network, whether called a "
         "station layout, a flowsheet, an admittance matrix or an incidence matrix, is an "
         "input, and the method asks which measurement disagrees with it. Entries 8 to 11 "
         "do recover structure from data, and the invention is distinguished from them "
         "narrowly: entry 8 returns a real-valued basis of the constraint space from "
         "simultaneously observed flows, whereas the invention returns individual signed "
         "junction relations from counts whose absent records fall in different intervals "
         "at different detectors; entries 9 and 10 supply the selection and pruning "
         "patterns, not the residual or the pairs to which they are applied here. Entry "
         "17 recovers conservation structure in a network whose roles are known: one "
         "parent and a set of candidate children, with coefficients of 0 or 1. Here no "
         "detector's role is known, the order of detectors along the road is itself "
         "recovered, and each coefficient carries a sign stating the direction of flow. "
         "Entry 20 infers a connectivity, but a learned, dense and unsigned one.")
    para(doc,
         "The present invention proceeds from the reverse premise. The counts of a "
         "detector network carry their own connectivity. Two detectors on the same "
         "uninterrupted carriageway agree to within their measurement noise; a detector "
         "between them agrees with each more tightly than they agree with each other; and "
         "the flow on a slip road is exactly the difference between the mainline detectors "
         "on either side of it. No reference located by the inventor recovers the signed "
         "junction relations of a road network from detector counts containing absent "
         "records, derives the tolerance for accepting such a relation from the same "
         "counts, and then imposes the recovered relations as hard constraints on the same "
         "dataset. Entries 1, 2, 5, 8, 9, 10, 17, 21 and 22 each supply one component of that "
         "arrangement and are conceded as such; what is claimed is the arrangement.")

    # ============================================================== 4
    h1(doc, "4. Summary and Background of the Invention (Gap / Novelty)")
    para(doc,
         "Roadside detector networks lose records. Loops fail, links drop, and individual "
         "intervals arrive blank. On the reference corridor used here, a month of "
         "fifteen-minute counts from %d detectors, the reconstruction evaluated in "
         "Section 8 withholds 10 %% of the recorded values in runs drawn from the measured "
         "gap-length distribution; values filled by a per-detector estimator violate the "
         "conservation relation at %.2f %% of node-intervals, describing junctions at "
         "which more vehicles leave than enter. Imposing conservation as a hard constraint "
         "cuts that share by about half, as de Souza and Yin already teach. But both "
         "need the network: which detectors form each junction, and the sign with which "
         "each slip road enters it."
         % (v25["sites"], c25["prior_only"]["outside"]))
    para(doc,
         "Network maps are not reliably available, and when they are they are not reliably "
         "right. On the reference corridor the surveyed junction list covers %d of the %d "
         "live detectors; the remainder appear in no relation at all. Of the %d relations "
         "the survey does list (%d plain continuity between consecutive mainline "
         "detectors, %d junctions with a slip road), %d have a conservation residual on "
         "the counts larger than the tolerance the detectors' own agreement supports, some "
         "of them by more than an order of magnitude. A method that takes the map as input "
         "inherits every one of those discrepancies silently."
         % (v25["sites_in_survey"], v25["sites"], ctl25["evaluable"], rs25["2"]["of"],
            slipt25, ctl25["false_flags"]))
    para(doc,
         "The invention recovers the constraint structure from the counts, in three "
         "stages. A pair stage finds detector pairs whose counts agree with unit "
         "coefficient. An ordering stage removes each pair that is bridged by a third "
         "detector agreeing more tightly with both, which leaves the chain of adjacent "
         "detectors: the order of sites along the road, recovered without coordinates. A "
         "junction stage takes each mainline pair that does not agree, forms the residual "
         "of the pair, and looks for slip-road detectors among those that correlate with "
         "that residual, fitting and rounding their coefficients to +1 or -1. A relation "
         "is kept only if its residual is within a limit measured from the adjacent pairs "
         "themselves and every member is necessary to it. The retained relations carry "
         "their own two-sided bands, and are imposed as hard inequality constraints.")
    figure(doc, "fig01.png",
           "Figure 1. What the counts alone reveal. Adjacent mainline detectors agree (pair "
           "relations); a shortcut pair is removed because a detector lies between; across "
           "a junction the slip-road detector closes the balance with a sign stating the "
           "direction of flow. No map, name or coordinate is supplied.")
    para(doc,
         "The junction stage is the step on which the invention turns. The obvious method, "
         "ranking candidate partners of a detector by how well they correlate with it, "
         "never finds a slip road, because every detector on a road carries the same daily "
         "profile and the next mainline detector always correlates best. Measured on the "
         "reference corridor, a slip-road detector at a real junction ranks %d of %d "
         "candidates by correlation with the upstream mainline detector, and first of %d by "
         "correlation with the residual of the mainline pair (Figure 4). %s"
         % (ex["rank_by_target"][0], ex["rank_by_target"][1], ex["rank_by_residual"][1],
            abl_sentence))
    para(doc,
         "The proposed system comprises: roadside detectors on the mainline and slip roads "
         "with a communication link to a count archive; a constraint-recovery arrangement "
         "comprising the pair stage, the ordering stage, the junction stage, a necessity "
         "test and a self-derived retention limit; a relation store and band unit holding "
         "the recovered hard constraint set; a map audit unit; a projection unit "
         "reconstructing absent records under the hard constraints, with irreconcilability "
         "reporting and certified intervals; a fault-attribution unit that names a "
         "miscounting detector and corrects its output; and outputs to a "
         "downstream traffic-control process and to a maintenance record.")
    figure(doc, "fig02.png",
           "Figure 2. System architecture. Counts from the detector network (100) reach the "
           "constraint-recovery stages (300-340); retained relations form the hard "
           "constraint set (400, 410), which drives reconstruction (510-530), the audit of "
           "any supplied map (600, 620) and fault attribution (700). Outputs (800) are "
           "technical: a corrected dataset, a maintenance record and a rewritten "
           "constraint set.")

    h2(doc, "4.1 Statement of Inventive Step (Non-Obviousness)")
    para(doc,
         "The inventive step does not reside in any element taken alone. Least-squares "
         "fitting is standard; sparse recovery of relations from data is SINDy; hard "
         "conservation constraints on traffic counts are de Souza and Yin; gross-error "
         "identification is Narasimhan and Mah. The invention resides in the following "
         "combination, and in technical effects that no element produces on its own:")
    bullets(doc, [
        ("(a)", "recovery of adjacency along the carriageway by a triangle rule on pairwise "
                "agreement, so that the order of detectors along the road, which every "
                "cited method receives as input, is produced from the counts;"),
        ("(b)", "a junction search in which slip-road candidates are ranked by correlation "
                "with the residual of a mainline pair rather than with any detector's own "
                "counts. At the junction of Figure 4 the slip detector moves from rank %d "
                "of %d to rank 1. %s"
                % (ex["rank_by_target"][0], ex["rank_by_target"][1], abl_sentence)),
        ("(c)", "rounding of every fitted coefficient to +1 or -1, so that a retained "
                "relation is not a regression but a statement of vehicle conservation, "
                "each sign stating whether a detector adds vehicles to the section or "
                "removes them;"),
        ("(d)", "a retention limit measured from the detectors' own disagreement, the "
                "median residual of the adjacent pairs found in (a), and not from any map "
                "or any tuning against one: %.2f %% of flow on the reference corridor and "
                "%.2f %% on the replication corridor, derived separately on each;"
                % (v25["meta"]["limit_pct"], v1["meta"]["limit_pct"])),
        ("(e)", "a necessity test under which every member of a retained relation must "
                "raise the residual materially when removed, so that a relation cannot "
                "carry a passenger detector;"),
        ("(f)", "imposition of the recovered relations as hard two-sided inequality "
                "constraints, each with a band from its own residual spread, on the very "
                "dataset from which they were recovered, with irreconcilable intervals "
                "reported rather than forced; and"),
        ("(g)", "the use of the same recovered relations, with no map, to name a "
                "miscounting detector from the pattern of deviations across the several "
                "relations it belongs to, to type its fault as proportional or constant, "
                "and to correct its output record, by inverting the fitted fault or, "
                "where the fault cannot be typed, by the value that closes its "
                "relations."),
    ])
    para(doc,
         "The synergy runs as follows. Element (b) is meaningful only because of element "
         "(a). The residual of a mainline pair isolates a slip road only when the pair "
         "brackets exactly one junction; a pair bracketing several junctions leaves a "
         "residual that is a sum of slip flows, which no small subset explains. The "
         "ordering stage is what supplies adjacent pairs. Element (d) is meaningful only "
         "because of (a) as well: the adjacent pairs are predominantly relations with no "
         "slip road between their detectors, so their median residual is the measurement "
         "noise of the detectors, measured without a map. A pair spanning a small slip "
         "can pass the pair tolerance, which is why the median and not the mean is taken. Remove (a) and both the junction search and "
         "the retention limit lose their footing.")
    para(doc,
         "Element (g) is conceded, for a known network, to entry 21, which estimates a "
         "per-sensor bias from nodal flow balance and corrects the counts, and is adjacent "
         "to gross-error identification (entry 5) and loop-drift diagnosis (entry 3); "
         "each needs a surveyed model. Element (c) is likewise conceded in part to entry "
         "22, which chooses the signs of meters already known to bound a zone. What is new is that the relations on which the "
         "detector is named are the ones recovered in (a) to (e), so the correction "
         "reaches detectors the map omits and does not inherit its errors. The effect is "
         "on the instrument's output: with no map, the net error removed from the output "
         "of a faulty detector lies between %s and %s across every fault injected on "
         "both corridors, charging every wrong correction against the result (Section "
         "8.6). The use of the same relations to audit a supplied map is disclosed and "
         "claimed only as a dependent use, since flagging a register against "
         "measurements is conceded to entries 5 and 19 (Section 8.4)."
         % (pct(min(net_removed(e) for d in (cor25, cor1) for e in d["cases"]
                    if e["mode"] != "none"), 0),
            pct(max(net_removed(e) for d in (cor25, cor1) for e in d["cases"]
                    if e["mode"] != "none"), 0)))
    para(doc,
         "A further technical effect follows from the same arrangement. Because the "
         "recovered relations cover detectors the map omits, a monitor built on them "
         "reaches more of the network: fault attribution on recovered relations admits "
         "%d detectors to the line-up against %d on the surveyed map (Section 8.5)."
         % (fr["detectors_eligible"], fs["detectors_eligible"]))

    # ============================================================== 5
    h1(doc, "5. Objectives of the Invention")
    bullets(doc, [
        ("1.", "To recover, from the counts of a roadside detector network alone, which "
               "detectors are joined by conservation of vehicles and with what sign, "
               "without a network map, junction register, naming convention or "
               "coordinates."),
        ("2.", "To recover slip-road junctions and not merely plain continuity between "
               "consecutive mainline detectors."),
        ("3.", "To decide which recovered relations to trust by a limit measured from the "
               "same counts, so that no threshold is borrowed from a map."),
        ("4.", "To reconstruct absent records so that the completed dataset satisfies the "
               "recovered relations as hard constraints, and to report, rather than force, "
               "intervals in which the observations cannot be reconciled."),
        ("5.", "To identify, classify and size a miscounting detector on a network whose "
               "map is absent or wrong, and to correct its output record."),
        ("6.", "To test a supplied network map against the counts, flag the relations it "
               "gets wrong, and propose a repair for each."),
        ("7.", "To keep every component explainable: least squares, rounding, medians and "
               "projections, and no trained black box."),
        ("8.", "To state an honest, quantified operating envelope, including where the "
               "method should not be relied upon."),
    ])

    # ============================================================== 6
    h1(doc, "6. Working Principle (in Brief)")
    para(doc,
         "Vehicles are conserved. Between two detectors on the same carriageway with no "
         "junction between them, every vehicle counted by the first is counted by the "
         "second, so their counts agree up to the detectors' measurement noise. Across a "
         "junction, the upstream count plus the vehicles joining from an on-slip minus the "
         "vehicles leaving by an off-slip equals the downstream count. Written as a linear "
         "relation among the counts, every coefficient is +1 or -1. This physical fact is "
         "what makes the structure recoverable: a relation that holds with integer "
         "coefficients to within the measurement noise, over thousands of intervals, is "
         "not a statistical coincidence.")
    para(doc,
         "The pair stage fits, for each pair of detectors, the coefficient relating their "
         "counts over the intervals both reported, and keeps the pair if the coefficient "
         "rounds to 1 and the median absolute difference is within a pair tolerance of "
         "flow. The ordering stage keeps a pair (i, k) only if no third detector j agrees "
         "more tightly with both i and k than they agree with each other. The median "
         "residual of the surviving adjacent pairs is the self-derived noise floor, and a "
         "fixed multiple of it is the retention limit.")
    para(doc,
         "The junction stage takes, for each detector, its most correlated partners of "
         "comparable flow that do not already form a tight adjacent pair with it. For each "
         "such pair it forms the residual series, ranks every other detector by the "
         "magnitude of its correlation with that residual, fits small subsets of the "
         "highest-ranked detectors to the residual, and keeps a subset only if every "
         "fitted coefficient rounds to +1 or -1. The resulting candidate relation is "
         "retained if its residual is within the limit and each member is necessary.")
    para(doc,
         "The retained relations, each with a two-sided band taken from its own residual "
         "spread over observed records, are the hard constraint set. A prior estimate of "
         "the absent records from any per-detector method is projected onto the "
         "intersection of the bands that touch an absent record, jointly across relations "
         "sharing a detector, by alternating closed-form projections. An empty "
         "intersection is reported with its shortfall in vehicles. The reconstructed "
         "dataset is supplied to the downstream control process in place of the received "
         "one. The same constraint set drives the map audit and fault attribution.")

    # ============================================================== 7
    h1(doc, "7. Detailed Description of the Invention")
    para(doc,
         "The system (900) carries the elements set out below. Figure 2 shows their "
         "arrangement; Figure 5 the sequence of operations of the method. Reference "
         "numerals are used consistently throughout this document and are collected in "
         "Table 1.")
    table(doc, ["Ref", "Element", "Ref", "Element"], [
        ["100", "roadside detector network", "410", "band unit"],
        ["110", "mainline detector", "500", "prior estimator"],
        ["120", "slip-road detector", "510", "projection unit"],
        ["130", "communication link", "520", "irreconcilability report"],
        ["200", "count archive", "530", "certified interval unit"],
        ["300", "pair stage", "600", "map audit unit"],
        ["310", "ordering stage", "610", "supplied network map"],
        ["320", "junction stage", "620", "repair proposer"],
        ["330", "necessity test", "700", "fault attribution unit"],
        ["340", "self-derived retention limit", "800", "outputs"],
        ["400", "relation store", "810", "reconstructed dataset"],
        ["", "", "820", "downstream traffic-control process"],
        ["", "", "830", "maintenance record"],
        ["", "", "840", "rewritten constraint set"],
        ["", "", "900", "data-processing system"],
    ], cap="Table 1: Reference Numerals Used in the Description and the Figures",
        widths=[0.55, 2.55, 0.55, 2.55], size=9.5, align_left_cols=(1, 3))

    para(doc,
         "Detectors (100). Mainline detectors (110) and slip-road detectors (120) each "
         "report a vehicle count per measurement interval, fifteen minutes in the "
         "embodiment, over a communication link (130) to a count archive (200). The archive "
         "holds a matrix of counts indexed by detector and interval, with absent records "
         "marked. No other input is required. In particular the system does not receive, "
         "and does not use, which detectors are mainline and which are slip roads; the "
         "labels 110 and 120 describe the road, not the input.")
    para(doc,
         "Pair stage (300). For each pair of detectors (i, k) with at least a minimum "
         "number of intervals in which both reported (400 in the embodiment), the "
         "least-squares coefficient of x_i on x_k is computed. If it lies within a rounding "
         "tolerance (0.30) of 1, the median absolute difference |x_i - x_k| is expressed "
         "as a percentage of the larger mean flow, and the pair is kept if that percentage "
         "is within a pair tolerance (4 %%). On the reference corridor %d pairs pass."
         % v25["meta"]["pairs"])
    para(doc,
         "Ordering stage (310). A kept pair (i, k) is removed if there is a detector j for "
         "which both (i, j) and (j, k) are kept and each has a smaller residual percentage "
         "than (i, k): j lies between i and k along the carriageway, and (i, k) is a "
         "shortcut. The pairs that remain are adjacent pairs (%d on the reference "
         "corridor). Figure 3(a) illustrates the rule."
         % v25["meta"]["adjacent"])
    para(doc,
         "Self-derived retention limit (340). The median residual percentage over the "
         "adjacent pairs is the noise floor of the detectors, measured on the one "
         "population of relations that contains no slip road. The retention limit is a "
         "fixed multiple (2) of it: %.3f %% x 2 = %.3f %% of flow on the reference "
         "corridor. The multiple is fixed before any comparison with a map and is not "
         "tuned. Adjacent pairs within the limit enter the relation store (400) directly."
         % (v25["meta"]["self_floor_pct"], v25["meta"]["limit_pct"]))
    figure(doc, "fig03.png",
           "Figure 3. (a) The ordering stage (310): a pair bridged by a detector that "
           "agrees more tightly with both ends is a shortcut and is removed. (b) The "
           "junction stage (320): slip candidates are ranked against the residual of the "
           "mainline pair, fitted, rounded to +/-1, and tested for necessity (330).")
    para(doc,
         "Junction stage (320). For each detector i, its partners k are the detectors "
         "most correlated with it (six in the embodiment) whose mean flow is between half "
         "and twice its own, excluding any k with which it already forms an adjacent pair "
         "within the limit. For each such (i, k) the residual series r = x_i - x_k is "
         "formed over the intervals both reported, and every other detector j is ranked by "
         "|corr(x_j, r)| over the intervals all three reported. Subsets of one to three of "
         "the eight highest-ranked detectors are fitted to r by least squares. A subset is "
         "kept as a candidate only if every fitted coefficient lies within the rounding "
         "tolerance of +1 or -1; the candidate relation is then x_i - x_k - sum(c_j x_j) "
         "= 0 with the rounded c_j. The sign of each c_j states whether detector j adds "
         "vehicles to the section between i and k or removes them.")
    para(doc,
         "Necessity test (330) and retention. A candidate is retained if its median "
         "absolute residual, as a percentage of the largest member flow, is within the "
         "retention limit (340), and if, for each member, the relation with that member "
         "removed has a residual at least a necessity factor (1.5) larger. Duplicate "
         "relations, including a relation and its negation, are retained once. On the "
         "reference corridor the relation store holds %d relations: %d of two detectors "
         "and %d of three or more."
         % (v25["found"], v25["found_by_size"]["2"],
            v25["found"] - v25["found_by_size"]["2"]))
    figure(doc, "fig04.png",
           "Figure 4. A junction recovered from the counts: M25 detectors 4432A, 4435A and "
           "off-slip 4435J, %d shared intervals. (a) The slip flow tracks the residual of "
           "the mainline pair, and ranks first against it but %d of %d against the "
           "upstream detector. (b) Adding the slip with coefficient -1 collapses the "
           "median residual from %.0f to %.0f vehicles per interval."
           % (ex["n"], ex["rank_by_target"][0], ex["rank_by_target"][1], ex["pair_med"],
              ex["rel_med"]))
    para(doc,
         "Band unit (410). Each retained relation is written with one member as the "
         "downstream term, and over the intervals in which all its members reported a "
         "downstream coefficient and an offset are fitted to it by least squares, which "
         "absorbs the small systematic disagreement between real detectors. The band is "
         "a predetermined upper quantile (0.95) of the absolute deviation of the "
         "calibrated relation over the same intervals, applied on both sides of it. The "
         "relation and its band "
         "are computed from observed records only; an absent record plays no part in the "
         "constraint that will be used to reconstruct it.")
    para(doc,
         "Projection unit (510), irreconcilability report (520) and certified interval "
         "unit (530). For each interval with at least one absent record, the relations "
         "touching an absent record are assembled, with observed members held at their "
         "observed values. A prior estimate from any per-detector method (500) is projected "
         "onto the intersection of the bands, together with non-negativity, jointly "
         "across relations sharing a detector, by Dykstra's alternating projections with "
         "a closed-form weighted least-squares step. The bands are hard inequalities: the "
         "solver may not trade a violation for closeness to the prior. Where the "
         "intersection is empty, established by a linear program computing the smallest "
         "uniform widening that admits a solution, the relation and interval are reported "
         "with that shortfall in vehicles and the nearest point is retained. For each "
         "reconstructed value, minimising and maximising that value over the intersection "
         "gives an interval outside which no value is consistent with the observations "
         "under the relations.")
    figure(doc, "fig05.png",
           "Figure 5. Sequence of operations of the method (steps S1-S10).", width=4.6)
    para(doc,
         "Map audit unit (600) and repair proposer (620). Where a network map (610) is "
         "supplied, each map relation's median residual is measured on the counts and the "
         "relation is flagged if the residual exceeds the retention limit (340), the same "
         "limit the recovered relations obey. For each flagged relation the repair "
         "proposer selects, among the recovered relations sharing at least two of its "
         "detectors and at least half of its members, the one with the smallest residual. "
         "The constraint set is rewritten (840) by replacing each flagged relation that "
         "has a repair, and the flagged relations are written to the maintenance record "
         "(830). Recovered relations that include a detector absent from the map are "
         "output as proposed additions to it.")
    figure(doc, "fig06.png",
           "Figure 6. The map audit. The map is judged by the counts, against the limit the "
           "recovery itself obeys; a recovered relation sharing its detectors is proposed "
           "as the repair.")
    para(doc,
         "Fault attribution unit (700). The recovered relations are fitted on a reference "
         "period. Over each span of consecutive intervals (192 in the embodiment) the mean "
         "residual of each relation is compared with a threshold taken from the empirical "
         "distribution of the same statistic at that relation over reference spans, at a "
         "chosen false-positive rate (1 %). For each detector belonging to at least two "
         "relations, a single bias is fitted by weighted least squares against the "
         "coefficients (+1 or -1) with which it enters each of its relations, and the "
         "detector whose fitted bias accounts for the most deviation is named. Its fault "
         "is classified as proportional or constant by fitting both models across the "
         "busier and quieter halves of the span, and the fitted magnitude is written to "
         "the maintenance record (830). The counts of the named detector over the span "
         "are then corrected: rescaled by the fitted proportion, or reduced by the fitted "
         "offset, according to the type found; where no type can be fitted, each count "
         "is replaced by the median, over the relations containing the detector, of the "
         "value that sets that relation's calibrated residual to zero. The corrected "
         "counts replace the received ones in the output dataset (810).")

    h2(doc, "7.1 Alternative Embodiments")
    bullets(doc, [
        ("(a)", "The recovered relations may be combined with those of a supplied map, the "
                "union being imposed as the constraint set. This is the configuration of "
                "lowest reconstruction error measured on both corridors (Section 8.3)."),
        ("(b)", "The relations may be recovered on a historical archive once and reused on "
                "a live feed, or re-recovered periodically so that a change in the road, "
                "such as a new or closed slip road, enters the constraint set without a "
                "survey. Periodic re-recovery has not been measured."),
        ("(c)", "The counts may be resolved by vehicle length class. The prototype "
                "measured class-resolved conservation to degrade reconstruction on a "
                "surveyed map, and it is therefore not proposed for reconstruction."),
        ("(d)", "The coefficient set may be widened from {-1, +1} to small integers, for "
                "a detector counting both lanes of a slip road separately or a detector "
                "whose count is duplicated. Not reduced to practice."),
        ("(e)", "A detector common to two adjacent flagged map relations may be reported "
                "as a detector fault rather than a map error, since one miscounting "
                "detector breaks both relations it belongs to. Observed in Section 8.4, "
                "not built as a rule and not claimed."),
        ("(f)", "The prior estimator (500) may be any per-detector method: historical "
                "mean, temporal interpolation, low-rank completion or spatial nearest "
                "neighbour. The projection leaves an already consistent prior unchanged."),
    ])

    # ============================================================== 8
    h1(doc, "8. Validation - Study on Recorded Detector Data")
    para(doc,
         "All measurements below were made on openly licensed counts from the National "
         "Highways WebTRIS service, March 2025: the M25 clockwise carriageway, %d "
         "detectors, as the reference corridor, and the M1, %d detectors, as a "
         "replication corridor on which nothing was retuned. The surveyed junction list "
         "used for scoring was built separately from detector site names and chainage "
         "markers; it is never an input to the recovery. Every number is read from the "
         "prototype's results files."
         % (v25["sites"], v1["sites"]))
    table(doc, ["Mechanism", "Evidence base", "Headline measurement", "Section"], [
        ["Junction recovery from counts", "M25, M1",
         "%d of %d and %d of %d slip-road junctions recovered, no map"
         % (slips25, slipt25, slips1, slipt1), "8.2"],
        ["Precision of recovered relations", "M25, M1",
         "%.1f %% and %.1f %% of relations the map can judge are confirmed"
         % (100 * v25["judged_precision"], 100 * v1["judged_precision"]), "8.2"],
        ["Reconstruction, no map", "M25, M1",
         "MAE %.2f and %.2f against %.2f and %.2f for the prior alone"
         % (c25["recovered"]["MAE"], c1["recovered"]["MAE"], c25["prior_only"]["MAE"],
            c1["prior_only"]["MAE"]), "8.3"],
        ["Reconstruction, map plus recovered", "M25, M1",
         "lowest MAE of all configurations: %.2f and %.2f"
         % (c25["both"]["MAE"], c1["both"]["MAE"]), "8.3"],
        ["Map audit", "M25, M1",
         "reversed sign %s / %s flagged; omitted slip %s / %s"
         % (pct(k25["sign_flip"]["detection_rate"], 0), pct(k1["sign_flip"]["detection_rate"], 0),
            pct(k25["drop_member"]["detection_rate"], 0),
            pct(k1["drop_member"]["detection_rate"], 0)), "8.4"],
        ["Fault attribution, no map", "M25",
         "%d detectors in the line-up against %d; 5 %% under-count named first in %s"
         % (fr["detectors_eligible"], fs["detectors_eligible"],
            pct(case(fr, "scale", 0.95)["attribution_top1"])), "8.5"],
        ["Correction of the faulty detector's output, no map", "M25, M1",
         "net error removed %s to %s across all injected faults"
         % (pct(min(net_removed(e) for d in (cor25, cor1) for e in d["cases"]
                    if e["mode"] != "none"), 0),
            pct(max(net_removed(e) for d in (cor25, cor1) for e in d["cases"]
                    if e["mode"] != "none"), 0)), "8.6"],
        ["Correction against the closest art (entry 21)", "M25, M1",
         "on the same injected faults, detector named correctly in %s-%s of trials "
         "against %s-%s for entry 21 on the surveyed map"
         % tuple(pct(x, 0) for x in yf_range()), "8.6"],
        ["Faults named on unmodified counts, no map", "M25, M1",
         "%d of %d named detectors dead within three months, against %d of %d controls "
         "(p = %s; March to June)" % (rfm["pooled_per_month"]["reported_failed"],
                         rfm["pooled_per_month"]["reported"],
                         rfm["pooled_per_month"]["control_failed"],
                         rfm["pooled_per_month"]["control"],
                         sci(rfm["pooled_per_month"]["fisher_exact_p_one_sided"])),
         "8.6a"],
    ], cap="Table 2: Summary of Validation Evidence", widths=[1.7, 0.8, 3.1, 0.6],
        size=9, align_left_cols=(0, 2))

    h2(doc, "8.1 Protocol")
    para(doc,
         "Recovery is run on the counts alone. For reconstruction, 10 % of recorded values "
         "are withheld in runs drawn from the measured gap-length distribution, the "
         "relations and their bands are recovered from the remaining values only, and the "
         "withheld values are then reconstructed and scored against what the detectors "
         "actually reported. Physical consistency is scored as the share of node-intervals "
         "violating the surveyed relations fitted on the full corridor, which serves as a "
         "reference and is never an input. For the map audit, errors of four kinds are "
         "injected into surveyed junctions that pass the audit uncorrupted. For fault "
         "attribution, faults of known type, size and detector are superimposed on the real "
         "counts in a half of the month disjoint from the half on which the relations and "
         "thresholds were fitted.")
    para(doc,
         "The constraint sets therefore differ between experiments, and each is stated. "
         "Section 8.2 scores recovery on the whole month (%d relations on the reference "
         "corridor, limit %.3f %%; %d on the replication corridor, limit %.3f %%). The "
         "reconstruction of Section 8.3 re-runs recovery on the 90 %% of values left "
         "visible, giving %d and %d relations usable as constraints, at limits of %.3f %% "
         "and %.3f %%. Fault attribution in Section 8.5 re-runs it on the reference half "
         "of the month, giving %d relations."
         % (v25["found"], v25["meta"]["limit_pct"], v1["found"], v1["meta"]["limit_pct"],
            c25["recovered"]["constraints"], c1["recovered"]["constraints"],
            v25["train_meta"]["limit_pct"], v1["train_meta"]["limit_pct"],
            fr["nodes_fitted"]))

    h2(doc, "8.2 Recovery of the relations")
    rows = []
    for d, nm in ((v25, "M25"), (v1, "M1")):
        r = d["recall_by_size"]
        rows.append([nm, d["sites"], "%.3f %%" % d["meta"]["limit_pct"], d["found"],
                     "%d / %d" % (r["2"]["recovered"], r["2"]["of"]),
                     "%d / %d" % (sum(r[s]["recovered"] for s in r if s != "2"),
                                  sum(r[s]["of"] for s in r if s != "2")),
                     "%.1f %%" % (100 * d["judged_precision"])])
    table(doc, ["Corridor", "Detectors", "Self-derived limit", "Relations retained",
                "Plain continuity recovered", "Slip-road junctions recovered",
                "Judged precision"], rows,
          cap="Table 3: Relations Recovered from the Counts, No Map Supplied",
          widths=[0.8, 0.8, 0.9, 0.9, 1.1, 1.1, 0.8], size=9)
    para(doc,
         "Judged precision counts a recovered relation as confirmed when it equals a "
         "surveyed relation or lies in the span of the surveyed relations, and as unjudged "
         "when it involves a detector the survey omits. On the reference corridor the %d "
         "retained relations divide into %d exact, %d implied by the surveyed set, %d "
         "involving a detector absent from the survey, and %d lying outside the span of "
         "the surveyed relations. The last group is not shown to be wrong, but nothing in "
         "the survey supports it, and it is imposed as a hard constraint all the same. "
         "Recall "
         "falls with relation size: %d of %d three-detector junctions but %d of %d "
         "four-detector ones, where two slip roads share a section and the residual of "
         "the mainline pair is a sum."
         % (v25["found"], v25["categories"]["exact"], v25["categories"]["implied"],
            v25["categories"]["unmapped_site"], v25["categories"]["outside_map"],
            rs25["3"]["recovered"], rs25["3"]["of"], rs25["4"]["recovered"],
            rs25["4"]["of"]))
    if jun:
        rj, cj = jun["recall_by_size"], jun["configs"]
        para(doc,
             "The recovery was repeated, unchanged, on a second month of the reference "
             "corridor (June 2025, %d detectors). The self-derived limit came out at "
             "%.3f %% of flow against %.3f %% in March; %d relations were retained, "
             "recovering %d of %d surveyed slip-road junctions, with judged precision "
             "%.1f %%. Reconstruction under the relations recovered from the June counts "
             "gave MAE %.2f and RMSE %.2f against %.2f and %.2f for the prior alone, and "
             "%.2f %% of node-intervals outside band against %.2f %%."
             % (jun["sites"], jun["meta"]["limit_pct"], v25["meta"]["limit_pct"],
                jun["found"], sum(rj[k]["recovered"] for k in rj if k != "2"),
                sum(rj[k]["of"] for k in rj if k != "2"), 100 * jun["judged_precision"],
                cj["recovered"]["MAE"], cj["recovered"]["RMSE"], cj["prior_only"]["MAE"],
                cj["prior_only"]["RMSE"], cj["recovered"]["outside"],
                cj["prior_only"]["outside"]))
    if abl:
        rows = []
        for nm in ("M25", "M1"):
            a = abl["corridors"][nm]
            for mode, lab in (("target", "detector's own counts |corr(x_j, x_i)|"),
                              ("residual", "mainline-pair residual |corr(x_j, x_i - x_k)|")):
                rows.append([nm, lab, a[mode]["found"],
                             "%d / %d" % (a[mode]["slip_recovered"], a["slip_total"]),
                             "%.1f %%" % (100 * a[mode]["judged_precision"])])
        table(doc, ["Corridor", "Slip candidates ranked against", "Relations retained",
                    "Slip-road junctions recovered", "Judged precision"], rows,
              cap="Table 3a: Controlled Ablation of the Junction-Stage Ranking",
              widths=[0.8, 2.6, 0.9, 1.1, 0.9], size=9, align_left_cols=(1,))
        para(doc,
             "Every other stage and constant is identical between the paired rows. Ranked "
             "against the detector's own counts, the shortlist fills with mainline "
             "detectors, which pass as plain continuity or as spurious combinations, and "
             "not one slip-road junction is recovered on either corridor.")
    if base:
        rows = []
        for nm, v in (("M25", v25), ("M1", v1)):
            bc = base["corridors"][nm]
            ip = bc["ipca"]
            fav = bc["ipca_favourable_subsets"][-1]
            om = bc["omp"]
            rows.append([nm, "IPCA, all detectors (entry 8)",
                         "%d of %d detectors, %d intervals" % (ip["detectors_retained"],
                                                                ip["detectors_total"],
                                                                ip["complete_intervals"]),
                         "0 / %d" % ip["slip_relations_among_retained"],
                         "%d of %d in recovered space; %d read off"
                         % (ip["in_recovered_span"], ip["surveyed_relations_among_retained"],
                            ip["surveyed_relations_read_off_exactly"])])
            rows.append([nm, "IPCA, favourable subset (entry 8)",
                         "%d detectors, %d intervals" % (fav["detectors_retained"],
                                                          fav["complete_intervals"]),
                         "%d / %d" % (fav["slip_relations_read_off_exactly"],
                                      fav["slip_relations_among_retained"]),
                         "%d of %d in recovered space; %d read off"
                         % (fav["in_recovered_span"], fav["surveyed_relations_among_retained"],
                            fav["surveyed_relations_read_off_exactly"])])
            rows.append([nm, "matching pursuit, given the method's limit (entry 9)",
                         "all %d detectors" % v["sites"],
                         "%d / %d" % (om["slip_recovered"], om["slip_total"]),
                         "%d retained, judged precision %.1f %%"
                         % (om["found"], 100 * om["judged_precision"])])
            gc = grid["corridors"][nm]
            gk = max((k for k in gc if isinstance(gc[k], dict)),
                     key=lambda k: gc[k]["slip_recovered"])
            g = gc[gk]
            rows.append([nm, "bounded least squares, every detector tried as parent "
                             "(entry 17), best of %d variants" % sum(
                                 1 for k in gc if isinstance(gc[k], dict)),
                         "all %d detectors, pool %s" % (v["sites"], gk.split("pool")[1]),
                         "%d / %d" % (g["slip_recovered"], g["slip_total"]),
                         "%d retained, judged precision %.1f %%"
                         % (g["found"], 100 * g["judged_precision"])])
            sc = sparse["corridors"][nm]
            vx = sc["varimax"]
            rows.append([nm, "IPCA space rotated by varimax (entry 8, sparse form)",
                         "%d detectors, %d intervals" % (sc["detectors_retained"],
                                                          sc["complete_intervals"]),
                         "%d / %d" % (vx["slip_recovered"], vx["slip_total"]),
                         "%d rows read off, judged precision %s"
                         % (vx["found"], "%.1f %%" % (100 * vx["judged_precision"])
                            if vx["judged_precision"] is not None else "n/a")])
            lk = max((k for k in sc if k.startswith("lasso_")),
                     key=lambda k: sc[k]["slip_recovered"])
            lz = sc[lk]
            rows.append([nm, "Lasso on every detector, given the method's limit "
                             "(entries 11, 17), best of %d penalties"
                         % sum(1 for k in sc if k.startswith("lasso_")),
                         "%d detectors, %d intervals" % (sc["detectors_retained"],
                                                          sc["complete_intervals"]),
                         "%d / %d" % (lz["slip_recovered"], lz["slip_total"]),
                         "%d retained, judged precision %s"
                         % (lz["found"], "%.1f %%" % (100 * lz["judged_precision"])
                            if lz["judged_precision"] is not None else "n/a")])
            rows.append([nm, "the invention", "all %d detectors" % v["sites"],
                         "%d / %d" % (sum(v["recall_by_size"][k]["recovered"]
                                          for k in v["recall_by_size"] if k != "2"),
                                      sum(v["recall_by_size"][k]["of"]
                                          for k in v["recall_by_size"] if k != "2")),
                         "%d retained, judged precision %.1f %%"
                         % (v["found"], 100 * v["judged_precision"])])
        table(doc, ["Corridor", "Method", "Data it can use", "Slip-road junctions "
                    "recovered", "Other"], rows,
              cap="Table 3b: The Closest Art Run on the Same Counts",
              widths=[0.75, 1.9, 1.45, 0.9, 1.6], size=8.5, align_left_cols=(1, 2, 4))
        dg = base["corridors"]["M25"]["ipca_diagnosis_2000rows"]
        para(doc,
             "Every baseline was given advantages it would not have in use. IPCA and its "
             "varimax-rotated form were told the number of constraints to find, taken from "
             "the survey, and were run on the complete-case data they require, which on "
             "the reference corridor means discarding detectors until enough intervals "
             "have every remaining detector reporting. Matching pursuit, Lasso and the "
             "grid-topology method were given the method's own self-derived limit, which "
             "none of them can derive. The grid-topology method, whose published form "
             "knows the parent meter, was run with every detector tried as parent, in its "
             "published 0/1 form and in a signed form it does not itself use, with "
             "candidate pools of two sizes; the best variant is shown. Lasso was run at "
             "four penalties and the best is shown. The IPCA implementation was checked on "
             "a synthetic chain network with exact conservation, where it recovers every "
             "relation.")
        para(doc,
             "On the counts it fails for a physical reason that can be measured. Traffic on "
             "every detector of a road follows the same daily profile, so the counts are "
             "nearly of low rank: on the favourable subset of the reference corridor the "
             "first principal direction carries %.1f %% of the variance and %d directions "
             "carry 99 %%. The remaining hundreds of directions are all quiet, and the "
             "conservation relations are not the quietest among them: their residual spread "
             "is %.1f per unit norm against %.1f for the quietest direction. IPCA, which "
             "selects the quietest directions, therefore returns a space from which the "
             "true relations lie at a median relative distance of %.2f, and no signed "
             "relation can be read from it. The invention does not rank directions by "
             "variance; it tests explicit integer relations against the detectors' own "
             "noise floor, which is why it is unaffected."
             % (100 * dg["variance_share_first_component"], dg["dims_for_99pct_variance"],
                dg["true_relation_residual_std_per_unit_norm_median"],
                dg["smallest_direction_std"],
                dg["true_relation_distance_from_ipca_space_median"]))
        para(doc,
             "Matching pursuit selects against a residual, as the junction stage does, but "
             "its first selection for any mainline detector is the next mainline detector "
             "with a fitted, not a unit, coefficient, and it has no ordering stage to "
             "supply a pair bracketing exactly one junction. It retains plain continuity "
             "with high precision and recovers few slip-road junctions. The grid-topology "
             "method and Lasso fail in the same way and for the same reason: fitted "
             "against a detector's own counts, the regression is dominated by the "
             "mainline detectors that share its daily profile, which is the effect the "
             "controlled ablation of Table 3a isolates; refitting the Lasso support by least "
             "squares before rounding, so that shrinkage cannot be blamed, does not change "
             "that. The sparse rotation of the IPCA space is the strongest baseline: it does "
             "yield rows that read as signed relations, and on the replication corridor "
             "%d of them are slip-road junctions, against %d for the invention. It needs "
             "the complete-case data and the number of constraints, which the invention "
             "does not, and on the reference corridor, with %d slip-road junctions to find, "
             "it reaches %d. The slip-road junction is the relation that carries the "
             "direction of flow, and on the larger corridor the closest art does not "
             "deliver it: no "
             "baseline or variant in Table 3b recovers more than %d of the %d "
             "surveyed slip-road junctions on the reference corridor, against %d for the "
             "invention."
             % (sparse["corridors"]["M1"]["varimax"]["slip_recovered"], slips1, slipt25,
                sparse["corridors"]["M25"]["varimax"]["slip_recovered"],
                max([base["corridors"]["M25"]["omp"]["slip_recovered"],
                     max(grid["corridors"]["M25"][k]["slip_recovered"]
                         for k in grid["corridors"]["M25"]
                         if isinstance(grid["corridors"]["M25"][k], dict)),
                     max(sparse["corridors"]["M25"][k]["slip_recovered"]
                         for k in sparse["corridors"]["M25"]
                         if isinstance(sparse["corridors"]["M25"][k], dict))]),
                slipt25, slips25))
    figure(doc, "fig07.png",
           "Figure 7. Surveyed relations recovered exactly from the counts, by relation "
           "size, on both corridors. The slip-road columns are the ones the obvious "
           "correlation ranking could not reach.")

    h2(doc, "8.2a Are the unconfirmed relations real?")
    catname = {"exact": "equal to a surveyed relation", "implied": "implied by the survey",
               "unmapped_site": "involving a detector the survey omits",
               "outside_map": "outside the span of the survey"}
    rows = []
    for nm in ("M25", "M1"):
        by = recur["corridors"][nm]["by_category"]
        for k in ("exact", "implied", "unmapped_site", "outside_map"):
            x = by[k]
            rows.append([nm, catname[k], x["relations"], pct(x["share_recur_all_3"], 0),
                         pct(x["share_recur_any"], 0)])
    table(doc, ["Corridor", "March relation", "Relations", "Recovered again in all of "
                "April, May and June", "Recovered again in at least one"], rows,
          cap="Table 3c: Recurrence of the Relations Recovered in March, by Category",
          widths=[0.7, 2.3, 0.8, 1.3, 1.2], size=8.8, align_left_cols=(1,))
    ex25 = recur["corridors"]["M25"]["by_category"]["exact"]
    om25 = recur["corridors"]["M25"]["by_category"]["outside_map"]
    om1 = recur["corridors"]["M1"]["by_category"]["outside_map"]
    para(doc,
         "The relations are imposed as hard constraints, so a relation that is recovered "
         "but not physical would corrupt the reconstruction. The test needs no ground "
         "truth: a physical relation holds in every month, a chance "
         "combination does not. Recovery was repeated, unchanged, on each of the three "
         "following months, and each March relation was checked for exact recurrence. "
         "Relations the survey confirms recur in all three months in %s of cases on the "
         "reference corridor; relations outside the span of the survey recur in %s on "
         "the reference corridor and %s on the replication corridor. So about half of "
         "the unconfirmed relations on the reference corridor behave as physical "
         "relations the survey omits, and the rest are probably spurious. Recurrence "
         "therefore separates physical relations from chance ones without any map, "
         "which is the basis of Claim 9: a relation is imposed only if it was also "
         "recovered from an earlier period."
         % (pct(ex25["share_recur_all_3"], 0), pct(om25["share_recur_all_3"], 0),
            pct(om1["share_recur_all_3"], 0)))

    h2(doc, "8.3 Reconstruction under the recovered constraints")
    rows = []
    labels = (("prior_only", "prior estimate only"), ("surveyed", "surveyed map"),
              ("recovered", "recovered relations, no map"),
              ("both", "surveyed map + recovered"))
    for key, nm in labels:
        rows.append([nm, "%.2f" % c25[key]["MAE"], "%.2f" % c25[key]["RMSE"],
                     "%.2f %%" % c25[key]["outside"],
                     "%.2f" % c1[key]["MAE"], "%.2f" % c1[key]["RMSE"],
                     "%.2f %%" % c1[key]["outside"]])
    table(doc, ["Constraint set", "M25 MAE", "M25 RMSE", "M25 outside band", "M1 MAE",
                "M1 RMSE", "M1 outside band"], rows,
          cap="Table 4: Reconstruction of Withheld Records (vehicles per interval)",
          widths=[1.9, 0.7, 0.7, 0.85, 0.7, 0.7, 0.85], size=9, align_left_cols=(0,))
    para(doc,
         "With no map at all, the recovered constraints reduce reconstruction error from "
         "%.2f to %.2f on the reference corridor and from %.2f to %.2f on the replication "
         "corridor, and reduce the share of node-intervals violating conservation from "
         "%.2f %% to %.2f %% and from %.2f %% to %.2f %%. Against the surveyed map, the "
         "recovered set is level on error on the reference corridor and better on the "
         "replication corridor, and worse on consistency on both, consistency being "
         "scored against the surveyed relations themselves. Combining the two gives the "
         "lowest mean absolute error on both corridors."
         % (c25["prior_only"]["MAE"], c25["recovered"]["MAE"], c1["prior_only"]["MAE"],
            c1["recovered"]["MAE"], c25["prior_only"]["outside"],
            c25["recovered"]["outside"], c1["prior_only"]["outside"],
            c1["recovered"]["outside"]))
    db = diag["breakdown"]
    big = [bk for bk in db["by_correction_size"] if bk["correction_from"] == 200][0]
    rm_ok = all(c[k]["RMSE"] <= c["prior_only"]["RMSE"] for c in (c25, c1)
                for k in ("surveyed", "recovered", "both"))
    para(doc,
         "Root-mean-square error was examined separately, because it is dominated by a "
         "few large errors and so exposes a failure that the mean hides. In the first "
         "version of the projection unit it rose under the recovered constraints, from "
         "%.2f to %.2f on the reference corridor and from %.2f to %.2f on the "
         "replication corridor. Breaking the added squared error down cell by cell on "
         "the replication corridor traced it to %d of %d withheld values, each moved by "
         "more than 200 vehicles, which together added more squared error than the whole "
         "net rise; values moved by less improved throughout. The fifteen largest, examined "
         "individually, had been set to zero or near it from priors close to the true "
         "count, in "
         "intervals whose intersection of bands was satisfiable but on which the "
         "alternating projection had stalled and been restarted from the vertex of the "
         "linear program that established satisfiability. That program places no "
         "cost on the unknowns, so its vertex sets them to zero, including unknowns that "
         "no violated relation touches. The restart is now taken instead from the "
         "feasible point nearest the prior in weighted L1 distance, itself found by a "
         "linear program (Claim 8). Table 4 is measured with that change and no other. %s"
         % (old25["configs"]["prior_only"]["RMSE"], old25["configs"]["recovered"]["RMSE"],
            old1["configs"]["prior_only"]["RMSE"], old1["configs"]["recovered"]["RMSE"],
            big["cells"], db["cells"],
            ("RMSE now falls under every constraint set on both corridors, so the mean "
             "improvement is no longer bought by a minority of large errors."
             if rm_ok else
             "RMSE under the recovered constraints is now %.2f against %.2f for the prior "
             "on the reference corridor and %.2f against %.2f on the replication corridor."
             % (c25["recovered"]["RMSE"], c25["prior_only"]["RMSE"],
                c1["recovered"]["RMSE"], c1["prior_only"]["RMSE"]))))
    if stab:
        sa, ss = stab["corridors"]["M25"]["recovered_all"], stab["corridors"]["M25"]["recovered_stable"]
        ta, ts = stab["corridors"]["M1"]["recovered_all"], stab["corridors"]["M1"]["recovered_stable"]
        para(doc,
             "A second remedy, tried before the cause was found, is not claimed: admitting "
             "a relation only if it holds within the limit in each half of the month "
             "separately removes %d of %d constraints on the reference corridor and moves "
             "neither error measure materially (MAE %.2f against %.2f and RMSE %.2f against "
             "%.2f on the reference corridor; MAE %.2f against %.2f and RMSE %.2f against "
             "%.2f on the replication corridor)."
             % (sa["constraints"] - ss["constraints"], sa["constraints"], ss["MAE"],
                sa["MAE"], ss["RMSE"], sa["RMSE"], ts["MAE"], ta["MAE"], ts["RMSE"],
                ta["RMSE"]))
    figure(doc, "fig08.png",
           "Figure 8. Accuracy and physical consistency of the reconstructed dataset under "
           "each constraint set, both corridors.")

    h2(doc, "8.4 Audit of a supplied map")
    rows = []
    for k, nm in (("sign_flip", "slip-road sign reversed"),
                  ("drop_member", "slip-road member omitted"),
                  ("wrong_site", "one detector replaced by a site within six positions"),
                  ("extra_member", "unrelated detector added")):
        rows.append([nm, k25[k]["trials"], pct(k25[k]["detection_rate"]),
                     pct(k25[k]["repair_rate"]), k1[k]["trials"],
                     pct(k1[k]["detection_rate"]), pct(k1[k]["repair_rate"])])
    rows.append(["uncorrupted map: relations over the limit",
                 ctl25["evaluable"], pct(ctl25["false_flag_rate"]), "-",
                 ctl1["evaluable"], pct(ctl1["false_flag_rate"]), "-"])
    table(doc, ["Injected map error", "M25 trials", "Flagged", "Repaired exactly",
                "M1 trials", "Flagged", "Repaired exactly"], rows,
          cap="Table 5: Map Audit Against the Counts", widths=[2.0, 0.65, 0.7, 0.8, 0.65,
                                                                0.7, 0.8],
          size=9, align_left_cols=(0,))
    para(doc,
         "Errors are injected only into surveyed junctions that the audit passes when "
         "uncorrupted, so that no error is credited as found merely because its junction "
         "already failed. Sign reversals, omitted slip roads and added members are flagged "
         "in every trial on both corridors. Replacement of a detector by a nearby one is "
         "flagged in about three trials of five, because a nearby mainline detector is "
         "often an almost equally valid member. Exact repair is lower than flagging "
         "throughout: a flagged relation has an exact repair only where the junction was "
         "itself recovered in Section 8.2.")
    para(doc,
         "The last row is not a false-alarm rate. On the uncorrupted survey, %d relations "
         "on the reference corridor and %d on the replication corridor have a residual on "
         "the counts above the limit, the largest at %.1f %% and %.1f %% of flow "
         "respectively. Several occur in "
         "adjacent pairs sharing one detector, which is the signature of a single "
         "miscounting detector rather than of a map error. Which of these are survey "
         "errors, detector faults or neither cannot be settled without independent ground "
         "truth, and is recorded in Section 8.8."
         % (ctl25["false_flags"], ctl1["false_flags"],
            max(f["residual_pct"] for f in ctl25["flagged"]),
            max(f["residual_pct"] for f in ctl1["flagged"])))
    figure(doc, "fig09.png",
           "Figure 9. Map errors of four kinds injected into surveyed junctions and flagged "
           "by the counts, with exact repair rates; both corridors.")

    h2(doc, "8.5 Fault attribution without a map")
    rows = []
    for mode, mag, nm in (("none", 0.0, "no fault (control)"),
                          ("scale", 0.99, "under-count by 1 %"),
                          ("scale", 0.95, "under-count by 5 %"),
                          ("offset", -2.0, "constant loss of 2 vehicles"),
                          ("offset", -8.0, "constant loss of 8 vehicles"),
                          ("stuck", 0.0, "detector repeats a constant")):
        a, b = case(fs, mode, mag), case(fr, mode, mag)
        if a and b:
            rows.append([nm, pct(a["detection_rate"]), pct(a["attribution_top1"]),
                         pct(b["detection_rate"]), pct(b["attribution_top1"]),
                         pct(b["type_correct"]) if "type_correct" in b else "-"])
    table(doc, ["Injected fault", "Surveyed: detected", "Surveyed: named 1st",
                "Recovered: detected", "Recovered: named 1st", "Recovered: type correct"],
          rows, cap="Table 6: Fault Attribution on Surveyed and on Recovered Relations, M25",
          widths=[1.9, 0.85, 0.85, 0.85, 0.85, 0.9], size=9, align_left_cols=(0,))
    s95 = case(fr, "scale", 0.95)
    para(doc,
         "On recovered relations, with no map, detection is at or above the surveyed-map "
         "figure in almost every case, and a detector with a large fault is named first "
         "more often. A 5 %% under-count is sized at %.2f %% (median over trials). Small "
         "constant offsets are named first less often, and the no-fault alarm rate rises "
         "from %s to %s, because each detector belongs to more relations and each is "
         "tested at 1 %%. The two runs draw their %d tested detectors from different "
         "line-ups (%d and %d eligible) with %d and %d spans per detector, so the "
         "comparison is not paired."
         % (s95["estimated_size_median"], pct(case(fs, "none", 0.0)["detection_rate"]),
            pct(case(fr, "none", 0.0)["detection_rate"]), fr["detectors_tested"],
            fs["detectors_eligible"], fr["detectors_eligible"], fs["repeats_per_detector"],
            fr["repeats_per_detector"]))
    figure(doc, "fig10.png",
           "Figure 10. Detection and first-rank attribution of injected faults, on the "
           "surveyed map and on relations recovered from the counts; M25.")

    h2(doc, "8.6 Correction of the named detector's output")
    rows = []
    for mode, mag, nm in (("scale", 0.90, "under-count by 10 %"),
                          ("scale", 0.95, "under-count by 5 %"),
                          ("scale", 1.05, "over-count by 5 %"),
                          ("offset", -8.0, "constant loss of 8 vehicles"),
                          ("offset", 15.0, "constant gain of 15 vehicles"),
                          ("stuck", 0.0, "detector repeats a constant"),
                          ("none", 0.0, "no fault (control)")):
        row = [nm]
        for d in (cor25, cor1):
            e = case(d, mode, mag)
            if mode == "none":
                row += ["0.00", "%.2f" % (e["innocent_corrections"]
                                          * e["innocent_mae_introduced"] / e["trials"]),
                        "-"]
            else:
                row += ["%.2f" % e["mae_before"], "%.2f" % e["mae_after"]["auto"],
                        pct(net_removed(e), 0)]
        rows.append(row)
    table(doc, ["Injected fault", "M25 MAE as received", "M25 MAE corrected",
                "M25 net error removed", "M1 MAE as received", "M1 MAE corrected",
                "M1 net error removed"], rows,
          cap="Table 6a: Output of the Faulty Detector Before and After Correction, "
              "Recovered Relations, No Map (vehicles per interval)",
          widths=[1.75, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8], size=8.8, align_left_cols=(0,))
    nets = [net_removed(e) for d in (cor25, cor1) for e in d["cases"] if e["mode"] != "none"]
    para(doc,
         "The diagnosis of Section 8.5 is closed into a correction of the instrument's "
         "output. Over each faulted span the detector named first is corrected, whichever "
         "detector that is: where the span is classified as proportional, its counts are "
         "rescaled by the fitted proportion; where constant, the fitted offset is removed; "
         "where the fault cannot be typed, as for a detector repeating a constant, each "
         "count is replaced by the value that closes the calibrated relations containing "
         "the detector, the median over those relations being taken. The error of the "
         "faulty detector's output against its own clean record is measured before and "
         "after. Every trial counts: a missed detection leaves the fault in place, and a "
         "wrong attribution leaves the faulty detector uncorrected and corrupts an "
         "innocent one, whose added error is charged against the result. The net error "
         "removed is the reduction in total absolute error over all detectors, after that "
         "charge. It lies between %s and %s across all faults injected on the two "
         "corridors (%d relations recovered on the reference half of the M25, %d on the "
         "M1; %d detectors tested per corridor, %d spans each)."
         % (pct(min(nets), 0), pct(max(nets), 0), cor25["relations"], cor1["relations"],
            cor25["detectors_tested"], cor25["repeats"]))
    para(doc,
         "The model-inverting correction is the more accurate where it applies: for a 5 %% "
         "under-count on the reference corridor it leaves %.2f vehicles per interval "
         "against %.2f for substitution from the relations, because it keeps the "
         "detector's own interval-to-interval detail. Substitution is what makes a stuck "
         "detector correctable at all. On clean data the correction fires on %d of %d "
         "spans on the reference corridor and %d of %d on the replication corridor, "
         "adding %.2f and %.2f vehicles per interval of error to the detector it names."
         % (case(cor25, "scale", 0.95)["mae_after"]["parametric"],
            case(cor25, "scale", 0.95)["mae_after"]["substitution"],
            case(cor25, "none", 0.0)["innocent_corrections"], case(cor25, "none", 0.0)["trials"],
            case(cor1, "none", 0.0)["innocent_corrections"], case(cor1, "none", 0.0)["trials"],
            case(cor25, "none", 0.0)["innocent_mae_introduced"],
            case(cor1, "none", 0.0)["innocent_mae_introduced"]))
    figure(doc, "fig12.png",
           "Figure 11. Error of the faulty detector's output, as received and after "
           "correction, for each injected fault; relations recovered from the counts, no "
           "map; both corridors. Logarithmic scale.")

    rows = []
    for nm, d in (("M25", yf25), ("M1", yf1)):
        for mode, mag in YF_CASES:
            c = yf_case(d, mode, mag)
            lab = {"scale": "%+d %%" % round(100 * (mag - 1)),
                   "offset": "%+d veh" % mag, "stuck": "stuck"}[mode]
            row = [nm, lab]
            for a in ("yf_surveyed", "ours_surveyed", "ours_recovered"):
                row += [pct(c[a]["named_correctly"], 0), pct(c[a]["net_error_removed"], 0)]
            rows.append(row)
    table(doc, ["Corridor", "Fault", "Entry 21, map: named", "Entry 21, map: net removed",
                "Ours, map: named", "Ours, map: net removed", "Ours, no map: named",
                "Ours, no map: net removed"], rows,
          cap="Table 6c: The Closest Art to Claim 13 on the Same Injected Faults",
          widths=[0.55, 0.65, 0.8, 0.85, 0.75, 0.8, 0.8, 0.85], size=8.2)
    cv1, cv25 = yf1["coverage"], yf25["coverage"]
    para(doc,
         "Entry 21 was implemented as published in its static form: per-sensor ratios "
         "estimated by the method of moments from nodal balance on the surveyed map, "
         "given the same reference half, the same two-day spans, the same 1 %% threshold "
         "rule and the same scoring as the invention, with its estimate bounded to a "
         "plausible range and sensors it cannot determine barred from being named, both "
         "in its favour. All three arms see identical faults at %d detectors per corridor "
         "that every arm can address. On the same surveyed map, the invention's "
         "attribution already names the faulty detector far more often than entry 21; on "
         "recovered relations, with no map, it does so about as often or more often. "
         "Entry 21's "
         "estimate is sound given enough data: over two weeks it recovers an injected 10 "
         "%% fault to within a median of %.3f in the ratio (%d detectors). Over a two-day "
         "span it is too noisy to invert reliably, and its model is multiplicative only, "
         "so constant and stuck faults fall outside it; for a proportional fault that "
         "persists for weeks on a well-surveyed network it would serve. What the invention "
         "adds is attribution from the pattern across several relations, which works on "
         "short spans and on any fault type, and relations that need no map. The number "
         "of detectors each can address is similar: %d and %d with a determined ratio "
         "under entry 21, against %d and %d in two or more recovered relations, on the "
         "M25 and M1."
         % (yf25["pool"], yfs["median_abs_ratio_error"], yfs["detectors"],
            cv25["yf_surveyed_identifiable"], cv1["yf_surveyed_identifiable"],
            cv25["ours_recovered_in_two_or_more"], cv1["ours_recovered_in_two_or_more"]))

    h2(doc, "8.6a Faults found on unmodified counts")
    mname = {3: "March", 4: "April", 5: "May", 6: "June"}
    rows = []
    for r in rfm["runs"]:
        rows.append([r["road"], mname[r["month"]], r["reports"], r["reports_reference_chance"],
                     "%d of %d" % (r["reported_failed"], r["reported_admitted"]),
                     "%d of %d" % (r["control_failed"], r["control"])])
    pm, pd = rfm["pooled_per_month"], rfm["pooled_per_detector"]
    rows.append(["pooled", "per corridor-month", sum(r["reports"] for r in rfm["runs"]),
                 sum(r["reports_reference_chance"] for r in rfm["runs"]),
                 "%d of %d (%s)" % (pm["reported_failed"], pm["reported"],
                                     pct(pm["reported_failed"] / pm["reported"], 0)),
                 "%d of %d (%s)" % (pm["control_failed"], pm["control"],
                                     pct(pm["control_failed"] / pm["control"], 0))])
    rows.append(["pooled", "per detector", "-", "-",
                 "%d of %d (%s)" % (pd["reported_failed"], pd["reported"],
                                     pct(pd["reported_failed"] / pd["reported"], 0)),
                 "%d of %d (%s)" % (pd["control_failed"], pd["control"],
                                     pct(pd["control_failed"] / pd["control"], 0))])
    table(doc, ["Corridor", "Month scanned", "Reports, second half", "Reports, first half "
                "(chance)", "Reported detectors dead within 3 months", "Control detectors "
                "dead within 3 months"], rows,
          cap="Table 6b: Detectors Named on Unmodified Counts, March to June 2025, and "
              "Whether They Failed Afterwards",
          widths=[0.7, 1.1, 0.9, 0.9, 1.3, 1.3], size=8.5)
    ex1, ex2 = rfx["M1/4669A"], rfx["M25/5814A"]
    pre = [d["detector_over_partner_a"] for d in ex1["days"]
           if d["date"] < "2025-03-19" and d["detector_over_partner_a"]]
    drift = [d for d in ex1["days"] if "2025-03-20" <= d["date"] <= "2025-03-23"]
    clean_days = [d for d in ex2["days"] if d["partner_a_over_partner_b"]
                  and abs(d["partner_a_over_partner_b"] - 1) <= 0.005
                  and d["detector_over_partner_a"] and d["detector_over_partner_a"] < 0.99]
    b25 = rfu["corridors"]["M25"]["bracketing"]
    b1 = rfu["corridors"]["M1"]["bracketing"]
    para(doc,
         "Nothing is injected here. For each corridor and each month from March to June "
         "2025, the relations are recovered from the first half of the month, with no map, "
         "and the second half is scanned in two-day spans. A detector is reported only "
         "when every one of its relations, at least two, deviates in the span. The same "
         "scan over the first half, against which the thresholds were set, gives the "
         "chance column; it is in-sample and therefore optimistic, which is why the "
         "outcome check carries the weight. That check uses records the method never "
         "saw: whether the detector stopped reporting altogether (any month at least "
         "95 %% absent) in the three months after the month scanned, fetched afterwards "
         "from the same public service, against %d randomly drawn controls per "
         "corridor-month. Both groups are admitted by one rule judged before any report, "
         "at least 90 %% of records present in the first half of the month, so that a "
         "detector already failing is not counted. Pooled over the eight corridor-months, "
         "%d of %d reported detectors failed against %d of %d controls (one-sided Fisher "
         "exact p = %s); counting each detector once, %d of %d against %d of %d (p = "
         "%s). A second check, whether the reported detector's two closest agreeing "
         "partners still agree with each other while contradicting it, was run for March "
         "only and is weak: it takes the median over the whole two-day span and confirms "
         "%d of %d testable reports, because most reported faults last hours or days "
         "within the span."
         % (rfm["runs"][0]["control"], pm["reported_failed"], pm["reported"],
            pm["control_failed"], pm["control"], sci(pm["fisher_exact_p_one_sided"]),
            pd["reported_failed"], pd["reported"], pd["control_failed"], pd["control"],
            sci(pd["fisher_exact_p_one_sided"]), b25["confirmed"] + b1["confirmed"],
            b25["testable"] + b1["testable"]))
    para(doc,
         "Two reports illustrate what is found. %s agreed with its closest partner %s at "
         "a ratio between %.3f and %.3f for the first eighteen days of March. From 20 "
         "March the ratio fell to %s; the detector was reported by the method, stopped "
         "reporting on %s, and was absent for %s of April, %s of May and %s of June: a "
         "detector drifting to under-count and then failing, named before it failed. "
         "%s lies between %s and %s, which agree with each other to within 0.5 %% on "
         "almost every day of March; on %s the partners agreed to that precision while "
         "%s read between %.1f %% and %.1f %% low. Its absent records then rose to %s, "
         "%s and %s over April, May and June."
         % (ex1["detector"], ex1["partners"][0], min(pre), max(pre),
            ", ".join("%.3f" % d["detector_over_partner_a"] for d in drift),
            "%d March" % int(ex1["first_day_absent"][8:]),
            pct(ex1["apr_jun_absent_share"]["2025-04"], 0),
            pct(ex1["apr_jun_absent_share"]["2025-05"], 0),
            pct(ex1["apr_jun_absent_share"]["2025-06"], 0),
            ex2["detector"], ex2["partners"][0], ex2["partners"][1],
            ", ".join(d["date"][8:].lstrip("0") for d in clean_days) + " March",
            ex2["detector"],
            100 * (1 - max(d["detector_over_partner_a"] for d in clean_days)),
            100 * (1 - min(d["detector_over_partner_a"] for d in clean_days)),
            pct(ex2["apr_jun_absent_share"]["2025-04"]),
            pct(ex2["apr_jun_absent_share"]["2025-05"]),
            pct(ex2["apr_jun_absent_share"]["2025-06"])))
    pj = rf25["persistence_june"]
    para(doc,
         "Other checks were weaker and are stated as found. Bin-sum integrity, whether a "
         "record's length-class counts add up to its total, was elevated in %d of %d and "
         "%d of %d reports. Of the reported M25 detectors whose bias could be measured in "
         "June under the March relations, %d of %d kept the sign of their March bias "
         "(one-sided binomial p = %.2f). Every reported detector, including the one that "
         "stopped reporting, is still listed as active by the service, so its status "
         "field carries no information. One M25 report, a slip-road detector whose count "
         "rose by about two thirds in the last week of March while neighbouring "
         "detectors fell silent, is more probably a change in the road, such as a "
         "diversion, than a detector fault: the method reports a broken relation, and "
         "which of the two broke it is not decided by the counts."
         % (rf25["binsum"]["reports_with_rate_over_2x_own_reference"], rf25["binsum"]["of"],
            rf1["binsum"]["reports_with_rate_over_2x_own_reference"], rf1["binsum"]["of"],
            pj["same_sign_as_march"], pj["same_sign_of"],
            pj["same_sign_binomial_p_one_sided"]))

    h2(doc, "8.7 Certified intervals")
    rows = []
    for nm, d in (("M25, recovered relations, no map", cr25),
                  ("M25, surveyed map", conf),
                  ("M1, recovered relations, no map", cr1),
                  ("M1, surveyed map", cs1)):
        rows.append([nm, d["values_checked"], "%.1f %%" % d["bounded_pct"],
                     "%.1f %%" % d["coverage_pct"], "%.1f %%" % d["point_estimate_inside_pct"],
                     "%.1f" % d["median_width_vehicles"]])
    table(doc, ["Constraint set", "Values checked", "Bounded by the constraints",
                "True value inside interval", "Reconstructed value inside interval",
                "Median width, vehicles"], rows,
          cap="Table 6d: Certified Intervals (Claim 10) on the Claimed and the Surveyed "
              "Constraint Sets", widths=[2.0, 0.8, 0.9, 0.9, 1.0, 0.8], size=8.8,
          align_left_cols=(0,))
    para(doc,
         "For each reconstructed value, the smallest and largest values consistent with the "
         "observed records under the relations are found by two linear programs; a value "
         "the relations do not pin down is reported as unbounded rather than given a width. "
         "Measured on the claimed configuration, relations recovered from the training "
         "view with no map, the interval contains the true withheld value in %.1f %% and "
         "%.1f %% of cases on the two corridors, against %.1f %% and %.1f %% under the "
         "surveyed map, over %d intervals sampled on each. Wider intervals on the "
         "reference corridor reflect its greater number of absent values sharing a "
         "relation."
         % (cr25["coverage_pct"], cr1["coverage_pct"], conf["coverage_pct"],
            cs1["coverage_pct"], cr25["intervals_examined"]))

    para(doc,
         "Claim 11 describes what the projection unit does when the bands of an interval "
         "cannot all be met: it computes the shortfall, reports the interval, and does not "
         "widen the bands. It is kept as a fallback describing that behaviour and is not "
         "relied on as a fault indicator, which is the role of Claim 13.")

    h2(doc, "8.8 Operating envelope and what is not established")
    bullets(doc, [
        ("Two corridors; a second month (June 2025) on the reference corridor for "
         "recovery and reconstruction only. " if jun else "Two corridors, one month. ") +
        "Recovery, reconstruction, map audit and detector "
        "correction are replicated on the M1; the full fault-attribution table (Section "
        "8.5) is measured on the M25 only.",
        "Junctions where two slip roads share a section are mostly missed (%d of %d on "
        "the M25). Networks dense in such junctions will recover fewer relations."
        % (rs25["4"]["recovered"], rs25["4"]["of"]),
        "Relations involving detectors the survey omits (%d on the M25) are unjudged: "
        "no ground truth exists for them." % v25["categories"]["unmapped_site"],
        "The map audit's flags on the uncorrupted survey are unresolved between survey "
        "error, detector fault and seasonal effect. Independent ground truth is needed.",
        "Replacement of a detector by a near neighbour is flagged in about 60 % of "
        "trials only.",
        "The irreconcilability report of Claim 11 is not relied on as a fault "
        "indicator (Section 8.7).",
        "The no-fault alarm rate of fault attribution on recovered relations is higher "
        "than on the surveyed map (Section 8.5); a corridor-wide false-alarm rate is not "
        "measured for either.",
        "Periodic re-recovery on a live feed, alternative embodiment 7.1(b), is not "
        "measured.",
        "%d recovered relations on the reference corridor lie outside the span of the "
        "survey. About half recur every month and are probably real; the rest are "
        "probably spurious (Section 8.2a)." % v25["categories"]["outside_map"],
        "The closest-art baselines of Table 3b are the inventor's implementations of "
        "published methods, not the authors' code.",
        "Detector correction (Section 8.6) is measured on injected faults over the span "
        "in which each was estimated. On unmodified counts (Section 8.6a) the detectors "
        "named are checked against independent evidence, but the true size of their "
        "faults is not known, so the correction cannot be scored there.",
    ])

    # ============================================================== 9
    h1(doc, "9. Contemplated Prototype and Planned Validation")
    para(doc,
         "The method is implemented and runs end to end on archived operational data "
         "(Section 8). Recovery on the 367-detector reference corridor takes %.0f s and "
         "reconstruction of a month under the recovered constraints %.0f s on a single "
         "desktop processor, with no specialised hardware. What has not been done is "
         "operation against a live detector feed and validation of the map audit against "
         "an independently verified survey."
         % (v25["seconds"], c25["recovered"]["seconds"]))
    table(doc, ["#", "Planned measurement", "What it would establish", "Claims evidenced"], [
        ["1", "Map audit flags on the uncorrupted M25 survey checked against site "
              "inspection or maintenance logs", "whether flagged relations are survey "
              "errors, detector faults or neither", "12, 20"],
        ["2", "Recovery repeated monthly over a year on one corridor",
         "stability of the recovered constraint set; detection of a road change", "1"],
        ["3", "Live-feed operation with reconstruction and correction per reporting cycle",
         "latency within the reporting interval", "18-22"],
        ["4", "Correction carried forward to the counts following the fitted span",
         "persistence of the correction of Section 8.6", "13-17"],
        ["5", "Certified intervals on recovered relations", "Section 8.7 on the claimed "
              "constraint set", "10"],
        ["6", "Detectors named on unmodified counts (Section 8.6a) checked against the "
              "operator's maintenance logs", "that named detectors are faulty in fact, "
              "beyond the bracketing and failure evidence", "13, 19"],
    ], cap="Table 7: Planned Measurements", widths=[0.3, 2.5, 2.3, 0.9], size=9,
        align_left_cols=(1, 2))

    # ============================================================== 10
    h1(doc, "10. Aspects of the Invention Requiring Protection (Claims)")
    para(doc,
         "The following elements are considered novel and inventive and are proposed for "
         "protection. Claims 1, 13 and 18 are independent. The set is drafted on four "
         "principles. First, each independent claim recites in full the recovery of the "
         "constraint structure from the counts by the specific stages of Section 7, "
         "because that is the element no reference in Section 3 discloses; recovery of a "
         "relation by sparse regression, selection against a residual and triangle "
         "pruning are each conceded to entries 8 to 11 and 17 in general form. Second, "
         "each independent claim ends in a change to the record the detectors produce: "
         "absent records reconstructed under the recovered relations imposed as hard "
         "constraints (Claims 1 and 18), or the output of a miscounting detector "
         "corrected on the evidence of those relations (Claim 13). Third, every quantity a claim relies on is defined in the "
         "claim, so that no term is left to the description. Fourth, no claim is directed "
         "to a computer-readable medium or to a set of instructions as such, and none "
         "recites a numerical procedure standing alone.")
    figure(doc, "fig11.png",
           "Figure 12. Structure of the claim set. Three independent claims carry the "
           "recovery-and-reconstruction method, the correction of a miscounting "
           "detector's output and the system; the map audit is a dependent use.",
           width=6.4)

    def recovery(a):
        """Steps (b)-(f) of the recovery, lettered from `a`, written out in full."""
        L = [chr(ord(a) + n) for n in range(5)]
        return (
            "(%s) for pairs of detectors having at least a predetermined number of "
            "intervals in which both reported, computing over those intervals a "
            "through-origin least-squares coefficient of the counts of one detector on "
            "the counts of the other, and a relative residual equal to the median "
            "absolute difference of their counts divided by the larger of their two mean "
            "counts, and retaining as a pair relation each pair whose coefficient lies "
            "within a rounding tolerance of unity and whose relative residual is within a "
            "pair tolerance; "
            "(%s) removing each pair relation (i, k) for which there exists a detector j "
            "such that (i, j) and (j, k) are both pair relations each having a smaller "
            "relative residual than (i, k), the remaining pair relations being adjacent "
            "pairs, whereby the order of the detectors along the carriageway is recovered "
            "from the counts; "
            "(%s) deriving a retention limit as a predetermined multiple of the median "
            "relative residual of the adjacent pairs, and adopting as retained relations "
            "the adjacent pairs whose relative residual is within the retention limit; "
            "(%s) for each detector i and each of a predetermined number of detectors k "
            "most correlated with it whose mean count lies within a predetermined ratio of "
            "that of i and which do not form a retained relation with i: forming the "
            "residual series of the counts of i less those of k over intervals in which "
            "both reported; ranking every other detector j by the magnitude of the "
            "correlation of its counts with that residual series over intervals in which "
            "i, k and j all reported; fitting to the residual series by least squares the "
            "counts of subsets of a predetermined number of highest-ranked detectors; and "
            "forming a candidate relation from each subset whose fitted coefficients each "
            "lie within the rounding tolerance of +1 or -1, the rounded sign of each "
            "coefficient denoting whether the corresponding detector adds vehicles to or "
            "removes vehicles from the carriageway between i and k; "
            "(%s) adopting a candidate relation as a retained relation only if its "
            "relative residual, being the median absolute value of the signed sum of its "
            "members' counts divided by the largest mean count among its members, is "
            "within the retention limit, and removal of any one of its members increases "
            "that relative residual by at least a predetermined necessity factor; "
            % tuple(L))

    def constrain(a):
        """Steps (g)-(h): calibrated bands and the hard-constrained projection."""
        return (
            "(%s) for each retained relation, fitting by least squares, over intervals in "
            "which all its members reported, a coefficient of one member and an offset, "
            "and deriving a two-sided tolerance band equal to a predetermined upper "
            "quantile of the absolute deviation of the relation so calibrated; "
            "(%s) reconstructing the absent records of an interval by projecting a prior "
            "estimate of them onto the set of values satisfying, jointly, every band of "
            "every relation of the constraint set containing an absent record in that "
            "interval, the observed records of that interval being held at their observed "
            "values and the bands being imposed as hard two-sided inequality constraints "
            "and not as a penalty term; "
            % (a, chr(ord(a) + 1)))

    receive = ("(a) receiving, from the detectors over a communication link, a dataset "
               "of vehicle counts indexed by detector and by measurement interval in which "
               "records are absent for some detectors in some intervals, without receiving "
               "a network map, a junction register, a detector naming convention or "
               "detector coordinates; ")

    h2(doc, "A. Method claims - restoring the record under relations recovered from the counts")
    claim(doc, 1,
          "A method of restoring the measurement record produced by a network of roadside "
          "vehicle-counting instruments disposed on a carriageway and on slip roads joining "
          "it (the instruments being referred to below also as detectors), by recovering from the instruments' own counts the conservation relations "
          "that physically connect them, the connectivity of the instruments not being "
          "supplied, the method being performed by a processor coupled to a count archive "
          "of the instruments and comprising: " + receive + recovery("b") +
          constrain("g").replace("every relation of the constraint set",
                                 "every retained relation") +
          "and thereafter writing to the count archive, in place of the received dataset, "
          "the dataset in which the absent records are replaced by the reconstructed "
          "values, whereby the measurement record of the instruments satisfies the "
          "recovered conservation relations within their bands.",
          independent=True)
    claim(doc, 2, "The method of Claim 1, wherein steps (b) to (g) are performed on the "
          "observed records only, so that no absent record contributes to a relation or "
          "band used to reconstruct it.")
    claim(doc, 3, "The method of Claim 1, wherein a network map is additionally received "
          "after steps (b) to (f), and the relations imposed in step (h) are the union of "
          "the retained relations and the relations of the said map.")
    claim(doc, 4, "The method of Claim 1, wherein the retained relations include relations "
          "of three or more instruments each containing an instrument disposed on a slip "
          "road, recovered without any indication of which instruments are disposed on "
          "slip roads or of the direction of flow on any slip road.")
    claim(doc, 5, "The method of Claim 1, wherein the retention limit is derived separately "
          "for each network from that network's own adjacent pairs, no limit being "
          "carried from one network to another.")
    claim(doc, 6, "The method of Claim 1, wherein the predetermined multiple is two, the "
          "necessity factor is one and a half, the rounding tolerance is 0.3 and the "
          "upper quantile is the 0.95 quantile.")
    claim(doc, 7, "The method of Claim 6, wherein the predetermined number of intervals is "
          "400, the pair tolerance is 4 % of the larger mean count, the predetermined "
          "number of most correlated instruments is six with the predetermined ratio "
          "lying between one half and two, and the subsets are of one to three of the "
          "eight highest-ranked instruments.")
    claim(doc, 8, "The method of Claim 1, wherein, where the projection of step (h) does "
          "not reach the said set for an interval and a linear program establishes that "
          "the set is not empty, the reconstructed values are taken as the point of the "
          "said set nearest the prior estimate in a weighted L1 distance, obtained by a "
          "further linear program, and not as a vertex of the set.")
    claim(doc, 9, "The method of Claim 1, wherein steps (b) to (f) are also applied to "
          "the counts of an earlier period, and a retained relation is imposed in step "
          "(h) only if the same relation, over the same instruments with the same signs, "
          "was also retained from the earlier period.")
    claim(doc, 10, "The method of Claim 1, further comprising outputting with each "
          "reconstructed value an interval obtained by minimising and by maximising that "
          "value over the set of step (h), together with an indication of whether that "
          "value is bounded by the said set.")
    claim(doc, 11, "The method of Claim 1, wherein, where no values satisfy the bands of "
          "step (h) for an interval, the smallest uniform widening of those bands that "
          "admits a solution is computed by a linear program, the interval is reported "
          "as irreconcilable together with that widening in vehicles, and the value "
          "nearest to the said set reached by the projection is retained without "
          "widening the bands.")
    claim(doc, 12, "The method of Claim 1, further comprising: receiving, after steps (b) to (f), a network map "
          "specifying, for each of a plurality of map relations, member instruments and "
          "the signs with which they enter a conservation relation; computing for each "
          "map relation its relative residual, being the median absolute value of the "
          "signed sum of its members' counts over intervals in which all its members "
          "reported divided by the largest mean count among its members; flagging each "
          "map relation whose relative residual exceeds the retention limit; selecting as "
          "the repair of each flagged map relation, from among the retained relations "
          "sharing at least two instruments and at least half of its members, the one "
          "having the smallest relative residual; and outputting a record naming each "
          "flagged map relation and its repair.")

    h2(doc, "B. Method claims - correcting the record of a miscounting instrument")
    claim(doc, 13,
          "A method of correcting the measurement record produced by a miscounting "
          "instrument in a network of roadside vehicle-counting instruments disposed on a "
          "carriageway and on slip roads joining it (the instruments being referred to below also as detectors), the connectivity of the instruments "
          "not being supplied, the method being performed by a processor coupled to a "
          "count archive of the instruments and comprising: " + receive + recovery("b") +
          "each of the following steps (g) to (k) using only the retained relations so "
          "recovered, and no network map: "
          "(g) for each retained relation, fitting by least squares, over intervals of a "
          "reference period in which all its members reported, a coefficient of one "
          "member and an offset, whereby a calibrated residual of the relation is defined "
          "for each interval; "
          "(h) computing for each retained relation, over a span of consecutive intervals "
          "outside the reference period, the mean of its calibrated residual, and "
          "determining that the relation deviates where that mean exceeds a predetermined "
          "quantile of the empirical distribution of the same statistic at that relation "
          "over spans of the reference period; "
          "(i) where a retained relation deviates, fitting, for each instrument belonging "
          "to at least two retained relations, by weighted least squares a single bias "
          "against the coefficients with which that instrument enters each of those "
          "relations, and naming the instrument whose fitted bias removes the greatest "
          "weighted sum of squared deviations of the span means; "
          "(j) classifying the fault of the named instrument as flow-proportional or as "
          "flow-independent by fitting both models over the higher-flow and the "
          "lower-flow parts of the span and selecting the better-fitting model together "
          "with its fitted magnitude; "
          "(k) correcting the counts of the named instrument over the span by inverting "
          "the selected model with its fitted magnitude; "
          "and thereafter writing to the count archive the corrected counts in place of "
          "the received counts of the named instrument over the span.",
          independent=True)
    claim(doc, 14, "The method of Claim 13, wherein, where the fault cannot be classified "
          "in step (j), each count of the named instrument over the span is instead "
          "replaced by the median, over the retained relations containing that "
          "instrument, of the value that sets the calibrated residual of that relation "
          "to zero.")
    claim(doc, 15, "The method of Claim 13, further comprising outputting a maintenance "
          "record naming the instrument, the type of its fault and its fitted magnitude.")
    claim(doc, 16, "The method of Claim 13, wherein an instrument is named in step (i) only "
          "where it belongs to at least two retained relations and every retained "
          "relation containing it deviates in the span.")
    claim(doc, 17, "The method of Claim 13, wherein the measurement interval is fifteen "
          "minutes, the span is 192 consecutive intervals and the predetermined quantile "
          "is the 0.99 quantile.")

    h2(doc, "C. System claims")
    claim(doc, 18,
          "A traffic-data processing system comprising: a plurality of roadside "
          "vehicle-counting instruments disposed on a carriageway and on slip roads "
          "joining it (referred to below also as detectors); a communication link conveying from the instruments a vehicle "
          "count per instrument per measurement interval; a count archive holding the "
          "said counts with absent records marked; an output interface; and a processor "
          "coupled to the count archive and to the output interface, the processor being "
          "configured to perform, without access to a network map of the instruments: " +
          recovery("a") +
          constrain("f").replace("every relation of the constraint set",
                                 "every retained relation") +
          "and (h) writing into the count archive, in place of the absent records, the "
          "reconstructed values, and supplying the counts so restored through the output "
          "interface.",
          independent=True)
    claim(doc, 19, "The system of Claim 18, wherein the processor is further configured to "
          "perform steps (g) to (k) of Claim 13 on the retained relations and to write "
          "the counts of the named instrument so corrected into the count archive in "
          "place of the counts received from it.")
    claim(doc, 20, "The system of Claim 18, wherein the processor is further configured to "
          "receive a network map, to flag each relation of the map whose relative "
          "residual exceeds the retention limit, and to select a repair of each flagged "
          "relation from among the retained relations sharing at least two of its "
          "instruments.")
    claim(doc, 21, "The system of Claim 18, wherein the output interface is connected to a "
          "traffic-control computer, to which the restored counts are supplied in place "
          "of the counts held before restoration.")
    claim(doc, 22, "The system of Claim 18, wherein the instruments are inductive-loop "
          "detectors and the retained relations include relations between instruments on "
          "the carriageway and instruments on slip roads, whose signs the processor "
          "determines.")
    para(doc,
         "The alternative embodiments 7.1(b) periodic re-recovery, 7.1(d) wider integer "
         "coefficients and 7.1(e) separation of detector faults from map errors are "
         "deliberately excluded from the claim set, as they have not been reduced to "
         "practice. So is carrying a correction under Claim 13 forward to counts received "
         "after the span on which it was fitted, which has not been measured. They are "
         "disclosed so that priority is preserved should they be claimed later.",
         lead="Note on scope.")

    # ============================================================== 11
    h1(doc, "11. Technology Readiness Level (TRL)")
    para(doc,
         "The method is implemented in full and has been validated on archived operational "
         "counts from two motorway corridors at full corridor scale, with each claimed "
         "mechanism measured against a control and against the surveyed alternative "
         "(Section 8). It has not been operated against a live detector feed, and the map "
         "audit has not been checked against independently verified ground truth. "
         "Readiness is therefore assessed at TRL 4 - technology validated in the "
         "laboratory. Completion of measurements 1 and 3 of Table 7 would support TRL 5.")
    trl = doc.add_table(rows=4, cols=9)
    trl.style = "Table Grid"
    trl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for lo, hi, lab in ((0, 2, "Research"), (3, 5, "Development"), (6, 8, "Deployment")):
        m = trl.rows[0].cells[lo].merge(trl.rows[0].cells[hi])
        m.text = ""
        pp = m.paragraphs[0]
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(pp, lab, size=9.5, bold=True)
    names = ["Basic principles observed", "Technology concept formulated",
             "Experimental proof of concept", "Technology validated in lab",
             "Validated in relevant environment", "Demonstrated in relevant environment",
             "Prototype in operational environment", "System complete and qualified",
             "Proven in operational environment"]
    for i in range(9):
        for r, txt, sz, bold in ((1, "TRL %d" % (i + 1), 9, True), (2, names[i], 7.8, False),
                                 (3, "\u2713" if i < 4 else "", 12, True)):
            c = trl.rows[r].cells[i]
            c.text = ""
            pp = c.paragraphs[0]
            pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _run(pp, txt, size=sz, bold=bold)
            c.width = Inches(0.71)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    _run(p, "Current TRL: Level 4 \u2014 Technology Validated in Laboratory.", size=11,
         bold=True)

    # ============================================================== 12
    h1(doc, "12. Note on Filing")
    para(doc, "Seven matters are flagged for the IPR & TT Cell.")
    para(doc,
         "subject-matter eligibility. The invention is a computer-related invention, and "
         "an objection under Section 3(k) of the Patents Act, 1970 covering a mathematical "
         "method, a computer programme per se and algorithms should be expected. The "
         "response proposed is that the claims receive measurements from physical "
         "instruments, recover from them the conservation law of the physical network "
         "those instruments observe, and change the record those instruments produce. The "
         "strongest form of that response is Claim 13: it names a physical instrument that "
         "is miscounting and corrects that instrument's output, and the correction is "
         "measured against the instrument's own clean record (Section 8.6); on "
         "unmodified counts, detectors it names fail outright in the following months "
         "at %.1f times the rate of other detectors (Section 8.6a). Claim 1 "
         "rests on reduced reconstruction error, both mean and root-mean-square, and "
         "reduced violation of conservation (Section 8.3). One respect in which the "
         "response is weaker than it could be is recorded here rather than left for the "
         "examiner: the prototype does not operate a control process. For that reason no "
         "independent claim rests on a control effect: each ends in the restored or "
         "corrected record of the instruments, which is measured, and the supply to a "
         "traffic-control computer is confined to dependent Claim 21. Microsoft Technology Licensing v. Assistant Controller "
         "(Madras High Court, 2024 SCC OnLine Mad 285), setting aside a refusal of an "
         "invention handling sensor data, supports the response. Kroll v. Controller "
         "(Delhi High Court, 2025), refusing "
         "a data-processing claim for want of technical effect, should be distinguished on "
         "the ground that the effect here is on the output of a measuring instrument."
         % ((rfm["pooled_per_month"]["reported_failed"] / rfm["pooled_per_month"]["reported"])
            / (rfm["pooled_per_month"]["control_failed"] / rfm["pooled_per_month"]["control"])),
         lead="First:")
    para(doc,
         "inventive step, the decisive objection. An independent strict review of an "
         "earlier draft identified entry 8, and a later search identified entry 17, the "
         "recovery of meter topology in electricity distribution from the same kind of "
         "conservation identity. The attack to be expected combines entry 8, 9 or 17 with "
         "entry 1 or 2. The answer relied on is measured, not argued: every one of those "
         "methods, run on the same counts with advantages it would not have in use, "
         "including a sparse rotation of entry 8, Lasso, and entry 17 with every detector "
         "tried as parent, recovers few slip-road junctions (Table 3b); and the element "
         "responsible is isolated by a controlled ablation (Table 3a). The weak point that "
         "remains is that the baselines are the inventor's own implementations of "
         "published methods. A search directed at the claims found two further "
         "references that narrow them, both conceded in Section 3: entry 21 corrects a "
         "traffic sensor's bias from nodal balance on a known network, which leaves Claim "
         "13 resting on the recovery of the relations, and entry 22 chooses the signs of "
         "water meters known to bound a zone, which leaves the signed coefficients of "
         "Claim 1 resting on recovery of membership and order, not on the signs alone. "
         "Neither recovers which sensors are joined.",
         lead="Second:")
    para(doc,
         "relation to the earlier draft of this disclosure (IDF-2). That draft led with a "
         "decomposition of fitted node offsets to find a bias present throughout the "
         "record, and with fault-onset detection from conservation residuals. The search "
         "found both met: the first by power-system network parameter error "
         "identification (entry 6), the second by Narasimhan and Mah (entry 5). They are "
         "not carried into this claim set. Fault attribution survives only in "
         "Claims 13 to 17, on relations recovered from the counts, and is carried through "
         "to a measured correction of the detector's output.", lead="Third:")
    para(doc,
         "claim breadth and the weakest positions. Claims 1 and 13 are the principal "
         "positions. The map audit, which an earlier draft claimed independently, is now "
         "dependent Claims 12 and 20: the concept of checking a register against "
         "measurements is conceded to entries 5 and 19. Claims 3 and 12 "
         "are exposed to entries 1, 2, 5 and 19 if read without the recovery steps of "
         "Claim 1. Claims 6, 7 and 17 recite the operative constants as fallbacks, each "
         "at the value used in every measurement of Section 8; Claim 16 recites the "
         "reporting rule used on the unmodified counts of Section 8.6a. Claims "
         "previously drafted to a numerical procedure standing alone, to ranked output, "
         "and to a list of environments without evidence have been removed.",
         lead="Fourth:")
    para(doc,
         "state of reduction to practice. The method runs end to end on archived data "
         "from two corridors over four months. Section 8.8 lists what is not "
         "established. The certified intervals of Claim 10 are now measured on the "
         "claimed configuration (Table 6d). The irreconcilability report of Claim 11 "
         "is kept only as a fallback describing the solver's behaviour. The correction of Claim 13 is measured on injected faults over the "
         "span on which it was fitted, and on unmodified counts only through the "
         "subsequent failure of the instruments it names. Some recovered relations are "
         "probably spurious (Section 8.2a). The rise in root-mean-square error reported against an "
         "earlier draft was traced to the restart rule of the projection unit and "
         "removed (Section 8.3). These limits should travel with any figure quoted from "
         "this disclosure.",
         lead="Fifth:")
    para(doc,
         "this note is internal and must not enter the filed specification, and neither "
         "may Sections 8, 9 and 12 in their present form. No part of this work has been "
         "publicly disclosed; no preprint or public repository exists, and none should be "
         "made until a priority date is secured. The Espacenet and InPASS searches are "
         "logged in Table A. Inventor details are recorded in the accompanying IDF-A.",
         lead="Sixth:")
    para(doc,
         "unity of invention. Claims 1, 13 and 18 share a single general inventive "
         "concept, and each recites it in full: conservation relations of a detector "
         "network recovered from its counts by the pair, ordering and junction stages "
         "under a self-derived limit, and then used to change the record the detectors "
         "produce. There are nonetheless two technical stories: restoring the record under "
         "recovered relations (Claims 1 to 12 and 18), and naming and correcting a "
         "miscounting instrument on recovered relations (Claims 13 to 17 and 19), which "
         "meets its own closest art (entry 21). The recommendation is to prosecute Claims "
         "1 to 12, 18 and 20 to 22 in the parent and to file Claims 13 to 17 and 19 as a divisional "
         "at the first sign of a unity objection, so that neither story is lost to it.",
         lead="Seventh:")

    endp = doc.add_paragraph()
    endp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    endp.paragraph_format.space_before = Pt(18)
    _run(endp, "\u2014\u2014\u2014\u2014\u2014 END OF THE DOCUMENT \u2014\u2014\u2014\u2014\u2014",
         size=11, bold=True)

    cp = doc.core_properties
    cp.author = "VIT IPR & TT Cell"
    cp.last_modified_by = "VIT IPR & TT Cell"
    cp.title = "Count-Derived Conservation Constraints - IDF-B"
    cp.comments = cp.category = cp.keywords = ""
    doc.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
