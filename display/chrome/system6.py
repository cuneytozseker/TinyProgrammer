"""System 6-style procedural chrome backend."""

from __future__ import annotations

import os
from collections.abc import Mapping
from types import MappingProxyType

import pygame
import numpy as np

from display.layout import (
    CANVAS_REFERENCE,
    REFERENCE_LAYOUT_OFFSET_X,
    REFERENCE_LAYOUT_OFFSET_Y,
    scale_floor,
    scale_round_half_up,
)

from .base import DEFAULT_ASSETS_DIR, ChromeRegions
from .primitives import ChromePainter, ScaleContext


ReferenceRect = tuple[int, int, int, int]
Color = tuple[int, int, int]

BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)
CHECKER_DARK: Color = (150, 150, 150)

REFERENCE_RECTS: Mapping[str, ReferenceRect] = MappingProxyType({
    "menu_bar": (0, 0, 480, 22),
    "main_window": (4, 26, 465, 281),
    "apple_icon": (20, 2, 13, 15),
    "status": (4, 289, 465, 18),
})

SYSTEM6_TOOLBAR_ICON_FILES: tuple[str, ...] = (
    "icon-new-system6.png",
    "icon-open-system6.png",
    "icon-save-system6.png",
    "icon-settings-system6.png",
    "icon-run-system6.png",
)
SYSTEM6_LOGO_FILE = "logo-system6.png"
SYSTEM6_TOOLBAR_ICON_EXTENTS = (8, 12, 16, 24, 32, 40, 48, 56, 64)
SYSTEM6_LOGO_ICON_EXTENTS = (8, 12, 15, 16, 23, 24, 32, 40, 48, 56, 64)

# IDE toolbar and desktop
TOOLBAR_HEIGHT = 34
TOOLBAR_BUTTON_SIZE = 25
TOOLBAR_BUTTON_GAP = 2
TOOLBAR_BUTTON_RADIUS = 2
TOOLBAR_BUTTON_RADIUS_LIMIT_DIVISOR = 4
TOOLBAR_ICON_PAD = 4
DESKTOP_CORNER_RADIUS = 5
DESKTOP_CORNER_MIN_RADIUS = 3

# IDE content wells
SIDEBAR_FRAME_WIDTH = 96
SIDEBAR_CONTENT_X_PAD = 3
CONTENT_Y_PAD = 4
EDITOR_X = 132
GUTTER_X = 104
GUTTER_W = 24
LINE_NUMBER_RIGHT_PAD = 2
CODE_X_PAD = 6
SCROLLBAR_BUTTON = 16
SCROLLBAR_THICKNESS_SCALE = 0.8
STATUS_TEXT_X_PAD = 18

# Window titlebars and menu bar
TITLEBAR_HEIGHT = 17
TITLE_STRIPE_COUNT = 6
TITLE_STRIPE_GAP = 2
TITLE_STRIPE_INSET = 1
TITLE_CLOSE_OFFSET = 12
TITLE_CLOSE_GAP = 2
TITLE_TEXT_PAD = 5
TITLE_FONT_SIZE = 11
TITLE_FONT_MIN_SIZE = 10
TITLE_STRIPE_MIN_GAP = 2
TITLE_STRIPE_ENDPOINT_ADJUST = 1
WINDOW_CONTENT_PAD = 3
MENU_FONT_SIZE = 15
MENU_FONT_MIN_SIZE = 10
MENU_LABEL_X = 50
MENU_LABEL_GAP = 13

# Scrollbars
SCROLLBAR_ARROW_MIN_DELTA = 2
SCROLLBAR_ARROW_WIDTH_DIVISOR = 3
SCROLLBAR_ARROW_HEIGHT_DIVISOR = 6

# BBS terminal window
BBS_REFERENCE_WIDTH = 800
BBS_REFERENCE_HEIGHT = 480
BBS_X = 12
BBS_Y = 55
BBS_LIFT = 6
BBS_LIFT_MIN = 3
BBS_BOTTOM_GAP = 4
BBS_X_INSET = 5
SHADOW_OFFSET_SCALE = 2


