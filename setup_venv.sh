#!/usr/bin/env bash
# Recreate the Linux/macOS .venv and install requirements.
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Removing old .venv (if any) ==="
rm -rf .venv

echo "=== Creating new .venv ==="
python3 -m venv .venv

echo "=== Upgrading pip and installing requirements ==="
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "=== Verifying imports ==="
.venv/bin/python -c "import sys; print('Python:', sys.executable); import PyQt6; print('PyQt6 OK:', PyQt6.__file__)"

echo
echo "SUCCESS. Activate with: source .venv/bin/activate"
echo "Or run: .venv/bin/python PLC/main.py"
