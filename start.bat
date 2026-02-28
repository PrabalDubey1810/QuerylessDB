@echo off
echo Starting MongoDB AI Application...

:: Kill existing python/node processes to cleanup ports (optional but helpful)
:: taskkill /F /IM python.exe /T 2>nul
:: taskkill /F /IM node.exe /T 2>nul

:: Start Backend
echo Starting Backend on Port 8000...
start "Backend API" cmd /k "C:\Users\praba\AppData\Local\Programs\Python\Python311\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload || pause"

:: Start Frontend
echo Starting Frontend on Port 5173...
start "Frontend UI" cmd /k "cd frontend && npm run dev || pause"

:: Wait a bit for servers to start
timeout /t 5

echo Application started!
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8000

:: Open Browser
start http://localhost:5173
pause
