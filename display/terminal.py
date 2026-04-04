"""
Terminal Display for TFT Screen - Retro Mac OS IDE Theme

Renders to an in-memory pygame surface with a classic Mac OS IDE background,
then writes directly to framebuffer. Bypasses SDL's broken fbcon driver.

Layout (480x320):
- Title bar + menus (from bg.png, static)
- Toolbar with icons (from bg.png, static)
- Sidebar: dynamic file list
- Code area: code with line numbers
- Status bar: line/col info and state
- Canvas popup: floating window for program output (composited on top)
"""

import os
import time
from typing import Tuple, Optional, Callable, List

# Force pygame to use dummy driver (we handle display ourselves)
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

import config
from .framebuffer import get_writer, IS_FRAMEBUFFER_AVAILABLE

# Initialize pygame with dummy driver
PYGAME_AVAILABLE = True
try:
    pygame.init()
except Exception as e:
    PYGAME_AVAILABLE = False
    print(f"[Terminal] pygame init failed: {e}")

# Path to assets relative to this file
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


class Terminal:
    """
    TFT terminal emulator with retro Mac OS IDE theme.
    Uses bg.png as background, Space Mono for code text,
    canvas.png as popup window for program output.
    """

    def __init__(self, width: int, height: int,
                 color_bg: Tuple[int, int, int],
                 color_fg: Tuple[int, int, int],
                 font_name: str, font_size: int,
                 status_bar_height: int = 16):
        self.width = width
        self.height = height
        self.color_bg = color_bg
        self.color_fg = color_fg
        self.screen = None
        self.font = None
        self.mock_mode = False
        self.fb_writer = None

        # Layout regions from config (scaled for display size)
        self.code_area_x = config.CODE_AREA_X
        self.code_area_y = config.CODE_AREA_Y
        self.code_area_w = config.CODE_AREA_W
        self.code_area_h = config.CODE_AREA_H
        self.line_num_x = config.LINE_NUM_X
        self.sidebar_x = config.SIDEBAR_X
        self.sidebar_y = config.SIDEBAR_Y
        self.sidebar_w = config.SIDEBAR_W
        self.sidebar_h = config.SIDEBAR_H
        self.status_bar_y = config.STATUS_BAR_Y

        self._init_display(font_name, font_size)
        self.char_width, self.char_height = self._get_char_size()

        # Calculate code area dimensions in characters
        self.cols = self.code_area_w // self.char_width
        self.rows = self.code_area_h // self.char_height

        # Cursor state
        self.cursor_x = 0
        self.cursor_y = 0
        self.cursor_visible = True
        self.cursor_enabled = True
        self.cursor_blink_time = 0

        # Text buffer
        self.lines = [""] * self.rows
        self.line_offset = 0

        # State
        self.current_state = "booting"
        self.current_mood = ""
        self.current_model = "?"

        # Sidebar file list
        self.sidebar_files: List[str] = []
        self.sidebar_current: str = ""

        # Canvas popup state
        self.canvas_surface = None
        self.canvas_visible = False
        self.canvas_image = None
        self._load_canvas_assets()

        # BBS mode state
        self._bbs_mode = False
        self._bbs_compose_text = ""
        self._bbs_compose_label = ""

        # Performance
        self.clock = pygame.time.Clock() if PYGAME_AVAILABLE else None
        self._dirty = True
        self._last_flip = 0
        self._min_flip_interval = 0.033  # ~30fps max

        self.clear()

    def _init_display(self, font_name: str, font_size: int):
        if not PYGAME_AVAILABLE:
            self.mock_mode = True
            return

        # Hide system mouse cursor
        pygame.mouse.set_visible(False)

        # Create in-memory surface for rendering
        self.screen = pygame.Surface((self.width, self.height))

        # Load background image (use resolution-specific if available)
        bg_path = os.path.join(ASSETS_DIR, f"bg-{self.width}-{self.height}.png")
        if not os.path.exists(bg_path):
            bg_path = os.path.join(ASSETS_DIR, "bg.png")

        if os.path.exists(bg_path):
            self.bg_image = pygame.image.load(bg_path)
            if self.bg_image.get_size() != (self.width, self.height):
                self.bg_image = pygame.transform.scale(
                    self.bg_image, (self.width, self.height))
            print(f"[Terminal] Loaded background: {bg_path}")
        else:
            self.bg_image = pygame.Surface((self.width, self.height))
            self.bg_image.fill((255, 255, 255))
            print(f"[Terminal] No bg.png found, using white background")

        # Initialize framebuffer writer
        if IS_FRAMEBUFFER_AVAILABLE:
            self.fb_writer = get_writer(self.width, self.height)
            print(f"[Terminal] Using direct framebuffer: {self.fb_writer.device}")
        else:
            print("[Terminal] No framebuffer, using windowed mode")
            os.environ.pop("SDL_VIDEODRIVER", None)
            pygame.quit()
            pygame.init()
            self._window = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Tiny Programmer")
            # Load resolution-specific background if available
            bg_path = os.path.join(ASSETS_DIR, f"bg-{self.width}-{self.height}.png")
            if not os.path.exists(bg_path):
                bg_path = os.path.join(ASSETS_DIR, "bg.png")
            if os.path.exists(bg_path):
                self.bg_image = pygame.image.load(bg_path)
                if self.bg_image.get_size() != (self.width, self.height):
                    self.bg_image = pygame.transform.scale(
                        self.bg_image, (self.width, self.height))

        # Load Space Mono font
        font_path = os.path.join(ASSETS_DIR, "SpaceMono-Regular.ttf")
        if os.path.exists(font_path):
            self.font = pygame.font.Font(font_path, font_size)
            print(f"[Terminal] Loaded font: SpaceMono-Regular ({font_size}pt)")
        else:
            try:
                self.font = pygame.font.SysFont(font_name, font_size)
                print(f"[Terminal] Using system font: {font_name}")
            except:
                self.font = pygame.font.Font(None, font_size)
                print(f"[Terminal] Using default font")

        # Load bold font for sidebar selected item
        bold_path = os.path.join(ASSETS_DIR, "SpaceMono-Bold.ttf")
        if os.path.exists(bold_path):
            self.font_bold = pygame.font.Font(bold_path, font_size)
        else:
            self.font_bold = self.font

    def _load_canvas_assets(self):
        """Load the canvas.png popup window chrome."""
        if self.mock_mode:
            return
        canvas_path = os.path.join(ASSETS_DIR, "canvas.png")
        if os.path.exists(canvas_path):
            # Don't use convert_alpha() — it requires a display surface
            # which doesn't exist with the dummy driver + framebuffer path.
            # pygame.image.load() preserves the PNG alpha channel already.
            self.canvas_image = pygame.image.load(canvas_path)
            # Scale canvas chrome to match display resolution
            if self.canvas_image.get_size() != (config.CANVAS_W, config.CANVAS_H):
                self.canvas_image = pygame.transform.scale(
                    self.canvas_image, (config.CANVAS_W, config.CANVAS_H))
            print(f"[Terminal] Loaded canvas chrome: {canvas_path}")
        else:
            print(f"[Terminal] Warning: canvas.png not found")

    def _get_char_size(self) -> Tuple[int, int]:
        if self.mock_mode:
            return (8, 16)
        surface = self.font.render("M", True, self.color_fg)
        return surface.get_width(), surface.get_height()

    # =========================================================================
    # Canvas popup methods
    # =========================================================================

    def show_canvas(self):
        """Show the canvas popup window and create the drawing surface."""
        self.canvas_surface = pygame.Surface(
            (config.CANVAS_DRAW_W, config.CANVAS_DRAW_H))
        self.canvas_surface.fill((0, 0, 0))
        self.canvas_visible = True
        self._dirty = True
        print("[Terminal] Canvas popup shown")

    def hide_canvas(self):
        """Hide the canvas popup window."""
        self.canvas_visible = False
        self.canvas_surface = None
        self._dirty = True
        print("[Terminal] Canvas popup hidden")

    def enable_cursor(self):
        """Show the blinking text cursor."""
        self.cursor_enabled = True
        self._dirty = True

    def disable_cursor(self):
        """Hide the blinking text cursor."""
        self.cursor_enabled = False
        self._dirty = True

    # =========================================================================
    # Text input methods
    # =========================================================================

    def clear(self):
        """Clear the code area."""
        self.lines = [""] * self.rows
        self.cursor_x = 0
        self.cursor_y = 0
        self.line_offset = 0
        self._render()

    def type_char(self, char: str, render: bool = True):
        """Type a single character to the code area."""
        if char == '\n':
            self._newline()
        elif char == '\b':
            self._backspace()
        elif char == '\t':
            for _ in range(4):
                self.type_char(' ', render=False)
        else:
            if self.cursor_x < self.cols:
                line = self.lines[self.cursor_y]
                while len(line) < self.cursor_x:
                    line += ' '
                self.lines[self.cursor_y] = (
                    line[:self.cursor_x] + char + line[self.cursor_x + 1:])
                self.cursor_x += 1
            if self.cursor_x >= self.cols:
                self._newline()
        self._dirty = True
        if render:
            self._render()

    def type_string(self, text: str,
                    delay_func: Optional[Callable[[], float]] = None):
        """Type a string character by character."""
        for char in text:
            self.type_char(char)
            if delay_func:
                delay = delay_func()
                if delay > 0:
                    time.sleep(delay)
                    self._handle_events()

    def _newline(self):
        self.cursor_x = 0
        self.cursor_y += 1
        self.line_offset += 1
        if self.cursor_y >= self.rows:
            self._scroll()

    def _backspace(self):
        if self.cursor_x > 0:
            self.cursor_x -= 1
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = (
                line[:self.cursor_x] + line[self.cursor_x + 1:])
        elif self.cursor_y > 0:
            self.cursor_y -= 1
            self.cursor_x = len(self.lines[self.cursor_y])

    def _scroll(self):
        self.lines = self.lines[1:] + [""]
        self.cursor_y = self.rows - 1

    def set_status(self, state: str, mood: str = ""):
        """Update the status bar state text."""
        self.current_state = state
        self.current_mood = mood
        self._render()

    def set_file_list(self, files: List[str], current: str = ""):
        """Update the sidebar file list."""
        self.sidebar_files = files
        self.sidebar_current = current
        self._dirty = True

    # =========================================================================
    # Rendering pipeline (single composited frame)
    # =========================================================================

    def _render(self):
        """Render the full IDE display with optional canvas popup."""
        if self.mock_mode:
            return

        # In BBS mode, skip the IDE render — BBS methods handle their own drawing
        if self._bbs_mode:
            self._flip()
            return

        # 1. Draw background image (title bar, toolbar, borders)
        self.screen.blit(self.bg_image, (0, 0))

        # 2. Render sidebar file list
        self._render_sidebar()

        # 3. Render line numbers + code text
        self._render_code()

        # 4. Render cursor
        self._render_cursor()

        # 5. Render status bar
        self._render_status()

        # 6. Composite canvas popup on top (if visible)
        if self.canvas_visible and self.canvas_image and self.canvas_surface:
            self.screen.blit(self.canvas_image,
                             (config.CANVAS_X, config.CANVAS_Y))
            self.screen.blit(self.canvas_surface,
                             (config.CANVAS_X + config.CANVAS_DRAW_OFFSET_X,
                              config.CANVAS_Y + config.CANVAS_DRAW_OFFSET_Y))

        # 7. Single flip to framebuffer
        self._flip()

    def _render_sidebar(self):
        """Render the file list in the sidebar."""
        if not self.sidebar_files:
            return

        sidebar_font_size = max(9, self.font.get_height() - 2)
        y = self.sidebar_y + 2
        max_files = self.sidebar_h // (sidebar_font_size + 4)

        for i, filename in enumerate(self.sidebar_files[:max_files]):
            display_name = filename
            if len(display_name) > 12:
                display_name = display_name[:11] + "."

            is_current = (filename == self.sidebar_current)

            if is_current:
                sel_rect = pygame.Rect(
                    self.sidebar_x, y - 1,
                    self.sidebar_w, sidebar_font_size + 3)
                pygame.draw.rect(self.screen, (0, 0, 0), sel_rect)
                txt = self.font_bold.render(
                    display_name, True, (255, 255, 255))
            else:
                txt = self.font.render(
                    display_name, True, (0, 0, 0))

            self.screen.blit(txt, (self.sidebar_x + 3, y))
            y += sidebar_font_size + 4

    def _render_code(self):
        """Render line numbers and code text in the code area."""
        total_lines_before = max(0, self.line_offset - self.cursor_y)

        for row, line in enumerate(self.lines):
            y = self.code_area_y + row * self.char_height

            if y + self.char_height > self.code_area_y + self.code_area_h:
                break

            line_num = total_lines_before + row + 1
            ln_text = f"{line_num:3d}"
            ln_surface = self.font.render(ln_text, True, (128, 128, 128))
            self.screen.blit(ln_surface, (self.line_num_x, y))

            if line:
                max_chars = self.cols
                display_line = line[:max_chars]
                txt_surface = self.font.render(
                    display_line, True, self.color_fg)
                self.screen.blit(txt_surface, (self.code_area_x, y))

    def _render_cursor(self):
        """Render the blinking cursor in the code area."""
        if self.cursor_enabled and self.cursor_visible:
            cx = self.code_area_x + self.cursor_x * self.char_width
            cy = self.code_area_y + self.cursor_y * self.char_height
            if (cx < self.code_area_x + self.code_area_w and
                    cy < self.code_area_y + self.code_area_h):
                cursor_rect = pygame.Rect(
                    cx, cy, self.char_width, self.char_height)
                pygame.draw.rect(self.screen, self.color_fg, cursor_rect)

    def _render_status(self):
        """Render the status bar at the bottom as a single line."""
        # Build status with model name
        status = f"Who: {self.current_model} | STATUS: {self.current_state}"
        if self.current_mood:
            status += f" | Mood: {self.current_mood}"

        st_surface = self.font_bold.render(status, True, (0, 0, 0))
        # Position status text (moved 4px up and 30px right)
        status_x = self.code_area_x + 30
        status_y = self.status_bar_y + 1  # was +5, now +1 (4px up)
        self.screen.blit(st_surface, (status_x, status_y))

    def set_model_name(self, model_name: str):
        """Set the display name for the current model."""
        self.current_model = model_name
        self._dirty = True

    # =========================================================================
    # Framebuffer output
    # =========================================================================

    def _flip(self, force: bool = False):
        """Send the rendered surface to the display. Rate-limited."""
        now = time.time()
        if not force and (now - self._last_flip) < self._min_flip_interval:
            return

        self._last_flip = now
        self._dirty = False

        if self.fb_writer:
            self.fb_writer.write(self.screen)
        elif hasattr(self, '_window'):
            self._window.blit(self.screen, (0, 0))
            pygame.display.flip()

    # =========================================================================
    # Canvas drawing commands (from running programs)
    # =========================================================================

    def process_draw_command(self, cmd_str: str):
        """Process drawing commands onto the canvas surface (not the screen).

        Commands are drawn to self.canvas_surface and composited during
        _render(). No direct _flip() call — avoids tearing on SPI display.
        """
        if self.mock_mode or not cmd_str.startswith("CMD:"):
            return
        if self.canvas_surface is None:
            return

        target = self.canvas_surface

        try:
            parts = cmd_str.strip().split(':')[1].split(',')
            c = parts[0]
            args = [int(x) for x in parts[1:]]
            if c == "CLEAR":
                target.fill(tuple(args[:3]))
            elif c == "PIXEL":
                target.set_at((args[0], args[1]), tuple(args[2:]))
            elif c == "LINE":
                pygame.draw.line(
                    target, tuple(args[4:]),
                    (args[0], args[1]), (args[2], args[3]))
            elif c == "RECT":
                pygame.draw.rect(
                    target, tuple(args[4:]),
                    (args[0], args[1], args[2], args[3]), 1)
            elif c == "FILLRECT":
                pygame.draw.rect(
                    target, tuple(args[4:]),
                    (args[0], args[1], args[2], args[3]))
            elif c == "CIRCLE":
                pygame.draw.circle(
                    target, tuple(args[3:]),
                    (args[0], args[1]), args[2], 1)
            elif c == "FILLCIRCLE":
                pygame.draw.circle(
                    target, tuple(args[3:]),
                    (args[0], args[1]), args[2])
            self._dirty = True  # Will be composited on next _render()
        except Exception as e:
            pass  # Silently ignore malformed commands

    # =========================================================================
    # Event handling and tick
    # =========================================================================

    def update_cursor_blink(self):
        if time.time() - self.cursor_blink_time > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_blink_time = time.time()
            self._dirty = True

    def _handle_events(self):
        if self.mock_mode:
            return
        if hasattr(self, '_window'):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
        else:
            pygame.event.pump()

    def tick(self, fps: int = 30):
        self._handle_events()
        self.update_cursor_blink()
        if self._dirty:
            self._render()
        if self.clock:
            self.clock.tick(fps)

    def shutdown(self):
        if PYGAME_AVAILABLE and not self.mock_mode:
            if self.fb_writer:
                self.fb_writer.clear(0, 0, 0)
            pygame.quit()

    def check_ghosting_refresh(self):
        pass

    # =========================================================================
    # BBS Display Mode
    # =========================================================================

    BBS_COLORS = {
        "green":  {"text": (51, 255, 51), "dim": (51, 90, 51), "accent": (255, 170, 0), "bg": (10, 10, 10), "border": (26, 90, 26)},
        "amber":  {"text": (255, 176, 0), "dim": (128, 88, 0), "accent": (255, 220, 100), "bg": (10, 8, 2), "border": (90, 62, 0)},
        "white":  {"text": (200, 200, 200), "dim": (100, 100, 100), "accent": (255, 255, 255), "bg": (10, 10, 10), "border": (60, 60, 60)},
    }

    BBS_BANNER = [
        " _____ _             ____  ____  ____  ",
        "|_   _(_)_ __  _   _| __ )| __ )/ ___| ",
        "  | | | | '_ \\| | | |  _ \\|  _ \\___ \\ ",
        "  | | | | | | | |_| | |_) | |_) |___) |",
        "  |_| |_|_| |_|\\__, |____/|____/|____/ ",
        "               |___/  v0.1",
    ]

    def _bbs_colors(self):
        scheme = getattr(config, "BBS_DISPLAY_COLOR", "green")
        return self.BBS_COLORS.get(scheme, self.BBS_COLORS["green"])

    def enter_bbs_mode(self):
        """Switch display from IDE to BBS terminal aesthetic."""
        self._bbs_mode = True
        self._bbs_compose_text = ""
        self._bbs_compose_label = ""
        if not self.mock_mode:
            colors = self._bbs_colors()
            self.screen.fill(colors["bg"])
            self._dirty = True
            self._render_bbs_banner()

    def exit_bbs_mode(self):
        """Switch back to IDE display."""
        self._bbs_mode = False
        if not self.mock_mode and self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
            self._dirty = True

    def _render_bbs_banner(self):
        """Draw the ASCII art header."""
        if self.mock_mode:
            return
        colors = self._bbs_colors()
        y = 8
        for line in self.BBS_BANNER:
            surf = self.font.render(line, True, colors["accent"])
            self.screen.blit(surf, (16, y))
            y += self.char_height
        self._flip(force=True)

    def _bbs_clear_content(self):
        """Clear the content area below the banner."""
        if self.mock_mode:
            return
        colors = self._bbs_colors()
        content_y = 95
        rect = pygame.Rect(0, content_y, self.width, self.height - content_y)
        pygame.draw.rect(self.screen, colors["bg"], rect)

    def render_bbs_menu(self, stats, device_name):
        """Render the BBS main menu with board listing."""
        if self.mock_mode:
            return
        colors = self._bbs_colors()
        self._bbs_clear_content()

        y = 100
        # Welcome line
        welcome = f"Welcome, {device_name}!"
        surf = self.font.render(welcome, True, colors["accent"])
        self.screen.blit(surf, (16, y))
        y += self.char_height + 8

        # Separator
        pygame.draw.line(self.screen, colors["border"], (16, y), (self.width - 16, y))
        y += 8

        # Board listing
        board_names = {
            "code_share": "Code Share",
            "chat": "Chat",
            "news": "News",
            "science_tech": "Science & Tech",
            "jokes": "Jokes",
            "lurk_report": "Lurk Report",
        }
        stats_map = {s["board"]: s["total_posts"] for s in stats}

        for slug, label in board_names.items():
            count = stats_map.get(slug, 0)
            line = f"  [{slug[:3].upper()}]  {label:<20s} ({count} posts)"
            surf = self.font.render(line, True, colors["text"])
            self.screen.blit(surf, (16, y))
            y += self.char_height + 2

        self._flip(force=True)

    def render_bbs_feed(self, board, posts):
        """Render a flat board feed."""
        if self.mock_mode:
            return
        colors = self._bbs_colors()
        self._bbs_clear_content()

        y = 100
        title = f"--- {board.upper()} ---"
        surf = self.font.render(title, True, colors["accent"])
        self.screen.blit(surf, (16, y))
        y += self.char_height + 8

        for p in posts:
            if y > 400:
                break
            author = p.get("author", "?")
            content = p.get("content", "")[:80]
            # Author line
            author_surf = self.font.render(f"{author}:", True, colors["accent"])
            self.screen.blit(author_surf, (16, y))
            y += self.char_height
            # Content line(s)
            for i in range(0, len(content), 70):
                chunk = content[i:i+70]
                txt_surf = self.font.render(chunk, True, colors["text"])
                self.screen.blit(txt_surf, (24, y))
                y += self.char_height
            # Separator
            y += 4

        self._flip(force=True)

    def render_bbs_thread_list(self, threads):
        """Render Code Share thread listing."""
        if self.mock_mode:
            return
        colors = self._bbs_colors()
        self._bbs_clear_content()

        y = 100
        title_surf = self.font.render("--- CODE SHARE ---", True, colors["accent"])
        self.screen.blit(title_surf, (16, y))
        y += self.char_height + 8

        for i, t in enumerate(threads):
            if y > 400:
                break
            title = t.get("title", "untitled")[:40]
            author = t.get("author", "?")
            line = f"  {i+1:2d}. {title}  ({author})"
            surf = self.font.render(line, True, colors["text"])
            self.screen.blit(surf, (16, y))
            y += self.char_height + 2

        self._flip(force=True)

    def render_bbs_thread_detail(self, detail):
        """Render a thread's top post and replies."""
        if self.mock_mode:
            return
        colors = self._bbs_colors()
        self._bbs_clear_content()

        y = 100
        post = detail.get("post", {})
        title = post.get("title", "untitled")
        author = post.get("author", "?")

        # Title
        surf = self.font.render(f"[{title}] by {author}", True, colors["accent"])
        self.screen.blit(surf, (16, y))
        y += self.char_height + 4

        # Code content (truncated to fit)
        content = post.get("content", "")
        for line in content.split("\n")[:12]:
            if y > 350:
                break
            surf = self.font.render(line[:70], True, colors["text"])
            self.screen.blit(surf, (16, y))
            y += self.char_height

        # Separator
        y += 4
        pygame.draw.line(self.screen, colors["border"], (16, y), (self.width - 16, y))
        y += 8

        # Replies
        for r in detail.get("replies", [])[:5]:
            if y > 430:
                break
            rauthor = r.get("author", "?")
            rcontent = r.get("content", "")[:60]
            surf = self.font.render(f"{rauthor}: {rcontent}", True, colors["dim"])
            self.screen.blit(surf, (24, y))
            y += self.char_height + 2

        self._flip(force=True)

    # Compose area: bottom third of content area (y: 300-440, ~8 lines)
    _BBS_COMPOSE_Y = 300
    _BBS_COMPOSE_H = 140
    _BBS_COMPOSE_COLS = 75  # chars per line

    def render_bbs_compose(self, context):
        """Show the multi-line compose area in the bottom third."""
        if self.mock_mode:
            return
        self._bbs_compose_label = context
        self._bbs_compose_text = ""
        colors = self._bbs_colors()

        # Clear compose area and draw header
        self._bbs_redraw_compose(colors, header_only=True)
        self._flip(force=True)

    def type_bbs_char(self, char):
        """Type a character in the multi-line BBS compose area."""
        if self.mock_mode:
            return
        self._bbs_compose_text += char
        self._bbs_redraw_compose(self._bbs_colors())
        self._dirty = True

    def _bbs_redraw_compose(self, colors, header_only=False):
        """Redraw the compose box with current text."""
        y_start = self._BBS_COMPOSE_Y
        rect = pygame.Rect(0, y_start, self.width, self._BBS_COMPOSE_H)
        pygame.draw.rect(self.screen, colors["bg"], rect)

        # Top border
        pygame.draw.line(self.screen, colors["border"],
                         (16, y_start), (self.width - 16, y_start))

        # Label
        label = f" composing ({self._bbs_compose_label}) "
        label_surf = self.font.render(label, True, colors["accent"])
        self.screen.blit(label_surf, (16, y_start + 4))

        if header_only:
            return

        # Wrap text into lines
        text = self._bbs_compose_text
        cols = self._BBS_COMPOSE_COLS
        lines = []
        for i in range(0, len(text) + 1, cols):
            lines.append(text[i:i + cols])

        # Show last N lines that fit
        max_lines = (self._BBS_COMPOSE_H - 28) // self.char_height
        visible_lines = lines[-max_lines:]

        y = y_start + 24
        for line in visible_lines:
            surf = self.font.render(line, True, colors["text"])
            self.screen.blit(surf, (20, y))
            y += self.char_height
