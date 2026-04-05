"""
Starry Night Screensaver — After Dark inspired

Black sky with twinkling stars, city skyline silhouette with
lit/unlit windows. Displayed when the device is off duty.
"""

import math
import random
import time

import pygame


class StarryNight:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.start_time = time.time()

        self.skyline_points = self._generate_skyline()
        self.stars = self._generate_stars(200)
        self.windows = self._generate_windows()
        self.shooting_star = None
        self._last_shooting = time.time()

    def _generate_skyline(self):
        """Generate city skyline as polygon points along the bottom ~30%."""
        points = [(0, self.height)]  # bottom-left
        x = 0
        skyline_base = int(self.height * 0.7)

        while x < self.width:
            # Building width and height
            bw = random.randint(20, 60)
            bh = random.randint(30, int(self.height * 0.35))
            top = skyline_base + random.randint(-bh, 0)
            top = max(int(self.height * 0.35), top)

            # Left edge up
            points.append((x, top))
            # Right edge across
            points.append((x + bw, top))

            x += bw
            # Occasional gap
            if random.random() < 0.3:
                gap = random.randint(3, 12)
                points.append((x, skyline_base))
                x += gap
                points.append((x, skyline_base))

        points.append((self.width, skyline_base))
        points.append((self.width, self.height))  # bottom-right
        return points

    def _point_in_skyline(self, px, py):
        """Check if a point is below the skyline (inside buildings)."""
        # Walk the skyline points to find the building height at px
        for i in range(len(self.skyline_points) - 1):
            x1, y1 = self.skyline_points[i]
            x2, y2 = self.skyline_points[i + 1]
            if x1 <= px < x2:
                # Linear interpolation of height at px
                if x2 == x1:
                    edge_y = min(y1, y2)
                else:
                    t = (px - x1) / (x2 - x1)
                    edge_y = y1 + t * (y2 - y1)
                return py >= edge_y
        return py >= self.height * 0.7

    def _generate_stars(self, count=200):
        """Generate star positions above the skyline."""
        stars = []
        for _ in range(count):
            for _attempt in range(20):
                x = random.randint(0, self.width)
                # Bias toward top of screen
                y = random.randint(0, int(self.height * 0.75))
                if not self._point_in_skyline(x, y):
                    break
            else:
                continue

            stars.append({
                "x": x, "y": y,
                "base_brightness": random.uniform(0.3, 1.0),
                "twinkle_speed": random.uniform(0.5, 3.0),
                "phase": random.uniform(0, math.pi * 2),
                "size": 1 if random.random() < 0.85 else 2,
            })
        return stars

    def _generate_windows(self):
        """Generate window positions within skyline buildings."""
        windows = []
        # Walk skyline pairs to find building rects
        i = 1
        while i < len(self.skyline_points) - 2:
            x1, y1 = self.skyline_points[i]
            x2, y2 = self.skyline_points[i + 1]
            if y1 == y2 and y1 < self.height * 0.7:
                # This is a building top edge
                bx, by, bw = x1, y1, x2 - x1
                bh = self.height - by
                # Place windows in grid
                for wy in range(by + 6, by + bh - 10, 10):
                    for wx in range(bx + 4, bx + bw - 4, 8):
                        if random.random() < 0.6:
                            windows.append({
                                "x": wx, "y": wy, "w": 3, "h": 4,
                                "lit": random.random() < 0.3,
                                "toggle_chance": random.uniform(0.0001, 0.0008),
                            })
            i += 1
        return windows

    def update(self):
        """Update star twinkle and window toggle states."""
        now = time.time() - self.start_time

        # Update star brightness
        for s in self.stars:
            s["_brightness"] = s["base_brightness"] * (
                0.5 + 0.5 * math.sin(now * s["twinkle_speed"] + s["phase"])
            )

        # Toggle windows occasionally
        for w in self.windows:
            if random.random() < w["toggle_chance"]:
                w["lit"] = not w["lit"]

        # Shooting star (rare)
        if self.shooting_star is None:
            if time.time() - self._last_shooting > 120 and random.random() < 0.005:
                self.shooting_star = {
                    "x": random.randint(50, self.width - 100),
                    "y": random.randint(20, int(self.height * 0.4)),
                    "dx": random.uniform(8, 15) * random.choice([-1, 1]),
                    "dy": random.uniform(2, 6),
                    "life": 0, "max_life": random.randint(10, 20),
                }
        else:
            ss = self.shooting_star
            ss["x"] += ss["dx"]
            ss["y"] += ss["dy"]
            ss["life"] += 1
            if ss["life"] >= ss["max_life"]:
                self.shooting_star = None
                self._last_shooting = time.time()

    def render(self, surface):
        """Draw the screensaver onto the given pygame surface."""
        surface.fill((0, 0, 0))

        # Stars
        for s in self.stars:
            b = max(0, min(255, int(s.get("_brightness", s["base_brightness"]) * 255)))
            color = (b, b, b)
            if s["size"] == 1:
                surface.set_at((s["x"], s["y"]), color)
            else:
                pygame.draw.circle(surface, color, (s["x"], s["y"]), 1)

        # Shooting star
        if self.shooting_star:
            ss = self.shooting_star
            fade = 1.0 - (ss["life"] / ss["max_life"])
            b = int(255 * fade)
            for i in range(4):
                tx = int(ss["x"] - ss["dx"] * i * 0.3)
                ty = int(ss["y"] - ss["dy"] * i * 0.3)
                tb = max(0, b - i * 60)
                surface.set_at((tx, ty), (tb, tb, tb))

        # Skyline silhouette
        if len(self.skyline_points) > 2:
            pygame.draw.polygon(surface, (0, 0, 0), self.skyline_points)

        # Lit windows
        for w in self.windows:
            if w["lit"]:
                brightness = random.randint(200, 255)
                color = (brightness, int(brightness * 0.78), int(brightness * 0.31))
                pygame.draw.rect(surface, color,
                                 (w["x"], w["y"], w["w"], w["h"]))
