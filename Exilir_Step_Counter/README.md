# Hands-on: counting langkah langsung di ESP32-C5

Sketch ini melanjutkan pembacaan IMU Chapter 3. Gunakan ESP32-C5 dengan MPU6050, SDA GPIO2, SCL GPIO3, alamat 0x68. Install library Adafruit MPU6050 beserta dependensinya. Buka `Exilir_Step_Counter.ino` dan pastikan `StepDetector.h` tetap di folder yang sama.

## Praktik 15–20 menit

1. Upload sketch, buka Serial Monitor 115200 baud. Kirim `r` untuk memulai ulang sesi setelah monitor terbuka.
2. Diam selama 3 detik. Setelah pesan `MULAI bergerak`, lakukan 20 langkah sambil dihitung pasangan. Untuk koneksi USB, lakukan stepping di tempat dan beri label yang sesuai.
3. Baca kolom `steps`; setiap kandidat diterima juga muncul pesan `# STEP`. Kolom lain: timestamp ms dan magnitude terfilter m/s². Ini keluaran demo Serial, bukan CSV mentah untuk script analisis.
4. Kirim `r`, ulangi kondisi diam, gerakan pelan, biasa, cepat, dan menggoyangkan sensor tanpa melangkah. Catat jumlah manual dan prediksi.
5. Ubah `THRESHOLD_HIGH` di `StepDetector.h` dari 1.2 menjadi 0.8 lalu 1.8; compile/upload dan ulangi. Ubah satu parameter pada satu waktu. Pastikan threshold bawah lebih kecil daripada threshold atas.
6. Kembalikan parameter awal, lalu bandingkan `MIN_INTERVAL_MS` 300 dengan 500. Jeda 500 ms dapat menolak langkah dengan interval di bawah 0,5 detik. Evaluasi pada rekaman/orang baru setelah tuning.

## Algoritma sesuai materi

```text
Setiap ~20 ms: baca ax, ay, az (m/s²)
magnitude = sqrt(ax² + ay² + az²)
baseline = median magnitude saat diam pada 3 detik pertama
filtered = moving_average_5(magnitude) - baseline
Jika filtered < 0.3: izinkan kandidat berikutnya
Jika sampel sebelumnya adalah puncak lokal, > 1.2,
  sudah diizinkan, dan >= 300 ms dari puncak terakhir:
    jumlah += 1; simpan waktu puncak; tunggu turun lagi
```

Puncak lokal dikonfirmasi setelah satu sampel berikutnya datang; ada keterlambatan filter dan konfirmasi. Counter tidak menghitung selama kalibrasi. Gyroscope tidak digunakan dalam algoritma ini. Nilai awal threshold bukan nilai universal: posisi sensor, kecepatan, dan penggunanya memengaruhi hasil. Goyangan dapat menghasilkan false step.

`τ_min` adalah jeda minimum antarpuncak yang diterima. Hysteresis mengharuskan sinyal turun di bawah threshold bawah sebelum kandidat berikutnya. Jeda sampel >60 ms mengosongkan riwayat filter/puncak; jumlah tetap dipertahankan, tetapi sesi dengan gap harus diperiksa. Kalibrasi gagal jika kurang dari 30 sampel baseline tersedia; reset sesi.

## Pilihan tanpa kabel: SoftAP

Upload sketch saudara `../Exilir_SoftAP_Logger/Exilir_SoftAP_Logger.ino`, beri daya dari power bank, hubungkan HP ke `Exilir-IMU-XXXX` (password `exilir12345`), lalu buka `http://192.168.4.1`. Tekan **Start**, diam 3 detik, bergerak, lalu **Stop** atau tunggu durasi habis.

Halaman menampilkan hitungan dengan pembaruan sekitar 1 detik. Perhitungan tetap berlangsung pada ESP32, target 50 Hz. Start mereset hitungan dan baseline; Stop mempertahankan hasil. Download CSV untuk analisis dan metadata untuk `steps` serta parameter detector. Data RAM hilang ketika reset/mati. Gunakan kedua file: CSV sengaja tetap berisi kanal sensor, tanpa kolom hitungan. Parameter diubah lewat header sketch dan upload ulang.

Bandingkan `N_manual`, `N_device`, dan hasil Python pada CSV mentah durasi default 23 detik. Ketiganya harus memakai interval aktivitas yang sama. Untuk N_manual > 0: error = |N_device − N_manual| / N_manual × 100%. Untuk diam, laporkan false steps per menit. Analisis Python memiliki pemeriksaan timing lebih ketat; jangan mengabaikan gap untuk memaksa hasil sama.

Belum diuji pada kit fisik. Validasi compile dan sinyal sintetis tidak membuktikan akurasi penghitungan langkah manusia.
