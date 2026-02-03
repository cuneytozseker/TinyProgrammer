#!/bin/bash
# Tiny Programmer - Pi Zero 2 W Setup Script (Part 2)
# Run this AFTER setup_pi.sh and LCD reboot

set -e

echo "=================================="
echo "Tiny Programmer Setup (Part 2)"
echo "=================================="
echo ""

# Build llama.cpp
echo "[1/3] Building llama.cpp (this takes ~30 minutes on Pi Zero 2 W)..."
cd ~
if [[ ! -d "llama.cpp" ]]; then
    git clone https://github.com/ggerganov/llama.cpp
fi
cd llama.cpp

# Clean build
make clean 2>/dev/null || true

# Build without Metal (no GPU on Pi)
# Use single thread to avoid running out of memory
make LLAMA_NO_METAL=1 -j1

# Create models directory
mkdir -p models

echo ""
echo "[2/3] Downloading model (SmolLM2-135M, ~100MB)..."
echo "This may take a while depending on your connection..."
cd models
if [[ ! -f "smollm2-135m-instruct-q4_k_m.gguf" ]]; then
    wget -c https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct-GGUF/resolve/main/smollm2-135m-instruct-q4_k_m.gguf
else
    echo "Model already downloaded"
fi

echo ""
echo "[3/3] Setting up autostart (optional)..."
echo ""

# Create systemd service file
cat > /tmp/tiny-programmer.service << 'EOF'
[Unit]
Description=Tiny Programmer
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/tiny-programmer
ExecStart=/usr/bin/python3 /home/pi/tiny-programmer/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "To enable autostart on boot:"
echo "  sudo cp /tmp/tiny-programmer.service /etc/systemd/system/"
echo "  sudo systemctl enable tiny-programmer"
echo "  sudo systemctl start tiny-programmer"
echo ""

echo "=================================="
echo "Setup complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Clone tiny-programmer repo:"
echo "   cd ~"
echo "   git clone <your-repo-url> tiny-programmer"
echo "   cd tiny-programmer"
echo ""
echo "2. Test the display:"
echo "   python3 test.py"
echo ""
echo "3. Start LLM server (in separate terminal or use screen/tmux):"
echo "   cd ~/llama.cpp"
echo "   ./llama-server -m models/smollm2-135m-instruct-q4_k_m.gguf --port 8080"
echo ""
echo "4. Run Tiny Programmer:"
echo "   cd ~/tiny-programmer"
echo "   python3 main.py"
echo ""
echo "Tip: Use 'screen' or 'tmux' to run llama-server in background:"
echo "   screen -S llm"
echo "   ./llama-server -m models/smollm2-135m-instruct-q4_k_m.gguf --port 8080"
echo "   # Press Ctrl+A, then D to detach"
echo ""
