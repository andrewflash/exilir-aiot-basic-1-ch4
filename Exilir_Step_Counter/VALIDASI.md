# Validasi counting

- Compile target esp32:esp32:dfrobot_firebeetle2_esp32c5, core3.3.11, Adafruit MPU6050 2.2.9: berhasil. Program336.088 byte; global RAM19.312 byte.
- Header detector kedua sketch identik.
- test_step_detector.cpp menguji implementasi C++ asli: diam0, sintetis2Hz selama20detik=40, amplitudo rendah0, refractory, gap, reset, baseline belum selesai dan sampel kalibrasi kurang: lulus.
- Tes native menggunakan Clang lokal dengan flag -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH karena versi header MSVC lebih baru. Kedua sketch juga dikompilasi memakai toolchain ESP32 sebenarnya.
- test_softap_ui.py: count muncul, tetap setelah Stop, kembali0 saat Start; browser Chrome dengan HTTP mock. Screenshot bukan data kit.
- Tiga tes analyzer Python sebelumnya tetap lulus.
- Tidak ada flash atau pengujian perangkat fisik; akurasi manusia dan timing Wi-Fi belum divalidasi.
