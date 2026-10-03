@echo off
echo ========================================================
echo  Starting Multilingual Govt Scheme Finder Backend API
echo ========================================================
echo.
py -3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
