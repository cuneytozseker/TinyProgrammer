"""
Win98-Style Disk Defragmenter Simulation

Purely cosmetic idle animation that faithfully recreates the look and feel
of the classic Windows 98 Disk Defragmenter. Runs during idle/off-hours as
a rare easter egg alongside the StarryNight screensaver.
"""

import os
import random
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

import config


# Block types
EMPTY = 0
REGULAR = 1
SYSTEM = 2
MOVED = 3
SELECTED = 4
PARTIAL = 5

# Block colors (applied before color_adjustment, so they get tinted)
BLOCK_COLORS = {
    EMPTY:    (255, 255, 255),   # White
    REGULAR:  (0, 255, 255),     # Cyan
    SYSTEM:   (255, 255, 255),   # White fill (red corner drawn separately)
    MOVED:    None,              # Per-pixel checkerboard
    SELECTED: (0, 255, 0),       # Green
    PARTIAL:  (255, 0, 0),       # Red
}

# Win98 chrome colors
CHROME_BLUE_DARK = (0, 0, 128)
CHROME_BLUE_LIGHT = (0, 0, 192)
CHROME_GRAY = (192, 192, 192)
CHROME_GRAY_DARK = (128, 128, 128)
CHROME_GRAY_LIGHT = (255, 255, 255)
CHROME_BLACK = (0, 0, 0)
CHROME_GREEN = (0, 128, 0)
CHROME_RED = (255, 0, 0)


class _PRNG:
    """Simple LCG pseudo-random number generator for deterministic disk layouts."""

    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF
        self._a = 1664525
        self._c = 1013904223
        self._m = 2 ** 32

    def next_int(self, lo=None, hi=None):
        self.state = (self._a * self.state + self._c) % self._m
        val = self.state
        if lo is not None and hi is not None:
            return lo + (val % (hi - lo))
        return val

    def next_float(self):
        return self.next_int() / (2 ** 32)

    def next_bool(self, p=0.5):
        return self.next_float() < p


class _DiskState:
    """Manages the flat block array and its initialization."""

    def __init__(self, size, regular_pct, system_pct, seed):
        self.size = size
        self.blocks = [REGULAR] * size
        rng = _PRNG(seed)

        # Place system blocks in small clusters
        system_count = int(size * system_pct)
        placed = 0
        while placed < system_count:
            cluster_size = min(rng.next_int(1, 4), system_count - placed)
            pos = rng.next_int(0, size - cluster_size)
            for i in range(cluster_size):
                if pos + i < size:
                    self.blocks[pos + i] = SYSTEM
            placed += cluster_size

        # Place empty blocks with varied cluster sizes
        empty_count = size - int(size * regular_pct) - system_count
        placed = 0
        while placed < empty_count:
            # Probability distribution: 50% size-1, 15% size-2, 10% size-3, 5% size-4, 20% size-5+
            r = rng.next_float()
            if r < 0.50:
                cluster_size = 1
            elif r < 0.65:
                cluster_size = 2
            elif r < 0.75:
                cluster_size = 3
            elif r < 0.80:
                cluster_size = 4
            else:
                cluster_size = rng.next_int(5, 12)

            cluster_size = min(cluster_size, empty_count - placed)
            pos = rng.next_int(0, size - cluster_size)
            for i in range(cluster_size):
                if pos + i < size and self.blocks[pos + i] == REGULAR:
                    self.blocks[pos + i] = EMPTY
                    placed += 1

    def count_regular_ahead(self, offset):
        """Count REGULAR blocks from offset onwards."""
        count = 0
        for i in range(offset, self.size):
            if self.blocks[i] == REGULAR:
                count += 1
        return count

    def find_empty_gap(self, offset):
        """Find the size of the next EMPTY gap starting from offset."""
        size = 0
        i = offset
        while i < self.size and self.blocks[i] != EMPTY:
            i += 1
        while i < self.size and self.blocks[i] == EMPTY:
            size += 1
            i += 1
        return size

    def collect_regular_blocks(self, start, count, rng):
        """Scan forward from start, collecting up to count REGULAR blocks.
        Returns list of indices."""
        collected = []
        # Occasional large jump forward
        if rng.next_bool(0.3):
            jump = rng.next_int(5, 30)
            start = min(start + jump, self.size - 1)

        i = start
        while i < self.size and len(collected) < count:
            if self.blocks[i] == REGULAR:
                collected.append(i)
            i += 1
        return collected


