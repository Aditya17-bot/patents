/*
 * Candidate-station interlock node (100) - firmware
 *
 * Reads the four physical channels of the candidate station, timestamps them on a
 * single monotonic clock, and streams them to the host controller.  Accepts gate
 * commands from the host and drives the in-line USB switch (920) and the desk
 * indicator (910).
 *
 * Two safety properties are enforced HERE, in hardware and firmware, rather than
 * in the host software, because a host that has crashed cannot enforce anything:
 *
 *   fail-closed   GATE_PIN drives /OE of the analog switch.  A 10k pulldown holds
 *                 /OE low - switch passing, keyboard working - whenever this MCU
 *                 is unpowered, in reset, or hung.  Opening the candidate's input
 *                 path is the ACTIVE state and needs a live MCU to assert it.
 *
 *   watchdog      Any asserted gate is released after GATE_MAX_MS unless the host
 *                 refreshes it with a heartbeat.  A wedged host cannot hold a
 *                 candidate's keyboard open indefinitely.
 *
 * Target: ESP32-WROOM (Arduino core).  Also builds on AVR with SAMPLE_HZ lowered.
 */

#include <Wire.h>

// ---- pin map (see hardware/BOM.md) -------------------------------------------
static const int PIN_PHOTO   = 36;   // 210  ADC1_CH0  transimpedance output
static const int PIN_PIEZO   = 39;   // 400  ADC1_CH3  JFET preamp output
static const int PIN_MIC     = 34;   // 402  ADC1_CH6  electret module output
static const int PIN_GATE    = 25;   // 920  drives /OE of TS3USB221A
static const int PIN_LED_R   = 26;   // 910
static const int PIN_LED_G   = 27;
static const int PIN_LED_B   = 14;

static const uint8_t MPU_ADDR = 0x68;   // 410

// ---- timing ------------------------------------------------------------------
static const uint32_t SAMPLE_HZ   = 200;      // channel sampling rate
static const uint32_t REPORT_HZ   = 50;       // frames to host
static const uint32_t GATE_MAX_MS = 3000;     // watchdog bound on any gate assertion
static const uint32_t SAMPLE_US   = 1000000UL / SAMPLE_HZ;
static const uint32_t REPORT_US   = 1000000UL / REPORT_HZ;

// ---- onset detection (210) ---------------------------------------------------
// The display renders a patch that inverts on every question transition.  We
// detect the edge against a slow-adapting baseline so ambient light drift and
// backlight PWM do not produce false anchors.
static const float   PHOTO_ALPHA  = 0.002f;   // baseline adaptation per sample
static const float   PHOTO_K      = 6.0f;     // edge threshold in baseline sigmas
static const uint32_t PHOTO_HOLDOFF_MS = 250; // min interval between anchors

struct Adaptive {
  float mean, var;
  bool  primed;
  void update(float x) {
    if (!primed) { mean = x; var = 1.0f; primed = true; return; }
    float d = x - mean;
    mean += PHOTO_ALPHA * d;
    var  += PHOTO_ALPHA * (d * d - var);
  }
  float z(float x) const { return (x - mean) / (sqrtf(var) + 1e-6f); }
};

static Adaptive photoBase, piezoBase, micBase;

// ---- state -------------------------------------------------------------------
static uint32_t lastSampleUs = 0, lastReportUs = 0;
static uint32_t gateAssertedMs = 0;
static bool     gateOpen = false;          // true = candidate input path BROKEN
static uint32_t lastOnsetMs = 0;
static uint32_t onsetSeq = 0;

// accumulators between host frames
static float pzPeak = 0, micPeak = 0, pzRms = 0, micRms = 0;
static uint16_t accN = 0;
static float axf = 0, ayf = 0, azf = 0, gxf = 0, gyf = 0, gzf = 0;

// ---- IMU (410) ---------------------------------------------------------------
static void mpuInit() {
  Wire.begin();
  Wire.setClock(400000);
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); Wire.write(0x00);          // wake
  Wire.endTransmission(true);
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1C); Wire.write(0x00);          // accel +/- 2g
  Wire.endTransmission(true);
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1B); Wire.write(0x00);          // gyro +/- 250 dps
  Wire.endTransmission(true);
}

static bool mpuRead(float *ax, float *ay, float *az,
                    float *gx, float *gy, float *gz) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)MPU_ADDR, 14, true) != 14) return false;
  int16_t r[7];
  for (int i = 0; i < 7; i++) r[i] = (Wire.read() << 8) | Wire.read();
  *ax = r[0] / 16384.0f * 9.80665f;            // m/s^2
  *ay = r[1] / 16384.0f * 9.80665f;
  *az = r[2] / 16384.0f * 9.80665f;
  *gx = r[4] / 131.0f * 0.017453f;             // rad/s
  *gy = r[5] / 131.0f * 0.017453f;
  *gz = r[6] / 131.0f * 0.017453f;
  return true;
}

// ---- actuators ---------------------------------------------------------------
static void setLed(uint8_t r, uint8_t g, uint8_t b) {
  digitalWrite(PIN_LED_R, r); digitalWrite(PIN_LED_G, g); digitalWrite(PIN_LED_B, b);
}

