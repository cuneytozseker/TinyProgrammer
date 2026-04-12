"""
Mac System 6 Disk Optimizer Simulation

Purely cosmetic idle animation that recreates a Mac System 6-style
disk optimizer. Runs during idle/off-hours as a rare easter egg
alongside the StarryNight screensaver.
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

# Block colors — 4-gray Mac palette
BLOCK_COLORS = {
    EMPTY:    (255, 255, 255),   # White
    REGULAR:  (170, 170, 170),   # Light gray — data blocks
    SYSTEM:   (85, 85, 85),      # Dark gray — system blocks
    MOVED:    (0, 0, 0),         # Black — optimized/moved blocks
    SELECTED: (0, 0, 0),         # Black with white highlight border
    PARTIAL:  (170, 170, 170),   # Light gray with dark gray crosshatch
}

# Mac System 6 chrome colors
_MAC_BLACK = (0, 0, 0)
_MAC_WHITE = (255, 255, 255)
_MAC_GRAY = (85, 85, 85)
_MAC_LIGHT_GRAY = (170, 170, 170)

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


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
        count = 0
        for i in range(offset, self.size):
            if self.blocks[i] == REGULAR:
                count += 1
        return count

    def find_empty_gap(self, offset):
        size = 0
        i = offset
        while i < self.size and self.blocks[i] != EMPTY:
            i += 1
        while i < self.size and self.blocks[i] == EMPTY:
            size += 1
            i += 1
        return size

    def collect_regular_blocks(self, start, count, rng):
        collected = []
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
        i = self.woffset
        while i < self.disk.size and self.disk.blocks[i] not in (EMPTY,):
            if self.disk.blocks[i] in (REGULAR, SELECTED, PARTIAL):
                self.disk.blocks[i] = MOVED
            i += 1

        gap_size = self.disk.find_empty_gap(self.woffset)
        if gap_size == 0:
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
        self._collected_indices = self.disk.collect_regular_blocks(
            self.roffset, self._next_file_len, self._rng
        )

        if not self._collected_indices:
            self.state = _ST_FINISHED
            self.progress = 1.0
            return False

        for idx in self._collected_indices:
            self.disk.blocks[idx] = SELECTED

        is_partial = len(self._collected_indices) < self._next_file_len

        if is_partial:
            for j in range(len(self._collected_indices)):
                if self.woffset + j < self.disk.size:
                    self.disk.blocks[self.woffset + j] = PARTIAL

        self._move_index = 0
        self.state = _ST_MOVE
        return True

    def _step_move(self):
        if self._move_index >= len(self._collected_indices):
            self.woffset += len(self._collected_indices)
            self.roffset = max(self.roffset, max(self._collected_indices) + 1) if self._collected_indices else self.roffset + 1
            self.moved_count += len(self._collected_indices)
            self.progress = self.moved_count / max(1, self.total_regular)
            self.state = _ST_NEXT_FILE
            return True

        src = self._collected_indices[self._move_index]
        dst = self.woffset + self._move_index

        if dst < self.disk.size:
            self.disk.blocks[src] = EMPTY
            self.disk.blocks[dst] = MOVED

        self._move_index += 1
        return True


class _DefragRenderer:
    """Draws the Mac System 6 disk optimizer popup over the IDE background."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.view_offset = 0

        # Block dimensions (scaled from 480x320 reference: 7px wide, 9px tall, 1px gap)
        self.block_w = max(3, int(7 * config._SX))
        self.block_h = max(4, int(9 * config._SY))
        self.gap = max(1, int(1 * config._SX))

        # Fixed fragmentation % for this run
        self.frag_pct = random.randint(30, 70)

        # Load IDE background image for compositing
        bg_path = os.path.join(_ASSETS_DIR, f"bg-{width}-{height}.png")
        if not os.path.exists(bg_path):
            bg_path = os.path.join(_ASSETS_DIR, "bg.png")
        if os.path.exists(bg_path):
            self.bg_image = pygame.image.load(bg_path)
            if self.bg_image.get_size() != (width, height):
                self.bg_image = pygame.transform.scale(self.bg_image, (width, height))
        else:
            self.bg_image = pygame.Surface((width, height))
            self.bg_image.fill(_MAC_WHITE)

        # Load font
        self._font_path = os.path.join(_ASSETS_DIR, "SpaceMono-Regular.ttf")

        # Compute popup layout
        self._compute_layout()

    def _get_font(self, size):
        try:
            return pygame.font.Font(self._font_path, max(7, int(size)))
        except Exception:
            return pygame.font.Font(None, max(7, int(size)))

    def _compute_layout(self):
        sx, sy = config._SX, config._SY

        # Popup window margins — IDE menu bar and status bar remain visible
        self.win_x = int(8 * sx)
        self.win_y = int(12 * sy)
        self.win_w = self.width - int(16 * sx)
        self.win_h = self.height - int(24 * sy)

        # Font sizes for layout measurement
        self._title_font = self._get_font(9 * sy)
        self._info_font = self._get_font(9 * sy)
        self._progress_font = self._get_font(8 * sy)
        self._status_font = self._get_font(8 * sy)

        # Measure actual text heights so sections don't overlap at small scales
        title_text_h = self._title_font.get_height()
        info_text_h = self._info_font.get_height()
        progress_text_h = self._progress_font.get_height()
        status_text_h = self._status_font.get_height()

        # Title bar: pad text height with 2*sy vertical padding
        self.title_h = title_text_h + int(4 * sy)

        # Info line: text height + 1px border + small pad
        self.info_h = info_text_h + int(2 * sy)

        # Progress bar height
        bar_h = max(6, int(8 * sy))
        # Progress section: label + gap + bar + padding
        self.progress_h = progress_text_h + bar_h + int(3 * sy)
        self._bar_h = bar_h

        # Status bar: separator + text + padding
        self.status_h = status_text_h + int(4 * sy)

        # Grid area fills remaining space between info line and progress
        chrome_top = self.title_h + self.info_h
        chrome_bottom = self.progress_h + self.status_h
        grid_border = int(3 * sy)

        self.grid_x = self.win_x + grid_border
        self.grid_y = self.win_y + chrome_top + grid_border
        self.grid_w = self.win_w - grid_border * 2
        self.grid_h = self.win_h - chrome_top - chrome_bottom - grid_border * 2

        # Blocks per row and visible rows
        self.blocks_per_row = max(1, self.grid_w // (self.block_w + self.gap))
        self.visible_rows = max(1, self.grid_h // (self.block_h + self.gap))

    def update_scroll(self, write_offset):
        head_row = write_offset // max(1, self.blocks_per_row)
        center_row = head_row - self.visible_rows // 3
        target_offset = max(0, center_row)

        if target_offset > self.view_offset:
            self.view_offset += max(1, (target_offset - self.view_offset) // 3)
        elif target_offset < self.view_offset:
            self.view_offset = max(0, target_offset)

    def render(self, surface, disk, algorithm, elapsed_time):
        # Composite: blit IDE background, then draw popup on top
        surface.blit(self.bg_image, (0, 0))
        self._draw_popup(surface, disk, algorithm, elapsed_time)

    def _draw_popup(self, surface, disk, algorithm, elapsed_time):
        sx, sy = config._SX, config._SY

        # Popup window: white fill with 1px black border
        pygame.draw.rect(surface, _MAC_WHITE,
                         (self.win_x, self.win_y, self.win_w, self.win_h))
        pygame.draw.rect(surface, _MAC_BLACK,
                         (self.win_x, self.win_y, self.win_w, self.win_h), 1)

        # Title bar: solid black with white text, close box top-right
        pygame.draw.rect(surface, _MAC_BLACK,
                         (self.win_x + 1, self.win_y + 1,
                          self.win_w - 2, self.title_h))
        title_surf = self._title_font.render("Disk Optimizer", True, _MAC_WHITE)
        box_size = int(8 * min(sx, sy))
        box_pad = int(3 * sx)
        title_x = self.win_x + box_size + box_pad * 2

        surface.blit(title_surf, (title_x,
                                  self.win_y + int(2 * sy)))

        # Close box: small white square in top-left of title bar (Mac style)
        box_x = self.win_x + box_pad
        box_y = self.win_y + (self.title_h - box_size) // 2
        pygame.draw.rect(surface, _MAC_WHITE, (box_x, box_y, box_size, box_size))
        pygame.draw.rect(surface, _MAC_WHITE, (box_x, box_y, box_size, box_size), 1)

        # Info line: drive info, separated by 1px black border
        info_y = self.win_y + self.title_h
        pygame.draw.line(surface, _MAC_BLACK,
                         (self.win_x, info_y), (self.win_x + self.win_w - 1, info_y))
        frag = self.frag_pct if algorithm.state != _ST_FINISHED else random.randint(0, 5)
        info_text = f"HD20 \u2014 847K \u2014 {frag}% fragmented"
        info_surf = self._info_font.render(info_text, True, _MAC_BLACK)
        surface.blit(info_surf, (self.win_x + int(6 * sx), info_y + int(1 * sy)))

        # Grid
        self._draw_grid(surface, disk)

        # Progress bar
        self._draw_progress_bar(surface, algorithm)

        # Status bar
        self._draw_status_bar(surface, algorithm, elapsed_time)

    def _draw_grid(self, surface, disk):
        # Grid border
        pygame.draw.rect(surface, _MAC_BLACK,
                         (self.grid_x - 1, self.grid_y - 1,
                          self.grid_w + 2, self.grid_h + 2), 1)

        start_block = self.view_offset * self.blocks_per_row

        for row in range(self.visible_rows):
            for col in range(self.blocks_per_row):
                idx = start_block + row * self.blocks_per_row + col
                if idx >= disk.size:
                    return

                block = disk.blocks[idx]
                bx = self.grid_x + col * (self.block_w + self.gap)
                by = self.grid_y + row * (self.block_h + self.gap)

                color = BLOCK_COLORS.get(block, _MAC_WHITE)
                pygame.draw.rect(surface, color, (bx, by, self.block_w, self.block_h))

                if block == SELECTED:
                    # Black fill with 1px white highlight border
                    pygame.draw.rect(surface, _MAC_WHITE,
                                     (bx, by, self.block_w, self.block_h), 1)
                elif block == PARTIAL:
                    # Light gray fill with dark gray crosshatch
                    step = max(2, self.block_w // 3)
                    for d in range(-self.block_h, self.block_w, step):
                        x0 = max(0, d)
                        y0 = max(0, -d)
                        x1 = min(self.block_w, d + self.block_h)
                        y1 = min(self.block_h, self.block_w - d)
                        pygame.draw.line(surface, _MAC_GRAY,
                                         (bx + x0, by + y0), (bx + x1, by + y1))
                    pygame.draw.rect(surface, _MAC_BLACK,
                                     (bx, by, self.block_w, self.block_h), 1)
                else:
                    pygame.draw.rect(surface, _MAC_BLACK,
                                     (bx, by, self.block_w, self.block_h), 1)

    def _draw_progress_bar(self, surface, algorithm):
        sx, sy = config._SX, config._SY

        bar_x = self.win_x + int(6 * sx)
        bar_y = self.win_y + self.win_h - self.progress_h - self.status_h
        bar_w = self.win_w - int(12 * sx)

        pct = int(algorithm.progress * 100)
        label = f"Optimizing\u2026 {pct}%"
        label_surf = self._progress_font.render(label, True, _MAC_BLACK)
        surface.blit(label_surf, (bar_x, bar_y))

        bar_top = bar_y + label_surf.get_height() + int(1 * sy)

        # White background, 1px black border
        pygame.draw.rect(surface, _MAC_WHITE, (bar_x, bar_top, bar_w, self._bar_h))
        pygame.draw.rect(surface, _MAC_BLACK, (bar_x, bar_top, bar_w, self._bar_h), 1)

        # Black fill
        fill_w = int(bar_w * algorithm.progress)
        if fill_w > 0:
            pygame.draw.rect(surface, _MAC_BLACK,
                             (bar_x, bar_top, fill_w, self._bar_h))

    def _draw_status_bar(self, surface, algorithm, elapsed_time):
        sx, sy = config._SX, config._SY
        # Separator line
        sep_y = self.win_y + self.win_h - self.status_h
        pygame.draw.line(surface, _MAC_BLACK,
                         (self.win_x, sep_y), (self.win_x + self.win_w - 1, sep_y))

        mins = int(elapsed_time) // 60
        secs = int(elapsed_time) % 60
        moved = algorithm.moved_count
        total = algorithm.total_regular

        status = f"{mins:02d}:{secs:02d}  {moved}/{total} clusters"
        if algorithm.state == _ST_FINISHED:
            status += "  Done."

        status_surf = self._status_font.render(status, True, _MAC_GRAY)
        surface.blit(status_surf, (self.win_x + int(4 * sx),
                                   sep_y + int(2 * sy)))


class DefragSimulation:
    """Mac System 6 disk optimizer simulation.

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

        seed = random.randint(0, 100_000_000)
        disk_size = getattr(config, 'DEFRAG_DISK_SIZE', 4000)
        regular_pct = getattr(config, 'DEFRAG_REGULAR_PCT', 0.75)
        system_pct = getattr(config, 'DEFRAG_SYSTEM_PCT', 0.01)

        self.disk = _DiskState(disk_size, regular_pct, system_pct, seed)
        self.algorithm = _DefragAlgorithm(self.disk)
        self.renderer = _DefragRenderer(width, height)

    def update(self):
        if self._finished:
            return

        now = time.time()
        step_delay = getattr(config, 'DEFRAG_STEP_DELAY', 0.08)

        if now - self._last_step_time < step_delay:
            return

        if random.random() < 0.10:
            self._last_step_time = now + random.uniform(0.05, 0.4)
            return

        self._last_step_time = now
        running = self.algorithm.step()
        if not running:
            self._finished = True

    def render(self, surface):
        elapsed = time.time() - self.start_time
        self.renderer.render(surface, self.disk, self.algorithm, elapsed)

    @property
    def finished(self):
        return self._finished
