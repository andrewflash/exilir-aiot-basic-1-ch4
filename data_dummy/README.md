# Data dummy untuk latihan threshold

**Semua data di folder ini sintetis, bukan hasil rekaman MPU6050 atau manusia.** Cocok untuk memahami kode, plotting, parameter, dan kesalahan detector. Bukan benchmark akurasi manusia atau dataset training model produksi.

Unduh paket `Data_Dummy_Langkah_Exilir.zip` di folder Slide. Ringkasan visual tersedia pada `ringkasan_skenario.png`; hasil perhitungan ada pada `ringkasan.csv` dan `kunci_eksperimen.csv`.

## Format

- `*.csv` tanpa akhiran tambahan: rekaman 23 detik, target50Hz (1150 sampel), 3 detik diam + 20 detik aktivitas. Kolom sama dengan logger: `timestamp,accX,accY,accZ,gyroX,gyroY,gyroZ`. Timestamp ms, akselerasi m/s², gyro rad/s. Kasus08 sengaja kehilangan10sampel.
- `*.activity.csv`: hanya aktivitas, timestamp kembali0, tiga kanal akselerasi. Untuk latihan import CSV pada sesi berikutnya; jangan gunakan untuk analyzer yang memerlukan baseline. Kasus08 masih memiliki gap dan tidak siap langsung dipakai.
- `*.events.csv`: waktu puncak ideal yang didefinisikan sebagai langkah dalam model. Ini bukan label kontak kaki hasil pengukuran. Waktu mengacu CSV lengkap termasuk baseline; kurangi3000ms jika dibandingkan dengan CSV aktivitas. Goyangan dan diam tidak mempunyai event langkah.
- `*.metadata.json`: sumber sintetis, satuan, referensi, dan hasil default detector.
- Gyro sengaja nol karena tidak dimodelkan. Tidak cocok untuk menjelaskan sinyal gyro atau perbedaan aktivitas dengan gyro.

## Delapan skenario

| Kasus | Referensi sintetis | Pelajaran |
|---|---:|---|
| 01 diam | 0 | Noise kecil tidak harus dihitung |
| 02 langkah teratur | 40 | Jalur dasar, 2 siklus/detik |
| 03 langkah pelan lemah | 24 | Threshold tinggi melewatkan puncak kecil |
| 04 langkah cepat | 60 | Jeda minimum terlalu besar melewatkan langkah |
| 05 goyangan bukan langkah | 0 | Pola periodik bisa menjadi false positive |
| 06 sensor miring | 40 | Rotasi sumbu tetap mengubah XYZ, tetapi magnitude tetap |
| 07 amplitudo berubah | 40 | Satu threshold belum tentu sesuai sepanjang sesi |
| 08 sampel hilang | 40 | Periksa timestamp; analyzer menolak gap |

Kasus02 dan05 **sengaja memiliki CSV identik dengan label skenario berbeda** untuk menunjukkan keterbatasan informasi: aturan maupun ML tidak dapat membedakan input identik secara andal. Pada kit nyata, kumpulkan data beragam dan cari informasi tambahan yang memang membedakan aktivitas; ML tidak otomatis memperbaiki masalah ini. Kasus06 adalah rotasi koordinat konstan, bukan perubahan orientasi dinamis pada manusia.

## Praktik 20–30 menit tanpa kit

Jalankan dari folder `Slide/lab` (atau folder ekstraksi ZIP):

```powershell
python -m pip install -r requirements.txt
python analisis_langkah.py data_dummy/02_langkah_teratur.csv --reference 40
python analisis_langkah.py data_dummy/03_langkah_pelan_lemah.csv --reference 24
python analisis_langkah.py data_dummy/03_langkah_pelan_lemah.csv --reference 24 --high 0.6
python analisis_langkah.py data_dummy/04_langkah_cepat.csv --reference 60 --min-interval 0.5
python analisis_langkah.py data_dummy/05_goyangan_bukan_langkah.csv --reference 0
python analisis_langkah.py data_dummy/08_sampel_hilang.csv --reference 40
```

Perintah terakhir **diharapkan gagal** karena interval sampling tidak memenuhi pemeriksaan. Jangan mengubah timestamp agar terlihat normal; identifikasi gap pada file asli. Perintah lain menghasilkan `.plot.png` dan `.hasil.json`. Eksekusi ulang pada CSV sama menimpa kedua hasil tersebut: salin hasil ke nama lain sebelum mengganti parameter jika ingin membandingkan.

Tugas peserta:

1. Prediksi hasil sebelum menjalankan detector; buka grafik setelahnya.
2. Bandingkan threshold1,2 dengan0,6 m/s² pada langkah lemah. Apa risiko jika diturunkan pada data nyata yang lebih berisik?
3. Bandingkan jeda300ms dengan500ms pada langkah cepat.
4. Bandingkan XYZ dan magnitude kasus02 versus06.
5. Jelaskan mengapa goyangan dihitung walau referensinya0. Untuk diam/goyangan gunakan false steps/menit, bukan persentase dengan penyebut0.
6. Catat parameter, referensi, prediksi, dan jenis kesalahan; bandingkan dengan `kunci_eksperimen.csv` setelah eksperimen.

## Reproduksi dan batas model

`python generate_data_dummy.py` membuat ulang data dengan seed42, grafik ringkasan, kunci, dan ZIP. Dependensi: requirements.txt yang disertakan. Generator menimpa artefak dengan nama sama. Referensi berasal dari jumlah siklus model, bukan keluaran detector. Model terdiri dari gravitasi konstan + sinusoidal + noise kecil, dengan komponen lateral kecil. Tidak mencakup biomekanika, variasi pengguna, benturan kompleks, drift, clipping sensor, atau timing Wi-Fi nyata. Grafik kasus08 menampilkan magnitude mentah dikurangi gravitasi; kasus lainnya menampilkan hasil filter.

Untuk sesi Edge Impulse, file aktivitas dapat dipakai memahami alur import setelah timing diperiksa, tetapi gunakan data manusia untuk pelatihan/evaluasi yang bermakna. File-file ini berasal dari model dan noise yang sama; membaginya acak menjadi train/test memberikan kesan generalisasi yang menyesatkan. Jangan menafsirkan nilai akurasi sintetis sebagai performa kit.
