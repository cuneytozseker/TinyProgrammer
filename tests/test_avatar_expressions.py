import importlib.util
import pathlib
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "web" / "avatar_expressions.py"
SPEC = importlib.util.spec_from_file_location("dashboard_avatar_expressions", MODULE_PATH)
avatar_expressions = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(avatar_expressions)

AVATAR_BLINK_PIXELS = avatar_expressions.AVATAR_BLINK_PIXELS
AVATAR_EXPRESSIONS = avatar_expressions.AVATAR_EXPRESSIONS
AVATAR_HEAD_PIXELS = avatar_expressions.AVATAR_HEAD_PIXELS
MOOD_ORDER = avatar_expressions.MOOD_ORDER


class AvatarExpressionsTest(unittest.TestCase):
    def test_expected_moods_are_present(self):
        expected = [
            "hopeful",
            "focused",
            "curious",
            "proud",
            "frustrated",
            "tired",
            "playful",
            "determined",
        ]
        self.assertEqual(list(MOOD_ORDER), expected)
        self.assertEqual(list(AVATAR_EXPRESSIONS.keys()), expected)

    def test_each_expression_uses_unique_in_bounds_pixels(self):
        for mood, pixels in AVATAR_EXPRESSIONS.items():
            with self.subTest(mood=mood):
                self.assertTrue(pixels)
                self.assertEqual(pixels, sorted(pixels))
                self.assertEqual(len(pixels), len(set(pixels)))
                self.assertTrue(all(0 <= pixel < 64 for pixel in pixels))

    def test_each_expression_keeps_the_shared_head_shape(self):
        for mood, pixels in AVATAR_EXPRESSIONS.items():
            with self.subTest(mood=mood):
                self.assertTrue(set(AVATAR_HEAD_PIXELS).issubset(set(pixels)))

    def test_blink_pixels_match_the_eye_band(self):
        self.assertEqual(AVATAR_BLINK_PIXELS, [18, 19, 20, 21, 22])
        for mood, pixels in AVATAR_EXPRESSIONS.items():
            with self.subTest(mood=mood):
                self.assertTrue(set(pixels) & set(AVATAR_BLINK_PIXELS))


if __name__ == "__main__":
    unittest.main()
