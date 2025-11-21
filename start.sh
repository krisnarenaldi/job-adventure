#!/bin/bash
set -e

echo "=== Starting Resume Job Matching System ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "PORT: ${PORT:-8000}"

# Navigate to backend directory
cd backend

echo "=== Installing/verifying dependencies ==="
pip install --no-cache-dir -r requirements-render.txt

echo "=== Starting application with uvicorn ==="
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
