# Exilir SoftAP IMU Logger

Firmware Arduino untuk ESP32-C5 + **MPU6050 terverifikasi**. Handphone mengontrol Start/Stop dan mengunduh CSV melalui Wi-Fi lokal, tanpa router, internet, laptop saat merekam, microSD, atau PSRAM.

## Upload sekali dari laptop

1. Pertahankan `Exilir_SoftAP_Logger.ino` dan `web_page.h` dalam satu folder bernama `Exilir_SoftAP_Logger`.
2. Buka `.ino` di Arduino IDE. Gunakan board package esp32 by Espressif Systems; pilih model aktual (proyek referensi: DFRobot FireBeetle 2 ESP32-C5).
3. Install **Adafruit MPU6050**, **Adafruit Unified Sensor**, dan **Adafruit BusIO**. WiFi/WebServer sudah termasuk core ESP32.
4. SDA GPIO2, SCL GPIO3, alamat I²C 0x68 mengikuti Chapter 3. Sketch memeriksa WHO_AM_I=0x68. Jika kit ternyata MPU6500, gunakan driver yang benar; jangan melewati pemeriksaan identitas.
5. Compile/upload, lalu hubungkan port USB daya board ke power bank 5 V. Tidak ada penantian Serial yang menghambat boot tanpa laptop.

## Jalankan dari HP

1. Sambungkan Wi-Fi HP ke **Exilir-IMU-XXXX**. Empat digit terakhir membedakan kit.
2. Password kelas: **exilir12345** (bisa diubah pada `AP_PASSWORD`).
3. Pilih **tetap terhubung** jika HP memberi peringatan Wi-Fi tanpa internet. Buka **http://192.168.4.1** di browser, bukan HTTPS. Ini bukan captive portal otomatis.
4. Isi nama rekaman, misalnya `walking_P01_S01`; pilih durasi total **23 detik**.
5. Tekan **Start**. Diam selama 3 detik awal; saat status AKTIVITAS, mulai berjalan dan hitung langkah manual.
6. Tekan **Stop** kapan saja, atau biarkan berhenti otomatis sesuai durasi. Maksimum 30 detik / 1500 sampel.
7. Tekan **Download CSV — akselerasi** atau **Download CSV — akselerasi + gyro**. Simpan metadata juga. Periksa Downloads/File pada HP. Jika browser menampilkan berkas, gunakan menu simpan/bagikan.
8. Start berikutnya mengganti rekaman lama setelah konfirmasi. Pengunduhan dapat diulang selama rekaman belum diganti.

**Data hanya disimpan di RAM. Matikan/reset perangkat = rekaman hilang.** Download tidak otomatis menghapus data. Koneksi HP yang putus tidak menghentikan sampling; perangkat tetap berhenti pada batas durasi, dan HP dapat menyambung kembali untuk mengunduh.

## Format berkas

CSV akselerasi:

```csv
timestamp,accX,accY,accZ
0.000,0.12000,-0.05000,9.79000
20.000,0.13000,-0.04000,9.80000
```

Angka di atas hanya contoh format. CSV enam kanal menambahkan `gyroX,gyroY,gyroZ`. Timestamp dalam **ms relatif terhadap sampel pertama**, akselerasi **m/s²**, dan gyro **rad/s**. Label berada pada nama berkas/metadata, bukan kolom sensor. Semua CSV **masih mencakup baseline 3 detik**; crop baseline sebelum memberi label aktivitas tunggal untuk training.

Metadata mencatat label, jumlah sampel, durasi, frekuensi aktual rata-rata, jeda maksimum, slot terlewat, dan alasan berhenti. `buffer_full` berarti kapasitas normal tercapai, bukan error. `duration_limit` adalah batas waktu; `manual_stop` adalah Stop dari HP. Metadata bukan ground truth; catat hitungan manual dan posisi sensor secara terpisah.

Untuk analyzer lab sebelumnya: pilih 23 detik, simpan file CSV tiga/six axis di laptop, lalu:

```powershell
python lab/analisis_langkah.py walking_P01_S01_3axis.csv --reference 40
```

