"""Water properties and pump hydraulic quantities used by the estimator.

Every function takes SI units (Pa, K or degC as named, m3/s, rad/s, W) and returns SI units.
"""
import math

G = 9.80665


def p_vapour(t_c):
    """Saturation pressure of water [Pa] at t_c [degC], IAPWS-IF97 region 4 (273.15-647.096 K)."""
    n = [0.11670521452767e4, -0.72421316703206e6, -0.17073846940092e2, 0.12020824702470e5,
         -0.32325550322333e7, 0.14915108613530e2, -0.48232657361591e4, 0.40511340542057e6,
         -0.23855557567849, 0.65017534844798e3]
    t = t_c + 273.15
    th = t + n[8] / (t - n[9])
    a = th * th + n[0] * th + n[1]
    b = n[2] * th * th + n[3] * th + n[4]
    c = n[5] * th * th + n[6] * th + n[7]
    return (2 * c / (-b + math.sqrt(b * b - 4 * a * c))) ** 4 * 1e6


def rho_water(t_c):
    """Density of liquid water [kg/m3] at 0.1 MPa, Kell (1975), 0-100 degC."""
    t = t_c
    return ((999.83952 + 16.945176 * t - 7.9870401e-3 * t ** 2 - 46.170461e-6 * t ** 3
             + 105.56302e-9 * t ** 4 - 280.54253e-12 * t ** 5) / (1 + 16.879850e-3 * t))


def velocity(q, d_pipe):
    return q / (math.pi * d_pipe ** 2 / 4)


def npsh_available(p_s_abs, t_c, q, d_suction, z_s=0.0):
    """NPSHa [m] at the suction flange: (p_s - p_v)/(rho g) + v_s^2/2g + z_s (gauge height above datum)."""
    rho = rho_water(t_c)
    v = velocity(q, d_suction)
    return (p_s_abs - p_vapour(t_c)) / (rho * G) + v * v / (2 * G) + z_s


def pump_head(p_s_abs, p_d_abs, t_c, q, d_suction, d_discharge, dz=0.0):
    """Total head [m] between suction and discharge flanges."""
    rho = rho_water(t_c)
    vs, vd = velocity(q, d_suction), velocity(q, d_discharge)
    return (p_d_abs - p_s_abs) / (rho * G) + (vd * vd - vs * vs) / (2 * G) + dz


def efficiency(q, h, t_c, p_shaft):
    """Pump (shaft-to-water) efficiency rho g Q H / P_shaft."""
    return rho_water(t_c) * G * q * h / p_shaft if p_shaft > 0 else float("nan")


def flow_coefficient(q, n_rps, d_imp):
    """phi = Q / (n D^3), n in rev/s."""
    return q / (n_rps * d_imp ** 3)


def head_coefficient(h, n_rps, d_imp):
    """psi = g H / (n D)^2."""
    return G * h / (n_rps * d_imp) ** 2


def suction_coefficient(npsha, n_rps, d_imp):
    """kappa = g NPSHa / (n D)^2: NPSH in the same affinity scaling as head.

    NPSHr at similar flow coefficient scales with n^2 (affinity law), so the ratio
    kappa / kappa_r(phi) is independent of speed.
    """
    return G * npsha / (n_rps * d_imp) ** 2
