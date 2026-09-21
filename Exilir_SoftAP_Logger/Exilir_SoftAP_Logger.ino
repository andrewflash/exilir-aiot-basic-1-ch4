/* Exilir Chapter 4: MPU6050 -> RAM -> phone over Wi-Fi SoftAP.
 * Based on Chapter_3/Baca_IMU_Library. No internet/SD/PSRAM required.
 * SDA=2 SCL=3, address=0x68. 50 Hz, maximum 30 seconds.
 * Connect phone to Exilir-IMU-XXXX / exilir12345, open http://192.168.4.1
 * web_page.h must remain in the same sketch folder.
 */
#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <math.h>
#include "web_page.h"
#include "StepDetector.h"

constexpr uint32_t PERIOD_US=20000, MAX_SAMPLES=1500;
const char* AP_PASSWORD="exilir12345"; // password for classroom SoftAP
struct Sample { uint32_t us; float ax,ay,az,gx,gy,gz; };
Sample dataBuffer[MAX_SAMPLES]; // 42,000 bytes, one recording only
Adafruit_MPU6050 mpu;
StepDetector detector;
WebServer server(80);
SemaphoreHandle_t guard;
bool sensorReady=false, samplerReady=false, recording=false;
uint32_t sampleCount=0, startedUs=0, nextUs=0, limitMs=23000;
uint32_t missedSlots=0, maxIntervalUs=0, finishedMs=0;
char label[33]="recording";
const char* reason="ready";

// All recording state and buffer writes use guard; only sampler touches I2C.
void sampler(void*) {
  for (;;) {
    xSemaphoreTake(guard,portMAX_DELAY);
    if (recording) {
      uint32_t now=micros();
      if (sampleCount && uint32_t(now-startedUs)>=limitMs*1000) {
        recording=false;finishedMs=(now-startedUs)/1000;reason="duration_limit";
      } else if (int32_t(now-nextUs)>=0) {
        if (!sampleCount) {startedUs=now;nextUs=now;}
        uint32_t skipped=uint32_t(now-nextUs)/PERIOD_US;
        missedSlots+=skipped;nextUs+=(skipped+1)*PERIOD_US;
        sensors_event_t a,g,temp;
        bool ok=mpu.getEvent(&a,&g,&temp);
        ok=ok&&isfinite(a.acceleration.x)&&isfinite(a.acceleration.y)&&isfinite(a.acceleration.z)
             &&isfinite(g.gyro.x)&&isfinite(g.gyro.y)&&isfinite(g.gyro.z);
        if (!ok) {
          recording=false;sensorReady=false;finishedMs=(now-startedUs)/1000;reason="read_error";
        } else {
          uint32_t t=now-startedUs;
          if (sampleCount) maxIntervalUs=max(maxIntervalUs,t-dataBuffer[sampleCount-1].us);
          dataBuffer[sampleCount++]={t,a.acceleration.x,a.acceleration.y,a.acceleration.z,g.gyro.x,g.gyro.y,g.gyro.z};
          detector.update(t/1000,a.acceleration.x,a.acceleration.y,a.acceleration.z);
          if (sampleCount==MAX_SAMPLES) {recording=false;finishedMs=t/1000;reason="buffer_full";}
        }
      }
    }
    xSemaphoreGive(guard);
    vTaskDelay(1); // yield to Wi-Fi/HTTP; schedule uses actual micros(), not arrival time
  }
}

String statusJson() {
  char out[1000];
  xSemaphoreTake(guard,portMAX_DELAY);
  uint32_t elapsed=recording?(sampleCount?(micros()-startedUs)/1000:0):finishedMs;
  float fs=sampleCount>1&&dataBuffer[sampleCount-1].us?1000000.0f*(sampleCount-1)/dataBuffer[sampleCount-1].us:0;
  snprintf(out,sizeof(out),"{\"sensor_ready\":%s,\"sampler_ready\":%s,\"recording\":%s,\"samples\":%lu,\"elapsed_ms\":%lu,\"limit_ms\":%lu,\"target_hz\":50,\"actual_hz\":%.3f,\"max_interval_ms\":%.3f,\"missed_slots\":%lu,\"reason\":\"%s\",\"label\":\"%s\",\"baseline_ms\":3000,\"acceleration_unit\":\"m/s2\",\"gyro_unit\":\"rad/s\",\"timestamp_unit\":\"ms\"}",
    sensorReady?"true":"false",samplerReady?"true":"false",recording?"true":"false",(unsigned long)sampleCount,(unsigned long)elapsed,(unsigned long)limitMs,fs,maxIntervalUs/1000.0,(unsigned long)missedSlots,reason,label);
  // Append counter diagnostics to both live status and downloaded metadata.
  String result(out);result.remove(result.length()-1);
  char counter[400];
  snprintf(counter,sizeof(counter),",\"steps\":%lu,\"detector_ready\":%s,\"calibration_failed\":%s,\"baseline_m_s2\":%.4f,\"filtered_m_s2\":%.4f,\"high_m_s2\":%.2f,\"low_m_s2\":%.2f,\"min_interval_ms\":%lu,\"detector_gaps\":%lu}",
    (unsigned long)detector.count,detector.ready?"true":"false",detector.calibrationFailed?"true":"false",detector.baseline,detector.filtered,StepDetector::THRESHOLD_HIGH,StepDetector::THRESHOLD_LOW,(unsigned long)StepDetector::MIN_INTERVAL_MS,(unsigned long)detector.gaps);
  result+=counter;
  xSemaphoreGive(guard);return result;
}

