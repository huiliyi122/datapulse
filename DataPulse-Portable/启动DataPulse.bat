@echo off
title DataPulse v0.3.3
set "DATAPULSE_PORTABLE=true"
set "PYTHONIOENCODING=utf-8"
set "PATH=%~dp0;%~dp0Library\bin;%~dp0Library\mingw-w64\bin;%~dp0Scripts;%PATH%"
set "PYTHONHOME=%~dp0"

echo ================================================
echo   DataPulse v0.3.3
echo   Opening http://127.0.0.1:8000
echo   Press Ctrl+C to stop
echo ================================================

"%~dp0python.exe" "%~dp0launch.py"

pause
