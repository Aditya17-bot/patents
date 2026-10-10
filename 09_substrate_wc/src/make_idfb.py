"""Build the IDF-B disclosure for drain-onset recalibration of substrate water-content sensors.

Layout: the accepted VIT IDF-B (masthead, eleven numbered sections), through the layout helpers of the
CausalInterlock generator and the table/figure/claim helpers of the patent 05 generator, imported
unchanged, as in patent 06.

Every measured number is read from results/*.json at build time and the operating constants are read
from the code that used them. The build refuses to run if a results file is missing or if a comparison
stated in words no longer holds. After writing, it scans the document for placeholders, business-method
vocabulary and banned phrases, and checks that more than 60 % of the numbered paragraphs name a
physical element.
"""
import importlib.util
import json
import os
import re
import sys

from docx import Document
from docx.shared import Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
SRC = os.path.join(ROOT, "src")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sys.path.insert(0, r"C:\adi\patents\01_02_infosec\IDF-B_CausalInterlock")
import build_idfb as B                                            # noqa: E402

P5 = _load_module("p05_make_idfb", r"C:\adi\patents\05_length_invariance\src\make_idfb.py")
sys.path.insert(0, SRC)
import rolling_anchor as RA                                       # noqa: E402

B.FIG = os.path.join(ROOT, "patent", "figures")
OUT = os.path.join(ROOT, "patent", "IDF-B_Substrate_WC_Drain_Onset_Recalibration.docx")
h1, h2, para, bullets = B.h1, B.h2, B.para, B.bullets
table, figure, claim, Numbering, trl_table = P5.table, P5.figure, P5.claim, P5.Numbering, P5.trl_table

FORBIDDEN = P5.FORBIDDEN + ["cost", "profit", "price"]
BANNED = P5.BANNED
OPENERS, PLACEHOLDER = P5.OPENERS, P5.PLACEHOLDER
PHYSICAL = re.compile(r"sensor|slab|valve|pump|dripper|meter|gutter|electrode|pin|substrate|"
                      r"greenhouse|irrigation section|controller \(900\)|system \(900\)|link \(130\)", re.I)

# operating constants, read from the code that used them
W_DAYS, MIN_DAYS = RA.W, RA.MIN_DAYS
THR = 0.3            # offset_anchor.daily_plateau default (thr_frac)
N_FIRST = 4          # first pulses of the day, offset_anchor.daily_plateau (early = g.rise.iloc[:4])
PLAT_MIN = 30        # minutes after drain onset, offset_anchor.daily_plateau
RISE_WIN = 3         # sampling intervals, pulse_gain.pulse_rises (wc.iloc[i:i + 3])
GATE = 0.10          # scale_offset / dryback agreement gate
SETBACK = 5          # control_replay: S = P* - 5
WINS = (7, 14, 28)   # windows of the sensitivity test, experiments.E1
THRS = (0.2, 0.3, 0.4)  # onset fractions of the sensitivity test, experiments.E1


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


def pc(x, nd=0):
    return ("%." + str(nd) + "f") % (100.0 * x)


TEAMS = ["Reference", "AICU", "Automatoes", "Digilog", "IUACAAS", "TheAutomators"]
LABEL = {"Reference": "Reference (growers)", "AICU": "AICU", "Automatoes": "Automatoes",
         "Digilog": "Digilog", "IUACAAS": "IUA.CAAS", "TheAutomators": "The Automators"}


