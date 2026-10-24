@echo off
setlocal
cd /d "%~dp0"
echo Menyiapkan aplikasi Bentuk dan Warna...
where py >nul 2>&1
if errorlevel 1 (
    python -m venv .venv
) else (
    py -3 -m venv .venv
)
if errorlevel 1 goto gagal
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto gagal
echo Instalasi selesai. Buka MULAI_WINDOWS.bat untuk menjalankan kamera.
pause
exit /b 0
:gagal
echo Instalasi gagal. Pastikan Python desktop terpasang dan internet aktif.
echo Jika versi Python belum didukung paket, gunakan Python 3.12 64-bit.
pause
exit /b 1
