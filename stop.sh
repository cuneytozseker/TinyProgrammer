#!/bin/bash
# Stop TinyProgrammer and all child processes

echo "[TinyProgrammer] Stopping..."

# Kill the main process and all its children (program subprocesses)
sudo pkill -9 -f "python3 main.py" 2>/dev/null || true
sudo pkill -9 -f "python3 /home/aerovisual/TinyProgrammer/programs/" 2>/dev/null || true
sudo pkill -9 -f "python3 -c" 2>/dev/null || true

# Also kill any orphaned tiny_canvas programs
sudo pkill -9 -f "tiny_canvas" 2>/dev/null || true

sleep 1
echo "[TinyProgrammer] Stopped"
