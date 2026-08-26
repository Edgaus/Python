@echo off
REM Install project libraries into your NORMAL Windows Python (no .venv).
cd /d "%~dp0"

echo.
echo === Using this Python ===
where python
python -c "import sys; print(sys.executable)"

echo.
echo === Installing requirements (user install) ===
python -m pip install --upgrade pip
python -m pip install --user -r requirements.txt
if errorlevel 1 (
  echo ERROR: pip install failed.
  exit /b 1
)

echo.
echo === Verifying PyQt6 ===
python -c "import PyQt6; print('PyQt6 OK:', PyQt6.__file__)"
if errorlevel 1 (
  echo ERROR: PyQt6 not importable. Check that 'python' is the interpreter you want.
  exit /b 1
)

echo.
echo SUCCESS — no .venv needed.
echo Run:  cd PLC ^& python main.py
echo.
pause
