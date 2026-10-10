"""Phase 0 probe: does the soil-water storage gain after each rain event match the rain? NEON STER 2023."""
import glob, json, os
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
D = os.path.join(ROOT, "data", "neon")

# depths (m) from sensor_positions zOffset; VER 501 is at the profile head, taken as 0.02 m
DEPTH = {501: 0.02, 502: 0.06, 503: 0.16, 504: 0.26, 505: 0.46, 506: 0.86, 507: 1.06, 508: 1.36}


def load_swc(qf=True):
    rows = []
    for f in glob.glob(os.path.join(D, "DP1.00094.001", "STER", "*", "*SWS_30_minute*.csv")):
        parts = os.path.basename(f).split(".")
        hor, ver = int(parts[6]), int(parts[7])
        d = pd.read_csv(f, usecols=["startDateTime", "VSWCMean", "VSWCFinalQF"])
        if qf:
            d = d[d.VSWCFinalQF == 0]
        d["plot"], d["ver"] = hor, ver
        rows.append(d)
    x = pd.concat(rows)
    x["t"] = pd.to_datetime(x.startDateTime)
    return x.pivot_table(index="t", columns=["plot", "ver"], values="VSWCMean")


def load_rain():
    fs = [f for f in glob.glob(os.path.join(D, "DP1.00045.001", "STER", "*", "*TIPPRE_30min*basic*.csv"))]
    r = pd.concat(pd.read_csv(f, usecols=["startDateTime", "precipBulk"]) for f in fs)
    r["t"] = pd.to_datetime(r.startDateTime)
    return r.set_index("t").precipBulk.sort_index()


def storage(sw, plot, vers, zmax):
    """Profile storage (mm) to zmax by trapezoid-style layer thickness around each sensor depth."""
    z = np.array([DEPTH[v] for v in vers])
    edges = np.concatenate([[0], (z[1:] + z[:-1]) / 2, [zmax]])
    th = np.diff(edges) * 1000
    return (sw[[(plot, v) for v in vers]] * th).sum(axis=1, min_count=len(vers))


def events(rain, gap_h=12, min_mm=5):
    wet = rain[rain > 0]
    ev, cur = [], None
    for t, v in wet.items():
        if cur and (t - cur[1]).total_seconds() <= gap_h * 3600:
            cur = [cur[0], t, cur[2] + v]
        else:
            if cur: ev.append(cur)
            cur = [t, t, v]
    if cur: ev.append(cur)
    return [e for e in ev if e[2] >= min_mm]


def main():
    sw, rain = load_swc(), load_rain()
    vers = [501, 502, 503, 504, 505]          # to 0.66 m
    out = []
    for t0, t1, p in events(rain):
        for plot in range(1, 6):
            try:
                s = storage(sw, plot, vers, 0.66)
            except KeyError:
                continue
            before = s[t0 - pd.Timedelta("2h"):t0].mean()
            after = s[t1 + pd.Timedelta("4h"):t1 + pd.Timedelta("8h")].mean()
            if np.isfinite(before) and np.isfinite(after):
                out.append(dict(start=str(t0), rain_mm=round(p, 1), plot=plot,
                                dS_mm=round(after - before, 1), ratio=round((after - before) / p, 2)))
    o = pd.DataFrame(out)
    print(o.to_string())
    summ = o.groupby("plot").ratio.describe()
    print(summ)
    json.dump(dict(events=out, note="ratio = storage gain to 0.66 m (4-8 h after rain) / tipping-bucket rain"),
              open(os.path.join(ROOT, "results", "probe_rain_storage.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
