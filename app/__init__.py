from flask import Flask
import os

def create_app():
    app = Flask(__name__, template_folder="./templates", static_folder="./static")

    app.config["ALLOWED_EXTENSIONS"] = ["csv"]
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["File_FOLDER"] = "file"
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["File_FOLDER"], exist_ok=True)

    from .routes import main
    app.register_blueprint(main)

    return app

