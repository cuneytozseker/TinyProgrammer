# Procedural Chrome

TinyProgrammer defaults to the PNG-backed `asset` chrome. Procedural chrome
backends are opt-in through `DISPLAY_CHROME_BACKEND` and live under
`display/chrome/`.

Each backend implements the `ChromeBackend` protocol: it draws IDE, canvas
window, and BBS window chrome onto the existing pygame surface and exposes
`ChromeRegions` for content areas plus small text-placement hints. `Terminal`
starts with `default_chrome_regions()` for the PNG asset layout, and procedural
backends replace those regions. `Terminal` owns code text, status text, canvas
drawing, and BBS text rendering; chrome backends only reserve the space those
renderers use.

System 6 chrome keeps its pixel-perfect measurements as grouped module constants
and computes derived rectangles in `System6Layout`. Shared helpers are
intentionally small: `ScaleContext` maps a backend's reference coordinates to
the current display, and `ChromePainter` wraps low-level pygame lines, borders,
fills, and scaled fragments. Prefer style-owned constants over generic widget
abstractions. System 6 uses a 480x320 reference for the IDE and canvas chrome,
and an 800x480 reference for the BBS terminal window.

Set `DISPLAY_CHROME_BACKEND=system6` in `.env`, Docker, or choose
`System 6 (experimental)` from web Settings > Display > Interface Theme to try
the procedural chrome. Changing the backend requires restarting TinyProgrammer
because the display surface and regions are created with the `Terminal`.

To add another theme, create a backend module, register it in
`display/chrome/registry.py`, and implement the same drawing and region
contract. This is a protocol plus a factory, not a widget toolkit or superclass
hierarchy. Only generalize code after a second backend proves that the shared
shape is real.
