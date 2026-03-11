import subprocess
import sys
import os

def install():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask_sqlalchemy"])
        with open("SUCCESS.txt", "w") as f:
            f.write("Installed successfully")
    except Exception as e:
        with open("FAILURE.txt", "w") as f:
            f.write(str(e))

if __name__ == "__main__":
    install()
