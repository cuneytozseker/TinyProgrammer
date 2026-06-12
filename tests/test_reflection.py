import unittest

from llm.generator import LLMGenerator
from programmer import brain as brain_module
from programmer.brain import (
    Brain,
    Program,
    REFLECTION_FAILURE_FALLBACK,
    REFLECTION_SUCCESS_FALLBACK,
    State,
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


class ReflectionValidationTests(unittest.TestCase):
    def test_rejects_missing_context_non_lessons(self):
        non_lessons = (
            "I do not have enough context and no code provided to review.",
            "I don't have any code to review and pull lessons from.",
            "Without seeing the code, I can only give generic advice.",
            "The source is missing, so no specific lesson can be drawn.",
            "Please provide more details about the code.",
        )

        for lesson in non_lessons:
            with self.subTest(lesson=lesson):
                self.assertTrue(
                    _is_reflection_non_lesson(lesson),
                    msg=f"Expected missing-context non-lesson: {lesson}",
                )
                self.assertEqual(
                    _final_reflection_lesson(lesson, success=True),
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

    def test_rejects_no_specific_lesson_responses(self):
        non_lessons = (
            "No specific lesson is clear from this run.",
            "There is no clear lesson to draw here.",
            "Nothing specific to learn.",
        )

        for lesson in non_lessons:
            with self.subTest(lesson=lesson):
                self.assertTrue(_is_reflection_non_lesson(lesson))
                self.assertEqual(
                    _final_reflection_lesson(lesson, success=True),
                    REFLECTION_SUCCESS_FALLBACK,
                )

    def test_replaces_empty_reflection_with_fallback(self):
        self.assertEqual(
            _final_reflection_lesson("", success=True),
            REFLECTION_SUCCESS_FALLBACK,
        )
        self.assertEqual(
            _final_reflection_lesson("   \n\t", success=False),
            REFLECTION_FAILURE_FALLBACK,
        )

    def test_accepts_normal_technical_lessons(self):
        lesson = "Always initialize variables before the loop."

        self.assertFalse(_is_reflection_non_lesson(lesson))
        self.assertEqual(_final_reflection_lesson(lesson, success=True), lesson)

    def test_normalizes_bullets_and_multiline_output(self):
        self.assertEqual(
            _final_reflection_lesson(
                "- Keep c.show() at the end of each frame.\nAvoid extra text.",
                success=True,
            ),
            "Keep c.show() at the end of each frame. Avoid extra text.",
        )


class FakeReflectionTerminal:
    def __init__(self):
        self.statuses = []
        self.strings = []
        self.chars = []
        self.ticks = 0

    def set_status(self, *args):
        self.statuses.append(args)

    def type_string(self, text):
        self.strings.append(text)

    def type_char(self, char):
        self.chars.append(char)

    def tick(self):
        self.ticks += 1


class FakeReflectionLLM:
    def __init__(self, output):
        self.output = output
        self.prompt_args = None

    def build_reflection_prompt(self, result, code="", program_type=""):
        self.prompt_args = {
            "result": result,
            "code": code,
            "program_type": program_type,
        }
        return "reflection prompt"

    def stream(self, *_args, **_kwargs):
        midpoint = len(self.output) // 2
        yield self.output[:midpoint]
        yield self.output[midpoint:]


class FakeReflectionLearning:
    def __init__(self):
        self.lessons = []

    def add_lesson(self, lesson):
        self.lessons.append(lesson)


class ReflectionFlowTests(unittest.TestCase):
    def test_reflect_displays_and_saves_fallback_instead_of_raw_non_lesson(self):
        terminal = FakeReflectionTerminal()
        learning = FakeReflectionLearning()
        llm = FakeReflectionLLM(
            "I don't have any code to review and pull lessons from."
        )
        program = Program(
            code="c.clear(0, 0, 0)\nc.show()",
            program_type="starfield",
            thought_process="",
            timestamp=0,
            success=True,
        )
        brain = object.__new__(Brain)
        brain.terminal = terminal
        brain.learning = learning
        brain.llm = llm
        brain.current_program = program
        brain.bbs_client = None
        transitions = []
        brain._transition = transitions.append

        original_sleep = brain_module.time.sleep
        original_uniform = brain_module.random.uniform
        try:
            brain_module.time.sleep = lambda *_args, **_kwargs: None
            brain_module.random.uniform = lambda *_args, **_kwargs: 0
            brain._do_reflect()
        finally:
            brain_module.time.sleep = original_sleep
            brain_module.random.uniform = original_uniform

        displayed = "".join(terminal.strings) + "".join(terminal.chars)
        self.assertNotIn("I don't have any code", displayed)
        self.assertIn(REFLECTION_SUCCESS_FALLBACK, displayed)
        self.assertEqual(learning.lessons, [REFLECTION_SUCCESS_FALLBACK])
        self.assertEqual(transitions, [State.THINK])
        self.assertEqual(llm.prompt_args["code"], program.code)
        self.assertEqual(llm.prompt_args["program_type"], program.program_type)


if __name__ == "__main__":
    unittest.main()
