#!/bin/bash
# TinyProgrammer one-line installer
# Usage: curl -sSL https://raw.githubusercontent.com/cuneytozseker/TinyProgrammer/main/setup.sh | bash

set -e

REPO="https://github.com/cuneytozseker/TinyProgrammer.git"
INSTALL_DIR="$HOME/TinyProgrammer"
TAG="${TINYPROGRAMMER_TAG:-v0.1}"

# Colors
R='\033[0;31m'
G='\033[0;32m'
Y='\033[1;33m'
B='\033[0;34m'
N='\033[0m'

echo -e "${B}=== TinyProgrammer installer ===${N}"
echo ""

# 1. Check we're on a Linux/Pi
if [[ ! -f /etc/os-release ]]; then
    echo -e "${R}This installer only works on Linux (Raspberry Pi OS recommended).${N}"
    echo "For Docker install, see: https://github.com/cuneytozseker/TinyProgrammer#running-on-desktop-docker"
    exit 1
fi

# 2. Detect display profile
echo -e "${B}[1/7]${N} Detecting hardware..."
if [[ -e /dev/fb0 ]]; then
    FB_INFO=$(fbset 2>/dev/null | grep -oP 'geometry \K\d+ \d+' || echo "")
    if echo "$FB_INFO" | grep -q "480 320\|320 480"; then
        PROFILE="pizero-spi"
        echo -e "  Detected: ${G}480x320 SPI${N} (Pi Zero profile)"
    else
        PROFILE="pi4-hdmi"
        echo -e "  Detected: ${G}800x480 HDMI${N} (Pi 4 profile)"
    fi
else
    PROFILE="pi4-hdmi"
    echo -e "  ${Y}No framebuffer detected, defaulting to pi4-hdmi${N}"
fi

# 3. Install system deps
echo -e "${B}[2/7]${N} Installing system dependencies..."
sudo apt update -qq
sudo apt install -y -qq \
    python3-pip python3-pygame python3-pil \
    git libsdl2-dev libsdl2-image-dev libsdl2-ttf-dev \
    > /dev/null

# 4. Install Python deps
echo -e "${B}[3/7]${N} Installing Python packages..."
pip3 install --quiet --break-system-packages requests flask python-dotenv 2>/dev/null || \
    pip3 install --quiet requests flask python-dotenv

# 5. Clone or update repo
echo -e "${B}[4/7]${N} Fetching TinyProgrammer ${TAG}..."
if [[ -d "$INSTALL_DIR/.git" ]]; then
    cd "$INSTALL_DIR"
    git fetch --tags --quiet
    git checkout "$TAG" --quiet
else
    git clone --quiet --depth 1 --branch "$TAG" "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 6. Set up .env
echo -e "${B}[5/7]${N} Configuring environment..."
if [[ ! -f .env ]]; then
    cp .env.example .env
    # Auto-set the detected profile
    sed -i "s|^DISPLAY_PROFILE=.*|DISPLAY_PROFILE=$PROFILE|" .env

    echo "  .env created with profile=$PROFILE"
    NEEDS_API_KEY=1
else
    echo "  .env already exists, keeping current settings"
    # Check if key is set
    if ! grep -qE '^OPENROUTER_API_KEY=sk-' .env; then
        NEEDS_API_KEY=1
    fi
fi

# 7. Pi Zero SPI driver check
if [[ "$PROFILE" == "pizero-spi" ]] && [[ ! -e /dev/fb0 ]]; then
    echo ""
    echo -e "${Y}Warning: pizero-spi profile selected but no framebuffer found.${N}"
    echo "You may need to install the Waveshare LCD driver:"
    echo "  cd ~ && git clone https://github.com/waveshare/LCD-show.git"
    echo "  cd LCD-show && chmod +x LCD4-show && sudo ./LCD4-show"
    echo ""
fi

# 8. Install systemd service (only if API key is set — otherwise it'd error loop)
if [[ -z "$NEEDS_API_KEY" ]]; then
    echo -e "${B}[6/7]${N} Installing systemd service..."
    chmod +x install-service.sh
    sudo ./install-service.sh > /dev/null
else
    echo -e "${B}[6/7]${N} Skipping service install (no API key yet)"
fi

# 9. Done
echo -e "${B}[7/7]${N} Done!"
echo ""
echo -e "${G}=== TinyProgrammer installed ===${N}"
echo ""

if [[ -n "$NEEDS_API_KEY" ]]; then
    echo -e "${Y}====================================================${N}"
    echo -e "${Y}  ACTION REQUIRED: Add your OpenRouter API key${N}"
    echo -e "${Y}====================================================${N}"
    echo ""
    echo "1. Get a free API key at https://openrouter.ai"
    echo "2. Edit the .env file:"
    echo "     nano $INSTALL_DIR/.env"
    echo "3. Set OPENROUTER_API_KEY=sk-or-v1-..."
    echo "4. Install the service:"
    echo "     cd $INSTALL_DIR && chmod +x install-service.sh && sudo ./install-service.sh"
    echo ""
else
    echo "Dashboard:  http://$(hostname -I | awk '{print $1}'):5000"
    echo "Logs:       tail -f /var/log/tinyprogrammer.log"
    echo "Service:    sudo systemctl status tinyprogrammer"
fi
