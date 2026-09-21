# Verifikasi

- Arduino CLI compile berhasil untuk `esp32:esp32:dfrobot_firebeetle2_esp32c5` dengan core ESP32 3.3.11, Adafruit MPU6050 2.2.9, Unified Sensor 1.1.15, BusIO 1.17.4.
- Program: 1.105.367 byte (84% dari partisi aplikasi default). Global RAM statis: 93.400 byte (28%), termasuk buffer 42 KB. Pemakaian heap Wi-Fi/HTTP saat runtime belum diukur.
- Browser Chrome, viewport HP 390 × 844: input nama invalid ditolak; Start/Stop dan enable/disable tombol sesuai status; cue baseline/aktivitas; download tiga/enam kanal dan metadata; konfirmasi penggantian data; error sensor; tidak ada overflow horizontal atau error JavaScript.
- Browser diuji dengan endpoint HTTP simulasi, bukan ESP32. Tes ada di `../test_softap_ui.py`. `preview_handphone.png` adalah screenshot pengujian UI, bukan bukti rekaman nyata.
- Belum flash firmware, uji perangkat fisik, verifikasi koneksi Android/iOS, uji jitter Wi-Fi, atau pengujian mati daya. Data RAM memang tidak bertahan saat reset.

Compile ulang dari folder Slide:

```powershell
arduino-cli compile --fqbn esp32:esp32:dfrobot_firebeetle2_esp32c5 lab/Exilir_SoftAP_Logger
```

Sebelum kelas: upload, nyalakan dari power bank, rekam 23 detik via HP, cek CSV dan metadata; ulangi pada aktivitas diam/berjalan. Coba Stop manual, unduh ulang, Start baru, putus-sambung Wi-Fi, dan rekam hingga batas 30 detik. Matikan perangkat hanya setelah semua berkas berhasil disimpan.

Counter tambahan: compile berhasil; UI mock memverifikasi count tampil, bertahan setelah Stop, dan reset pada Start. Header detector sama dengan sketch Serial. Uji C++ native mencakup diam, 40 puncak sintetis, amplitudo di bawah threshold, refractory, gap, reset, dan kalibrasi kurang. Belum pengujian langkah manusia.
