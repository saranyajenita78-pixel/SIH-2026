@echo off
echo ============================================================
echo  PolarOps AI - Antarctic Station Intelligence Platform
echo  STARTING DASHBOARD
echo ============================================================

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

if not exist "database\antarctic.db" (
    echo Database not found - initializing now ...
    python scripts\initialize_database.py
    python scripts\generate_demo_data.py
)

echo.
echo Launching Streamlit ... your browser will open automatically.
echo Press CTRL+C in this window to stop the application.
echo.

streamlit run app.py

pause
