# Konten slide hands-on lab
Pada deck v8: slide 38–47; total 53 slide.

## 1. Hands-on lab: dari IMU ke hitungan langkah
- Bekerja berpasangan: satu peserta bergerak, satu merekam dan menghitung.
- Hasil akhir: CSV + metadata + grafik + tabel evaluasi.
- Urutan: verifikasi sensor → rekam → plot → deteksi → evaluasi.
- Alokasi 45–60 menit; siapkan Python dan Arduino sebelum kelas.

Catatan pengajar: Lab memakai firmware USB sederhana. Untuk setup bertambat lakukan stepping di tempat dan beri label sesuai aktivitas aktual. Jalan di lintasan bebas menjadi latihan setelah logger nirkabel tersedia. Tidak melakukan training ML dalam lab ini.

## 2. Lab 1 • Lanjutkan kode pembacaan IMU Chapter 3
- Sketch baru: lab/Exilir_IMU_Logger/Exilir_IMU_Logger.ino
- ESP32-C5, SDA GPIO2, SCL GPIO3, alamat 0x68 sesuai proyek.
- Install Adafruit MPU6050, Unified Sensor, dan BusIO.
- Pilih board/port aktual, compile lalu upload. WHO_AM_I harus 0x68.

Catatan pengajar: Referensi: Chapter_3/Baca_IMU_Library. Kode sebelumnya mencampur nama MPU6500/MPU6050. Sketch ini secara eksplisit untuk MPU6050; jika sensor berbeda, gunakan driver yang benar. Baud 115200. Matikan Serial Monitor saat logger Python memakai port. Compile diuji terpisah dari upload; belum uji hardware.

## 3. Lab 2 • Konfigurasi akuisisi yang konsisten
- Target 50 Hz; pembacaan tiap 20 ms.
- Rentang ±8 g; filter hardware 10 Hz.
- Rekam akselerasi dan gyro; detector awal memakai akselerasi.
- Saat diam: magnitude sekitar 9,81 m/s²; gyro sekitar nol.

```text
Wire.begin(2, 3);
mpu.begin(0x68, &Wire);
mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
mpu.setGyroRange(MPU6050_RANGE_500_DEG);
mpu.setFilterBandwidth(MPU6050_BAND_10_HZ);
```

Catatan pengajar: Adafruit menghasilkan akselerasi dalam m/s² dan kecepatan rotasi dalam rad/s. Timestamp dibuat di perangkat pada awal pembacaan. Polling tetap memiliki jitter, sehingga interval aktual harus diperiksa. Snippet adalah konfigurasi; gunakan sketch lengkap untuk setup dan loop.

## 4. Lab 3 • Apa yang dilakukan loop logger?
- Tunggu perintah s untuk memulai sesi.
- Baca hanya ketika jadwal 20 ms tiba.
- Catat timestamp aktual dan keluarkan satu baris CSV.
- Akhiri setelah 23 detik; jangan membuat sampel palsu saat terlambat.

```text
sensors_event_t a, g, temperature;
mpu.getEvent(&a, &g, &temperature);
float t_ms = (micros() - started) / 1000.0;
// satu baris: waktu, ax, ay, az, gx, gy, gz
// a.acceleration.x  -> m/s2
// g.gyro.x          -> rad/s
```

Catatan pengajar: Ini potongan inti, bukan sketch mandiri; penjadwalan dan penanda BEGIN/ACTIVITY/END ada di file .ino lengkap. Header: timestamp,accX,accY,accZ,gyroX,gyroY,gyroZ. Serial.print menulis kanal lainnya dalam sketch lengkap. Timestamp dari micros() dikonversi menjadi milidetik relatif.

## 5. Lab 4 • Simpan rekaman ke CSV di laptop
- Jalankan perintah dari folder Slide/lab.
- Tutup Serial Monitor; ganti COM7 dengan port kit.
- DIAM: baseline 3 detik. MULAI: aktivitas dan hitungan 20 detik.
- Output disimpan ke folder rekaman; gunakan ID sesi baru.

```text
python -m pip install -r requirements.txt
python -m serial.tools.list_ports
python rekam_serial.py --port COM7 --subject P01 --session S01 --label stepping_in_place
```

