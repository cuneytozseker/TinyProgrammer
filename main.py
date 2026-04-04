#!/usr/bin/env python3
"""
Tiny Programmer - Main Entry Point

A self-contained device that writes code, runs it, and repeats forever.
"""

import os
import time
import signal
import sys

# Load .env file BEFORE importing config (which reads env vars at import time)
try:
    from dotenv import load_dotenv
    # Load from .env in the same directory as this script
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"[Tiny Programmer] Loaded environment from {env_path}")
except ImportError:
    # dotenv not installed, try manual loading
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"[Tiny Programmer] Loaded environment from {env_path}")

# Hide the Linux console cursor (the blinking rectangle on framebuffer)
os.system('sudo sh -c \'echo -e "\\033[?25l" > /dev/tty1\' 2>/dev/null')

import datetime

import config
from display.terminal import Terminal
from display.screensaver import StarryNight
from llm.generator import LLMGenerator
from programmer.brain import Brain, State
from programmer.personality import Personality, Mood
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

    # Apply config overrides before initializing anything
    from web.config_manager import ConfigManager
    ConfigManager()

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
    
    # Initialize LLM with OpenRouter
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("[ERROR] OPENROUTER_API_KEY not set. Add it to .env file")
        sys.exit(1)

    llm = LLMGenerator(
        api_key=api_key,
        model_name=getattr(config, 'LLM_MODEL', '')
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
    
    # Initialize BBS client (optional social layer)
    bbs_client = None
    if getattr(config, 'BBS_ENABLED', False):
        try:
            from bbs.client import BBSClient
            bbs_client = BBSClient(
                supabase_url=config.BBS_SUPABASE_URL,
                supabase_anon_key=config.BBS_SUPABASE_ANON_KEY,
                edge_function_url=config.BBS_EDGE_FUNCTION_URL,
                device_name=config.BBS_DEVICE_NAME,
            )
            print(f"[BBS] Registered as: {bbs_client.device_name}")
        except Exception as e:
            print(f"[BBS] Init failed, BBS disabled: {e}")
            bbs_client = None

    # Initialize brain (main state machine)
    brain = Brain(
        terminal=terminal,
        llm=llm,
        personality=personality,
        archive=archive,
        bbs_client=bbs_client,
    )
    
    print("[Tiny Programmer] All systems ready.")

    # Initialize color scheme from config
    if hasattr(config, 'COLOR_SCHEME') and config.COLOR_SCHEME != 'none':
        try:
            from display.framebuffer import set_color_scheme
            set_color_scheme(config.COLOR_SCHEME)
        except ImportError:
            pass  # Framebuffer not available

    # Start web server in background if enabled
    if getattr(config, 'WEB_ENABLED', False):
        try:
            from web import start_web_server
            start_web_server(
                brain,
                host=getattr(config, 'WEB_HOST', '0.0.0.0'),
                port=getattr(config, 'WEB_PORT', 5000)
            )
        except ImportError as e:
            print(f"[Tiny Programmer] Web server not available: {e}")

    print("[Tiny Programmer] Starting main loop...")

    # Screensaver instance
    screensaver = StarryNight(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)

    def is_work_time():
        # Manual override from dashboard (always takes priority)
        if getattr(brain, "_force_screensaver", False):
            return False
        if not getattr(config, "SCHEDULE_ENABLED", False):
            return True
        now = datetime.datetime.now()
        clock_in = getattr(config, "SCHEDULE_CLOCK_IN", 9)
        clock_out = getattr(config, "SCHEDULE_CLOCK_OUT", 23)
        if clock_in <= clock_out:
            return clock_in <= now.hour < clock_out
        else:
            return now.hour >= clock_in or now.hour < clock_out

    # Main loop: alternate between work and screensaver
    try:
        while True:
            if is_work_time():
                personality.mood = Mood.HOPEFUL
                brain.state = State.THINK
                brain.run(should_continue=is_work_time)
            else:
                print("[Tiny Programmer] Off duty — screensaver mode")
                terminal.enter_screensaver_mode()
                while not is_work_time():
                    screensaver.update()
                    screensaver.render(terminal.screen)
                    terminal.flush()
                    terminal.tick(30)
                terminal.exit_screensaver_mode()
                print("[Tiny Programmer] Clock in — back to work")
    except Exception as e:
        print(f"[Tiny Programmer] Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
