@echo off
echo ========================================
echo Starting Spam Detection System
echo ========================================

echo.
echo Starting UI Gateway (Auto-starts all services)...
echo.
echo Please wait 10 seconds for all services to initialize...
echo.

cd /d D:\Yash\samp-detection-v2\ui-gateway-service
python app.py

echo.
echo Services stopped.
pause

