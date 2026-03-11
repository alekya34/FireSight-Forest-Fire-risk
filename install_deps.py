import subprocess
import sys

def install():
    with open("install.log", "w") as f:
        try:
            f.write("Starting installation...\n")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flask_sqlalchemy"], stdout=f, stderr=f)
            f.write("Installation successful.\n")
        except subprocess.CalledProcessError as e:
            f.write(f"Installation failed with code {e.returncode}\n")
        except Exception as e:
            f.write(f"An error occurred: {e}\n")

if __name__ == "__main__":
    install()
