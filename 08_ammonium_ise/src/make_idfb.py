"""Build the IDF-B for the ammonium sonde corrected by its own record floor, anchored at
laboratory samples.

Layout: the accepted VIT IDF-B (masthead, eleven numbered sections), through the layout helpers
of the CausalInterlock generator and the table/figure/claim helpers of the patent 05 generator,
imported unchanged (as in patent 06). Every measured number is read from results/*.json at build
time; the build refuses to run when a results file is missing or when a comparison stated in
words no longer holds. After writing, the document is scanned for placeholders, business-method
vocabulary and banned phrases.
"""
import datetime as dt
import importlib.util
import json
import os
import re
import sys

from docx import Document
from docx.shared import Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sys.path.insert(0, r"C:\adi\patents\01_02_infosec\IDF-B_CausalInterlock")
import build_idfb as B                                            # noqa: E402

P3 = _load_module("p3_make_idfb", r"C:\adi\patents\05_length_invariance\src\make_idfb.py")
sys.path.insert(0, os.path.join(ROOT, "src"))
import ea                                                         # noqa: E402
import evidence as EV                                             # noqa: E402

B.FIG = os.path.join(ROOT, "patent", "figures")
OUT = os.path.join(ROOT, "patent", "IDF-B_Ammonium_Sonde_Floor_Anchor.docx")
h1, h2, para, bullets = B.h1, B.h2, B.para, B.bullets
table, figure, claim, Numbering, trl_table = P3.table, P3.figure, P3.claim, P3.Numbering, P3.trl_table
FORBIDDEN = P3.FORBIDDEN
BANNED = [b for b in P3.BANNED if b not in ("python",)] + ["python"]
OPENERS, PLACEHOLDER = P3.OPENERS, P3.PLACEHOLDER
PHYSICAL = re.compile(r"sonde|sensor|electrode|ISE|controller|river|laborator|sample|link \(130\)|"
                      r"archive|membrane|ammonium", re.I)

TITLE = ("In-Situ River Ammonium Monitoring Station with Electrode-Offset Tracking from the Floor "
         "of Its Own Record Anchored at Laboratory Samples, and Method Thereof")