Catatan pengajar: Pasang dependensi sekali sebelum kelas. Script mengirim s secara otomatis. Cue terminal memiliki latensi USB dan reaksi pengamat. Untuk referensi waktu yang presisi gunakan video tersinkron. Contoh ini memakai stepping_in_place, karena firmware USB masih bertambat.

## 6. Lab 5 • Periksa tiga berkas hasil
- *.csv: 23 detik penuh, enam kanal + timestamp.
- *.activity.csv: 20 detik aktivitas, hanya tiga kanal akselerasi.
- *.json: subjek, sesi, label, posisi, dan kualitas sampling.
- Isi reference_steps sesuai pengamat; baseline tidak ikut dihitung.

Catatan pengajar: CSV aktivitas membuang bagian baseline dan mengembalikan timestamp awal ke nol; cocok untuk latihan import berikutnya setelah timing diperiksa. Label tidak menjadi kolom numerik sensor. Jangan menganalisis .activity.csv dengan analyzer baseline. Frekuensi nyata dihitung dari selisih timestamp; logger menandai interval di luar 18–22 ms. Satuan dan kanal harus tetap konsisten.

## 7. Lab 6 • Plot sinyal dan jalankan peak detector
- Gunakan CSV mentah yang masih memiliki baseline.
- Median baseline → magnitude → moving average lima sampel.
- Awal: T_high=1,2; T_low=0,3 m/s²; τ_min=0,30 detik.
- Buka *.plot.png dan *.hasil.json; tandai puncak salah atau hilang.

```text
python analisis_langkah.py rekaman/stepping_in_place_P01_S01.csv --reference 40

# Setelah tuning pada data latihan:
# tambahkan --high 1.8 --min-interval 0.4
```

Catatan pengajar: Ganti 40 dengan hitungan aktual pengamat. Analisis menghasilkan count dan error relatif jika reference >0. Untuk reference 0 gunakan false steps/menit. Analyzer menolak timestamp terlalu tidak teratur; periksa logger, jangan memaksa lanjut. Kelima sampel filtering pada 50Hz setara jendela100ms; ada delay yang perlu dipahami.

## 8. Lab 7 • Uji lima kondisi, ulangi tiga kali
- Diam; stepping pelan; stepping biasa; stepping cepat.
- Goyang tanpa berjalan sebagai contoh aktivitas pengganggu.
- Bekukan parameter setelah tuning; uji sesi baru dan orang kedua.
- Catat posisi sensor dan aktivitas aktual pada setiap rekaman.

Catatan pengajar: Jika melakukan jalan di lintasan dengan setup yang memadai, ganti label stepping menjadi walking; jangan menyamakan kedua domain. Jangan membandingkan parameter hanya pada satu rekaman. Gunakan template_hasil.csv untuk jumlah manual/prediksi dan konfigurasi. Untuk goyangan setelah sensor dilepas, posisi menjadi hand; metadata harus mencerminkannya.

## 9. Lab 8 • Apa yang harus dikumpulkan?
- CSV, metadata, dan satu grafik yang sudah diberi penjelasan.
- Tabel N_ref, N_pred, error, threshold, jeda, dan filter.
- Contoh kasus berhasil serta kegagalan yang ditemukan.
- Kesimpulan: aturan cukup, perlu perbaikan, atau layak mencoba ML?

Catatan pengajar: Kriteria: data lengkap, timestamp masuk akal, baseline benar-benar diam, hitungan pada interval sama, set uji tidak dipakai untuk tuning. Tidak menetapkan persentase akurasi universal. Peserta harus menjelaskan alasan salah hitung; ML adalah hipotesis perbaikan yang perlu diuji, bukan jawaban otomatis.

## 10. Bonus • Ubah logger menjadi nirkabel
- Referensi koneksi: Chapter_2/MQTT_Example.
- Sampling → ring buffer → batch → MQTT → CSV laptop.
- Tambahkan session_id, sequence, dan timestamp sensor.
- Setelah logger bekerja tanpa USB, gunakan power bank.

Catatan pengajar: Bonus masih rancangan pengembangan, bukan firmware Wi-Fi siap pakai. Sketch lab USB tidak menyimpan data ketika hanya diberi power bank. Pisahkan akuisisi dari jaringan, deteksi buffer overflow dan paket hilang/duplikat. Uji end-to-end sebelum berjalan bebas. Di sesi selanjutnya file aktivitas yang sudah diperiksa dapat diimpor ke Edge Impulse.