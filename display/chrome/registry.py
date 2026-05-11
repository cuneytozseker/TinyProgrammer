"""Factory for opt-in procedural chrome backends."""

from __future__ import annotations

import pygame

from .base import ChromeBackend


def create_chrome_backend(
    name: str,
    surface: pygame.Surface,
    width: int,
    height: int,
) -> ChromeBackend | None:
    normalized = (name or "asset").lower()
    if normalized == "asset":
        return None
    if normalized == "system6":
        from .system6 import System6Chrome

        return System6Chrome(surface, width, height)
    raise ValueError(f"Unknown chrome backend '{name}'")