static void gateSet(bool open) {
  // HIGH on /OE disables the switch -> candidate input path broken.
  digitalWrite(PIN_GATE, open ? HIGH : LOW);
  if (open && !gateOpen) gateAssertedMs = millis();
  gateOpen = open;
  if (open)            setLed(1, 0, 0);        // red   - GATE
  else if (lastOnsetMs) setLed(0, 1, 0);       // green - running
}

void setup() {
  Serial.begin(921600);
  pinMode(PIN_GATE, OUTPUT);
  digitalWrite(PIN_GATE, LOW);                 // fail-closed on boot
  pinMode(PIN_LED_R, OUTPUT); pinMode(PIN_LED_G, OUTPUT); pinMode(PIN_LED_B, OUTPUT);
  setLed(0, 0, 1);                             // blue - waiting for host
  analogReadResolution(12);
  mpuInit();
  Serial.println(F("# interlock-node v1 ch=photo,piezo,mic,imu gate=fail-closed"));
}

// Host protocol, newline delimited ASCII so it can be driven from a terminal:
//   G1  assert gate (open the input path)      G0  release gate
//   A1  advise indicator on                    A0  off
//   H   heartbeat, refreshes the gate watchdog
//   P   ping -> "# pong"
static void serviceHost() {
  while (Serial.available()) {
    int c = Serial.read();
    if (c == 'G') {
      while (!Serial.available()) {}
      gateSet(Serial.read() == '1');
    } else if (c == 'A') {
      while (!Serial.available()) {}
      if (Serial.read() == '1' && !gateOpen) setLed(1, 1, 0);   // amber - ADVISE
      else if (!gateOpen) setLed(0, 1, 0);
    } else if (c == 'H') {
      if (gateOpen) gateAssertedMs = millis();                  // refresh watchdog
    } else if (c == 'P') {
      Serial.println(F("# pong"));
    }
  }
}

void loop() {
  serviceHost();

  // watchdog: release an unrefreshed gate
  if (gateOpen && (millis() - gateAssertedMs) > GATE_MAX_MS) {
    gateSet(false);
    Serial.println(F("# watchdog-release"));
  }

  uint32_t now = micros();
  if ((uint32_t)(now - lastSampleUs) >= SAMPLE_US) {
    lastSampleUs = now;

    float ph = analogRead(PIN_PHOTO);
    float pz = analogRead(PIN_PIEZO);
    float mc = analogRead(PIN_MIC);

    // ---- 210 question-onset anchor: edge against an adaptive baseline
    float pz_z = piezoBase.primed ? fabsf(piezoBase.z(pz)) : 0.0f;
    float mc_z = micBase.primed   ? fabsf(micBase.z(mc))   : 0.0f;
    if (photoBase.primed && fabsf(photoBase.z(ph)) > PHOTO_K &&
        (millis() - lastOnsetMs) > PHOTO_HOLDOFF_MS) {
      lastOnsetMs = millis();
      onsetSeq++;
      // emitted immediately, not at the next report boundary, so the host sees
      // the anchor with sampling-period latency rather than frame latency
      Serial.print(F("O ")); Serial.print(onsetSeq);
      Serial.print(' ');     Serial.println(micros());
    }
    photoBase.update(ph); piezoBase.update(pz); micBase.update(mc);

    if (pz_z > pzPeak)  pzPeak  = pz_z;
    if (mc_z > micPeak) micPeak = mc_z;
    pzRms += pz_z * pz_z; micRms += mc_z * mc_z; accN++;

    float ax, ay, az, gx, gy, gz;
    if (mpuRead(&ax, &ay, &az, &gx, &gy, &gz)) {
      axf = ax; ayf = ay; azf = az; gxf = gx; gyf = gy; gzf = gz;
    }
  }

  if ((uint32_t)(now - lastReportUs) >= REPORT_US) {
    lastReportUs = now;
    uint16_t n = accN ? accN : 1;
    // Equation 1: M_total = sqrt(|a|^2 + (lambda*|w|)^2), lambda = 0.25
    float amag = sqrtf(axf * axf + ayf * ayf + azf * azf);
    float wmag = sqrtf(gxf * gxf + gyf * gyf + gzf * gzf);
    float mtot = sqrtf(amag * amag + (0.25f * wmag * 9.80665f) *
                                     (0.25f * wmag * 9.80665f));
    // F <us> <since_onset_ms> <piezo_pk> <piezo_rms> <mic_pk> <mic_rms> <M_total> <gate>
    Serial.print(F("F "));
    Serial.print(now);                                  Serial.print(' ');
    Serial.print(lastOnsetMs ? (millis() - lastOnsetMs) : 0); Serial.print(' ');
    Serial.print(pzPeak, 3);                            Serial.print(' ');
    Serial.print(sqrtf(pzRms / n), 3);                  Serial.print(' ');
    Serial.print(micPeak, 3);                           Serial.print(' ');
    Serial.print(sqrtf(micRms / n), 3);                 Serial.print(' ');
    Serial.print(mtot, 4);                              Serial.print(' ');
    Serial.println(gateOpen ? 1 : 0);
    pzPeak = micPeak = pzRms = micRms = 0; accN = 0;
  }
}
