"""
Terminal Display for TFT Screen

Renders to an in-memory pygame surface, then writes directly to framebuffer.
This bypasses SDL's broken fbcon driver on Bookworm/Trixie.

Two modes:
- TERMINAL: Shows code being written character by character
- RUN: Displays program output (can be graphical)
"""

import os
import time
from typing import Tuple, Optional, Callable

# Force pygame to use dummy driver (we handle display ourselves)
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

from .framebuffer import get_writer, IS_FRAMEBUFFER_AVAILABLE

# Initialize pygame with dummy driver
PYGAME_AVAILABLE = True
try:
    pygame.init()
except Exception as e:
    PYGAME_AVAILABLE = False
    print(f"[Terminal] pygame init failed: {e}")


class Terminal:
    """
    TFT terminal emulator using pygame for rendering,
    direct framebuffer writes for display.
    """

    def __init__(self, width: int, height: int,
                 color_bg: Tuple[int, int, int],
                 color_fg: Tuple[int, int, int],
                 font_name: str, font_size: int,
                 status_bar_height: int = 32):
        self.width = width
        self.height = height
        self.color_bg = color_bg
        self.color_fg = color_fg
        self.status_bar_height = status_bar_height
        self.terminal_height = height - status_bar_height
        self.screen = None
        self.font = None
        self.mock_mode = False
        self.fb_writer = None

        self._init_display(font_name, font_size)
        self.char_width, self.char_height = self._get_char_size()
        self.cols = width // self.char_width
        self.rows = self.terminal_height // self.char_height
        self.cursor_x = 0
        self.cursor_y = 0
        self.cursor_visible = True
        self.cursor_blink_time = 0
        self.lines = [""] * self.rows
        self.current_state = "booting"
        self.current_mood = ""
        self.clock = pygame.time.Clock() if PYGAME_AVAILABLE else None
        self._dirty = True  # Track if we need to redraw
        self._last_flip = 0  # Rate limit framebuffer writes
        self._min_flip_interval = 0.033  # ~30fps max
        self.clear()

    def _init_display(self, font_name: str, font_size: int):
        if not PYGAME_AVAILABLE:
            self.mock_mode = True
            return

        # Create in-memory surface for rendering
        self.screen = pygame.Surface((self.width, self.height))

        # Initialize framebuffer writer
        if IS_FRAMEBUFFER_AVAILABLE:
            self.fb_writer = get_writer(self.width, self.height)
            print(f"[Terminal] Using direct framebuffer: {self.fb_writer.device}")
        else:
            # Desktop mode - create a window for testing
            print("[Terminal] No framebuffer, using windowed mode")
            os.environ.pop("SDL_VIDEODRIVER", None)
            pygame.quit()
            pygame.init()
            self._window = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Tiny Programmer")

        # Load font
        try:
            self.font = pygame.font.SysFont(font_name, font_size)
        except:
            self.font = pygame.font.Font(None, font_size)

    def _get_char_size(self) -> Tuple[int, int]:
        if self.mock_mode:
            return (9, 16)
        surface = self.font.render("M", True, self.color_fg)
        return surface.get_width(), surface.get_height()

    def clear(self):
        self.lines = [""] * self.rows
        self.cursor_x = 0
        self.cursor_y = 0
        self._render()

    def type_char(self, char: str, render: bool = True):
        """Type a single character. Set render=False to batch updates."""
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
                self.lines[self.cursor_y] = line[:self.cursor_x] + char + line[self.cursor_x + 1:]
                self.cursor_x += 1
            if self.cursor_x >= self.cols:
                self._newline()
        self._dirty = True
        if render:
            self._render()

    def type_string(self, text: str, delay_func: Optional[Callable[[], float]] = None):
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
        if self.cursor_y >= self.rows:
            self._scroll()

    def _backspace(self):
        if self.cursor_x > 0:
            self.cursor_x -= 1
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x + 1:]
        elif self.cursor_y > 0:
            self.cursor_y -= 1
            self.cursor_x = len(self.lines[self.cursor_y])

    def _scroll(self):
        self.lines = self.lines[1:] + [""]
        self.cursor_y = self.rows - 1

    def set_status(self, state: str, mood: str = ""):
        self.current_state = state
        self.current_mood = mood
        self._render()

    def _render(self):
        if self.mock_mode:
            return

        # Render to in-memory surface
        self.screen.fill(self.color_bg)

        # Draw text lines
        for row, line in enumerate(self.lines):
            if line:
                y = row * self.char_height
                txt = self.font.render(line, True, self.color_fg)
                self.screen.blit(txt, (0, y))

        # Draw cursor
        if self.cursor_visible:
            r = pygame.Rect(
                self.cursor_x * self.char_width,
                self.cursor_y * self.char_height,
                self.char_width,
                self.char_height
            )
            pygame.draw.rect(self.screen, self.color_fg, r)

        # Status bar
        pygame.draw.rect(
            self.screen,
            (0, 40, 0),
            (0, self.terminal_height, self.width, self.status_bar_height)
        )
        st = self.font.render(f"{self.current_state} {self.current_mood}", True, self.color_fg)
        self.screen.blit(st, (5, self.terminal_height + 5))

        # Output to display
        self._flip()

    def _flip(self, force: bool = False):
        """Send the rendered surface to the display. Rate-limited for performance."""
        now = time.time()
        # Rate limit framebuffer writes unless forced
        if not force and (now - self._last_flip) < self._min_flip_interval:
            return

        self._last_flip = now
        self._dirty = False

        if self.fb_writer:
            # Direct framebuffer write
            self.fb_writer.write(self.screen)
        elif hasattr(self, '_window'):
            # Desktop windowed mode
            self._window.blit(self.screen, (0, 0))
            pygame.display.flip()

    def process_draw_command(self, cmd_str: str):
        if self.mock_mode or not cmd_str.startswith("CMD:"):
            return
        try:
            parts = cmd_str.strip().split(':')[1].split(',')
            c = parts[0]
            args = [int(x) for x in parts[1:]]
            if c == "CLEAR":
                self.screen.fill(tuple(args[:3]))
            elif c == "PIXEL":
                self.screen.set_at((args[0], args[1]), tuple(args[2:]))
            elif c == "LINE":
                pygame.draw.line(self.screen, tuple(args[4:]), (args[0], args[1]), (args[2], args[3]))
            elif c == "RECT":
                pygame.draw.rect(self.screen, tuple(args[4:]), (args[0], args[1], args[2], args[3]), 1)
            elif c == "FILLRECT":
                pygame.draw.rect(self.screen, tuple(args[4:]), (args[0], args[1], args[2], args[3]))
            elif c == "CIRCLE":
                pygame.draw.circle(self.screen, tuple(args[3:]), (args[0], args[1]), args[2], 1)
            elif c == "FILLCIRCLE":
                pygame.draw.circle(self.screen, tuple(args[3:]), (args[0], args[1]), args[2])
            self._flip()
        except Exception as e:
            pass  # Silently ignore malformed commands

    def update_cursor_blink(self):
        if time.time() - self.cursor_blink_time > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_blink_time = time.time()
            self._dirty = True

    def _handle_events(self):
        if self.mock_mode:
            return
        # With dummy driver, only check events if we have a window
        if hasattr(self, '_window'):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
        else:
            # Dummy driver - just pump events to prevent queue buildup
            pygame.event.pump()

    def tick(self, fps: int = 30):
        self._handle_events()
        self.update_cursor_blink()
        # Flush any pending renders
        if self._dirty:
            self._render()
        if self.clock:
            self.clock.tick(fps)

    def shutdown(self):
        if PYGAME_AVAILABLE and not self.mock_mode:
            # Clear screen on exit
            if self.fb_writer:
                self.fb_writer.clear(0, 0, 0)
            pygame.quit()

    def check_ghosting_refresh(self):
        pass
