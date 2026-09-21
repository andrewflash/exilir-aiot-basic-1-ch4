# Hands-on: dari IMU ke penghitung langkah

Target 45–60 menit, kelompok dua orang. Hasil: CSV mentah enam kanal, metadata, CSV aktivitas tiga kanal, grafik, serta evaluasi hitungan. Dasar kode: `../../../Chapter_3/Baca_IMU_Library/Baca_IMU_Library.ino`; sketch lama tidak diubah.

## 1. Siapkan board

Gunakan ESP32-C5 dengan MPU6050 yang sudah diverifikasi, SDA GPIO2, SCL GPIO3, alamat 0x68 sesuai kode sebelumnya. WHO_AM_I harus 0x68. MPU6500 memerlukan driver yang sesuai; jangan hanya mengganti angka identitas agar pemeriksaan lolos.

Arduino IDE: install board package **esp32 by Espressif Systems** dan library **Adafruit MPU6050**, **Adafruit Unified Sensor**, **Adafruit BusIO**. Pilih model board aktual; proyek sebelumnya menunjuk DFRobot FireBeetle 2 ESP32-C5. Pilih port yang muncul ketika board dihubungkan. Pengaturan USB CDC/port mengikuti jalur USB board yang dipakai; gunakan konfigurasi yang berhasil pada Chapter 3.

Buka `Exilir_IMU_Logger/Exilir_IMU_Logger.ino`, compile lalu upload. Buka Serial Monitor 115200 sementara untuk diagnosis. Bila muncul `#ERROR`, cek identitas sensor, kabel/pin, daya dan alamat. Logger Python juga akan menangkap pesan error ini. **Tutup Serial Monitor sebelum menjalankan Python.**

Perubahan dari Chapter 3: target 50 Hz, filter hardware 10 Hz, rentang ±8 g, boot Serial dibatasi 2 detik, sensor identity check, sesi dimulai dengan perintah `s`, baseline 3 detik, aktivitas 20 detik, dan penanda protokol. Timestamp dibuat saat awal pembacaan sensor; data tidak diberi waktu berdasarkan kedatangan USB. Ini polling terjadwal, bukan akuisisi FIFO hardware yang menjamin zero jitter.

## 2. Rekam satu sesi

Dari terminal PowerShell pada folder `Slide/lab`:

```powershell
python -m pip install -r requirements.txt
python -m serial.tools.list_ports
python rekam_serial.py --port COM7 --subject P01 --session S01 --label walking_normal
```

Ganti `COM7` dengan port kit. Saat program menampilkan **DIAM**, pertahankan sensor diam selama 3 detik. Saat **MULAI**, peserta bergerak dan pengamat menghitung step. Hentikan hitungan ketika **SELESAI** muncul. Cue terminal memiliki latensi transport/reaksi manusia; untuk evaluasi timing presisi gunakan rekaman video atau anotasi tersinkron. Jangan menghitung baseline sebagai aktivitas.

Lab wajib memakai USB: gunakan stepping/jalan di tempat untuk demo terbatas atau amankan laptop dan kabel bersama pengamat. Jangan berjalan menjauh hingga kabel tertarik. Stepping di tempat bukan pengganti data berjalan normal; catat label `stepping_in_place` jika itu yang dilakukan. Untuk jalan di lintasan tanpa tambatan gunakan logger Wi-Fi yang dikembangkan pada latihan lanjutan. Power bank saja tidak menyimpan data dari sketch USB ini.

Output:

- `rekaman/walking_normal_P01_S01.csv`: seluruh 23 detik; header `timestamp,accX,accY,accZ,gyroX,gyroY,gyroZ`.
- `rekaman/walking_normal_P01_S01.activity.csv`: aktivitas saja, baseline dibuang, timestamp dimulai dari nol; tiga kanal akselerasi untuk latihan import Edge Impulse berikutnya.
- `rekaman/walking_normal_P01_S01.json`: subjek, sesi, posisi, label, rentang waktu dan kualitas sampling. Isi `reference_steps` berdasarkan pengamat.

Akselerasi dalam m/s², gyroscope dalam rad/s, timestamp dalam ms. Detector pada lab hanya memakai akselerasi. File activity masih perlu inspeksi timing sebelum training; script tidak diam-diam melakukan resampling. Label aktivitas ditentukan saat import, tidak menjadi kolom sensor. Gunakan ID sesi baru untuk setiap pengulangan; output sesi lama tidak ditimpa.

