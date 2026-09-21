# Status verifikasi hands-on lab

- Compile berhasil dengan Arduino CLI, core esp32 3.3.11, Adafruit MPU6050 2.2.9, Unified Sensor 1.1.15, BusIO 1.17.4.
- Target `esp32:esp32:dfrobot_firebeetle2_esp32c5`: program 333286 byte (25%); global RAM 18640 byte (5%).
- Target generik `esp32:esp32:esp32c5`: compile berhasil; program 352750 byte; global RAM 19140 byte.
- Tiga pengujian offline lulus: sinyal diam menghasilkan 0 kandidat; sinyal sintetis 2 Hz selama interval aktivitas 20 detik menghasilkan 40 kandidat; aktivitas diekspor menjadi 1000 sampel tanpa baseline; parser menolak nilai non-finite; timestamp tidak berurutan dan gap terdeteksi.
- CLI perekam dan analyzer dapat dibuka; pyserial terpasang pada lingkungan pembuatan.
- PPTX terpisah berisi 10 slide; deck v8 berisi 53 slide dengan lab pada posisi 38–47. Estimasi ukuran teks tidak menemukan overflow. Ini pemeriksaan geometris, bukan render PowerPoint/Google Slides.

Belum melakukan upload firmware, pengukuran pada kit fisik, uji akurasi langkah manusia, atau pengiriman ke Edge Impulse. Compile dan uji sintetis tidak membuktikan kualitas sampling maupun akurasi di perangkat. Firmware tambahan Wi-Fi/MQTT belum dibuat; bonus nirkabel adalah rancangan tugas.

Jalankan ulang dari folder Slide:

```powershell
arduino-cli compile --fqbn esp32:esp32:dfrobot_firebeetle2_esp32c5 lab/Exilir_IMU_Logger
python -m unittest discover -s lab -p test_lab.py
python lab/check_slide_lab.py
```
