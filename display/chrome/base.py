"""Small interface shared by chrome backends."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import pygame


DEFAULT_ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
)


@dataclass
class ChromeRegions:
    sidebar: pygame.Rect
    line_numbers: pygame.Rect
    code: pygame.Rect
    status: pygame.Rect
    canvas_window: pygame.Rect
    canvas_content: pygame.Rect
    bbs_window: pygame.Rect
    bbs_content: pygame.Rect
    line_number_align: str = "left"
    status_text_centered: bool = False


class ChromeBackend(Protocol):
    """Surface-oriented drawing contract used by Terminal."""

    regions: ChromeRegions

    def draw_ide(self) -> None:
        """Draw the base IDE chrome."""

    def draw_canvas_window(self) -> None:
        """Draw the floating canvas window chrome."""

    def draw_bbs_window(self) -> None:
        """Draw the BBS terminal window chrome."""


def default_chrome_regions(config_module, width: int, height: int) -> ChromeRegions:
    """Return the PNG asset layout as the default region contract."""
    bbs_window, bbs_content = _default_bbs_regions(width, height)
    return ChromeRegions(
        sidebar=pygame.Rect(
            config_module.SIDEBAR_X,
            config_module.SIDEBAR_Y,
            config_module.SIDEBAR_W,
            config_module.SIDEBAR_H,
        ),
        line_numbers=pygame.Rect(
            config_module.LINE_NUM_X,
            config_module.CODE_AREA_Y,
            config_module.LINE_NUM_W,
            config_module.CODE_AREA_H,
        ),
        code=pygame.Rect(
            config_module.CODE_AREA_X,
            config_module.CODE_AREA_Y,
            config_module.CODE_AREA_W,
            config_module.CODE_AREA_H,
        ),
        status=pygame.Rect(
            0,
            config_module.STATUS_BAR_Y,
            width,
            config_module.STATUS_BAR_HEIGHT,
        ),
        canvas_window=pygame.Rect(
            config_module.CANVAS_X,
            config_module.CANVAS_Y,
            config_module.CANVAS_W,
            config_module.CANVAS_H,
        ),
        canvas_content=pygame.Rect(
            config_module.CANVAS_X + config_module.CANVAS_DRAW_OFFSET_X,
            config_module.CANVAS_Y + config_module.CANVAS_DRAW_OFFSET_Y,
            config_module.CANVAS_DRAW_W,
            config_module.CANVAS_DRAW_H,
        ),
        bbs_window=bbs_window,
        bbs_content=bbs_content,
    )


def _default_bbs_regions(width: int, height: int) -> tuple[pygame.Rect, pygame.Rect]:
    chrome_x = int(12 * width / 800)
    chrome_y = int(55 * height / 480)
    window = pygame.Rect(
        chrome_x,
        chrome_y,
        width - chrome_x * 2,
        height - chrome_y - 4,
    )
    content = pygame.Rect(
        window.x + int(5 * width / 800),
        window.y + int(32 * height / 480),
        int(763 * width / 800),
        int(385 * height / 480),
    )
    return window, content
