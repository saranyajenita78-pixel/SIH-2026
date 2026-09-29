@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   POLAR TWIN SENTINEL - START
 echo ============================================================
echo Project: %CD%

echo.

if not exist "app.py" (
  echo [ERROR] app.py not found. This launcher must stay in the project root.
  pause
  exit /b 1
)

python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
  echo Streamlit is not installed. Installing project requirements...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
  )
)

echo.
echo Checking AI configuration...
python -c "from src.ai.copilot import is_configured; print('OpenAI AI Agent: CONNECTED' if is_configured() else 'OpenAI AI Agent: NOT CONFIGURED')"
echo.
echo Starting dashboard...
python -m streamlit run app.py
pause
