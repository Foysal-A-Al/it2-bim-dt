@echo off
REM Run this once from the Anaconda Prompt, inside the it2-bim-dt folder.
REM It creates (or updates) the conda environment "it2" and downloads the study models.
where conda >nul 2>nul || (echo conda not found. Open the Anaconda Prompt and run this file again. & exit /b 1)
call conda env list | findstr /B /C:"it2 " >nul
if %errorlevel%==0 (
  call conda env update -n it2 -f environment.yml --prune
) else (
  call conda env create -f environment.yml
)
call conda activate it2 || exit /b 1
python data\download.py
echo.
echo Setup finished. Start the app with:  run_app_windows.bat