def load(name):
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path):
        raise SystemExit("results absent, refusing to build with invented figures: %s" % name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def f1(x):
    return "%.1f" % x


def f2(x):
    return "%.2f" % x


def f3(x):
    return "%.3f" % x


def ordinal(n):
    n = int(round(n))
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "%d%s" % (n, suf)


def flip(s):
    """A sign test of x against the method, read from the method's side."""
    return {"better": s["worse"], "worse": s["better"], "of": s["of"], "z": -s["z"]}


def mmt(b):
    """'median / p90 / trimmed mean' of a summary block, mg/L."""
    return "%s / %s / %s" % (f3(b["median"]), f2(b["p90"]), f2(b["trimmed_mean_99"]))


def bz(b):
    return "%d of %d (z = %s)" % (b["better"], b["of"], f2(b["z"]))


def ci(b):
    return "%s (95 %% interval %s to %s)" % (f3(b["mean"]), f3(b["ci95"][0]), f3(b["ci95"][1]))


def build():
    m = load("ev_main.json")
    sens = load("ev_sens.json")
    ex = load("fig05_example.json")
    sites = load("sites_amm.json")
    meta = m["meta"]
    W = m["with_prior"]
    P = m["with_prior_paired"]
    A = m["alarms"]
    FS, FSP = m["first_sample"], m["first_sample_paired"]
    FF = m["floor_follows_offset"]
    SV = m["serviced"]
    LB = m["by_lab_band"]
    HV = m["halves"]
    HOLD = load("e6_guard_hold.json")
    VEND = load("e6_guard_vendor.json")
    PH = load("e8_physical.json")
    n_amm = len(ea.sonde_stations("ammonium"))
    DAYS, Q, WIN, MINR = meta["floor_days"], meta["floor_q"], meta["window"], meta["min_read"]
    QP = int(round(100 * Q))
    s_lo = min(s["method"]["median"] for s in sens)
    s_hi = max(s["method"]["median"] for s in sens)
    zb_lo = min(s["paired_best"]["z"] for s in sens)
    zb_hi = max(s["paired_best"]["z"] for s in sens)
    # comparisons stated in words; refuse to build if the numbers no longer say so
    words = {
        "method lowest median of all baselines": all(W["method"]["median"] < W[h]["median"] for h in W if h != "method"),
        "method better more often than every practice baseline": all(P[h]["z"] > 1.96 for h in ("median", "last", "trend", "practice_best")),
        "station bootstrap median CIs exclude zero": all(m[k]["median"]["ci95"][0] > 0 for k in ("bootstrap_vs_median", "bootstrap_vs_last", "bootstrap_vs_practice_best")),
        "p90 CI includes zero vs chosen practice": m["bootstrap_vs_practice_best"]["p90"]["ci95"][0] < 0,
        "both halves significant vs chosen practice": all(v["paired_best"]["z"] > 1.96 for v in HV.values()),
        "every sensitivity run beats chosen practice": all(s["paired_best"]["z"] > 1.96 and s["method"]["median"] < s["practice_best"]["median"] for s in sens),
        "gain in both service splits": all(v["paired"]["z"] > 1.96 for v in SV.values()),
        "no significant gain above 1 mg/L": all(abs(LB[k]["paired"]["z"]) < 1.96 for k in ("1-3", "3-1e+09")),
        "fewer false alarms than every practice baseline at 0.6 and 1 mg/L":
            all(A[t]["method"]["false_alarms"] < A[t][h]["false_alarms"] for t in ("0.6", "1")
                for h in ("median", "last", "trend", "practice_best")),
        "false alarms level with chosen practice at 2 mg/L (within 5)":
            abs(A["2"]["method"]["false_alarms"] - A["2"]["practice_best"]["false_alarms"]) <= 5,
        "more misses than chosen practice at 2 mg/L": A["2"]["method"]["missed"] > A["2"]["practice_best"]["missed"],
        "floor alone not better than practice in median": W["floor_net"]["median"] >= W["last"]["median"] - 0.002,
        "first sample beats network constant": FSP["net_const"]["z"] > 1.96,
        "slope near one": 0.7 < FF["slope_departure_on_floor"] < 1.3,
        "watch tier misses fewer than median, last and chosen practice at every threshold":
            all(A[t]["watch"]["missed"] < A[t][h]["missed"] for t in A for h in ("median", "last", "practice_best")),
        "trend misses fewer than watch at 2 mg/L but with more false alarms":
            A["2"]["trend"]["missed"] < A["2"]["watch"]["missed"] and A["2"]["trend"]["false_alarms"] > A["2"]["watch"]["false_alarms"],
        "confirmed tier fewer false alarms than every practice baseline at every threshold":
            all(A[t]["confirmed"]["false_alarms"] < A[t][h]["false_alarms"] for t in A for h in ("median", "last", "trend", "practice_best")),
        "offset held between services is no better than practice":
            abs(HOLD["all"]["guarded"]["median"] - W["practice_best"]["median"]) < 0.01 and HOLD["guarded_vs_method"]["z"] < -1.96,
        "vendor drift cap worse than free floor": VEND["guarded_vs_method"]["z"] < -1.96
            and VEND["all"]["guarded"]["median"] > W["method"]["median"],
        "e6 used the same samples": HOLD["n"] == meta["samples_with_prior"] and abs(HOLD["all"]["method"]["median"] - W["method"]["median"]) < 1e-9,
    }
    wrong = [k for k, ok in words.items() if not ok]
    if wrong:
        raise SystemExit("text no longer matches the results: %s" % wrong)

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = B.BODY_FONT
    st.font.size = Pt(11)
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Inches(0.9)
    sec.top_margin = sec.bottom_margin = Inches(0.85)
    B.running_heads(sec)
    B.letterhead(doc)
    num = Numbering()

    # ============================================================== 1
    h1(doc, "1. Title of the Invention")
    para(doc, TITLE + ".")

    # ============================================================== 2
    h1(doc, "2. Field / Area of Invention")
    para(doc,
         "The present invention relates to in-situ water-quality monitoring stations in which a sonde "
         "carrying an ammonium ion-selective electrode (ISE), a high-impedance analogue front end and a "
         "sonde controller is placed in a river and reports ammonium over a telemetry link. More "
         "particularly, it pertains to a station and method that determine, at every reading, the "
         "calibration offset carried by the ammonium electrode, from the lower envelope (floor) of the "
         "electrode's own recent record anchored to laboratory analyses of grab samples taken at the "
         "sonde; that write the offset in force into the sonde controller; and that drive an automatic "
         "sampler and an intake isolation interlock from a two-tier alarm on the corrected reading.")
    para(doc,
         "An ammonium ISE turns the potential between an ammonium-selective membrane and a reference "
         "electrode into a concentration through a calibration line. Its offset is set at calibration "
         "and then moves: the reference junction ages, the membrane conditions and fouls, and each "
         "service or swap of the sonde sets a new offset. Grab samples analysed in a laboratory check "
         "the reading every few weeks, and the difference is applied as a correction value to later "
         "readings (US 8,691,074 B2 [P1]) or spread between samples after the fact (Wagner et al. [N3]; "
         "Pedersen et al. [N1]). At %d sondes of the Environment Agency of England that carried an "
         "ammonium electrode next to a laboratory sampling point, the raw reading differed from the "
         "laboratory result by a median of %s mg/L N (90th percentile %s mg/L); after the best of the "
         "current corrections, chosen per sonde from its own earlier samples, the median error was "
         "still %s mg/L, against laboratory values with a median of %s mg/L."
         % (meta["sites"], f3(W["raw"]["median"]), f2(W["raw"]["p90"]), f3(W["practice_best"]["median"]),
            f3(lab_median(m))))
    para(doc,
         "The technical problem addressed is to follow the offset of the electrode between laboratory "
         "samples from signals the station already records, without an added sensor, so that the "
         "ammonium the sonde reports, and the sampler and intake actions taken on it, follow the river "
         "and not the electrode.")

    h2(doc, "2.1 Technical Problem Addressed by the Invention")
    bullets(doc, [
        "The calibration offset of an ammonium electrode moves between laboratory samples, at "
        "services and by drift, and a correction value taken at the last sample is stale until the "
        "next one.",
        "The electrode signal alone cannot separate a moved offset from a change of the river: both "
        "raise or lower the whole record.",
        "Spreading corrections between samples needs the next sample, so it serves the archive after "
        "the fact and not the reading, the alarm or the sampler in real time.",
        "A failing electrode that reads far too high for days passes through a fixed correction value "
        "unchanged and keeps an alarm, a sampler or an intake interlock in the wrong state."])
    h2(doc, "2.2 Definitions")
    bullets(doc, [
        "Sonde (100): an in-situ water-quality instrument with an ammonium ISE (110) and a sonde "
        "controller (115) that digitises the electrode potential, logs a reading every 15 minutes and "
        "transmits it over a telemetry link (130).",
        "Reading A(t): the ammonium concentration (mg/L as N) reported by the sonde at time t.",
        "Laboratory result L_j: the ammoniacal nitrogen (mg/L as N) of a grab sample taken at the sonde "
        "at time t_j.",
        "Departure d_j: A(t_j) - L_j, the error of the reading at a laboratory sample.",
        "Floor F(t): a low quantile of the readings over a window of several days ending at t.",
        "Anchor gap g: the height of the floor above the true background at the site, F(t_j) - d_j, "
        "combined over earlier laboratory samples.",
        "Offset in force: F(t) - g, subtracted from A(t) by the sonde controller."])

    # ============================================================== 3
    h1(doc, "3. Prior Patents and Publications from Literature")
    para(doc,
         "Each reference below was checked against its own text before any statement about it was "
         "made: the full text of each publication where it is open, and the abstract and claims of each "
         "patent as published.")
    h2(doc, "A. Prior Patent Literature")
    PAT = [
        ("P1", "US 8,691,074 B2", "Method for operating a measuring device having at least one probe, which has at least one ion selective electrode",
         "Determines an apparent concentration in a first sample by standard addition and a reference "
         "concentration in a second sample by a reference method, and derives from their difference a "
         "correction value for future measured values (claim 1). One correction value until the next "
         "reference measurement; the probe's own record is not used to follow the offset."),
        ("P2", "CN 118914491 A", "Water quality monitoring station calibration, compensation, data processing and evaluation method and system",
         "Calibrates electrode sensors with standard solutions; compensates ion-selective sensors for "
         "sludge modelled from time since maintenance, flow and sludge properties; smooths data with "
         "slope and offset interpolated between concentrated-water-sample calibrations. No floor of the "
         "record anchored to laboratory results."),
        ("P3", "US 5,594,667 A", "Method and apparatus for baseline drift correction for a sensor",
         "Takes a sensor's baseline as the average of a fixed percentage of the lowest points of its own "
         "record (grain mass-flow sensor) and subtracts it. The baseline is the sensor's zero; no "
         "reference measurement fixes how far the true quantity lies above it."),
        ("P4", "US 10,918,318 B2", "System and methods for processing analyte sensor data for sensor calibration",
         "Calibrates a continuous implanted glucose sensor from a calibration set of matched sensor and "
         "reference data pairs (baseline and sensitivity). Calibration from matched pairs only; no low "
         "quantile of the sensor's record, no river ammonium."),
        ("P5", "JP H08-304324 A", "Method for correcting base concentration of sample water",
         "Spikes the sample water with a reference solution and corrects the electrode calibration "
         "curve for the sample's own base concentration, computed by a microcomputer. Laboratory-style "
         "spiking of one sample; no continuous record and no field laboratory samples."),
        ("P6", "EP 2 656 059 B1", "Analyte ion detection method and device",
         "Processes the signals of several electrodes with a neural network trained to calculate ion "
         "interference and electrode interference against known concentrations (claim 1). Needs an "
         "electrode array; no use of the record floor or of field laboratory samples."),
        ("P7", "CN 107884535 A", "An automatic calibration device and calibration method for a water quality on-line analyzer",
         "Calibration hardware: control modules, mixing tank, injection and peristaltic pumps and stirrer "
         "that prepare standard solutions for the analyser. Corrects at calibration events only."),
        ("P8", "CN 111398549 A", "A reagent-free multi-parameter water quality in-situ monitor",
         "Buoy with electrode and photometric modules for temperature, conductivity, dissolved oxygen, pH, "
         "ammonia nitrogen, turbidity and chemical oxygen demand, powered by solar panels. Hardware; no "
         "correction of the electrode between samples."),
    ]
    table(doc, ["S.No.", "Patent No.", "Title", "Comments"], [list(r) for r in PAT],
          "Table 1: Prior patent literature", widths=[0.5, 1.2, 1.7, 3.3], size=9, align_left_cols=(1, 2, 3))
    h2(doc, "B. Non-Patent Literature")
    NPL = [
        ("N1", "Pedersen et al. (2020), Water Research 185, 116227",
         "Reconstruction of corrupted datasets from ammonium-ISE sensors at WRRFs through merging with daily composite samples",
         "Removes recalibration jumps located from the operators' maintenance logbook, using the mean of "
         "10 observations before and after each jump, then multiplies the series by correction factors "
         "fixed on composite-sample days and linearly weighted between them. Retrospective: it needs the "
         "next sample; it does not use the floor of the record."),
        ("N2", "Jones et al. (2022), Environmental Modelling & Software 151, 105364",
         "Toward automating post processing of aquatic sensor data",
         "Detects calibration events from shifts and persistence in the record during field hours and "
         "applies a linear drift correction between two calibrations retroactively, from a gap value. "
         "After the fact; no laboratory-anchored floor."),
        ("N3", "Wagner et al. (2006), U.S. Geological Survey Techniques and Methods 1-D3",
         "Guidelines and standard procedures for continuous water-quality monitors",
         "Fouling and calibration-drift corrections measured at servicing and prorated linearly in time "
         "between the start and end of the correction interval. Practice reference; retrospective."),
        ("N4", "Kaelin et al. (2008), Water Science & Technology 58(3)",
         "Potential of in-situ sensors with ion-selective electrodes for aeration control at wastewater treatment plants",
         "Ammonium ISEs recalibrated at one point from weekly laboratory measurements; potassium "
         "interference corrected with a constant offset. One correction value per laboratory check."),
        ("N5", "Capella et al. (2020), Sensors 20, 7102",
         "A new ammonium smart sensor with interference rejection",
         "Supervises a set of redundant ISEs with an expert system to avoid random failures and reject "
         "interference from potassium and sodium. Needs several electrodes; no laboratory anchoring of an "
         "offset."),
        ("N6", "Research Square preprint (2026), doi 10.21203/rs.3.rs-8649960/v1",
         "Accurate measurement of ammonia nitrogen in water based on ammonium ion-selective electrodes with a hydrophobic layer and a parameter compensation strategy",
         "All-solid-state ammonium ISE with potassium-ISE calibration, pH compensation and temperature "
         "coefficient correction. Compensates interferents with added sensors; no record floor."),
        ("N7", "Xylem / YSI application note, EXO Ammonium ISE in UK water utilities",
         "Continuous monitoring of water utilities in the UK using the EXO Ammonium ISE",
         "Sondes calibrated in a laboratory about every two months and swapped in the field; grab samples "
         "every two weeks analysed by a certified laboratory; interfering species can cause false-positive "
         "readings; drift of 0.25 and 0.31 mg/L reported over a 73-day trial. No tracking of the offset "
         "between samples."),
        ("N8", "In-Situ Inc., technical note",
         "Follow these 5 tips to get the best data from your ammonium sensor",
         "Ammonium ISEs are particularly sensitive to sodium, potassium and magnesium; storage, "
         "conditioning and maintenance practice. No data-processing correction."),
    ]
    table(doc, ["S.No.", "Reference", "Title", "Comments"], [list(r) for r in NPL],
          "Table 2: Non-patent literature", widths=[0.5, 1.45, 1.6, 3.15], size=9, align_left_cols=(1, 2, 3))

    # ============================================================== 4
    h1(doc, "4. Summary and Background of the Invention")
    h2(doc, "4.1 Background")
    para(doc,
         "Rivers receive ammonium from sewage overflows, treatment works and farm runoff, and a few "
         "milligrams per litre harm fish and complicate treatment at downstream drinking-water intakes. "
         "Continuous sondes with an ammonium ISE are deployed so that an event is seen while it happens: "
         "an alarm calls staff, an automatic sampler takes a confirmation sample, and an intake can be "
         "isolated. The electrode is the weak part of the chain. Its offset moves with age, fouling and "
         "every service, and the sonde reports whatever offset it carries, so the sampler and the intake "
         "act on the electrode as much as on the river. Grab samples analysed in a laboratory measure the "
         "true concentration, but only every few weeks.")
    para(doc,
         "Existing practice keeps one correction value from the last laboratory check until the next "
         "[P1, N4, N7], spreads corrections between checks after the fact [N1, N2, N3, P2], or calibrates "
         "against matched reference pairs [P4, P5]. A sensor baseline can be taken from the lowest part of "
         "its own record [P3], but a river's true ammonium is not zero and differs between sites, so a floor "
         "alone mixes the offset with the background. Interference is handled with added electrodes or "
         "learned models [P6, N5, N6], and calibration with hardware [P7, P8]. None combines the floor of "
         "the record, which follows the offset continuously, with the laboratory samples, which fix how far "
         "that floor sits above the true background, and none drives the sonde controller, the sampler and "
         "the intake from two estimates of the offset.")
    h2(doc, "4.2 Distinctions from Prior Art")
    bullets(doc, [
        "From P1, N4 and N7: these apply the difference found at the last laboratory check until the next "
        "one. The invention updates the offset at every reading from the electrode's own record and uses "
        "the laboratory samples only to fix the height of the floor above background; on the same samples "
        "it is better more often than the last-sample correction: %s." % bz(P["last"]),
        "From N1, N2, N3 and P2: these spread corrections between checks or model sludge from time since "
        "maintenance, after the fact; N1 needs the maintenance logbook and N2 detects calibration events "
        "to correct retroactively. The invention needs neither and acts in real time, from readings up to "
        "the moment corrected and samples before it.",
        "From P3: P3 takes the low part of the record as the sensor's zero. Without the laboratory anchor "
        "the floor gives a median error of %s mg/L, no better than current practice (%s mg/L); with it, "
        "%s mg/L." % (f3(W["floor_net"]["median"]), f3(W["last"]["median"]), f3(W["method"]["median"])),
        "From P4 and P5: these calibrate from matched reference pairs or from a spiked sample; the "
        "invention keeps the calibration of the electrode and follows its offset between references "
        "through the floor of its record.",
        "From P6, N5, N6, P7 and P8: these reject interference with added electrodes or models, or provide "
        "calibration and sensing hardware; the invention adds no sensor and acts on the offset that these "
        "leave to calibration."])
    h2(doc, "4.3 Inventive Combination")
    para(doc,
         "The combination is: (i) the floor of the electrode's own ammonium record over a window of several "
         "days, which between pollution pulses returns to the river's background plus the offset in force; "
         "(ii) the anchor gap, fixed at earlier laboratory samples as the height of that floor above the true "
         "concentration's background; (iii) the offset in force taken as the floor less the gap, written to "
         "the sonde controller and subtracted from every reading in real time; and (iv) a two-tier alarm "
         "from the floor-tracked and the last-sample estimates of the offset, which drives an automatic "
         "sampler at the watch tier and an intake isolation interlock at the confirmed tier. Each part carries "
         "weight on the same %d samples: the floor without the anchor gives %s mg/L median error, the anchor "
         "without the floor (current practice) %s mg/L at best, an offset held between services %s mg/L, and "
         "the combination %s mg/L."
         % (meta["samples_with_prior"], f3(W["floor_net"]["median"]),
            f3(min(W[h]["median"] for h in ("median", "last", "trend", "practice_best"))),
            f3(HOLD["all"]["guarded"]["median"]), f3(W["method"]["median"])))
    h2(doc, "4.4 Feature Mapping Against Prior Art")
    FEAT = [
        ("F1", "Electrode's own continuous record used to follow the offset", "No", "Yes", "No", "No", "Yes", "No"),
        ("F2", "Low quantile (floor) of the record over a window of days", "No", "Yes", "No", "No", "No", "No"),
        ("F3", "Laboratory or reference results at the sensor", "Yes", "No", "Yes", "Yes", "No", "Yes"),
        ("F4", "Height of the floor above background fixed at laboratory samples", "No", "No", "No", "No", "No", "No"),
        ("F5", "Correction at every reading from earlier samples only (real time)", "Partial", "Yes", "Yes", "No", "No", "No"),
        ("F6", "Offset written to the sonde controller", "No", "No", "No", "No", "No", "No"),
        ("F7", "Two-tier alarm driving sampler and intake interlock", "No", "No", "No", "No", "No", "No"),
    ]
    table(doc, ["#", "Feature", "P1", "P3", "P4", "N1", "N2", "N7"], [list(r) for r in FEAT],
          "Table 3: Feature mapping of the invention against the nearest art",
          widths=[0.4, 2.9, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55], size=9, align_left_cols=(1,))
    h2(doc, "4.5 Technical Effects")
    bullets(doc, [
        "Ammonium reported by the sonde between laboratory samples: at %d samples of %d sondes, each "
        "corrected from readings up to its own time and laboratory results before it, the median absolute "
        "error falls from %s mg/L N for the best current correction chosen per sonde to %s mg/L (%d %% "
        "lower); better at %s and at %d of %d sondes. Resampling whole sondes, the median error falls by "
        "%s mg/L."
        % (meta["samples_with_prior"], m["sites_with_prior"], f3(W["practice_best"]["median"]),
           f3(W["method"]["median"]), round(100 * (1 - W["method"]["median"] / W["practice_best"]["median"])),
           bz(P["practice_best"]), m["sites_better"]["practice_best"], m["sites_with_prior"],
           ci(m["bootstrap_vs_practice_best"]["median"])),
        "Failing electrodes: the mean absolute error, dominated by readings far from the true value, falls "
        "from %s to %s mg/L, because such a fault lifts the floor with the reading."
        % (f1(W["practice_best"]["mean"]), f1(W["method"]["mean"])),
        "Sampler and intake actions: the watch tier, which triggers the automatic sampler, misses fewer "
        "exceedances than the per-sonde practice at every threshold (at 1 mg/L N, %d against %d); the "
        "confirmed tier, which operates the intake interlock, acts falsely less often (%d against %d); each "
        "tier gives up some performance on its other side (Table 10)."
        % (A["1"]["watch"]["missed"], A["1"]["practice_best"]["missed"],
           A["1"]["confirmed"]["false_alarms"], A["1"]["practice_best"]["false_alarms"]),
        "A sonde without its own laboratory history: at the first sample of each sonde the median error is "
        "%s mg/L, against %s for one network-wide correction value and %s for the raw reading."
        % (f3(FS["method"]["median"]), f3(FS["net_const"]["median"]), f3(FS["raw"]["median"])),
        "Within the station's timing and memory: %s microseconds of processing per 15-minute reading on one "
        "core and at most %d readings (about %s kB) held per sonde, so the corrected reading, the alarm tier "
        "and any relay command leave in the same reporting interval as the raw reading."
        % (f1(PH["processing_us_per_reading"]["median"]), PH["window_readings_max"],
           f1(PH["window_bytes_max_float32"] / 1000.0))])
    h2(doc, "4.6 Applicability")
    para(doc,
         "The station applies wherever a sonde or fixed analyser reports ammonium from an ion-selective "
         "electrode and laboratory samples are taken at it now and then: river and lake networks, stations "
         "upstream and downstream of sewage overflows and treatment works, raw-water intakes of treatment "
         "plants, and aquaculture. It helps most where the river returns to a low background between events, "
         "which is when the floor shows the offset (Section 8.12). The same arrangement applies to continuous "
         "water-quality stations on Indian rivers that report ammonium from electrodes and take grab samples "
         "for laboratory analysis.")

    # ============================================================== 5
    h1(doc, "5. Objective(s) of the Invention")
    para(doc,
         "The primary objective is a river ammonium monitoring station whose sonde controller applies, at "
         "every reading, the offset that its ammonium electrode actually carries, found from the floor of the "
         "electrode's own record anchored at laboratory samples, and whose sampler and intake interlock act on "
         "the corrected reading.")
    bullets(doc, [
        "(a) To follow offset changes of the ammonium electrode between laboratory samples, at services and "
        "by drift, from the electrode signal itself and without waiting for the next sample.",
        "(b) To separate the electrode offset from the river's own background ammonium by fixing the height "
        "of the floor above background at the laboratory samples.",
        "(c) To write the offset in force into the sonde controller so that the sonde reports the corrected "
        "ammonium on site.",
        "(d) To trigger the automatic sampler and the intake isolation interlock from two estimates of the "
        "offset, so that the watch tier misses fewer events and the confirmed tier acts falsely less often.",
        "(e) To evidence each effect against laboratory analysis of grab samples."])

    # ============================================================== 6
    h1(doc, "6. Working Principle of the Invention (in brief)")
    num(doc,
        "A sonde (100) placed in a river carries an ammonium ion-selective electrode (110) whose membrane "
        "potential, measured against a reference electrode, is digitised by a high-impedance analogue front "
        "end (116). The sonde controller (115) converts that potential to ammonium with a calibration line "
        "and a stored offset, logs a reading A(t) every 15 minutes and sends it through a cellular modem "
        "(117) over a telemetry link (130) to a record archive (200).")
    num(doc,
        "From time to time a grab sample (610) is drawn at the sonde and analysed in a laboratory (620). "
        "Its result L_j at time t_j is the true ammoniacal nitrogen at that instant and enters the same "
        "archive.")
    num(doc,
        "Whatever the electrode reports is the true concentration plus the offset it carries, A(t) = C(t) + "
        "o(t). A service, when the sonde is recalibrated or swapped, resets that offset; between services it "
        "drifts as the reference junction ages and the membrane conditions and fouls.")
    num(doc,
        "River ammonium behaves differently. It rises in pulses from overflows, discharges and runoff, and "
        "between pulses falls back towards a low background b that belongs to the river at that site. Over "
        "a window of several days a low quantile of the electrode readings, the floor F(t), therefore sits at "
        "b + o(t): the pulses lie above it, while the offset lifts or lowers the whole record with it.")
    num(doc,
        "The floor follows the offset without any reference measurement but cannot know b. At laboratory "
        "sample j the departure d_j = A(t_j) - L_j is the offset then in force, so F(t_j) - d_j is the height "
        "of the floor above the true background. Its median over the most recent earlier samples is the "
        "anchor gap g, and the offset in force at any later time is F(t) - g.")
    num(doc,
        "The station writes that offset into the sonde controller (115) over the link (130); the controller "
        "subtracts it from every reading it reports, so the ammonium leaving the sonde is A_c(t) = A(t) - (F(t) "
        "- g), not below zero, and the same values replace the provisional record in the archive (210).")
    num(doc,
        "A second estimate of the offset is kept beside it: the departure at the most recent laboratory "
        "sample. The two agree while the offset is steady; they part when the offset has moved since the "
        "sample, or when the river has stayed high for days and lifted the floor.")
    num(doc,
        "From the two corrected readings the output unit (400) forms a two-tier alarm. A watch alarm, raised "
        "when either exceeds the threshold for the river, closes a relay that starts the automatic sampler "
        "(440) so that a confirmation sample is taken during the event; a confirmed alarm, raised when both "
        "exceed it, operates the isolation interlock (450) of a downstream raw-water intake.")
    num(doc,
        "No step needs the maintenance logbook or the next sample. The floor is updated with every reading "
        "and the gap with every new laboratory result, and a service of the sonde needs no entry because the "
        "floor moves with the new offset.")
    h2(doc, "6.1 Claimed Function Against Example Implementation")
    table(doc, ["Claimed function", "Example implementation (Section 8)"], [
        ["Receive readings and laboratory results (claim 1 (a), (b)); pairing, claim 5",
         "Environment Agency sonde readings every 15 minutes; laboratory ammoniacal nitrogen; reading "
         "nearest the sampling time within %d minutes (median gap %s minutes)" % (meta["match_min"], f1(PH["lab_to_reading_gap_min"]["median"]))],
        ["Floor (claim 1 (c)); constants, claim 3",
         "%s percentile of the readings over the %g days before t, at least %d readings" % (ordinal(QP), DAYS, MINR)],
        ["Anchor gap (claim 1 (d)); constants, claim 3",
         "median of F(t_j) - d_j over the %d most recent earlier samples" % WIN],
        ["Correction written to the controller (claim 1 (e), (f))",
         "A_c = max(A - (F - g), 0) applied to every reading"],
        ["Two-tier alarm, sampler and intake interlock (claim 2)",
         "second estimate A - d_last; watch if either, confirmed if both exceed 0.6, 1 or 2 mg/L N"],
        ["No laboratory history yet, claim 4",
         "g from the low decile of laboratory results at the other sondes"],
    ], "Table 4: Claimed functional combination against the example implementation",
        widths=[2.3, 4.4], size=9, align_left_cols=(0, 1))
    h2(doc, "6.2 Technical Contribution")
    para(doc,
         "The contribution is a change in how the offset of an ammonium electrode is known and applied between "
         "laboratory samples: from a value frozen at the last sample to a value followed at every reading through "
         "the floor of the electrode's own record, with the laboratory samples fixing only the height of that floor "
         "above the river's background, and with the result written into the sonde controller and used to operate "
         "the sampler and the intake interlock. The effect is on the ammonium the instrument reports and on the "
         "physical actions taken on it, evidenced against laboratory analysis of grab samples, not against another "
         "computed record.")
    h2(doc, "6.3 Drawings")
    bullets(doc, [
        "Figure 1: architecture of the monitoring station: sonde, sampling and laboratory, telemetry, data "
        "processing, controller write-back, sampler and intake interlock.",
        "Figure 2: flowchart of the method with the hardware it exchanges signals with.",
        "Figure 3: mechanism: the floor follows the offset; gain with and without a service; by laboratory "
        "concentration; alarm tiers.",
        "Figure 4: accuracy at laboratory samples against current practice, ablation, sensitivity and per sonde.",
        "Figure 5: record, floor and errors at one sonde.",
        "Figure 6: first sample of each sonde and station-level uncertainty.",
        "Figure 7: claim tree."])
    figure(doc, "fig01.png", "Figure 1: Monitoring station with electrode-offset tracking, controller write-back and alarm actuation",
           "Readings of sonde 100 and laboratory results of grab samples 610 reach the archive (200) over link "
           "130; units 310-340 return the corrected record (410) and the offset in force (430) for controller "
           "115, and the output unit drives the automatic sampler (440) and the intake interlock (450).")
    figure(doc, "fig02.png", "Figure 2: Flowchart of the offset-tracking method with its hardware interfaces",
           "S1-S5 form the floor, the anchor gap and the corrected reading; S6 sets the alarm tier; S7 writes "
           "the record and the controller offset and switches the sampler and intake relays.", width=5.2)

    # ============================================================== 7
    h1(doc, "7. Description of the Invention in Detail")
    h2(doc, "7.1 Station Hardware")
    num(doc,
        "The ammonium electrode (110) of the sonde (100) is a membrane selective to ammonium in contact with "
        "the river, measured against a reference electrode whose porous junction lets a small flow of "
        "electrolyte reach the water. Its potential changes by close to the Nernstian slope per decade of "
        "ammonium (58.57 mV per decade reported for a recent electrode [N6]) and is read by the "
        "high-impedance analogue front end and analogue-to-digital converter (116) of the sonde.")
    num(doc,
        "Other sensors (112) of the same sonde report temperature, pH and conductivity, and a wiper (114) "
        "cleans the sensor faces. These are not needed by the method, which works on the ammonium channel "
        "alone, but they share the controller (115) and the reporting interval.")
    num(doc,
        "Every 15 minutes the controller converts the digitised potential to ammonium with its calibration "
        "line and stored offset and passes the reading over its serial sensor bus to the cellular modem (117), "
        "which sends it over the telemetry link (130). Across the %d sondes evaluated the median reporting "
        "interval is %s minutes." % (PH["sondes"], f1(PH["reading_interval_min"]["median"])))
    num(doc,
        "Grab samples (610) are taken at the sonde during routine and pollution sampling and analysed in a "
        "laboratory (620) for ammoniacal nitrogen. The automatic sampler (440) beside the sonde and the "
        "isolation interlock (450) of a downstream raw-water intake are each switched by a relay output of "
        "the output unit (400).")
    h2(doc, "7.2 Records (200)")
    num(doc,
        "The archive holds the readings A(t) (210) and the laboratory results (230). A result is paired with "
        "the reading nearest its sampling time within %d minutes; in the evaluation the median gap was %s "
        "minutes and the 90th percentile %s minutes. A result equal to the reading is a copy of the sonde value, "
        "not a laboratory analysis, and is discarded."
        % (meta["match_min"], f1(PH["lab_to_reading_gap_min"]["median"]), f1(PH["lab_to_reading_gap_min"]["p90"])))
    h2(doc, "7.3 Floor Unit (310)")
    num(doc,
        "For each time t the floor unit keeps the readings of the %g days ending at t in a sorted window and "
        "returns their %s percentile, provided the window holds at least %d readings. Inserting the new reading, "
        "dropping the one that left the window and reading the percentile take %s microseconds per reading on "
        "one processor core, and the window holds at most %d readings (about %s kB) per sonde."
        % (DAYS, ordinal(QP), MINR, f1(PH["processing_us_per_reading"]["median"]), PH["window_readings_max"],
           f1(PH["window_bytes_max_float32"] / 1000.0)))
    num(doc,
        "A window of several days is longer than most pollution pulses, so its low part is the background "
        "between them; a percentile rather than the minimum ignores single low spikes in the record. A failing electrode that reads far too high for days lifts the floor with it, so "
        "the correction removes the fault as an offset; this is why the mean error falls from %s to %s mg/L "
        "(Table 8)." % (f1(W["practice_best"]["mean"]), f1(W["method"]["mean"])))
    num(doc,
        "Between consecutive laboratory samples the change of the floor follows the change of the departure "
        "with a slope of %s, and the two move in the same direction %d times against %d (Figure 3(a)): the floor "
        "carries the offset, which is what the method needs."
        % (f2(FF["slope_departure_on_floor"]), FF["same_sign"], FF["opposite_sign"]))
    h2(doc, "7.4 Departure and Anchor Gap (320, 330)")
    num(doc,
        "At each earlier laboratory sample j the departure unit (320) forms d_j = A(t_j) - L_j, and the gap unit "
        "(330) forms F(t_j) - d_j, the height of the floor above the true concentration's background at that "
        "time. The anchor gap g is the median of this height over the %d most recent earlier samples, so that "
        "one doubtful sample does not move it; Table 11 shows that 6 or 20 samples give the same picture." % WIN)
    num(doc,
        "A sonde without a laboratory sample of its own takes g from the network: the median, over other sondes, "
        "of the low decile of their laboratory results, the background that sondes of the network typically see. "
        "At the first sample of each sonde this gives a median error of %s mg/L against %s for one network-wide "
        "correction value (Section 8.7)." % (f3(FS["method"]["median"]), f3(FS["net_const"]["median"])))
    h2(doc, "7.5 Controller Write-Back (340)")
    num(doc,
        "The correction unit (340) forms the offset in force F(t) - g and sends it over the link (130) to the "
        "controller (115), which stores it in place of the offset correction it holds and subtracts it from each "
        "reading it reports; the archive receives the same corrected values A_c(t) = max(A(t) - (F(t) - g), 0) "
        "for the corrected record (410). Against the best current correction chosen per sonde, the median "
        "error falls from %s to %s mg/L (Figure 4, Table 8)."
        % (f3(W["practice_best"]["median"]), f3(W["method"]["median"])))
    num(doc,
        "Most of this gain comes from drift within a service period. An offset taken from the last sample and "
        "allowed to change only at a service gives %s mg/L, the same as current practice; one limited to the "
        "drift the manufacturer reports [N7] gives %s mg/L. The floor follows faster drift than either, at a "
        "service and between services (Figure 3(b))."
        % (f3(HOLD["all"]["guarded"]["median"]), f3(VEND["all"]["guarded"]["median"])))
    h2(doc, "7.6 Two-Tier Alarm and Actuation (400, 420, 440, 450)")
    num(doc,
        "The output unit keeps two corrected readings: the floor-tracked A_c(t), and A(t) less the departure at "
        "the most recent laboratory sample. A watch alarm (420) is raised when either exceeds the threshold "
        "set for the river; its relay starts the automatic sampler (440), which fills a bottle for laboratory "
        "confirmation. A confirmed alarm, raised when both exceed the threshold, switches the relay of the "
        "isolation interlock (450) at the downstream intake.")
    num(doc,
        "The two tiers answer the weakness of a single estimate. When the river stays high for days the floor "
        "rises and the floor-tracked reading alone would miss an exceedance; the last-sample reading still sees "
        "it, so the watch tier misses %d exceedances at 1 mg/L N against %d for the per-sonde practice. When the "
        "offset has drifted upward, the last-sample reading alone would raise a false alarm; the floor-tracked "
        "reading removes it, so the confirmed tier acts falsely %d times against %d. Each tier pays for its "
        "gain on the other side: the watch tier raises %d false alarms against %d and the confirmed tier misses "
        "%d exceedances against %d, which is why the sampler, a reversible action, is put on the watch tier and "
        "the intake, whose closure interrupts supply, on the confirmed tier (Table 10, Figure 3(d))."
        % (A["1"]["watch"]["missed"], A["1"]["practice_best"]["missed"], A["1"]["confirmed"]["false_alarms"],
           A["1"]["practice_best"]["false_alarms"], A["1"]["watch"]["false_alarms"], A["1"]["practice_best"]["false_alarms"],
           A["1"]["confirmed"]["missed"], A["1"]["practice_best"]["missed"]))
    num(doc,
        "Both readings and the alarm state are available in the same 15-minute interval as the raw reading: "
        "the processing is a few microseconds per reading, so a relay command follows the reading that caused "
        "it without waiting for a later report.")
    figure(doc, "fig03.png", "Figure 3: How the floor follows the electrode offset and where the gain comes from",
           "(a) change of the floor against change of the departure between consecutive samples; (b) median "
           "error with and without a sonde service since the last sample; (c) by laboratory concentration; (d) "
           "false alarms (up) and missed exceedances (down) at three thresholds for the practice chosen per sonde "
           "and the two alarm tiers.")
    h2(doc, "7.7 Reference Numerals")
    table(doc, ["Numeral", "Element", "Numeral", "Element"], [
        ["100", "In-situ water-quality sonde", "300", "Offset tracking"],
        ["110", "Ammonium ion-selective electrode", "310", "Floor unit"],
        ["112", "Other sensors (temperature, pH, conductivity)", "320", "Departure unit"],
        ["114", "Wiper", "330", "Gap unit"],
        ["115", "Sonde controller", "340", "Correction unit"],
        ["116", "Analogue front end and converter", "400", "Output unit"],
        ["117", "Cellular modem", "410", "Corrected ammonium record"],
        ["118", "River water at the sonde", "420", "Pollution alarm (watch, confirmed)"],
        ["130", "Telemetry link", "430", "Offset in force"],
        ["200", "Record archive", "440", "Automatic sampler (relay-started)"],
        ["210", "Sonde readings", "450", "Intake isolation interlock (relay)"],
        ["230", "Laboratory results", "600", "Sampling and laboratory"],
        ["900", "Data-processing system", "610, 620", "Grab sample; laboratory analysis"],
    ], "Table 5: Reference numerals", widths=[0.9, 2.45, 0.9, 2.45], size=9, align_left_cols=(1, 3))

    # ============================================================== 8
    h1(doc, "8. Experimental Validation Results")
    h2(doc, "8.1 Data and Configuration")
    para(doc,
         "All inputs are public records of the Environment Agency of England under the Open Government "
         "Licence, read without registration: the raw 15-minute sonde readings (quality 'Unchecked') of "
         "the Hydrology service, and the laboratory results (ammoniacal nitrogen as N) of the Water "
         "Quality Archive. Of %d sondes that reported ammonium, those that ran for at least 180 days, "
         "also reported conductivity and had a sampling point within 300 m with at least 8 laboratory "
         "results during the deployment were kept: %d sondes, of which %d had matched samples with a "
         "full floor window (%d samples, %s to %s, %s readings). Table 6 lists the constants, read from "
         "the code that used them; they were fixed before the comparisons with the practice baselines, "
         "the station halves and the sensitivity runs, and were not changed for them."
         % (n_amm, len(sites), meta["sites"], meta["samples"], meta["period"][0], meta["period"][1],
            "{:,}".format(meta["readings"])))
    table(doc, ["Parameter", "Value", "Role"], [
        ["Floor window", "%g days, >= %d readings" % (DAYS, MINR), "floor F(t)"],
        ["Floor quantile", "%s percentile" % ordinal(QP), "floor F(t)"],
        ["Anchor samples", "%d most recent earlier samples, median" % WIN, "anchor gap g"],
        ["Pairing", "nearest reading within %d minutes" % meta["match_min"], "departure d_j"],
        ["Alarm thresholds", "0.6, 1 and 2 mg/L N", "alarm test"],
    ], "Table 6: Configuration parameters", widths=[2.1, 2.3, 2.3], size=9, align_left_cols=(0, 2))
    h2(doc, "8.2 Tests")
    table(doc, ["Test", "Question", "Ground truth"], [
        ["V1", "Is the reading at each laboratory sample closer to the laboratory result after the "
               "correction than after the current corrections (median, last and trend of earlier "
               "departures, and the one of these that served the sonde best)?", "Laboratory result"],
        ["V2", "Ablation: floor without the laboratory anchor", "As V1"],
        ["V3", "Does the floor move with the offset between consecutive samples?", "Change of departure"],
        ["V4", "Gain with and without a sonde service; by concentration", "As V1"],
        ["V5", "Alarms at fixed thresholds", "Laboratory result above the threshold"],
        ["V6", "First sample of each sonde (no history)", "As V1"],
        ["V7", "Station resampling, two halves of the sondes, changed constants", "As V1"],
    ], "Table 7: Validation tests", widths=[0.5, 4.2, 2.0], size=9, align_left_cols=(1, 2))
    h2(doc, "8.3 Accuracy at Laboratory Samples (V1, V2)")
    para(doc,
         "Each sample with at least one earlier sample at its sonde is corrected from the readings up to "
         "its own time and the laboratory results before it, so its own result never enters its "
         "correction. Table 8 gives the absolute error against the laboratory result.")
    rowsT = [("Raw reading", "raw"), ("Median of earlier departures", "median"), ("Last departure", "last"),
             ("Trend of earlier departures in time", "trend"), ("Practice chosen per sonde from its earlier samples", "practice_best"),
             ("Floor without anchor (ablation)", "floor_net"), ("Floor anchored at samples (claim 1)", "method")]
    hold_row = ["Offset from the last sample, held between services, free at services (ablation)",
                mmt(HOLD["all"]["guarded"]), bz(flip(HOLD["guarded_vs_method"]))]
    vend_row = ["As above, drifting at most 0.31 mg/L per 73 days [N7] (ablation)",
                mmt(VEND["all"]["guarded"]), bz(flip(VEND["guarded_vs_method"]))]
    trows = [[lab, mmt(W[k]), "-" if k == "method" else bz(P[k])] for lab, k in rowsT]
    table(doc, ["Correction", "Median / p90 / trimmed mean (mg/L N)", "Method better at"],
          trows[:-1] + [hold_row, vend_row] + trows[-1:],
        "Table 8: Absolute error at %d laboratory samples of %d sondes" % (meta["samples_with_prior"], m["sites_with_prior"]),
        widths=[2.6, 2.3, 1.8], size=9, align_left_cols=(0,))
    para(doc,
         "The trimmed mean leaves out the largest 1 %% of errors, which come from gross electrode faults; "
         "with them, the mean error is %s mg/L for the practice chosen per sonde and %s mg/L for the "
         "method. Against that practice the method is better at %d of %d sondes. Resampling whole "
         "sondes (2000 draws), the median error falls by %s against the practice chosen per sonde and by "
         "%s against the last departure; the 90th percentile falls by %s, an interval that includes zero."
         % (f1(W["practice_best"]["mean"]), f1(W["method"]["mean"]), m["sites_better"]["practice_best"],
            m["sites_with_prior"], ci(m["bootstrap_vs_practice_best"]["median"]),
            ci(m["bootstrap_vs_last"]["median"]), ci(m["bootstrap_vs_practice_best"]["p90"])))
    figure(doc, "fig04.png", "Figure 4: Accuracy at laboratory samples",
           "(a) cumulative error, raw, current practice and this method; (b) practice baselines and "
           "ablation; (c) sensitivity of window, quantile and anchor samples; (d) mean error per sonde.")
    h2(doc, "8.4 Mechanism (V3, V4)")
    para(doc,
         "Between consecutive samples at a sonde the change of departure follows the change of floor "
         "with a slope of %s (1 expected if the floor carries the whole offset), and the two move in the "
         "same direction %d times and in opposite directions %d times (%d pairs, largest 1 %% of "
         "departure changes left out of the slope). Where the sonde was serviced between the last sample "
         "and the one corrected, the median error falls from %s to %s mg/L, better at %s; elsewhere from "
         "%s to %s mg/L, better at %s: the floor follows offset changes at services and between them."
         % (f2(FF["slope_departure_on_floor"]), FF["same_sign"], FF["opposite_sign"], FF["n"],
            f3(SV["serviced_since_last_lab"]["median"]["median"]), f3(SV["serviced_since_last_lab"]["method"]["median"]),
            bz(SV["serviced_since_last_lab"]["paired"]), f3(SV["not_serviced"]["median"]["median"]),
            f3(SV["not_serviced"]["method"]["median"]), bz(SV["not_serviced"]["paired"])))
    para(doc,
         "Most of the gain comes from drift within a service period. If the offset is taken from the last "
         "sample and allowed to change only at a service (a gap of more than 6 hours in the record), the "
         "median error is %s mg/L, the same as current practice; if it may also drift, but no faster than "
         "the 0.31 mg/L that the manufacturer reports for its electrode over a 73-day trial [N7], it is %s mg/L "
         "(Table 8). The floor follows drift that is faster than that figure, which a correction value "
         "kept until the next sample cannot."
         % (f3(HOLD["all"]["guarded"]["median"]), f3(VEND["all"]["guarded"]["median"])))
    table(doc, ["Laboratory band (mg/L N)", "Samples", "Practice median error", "Method median error", "Method better at",
                "Under-read: practice / method"], [
        [k.replace("-1e+09", " and above"), str(v["median"]["n"]), f3(v["median"]["median"]), f3(v["method"]["median"]),
         bz(v["paired"]), "%d / %d" % (v["under_read_median"], v["under_read_method"])] for k, v in LB.items()],
        "Table 9: By laboratory concentration (practice = median of earlier departures)",
        widths=[1.2, 0.7, 1.0, 1.0, 1.6, 1.2], size=9, align_left_cols=())
    para(doc,
         "The gain lies at low and moderate concentrations, where the offset dominates the error; above 1 "
         "mg/L N the method and practice are level and the method under-reads no more often, so a "
         "pollution event is not taken for an offset.")
    h2(doc, "8.5 Alarms (V5)")
    para(doc,
         "The corrected reading alone raises fewer false alarms than every practice baseline at 0.6 and 1 "
         "mg/L, but at 2 mg/L it misses more exceedances (%d against %d), because those concentrations lie "
         "in the band in which the method has no accuracy gain and a long episode lifts the floor. The "
         "system therefore keeps two estimates of the offset in force: the floor-tracked one and the "
         "departure at the last laboratory sample. They differ when the offset has moved since the sample "
         "or when the river has risen for days. A watch alarm is raised when either corrected reading "
         "exceeds the threshold and a confirmed alarm when both do (claim 2; Table 10, Figure 3(d))."
         % (A["2"]["method"]["missed"], A["2"]["practice_best"]["missed"]))
    table(doc, ["Threshold (mg/L N)", "Exceedances in laboratory", "Raw: false / missed",
                "Practice chosen per sonde: false / missed", "Corrected reading: false / missed",
                "Watch tier: false / missed", "Confirmed tier: false / missed"], [
        [t, str(A[t]["lab_exceed"]), "%d / %d" % (A[t]["raw"]["false_alarms"], A[t]["raw"]["missed"]),
         "%d / %d" % (A[t]["practice_best"]["false_alarms"], A[t]["practice_best"]["missed"]),
         "%d / %d" % (A[t]["method"]["false_alarms"], A[t]["method"]["missed"]),
         "%d / %d" % (A[t]["watch"]["false_alarms"], A[t]["watch"]["missed"]),
         "%d / %d" % (A[t]["confirmed"]["false_alarms"], A[t]["confirmed"]["missed"])] for t in A],
        "Table 10: Alarm decisions at %d samples" % (A["1"]["lab_exceed"] + A["1"]["lab_below"]),
        widths=[0.8, 0.9, 0.9, 1.1, 1.0, 1.0, 1.0], size=8.5, align_left_cols=())
    para(doc,
         "The watch tier misses fewer exceedances than the median, last-departure and per-sonde practice at "
         "every threshold (%s at 0.6, 1 and 2 mg/L, against %s for the practice chosen per sonde), in exchange "
         "for more false alarms; only the trend correction misses fewer at 2 mg/L (%d), with %d false alarms "
         "against the watch tier's %d; the confirmed tier raises fewer false alarms than every practice baseline at every "
         "threshold (%s against %s), in exchange for more misses. A single correction value offers one "
         "decision only."
         % (", ".join(str(A[t]["watch"]["missed"]) for t in A), ", ".join(str(A[t]["practice_best"]["missed"]) for t in A),
            A["2"]["trend"]["missed"], A["2"]["trend"]["false_alarms"], A["2"]["watch"]["false_alarms"],
            ", ".join(str(A[t]["confirmed"]["false_alarms"]) for t in A), ", ".join(str(A[t]["practice_best"]["false_alarms"]) for t in A)))
    h2(doc, "8.6 One Sonde")
    para(doc,
         "Figure 5 shows sonde %s from %s to %s: the raw record moves up and down with services while the "
         "laboratory results stay low, and the floor follows those moves. Over the %d samples shown the "
         "median error is %s mg/L with the practice chosen per sonde and %s mg/L with the method."
         % (ex["station"], ex["from"], ex["to"], ex["n_samples_shown"], f3(ex["median_practice_best"]),
            f3(ex["median_method"])))
    figure(doc, "fig05.png", "Figure 5: Record, floor and errors at one sonde",
           "(a) raw readings, 7-day floor and laboratory results; (b) error at each laboratory sample, "
           "using only earlier samples.")
    h2(doc, "8.7 Sonde without Laboratory History (V6)")
    para(doc,
         "At the first laboratory sample of each sonde, with no earlier sample, the gap is taken from the "
         "other sondes (claim 4): median error %s mg/L, against %s for one network-wide correction value "
         "(mean departure of the other sondes) and %s for the raw reading; better than the network value "
         "at %s. Over all samples treated in the same way, the floor with the network background is "
         "better than the network value at %s, with a median error of %s against %s."
         % (f3(FS["method"]["median"]), f3(FS["net_const"]["median"]), f3(FS["raw"]["median"]),
            bz(FSP["net_const"]), bz(m["cold_start_paired"]["net_const"]),
            f3(m["cold_start"]["floor_net"]["median"]), f3(m["cold_start"]["net_const"]["median"])))
    figure(doc, "fig06.png", "Figure 6: First sample of each sonde and station-level uncertainty",
           "(a) median error at the first laboratory sample of each sonde; (b) reduction of the median "
           "error with 95 % intervals from resampling whole sondes.")
    h2(doc, "8.8 Station Halves and Changed Constants (V7)")
    para(doc,
         "With every constant frozen, the sondes were sorted by identifier and dealt alternately into two "
         "halves. On the first (%d sondes) the method is better than the practice chosen per sonde at %s; "
         "on the second (%d sondes) at %s. Changing one constant at a time (Table 11), the method's median "
         "error stays between %s and %s mg/L and it is better than the practice chosen per sonde in every "
         "run (z from %s to %s)."
         % (HV["first"]["sites"], bz(HV["first"]["paired_best"]), HV["second"]["sites"], bz(HV["second"]["paired_best"]),
            f3(s_lo), f3(s_hi), f2(zb_lo), f2(zb_hi)))
    table(doc, ["Window (days)", "Quantile", "Anchor samples", "Samples", "Practice chosen per sonde", "Method", "Method better at"], [
        ["%g" % s["floor_days"], ordinal(100 * s["floor_q"]), str(s["window"]), str(s["n"]),
         f3(s["practice_best"]["median"]), f3(s["method"]["median"]), bz(s["paired_best"])] for s in sens],
        "Table 11: Sensitivity of the constants (median absolute error, mg/L N)",
        widths=[0.8, 0.7, 0.8, 0.7, 1.2, 0.8, 1.7], size=9, align_left_cols=())
    para(doc,
         "A window of 3 days keeps fewer samples because some sondes log hourly and do not reach %d "
         "readings in 3 days." % MINR)
    h2(doc, "8.9 Timing, Memory and Pairing at the Station")
    para(doc,
         "Run as it would at a station, inserting each new reading into a sorted %g-day window, dropping the "
         "oldest and reading the percentile, the floor takes %s microseconds per reading on one processor core "
         "(largest sonde %s microseconds), about %s parts in a billion of the 15-minute reporting interval, and holds at most "
         "%d readings, about %s kB, per sonde. The median reporting interval of the %d sondes is %s minutes. "
         "Laboratory samples were paired with readings a median of %s minutes away (90th percentile %s, "
         "largest %s minutes). The whole evaluation of 10 sondes, all samples and baselines, takes %s s."
         % (DAYS, f1(PH["processing_us_per_reading"]["median"]), f1(PH["processing_us_per_reading"]["max"]),
            "%.0f" % (1e9 * PH["share_of_15min_interval"]), PH["window_readings_max"], f1(PH["window_bytes_max_float32"] / 1000.0),
            PH["sondes"], f1(PH["reading_interval_min"]["median"]), f1(PH["lab_to_reading_gap_min"]["median"]),
            f1(PH["lab_to_reading_gap_min"]["p90"]), f1(PH["lab_to_reading_gap_min"]["max"]),
            f2(m["timing_s_per_10_sites"] + 0.005)))
    h2(doc, "8.10 Technical Effect Summary")
    table(doc, ["Effect", "Mechanism", "Evidence"], [
        ["Lower error of the ammonium record between samples", "Floor follows the offset; gap fixed at samples",
         "Table 8: median %s -> %s mg/L; %s" % (f3(W["practice_best"]["median"]), f3(W["method"]["median"]), bz(P["practice_best"]))],
        ["Effect holds across sondes", "Same constants on every sonde",
         "%d of %d sondes; bootstrap %s" % (m["sites_better"]["practice_best"], m["sites_with_prior"], ci(m["bootstrap_vs_practice_best"]["median"]))],
        ["Gross faults removed", "Fault lifts the floor with the reading",
         "mean error %s -> %s mg/L" % (f1(W["practice_best"]["mean"]), f1(W["method"]["mean"]))],
        ["Two-tier alarm", "Floor-tracked and last-sample offsets; either / both",
         "Table 10, 1 mg/L: watch %d missed (practice %d); confirmed %d false (practice %d)"
         % (A["1"]["watch"]["missed"], A["1"]["practice_best"]["missed"], A["1"]["confirmed"]["false_alarms"],
            A["1"]["practice_best"]["false_alarms"])],
        ["Drift within a service followed", "Floor, not a held value",
         "held between services %s, drift-capped %s, floor %s mg/L" % (f3(HOLD["all"]["guarded"]["median"]),
                                                                   f3(VEND["all"]["guarded"]["median"]), f3(W["method"]["median"]))],
        ["Offset followed between samples", "Low quantile over days",
         "slope %s; same direction %d of %d" % (f2(FF["slope_departure_on_floor"]), FF["same_sign"], FF["same_sign"] + FF["opposite_sign"])],
    ], "Table 12: Technical effects, mechanism and evidence", widths=[2.0, 2.0, 2.7], size=9, align_left_cols=(0, 1, 2))
    h2(doc, "8.11 Insights")
    bullets(doc, [
        "Most of the ammonium error of these sondes is an offset that moves, not noise: the raw median "
        "error is %s mg/L and a correction from laboratory samples removes most of it." % f3(W["raw"]["median"]),
        "On its own the floor cannot place the river's background; the laboratory samples alone cannot follow "
        "the offset between them. Together they beat each.",
        "Within a service period the electrode offset moves faster than the drift its manufacturer reports "
        "for a 73-day trial would allow, to judge from Table 8; holding the offset between services gives no "
        "gain over current practice.",
        "The gain is in the typical error; the largest errors (90th percentile) are not reduced with "
        "certainty. Two estimates of the offset give a choice of alarm tier that one correction value "
        "cannot."])
    h2(doc, "8.12 Limitations and Acceptance Criteria")
    bullets(doc, [
        "Above 1 mg/L N the method has no accuracy gain, and the corrected reading alone misses more "
        "exceedances at 2 mg/L than current practice; the watch tier removes that deficit in exchange for "
        "more false alarms (Table 10). Acceptance: at each new network the watch tier must miss no more "
        "exceedances at the alarm threshold in use than the current practice.",
        "Where ammonium stays high for longer than the floor window (a long discharge, a drying river), "
        "the floor rises with the river; the last-sample estimate in the watch tier keeps such an episode "
        "visible, but the corrected record under-reads it. Limiting how fast the offset may move between "
        "services prevents this but removes most of the gain (Section 8.4).",
        "Evaluated on sondes of one agency in England; the laboratory samples are routine and pollution "
        "samples taken near the sonde, not always at the same minute. Acceptance: on each new network, "
        "V1 must show a lower median error than the current practice chosen per sonde.",
        "The 90th percentile of the error is not reduced with certainty (interval includes zero)."])

    # ============================================================== 9
    h1(doc, "9. Discussion")
    para(doc,
         "The invention turns the shape of the sonde's own record into a measurement of the electrode "
         "offset. Two facts make this possible: a river's ammonium falls back to a background between "
         "pulses, so the floor of a few days of readings is that background plus the offset; and at a "
         "laboratory sample the true concentration is known, so the height of the floor above background "
         "can be fixed there rather than assumed. The offset is then followed at every reading, through "
         "services and drift, without the maintenance logbook and without waiting for the next sample. "
         "The results show the gain against every current correction, at most sondes and in both halves, "
         "and show that it comes from drift within service periods that a held correction value cannot "
         "follow. Keeping the last-sample estimate beside the floor-tracked one turns the remaining "
         "weakness, long episodes at high concentration, into a choice of alarm tier.")

    # ============================================================== 10
    h1(doc, "10. What Aspect(s) of the Invention Need(s) Protection?")
    bullets(doc, [
        "River ammonium monitoring station whose sonde controller follows the electrode offset through a low "
        "quantile of the electrode's own readings over several days.",
        "Height of that floor above the river's background fixed at laboratory samples from the departure of the "
        "reading at each sample.",
        "Offset in force, floor less that height, written to the sonde controller and subtracted from every reading "
        "in real time.",
        "Two-tier alarm from the floor-tracked and last-sample offsets, starting an automatic sampler and "
        "operating an intake isolation interlock by relay.",
        "Height taken from other sondes of the network before a sonde has laboratory samples of its own."])
    figure(doc, "fig07.png", "Figure 7: Claim tree",
           "Independent method claim 1, its dependents 2 (two-tier alarm, sampler and intake relays), 3 (constants), 4 (no laboratory history) "
           "and 5 (pairing), and system claim 6 carrying out the method.")
    h2(doc, "Claims")
    CLAIMS(doc, DAYS, QP, MINR, WIN, meta["match_min"])

    # ============================================================== 11
    h1(doc, "11. Technology Readiness Level of the Invention")
    para(doc,
         "The method runs end to end on the public records of operating sondes and is scored against laboratory "
         "analysis of grab samples; the controller write-back and the sampler and intake relays have not yet been "
         "connected at a station.")
    trl_table(doc)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    B._run(p, "END OF THE DOCUMENT", size=11, bold=True)
    p.alignment = 1
    return doc, num


def lab_median(m):
    rows = load("ev_rows.json")
    v = sorted(r["lab"] for r in rows if r["i"] >= 1)
    return v[len(v) // 2]


def CLAIMS(doc, DAYS, QP, MINR, WIN, MATCH):
    sonde = ("an in-situ water-quality sonde (100) placed in a river and comprising an ammonium "
             "ion-selective electrode (110) and a sonde controller (115) that converts the potential of the "
             "electrode to an ammonium concentration with a stored calibration offset and reports a reading "
             "at successive intervals")
    claim(doc, 1,
          "A method of correcting the ammonium record of " + sonde + ", the sonde transmitting the readings "
          "over a telemetry link (130) to a record archive (200), the method being carried out by a "
          "data-processing system (900) and comprising: "
          "(a) receiving over the link (130) the readings A(t) of the sonde at the successive intervals; "
          "(b) receiving laboratory results L_j of the ammonium concentration of grab samples (610) taken at "
          "the sonde at sampling times t_j, and pairing each with the reading of the sonde at that time; "
          "(c) computing, for each time t, a floor F(t) as a low quantile of the readings over a window of "
          "several days ending at t, the window being longer than a pollution pulse in the river so that the "
          "floor follows the river's background ammonium plus the offset carried by the electrode; "
          "(d) computing an anchor gap g from laboratory results taken before t, as a combination over "
          "those samples of F(t_j) less the departure A(t_j) - L_j, being the height of the floor above "
          "the background; "
          "(e) computing a corrected reading A_c(t) as A(t) less the offset in force F(t) - g, and not less "
          "than zero; and "
          "(f) replacing in the record archive (200) the readings with the corrected readings, and "
          "transmitting the offset in force over the link (130) to the sonde controller (115), which "
          "applies it to the readings it reports.", independent=True)
    claim(doc, 2,
          "The method of claim 1, further comprising computing a second corrected reading as A(t) less the "
          "departure A(t_j) - L_j at the most recent laboratory sample taken before t; raising a watch "
          "pollution alarm (420) when either corrected reading exceeds an alarm threshold set for the river and "
          "closing a relay that starts an automatic sampler (440) at the sonde; and raising a confirmed "
          "pollution alarm when both exceed it and switching a relay of an isolation interlock (450) of a "
          "raw-water intake downstream of the sonde.")
    claim(doc, 3,
          "The method of claim 1 or claim 2, wherein the window spans the %g days ending at t and holds at "
          "least %d readings, the low quantile is the %s percentile, and the anchor gap is the median of "
          "F(t_j) - (A(t_j) - L_j) over the %d most recent laboratory samples taken before t."
          % (DAYS, MINR, ordinal(QP), WIN))
    claim(doc, 4,
          "The method of any of claims 1 to 3, wherein, before a first laboratory sample has been taken at "
          "the sonde, the anchor gap is the median, over other sondes of a monitoring network, of a low "
          "quantile of their laboratory results.")
    claim(doc, 5,
          "The method of any of claims 1 to 4, wherein each laboratory result is paired with the reading "
          "nearest its sampling time within %d minutes, and a result equal to the paired reading is "
          "discarded as a copy of the sonde value." % MATCH)
    claim(doc, 6,
          "A system for correcting the ammonium record of an in-situ river water-quality sonde, comprising: "
          + sonde + "; a telemetry link (130); a record archive (200) receiving over the link the readings of "
          "the sonde and laboratory results of grab samples taken at the sonde; an automatic sampler (440) and an "
          "intake isolation interlock (450), each switched by a relay; and a data-processing system (900) "
          "comprising a floor unit (310), a departure unit (320), a gap unit (330), a correction unit (340) and an "
          "output unit (400) driving the relays, configured to carry out the method of any one of claims 1 to 5.",
          independent=True)


def check(path, num):
    d = Document(path)
    paras = [p.text for p in d.paragraphs]
    tables = [[c.text for row in t.rows for c in row.cells] for t in d.tables]
    body = "\n".join(paras)
    prior = [c for cells in tables if cells[:1] == ["S.No."] and "Comments" in cells[:4] for c in cells]
    other = [c for cells in tables for c in cells if c not in prior]
    own = body + "\n" + "\n".join(other)
    everything = own + "\n" + "\n".join(prior)
    bad = [w for w in FORBIDDEN if re.search(w, everything, re.I)]
    ban = [w for w in BANNED if re.search(w, own, re.I)]
    ph = PLACEHOLDER.findall(everything)
    open_ = [p[:40] for p in paras if OPENERS.match(p)]
    phys = sum(1 for t in num.texts if PHYSICAL.search(t))
    share = phys / len(num.texts)
    refs = set(re.findall(r"Table (\d+)", everything))
    caps = set(re.findall(r"^Table (\d+):", "\n".join(paras), re.M))
    figs = set(re.findall(r"Figure (\d+)", everything))
    problems = []
    if bad:
        problems.append("business vocabulary %s" % bad)
    if ban:
        problems.append("banned phrases %s" % ban)
    if ph:
        problems.append("placeholders %s" % ph)
    if open_:
        problems.append("banned paragraph openers %s" % open_)
    if share <= 0.6:
        problems.append("physical tie-in only %.0f %%" % (100 * share))
    if refs - caps:
        problems.append("tables referenced without caption %s" % sorted(refs - caps))
    if problems:
        raise SystemExit("refused: " + "; ".join(problems))
    print("checked: %d numbered paragraphs, %.0f %% name a physical element; tables %s; figures %s; %d words"
          % (len(num.texts), 100 * share, sorted(caps, key=int), sorted(figs, key=int), len(everything.split())))


if __name__ == "__main__":
    doc, num = build()
    for p in doc.paragraphs:          # keep each figure on the page of its caption
        if p._p.xpath(".//w:drawing"):
            p.paragraph_format.keep_with_next = True
    doc.save(OUT)
    print("wrote", OUT)
    check(OUT, num)
