#!/bin/bash
# TinyProgrammer Startup Script
# Kills existing processes and starts fresh

cd "$(dirname "$0")"

echo "[TinyProgrammer] Stopping existing processes..."
sudo pkill -f "python3 main.py" 2>/dev/null || true
sleep 2

echo "[TinyProgrammer] Pulling latest code..."
git pull

echo "[TinyProgrammer] Starting..."
sudo python3 main.py 2>&1 | tee /tmp/tinyprogrammer.log
