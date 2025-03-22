import atexit
import os
from app import create_app

def shutdown_docker():
    os.system("docker-compose -f ./docker/docker-compose.yml down")

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


atexit.register(shutdown_docker)