import threading
import unittest

import pygame

from display.terminal import Terminal


class TerminalCanvasFrameTests(unittest.TestCase):
    def make_terminal(self):
        terminal = Terminal.__new__(Terminal)
        terminal.mock_mode = False
        terminal.canvas_surface = pygame.Surface((4, 4))
        terminal.canvas_surface.fill((0, 0, 0))
        terminal._canvas_staging_surface = pygame.Surface((4, 4))
        terminal.canvas_draw_rect = pygame.Rect(0, 0, 4, 4)
        terminal._render_lock = threading.RLock()
        terminal._dirty = False
        terminal._render = lambda force_flip=False: None
        return terminal

    def test_apply_canvas_frame_swaps_completed_staging_surface(self):
        terminal = self.make_terminal()

        terminal.apply_canvas_frame([
            ["CLEAR", 10, 20, 30],
            ["PIXEL", 1, 2, 200, 210, 220],
        ])

        self.assertEqual(terminal.canvas_surface.get_at((0, 0))[:3], (10, 20, 30))
        self.assertEqual(terminal.canvas_surface.get_at((1, 2))[:3], (200, 210, 220))

    def test_malformed_canvas_frame_is_dropped_without_swap(self):
        terminal = self.make_terminal()
        terminal.canvas_surface.fill((5, 6, 7))

        terminal.apply_canvas_frame([
            ["CLEAR", 10, 20, 30],
            ["PIXEL"],
        ])

        self.assertEqual(terminal.canvas_surface.get_at((0, 0))[:3], (5, 6, 7))

    def test_draw_error_drops_canvas_frame_without_swap(self):
        terminal = self.make_terminal()
        terminal.canvas_surface.fill((5, 6, 7))

        terminal.apply_canvas_frame([
            ["PIXEL", 99, 99, 200, 210, 220],
        ])

        self.assertEqual(terminal.canvas_surface.get_at((0, 0))[:3], (5, 6, 7))


if __name__ == "__main__":
    unittest.main()