Ganti nama/path serta 40 dengan hitungan aktual. Analyzer lama mengharapkan baseline 3 detik + aktivitas 20 detik dan interval mendekati 20 ms. File yang dihentikan lebih awal, durasi lain, atau jitter besar perlu analisis sesuai durasi sebenarnya. Jangan menganggap semua file otomatis memenuhi prasyarat analyzer atau Edge Impulse.

## Cara kerja kode

```text
HP -- POST /start --> webserver --> aktifkan rekaman
Task sampling: MPU6050 setiap ~20 ms --> buffer RAM
HP -- POST /stop --> hentikan rekaman
HP -- GET /download --> buffer diubah menjadi CSV per potongan
```

- Buffer tetap 1500 × 28 byte ≈ 42 KB; tidak membangun satu String besar berisi seluruh CSV.
- Sampling di task FreeRTOS terpisah; webserver tetap dapat melayani Stop/status saat merekam.
- Mutex melindungi state dan penulisan buffer. Unduhan hanya boleh setelah Stop; Start tidak diproses selama handler unduh sedang berjalan.
- Timestamp berasal dari awal pembacaan sensor. Slot jadwal yang terlambat dilewati, tidak diganti sampel palsu. Polling I²C/RTOS masih bisa jitter; bukan sistem hard real-time.
- Rentang ±8 g, gyro ±500 deg/s, bandwidth filter 10 Hz, target 50 Hz. Identitas dicek saat boot; nilai finite dicek saat baca. Driver tidak menjamin semua gangguan bus saat berjalan dapat dikenali dari nilai data; periksa juga kualitas rekaman.
- Ponsel hanya polling status setiap sekitar 1 detik; cue baseline/aktivitas di layar bisa terlambat. Untuk ground truth waktu yang presisi gunakan video/sinkronisasi tambahan. Status sensor yang belum siap terlihat pada web; perbaiki koneksi kemudian reset.
- Hanya satu rekaman bersama untuk semua klien; gunakan satu operator per kit. Kontrol HTTP bersifat lokal pada SoftAP dengan password kelas, tanpa login pengguna terpisah.

## Endpoint untuk pengembangan

| Endpoint | Metode | Kegunaan |
|---|---|---|
| `/` | GET | Halaman HP |
| `/status` | GET | Status dan statistik JSON |
| `/start` | POST | Form `label`, `duration` (5–30 detik), `replace=1` untuk mengganti data lama |
| `/stop` | POST | Hentikan rekaman; aman dipanggil ulang |
| `/download?axes=3` | GET | CSV akselerasi |
| `/download?axes=6` | GET | CSV akselerasi + gyro |
| `/metadata` | GET | Metadata JSON setelah Stop |

## Troubleshooting

- Wi-Fi tidak terlihat: cek power bank tetap menyala, hasil upload, SSID suffix, dan konfigurasi board.
- Halaman tidak terbuka: ketik HTTP lengkap; tetap gunakan Wi-Fi tanpa internet. Matikan fitur perpindahan otomatis ke jaringan lain bila HP beralih sendiri.
- Sensor belum siap: cek MPU6050 vs MPU6500, pin I²C, alamat, dan restart setelah diperbaiki.
- Stop terlihat lambat: mungkin HP telah kehilangan koneksi. Rekaman tetap dibatasi otomatis, lalu data dapat diunduh setelah menyambung kembali.
- `missed_slots` bukan nol atau jeda maksimum jauh di atas 20 ms: periksa kualitas data; kurangi gangguan dan ulangi. Jangan mengklaim sampling seragam hanya karena targetnya 50 Hz.

Referensi proyek: `Chapter_3/Baca_IMU_Library` untuk IMU, `Chapter_2/MQTT_Example` untuk konteks jaringan. Sketch ini menggunakan SoftAP HTTP langsung, bukan MQTT. API resmi: [Espressif Wi-Fi](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html), [WebServer](https://github.com/espressif/arduino-esp32/tree/master/libraries/WebServer), [Adafruit MPU6050](https://github.com/adafruit/Adafruit_MPU6050).

Belum di-flash atau diuji pada kit fisik. Lihat `VALIDASI.md` untuk compile dan pengujian browser dengan perangkat simulasi.
