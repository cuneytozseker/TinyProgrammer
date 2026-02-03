"""
Brain - Main State Machine

Controls the overall behavior loop:
THINK → WRITE → RUN → WATCH → ARCHIVE → repeat
"""

import time
import random
from enum import Enum, auto
from typing import Optional
from dataclasses import dataclass

from display.terminal import Terminal
from llm.generator import LLMGenerator
from programmer.personality import Personality
from archive.repository import Repository
import config


class State(Enum):
    """Possible states for Tiny Programmer."""
    BOOT = auto()
    THINK = auto()
    WRITE = auto()
    RUN = auto()
    WATCH = auto()
    ARCHIVE = auto()
    ERROR = auto()


@dataclass
class Program:
    """Represents a generated program."""
    code: str
    program_type: str
    thought_process: str  # The "thinking" comments
    timestamp: float
    success: bool = False
    error_message: Optional[str] = None


class Brain:
    """
    Main state machine controlling Tiny Programmer behavior.
    
    Orchestrates the cycle of thinking about what to write,
    writing code character by character, running it, and
    archiving the results.
    """
    
    def __init__(self, terminal: Terminal, llm: LLMGenerator,
                 personality: Personality, archive: Repository):
        """
        Initialize brain.
        
        Args:
            terminal: Display interface
            llm: LLM interface for code generation
            personality: Personality controller
            archive: Program storage
        """
        self.terminal = terminal
        self.llm = llm
        self.personality = personality
        self.archive = archive
        
        self.state = State.BOOT
        self.current_program: Optional[Program] = None
        self.programs_written = 0
    
    def run(self):
        """
        Main loop. Runs forever.
        
        Transitions through states based on current state.
        """
        while True:
            try:
                if self.state == State.BOOT:
                    self._do_boot()
                elif self.state == State.THINK:
                    self._do_think()
                elif self.state == State.WRITE:
                    self._do_write()
                elif self.state == State.RUN:
                    self._do_run()
                elif self.state == State.WATCH:
                    self._do_watch()
                elif self.state == State.ARCHIVE:
                    self._do_archive()
                elif self.state == State.ERROR:
                    self._do_error()
                
                # Check if we need a full refresh to clear ghosting
                self.terminal.check_ghosting_refresh()
                
            except Exception as e:
                print(f"[Brain] Error in state {self.state}: {e}")
                self.state = State.ERROR
    
    def _transition(self, new_state: State):
        """Transition to a new state with delay."""
        print(f"[Brain] {self.state.name} → {new_state.name}")
        time.sleep(config.STATE_TRANSITION_DELAY)
        self.state = new_state
    
    def _do_boot(self):
        """
        Boot sequence.
        
        Display welcome message, initialize display.
        """
        # TODO: Show boot message
        # TODO: Display "Tiny Programmer v0.1"
        # TODO: Maybe show a small ASCII art logo
        # TODO: Wait a moment
        # TODO: Transition to THINK
        pass
    
    def _do_think(self):
        """
        Thinking state.
        
        Decide what program to write, show "thinking" on display.
        """
        # TODO: Update status bar to "thinking"
        # TODO: Choose a program type (weighted random from config)
        # TODO: Update mood based on recent success/failure
        # TODO: Display thinking comments like:
        #       "// hmm, what should i make today?"
        #       "// maybe a bouncing ball..."
        #       "// yes, let's try that"
        # TODO: Build prompt for LLM
        # TODO: Transition to WRITE
        pass
    
    def _choose_program_type(self) -> str:
        """Choose what type of program to write (weighted random)."""
        types, weights = zip(*config.PROGRAM_TYPES)
        return random.choices(types, weights=weights)[0]
    
    def _do_write(self):
        """
        Writing state.
        
        Generate code via LLM and display character by character.
        This is where the magic happens.
        """
        # TODO: Update status bar to "writing" with current mood
        # TODO: Clear terminal (or continue from thinking comments)
        # TODO: Stream tokens from LLM
        # TODO: For each token:
        #       - Apply personality (maybe typo, maybe pause)
        #       - Display via terminal.type_char()
        #       - Small delay based on personality
        # TODO: Collect full code into current_program
        # TODO: Transition to RUN
        pass
    
    def _do_run(self):
        """
        Run state.
        
        Try to execute the generated program.
        """
        # TODO: Update status bar to "running"
        # TODO: Clear terminal
        # TODO: Save code to temp file
        # TODO: Try to execute with subprocess
        # TODO: If success, transition to WATCH
        # TODO: If error, maybe try to fix (or transition to THINK to start over)
        #
        # Note: Programs should be sandboxed / simple enough to not cause issues
        # Consider using exec() with restricted globals for safety
        pass
    
    def _do_watch(self):
        """
        Watch state.
        
        Let the program run for a while, display its output.
        """
        # TODO: Update status bar to "watching" with proud/satisfied mood
        # TODO: Capture program stdout
        # TODO: Display output on terminal
        # TODO: Wait for WATCH_DURATION
        # TODO: Kill program subprocess
        # TODO: Transition to ARCHIVE
        pass
    
    def _do_archive(self):
        """
        Archive state.
        
        Save the program and its metadata.
        """
        # TODO: Update status bar to "archiving"
        # TODO: Generate metadata (timestamp, type, success)
        # TODO: Take screenshot of display (optional)
        # TODO: Save to archive
        # TODO: Increment programs_written counter
        # TODO: Display brief "saved" message
        # TODO: Transition to THINK
        pass
    
    def _do_error(self):
        """
        Error state.
        
        Handle errors gracefully, try to recover.
        """
        # TODO: Display error message briefly
        # TODO: Clear state
        # TODO: Transition back to THINK
        pass
