@echo off
REM Starts the IT2 checker in your browser. Run from the Anaconda Prompt inside it2-bim-dt.
call conda activate it2 || (echo Run setup_windows.bat first. & exit /b 1)
streamlit run app\app.py
