"""Margin-gated self-calibrating efficiency baseline and margin-signature cavitation detector.

Per sample the estimator receives speed, flow, suction and discharge pressure, water temperature
and shaft power, and computes in affinity coordinates:

    phi   = Q / (n D^3)                 flow coefficient
    psi   = g H / (n D)^2               head coefficient
    eta   = rho g Q H / P               efficiency
    R     = NPSHa / NPSHr_ref(phi, n)   suction margin ratio (NPSHr_ref scaled by n^2)

N1  Healthy surfaces eta0(phi), psi0(phi) are polynomials fitted by recursive least squares with
    forgetting, updated ONLY when R >= R_SAFE and the operating point is steady. Wear and deposits
    therefore move the baseline; cavitation (which needs a low R) never enters it.
N2  Residuals r = eta/eta0(phi) - 1 are split into
      c  : margin-independent part = mean residual of recent gated (R >= R_SAFE) samples, a fast
           tracker of a wear step the slow baseline has not absorbed yet;
      d  : margin-dependent part = r - c, evaluated when R < R_SAFE.
    A cavitation alarm needs d below -K_SIGMA * noise for DWELL seconds; c never raises it.
N3  Pairs (R, d) are kept; a hinge d = -s * max(0, R_k - R) is fitted by grid search on R_k,
    giving this pump's own margin of performance-affecting cavitation onset.

Constants are fixed here before any rig data are seen (PLAN Gate B).
"""
import collections
import math

import numpy as np

import physics

R_SAFE = 2.0        # gate: NPSHa at least 2 x reference NPSH3 (datasheet) -> cavitation-free
STEADY_DPHI = 0.02  # relative change of phi over the steady window allowed for calibration
STEADY_N = 10       # samples in the steady window
LAMBDA = 0.9995     # RLS forgetting factor per gated sample (~2000-sample memory)
DEG = 2             # polynomial degree of eta0(phi), psi0(phi)
C_WINDOW = 120      # gated samples averaged for c (fast wear tracker)
K_SIGMA = 4.0       # alarm threshold in units of gated residual noise
DWELL = 20          # consecutive samples below threshold before alarm
MIN_CAL = 200       # gated samples before the detector is armed
SMOOTH = 10         # samples averaged in the margin-dependent residual before thresholding
KNEE_GRID = np.round(np.arange(1.0, R_SAFE + 1e-9, 0.02), 3)


class RLSPoly:
    """y ~ sum_k a_k x^k, recursive least squares with exponential forgetting."""

    def __init__(self, deg, lam, x0=None):
        self.deg, self.lam = deg, lam
        self.a = np.zeros(deg + 1)
        self.P = np.eye(deg + 1) * 1e4
        self.n = 0
        self.x0 = x0  # centring point of x, set from first sample

    def _basis(self, x):
        u = x / self.x0 - 1.0
        return np.array([u ** k for k in range(self.deg + 1)])

    def update(self, x, y):
        if self.x0 is None:
            self.x0 = x
        h = self._basis(x)
        k = self.P @ h / (self.lam + h @ self.P @ h)
        self.a = self.a + k * (y - h @ self.a)
        self.P = (self.P - np.outer(k, h @ self.P)) / self.lam
        self.n += 1

    def __call__(self, x):
        return float(self._basis(x) @ self.a)


class Pump:
    """Fixed geometry and datasheet reference of the monitored pump."""

    def __init__(self, d_imp, d_suction, d_discharge, npsh3_ref, dz=0.0):
        self.d_imp, self.ds, self.dd, self.dz = d_imp, d_suction, d_discharge, dz
        self.npsh3_ref = npsh3_ref  # callable (q, n_rps) -> datasheet NPSH3 [m]


