#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=== [1/3] Upgrading pip and installing backend dependencies ==="
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

echo "=== [2/3] Installing frontend dependencies and building production assets ==="
cd frontend
npm install
npm run build
cd ..

echo "=== [3/3] Build completed successfully ==="
