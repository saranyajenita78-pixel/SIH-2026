@echo off
setlocal enabledelayedexpansion
echo ============================================================
echo  PolarOps AI - Antarctic Station Intelligence Platform
echo  SETUP
echo ============================================================

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH. Install Python 3.11+ from
    echo         https://www.python.org/downloads/ and check "Add to PATH"
    echo         during installation, then re-run setup.bat.
    pause
    exit /b 1
)

echo.
echo [1/5] Creating virtual environment (.venv) ...
if not exist ".venv" (
    python -m venv .venv
) else (
    echo       .venv already exists, skipping.
)

echo.
echo [2/5] Activating virtual environment ...
call .venv\Scripts\activate.bat

echo.
echo [3/5] Installing dependencies from requirements.txt ...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed. See the message above.
    pause
    exit /b 1
)

echo.
echo [4/5] Preparing required directories ...
if not exist "data\raw\ncpor" mkdir "data\raw\ncpor"
if not exist "data\raw\ncpor\historical" mkdir "data\raw\ncpor\historical"
if not exist "data\raw\external" mkdir "data\raw\external"
if not exist "data\processed" mkdir "data\processed"
if not exist "data\simulated" mkdir "data\simulated"
if not exist "database" mkdir "database"
if not exist "models" mkdir "models"
if not exist "logs" mkdir "logs"
if not exist "assets\stations" mkdir "assets\stations"

echo.
echo [5/6] Initializing database and generating demo data ...
python scripts\initialize_database.py
python scripts\generate_demo_data.py
python scripts\build_model_artifacts.py

echo.
echo [6/6] Downloading station photos (optional, internet required) ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; $urls=@{ 'maitri_station.jpg'='https://4.bp.blogspot.com/-8joo9jaaIHo/U1Rw8jzlxQI/AAAAAAAAA0o/dLkP21YBmyk/s1600/DSCN0451.JPG'; 'bharati_station.jpg'='https://artisianhomes.com/wp-content/uploads/2022/11/Bharati-Antarctic-Research-Station-10.jpg' }; foreach($n in $urls.Keys){$dest=Join-Path 'assets\stations' $n; if(!(Test-Path $dest)){try{Invoke-WebRequest -Uri $urls[$n] -OutFile $dest -UseBasicParsing -TimeoutSec 20}catch{}}}"

echo.
echo ============================================================
echo  SETUP COMPLETE
echo  Next step: double-click run.bat to launch the dashboard.
echo ============================================================
pause
