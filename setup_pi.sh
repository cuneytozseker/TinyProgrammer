#!/bin/bash
# Tiny Programmer - Pi Zero 2 W Setup Script
# For Waveshare 4inch RPi LCD (A) - SPI TFT Display

set -e

echo "=================================="
echo "Tiny Programmer Setup"
echo "=================================="
echo ""

# Check if running on Pi
if [[ ! -f /proc/device-tree/model ]]; then
    echo "Warning: Not running on Raspberry Pi"
    echo "Some steps may fail."
    echo ""
fi

# Update system
echo "[1/6] Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo "[2/6] Installing dependencies..."
sudo apt install -y \
    python3-pip \
    python3-pygame \
    python3-pil \
    git \
    cmake \
    build-essential \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-ttf-dev

pip3 install requests --break-system-packages

# Install Waveshare LCD driver
echo "[3/6] Installing Waveshare LCD driver..."
cd ~
if [[ ! -d "LCD-show" ]]; then
    git clone https://github.com/waveshare/LCD-show.git
fi
cd LCD-show
chmod +x LCD4-show

echo ""
echo "WARNING: The next step will install LCD drivers and REBOOT."
echo "After reboot, run this script again with --continue flag."
echo ""
read -p "Continue with LCD driver installation? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo ./LCD4-show
    # Script won't reach here - Pi will reboot
fi

exit 0
