import os
import sys
import subprocess
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent
    
    # 1. Locate the virtual environment (supports .venv or venv)
    venv_dir = base_dir / ".venv"
    if not venv_dir.exists():
        venv_dir = base_dir / "venv"
    
    if not venv_dir.exists():
        print("[ERROR] Virtual environment (.venv or venv) not found!")
        print("Please create one using: python -m venv .venv")
        sys.exit(1)

    # 2. Determine the path to the Python executable inside the virtual environment
    if os.name == "nt":  # Windows
        python_executable = venv_dir / "Scripts" / "python.exe"
    else:  # Linux / macOS / Android (Termux)
        python_executable = venv_dir / "bin" / "python"

    if not python_executable.exists():
        print(f"[ERROR] Could not find python executable inside {venv_dir}")
        sys.exit(1)

    print("========================================")
    print("   Starting Home Server via Python...   ")
    print("========================================")
    print(f"Using Python: {python_executable}")
    print("Server running at: http://localhost:8000\n")

    # 3. Run Uvicorn using the virtual environment's Python interpreter
    try:
        subprocess.run([
            str(python_executable), 
            "-m", 
            "uvicorn", 
            "main:app", 
            "--host", 
            "0.0.0.0", 
            "--port", 
            "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user.")

if __name__ == "__main__":
    main()