class Detector:
    def __init__(self, pump):
        self.pump = pump
        self.eta0 = RLSPoly(DEG, LAMBDA)
        self.psi0 = RLSPoly(DEG, LAMBDA)
        self.phis = collections.deque(maxlen=STEADY_N)
        self.cbuf_eta = collections.deque(maxlen=C_WINDOW)
        self.cbuf_psi = collections.deque(maxlen=C_WINDOW)
        self.below = 0
        self.dbuf = collections.deque(maxlen=SMOOTH)
        self.noise_floor = 0.0
        self.pairs = []          # (R, d_eta, d_psi) at R < R_SAFE, detector armed
        self.wear_ref = None     # eta0 at the reference phi when first armed
        self.phi_ref = None

    def step(self, n_rps, q, p_s, p_d, t_c, p_shaft):
        pm = self.pump
        h = physics.pump_head(p_s, p_d, t_c, q, pm.ds, pm.dd, pm.dz)
        eta = physics.efficiency(q, h, t_c, p_shaft)
        phi = physics.flow_coefficient(q, n_rps, pm.d_imp)
        psi = physics.head_coefficient(h, n_rps, pm.d_imp)
        npsha = physics.npsh_available(p_s, t_c, q, pm.ds)
        R = npsha / pm.npsh3_ref(q, n_rps)
        self.phis.append(phi)
        steady = (len(self.phis) == STEADY_N and
                  (max(self.phis) - min(self.phis)) / phi < STEADY_DPHI)
        armed = self.eta0.n >= MIN_CAL
        out = {"phi": phi, "psi": psi, "eta": eta, "R": R, "npsha": npsha, "head": h,
               "gated": False, "armed": armed, "alarm": False}
        r_eta = eta / self.eta0(phi) - 1 if armed else float("nan")
        r_psi = psi / self.psi0(phi) - 1 if armed else float("nan")
        out.update(r_eta=r_eta, r_psi=r_psi)
        if R >= R_SAFE and steady:
            out["gated"] = True
            if armed:
                self.cbuf_eta.append(r_eta)
                self.cbuf_psi.append(r_psi)
            self.eta0.update(phi, eta)
            self.psi0.update(phi, psi)
            if armed and self.wear_ref is None:
                self.phi_ref = phi
                self.wear_ref = self.eta0(phi)
        if not armed or len(self.cbuf_eta) < 10:
            return out
        c_eta = float(np.mean(self.cbuf_eta))
        if len(self.cbuf_eta) == C_WINDOW:
            self.noise_floor = float(np.std(self.cbuf_eta)) / math.sqrt(SMOOTH)
        noise = max(float(np.std(self.cbuf_eta)) / math.sqrt(SMOOTH), self.noise_floor) + 1e-6
        out["c_eta"] = c_eta
        out["noise"] = noise
        out["wear"] = self.eta0(self.phi_ref) / self.wear_ref - 1 + c_eta
        if R < R_SAFE:
            d_eta = r_eta - c_eta
            d_psi = r_psi - float(np.mean(self.cbuf_psi))
            out["d_eta"], out["d_psi"] = d_eta, d_psi
            self.pairs.append((R, d_eta, d_psi))
            self.dbuf.append(d_eta)
            d_mean = float(np.mean(self.dbuf))
            out["d_mean"] = d_mean
            self.below = self.below + 1 if d_mean < -K_SIGMA * noise else 0
            out["alarm"] = self.below >= DWELL
        else:
            self.below = 0
            self.dbuf.clear()
        return out

    def rebase(self, r_eta, r_psi):
        """Accept a margin-independent loss confirmed by the drive's margin-step test (wear).

        The fast wear tracker c is reset to the residual measured at restored margin, so the same
        loss does not trigger a second test; the slow baseline absorbs it at the next gated samples.
        """
        self.cbuf_eta.clear()
        self.cbuf_psi.clear()
        self.cbuf_eta.extend([r_eta] * 10)
        self.cbuf_psi.extend([r_psi] * 10)
        self.dbuf.clear()
        self.below = 0

    def knee(self, min_pairs=50):
        """Fit d = -s * max(0, R_k - R) on the stored pairs; returns (R_k, s) or None."""
        if len(self.pairs) < min_pairs:
            return None
        R = np.array([p[0] for p in self.pairs])
        d = np.array([p[1] for p in self.pairs])
        best = None
        for rk in KNEE_GRID:
            x = np.maximum(0.0, rk - R)
            if not np.any(x > 0):
                continue
            s = -float(x @ d) / float(x @ x)
            sse = float(np.sum((d + s * x) ** 2))
            if best is None or sse < best[2]:
                best = (float(rk), s, sse)
        return None if best is None else best[:2]
