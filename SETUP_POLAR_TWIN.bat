@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   POLAR TWIN SENTINEL - SETUP
echo ============================================================
echo Project: %CD%
echo.

if not exist "app.py" (
  echo [ERROR] app.py not found. Run this file from the project folder.
  pause
  exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python is not installed or not added to PATH.
  echo Install Python 3.10+ and enable "Add Python to PATH".
  pause
  exit /b 1
)

echo Installing required Python packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Dependency installation failed.
  pause
  exit /b 1
)

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo.
  echo Created .env from .env.example.
  echo IMPORTANT: Open .env and replace the placeholder API key with YOUR OWN key.
) else (
  echo.
  echo Existing .env found - it was NOT overwritten.
)

echo.
echo ============================================================
echo SETUP COMPLETE
echo ============================================================
echo Next: edit .env, save it, then double-click START_POLAR_TWIN.bat
echo ============================================================
pause
