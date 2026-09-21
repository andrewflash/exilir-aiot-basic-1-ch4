# Tambahan hands-on counting
Deck v9: slide 48–50.

## Lab 9 • Hitung langkah langsung di ESP32
- Upload Exilir_Step_Counter; buka Serial Monitor 115200.
- Kirim r → diam 3 detik → lakukan 20 langkah / stepping.
- Bandingkan kolom steps dengan hitungan pasangan.
- Gyroscope tidak dipakai; parameter ada di StepDetector.h.

Catatan: Sketch dan header harus satu folder. SDA2/SCL3, MPU6050 0x68; lanjutkan setup Chapter 3. Jika memakai USB, stepping di tempat dan beri label sesuai aktivitas. Reset sebelum setiap percobaan. Hitungan ini estimasi kandidat langkah, bukan ground truth. Belum diuji pada kit fisik.

## Lab 10 • Aturan threshold dalam kode
- Magnitude → moving average 5 sampel → kurangi baseline.
- Terima puncak lokal > 1,2 m/s² dengan jeda ≥300 ms.
- Sinyal harus turun <0,3 m/s² sebelum kandidat berikutnya.
- Coba threshold 0,8 / 1,2 / 1,8; uji sesi baru.

Catatan: Baseline median 3 detik diam. Puncak sebelumnya dikonfirmasi dengan sampel berikutnya. τ_min adalah interval minimum antara dua puncak diterima. Potongan di slide hanya pemakaian class; implementasi lengkap ada pada StepDetector.h. Ubah satu parameter per percobaan, catat false positive/negative. Jangan mengklaim akurasi dari sinyal sintetis.

```cpp
bool accepted = detector.update(t_ms, ax, ay, az);
// di dalam detector: peak + threshold + hysteresis + jeda
Serial.println(detector.count);
// reset sesi: detector.reset(); mulai ulang t_ms dari 0
```

## Lab 11 • Counter + CSV dari handphone
- Upload Exilir_SoftAP_Logger; nyalakan dengan power bank.
- Wi-Fi Exilir-IMU-XXXX → buka http://192.168.4.1.
- Start → diam 3 detik → bergerak → Stop → unduh CSV + metadata.
- Catat hitungan HP, manual, dan hasil Python; jelaskan selisih.

Catatan: Password exilir12345. Counter diproses di ESP32 target50Hz; tampilan HP diperbarui sekitar1detik. Start mereset count; Stop mempertahankan sampai Start/reset berikutnya. Metadata berisi steps, threshold, baseline dan gap. CSV tetap kanal sensor untuk analisis ulang. Default23detik=3baseline+20aktivitas; samakan interval referensi. Data hilang saat mati/reset. Koneksi power bank dan Wi-Fi masih perlu pengujian fisik. Panduan: lab/Exilir_Step_Counter/README.md.