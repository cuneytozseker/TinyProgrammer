"""Reference layout values shared by display chrome backends."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceRect:
    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class CanvasReference:
    window: ReferenceRect
    content_offset_x: int
    content_offset_y: int
    content_w: int
    content_h: int


CANVAS_REFERENCE = CanvasReference(
    window=ReferenceRect(31, 36, 422, 242),
    content_offset_x=3,
    content_offset_y=19,
    content_w=416,
    content_h=212,
)


def scale_floor(value: int, factor: float) -> int:
    return int(value * factor)