def build():
    dc = load("data_check.json")
    ra = load("rolling_anchor.json")
    oa = load("offset_anchor.json")
    ex = load("experiments.json")
    cr = load("control_replay.json")
    so = load("scale_offset.json")
    db = load("dryback.json")
    dr = load("dripper_ratio.json")
    pg = load("pulse_gain.json")
    f3 = load("fig03_example.json")
    ub = load("uptake_balance.json")
    e6 = load("e6_commissioning.json")
    e7 = load("e7_delivery.json")
    e8 = load("e8_drain_cup.json")
    e9 = load("e9_dripper_fault.json")
    e10 = load("e10_litres_to_drain.json")
    e11 = load("e11_p2_anchor.json")
    p2l, onl = e11["level"]["p2"], e11["level"]["onset"]
    if not (onl["pooled_median_abs"] < p2l["pooled_median_abs"] and onl["sensors_within_1"] > p2l["sensors_within_1"]
            and e11["litres_onset_minus_p2_ci95"][0] > 0):
        raise SystemExit("e11 no longer supports the wording of Sections 4.2 and 8.8")
    lp = e10["pooled"]
    if not (lp["roll"] > lp["comm"] > lp["raw"] and e10["boot_roll_minus_raw_ci95"][0] > 0
            and e10["boot_roll_minus_comm_ci95"][0] > 0):
        raise SystemExit("e10 no longer supports the wording of Section 8.8")
    inj = e9["by_limit"]["0.3"]
    if inj["no_fault"]["with_alarm"] != 0 or not inj["0.5"]["rate"] > inj["0.6"]["rate"] > inj["0.7"]["rate"]:
        raise SystemExit("e9 no longer supports the wording of Section 8.6")
    lv = e8["level_at_cup_onset"]
    lc = e8["label_check"]
    lc_zero = max(v["after_pulse_metered_drain_zero"] for v in lc.values())
    lc_pulse = [v["after_pulse"] for v in lc.values()]
    P_STAR = ra["P_star"]
    med = ra["median_over_compartments"]
    e2 = ex["E2_daily_sign"]
    grid = ex["E1_sensitivity"]
    gmin, gmax = min(g["gap_median"] for g in grid), max(g["gap_median"] for g in grid)
    if {g["W"] for g in grid} != set(WINS) or {g["thr"] for g in grid} != set(THRS):
        raise SystemExit("claim 3 ranges no longer match the sensitivity test")
    mm = cr["median_over_sensors"]
    n_bad = cr["sensors_with_mismatch_over_20pct"]
    sens = cr["sensors"]
    worst = max(sens, key=lambda k: sens[k]["mismatch"])
    dbm = db["median_over_compartments"]
    agree = [t for t in TEAMS if so[t]["routes_agree"]]
    cov = ex["E3_coverage"]
    covs = [cov[t][s]["coverage"] for t in TEAMS for s in ("1", "2")]
    e5 = ex["E5_whole_season"]
    tm = ex["E4_timing"]
    raw_max_t = max(TEAMS, key=lambda t: ra["teams"][t]["raw"])
    gaps_raw_sorted = sorted(ra["teams"][t]["raw"] for t in TEAMS)
    agreed_pair = [t for t in TEAMS if ra["teams"][t]["raw"] < 1.5]
    uc = [ub["%s_%d" % (t, s)]["corr_D_R"] for t in TEAMS for s in (1, 2)]

    claims_in_words = {
        "rolling better than raw in every compartment that disagreed":
            all(ra["teams"][t]["rolling"] < ra["teams"][t]["raw"] for t in TEAMS if t not in agreed_pair),
        "rolling no worse than raw where the pair already agreed":
            all(ra["teams"][t]["rolling"] <= ra["teams"][t]["raw"] + 0.05 for t in agreed_pair),
        "rolling median below fixed median": med["rolling"] < med["fixed"] < med["raw"],
        "every sensitivity setting far below raw": gmax < ex["E1_raw_gap_median"] / 3,
        "pooled daily sign test significant": e2["pooled"]["z"] > 3,
        "gated gain no worse than raw on dry-back, ungated worse":
            dbm["gap_scale_gated"] < dbm["gap_raw"] < dbm["gap_scale_ungated"],
        "most sensors make wrong valve decisions >20 %": n_bad >= 6,
        "rolling below one-off commissioning anchor in the median and in most compartments":
            e6["median_rolling"] < e6["median_commissioning"] and e6["rolling_lower_in"] >= 4,
        "drain-probe check: rolling anchor nearest the physical drain, most sensors within 1 WC %":
            lv["roll"]["pooled_median_abs"] < lv["comm"]["pooled_median_abs"]
            and lv["roll"]["pooled_median_abs"] < lv["raw"]["pooled_median_abs"]
            and lv["roll"]["sensors_within_1"] >= 9 and lv["raw"]["sensors_within_1"] <= 1,
        "drain-probe label quiet when no drain": lc_zero <= 0.07,
        "pulse log matches irrigation meter within 1 %":
            dc["pulse_over_meter_range"][0] >= 0.99 and dc["pulse_over_meter_range"][1] <= 1.011,
    }
    wrong = [k for k, ok in claims_in_words.items() if not ok]
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
         "The present invention relates to the irrigation of crops grown in soilless culture, in which plants "
         "stand on slabs of a plant-growth substrate such as stone wool, an irrigation valve or pump doses "
         "nutrient solution to the slabs through drippers in short pulses, and dielectric water-content "
         "sensors inserted in the slabs report the water content that the irrigation controller steers on. "
         "More particularly, it pertains to a system and method that recalibrate each water-content sensor "
         "in place, from the moment its own slab starts to drain under the routine irrigation pulses, express "
         "each reading as the deficit of water content still missing before that slab drains, and open or "
         "hold the irrigation valve on that deficit.")
    para(doc,
         "Growers of tomato, cucumber, pepper and strawberry on stone wool steer irrigation by the water "
         "content (WC) of the slab: the first pulse of the day is given when the slab has dried back by a "
         "chosen amount, pulses follow while WC is below a set-point, and the slab is brought to drainage "
         "before noon. The sensors are trusted as read. In the six greenhouse compartments evaluated here "
         "(%d sensors, two per compartment, on slabs of one type, %s to %s), the two sensors of one "
         "compartment, which see the same crop, the same nutrient solution and the same pulses, differed by "
         "a median of %s WC %% over the second half of the season, and by %s WC %% in the worst compartment. "
         "A controller that compares such a reading with a set-point opens the valve at the wrong times: "
         "replaying a set-point rule on the raw readings, %d of the %d sensors gave a different valve decision "
         "from their corrected reading on more than 20 %% of the daytime sampling intervals. The technical "
         "problem addressed is to refer each slab sensor to a physical event of its own slab in place, "
         "continuously and without sampling or weighing the slab, so that the irrigation valve acts on how "
         "far each slab actually is from draining."
         % (dc["sensors"], dc["period"][0], dc["period"][1], f1(med["raw"]), f1(gaps_raw_sorted[-1]),
            n_bad, len(sens)))
    h2(doc, "2.1 Technical Problem Addressed by the Invention")
    bullets(doc, [
        "A dielectric slab sensor reports WC through a factory calibration for the slab type; electrode "
        "contact, position in the slab, root growth around the pins and the salinity of the solution move the "
        "reading away from the water actually present, and nothing in the irrigation loop detects it.",
        "Two sensors in one irrigation section disagree by several WC % for weeks; a set-point that is right "
        "for one sensor is wrong for the other, and averaging the two does not tell which one is right.",
        "Calibration by weighing slabs or by gravimetric samples needs a scale under the gutter or "
        "destructive sampling, and is done once, while the error drifts over the season.",
        "One-off field-capacity calibration of soil sensors (Section 3, P1) irrigates in special cycles "
        "until two readings agree and sets a target relative to that reading for a single sensor; it neither "
        "refreshes the reference from routine production pulses nor brings several sensors onto one scale.",
        "A gain error of a sensor scales the overnight dry-back that growers steer on; correcting the gain "
        "from one noisy route can make the dry-back worse rather than better."])
    h2(doc, "2.2 Definitions")
    bullets(doc, [
        "Irrigation section (100): a group of slabs (150) of one substrate type fed by one irrigation valve "
        "or pump (510) through drippers, carrying two or more WC sensors (110, 120).",
        "WC reading: the water content, in % of slab volume, reported by a sensor at each sampling interval "
        "(5 minutes in the example).",
        "Pulse: one opening of the valve (510); its volume per m2 of floor is registered by the dose meter (530).",
        "Rise: the increase of a sensor's reading caused by one pulse, taken as the largest reading in the "
        "%d sampling intervals from the pulse less the reading in the interval before it." % RISE_WIN,
        "Drain onset: the pulse of a day from which the slab passes the added water to the gutter (170) "
        "instead of storing it; seen on the sensor as a collapse of the rise.",
        "Daily plateau P_s(day): the reading of sensor s over the %d minutes after its drain onset." % PLAT_MIN,
        "Reference plateau P_s(d): the median of the sensor's daily plateaus over the %d days before day d." % W_DAYS,
        "Drain deficit D_s(t) = P_s(d) - WC_s(t): the reading still missing before the slab of sensor s "
        "drains; the offset of the sensor cancels in it.",
        "Common plateau constant P* (optional): one value for all sensors in slabs of one substrate type; "
        "corrected reading WC* = P* - D_s, used for display and for set-points written as water contents.",
        "Dry-back: the largest drain deficit of a slab before the first pulse of the next day.",
        "Drain EC probe (550): the conductivity probe in the drain collector of the gutter, which the "
        "irrigation computer already reads; its reading changes when fresh drain water reaches it."])

    # ============================================================== 3
    h1(doc, "3. Prior Patents and Publications from Literature")
    para(doc,
         "Each reference below was checked against its own text before any statement about it was made: the "
         "abstract and first claim of each patent as published, and the full text of each publication "
         "(the abstract only for N3).")
    h2(doc, "A. Prior Patent Literature")
    PAT = [
        ("P1", "US 7,133,749 B2 (family: US 7,574,284 B2)", "Method and apparatus for optimizing soil moisture",
         "Automatic sensor calibration at the first scheduled cycle or on recalibration: a reading, a short "
         "irrigation, a second reading two hours later, repeated until consecutive readings agree within a "
         "set fraction; the stable reading is taken as field capacity and the target is set at a margin "
         "from it. A commissioning routine with dedicated cycles for one soil sensor per zone group; no "
         "reference refreshed from production pulses, no collapse of the pulse response, no common scale for "
         "several sensors, no substrate slab."),
        ("P2", "US 8,862,277 B1 (family: US 8,751,052 B1)", "Automatic efficient irrigation threshold setting",
         "Determines field capacity from the dynamic response of soil moisture after wetting above field "
         "capacity: a fast fall to field capacity followed by a slower fall by evapotranspiration. In an "
         "adaptive mode the value is re-determined from irrigation events or rainfall with a time constant of "
         "about ten days; the threshold is set at 70 to 80 % of field capacity, and the interrupter can only "
         "suspend scheduled watering, not start it. Also detects broken sprinkler heads and drip lines. The "
         "daily value comes from the drainage fall after wetting, not from the collapse of the rise of the "
         "refill pulses; the threshold is a fraction of the reading, so a sensor offset enters it; no "
         "reconciliation of several sensors and no gain gate."),
        ("P3", "US 9,775,308 B2", "Method and apparatus for the automatic regulation of the irrigation of plants",
         "Computes an irrigation duration from a characteristic K, measures soil moisture after irrigating, "
         "and enlarges or reduces K according to whether a target upper moisture limit was exceeded. Adapts "
         "the dose to the reading as read; the sensor itself is not corrected."),
        ("P4", "EP 0 392 639 A2 (Rockwool/Grodan)", "Method and device for measuring the moisture content of a substrate for growing",
         "Measures the capacitance between electrodes in an artificial (rock-wool) substrate, and the "
         "resistance for its salinity. Sensor construction; no in-place recalibration."),
        ("P5", "EP 2 166 347 A1", "A substrate water content measuring device",
         "Capacitance between two electrodes, at least one extending along an outer boundary plane of a "
         "mineral-wool slab, converted to water content. Device construction; no recalibration."),
        ("P6", "US 12,480,932 B2", "Sensor and system for monitoring a substrate",
         "Two sensing elements in the substrate, an applied electrical signal and an electrical model with "
         "inductances, capacitance and conductance from which the water amount and nutrient concentration "
         "are computed. Improves the conversion inside one sensor; no reference from drain onset and no "
         "reconciliation between sensors."),
        ("P8", "US 11,930,744 B2", "System and method of adjusting irrigation schedules with soil moisture data",
         "Claim 1: a predicted soil moisture value, the current value adjusted by the average or median of "
         "negative net changes of historic sensor values, is compared with a low threshold to allow the next "
         "scheduled irrigation. Uses history to anticipate drying; the reading itself and the threshold stay "
         "on the sensor's own uncorrected scale."),
        ("P9", "US 8,961,068 B2", "Device, system, and method of irrigation",
         "Times the arrival of irrigation water at a buried moisture sensor after the valve opens, computes a "
         "drainage speed from the sensor depth and sets the remaining irrigation time to reach the root depth. "
         "Uses the wetting front in soil; no drainage plateau of a slab and no sensor correction."),
        ("P7", "EP 3 016 492 B1 (Rockwool)", "Plant growth system",
         "Claim 1: central processing receives temperature, water content and nutrient content of a "
         "hydroponic substrate from wireless detectors, stores predefined irrigation data relating such "
         "values to desired irrigation outputs, and outputs the desired irrigation input. The detectors' "
         "readings are used as reported; the text does not address their calibration."),
    ]
    table(doc, ["S.No.", "Patent No.", "Title", "Comments"], [[a, b, c, d] for a, b, c, d in PAT],
          "Table 1: Prior patent literature", widths=[0.5, 1.3, 1.6, 3.3], size=9, align_left_cols=(2, 3))
    h2(doc, "B. Non-Patent Literature")
    NPL = [
        ("N1", "Hemming, de Zwart, Elings, Petropoulou, Righini (2020), Sensors 20, 6430",
         "Cherry tomato production in intelligent greenhouses: sensors and AI for control of climate, irrigation, crop yield, and quality",
         "Describes the six compartments from which the example data come: cherry tomato on Grodan GT Master "
         "stone wool slabs on elevated gutters, drippers fed by an on/off irrigation pump, drain collected "
         "in the gutter and measured for quantity, EC and pH, GroSens sensors in the slabs, 5-minute data "
         "exchange. The slab sensors are used as read."),
        ("N2", "Hemming, de Zwart, Elings, Righini, Petropoulou (2019), Sensors 19, 1807",
         "Remote control of greenhouse vegetable production with artificial intelligence: greenhouse climate, irrigation, and crop production",
         "First edition of the same facility with cucumber: rockwool cubes on slabs on hanging gutters, "
         "drippers operated by a valve, drain recollected in a closed loop. No sensor recalibration."),
        ("N3", "Montesano, van Iersel, Boari, Cantore, D'Amato, Parente (2018), Agric. Water Manage. 203, 20-29",
         "Sensor-based irrigation management of soilless basil using a new smart irrigation system",
         "Cloud-connected wireless irrigation with dielectric moisture/salinity sensors in a perlite-coco "
         "substrate, irrigation set-points of 0.40, 0.30 and 0.20 m3/m3. The set-point is compared with the "
         "reading as reported."),
        ("N4", "van Iersel and Burnett, Decagon Devices application note (2015)",
         "Using soil water sensors for efficient irrigation in greenhouses",
         "Opens an irrigation valve when the substrate water content measured by EC-5 probes drops below a "
         "grower set-point; a controller takes one to four probes. The probes are taken to read the "
         "substrate correctly."),
        ("N5", "Grodan (Rockwool group), product brochure",
         "Grodan GroSens MultiSensor System",
         "Wireless WC, EC and temperature sensors for stone wool slabs; a Smartbox processes sensor data "
         "taking the slab type and dimension into account; more sensors give more representative figures "
         "for the irrigation section. Averaging; no reconciliation of sensor offsets."),
        ("N6", "Hemming et al., 4TU.ResearchData, doi 10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7",
         "Autonomous Greenhouse Challenge, second edition (2019): data set and parameter description",
         "Defines the recorded variables: cumulative irrigation per day computed from valve minutes, daily "
         "irrigation and drain, two GroSens slab sensors per compartment (WC, EC, temperature, 5 minutes). "
         "Source of the example data."),
    ]
    table(doc, ["S.No.", "Reference", "Title", "Comments"], [[a, b, c, d] for a, b, c, d in NPL],
          "Table 2: Non-patent literature", widths=[0.5, 1.5, 1.6, 3.1], size=9, align_left_cols=(1, 2, 3))

    # ============================================================== 4
    h1(doc, "4. Summary and Background of the Invention")
    h2(doc, "4.1 Background")
    para(doc,
         "Soilless culture on stone wool is steered by the water content of the slab. A drained stone wool slab "
         "holds a fixed amount of water set by its pore structure; the grower lets it dry back overnight, "
         "doses pulses from the morning until it drains again, and repeats. The sensor that reports WC is a "
         "dielectric probe with pins through the slab [N5, P4, P5, P6]. Its reading feeds the irrigation "
         "computer directly [P7, N3, N4]. In the example data the median raw readings of the two sensors in "
         "one compartment were %s and %s WC %% (AICU), %s and %s (Digilog), %s and %s (IUA.CAAS), on slabs of "
         "one type." % (f1(dc["per_compartment"]["AICU"]["wc_median_1"]), f1(dc["per_compartment"]["AICU"]["wc_median_2"]),
                        f1(dc["per_compartment"]["Digilog"]["wc_median_1"]), f1(dc["per_compartment"]["Digilog"]["wc_median_2"]),
                        f1(dc["per_compartment"]["IUACAAS"]["wc_median_1"]), f1(dc["per_compartment"]["IUACAAS"]["wc_median_2"])))
    para(doc,
         "Two remedies exist. A calibration can be made once, by weighing slabs or sampling, or by a "
         "commissioning routine that irrigates until readings stop rising and treats that reading as field "
         "capacity [P1, P2]; P2 also re-determines field capacity from the drainage fall after wetting, with "
         "a time constant of about ten days. The dose can be adapted to the reading or its recent history "
         "[P3, P8], or to the travel time of the wetting front [P9]. None of these takes the reference from "
         "the moment the substrate stops storing the pulses that the crop receives anyway, and none steers "
         "on the distance of each reading from its own slab's drainage, so a section with two sensors still "
         "has two different readings of the same water.")
    h2(doc, "4.2 Distinctions from Prior Art")
    para(doc,
         "The references are distinguished below by what they teach and by the technical effect they do not "
         "produce. Where a prior teaching could be applied to the example data, it was applied with the same "
         "window and the same held-out half, and its result is given beside that of the invention.")
    bullets(doc, [
        "Drainage-based calibration, once (P1). P1 runs dedicated watering cycles until one sensor's reading "
        "stops changing and keeps that reading as field capacity until a recalibration is requested. An "
        "anchor of this kind, fixed from each sensor's first %d onset days, lay a median %s WC %% from the "
        "reading at the moment fresh drain reached the drain EC probe, against %s WC %% for the rolling "
        "drain-onset anchor; it left a median paired gap of %s WC %% against %s, and the valve decisions of "
        "the two differ on a median %s %% of daytime intervals (Sections 8.4, 8.8)."
        % (e6["commissioning_days"], f2(lv["comm"]["pooled_median_abs"]), f2(lv["roll"]["pooled_median_abs"]),
           f2(e6["median_commissioning"]), f2(e6["median_rolling"]),
           pc(e6["decision_mismatch_commissioning_vs_rolling_median"])),
        "Drainage-based calibration, adaptive (P2). P2 takes field capacity from the fast fall of the "
        "reading after the soil is wetted above it, renews it from later irrigation events, sets the "
        "threshold at a fraction of it and can only suspend watering. The event differs: the fall after "
        "wetting mixes the drainage of excess water with the crop's uptake and ends gradually, whereas the "
        "collapse of the rise of the refill pulses marks the pulse at which the slab stops storing water. "
        "Applied to the example data, field capacity from the fall after the last pulse of each day, renewed "
        "over the same %d-day window, lay a median %s WC %% from the reading at physical drain, with %d of "
        "%d sensors within 1 WC %%; the drain-onset anchor lay %s WC %% from it, with %d of %d. The morning "
        "deficit to the drain-onset anchor also ranks the litres dosed until drain better (Spearman %s "
        "against %s; 95 %% interval of the difference %s to %s, Section 8.8). A threshold set as a "
        "fraction of the reading keeps part of the sensor offset; the drain deficit cancels it."
        % (W_DAYS, f2(p2l["pooled_median_abs"]), p2l["sensors_within_1"], p2l["sensors"],
           f2(onl["pooled_median_abs"]), onl["sensors_within_1"], onl["sensors"],
           f2(e11["litres_spearman"]["onset"]), f2(e11["litres_spearman"]["p2"]),
           f2(e11["litres_onset_minus_p2_ci95"][0]), f2(e11["litres_onset_minus_p2_ci95"][1])),
        "Dynamic soil-moisture irrigation (P3, P7, P8, P9, N3, N4). These adapt the dose or the timing to "
        "the reading, to its recent history or to the travel time of the wetting front, but compare a "
        "reading on the sensor's own scale with a threshold. With one constant on the raw readings, the "
        "reading at physical drain lay a median %s WC %% from it and within 1 WC %% for %d of %d sensors; on "
        "raw readings %d of %d sensors decide the valve differently from the drain deficit on more than "
        "20 %% of daytime intervals (Sections 8.5, 8.8)."
        % (f2(lv["raw"]["pooled_median_abs"]), lv["raw"]["sensors_within_1"], dc["sensors"], n_bad, len(sens)),
        "Sensor construction (P4, P5, P6, N5). These improve the electrodes or the conversion inside one "
        "sensor, or average several sensors; the invention needs no change to the sensor and removes, in "
        "place, the offset that the conversion leaves behind.",
        "Gain and delivery (P2, N5). Neither estimates a sensor gain by two physically independent routes. "
        "Applying a gain from one route always raised the median paired dry-back gap from %s %% to %s %%; "
        "applying it only when both routes agree lowered it to %s %% (Section 8.6). The gain-free delivery "
        "ratio between slabs is absent from all references."
        % (pc(dbm["gap_raw"], 1), pc(dbm["gap_scale_ungated"], 1), pc(dbm["gap_scale_gated"], 1))])
    para(doc,
         "No reference teaches the sequence of claim 1, from the response of each sensor to the pulses "
         "through the collapse of that response, the sensor-specific plateau and the rolling reference to "
         "the drain deficit on which the valve acts; and none of the prior anchors that could be computed on "
         "the same data reaches the agreement with the physical drain that the sequence gives.")
    h2(doc, "4.3 Inventive Combination")
    para(doc,
         "The combination is: (i) the response of each sensor to every routine irrigation pulse; (ii) the "
         "collapse of that response relative to the same sensor's earlier pulses of the day, taken as the "
         "drain onset of its slab, a physical event that does not depend on the sensor's scale or offset; "
         "(iii) the sensor's reading after that onset as its own daily plateau; (iv) a reference built from "
         "past days only, held in a reference memory, so that the controller can apply it in real time and "
         "follow drift; (v) the drain deficit of each reading to that reference, in which the sensor's "
         "offset cancels and which needs no assumption that different slabs drain at the same water "
         "content; and (vi) the irrigation valve opened when the deficit exceeds one set-point. The effect "
         "does not hinge on particular constants: over onset fractions of %s to %s and windows of %d to %d "
         "days the median paired gap stayed between %s and %s WC %% against %s raw (Section 8.4)."
         % (f1(min(THRS)), f1(max(THRS)), min(WINS), max(WINS), f2(gmin), f2(gmax), f2(ex["E1_raw_gap_median"])))
    h2(doc, "4.4 Feature Mapping Against Prior Art")
    FEAT = [
        ("F1", "Reference from the drain-onset reading of the sensor's own slab", "Partial", "Partial", "No", "No", "No"),
        ("F2", "Drain onset from collapse of the response to routine production pulses", "No", "No", "No", "No", "No"),
        ("F3", "Reference renewed from past days only", "No", "Partial", "No", "Partial", "No"),
        ("F4", "Valve opened on the deficit to the slab's own drain onset", "No", "No", "No", "No", "No"),
        ("F5", "Gain applied only when two physical routes agree", "No", "No", "No", "No", "No"),
        ("F6", "Gain-free delivery ratio between slabs", "No", "Partial", "No", "No", "No"),
        ("F7", "Irrigation valve actuated on the corrected reading", "Partial", "Partial", "Partial", "Partial", "Yes"),
        ("F8", "Sensor checked against the drain EC probe at the first drained pulse", "No", "No", "No", "No", "No"),
    ]
    table(doc, ["#", "Feature", "P1", "P2", "P3", "P8", "N4"], [list(r) for r in FEAT],
          "Table 3: Feature mapping of the invention against the nearest art",
          widths=[0.4, 3.4, 0.58, 0.58, 0.58, 0.58, 0.58], size=9, align_left_cols=(1,))
    h2(doc, "4.5 Technical Effects")
    bullets(doc, [
        "The corrected reading meets the physical drain: at the first pulse of each day after which the "
        "drain EC probe (550) registered fresh drain, the readings of the %d sensors lay a median %s WC %% "
        "from their rolling anchors (%d of %d sensors within 1 WC %%), against %s WC %% from a one-off "
        "commissioning anchor and %s WC %% from one common constant on the raw reading (%d of %d)."
        % (dc["sensors"], f2(lv["roll"]["pooled_median_abs"]), lv["roll"]["sensors_within_1"], dc["sensors"],
           f2(lv["comm"]["pooled_median_abs"]), f2(lv["raw"]["pooled_median_abs"]),
           lv["raw"]["sensors_within_1"], dc["sensors"]),
        "The deficit follows the water the slab physically takes: against the litres dosed each morning "
        "until the drain EC probe registered drain, read without any slab sensor, the rank correlation "
        "of the morning deficit over all %d sensors is %s with the rolling anchor, against %s with a "
        "one-off commissioning anchor and %s with one common constant on the raw reading."
        % (dc["sensors"], f2(lp["roll"]), f2(lp["comm"]), f2(lp["raw"])),
        "Paired sensors on one substrate type read alike: over the held-out second half, the median gap "
        "between the two sensors of a compartment falls from %s to %s WC %% (median over %d compartments); in "
        "the worst compartment from %s to %s WC %%. On %d of %d compartment-days where the two differ the "
        "corrected gap is the smaller (sign test z = %s)."
        % (f2(med["raw"]), f2(med["rolling"]), len(TEAMS), f1(ra["teams"][raw_max_t]["raw"]),
           f1(ra["teams"][raw_max_t]["rolling"]), e2["pooled"]["anchor_lower"], e2["pooled"]["of"],
           f2(e2["pooled"]["z"])),
        "Valve decisions follow the water in the slab: on raw readings %d of %d sensors would have opened or "
        "held the valve differently from the corrected reading on more than 20 %% of daytime intervals "
        "(median %s %%), and in a median %s %% of intervals called for a pulse while the corrected slab was "
        "already at its drainage plateau, so that the pulse would have passed to the gutter."
        % (n_bad, len(sens), pc(mm["mismatch"]), pc(mm["full_slab_irr"])),
        "Insensitive to the constants: over windows of 7, 14 and 28 days and onset thresholds of 0.2, 0.3 "
        "and 0.4 the median gap stays between %s and %s WC %% (raw %s)."
        % (f2(gmin), f2(gmax), f2(ex["E1_raw_gap_median"])),
        "Gain correction without harm: applying a gain only when the rise route and the decline route agree "
        "within %d %% lowers the median paired dry-back gap from %s %% to %s %%, while applying it always "
        "raises it to %s %%." % (round(100 * GATE), pc(dbm["gap_raw"], 1), pc(dbm["gap_scale_gated"], 1),
                                  pc(dbm["gap_scale_ungated"], 1)),
        "A partly closed dripper line shows without any gain: closures of %d %% injected into the measured "
        "delivery ratios raised the alarm within two to four weeks in %s %% of cases, with no alarm in the "
        "same windows without a closure." % (inj["0.6"]["closed_pct"], pc(inj["0.6"]["rate"])),
        "No new instrument: the inputs are the readings of the slab sensors and the pulse volumes already "
        "registered by the dose meter; the computation takes %s ms for each sensor and day on one processor core."
        % f1(tm["ms_per_sensor_day"])])
    h2(doc, "4.6 Applicability")
    para(doc,
         "The method applies to any soilless irrigation section with dielectric substrate sensors and pulsed "
         "irrigation that brings the slab to drainage on most days: stone wool and other mineral-wool slabs "
         "for tomato, cucumber, pepper, aubergine, strawberry and cut flowers, and coir slabs where the "
         "drainage plateau is equally fixed by the pore structure. It runs in the irrigation computer that "
         "already receives the sensor readings and the pulse log. Indian protected cultivation of capsicum, "
         "cucumber and tomato in polyhouses on coco-peat slabs with drip fertigation uses the same hardware.")

    # ============================================================== 5
    h1(doc, "5. Objective(s) of the Invention")
    para(doc,
         "The primary objective is to provide a system that recalibrates each substrate water-content sensor "
         "of an irrigation section in place, from the drain onset of its own slab under routine irrigation "
         "pulses, and opens or holds the irrigation valve on the corrected reading.")
    bullets(doc, [
        "(a) To detect, every irrigated day, the moment a slab starts to drain from the collapse of the rise "
        "of the sensor reading per irrigation pulse.",
        "(b) To keep for each sensor a reference reading at drainage plateau built from its past days only.",
        "(c) To express every reading as its deficit to the drain onset of its own slab, so that one "
        "set-point means the same distance from drainage on every slab.",
        "(d) To actuate the irrigation valve or pump on that deficit, and to check each sensor against the "
        "drain EC probe of the gutter.",
        "(e) To correct the gain of a sensor only when two physically different routes agree.",
        "(f) To compare the water delivered to two slabs per unit of their demand, free of sensor gain.",
        "(g) To evidence the correction on real sensor records of operating greenhouse compartments."])

    # ============================================================== 6
    h1(doc, "6. Working Principle of the Invention (in brief)")
    num(doc,
        "An irrigation section (100) of a greenhouse holds slabs (150) of one plant-growth substrate, for "
        "example stone wool, on a gutter (170). An irrigation valve or pump (510) doses nutrient solution "
        "through drippers in pulses; a dose meter (530) registers each pulse volume and a drain meter (540) "
        "the water collected by the gutter. Two or more dielectric water-content sensors (110, 120), each "
        "with pins inserted in a different slab, report the WC reading every sampling interval to a "
        "data-processing system (900), the irrigation computer of the section.")
    num(doc,
        "A slab stores water from each pulse until its pores are filled to the level that the pore structure "
        "can hold against gravity; from then on, each further pulse drains through to the gutter (170). The "
        "water content at which this happens, the drainage plateau, is set by the pore structure of the "
        "slab. On the sensor it shows as a collapse of the rise "
        "of the reading per pulse: large rises in the morning while the slab is filling, small rises once it "
        "drains (Figure 3(b)).")
    num(doc,
        "A sensor with an offset reads the plateau high or low, and every other reading by the same amount. "
        "The difference between a reading and the same sensor's plateau reading is therefore free of the "
        "offset: it is the water content still missing before that slab drains. This holds whether or not "
        "two slabs drain at exactly the same water content, since each sensor is referred to its own slab. "
        "The system (900) therefore detects the drain onset "
        "of each sensor's slab each day as the first pulse, after the first %d pulses of the day, whose rise "
        "falls below %s of their median rise, and records the reading over the %d minutes after it as that "
        "day's plateau reading." % (N_FIRST, f1(THR), PLAT_MIN))
    num(doc,
        "The reference plateau of each sensor on day d is the median of its plateau readings over the %d "
        "preceding days, provided at least %d were found; otherwise the last reference is kept. It uses past "
        "days only, so the irrigation computer can apply it in real time, and it follows slow drift of the "
        "sensor, such as roots growing around the pins or a change of solution salinity." % (W_DAYS, MIN_DAYS))
    num(doc,
        "At every interval the drain deficit of each sensor is D = P_s(d) - WC. Where the grower prefers "
        "set-points written as water contents, the deficit is shown on a common scale WC* = P* - D, P* being "
        "one plateau constant for the substrate type, in the example the median of all sensors' plateau "
        "readings over a commissioning period; a set-point S = P* - d on WC* is the same rule as d on D.")
    num(doc,
        "At every sampling interval the system (900) compares the drain deficit of the section with the "
        "set-point d and opens the valve or starts the pump (510) for a pulse when it is larger, and keeps "
        "it closed otherwise. A pulse is thus no longer given to a slab that is already draining because its "
        "sensor reads low, and no longer withheld from a drying slab because its sensor reads high.")
    num(doc,
        "A gain error of a sensor stretches its excursions from the plateau, such as the overnight dry-back. "
        "Two routes see the gain: the rise per litre dosed before the drain onset, and the fall of the "
        "reading per day as the crop takes up water. Their ratios between two sensors of a section are "
        "estimates of the relative gain from different physical processes; the system scales the excursion "
        "only when the two agree within %d %%, so that a wrong estimate from one route is not applied."
        % round(100 * GATE))
    num(doc,
        "The ratio of the two routes for one sensor, the rise per litre divided by the daily fall, does not "
        "contain the sensor's gain at all. Between two slabs of a section it compares the water each slab "
        "receives from its drippers per unit of its crop's demand; the system watches its weekly value and "
        "raises a delivery alarm (430) when it drifts.")
    num(doc,
        "The drain EC probe (550) in the drain collector gives an independent check. Its reading moves only "
        "when fresh drain reaches it, so a step of at least %s dS/m within %d minutes of a pulse marks that "
        "pulse as drained. At the first drained pulse of a day the drain deficit of a correct sensor is near "
        "zero; the check unit (360) keeps this value for each sensor and day and issues a sensor check "
        "signal (440) when its median over the window departs from zero by more than a limit."
        % (f2(e8["step_dS_m"]), e8["lag_min"]))
    h2(doc, "6.1 Claimed Function Against Example Implementation")
    table(doc, ["Claimed function", "Example implementation (Section 8)"], [
        ["Pulses delivered; readings and pulse volumes received (claim 1 (a))",
         "GroSens WC at 5-min intervals, two sensors per compartment; pulse volume = step of the daily "
         "cumulative irrigation, reset detected by the counter falling"],
        ["Response per pulse and its collapse = drain onset (claim 1 (b), (c)); constants, claim 3",
         "Rise = max of %d intervals from the pulse - interval before; onset = first pulse after the first %d "
         "with rise < %s x their median rise" % (RISE_WIN, N_FIRST, f1(THR))],
        ["Sensor-specific daily plateau (claim 1 (d))", "Median reading over %d min after the onset" % PLAT_MIN],
        ["Rolling reference from the reference memory (claim 1 (e)); claim 3",
         "Median of plateaus over the %d days before; >= %d days, else last kept" % (W_DAYS, MIN_DAYS)],
        ["Drain deficit (claim 1 (f)); common scale, claim 2",
         "D = P_s(d) - WC; WC* = P* - D with P* = %s WC %%, median of the %d sensors' first-half plateaus"
         % (f2(P_STAR), dc["sensors"])],
        ["Valve on the deficit (claim 1 (g))",
         "Replayed rule: pulse when D > %d (same as WC* < P* - %d), 06:00-18:00" % (SETBACK, SETBACK)],
        ["Gated gain (claim 4)", "28-day rolling ratios by the two routes; applied if within %d %%" % round(100 * GATE)],
        ["Delivery ratio (claim 5)", "Weekly rise per litre / mean daily fall, slab 1 over slab 2"],
        ["Drain-probe check (claim 6)", "Drain EC step >= %s dS/m within %d min of a pulse; deficit at the "
         "first drained pulse of each day (Section 8.8)" % (f2(e8["step_dS_m"]), e8["lag_min"])],
    ], "Table 4: Claimed functional combination against the example implementation",
        widths=[2.4, 4.3], size=9, align_left_cols=(0, 1))
    h2(doc, "6.2 Technical Contribution")
    para(doc,
         "The contribution is a change in what a substrate water-content sensor is referenced to: from a "
         "factory conversion fixed at installation to a physical event of its own slab, the drain onset, "
         "observed every irrigated day under ordinary production pulses, and from a raw reading to a deficit "
         "to that event that means the same distance from drainage on every slab. The effect is on the "
         "irrigation valve: it acts on how far each slab is from draining rather than on a reading that "
         "differs from sensor to sensor.")
    h2(doc, "6.3 Drawings")
    bullets(doc, [
        "Figure 1: architecture: irrigation section, dosing hardware and the data-processing system.",
        "Figure 2: flowchart of the method.",
        "Figure 3: physics: pulse response, drain onset and the plateau of each sensor.",
        "Figure 4: paired-sensor agreement, sensitivity and valve decisions.",
        "Figure 5: gain routes, dry-back, delivery ratio and coverage.",
        "Figure 6: claim tree."])
    figure(doc, "fig01.png", "Figure 1: Irrigation section with slab water-content sensors, dosing hardware and the recalibrating controller",
           "Sensors 110 and 120 in slabs 150 and dose meter 530 report to system 900; units 310-350 detect the "
           "drain onset and correct the reading; unit 410 sends the valve command to valve or pump 510.")
    figure(doc, "fig02.png", "Figure 2: Flowchart of the method",
           "S1-S6 detect the drain onset, update the rolling reference and correct the reading; the decision "
           "opens or holds valve 510 (S7a, S7b); S8 checks delivery weekly.", width=5.2)

    # ============================================================== 7
    h1(doc, "7. Description of the Invention in Detail")
    h2(doc, "7.1 Irrigation Section Hardware")
    num(doc,
        "The slabs (150) are mineral-wool slabs of one product, in the example Grodan GT Master stone wool on "
        "elevated gutters [N1], each carrying plants in propagation blocks with one dripper per block. The "
        "irrigation valve or pump (510) is switched on and off by the irrigation computer and doses nutrient "
        "solution from a day tank; the dose meter (530) registers the litres per m2 of each pulse, in the "
        "example as valve minutes converted to litres (median pulse %s L/m2). The gutter (170) collects the "
        "drain water and the drain meter (540) registers it per day."
        % f1(dc["per_compartment"]["Reference"]["pulse_volume_median_l_m2"]))
    num(doc,
        "Each WC sensor (110, 120) has metal pins inserted vertically through the slab about 10 cm from a "
        "block on the drain side; the sensor measures the dielectric permittivity and the bulk conductivity "
        "between the pins and converts them to WC, EC and temperature for the slab type set at "
        "installation, and transmits them wirelessly every few minutes to a receiver connected to the "
        "irrigation computer (900).")
    h2(doc, "7.2 Signals")
    num(doc,
        "The system (900) receives every sampling interval the WC reading of each sensor and the "
        "cumulative irrigation volume of the day. The pulse volume is the step of the cumulative volume "
        "between intervals; when the counter falls, the day has been reset and the new value is the first "
        "pulse of the new day. Detecting the reset by the fall of the counter, rather than by the clock, "
        "matters: the counter of the example resets shortly after midnight, so that the midnight sample "
        "still holds the previous day's total. With this rule the pulse volumes add up to %s-%s times the "
        "daily irrigation meter in every compartment (correlation of daily totals >= %s)."
        % (f2(dc["pulse_over_meter_range"][0]), f2(dc["pulse_over_meter_range"][1]), f2(dc["corr_daily_min"])))
    h2(doc, "7.3 Pulse Response and Drain Onset (310, 320)")
    num(doc,
        "The pulse-response unit (310) computes, for each pulse and each sensor, the rise of the reading: "
        "the largest reading over the %d sampling intervals from the pulse less the reading in the interval "
        "before it. The window covers the wetting front reaching the pins. Rises of a filling slab in the "
        "example were 1 to 2 WC %% per pulse (Figure 3(b))." % RISE_WIN)
    num(doc,
        "The drain-onset unit (320) takes, each day with at least six pulses, the median rise of the first "
        "%d pulses; if it is at least 0.5 WC %%, the drain onset is the first later pulse whose rise is below "
        "%s of that median. Because the threshold is a fraction of the same sensor's morning rise on the "
        "same day, a sensor with a gain error finds the onset at the same pulse as a correct one; the "
        "detection does not depend on the sensor's scale or offset. Figure 3(a) shows one day of IUA.CAAS "
        "(%s): both sensors find their onset, and their plateaus differ by the sensors' offsets."
        % (N_FIRST, f1(THR), f3["day"]))
    figure(doc, "fig03.png", "Figure 3: Pulse response, drain onset and plateau readings of slab sensors",
           "(a) one day of readings of the two sensors of a compartment and the pulses; (b) rise per pulse; "
           "(c) daily plateau and rolling reference over the season; (d) day-to-day change of the plateau, "
           "%d consecutive sensor-days." % f3["n_changes"])
    h2(doc, "7.4 Rolling Reference (330) and Common Constant (340)")
    num(doc,
        "The plateau of the day is the median reading over the %d minutes after the onset. Across all twelve "
        "sensors the plateau changed by a median of %s WC %% from one day to the next (Figure 3(d)), so a "
        "few days suffice to fix it. The rolling-reference unit (330) takes the median of a sensor's plateaus "
        "over the %d days before the current day when at least %d exist, and otherwise keeps the last "
        "reference; a section irrigated with little drain, where onsets are rare, keeps its last reference "
        "until the next ones arrive." % (PLAT_MIN, f2(f3["median_abs_change"]), W_DAYS, MIN_DAYS))
    num(doc,
        "The optional common-scale unit (340) holds one plateau value P* for the substrate type, used only "
        "to show the deficit as a water content. In the example it "
        "is the median of the first-half plateau readings of the %d sensors, %s WC %%. Where the slab "
        "manufacturer states the water content of the drained slab, that value can be used instead; the "
        "valve decision on the deficit does not depend on the choice."
        % (dc["sensors"], f2(P_STAR)))
    num(doc,
        "When a sensor is replaced, moved to another slab or re-inserted, its reference is cleared and "
        "rebuilt from the onsets that follow; until %d have been found the sensor's reading is shown but "
        "not used for the valve decision of the section, which then uses the other sensors. A new slab "
        "type, or a slab replaced at the start of a crop, starts a new commissioning period for P*."
        % MIN_DAYS)
    num(doc,
        "Example: in the IUA.CAAS compartment on %s the rolling references of the two sensors were %s and "
        "%s WC %%. With P* = %s, a raw reading of 80.0 WC %% becomes %s WC %% on the first sensor and %s WC %% "
        "on the second; a set-point of %s WC %% therefore calls for a pulse on the first slab and not on the "
        "second, although both raw readings are equal."
        % (f3["day"], f1(f3["ref1"]), f1(f3["ref2"]), f2(P_STAR), f1(80.0 - f3["ref1"] + P_STAR),
           f1(80.0 - f3["ref2"] + P_STAR), f2(P_STAR - SETBACK)))
    h2(doc, "7.5 Corrected Reading and Gated Gain (350)")
    num(doc,
        "The correction unit (350) outputs the drain deficit D = P_s(d) - WC for every sensor at every "
        "interval. "
        "Optionally it also corrects the gain of one sensor relative to another. The rise route takes the "
        "summed rises over the summed volumes of pre-drain pulses of each sensor (WC %% per L/m2), the "
        "decline route takes the mean daily fall of the reading outside pulses after a three-sample running "
        "median; both are computed weekly and their 28-day medians form the relative gain by each route. "
        "Where the two agree within %d %%, the deficit of the second sensor is divided by the "
        "gain; otherwise only the offset is corrected. In the first half of the season the routes agreed "
        "within %d %% in %d of %d compartments (Figure 5(a))."
        % (round(100 * GATE), round(100 * GATE), len(agree), len(TEAMS)))
    h2(doc, "7.6 Valve Control (410, 420)")
    num(doc,
        "The valve-decision unit (410) compares the drain deficit of the section, that of one sensor or "
        "the mean of its sensors, with a set-point d, the dry-back the grower allows during the day, and "
        "the valve-command unit (420) switches the valve or pump (510) through its output relay: a pulse "
        "when D > d, none otherwise. The first pulse of the morning, the pulse interval and the "
        "pulse volume remain set by the grower's strategy; the invention changes which reading the "
        "comparison uses.")
    num(doc,
        "The units 310 to 430 run in the irrigation computer (900) of the greenhouse, which already "
        "receives the sensor readings through the sensor receiver and switches the valve or pump (510) "
        "through a relay output; onset, plateau and reference are updated once a day, the correction and "
        "the comparison at every sampling interval. The state kept for each sensor is the list of plateau "
        "readings of the window, a few hundred bytes. In the example the whole computation took %s ms for "
        "each sensor and day on one processor core." % f1(tm["ms_per_sensor_day"]))
    h2(doc, "7.7 Delivery Ratio and Alarm (430)")
    num(doc,
        "For each sensor the ratio of its weekly pre-drain rise per litre to its weekly mean daily fall is "
        "free of its gain and of the slab volume; between two slabs of a section it is the water delivered "
        "per unit of crop demand on one slab relative to the other. A clogged dripper or a slab with fewer "
        "plants moves it; the alarm unit (430) signals when it departs from 1 by more than a limit set for "
        "the section.")
    num(doc,
        "The limit is set from the week-to-week scatter of the ratio in the first weeks of the section; in "
        "the example the interquartile range of the weekly ratio was %s to %s in the growers' compartment "
        "and %s to %s in IUA.CAAS. With the rule 'alarm when the weekly ratio departs from the median of its "
        "previous four weeks by more than L in two consecutive weeks', L = 0.3 raised no alarm in %d "
        "section-weeks without a recorded fault and L = 0.2 raised %d. On an alarm the grower checks the "
        "drippers of the two slabs with a measuring cup."
        % (f2(dr["Reference"]["rho_ratio_iqr"][0]), f2(dr["Reference"]["rho_ratio_iqr"][1]),
           f2(dr["IUACAAS"]["rho_ratio_iqr"][0]), f2(dr["IUACAAS"]["rho_ratio_iqr"][1]),
           e7["0.3"]["section_weeks"], e7["0.2"]["alarm_weeks"]))
    num(doc,
        "Where a section has three or more sensors, the corrected readings can also be compared with one "
        "another at each interval: after correction they differ by about the scatter of Section 8.3, and a "
        "sensor that departs from the others by much more, for example one pulled partly out of its slab, "
        "is reported for inspection.")
    h2(doc, "7.8 Reference Numerals")
    table(doc, ["Numeral", "Element", "Numeral", "Element"], [
        ["100", "Irrigation section", "310", "Pulse-response unit"],
        ["110, 120", "Water-content sensors", "320", "Drain-onset unit"],
        ["150", "Substrate slabs", "330", "Rolling-reference unit"],
        ["160, 161", "Plants and drippers", "340", "Common-scale unit (optional)"],
        ["170", "Gutter", "350", "Correction (deficit) unit"],
        ["200", "Signal input", "360", "Drain-probe check unit"],
        ["210", "WC readings", "400", "Irrigation control"],
        ["220", "Pulse log", "410", "Valve-decision unit"],
        ["500", "Dosing hardware", "420", "Valve command"],
        ["510", "Irrigation valve or pump", "430", "Delivery alarm"],
        ["530", "Dose meter", "440", "Sensor check signal"],
        ["540", "Drain meter", "550", "Drain EC probe"],
        ["900", "Data-processing system", "", ""],
    ], "Table 5: Reference numerals", widths=[0.9, 2.45, 0.9, 2.45], size=9, align_left_cols=(1, 3))

    # ============================================================== 8
    h1(doc, "8. Experimental Validation Results")
    h2(doc, "8.1 Data and Configuration")
    para(doc,
         "All inputs are the published records of the second Autonomous Greenhouse Challenge [N1, N6]: six "
         "greenhouse compartments of Wageningen University & Research growing cherry tomato on stone wool "
         "from %s to %s, each with two GroSens slab sensors reporting every 5 minutes, the cumulative "
         "irrigation of the day and the daily irrigation and drain totals. %d sampling intervals carried "
         "both sensors' readings and %d pulses were dosed. Five compartments were operated by international "
         "teams, one by commercial growers; their irrigation strategies differed. The first half of the "
         "season (to the middle day) is used only to fix P* and, for the fixed-anchor comparison, the "
         "reference; all scores are on the second half. Table 6 lists the operating constants, read from "
         "the code that used them; they were set before the sensitivity runs of Section 8.4 and not changed "
         "for them." % (dc["period"][0], dc["period"][1], dc["samples_both_wc"], dc["pulses"]))
    table(doc, ["Parameter", "Value", "Role"], [
        ["Sampling interval", "5 min", "readings and pulse log"],
        ["Rise window", "%d intervals" % RISE_WIN, "rise per pulse"],
        ["First pulses / threshold", "%d / %s of their median rise" % (N_FIRST, f1(THR)), "drain onset"],
        ["Plateau period", "%d min after onset" % PLAT_MIN, "daily plateau"],
        ["Rolling window", "%d days, >= %d plateau days" % (W_DAYS, MIN_DAYS), "reference plateau"],
        ["Common constant P*", "%s WC %%" % f2(P_STAR), "corrected scale"],
        ["Set-point in the replay", "P* - %d WC %%, 06:00-18:00" % SETBACK, "valve decision"],
        ["Gain gate", "routes within %d %%, 28-day ratios" % round(100 * GATE), "gain correction"],
    ], "Table 6: Configuration parameters", widths=[2.0, 2.3, 2.4], size=9, align_left_cols=(0, 2))
    h2(doc, "8.2 Tests")
    table(doc, ["Test", "Question", "Ground truth"], [
        ["V1", "Do the two sensors of one compartment, on the same slab type under the same pulses, read "
               "alike after correction, in the held-out half?", "The physical identity of the two slabs' plateau"],
        ["V2", "Do the results hold when the window and the onset threshold change, and day by day?", "As V1"],
        ["V3", "How often does a set-point rule decide the valve differently on raw and on corrected readings?",
         "Corrected reading (V1)"],
        ["V4", "Does a gain correction improve the paired dry-back, with and without the two-route gate?", "As V1"],
        ["V5", "Is the gain-free delivery ratio near 1 and stable, and does its alarm find a partly closed "
               "dripper line?", "Equal slabs and drippers; closure injected into the measured ratio"],
        ["V6", "How often is a drain onset found, and how long does the computation take?", "Count, wall clock"],
        ["V7", "Can the metered irrigation minus drain serve as a direct check of the sensor scale?",
         "Daily irrigation and drain meters"],
        ["V8", "At the moment drain reaches the drain EC probe, how far is each sensor's reading from its "
               "anchor (raw with P*, one-off commissioning, rolling)?", "Drain EC probe 550, a separate instrument"],
        ["V9", "Does the morning drain deficit predict the litres the slab takes before it drains?",
         "Dose meter 530 and drain EC probe 550, no slab sensor"],
        ["V10", "Do V8 and V9 separate the drain-onset anchor from a field-capacity anchor taken from the "
                "drainage fall after wetting (as P2)?", "As V8 and V9"],
    ], "Table 7: Validation tests", widths=[0.5, 4.2, 2.0], size=9, align_left_cols=(1, 2))
    h2(doc, "8.3 Paired Sensors (V1)")
    para(doc,
         "For each compartment the median absolute difference between the readings of its two sensors over "
         "the second half is given raw, with each sensor's reference fixed from its first-half plateaus, and "
         "with the rolling reference (Table 8, Figure 4(a)). The rolling reference lowers the gap in every "
         "compartment whose sensors disagreed, and leaves the one compartment whose sensors already agreed "
         "unchanged. Figure 4(b) follows the daily gap of AICU, where the raw gap rose above 20 WC %% while "
         "the corrected gap stayed mostly below 5 WC %% once the first onsets had been found. Over the whole "
         "season after the first %d days, the gap falls from %s to %s WC %% in AICU and from %s to %s in "
         "IUA.CAAS." % (W_DAYS, f1(e5["AICU"]["raw"]), f1(e5["AICU"]["anchor"]), f1(e5["IUACAAS"]["raw"]),
                         f1(e5["IUACAAS"]["anchor"])))
    rows = [[LABEL[t], f1(ra["teams"][t]["raw"]), f1(oa[t]["wc_gap_offset_median"]), f1(ra["teams"][t]["rolling"]),
             f1(ra["teams"][t]["raw_p90"]), f1(ra["teams"][t]["rolling_p90"]),
             "%d of %d" % (e2["per_compartment"][t]["anchor_lower"], e2["per_compartment"][t]["of"])] for t in TEAMS]
    rows.append(["Median of compartments", f2(med["raw"]), f2(med["fixed"]), f2(med["rolling"]), "", "",
                 "%d of %d" % (e2["pooled"]["anchor_lower"], e2["pooled"]["of"])])
    table(doc, ["Compartment", "Raw", "Fixed anchor", "Rolling anchor", "Raw p90", "Rolling p90",
                "Days rolling lower"], rows,
          "Table 8: Paired-sensor gap |WC1 - WC2| over the held-out half (WC %)",
          widths=[1.6, 0.7, 0.85, 0.9, 0.75, 0.85, 1.05], size=9, align_left_cols=(0,))
    figure(doc, "fig04.png", "Figure 4: Paired-sensor agreement, sensitivity of the constants and valve decisions",
           "(a) pair gap per compartment; (b) daily pair gap, AICU; (c) median gap for windows and thresholds; "
           "(d) share of daytime intervals with a different valve decision and with a pulse into a draining slab.")
    h2(doc, "8.4 Constants and Daily Comparison (V2)")
    para(doc,
         "Over the nine combinations of window (7, 14, 28 days) and onset threshold (0.2, 0.3, 0.4) the median "
         "pair gap lies between %s and %s WC %% against %s raw (Figure 4(c)); the lowest value came at a "
         "threshold of 0.2 and a 7-day window, but the configured values were kept. Day by day, the "
         "corrected gap is the smaller on %d of %d compartment-days with a difference (sign test z = %s); "
         "in the compartment whose sensors already agreed, %d of %d (z = %s)."
         % (f2(gmin), f2(gmax), f2(ex["E1_raw_gap_median"]), e2["pooled"]["anchor_lower"], e2["pooled"]["of"],
            f2(e2["pooled"]["z"]), e2["per_compartment"]["TheAutomators"]["anchor_lower"],
            e2["per_compartment"]["TheAutomators"]["of"], f2(e2["per_compartment"]["TheAutomators"]["z"])))
    para(doc,
         "Against a one-off commissioning calibration, each sensor's anchor fixed from its first %d days "
         "with an onset and kept for the season, the median paired gap over the held-out half is %s WC %% "
         "against %s WC %% for the rolling anchor; the rolling anchor is lower in %d of the %d compartments, "
         "level in Automatoes (%s and %s) and higher in Digilog (%s against %s), whose second sensor gave "
         "erratic plateaus (Section 8.11). Where the two corrections differ, they lead to different valve "
         "decisions on a median %s %% of daytime intervals."
         % (e6["commissioning_days"], f2(e6["median_commissioning"]), f2(e6["median_rolling"]),
            e6["rolling_lower_in"], len(TEAMS), f1(e6["per_compartment"]["Automatoes"]["commissioning"]),
            f1(e6["per_compartment"]["Automatoes"]["rolling"]), f1(e6["per_compartment"]["Digilog"]["rolling"]),
            f1(e6["per_compartment"]["Digilog"]["commissioning"]),
            pc(e6["decision_mismatch_commissioning_vs_rolling_median"])))
    h2(doc, "8.5 Valve Decisions (V3)")
    para(doc,
         "A set-point rule, pulse when the reading is below S = P* - %d = %s WC %%, was replayed on every "
         "daytime interval of the second half, once on the raw reading of each sensor and once on its "
         "corrected reading (Figure 4(d)). %d of the %d sensors give a different decision on more than 20 %% "
         "of the intervals; the median share is %s %%. The worst sensor, %s %s, reads %s WC %% below its "
         "corrected value on average and decides differently on %s %% of the intervals; on %s %% it calls "
         "for a pulse while its slab, by the corrected reading, is at drainage plateau. The reference reading "
         "here is the corrected one; the test shows the size of the decision change, not an error measured "
         "against slab weight."
         % (SETBACK, f2(cr["setpoint"]), n_bad, len(sens), pc(mm["mismatch"]), LABEL[worst.rsplit("_", 1)[0]],
            "sensor " + worst.rsplit("_", 1)[1], f1(-sens[worst]["offset_mean"]), pc(sens[worst]["mismatch"]),
            pc(sens[worst]["full_slab_irr"])))
    h2(doc, "8.6 Gain, Dry-Back and Delivery (V4, V5)")
    para(doc,
         "In the first half the relative gain of the two sensors by the rise route and by the decline route "
         "was %s / %s (growers' compartment), %s / %s (Automatoes), %s / %s (IUA.CAAS) and %s / %s (The "
         "Automators), and disagreed in AICU (%s / %s) and Digilog (%s / %s) (Figure 5(a)). Over the second "
         "half the median relative gap of the paired overnight dry-back is %s %% raw, %s %% with the gain "
         "always applied and %s %% with the gain applied only where the two 28-day routes agree (Figure "
         "5(b)); the gate is what keeps the gain from doing harm. The gain-free delivery ratio between the "
         "two slabs had a median of %s, %s and %s in three compartments, and %s, %s and %s in the others "
         "(Figure 5(c)); Digilog moved from %s in its first four weeks to %s in its last four. With an "
         "alarm limit of 0.3 (Section 7.7) no alarm was raised in %d section-weeks."
         % (f2(so["Reference"]["G_first_half"]), f2(so["Reference"]["G_decl_first_half"]),
            f2(so["Automatoes"]["G_first_half"]), f2(so["Automatoes"]["G_decl_first_half"]),
            f2(so["IUACAAS"]["G_first_half"]), f2(so["IUACAAS"]["G_decl_first_half"]),
            f2(so["TheAutomators"]["G_first_half"]), f2(so["TheAutomators"]["G_decl_first_half"]),
            f2(so["AICU"]["G_first_half"]), f2(so["AICU"]["G_decl_first_half"]),
            f2(so["Digilog"]["G_first_half"]), f2(so["Digilog"]["G_decl_first_half"]),
            pc(dbm["gap_raw"], 1), pc(dbm["gap_scale_ungated"], 1), pc(dbm["gap_scale_gated"], 1),
            f2(dr["Reference"]["rho_ratio_median"]), f2(dr["Digilog"]["rho_ratio_median"]),
            f2(dr["IUACAAS"]["rho_ratio_median"]), f2(dr["Automatoes"]["rho_ratio_median"]),
            f2(dr["TheAutomators"]["rho_ratio_median"]), f2(dr["AICU"]["rho_ratio_median"]),
            f2(dr["Digilog"]["rho_ratio_first4"]), f2(dr["Digilog"]["rho_ratio_last4"]),
            e7["0.3"]["section_weeks"]))
    para(doc,
         "No dripper fault occurred in the data, so a partial closure was injected into the measured weekly "
         "ratios. A dripper line passing a fraction k of its former flow multiplies the delivered share f of "
         "its slab by k, and with it the ratio, while leaving the gain and the uptake of the plants unchanged "
         "to first order. The closure was started in every week with four clean weeks before it and three "
         "after, in all six compartments and on either slab (%d cases for each k). With L = 0.3 the alarm "
         "was raised within two to four weeks of fault for %s %% of closures of %d %%, %s %% of closures of "
         "%d %% and %s %% of closures of %d %% (median %d weeks), and in none of the same %d windows without "
         "a closure. Closures of %d %% stay inside the week-to-week scatter (%s %% found). With L = 0.2 a "
         "closure of %d %% is found in %s %% of cases but also raises an alarm in %s %% of windows without "
         "a fault."
         % (inj["0.7"]["cases"], pc(inj["0.7"]["rate"]), inj["0.7"]["closed_pct"], pc(inj["0.6"]["rate"]),
            inj["0.6"]["closed_pct"], pc(inj["0.5"]["rate"]), inj["0.5"]["closed_pct"],
            inj["0.6"]["median_weeks_to_alarm"], inj["no_fault"]["windows"], inj["0.9"]["closed_pct"],
            pc(inj["0.9"]["rate"]), e9["by_limit"]["0.2"]["0.7"]["closed_pct"],
            pc(e9["by_limit"]["0.2"]["0.7"]["rate"]), pc(e9["by_limit"]["0.2"]["no_fault"]["rate"])))
    figure(doc, "fig05.png", "Figure 5: Gain routes, dry-back agreement, delivery ratio and drain-onset coverage",
           "(a) relative gain by the two routes, first half; (b) paired dry-back gap; (c) weekly delivery "
           "ratio; (d) share of irrigated days with a detected drain onset for each sensor.")
    h2(doc, "8.7 Coverage, Processing Time and Meter Balance (V6, V7)")
    para(doc,
         "A drain onset was found on %s to %s %% of irrigated days, depending on the sensor (Figure 5(d)); the lowest "
         "values belong to AICU, whose strategy rarely drained the slabs, and the carried reference still "
         "reduced its gap (Table 8). The full computation, onset detection, reference and correction, took "
         "%s ms for each sensor and day on one processor core. A direct check of the sensor scale against the "
         "metered daily irrigation minus drain was attempted and is not used as evidence: the daily drain "
         "meter registers in batches, and the correlation between the metered daily balance and the "
         "sensor's daily fall ranged from %s to %s across the sensors."
         % (pc(min(covs)), pc(max(covs)), f1(tm["ms_per_sensor_day"]), f2(min(uc)), f2(max(uc))))
    h2(doc, "8.8 Check Against the Drain EC Probe and the Dose Meter (V8 to V10)")
    para(doc,
         "V1 to V4 compare sensors with one another. V8 compares them with an instrument that is not a slab "
         "sensor: the drain EC probe of each compartment, logged every 5 minutes by the process computer. "
         "A pulse counts as drained when the probe reading steps by at least %s dS/m within %d minutes. The "
         "label behaves as drain: it fired after %s to %s %% of pulses, after at most %s %% of pulses on days "
         "whose drain meter read zero, and in at most %s %% of quiet intervals without pulses. Over the "
         "held-out half, %d sensor-days had a drained pulse after the first pulse of the day. For each, the "
         "sensor's reading over 30 minutes from that pulse was compared with three anchors: the common "
         "constant P* applied to the raw reading, a one-off commissioning anchor (the sensor's first %d "
         "onset days), and the rolling anchor from the 14 days before (Table 9, which also carries the anchor of V10). None of these anchors used "
         "the probe."
         % (f2(e8["step_dS_m"]), e8["lag_min"], pc(min(lc_pulse)), pc(max(lc_pulse)), pc(lc_zero, 1),
            pc(max(v["quiet"] for v in lc.values()), 1), e8["level_at_cup_onset_n"], e6["commissioning_days"]))
    rows = []
    for t in TEAMS:
        for s_ in (1, 2):
            k = "%s_%d" % (t, s_)
            rows.append(["%s, sensor %d" % (LABEL[t], s_), "%+.1f" % lv["raw"]["per_sensor"][k],
                         "%+.1f" % lv["comm"]["per_sensor"][k], "%+.1f" % p2l["per_sensor"][k],
                         "%+.1f" % lv["roll"]["per_sensor"][k]])
    rows.append(["Median |difference|, all sensor-days", f2(lv["raw"]["pooled_median_abs"]),
                 f2(lv["comm"]["pooled_median_abs"]), f2(p2l["pooled_median_abs"]), f2(lv["roll"]["pooled_median_abs"])])
    rows.append(["Sensors with median within 1 WC %", "%d of %d" % (lv["raw"]["sensors_within_1"], dc["sensors"]),
                 "%d of %d" % (lv["comm"]["sensors_within_1"], dc["sensors"]),
                 "%d of %d" % (p2l["sensors_within_1"], p2l["sensors"]),
                 "%d of %d" % (lv["roll"]["sensors_within_1"], dc["sensors"])])
    table(doc, ["Sensor", "Raw - P*", "Raw - one-off anchor (as P1)", "Raw - drainage-fall anchor (as P2)",
                "Raw - rolling drain-onset anchor"], rows,
          "Table 9: Reading at the first drained pulse of the day (drain EC probe) less each anchor, "
          "held-out half, median of each sensor (WC %)", widths=[2.2, 0.9, 1.2, 1.3, 1.2], size=9, align_left_cols=(0,))
    onsets = [v for t in e8["onset_cup_vs_collapse"].values() for v in t.values()]
    para(doc,
         "With the rolling anchor the reading at physical drain is within 1 WC %% of the anchor for %d of "
         "the %d sensors; with one common constant on the raw reading for %d, and with the one-off "
         "commissioning anchor for %d, because the plateau readings drifted over the season. This checks "
         "the corrected scale at the point that matters for irrigation, the drain, against an instrument "
         "independent of the slab sensors. The drain-onset rule itself found the onset later in the day "
         "than the probe (the median of each sensor %d to %d minutes later), as the rise falls off gradually; the "
         "readings at the two moments differed by a median %s WC %%, since the slab is on its plateau at both."
         % (lv["roll"]["sensors_within_1"], dc["sensors"], lv["raw"]["sensors_within_1"],
            lv["comm"]["sensors_within_1"],
            int(min(-v["time_cup_minus_collapse_min_median"] for v in onsets)),
            int(max(-v["time_cup_minus_collapse_min_median"] for v in onsets)),
            f2(e8["onset_median_abs_diff_over_sensors"])))
    para(doc,
         "V9 checks the deficit in litres. Each morning the slab is refilled by pulses until it drains; the "
         "water dosed from the first pulse of the day up to the first pulse after which the drain EC probe "
         "registers fresh drain is what the slab took up to drainage, its overnight dry-back plus the crop's "
         "uptake during the refill. It comes from the dose meter and the drain EC probe alone, without any "
         "slab sensor and without the daily drain meter. Over %d sensor-days of the held-out half it was a "
         "median %s L/m2 (interquartile range %s to %s). If the drain deficit before the first pulse "
         "measures the water missing from the slab, one scale must link it to those litres on every slab. "
         "Pooled over all sensors, the Spearman correlation between deficit and litres is %s with the "
         "rolling anchor, %s with the one-off commissioning anchor and %s with the common constant P* on "
         "the raw reading; resampling the %d days, the rise in correlation from the raw reading to the rolling anchor lies "
         "between %s and %s (95 %% interval) and from the commissioning anchor between %s and %s. Within one "
         "sensor, where the offset plays no part, the correlation is weaker (median %s, range %s to %s), as "
         "pulse size and uptake vary from day to day. Litres per WC %% of deficit, taken for each sensor, "
         "give a third route to the relative gain of a pair: it lies within 15 %% of the rise route in %d of "
         "%d compartments and on the same side of 1 in %d."
         % (e10["n_sensor_days"], f2(e10["V_median"]), f2(e10["V_iqr"][0]), f2(e10["V_iqr"][1]),
            f2(lp["roll"]), f2(lp["comm"]), f2(lp["raw"]), e10["n_days"],
            f2(e10["boot_roll_minus_raw_ci95"][0]), f2(e10["boot_roll_minus_raw_ci95"][1]),
            f2(e10["boot_roll_minus_comm_ci95"][0]), f2(e10["boot_roll_minus_comm_ci95"][1]),
            f2(e10["per_sensor_spearman_median"]), f2(e10["per_sensor_spearman_range"][0]),
            f2(e10["per_sensor_spearman_range"][1]), e10["litre_gain_within_15pct_of_rise"],
            e10["litre_gain_compartments"], e10["litre_gain_same_side_of_1_as_rise"]))
    para(doc,
         "V10 applies both checks to an anchor of the kind P2 describes: for each sensor and day, the "
         "reading at which the fast fall after the last pulse of the day gives way to the slower fall of "
         "uptake (fall over 30 minutes below %s of its peak, peak of at least %s WC %% per 30 minutes), "
         "renewed as the median of the past %d days exactly as the drain-onset anchor. At physical drain it "
         "lay a median %s WC %% from the reading, with %d of %d sensors within 1 WC %% (Table 9), against %s "
         "WC %% and %d of %d for the drain-onset anchor; its morning deficit ranked the litres dosed until "
         "drain with a Spearman correlation of %s against %s (95 %% interval of the difference %s to %s over "
         "the days). Both anchors remove most of the offset between the two sensors of a compartment "
         "(median paired gap %s and %s WC %%); they differ in what the anchor means, and only the drain onset "
         "of the refill places it at the drainage of the slab."
         % (f1(e11["FRAC"]), f1(e11["R0_MIN"]), W_DAYS, f2(p2l["pooled_median_abs"]), p2l["sensors_within_1"],
            p2l["sensors"], f2(onl["pooled_median_abs"]), onl["sensors_within_1"], onl["sensors"],
            f2(e11["litres_spearman"]["p2"]), f2(e11["litres_spearman"]["onset"]),
            f2(e11["litres_onset_minus_p2_ci95"][0]), f2(e11["litres_onset_minus_p2_ci95"][1]),
            f2(e11["pair_gap_median"]["p2"]), f2(e11["pair_gap_median"]["onset"])))
    h2(doc, "8.9 Technical Effect Summary")
    table(doc, ["Effect", "Mechanism", "Evidence"], [
        ["Corrected reading meets the physical drain", "Deficit to the slab's own drain onset, rolling anchor",
         "Table 9: %s WC %% rolling vs %s commissioning vs %s raw; %d of %d sensors within 1 WC %%"
         % (f2(lv["roll"]["pooled_median_abs"]), f2(lv["comm"]["pooled_median_abs"]),
            f2(lv["raw"]["pooled_median_abs"]), lv["roll"]["sensors_within_1"], dc["sensors"])],
        ["Anchor placed at the slab's drainage, unlike a drainage-fall anchor (P2)",
         "Collapse of the refill response instead of the fall after wetting",
         "Table 9: %s vs %s WC %%; %d vs %d sensors within 1 WC %%"
         % (f2(onl["pooled_median_abs"]), f2(p2l["pooled_median_abs"]), onl["sensors_within_1"], p2l["sensors_within_1"])],
        ["Deficit follows the metered water to drain", "Deficit to the slab's own drain onset, rolling anchor",
         "Section 8.8 (V9): Spearman %s rolling vs %s commissioning vs %s raw with P*"
         % (f2(lp["roll"]), f2(lp["comm"]), f2(lp["raw"]))],
        ["Sensors of one substrate type read alike", "Drain-onset plateau, rolling reference",
         "Table 8: median gap %s -> %s WC %%; %d of %d days lower (z = %s)"
         % (f2(med["raw"]), f2(med["rolling"]), e2["pooled"]["anchor_lower"], e2["pooled"]["of"], f2(e2["pooled"]["z"]))],
        ["Reference follows drift", "Past-days median instead of one-off calibration",
         "Table 8: fixed %s vs rolling %s WC %%; Section 8.4: commissioning anchor %s WC %%"
         % (f2(med["fixed"]), f2(med["rolling"]), f2(e6["median_commissioning"]))],
        ["Valve acts on the distance from drainage", "Set-point on the drain deficit",
         "Section 8.5: %d of %d sensors > 20 %% decisions changed; median %s %% pulses into draining slabs"
         % (n_bad, len(sens), pc(mm["full_slab_irr"]))],
        ["Constants not critical", "Onset as a fraction of the same day's rise", "Figure 4(c): %s-%s WC %%" % (f2(gmin), f2(gmax))],
        ["Gain correction without harm", "Two-route agreement gate",
         "Section 8.6: dry-back gap %s %% raw, %s %% gated, %s %% ungated"
         % (pc(dbm["gap_raw"], 1), pc(dbm["gap_scale_gated"], 1), pc(dbm["gap_scale_ungated"], 1))],
        ["Partly closed dripper line found without a gain", "Delivery ratio, alarm limit L = 0.3",
         "Section 8.6: %s %% of injected %d %% closures within 2-4 weeks; 0 of %d fault-free windows"
         % (pc(inj["0.6"]["rate"]), inj["0.6"]["closed_pct"], inj["no_fault"]["windows"])],
    ], "Table 10: Technical effects, mechanism and evidence", widths=[1.9, 2.3, 2.5], size=9, align_left_cols=(0, 1, 2))
    h2(doc, "8.10 Insights")
    bullets(doc, [
        "Offsets dominate the disagreement between slab sensors: the offset correction alone removes most of "
        "it, and the drain onset fixes the offset because it is a property of the slab, not of the sensor.",
        "The offset drifts over a season (Figure 3(c)); a reference fixed from the first half leaves %s WC %% "
        "against %s WC %% for a reference renewed every day." % (f2(med["fixed"]), f2(med["rolling"])),
        "Gain errors exist and two independent routes find the same value where both are clean, but a "
        "gain applied from one route alone degrades the dry-back."])
    h2(doc, "8.11 Limitations and Acceptance Criteria")
    bullets(doc, [
        "The drain EC probe checks the corrected scale at the drain point (Section 8.8, V8); over the "
        "dry-back the deficit is checked only against the litres dosed until drain (V9), which include the "
        "crop's uptake during the refill and correlate with it moderately within one sensor. No slab-weight "
        "measurement was available. Acceptance: on a section with a gutter-weighing scale, the "
        "deficit times the slab volume must match the weighed water loss within the gain gate.",
        "The plateau readings of both sensors of a compartment fell over the season (Figure 3(c)); whether "
        "the drained slab truly held less water as roots filled it, or both sensors drifted, cannot be "
        "separated without slab weights. The valve decision on the deficit does not depend on it, since in "
        "both cases the slab drains at its current plateau; only the common-scale display (claim 2) does.",
        "The pre-pulse reading alone separates drained from undrained pulses weakly for every anchor "
        "(area under the curve %s raw, %s rolling): whether a pulse drains also depends on its volume and on "
        "the delay of the gutter. The check of Section 8.8 therefore uses the first drained pulse of the day."
        % (f2(e8["pre_pulse_auc_not_used"]["raw"]), f2(e8["pre_pulse_auc_not_used"]["rolling"])),
        "The method needs days on which the slab drains; in a section kept below drainage for weeks the "
        "reference is carried unchanged (AICU found onsets on %s %% of days for one sensor)." % pc(min(covs)),
        "One sensor (Digilog, sensor 2) showed plateaus that jumped from day to day (standard deviation of "
        "the daily change %s WC %%); its correction was the weakest. Acceptance: a sensor whose plateau "
        "varies by more than a set limit is flagged for inspection rather than corrected."
        % f1(cov["Digilog"]["2"]["day_to_day_sd"]),
        "No dripper fault was recorded in the data; the detection rates of Section 8.6 come from closures "
        "injected into the measured ratio at first order, which leaves out the further drying of the "
        "under-watered slab. Acceptance: a dripper line of a monitored slab physically closed by %d %% for "
        "three weeks must raise the alarm." % inj["0.6"]["closed_pct"],
        "Evaluated on six compartments of one facility and one stone wool product; coir and other mineral "
        "wool products need their own constants, and their own P* where the common scale is used."])

    # ============================================================== 9
    h1(doc, "9. Discussion")
    para(doc,
         "The invention gives every slab sensor a reference that the slab itself provides each day. The "
         "moment a slab starts to drain shows in the sensor's own response to the pulses that the crop "
         "receives anyway. Anchoring each sensor there, refreshing the anchor from past days, and steering "
         "the valve on the deficit to that anchor turns readings that differ by up to %s WC %% into deficits "
         "that differ by about 1 to 2 WC %%, and a separate instrument, the drain EC probe, finds the "
         "reading at physical drain within %s WC %% of the anchor (median); the morning deficit ranks the "
         "litres the slab takes before it drains better than either fixed anchor. The results also mark the "
         "boundary: the size of a deficit in litres rests on the gain until slab weights confirm it, and a "
         "gain correction is applied only where two physical routes agree."
         % (f1(gaps_raw_sorted[-1]), f2(lv["roll"]["pooled_median_abs"])))

    # ============================================================== 10
    h1(doc, "10. What Aspect(s) of the Invention Need(s) Protection?")
    bullets(doc, [
        "Detecting the drain onset of a substrate slab from the collapse of the rise of its sensor reading "
        "per routine irrigation pulse, relative to the same day's first pulses.",
        "A reference plateau reading for each sensor renewed from its past days' drain-onset readings only.",
        "Opening or holding the irrigation valve on the deficit of each reading to its own slab's drain "
        "onset, free of the sensor's offset and of any assumption that slabs drain at one water content.",
        "Checking each sensor against the drain EC probe of the gutter at the first drained pulse of the day.",
        "A relative gain correction applied only when the rise-per-litre route and the daily-decline route "
        "agree.",
        "A gain-free delivery ratio between slabs with an alarm on drift."])
    figure(doc, "fig06.png", "Figure 6: Claim tree",
           "Independent method claim 1, its dependents 2 to 6, and system claim 7 carrying out the method.")
    h2(doc, "Claims")
    CLAIMS(doc)

    # ============================================================== 11
    h1(doc, "11. Technology Readiness Level of the Invention")
    para(doc,
         "The method runs end to end on the recorded sensor readings and pulse logs of six operating "
         "greenhouse compartments; it has not yet been connected to an irrigation valve in a greenhouse.")
    trl_table(doc)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    B._run(p, "END OF THE DOCUMENT", size=11, bold=True)
    p.alignment = 1
    return doc, num


