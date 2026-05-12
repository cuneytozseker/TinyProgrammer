"""Region helpers shared by Terminal and procedural chrome."""

from __future__ import annotations

import os
from dataclasses import dataclass

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


def default_chrome_regions(config_module) -> ChromeRegions:
    """Return the PNG asset layout from the active config module."""
    bbs_window, bbs_content = _default_bbs_regions(config_module)
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
            config_module.DISPLAY_WIDTH,
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


def _default_bbs_regions(config_module) -> tuple[pygame.Rect, pygame.Rect]:
    width = config_module.DISPLAY_WIDTH
    height = config_module.DISPLAY_HEIGHT
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
