"""
LLM Generator

Interface to LLMs via OpenRouter API.
Supports easy model switching through a unified API.
"""

import json
import os
import random
import requests
import time
from typing import Generator, Optional

import config


# Available models on OpenRouter {model_id: (display_name, short_name)}
AVAILABLE_MODELS = {
    "anthropic/claude-haiku-4.5": ("Claude Haiku 4.5", "Haiku 4.5"),
    "anthropic/claude-3.5-haiku": ("Claude 3.5 Haiku", "Haiku 3.5"),
    "google/gemini-3-flash-preview": ("Gemini 3 Flash", "Flash"),
    "openai/gpt-5.1-codex-mini": ("GPT-5.1 Codex Mini", "Codex"),
    "x-ai/grok-code-fast-1": ("Grok Code Fast", "Grok"),
    "deepseek/deepseek-v3.2": ("DeepSeek V3.2", "DeepSeek"),
    "moonshotai/kimi-k2.5": ("Kimi K2.5", "Kimi"),
}

# Special mode for random model selection
SURPRISE_ME = "surprise_me"

# Default model
DEFAULT_MODEL = "anthropic/claude-haiku-4.5"


class LLMGenerator:
    """
    Interface to LLM for code generation via OpenRouter.
    """

    def __init__(self, api_key: str = "", model_name: str = ""):
        """
        Initialize LLM interface.

        Args:
            api_key: OpenRouter API key
            model_name: Model name (e.g., 'anthropic/claude-3.5-haiku') or 'surprise_me'
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.model_setting = model_name or DEFAULT_MODEL  # What user selected
        self.model_name = model_name or DEFAULT_MODEL     # Actual model to use
        self._last_request_time = 0
        self.current_seed = None  # Seed for current program

        # If surprise_me, pick a random model now
        if self.model_setting == SURPRISE_ME:
            self._pick_random_model()

    def _pick_random_model(self):
        """Pick a random model from available models."""
        self.model_name = random.choice(list(AVAILABLE_MODELS.keys()))
        print(f"[LLM] Surprise! Selected: {self.get_short_name()}")

    def set_model(self, model_name: str):
        """Change the current model (or set to surprise_me mode)."""
        self.model_setting = model_name
        if model_name == SURPRISE_ME:
            self._pick_random_model()
        elif model_name in AVAILABLE_MODELS:
            self.model_name = model_name
            print(f"[LLM] Switched to model: {AVAILABLE_MODELS[model_name][0]}")
        else:
            print(f"[LLM] Unknown model: {model_name}, keeping {self.model_name}")

    def select_for_new_program(self):
        """Called when starting a new program - picks random model and new seed."""
        # New seed for new program
        self.current_seed = random.randint(0, 2147483647)
        print(f"[LLM] New seed: {self.current_seed}")

        if self.model_setting == SURPRISE_ME:
            self._pick_random_model()

    def get_current_model(self) -> str:
        """Get the current model setting (may be 'surprise_me')."""
        return self.model_setting

    def get_actual_model(self) -> str:
        """Get the actual model being used for requests."""
        return self.model_name

    def get_short_name(self) -> str:
        """Get the short display name for the current model."""
        if self.model_name in AVAILABLE_MODELS:
            return AVAILABLE_MODELS[self.model_name][1]
        return "?"

    def get_available_models(self) -> dict:
        """Get dict of available models {id: display_name} including Surprise Me."""
        models = {SURPRISE_ME: ("Surprise Me!", "?")}
        for k, v in AVAILABLE_MODELS.items():
            models[k] = v
        return models

    def stream(self, prompt: str, max_tokens: int = 1024,
               temperature: float = 0.7, stop: list = None) -> Generator[str, None, None]:
        """
        Stream text completion token by token via OpenRouter.
        """
        yield from self._stream_openrouter(prompt, max_tokens, temperature, stop)

    def _stream_openrouter(self, prompt: str, max_tokens: int,
                           temperature: float, stop: list) -> Generator[str, None, None]:
        """Stream from OpenRouter API (OpenAI-compatible)."""
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/cuneytozseker/TinyProgrammer",
            "X-Title": "TinyProgrammer"
        }

        data = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "reasoning": {"exclude": True},  # Skip reasoning for faster response
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": True
        }

        # Add seed if set (same seed for retries, new seed for new programs)
        if self.current_seed is not None:
            data["seed"] = self.current_seed

        if stop:
            data["stop"] = stop

        print(f"[LLM] Sending request to OpenRouter ({self.model_name}) [seed: {self.current_seed}]")

        try:
            with requests.post(url, headers=headers, json=data, stream=True, timeout=60) as response:
                # Check for API errors
                if response.status_code == 529:
                    raise Exception("Oh no! My brain is fried! (err: 529 overloaded)")
                elif response.status_code == 429:
                    raise Exception("Whoa, too many thoughts! (err: 429 rate limited)")
                elif response.status_code == 402:
                    raise Exception("Oops! Out of credits! (err: 402 payment required)")
                elif response.status_code >= 500:
                    raise Exception(f"Cloud brain is having issues! (err: {response.status_code})")
                elif response.status_code >= 400:
                    raise Exception(f"Request error! (err: {response.status_code})")

                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith('data: '):
                            data_str = decoded[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data_str)
                                choices = chunk.get('choices', [])
                                if choices:
                                    delta = choices[0].get('delta', {})
                                    text = delta.get('content', '')
                                    if text:
                                        yield text
                            except json.JSONDecodeError:
                                pass
        except requests.exceptions.Timeout:
            raise Exception("Brain timed out! (err: timeout)")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 0
            if status == 529:
                raise Exception("Oh no! My brain is fried! (err: 529 overloaded)")
            elif status == 429:
                raise Exception("Whoa, too many thoughts! (err: 429 rate limited)")
            else:
                raise Exception(f"Cloud brain error! (err: {status})")
        except Exception as e:
            if "fried" in str(e) or "thoughts" in str(e) or "credits" in str(e):
                raise  # Re-raise our custom exceptions
            print(f"[LLM] Error streaming from OpenRouter: {e}")
            raise

    def get_header(self) -> str:
        """Get the standard imports header."""
        return "import time\nimport random\nimport math\nfrom tiny_canvas import Canvas\n\nc = Canvas()\n"

    def build_prompt(self, program_type: str, mood: str, lessons: str = "") -> str:
        """
        Build a prompt for generating a specific type of program.
        """
        description = PROGRAM_DESCRIPTIONS.get(program_type, "does something interesting")

        # Add learned lessons if available
        lessons_text = ""
        if lessons:
            lessons_text = f"Remember: {lessons}\n\n"

        # Get canvas dimensions from config
        canvas_w = config.CANVAS_DRAW_W
        canvas_h = config.CANVAS_DRAW_H

        prompt = (
            f"{lessons_text}"
            f"Write a short Python program that {description}.\n\n"
            "RULES:\n"
            "- 20-50 lines of code\n"
            "- NO imports (already done)\n"
            "- Start with variables, then while True loop\n"
            f"- Canvas: {canvas_w}x{canvas_h} pixels\n"
            "- ALWAYS call c.sleep(0.033) at end of loop\n"
            "- Use creative background colors with c.clear(), not just black\n"
            "- Use simple shapes, avoid too many draw calls per frame\n"
            "- Add short casual comments like a human thinking out loud\n"
            "  e.g. '# hmm let's try a spiral', '# this should bounce nicely'\n\n"
            "ONLY these methods exist on 'c':\n"
            "  c.clear(r,g,b)\n"
            "  c.pixel(x,y,r,g,b)\n"
            "  c.line(x1,y1,x2,y2,r,g,b)\n"
            "  c.rect(x,y,w,h,r,g,b)\n"
            "  c.fill_rect(x,y,w,h,r,g,b)\n"
            "  c.circle(x,y,radius,r,g,b)\n"
            "  c.fill_circle(x,y,radius,r,g,b)\n"
            "  c.sleep(seconds)\n"
            "Do NOT use any other methods.\n\n"
            "Output ONLY Python code. No markdown, no explanation.\n"
        )

        return prompt

    def build_reflection_prompt(self, code: str, result: str) -> str:
        """Build a prompt to learn from code execution."""
        # Get canvas dimensions from config
        canvas_w = config.CANVAS_DRAW_W
        canvas_h = config.CANVAS_DRAW_H

        prompt = (
            "Review this Python code execution:\n"
            f"Result: {result}\n\n"
            "What is ONE technical lesson to remember for next time?\n"
            "Focus on syntax, libraries, or logic errors.\n"
            "Examples:\n"
            "- 'Do not use c.move() because it does not exist.'\n"
            "- 'Always initialize variables before the loop.'\n"
            f"- 'The canvas size is {canvas_w}x{canvas_h}.'\n"
            "\n"
            "Write ONLY the lesson (1 sentence).\n"
        )
        return prompt

    def build_fix_prompt(self, code: str, error: str) -> str:
        """Build a prompt to fix broken code."""
        prompt = (
            "The following Python script failed:\n\n"
            f"{code}\n\n"
            f"Error: {error}\n\n"
            "FIX IT. Write ONLY the fixed code.\n"
            "NO explanations. NO markdown.\n"
            "Constraints:\n"
            "- Keep it simple.\n"
            "- Use 'c' for drawing.\n"
        )
        return prompt


# Program type descriptions for prompts
PROGRAM_DESCRIPTIONS = {
    "bouncing_ball": "animates a ball bouncing around the canvas",
    "pattern": "generates a mesmerizing geometric pattern with shapes and colors",
    "animation": "creates a simple looping animation with moving shapes",
    "game_of_life": "implements Conway's Game of Life using small filled rectangles as cells",
    "cellular_automata": "implements a 1D cellular automaton (like Rule 30 or Rule 110) drawing rows of cells",
    "l_system": "draws an L-system fractal pattern like a tree, snowflake, or fern using lines",
    "spiral": "draws an expanding or rotating spiral pattern",
    "random_walker": "animates a dot randomly walking around the canvas leaving a trail",
    "starfield": "simulates stars flying toward the viewer",
    "rain": "simulates falling raindrops using lines",
    "generative_glyphs": "generates abstract procedural glyphs or symbols on a grid using basic shapes",
    "pong": "simulates a game of pong with a ball bouncing between two paddles that move on their own",
}
