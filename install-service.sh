#!/bin/bash
# Install TinyProgrammer as a systemd service
# Run this script once to set up autostart on boot
# Automatically detects your install path — no manual editing needed

set -e

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(which python3)"

echo "[TinyProgrammer] Installing systemd service..."
echo "  Install dir: $INSTALL_DIR"
echo "  Python:      $PYTHON"

# Generate service file with correct paths
sed "s|/home/aerovisual/TinyProgrammer|$INSTALL_DIR|g; s|/usr/bin/python3|$PYTHON|g" \
    "$INSTALL_DIR/tinyprogrammer.service" > /tmp/tinyprogrammer.service

sudo cp /tmp/tinyprogrammer.service /etc/systemd/system/
rm /tmp/tinyprogrammer.service

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
echo "  tail -f /var/log/tinyprogrammer.log    - View app logs"