def _scaled_scrollbar_button(scale: ScaleContext) -> int:
    return max(1, int(scale.u(SCROLLBAR_BUTTON) * SCROLLBAR_THICKNESS_SCALE + 0.5))


def _window_content_pad(scale: ScaleContext) -> int:
    return max(1, scale.u(WINDOW_CONTENT_PAD))


class System6Layout:
    """Computes regions and helper rectangles for the System 6 chrome."""

    def __init__(self, width: int, height: int, scale: ScaleContext):
        self.width = width
        self.height = height
        self.scale = scale
        self.regions = self._build_regions()

    def rect_from_ref(self, name: str) -> pygame.Rect:
        return self.scale.rect(pygame.Rect(REFERENCE_RECTS[name]))

    def main_window_rect(self) -> pygame.Rect:
        return self.rect_from_ref("main_window")

    def toolbar_rect(self) -> pygame.Rect:
        window = self.main_window_rect()
        return pygame.Rect(window.x, window.y, window.w, self.scale.u(TOOLBAR_HEIGHT))

    def status_rect(self) -> pygame.Rect:
        return self.rect_from_ref("status")

    def content_row_rect(self) -> pygame.Rect:
        toolbar = self.toolbar_rect()
        status = self.status_rect()
        return pygame.Rect(toolbar.x, toolbar.bottom, toolbar.w, status.y - toolbar.bottom)

    def sidebar_frame_rect(self) -> pygame.Rect:
        content = self.content_row_rect()
        return pygame.Rect(
            content.x,
            content.y,
            self.scale.x(SIDEBAR_FRAME_WIDTH),
            content.h,
        )

    def editor_outer_rect(self) -> pygame.Rect:
        content = self.content_row_rect()
        x = self.scale.x(EDITOR_X)
        return pygame.Rect(x, content.y, content.right - x, content.h)

    def _build_regions(self) -> ChromeRegions:
        sidebar, line_numbers, code, status = self._build_ide_regions()
        canvas_window, canvas_content = self._build_canvas_regions()
        bbs_window, bbs_content = self._build_bbs_regions()

        return ChromeRegions(
            sidebar=sidebar,
            line_numbers=line_numbers,
            code=code,
            status=status,
            canvas_window=canvas_window,
            canvas_content=canvas_content,
            bbs_window=bbs_window,
            bbs_content=bbs_content,
        )

    def _build_ide_regions(self) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect]:
        scale = self.scale
        status_frame = self.status_rect()
        editor = self.editor_outer_rect()
        button = _scaled_scrollbar_button(scale)
        sidebar_frame = self.sidebar_frame_rect()
        sidebar = pygame.Rect(
            sidebar_frame.x + scale.x(SIDEBAR_CONTENT_X_PAD),
            editor.y + scale.u(CONTENT_Y_PAD),
            sidebar_frame.w - scale.x(SIDEBAR_CONTENT_X_PAD * 2),
            editor.h - scale.u(CONTENT_Y_PAD * 2),
        )
        line_numbers = pygame.Rect(
            scale.x(GUTTER_X),
            editor.y + scale.u(CONTENT_Y_PAD),
            max(1, scale.x(GUTTER_W) - scale.x(LINE_NUMBER_RIGHT_PAD)),
            editor.h - button - scale.u(CONTENT_Y_PAD * 2),
        )
        code_x = editor.x + scale.x(CODE_X_PAD)
        code_y = editor.y + scale.u(CONTENT_Y_PAD)
        code = pygame.Rect(
            code_x,
            code_y,
            editor.right - button - code_x,
            editor.bottom - button - code_y,
        )
        status_pad = scale.x(STATUS_TEXT_X_PAD)
        status = pygame.Rect(
            status_frame.x + status_pad,
            status_frame.y,
            max(1, status_frame.w - status_pad * 2),
            status_frame.h,
        )
        return sidebar, line_numbers, code, status

    def _build_canvas_regions(self) -> tuple[pygame.Rect, pygame.Rect]:
        scale = self.scale
        reference = CANVAS_REFERENCE
        content_pad = _window_content_pad(scale)
        title_h = scale.u(TITLEBAR_HEIGHT)
        canvas_window = pygame.Rect(
            scale_floor(reference.window.x, scale.sx)
            + scale_round_half_up(REFERENCE_LAYOUT_OFFSET_X, scale.sx),
            scale_floor(reference.window.y, scale.sy)
            + scale_round_half_up(REFERENCE_LAYOUT_OFFSET_Y, scale.sy),
            max(1, scale_floor(reference.window.w, scale.sx)),
            max(1, scale_floor(reference.window.h, scale.sy)),
        )
        canvas_content = pygame.Rect(
            canvas_window.x + content_pad,
            canvas_window.y + title_h + content_pad,
            max(1, canvas_window.w - content_pad * 2),
            max(1, canvas_window.h - title_h - content_pad * 2),
        )
        return canvas_window, canvas_content

    def _build_bbs_regions(self) -> tuple[pygame.Rect, pygame.Rect]:
        bbs_scale = ScaleContext(
            self.width,
            self.height,
            BBS_REFERENCE_WIDTH,
            BBS_REFERENCE_HEIGHT,
        )
        bbs_x = bbs_scale.x(BBS_X)
        bbs_y = bbs_scale.y(BBS_Y)
        bbs_lift = max(BBS_LIFT_MIN, bbs_scale.y(BBS_LIFT))
        bbs_bottom_gap = max(1, bbs_scale.y(BBS_BOTTOM_GAP))
        bbs_window = pygame.Rect(
            bbs_x,
            max(0, bbs_y - bbs_lift),
            self.width - bbs_x * 2,
            self.height - bbs_y - bbs_bottom_gap,
        )
        bbs_x_inset = bbs_scale.x(BBS_X_INSET)
        bbs_y_inset = _window_content_pad(self.scale)
        title_h = self.scale.u(TITLEBAR_HEIGHT)
        bbs_content_y = bbs_window.y + title_h + bbs_y_inset
        bbs_content = pygame.Rect(
            bbs_window.x + bbs_x_inset,
            bbs_content_y,
            bbs_window.w - bbs_x_inset * 2,
            bbs_window.bottom - bbs_content_y - bbs_y_inset,
        )
        return bbs_window, bbs_content


