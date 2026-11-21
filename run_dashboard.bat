@echo off
cd /d "%~dp0"
echo Installing required libraries (first run only)...
python -m pip install -r requirements.txt
echo Starting the dashboard. Close this window to stop it.
python -m streamlit run app.py
pause
