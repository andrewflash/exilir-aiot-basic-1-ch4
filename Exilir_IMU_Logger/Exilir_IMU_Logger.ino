/* Chapter 4 lab, adapted from Chapter_3/Baca_IMU_Library.
 * Target: ESP32-C5 + verified MPU6050. SDA=2, SCL=3, I2C=0x68.
 * USB serial 115200. Send 's' to record 3s baseline + 20s activity.
 * Output: timestamp(ms), acceleration(m/s2), angular velocity(rad/s).
 * Lines beginning # are protocol messages, not CSV samples.
 * USB acquisition only: power bank alone does NOT save or transmit data.
 */
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;
constexpr uint32_t PERIOD_US = 20000;  // target 50 Hz
constexpr uint32_t BASELINE_US = 3000000;
constexpr uint32_t DURATION_US = 23000000;
bool recording = false, activity = false, firstSample = false;
uint32_t started, nextRead, samples, lateSlots;

void setup() {
  Serial.begin(115200);
  uint32_t waitStart = millis();
  while (!Serial && millis() - waitStart < 2000) delay(10);
  Wire.begin(2, 3);
  Wire.setTimeOut(50);
  // Address alone does not identify sensor type.
  Wire.beginTransmission(0x68);
  Wire.write(0x75); // WHO_AM_I
  uint8_t id = 0xFF;
  if (Wire.endTransmission(false) == 0 && Wire.requestFrom(0x68, 1) == 1)
    id = Wire.read();
  if (id != 0x68 || !mpu.begin(0x68, &Wire)) {
    while (true) {
      Serial.printf("#ERROR expected MPU6050 WHO_AM_I=0x68; read 0x%02X\n", id);
      delay(1000);
    }
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_10_HZ);
  delay(100);
  Serial.println("#READY send s; keep sensor still for first 3 seconds");
}

void loop() {
  while (Serial.available()) {
    char command = Serial.read();
    if ((command == 's' || command == 'S') && !recording) {
      recording = true; activity = false; firstSample = true;
      samples = 0; lateSlots = 0;
      Serial.println("#BEGIN baseline_ms=3000 duration_ms=23000 target_hz=50");
      Serial.println("timestamp,accX,accY,accZ,gyroX,gyroY,gyroZ");
      nextRead = micros();
    }
  }
  if (!recording) { delay(1); return; }
  uint32_t now = micros();
  if (!firstSample && uint32_t(now - started) >= DURATION_US) {
    recording = false;
    Serial.printf("#END samples=%lu late_slots=%lu\n", (unsigned long)samples, (unsigned long)lateSlots);
    return;
  }
  if (int32_t(now - nextRead) < 0) return;
  // Skip missed schedule slots, never fabricate old readings to catch up.
  uint32_t missed = uint32_t(now - nextRead) / PERIOD_US;
  lateSlots += missed;
  nextRead += (missed + 1) * PERIOD_US;
  if (firstSample) { started = now; firstSample = false; }
  uint32_t elapsed = now - started; // timestamp at sensor read start
  if (!activity && elapsed >= BASELINE_US) {
    activity = true;
    Serial.println("#ACTIVITY start moving/counting now");
  }
  sensors_event_t a, g, temperature;
  if (!mpu.getEvent(&a, &g, &temperature)) {
    Serial.println("#ERROR sensor read failed; discard recording");
    recording = false; return;
  }
  Serial.printf("%.3f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f\n",
    elapsed / 1000.0, a.acceleration.x, a.acceleration.y, a.acceleration.z,
    g.gyro.x, g.gyro.y, g.gyro.z);
  samples++;
}