class System6Chrome:
    """Draw scalable System 6-style chrome with pygame primitives."""

    def __init__(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
        assets_dir: str = DEFAULT_ASSETS_DIR,
    ):
        self.surface = surface
        self.width = width
        self.height = height
        self.assets_dir = assets_dir
        self.scale_context = ScaleContext(width, height)
        self.scale = self.scale_context.stroke
        self.unit = self.scale_context.unit
        self._painter = ChromePainter(self.surface, self.scale)
        self.layout = System6Layout(width, height, self.scale_context)
        self.regions = self.layout.regions
        self._checker_cache: dict[tuple[int, int, int, Color, Color], pygame.Surface] = {}

        self._title_font = self._load_font(
            "ChicagoFLF.ttf",
            max(
                TITLE_FONT_MIN_SIZE,
                int(TITLE_FONT_SIZE * self.unit + 0.5),
            ),
        )
        self._menu_font = self._load_font(
            "ChicagoFLF.ttf",
            max(MENU_FONT_MIN_SIZE, int(MENU_FONT_SIZE * self.unit)),
        )
        self._toolbar_icon_extent = self._compute_toolbar_icon_extent()
        self._toolbar_icons = self._load_toolbar_icons(self._toolbar_icon_extent)
        self._menu_logo = self._load_menu_logo()

    def draw_ide(self) -> None:
        """Draw the base IDE chrome and content wells."""
        menu_h = self.layout.rect_from_ref("menu_bar").h
        window_rect = self.layout.main_window_rect()

        self.surface.fill(WHITE)
        self._fill_checker(pygame.Rect(0, menu_h, self.width, self.height - menu_h))
        self._draw_menu_bar(menu_h)
        self._draw_main_window_frame(window_rect)

        toolbar_rect = self.layout.toolbar_rect()
        pygame.draw.rect(self.surface, WHITE, toolbar_rect)
        self._painter.single_border_box(toolbar_rect, right=False, bottom=False)
        self._draw_toolbar_glyphs(toolbar_rect)

        self._draw_content_wells()
        self._draw_desktop_corners()

    def draw_canvas_window(self) -> None:
        self._draw_system6_window(self.regions.canvas_window, "Canvas")

    def draw_bbs_window(self) -> None:
        """Draw the BBS terminal frame."""
        self._draw_system6_window(self.regions.bbs_window, "Terminal")

    def _load_toolbar_icons(self, extent: int) -> list[pygame.Surface]:
        return [
            self._load_generated_icon(filename, extent)
            for filename in SYSTEM6_TOOLBAR_ICON_FILES
        ]

    def _load_generated_icon(self, filename: str, extent: int) -> pygame.Surface:
        path = os.path.join(
            self.assets_dir,
            "system6",
            "generated",
            str(extent),
            filename,
        )
        if not os.path.exists(path):
            raise FileNotFoundError(f"missing generated System 6 icon: {path}")
        return pygame.image.load(path)

    def _load_menu_logo(self) -> pygame.Surface:
        reference_logo = self._load_generated_icon(
            SYSTEM6_LOGO_FILE,
            SYSTEM6_LOGO_ICON_EXTENTS[-1],
        )
        extent = self._menu_logo_extent(reference_logo)
        if extent == SYSTEM6_LOGO_ICON_EXTENTS[-1]:
            return reference_logo
        return self._load_generated_icon(SYSTEM6_LOGO_FILE, extent)

    def _load_font(self, filename: str, size: int) -> pygame.font.Font:
        path = os.path.join(self.assets_dir, filename)
        if os.path.exists(path):
            return pygame.font.Font(path, size)
        return pygame.font.Font(None, size)

    def _draw_menu_bar(self, height: int) -> None:
        pygame.draw.rect(self.surface, WHITE, (0, 0, self.width, height))
        self._painter.line((0, height - self.scale), (self.width, height - self.scale))
        self._blit_menu_logo(self.layout.rect_from_ref("apple_icon"))
        x = self.scale_context.x(MENU_LABEL_X)
        y = max(self.scale, (height - self._menu_font.get_height()) // 2)
        for label in ("File", "Edit", "View", "Compile", "Debug", "Special"):
            text = self._menu_font.render(label, True, BLACK)
            self.surface.blit(text, (x, y))
            x += text.get_width() + self.scale_context.x(MENU_LABEL_GAP)

    def _draw_desktop_corners(self) -> None:
        radius = max(
            DESKTOP_CORNER_MIN_RADIUS,
            self.scale_context.u(DESKTOP_CORNER_RADIUS),
        )
        offsets = []
        center = radius - 1
        for y in range(radius):
            for x in range(radius):
                if (x - center) ** 2 + (y - center) ** 2 > center ** 2:
                    offsets.append((x, y))

        for x, y in offsets:
            pygame.draw.rect(self.surface, BLACK, (x, y, self.scale, self.scale))
            pygame.draw.rect(
                self.surface,
                BLACK,
                (self.width - self.scale - x, y, self.scale, self.scale),
            )
            pygame.draw.rect(
                self.surface,
                BLACK,
                (x, self.height - self.scale - y, self.scale, self.scale),
            )
            pygame.draw.rect(
                self.surface,
                BLACK,
                (self.width - self.scale - x, self.height - self.scale - y, self.scale, self.scale),
            )

    def _draw_toolbar_glyphs(self, rect: pygame.Rect) -> None:
        for index, button in enumerate(self._toolbar_button_rects(rect)):
            icon = self._toolbar_icons[index] if index < len(self._toolbar_icons) else None
            self._draw_toolbar_button(button, icon)

    def _toolbar_button_rects(self, rect: pygame.Rect) -> tuple[pygame.Rect, ...]:
        size = self.scale_context.u(TOOLBAR_BUTTON_SIZE)
        gap = self.scale_context.u(TOOLBAR_BUTTON_GAP)
        interior_h = max(0, rect.h - self.scale * 2)
        vertical_pad = max(0, (interior_h - size + 1) // 2)
        x = rect.x + self.scale + vertical_pad
        y = rect.y + self.scale + vertical_pad
        buttons = []
        for _ in SYSTEM6_TOOLBAR_ICON_FILES:
            buttons.append(pygame.Rect(x, y, size, size))
            x += size + gap
        return tuple(buttons)

    def _draw_content_wells(self) -> None:
        sidebar_frame = self.layout.sidebar_frame_rect()
        pygame.draw.rect(self.surface, WHITE, sidebar_frame)
        self._painter.line(sidebar_frame.topleft, sidebar_frame.bottomleft)
        self._painter.line(sidebar_frame.topright, sidebar_frame.bottomright)

        content_row = self.layout.content_row_rect()
        gutter = self.regions.line_numbers
        editor = self.layout.editor_outer_rect()
        pygame.draw.rect(self.surface, WHITE, gutter)
        pygame.draw.rect(self.surface, WHITE, self.regions.code)
        self._painter.line((editor.x, content_row.y), (editor.x, content_row.bottom))
        self._painter.line(
            (editor.right - self.scale, content_row.y),
            (editor.right - self.scale, content_row.bottom),
        )

        self._draw_scrollbars()
        self._painter.line(content_row.topleft, content_row.topright)

        status = self.layout.status_rect()
        pygame.draw.rect(self.surface, WHITE, status)
        self._painter.single_border_box(status, right=False)

    def _draw_main_window_frame(self, rect: pygame.Rect) -> None:
        self._draw_shadow(rect)
        pygame.draw.rect(self.surface, WHITE, rect)

    def _draw_system6_window(self, rect: pygame.Rect, title: str) -> None:
        title_h = self._window_titlebar_height()
        self._draw_shadow(rect)
        pygame.draw.rect(self.surface, WHITE, rect)
        pygame.draw.rect(self.surface, BLACK, rect, self.scale)

        title_rect = pygame.Rect(
            rect.x + self.scale,
            rect.y + self.scale,
            rect.w - self.scale * 2,
            title_h - self.scale,
        )
        pygame.draw.rect(self.surface, WHITE, title_rect)

        stripe_inset = self.scale_context.u(TITLE_STRIPE_INSET)
        stripe_gap = max(self.scale, self.scale_context.u(TITLE_CLOSE_GAP))
        first_stripe_y, last_stripe_y, _ = self._title_stripe_metrics(title_rect)

        close_size = last_stripe_y - first_stripe_y + self.scale
        close = pygame.Rect(
            rect.x + self.scale_context.u(TITLE_CLOSE_OFFSET),
            first_stripe_y,
            close_size,
            close_size,
        )
        title_center_y = close.centery
        pygame.draw.rect(self.surface, WHITE, close)
        pygame.draw.rect(self.surface, BLACK, close, self.scale)

        text = self._title_font.render(title, True, BLACK)
        text_rect = text.get_rect(center=(rect.centerx, title_center_y))
        title_pad = self.scale_context.u(TITLE_TEXT_PAD)
        erase = pygame.Rect(
            text_rect.x - title_pad,
            title_rect.y,
            text_rect.w + title_pad * 2,
            title_rect.h,
        ).clip(title_rect)
        left_of_close_x = title_rect.x + stripe_inset
        left_of_close = pygame.Rect(
            left_of_close_x,
            title_rect.y,
            max(
                0,
                close.x - left_of_close_x - stripe_gap - TITLE_STRIPE_ENDPOINT_ADJUST,
            ),
            title_rect.h,
        )
        left_x = close.right + stripe_gap
        left_right = max(left_x, erase.x - stripe_gap)
        left_stripe = pygame.Rect(left_x, title_rect.y, left_right - left_x, title_rect.h)
        right_x = min(title_rect.right - stripe_inset, erase.right + stripe_gap)
        right_stripe = pygame.Rect(
            right_x,
            title_rect.y,
            max(0, title_rect.right - stripe_inset - right_x),
            title_rect.h,
        )
        self._draw_title_stripes(left_of_close)
        self._draw_title_stripes(left_stripe)
        self._draw_title_stripes(right_stripe)
        pygame.draw.rect(self.surface, WHITE, erase)
        self.surface.blit(text, text_rect)
        title_bottom_y = title_rect.bottom
        title_bottom_right = rect.right - self.scale
        if erase.x > rect.x:
            self._painter.line(
                (rect.x, title_bottom_y),
                (erase.x - self.scale, title_bottom_y),
            )
        if erase.right < title_bottom_right:
            self._painter.line(
                (erase.right, title_bottom_y),
                (title_bottom_right, title_bottom_y),
            )

    def _window_titlebar_height(self) -> int:
        return self.scale_context.u(TITLEBAR_HEIGHT)

    def _draw_shadow(self, rect: pygame.Rect) -> None:
        offset = max(1, self.scale * SHADOW_OFFSET_SCALE)
        right = pygame.Rect(rect.right, rect.y + offset, offset, rect.h)
        bottom = pygame.Rect(rect.x + offset, rect.bottom, rect.w, offset)
        self._painter.clip_rect_fill(right, BLACK)
        self._painter.clip_rect_fill(bottom, BLACK)

    def _draw_title_stripes(self, rect: pygame.Rect) -> None:
        if rect.w <= 0 or rect.h <= 0:
            return
        y, _, gap = self._title_stripe_metrics(rect)
        for _ in range(TITLE_STRIPE_COUNT):
            if y < rect.y or y >= rect.bottom:
                break
            self._painter.line((rect.x, y), (rect.right, y))
            y += gap

    def _title_stripe_metrics(self, rect: pygame.Rect) -> tuple[int, int, int]:
        gap = max(TITLE_STRIPE_MIN_GAP, self.scale_context.u(TITLE_STRIPE_GAP))
        span = (TITLE_STRIPE_COUNT - 1) * gap
        first_y = rect.y + max(0, (rect.h - 1 - span) // 2)
        last_y = first_y + span
        return first_y, last_y, gap

    def _draw_scrollbars(self) -> None:
        editor = self.layout.editor_outer_rect()
        button = _scaled_scrollbar_button(self.scale_context)
        corner_join = self.scale
        right = pygame.Rect(
            editor.right - button,
            editor.y,
            button,
            editor.h - button + corner_join,
        )
        bottom = pygame.Rect(
            editor.x,
            editor.bottom - button,
            editor.w - button + corner_join,
            button,
        )
        corner = pygame.Rect(right.x, bottom.y, right.w, bottom.h)
        arrow_h = button
        arrow_w = button

        pygame.draw.rect(self.surface, WHITE, right)
        up = pygame.Rect(right.x, right.y, right.w, arrow_h)
        down = pygame.Rect(right.x, right.bottom - arrow_h, right.w, arrow_h)
        track = pygame.Rect(right.x, up.bottom, right.w, down.y - up.bottom)
        self._fill_checker(track, dark=CHECKER_DARK, light=WHITE)
        self._painter.line(track.topleft, track.bottomleft)
        pygame.draw.rect(self.surface, WHITE, up)
        pygame.draw.rect(self.surface, WHITE, down)
        self._painter.single_border_box(up, top=False, right=False)
        self._painter.single_border_box(down, right=False)
        self._draw_arrow(up, "up")
        self._draw_arrow(down, "down")

        pygame.draw.rect(self.surface, WHITE, bottom)
        pygame.draw.rect(self.surface, WHITE, corner)
        left = pygame.Rect(bottom.x, bottom.y, arrow_w, bottom.h)
        right_btn = pygame.Rect(right.x - arrow_w, bottom.y, arrow_w + corner_join, bottom.h)
        right_arrow = pygame.Rect(right_btn.x, right_btn.y, arrow_w, right_btn.h)
        track = pygame.Rect(left.right, bottom.y, right_btn.x - left.right, bottom.h)
        self._fill_checker(track, dark=CHECKER_DARK, light=WHITE)
        self._painter.line(track.topleft, track.topright)
        pygame.draw.rect(self.surface, WHITE, left)
        pygame.draw.rect(self.surface, WHITE, right_btn)
        self._painter.single_border_box(left, bottom=False)
        self._painter.single_border_box(right_btn, bottom=False)
        self._draw_arrow(left, "left")
        self._draw_arrow(right_arrow, "right")
        self._painter.single_border_box(down, right=False)

    def _draw_toolbar_button(self, rect: pygame.Rect, icon: pygame.Surface | None) -> None:
        radius = min(
            rect.w // TOOLBAR_BUTTON_RADIUS_LIMIT_DIVISOR,
            rect.h // TOOLBAR_BUTTON_RADIUS_LIMIT_DIVISOR,
            self.scale_context.u(TOOLBAR_BUTTON_RADIUS),
        )
        pygame.draw.rect(self.surface, WHITE, rect, border_radius=radius)
        if icon is not None:
            self._blit_toolbar_icon(icon, rect)
        pygame.draw.rect(self.surface, BLACK, rect, self.scale, border_radius=radius)

    def _blit_toolbar_icon(self, icon: pygame.Surface, rect: pygame.Rect) -> None:
        target = icon.get_rect(center=rect.center)
        self.surface.blit(icon, target.topleft)

    def _blit_menu_logo(self, rect: pygame.Rect) -> None:
        target = self._menu_logo.get_rect(center=rect.center)
        self.surface.blit(self._menu_logo, target.topleft)

    def _compute_toolbar_icon_extent(self) -> int:
        button_size = self.scale_context.u(TOOLBAR_BUTTON_SIZE)
        pad = self.scale_context.u(TOOLBAR_ICON_PAD)
        return self._preferred_icon_extent(
            max(1, button_size - pad * 2),
            SYSTEM6_TOOLBAR_ICON_EXTENTS,
        )

    def _menu_logo_extent(self, reference_logo: pygame.Surface) -> int:
        logo_rect = self.layout.rect_from_ref("apple_icon")
        target_size = self._fit_icon_size(reference_logo.get_size(), logo_rect.size)
        return self._preferred_icon_extent(
            max(target_size),
            SYSTEM6_LOGO_ICON_EXTENTS,
        )

    @staticmethod
    def _fit_icon_size(
        source_size: tuple[int, int],
        max_size: tuple[int, int],
    ) -> tuple[int, int]:
        source_w, source_h = source_size
        max_w, max_h = max_size
        scale = min(max_w / source_w, max_h / source_h)
        return (
            max(1, int(source_w * scale + 0.5)),
            max(1, int(source_h * scale + 0.5)),
        )

    @staticmethod
    def _preferred_icon_extent(max_extent: int, extents: tuple[int, ...]) -> int:
        for extent in reversed(extents):
            if extent <= max_extent:
                return extent
        return extents[0]

    def _draw_arrow(self, rect: pygame.Rect, direction: str) -> None:
        cx, cy = rect.center
        dx = max(
            SCROLLBAR_ARROW_MIN_DELTA,
            rect.w // SCROLLBAR_ARROW_WIDTH_DIVISOR,
        )
        dy = max(
            SCROLLBAR_ARROW_MIN_DELTA,
            rect.h // SCROLLBAR_ARROW_HEIGHT_DIVISOR,
        )
        if direction == "up":
            pts = [(cx, cy - dy), (cx - dx, cy + dy), (cx + dx, cy + dy)]
        elif direction == "down":
            pts = [(cx, cy + dy), (cx - dx, cy - dy), (cx + dx, cy - dy)]
        elif direction == "left":
            pts = [(cx - dy, cy), (cx + dy, cy - dx), (cx + dy, cy + dx)]
        else:
            pts = [(cx + dy, cy), (cx - dy, cy - dx), (cx - dy, cy + dx)]
        pygame.draw.polygon(self.surface, BLACK, pts)

    def _fill_checker(
        self,
        rect: pygame.Rect,
        dark: Color = BLACK,
        light: Color = WHITE,
    ) -> None:
        if rect.w <= 0 or rect.h <= 0:
            return
        self.surface.blit(self._checker_surface(rect.size, dark, light), rect.topleft)

    def _checker_surface(
        self,
        size: tuple[int, int],
        dark: Color,
        light: Color,
    ) -> pygame.Surface:
        cell = max(1, self.scale)
        key = (size[0], size[1], cell, dark, light)
        cached = self._checker_cache.get(key)
        if cached is not None:
            return cached

        pattern = pygame.Surface(size)
        pattern.fill(light)
        arr = pygame.surfarray.pixels3d(pattern)
        xs = np.arange(size[0]) // cell
        ys = np.arange(size[1]) // cell
        mask = ((xs[:, None] + ys[None, :]) % 2) == 0
        arr[mask] = dark
        del arr

        self._checker_cache[key] = pattern
        return pattern
