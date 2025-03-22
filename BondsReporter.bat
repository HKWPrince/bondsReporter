@echo off
title BondsReporter Startup
chcp 65001 >nul  :: 支援 UTF-8 中文輸出

:: 設定顏色變數（使用 ANSI escape code）
set "ESC="
set "RESET=%ESC%[0m"
set "BOLD=%ESC%[1m"
set "GREEN=%ESC%[32m"
set "RED=%ESC%[31m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"
:: 顯示分隔線
set "LINE=-----------------------------------------------------------"

:: 1/5 Git Pull
echo %CYAN%%LINE%%RESET%
echo %BOLD%%CYAN% 1/5 Updating project from GitHub...%RESET%
git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo %RED% Git pull failed. Please check your network or repository settings. %RESET%
    pause
    exit /b 1
)

:: 2/5 Docker 狀態檢查
echo %CYAN%%LINE%%RESET%
echo %BOLD%%CYAN% 2/5 Checking if Docker is running...%RESET%

tasklist | findstr "Docker Desktop.exe" >nul
if %ERRORLEVEL% NEQ 0 (
    echo %YELLOW% Docker is not running. Starting Docker... %RESET%
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting for Docker to start...
    timeout /t 10 >nul
    
    :check_docker
    docker info >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Docker is still starting... waiting 5 more seconds...
        timeout /t 5 >nul
        goto check_docker
    )
)

echo %GREEN% Docker is running. Continuing... %RESET%

:: 3/5 Docker Compose
echo %CYAN%%LINE%%RESET%
echo %BOLD%%CYAN% 3/5 Rebuilding Docker containers...%RESET%

cd docker
docker-compose down -v
docker-compose up --build -d
cd ..

timeout /t 5 >nul

:: 4/5 Docker 容器檢查
docker ps | findstr "mssql_container" >nul
if %ERRORLEVEL% NEQ 0 (
    echo %RED% Docker services failed to start. %RESET%
    pause
    exit /b 1
)
:: 3/5 Docker Compose
echo %CYAN%%LINE%%RESET%
echo %BOLD%%CYAN% 4/5 Python is running...%RESET%
echo %CYAN%%LINE%%RESET%

:: Python 檢查
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo %RED% Python is not installed. Please install Python and try again. %RESET%
    pause
    exit /b 1
)

:: 5/5 啟動 Flask
echo %CYAN%%LINE%%RESET%
echo %BOLD%%CYAN% 5/5 Starting BondsReporter...%RESET%
echo %GREEN% Flask is running. Press Ctrl+C to stop and clean up.%RESET%
echo %CYAN%%LINE%%RESET%

:: === 啟動 Flask & 等待 Ctrl+C ===
:: 使用 CALL 讓 Ctrl+C 結束後還能繼續往下走
call python run.py

:: 自動關閉 Docker 容器
echo %YELLOW% Shutting down Docker containers...%RESET%
cd docker
docker-compose down
cd ..

echo %GREEN% BondsReporter is running...%RESET%
echo %GREEN% Please open browser then enter the address below%RESET%
echo %GREEN% http://127.0.0.1:5000 %RESET%
:: 等待 5 秒
timeout /t 5 /nobreak >nul
echo %CYAN%%LINE%%RESET%
echo %BOLD%%CYAN% If you wan to leave BondsReporter...%RESET%
echo %RED%Press Ctrl+C to stop and clean up.%RESET%
echo %CYAN%%LINE%%RESET%
pause
