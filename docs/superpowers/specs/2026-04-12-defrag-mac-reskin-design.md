# Mac System 6 Disk Optimizer Reskin

Reskin the Win98-style disk defragmenter simulation (`display/defrag.py`) to match the TinyProgrammer IDE's Mac System 6 aesthetic. The algorithm and state machine remain unchanged — this is a pure visual redesign.

## Visual Identity

Replace all Win98 chrome with Mac System 6 styling:

- **Window frame**: White `#fff` background, 1px solid black border — no outset/inset 3D effects
- **Title bar**: Solid black `#000` background, white text "Disk Optimizer", small white square close box in top-right
- **Info line**: "HD20 — 847K — 67% fragmented" in black text below title bar, separated by 1px black border-bottom
- **No legend row** — removed to save space; the 4 gray levels are self-evident
- **Progress bar**: White background, 1px black border, black fill — no color, no gradients
- **Status bar**: Elapsed time and cluster count in gray `#555` text, separated by 1px black border-top
- **Font**: Space Mono, sized per display profile via `config._SX`/`config._SY`

### Block Colors (4-Gray Mac Palette)

| Block type  | Color       | Hex       | Notes                              |
|-------------|-------------|-----------|------------------------------------|
| REGULAR     | Light gray  | `#aaaaaa` | Data blocks                        |
| MOVED       | Black       | `#000000` | Optimized/moved blocks (solid)     |
| SYSTEM      | Dark gray   | `#555555` | System blocks                      |
| EMPTY       | White       | `#ffffff` | Empty gaps                         |
| SELECTED    | Black with 1px white highlight border | Reading/head block |
| PARTIAL     | Light gray with dark gray crosshatch   | Fragment marker   |

## Rendering Architecture

**Composited popup over IDE background** — same pattern as `canvas.png`:

1. `render()` blits `bg_image` first (IDE background with menu bar, toolbar, sidebar)
2. Draws the popup window on top with absolute positioning
3. IDE remains visible behind/around the popup — maintaining visual cohesion
4. No black full-screen background fill (unlike the Win98 version)

### Removals from Win98 Version

- All `CHROME_BLUE_*`, `CHROME_GRAY_*` constants
- `_draw_outset_rect()` method
- Blue gradient title bar rendering loop
- Legend row with color icons
- Win98-style checkerboard MOVED surface — replaced with solid black

## Algorithm and State Machine (Unchanged)

The following are not modified:

- `_PRNG` — deterministic LCG pseudo-random number generator
- `_DiskState` — flat block array initialization and gap/block queries
- `_DefragAlgorithm` — state machine (`NEXT_FILE → NEXT_BLOCK → MOVE → NEXT_FILE → FINISHED`)
- Block type constants: `EMPTY=0, REGULAR=1, SYSTEM=2, MOVED=3, SELECTED=4, PARTIAL=5`
- Timing, seek delays, auto-scroll behavior
- `DefragSimulation` public interface (`__init__`, `update`, `render`, `finished`)

## Layout and Scaling

All dimensions computed from 480x320 reference via `config._SX`/`config._SY`:

| Element          | Reference height | Scaled            |
|------------------|-----------------|-------------------|
| Title bar        | `14 * _SY`      | Includes close box|
| Info line        | `10 * _SY`      | Drive info text   |
| Grid area        | Remaining space | Auto-calculated   |
| Progress section | `16 * _SY`      | Label + bar       |
| Status bar       | `10 * _SY`      | Time + clusters   |

Popup window positioned with small margins so the IDE menu bar and status bar remain visible around the edges.

Block size scaled from 7x9px reference (same as Win98 version).

## Config Changes

No changes to `config.py`. All `DEFRAG_*` values remain as-is. The reskin is purely visual.

## Files Changed

| File              | Change                                                                            |
|-------------------|-----------------------------------------------------------------------------------|
| `display/defrag.py` | Rewrite `_DefragRenderer`, update `BLOCK_COLORS`, remove Win98 constants, add composited popup rendering |
| `config.py`       | No changes                                                                        |
| `main.py`         | No changes                                                                        |

## Code Size Impact

The Win98 `_DefragRenderer` is ~250 lines. The Mac System 6 renderer targets ~120-150 lines because:

- No gradient title bar loop
- No outset border helper method
- No legend row rendering
- No checkerboard MOVED surface pre-rendering
- Simpler color map (4 solid grays)

This addresses the project owner's second concern about the original PR's code size.