# Algorithm states
_ST_NEXT_FILE = 0
_ST_NEXT_BLOCK = 1
_ST_MOVE = 2
_ST_FINISHED = 3


class _DefragAlgorithm:
    """State machine that drives the defrag animation."""

    def __init__(self, disk):
        self.disk = disk
        self.roffset = 0
        self.woffset = 0
        self.state = _ST_NEXT_FILE
        self.progress = 0.0
        self.total_regular = disk.count_regular_ahead(0)
        self.moved_count = 0

        self._next_file_len = 0
        self._collected_indices = []
        self._move_index = 0
        self._rng = _PRNG(random.randint(0, 100_000_000))

    def step(self):
        """Advance one step. Returns True if still running."""
        if self.state == _ST_FINISHED:
            return False

        if self.state == _ST_NEXT_FILE:
            return self._step_next_file()
        elif self.state == _ST_NEXT_BLOCK:
            return self._step_next_block()
        elif self.state == _ST_MOVE:
            return self._step_move()

        return True

    def _step_next_file(self):
        # Mark contiguous blocks at write head as MOVED until hitting EMPTY
        i = self.woffset
        while i < self.disk.size and self.disk.blocks[i] not in (EMPTY,):
            if self.disk.blocks[i] in (REGULAR, SELECTED, PARTIAL):
                self.disk.blocks[i] = MOVED
            i += 1

        # Count the empty gap
        gap_size = self.disk.find_empty_gap(self.woffset)
        if gap_size == 0:
            # No gap found, try to find one further ahead
            for j in range(self.woffset + 1, self.disk.size):
                if self.disk.blocks[j] == EMPTY:
                    gap_size = self.disk.find_empty_gap(j)
                    break

        max_per_step = self._rng.next_int(1, 6)
        self._next_file_len = min(gap_size, max_per_step) if gap_size > 0 else 0

        if self._next_file_len == 0 or self.disk.count_regular_ahead(self.roffset) == 0:
            self.state = _ST_FINISHED
            self.progress = 1.0
            return False

        self.state = _ST_NEXT_BLOCK
        return True

    def _step_next_block(self):
        # Collect blocks to move
        self._collected_indices = self.disk.collect_regular_blocks(
            self.roffset, self._next_file_len, self._rng
        )

        if not self._collected_indices:
            self.state = _ST_FINISHED
            self.progress = 1.0
            return False

        # Mark as SELECTED (green)
        for idx in self._collected_indices:
            self.disk.blocks[idx] = SELECTED

        # Check if partial move
        is_partial = len(self._collected_indices) < self._next_file_len

        if is_partial:
            # Mark destination slots as PARTIAL (red)
            for j in range(len(self._collected_indices)):
                if self.woffset + j < self.disk.size:
                    self.disk.blocks[self.woffset + j] = PARTIAL

        self._move_index = 0
        self.state = _ST_MOVE
        return True

    def _step_move(self):
        if self._move_index >= len(self._collected_indices):
            # All blocks moved, advance write head
            self.woffset += len(self._collected_indices)
            self.roffset = max(self.roffset, max(self._collected_indices) + 1) if self._collected_indices else self.roffset + 1
            self.moved_count += len(self._collected_indices)
            self.progress = self.moved_count / max(1, self.total_regular)
            self.state = _ST_NEXT_FILE
            return True

        src = self._collected_indices[self._move_index]
        dst = self.woffset + self._move_index

        if dst < self.disk.size:
            # Source -> EMPTY
            self.disk.blocks[src] = EMPTY
            # Destination -> MOVED
            self.disk.blocks[dst] = MOVED

        self._move_index += 1
        return True


