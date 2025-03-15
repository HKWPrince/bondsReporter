from flask import Flask
import os

def create_app():
    app = Flask(__name__, template_folder="./templates", static_folder="./static")

    # 設定應用程式的環境變數
    app.config["ALLOWED_EXTENSIONS"] = ["xlsx"]
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["File_FOLDER"] = "file"
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")


    # 註冊 Blueprint（載入 `routes.py`）
    from .routes import main
    app.register_blueprint(main)

    return app
