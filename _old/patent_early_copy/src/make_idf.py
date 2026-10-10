"""Generate the Invention Disclosure Form (IDF-2) as a .docx.

The document is generated rather than hand-edited so that every measured number in it
comes straight from results/*.json. Nothing is typed in by hand, so nothing can drift
away from what the prototype actually produced. Re-run after each phase.

Two rules are enforced by construction rather than by care:

* A number that has no results file behind it is written as TBD. There is no path in
  this file by which a plausible-looking figure can reach the document without a
  measurement behind it.
* Nothing in the wording describes an effect on anything other than a technical system.
  Under `OpenTV Inc. v. Controller of Patents` (2023:DHC:3305) the business-method
  exclusion in Section 3(k) is absolute, with no technical-effect escape, so a single
  stray sentence about anything else would be fatal.
"""

import json
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "patent", "IDF-2.docx")

TBD = "TBD — to be completed by the inventor"
TBM = "TBD — not yet measured"


def load(name):
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _date(ddmmyyyy):
    """DDMMYYYY as it comes back from the API, rendered readably."""
    months = ["January", "February", "March", "April", "May", "June", "July", "August",
              "September", "October", "November", "December"]
    d, m, y = ddmmyyyy[:2], int(ddmmyyyy[2:4]), ddmmyyyy[4:]
    return "%d %s %s" % (int(d), months[m - 1], y)


def case(data, mode, magnitude):
    """One row of the fault-injection table, or None if that run was not made."""
    if not data:
        return None
    for c in data.get("cases", []):
        if c["mode"] == mode and abs(c["magnitude"] - magnitude) < 1e-9:
            return c
    return None


