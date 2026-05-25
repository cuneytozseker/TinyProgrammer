import unittest

from llm.generator import LLMGenerator


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
        self.assertIn("drawing object named c is already created", prompt)
        self.assertIn("clear, pixel, line, rect", prompt)
        self.assertIn("integer RGB values from 0 to 255", prompt)
        self.assertIn("```python\nfrom tiny_canvas import TinyCanvas", prompt)
        self.assertIn("c.circle(10, 20, 5)", prompt)
        self.assertIn("Do not ask for more code", prompt)
        self.assertIn("If no specific lesson is clear, write nothing.", prompt)
        self.assertNotIn("```python\n```python", prompt)

    def test_wireframe_prompt_uses_plot3d_context(self):
        code = (
            "p.set_grid(12)\n"
            "def surface(x, y):\n"
            "    return math.sin(x) + math.cos(y)\n"
            "p.run(surface)\n"
        )

        prompt = self.generator.build_reflection_prompt(
            "Success.",
            code=code,
            program_type="wireframe_plot",
        )

        self.assertIn("Program type: wireframe_plot", prompt)
        self.assertIn("Plot3D instance named p", prompt)
        self.assertIn("p.run(func)", prompt)
        self.assertIn("returns a numeric z value", prompt)
        self.assertIn("p.set_grid(12)", prompt)
        self.assertNotIn("The only valid c methods", prompt)

    def test_prompt_truncates_long_source_with_marker(self):
        code = "x = 1\n" + ("a" * 2100)

        prompt = self.generator.build_reflection_prompt(
            "Failed. Error: boom",
            code=code,
            program_type="clock",
        )

        self.assertIn("... [source truncated]", prompt)


if __name__ == "__main__":
    unittest.main()
