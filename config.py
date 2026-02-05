import os

# Tiny Programmer Configuration

# =============================================================================
# DISPLAY (Waveshare 4inch RPi LCD A - 480x320 TFT)
# =============================================================================

DISPLAY_WIDTH = 480
DISPLAY_HEIGHT = 320

# Colors (retro Mac OS IDE aesthetic)
COLOR_BG = (255, 255, 255)      # White background
COLOR_FG = (0, 0, 0)            # Black text
COLOR_CURSOR = (0, 0, 0)        # Black cursor
COLOR_LINE_NUM = (128, 128, 128)  # Gray line numbers
COLOR_SIDEBAR_FG = (0, 0, 0)    # Black sidebar text
COLOR_SIDEBAR_SEL = (0, 0, 0)   # Selected file (inverted)
COLOR_STATUS_FG = (0, 0, 0)     # Status bar text
COLOR_DIM = (128, 128, 128)     # Dimmed text for comments

# Font settings (Space Mono from Google Fonts)
FONT_NAME = "SpaceMono-Regular"
FONT_SIZE = 12
CHAR_WIDTH = 8    # Will be calculated from font
CHAR_HEIGHT = 16

# Layout regions (pixel coordinates on 480x320 bg.png)
# Sidebar: file list
SIDEBAR_X = 5
SIDEBAR_Y = 63
SIDEBAR_W = 90
SIDEBAR_H = 210

# Code area: where code is rendered
CODE_AREA_X = 130
CODE_AREA_Y = 63
CODE_AREA_W = 320    # ~130 to ~452
CODE_AREA_H = 210    # ~63 to ~275

# Line number column (between sidebar and code)
LINE_NUM_X = 105
LINE_NUM_W = 25

# Status bar
STATUS_BAR_Y = 300
STATUS_BAR_HEIGHT = 16

# Display modes
MODE_TERMINAL = "terminal"  # Code writing mode
MODE_RUN = "run"            # Program execution mode

# Canvas popup window (Mac OS floating window for program output)
CANVAS_X = 29                # Position of canvas.png on screen
CANVAS_Y = 35
CANVAS_W = 422               # Full chrome size (including title bar)
CANVAS_H = 242
CANVAS_DRAW_OFFSET_X = 2     # Drawable area offset within chrome
CANVAS_DRAW_OFFSET_Y = 20
CANVAS_DRAW_W = 416           # Drawable area size
CANVAS_DRAW_H = 218

# Framerate cap (saves CPU, SPI can't go much faster anyway)
TARGET_FPS = 30

# =============================================================================
# LLM
# =============================================================================

# Backend type: "ollama", "llamacpp", "gemini", or "anthropic"
LLM_BACKEND = "gemini"  # Cloud API for Pi Zero

# --- Local backends (for Pi 4B with more RAM) ---
# llama.cpp server endpoint
LLM_ENDPOINT = "http://localhost:8080/completion"

# Ollama endpoint
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:0.5b"

# Path to model for subprocess mode (llamacpp only)
LLM_MODEL_PATH = os.path.join(os.path.expanduser("~"), "llama.cpp", "models", "smollm2-135m-instruct-q4_k_m.gguf")
LLAMA_CPP_PATH = os.path.join(os.path.expanduser("~"), "llama.cpp", "llama-cli")

# --- Cloud API backends (for Pi Zero) ---
# Gemini (Google AI)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash-lite"  # Fast and cheap

# Anthropic (Claude)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"  # Fast and cheap

# Generation settings
LLM_CONTEXT_SIZE = 2048
LLM_MAX_TOKENS = 512
LLM_TEMPERATURE = 0.7
LLM_STOP_TOKENS = ["```", "# END", "if __name__"]

# =============================================================================
# PERSONALITY
# =============================================================================

# Typing speed (characters per second) - will vary by mood
TYPING_SPEED_MIN = 2
TYPING_SPEED_MAX = 8

# Probability of making a typo (0.0 - 1.0)
TYPO_PROBABILITY = 0.02

# Probability of pausing mid-line to "think"
PAUSE_PROBABILITY = 0.05
PAUSE_DURATION_MIN = 1.0  # seconds
PAUSE_DURATION_MAX = 4.0

# Probability of deleting and rewriting a line
REWRITE_PROBABILITY = 0.03

# =============================================================================
# STATE MACHINE
# =============================================================================

# How long to display "thinking" state
THINK_DURATION_MIN = 3
THINK_DURATION_MAX = 10

# How long to run a program before moving on
WATCH_DURATION_MIN = 300
WATCH_DURATION_MAX = 300

# Delay between state transitions
STATE_TRANSITION_DELAY = 2

# =============================================================================
# ARCHIVE
# =============================================================================

# Local storage
# Use relative path 'programs' in current directory by default
ARCHIVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "programs")

# GitHub sync (future)
GITHUB_ENABLED = False
GITHUB_REPO = "yourusername/tiny-programmer-archive"
GITHUB_TOKEN = ""  # Personal access token
GITHUB_SYNC_INTERVAL = 3600  # Sync every hour

# =============================================================================
# PROGRAMS
# =============================================================================

# Types of programs to generate (weighted)
PROGRAM_TYPES = [
    ("bouncing_ball", 3),
    ("clock", 2),
    ("pattern", 3),
    ("animation", 2),
    ("game_of_life", 1),
    ("spiral", 2),
    ("text_scroller", 1),
    ("random_walker", 2),
]

# Maximum lines of code to generate
MAX_PROGRAM_LINES = 50
