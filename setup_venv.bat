@echo off
REM Recreate the Windows .venv and install requirements.
REM Run this from the repo root (same folder as requirements.txt).

cd /d "%~dp0"

echo.
echo === Removing old .venv (if any) ===
if exist ".venv" (
  rmdir /s /q ".venv"
)

echo.
echo === Creating new .venv with your Windows Python ===
py -3 -m venv .venv
if errorlevel 1 (
  echo py launcher failed, trying python...
  python -m venv .venv
)
if errorlevel 1 (
  echo ERROR: could not create venv. Install Python 3 and enable "Add to PATH".
  exit /b 1
)

echo.
echo === Upgrading pip and installing requirements ===
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: pip install failed.
  exit /b 1
)

echo.
echo === Verifying imports ===
python -c "import sys; print('Python:', sys.executable); import PyQt6; print('PyQt6 OK:', PyQt6.__file__)"
if errorlevel 1 (
  echo ERROR: PyQt6 import failed inside .venv
  exit /b 1
)

echo.
echo SUCCESS.
echo Next in Cursor/VS Code:
echo   1) Ctrl+Shift+P
echo   2) Python: Select Interpreter
echo   3) Choose: .venv\Scripts\python.exe
echo Then open a NEW terminal and run:
echo   cd PLC
echo   python main.py
echo.
pause
