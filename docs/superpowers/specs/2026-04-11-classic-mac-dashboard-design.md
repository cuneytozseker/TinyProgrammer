# Classic Mac OS Dashboard Redesign

**Date:** 2026-04-11
**Scope:** Web dashboard (`web/`) — templates, static CSS/JS, and Flask routes

## Problem

The current dashboard header is a flat grid of 6 identical status cards with no visual hierarchy, no personality, and no connection to the device's retro Mac OS aesthetic. BBS and schedule info live in separate card grids that add clutter. The rest of the dashboard uses modern rounded cards that look like a generic admin panel.

## Design

Replace the entire dashboard with a classic Mac OS visual language that mirrors the on-device IDE display. Every section is rendered as a Mac window. Two themes: light (Classic Mac OS, default) and dark (terminal/phosphor CRT).

### Layout (top to bottom)

1. **Menu bar** — full-width strip at top of page. `◪ File Edit View` on left, system time on right. Light theme: white background, 2px black bottom border. Dark theme: dark background with phosphor-colored text.

2. **Hero window** ("TinyProgrammer") — the focal point:
   - **Left:** CSS pixel art avatar (8x8 grid of divs). Eyes blink on a 3-5s random timer. Mouth shape changes per mood. Border and pixel color reflect theme.
   - **Center:** Terminal-prompt state display (`tiny@pi:~$ run`), mood name (large, bold), and a mood-specific personality quote in italics (2-3 rotating quotes per mood).
   - **Right:** Small text showing schedule status (clocked in/out + system time), BBS device name, and current LLM model. Only shown if the feature is enabled.
   - **Bottom:** Status bar mirroring the device's format: `Who: {model} | STATUS: {state} | Mood: {mood} | running {program}.py`
   - **Error states:** FIX and ERROR get a pulsing glow on the avatar border and a blinking state label. Fix attempts shown inline (`attempt 1/2`).

3. **Statistics window** ("Statistics") — three columns with thin vertical dividers: Programs Written | Success Rate | Total Archived. Small uppercase labels, large number values.

4. **Action buttons** — Skip to Next, Wake Up/Screensaver, Refresh, Screenshot. Light theme: 3D beveled with outset/inset borders. Dark theme: flat with 1px border.

5. **Activity window** ("Activity") — existing pulse chart, mood timeline, activity log, and canvas gallery all inside one Mac window. Content is unchanged from current implementation; only the container chrome changes.

6. **Settings and Prompts pages** — same Mac window chrome applied to existing content.

### Light Theme (default)

- **Page background:** Desktop gray `#ddddbb`
- **Window bodies:** White `#ffffff`, status bars cream `#f0f0e8`
- **Window chrome:** Horizontally striped title bars (alternating white/`#cccccc`), 2px solid black borders
- **Window controls:** Circle buttons with 1.5px black borders (close with ×, minimize, zoom)
- **Typography:** Space Mono (loaded from Google Fonts). Black `#000` text, gray `#666` secondary
- **Buttons:** 3D beveled — `outset` borders, `#ddd` background, pressed state with `inset` borders
- **Avatar:** Black pixels on `#f0f0e8` background, 2px inset border

### Dark Theme (auto-matches device color scheme)

- **Page background:** `#1a1a1a`
- **Window bodies:** `#111`, title bars `#2a2a2a`
- **Window chrome:** Flat dark borders `#444`, circle controls with `#333` background
- **Phosphor colors** (matches device's active color scheme):
  - green: text `#33ff33`, dim `#228822`, glow `rgba(51,255,51,0.3)`
  - amber: text `#ffb000`, dim `#805800`, glow `rgba(255,176,0,0.3)`
  - blue: text `#508cff`, dim `#284688`, glow `rgba(80,140,255,0.3)`
  - night: text `#ff5050`, dim `#802828`, glow `rgba(255,80,80,0.3)`
- **CRT effects:** Scanline overlay (2px repeating transparent/dark stripes), edge vignette (radial gradient darkening edges)
- **Text glow:** `text-shadow` with phosphor color at low opacity on all primary text
- **Avatar:** Phosphor-colored pixels, 1px border in phosphor color, box-shadow glow
- **Buttons:** Flat `#2a2a2a` background, 1px `#444` border, phosphor-colored text with glow

### Theme Toggle

- Toggle control in the menu bar or nav bar
- Saves preference to `localStorage`, applied on page load before render (prevents flash)
- Dark theme phosphor color auto-matches the device's active color scheme from `config_overrides.json`. Changing the color scheme on the settings page updates both the device display and the dashboard dark theme.

### Pixel Art Avatar

Pure CSS — no images. 8x8 grid of `div` elements inside a container.

**Mood-to-expression mapping:**
- hopeful: smile + wide open eyes
- focused: neutral mouth + narrow determined eyes
- curious: slight smile + one raised eyebrow (asymmetric eyes)
- proud: smirk + half-lidded eyes
- frustrated: frown + angry angled brows (row above eyes)
- tired: flat mouth + half-height eyes (rows 2-3 only, not 3-4)
- playful: open smile + one eye wink (asymmetric)
- determined: clenched teeth (zigzag mouth) + intense eyes

**Blink animation:** Random interval 3-5 seconds. Eyes collapse to a single row for 150ms then restore. CSS animation triggered via JS `setTimeout` with `Math.random()` interval.

**Personality quotes** (2-3 per mood, rotate randomly):
- hopeful: "Something good is about to happen...", "I can feel it — this one's going to work."
- focused: "Concentrating...", "Every pixel matters."
- curious: "What happens if I change this...?", "I wonder what that API does."
- proud: "That was a good one.", "Not bad, if I say so myself."
- frustrated: "This error doesn't make any sense...", "Why won't you just work?!"
- tired: "Maybe just one more program...", "My fans are spinning pretty loud."
- playful: "Let me try something weird with the pixels...", "What could go wrong?"
- determined: "I'm going to fix this.", "Third time's the charm."

### API Changes

**`GET /api/status`** — add these fields:
- `model_short_name`: string from `brain.llm.get_short_name()` (e.g. "haiku-4.5")
- `color_scheme`: string from config (e.g. "green", "amber", "blue", "night")

Personality quotes are embedded in the dashboard JS as a static lookup object keyed by mood. No separate API endpoint needed — the JS picks a random quote for the current mood on each status poll.

### Removed

- 6-card flat status grid (replaced by hero window + statistics window)
- Separate BBS Status section (absorbed into hero window right side)
- Separate Schedule section (absorbed into hero window right side)
- Modern rounded card styling with box shadows
- Current nav bar (replaced by menu bar)

### Responsive

- Desktop: horizontal layout as described
- Mobile (<600px): windows stack full-width, hero window contents stack vertically (avatar centered above text), stats columns remain horizontal but smaller, menu bar wraps

### Files Modified

- `web/templates/dashboard.html` — full rewrite of top section, add Mac window wrappers to activity section
- `web/templates/base.html` — replace nav bar with menu bar, add theme toggle, load Space Mono font
- `web/templates/settings.html` — wrap content in Mac window chrome
- `web/templates/prompts.html` — wrap content in Mac window chrome (if exists)
- `web/static/style.css` — new theme system (CSS custom properties), Mac window chrome classes, pixel art avatar styles, CRT overlay styles, light/dark color variables
- `web/app.py` — add `model_short_name` and `color_scheme` to status response, add `/api/personality-quote` endpoint
