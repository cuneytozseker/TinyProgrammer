import os

# Tiny Programmer Configuration

# =============================================================================
# DISPLAY (Waveshare 4inch HDMI LCD - 800x480)
# =============================================================================

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

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
FONT_SIZE = 16                  # Larger font for bigger display
CHAR_WIDTH = 10                 # Will be calculated from font
CHAR_HEIGHT = 20

# Layout regions (pixel coordinates on 800x480 - scaled from 480x320)
# Scale factors: 800/480 = 1.667 horizontal, 480/320 = 1.5 vertical
# Original 480x320 values scaled up:
# Sidebar: file list (orig: x=5, y=63, w=90, h=210)
SIDEBAR_X = 8                   # 5 * 1.667
SIDEBAR_Y = 95                  # 63 * 1.5
SIDEBAR_W = 150                 # 90 * 1.667
SIDEBAR_H = 315                 # 210 * 1.5

# Code area: where code is rendered (orig: x=130, y=63, w=320, h=210)
CODE_AREA_X = 217               # 130 * 1.667
CODE_AREA_Y = 95                # 63 * 1.5
CODE_AREA_W = 533               # 320 * 1.667
CODE_AREA_H = 315               # 210 * 1.5

# Line number column (orig: x=105)
LINE_NUM_X = 175                # 105 * 1.667
LINE_NUM_W = 42

# Status bar (orig: y=289)
STATUS_BAR_Y = 434              # 289 * 1.5
STATUS_BAR_HEIGHT = 36          # 24 * 1.5

# Display modes
MODE_TERMINAL = "terminal"  # Code writing mode
MODE_RUN = "run"            # Program execution mode

# Canvas popup window (Mac OS floating window for program output)
# Original 480x320: x=29, y=35, chrome=422x242, draw_area=416x212
# The canvas.png is 422x242, will be scaled to 703x363
CANVAS_X = 48                # 29 * 1.667 (position on screen)
CANVAS_Y = 53                # 35 * 1.5
CANVAS_W = 703               # 422 * 1.667 (full chrome size after scaling)
CANVAS_H = 363               # 242 * 1.5
CANVAS_DRAW_OFFSET_X = 5     # Offset within scaled chrome
CANVAS_DRAW_OFFSET_Y = 45    # 30 * 1.5 (title bar height scaled)
CANVAS_DRAW_W = 693          # Draw area width (416 * 1.667)
CANVAS_DRAW_H = 318          # Draw area height (212 * 1.5)

# Framerate cap (HDMI can handle higher FPS)
TARGET_FPS = 60

# =============================================================================
# LLM
# =============================================================================

# Backend type: "ollama", "llamacpp", "gemini", or "anthropic"
LLM_BACKEND = "anthropic"  # Claude Haiku for Pi Zero

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
#GEMINI_MODEL = "gemini-2.0-flash-lite"  # Fast and cheap
GEMINI_MODEL = "gemini-3-flash-preview"

# Anthropic (Claude)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"  # Haiku 4.5

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
