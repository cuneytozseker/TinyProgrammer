#!/bin/bash
# Stop TinyProgrammer

echo "[TinyProgrammer] Stopping..."
sudo pkill -f "python3 main.py" 2>/dev/null || true
sleep 1
echo "[TinyProgrammer] Stopped"