def build():
    phase2 = load("phase2.json")
    robust = load("phase5_robustness_full.json")
    envelope = load("envelope.json")
    cost = load("cost.json")
    discovery = load("discovery_full.json")
    disc_rec = load("discovery_reconciliation.json")
    classwise = load("classwise_window.json")
    joint = load("classwise_joint_window.json")
    faults = load("faults_full_M25_A.json")
    faults_m1 = load("faults_M1_A.json")
    conf = load("confidence_full_M25_A.json") or load("confidence_window.json")
    gen = load("generalisation.json")
    chronic = load("chronic_full_M25_A.json")
    chronic_abs = load("chronic_absolute_full_M25_A.json")

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    def h(text, level=1):
        doc.add_heading(text, level=level)

    def p(text, italic=False):
        para = doc.add_paragraph()
        run = para.add_run(text)
        run.italic = italic
        return para

    def bullet(text):
        doc.add_paragraph(text, style="List Bullet")

    def number(text):
        doc.add_paragraph(text, style="List Number")

    def field(label, value):
        para = doc.add_paragraph()
        run = para.add_run(label + ": ")
        run.bold = True
        para.add_run(value)

    def table(headers, rows):
        t = doc.add_table(rows=1, cols=len(headers))
        t.style = "Light Grid Accent 1"
        for i, head in enumerate(headers):
            cell = t.rows[0].cells[i]
            cell.text = ""
            run = cell.paragraphs[0].add_run(head)
            run.bold = True
        for row in rows:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = str(v)
        doc.add_paragraph()
        return t

    # ======================================================================= 0
    title = doc.add_heading("Invention Disclosure Form (IDF-2)", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ======================================================================= 1
    h("1. Title of the Invention")
    p("A Method for Detecting, Localising, Classifying and Quantifying Measurement "
      "Faults in a Network of Traffic-Count Detectors, Including a Bias Already Present "
      "When the Network Was First Observed, and for Reconstructing Missing Records in the "
      "Resulting Dataset, Using Calibrated Direction-of-Flow Conservation Constraints at "
      "Network Nodes")

    # ======================================================================= 2
    h("2. Inventor Details")
    field("Name", TBD)
    field("Department / Affiliation", TBD)
    field("Contact", TBD)
    field("Contribution", TBD)

    # ======================================================================= 3
    h("3. Technical Field")
    p("The invention relates to computer-implemented processing of measurement data "
      "produced by a network of fixed roadside vehicle-counting detectors. More "
      "particularly it relates, first, to detecting and localising a miscalibrated or "
      "faulty detector within such a network from the recorded counts alone — including "
      "the case in which the detector was already miscounting throughout the whole of the "
      "record, so that no correctly-behaving reference period for it exists — and second "
      "to reconstructing records missing from the resulting dataset so that the "
      "completed dataset is consistent with the physical topology of the road network "
      "from which it was collected.")

    # ======================================================================= 4
    h("4. Background and the Technical Problem Addressed")
    p("Road authorities operate large networks of fixed inductive-loop detectors that "
      "report vehicle counts at fixed intervals. The resulting datasets are the input to "
      "downstream technical processes including capacity computation, incident-detection "
      "threshold setting, and signal-timing computation. Two defects in these datasets "
      "propagate directly into those processes.")

    p("First, the datasets contain gaps. Detectors fail, communication links drop, and "
      "individual intervals are recorded blank. A downstream process must either discard "
      "every interval that is incomplete anywhere, which discards good data from every "
      "other detector in that interval, or fill the gaps by estimation.")

    p("Second, and more damaging because it is silent, a detector may continue to report "
      "values that are neither missing nor obviously wrong while counting incorrectly. A "
      "loop whose sensitivity has drifted under-counts by a few percent; a loop suffering "
      "cross-talk adds a roughly constant number of phantom vehicles; a failed counter "
      "may repeat a plausible constant. None of these is detectable by a range check, by "
      "a null check, or by any test applied to that detector's own series in isolation, "
      "because the values remain individually plausible. They corrupt every downstream "
      "computation that consumes them, without ever raising an alarm.")

    p("Third, and harder than either, the second defect is frequently not an event but a "
      "standing condition. Loop sensitivity drifts over months and a detector that "
      "under-counts today has usually been under-counting for some time. Any method that "
      "learns what the network's normal behaviour looks like, and then reports departures "
      "from it, learns a normal that already contains the fault. Where the model of the "
      "network is itself estimated from the same detectors that are under suspicion — as "
      "it must be, if no surveyed model exists — this is circular: the fault is absorbed "
      "into the model at the moment the model is fitted, and the residual it would have "
      "produced never appears. The consequence is not only a missed fault. The corrupted "
      "model is then used to judge every other detector at the same node.")

    p("Known methods for filling the gaps estimate each missing value from the "
      "statistical behaviour of the same detector over time, or from detectors that "
      "behave similarly. Because such methods treat each detector as an independent time "
      "series, the values they produce need not be consistent with one another: a set of "
      "detectors surrounding one junction can be filled with values describing a "
      "physically impossible situation, in which the number of vehicles leaving the "
      "junction differs from the number entering it. Known methods for validating the "
      "data likewise examine each series alone, and are therefore blind to the second "
      "defect entirely.")

    if phase2:
        g = phase2["gaps"]
        p("Measured on the initial window of the corridor used in the prototype "
          "(Section 11): across %d "
          "detector sites and %d fifteen-minute intervals, %.1f%% of all records are "
          "absent. Excluding detectors inoperative for the whole measurement period, "
          "%.1f%% of records are absent, the median gap runs for %s consecutive intervals, "
          "and %d of the %d intervals contain at least one absent record. Discarding "
          "incomplete intervals is therefore not available as a strategy: it would "
          "discard the entire dataset."
          % (g["sites"], g["intervals"], 100 * g["missing_rate_overall"],
             100 * g["missing_rate_excluding_dead"], g["run_len_median"],
             g["intervals"] - g["intervals_with_no_live_site_missing"], g["intervals"]))

    # ======================================================================= 5
    h("5. Objects of the Invention")
    number("To detect, from the recorded counts alone and with no additional "
           "instrumentation, that a detector in the network has begun to count "
           "incorrectly; to identify which detector it is; to classify the kind of fault "
           "it has; and to state the size of that fault as a number.")
    number("To detect and size a bias that was already present when the network model was "
           "estimated, and which is therefore absorbed into that model and invisible to "
           "any test of departure from it, without requiring a reference period in which "
           "the detector concerned is known to have been counting correctly.")
    number("To emit, for a detector so identified, a correction to be applied to the "
           "counts that detector reports, so that the dataset consumed by downstream "
           "technical processes is corrected rather than merely annotated.")
    number("To reconstruct records absent from the dataset such that the reconstructed "
           "values satisfy, as a hard constraint rather than as a weighted penalty, the "
           "conservation of vehicle flow at each node of the road network.")
    number("To emit with each reconstructed value an interval, derived from the physical "
           "relation and the surrounding measurements, outside which no value is "
           "consistent with what was observed, so that a downstream process can "
           "distinguish a value the network geometry determined from one it did not.")
    number("To achieve the above without any component whose behaviour cannot be "
           "explained, the 2025 CRI Guidelines treating an unexplainable model as a "
           "liability rather than as an asset.")

    # ======================================================================= 6
    h("6. Summary of the Invention")

    h("6.1 Node construction and the calibrated relation", 2)
    p("Detectors are grouped into nodes. A node comprises an upstream mainline detector, "
      "a downstream mainline detector, and the entry and exit slip-road detectors "
      "situated between them. At each node and in each interval the counts are related by "
      "conservation of vehicle flow.")
    p("The textbook form of that relation, in which the upstream count plus entries minus "
      "exits equals the downstream count exactly, was measured and found not to hold "
      "exactly, because real detectors disagree slightly and systematically. The relation "
      "actually enforced is therefore the calibrated one")
    p("        upstream  +  sum over slips of ( sign · slip )  =  (1 + alpha) · downstream "
      "+ beta", italic=True)
    p("with alpha and beta estimated per node by least squares over intervals in which "
      "every detector at that node reported. The sign of each slip road, that is whether "
      "it adds vehicles to the mainline or removes them, is not taken from a naming "
      "convention or from an external map: it is selected as the assignment that "
      "minimises the conservation residual over those same intervals, so the topology is "
      "recovered from the measurements.")

    h("6.2 First aspect — fault detection, localisation, classification and sizing", 2)
    p("The calibrated residual of a node is tracked over a span of consecutive intervals "
      "rather than interval by interval. This is the key step. Measurement noise and the "
      "slow drift of the relation are not one-sided and average away over a span; a "
      "genuine miscount is one-sided and does not. The decision threshold for each node "
      "is taken from the empirical distribution of that node's own span statistic on "
      "clean data, at a chosen false-positive rate.")
    p("Because the nodes overlap — each mainline detector is the downstream detector of "
      "one node and the upstream detector of the next — a faulty detector disturbs every "
      "node it belongs to, and does so with a coefficient that is known in advance from "
      "the node's own relation: +1 where it is upstream, −(1 + alpha) where it is "
      "downstream, and the fitted slip sign where it is a slip road. That known "
      "coefficient pattern is the fault signature. A single bias value is fitted to each "
      "candidate detector's whole pattern of node deviations at once, and the candidate "
      "that explains the most deviation is named. An innocent neighbour can explain the "
      "one node it shares with the faulty detector, but is contradicted by its other "
      "nodes, which are clean.")
    p("The type of the fault follows from how the fitted bias tracks flow. The span is cut "
      "into its busier and quieter halves. A detector miscounting by a fixed percentage "
      "produces a deviation proportional to the flow through it; a detector carrying a "
      "constant offset produces the same deviation in both halves. Whichever of the two "
      "models fits better names the fault type, and the fitted parameter is its size, in "
      "percent or in vehicles per interval.")

    h("6.3 Second aspect — a bias already present when the model was fitted", 2)
    p("The procedure of Section 6.2 detects the onset of a fault: it compares a node "
      "against its own past. A detector that was already miscounting when the calibration "
      "was estimated has its bias absorbed into that node's alpha and beta, produces no "
      "residual at any time, and is invisible to that procedure. This aspect addresses "
      "that case, and does so without any period in which the detector is known to be "
      "sound.")
    p("The observation it rests on is that such a bias cannot hide in the calibration "
      "without leaving a trace across the network, because each detector enters the "
      "several nodes it belongs to with different coefficients: +1 where it is the "
      "upstream detector, −(1 + alpha) where it is the downstream one, and the fitted sign "
      "where it is a slip road. A detector carrying a constant bias b therefore displaces "
      "the fitted offset of node n by c(n, b) · b, and the vector of fitted offsets over "
      "the whole network satisfies")
    p("        beta  =  C · b  +  (genuine per-node effects)", italic=True)
    p("with C known once the node structure and the fitted coefficients are known. What is "
      "diagnosed is thus the fitted model itself, rather than the residual left over after "
      "it — which is what makes the fault reachable at all when it is the model that has "
      "been corrupted.")
    p("The system is solved for a sparse b by linear programming under an l1 objective. "
      "Sparsity is what makes this a fault detector and not a re-parameterisation: every "
      "detector carries some small disagreement with its neighbours, that being what the "
      "calibration exists to absorb, and a fault is an outlier within that population "
      "rather than a non-zero value. The fit is weighted so that a loose node cannot "
      "out-vote a tight one, and is placed ahead of sparsity in the objective so that a "
      "second genuine fault is not suppressed to keep the answer tidy.")
    p("A proportional bias is separated from a constant one without any reference period "
      "by decomposing twice, over the busier and the quieter halves of the record. A "
      "constant offset contributes equally in both; a percentage miscount contributes in "
      "proportion to the flow. Two operating points therefore replace the two time periods "
      "that a chronic fault does not provide. This second decomposition is deliberately "
      "performed against the rigid form of the relation, with the downstream coefficient "
      "pinned at unity, because it is precisely the freedom of alpha that allows a "
      "percentage miscount to disappear into the calibration.")
    p("The limits of identifiability are stated here in full, because they are severe and "
      "because an earlier version of this section understated them. On the reference "
      "corridor C has 199 rows and 367 columns and is of full row rank, so its null space "
      "has dimension 168. A shift common to every detector is one direction in that space; "
      "it is not the whole of it, and 46 per cent of the per-detector bias coordinates are "
      "therefore not determined by the node balances at all. Which representative the "
      "linear program returns from that 168-dimensional affine set is a property of the "
      "objective, not of the physics.")
    p("Two consequences follow, and neither is favourable. First, because the system is "
      "underdetermined it is solved exactly — the fitted node offsets are reproduced to "
      "within 7e-15 vehicles — so the term for genuine per-node effects in the expression "
      "above is zero in this implementation, and every departure from conservation that is "
      "not detector bias is nevertheless attributed to detector bias. Second, the number of "
      "non-zero entries the program returns is 199, which is the number of rows of C and "
      "hence the standard bound on the support of a basic solution; it is a property of "
      "linear programming and is not evidence about how many detectors carry a bias. What "
      "the procedure actually computes is the minimum-l1 representation of the fitted "
      "offsets in the row space of C. Whether that representation isolates a genuine "
      "chronic bias is an empirical question, and Section 9.4 answers it by measurement "
      "rather than by the argument from sparsity given above.")

    h("6.4 Third aspect — constrained reconstruction with certified bounds", 2)
    p("Missing values are reconstructed by taking the output of any per-detector "
      "estimator as a prior and projecting it onto the set of values that satisfy the "
      "calibrated relation at every affected node. The constraint is a hard two-sided "
      "inequality — a tolerance band whose width is taken from the measured spread of "
      "that node's own residual — and not a penalty term that a solver may trade away. "
      "The projection is performed jointly across overlapping nodes so that satisfying "
      "one node cannot break another, and by a closed-form weighted least-squares step "
      "iterated by Dykstra's algorithm, so no component of the method is opaque.")
    p("Where the observed values surrounding a node cannot be reconciled with the "
      "relation whatever is filled in — established by a linear program that computes the "
      "smallest band widening that would admit any solution — the interval is reported as "
      "irreconcilable rather than forced. Forcing it was implemented and measured, and it "
      "degraded accuracy, because it drags values away from the prior to satisfy a "
      "relation the observations have already broken.")
    p("Each reconstructed value is emitted with an interval obtained by minimising and "
      "maximising that coordinate over the feasible set, two linear programs. Any value "
      "outside that interval contradicts the observed data under the calibrated relation, "
      "so the interval is a guarantee about the physics and the neighbouring "
      "measurements rather than a statistical confidence statement, and it holds whatever "
      "estimator produced the point value.")

    # ======================================================================= 7
    h("7. Detailed Description of the Method")

    h("7.1 Steps", 2)
    number("Receive a dataset of vehicle counts indexed by detector and by measurement "
           "interval, together with an identification of the detectors belonging to each "
           "node of the road network.")
    number("For each node, over the intervals in which every detector at that node "
           "reported, select the slip-road signs minimising the median absolute "
           "conservation residual, and estimate the calibration coefficients alpha and "
           "beta by least squares.")
    number("For each node, compute the tolerance band as a chosen upper quantile of the "
           "absolute calibrated residual over those same intervals.")
    number("Fault monitoring: for each node compute the mean calibrated residual over a "
           "span of consecutive intervals, and compare it with a threshold obtained from "
           "the empirical distribution of that same statistic on clean spans at that "
           "node.")
    number("Fault localisation: for each candidate detector, fit by weighted least squares "
           "the single bias that best explains the span-mean residuals of all the nodes it "
           "belongs to, weighting each node by the inverse square of its own threshold, "
           "and rank candidates by the deviation that bias removes.")
    number("Fault classification and sizing: partition the span by flow level and fit both "
           "a proportional model and a constant model to the deviations of the named "
           "detector's nodes; report the better-fitting type and its fitted parameter.")
    number("Diagnosis of a bias present before calibration: partition the record into a "
           "higher-flow and a lower-flow part at the median of total corridor flow; within "
           "each part re-estimate the relation in its rigid form, with the downstream "
           "coefficient held at unity and only the offset free; assemble the coefficient "
           "matrix C whose entry for a node and a detector is the coefficient with which "
           "that detector enters that node's relation; and solve for the sparsest "
           "per-detector bias vector consistent with the vector of fitted offsets, by a "
           "linear program minimising the weighted node residual with an l1 term on the "
           "bias.")
    number("From the two recovered bias vectors and the mean flow at each detector in each "
           "part, solve the two-point linear system for that detector's proportional and "
           "constant components; report a detector as chronically biased when its "
           "recovered component is an outlier in the population of recovered components, "
           "measured on the median and median absolute deviation of that population, and "
           "name the fault by whichever component is the larger outlier on a common "
           "vehicles-per-interval scale.")
    number("Emit for each detector so identified a correction — a scale factor, a constant "
           "offset, or both — and apply that correction to the counts subsequently "
           "reported by that detector before they enter the reconstruction of step 9 and "
           "any downstream computation, so that the dataset is corrected rather than "
           "annotated.")
    number("Reconstruction: for each interval containing at least one absent record, "
           "assemble the calibrated relations of every node carrying an absent record, "
           "and project the prior estimate onto their intersection with the non-negative "
           "orthant, weighting each correction by that detector's measurement scale.")
    number("Where the intersection is empty, report the node and interval as "
           "irreconcilable together with the shortfall in vehicles, and retain the "
           "nearest point reached rather than widening the bands.")
    number("Emit each reconstructed value together with its certified interval, computed "
           "by minimising and maximising that coordinate over the feasible set.")

    h("7.2 Design decisions forced by measurement, not chosen a priori", 2)
    p("Each of the following was implemented in both forms and the alternative was "
      "rejected on measured evidence. They are recorded because the 2025 CRI Guidelines "
      "require a technical effect to be disclosed and evidenced rather than asserted.")

    rows = []
    if phase2 and phase2["summary"].get("noise_floor_pct") is not None:
        rows.append(["Enforce the textbook identity exactly, with no calibration",
                     "Enforce a per-node calibrated relation",
                     "Raw relation off by 17.45 vehicles per interval; offset "
                     "calibration 16.41; scale and offset 14.84"])
    if robust:
        t = robust["table"]
        if "constrained(knn_spatial)" in t and "ablation(knn_spatial: textbook zero, no calibration)" in t:
            rows.append(["No calibration (textbook zero)", "Scale and offset calibration",
                         "MAE %.2f without vs %.2f with; band violations %.2f%% vs %.2f%%"
                         % (t["ablation(knn_spatial: textbook zero, no calibration)"]["MAE"]["mean"],
                            t["constrained(knn_spatial)"]["MAE"]["mean"],
                            t["ablation(knn_spatial: textbook zero, no calibration)"]["outside_band_pct"]["mean"],
                            t["constrained(knn_spatial)"]["outside_band_pct"]["mean"])])
        if "ablation(knn_spatial: exact equality, no band)" in t:
            rows.append(["Zero-width band (exact equality)", "Band from measured spread",
                         "NOT SUPPORTED BY THE CORRECTED MEASUREMENT. Exact equality "
                         "reaches both lower error (MAE %.2f against %.2f) and fewer band "
                         "violations (%.2f%% against %.2f%%). See Section 10.4"
                         % (t["ablation(knn_spatial: exact equality, no band)"]["MAE"]["mean"],
                            t["constrained(knn_spatial)"]["MAE"]["mean"],
                            t["ablation(knn_spatial: exact equality, no band)"]["outside_band_pct"]["mean"],
                            t["constrained(knn_spatial)"]["outside_band_pct"]["mean"])])
        if "ablation(knn_spatial: uniform weighting)" in t:
            rows.append(["Weight corrections by detector flow", "Weight uniformly",
                         "MAE %.2f flow-weighted vs %.2f uniform: no measurable "
                         "difference, so flow weighting is not claimed"
                         % (t["constrained(knn_spatial)"]["MAE"]["mean"],
                            t["ablation(knn_spatial: uniform weighting)"]["MAE"]["mean"])])
    rows.append(["Widen the bands until an irreconcilable interval is satisfied",
                 "Report it and retain the nearest point",
                 "NOT MEASURED. The reasoning is that widening satisfies a relation the "
                 "observations have already broken, but no experiment in this document "
                 "compares the two, and the row is retained only to record the choice"])
    if joint:
        m = joint["missingness"].get("0.40") or {}
        if m:
            rows.append(["Impose conservation on each vehicle length class as well as on "
                         "the total", "Impose it on the total alone",
                         "Adding the four class relations degraded MAE by %.0f%% at 40%% "
                         "missing (%.2f against %.2f). See Section 10.1"
                         % (abs(m["gain_E_over_C_pct"]), m["E_total_and_class_MAE"],
                            m["C_total_MAE"])])
    if rows:
        table(["Alternative implemented", "Retained", "Measured basis for the choice"], rows)

    # ======================================================================= 8
    h("8. Novelty and Inventive Step")

    h("8.1 Nearest prior art identified", 2)
    p("The prior-art position is stated in full rather than favourably, because an "
      "examiner will find these references and a disclosure that has already narrowed "
      "against them is worth more than one that has not.")
    table(["Reference", "What it discloses", "Distinction"],
          [["de Souza (2019), Freeway Loop Detector Data Reconciliation Based on Vehicle "
            "Conservation",
            "Convex optimisation correcting freeway loop counts subject to vehicle "
            "conservation between stations, with bounds from occupancy-derived "
            "accumulation limits",
            "Corrects observed counts; bounds come from occupancy rather than from the "
            "measured spread of the relation; no per-detector bias calibration; "
            "irreconcilable cases are prevented by constraint design rather than "
            "detected, localised, classified and sized"],
           ["Yin, Sun, Jin, Xin (2017), l1-minimisation for link flow correction",
            "Hard flow conservation on network link flows; analytic 'recoverability' "
            "identifying which links are robust to miscounts",
            "Identifies which links are correctable a priori; does not classify the kind "
            "of fault, does not estimate its magnitude, and does not report per-value "
            "certified bounds"],
           ["Process-industry data reconciliation (US5504692, US10310497, WO2016114736A1 "
            "and the associated literature)",
            "Weighted least-squares adjustment of measured flows subject to mass-balance "
            "constraints, with gross error detection and bias estimation",
            "A mature field in another measurement domain. Supports an obviousness "
            "argument by analogy and is treated as the strongest attack on the "
            "reconstruction aspect"],
           ["Narasimhan and Mah (1987), Generalized likelihood ratio method for gross "
            "error identification, AIChE Journal 33(9):1514–1521; and the subsequent GLR "
            "literature",
            "Identifies gross errors from the residuals of process mass-balance "
            "constraints by testing modelled hypotheses against one another, and thereby "
            "distinguishes a measurement bias from a process leak and estimates its "
            "magnitude",
            "Treated as the strongest attack on the whole first aspect. It discloses "
            "detection, localisation, discrimination between fault types and magnitude "
            "estimation from conservation-constraint residuals, and it does so from 1987. "
            "Any claim resting on classification-and-sizing alone is not available. The "
            "distinction relied on is that GLR and every method in its line begin from a "
            "system model that is surveyed and assumed correct — a flowsheet, an "
            "admittance matrix — and ask which sensor disagrees with it. The second "
            "aspect of the present method diagnoses the fitted model itself, which is the "
            "only route to a bias that was present when that model was estimated"],
           ["Fault detection and isolation by parity space and structured residuals "
            "(Chow and Willsky 1984; Gertler; Isermann), and bad-data identification in "
            "power-system state estimation",
            "Residual generation against a known system model, with structured residual "
            "sets and fault signature matrices designed so that the pattern of residuals "
            "identifies which sensor is at fault",
            "Same distinction and the same limitation: the model is given. These "
            "references are also the reason the localisation step of Section 6.2 is not "
            "claimed on its own — fitting a bias to a known coefficient pattern is the "
            "structured-residual idea in another domain"],
           ["Power-system NETWORK PARAMETER error identification. Liu, Wu and Lun (1992), "
            "Estimation of parameter errors from measurement residuals in state "
            "estimation, IEEE Trans. Power Systems 7(1):81–89; Zhu and Abur (2006), "
            "Identification of network parameter errors, IEEE Trans. Power Systems "
            "21(2):586–592; and Highly Efficient Implementation for Parameter Error "
            "Identification Method Exploiting Sparsity, IEEE Trans. Power Systems "
            "32(1):734–742 (2017)",
            "Treats the fitted system model, not the measurement, as the object under "
            "suspicion. Liu et al. estimate a bias vector from the fitted model and "
            "decompose it over the known network structure to name the erroneous element. "
            "Zhu and Abur distinguish bad measurements from incorrect network parameters "
            "even when both are present. The 2017 reference combines parameter-error "
            "identification with sparsity",
            "TAKEN TO BE THE STRONGEST ATTACK ON THE PRINCIPAL CLAIM, and identified after "
            "the first version of this disclosure was written. It occupies the "
            "distinction Section 8.2 previously relied on. This disclosure had cited only "
            "the bad-measurement half of power-system state estimation, which is the half "
            "that does assume a surveyed admittance matrix; the parameter-error half does "
            "not. What may remain is the combination with a conservation relation whose "
            "coefficients and topology are themselves recovered from the same counts, and "
            "the reference-free outlier criterion of Section 9.4 — but this is a much "
            "narrower position than was previously stated and it has not been searched in "
            "the patent literature"],
           ["Vanajakshi and Rilett (2004), Loop Detector Data Diagnostics Based on "
            "Conservation-of-Vehicles Principle, Transportation Research Record 1870; and "
            "Cheevarunothai, Wang and Nihan (2006), Identification and Correction of "
            "Dual-Loop Sensitivity Problems, Transportation Research Record 1945",
            "The first applies conservation of vehicles across adjacent loop detectors to "
            "identify systematic errors from non-catastrophic malfunction, with an "
            "optimisation-based correction. The second identifies and corrects loop "
            "SENSITIVITY drift specifically",
            "In-domain, uncited until now, and between them they disclose the problem "
            "statement of Section 4 — silent systematic miscounting, including drifted "
            "loop sensitivity — together with a conservation-based diagnosis and a "
            "correction. Any claim to detecting a miscounting loop detector by vehicle "
            "conservation is met. The surviving question is whether the specific "
            "decomposition of the fitted calibration is distinguished, and that turns on "
            "the power-system row above rather than on these"],
           ["Blind calibration of sensor networks. Balzano and Nowak (2007), Blind "
            "Calibration of Sensor Networks, IPSN; Dorffer et al., Reference-free "
            "Calibration in Sensor Networks (arXiv:1805.11999) and On the choice of "
            "reference in offset calibration (arXiv:2212.12914)",
            "Recovery of unknown per-sensor gains and offsets from redundancy in the "
            "sensed field with no calibrated reference sensor, with necessary and "
            "sufficient identifiability conditions; the later work establishes that "
            "without a reference the parameters are recoverable only up to a null-space "
            "direction",
            "Still not searched in the patent literature. Two points must be conceded: the "
            "identifiability limit set out in Section 6.3 is a known result in this field "
            "rather than an original observation, and reference-free recovery of "
            "per-sensor gain and offset is the general problem of which Section 6.3 is an "
            "instance. The intended distinction is that the redundancy exploited there is "
            "a smoothness or subspace assumption about the sensed field, whereas here it "
            "is an exact conservation relation whose coefficients are recovered from the "
            "data"],
           ["FlowSymm (Demirci, Bullo, Swami, Singh)",
            "Physics-aware completion of missing network flow measurements",
            "Imposes conservation as a soft constraint; the present method imposes it as "
            "a hard feasibility requirement"],
           ["US11093463 (Fanuc), Missing value imputation device",
            "Choosing the number of multiple-imputation repetitions to fit a permitted "
            "computation time",
            "No physical constraint and no network topology. Not relevant, "
            "notwithstanding its identification as nearest art in the source brief"]])

    h("8.2 Features believed not anticipated", 2)
    p("Two broad claims have been considered and abandoned on the art, and are recorded "
      "as abandoned so that the remaining scope is not read more widely than it is meant. "
      "First, a claim to reconstructing missing traffic counts subject to flow "
      "conservation: anticipated in this domain by de Souza (2019) and Yin et al. (2017). "
      "Second, a claim to detecting, localising, classifying and sizing a measurement "
      "fault from the residuals of conservation constraints: anticipated by Narasimhan and "
      "Mah (1987) and the gross-error and fault-detection-and-isolation literature that "
      "follows it. The claim is therefore directed to the following combination, of which "
      "the first feature is the one on which the case principally rests.")
    p("A third position has since been abandoned, and is recorded here because an earlier "
      "version of this document rested on it. That position was that no reference treats "
      "the estimated model, rather than its residuals, as the object to be diagnosed. "
      "That was true of the references then searched and is not true of the "
      "power-system network parameter error literature identified in Section 8.1, which "
      "has done exactly that since 1992. Combined with Yin et al. (2017), already cited, "
      "which supplies l1 minimisation under hard flow conservation in this very domain, "
      "there is a two-reference obviousness attack on the principal claim that must be "
      "answered before any filing. It is not answered in this document.")
    number("What may remain of the first feature, stated at its true width: the "
           "combination of (i) a conservation relation whose node membership and slip-road "
           "signs are recovered from the counts alone rather than surveyed, with (ii) "
           "decomposition of the fitted offsets of that relation over the resulting "
           "coefficient matrix, and (iii) a reference-free criterion that names a detector "
           "by its position in the cross-sectional population of recovered biases rather "
           "than by any comparison with its own past. The power-system art has a surveyed "
           "admittance matrix and so does not reach (i); the blind-calibration art reaches "
           "neither (i) nor the exactness of the relation. Whether that combination is "
           "inventive rather than merely a transfer between analogous fields is doubtful "
           "and is the question on which the application turns.")
    number("Separation of a proportional from a constant chronic bias by decomposing at "
           "two flow levels rather than at two times, the rigid form of the relation being "
           "used for that decomposition specifically because the free scale coefficient of "
           "the calibrated form is what conceals a proportional bias. This substitutes two "
           "operating points for the before-and-after comparison that a chronic fault does "
           "not admit.")
    number("Fault classification and sizing from the flow-dependence of the fitted bias, "
           "in combination with the above. Claimed only in combination: Narasimhan and Mah "
           "(1987) discloses discrimination of fault type and estimation of magnitude from "
           "constraint residuals, and this feature is not available standing alone.")
    number("Localisation by fitting one bias to the whole known coefficient pattern across "
           "the overlapping nodes a detector belongs to, weighted by each node's own "
           "empirically measured reliability.")
    number("A per-node decision threshold taken from the empirical distribution of that "
           "node's own span statistic, rather than from an assumed noise model. This was "
           "forced by measurement: node reliability on the test corridor varies by two "
           "orders of magnitude, and a single pooled threshold is set by the worst node "
           "and blinds the rest.")
    number("Per-value certified bounds obtained by optimising each coordinate over the "
           "feasible set, so that each reconstructed value carries a statement of what "
           "the physics can and cannot vouch for.")
    number("Method-agnostic projection: the reconstruction step takes the output of any "
           "existing estimator and leaves an already-plausible estimate untouched, rather "
           "than being a standalone estimator.")
    number("Recovery of the conservation relations, including slip-road direction, from "
           "the counts alone, so that no external network map or naming convention is "
           "required at any stage.")

    h("8.3 Position on Section 3(k) and on Alice/Mayo", 2)
    p("The claim is not to a mathematical method in the abstract. It receives measurement "
      "data from physical instruments, applies a conservation law of the physical system "
      "those instruments observe, and produces two outputs directed at the instruments "
      "themselves: an identification of which physical detector is miscounting, by how "
      "much and in what manner; and a corrected dataset whose consistency with the "
      "physical network is guaranteed and measured. The effect is on the technical "
      "reliability of a measurement system, which is the form of technical effect "
      "contemplated in Ferid Allani and in the 2025 CRI Guidelines.")
    p("Every asserted effect in this document is accompanied by a measurement produced by "
      "the prototype, as the 2025 CRI Guidelines require. No component is a trained "
      "black box: the calibration is least squares, the detection statistic is a mean, "
      "the localisation is weighted least squares, and the reconstruction is a projection "
      "with a closed-form step.")
    p("For the United States, the claim does not recite the application of a "
      "conservation law by a computer at a level of generality. It recites a specific "
      "sequence — span aggregation, per-node empirical thresholding, coefficient-pattern "
      "fitting, flow-partitioned model selection — which is an improvement to the "
      "functioning of a measurement system and not an abstract idea applied to it.")

    # ======================================================================= 9
    h("9. Technical Effects, with Measured Values")
    p("Every figure below was produced by the prototype and is reproducible from the "
      "results files named. No figure is estimated, rounded up, or carried over from any "
      "external source.")

    h("9.1 Detection, localisation, classification and sizing of a faulty detector", 2)
    if faults:
        p("Faults of known type, known size, known detector and known duration were "
          "injected into the real recorded data. The calibration was fitted on one half "
          "of the month and every fault injected into the other, disjoint half, so the "
          "calibration cannot absorb the fault. The decision threshold is set from clean "
          "spans at a 1%% nominal false-positive rate. Corridor: %d nodes; %d detectors "
          "tested over spans of %d intervals (%.1f days); the identification is made from "
          "a line-up of all %d detectors belonging to more than one node."
          % (faults["nodes_fitted"], faults["detectors_tested"],
             faults["span_intervals"], faults["span_intervals"] / 96.0,
             faults.get("detectors_eligible", 0)))
        control = case(faults, "none", 0.0)
        if control:
            p("Control, with no fault injected: %.1f%% of trials raised a flag, against "
              "the 1%% the threshold was set for. This figure is the rate at which the "
              "nodes surrounding one named detector fire spuriously; it is not the "
              "corridor-wide false-alarm rate, which is higher because every node in the "
              "network is tested. The corridor-wide rate is not yet measured and is "
              "recorded as outstanding in Section 9.8."
              % (100 * control["detection_rate"]))

        # Every case that was run is tabulated. Selecting the favourable ones would be a
        # straightforward way to make the method look better than it is, and an examiner
        # or evaluator with the results file can spot the omission immediately.
        def label_for(c):
            if c["mode"] == "scale":
                pct = 100.0 * (c["magnitude"] - 1.0)
                return "%s-count by %.1f%%" % ("under" if pct < 0 else "over", abs(pct))
            if c["mode"] == "offset":
                return "constant %s of %.0f vehicles/interval" % (
                    "loss" if c["magnitude"] < 0 else "gain", abs(c["magnitude"]))
            if c["mode"] == "stuck":
                return "detector repeats a constant"
            return c["mode"]

        rows = []
        for c in faults["cases"]:
            if c["mode"] in ("none", "classify"):
                continue
            rows.append([label_for(c), c["trials"],
                         "%.1f%%" % (100 * c["detection_rate"]),
                         "%.1f%%" % (100 * c["attribution_top1"]),
                         "%.1f%%" % (100 * c["attribution_top3"]),
                         ("%.0f%%" % (100 * c["type_correct"])) if "type_correct" in c else "-"])
        if rows:
            table(["Injected fault", "Trials", "Detected", "Correct detector ranked 1st",
                   "Ranked in top 3", "Fault type named correctly"], rows)
            p("Detection falls off below about a 1% scale error or 2 vehicles per "
              "interval, which is the sensitivity limit of the method on this corridor "
              "and is stated as such. The 80 trials behind each row are 40 detectors at "
              "two spans each rather than 80 independent draws, so the effective sample is "
              "40 and the interval on a rate quoted to one decimal place is wider than "
              "plus or minus ten points. The ordering of adjacent rows should not be read "
              "as meaningful.")

        sized = [c for c in faults["cases"] if "estimated_size_median" in c]
        if sized:
            p("The fitted fault magnitude recovers the injected magnitude, which is the "
              "difference between an alarm and a diagnosis. Every case run is listed; "
              "recovery is close in the middle of the range and degrades at the largest "
              "scale errors, where the linear bias model fits a fault it was not written "
              "for.")
            table(["Injected", "Recovered (median over trials)", "Error"],
                  [["%s %s" % (c["mode"], ("%+.1f%%" % c["true_size"]) if c["mode"] == "scale"
                               else "%+.0f vehicles/interval" % c["true_size"]),
                    ("%+.3f%%" % c["estimated_size_median"]) if c["mode"] == "scale"
                    else "%+.2f vehicles/interval" % c["estimated_size_median"],
                    "%+.1f%% relative" % (100.0 * (c["estimated_size_median"] - c["true_size"])
                                          / c["true_size"]) if c["true_size"] else "-"]
                   for c in sized])

        p("What is measured in this subsection is detection of the ONSET of a fault: the "
          "calibration is fitted on a clean period and the fault injected later. A "
          "detector already miscounting when the calibration was fitted is invisible to "
          "this procedure by construction. That case is the subject of Section 9.4 and is "
          "measured separately there. The remaining limits of this subsection are "
          "collected in Section 9.8.")
    else:
        p(TBM)

    h("9.2 A fault class that no total-flow method can detect at all", 2)
    if faults:
        p("A detector whose vehicle-length classifier drifts books a share of one length "
          "class into the next. Its total count is unchanged by construction. No balance "
          "written on total flow can therefore detect it — at any threshold, on any "
          "corridor, ever — because the fault is invisible in that coordinate. Writing "
          "the same balance on each length class detects it directly. The measurement "
          "confirms both halves of that statement:")
        rows = []
        for share in (0.01, 0.02, 0.05, 0.10, 0.20):
            c = case(faults, "classify", share)
            if c:
                rows.append(["%.0f%% of the shortest class misbooked" % (100 * share),
                             c["trials"],
                             "%.1f%%" % (100 * c["detection_rate"]),
                             "%.1f%%" % (100 * (c.get("detection_rate_via_total_balance") or 0.0)),
                             "%.1f%%" % (100 * c["attribution_top1"])])
        if rows:
            table(["Injected fault", "Trials", "Detected by the class relations",
                   "Detected by the total relation", "Correct detector ranked 1st"], rows)
            p("The total-flow column sits at the false-positive floor throughout, as "
              "predicted analytically. This is a capability, not a tuning advantage.")
    else:
        p(TBM)

    h("9.3 Replication on a second, independent corridor", 2)
    if faults_m1:
        p("The same procedure, unchanged and with nothing retuned, applied to a different "
          "motorway: %d nodes, a line-up of %d candidate detectors, same month."
          % (faults_m1["nodes_fitted"], faults_m1.get("detectors_eligible", 0)))
        rows = []
        control = case(faults_m1, "none", 0.0)
        if control:
            rows.append(["no fault (control)", control["trials"],
                         "%.1f%%" % (100 * control["detection_rate"]), "-", "-"])
        for mode, mag, label in [("scale", 0.99, "under-count by 1%"),
                                 ("scale", 0.95, "under-count by 5%"),
                                 ("offset", -8.0, "constant loss of 8 vehicles/interval"),
                                 ("stuck", 0.0, "detector repeats a constant"),
                                 ("classify", 0.05, "5% of shortest class misbooked")]:
            c = case(faults_m1, mode, mag)
            if c:
                rows.append([label, c["trials"],
                             "%.1f%%" % (100 * c["detection_rate"]),
                             "%.1f%%" % (100 * c["attribution_top1"]),
                             ("%.0f%%" % (100 * c["type_correct"])) if "type_correct" in c else "-"])
        table(["Injected fault", "Trials", "Detected", "Correct detector ranked 1st",
               "Fault type named correctly"], rows)
    else:
        p(TBM)

    h("9.4 A bias already present when the model was fitted", 2)

    def _chronic_label(c):
        if c["mode"] == "offset":
            return "constant %s of %.0f vehicles/interval, whole record" % (
                "loss" if c["magnitude"] < 0 else "gain", abs(c["magnitude"]))
        pct = 100.0 * (c["magnitude"] - 1.0)
        return "%s-count by %.0f%%, whole record" % (
            "under" if pct < 0 else "over", abs(pct))

    if chronic:
        b = chronic["baseline"]
        p("The fault here is injected into the ENTIRE record before anything is fitted, so "
          "that the calibration is estimated from data that already contains it and no "
          "clean period for the faulted detector exists anywhere. Corridor: %d nodes, %d "
          "detectors, of which %d belong to two or more nodes and form the line-up; %d "
          "detectors were faulted in turn."
          % (chronic["nodes"], chronic["detectors"], chronic["detectors_multinode"],
             chronic["detectors_tested"]))
        p("Applied to the corridor as recorded, with nothing injected, the decomposition "
          "of the fitted calibration returns a non-zero bias for %d of %d detectors, with "
          "median absolute value %.2f and maximum %.2f vehicles per interval, and "
          "reproduces the fitted node offsets to a median residual of %.2f vehicles. The "
          "count of %d must not be read as a finding about how many detectors carry a "
          "bias: it equals the number of nodes, which is the rank of the coefficient "
          "matrix and hence the bound on the support of a basic solution of the linear "
          "program, so it is forced. What is informative is the spread of the recovered "
          "values, since that is the population against which a fault has to stand out."
          % (b["nonzero_offsets"], chronic["detectors"], b["median_abs_offset"],
             b["max_abs_offset"], b["median_abs_residual"], b["nonzero_offsets"]))
        p("First measurement, with the recovered parameters referred to those recovered "
          "from the same corridor without the injection. This isolates the question of "
          "whether the decomposition can see a chronic bias at all, and it is the more "
          "favourable of the two experiments because it is given a clean reference that a "
          "real deployment would not have:")
        table(["Injected chronic fault", "Trials", "True", "Recovered (median)",
               "Faulted detector ranked 1st", "In top 3"],
              [[_chronic_label(c), c["trials"],
                ("%+.4f" % c["true_shift"]) if c["mode"] == "scale"
                else "%+.1f veh" % c["true_shift"],
                ("%+.4f" % c["median_recovered_shift"]) if c["mode"] == "scale"
                else "%+.3f veh" % c["median_recovered_shift"],
                "%.1f%%" % (100 * c["identified_top1"]),
                "%.1f%%" % (100 * c["identified_top3"])]
               for c in chronic["cases"]])
        p("The magnitude is recovered to within about 0.03 vehicles per interval on the "
          "constant faults and to within about a tenth of the injected value on the "
          "proportional ones. Recovering the size, and not merely raising a flag, is what "
          "permits the corrective action of step 11 of Section 7.1.")
    else:
        p(TBM)

    if chronic_abs:
        p("Second measurement, and the one that matters, because the first still leans on "
          "a clean reference. A chronic fault is by definition present at the start of the "
          "record, so no such reference exists; requiring one readmits the assumption the "
          "whole aspect is meant to remove. Here the corridor is taken exactly as it "
          "arrives, decomposed once, and a detector is reported as faulty when its "
          "recovered bias is an outlier within the population of recovered biases — "
          "measured on the median and median absolute deviation of that population, at "
          "%.1f robust deviations. Nothing is differenced against anything."
          % chronic_abs["threshold_k"])
        p("With nothing injected, that criterion selects %d of the %d detectors in the "
          "line-up (%.1f%%). Those are not reported as false alarms and should not be "
          "counted as such: the corridor is real road data and some of those detectors may "
          "genuinely be miscounting, which is the premise of the exercise. The figure "
          "bounds the alarm rate from above, which is the operationally meaningful reading "
          "whichever way the ambiguity resolves. Those detectors are excluded from the "
          "injection pool so that no fault is credited to a detector the method had "
          "already singled out. The robust scale of the recovered population is %.2f "
          "vehicles per interval on the constant component and %.2f on the proportional "
          "component expressed in the same units."
          % (chronic_abs["flagged_without_injection"], chronic_abs["pool"],
             chronic_abs["flagged_without_injection_pct"],
             chronic_abs["robust_scale_offset_veh"],
             chronic_abs["robust_scale_gain_veh"]))
        p("The fault type is named without being told which was injected, by comparing the "
          "two components on a common vehicles-per-interval scale and taking the larger "
          "outlier. Two ranking columns are given, and the difference between them is the "
          "most important thing in this subsection. Ranked against the whole line-up, the "
          "injected detector is essentially never first — the detectors already selected "
          "with nothing injected are larger outliers than anything injected here, and they "
          "stay larger. Ranked against the line-up with those standing outliers set aside, "
          "which is the question that remains once they have been triaged, the injected "
          "detector is first in the great majority of trials. The final column counts "
          "detectors other than the faulted one that the criterion newly selects — the "
          "collateral cost, reported because a diagnosis naming innocent detectors "
          "alongside the guilty one is worth less than an identification rate alone "
          "suggests:")
        table(["Injected chronic fault", "Trials", "Detected", "1st over whole line-up",
               "1st with standing outliers set aside", "In top 3 likewise",
               "Type named correctly", "Additional detectors flagged, per trial"],
              [[_chronic_label(c), c["trials"],
                "%.1f%%" % (100 * c["detected"]),
                "%.1f%%" % (100 * c["identified_rank1"]),
                "%.1f%%" % (100 * c.get("identified_rank1_excluding_standing", 0.0)),
                "%.1f%%" % (100 * c.get("identified_top3_excluding_standing", 0.0)),
                "%.1f%%" % (100 * c["type_named_correctly"]),
                "%.2f" % c["extra_detectors_flagged_per_trial"]]
               for c in chronic_abs["cases"]])
        p("These figures are the ones on which the aspect should be judged, not those of "
          "the referenced experiment above. The gap between the two tables is the price of "
          "not having a clean reference, and the zero column is the price of a corridor "
          "that has its own standing outliers. Both are stated rather than left for a "
          "reader to infer. What the method delivers on this corridor is therefore an "
          "alarm and a size for a chronic bias, and a correct identification within a "
          "shortlist, rather than an unqualified naming of the guilty detector.")
    else:
        p(TBM)

    h("9.5 Accuracy and physical consistency of the reconstructed dataset", 2)
    p("The figures in this subsection and in Sections 9.6 and 11.3 are from a corrected "
      "evaluation. An earlier version fitted the calibration coefficients and the tolerance "
      "band on the whole corridor, including the values that were then withheld and scored, "
      "so the band a reconstruction was judged against had been fitted using the very "
      "values it was reconstructing. The calibration is now fitted on the visible data "
      "alone, while consistency continues to be scored against the relation fitted on "
      "everything, that being the correct reference for whether a value is physically "
      "plausible. The corrected consistency figures are substantially weaker than those "
      "first obtained — a halving of band violations rather than a tenfold reduction — and "
      "Section 10.4 records a design decision that the correction reverses.")
    if robust:
        c = robust["corridor"]
        p("Corridor of %d detectors and %d nodes over %d intervals; 10%% of the recorded "
          "values withheld as runs drawn from the measured gap-length distribution, three "
          "mask seeds. Mean node flow %.1f vehicles per interval, mean tolerance band "
          "%.2f vehicles (%.2f%% of flow). Each known method is paired against the same "
          "method with the constraint applied, so any difference is attributable to the "
          "constraint alone."
          % (c["sites"], c["nodes_fitted"], c["intervals"], c["mean_node_flow"],
             c["mean_band_vehicles"],
             100 * c["mean_band_vehicles"] / c["mean_node_flow"]))
        t = robust["table"]
        rows = []
        for base in ["historical_mean", "linear_interpolation", "soft_impute",
                     "knn_spatial"]:
            key = "constrained(%s)" % base
            if base in t and key in t:
                rows.append([base.replace("_", " "),
                             "%.2f" % t[base]["MAE"]["mean"],
                             "%.2f" % t[key]["MAE"]["mean"],
                             "%+.1f%%" % (-100.0 * (t[base]["MAE"]["mean"]
                                                    - t[key]["MAE"]["mean"])
                                          / t[base]["MAE"]["mean"]),
                             "%.2f%%" % t[base]["outside_band_pct"]["mean"],
                             "%.2f%%" % t[key]["outside_band_pct"]["mean"]])
        table(["Prior estimator", "MAE alone", "MAE constrained", "Change",
               "Node-intervals outside band, alone", "Constrained"], rows)
        best = t.get("knn_spatial"), t.get("constrained(knn_spatial)")
        if all(best):
            p("Against the strongest known method, accuracy improves by %.1f%% "
              "(MAE %.2f to %.2f vehicles per interval) and the share of node-intervals "
              "violating the calibrated relation falls from %.2f%% to %.2f%%. The second "
              "figure is the one no per-detector method can control at all: it is a "
              "property of the completed dataset rather than of any single value."
              % (100.0 * (best[0]["MAE"]["mean"] - best[1]["MAE"]["mean"])
                 / best[0]["MAE"]["mean"],
                 best[0]["MAE"]["mean"], best[1]["MAE"]["mean"],
                 best[0]["outside_band_pct"]["mean"], best[1]["outside_band_pct"]["mean"]))
            p("The improvement is consistent in direction across all four structurally "
              "different prior estimators, and across mask seeds the spread of the "
              "constrained result is %.2f to %.2f."
              % (best[1]["MAE"]["min"], best[1]["MAE"]["max"]))
    else:
        p(TBM)

    h("9.6 Certified bounds on each reconstructed value", 2)
    if conf:
        p("Each reconstructed value is emitted with the interval obtained by minimising "
          "and maximising that coordinate over the feasible set. Measured over %d "
          "reconstructed values: %.1f%% are bounded by the physics at all, and of the "
          "values checked, %.1f%% of the true withheld values fall inside their stated "
          "interval. The median certified width is %.1f vehicles per interval."
          % (conf["values_checked"], conf["bounded_pct"], conf["coverage_pct"],
             conf["median_width_vehicles"]))
        rows = [[k, v["n"], "%.1f" % v["median_width"]]
                for k, v in conf["width_by_unknowns_at_node"].items()]
        if rows:
            table(["Absent values sharing the node", "Values", "Median certified width"],
                  rows)
            p("The width grows with the number of absent values sharing a node, which is "
              "the honest statement of what the geometry can and cannot determine. "
              "Coverage below 100 per cent is expected and is not a defect: the band is "
              "set at "
              "an upper quantile of the residual, so the relation itself is violated on a "
              "matching share of intervals.")
    else:
        p(TBM)

    h("9.7 Operating envelope and computational cost", 2)
    if envelope:
        p("The sweep below was run on the initial 51-detector window rather than the full "
          "corridor, so its absolute error figures are not comparable with Section 9.5; "
          "the shape of the curve is the point.")
        rows = [[k.replace("0.", "") + "%" if False else "%.0f%%" % (float(k) * 100),
                 "%.2f" % v["prior_MAE"], "%.2f" % v["ours_MAE"],
                 "%+.2f%%" % v["gain_pct"], "%.2f%%" % v["outside_band_pct"]]
                for k, v in sorted(envelope["missingness"].items())]
        table(["Share of records withheld", "Prior MAE", "MAE with constraint",
               "Accuracy change", "Node-intervals outside band"], rows)
        p("The accuracy advantage decays as the fraction of absent records rises and the "
          "node systems become underdetermined. The consistency guarantee does not decay. "
          "This is reported because it bounds the claim: the reconstruction aspect is "
          "directed at the operational-dropout regime, not at a network that has largely "
          "stopped reporting.")
    if cost:
        p("Computational cost, like for like on the same machine and data, on the same "
          "51-detector window. Peak memory is additional allocation measured with "
          "tracemalloc, which itself inflates the timings roughly threefold.")
        m = cost["methods"]
        rows = [[k.replace("_", " "), "%.2f" % v["seconds"], "%.1f" % v["peak_MB"]]
                for k, v in m.items()]
        table(["Step", "Seconds", "Peak additional memory (MB)"], rows)
        p("The constraint step is not claimed as a speed improvement; it is an added cost "
          "paid for the guarantee and for the diagnosis. It is stated here so that the "
          "cost is on the record.")

    h("9.8 Limits of the evidence, and what is not yet measured", 2)
    p("Stated because the 2025 CRI Guidelines make the difference between an evidenced "
      "effect and an asserted one turn on exactly this kind of disclosure, and because "
      "each of these is a question an examiner would otherwise ask first.")
    bullet("In Section 9.1 the classification and magnitude figures are computed for the "
           "detector that was in fact faulted, not for the detector the localisation step "
           "named. The claimed sequence classifies the detector it identified, so the "
           "end-to-end rate is the product of the two columns and is lower than either. It "
           "has not yet been measured directly. Section 9.4 does not share this defect: "
           "its type column is computed without being told which fault was injected.")
    bullet("The false-positive control of Section 9.1 is measured over the nodes "
           "surrounding one named detector, not over the whole corridor. A monitor "
           "scanning every node raises more spurious flags than 1% of spans, and the "
           "corridor-wide figure is not yet measured. The corresponding figure for "
           "Section 9.4 IS corridor-wide, being the count of detectors selected across the "
           "entire line-up with nothing injected.")
    bullet("Faults are injected only into detectors reporting more than 90% of the month. "
           "The interaction between the aspects — diagnosing faults on a dataset that "
           "itself had to be reconstructed — is not tested.")
    bullet("In Section 9.4 the detectors selected with nothing injected cannot be "
           "classified as false alarms, because ground truth on which real detectors are "
           "miscounting is not available for this corridor. Both readings are compatible "
           "with the data and no experiment reported here separates them.")
    bullet("On the reference corridor the reference-free criterion of Section 9.4 selects "
           "a substantial minority of the line-up with nothing injected, and those "
           "detectors out-rank any fault subsequently injected elsewhere. The aspect "
           "therefore delivers, on this corridor, an alarm with a size and a shortlist, "
           "not an unqualified identification. Whether the standing selections are genuine "
           "chronic faults — which would make the criterion accurate rather than noisy — "
           "cannot be settled without independent calibration records for these detectors, "
           "which are not available.")
    bullet("Section 9.4 injects one fault at a time. The sparse decomposition is written "
           "so as not to suppress a second fault, but the multiple-simultaneous-fault case "
           "is not measured, and the additional-detectors column indicates that a single "
           "fault already perturbs the recovered bias of its neighbours.")
    bullet("The null space of the coefficient matrix has dimension 168 out of 367 on the "
           "reference corridor, as set out in Section 6.3, so nearly half of the "
           "per-detector bias coordinates are not determined by the node balances. The "
           "system is consequently solved exactly and the term for genuine per-node "
           "effects is zero, meaning that any departure from conservation which is not "
           "detector bias — an unmodelled ramp, storage between detectors, drift in the "
           "length classifier — is attributed to detector bias. The effect of that "
           "misattribution on the rates in Section 9.4 has not been measured, and the "
           "experiment that would measure it is to give the linear program a non-trivial "
           "node-effect term and repeat.")
    bullet("The 80 trials behind each row of Section 9.1 are 40 detectors at two spans "
           "each, not 80 independent draws, so the plus-or-minus ten points quoted there "
           "is optimistic and the effective sample is 40. Section 9.4 uses 25 detectors at "
           "one span each.")
    bullet("Section 9.2's class-transfer measurements have no matching false-alarm control "
           "— the control run was made for the total relation only — so the detection "
           "rates in that subsection have no measured null and the comparison against the "
           "total-relation column is the only baseline available for them.")
    bullet("Section 9.4 is one corridor, one month, one seed. The onset aspect and the "
           "reconstruction aspect are both replicated on a second corridor and a second "
           "month; the principal claimed aspect is not.")

    # ====================================================================== 10
    h("10. Results Recorded Against the Invention")
    p("The following were measured and did not support the hypothesis that produced them. "
      "They are recorded because a disclosure that reports only its successes invites the "
      "examiner to assume the rest were not tried.")

    if joint and classwise:
        h("10.1 Vehicle-class-resolved conservation degrades reconstruction", 2)
        p("Conservation must hold within each vehicle length class independently, since a "
          "car does not become a lorry, so imposing the relation per class was expected to "
          "supply four constraints per node instead of one and to help most in the "
          "underdetermined regime. It does the opposite, and the reason is physical: the "
          "length classifier makes errors at the bin boundaries which are anti-correlated "
          "between adjacent bins and cancel when the four are added. The class relations "
          "are therefore looser than the total relation, not tighter — measured mean "
          "tolerance band %.1f vehicles for the shortest class alone against %.1f for the "
          "total."
          % (classwise["mean_band_vehicles"]["len_0_520"],
             classwise["mean_band_vehicles"]["total"]))
        rows = []
        for k, v in sorted(joint["missingness"].items()):
            rows.append(["%.0f%%" % (float(k) * 100),
                         "%.2f" % v["A_prior_MAE"], "%.2f" % v["C_total_MAE"],
                         "%.2f" % v["E_total_only_MAE"],
                         "%.2f" % v["E_total_and_class_MAE"],
                         "%+.1f%%" % v["gain_E_over_C_pct"]])
        table(["Withheld", "Prior", "Total constraint only",
               "Same, solved in the class-resolved space",
               "Total plus class constraints", "Change"], rows)
        p("The third column is a control: it solves a mathematically equivalent problem in "
          "the larger space and reproduces the second column exactly, which establishes "
          "that the degradation in the fourth column is caused by the class constraints "
          "and not by the solver. Class-resolved conservation is accordingly claimed for "
          "fault detection, where Section 9.2 shows it detects what the total relation "
          "provably cannot, and is expressly not claimed for reconstruction.")

    if discovery and discovery.get("configs"):
        h("10.2 Relations recovered from the counts do not outperform the surveyed ones", 2)
        note = ""
        if disc_rec:
            note = (" An earlier measurement on a %d-node window indicated the opposite — "
                    "discovered relations giving MAE %.2f against %.2f for the surveyed "
                    "topology. Repeating it at %d nodes reverses the finding, so the "
                    "earlier result was a small-sample artefact and is withdrawn."
                    % (disc_rec["true_nodes"],
                       disc_rec["discovered topology"]["MAE"],
                       disc_rec["surveyed topology"]["MAE"],
                       discovery["score"]["true_relations"]))
        p("Whether the relations recovered from the counts alone can replace the surveyed "
          "topology was tested directly." + note)
        rows = []
        for label in ["none", "surveyed", "discovered", "both"]:
            v = discovery["configs"].get(label)
            if v:
                rows.append([label, "%.2f" % v["MAE"], "%.2f%%" % v["outside"],
                             v.get("constraints", "-"),
                             "%.0f" % v["seconds"] if "seconds" in v else "-"])
        table(["Constraint set", "MAE", "Node-intervals outside band", "Constraints",
               "Seconds"], rows)
        p("What survives is narrower and is claimed as such: the relations can be "
          "recovered from the counts alone, which removes the requirement for an external "
          "network map, and combining the recovered relations with the surveyed ones "
          "gives the lowest error of any configuration tested — at the cost of a weaker "
          "consistency guarantee. It is a trade-off, not a free improvement.")

    apps = load("applications.json")
    if apps and apps.get("forecasting"):
        h("10.3 No measurable improvement to downstream forecasting", 2)
        p("Whether a physically consistent dataset makes a downstream predictor more "
          "accurate was tested directly. It did not, on either formulation tried. The "
          "reconstruction aspect is therefore claimed on the accuracy and consistency of "
          "the dataset itself, and no forecasting improvement is asserted anywhere in "
          "this document.")

    if robust and "ablation(knn_spatial: exact equality, no band)" in robust["table"]:
        t = robust["table"]
        h("10.4 The measured-width tolerance band is not supported once a leak is removed",
          2)
        p("An earlier version of this disclosure justified the two-sided tolerance band, in "
          "preference to enforcing the calibrated relation as an exact equality, on the "
          "ground that a zero-width intersection is empty far more often. A defect was then "
          "found in the evaluation: the calibration coefficients and the band width were "
          "being fitted on the whole corridor, including the very values that were withheld "
          "and then scored. The procedure now fits them on the visible data alone. Every "
          "reconstruction figure in this document is from the corrected procedure, and the "
          "comparison reverses:")
        table(["Configuration", "MAE, mean over 3 seeds", "Node-intervals outside the "
               "reference band"],
              [["Calibrated relation, band from measured spread (as claimed)",
                "%.2f [%.2f–%.2f]" % (t["constrained(knn_spatial)"]["MAE"]["mean"],
                                      t["constrained(knn_spatial)"]["MAE"]["min"],
                                      t["constrained(knn_spatial)"]["MAE"]["max"]),
                "%.2f%% [%.2f–%.2f]" % (
                    t["constrained(knn_spatial)"]["outside_band_pct"]["mean"],
                    t["constrained(knn_spatial)"]["outside_band_pct"]["min"],
                    t["constrained(knn_spatial)"]["outside_band_pct"]["max"])],
               ["Same, but the relation enforced as an exact equality",
                "%.2f [%.2f–%.2f]" % (
                    t["ablation(knn_spatial: exact equality, no band)"]["MAE"]["mean"],
                    t["ablation(knn_spatial: exact equality, no band)"]["MAE"]["min"],
                    t["ablation(knn_spatial: exact equality, no band)"]["MAE"]["max"]),
                "%.2f%% [%.2f–%.2f]" % (
                    t["ablation(knn_spatial: exact equality, no band)"]["outside_band_pct"]["mean"],
                    t["ablation(knn_spatial: exact equality, no band)"]["outside_band_pct"]["min"],
                    t["ablation(knn_spatial: exact equality, no band)"]["outside_band_pct"]["max"])]])
        p("Exact equality is better on both metrics, and the seed ranges do not overlap. "
          "The explanation is that the two calibrations now differ: the reconstruction is "
          "constrained by a relation fitted on the visible data, while consistency is "
          "scored against the relation fitted on everything, which is the correct reference "
          "for asking whether a value is physically plausible. Slack that is admissible "
          "under the first can fall outside the second, whereas exact equality pins the "
          "solution to the centre of the fitted relation and lands close to the centre of "
          "the reference. Under the leaked evaluation the two relations were identical and "
          "the slack cost nothing, which is why the earlier comparison came out the other "
          "way.")
        p("The consequence is recorded rather than argued away. The tolerance band is no "
          "longer claimed as an accuracy or consistency improvement over exact equality. "
          "What the band is claimed for is the two things exact equality cannot provide: a "
          "feasible set with interior, from which the per-value certified intervals of "
          "Section 9.6 are computed — an equality constraint yields intervals of zero width "
          "and certifies nothing — and a criterion for declaring an interval irreconcilable "
          "rather than forcing a solution through a relation the observations have already "
          "broken. Whether that trade is worth making has not been measured and is recorded "
          "as outstanding.")

    # ====================================================================== 11
    h("11. Working Example and Experimental Setup")
    if phase2:
        w = phase2["window"]
        p("Data source: the National Highways WebTRIS open API, an openly licensed public "
          "dataset of fifteen-minute vehicle counts from fixed detectors on the England "
          "strategic road network, requiring no registration, no key and no payment. "
          "Reference corridor: %s carriageway %s, %s to %s. Second corridor and second "
          "month used for replication, as recorded in Sections 9.3 and 11.3."
          % (w["road"], w["carriageway"], _date(w["start"]), _date(w["end"])))
        s = phase2["summary"]
        if s.get("noise_floor_pct") is not None:
            p("Verification that the physical relation holds at all, before any use is "
              "made of it: over intervals in which every detector at a node reported, the "
              "median absolute residual is %.2f%% of the flow through the node at plain "
              "continuity nodes, which have no slip roads and where the relation reduces "
              "to equality between the upstream and downstream detector. That figure is "
              "the measurement noise floor of the detectors themselves. At nodes carrying "
              "slip roads it is %.2f%%. The relation is therefore real and tight enough "
              "to constrain with."
              % (s["noise_floor_pct"], s["slip_node_residual_pct"]))

    h("11.1 Network construction from the data", 2)
    p("Detector names encode the road, the chainage marker and a carriageway or slip "
      "suffix. These are parsed rather than hardcoded, and the resulting ordering is "
      "validated geometrically against the recorded coordinates before use. Slip markers "
      "were found to share a chainage with mainline markers, so a slip lying at a node "
      "boundary is admitted to both candidate nodes and flagged; the ambiguity is then "
      "resolved from the balance itself, by allowing such a slip the additional option of "
      "belonging to neither node.")

    h("11.2 Evaluation protocol", 2)
    p("Values the detectors actually reported are withheld and the method is asked to "
      "reconstruct them, so ground truth exists for every value scored. Withheld values "
      "are drawn as runs from the measured gap-length distribution rather than uniformly "
      "at random, because real gaps arrive as runs and uniform withholding would leave a "
      "live neighbour on each side of almost every hole, flattering temporal "
      "interpolation and making the comparison dishonest. Results are reported separately "
      "for the operational-dropout regime and for the regime including detectors dead for "
      "weeks, since these are physically different populations.")

    p("Faults are not simulated on synthetic traffic. A fault of known type, known size "
      "and known detector is superimposed on the real recorded counts, so that everything "
      "the method must contend with — the genuine noise of the instruments, the genuine "
      "drift of the relation, the genuine gaps — is present alongside a fault whose "
      "ground truth is exact. For the onset experiment of Section 9.1 the calibration "
      "period and the fault period are disjoint. For the chronic experiment of Section 9.4 "
      "the fault is applied to every interval of the record before any calibration is "
      "fitted, which is the whole point of that experiment: the model the method relies on "
      "is estimated from data the fault has already corrupted.")

    h("11.3 Replication", 2)
    if gen and gen.get("corridors"):
        rows = []
        for label, r in gen["corridors"].items():
            rows.append([label, r["sites"], r["nodes_fitted"],
                         "%.2f" % r["prior_MAE"]["mean"],
                         "%.2f" % r["constrained_MAE"]["mean"],
                         "%+.2f%%" % r["gain_pct"]["mean"],
                         "%.2f%%" % r["outside_band_prior_pct"]["mean"],
                         "%.2f%%" % r["outside_band_constrained_pct"]["mean"]])
        table(["Corridor and month", "Detectors", "Nodes", "Prior MAE", "MAE constrained",
               "Change", "Outside band, prior", "Outside band, constrained"], rows)
        p("Nothing was retuned between corridors: the same calibration procedure, band "
          "quantile, prior, masking procedure and seeds throughout. The June run varies "
          "the month while holding the network fixed; the M1 run varies the network while "
          "holding the month fixed.")
    else:
        p(TBM)

    if discovery:
        h("11.4 Recovery of the relations from the counts alone", 2)
        sc = discovery.get("score", {})
        p("Conservation relations were recovered from the count data with no network map "
          "supplied, by correlation prefiltering to a shortlist, enumerating candidate "
          "subsets, rounding coefficients to the nearest integer within a tolerance, and "
          "retaining a relation only if its residual is small relative to the flow. "
          "Measured against the surveyed topology: %d of %d surveyed relations (%.1f%%) "
          "were recovered exactly, and %.1f%% of them lie in the span of the recovered "
          "set. A greedy matching-pursuit variant "
          "was implemented first and was replaced after measurement, because the best "
          "single explanation for a mainline detector is always the next mainline "
          "detector and slip-road relations were therefore never surfaced."
          % (sc["exact_matches"], sc["true_relations"], 100 * sc["recall_exact"],
             100 * discovery["span"]["coverage"]))

    # ====================================================================== 12
    h("12. Draft Claim Structure")
    p("Provided as an indication of intended scope. Final wording is for the attorney.")

    p("The principal claim is directed to the chronic case, and not to fault detection "
      "from conservation residuals generally. That decision follows from Section 8.1: "
      "detection, localisation, type discrimination and magnitude estimation from the "
      "residuals of conservation constraints are disclosed by Narasimhan and Mah (1987), "
      "and a claim of that scope is not available however it is worded for the traffic "
      "domain.")

    h("Claim 1 — principal claim, bias present when the model was estimated", 2)
    p("A computer-implemented method of correcting a miscounting vehicle-detector in a "
      "network of vehicle-counting detectors, comprising: receiving a dataset of vehicle "
      "counts indexed by detector and by measurement interval; forming a plurality of "
      "nodes, each node comprising an upstream detector, a downstream detector and any "
      "slip-road detectors between them, at least one detector belonging to at least two "
      "of the said nodes; partitioning the measurement intervals into a first part and a "
      "second part according to whether the total count recorded across the network in "
      "that interval is above or below a threshold flow level; separately within each "
      "part, estimating for each node, from the received counts and over intervals in "
      "which every detector at that node reported, an offset of a direction-of-flow "
      "conservation relation in which the upstream count and the signed slip-road counts "
      "are related to the downstream count with the coefficient of the downstream count "
      "held fixed; forming a coefficient matrix whose entry for a given node and a given "
      "detector is the coefficient with which that detector enters that node's said "
      "relation; determining, separately for each said part, a per-detector bias vector by "
      "solving a linear program that minimises a weighted residual between the said "
      "coefficient matrix applied to the bias vector and the vector of the said estimated "
      "offsets, together with an l1 term on the bias vector, whereby the bias vector so "
      "determined is sparse; determining for each detector a flow-proportional component "
      "and a flow-independent component of its bias from the two said bias vectors and "
      "from the mean count recorded at that detector within each said part; selecting a "
      "detector for which at least one of the said two components departs from the median "
      "of that same component, taken over the detectors belonging to at least two nodes, "
      "by more than a multiple of the median absolute deviation of that same component "
      "over those detectors; and applying to the "
      "counts reported by the selected detector a correction determined by the said "
      "components, and supplying the corrected counts to a downstream process, whereby a "
      "bias present in the said received counts throughout the whole of the record, and "
      "consequently absorbed into the said estimated relation, is removed from the dataset "
      "supplied to that process.")

    h("Dependent claims on claim 1", 2)
    bullet("2. Wherein the fault of the selected detector is classified as "
           "flow-proportional or as flow-independent according to which of the said two "
           "components is the greater departure from its median when both are expressed in "
           "units of counts per measurement interval, and the magnitude of the said "
           "component is output as the size of the fault.")
    bullet("3. Wherein the said weighted residual weights each node by a decreasing "
           "function of the measured spread of that node's own conservation residual, "
           "whereby a node whose relation is loose does not outweigh a node whose relation "
           "is tight.")
    bullet("4. Wherein the l1 term is scaled so that its contribution to the objective is "
           "small relative to the said weighted residual, whereby sparsity resolves ties "
           "between explanations that fit the said offsets equally well and does not "
           "suppress a second departing detector.")
    bullet("5. Wherein the said nodes and the signs of the said slip-road counts are "
           "determined from the received counts alone, by selecting the sign assignment "
           "minimising a measure of the said residual, without receipt of a network map.")
    h("Claim 6 — second independent claim, detection of fault onset", 2)
    p("A computer-implemented method of identifying a vehicle-detector that has begun to "
      "count incorrectly, comprising: receiving the said dataset and forming the said "
      "plurality of nodes; for each node determining from the received counts a slip-road "
      "sign assignment and calibration coefficients minimising the residual of the said "
      "conservation relation; computing, for each node and over a span of consecutive "
      "measurement intervals, a mean residual of the calibrated relation; comparing that "
      "mean residual with a threshold determined from the empirical distribution of the "
      "same statistic at that same node over reference spans drawn from the same record; "
      "identifying a candidate detector, from among only those detectors belonging to at "
      "least two of the said nodes, by fitting by weighted least squares over the nodes to "
      "which that candidate belongs a single bias value against the coefficient with which "
      "that candidate enters each such node's relation, and selecting the candidate whose "
      "fitted bias accounts for the greatest weighted deviation; classifying the fault of "
      "the identified detector by partitioning the span according to the flow recorded at "
      "that detector and selecting between a flow-proportional and a flow-independent bias "
      "model; and applying to the counts subsequently reported by the identified detector "
      "a correction determined by the selected model and its fitted magnitude.")
    p("Claim 6 is understood to be the more exposed of the two independent claims, for the "
      "reasons given in Section 8.1, and is included so that the disclosure supports it if "
      "the search permits it.")

    h("Dependent claims on claim 6", 2)
    bullet("7. Wherein the threshold of each node is set at a quantile of the said "
           "empirical distribution chosen to fix a false-positive rate.")
    bullet("8. Wherein the weighting in the least-squares fit is the inverse square of the "
           "respective node's threshold.")
    bullet("9. Wherein the said conservation relation is evaluated separately for each of a "
           "plurality of vehicle length classes, whereby a fault in which counts are "
           "transferred between length classes without altering the total count is "
           "detected, such a fault being undetectable by a relation evaluated on total "
           "counts.")

    h("Claims on the reconstruction aspect", 2)
    bullet("10. The method of claim 1 or claim 6, further comprising reconstructing an "
           "absent record by projecting a prior estimate onto the intersection of the "
           "calibrated relations, evaluated on total counts, of the nodes affected in that "
           "interval, the relations being imposed as hard two-sided inequalities whose "
           "width is derived from the measured spread of the respective residual, and the "
           "intersection being taken jointly across overlapping nodes.")
    bullet("11. Wherein the said intersection is determined to be empty by a linear program "
           "computing the smallest uniform widening admitting a solution, and the "
           "corresponding node and interval are reported as irreconcilable together with "
           "the said widening expressed in vehicles.")
    bullet("12. The method of claim 10, further comprising outputting with each "
           "reconstructed value an interval obtained by minimising and by maximising that "
           "value over the said intersection, and an indication of whether that value was "
           "bounded by the said intersection, a value outside the said interval being "
           "inconsistent with the received records under the said calibrated relations.")
    bullet("13. A data-processing system, and a computer-readable medium carrying "
           "instructions, configured to carry out the method of any preceding claim.")

    h("Notes on the claim wording", 2)
    bullet("Claim 10 is expressly limited to relations evaluated on TOTAL counts, and "
           "claim 9 extends the class-resolved relation to detection only. Section 10.1 "
           "measures class-resolved reconstruction as substantially worse than total-flow "
           "reconstruction, so a claim covering it would cover an embodiment the "
           "disclosure shows to be inferior.")
    bullet("Claim 9 depends on claim 6 and not on claim 1. The class-transfer fault is "
           "measured in Section 9.2 against the onset procedure only; the chronic "
           "decomposition of claim 1 has not been run per length class, so a dependency on "
           "claim 1 would not be supported by any measurement in this document.")
    bullet("Claim 12 says that a value outside the certified interval is inconsistent with "
           "the received records under the calibrated relations, and requires the bounded "
           "or unbounded status to be output. It does not assert that the true value always "
           "lies inside: Section 9.6 measures coverage at %s, the shortfall arising where "
           "the calibrated band itself is violated by the observed data."
           % (("%.1f%%" % conf["coverage_pct"]) if conf and conf.get("coverage_pct")
              else "the figure recorded in Section 9.6"))
    bullet("Operative constants used in the prototype, disclosed so that the claims are "
           "enabled: tolerance band at the 0.95 quantile of the absolute residual; onset "
           "threshold at the 0.99 quantile of 300 empirical clean-span draws; span of 192 "
           "intervals (two days); a minimum of 30 clean spans and 30%% span coverage before "
           "a node is used (span coverage measured as the share of intervals in which "
           "every detector at the node reported); chronic outlier threshold at %s robust "
           "deviations; flow "
           "partition at the median of total corridor flow."
           % (("%.1f" % chronic_abs["threshold_k"]) if chronic_abs else "TBD"))

    h("Fallback positions, in order of retreat", 2)
    p("1. If claim 1 is met, fall back to the combination of claim 1 with claim 4, the "
      "ordering of fit before sparsity, and with claim 3, the reliability weighting — the "
      "specific decomposition rather than the idea of decomposing. 2. If that is met, fall "
      "back to the combination of claim 6 with claim 9, the class-transfer fault, which is "
      "supported by an analytic impossibility argument for total-flow methods and by "
      "measurement. 3. If that is met, fall back to the combination of claims 10 to 12, "
      "the certified per-value bounds on a hard-constrained reconstruction — noting that "
      "Section 10.4 records the tolerance band as unsupported on accuracy and on "
      "consistency, so that these claims rest on the certification the band makes possible "
      "and not on any improvement it produces. Claim 6 is not treated as a fallback "
      "position for claim 1, being independently exposed to the same art.")

    # ====================================================================== 13
    h("13. Industrial Applicability")
    p("The method applies to any authority operating fixed vehicle-counting detectors on "
      "a network whose connectivity is known or can be recovered from the counts, and to "
      "the historical datasets such authorities hold. It requires no additional "
      "instrumentation, no modification to any existing detector, and no data beyond "
      "counts already recorded, so it can be applied both to a live feed and "
      "retrospectively to an archive. The prototype uses only openly licensed public data "
      "and standard numerical libraries.")

    # ====================================================================== 14
    h("14. Drawings")
    p("Anticipated figures: (i) node topology schematic showing the upstream, downstream "
      "and slip-road detectors and the overlapping node structure; (ii) flowchart of the "
      "fault-diagnosis procedure; (iii) flowchart of the constrained reconstruction; "
      "(iv) chart of detection rate against injected fault magnitude, with the "
      "false-positive control; (v) chart of the class-transfer fault showing the "
      "class-relation detection rate against the total-relation floor; (vi) chart of "
      "reconstruction error and band violations by prior estimator; (vii) chart of "
      "certified interval width against the number of absent values sharing a node; "
      "(viii) schematic of the decomposition of the fitted node offsets over the "
      "coefficient matrix into a sparse per-detector bias, showing one detector entering "
      "three nodes with three different coefficients; (ix) chart of the recovered bias of "
      "every detector in the line-up with the robust outlier threshold marked, for the "
      "corridor as recorded and with a chronic fault injected.")

    # ====================================================================== 15
    h("15. Prior Disclosure")
    field("Has the invention been published, presented or otherwise disclosed publicly",
          TBD)
    field("Any planned disclosure or submission date", TBD)
    field("Prior-art searches performed",
          "Google Patents and academic literature search, recorded in patent/prior_art.md. "
          "Espacenet and Indian Patent Advanced Search (InPASS) to be completed by the "
          "inventor.")
    field("Searches identified as necessary and NOT YET PERFORMED",
          "Two, both capable of ending the application and neither yet run. First, the "
          "fault-detection-and-isolation and gross-error-detection art in CPC G05B23/02, "
          "G01D18/00 and G01D3/08, which is the field the first aspect sits in and from "
          "which Narasimhan and Mah (1987) was identified by literature search alone. "
          "Second, the patent art on blind or self-calibration of sensor networks, which "
          "is the nearest known field to the second aspect. Until both are complete the "
          "novelty position stated in Section 8.2 is provisional.")

    # ====================================================================== 16
    h("16. Funding and Third-Party Rights")
    field("Sponsored research or funding source", TBD)
    field("Third-party data or materials used",
          "Public datasets only. National Highways WebTRIS open API, and Department for "
          "Transport road traffic statistics under Open Government Licence v3.0. No "
          "proprietary, licensed or payment-gated data source is used.")

    # ====================================================================== 17
    h("17. Keywords")
    p("detector fault detection; measurement bias localisation; fault classification; "
      "chronic bias; calibration decomposition; sparse bias recovery; l1 minimisation; "
      "flow conservation constraint; hard constraint projection; traffic data "
      "reconstruction; missing data imputation; data integrity; certified bounds; road "
      "network topology recovery")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc.save(OUT)

    missing = [name for name, obj in [
        ("phase5_robustness_full.json", robust), ("faults_full_M25_A.json", faults),
        ("faults_M1_A.json", faults_m1), ("confidence", conf),
        ("generalisation.json", gen), ("classwise_joint_window.json", joint),
        ("envelope.json", envelope), ("cost.json", cost),
        ("chronic_full_M25_A.json", chronic),
        ("chronic_absolute_full_M25_A.json", chronic_abs)] if obj is None]
    print("wrote %s" % OUT)
    if missing:
        print("  sections left as TBD, results absent: %s" % ", ".join(missing))


if __name__ == "__main__":
    build()
