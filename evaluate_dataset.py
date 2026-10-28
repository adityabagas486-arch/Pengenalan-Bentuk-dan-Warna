"""Evaluasi gambar berdasarkan nama folder, tanpa manifest.csv."""

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from detector import Detector


BASE = Path(__file__).resolve().parent

BENTUK = {
    "segitiga",
    "persegi",
    "persegi_panjang",
    "lingkaran",
    "jajar_genjang",
    "trapesium",
}

WARNA = {
    "putih", "biru", "kuning", "merah", "hitam",
    "hijau", "coklat", "ungu", "pink",
}

EKSTENSI = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def normalisasi(teks):
    return "_".join(teks.strip().lower().split())


def baca_label(folder):
    """Contoh: persegi_panjang_biru -> persegi_panjang, biru."""
    nama = normalisasi(folder)

    if "_" not in nama:
        raise ValueError(f"Nama folder tidak sesuai: {folder}")

    bentuk, warna = nama.rsplit("_", 1)

    if bentuk not in BENTUK or warna not in WARNA:
        raise ValueError(
            f"Label folder tidak dikenal: {folder}. "
            "Gunakan pola seperti persegi_panjang_biru."
        )

    return bentuk, warna


def baca_gambar(path):
    # Mendukung nama/path Windows yang mengandung karakter non-ASCII.
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=Path,
        default=BASE / "dataset" / "test",
        help="Folder yang berisi subfolder bentuk_warna.",
    )
    args = parser.parse_args()

    dataset = args.dataset
    if not dataset.is_dir():
        raise SystemExit(f"Folder tidak ditemukan: {dataset}")

    # Baca semua gambar, termasuk yang baru ditambahkan.
    files = sorted(
        path for path in dataset.rglob("*")
        if path.is_file() and path.suffix.lower() in EKSTENSI
    )

    if not files:
        raise SystemExit("Tidak ada gambar dalam folder dataset.")

    # Validasi label sebelum evaluasi dimulai.
    samples = []
    for path in files:
        try:
            bentuk, warna = baca_label(path.parent.name)
        except ValueError as error:
            raise SystemExit(f"{error}\nLokasi: {path}") from error

        samples.append((path, bentuk, warna))

    cv2.setNumThreads(1)
    detector = Detector()

    predictions = []
    gagal_dibaca = []
    waktu_ms = []
    per_shape = defaultdict(Counter)

    for nomor, (path, bentuk, warna) in enumerate(samples, start=1):
        try:
            image = baca_gambar(path)
        except (OSError, ValueError, cv2.error):
            image = None

        if image is None:
            gagal_dibaca.append(str(path.relative_to(dataset)))
            print(f"[GAGAL DIBACA] {path.name}")
            continue

        mulai = time.perf_counter()
        detections = detector.detect(image)
        waktu_ms.append((time.perf_counter() - mulai) * 1000)

        if detections:
            pred_shape = normalisasi(detections[0]["shape"])
            pred_color = normalisasi(detections[0]["color"])
        else:
            pred_shape = "tidak_terdeteksi"
            pred_color = "tidak_terdeteksi"

        shape_ok = pred_shape == bentuk
        color_ok = pred_color == warna
        joint_ok = shape_ok and color_ok

        predictions.append({
            "path": str(path.relative_to(dataset)),
            "shape": bentuk,
            "color": warna,
            "pred_shape": pred_shape,
            "pred_color": pred_color,
            "shape_ok": int(shape_ok),
            "color_ok": int(color_ok),
            "joint_ok": int(joint_ok),
        })

        per_shape[bentuk]["n"] += 1
        per_shape[bentuk]["shape_ok"] += int(shape_ok)
        per_shape[bentuk]["joint_ok"] += int(joint_ok)

        if nomor % 100 == 0 or nomor == len(samples):
            print(f"Diproses: {nomor}/{len(samples)} gambar")

    if not predictions:
        raise SystemExit("Semua gambar gagal dibaca. Periksa file dataset.")

    n = len(predictions)
    shape_correct = sum(row["shape_ok"] for row in predictions)
    color_correct = sum(row["color_ok"] for row in predictions)
    joint_correct = sum(row["joint_ok"] for row in predictions)

    result = {
        "version": "automatic-v3-folder-evaluation",
        "dataset_directory": str(dataset.resolve()),
        "files_found": len(files),
        "n": n,
        "unreadable_count": len(gagal_dibaca),
        "unreadable_files": gagal_dibaca,
        "shape_correct": shape_correct,
        "color_correct": color_correct,
        "joint_correct": joint_correct,
        "shape_accuracy_percent": round(shape_correct / n * 100, 2),
        "color_accuracy_percent": round(color_correct / n * 100, 2),
        "joint_accuracy_percent": round(joint_correct / n * 100, 2),
        "per_shape": dict(per_shape),
        "median_ms": float(np.median(waktu_ms)),
        "p95_ms": float(np.percentile(waktu_ms, 95)),
        "opencv": cv2.__version__,
        "scope": (
            "Evaluasi gambar berdasarkan label folder. "
            "Bukan training dan bukan pengukuran akurasi webcam. "
            "File tidak terbaca dilaporkan terpisah dan dikeluarkan "
            "dari perhitungan ketepatan."
        ),
    }

    output = BASE / "hasil_uji"
    output.mkdir(exist_ok=True)

    with (output / "dataset_predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=list(predictions[0]))
        writer.writeheader()
        writer.writerows(predictions)

    (output / "dataset_metrics.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nHasil tersimpan di: {output}")


if __name__ == "__main__":
    main()