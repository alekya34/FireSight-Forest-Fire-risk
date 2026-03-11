import sys
import subprocess
import os

log_file = "debug_install.log"

def log(msg):
    with open(log_file, "a") as f:
        f.write(msg + "\n")
    print(msg)

def main():
    if os.path.exists(log_file):
        os.remove(log_file)
    
    log(f"Python Executable: {sys.executable}")
    log(f"CWD: {os.getcwd()}")
    
    try:
        import flask_sqlalchemy
        log("flask_sqlalchemy is ALREADY installed.")
        log(f"Location: {flask_sqlalchemy.__file__}")
    except ImportError:
        log("flask_sqlalchemy not found. Attempting install...")
        try:
            # Install using the current interpreter
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flask_sqlalchemy"])
            log("Installation command finished successfully.")
            
            # Verify
            try:
                import flask_sqlalchemy
                log(f"Verified installation. Location: {flask_sqlalchemy.__file__}")
            except ImportError:
                log("Still ImportError after installation!")
                
        except subprocess.CalledProcessError as e:
            log(f"Installation failed with code {e.returncode}")
        except Exception as e:
            log(f"Installation failed with error: {e}")

if __name__ == "__main__":
    main()
