"""
Brain - Main State Machine

Controls the overall behavior loop:
THINK → WRITE → RUN → WATCH → ARCHIVE → repeat
"""

import os
import sys
import time
import random
import select
import subprocess
from datetime import datetime
from enum import Enum, auto
from typing import Optional
from dataclasses import dataclass

from display.terminal import Terminal
from llm.generator import LLMGenerator
from programmer.personality import Personality
from archive.repository import Repository
from archive.learning import LearningSystem
import config


class State(Enum):
    """Possible states for Tiny Programmer."""
    BOOT = auto()
    THINK = auto()
    WRITE = auto()
    REVIEW = auto()
    RUN = auto()
    WATCH = auto()
    FIX = auto()
    ARCHIVE = auto()
    REFLECT = auto()
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
        self.learning = LearningSystem()

        self.state = State.BOOT
        self.current_program: Optional[Program] = None
        self.programs_written = 0
        self.fix_attempts = 0

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
                elif self.state == State.REVIEW:
                    self._do_review()
                elif self.state == State.RUN:
                    self._do_run()
                elif self.state == State.WATCH:
                    self._do_watch()
                elif self.state == State.FIX:
                    self._do_fix()
                elif self.state == State.ARCHIVE:
                    self._do_archive()
                elif self.state == State.REFLECT:
                    self._do_reflect()
                elif self.state == State.ERROR:
                    self._do_error()

            except Exception as e:
                print(f"[Brain] Error in state {self.state}: {e}")
                self.state = State.ERROR

    def _update_sidebar(self):
        """Update the sidebar with recent program filenames from archive."""
        recent = self.archive.get_recent(count=12)
        files = [p.filename for p in recent]
        # Show most recent at top
        files.reverse()
        current = files[0] if files else ""
        self.terminal.set_file_list(files, current)

    def _transition(self, new_state: State):
        """Transition to a new state with delay."""
        print(f"[Brain] {self.state.name} → {new_state.name}")
        self._update_sidebar()
        time.sleep(config.STATE_TRANSITION_DELAY)
        self.state = new_state

    def _do_boot(self):
        """
        Boot sequence.
        """
        self.terminal.clear()
        self.terminal.set_status("BOOTING")
        self.terminal.type_string("Tiny Programmer v0.1\n")
        time.sleep(0.5)
        self.terminal.type_string("Initializing brain...\n")
        time.sleep(1.0)
        self.terminal.type_string("Ready.\n")
        time.sleep(0.5)
        self._transition(State.THINK)

    def _do_think(self):
        """
        Thinking state.
        """
        self.terminal.set_status("THINKING", self.personality.get_mood_status())

        self.fix_attempts = 0

        # Decide what to write
        program_type = self._choose_program_type()

        # Thinking comments
        comment = self.personality.get_thinking_comment()
        self.terminal.type_string(f"\n{comment}\n")

        # Simulate thinking time
        time.sleep(random.uniform(2.0, 4.0))

        # Prepare for writing
        mood = self.personality.get_mood_status()
        lessons = self.learning.get_recent_lessons()
        self._current_prompt = self.llm.build_prompt(program_type, mood, lessons)

        # Initialize current program container
        self.current_program = Program(
            code="",
            program_type=program_type,
            thought_process=comment,
            timestamp=time.time()
        )

        self._transition(State.WRITE)

    def _choose_program_type(self) -> str:
        """Choose what type of program to write, avoiding immediate repeats."""
        types, weights = zip(*config.PROGRAM_TYPES)
        # Filter out last type to avoid back-to-back repeats
        if hasattr(self, '_last_program_type') and self._last_program_type in types:
            filtered = [(t, w) for t, w in zip(types, weights) if t != self._last_program_type]
            types, weights = zip(*filtered)
        choice = random.choices(types, weights=weights)[0]
        self._last_program_type = choice
        return choice

    def _do_write(self):
        """
        Writing state.

        Generate code via LLM and display character by character.
        """
        self.terminal.set_status("WRITING", self.personality.get_mood_status())
        self.terminal.clear()  # Reset line counter

        # Start with the header
        header = self.llm.get_header()
        self.terminal.type_string(header)
        full_code = header

        in_code_block = False

        # Track lines to filter duplicates from LLM output
        current_line = ""
        skip_patterns = [
            "import time",
            "import random",
            "import math",
            "from tiny_canvas import Canvas",
            "c = Canvas()",
            "python",  # From ```python markdown
            "",  # Empty lines at start
        ]

        # Stream from LLM - filter duplicate header lines
        try:
            for token in self.llm.stream(self._current_prompt, stop=["if __name__", "<|im_end|>"]):
                # Basic markdown filtering
                if "```" in token:
                    if not in_code_block:
                        in_code_block = True
                        token = token.replace("```python", "").replace("```", "")
                    else:
                        break  # End of block

                token = token.replace("```python", "").replace("```", "")
                token = token.replace("<|im_end|>", "")

                if not token:
                    continue

                for char in token:
                    current_line += char

                    # When we hit a newline, check if line should be skipped
                    if char == '\n':
                        line_stripped = current_line.strip()
                        should_skip = any(line_stripped == pat for pat in skip_patterns)

                        if not should_skip:
                            # Output the line
                            for c in current_line:
                                self.terminal.type_char(c)
                                full_code += c
                                time.sleep(random.uniform(0.02, 0.08))
                                self.terminal.tick()
                        else:
                            print(f"[Brain] Skipping duplicate: {line_stripped}")

                        current_line = ""
                    else:
                        # Buffer the character, don't output yet
                        pass

        except Exception as e:
            print(f"[Brain] LLM Error: {e}")
            self.terminal.type_string(f"\n// Error: {e}\n")
            self.current_program.success = False
            self.current_program.error_message = str(e)
            self._transition(State.ERROR)
            return

        # Output any remaining buffered content
        if current_line:
            for c in current_line:
                self.terminal.type_char(c)
                full_code += c

        self.current_program.code = full_code
        self.terminal.type_string("\n\n// finished.\n")
        time.sleep(0.5)
        self._transition(State.REVIEW)

    def _do_review(self):
        """
        Review state: check code for obvious errors.
        """
        self.terminal.set_status("REVIEWING", "careful")
        self.terminal.type_string("\n// checking my work...\n")
        time.sleep(1)

        # Clean the code (same as in _do_run)
        raw_code = self.current_program.code
        lines = raw_code.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```') or stripped == 'python':
                continue
            clean_lines.append(line)
        code = '\n'.join(clean_lines).strip()

        # 1. Check for banned imports
        banned = ["pygame", "turtle", "tkinter", "matplotlib"]
        for lib in banned:
            if f"import {lib}" in code or f"from {lib}" in code:
                msg = f"Forbidden library usage: {lib}"
                self.terminal.type_string(f"// oops, I used {lib}!\n")
                if self.fix_attempts < 2:
                    self.current_program.error_message = msg
                    self._transition(State.FIX)
                    return
                else:
                    self.terminal.type_string("// ignoring it...\n")

        # 2. Check syntax
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            msg = f"SyntaxError: {e.msg} at line {e.lineno}"
            self.terminal.type_string(f"// syntax error found!\n")
            if self.fix_attempts < 2:
                self.current_program.error_message = msg
                self._transition(State.FIX)
                return
            else:
                self.terminal.type_string("// still broken, giving up.\n")
                self.current_program.success = False
                self._transition(State.ARCHIVE)
                return

        self.terminal.type_string("// looks good!\n")
        time.sleep(0.5)
        self._transition(State.RUN)

    def _do_run(self):
        """
        Run state.

        Try to execute the generated program.
        """
        self.terminal.set_status("RUNNING")
        self.terminal.show_canvas()

        # Clean the code
        code = self.current_program.code
        # Strip markdown and language identifiers
        lines = code.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```') or stripped == 'python':
                continue
            clean_lines.append(line)
        code = '\n'.join(clean_lines).strip()

        # Save cleaned code to temp file for execution
        filename = "temp_execution.py"
        programs_dir = "programs"
        if not os.path.exists(programs_dir):
            os.makedirs(programs_dir)

        filepath = os.path.join(programs_dir, filename)
        with open(filepath, 'w') as f:
            f.write(code)

        try:
            # Run with python -u (unbuffered) so we can see output immediately
            self.current_process = subprocess.Popen(
                [sys.executable, "-u", filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1  # Line buffered
            )

            self.current_program.success = True
            self._transition(State.WATCH)

        except Exception as e:
            self.terminal.type_string(f"Error starting program: {e}\n")
            self.current_program.success = False
            self.current_program.error_message = str(e)
            self._transition(State.ERROR)

    def _do_watch(self):
        """
        Watch state.

        Let the program run for a while, display its output.
        """
        self.terminal.set_status("WATCHING", "proud")

        start_time = time.time()
        duration = random.randint(config.WATCH_DURATION_MIN, config.WATCH_DURATION_MAX)

        last_output = ""

        while time.time() - start_time < duration:
            # Check if process finished
            if self.current_process.poll() is not None:
                self.terminal.type_string("\n// Program finished early.\n")
                break

            # Non-blocking read so timeout always works
            try:
                ready, _, _ = select.select(
                    [self.current_process.stdout], [], [], 0.1)
                if ready:
                    line = self.current_process.stdout.readline()
                    if line:
                        if line.startswith("CMD:"):
                            self.terminal.process_draw_command(line)
                        else:
                            self.terminal.type_string(line)
                        last_output = line
            except Exception:
                pass

            # Flush display to show drawing updates
            self.terminal.tick()

        # Hide canvas popup
        self.terminal.hide_canvas()

        # Cleanup process
        exit_code = self.current_process.poll()
        if exit_code is None:
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=1.0)
            except:
                self.current_process.kill()
            self.current_program.success = True
            self._transition(State.ARCHIVE)
        else:
            # Process exited early, check if error
            if exit_code != 0:
                # Try to read remaining stderr/stdout
                remaining = self.current_process.stdout.read()
                error_msg = (last_output + "\n" + remaining).strip()
                if not error_msg:
                    error_msg = f"Process exited with code {exit_code}"

                if self.fix_attempts < 2:
                    self.current_program.error_message = error_msg
                    self._transition(State.FIX)
                    return
                else:
                    self.current_program.success = False
            else:
                self.current_program.success = True

            self._transition(State.ARCHIVE)

    def _do_fix(self):
        """Fix state: try to repair broken code."""
        self.fix_attempts += 1
        self.terminal.set_status("FIXING", "worried")
        self.terminal.type_string(f"\n// oh no, it broke :(\n")
        time.sleep(1)
        self.terminal.type_string(f"// trying to fix it (attempt {self.fix_attempts})...\n")
        time.sleep(1)

        prompt = self.llm.build_fix_prompt(self.current_program.code, self.current_program.error_message)

        full_code = ""
        in_code_block = False

        try:
            for token in self.llm.stream(prompt, stop=["if __name__", "<|im_end|>"]):
                # Basic markdown filtering
                if "```" in token:
                    if not in_code_block:
                        in_code_block = True
                        token = token.replace("```python", "").replace("```", "")
                    else:
                        break  # End of block

                token = token.replace("```python", "").replace("```", "")

                if not token:
                    continue

                for char in token:
                    self.terminal.type_char(char)
                    full_code += char
                    time.sleep(random.uniform(0.01, 0.05))
                    self.terminal.tick()

        except Exception as e:
            print(f"[Brain] Fix Error: {e}")
            self._transition(State.ERROR)
            return

        self.current_program.code = full_code
        self.terminal.type_string("\n\n// fixed?\n")
        time.sleep(1)
        self._transition(State.REVIEW)

    def _do_reflect(self):
        """Reflect on what happened and learn a lesson."""
        self.terminal.set_status("REFLECTING", "wise")
        self.terminal.type_string("\n// what did I learn?\n")
        time.sleep(1)

        # Determine result string
        if self.current_program.success:
            result = "Success."
        else:
            result = f"Failed. Error: {self.current_program.error_message}"

        prompt = self.llm.build_reflection_prompt(self.current_program.code, result)

        # Stream reflection
        lesson = ""
        try:
            for token in self.llm.stream(prompt, stop=["<|im_end|>"]):
                # Filter newlines to keep it clean
                token = token.replace("\n", " ")
                self.terminal.type_char(token)
                lesson += token
                time.sleep(random.uniform(0.01, 0.05))
                self.terminal.tick()
        except Exception:
            pass

        if lesson:
            self.learning.add_lesson(lesson)
            self.terminal.type_string("\n// saved to memory.\n")

        time.sleep(2)
        self._transition(State.THINK)

    def _do_archive(self):
        """
        Archive state.

        Save the program and its metadata.
        """
        self.terminal.set_status("ARCHIVING")

        try:
            self.archive.save(
                code=self.current_program.code,
                program_type=self.current_program.program_type,
                mood=self.personality.get_mood_status(),
                success=self.current_program.success,
                thought_process=self.current_program.thought_process,
                error_message=self.current_program.error_message
            )
            self.terminal.type_string(f"\n// Saved to archive.\n")
        except Exception as e:
            print(f"[Brain] Archive error: {e}")

        self.personality.update_mood(self.current_program.success)
        self.programs_written += 1

        time.sleep(1)
        self._transition(State.REFLECT)

    def _do_error(self):
        """
        Error state.

        Handle errors gracefully, try to recover.
        """
        self.terminal.set_status("ERROR", "confused")
        self.terminal.type_string("// something went wrong...\n")
        time.sleep(2)
        self.personality.update_mood(False)
        self._transition(State.THINK)
