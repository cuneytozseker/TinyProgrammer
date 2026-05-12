# Procedural Chrome

TinyProgrammer defaults to the PNG-backed `asset` chrome. The System 6
procedural chrome is opt-in through `DISPLAY_CHROME_BACKEND=system6` and lives
under `display/chrome/`.

System6Chrome draws IDE, canvas window, and BBS window chrome onto the existing
pygame surface and exposes `ChromeRegions` for the content areas. `Terminal`
starts with `default_chrome_regions()` for the PNG asset layout, and System6
replaces those regions when selected. `Terminal` owns code text, status text,
canvas drawing, and BBS text rendering; chrome drawing only reserves the space
those renderers use.

System 6 chrome keeps its pixel-perfect measurements as grouped module constants
and computes derived rectangles in `System6Layout`. Shared helpers are
intentionally small: `ScaleContext` maps reference coordinates to the current
display, and `ChromePainter` wraps low-level pygame lines, borders, fills, and
scaled fragments. Prefer style-owned constants over generic widget abstractions.
System 6 uses a 480x320 reference for the IDE and canvas chrome,
and an 800x480 reference for the BBS terminal window.

Set `DISPLAY_CHROME_BACKEND=system6` in `.env`, Docker, or choose
`System 6 (experimental)` from web Settings > Display > Interface Theme to try
the procedural chrome. Changing the backend requires restarting TinyProgrammer
because the display surface and regions are created with the `Terminal`.

Keep this as one concrete renderer while the experiment is active. Only
generalize the chrome package after a second procedural style proves a shared
shape is real.
