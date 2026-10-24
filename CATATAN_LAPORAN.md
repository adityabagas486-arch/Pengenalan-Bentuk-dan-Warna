# Catatan pembaruan laporan — otomatis v3

Versi terbaru menggunakan deteksi otomatis setiap frame melalui beberapa mask HSV
serta tepi Canny, seleksi kontur, estimasi warna dominan, dan stabilisasi label.
Tidak ada pemilihan warna melalui klik, kalibrasi W, atau pembatasan area scan kecil.
Pustaka tetap OpenCV dan NumPy. Tidak ada model deep learning yang dilatih.

Hasil eksekusi versi ini pada 3.840 gambar subset sumber:
- Bentuk sesuai label: 3669/3.840 (95.55%).
- Bentuk dan warna sesuai label: 3443/3.840 (89.66%).
- Median waktu detektor pada 224x224: 1.97 ms; tidak termasuk kamera/GUI.

Data tersebut telah diperiksa selama pengembangan dan tidak boleh diklaim sebagai
uji independen final. Hasil tidak dapat disamakan dengan akurasi webcam atau
keberhasilan penggunaan oleh anak. Lakukan pengujian baru pada foto/video nyata
yang tidak digunakan untuk memilih parameter.

Uji terkontrol: 162/162 kombinasi bentuk-warna/posisi/rotasi/terang lulus; enam
pemeriksaan perilaku lulus. Buku pada screenshot sumber dan variasi digitalnya
sesuai pada 9/10 kasus; satu gambar yang diredupkan 20% menghasilkan Jajar Genjang
Putih, bukan Persegi Panjang Putih. Spons pada screenshot menghasilkan Persegi
Panjang Kuning. Screenshot digunakan sebagai data pengembangan, bukan validasi
independen. GUI diuji dengan pengganti fungsi tampilan pada loop video 13 frame;
kamera Windows aktual belum diuji.

Perbarui bagian metode, implementasi, hasil, evaluasi, dan rencana pengujian di PDF
lama. Hapus keterangan klik/W jika mode tersebut tidak digunakan lagi. Ganti angka
versi lama dengan angka yang sesuai kode yang benar-benar dikumpulkan. Lampirkan
bukti webcam sendiri; jangan menyatakan hasil simulasi sebagai rekaman langsung.

Batasan: tidak memisahkan tangan dengan model khusus, masih sensitif pada oklusi
besar/perspektif, latar geometris bisa ikut terdeteksi, dan warna fisik tertentu
ambigu. Lingkaran di sini adalah bentuk tampak 2D. Versi ini belum membuktikan
bahwa kebutuhan semua benda yang dipegang telah terpenuhi.
