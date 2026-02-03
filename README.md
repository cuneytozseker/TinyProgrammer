# Tiny Programmer

A self-contained device that writes code, runs it, and repeats forever. A tiny local LLM slowly codes little programs at human speed, complete with mistakes, comments, and personality.

## Hardware

- Raspberry Pi Zero 2 W
- Waveshare 4inch RPi LCD (A) - 480×320 TFT, SPI interface

The TFT display plugs directly onto the GPIO header (no HDMI needed). Uses FBCP driver to mirror framebuffer over SPI, giving ~30fps refresh rate suitable for animations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                               │
│                    (orchestrator)                            │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    brain     │    │   display    │    │   archive    │
│              │    │              │    │              │
│ - state      │    │ - terminal   │    │ - local      │
│ - loop       │───▶│ - partial    │    │ - github     │
│ - decisions  │    │   refresh    │    │   (future)   │
└──────────────┘    └──────────────┘    └──────────────┘
        │
        ▼
┌──────────────┐    ┌──────────────┐
│     llm      │    │  personality │
│              │    │              │
│ - generate   │◀───│ - mood       │
│ - stream     │    │ - comments   │
└──────────────┘    └──────────────┘
```

## State Machine

```
    ┌─────────┐
    │  BOOT   │
    └────┬────┘
         ▼
    ┌─────────┐
    │  THINK  │◀─────────────────┐
    └────┬────┘                  │
         ▼                       │
    ┌─────────┐                  │
    │  WRITE  │                  │
    └────┬────┘                  │
         ▼                       │
    ┌─────────┐    (failed)      │
    │  RUN    │──────────────────┤
    └────┬────┘                  │
         ▼ (success)             │
    ┌─────────┐                  │
    │  WATCH  │                  │
    └────┬────┘                  │
         ▼                       │
    ┌─────────┐                  │
    │ ARCHIVE │──────────────────┘
    └─────────┘
```

## Local LLM Options

Tested/recommended for Pi Zero 2 W (512MB RAM):

### Primary Recommendation: SmolLM2-135M

```bash
# Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make

# Download model (Q4_K_M quantization, ~100MB)
wget https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct-GGUF/resolve/main/smollm2-135m-instruct-q4_k_m.gguf
```

- Size: ~100MB quantized
- Speed: ~5-10 tokens/sec on Pi Zero 2 W
- Quality: Decent for simple programs
- **Best starting point**

### Alternative: Qwen2.5-Coder-0.5B

```bash
wget https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf
```

- Size: ~400MB quantized
- Speed: ~2-4 tokens/sec (slower, needs swap)
- Quality: Better code understanding
- **Use if SmolLM2 quality is insufficient**

### Testing on Desktop First

For faster iteration, test on your main machine first:

```bash
# Run with llama.cpp server
./llama-server -m smollm2-135m-instruct-q4_k_m.gguf -c 2048 --port 8080

# Or use Ollama
ollama run smollm2:135m
```

## Setup

### 1. Prepare Pi Zero 2 W

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3-pip python3-pygame git cmake build-essential

pip3 install requests

# Install Waveshare LCD driver
git clone https://github.com/waveshare/LCD-show.git
cd LCD-show
chmod +x LCD4-show
sudo ./LCD4-show
# Pi will reboot automatically
```

### 2. Install llama.cpp

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make LLAMA_NO_METAL=1  # No GPU on Pi Zero

# Download model
mkdir -p models
cd models
wget <model_url>
```

### 3. Clone this repo

```bash
git clone https://github.com/yourusername/tiny-programmer.git
cd tiny-programmer
cp config.example.py config.py
# Edit config.py with your settings
```

### 4. Run

```bash
python3 main.py
```

## Project Structure

```
tiny-programmer/
├── main.py              # Entry point, orchestrates everything
├── config.py            # User configuration
├── test.py              # Test suite for components
├── test_display.py      # Visual display test (bouncing ball)
├── setup_pi.sh          # Pi setup script (part 1 - LCD driver)
├── setup_pi_part2.sh    # Pi setup script (part 2 - llama.cpp)
├── display/
│   ├── __init__.py
│   └── terminal.py      # Pygame-based terminal emulator
├── llm/
│   ├── __init__.py
│   └── generator.py     # LLM interface (llama.cpp)
├── programmer/
│   ├── __init__.py
│   ├── brain.py         # Main state machine
│   └── personality.py   # Mood, comments, typing quirks
├── archive/
│   ├── __init__.py
│   └── repository.py    # Local storage + GitHub sync
└── programs/            # Generated programs saved here
```

## Roadmap

### v0.1 - Proof of Concept (current)
- [x] Architecture
- [x] Pygame terminal emulator
- [ ] LLM streaming integration
- [ ] Basic state machine (think → write → run → repeat)

### v0.2 - Personality
- [ ] Mood system
- [ ] Human-like typing (variable speed, pauses)
- [ ] Mistakes and corrections
- [ ] Self-aware comments

### v0.3 - Visual Programs
- [ ] Program execution sandbox
- [ ] Graphical output display (bouncing ball, patterns, etc.)
- [ ] Smooth transition between code view and running program

### v0.4 - Archive
- [ ] Local program storage with metadata
- [ ] Screenshot capture of running programs
- [ ] JSON index of all creations

### v0.5 - GitHub Sync
- [ ] Push programs to repository
- [ ] README auto-generation
- [ ] "The Complete Works of Tiny Programmer"

### v1.0 - Release
- [ ] Enclosure design
- [ ] Full documentation
- [ ] Kit BOM and build guide

## License

**CERN-OHL-S** (Strongly Reciprocal) for hardware designs.
**GPL-3.0** for software.

Anyone can build and sell clones, but must share their designs.
For proprietary/commercial licensing, contact [you].
