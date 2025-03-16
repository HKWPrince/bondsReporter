#!/bin/bash

echo "Starting BondsReporter..."
echo Please Wait...

# 啟動 Docker Compose
cd docker

docker-compose down -v
docker-compose up --build -d
cd ..

# 等待 Docker 服務啟動
sleep 5

# 檢查 Docker 是否正在運行
if ! docker ps | grep mssql_container; then
    echo "Docker services failed to start. Please check your Docker setup."
    exit 1
fi

echo "ondsReporter..."
echo "Available services:"




# 定義清理函數，當視窗關閉時停止 Docker
cleanup() {
    cd docker
    echo "Closing Docker services..."
    docker-compose down
    exit 0
}

# 設置 trap，在腳本結束或視窗關閉時執行 cleanup()
trap cleanup SIGINT SIGTERM EXIT

# 確保 Python 存在
if ! command -v python3 &> /dev/null
then
    echo "Python3 is not installed. Please install Python3 and try again."
    exit 1
fi

# 啟動 Flask 應用程式
echo "Running Flask application..."
python3 run.py
