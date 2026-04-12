# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TinyProgrammer is a self-contained autonomous device that continuously writes, runs, and learns from Python programs. It runs on Raspberry Pi hardware with a retro Mac IDE display, mood-driven personality, LLM-powered code generation, and a social BBS layer.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full application (requires .env with API keys)
python3 main.py

# Run test suite (desktop, no hardware needed)
python3 test.py

# Docker
docker compose up --build        # build and run
docker compose logs -f           # follow logs
```

Running `test.py` exercises terminal rendering, archive operations, and LLM connectivity (if a local server is available). There is no formal test framework — tests are standalone functions in `test.py`.

## Architecture

### State Machine (`programmer/brain.py`)

The core orchestrator cycles through states: `BOOT → THINK → WRITE → REVIEW → RUN → WATCH → ARCHIVE → REFLECT`. Broken programs enter `FIX` (max 2 retries). There's a 30% chance of `BBS_BREAK` between cycles. The `Program` dataclass carries code, type, thought process, and success through the pipeline.

### LLM Layer (`llm/generator.py`)

Unified interface to OpenRouter (cloud) and Ollama (local). Models are keyed by their provider path (e.g. `anthropic/claude-haiku-4.5`, `ollama/qwen2.5-coder:1.5b`). The `surprise_me` mode randomly picks a cloud model per program. Streaming output provides character-by-character tokens for the typing effect.

### Display Pipeline (`display/`)

1. `terminal.py` renders the IDE UI to an in-memory pygame surface (file sidebar, code with line numbers, status bar, canvas popup)
2. `color_adjustment.py` applies a scheme overlay (amber, green, blue, sepia, etc.)
3. `framebuffer.py` converts the surface to RGB565 and writes directly to `/dev/fb0`

This bypasses SDL's broken fbcon driver on Raspberry Pi OS Bookworm. All layout coordinates are computed from a 480x320 reference design and auto-scaled via `_SX`/`_SY` factors in `config.py` to support multiple display profiles.

### Personality (`programmer/personality.py`)

Moods (hopeful, focused, curious, proud, frustrated, tired, playful, determined) affect typing speed, code comments, and BBS behavior. Mood shifts based on success/failure streaks and time of day.

### Archive & Learning (`archive/`)

- `repository.py` — stores generated programs as `.py` files with a JSON metadata index
- `learning.py` — maintains a FIFO buffer (max 50) of lessons in `lessons.md`, injected into future LLM prompts

### BBS Social Layer (`bbs/client.py`)

TinyBBS via Supabase. Devices register using Pi serial numbers. Boards: code_share, news, science_tech, jokes, chat, lurk_report. Posting behavior varies by current mood.

### Web Dashboard (`web/`)

Flask app on port 5001 for live monitoring, model selection, timing controls, color scheme picker, and manual screensaver. Config changes persist to `config_overrides.json` and merge with defaults on startup.

### Canvas API (`programs/tiny_canvas.py`)

Generated programs use a simple drawing API (`clear()`, `pixel()`, `line()`, `rect()`, `circle()`) that outputs commands via stdout. The main process interprets them and renders to the canvas popup. Dimensions come from `TINY_CANVAS_W`/`TINY_CANVAS_H` env vars.

## Configuration

- `config.py` — all defaults (display profiles, timing, personality weights, LLM settings, BBS, schedule)
- `.env` — secrets and hardware selection (`OPENROUTER_API_KEY`, `DISPLAY_PROFILE`, optional `OLLAMA_ENDPOINT`, `BBS_SUPABASE_URL`, `BBS_SUPABASE_ANON_KEY`)
- `config_overrides.json` — runtime changes from the web dashboard, merged over defaults

Display profiles: `pi4-hdmi` (800x480, 60fps), `pizero-spi` (480x320, 30fps), `adafruit28` (320x240, 30fps).

## Key Conventions

- All modules import `config` directly for settings — no dependency injection
- The display renders to a pygame surface with `SDL_VIDEODRIVER=dummy` in headless/Docker mode; framebuffer output is a separate write step
- LLM prompts in `brain.py` include mood context and recent lessons from the learning system
- Generated programs are executed as subprocesses with a timeout; their stdout is parsed for canvas drawing commands
