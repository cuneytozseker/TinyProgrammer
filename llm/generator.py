"""
LLM Generator

Interface to local LLM via llama.cpp.
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
    1. HTTP mode: Connect to running llama.cpp server
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

    # ... generate method remains same ...

    def stream(self, prompt: str, max_tokens: int = 512,
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

    def build_prompt(self, program_type: str, mood: str) -> str:
        """
        Build a prompt for generating a specific type of program.
        """
        description = PROGRAM_DESCRIPTIONS.get(program_type, "does something interesting")
        
        prompt = (
            f"Write a Python script that {description}.\n"
            "You are a tiny programmer. Write ONLY the code.\n"
            "NO explanations. NO markdown code blocks.\n"
            "### VISUALS ###\n"
            "You MUST use the custom 'Canvas' library I provided.\n"
            "The variable 'c' is already initialized as 'c = Canvas()'.\n"
            "Methods available on 'c':\n"
            "- c.clear(r, g, b)\n"
            "- c.fill_rect(x, y, w, h, r, g, b)\n"
            "- c.fill_circle(x, y, radius, r, g, b)\n"
            "- c.sleep(seconds)\n"
            "\n"
            "### CONSTRAINTS ###\n"
            "- NEVER use `pygame`, `turtle`, `tkinter`, or `matplotlib`.\n"
            "- The program MUST run in an infinite `while True:` loop.\n"
            "- Do NOT import anything else.\n"
            "\n"
            "### YOUR CODE STARTS HERE ###\n"
            "import time\n"
            "import random\n"
            "import math\n"
            "from tiny_canvas import Canvas\n"
            "\n"
            "c = Canvas()\n"
        )
        
        return prompt

    def build_fix_prompt(self, code: str, error: str) -> str:
        """Build a prompt to fix broken code."""
        prompt = (
            "The following Python script failed to run:\n\n"
            f"{code}\n\n"
            f"Error message:\n{error}\n\n"
            "Fix the code. Write ONLY the fixed code.\n"
            "NO explanations. NO markdown.\n"
            "Keep the same logic but fix the error.\n"
            "Ensure it runs in an infinite loop using only standard libraries.\n"
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
