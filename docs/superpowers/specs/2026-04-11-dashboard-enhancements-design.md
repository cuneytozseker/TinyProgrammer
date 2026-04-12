# Dashboard Enhancements Design

## Overview

Enhance the TinyProgrammer web dashboard with historical tracking and richer visualization. The dashboard currently shows live state only — this adds an activity timeline, success/failure pulse chart, mood timeline, canvas gallery, and a program detail panel. All on the existing single-page dashboard, backed by a JSON history file.

## Features

### 1. Activity Timeline

A scrollable feed showing what the device has been doing, displayed below the status cards and charts. Each event shows a timestamp, colored indicator dot, and description.

Event types rendered:
- **Program results** — green dot for success, red for failure. Shows filename, program type, run time, and error summary if failed.
- **Mood shifts** — blue dot. Shows "Mood shifted: focused → proud".
- **BBS posts** — purple dot. Shows board name and post subject.
- **State transitions** are not shown individually (too noisy); only the significant events above.

The timeline shows the 20 most recent events by default with a "Show more" link that loads older events from `/api/history`.

### 2. Success/Failure Pulse Chart

A line graph on a dark background showing per-program outcomes over time. Each data point represents one completed program — positioned high for success, low for failure. The line has a green glow with a gradient fill underneath, giving it a heart-monitor/pulse aesthetic. A bright dot marks the latest result.

Rendered as an SVG using Chart.js (loaded from CDN). X-axis shows relative time, Y-axis shows outcome (top = success, bottom = failure). Shows the last 50 programs.

### 3. Mood Timeline

A horizontal strip of colored bars, one per mood shift. Each bar's height is fixed (purely decorative — all same height) and color maps to the mood:

| Mood | Color |
|------|-------|
| hopeful | #f39c12 |
| focused | #3498db |
| curious | #f39c12 |
| proud | #2ecc71 |
| frustrated | #e74c3c |
| tired | #95a5a6 |
| playful | #f39c12 |
| determined | #9b59b6 |

A color legend sits below the strip. Shows the last 50 mood shifts.

### 4. Canvas Gallery

A 5-column grid of canvas thumbnail images. Each thumbnail shows the captured canvas output with the program type label below it. Clicking a thumbnail opens the program detail panel.

A `canvas/` directory stores PNG files captured from successful programs that used the canvas API. The gallery endpoint lists these with metadata from the associated `canvas_capture` events in history.

Below the grid, a "View all N canvases" link loads the full gallery.

### 5. Program Detail Panel

An overlay/modal that appears when clicking any program in the timeline or gallery. Dark semi-transparent backdrop, centered white card. Shows:

- **Header**: filename, timestamp, success/fail badge
- **Meta row**: program type, run time, mood at time of writing, LLM model used
- **Thought process**: the LLM's reasoning before writing the code (yellow callout)
- **Generated code**: syntax-highlighted in a dark monospace block, scrollable
- **Run output**: stdout from program execution and canvas preview image if applicable

Data comes from the existing archive metadata and the program `.py` file, plus the `program_result` event in history for the run-time stats.

## Architecture

### History Logger (`web/history.py`)

A new module that provides `HistoryLogger`:

- `log(event_type, data)` — appends an event to `history.json`
- `get_recent(n)` — returns the last N events
- `get_stats()` — returns aggregated stats (success/fail counts, per-type breakdown, time-bucketed rates for charting)
- `get_moods(n)` — returns the last N mood events
- Thread-safe with a `threading.Lock` (brain writes, web reads)
- File rotation: caps at 500 events. When exceeded, trims oldest 50 in batch.

### Event Schema

Events stored in `history.json` as a JSON array:

```json
{
  "ts": "2026-04-11T14:33:45",
  "type": "program_result",
  "data": {
    "name": "bouncing_ball_047.py",
    "prog_type": "bouncing_ball",
    "success": true,
    "run_time": 12.3,
    "thought": "Let's try a bouncy ball with gravity...",
    "error": null
  }
}
```

