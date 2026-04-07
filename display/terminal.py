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
import random
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
        self._terminal_image = None
        self._bbs_content_y = 0
        self._screensaver_mode = False

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

        # In BBS or screensaver mode, skip the IDE render
        if self._bbs_mode or self._screensaver_mode:
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

        # Push frame to web stream (non-blocking best-effort)
        try:
            from .frame_stream import put_frame
            put_frame(self.screen)
        except Exception:
            pass

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
    # Screensaver Mode
    # =========================================================================

    def enter_screensaver_mode(self):
        """Switch to screensaver — blank the screen."""
        self._screensaver_mode = True
        if not self.mock_mode:
            self.screen.fill((0, 0, 0))
            self._flip(force=True)

    def exit_screensaver_mode(self):
        """Leave screensaver, restore IDE background."""
        self._screensaver_mode = False
        if not self.mock_mode and self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
            self._flip(force=True)

    def flush(self):
        """Push the current screen surface to the display."""
        self._flip(force=True)

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

    # Terminal window chrome — scaled from 800x480 reference
    @property
    def _BBS_CHROME_X(self):
        return int(12 * self.width / 800)

    @property
    def _BBS_CHROME_Y(self):
        return int(55 * self.height / 480)

    @property
    def _BBS_DRAW_OFFSET_X(self):
        return int(5 * self.width / 800)

    @property
    def _BBS_DRAW_OFFSET_Y(self):
        return int(32 * self.height / 480)

    @property
    def _BBS_DRAW_W(self):
        return int(763 * self.width / 800)

    @property
    def _BBS_DRAW_H(self):
        return int(385 * self.height / 480)

    def _load_terminal_assets(self):
        """Load Terminal.png chrome for BBS mode, scaled to display resolution."""
        if self.mock_mode:
            return
        term_path = os.path.join(ASSETS_DIR, "Terminal.png")
        if os.path.exists(term_path):
            self._terminal_image = pygame.image.load(term_path)
            # Scale to fit current display (chrome is 775x423, designed for 800x480)
            target_w = self.width - self._BBS_CHROME_X * 2
            target_h = self.height - self._BBS_CHROME_Y - 4
            if self._terminal_image.get_size() != (target_w, target_h):
                self._terminal_image = pygame.transform.scale(
                    self._terminal_image, (target_w, target_h))
            print(f"[Terminal] Loaded BBS chrome: {term_path} (scaled to {target_w}x{target_h})")
        else:
            self._terminal_image = None
            print("[Terminal] Warning: Terminal.png not found")

    def _bbs_colors(self):
        scheme = getattr(config, "BBS_DISPLAY_COLOR", "green")
        return self.BBS_COLORS.get(scheme, self.BBS_COLORS["green"])

    @property
    def _bbs_x(self):
        """Absolute X of the BBS draw area on screen."""
        return self._BBS_CHROME_X + self._BBS_DRAW_OFFSET_X

    @property
    def _bbs_y(self):
        """Absolute Y of the BBS draw area on screen."""
        return self._BBS_CHROME_Y + self._BBS_DRAW_OFFSET_Y

    @property
    def _bbs_max_y(self):
        """Max Y for content before it goes outside the draw area."""
        return self._bbs_y + self._BBS_DRAW_H

    @property
    def _bbs_cols(self):
        """Max characters per line inside the terminal draw area."""
        return self._BBS_DRAW_W // self.char_width

    def enter_bbs_mode(self):
        """Switch display from IDE to BBS terminal aesthetic."""
        self._bbs_mode = True
        self._bbs_compose_text = ""
        self._bbs_compose_label = ""
        if not self.mock_mode:
            self._load_terminal_assets()
            self._render_bbs_chrome()

    def exit_bbs_mode(self):
        """Switch back to IDE display."""
        self._bbs_mode = False
        if not self.mock_mode and self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
            self._dirty = True

    def _render_bbs_chrome(self):
        """Draw the bg, terminal chrome, and fill draw area with BBS bg color."""
        if self.mock_mode:
            return
        colors = self._bbs_colors()

        # Draw the IDE background first (menu bar etc.)
        self.screen.blit(self.bg_image, (0, 0))

        # Blit terminal chrome
        if self._terminal_image:
            self.screen.blit(self._terminal_image,
                             (self._BBS_CHROME_X, self._BBS_CHROME_Y))

        # Fill draw area with BBS background color
        draw_rect = pygame.Rect(self._bbs_x, self._bbs_y,
                                self._BBS_DRAW_W, self._BBS_DRAW_H)
        pygame.draw.rect(self.screen, colors["bg"], draw_rect)

        # Draw banner inside terminal
        self._render_bbs_banner()
        self._flip(force=True)

    def _render_bbs_banner(self):
        """Draw the ASCII art header inside the terminal draw area."""
        if self.mock_mode:
            return
        colors = self._bbs_colors()
        y = self._bbs_y + 4
        for line in self.BBS_BANNER:
            surf = self.font.render(line, True, colors["accent"])
            self.screen.blit(surf, (self._bbs_x + 8, y))
            y += self.char_height

    def _bbs_clear_content(self):
        """Clear the content area below the banner inside the terminal."""
        if self.mock_mode:
            return
        colors = self._bbs_colors()
        # Banner takes ~6 lines + padding
        content_y = self._bbs_y + (len(self.BBS_BANNER) * self.char_height) + 12
        content_h = self._bbs_max_y - content_y
        rect = pygame.Rect(self._bbs_x, content_y, self._BBS_DRAW_W, content_h)
        pygame.draw.rect(self.screen, colors["bg"], rect)
        # Store for render methods
        self._bbs_content_y = content_y

    def _bbs_render_scrolled(self, lines, title=None):
        """Render lines with auto-scrolling inside the terminal draw area.

        Each entry in lines is (text, color_key) where color_key is
        'text', 'dim', 'accent', or 'separator'.
        If title is set, it stays pinned at the top while lines scroll below.
        """
        if self.mock_mode:
            return
        colors = self._bbs_colors()
        lx = self._bbs_x + 8
        content_y = self._bbs_content_y + 4

        # Reserve space for pinned title
        title_rows = 0
        if title:
            title_rows = 2  # title line + separator
            content_y += title_rows * self.char_height

        visible_h = self._bbs_max_y - content_y
        visible_rows = visible_h // self.char_height

        # Draw pinned title + first screenful
        offset = 0
        self._bbs_draw_title(title, colors, lx)
        self._bbs_draw_lines(lines, offset, visible_rows, colors, lx, content_y)
        self._flip(force=True)

        # If everything fits, done
        if len(lines) <= visible_rows:
            return

        # Pause on first screenful
        time.sleep(random.uniform(2.0, 3.5))

        # Scroll through remaining lines
        while offset + visible_rows < len(lines):
            offset += 1
            self._bbs_clear_content()
            self._bbs_draw_title(title, colors, lx)
            self._bbs_draw_lines(lines, offset, visible_rows, colors, lx, content_y)
            self._flip(force=True)
            time.sleep(random.uniform(0.15, 0.35))

        # Pause on last screenful
        time.sleep(random.uniform(1.5, 3.0))

    def _bbs_draw_title(self, title, colors, lx):
        """Draw the pinned board title at the top of the content area."""
        if not title:
            return
        y = self._bbs_content_y + 4
        surf = self.font.render(title, True, colors["accent"])
        self.screen.blit(surf, (lx, y))
        # Separator line below title
        sep_y = y + self.char_height + 2
        pygame.draw.line(self.screen, colors["border"],
                         (lx, sep_y), (self._bbs_x + self._BBS_DRAW_W - 8, sep_y))

    def _bbs_draw_lines(self, lines, offset, visible_rows, colors, lx, start_y):
        """Draw a window of lines at the given offset."""
        y = start_y
        for line_text, color_key in lines[offset:offset + visible_rows]:
            if color_key == "separator":
                pygame.draw.line(self.screen, colors["border"],
                                 (lx, y + self.char_height // 2),
                                 (self._bbs_x + self._BBS_DRAW_W - 8,
                                  y + self.char_height // 2))
            else:
                color = colors.get(color_key, colors["text"])
                surf = self.font.render(line_text, True, color)
                self.screen.blit(surf, (lx, y))
            y += self.char_height

    def _bbs_wrap(self, text, indent=0):
        """Wrap text to fit terminal width, return list of strings."""
        max_chars = self._bbs_cols - 2 - indent
        if max_chars < 10:
            max_chars = 10
        result = []
        for i in range(0, len(text), max_chars):
            result.append((" " * indent) + text[i:i + max_chars])
        return result if result else [""]

    def render_bbs_menu(self, stats, device_name):
        """Render the BBS main menu with board listing."""
        if self.mock_mode:
            return
        colors = self._bbs_colors()
        self._bbs_clear_content()

        lines = []
        lines.append((f"Welcome, {device_name}!", "accent"))
        lines.append(("", "separator"))

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
            lines.append((f"  [{slug[:3].upper()}]  {label:<20s} ({count} posts)", "text"))

        self._bbs_render_scrolled(lines)

    def render_bbs_feed(self, board, posts):
        """Render a flat board feed with auto-scrolling."""
        if self.mock_mode:
            return
        self._bbs_clear_content()

        board_titles = {
            "chat": "Chat", "news": "News", "jokes": "Jokes",
            "science_tech": "Science & Tech", "lurk_report": "Lurk Report",
        }
        title = f"--- {board_titles.get(board, board.upper())} ---"

        lines = []
        for p in posts:
            author = p.get("author", "?")
            content = p.get("content", "")
            lines.append((f"{author}:", "accent"))
            for wrapped in self._bbs_wrap(content, indent=1):
                lines.append((wrapped, "text"))
            lines.append(("", "text"))

        self._bbs_render_scrolled(lines, title=title)

    def render_bbs_thread_list(self, threads):
        """Render Code Share thread listing."""
        if self.mock_mode:
            return
        self._bbs_clear_content()

        lines = []
        for i, t in enumerate(threads):
            title = t.get("title", "untitled")[:40]
            author = t.get("author", "?")
            lines.append((f"  {i+1:2d}. {title}  ({author})", "text"))

        self._bbs_render_scrolled(lines, title="--- Code Share ---")

    def render_bbs_thread_detail(self, detail):
        """Render a thread's top post and replies with auto-scrolling."""
        if self.mock_mode:
            return
        self._bbs_clear_content()

        post = detail.get("post", {})
        post_title = post.get("title", "untitled")
        author = post.get("author", "?")
        pinned_title = f"[{post_title}] by {author}"

        lines = []
        content = post.get("content", "")
        for code_line in content.split("\n"):
            for wrapped in self._bbs_wrap(code_line):
                lines.append((wrapped, "text"))

        lines.append(("", "separator"))

        for r in detail.get("replies", []):
            rauthor = r.get("author", "?")
            rcontent = r.get("content", "")
            lines.append((f"{rauthor}:", "accent"))
            for wrapped in self._bbs_wrap(rcontent, indent=1):
                lines.append((wrapped, "dim"))
            lines.append(("", "text"))

        self._bbs_render_scrolled(lines, title=pinned_title)

    def render_bbs_compose(self, context):
        """Show the multi-line compose area in the bottom of the terminal."""
        if self.mock_mode:
            return
        self._bbs_compose_label = context
        self._bbs_compose_text = ""
        colors = self._bbs_colors()
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
        """Redraw the compose box at the bottom of the terminal draw area."""
        compose_h = self.char_height * 6 + 28
        y_start = self._bbs_max_y - compose_h
        lx = self._bbs_x + 8
        compose_w = self._BBS_DRAW_W
        max_chars = self._bbs_cols - 2

        rect = pygame.Rect(self._bbs_x, y_start, compose_w, compose_h)
        pygame.draw.rect(self.screen, colors["bg"], rect)

        pygame.draw.line(self.screen, colors["border"],
                         (lx, y_start), (self._bbs_x + compose_w - 8, y_start))

        label = f" composing ({self._bbs_compose_label}) "
        label_surf = self.font.render(label, True, colors["accent"])
        self.screen.blit(label_surf, (lx, y_start + 4))

        if header_only:
            return

        text = self._bbs_compose_text
        lines = []
        for i in range(0, len(text) + 1, max_chars):
            lines.append(text[i:i + max_chars])

        max_lines = 5
        visible_lines = lines[-max_lines:]

        y = y_start + 24
        for line in visible_lines:
            surf = self.font.render(line, True, colors["text"])
            self.screen.blit(surf, (lx + 4, y))
            y += self.char_height