TITLE = ("System and Method for Recalibrating Substrate Water-Content Sensors from the Drain Onset of "
         "their Slabs and Controlling the Irrigation Valve on the Corrected Reading")


def CLAIMS(doc):
    """One independent method claim, five dependents, one system claim. Claim 1 carries the physical chain
    without numbers; the operating constants sit in claim 3, as tested ranges and as the configured values."""
    section = (
        "an irrigation section (100) of a greenhouse comprising plant-growth substrate slabs (150) of one "
        "substrate type, an irrigation valve or pump (510) that delivers nutrient solution to the slabs "
        "through drippers in pulses, a dose meter (530) that registers the volume of each pulse, and at "
        "least two dielectric water-content sensors (110, 120), each inserted in a different slab of the "
        "section and reporting a water-content reading")
    claim(doc, 1,
          "A method of controlling the irrigation of plants grown in " + section + ", the method being "
          "carried out by a data-processing system (900) connected to the sensors and to the valve or pump, "
          "and comprising: "
          "(a) delivering irrigation pulses to the slabs through the valve or pump during the day, and "
          "receiving the reading of each sensor at successive sampling intervals and the volume of each "
          "pulse from the dose meter; "
          "(b) determining, for each sensor, the response of its reading to each pulse, being the rise of "
          "the reading caused by that pulse; "
          "(c) detecting, for each sensor and each day, a collapse of that response, being the first pulse "
          "of the day whose rise has fallen below a fraction of the rise caused by earlier pulses of the "
          "same day, and taking that pulse as the drain onset of the slab of that sensor, at which the slab "
          "has reached its drainage plateau and further water passes to drain, the collapse being judged "
          "relative to the same sensor's own earlier rises so that it does not depend on the scale or the "
          "offset of the sensor; "
          "(d) recording, for each sensor and each day with a drain onset, a sensor-specific daily plateau "
          "reading, being the reading of that sensor following the drain onset of its own slab; "
          "(e) storing the daily plateau readings of each sensor in a reference memory and computing, for "
          "each sensor and each day, a rolling reference plateau reading from the daily plateau readings of "
          "that sensor on preceding days only; "
          "(f) computing at each sampling interval a drain deficit of each sensor as its rolling reference "
          "plateau reading less its current reading, whereby the offset of the sensor cancels and the "
          "deficit measures how far the slab of that sensor is from its own drainage plateau, without "
          "assuming that different slabs drain at the same water content; and "
          "(g) opening the valve or starting the pump (510) to deliver a further pulse to the section when a "
          "drain deficit of the section, being the drain deficit of one of its sensors or a combination of "
          "the drain deficits of its sensors, exceeds a set-point, and otherwise keeping the valve closed or "
          "the pump stopped.", independent=True)
    claim(doc, 2,
          "The method of claim 1, further comprising computing a corrected reading of each sensor as a "
          "plateau constant common to all sensors in slabs of that substrate type less its drain deficit, "
          "the plateau constant being the median of the daily plateau readings of the sensors of one or more "
          "irrigation sections with slabs of that substrate type over a commissioning period, and the "
          "set-point of step (g) being expressed as that constant less the set-point.")
    claim(doc, 3,
          "The method of claim 1 or claim 2, wherein the earlier pulses of step (c) are a number of first "
          "pulses of the day and the fraction lies between %s and %s of their median rise, preferably %d "
          "pulses and %s; the daily plateau reading is the reading over a period following the drain onset, "
          "preferably %d minutes; the rolling reference plateau reading is the median of the daily plateau "
          "readings in a window of %d to %d days before the current day, preferably %d days, renewed only "
          "when the window holds at least %d daily plateau readings, the previous reference being kept "
          "otherwise; and the rise is the largest reading in the %d sampling intervals beginning with the "
          "pulse less the reading in the interval before the pulse."
          % (f1(min(THRS)), f1(max(THRS)), N_FIRST, f1(THR), PLAT_MIN, min(WINS), max(WINS), W_DAYS, MIN_DAYS,
             RISE_WIN))
    claim(doc, 4,
          "The method of any one of claims 1 to 3, further comprising estimating a relative gain of a second "
          "sensor with respect to a first sensor of the section by two physically independent routes, (i) a "
          "filling route, as the ratio of their summed rises per summed pulse volume over pulses delivered "
          "before the drain onset, and (ii) an uptake route, as the ratio of their mean daily falls of "
          "reading between pulses; comparing the two estimates; and dividing the drain deficit of the second "
          "sensor by the relative gain before step (g) only when the two estimates agree within a "
          "predetermined tolerance, the drain deficit being left uncorrected for gain otherwise, whereby a "
          "gain estimate distorted on one route, by uneven dripper delivery on the filling route or by "
          "uneven crop uptake on the uptake route, is not applied to the valve decision; the daily dry-back "
          "of each slab, being its largest drain deficit before the first pulse of the next day, being "
          "computed from the deficits so corrected.")
    claim(doc, 5,
          "The method of any one of claims 1 to 4, further comprising computing for each sensor a delivery "
          "ratio, being its summed rises per summed pulse volume before the drain onset divided by its mean "
          "daily fall of reading, both over the same week; computing the ratio of the delivery ratios of two "
          "sensors of the section; and issuing a delivery alarm signal (430) when that ratio departs from "
          "one by more than a predetermined limit.")
    claim(doc, 6,
          "The method of any one of claims 1 to 5, wherein the gutter (170) of the section carries a drain "
          "conductivity probe (550), the method further comprising: receiving the reading of the probe at "
          "the sampling intervals; marking a pulse as drained when the probe reading changes by at least a "
          "predetermined step within a predetermined time after the pulse; recording, for each sensor and "
          "each day, its drain deficit at the first drained pulse of that day after the day's first pulse; "
          "and issuing a sensor check signal (440) for a sensor when the median of the deficits so recorded "
          "over the window departs from zero by more than a predetermined limit.")
    claim(doc, 7,
          "A system for controlling the irrigation of plants, comprising " + section + "; and a "
          "data-processing system (900) comprising: "
          "(i) a sensor input (210) connected to each water-content sensor and receiving its reading at "
          "successive sampling intervals; "
          "(ii) a pulse-volume input (220) connected to the dose meter (530) and receiving the volume of each "
          "pulse delivered by the valve or pump; "
          "(iii) a pulse-response unit (310) connected to both inputs that computes, for each sensor, the "
          "rise of its reading caused by each pulse; "
          "(iv) a drain-onset unit (320) that detects, for each sensor and each day, the pulse at which the "
          "rise collapses relative to the earlier rises of the same sensor on that day, and records the "
          "sensor's reading following that pulse as its daily plateau reading; "
          "(v) a reference memory (330) that holds, for each sensor, its daily plateau readings of the "
          "preceding days and supplies a rolling reference plateau reading computed from them only; "
          "(vi) a deficit unit (350) that computes at each sampling interval the drain deficit of each sensor "
          "as its rolling reference plateau reading less its current reading; and "
          "(vii) a valve-control output (410, 420) connected to the valve or pump (510) that opens the valve "
          "or starts the pump to deliver a pulse when a drain deficit of the section exceeds a set-point, "
          "and keeps it closed or stopped otherwise; "
          "the data-processing system being configured to carry out the method of any one of claims 1 to 6.",
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
    for p in doc.paragraphs:
        if p._p.xpath(".//w:drawing"):
            p.paragraph_format.keep_with_next = True
    doc.save(OUT)
    print("wrote", OUT)
    check(OUT, num)