class _DefragRenderer:
    """Draws the defrag visualization onto a pygame surface."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.view_offset = 0  # Scroll position in blocks

        # Block dimensions (scaled from 480x320 reference: 7px wide, 9px tall, 1px gap)
        self.block_w = max(3, int(7 * config._SX))
        self.block_h = max(4, int(9 * config._SY))
        self.gap = max(1, int(1 * config._SX))

        # Fixed fragmentation % for this run (not random each frame)
        self.frag_pct = random.randint(30, 70)

        # Pre-render the MOVED checkerboard block surface
        self._moved_surf = pygame.Surface((self.block_w, self.block_h))
        for py in range(self.block_h):
            for px in range(self.block_w):
                if (px + py) % 2 == 0:
                    self._moved_surf.set_at((px, py), (0, 0, 255))
                else:
                    self._moved_surf.set_at((px, py), (0, 255, 255))
        pygame.draw.rect(self._moved_surf, CHROME_BLACK,
                         (0, 0, self.block_w, self.block_h), 1)

        # Calculate grid area (inside the window chrome)
        self._compute_layout()

    def _compute_layout(self):
        """Compute the window chrome and grid layout."""
        sx, sy = config._SX, config._SY

        # Window chrome dimensions (scaled from 480x320)
        self.win_x = int(5 * sx)
        self.win_y = int(8 * sy)
        self.win_w = self.width - int(10 * sx)
        self.win_h = self.height - int(16 * sy)

        # Title bar height
        self.title_h = int(20 * sy)

        # Info bar below title
        self.info_h = int(16 * sy)

        # Legend row
        self.legend_h = int(14 * sy)

        # Progress bar area
        self.progress_h = int(20 * sy)

        # Status bar
        self.status_h = int(16 * sy)

        # Grid area: between info/legend and progress bar
        # Add padding: 6px below legend, 8px above progress label
        chrome_top = self.title_h + self.info_h + self.legend_h + int(6 * sy)
        chrome_bottom = self.progress_h + self.status_h + int(8 * sy)
        grid_border = int(4 * sy)

        self.grid_x = self.win_x + grid_border
        self.grid_y = self.win_y + chrome_top + grid_border
        self.grid_w = self.win_w - grid_border * 2
        self.grid_h = self.win_h - chrome_top - chrome_bottom - grid_border * 2

        # Calculate blocks per row and visible rows
        self.blocks_per_row = max(1, self.grid_w // (self.block_w + self.gap))
        self.visible_rows = max(1, self.grid_h // (self.block_h + self.gap))

    def update_scroll(self, write_offset):
        """Auto-scroll to keep the write head roughly centered."""
        head_row = write_offset // max(1, self.blocks_per_row)
        center_row = head_row - self.visible_rows // 3
        target_offset = max(0, center_row)

        # Smooth scroll — move toward target
        if target_offset > self.view_offset:
            self.view_offset += max(1, (target_offset - self.view_offset) // 3)
        elif target_offset < self.view_offset:
            self.view_offset = max(0, target_offset)

    def render(self, surface, disk, algorithm, elapsed_time):
        """Draw the complete defrag visualization."""
        surface.fill((0, 0, 0))
        self._draw_window_chrome(surface, disk, algorithm, elapsed_time)
        self._draw_grid(surface, disk, algorithm)
        self._draw_progress_bar(surface, algorithm)
        self._draw_status_bar(surface, algorithm, elapsed_time)

    def _draw_outset_rect(self, surface, rect, base_color):
        """Draw a Win98-style outset (raised) rectangle."""
        x, y, w, h = rect
        dark = tuple(max(0, c - 64) for c in base_color)
        light = tuple(min(255, c + 40) for c in base_color)
        pygame.draw.rect(surface, base_color, rect)
        # Top and left edges (light)
        pygame.draw.line(surface, light, (x, y), (x + w - 1, y))
        pygame.draw.line(surface, light, (x, y), (x, y + h - 1))
        # Bottom and right edges (dark)
        pygame.draw.line(surface, dark, (x, y + h - 1), (x + w - 1, y + h - 1))
        pygame.draw.line(surface, dark, (x + w - 1, y), (x + w - 1, y + h - 1))

    def _draw_window_chrome(self, surface, disk, algorithm, elapsed_time):
        """Draw the Win98 window frame, title bar, info bar, and legend."""
        sx, sy = config._SX, config._SY

        # Window background (gray)
        self._draw_outset_rect(
            surface,
            (self.win_x, self.win_y, self.win_w, self.win_h),
            CHROME_GRAY
        )

        # Title bar (blue gradient)
        title_rect = (self.win_x + 2, self.win_y + 2, self.win_w - 4, self.title_h)
        for row in range(self.title_h):
            t = row / max(1, self.title_h - 1)
            r = int(CHROME_BLUE_DARK[0] + t * (CHROME_BLUE_LIGHT[0] - CHROME_BLUE_DARK[0]))
            g = int(CHROME_BLUE_DARK[1] + t * (CHROME_BLUE_LIGHT[1] - CHROME_BLUE_DARK[1]))
            b = int(CHROME_BLUE_DARK[2] + t * (CHROME_BLUE_LIGHT[2] - CHROME_BLUE_DARK[2]))
            pygame.draw.line(surface, (r, g, b),
                             (self.win_x + 2, self.win_y + 2 + row),
                             (self.win_x + self.win_w - 3, self.win_y + 2 + row))

        # Title text
        font_size = max(8, int(10 * sy))
        try:
            font = pygame.font.Font(
                os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "assets", "SpaceMono-Regular.ttf"),
                font_size)
        except Exception:
            font = pygame.font.Font(None, font_size)

        title_surf = font.render("Disk Defragmenter - [C:]", True, (255, 255, 255))
        surface.blit(title_surf, (self.win_x + int(8 * sx), self.win_y + int(4 * sy)))

        # Info bar
        info_y = self.win_y + self.title_h + int(4 * sy)
        frag_pct = self.frag_pct if algorithm.state != _ST_FINISHED else random.randint(0, 5)
        info_text = f"Drive C: 847 MB {frag_pct}% fragmented"
        info_surf = font.render(info_text, True, CHROME_BLACK)
        surface.blit(info_surf, (self.win_x + int(8 * sx), info_y))

        # Legend row
        legend_y = info_y + int(16 * sy)
        legend_items = [
            ("Data", (0, 255, 255)),
            ("Optimized", (0, 0, 255)),
            ("Reading", (0, 255, 0)),
            ("Fragment", (255, 0, 0)),
            ("Empty", (255, 255, 255)),
        ]
        legend_x = self.win_x + int(6 * sx)
        box_size = max(4, int(6 * min(sx, sy)))
        for label, color in legend_items:
            lbl_surf = font.render(label, True, CHROME_BLACK)
            # Vertically center the icon with the text
            text_h = lbl_surf.get_height()
            icon_y = legend_y + (text_h - box_size) // 2
            text_y = legend_y
            pygame.draw.rect(surface, color, (legend_x, icon_y, box_size, box_size))
            pygame.draw.rect(surface, CHROME_BLACK, (legend_x, icon_y, box_size, box_size), 1)
            surface.blit(lbl_surf, (legend_x + box_size + int(2 * sx), text_y))
            legend_x += box_size + lbl_surf.get_width() + int(6 * sx)

    def _draw_grid(self, surface, disk, algorithm):
        """Draw the block grid with auto-scrolling."""
        self.update_scroll(algorithm.woffset)

        start_block = self.view_offset * self.blocks_per_row
        grid_bg_rect = (self.grid_x - 1, self.grid_y - 1,
                        self.grid_w + 2, self.grid_h + 2)
        pygame.draw.rect(surface, CHROME_BLACK, grid_bg_rect)

        for row in range(self.visible_rows):
            for col in range(self.blocks_per_row):
                idx = start_block + row * self.blocks_per_row + col
                if idx >= disk.size:
                    break

                block = disk.blocks[idx]
                bx = self.grid_x + col * (self.block_w + self.gap)
                by = self.grid_y + row * (self.block_h + self.gap)

                # Get block color
                if block == MOVED:
                    surface.blit(self._moved_surf, (bx, by))
                    continue

                color = BLOCK_COLORS.get(block, (255, 255, 255))
                if color is None:
                    color = (255, 255, 255)

                pygame.draw.rect(surface, color, (bx, by, self.block_w, self.block_h))
                pygame.draw.rect(surface, CHROME_BLACK,
                                 (bx, by, self.block_w, self.block_h), 1)

                # System blocks: red corner marker
                if block == SYSTEM:
                    corner_w = max(2, self.block_w // 3)
                    corner_h = max(2, self.block_h // 3)
                    pygame.draw.rect(surface, CHROME_RED,
                                     (bx + self.block_w - corner_w - 1,
                                      by + 1, corner_w, corner_h))

    def _draw_progress_bar(self, surface, algorithm):
        """Draw the progress bar with percentage."""
        sx, sy = config._SX, config._SY

        bar_x = self.win_x + int(8 * sx)
        bar_y = self.win_y + self.win_h - self.progress_h - self.status_h + int(4 * sy)
        bar_w = self.win_w - int(16 * sx)
        bar_h = max(8, int(12 * sy))

        font_size = max(7, int(9 * sy))
        try:
            font = pygame.font.Font(
                os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "assets", "SpaceMono-Regular.ttf"),
                font_size)
        except Exception:
            font = pygame.font.Font(None, font_size)

        pct = int(algorithm.progress * 100)
        label = f"Consolidating clusters... {pct}%"
        label_surf = font.render(label, True, CHROME_BLACK)
        surface.blit(label_surf, (bar_x, bar_y - int(12 * sy)))

        # Progress bar background
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, CHROME_BLACK, (bar_x, bar_y, bar_w, bar_h), 1)

        # Filled portion
        fill_w = int(bar_w * algorithm.progress)
        if fill_w > 0:
            pygame.draw.rect(surface, (0, 0, 128),
                             (bar_x, bar_y, fill_w, bar_h))

    def _draw_status_bar(self, surface, algorithm, elapsed_time):
        """Draw the status bar with elapsed time and cluster counts."""
        sx, sy = config._SX, config._SY

        bar_x = self.win_x + int(4 * sx)
        bar_y = self.win_y + self.win_h - self.status_h - int(2 * sy)
        bar_w = self.win_w - int(8 * sx)

        font_size = max(7, int(8 * sy))
        try:
            font = pygame.font.Font(
                os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "assets", "SpaceMono-Regular.ttf"),
                font_size)
        except Exception:
            font = pygame.font.Font(None, font_size)

        mins = int(elapsed_time) // 60
        secs = int(elapsed_time) % 60
        moved = algorithm.moved_count
        total = algorithm.total_regular

        status = f"Time: {mins:02d}:{secs:02d}  Clusters: {moved}/{total}"
        if algorithm.state == _ST_FINISHED:
            status += "  Complete."

        status_surf = font.render(status, True, CHROME_BLACK)
        surface.blit(status_surf, (bar_x + int(4 * sx), bar_y))


class DefragSimulation:
    """Win98-style disk defragmenter simulation.

    Follows the same interface as StarryNight:
        __init__(width, height)
        update()
        render(surface)
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.start_time = time.time()
        self._last_step_time = time.time()
        self._finished = False

        # Create a unique disk layout each run
        seed = random.randint(0, 100_000_000)
        disk_size = getattr(config, 'DEFRAG_DISK_SIZE', 4000)
        regular_pct = getattr(config, 'DEFRAG_REGULAR_PCT', 0.75)
        system_pct = getattr(config, 'DEFRAG_SYSTEM_PCT', 0.01)

        self.disk = _DiskState(disk_size, regular_pct, system_pct, seed)
        self.algorithm = _DefragAlgorithm(self.disk)
        self.renderer = _DefragRenderer(width, height)

    def update(self):
        """Advance the defrag by one step (with timing)."""
        if self._finished:
            return

        now = time.time()
        step_delay = getattr(config, 'DEFRAG_STEP_DELAY', 0.08)

        if now - self._last_step_time < step_delay:
            return

        # 10% chance of extra "disk seek" delay
        if random.random() < 0.10:
            self._last_step_time = now + random.uniform(0.05, 0.4)
            return

        self._last_step_time = now
        running = self.algorithm.step()
        if not running:
            self._finished = True

    def render(self, surface):
        """Draw current defrag state to the pygame surface."""
        elapsed = time.time() - self.start_time
        self.renderer.render(surface, self.disk, self.algorithm, elapsed)

    @property
    def finished(self):
        return self._finished
