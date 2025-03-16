@echo off
echo Starting BondsReporter...
echo Please Wait...

:: 啟動 Docker Compose
cd docker
docker-compose down -v
docker-compose up --build -d
cd ..

:: 檢查 Python 是否安裝
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python and try again.
    exit /b 1
)

:: 啟動 Flask 應用程式 (在新 cmd 窗口執行)
start cmd /k python run.py

:: 檢查 Docker 是否正在運行
timeout /t 5 >nul
docker ps | findstr "mssql_container"
if %ERRORLEVEL% NEQ 0 (
    echo Docker services failed to start. Please check your Docker setup.
    exit /b 1
)

echo Docker services are running.
echo Available services:


:: 等待 cmd 視窗關閉，然後停止 Docker 容器
:loop
tasklist | findstr "python.exe" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Closing Docker services...
    docker-compose down
    exit
)
timeout /t 3 >nul
goto loop