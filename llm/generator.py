"""
LLM Generator

Interface to LLMs via OpenRouter API and local Ollama.
Supports easy model switching through a unified API.
"""

import json
import os
import random
import requests
import time
from typing import Generator, Optional

import config


# Available models {model_id: (display_name, short_name)}
# Cloud models via OpenRouter, local models via Ollama (prefix: "ollama/")
# Note: Reasoning models removed - they use tokens on thinking, not code
AVAILABLE_MODELS = {
    # Cloud models (OpenRouter) - require OPENROUTER_API_KEY
    "anthropic/claude-haiku-4.5": ("Claude Haiku 4.5", "Haiku 4.5"),
    "anthropic/claude-3.5-haiku": ("Claude 3.5 Haiku", "Haiku 3.5"),
    "google/gemini-3-flash-preview": ("Gemini 3 Flash", "Flash"),
    "openai/gpt-4.1-mini": ("GPT-4.1 Mini", "GPT-4.1"),
    "x-ai/grok-code-fast-1": ("Grok Code Fast", "Grok"),
    "deepseek/deepseek-v3.2": ("DeepSeek V3.2", "DeepSeek"),
    # Local models (Ollama) - require Ollama running locally
    # EXPERIMENTAL: Local models may be slow and produce lower quality code on Pi4
    # Install: curl -fsSL https://ollama.com/install.sh | sh
    # Pull model: ollama pull qwen2.5-coder:1.5b
    "ollama/qwen2.5-coder:1.5b": ("Qwen 2.5 Coder 1.5B (Local/Experimental)", "Qwen-Local"),
}

# Ollama endpoint (can override via env)
OLLAMA_ENDPOINT = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434")

# Special mode for random model selection (cloud models only)
SURPRISE_ME = "surprise_me"

# Default model
DEFAULT_MODEL = "surprise_me"


