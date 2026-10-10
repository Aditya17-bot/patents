"""Phase 0 probe: night-time redistribution conserves profile water -> relative sensor gains.
For each rain-free night (local 22:00-05:00) after a rain event, sum_i g_i * dz_i * dtheta_i ~ 0 (no ET, no
drainage past the deepest sensor). Fit g (top sensor fixed to 1) by least squares; check stability across halves."""
import os, json
import numpy as np, pandas as pd
from probe_rain_storage import load_swc, load_rain, DEPTH, events

ROOT = os.path.join(os.path.dirname(__file__), "..")


def nights(sw, rain, plot, vers, days_after=6):
    z = np.array([DEPTH[v] for v in vers])
    edges = np.concatenate([[0], (z[1:] + z[:-1]) / 2, [z[-1] + (z[-1] - z[-2]) / 2]])
    dz = np.diff(edges) * 1000
    rows = []
    for t0, t1, p in events(rain, min_mm=3):
        for k in range(days_after):
            # STER is UTC-7: local 22:00-05:00 = 05:00-12:00 UTC next day
            day = (t1 + pd.Timedelta(days=k)).normalize()
            a, b = day + pd.Timedelta("1D5h"), day + pd.Timedelta("1D12h")
            if rain[a - pd.Timedelta("3h"):b].sum() > 0:
                continue
            seg = sw.loc[a:b, [(plot, v) for v in vers]]
            if len(seg) < 12 or seg.isna().any().any():
                continue
            d = (seg.iloc[-3:].mean() - seg.iloc[:3].mean()).values * dz
            rows.append(d)
    return np.array(rows), dz


def fit(D):
    # minimise |D g|^2 with g0 = 1 -> D[:,1:] g' = -D[:,0]
    A, b = D[:, 1:], -D[:, 0]
    g, *_ = np.linalg.lstsq(A, b, rcond=None)
    return np.concatenate([[1.0], g])


def main():
    sw, rain = load_swc(qf=False), load_rain()
    out = {}
    for plot in range(1, 6):
        good = [v for v in range(501, 509) if (plot, v) in sw.columns and sw[(plot, v)].notna().mean() > 0.3]
        vers = [v for v in good if DEPTH[v] <= 0.5]
        if len(vers) < 3:
            continue
        D, dz = nights(sw, rain, plot, vers)
        if len(D) < 2 * len(vers):
            print(plot, vers, "nights", len(D), "too few"); continue
        g = fit(D)
        h = len(D) // 2
        g1, g2 = fit(D[:h]), fit(D[h:])
        raw_net = np.abs(D.sum(1)).mean(); fit_net = np.abs(D @ g).mean(); move = np.abs(D).sum(1).mean() / 2
        out[plot] = dict(vers=vers, n=len(D), gain=g.round(2).tolist(), gain_half1=g1.round(2).tolist(),
                         gain_half2=g2.round(2).tolist(), mean_abs_net_raw_mm=round(raw_net, 2),
                         mean_abs_net_fit_mm=round(fit_net, 2), mean_redistributed_mm=round(move, 2))
        print(plot, out[plot])
    json.dump(out, open(os.path.join(ROOT, "results", "probe_night_conservation.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
