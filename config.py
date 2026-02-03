import os

# Tiny Programmer Configuration

# =============================================================================
# DISPLAY (Waveshare 4inch RPi LCD A - 480x320 TFT)
# =============================================================================

DISPLAY_WIDTH = 480
DISPLAY_HEIGHT = 320

# Colors (retro terminal aesthetic)
COLOR_BG = (0, 0, 0)           # Black background
COLOR_FG = (0, 255, 0)         # Green text (classic terminal)
# COLOR_FG = (255, 176, 0)     # Amber alternative
COLOR_CURSOR = (0, 255, 0)
COLOR_STATUS_BG = (0, 40, 0)   # Darker green for status bar
COLOR_DIM = (0, 128, 0)        # Dimmed text for comments

# Font settings (use monospace!)
FONT_NAME = "DejaVu Sans Mono"  # pygame will find system font
FONT_SIZE = 14
CHAR_WIDTH = 9    # Will be calculated from font
CHAR_HEIGHT = 16

# Terminal dimensions (in characters)
TERMINAL_COLS = 52   # 480 / 9 ≈ 53
TERMINAL_ROWS = 18   # Leave room for status bar (320 - 32) / 16 ≈ 18

# Status bar
STATUS_BAR_HEIGHT = 32

# Display modes
MODE_TERMINAL = "terminal"  # Code writing mode
MODE_RUN = "run"            # Program execution mode

# Framerate cap (saves CPU, SPI can't go much faster anyway)
TARGET_FPS = 30

# =============================================================================
# LLM
# =============================================================================

# Backend type: "llamacpp" or "ollama"
LLM_BACKEND = "ollama"

# llama.cpp server endpoint
LLM_ENDPOINT = "http://localhost:8080/completion"

# Ollama endpoint
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:0.5b"  # Run 'ollama pull qwen2.5-coder:0.5b' first

# Or path to model for subprocess mode (llamacpp only)
# Default relative path or absolute path
LLM_MODEL_PATH = os.path.join(os.path.expanduser("~"), "llama.cpp", "models", "smollm2-135m-instruct-q4_k_m.gguf")
LLAMA_CPP_PATH = os.path.join(os.path.expanduser("~"), "llama.cpp", "llama-cli")

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
WATCH_DURATION_MIN = 10
WATCH_DURATION_MAX = 30

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
