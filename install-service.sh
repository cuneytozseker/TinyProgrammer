#!/bin/bash
# Install TinyProgrammer as a systemd service
# Run this script once to set up autostart on boot

set -e

echo "[TinyProgrammer] Installing systemd service..."

# Copy service file
sudo cp tinyprogrammer.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable tinyprogrammer

# Start the service now
sudo systemctl start tinyprogrammer

echo ""
echo "TinyProgrammer service installed and started!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status tinyprogrammer   - Check status"
echo "  sudo systemctl stop tinyprogrammer     - Stop"
echo "  sudo systemctl start tinyprogrammer    - Start"
echo "  sudo systemctl restart tinyprogrammer  - Restart"
echo "  journalctl -u tinyprogrammer -f        - View logs"
echo "  tail -f /var/log/tinyprogrammer.log    - View app logs"
