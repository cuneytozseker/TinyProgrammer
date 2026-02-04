"""
LLM Generator

Interface to LLMs for code generation.
Supports local (llama.cpp, Ollama) and cloud (Gemini, Anthropic) backends.
"""

import json
import os
import subprocess
import requests
import sys
import time
from typing import Generator, Optional


# Rate limiting for cloud APIs (requests per minute)
RATE_LIMIT_RPM = 3  # Conservative limit to avoid 429 errors
MIN_REQUEST_INTERVAL = 60.0 / RATE_LIMIT_RPM  # 20 seconds between requests


class LLMGenerator:
    """
    Interface to LLM for code generation.

    Backends:
    - llamacpp: Local llama.cpp server or subprocess
    - ollama: Local Ollama server
    - gemini: Google Gemini API (cloud)
    - anthropic: Anthropic Claude API (cloud)
    """

    def __init__(self, endpoint: str, model_path: str, context_size: int,
                 backend: str = "llamacpp", model_name: str = "",
                 api_key: str = ""):
        """
        Initialize LLM interface.

        Args:
            endpoint: HTTP endpoint (for local backends)
            model_path: Path to GGUF model file (for llamacpp subprocess)
            context_size: Context window size in tokens
            backend: "llamacpp", "ollama", "gemini", or "anthropic"
            model_name: Model name (for Ollama/cloud APIs)
            api_key: API key (for cloud backends)
        """
        self.endpoint = endpoint
        self.model_path = model_path
        self.context_size = context_size
        self.backend = backend
        self.model_name = model_name
        self.api_key = api_key
        self.mode = None
        self._last_request_time = 0  # For rate limiting
        
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

    def _rate_limit(self):
        """Enforce rate limiting for cloud APIs."""
        if self.backend in ("gemini", "anthropic"):
            elapsed = time.time() - self._last_request_time
            if elapsed < MIN_REQUEST_INTERVAL:
                wait_time = MIN_REQUEST_INTERVAL - elapsed
                print(f"[LLM] Rate limiting: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            self._last_request_time = time.time()

    def stream(self, prompt: str, max_tokens: int = 512,
               temperature: float = 0.7, stop: list = None) -> Generator[str, None, None]:
        """
        Stream text completion token by token.
        """
        # Apply rate limiting for cloud APIs
        self._rate_limit()

        if self.backend == "ollama":
            yield from self._stream_ollama(prompt, max_tokens, temperature, stop)
        elif self.backend == "gemini":
            yield from self._stream_gemini(prompt, max_tokens, temperature, stop)
        elif self.backend == "anthropic":
            yield from self._stream_anthropic(prompt, max_tokens, temperature, stop)
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
        # print(f"[LLM] Prompt: {prompt[:50]}...")
        
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
                                # print(f"[LLM] Token: {repr(content)}")
                                yield content
                            if chunk.get('done', False):
                                break
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"[LLM] Error streaming from Ollama: {e}")

    def _stream_gemini(self, prompt: str, max_tokens: int,
                       temperature: float, stop: list) -> Generator[str, None, None]:
        """Stream from Google Gemini API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:streamGenerateContent"

        headers = {
            "Content-Type": "application/json",
        }

        data = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
                "stopSequences": stop or []
            }
        }

        print(f"[LLM] Sending request to Gemini ({self.model_name})")

        try:
            with requests.post(
                f"{url}?key={self.api_key}&alt=sse",
                headers=headers,
                json=data,
                stream=True
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith('data: '):
                            try:
                                chunk = json.loads(decoded[6:])
                                candidates = chunk.get('candidates', [])
                                if candidates:
                                    content = candidates[0].get('content', {})
                                    parts = content.get('parts', [])
                                    if parts:
                                        text = parts[0].get('text', '')
                                        if text:
                                            yield text
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            print(f"[LLM] Error streaming from Gemini: {e}")

    def _stream_anthropic(self, prompt: str, max_tokens: int,
                          temperature: float, stop: list) -> Generator[str, None, None]:
        """Stream from Anthropic Claude API."""
        url = "https://api.anthropic.com/v1/messages"

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        data = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": True
        }

        if stop:
            data["stop_sequences"] = stop

        print(f"[LLM] Sending request to Anthropic ({self.model_name})")

        try:
            with requests.post(url, headers=headers, json=data, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith('data: '):
                            try:
                                chunk = json.loads(decoded[6:])
                                if chunk.get('type') == 'content_block_delta':
                                    delta = chunk.get('delta', {})
                                    text = delta.get('text', '')
                                    if text:
                                        yield text
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            print(f"[LLM] Error streaming from Anthropic: {e}")

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
            
        # If model path is absolute, use it. If not, maybe we should warn.
        # But we'll try to execute 'llama-cli' from PATH.
        
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
                stderr=subprocess.DEVNULL, # Hide logging
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
            "- NO functions, NO classes\n"
            "- Start with variables, then while True loop\n"
            "- Screen: 480x320, SPI display runs at ~4 FPS\n"
            "- ALWAYS call c.sleep(0.2) at end of loop (slow screen)\n"
            "- Use simple shapes, avoid too many draw calls per frame\n\n"
            "ONLY these methods exist:\n"
            "  c.clear(r,g,b)\n"
            "  c.fill_rect(x,y,w,h,r,g,b)\n"
            "  c.fill_circle(x,y,radius,r,g,b)\n"
            "  c.sleep(seconds)\n"
            "Do NOT use any other methods.\n\n"
            "Output ONLY code, no markdown, no explanation:\n"
            "x = 100\n"
            "y = 100\n"
            "dx = 3\n"
            "while True:\n"
            "    c.clear(0,0,0)\n"
            "    c.fill_circle(x,y,20,255,0,0)\n"
            "    x += dx\n"
            "    if x > 460 or x < 20:\n"
            "        dx = -dx\n"
            "    c.sleep(0.2)\n"
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
            "- 'The canvas size is 480x320.'\n"
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
            "- NO `def` (no functions).\n"
            "- Keep it simple and flat.\n"
            "- Use 'c' for drawing.\n"
        )
        return prompt


# Program type descriptions for prompts
PROGRAM_DESCRIPTIONS = {
    "bouncing_ball": "animates a ball bouncing around the screen using ASCII characters",
    "clock": "displays a simple digital clock that updates every second",
    "pattern": "generates a mesmerizing repeating pattern",
    "animation": "creates a simple looping ASCII animation",
    "game_of_life": "implements Conway's Game of Life in a small grid",
    "spiral": "draws an expanding spiral pattern",
    "text_scroller": "scrolls a message across the screen",
    "random_walker": "animates a dot randomly walking around the screen",
}
