"""Sections 8.8 (Indian gauge sites, V8) and 8.9 (station-level uncertainty, hold-out and
sensitivity, V9) of the IDF-B, kept in their own module so make_idfb.py stays readable."""

FT = 0.3048


def f1(x):
    return "%.1f" % x


def f2(x):
    return "%.2f" % x


def m3(ft):
    return "%.3f m" % (FT * ft)


def basins_text(e8):
    b = list(e8["basins"])
    return ", ".join(b[:-1]) + " and " + b[-1] if len(b) > 1 else b[0]


def india_section(doc, h2, para, figure, e8, e9, pub, BIG, var, ho):
    adm = e8["admitted"]
    lags = sorted({abs(r["lag"]) for r in adm})
    cmax = max(r["coupling"] for r in adm)
    fi, fu = e8["india_floor"], e8["us_floor_upper"]
    h2(doc, "8.8 Indian Gauge Sites (V8)")
    para(doc,
         "The CAMELS-IND data set (Mangukiya et al., Earth System Science Data 17, 461, 2025) "
         "gives the observed daily discharge of %d gauge sites of the Central Water Commission "
         "for 1980-2020, with the river each site stands on and its drainage area; it carries "
         "no stage record, so only the steps of the method that use discharge were run on it. "
         "Ordering the sites on each river by drainage area gives %d consecutive pairs, %d of "
         "them with an area increment of 20 %% or less. %d pairs (%d directions) in the %s "
         "basins pass the admission test of claim 3, with travel-time lags of %d to %d days and "
         "coupling up to %s (Figure 6(a), 6(b))."
         % (e8["stations_with_flow"], e8["same_river_consecutive_pairs"], e8["pairs_incr_ok"],
            e8["admitted_pairs"], e8["admitted_directions"], basins_text(e8), lags[0], lags[-1],
            "%.3f" % cmax))
    para(doc,
         "Over one interval between visits (%d days), the neighbour's log ratio on these Indian "
         "pairs departs from its linear interpolation by a median of %s %% of discharge (90th "
         "percentile %s %%), against %s %% (%s %%) on the admitted United States pairs (Figure "
         "6(c)). The United States figure includes the real offset departures that the "
         "method detects, so it is an upper bound on the noise there. The Indian network "
         "therefore offers admissible neighbours with a departure noise about %s times larger; "
         "the departures that dominate the error (mean %s %% at departures of %s or more, "
         "Table 8) are larger than that median, and the gain learned per station limits how "
         "much of the smaller departures is applied. Whether the method lowers the error of "
         "Indian records remains to be shown with their stage records (Section 8.12)."
         % (e8["gap_days"], f1(100 * fi["median"]), f1(100 * fi["p90"]), f1(100 * fu["median"]),
            f1(100 * fu["p90"]), f1(fi["median"] / fu["median"]), f1(pub["big"]["baseline"]["mean"]),
            m3(BIG)))

    h2(doc, "8.9 Station-Level Uncertainty, Hold-Out and Sensitivity (V9)")
    a, o, b, bs = e9["e1_all"], e9["e1_open_water"], e9["e1_big"], e9["e1_vs_practice"]
    rta, ra, rb = e9["e1_rt_all"], e9["e2_rt_all"], e9["e2_rt_big"]
    sa, sb = e9["sensitivity_range_all"], e9["sensitivity_range_big"]
    para(doc,
         "Visits at one station are not independent, so the main effects were recomputed after "
         "resampling whole stations with replacement (%d draws). For the record between visits "
         "the mean error falls by %s points (95 %% interval %s to %s) over all visits, by %s "
         "points (%s to %s) in open water, and by %s points (%s to %s) where the control moved "
         "by %s or more, where %d of the %d stations with at least five such visits improve; "
         "against the practice chosen per station, over all visits, the reduction is %s "
         "points (%s to %s), and with the neighbour's record rebuilt from its own visits it is "
         "%s points (%s to %s). With the neighbour computed as in real time the record's interval "
         "over all visits is %s to %s points, which includes zero. In real time the reduction "
         "is %s points (%s to %s) over all visits and %s points (%s to %s) where the offset "
         "changed (Figure 6(d))."
         % (e9["B"], f1(a["reduction_pts"]), f1(a["ci95"][0]), f1(a["ci95"][1]),
            f1(o["reduction_pts"]), f1(o["ci95"][0]), f1(o["ci95"][1]),
            f1(b["reduction_pts"]), f1(b["ci95"][0]), f1(b["ci95"][1]), m3(BIG),
            b["stations_better"], b["stations_with_5plus"],
            f1(bs["reduction_pts"]), f1(bs["ci95"][0]), f1(bs["ci95"][1]),
            f1(e9["e1_ip_all"]["reduction_pts"]), f1(e9["e1_ip_all"]["ci95"][0]), f1(e9["e1_ip_all"]["ci95"][1]),
            f1(rta["ci95"][0]), f1(rta["ci95"][1]),
            f1(ra["reduction_pts"]), f1(ra["ci95"][0]), f1(ra["ci95"][1]),
            f1(rb["reduction_pts"]), f1(rb["ci95"][0]), f1(rb["ci95"][1])))
    h1_, h2_ = ho["first"], ho["second"]
    para(doc,
         "With every constant frozen, the stations were sorted by number and dealt into two "
         "halves. On the first (%d stations, %d visits) the mean error falls from %s %% to %s %% "
         "(z = %s); on the second (%d stations, %d visits) from %s %% to %s %% (z = %s)."
         % (h1_["stations"], h1_["n"], f1(h1_["all"][0]), f1(h1_["all"][1]), f2(h1_["all_paired"]["z"]),
            h2_["stations"], h2_["n"], f1(h2_["all"][0]), f1(h2_["all"][1]), f2(h2_["all_paired"]["z"])))
    names = {"coupling": "coupling threshold %.2f", "window_days": "windows of %d days",
             "steady_ft": None}
    parts = []
    for v in var:
        if v["what"] == "steady_ft":
            lab = "steadiness threshold %s" % m3(v["value"])
        else:
            lab = names[v["what"]] % v["value"]
        parts.append("%s: %s %% to %s %% (z = %s)" % (lab, f1(v["all"][0]), f1(v["all"][1]),
                                                      f2(v["all_paired"]["z"])))
    para(doc,
         "Changing one constant at a time, each run rescoring the visits it admits, the mean "
         "error over all visits moves as follows (linear interpolation to the method): %s. "
         "Setting the gain prior anywhere from 0 to 0.75 and the number of visits before a "
         "station's own gain is used anywhere from 3 to 8 keeps the method's mean error between "
         "%s %% and %s %% over all visits and between %s %% and %s %% at departures of %s or "
         "more." % ("; ".join(parts), f1(sa[0]), f1(sa[1]), f1(sb[0]), f1(sb[1]), m3(BIG)))
    figure(doc, "fig06.png",
           "Figure 6: Indian gauge sites and station-level uncertainty",
           "(a) CWC gauge sites of CAMELS-IND with the admitted pairs; (b) coupling against area "
           "increment for Indian and United States pairs, admitted region shaded; (c) noise "
           "floor of the neighbour departure over one visit interval; (d) reduction of mean "
           "error with 95 % intervals from resampling whole stations.")
