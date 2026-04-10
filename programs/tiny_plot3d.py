"""
Tiny Plot3D — 3D wireframe surface plotter for tiny_canvas.

Handles projection, rotation, axes, and wireframe rendering so the
LLM only has to provide the surface function f(x, y) -> z.

Usage:
    from tiny_canvas import Canvas
    from tiny_plot3d import Plot3D
    import math

    c = Canvas()
    p = Plot3D(c)
    p.set_range(x=(-5, 5), y=(-5, 5))
    p.set_style("mono_dark")
    p.run(lambda x, y: math.sin(math.sqrt(x*x + y*y)))
"""

import math


class Plot3D:

    STYLES = {
        "mono_light": {"bg": (255, 255, 255), "fg": (0, 0, 0), "axis": (0, 0, 0)},
        "mono_dark":  {"bg": (0, 0, 0), "fg": (51, 255, 51), "axis": (80, 80, 80)},
        "height":     {"bg": (0, 0, 0), "fg": None, "axis": (80, 120, 80)},
    }

    def __init__(self, canvas):
        self.c = canvas
        self.x_range = (-5.0, 5.0)
        self.y_range = (-5.0, 5.0)
        self.steps = 15
        self.style = "height"
        self.line_color = None  # override for fg; None uses style default
        self.rotation_speed = 1.5  # degrees per frame
        self.angle = 45.0
        self.elevation = 15.0  # 0=side, 90=top-down
        self.center_x = canvas.width / 2
        self.center_y = canvas.height / 2
        # Scale is recalculated each frame based on actual ranges
        self.scale = min(canvas.width, canvas.height) * 0.3
        self.z_scale = 1.0  # auto-calculated each frame from actual z range

    # =========================================================================
    # Configuration
    # =========================================================================

    def set_range(self, x=(-5, 5), y=(-5, 5)):
        self.x_range = (float(x[0]), float(x[1]))
        self.y_range = (float(y[0]), float(y[1]))

    def set_style(self, style):
        if style in self.STYLES:
            self.style = style

    def set_grid(self, steps=20):
        self.steps = max(4, min(40, int(steps)))

    def set_rotation_speed(self, degrees_per_frame=1.5):
        self.rotation_speed = float(degrees_per_frame)

    def set_elevation(self, degrees=30):
        self.elevation = float(degrees)

    def set_color(self, r, g, b):
        """Override the wireframe line color."""
        self.line_color = (int(r), int(g), int(b))

    # =========================================================================
    # Projection
    # =========================================================================

    def project(self, x, y, z):
        """3D -> 2D perspective projection with rotation around Z axis."""
        # Scale z to match xy visual range
        zs = z * self.z_scale

        # Rotate around Z (only x, y rotate — z stays vertical)
        a = math.radians(self.angle)
        cos_a = math.cos(a)
        sin_a = math.sin(a)
        rx = x * cos_a - y * sin_a
        ry = x * sin_a + y * cos_a
        rz = zs

        # Tilt: at elevation=0 we see the side (z is vertical),
        # at elevation=90 we look straight down (y is vertical, z is depth).
        e = math.radians(self.elevation)
        cos_e = math.cos(e)
        sin_e = math.sin(e)
        ty = ry * sin_e + rz * cos_e
        tz = ry * cos_e - rz * sin_e

        # Near-orthographic projection (large camera distance = subtle depth cue)
        camera_dist = 50.0
        persp = camera_dist / (camera_dist + tz + 0.001)

        sx = self.center_x + rx * self.scale * persp
        sy = self.center_y - ty * self.scale * persp
        return (sx, sy)

    def _auto_scale(self, z_min, z_max):
        """Auto-calculate xy scale and z_scale so everything fits on canvas.

        xy scale: make the xy box fit within ~75% of canvas (min dimension)
        z scale: scale z values so their visual range is ~60% of xy span
        """
        xy_span = max(
            self.x_range[1] - self.x_range[0],
            self.y_range[1] - self.y_range[0],
        )
        if xy_span < 0.001:
            return

        # Target visual z span = 45% of xy span. In the new projection,
        # z contributes via cos(elevation), and y (rotated) via sin(elevation).
        z_span = z_max - z_min
        sin_e = math.sin(math.radians(self.elevation))
        cos_e = math.cos(math.radians(self.elevation))
        abs_cos_e = max(abs(cos_e), 0.01)
        abs_sin_e = abs(sin_e)
        if z_span < 0.001:
            self.z_scale = 1.0
            z_span_scaled = 0
        else:
            # z_scale such that z_span * z_scale * |cos_e| = xy_span * 0.45
            self.z_scale = (xy_span * 0.45) / (z_span * abs_cos_e)
            z_span_scaled = z_span * self.z_scale

        # Worst case extent is at angle=45 (xy rotates to diagonal sqrt(2)*span)
        total_horiz = xy_span * 1.414
        # Vertical: xy diag projects via sin(e), z via cos(e)
        total_vert = xy_span * 1.414 * abs_sin_e + z_span_scaled * abs_cos_e

        scale_horiz = (self.c.width * 0.92) / total_horiz
        scale_vert = (self.c.height * 0.88) / total_vert
        self.scale = min(scale_horiz, scale_vert)

        # Recenter by projecting the box at the CURRENT angle and shifting
        # center_x/center_y so the box midpoint is always at canvas center.
        self.center_x = self.c.width / 2
        self.center_y = self.c.height / 2
        x0, x1 = self.x_range
        y0, y1 = self.y_range
        xs_vals = []
        ys_vals = []
        for x in (x0, x1):
            for y in (y0, y1):
                for z in (z_min, z_max):
                    sx, sy = self.project(x, y, z)
                    xs_vals.append(sx)
                    ys_vals.append(sy)
        box_mid_x = (min(xs_vals) + max(xs_vals)) / 2
        box_mid_y = (min(ys_vals) + max(ys_vals)) / 2
        self.center_x += (self.c.width / 2 - box_mid_x)
        self.center_y += (self.c.height / 2 - box_mid_y)

    # =========================================================================
    # Drawing
    # =========================================================================

    def _draw_bbox(self, z_min, z_max):
        """Draw a 3D bounding box around the data region."""
        colors = self.STYLES[self.style]
        c_box = colors["axis"]
        x0, x1 = self.x_range
        y0, y1 = self.y_range
        z0 = z_min
        z1 = z_max

        # 8 corners of the box
        corners = {}
        for name, (x, y, z) in {
            "000": (x0, y0, z0), "100": (x1, y0, z0),
            "010": (x0, y1, z0), "110": (x1, y1, z0),
            "001": (x0, y0, z1), "101": (x1, y0, z1),
            "011": (x0, y1, z1), "111": (x1, y1, z1),
        }.items():
            corners[name] = self.project(x, y, z)

        # 12 edges
        edges = [
            # Bottom face
            ("000", "100"), ("100", "110"), ("110", "010"), ("010", "000"),
            # Top face
            ("001", "101"), ("101", "111"), ("111", "011"), ("011", "001"),
            # Vertical edges
            ("000", "001"), ("100", "101"), ("110", "111"), ("010", "011"),
        ]
        for a, b in edges:
            p1 = corners[a]
            p2 = corners[b]
            self.c.line(p1[0], p1[1], p2[0], p2[1], *c_box)

    def _draw_axes(self, z_min, z_max):
        """Draw X, Y, Z axes through origin with tick marks."""
        colors = self.STYLES[self.style]
        axis_color = colors["axis"]

        # Axis extents — match the data range
        ax_range = self.x_range
        ay_range = self.y_range
        az_range = (z_min, z_max)

        # X axis
        p1 = self.project(ax_range[0], 0, 0)
        p2 = self.project(ax_range[1], 0, 0)
        self.c.line(p1[0], p1[1], p2[0], p2[1], *axis_color)

        # Y axis
        p1 = self.project(0, ay_range[0], 0)
        p2 = self.project(0, ay_range[1], 0)
        self.c.line(p1[0], p1[1], p2[0], p2[1], *axis_color)

        # Z axis
        p1 = self.project(0, 0, az_range[0])
        p2 = self.project(0, 0, az_range[1])
        self.c.line(p1[0], p1[1], p2[0], p2[1], *axis_color)

        # Tick marks
        tick_size = 0.15
        x_step = max(1, int((ax_range[1] - ax_range[0]) / 10))
        for x in range(int(ax_range[0]), int(ax_range[1]) + 1, x_step):
            if x == 0:
                continue
            p1 = self.project(x, -tick_size, 0)
            p2 = self.project(x, tick_size, 0)
            self.c.line(p1[0], p1[1], p2[0], p2[1], *axis_color)

        y_step = max(1, int((ay_range[1] - ay_range[0]) / 10))
        for y in range(int(ay_range[0]), int(ay_range[1]) + 1, y_step):
            if y == 0:
                continue
            p1 = self.project(-tick_size, y, 0)
            p2 = self.project(tick_size, y, 0)
            self.c.line(p1[0], p1[1], p2[0], p2[1], *axis_color)

        # Z ticks
        z_span = az_range[1] - az_range[0]
        z_step = z_span / 4 if z_span > 0 else 0.5
        z = az_range[0]
        while z <= az_range[1] + 0.001:
            if abs(z) > 0.001:
                p1 = self.project(-tick_size, 0, z)
                p2 = self.project(tick_size, 0, z)
                self.c.line(p1[0], p1[1], p2[0], p2[1], *axis_color)
            z += z_step

    def _height_color(self, z, z_min, z_max):
        """Map z to a green hue gradient (dark green -> bright green -> cyan-green)."""
        if z_max - z_min < 0.001:
            t = 0.5
        else:
            t = (z - z_min) / (z_max - z_min)
        t = max(0.0, min(1.0, t))
        # Low z: dark muted green (30, 100, 40)
        # Mid z: bright phosphor green (51, 255, 51)
        # High z: cyan-tinted green (120, 255, 180)
        if t < 0.5:
            k = t / 0.5
            r = int(30 + k * 21)
            g = int(100 + k * 155)
            b = int(40 + k * 11)
        else:
            k = (t - 0.5) / 0.5
            r = int(51 + k * 69)
            g = 255
            b = int(51 + k * 129)
        return (r, g, b)

    def _compute_surface(self, func):
        """Evaluate func(x, y) over the grid. Returns (z_values, z_min, z_max)."""
        x0, x1 = self.x_range
        y0, y1 = self.y_range
        n = self.steps
        dx = (x1 - x0) / n
        dy = (y1 - y0) / n

        z_values = [[0.0] * (n + 1) for _ in range(n + 1)]
        z_min = float("inf")
        z_max = float("-inf")
        for i in range(n + 1):
            for j in range(n + 1):
                x = x0 + i * dx
                y = y0 + j * dy
                try:
                    z = float(func(x, y))
                    if math.isnan(z) or math.isinf(z):
                        z = 0.0
                except Exception:
                    z = 0.0
                z_values[i][j] = z
                if z < z_min:
                    z_min = z
                if z > z_max:
                    z_max = z
        if z_min == float("inf"):
            z_min, z_max = -1.0, 1.0
        return z_values, z_min, z_max

    def _draw_surface(self, z_values, z_min, z_max):
        """Draw the wireframe mesh."""
        colors = self.STYLES[self.style]
        fg = self.line_color if self.line_color else colors["fg"]
        x0, x1 = self.x_range
        y0, y1 = self.y_range
        n = self.steps
        dx = (x1 - x0) / n
        dy = (y1 - y0) / n

        # Project all points once
        projected = [[None] * (n + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            for j in range(n + 1):
                x = x0 + i * dx
                y = y0 + j * dy
                projected[i][j] = self.project(x, y, z_values[i][j])

        # Draw rows (lines along x for fixed j)
        for j in range(n + 1):
            for i in range(n):
                p1 = projected[i][j]
                p2 = projected[i + 1][j]
                if self.style == "height":
                    avg_z = (z_values[i][j] + z_values[i + 1][j]) / 2
                    color = self._height_color(avg_z, z_min, z_max)
                else:
                    color = fg
                self.c.line(p1[0], p1[1], p2[0], p2[1], *color)

        # Draw columns (lines along y for fixed i)
        for i in range(n + 1):
            for j in range(n):
                p1 = projected[i][j]
                p2 = projected[i][j + 1]
                if self.style == "height":
                    avg_z = (z_values[i][j] + z_values[i][j + 1]) / 2
                    color = self._height_color(avg_z, z_min, z_max)
                else:
                    color = fg
                self.c.line(p1[0], p1[1], p2[0], p2[1], *color)

    # =========================================================================
    # Main loop
    # =========================================================================

    def run(self, func):
        """Animation loop — clears, computes, draws, rotates, sleeps."""
        colors = self.STYLES[self.style]
        while True:
            self.c.clear(*colors["bg"])
            z_values, z_min, z_max = self._compute_surface(func)
            # Pad z range slightly so the surface doesn't touch the bbox
            z_pad = max(abs(z_min), abs(z_max), 0.5) * 0.1
            z_min_p = z_min - z_pad
            z_max_p = z_max + z_pad
            self._auto_scale(z_min_p, z_max_p)

            self._draw_bbox(z_min_p, z_max_p)
            self._draw_axes(z_min_p, z_max_p)
            self._draw_surface(z_values, z_min, z_max)

            self.angle += self.rotation_speed
            if self.angle >= 360:
                self.angle -= 360

            self.c.sleep(0.033)
