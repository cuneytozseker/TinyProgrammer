import unittest

from programmer.program_source import (
    ProgramSourceError,
    clean_generated_source,
    validate_canvas_function_source,
    validate_canvas_runtime_namespace,
)


class ProgramSourceValidationTests(unittest.TestCase):
    def test_valid_setup_draw_with_imports(self):
        source = """
import math
import random
from tiny_plot3d import Plot3D

def setup(c):
    return {"x": c.width / 2, "p": Plot3D(c)}

def draw(c, state, t, dt):
    c.clear(0, 0, 0)
    state["x"] += math.cos(t) * dt
    c.fill_circle(state["x"], c.height / 2, 8, 255, 255, 255)
"""
        validate_canvas_function_source(source)

    def test_missing_draw_is_rejected(self):
        with self.assertRaisesRegex(ProgramSourceError, "Missing required draw"):
            validate_canvas_function_source("def setup(c):\n    return {}\n")

    def test_bad_draw_signature_is_rejected(self):
        with self.assertRaisesRegex(ProgramSourceError, "draw must have signature"):
            validate_canvas_function_source("def draw(c, state):\n    pass\n")

    def test_imports_are_not_policy_rejected(self):
        validate_canvas_function_source(
            "import os\n"
            "def draw(c, state, t, dt):\n"
            "    c.clear(0, 0, 0)\n"
        )

    def test_clean_generated_source_extracts_fenced_code(self):
        raw = "notes\n```python\ndef draw(c, state, t, dt):\n    c.clear(0, 0, 0)\n```\nmore notes"

        self.assertEqual(
            clean_generated_source(raw),
            "def draw(c, state, t, dt):\n    c.clear(0, 0, 0)",
        )

    def test_runtime_namespace_rejects_reassigned_draw(self):
        def draw(c, state, t, dt):
            pass

        namespace = {"draw": draw}
        validate_canvas_runtime_namespace(namespace)

        namespace["draw"] = None
        with self.assertRaisesRegex(ProgramSourceError, "draw must be callable"):
            validate_canvas_runtime_namespace(namespace)

    def test_runtime_namespace_rejects_bad_setup_signature(self):
        def draw(c, state, t, dt):
            pass

        def setup(c, extra):
            return {}

        with self.assertRaisesRegex(ProgramSourceError, "setup must have signature"):
            validate_canvas_runtime_namespace({"draw": draw, "setup": setup})


if __name__ == "__main__":
    unittest.main()
