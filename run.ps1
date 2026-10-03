Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Starting Multilingual Govt Scheme Finder Backend API   " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access Swagger Documentation at: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host ""

py -3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
