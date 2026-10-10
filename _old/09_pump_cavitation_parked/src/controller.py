"""Drive-side action: margin restore and margin-step discrimination test.

States
  RUN      normal; follows the process speed setpoint n_set.
  PROBE    a candidate alarm (efficiency drop at low margin) is tested by lowering speed so that
           the suction margin ratio rises to R_PROBE. NPSHr at similar flow coefficient scales with
           n^2, so the speed needed is n * sqrt(R / R_PROBE) (velocity-head change of NPSHa ignored,
           which is conservative). After PROBE_HOLD samples the margin-dependent residual is read:
             recovered (|d| < half the drop)  -> cavitation confirmed -> LIMIT
             not recovered                    -> margin-independent loss (wear) -> RUN, report wear
  LIMIT    speed capped at the value that keeps R >= R_k + BUFFER, R_k the learned knee
           (or R_PROBE before a knee is learned). Released after RELEASE samples with
           margin above the cap requirement at the process setpoint.

The speed command leaves as a drive frequency setpoint (Hz x 100, Modbus holding register value)
with a rate limit, so that every action is a physical command to the variable-frequency drive.
"""
import math

R_PROBE = 2.0
BUFFER = 0.15
PROBE_HOLD = 30
RELEASE = 300
N_MIN_FRAC = 0.6         # never command below 60 % of the process setpoint
RATE = 0.5               # max speed change per sample [Hz]
POLES = 4                # motor poles: n_rps = f * 2 / POLES


def hz_to_rps(f):
    return f * 2 / POLES


def rps_to_hz(n):
    return n * POLES / 2


class Controller:
    def __init__(self):
        self.state = "RUN"
        self.f_cmd = None
        self.t = 0
        self.drop = 0.0
        self.knee = None
        self.events = []
        self.rebase = None   # (r_eta, r_psi) for Detector.rebase after a wear verdict

    def _target(self, f_now, R, r_target):
        return f_now * math.sqrt(max(R, 1e-3) / r_target)

    def step(self, f_set, est, knee=None):
        """f_set: process frequency setpoint [Hz]; est: Detector output dict. Returns command [Hz]."""
        if knee is not None:
            self.knee = knee
        if self.f_cmd is None:
            self.f_cmd = f_set
        R = est["R"]
        r_need = (self.knee + BUFFER) if self.knee else R_PROBE
        want = f_set
        if self.state == "RUN":
            if est.get("alarm"):
                self.state, self.t = "PROBE", 0
                self.drop = est.get("d_eta", 0.0)
                self.c0 = est.get("c_eta", 0.0)
                self.events.append(("probe", self.drop))
        if self.state == "PROBE":
            self.t += 1
            want = max(f_set * N_MIN_FRAC, self._target(self.f_cmd, R, R_PROBE))
            if self.t >= PROBE_HOLD:
                d = est["r_eta"] - self.c0
                if R >= R_PROBE * 0.95 and abs(d) < 0.5 * abs(self.drop):
                    self.state, self.t = "LIMIT", 0
                    self.events.append(("cavitation", self.drop, d))
                else:
                    self.state = "RUN"
                    self.events.append(("wear", self.drop, d))
                    self.rebase = (est["r_eta"], est["r_psi"])
        if self.state == "LIMIT":
            cap = max(f_set * N_MIN_FRAC, self._target(self.f_cmd, R, r_need))
            want = min(f_set, cap)
            self.t = self.t + 1 if cap >= f_set else 0
            if self.t >= RELEASE:
                self.state = "RUN"
        step = max(-RATE, min(RATE, want - self.f_cmd))
        self.f_cmd += step
        return self.f_cmd

    @staticmethod
    def modbus_register(f_hz):
        """Frequency setpoint as written to the drive (unsigned 16-bit, 0.01 Hz units)."""
        return max(0, min(65535, int(round(f_hz * 100))))
