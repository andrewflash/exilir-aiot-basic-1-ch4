/* Simple on-device threshold step counter: ESP32-C5 + verified MPU6050.
 * SDA=2 SCL=3. Keep still for 3s after boot/reset; then move.
 * Serial 115200: r resets calibration and count. No Wi-Fi required.
 * StepDetector.h contains the short reusable detector implementation.
 */
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "StepDetector.h"

Adafruit_MPU6050 mpu;
StepDetector detector;
uint32_t sessionStart, nextRead;
bool announced=false;

void resetSession() {
  detector.reset();announced=false;
  Serial.println("# DIAM 3 detik untuk baseline; r untuk reset");
  Serial.println("timestamp,filteredMagnitude,steps");
  sessionStart=millis();nextRead=sessionStart;
}
void setup() {
  Serial.begin(115200);
  uint32_t wait=millis();while(!Serial && millis()-wait<2000) delay(10);
  Wire.begin(2,3);Wire.setTimeOut(50);
  // Adafruit begin checks WHO_AM_I for MPU6050.
  if(!mpu.begin(0x68,&Wire)) {
    while(true) {Serial.println("# ERROR: cek MPU6050 dan pin I2C");delay(1000);}
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_10_HZ);
  resetSession();
}
void loop() {
  while(Serial.available()) {char c=Serial.read();if(c=='r'||c=='R') resetSession();}
  uint32_t now=millis();
  if(int32_t(now-nextRead)<0) {delay(1);return;}
  nextRead+=((now-nextRead)/20+1)*20; // no burst of fake catch-up samples
  sensors_event_t a,g,temp;
  if(!mpu.getEvent(&a,&g,&temp)) {Serial.println("# ERROR: baca sensor gagal");return;}
  bool step=detector.update(now-sessionStart,a.acceleration.x,a.acceleration.y,a.acceleration.z);
  if(detector.ready&&!announced) {
    announced=true;Serial.printf("# MULAI bergerak; baseline=%.3f m/s2\n",detector.baseline);
  }
  Serial.printf("%lu,%.4f,%lu\n",(unsigned long)(now-sessionStart),detector.filtered,(unsigned long)detector.count);
  if(step) Serial.println("# STEP: satu kandidat diterima");
}
