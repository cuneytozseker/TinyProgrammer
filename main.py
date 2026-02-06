#!/usr/bin/env python3
"""
Tiny Programmer - Main Entry Point

A self-contained device that writes code, runs it, and repeats forever.
"""

import os
import time
import signal
import sys

# Hide the Linux console cursor (the blinking rectangle on framebuffer)
os.system('sudo sh -c \'echo -e "\\033[?25l" > /dev/tty1\' 2>/dev/null')

import config
from display.terminal import Terminal
from llm.generator import LLMGenerator
from programmer.brain import Brain
from programmer.personality import Personality
from archive.repository import Repository


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n[Tiny Programmer] Shutting down...")
    # TODO: Clean up display, save state
    sys.exit(0)


def main():
    """
    Main entry point.
    
    Initializes all components and starts the main loop.
    """
    signal.signal(signal.SIGINT, signal_handler)
    
    print("[Tiny Programmer] Booting up...")
    
    # Initialize components
    terminal = Terminal(
        width=config.DISPLAY_WIDTH,
        height=config.DISPLAY_HEIGHT,
        color_bg=config.COLOR_BG,
        color_fg=config.COLOR_FG,
        font_name=config.FONT_NAME,
        font_size=config.FONT_SIZE,
        status_bar_height=config.STATUS_BAR_HEIGHT
    )
    
    # Determine endpoint based on backend
    if config.LLM_BACKEND == "ollama":
        endpoint = config.OLLAMA_ENDPOINT
    else:
        endpoint = config.LLM_ENDPOINT

    llm = LLMGenerator(
        endpoint=endpoint,
        model_path=config.LLM_MODEL_PATH,
        context_size=config.LLM_CONTEXT_SIZE,
        backend=config.LLM_BACKEND,
        model_name=getattr(config, "OLLAMA_MODEL", "")
    )
    
    personality = Personality(
        typing_speed_range=(config.TYPING_SPEED_MIN, config.TYPING_SPEED_MAX),
        typo_probability=config.TYPO_PROBABILITY,
        pause_probability=config.PAUSE_PROBABILITY
    )
    
    archive = Repository(
        local_path=config.ARCHIVE_PATH,
        github_enabled=config.GITHUB_ENABLED,
        github_repo=config.GITHUB_REPO
    )
    
    # Initialize brain (main state machine)
    brain = Brain(
        terminal=terminal,
        llm=llm,
        personality=personality,
        archive=archive
    )
    
    print("[Tiny Programmer] All systems ready.")
    print("[Tiny Programmer] Starting main loop...")
    
    # Run forever
    try:
        brain.run()
    except Exception as e:
        print(f"[Tiny Programmer] Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