void startRecording() {
  String name=server.arg("label"),seconds=server.arg("duration");
  bool valid=name.length()>0&&name.length()<=32&&seconds.length()>0;
  for (char c:name) valid=valid&&((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-');
  for (char c:seconds) valid=valid&&(c>='0'&&c<='9');
  int duration=seconds.toInt();
  if (!valid||duration<5||duration>30) {server.send(400,"text/plain","Nama tidak valid atau durasi di luar 5-30 detik.");return;}
  xSemaphoreTake(guard,portMAX_DELAY);
  int error=0;
  if (!sensorReady||!samplerReady) error=503;
  else if (recording||(sampleCount&&server.arg("replace")!="1")) error=409;
  else {
    name.toCharArray(label,sizeof(label));sampleCount=0;missedSlots=0;maxIntervalUs=0;finishedMs=0;
    detector.reset(); // every Start has its own stationary baseline and count
    limitMs=duration*1000;nextUs=micros();reason="recording";recording=true;
  }
  xSemaphoreGive(guard);
  if (error) {server.send(error,"text/plain",error==503?"Sensor belum siap. Cek MPU6050, kabel, dan restart.":"Sedang merekam, atau data lama belum diizinkan untuk diganti.");return;}
  server.send(200,"application/json",statusJson());
}

void stopRecording() {
  xSemaphoreTake(guard,portMAX_DELAY);
  if (recording) {finishedMs=sampleCount?(micros()-startedUs)/1000:0;recording=false;reason="manual_stop";}
  xSemaphoreGive(guard);server.send(200,"application/json",statusJson());
}

bool downloadable() {
  xSemaphoreTake(guard,portMAX_DELAY);bool active=recording;uint32_t count=sampleCount;xSemaphoreGive(guard);
  if (active) {server.send(409,"text/plain","Tekan Stop sebelum mengunduh.");return false;}
  if (!count) {server.send(404,"text/plain","Belum ada sampel.");return false;}
  return true;
}

void downloadCsv() {
  if (!downloadable()) return;
  // WebServer handles one request at a time; stopped buffer is immutable throughout this handler.
  bool six=server.arg("axes")=="6";
  server.sendHeader("Content-Disposition",String("attachment; filename=\"")+label+(six?"_6axis.csv\"":"_3axis.csv\""));
  server.sendHeader("Cache-Control","no-store");server.setContentLength(CONTENT_LENGTH_UNKNOWN);
  server.send(200,"text/csv; charset=utf-8","");
  server.sendContent(six?"timestamp,accX,accY,accZ,gyroX,gyroY,gyroZ\r\n":"timestamp,accX,accY,accZ\r\n");
  char row[180];String chunk;chunk.reserve(2200);
  for (uint32_t i=0;i<sampleCount&&server.client().connected();i++) {
    const Sample& s=dataBuffer[i];
    if (six) snprintf(row,sizeof(row),"%.3f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f\r\n",s.us/1000.0,s.ax,s.ay,s.az,s.gx,s.gy,s.gz);
    else snprintf(row,sizeof(row),"%.3f,%.5f,%.5f,%.5f\r\n",s.us/1000.0,s.ax,s.ay,s.az);
    chunk+=row;
    if (chunk.length()>1800) {server.sendContent(chunk);chunk="";delay(1);}
  }
  if (chunk.length()) server.sendContent(chunk);
  server.sendContent("");
}

void setup() {
  Serial.begin(115200); // never wait for USB host: power-bank boot supported
  guard=xSemaphoreCreateMutex();
  if (!guard) {while(true) delay(1000);}
  Wire.begin(2,3);Wire.setTimeOut(50);
  Wire.beginTransmission(0x68);Wire.write(0x75);uint8_t id=0xFF;
  if (Wire.endTransmission(false)==0&&Wire.requestFrom(0x68,1)==1) id=Wire.read();
  sensorReady=id==0x68&&mpu.begin(0x68,&Wire);
  if (sensorReady) {
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_10_HZ);
  } else reason="sensor_not_found";
  char ssid[32];snprintf(ssid,sizeof(ssid),"Exilir-IMU-%04X",(unsigned)(ESP.getEfuseMac()&0xFFFF));
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(IPAddress(192,168,4,1),IPAddress(192,168,4,1),IPAddress(255,255,255,0));
  if (!WiFi.softAP(ssid,AP_PASSWORD,1,false,2)) {Serial.println("SoftAP failed");while(true) delay(1000);}
  samplerReady=xTaskCreate(sampler,"imuSampler",4096,nullptr,2,nullptr)==pdPASS;
  if (!samplerReady) reason="sampler_not_started";
  server.on("/",HTTP_GET,[]{server.sendHeader("Cache-Control","no-store");server.send_P(200,"text/html; charset=utf-8",INDEX_HTML);});
  server.on("/status",HTTP_GET,[]{server.sendHeader("Cache-Control","no-store");server.send(200,"application/json",statusJson());});
  server.on("/start",HTTP_POST,startRecording);server.on("/stop",HTTP_POST,stopRecording);
  server.on("/download",HTTP_GET,downloadCsv);
  server.on("/metadata",HTTP_GET,[]{if (!downloadable()) return;server.sendHeader("Content-Disposition",String("attachment; filename=\"")+label+".json\"");server.send(200,"application/json",statusJson());});
  server.onNotFound([]{server.send(404,"text/plain","Buka http://192.168.4.1");});
  server.begin();Serial.printf("WiFi: %s\nPassword: %s\nhttp://192.168.4.1\nWHO_AM_I: 0x%02X\n",ssid,AP_PASSWORD,id);
}

void loop() { server.handleClient();delay(1); }
