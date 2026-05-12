"""Shared low-level pygame helpers for procedural chrome backends."""

from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class ScaleContext:
    width: int
    height: int
    reference_width: int = 480
    reference_height: int = 320

    @property
    def sx(self) -> float:
        return self.width / self.reference_width

    @property
    def sy(self) -> float:
        return self.height / self.reference_height

    @property
    def unit(self) -> float:
        return min(self.sx, self.sy)

    @property
    def stroke(self) -> int:
        return max(1, int(round(min(self.sx, self.sy))))

    def x(self, value: int) -> int:
        return self._scale(value, self.sx)

    def y(self, value: int) -> int:
        return self._scale(value, self.sy)

    def u(self, value: int) -> int:
        return self._scale(value, self.unit)

    @staticmethod
    def _scale(value: int, factor: float) -> int:
        if value == 0:
            return 0
        magnitude = max(1, int(abs(value) * factor + 0.5))
        return magnitude if value > 0 else -magnitude

    def rect(self, rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(self.x(rect.x), self.y(rect.y), self.x(rect.w), self.y(rect.h))


class ChromePainter:
    """Thin drawing wrapper for shared pygame primitives."""

    def __init__(self, surface: pygame.Surface, stroke: int):
        self.surface = surface
        self.stroke = stroke

    def line(self, start, end, color: tuple[int, int, int] = (0, 0, 0)) -> None:
        pygame.draw.line(self.surface, color, start, end, self.stroke)

    def single_border_box(
        self,
        rect: pygame.Rect,
        *,
        top: bool = True,
        right: bool = True,
        bottom: bool = True,
        left: bool = True,
        color: tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        if top:
            self.line(rect.topleft, rect.topright, color)
        if left:
            self.line(rect.topleft, rect.bottomleft, color)
        if right:
            self.line(
                (rect.right - self.stroke, rect.y),
                (rect.right - self.stroke, rect.bottom),
                color,
            )
        if bottom:
            self.line(
                (rect.x, rect.bottom - self.stroke),
                (rect.right, rect.bottom - self.stroke),
                color,
            )

    def clip_rect_fill(self, rect: pygame.Rect, color: tuple[int, int, int]) -> None:
        clipped = rect.clip(self.surface.get_rect())
        if clipped.w > 0 and clipped.h > 0:
            pygame.draw.rect(self.surface, color, clipped)