## 3. Kondisi eksperimen

Ambil `standing`, `stepping_slow`, `stepping_normal`, `stepping_fast`, `shaking_without_walking` untuk setup USB di tempat. Jika benar-benar berjalan di lintasan, gunakan label `walking_*`. Ulangi tiap kondisi tiga kali. Tetapkan lokasi awal pinggang. Pada percobaan goyang tanpa berjalan, dokumentasikan perubahan posisi jika sensor dilepas dan dipegang.

Gunakan beberapa sesi untuk tuning. Bekukan high/low/jeda/filter sebelum mengevaluasi sesi lain atau orang kedua. Catat label aktual, bukan label yang diharapkan detector.

## 4. Plot dan evaluasi

```powershell
python analisis_langkah.py rekaman/walking_normal_P01_S01.csv --reference 40
python analisis_langkah.py rekaman/walking_normal_P01_S01.csv --reference 40 --high 1.8 --min-interval 0.4
```

Ganti 40 dengan hitungan pengamat. Gunakan CSV mentah yang memiliki baseline, **bukan** `.activity.csv`. Baseline median tiga detik → magnitude dikurangi baseline → moving average kausal lima sampel → peak detector dengan high, low dan jeda minimum. PNG grafik dan `.hasil.json` dibuat di samping CSV. Analisis ulang sesi yang sama memperbarui hasil/grafik; salin hasil atau catat parameter di lembar eksperimen untuk perbandingan.

Untuk `standing` atau `shaking_without_walking`, pakai `--reference 0`: hasil berupa false steps/menit, bukan pembagian dengan nol. Referensi harus mencakup hanya interval aktivitas 20 detik. Puncak terakhir memerlukan sampel berikutnya untuk konfirmasi; kejadian tepat di batas akhir dapat terlewat.

## 5. Tugas dan kriteria selesai

- CSV lengkap kira-kira 1150 sampel; aktivitas kira-kira 1000 sampel pada target 50 Hz. Nilai aktual boleh berbeda jika ada keterlambatan; periksa gap, jangan mengarang data.
- Saat diam, magnitude mendekati 9,81 m/s² dan gyroscope mendekati nol. Periksa bias dan pemasangan jika jauh menyimpang.
- Semua interval ditargetkan 20 ms. Logger menandai interval di luar 18–22 ms; analyzer menolak timing di luar toleransi. Periksa beban Serial, konfigurasi USB dan sensor sebelum mengulang.
- Serahkan minimal lima kondisi, catatan hitungan manual, satu grafik, tabel hasil parameter yang dibekukan, dan penjelasan satu false positive serta satu false negative bila ditemukan. Tidak ada target akurasi universal yang dipaksakan.

## 6. Bonus nirkabel: mengembangkan Chapter 2

Gunakan `../../../Chapter_2/MQTT_Example/MQTT_Example.ino` sebagai referensi koneksi Wi-Fi/MQTT, bukan langsung sebagai logger IMU. Rancangan latihan: sampling → ring buffer → batch 25 sampel → topic unik per perangkat/sesi → subscriber laptop → CSV dengan header yang sama. Sertakan sequence dan timestamp sensor; deteksi kehilangan/duplikasi. Jaringan harus berada di luar jalur sampling. Setelah boot tanpa Serial dan logger penerima berhasil, barulah lepas USB laptop dan gunakan power bank. Bonus ini berupa rancangan tugas, **belum firmware Wi-Fi siap pakai**.

## Verifikasi

`python -m unittest discover -s lab -p test_lab.py` dijalankan dari folder Slide untuk memeriksa data sintetis, ekspor aktivitas, timing gap, serta parser. Status compile dicatat pada `VALIDASI.md`. Belum diuji pada kit fisik dan tidak ada firmware yang di-flash otomatis.

Referensi API resmi: [Adafruit basic readings](https://github.com/adafruit/Adafruit_MPU6050/blob/master/examples/basic_readings/basic_readings.ino) dan [header library](https://github.com/adafruit/Adafruit_MPU6050/blob/master/Adafruit_MPU6050.h).
