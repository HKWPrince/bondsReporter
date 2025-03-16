@echo off
echo Starting BondsReporter...
echo Please Wait...

:: 進入 Docker 目錄
cd docker

:: 關閉並重啟 Docker 服務
docker-compose down -v
docker-compose up --build -d

:: 返回專案根目錄
cd ..

:: 等待 5 秒，讓 Docker 啟動
timeout /t 5 /nobreak >nul

:: 檢查 Docker 是否正在運行
docker ps | findstr "mssql_container"
if %ERRORLEVEL% NEQ 0 (
    echo Docker services failed to start. Please check your Docker setup.
    pause
    exit /b 1
)

echo BondsReporter is running...
echo Available services:
docker ps --format "table {{.Names}}\t{{.Ports}}"

:: 確保 Python 存在
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b 1
)

:: 啟動 Flask 應用程式
echo Running Flask application...
python run.py

:: 等待使用者按鍵再關閉，防止視窗自動關閉
pause
