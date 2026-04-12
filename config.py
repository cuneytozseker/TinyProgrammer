import os

# Tiny Programmer Configuration

# =============================================================================
# DISPLAY — auto-scaled from 480x320 reference layout
# =============================================================================
# Set DISPLAY_PROFILE in .env or config_overrides.json:
#   "pi4-hdmi"   → 800x480, 16pt font, 60fps (default)
#   "pizero-spi" → 480x320, 12pt font, 30fps

DISPLAY_PROFILE = os.environ.get("DISPLAY_PROFILE", "pi4-hdmi")

if DISPLAY_PROFILE == "adafruit28":
    DISPLAY_WIDTH = 320
    DISPLAY_HEIGHT = 240
    FONT_SIZE = 8
    CHAR_WIDTH = 6
    CHAR_HEIGHT = 10
    TARGET_FPS = 30
elif DISPLAY_PROFILE == "pizero-spi":
    DISPLAY_WIDTH = 480
    DISPLAY_HEIGHT = 320
    FONT_SIZE = 12
    CHAR_WIDTH = 8
    CHAR_HEIGHT = 16
    TARGET_FPS = 30
else:  # pi4-hdmi (default)
    DISPLAY_WIDTH = 800
    DISPLAY_HEIGHT = 480
    FONT_SIZE = 16
    CHAR_WIDTH = 10
    CHAR_HEIGHT = 20
    TARGET_FPS = 60

# Scale factors from the 480x320 reference design
_SX = DISPLAY_WIDTH / 480.0
_SY = DISPLAY_HEIGHT / 320.0

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

# Global offset to align with background
LAYOUT_OFFSET_X = int(2 * _SX + 0.5)
LAYOUT_OFFSET_Y = int(1 * _SY + 0.5)

# Layout regions — computed from 480x320 reference coordinates
SIDEBAR_X = int(5 * _SX) + LAYOUT_OFFSET_X
SIDEBAR_Y = int(63 * _SY) + LAYOUT_OFFSET_Y
SIDEBAR_W = int(90 * _SX)
SIDEBAR_H = int(210 * _SY)

CODE_AREA_X = int(130 * _SX) + LAYOUT_OFFSET_X
CODE_AREA_Y = int(63 * _SY) + LAYOUT_OFFSET_Y
CODE_AREA_W = int(320 * _SX)
CODE_AREA_H = int(210 * _SY)

LINE_NUM_X = int(105 * _SX) + LAYOUT_OFFSET_X
LINE_NUM_W = int(25 * _SX)

STATUS_BAR_Y = int(289 * _SY) + LAYOUT_OFFSET_Y
STATUS_BAR_HEIGHT = int(24 * _SY)

# Display modes
MODE_TERMINAL = "terminal"
MODE_RUN = "run"

# Canvas popup window — scaled from 480x320 reference
CANVAS_X = int(29 * _SX) + LAYOUT_OFFSET_X
CANVAS_Y = int(35 * _SY) + LAYOUT_OFFSET_Y
CANVAS_W = int(422 * _SX)
CANVAS_H = int(242 * _SY)
CANVAS_DRAW_OFFSET_X = int(3 * _SX)
CANVAS_DRAW_OFFSET_Y = int(19 * _SY)
CANVAS_DRAW_W = int(416 * _SX)
CANVAS_DRAW_H = int(212 * _SY)

# =============================================================================
# LLM
# =============================================================================

# Backend type: legacy/unused — actual routing is done via LLM_MODEL and
# the model registry in llm/generator.py.
LLM_BACKEND = "anthropic"
LLM_MODEL = os.environ.get("LLM_MODEL", "")

# --- Local backends (for Pi 4B with more RAM) ---
# llama.cpp server endpoint
LLM_ENDPOINT = "http://localhost:8080/completion"

# Ollama endpoint
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"

# Path to model for subprocess mode (llamacpp only)
LLM_MODEL_PATH = os.path.join(os.path.expanduser("~"), "llama.cpp", "models", "smollm2-135m-instruct-q4_k_m.gguf")
LLAMA_CPP_PATH = os.path.join(os.path.expanduser("~"), "llama.cpp", "llama-cli")

# --- Cloud API backends (for Pi Zero) ---
# Gemini (Google AI)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
#GEMINI_MODEL = "gemini-2.0-flash-lite"  # Fast and cheap
GEMINI_MODEL = "gemini-3-flash-preview"

# Anthropic (Claude)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"  # Haiku 4.5

# Generation settings
LLM_CONTEXT_SIZE = 4096
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

# How long to run a program before moving on (seconds)
WATCH_DURATION_MIN = 120
WATCH_DURATION_MAX = 120

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
    ("bouncing_ball", 1),
    ("pattern", 1),
    ("animation", 1),
    ("game_of_life", 1),
    ("cellular_automata", 1),
    ("l_system", 1),
    ("spiral", 1),
    ("random_walker", 1),
    ("starfield", 1),
    ("rain", 1),
    ("generative_glyphs", 1),
    ("pong", 1),
    ("wireframe_plot", 1),
]

# Maximum lines of code to generate
MAX_PROGRAM_LINES = 50

# =============================================================================
# WEB INTERFACE
# =============================================================================

# Enable web UI for remote configuration
WEB_ENABLED = True
WEB_HOST = "0.0.0.0"   # Listen on all interfaces
WEB_PORT = 5000
WEB_STREAM_ENABLED = os.environ.get("WEB_STREAM_ENABLED", "false").lower() in ("1", "true", "yes")

# =============================================================================
# DISPLAY COLOR SCHEME
# =============================================================================

# Color adjustment layer (like Photoshop adjustment layer)
# Options: none, amber, green, blue, sepia, cool, warm, night
COLOR_SCHEME = "none"

# =============================================================================
# BBS (TinyBBS social layer)
# =============================================================================

BBS_ENABLED = True
BBS_SUPABASE_URL = os.environ.get("BBS_SUPABASE_URL", "")
BBS_SUPABASE_ANON_KEY = os.environ.get("BBS_SUPABASE_ANON_KEY", "")
BBS_EDGE_FUNCTION_URL = os.environ.get("BBS_EDGE_FUNCTION_URL", "") or (BBS_SUPABASE_URL.rstrip("/") + "/functions/v1" if BBS_SUPABASE_URL else "")
BBS_BREAK_CHANCE = 0.3              # base probability after each reflect cycle
BBS_BREAK_DURATION_MIN = 120        # seconds
BBS_BREAK_DURATION_MAX = 300        # seconds
BBS_DISPLAY_COLOR = "green"         # "green", "amber", "white"
BBS_DEVICE_NAME = "TinyProgrammer"  # preferred name for registration

# =============================================================================
# HISTORY (Dashboard activity tracking)
# =============================================================================

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
HISTORY_MAX_EVENTS = 500

# =============================================================================
# SCHEDULE (Clock In / Clock Out)
# =============================================================================

SCHEDULE_ENABLED = False
SCHEDULE_CLOCK_IN = 9               # hour (0-23) — device starts coding
SCHEDULE_CLOCK_OUT = 23             # hour (0-23) — device stops, shows screensaver
