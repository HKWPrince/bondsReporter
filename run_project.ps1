Write-Host "Checking if Docker is running..."

# 檢查 Docker 進程是否運行
$dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if (-not $dockerProcess) {
    Write-Host "Docker is not running. Starting Docker..."
    Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe" -PassThru

    Write-Host "Waiting for Docker to start..."
    Start-Sleep -Seconds 10

    # 等待 Docker 啟動
    while (-not (docker info 2>$null)) {
        Write-Host "Docker is still starting, waiting 5 more seconds..."
        Start-Sleep -Seconds 5
    }
}

Write-Host "Docker is running. Continuing execution..."

# 進入 Docker 目錄
Set-Location -Path "docker"

# 關閉並重啟 Docker
docker-compose down -v
docker-compose up --build -d

# 返回專案根目錄
Set-Location -Path ".."

# 等待 5 秒，確保 Docker 服務啟動
Start-Sleep -Seconds 5

# 檢查 Docker 容器是否運行
if (-not (docker ps | Select-String "mssql_container")) {
    Write-Host "Docker services failed to start. Please check your Docker setup."
    pause
    exit
}

Write-Host "BondsReporter is running..."
Write-Host "Available services:"
docker ps --format "table {{.Names}}\t{{.Ports}}"

# 確保 Python 存在
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed. Please install Python and try again."
    pause
    exit
}

# 啟動 Flask 應用程式
Write-Host "Running Flask application..."
python run.py

# 等待使用者按鍵再關閉
pause
