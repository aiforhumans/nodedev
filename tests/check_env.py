"""Quick sanity checks for the 🤖Xtremetools dev environment."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_PATHS = [PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
              PROJECT_ROOT / ".venv" / "bin" / "python"]

def main() -> None:
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")

    venv_exists = any(path.exists() for path in VENV_PATHS)
    if not venv_exists:
        raise SystemExit("Expected virtual environment in .venv but none was found.")

    print("Virtual environment detected at .venv")
    print("Environment looks ready for ComfyUI node work.")


if __name__ == "__main__":
    main()
