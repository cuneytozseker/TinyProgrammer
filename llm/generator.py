"""
LLM Generator

Interface to local LLM via llama.cpp.
Supports both HTTP API mode and subprocess mode.
"""

import json
import subprocess
from typing import Generator, Optional


class LLMGenerator:
    """
    Interface to local LLM for code generation.
    
    Can operate in two modes:
    1. HTTP mode: Connect to running llama.cpp server
    2. Subprocess mode: Launch llama.cpp directly (slower startup)
    """
    
    def __init__(self, endpoint: str, model_path: str, context_size: int):
        """
        Initialize LLM interface.
        
        Args:
            endpoint: HTTP endpoint for llama.cpp server (e.g., "http://localhost:8080/completion")
            model_path: Path to GGUF model file (for subprocess mode)
            context_size: Context window size in tokens
        """
        self.endpoint = endpoint
        self.model_path = model_path
        self.context_size = context_size
        self.mode = None  # Will be set on first call
        
    def _check_server(self) -> bool:
        """Check if llama.cpp server is running."""
        # TODO: Try to connect to endpoint
        # TODO: Return True if server responds, False otherwise
        pass
    
    def generate(self, prompt: str, max_tokens: int = 512, 
                 temperature: float = 0.7, stop: list = None) -> str:
        """
        Generate text completion (non-streaming).
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: List of stop sequences
            
        Returns:
            Generated text
        """
        # TODO: Use stream() and collect all tokens
        pass
    
    def stream(self, prompt: str, max_tokens: int = 512,
               temperature: float = 0.7, stop: list = None) -> Generator[str, None, None]:
        """
        Stream text completion token by token.
        
        This is the key method - yields tokens as they're generated,
        allowing real-time display at inference speed.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature  
            stop: List of stop sequences
            
        Yields:
            Individual tokens as strings
        """
        if self._check_server():
            yield from self._stream_http(prompt, max_tokens, temperature, stop)
        else:
            yield from self._stream_subprocess(prompt, max_tokens, temperature, stop)
    
    def _stream_http(self, prompt: str, max_tokens: int,
                     temperature: float, stop: list) -> Generator[str, None, None]:
        """
        Stream from llama.cpp HTTP server.
        
        Uses the /completion endpoint with stream=true.
        """
        # TODO: POST to endpoint with stream=true
        # TODO: Parse SSE events
        # TODO: Yield token from each event
        # 
        # Example request:
        # {
        #     "prompt": prompt,
        #     "n_predict": max_tokens,
        #     "temperature": temperature,
        #     "stop": stop,
        #     "stream": true
        # }
        #
        # Example SSE response:
        # data: {"content": "def", "stop": false}
        # data: {"content": " hello", "stop": false}
        # data: {"content": "", "stop": true}
        pass
    
    def _stream_subprocess(self, prompt: str, max_tokens: int,
                           temperature: float, stop: list) -> Generator[str, None, None]:
        """
        Stream from llama.cpp subprocess.
        
        Launches llama-cli and reads stdout.
        Slower startup but doesn't require running server.
        """
        # TODO: Build command line args
        # TODO: subprocess.Popen with stdout=PIPE
        # TODO: Read and yield characters/tokens as they come
        #
        # Example command:
        # ./llama-cli -m model.gguf -p "prompt" -n 512 --temp 0.7
        pass
    
    def build_prompt(self, program_type: str, mood: str) -> str:
        """
        Build a prompt for generating a specific type of program.
        
        Args:
            program_type: Type of program (e.g., "bouncing_ball", "clock")
            mood: Current personality mood (affects commenting style)
            
        Returns:
            Formatted prompt string
        """
        # TODO: Build system prompt with personality
        # TODO: Add specific instructions for program type
        # TODO: Include constraints (simple, short, runs in terminal/display)
        #
        # Example structure:
        # """
        # You are a tiny programmer living in a small device. You write simple, 
        # beautiful programs. You're feeling {mood} today.
        # 
        # Write a simple Python program that {program_description}.
        # Keep it under 50 lines. Add comments showing your thought process.
        # The program should run in a loop and be visually interesting.
        # 
        # ```python
        # """
        pass


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