def detect_ollama_models(endpoint=None):
    """
    Detect if Ollama is running and list locally available models.

    Returns:
        tuple: (available: bool, models: list[str]) where models are raw
               model names like 'qwen2.5-coder:1.5b'
    """
    url = (endpoint or OLLAMA_ENDPOINT).rstrip("/") + "/api/tags"
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return (True, models)
    except (requests.RequestException, ValueError):
        pass
    return (False, [])


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
        """Pick a random cloud model (exclude local ollama models)."""
        cloud_models = [k for k in AVAILABLE_MODELS.keys() if not k.startswith("ollama/")]
        self.model_name = random.choice(cloud_models)
        print(f"[LLM] Surprise! Selected: {self.get_short_name()}")

    def set_model(self, model_name: str):
        """Change the current model (or set to surprise_me mode)."""
        self.model_setting = model_name
        if model_name == SURPRISE_ME:
            self._pick_random_model()
        elif model_name in AVAILABLE_MODELS:
            self.model_name = model_name
            print(f"[LLM] Switched to model: {AVAILABLE_MODELS[model_name][0]}")
        elif model_name.startswith("ollama/"):
            # Dynamic Ollama model not in AVAILABLE_MODELS — allow it
            self.model_name = model_name
            display = model_name.replace("ollama/", "")
            print(f"[LLM] Switched to Ollama model: {display}")
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
        if self.model_name.startswith("ollama/"):
            return self.model_name.replace("ollama/", "")
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
        Stream text completion token by token.
        Routes to OpenRouter (cloud) or Ollama (local) based on model prefix.
        """
        if self.model_name.startswith("ollama/"):
            yield from self._stream_ollama(prompt, max_tokens, temperature, stop)
        else:
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
            with requests.post(url, headers=headers, json=data, stream=True, timeout=(10, 30)) as response:
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

    def _stream_ollama(self, prompt: str, max_tokens: int,
                       temperature: float, stop: list) -> Generator[str, None, None]:
        """Stream from local Ollama server."""
        # Extract model name (remove "ollama/" prefix)
        model = self.model_name.replace("ollama/", "")
        url = f"{OLLAMA_ENDPOINT}/api/generate"

        data = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "think": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }

        if stop:
            data["options"]["stop"] = stop

        print(f"[LLM] Sending request to Ollama ({model})")

        try:
            with requests.post(url, json=data, stream=True, timeout=(10, 120)) as response:
                if response.status_code != 200:
                    raise Exception(f"Ollama error! (err: {response.status_code})")

                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            text = chunk.get('response', '')
                            if text:
                                yield text
                            if chunk.get('done', False):
                                break
                        except json.JSONDecodeError:
                            pass
        except requests.exceptions.ConnectionError:
            raise Exception("Can't connect to Ollama! Is it running? (ollama serve)")
        except requests.exceptions.Timeout:
            raise Exception("Ollama timed out! Model might be too slow.")
        except Exception as e:
            if "Ollama" in str(e):
                raise
            print(f"[LLM] Error streaming from Ollama: {e}")
            raise

    def get_header(self, program_type: str = "") -> str:
        """Get the standard imports header. Extended for wireframe_plot."""
        base = "import time\nimport random\nimport math\nfrom tiny_canvas import Canvas\n\nc = Canvas()\n"
        if program_type == "wireframe_plot":
            base += "from tiny_plot3d import Plot3D\n\np = Plot3D(c)\n"
        return base

    def build_prompt(self, program_type: str, mood: str, lessons: str = "", creative: dict = None) -> str:
        """
        Build a prompt for generating a specific type of program.

        Args:
            program_type: type slug (e.g. "bouncing_ball")
            mood: current mood name
            lessons: recent lessons as a string (may be empty)
            creative: dict from creativity.pick_creative_dimensions() with
                      style, palette, inspiration_seed, directive keys.
                      If None, falls back to the plain prompt.
        """
        # Special case: wireframe_plot uses the Plot3D helper
        if program_type == "wireframe_plot":
            return self._build_wireframe_prompt(lessons)

        # Local Ollama models get a stripped-down prompt (weak instruction following)
        if self.model_name.startswith("ollama/"):
            return self._build_simple_prompt(program_type, creative)

        description = PROGRAM_DESCRIPTIONS.get(program_type, "does something interesting")

        # Add learned lessons if available
        lessons_text = ""
        if lessons:
            lessons_text = f"Remember: {lessons}\n\n"

        # Get canvas dimensions from config
        canvas_w = config.CANVAS_DRAW_W
        canvas_h = config.CANVAS_DRAW_H

        # Creative direction from dimensions dict
        creative_block = ""
        if creative:
            style = creative.get("style", "")
            palette = creative.get("palette", "")
            seed = creative.get("inspiration_seed")
            directive = creative.get("directive", "")

            creative_block = f"You're writing a short Python program in the style of {style}"
            if seed:
                creative_block += f", inspired by {seed}"
            creative_block += f".\nYour mood right now is {mood} — {directive}.\n\n"
            creative_block += f"Focus on: {description}\n"
            creative_block += f"Use a {palette} color palette.\n\n"
        else:
            creative_block = f"Write a short Python program that {description}.\n\n"

        prompt = (
            f"{lessons_text}"
            f"{creative_block}"
            "RULES:\n"
            "- 20-50 lines of code\n"
            "- NO imports (already done)\n"
            "- Start with variables, then while True loop\n"
            f"- Canvas: {canvas_w}x{canvas_h} pixels\n"
            "- RGB values are integers 0-255 (NOT floats 0.0-1.0)\n"
            "- ALWAYS call c.sleep(0.033) at end of loop\n"
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

    def _build_simple_prompt(self, program_type: str, creative: dict = None) -> str:
        """Stripped-down prompt for local Ollama models (weak instruction following).

        Only includes: program type, palette, rules, API. No style, no seed,
        no mood directive, no creative direction block.
        """
        description = PROGRAM_DESCRIPTIONS.get(program_type, "does something interesting")
        canvas_w = config.CANVAS_DRAW_W
        canvas_h = config.CANVAS_DRAW_H

        palette = ""
        if creative and creative.get("palette"):
            palette = f"Use a {creative['palette']} color palette.\n"

        prompt = (
            f"Write a short Python program that {description}.\n"
            f"{palette}\n"
            "RULES:\n"
            "- 20-50 lines of code, no imports\n"
            "- while True loop, call c.sleep(0.033) each frame\n"
            f"- Canvas: {canvas_w}x{canvas_h} pixels\n\n"
            "Methods on 'c': clear, pixel, line, rect, fill_rect, circle, fill_circle, sleep\n"
            "All take r,g,b after coordinates.\n\n"
            "Output ONLY Python code.\n"
        )
        return prompt

    def _build_wireframe_prompt(self, lessons: str = "") -> str:
        """Special prompt for wireframe_plot — uses the Plot3D helper."""
        lessons_text = f"Remember: {lessons}\n\n" if lessons else ""

        prompt = (
            f"{lessons_text}"
            "Write a short Python program that plots an animated 3D wireframe surface.\n\n"
            "The canvas 'c' and Plot3D instance 'p' are ALREADY created. Just configure\n"
            "p and call p.run(func) at the end.\n\n"
            "Plot3D API (the only methods you need):\n"
            "  p.set_range(x=(min,max), y=(min,max))    # default (-5, 5)\n"
            "  p.set_grid(steps=20)                       # 10-30 recommended\n"
            "  p.set_rotation_speed(1.5)                  # degrees per frame\n"
            "  p.run(func)                                # func(x, y) -> z, starts loop\n\n"
            "Write a surface function that's visually interesting. Not just sin(x+y).\n"
            "Think: peaks, saddles, ripples, Gaussian bumps, spirals, interference patterns,\n"
            "concentric waves, tilted planes with noise. Use math.sin, cos, exp, sqrt, etc.\n\n"
            "RULES:\n"
            "- NO imports (already done — math, Plot3D, Canvas are ready)\n"
            "- Keep it under 15 lines\n"
            "- End with p.run(func) — do NOT add a while loop\n"
            "- Add a short comment above the function describing the shape\n\n"
            "Example structure:\n"
            "  # ripples from the origin\n"
            "  p.set_range(x=(-4, 4), y=(-4, 4))\n"
            "  def surface(x, y):\n"
            "      return math.sin(math.sqrt(x*x + y*y))\n"
            "  p.run(surface)\n\n"
            "Output ONLY Python code. No markdown, no explanation.\n"
        )
        return prompt

    def build_variation_prompt(self, code: str, program_type: str) -> str:
        """Build a prompt asking the LLM to create a small variation of a liked program."""
        canvas_w = config.CANVAS_DRAW_W
        canvas_h = config.CANVAS_DRAW_H

        prompt = (
            "Here's a Python program the user enjoyed:\n\n"
            f"{code}\n\n"
            "Write a variation of this program with minor changes. Try one or two of:\n"
            "- Different color palette\n"
            "- Different sizes or proportions\n"
            "- Different speed or direction\n"
            "- Slightly different shapes or patterns\n\n"
            "Keep the core behavior and structure the same.\n\n"
            "RULES:\n"
            "- 20-50 lines of code\n"
            "- NO imports (already done)\n"
            "- Start with variables, then while True loop\n"
            f"- Canvas: {canvas_w}x{canvas_h} pixels\n"
            "- RGB values are integers 0-255 (NOT floats 0.0-1.0)\n"
            "- ALWAYS call c.sleep(0.033) at end of loop\n"
            "- Use simple shapes, avoid too many draw calls per frame\n\n"
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
    # Motion & Physics
    "bouncing_ball": "animates a ball bouncing around the canvas",
    "pong": "simulates a game of pong with a ball bouncing between two paddles that move on their own",
    "orbit_system": "simulates planets orbiting a central body with simple gravity",
    "pendulum": "animates one or more swinging pendulums with damping",
    "spring_chain": "simulates a chain of masses connected by springs, wobbling realistically",
    "particle_fountain": "emits particles from a point with gravity and fade-out trails",
    "gravity_well": "shows particles attracted to a moving gravitational well",
    "flock": "simulates a flock of dots moving together with simple boids-style rules",
    # Cellular & Grid
    "game_of_life": "implements Conway's Game of Life using small filled rectangles as cells",
    "cellular_automata": "implements a 1D cellular automaton (like Rule 30 or Rule 110) drawing rows of cells",
    "wire_world": "implements Wireworld, a cellular automaton modeling electronic circuits",
    "ant_trail": "simulates ants leaving pheromone trails that other ants follow",
    "langton_ant": "implements Langton's Ant on a grid, leaving a path of flipped cells",
    "voronoi_grow": "grows a Voronoi diagram from seed points, cells expanding outward",
    # Generative & Procedural
    "pattern": "generates a mesmerizing geometric pattern with shapes and colors",
    "generative_glyphs": "generates abstract procedural glyphs or symbols on a grid using basic shapes",
    "l_system": "draws an L-system fractal pattern like a tree, snowflake, or fern using lines",
    "fractal_tree": "draws a recursive fractal tree with branches swaying slightly",
    "tile_weaver": "weaves an interlocking tile pattern like a generative textile",
    "mandala": "draws a symmetric mandala with rotational symmetry and layered motifs",
    "plasma": "renders a flowing plasma-like field using trigonometric color functions",
    # Natural Phenomena
    "rain": "simulates falling raindrops using lines",
    "starfield": "simulates stars flying toward the viewer",
    "fire": "simulates rising flames with flickering colors",
    "lightning": "draws occasional forked lightning bolts across the canvas",
    "snow": "animates snowflakes drifting down with subtle horizontal sway",
    "waves": "simulates ocean waves rolling across the canvas",
    "aurora": "animates aurora-like bands of color rippling across the sky",
    # Abstract & Artistic
    "spiral": "draws an expanding or rotating spiral pattern",
    "random_walker": "animates a dot randomly walking around the canvas leaving a trail",
    "animation": "creates a simple looping animation with moving shapes",
    "brush_strokes": "simulates expressive brush strokes appearing one by one",
    "geometric_drift": "shows geometric shapes slowly drifting and rearranging",
    "color_fields": "renders evolving abstract color fields like a Rothko painting",
    "warp_grid": "distorts a grid with smooth wave-based warping over time",
    # Math
    "wireframe_plot": "renders an animated 3D wireframe plot of a mathematical surface",
}