Event types:
- `program_result` — after RUN/WATCH completes. Fields: name, prog_type, success, run_time, thought, error (error message or null)
- `mood_shift` — on mood change. Fields: from, to
- `bbs_post` — after posting. Fields: board, subject
- `canvas_capture` — when canvas output is saved. Fields: filename

### Canvas Capture

When a program finishes successfully and produced canvas drawing commands, the main process saves the rendered pygame surface as a PNG to `canvas/<program_name>.png`. This uses pygame's `save()` on the canvas surface. The history logger records a `canvas_capture` event linking to the filename.

### API Endpoints

All served by the existing Flask app in `web/app.py`:

| Endpoint | Returns | Used by |
|---|---|---|
| `GET /api/history?limit=50` | Recent events (all types) | Activity timeline |
| `GET /api/history/stats` | Aggregated success/fail data per program | Pulse chart |
| `GET /api/history/moods?limit=50` | Recent mood shift events | Mood timeline |
| `GET /api/canvas` | List of saved canvas images with metadata | Gallery grid |
| `GET /api/program/<name>` | Full program details (code, thought, output, metadata) | Detail modal |

The existing `/api/status` response is extended to include a `recent_history` field (last 10 events) so the dashboard can show initial timeline data on first load without a separate request.

### Data Flow

1. Brain runs its state machine as usual
2. At key moments (program result, mood shift, BBS post, canvas capture), brain calls `history.log()`
3. Dashboard polls `/api/status` every 5 seconds (existing behavior)
4. Response now includes `recent_history`, `stats`, and `moods`
5. Dashboard JS renders timeline, charts, and mood strip from this data
6. Gallery and program details load on demand via their own endpoints
7. Canvas images are served as static files from the `canvas/` directory

### Frontend Changes

The dashboard template (`web/templates/dashboard.html`) grows to include the new sections. A single JavaScript block handles:
- Polling `/api/status` and updating all sections
- Rendering the pulse chart via Chart.js line chart
- Building the timeline HTML from event data
- Loading gallery thumbnails on scroll/click
- Opening the program detail modal on click

Chart.js is loaded from CDN (`https://cdn.jsdelivr.net/npm/chart.js`). No other new frontend dependencies.

### Integration Points

Brain modifications (minimal):
- `brain.py`: call `history.log("program_result", ...)` after WATCH state completes
- `brain.py`: call `history.log("canvas_capture", ...)` after saving canvas output
- `personality.py`: call `history.log("mood_shift", ...)` when mood changes
- `bbs/client.py`: call `history.log("bbs_post", ...)` after successful post
- `main.py`: instantiate `HistoryLogger` and pass it to brain, personality, and BBS client

### Page Layout (top to bottom)

1. **Status cards + actions** — existing, unchanged
2. **Pulse chart + Mood timeline** — side by side, new
3. **Activity timeline** — scrollable event feed, new
4. **Canvas gallery** — 5-column thumbnail grid, new
5. **Programs by type** — existing, unchanged
6. **Program detail modal** — overlay, opened on click

### File Changes Summary

| File | Change |
|---|---|
| `web/history.py` | **New** — HistoryLogger class |
| `web/app.py` | Add 5 new API endpoints, inject history logger |
| `web/templates/dashboard.html` | Add new sections + JS for charts, timeline, gallery, modal |
| `web/static/style.css` | Styles for new sections (pulse chart, timeline, gallery, modal) |
| `brain.py` | Call `history.log()` at key moments |
| `personality.py` | Call `history.log("mood_shift", ...)` on mood change |
| `bbs/client.py` | Call `history.log("bbs_post", ...)` after posting |
| `main.py` | Instantiate HistoryLogger, pass to subsystems |
| `canvas/` | **New directory** — stores captured canvas PNGs |
| `config.py` | Add `HISTORY_MAX_EVENTS = 500`, `HISTORY_FILE = "history.json"` |
