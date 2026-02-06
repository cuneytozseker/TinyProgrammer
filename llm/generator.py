"""
LLM Generator

Interface to local LLM via llama.cpp or Ollama.
Supports both HTTP API mode and subprocess mode.
"""

import json
import subprocess
import requests
import sys
from typing import Generator, Optional


class LLMGenerator:
    """
    Interface to local LLM for code generation.

    Can operate in two modes:
    1. HTTP mode: Connect to running llama.cpp server or Ollama
    2. Subprocess mode: Launch llama.cpp directly (slower startup)
    """

    def __init__(self, endpoint: str, model_path: str, context_size: int,
                 backend: str = "llamacpp", model_name: str = ""):
        """
        Initialize LLM interface.

        Args:
            endpoint: HTTP endpoint (llama.cpp or ollama)
            model_path: Path to GGUF model file (for subprocess mode)
            context_size: Context window size in tokens
            backend: "llamacpp" or "ollama"
            model_name: Model name for Ollama (e.g. "smollm:135m")
        """
        self.endpoint = endpoint
        self.model_path = model_path
        self.context_size = context_size
        self.backend = backend
        self.model_name = model_name
        self.mode = None

    def _check_server(self) -> bool:
        """Check if server is running."""
        try:
            # simple health check
            if self.backend == "ollama":
                # Ollama is usually at localhost:11434
                # We can check root /
                root_url = self.endpoint.replace("/api/generate", "")
                requests.get(root_url, timeout=0.5)
            else:
                requests.get(self.endpoint, timeout=0.5)
            return True
        except requests.exceptions.RequestException:
            return False

    def stream(self, prompt: str, max_tokens: int = 1024,
               temperature: float = 0.7, stop: list = None) -> Generator[str, None, None]:
        """
        Stream text completion token by token.
        """
        if self.backend == "ollama":
            yield from self._stream_ollama(prompt, max_tokens, temperature, stop)
        elif self._check_server():
            yield from self._stream_http(prompt, max_tokens, temperature, stop)
        else:
            yield from self._stream_subprocess(prompt, max_tokens, temperature, stop)

    def _stream_ollama(self, prompt: str, max_tokens: int,
                       temperature: float, stop: list) -> Generator[str, None, None]:
        """Stream from Ollama API using Chat endpoint."""
        # Use /api/chat instead of /api/generate for better compatibility
        chat_endpoint = self.endpoint.replace("/api/generate", "/api/chat")

        data = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "stop": stop or []
            },
            "stream": True
        }

        print(f"[LLM] Sending request to {chat_endpoint} with model {self.model_name}")

        try:
            with requests.post(chat_endpoint, json=data, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            # Chat endpoint returns 'message' object
                            content = chunk.get('message', {}).get('content', '')
                            if content:
                                yield content
                            if chunk.get('done', False):
                                break
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"[LLM] Error streaming from Ollama: {e}")

    def _stream_http(self, prompt: str, max_tokens: int,
                     temperature: float, stop: list) -> Generator[str, None, None]:
        """
        Stream from llama.cpp HTTP server.

        Uses the /completion endpoint with stream=true.
        """
        data = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "stop": stop or [],
            "stream": True
        }

        try:
            with requests.post(self.endpoint, json=data, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            json_str = decoded_line[6:]
                            try:
                                chunk = json.loads(json_str)
                                content = chunk.get('content', '')
                                if content:
                                    yield content
                                if chunk.get('stop', False):
                                    break
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            print(f"[LLM] Error streaming from HTTP: {e}")

    def _stream_subprocess(self, prompt: str, max_tokens: int,
                           temperature: float, stop: list) -> Generator[str, None, None]:
        """
        Stream from llama.cpp subprocess.
        """
        # Determine executable name based on platform
        executable = "llama-cli"
        if sys.platform == "win32":
            executable = "llama-cli.exe"

        cmd = [
            executable,
            "-m", self.model_path,
            "-p", prompt,
            "-n", str(max_tokens),
            "--temp", str(temperature),
            "--no-display-prompt"  # Don't echo the prompt
        ]

        if stop:
            for s in stop:
                cmd.extend(["-r", s])

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # Hide logging
                universal_newlines=True,
                encoding='utf-8',
                bufsize=0  # Unbuffered
            )

            while True:
                char = process.stdout.read(1)
                if not char and process.poll() is not None:
                    break
                if char:
                    yield char

        except FileNotFoundError:
            print(f"[LLM] {executable} not found. Make sure it is in your PATH.")
        except Exception as e:
            print(f"[LLM] Error in subprocess: {e}")

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

        prompt = (
            f"{lessons_text}"
            f"Write a short Python program that {description}.\n\n"
            "RULES:\n"
            "- 20-50 lines of code\n"
            "- NO imports (already done)\n"
            "- Start with variables, then while True loop\n"
            "- Canvas: 416x218 pixels\n"
            "- ALWAYS call c.sleep(0.1) at end of loop\n"
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
        prompt = (
            "Review this Python code execution:\n"
            f"Result: {result}\n\n"
            "What is ONE technical lesson to remember for next time?\n"
            "Focus on syntax, libraries, or logic errors.\n"
            "Examples:\n"
            "- 'Do not use c.move() because it does not exist.'\n"
            "- 'Always initialize variables before the loop.'\n"
            "- 'The canvas size is 416x218.'\n"
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
