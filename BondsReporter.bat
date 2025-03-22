@echo off
echo 1/5 Updating project from GitHub...
git pull origin main


if %ERRORLEVEL% NEQ 0 (
    echo Git pull failed. Please check your network or repository settings.
    pause
    exit /b 1
)


echo 2/5 Checking if Docker is running...

:: 嘗試取得 Docker 服務狀態
tasklist | findstr "Docker Desktop.exe" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Docker is not running. Starting Docker...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    echo Waiting for Docker to start...
    timeout /t 10 >nul
    
    :check_docker
    docker info >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Docker is still starting, waiting 5 more seconds...
        timeout /t 5 >nul
        goto check_docker
    )
)

echo 3/5 Docker is running. Continuing execution...

:: 進入 Docker 目錄
cd docker

:: 關閉並重啟 Docker 容器
docker-compose down -v
docker-compose up --build -d

:: 返回專案根目錄
cd ..

:: 等待 5 秒，確保 Docker 服務啟動
timeout /t 5 /nobreak >nul

:: 檢查 Docker 容器是否運行
docker ps | findstr "mssql_container" >nul
if %ERRORLEVEL% NEQ 0 (
    echo 4/5 Docker services failed to start. Please check your Docker setup.
    pause
    exit /b 1
)

:: 確保 Python 存在
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b 1
)

:: 啟動 Flask 應用程式 (在新 cmd 窗口執行)
start cmd /k python run.py
echo 5/5 BondsReporter is running...
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