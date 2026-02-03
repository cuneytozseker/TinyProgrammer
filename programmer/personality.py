"""
Personality System

Handles:
- Mood (affects comments, typing speed, behavior)
- Typing quirks (typos, pauses, corrections)
- Self-aware comments
"""

import random
import time
from enum import Enum
from typing import Tuple, Optional
from dataclasses import dataclass


class Mood(Enum):
    """Possible moods for Tiny Programmer."""
    HOPEFUL = "hopeful"
    FOCUSED = "focused"
    CURIOUS = "curious"
    PROUD = "proud"
    FRUSTRATED = "frustrated"
    TIRED = "tired"
    PLAYFUL = "playful"
    DETERMINED = "determined"


@dataclass
class TypingEvent:
    """Represents a typing action."""
    char: str
    delay: float
    is_typo: bool = False
    correction: Optional[str] = None  # If typo, what to correct to


class Personality:
    """
    Controls the "personality" of Tiny Programmer.
    
    Makes typing feel human through:
    - Variable typing speed based on mood
    - Occasional typos followed by corrections
    - Pauses mid-line as if thinking
    - Mood-appropriate comments
    """
    
    def __init__(self, typing_speed_range: Tuple[float, float],
                 typo_probability: float, pause_probability: float):
        """
        Initialize personality.
        
        Args:
            typing_speed_range: (min, max) characters per second
            typo_probability: Chance of making a typo (0.0 - 1.0)
            pause_probability: Chance of pausing mid-line (0.0 - 1.0)
        """
        self.speed_min, self.speed_max = typing_speed_range
        self.typo_probability = typo_probability
        self.pause_probability = pause_probability
        
        self.mood = Mood.HOPEFUL
        self.consecutive_failures = 0
        self.consecutive_successes = 0
    
    def update_mood(self, success: bool):
        """
        Update mood based on program success/failure.
        
        Args:
            success: Whether the last program ran successfully
        """
        if success:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0
        
        # TODO: Transition mood based on history
        # - Multiple successes → PROUD, PLAYFUL
        # - Multiple failures → FRUSTRATED, DETERMINED
        # - Late at night → TIRED (check system time)
        # - Starting fresh → HOPEFUL, CURIOUS
        pass
    
    def get_typing_delay(self) -> float:
        """
        Get delay before next character based on mood.
        
        Returns:
            Delay in seconds
        """
        # TODO: Calculate base speed from mood
        # - FOCUSED, DETERMINED → faster
        # - TIRED, FRUSTRATED → slower, more variable
        # - PLAYFUL → very variable
        # TODO: Add some randomness
        # TODO: Return 1.0 / chars_per_second
        pass
    
    def should_typo(self) -> bool:
        """Check if we should make a typo."""
        # TODO: Base probability modified by mood
        # - TIRED → more typos
        # - FOCUSED → fewer typos
        pass
    
    def generate_typo(self, intended_char: str) -> str:
        """
        Generate a typo for a character.
        
        Args:
            intended_char: What we meant to type
            
        Returns:
            Typo character (nearby on keyboard)
        """
        # TODO: Map characters to nearby keys
        # e.g., 'r' might become 'e', 't', 'f'
        pass
    
    def should_pause(self) -> bool:
        """Check if we should pause mid-line to 'think'."""
        # TODO: Base probability modified by mood
        # - CURIOUS → more pauses
        # - DETERMINED → fewer pauses
        pass
    
    def get_pause_duration(self) -> float:
        """Get duration of a thinking pause."""
        # TODO: Return random duration in range
        # TODO: Mood affects range
        pass
    
    def should_rewrite_line(self) -> bool:
        """Check if we should delete and rewrite current line."""
        # TODO: Small probability, higher when FRUSTRATED
        pass
    
    def get_thinking_comment(self) -> str:
        """
        Generate a thinking comment based on mood.
        
        Returns:
            Comment string like "// hmm, this might work"
        """
        comments = THINKING_COMMENTS.get(self.mood, THINKING_COMMENTS[Mood.HOPEFUL])
        return random.choice(comments)
    
    def get_mood_status(self) -> str:
        """Get mood string for status bar."""
        return self.mood.value


# Comment templates by mood
THINKING_COMMENTS = {
    Mood.HOPEFUL: [
        "// this could be fun",
        "// let's try something new",
        "// i have a good feeling about this",
        "// maybe this will work",
    ],
    Mood.FOCUSED: [
        "// okay, let's do this",
        "// concentrate...",
        "// step by step",
    ],
    Mood.CURIOUS: [
        "// what if i try...",
        "// hmm, interesting",
        "// i wonder what happens if...",
    ],
    Mood.PROUD: [
        "// that last one was nice",
        "// i'm getting better at this",
        "// another one!",
    ],
    Mood.FRUSTRATED: [
        "// okay, simpler this time",
        "// maybe i was overcomplicating it",
        "// let me try again",
        "// ugh, focus",
    ],
    Mood.TIRED: [
        "// one more...",
        "// keeping it simple",
        "// *yawn* okay",
    ],
    Mood.PLAYFUL: [
        "// ooh what about...",
        "// hehe this will be fun",
        "// let's get silly",
    ],
    Mood.DETERMINED: [
        "// i can do this",
        "// not giving up",
        "// here we go again",
    ],
}


# Keyboard adjacency for typo generation
KEYBOARD_ADJACENT = {
    'a': 'sqwz',
    'b': 'vghn',
    'c': 'xdfv',
    'd': 'serfcx',
    'e': 'wrsdf',
    'f': 'drtgvc',
    'g': 'ftyhbv',
    'h': 'gyujnb',
    'i': 'ujkol',
    'j': 'huiknm',
    'k': 'jiolm',
    'l': 'kop',
    'm': 'njk',
    'n': 'bhjm',
    'o': 'iklp',
    'p': 'ol',
    'q': 'wa',
    'r': 'edft',
    's': 'awedxz',
    't': 'rfgy',
    'u': 'yhji',
    'v': 'cfgb',
    'w': 'qase',
    'x': 'zsdc',
    'y': 'tghu',
    'z': 'asx',
}
