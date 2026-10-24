# Bentuk dan Warna — OTOMATIS v3

Versi ini menggantikan cara penggunaan main.py lama dan webcam_interaktif.py.
Buka aplikasi, lalu tunjukkan benda. Tidak ada klik warna, tombol kalibrasi W,
atau kotak kecil yang harus diikuti. Objek dicari ulang pada setiap frame.

## Cara paling mudah (Windows)
1. Ekstrak ZIP ke folder baru. Jangan mencampurnya dengan folder versi lama.
2. Buka folder OpenCV_Automatis.
3. Klik dua kali INSTALL_WINDOWS.bat. Langkah ini hanya perlu dilakukan sekali;
   instalasi membutuhkan Python desktop dan internet.
4. Klik dua kali MULAI_WINDOWS.bat untuk membuka kamera.
5. Judul jendela harus **Bentuk dan Warna - OTOMATIS v3**.
6. Tunjukkan benda. Tidak perlu menjalankan file .py lain satu per satu.

Nama bentuk dan warna ditampilkan besar di bawah kamera. Satu objek utama
terbesar diprioritaskan agar tampilan mudah dibaca. Bentuk di latar juga bisa
terpilih; sistem belum mengetahui secara semantik benda mana yang dipegang.

## Terminal (alternatif)
```bash
python -m pip install -r requirements.txt
python main.py
```
Bila kamera salah atau tidak terbuka:
```bash
python main.py --camera 1
```
Tutup Zoom/Meet atau aplikasi kamera lain. Aplikasi perlu dijalankan secara
lokal, bukan di Google Colab. Jangan memasang paket headless untuk tampilan GUI.
Paket diuji pada Python 3.12 dan OpenCV 4.12.0; instalasi memakai rentang versi
kompatibel agar pip dapat memilih paket untuk interpreter pengguna. Jika Python
terbaru gagal memasang dependensi, gunakan Python 3.12 64-bit.

## Tombol tambahan (tidak diperlukan untuk deteksi)
- Q/Esc atau tombol X: keluar.
- S: simpan input, output, dan JSON ke folder hasil.
- R: mulai/akhiri video MP4 tanpa audio. Untuk narasi demo, gunakan screen recorder.
- Tiga objek terpisah: jalankan `python main.py --max-objects 3`.

## Target
Segitiga, persegi, persegi panjang, lingkaran, jajar genjang, trapesium.
Putih, biru, kuning, merah, hitam, hijau, coklat, ungu, pink.
Warna dominan dibaca dari bagian dalam bentuk. Sampul dengan beberapa warna
bisa menghasilkan Multicolor. Warna di luar rentang dapat menjadi Warna Belum
Pasti. Putih dalam kondisi redup/bergeser warna ditandai (?) atau (perkiraan).
Tidak ada pemaksaan semua objek menjadi salah satu warna target.

## Perubahan teknis
- Beberapa mask HSV dan jalur tepi Canny mencari kandidat secara otomatis.
- Kandidat dari semua jalur digabung dan deteksi tumpang tindih disaring.
- Convex hull dipakai hanya bila solidity minimal 0,88, untuk toleransi cekungan
  kecil. Ini bukan pemulihan objek yang tertutup banyak atau model pemisah tangan.
- Bentuk ditentukan dari sudut, perbandingan sisi, kesejajaran, dan circularity.
- Pembacaan warna di dalam polygon mengurangi campuran piksel batas.
- Pencocokan bounding box dan voting singkat membantu kestabilan label.
- Deteksi yang hilang tidak tetap digambar sebagai hasil lama; pergantian warna
  mereset riwayat warna sehingga label sebelumnya tidak terus ditampilkan.

## Batas kemampuan yang perlu dipahami
Ini adalah prototipe otomatis berbasis OpenCV klasik, **bukan model deep learning
terlatih pada benda yang dipegang**. Tidak ada bobot model baru atau training foto
nyata dalam paket. Versi ini memperbaiki kemudahan penggunaan dan kasus yang
tersedia, tetapi belum terbukti andal untuk semua anak, benda, ruangan, dan kamera.

Kontur yang terlihat digunakan untuk menilai bentuk 2D. Persegi yang sangat
miring dapat terlihat seperti jajar genjang atau trapesium. Benda berbentuk bulat
3D tidak otomatis dapat diberi label lingkaran dari semua sudut. Tangan yang
menutup banyak sisi, blur berat, objek transparan, warna serupa dengan latar,
dan latar dengan banyak bentuk geometris masih dapat menyebabkan salah deteksi.
Warna putih/abu-abu/biru muda serta kuning gelap/coklat dapat ambigu tanpa
referensi warna. Tidak ada jaminan warna fisik asli dapat dipulihkan dari kamera.

Gambar arsiran pena di kertas bergaris belum menjadi skenario yang didukung
secara andal. Area arsiran bisa dianggap memiliki warna dominan kertas. Jangan
menggunakan hasilnya sebagai contoh pengenalan tinta yang sudah berhasil.

## Dataset dan pengujian
Subset test dari _output_.zip disertakan: 3.840 gambar sintetis, enam bentuk,
delapan label warna. Tidak ada kelas putih. Dataset ini dipakai untuk evaluasi,
bukan melatih model yang memahami benda nyata. manifest.csv mempertahankan
jalur asal dan SHA-256 sampel. Label kuning sumber mencakup oranye; label sumber
tidak diubah untuk menaikkan skor. Sumber pencipta dan lisensi asli belum tersedia.

```bash
python evaluate_dataset.py
python test_detector.py
```
Angka versi baru ada di hasil_uji/dataset_metrics.json. Subset telah dipakai
untuk memeriksa perbaikan selama pengembangan, sehingga bukan evaluasi
independen final. Angka versi sebelumnya
95,18% dan 89,32% tidak boleh dipakai untuk mengklaim akurasi versi ini.
controlled_tests.json berisi uji gambar buatan serta perilaku pergantian objek.
screenshot_checks.json berisi uji pengembangan pada screenshot pengguna dan
transformasi digitalnya; screenshot tidak dimasukkan ke paket. Kasus tersebut
bukan uji independen atau bukti kamera live. Pengujian lokal GUI/kamera Windows
belum dilakukan di lingkungan penyusun kode.

Mode gambar (opsional):
```bash
python main.py --image "contoh.png" --output "hasil/contoh.png"
```
Jangan menjalankan perintah ini tanpa mengganti contoh.png dengan file yang ada.

## Pembaruan laporan
Lihat CATATAN_LAPORAN.md. Laporan PDF lama menjelaskan versi sebelumnya.
Rekam pemakaian nyata, simpan screenshot S, dan isi template_uji_webcam.csv
sebelum menyatakan bahwa prototipe berhasil pada perangkat kelompok.

## Anggota
- M. Bagas Aditya — 5026241011
- Anastasia Azzahra Rafif — 5026241036
- Muhammad Rafi Aryandono — 5026241150
- Raffly Faizal Altariq — 5026241158

Kode disusun dengan bantuan ChatGPT/Codex dan perlu ditinjau serta dipahami
kelompok. Kontribusi aktual anggota tidak diasumsikan dari nama.

Referensi API:
https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html
https://docs.opencv.org/4.x/da/d97/tutorial_threshold_inRange.html
