"""
Terminal Display for TFT Screen

Uses pygame to render to framebuffer, FBCP driver handles SPI transfer.
Two modes:
- TERMINAL: Shows code being written character by character
- RUN: Displays program output (can be graphical)
"""

import os
import time
from typing import Tuple, Optional, Callable

# Set SDL to use framebuffer (no X11 needed)
os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb1"  # FBCP creates fb1 for SPI display

import pygame

# Fallback for desktop development
PYGAME_AVAILABLE = True
try:
    pygame.init()
except:
    PYGAME_AVAILABLE = False
    print("[Terminal] pygame init failed, running in mock mode")


class Terminal:
    """
    TFT terminal emulator using pygame.
    
    Renders a retro terminal aesthetic with:
    - Monospace font
    - Green-on-black (or amber-on-black) colors
    - Blinking cursor
    - Status bar at bottom
    """
    
    def __init__(self, width: int, height: int, 
                 color_bg: Tuple[int, int, int],
                 color_fg: Tuple[int, int, int],
                 font_name: str, font_size: int,
                 status_bar_height: int = 32):
        """
        Initialize terminal.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            color_bg: Background color (R, G, B)
            color_fg: Foreground/text color (R, G, B)
            font_name: Name of monospace font
            font_size: Font size in points
            status_bar_height: Height of status bar in pixels
        """
        self.width = width
        self.height = height
        self.color_bg = color_bg
        self.color_fg = color_fg
        self.status_bar_height = status_bar_height
        
        # Terminal area (above status bar)
        self.terminal_height = height - status_bar_height
        
        # Initialize pygame display
        self.screen = None
        self.font = None
        self.mock_mode = False
        
        self._init_display(font_name, font_size)
        
        # Calculate character dimensions from font
        self.char_width, self.char_height = self._get_char_size()
        
        # Terminal dimensions in characters
        self.cols = width // self.char_width
        self.rows = self.terminal_height // self.char_height
        
        # Cursor position (in characters)
        self.cursor_x = 0
        self.cursor_y = 0
        self.cursor_visible = True
        self.cursor_blink_time = 0
        
        # Text buffer (list of strings, one per line)
        self.lines = [""] * self.rows
        
        # Current state and mood for status bar
        self.current_state = "booting"
        self.current_mood = ""
        
        # Clock for framerate
        self.clock = pygame.time.Clock() if PYGAME_AVAILABLE else None
        
        # Initial render
        self.clear()
    
    def _init_display(self, font_name: str, font_size: int):
        """Initialize pygame display and font."""
        if not PYGAME_AVAILABLE:
            self.mock_mode = True
            print(f"[Terminal] Mock mode: {self.width}x{self.height}")
            return
        
        try:
            # Try framebuffer mode first (for Pi)
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Tiny Programmer")
            pygame.mouse.set_visible(False)
        except Exception as e:
            print(f"[Terminal] Framebuffer failed ({e}), trying windowed mode")
            # Fall back to windowed mode (for desktop dev)
            os.environ.pop("SDL_VIDEODRIVER", None)
            os.environ.pop("SDL_FBDEV", None)
            pygame.quit()
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Tiny Programmer")
        
        # Load font
        try:
            self.font = pygame.font.SysFont(font_name, font_size)
        except:
            print(f"[Terminal] Font '{font_name}' not found, using default")
            self.font = pygame.font.Font(None, font_size)
    
    def _get_char_size(self) -> Tuple[int, int]:
        """Get character dimensions from font."""
        if self.mock_mode:
            return (9, 16)  # Reasonable defaults
        
        # Measure a character
        surface = self.font.render("M", True, self.color_fg)
        return surface.get_width(), surface.get_height()
    
    def clear(self):
        """Clear the terminal."""
        self.cursor_x = 0
        self.cursor_y = 0
        self.lines = [""] * self.rows
        self._render()
    
    def type_char(self, char: str):
        """
        Display a single character at cursor position.
        
        Handles:
        - Regular characters
        - Newline (\\n)
        - Backspace (\\b)
        - Tab (\\t) - converts to spaces
        
        Args:
            char: Single character to display
        """
        if char == '\n':
            self._newline()
        elif char == '\b':
            self._backspace()
        elif char == '\t':
            # Tab = 4 spaces
            for _ in range(4):
                self.type_char(' ')
        else:
            # Add character to current line
            if self.cursor_x < self.cols:
                line = self.lines[self.cursor_y]
                # Pad line if needed
                while len(line) < self.cursor_x:
                    line += ' '
                # Insert character
                self.lines[self.cursor_y] = line[:self.cursor_x] + char + line[self.cursor_x + 1:]
                self.cursor_x += 1
            
            # Wrap if at end of line
            if self.cursor_x >= self.cols:
                self._newline()
        
        self._render()
    
    def type_string(self, text: str, delay_func: Optional[Callable[[], float]] = None):
        """
        Display a string character by character.
        
        Args:
            text: String to display
            delay_func: Optional callable returning delay in seconds per char
        """
        for char in text:
            self.type_char(char)
            if delay_func:
                delay = delay_func()
                if delay > 0:
                    time.sleep(delay)
                    self._handle_events()  # Keep responsive during delays
    
    def _newline(self):
        """Move to next line, scroll if needed."""
        self.cursor_x = 0
        self.cursor_y += 1
        
        if self.cursor_y >= self.rows:
            self._scroll()
    
    def _backspace(self):
        """Delete character before cursor."""
        if self.cursor_x > 0:
            self.cursor_x -= 1
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x + 1:]
        elif self.cursor_y > 0:
            # Move to end of previous line
            self.cursor_y -= 1
            self.cursor_x = len(self.lines[self.cursor_y])
    
    def _scroll(self):
        """Scroll terminal up by one line."""
        self.lines = self.lines[1:] + [""]
        self.cursor_y = self.rows - 1
    
    def delete_line(self):
        """Delete current line and move cursor to start."""
        self.lines[self.cursor_y] = ""
        self.cursor_x = 0
        self._render()
    
    def set_status(self, state: str, mood: str = ""):
        """
        Update status bar.
        
        Args:
            state: Current state (e.g., "writing", "thinking")
            mood: Current mood (e.g., "hopeful", "frustrated")
        """
        self.current_state = state
        self.current_mood = mood
        self._render()
    
    def _render(self):
        """Render the full display."""
        if self.mock_mode:
            return
        
        # Clear screen
        self.screen.fill(self.color_bg)
        
        # Render text lines
        for row, line in enumerate(self.lines):
            if line:
                y = row * self.char_height
                text_surface = self.font.render(line, True, self.color_fg)
                self.screen.blit(text_surface, (0, y))
        
        # Render cursor
        if self.cursor_visible:
            cursor_x_px = self.cursor_x * self.char_width
            cursor_y_px = self.cursor_y * self.char_height
            cursor_rect = pygame.Rect(cursor_x_px, cursor_y_px, 
                                       self.char_width, self.char_height)
            pygame.draw.rect(self.screen, self.color_fg, cursor_rect)
            
            # Draw character under cursor in inverse color if exists
            line = self.lines[self.cursor_y]
            if self.cursor_x < len(line):
                char_surface = self.font.render(line[self.cursor_x], True, self.color_bg)
                self.screen.blit(char_surface, (cursor_x_px, cursor_y_px))
        
        # Render status bar
        self._render_status_bar()
        
        pygame.display.flip()
    
    def _render_status_bar(self):
        """Render the status bar at bottom of screen."""
        # Status bar background
        status_rect = pygame.Rect(0, self.terminal_height, 
                                   self.width, self.status_bar_height)
        status_bg = tuple(c // 4 for c in self.color_fg)  # Dimmed version of fg
        pygame.draw.rect(self.screen, status_bg, status_rect)
        
        # Separator line
        pygame.draw.line(self.screen, self.color_fg,
                        (0, self.terminal_height),
                        (self.width, self.terminal_height), 1)
        
        # Status text
        status_text = f"STATE: {self.current_state}"
        if self.current_mood:
            status_text += f" · MOOD: {self.current_mood}"
        
        text_surface = self.font.render(status_text, True, self.color_fg)
        text_y = self.terminal_height + (self.status_bar_height - self.char_height) // 2
        self.screen.blit(text_surface, (8, text_y))
    
    def update_cursor_blink(self):
        """Toggle cursor visibility for blink effect."""
        now = time.time()
        if now - self.cursor_blink_time > 0.5:  # Blink every 500ms
            self.cursor_visible = not self.cursor_visible
            self.cursor_blink_time = now
            self._render()
    
    def _handle_events(self):
        """Handle pygame events (keeps app responsive)."""
        if self.mock_mode:
            return
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise KeyboardInterrupt
    
    def tick(self, fps: int = 30):
        """
        Call once per frame to maintain framerate and handle events.
        
        Args:
            fps: Target frames per second
        """
        self._handle_events()
        self.update_cursor_blink()
        if self.clock:
            self.clock.tick(fps)
    
    def get_surface(self) -> Optional[pygame.Surface]:
        """
        Get the pygame surface for direct drawing (RUN mode).
        
        Returns:
            pygame.Surface or None in mock mode
        """
        return self.screen
    
    def show_program_output(self, surface: pygame.Surface):
        """
        Display a program's graphical output.
        
        Args:
            surface: pygame.Surface with program output
        """
        if self.mock_mode:
            return
        
        # Scale surface to fit terminal area (above status bar)
        scaled = pygame.transform.scale(surface, (self.width, self.terminal_height))
        self.screen.blit(scaled, (0, 0))
        self._render_status_bar()
        pygame.display.flip()
    
    def shutdown(self):
        """Clean up pygame."""
        if PYGAME_AVAILABLE and not self.mock_mode:
            pygame.quit()
