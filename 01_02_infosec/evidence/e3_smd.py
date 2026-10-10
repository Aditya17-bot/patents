"""
E3(i) -- cross-station residual commensurability, Server Machine Dataset (SMD).

Question under test (Label-Free disclosure, Sec 4.1(a)+(c), Claims 11/17):

  Does applying ONE normal-only predictive model, by independent per-station
  inference, to physically separate and independently instrumented stations
  render their residual series COMMENSURABLE -- so that a decision threshold
  calibrated at one station holds at another -- where per-station models,
  trained on the same data with the same architecture, do not?

Design
  corpus     SMD, 28 server entities x 38 channels, MIT licence.
             train split is anomaly-free by construction.
  split      GROUP-DISJOINT. Shared model sees groups 1 and 2 only (17 entities).
             All commensurability measurement happens on group 3 (11 entities),
             which the shared model never saw during training.
  control    PER-STATION condition trains one model per held-out entity on that
             entity's own normal data. Same architecture, same optimiser, same
             epochs, same normalisation. The ONLY difference is shared vs local
             parameters, so any gap is attributable to parameter sharing alone.
  residual   one-step-ahead prediction error, giving a residual value per
             timestep (needed downstream for lagged cross-station coupling).

Primary metric -- THRESHOLD TRANSFER
  tau_A := q-th percentile of station A residuals on A calibration normals.
  Apply tau_A to station B held-out normals; record realised exceedance rate.
  Commensurable  => realised rate ~= nominal (1 - q) for every ordered pair.
  Not            => realised rate scatters over orders of magnitude.
  Reported as median and IQR of realised FPR over all ordered pairs A != B.

Secondary metric -- DISTRIBUTIONAL ALIGNMENT
  two-sample Kolmogorov-Smirnov statistic between the held-out normal residual
  distributions of each station pair.

Guard -- DETECTION IS NOT SACRIFICED
  per-entity AUROC on the labelled test split, both conditions. Sharing must not
  be bought with accuracy.

Honest-reporting note: SMD ships per-entity min-max normalised to [0,1]. That
preprocessing is identical in both conditions, so it cannot explain a gap
between them, but it does mean the absolute commensurability of the shared
condition is measured on top of a per-station scaling step. Stated in results.
"""

import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn

SEED = 0
W = int(os.environ.get("E3_W", 20))          # window length, timesteps
HID = int(os.environ.get("E3_HID", 128))
EPOCHS = int(os.environ.get("E3_EPOCHS", 5))
BATCH = 512
LR = 1e-3
CALIB_FRAC = 0.70      # of each entity normal split: calibrate on first 70%
NOMINAL_FPR = 0.01     # threshold set at the 99th percentile
DEV = torch.device("cpu")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
TAG = os.environ.get("E3_TAG", "")
SMD = os.environ.get(
    "SMD_DIR",
    "C:/Users/rober/AppData/Local/Temp/claude/C--adi-patent-InfoSec"
    "/68b582ab-0783-46c4-a7c2-0d02d46c0bdd/scratchpad/ds/omni/ServerMachineDataset",
)


def entities():
    names = sorted(
        f[:-4] for f in os.listdir(os.path.join(SMD, "train")) if f.endswith(".txt")
    )
    train_group = [n for n in names if n.startswith(("machine-1-", "machine-2-"))]
    holdout = [n for n in names if n.startswith("machine-3-")]
    return train_group, holdout


def load(name):
    def p(sub):
        return os.path.join(SMD, sub, name + ".txt")
    tr = np.genfromtxt(p("train"), delimiter=",", dtype=np.float32)
    te = np.genfromtxt(p("test"), delimiter=",", dtype=np.float32)
    lb = np.genfromtxt(p("test_label"), delimiter=",", dtype=np.float32)
    return tr, te, lb


def windowize(x):
    """x (T,D) -> X (T-W, W*D) past windows, Y (T-W, D) next step."""
    T, D = x.shape
    n = T - W
    X = np.empty((n, W * D), dtype=np.float32)
    for i in range(n):
        X[i] = x[i:i + W].ravel()
    return X, x[W:]


class Predictor(nn.Module):
    def __init__(self, d_in, d_out):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, HID), nn.ReLU(),
            nn.Linear(HID, HID), nn.ReLU(),
            nn.Linear(HID, d_out),
        )

    def forward(self, x):
        return self.net(x)


def fit(X, Y, seed, epochs=EPOCHS, tag=""):
    torch.manual_seed(seed)
    m = Predictor(X.shape[1], Y.shape[1]).to(DEV)
    opt = torch.optim.Adam(m.parameters(), lr=LR)
    lossf = nn.MSELoss()
    Xt = torch.from_numpy(X)
    Yt = torch.from_numpy(Y)
    n = len(Xt)
    g = torch.Generator().manual_seed(seed)
    for ep in range(epochs):
        perm = torch.randperm(n, generator=g)
        tot = 0.0
        for i in range(0, n, BATCH):
            idx = perm[i:i + BATCH]
            opt.zero_grad()
            loss = lossf(m(Xt[idx]), Yt[idx])
            loss.backward()
            opt.step()
            tot += loss.item() * len(idx)
        if tag:
            print("    %s epoch %d/%d mse %.6f" % (tag, ep + 1, epochs, tot / n),
                  flush=True)
    m.eval()
    return m


