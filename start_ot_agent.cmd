@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Running setup_portable.ps1...
    powershell -NoProfile -ExecutionPolicy Bypass -File ".\setup_portable.ps1"
    if errorlevel 1 exit /b 1
)

call ".venv\Scripts\activate.bat"
set PYTHONUTF8=1
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
endlocal
