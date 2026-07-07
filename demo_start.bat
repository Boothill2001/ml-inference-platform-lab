@echo off
setlocal enabledelayedexpansion

title ML Inference Platform Lab Demo
cd /d "%~dp0"

echo.
echo ============================================================
echo  ML Inference Platform Lab - Demo Launcher
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python 3.11+ and try again.
    pause
    exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.11+ is required.
    python --version
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [1/5] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/5] Virtual environment already exists.
)

echo [2/5] Activating virtual environment...
call ".venv\Scripts\activate.bat"

echo [3/5] Installing dependencies...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

if not exist "models\artifacts\churn_model_v1.joblib" (
    echo [4/5] Training demo models...
    python models\train_model.py
) else (
    echo [4/5] Model artifacts already exist.
)

echo [5/5] Starting API and dashboard...
echo.
echo Dashboard: http://127.0.0.1:8000
echo API docs:  http://127.0.0.1:8000/docs
echo Metrics:   http://127.0.0.1:8000/metrics
echo.
echo Keep this window open while presenting the demo.
echo Press CTRL+C in this window to stop the server.
echo.

start "" "http://127.0.0.1:8000"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