@torch.no_grad()
def residuals(m, X, Y):
    """mean absolute one-step-ahead error per timestep -> (n,)"""
    out = []
    Xt = torch.from_numpy(X)
    for i in range(0, len(Xt), 4096):
        out.append(m(Xt[i:i + 4096]).numpy())
    P = np.concatenate(out, 0)
    return np.abs(P - Y).mean(1)


def auroc(y, s):
    y = np.asarray(y).astype(int)
    if y.min() == y.max():
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=np.float64)
    ranks[order] = np.arange(1, len(s) + 1)
    s_sorted = s[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def ks_stat(a, b):
    a = np.sort(a)
    b = np.sort(b)
    allv = np.concatenate([a, b])
    ca = np.searchsorted(a, allv, side="right") / len(a)
    cb = np.searchsorted(b, allv, side="right") / len(b)
    return float(np.max(np.abs(ca - cb)))


def transfer_table(res_calib, res_eval, names):
    """realised FPR at every ordered pair (A calibrates, B is evaluated)."""
    tau = {n: float(np.quantile(res_calib[n], 1.0 - NOMINAL_FPR)) for n in names}
    rows, self_rows = [], []
    for a in names:
        for b in names:
            fpr = float((res_eval[b] > tau[a]).mean())
            if a == b:
                self_rows.append(fpr)
            else:
                rows.append({"calib": a, "eval": b, "fpr": fpr})
    return tau, rows, self_rows


def summarise(rows):
    v = np.array([r["fpr"] for r in rows])
    nz = v[v > 0]
    return {
        "n_pairs": int(len(v)),
        "fpr_median": float(np.median(v)),
        "fpr_p25": float(np.quantile(v, 0.25)),
        "fpr_p75": float(np.quantile(v, 0.75)),
        "fpr_p95": float(np.quantile(v, 0.95)),
        "fpr_max": float(v.max()),
        "frac_within_2x": float(((v >= NOMINAL_FPR / 2) & (v <= NOMINAL_FPR * 2)).mean()),
        "frac_within_10x": float(((v >= NOMINAL_FPR / 10) & (v <= NOMINAL_FPR * 10)).mean()),
        "log10_spread_p5_p95": (
            float(np.log10(np.quantile(nz, 0.95)) - np.log10(np.quantile(nz, 0.05)))
            if len(nz) > 4 else None
        ),
        "frac_zero_fpr": float((v == 0).mean()),
    }


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    np.random.seed(SEED)
    train_group, holdout = entities()
    print("train-group entities (%d): %s" % (len(train_group), train_group))
    print("held-out entities   (%d): %s" % (len(holdout), holdout), flush=True)

    # ---- load held-out entities, split their normals into calib / eval ----
    store = {}
    for n in holdout:
        tr, te, lb = load(n)
        cut = int(len(tr) * CALIB_FRAC)
        Xc, Yc = windowize(tr[:cut])
        Xe, Ye = windowize(tr[cut:])
        Xt, Yt = windowize(te)
        store[n] = dict(Xc=Xc, Yc=Yc, Xe=Xe, Ye=Ye, Xt=Xt, Yt=Yt, lb=lb[W:])
        print("  loaded %s: calib %d eval %d test %d anom %.3f"
              % (n, Xc.shape[0], Xe.shape[0], Xt.shape[0], store[n]["lb"].mean()),
              flush=True)

    # ---- SHARED: one model, groups 1+2 only, never sees group 3 ----
    print("\n[SHARED] pooling normals from groups 1+2 ...", flush=True)
    Xs, Ys = [], []
    for n in train_group:
        tr, _, _ = load(n)
        a, b = windowize(tr)
        Xs.append(a)
        Ys.append(b)
    Xs = np.concatenate(Xs, 0)
    Ys = np.concatenate(Ys, 0)
    print("[SHARED] %d windows from %d entities" % (Xs.shape[0], len(train_group)),
          flush=True)
    shared = fit(Xs, Ys, SEED, tag="shared")
    del Xs, Ys

    # ---- PER-STATION control: one model per held-out entity, own normals ----
    print("\n[PER-STATION] fitting one model per held-out entity ...", flush=True)
    local = {}
    for k, n in enumerate(holdout):
        local[n] = fit(store[n]["Xc"], store[n]["Yc"], SEED + 100 + k)
        print("    fitted %s" % n, flush=True)

    # ---- residuals under both conditions ----
    res = {"shared": {"calib": {}, "eval": {}, "test": {}},
           "per_station": {"calib": {}, "eval": {}, "test": {}}}
    for n in holdout:
        s = store[n]
        res["shared"]["calib"][n] = residuals(shared, s["Xc"], s["Yc"])
        res["shared"]["eval"][n] = residuals(shared, s["Xe"], s["Ye"])
        res["shared"]["test"][n] = residuals(shared, s["Xt"], s["Yt"])
        m = local[n]
        res["per_station"]["calib"][n] = residuals(m, s["Xc"], s["Yc"])
        res["per_station"]["eval"][n] = residuals(m, s["Xe"], s["Ye"])
        res["per_station"]["test"][n] = residuals(m, s["Xt"], s["Yt"])

    out = {
        "config": dict(seed=SEED, window=W, hidden=HID, epochs=EPOCHS, batch=BATCH,
                       lr=LR, calib_frac=CALIB_FRAC, nominal_fpr=NOMINAL_FPR,
                       train_entities=train_group, holdout_entities=holdout,
                       corpus="SMD (Server Machine Dataset), MIT licence",
                       note="SMD ships per-entity min-max normalised to [0,1]; "
                            "identical in both conditions."),
        "conditions": {},
    }

    for cond in ("shared", "per_station"):
        tau, rows, self_rows = transfer_table(
            res[cond]["calib"], res[cond]["eval"], holdout
        )
        summ = summarise(rows)
        summ["self_fpr_median"] = float(np.median(self_rows))
        ks = [ks_stat(res[cond]["eval"][a], res[cond]["eval"][b])
              for i, a in enumerate(holdout) for b in holdout[i + 1:]]
        aur = {n: auroc(store[n]["lb"], res[cond]["test"][n]) for n in holdout}
        vals = [v for v in aur.values() if v == v]
        out["conditions"][cond] = {
            "thresholds": tau,
            "transfer_summary": summ,
            "transfer_pairs": rows,
            "ks_median": float(np.median(ks)),
            "ks_p90": float(np.quantile(ks, 0.90)),
            "auroc_per_entity": aur,
            "auroc_mean": float(np.mean(vals)),
            "auroc_median": float(np.median(vals)),
        }

    sh = out["conditions"]["shared"]["transfer_summary"]
    ps = out["conditions"]["per_station"]["transfer_summary"]
    out["headline"] = {
        "nominal_fpr": NOMINAL_FPR,
        "shared_fpr_median": sh["fpr_median"],
        "per_station_fpr_median": ps["fpr_median"],
        "shared_frac_within_2x": sh["frac_within_2x"],
        "per_station_frac_within_2x": ps["frac_within_2x"],
        "shared_frac_within_10x": sh["frac_within_10x"],
        "per_station_frac_within_10x": ps["frac_within_10x"],
        "shared_fpr_p95": sh["fpr_p95"],
        "per_station_fpr_p95": ps["fpr_p95"],
        "shared_ks_median": out["conditions"]["shared"]["ks_median"],
        "per_station_ks_median": out["conditions"]["per_station"]["ks_median"],
        "shared_auroc_mean": out["conditions"]["shared"]["auroc_mean"],
        "per_station_auroc_mean": out["conditions"]["per_station"]["auroc_mean"],
        "runtime_s": round(time.time() - t0, 1),
    }

    with open(os.path.join(OUT, "e3_smd_commensurability%s.json" % TAG), "w") as f:
        json.dump(out, f, indent=2)

    np.savez_compressed(
        os.path.join(OUT, "e3_smd_residuals%s.npz" % TAG),
        **{"%s__%s__%s" % (c, sp, n): res[c][sp][n]
           for c in res for sp in res[c] for n in res[c][sp]}
    )

    print("\n================ E3(i) RESULT ================")
    print("nominal FPR %.3f, %d held-out entities, %d ordered cross-station pairs\n"
          % (NOMINAL_FPR, len(holdout), sh["n_pairs"]))
    print("%-22s%12s%14s" % ("", "SHARED", "PER-STATION"))
    for lab, k in [("median realised FPR", "fpr_median"),
                   ("p95 realised FPR", "fpr_p95"),
                   ("max realised FPR", "fpr_max"),
                   ("within 2x nominal", "frac_within_2x"),
                   ("within 10x nominal", "frac_within_10x"),
                   ("pairs with zero FPR", "frac_zero_fpr")]:
        print("%-22s%12.4f%14.4f" % (lab, sh[k], ps[k]))
    print("%-22s%12.4f%14.4f" % ("KS median",
                                 out["conditions"]["shared"]["ks_median"],
                                 out["conditions"]["per_station"]["ks_median"]))
    print("%-22s%12.4f%14.4f" % ("AUROC mean (test)",
                                 out["conditions"]["shared"]["auroc_mean"],
                                 out["conditions"]["per_station"]["auroc_mean"]))
    print("\nruntime %s s" % out["headline"]["runtime_s"])
    print("wrote results/e3_smd_commensurability.json and e3_smd_residuals.npz")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
