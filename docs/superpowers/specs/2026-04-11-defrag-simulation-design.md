# Retro Defrag Simulation — Design Spec

## Overview

A Windows 98-style disk defragmenter simulation that runs during idle/off-hours on the TinyProgrammer display. It faithfully recreates the look and feel of the classic Win98 defrag tool — colored block grid, animated block movement, scrolling view, and progress indicators. Purely cosmetic; no effect on mood, learning, or state machine.

## Trigger & Duration

- Runs **only during idle hours**, alongside the existing StarryNight screensaver
- Each ~60 seconds of idle time, a **5% chance** triggers defrag mode
- Once triggered, runs for **120–300 seconds** (random), then returns to screensaver
- Low probability makes it a rare, surprising easter egg

## Visual Design

### Win98 Window Chrome

- Blue gradient title bar: "Disk Defragmenter - [C:]"
- Gray (#c0c0c0) window background with outset borders
- Info bar showing "Drive C: 847 MB X% fragmented"
- Legend row: Data (cyan), Optimized (blue), Reading (green), Fragment (red), Empty (white), System (white+red corner)
- Progress bar with "Consolidating clusters... X%" label
- Status bar with elapsed time and cluster counts

### Block Grid

- Blocks are **7px wide x 9px tall** (scaled by `_SX`/`_SY`)
- 1px gap between blocks
- Black border (1px) on each block
- Grid fills the display area, auto-scrolls to follow the write head

### Block Colors

| Type | Color | Hex | Visual Detail |
|---|---|---|---|
| EMPTY | White | `#ffffff` | Plain white fill |
| REGULAR | Cyan | `#00ffff` | Solid cyan — data block |
| SYSTEM | White + red corner | `#ffffff` + `#ff0000` | White fill, small red rectangle in top-right quarter — never moves |
| MOVED | Blue/cyan checkerboard | `#0000ff` / `#00ffff` | Per-pixel alternating (i+j)%2 pattern — already placed |
| SELECTED | Green | `#00ff00` | Block being picked up by read head |
| PARTIAL | Red | `#ff0000` | Partially moved file fragment |

### Color Adjustment Compatibility

The defrag simulation should render **before** `color_adjustment.py` is applied, same as the screensaver. This means the base colors above will be tinted by the active color scheme (amber, green, sepia, etc.), which adds to the retro feel.

## Animation Algorithm

The defrag is driven by a state machine operating on a flat array of block types. Each `update()` call advances one step.

### Disk Initialization

1. Generate a **random seed** each time (`random.randint(0, 100_000_000)`) — every defrag run produces a unique disk layout
2. Use a deterministic PRNG (LCG) seeded with that value for all placement decisions
3. Create array of `DISK_SIZE` blocks, all `REGULAR`
4. Place `SYSTEM` blocks (1% of total) in small random clusters of 1–3
5. Place `EMPTY` blocks (remaining ~24%) in varied cluster sizes using a probability distribution: 50% size-1, 15% size-2, 10% size-3, 5% size-4, 20% size-5+
6. Result: unique fragmented disk layout every run

### State Machine

Two pointers: `roffset` (read head) and `woffset` (write head), both start at 0.

**State: NEXT_FILE**
1. Starting from `woffset`, advance forward marking all non-empty blocks as `MOVED` until hitting `EMPTY`
2. Count the size of the empty gap ahead
3. Decide `nextFileLen` = min(gap_size, random(1, maxBlocksPerStep))
4. → NEXT_BLOCK

**State: NEXT_BLOCK**
1. Jump to a random position ahead of `roffset` (occasional large jumps)
2. Scan forward, collecting `nextBlockLen` `REGULAR` blocks
3. Mark collected blocks as `SELECTED` (green) if moving a complete file
4. If partial: mark source as `EMPTY`, mark destination slots as `PARTIAL` (red)
5. → MOVE

**State: MOVE**
1. For each collected block: source → `EMPTY`, destination at `woffset` → `MOVED`
2. Advance `woffset`
3. → NEXT_FILE

**State: FINISHED**
- No more `REGULAR` blocks ahead of the write head

### View Scrolling

The visible portion of the grid auto-scrolls to keep the write head roughly centered:
- When write head passes the lower half of the visible window, scroll down by a portion of the view
- When write head moves above the view (shouldn't happen, but safe), snap to its position

### Timing

- Base step delay: 80ms (12–13 steps/second)
- 10% chance per step of an extra random delay of 50–400ms (simulates disk seeking)

## Architecture

### New File: `display/defrag.py`

Class `DefragSimulation` follows the same interface as `StarryNight`:

```python
class DefragSimulation:
    def __init__(self, width, height):
        # Initialize disk array, renderer state, grid dimensions

    def update(self):
        # Advance defrag algorithm by one step

    def render(self, surface):
        # Draw current block state to pygame surface
```

Internal structure:
- `_PRNG` — simple LCG random number generator (seeded per-run for reproducibility within a session)
- `_DiskState` — holds block array, handles initialization and block placement using the PRNG
- `_DefragAlgorithm` — state machine with roffset/woffset, step logic (also uses its own PRNG seed)
- `_DefragRenderer` — draws blocks to surface, handles view scrolling
- All block dimension calculations use `_SX`/`_SY` scale factors from `config.py`

### Modified: `main.py`

In the idle loop (`while not is_work_time()`), add defrag trigger:

```python
# Current: screensaver loop
# Change: after each screensaver cycle, 5% chance to switch to defrag mode
# Defrag runs for random(120, 300) seconds, then returns to screensaver
```

No changes to the work-time loop, brain state machine, or personality system.

### Modified: `config.py`

New settings:

```python
DEFRAG_IDLE_CHANCE = 0.05       # 5% chance per idle tick
DEFRAG_DURATION_MIN = 120       # seconds
DEFRAG_DURATION_MAX = 300       # seconds
DEFRAG_DISK_SIZE = 4000         # number of blocks
DEFRAG_STEP_DELAY = 0.08        # seconds between steps
DEFRAG_REGULAR_PCT = 0.75       # % of blocks that are data
DEFRAG_SYSTEM_PCT = 0.01        # % of blocks that are system
```

## Files Changed

| File | Action | Summary |
|---|---|---|
| `display/defrag.py` | **Create** | DefragSimulation class with disk init, algorithm, and renderer |
| `main.py` | **Modify** | Add defrag trigger in idle loop alongside screensaver |
| `config.py` | **Modify** | Add defrag timing/probability settings |

## Out of Scope

- No web dashboard controls for defrag (not needed for a rare easter egg)
- No effect on personality, mood, or learning system
- No state machine changes (defrag is idle-loop only, not a brain state)
- No BBS posting about defrag
- No canvas API integration (defrag renders directly to the pygame surface)
