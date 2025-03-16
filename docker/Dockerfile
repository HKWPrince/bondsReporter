# 使用官方 Python 映像
FROM python:3.9

# 更新 & 安裝系統相依套件
RUN apt-get update && apt-get install -y \
    curl \
    unixodbc \
    unixodbc-dev \
    odbcinst \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get install -y msodbcsql18

# 設定工作目錄
WORKDIR /app

# 複製 Flask 應用程式和 run.py
COPY ../app /app

# 安裝相依套件
RUN pip install --no-cache-dir -r /app/requirements.txt

# 啟動 Flask 應用
CMD ["flask", "run.py", "--host=0.0.0.0"]
