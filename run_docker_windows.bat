@echo off
setlocal
cd /d "%~dp0"
where docker >nul 2>nul || (echo Docker CLI not found. Install and start Docker Desktop. & exit /b 1)
docker info >nul 2>nul || (echo Docker Desktop is not ready. Start it and try again. & exit /b 1)
docker compose up -d --build --remove-orphans
if errorlevel 1 exit /b 1
echo IT2 checker: http://127.0.0.1:8501
echo Study models may need a few seconds to finish downloading.
