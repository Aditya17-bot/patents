"""DEVELOPMENT-ONLY pump simulator. Output is never evidence and never enters results/ or the IDF.

Purpose: exercise every code path (gate, baseline, separation, knee, probe, limit) before rig
data exist, and check that constants are sane. Every physical law used here is a modelling
assumption that the rig must test.

Model (single-stage end-suction pump, 4-pole motor, D = 0.25 m):
  psi(phi) = PSI_B (1.25 - 0.25 x^2),   eta(phi) = ETA_B (2x - x^2),   x = phi / PHI_B
  shaft power P = rho g Q H_nc / eta_nc  (cavitation lowers head at nearly unchanged power)
  datasheet NPSH3_ds(Q, n) = (n/n0)^2 (1.5 + 2.5 (Q n0 / n / Q_B)^2)       [m]
  true NPSH3 = TRUE_FACTOR * NPSH3_ds (pump worse than datasheet; the knee must find this)
  head and efficiency loss for R_t = NPSHa / NPSH3_true below R_ON:
      loss = 0.03 ((R_ON - R_t) / (R_ON - 1))^2      -> 3 % at R_t = 1 by definition of NPSH3
  wear w (leakage): eta x (1 - w), head x (1 - 0.5 w)
  suction: p_s = p_tank + rho g Z_TANK - K_S Q^2
Sensor noise (1 Hz logged means): pressures 0.05 % FS, flow 0.3 %, power 0.3 %, T 0.05 K.
"""
import math

import numpy as np

import physics

D_IMP, D_S, D_D = 0.25, 0.10, 0.08
N0 = 1450 / 60
Q_B = 0.025
PHI_B = Q_B / (N0 * D_IMP ** 3)
PSI_B = physics.G * 20.0 / (N0 * D_IMP) ** 2
ETA_B = 0.75
TRUE_FACTOR = 1.15
R_ON = 1.7
Z_TANK = 1.0
K_S = 800.0          # suction line loss coefficient [Pa / (m3/s)^2] x 1e3 below
FS_S, FS_D = 2.0e5, 6.0e5


def npsh3_datasheet(q, n):
    return (n / N0) ** 2 * (1.5 + 2.5 * (q * N0 / n / Q_B) ** 2)


class SimPump:
    def __init__(self, seed=1):
        self.rng = np.random.default_rng(seed)
        self.wear = 0.0

    def measure(self, n, q, p_tank, t_c=25.0):
        """Return noisy (n, q, p_s, p_d, t, P) and the true state dict."""
        rho = physics.rho_water(t_c)
        x = (q / (n * D_IMP ** 3)) / PHI_B
        psi_nc = PSI_B * (1.25 - 0.25 * x * x)
        eta_nc = ETA_B * (2 * x - x * x)
        h_nc = psi_nc * (n * D_IMP) ** 2 / physics.G
        p_s = p_tank + rho * physics.G * Z_TANK - K_S * 1e3 * q * q
        npsha = physics.npsh_available(p_s, t_c, q, D_S)
        r_true = npsha / (TRUE_FACTOR * npsh3_datasheet(q, n))
        loss = 0.03 * ((R_ON - r_true) / (R_ON - 1)) ** 2 if r_true < R_ON else 0.0
        h_w = h_nc * (1 - 0.5 * self.wear)
        p_shaft = rho * physics.G * q * h_w / (eta_nc * (1 - self.wear))  # cavitation: power unchanged
        h = h_w * (1 - loss)
        # discharge pressure that reproduces head h through physics.pump_head
        vs, vd = physics.velocity(q, D_S), physics.velocity(q, D_D)
        p_d = p_s + rho * physics.G * (h - (vd * vd - vs * vs) / (2 * physics.G))
        r = self.rng.normal
        meas = (n, q * (1 + r(0, 0.003)), p_s + r(0, 5e-4 * FS_S), p_d + r(0, 5e-4 * FS_D),
                t_c + r(0, 0.05), p_shaft * (1 + r(0, 0.003)))
        return meas, {"loss": loss, "R_true": r_true, "npsha": npsha, "head": h}


def pump_def():
    import estimator
    return estimator.Pump(D_IMP, D_S, D_D, npsh3_datasheet)
