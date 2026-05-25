import unittest

from llm.generator import LLMGenerator
from programmer.brain import (
    REFLECTION_FAILURE_FALLBACK,
    REFLECTION_SUCCESS_FALLBACK,
    _final_reflection_lesson,
    _is_reflection_non_lesson,
)


class ReflectionPromptTests(unittest.TestCase):
    def setUp(self):
        self.generator = LLMGenerator(
            api_key="",
            model_name="openai/gpt-4.1-mini",
        )

    def test_prompt_includes_execution_context_and_clean_source(self):
        code = (
            "```python\n"
            "from tiny_canvas import TinyCanvas\n"
            "c = TinyCanvas()\n"
            "c.circle(10, 20, 5)\n"
            "```\n"
        )

        prompt = self.generator.build_reflection_prompt(
            "Success.",
            code=code,
            program_type="starfield",
        )

        self.assertIn("Program type: starfield", prompt)
        self.assertIn("Result: Success.", prompt)
        self.assertIn("Canvas size:", prompt)
        self.assertIn("```python\nfrom tiny_canvas import TinyCanvas", prompt)
        self.assertIn("c.circle(10, 20, 5)", prompt)
        self.assertIn("Do not ask for more code", prompt)
        self.assertNotIn("```python\n```python", prompt)

    def test_prompt_truncates_long_source_with_marker(self):
        code = "x = 1\n" + ("a" * 2100)

        prompt = self.generator.build_reflection_prompt(
            "Failed. Error: boom",
            code=code,
            program_type="clock",
        )

        self.assertIn("... [source truncated]", prompt)


class ReflectionValidationTests(unittest.TestCase):
    def test_rejects_missing_context_non_lessons(self):
        self.assertTrue(
            _is_reflection_non_lesson(
                "I do not have enough context and no code provided to review."
            )
        )
        self.assertEqual(
            _final_reflection_lesson("I have no code to review.", success=True),
            REFLECTION_SUCCESS_FALLBACK,
        )
        self.assertEqual(
            _final_reflection_lesson("Cannot review without more details.", success=False),
            REFLECTION_FAILURE_FALLBACK,
        )
        self.assertEqual(
            _final_reflection_lesson("I can\u2019t review this without source.", success=True),
            REFLECTION_SUCCESS_FALLBACK,
        )

    def test_accepts_normal_technical_lessons(self):
        lesson = "Always initialize variables before the loop."

        self.assertFalse(_is_reflection_non_lesson(lesson))
        self.assertEqual(_final_reflection_lesson(lesson, success=True), lesson)


if __name__ == "__main__":
    unittest.main()
