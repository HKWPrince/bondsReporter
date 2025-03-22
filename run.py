import atexit
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

def shutdown_docker():
    os.system("docker-compose down")

atexit.register(shutdown_docker)