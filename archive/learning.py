import os
import random
from typing import List

class LearningSystem:
    """
    Manages the 'long-term memory' of the Tiny Programmer.
    Stores lessons learned from successes and failures.
    """
    
    def __init__(self, filepath="lessons.md"):
        self.filepath = filepath
        self._ensure_file()
        
    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                f.write("# Developer Journal\n\n")
                
    def add_lesson(self, lesson: str, max_lessons=50):
        """
        Add a new lesson to the journal.
        Keeps file size limited to max_lessons (FIFO), preserving header.
        """
        # Clean up lesson
        lesson = lesson.strip().replace("\n", " ")
        if not lesson:
            return
            
        # Read existing content
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                lines = f.readlines()
        else:
            lines = ["# Developer Journal\n", "\n"]
            
        # Separate header and lessons
        header = []
        lessons = []
        for line in lines:
            if line.startswith("- "):
                lessons.append(line)
            elif line.strip():
                header.append(line)
        
        # Add new lesson
        lessons.append(f"- {lesson}\n")
        
        # Truncate if too many (keep most recent)
        if len(lessons) > max_lessons:
            lessons = lessons[-max_lessons:]
            
        # Write back
        with open(self.filepath, "w") as f:
            f.writelines(header)
            if header and not header[-1].endswith("\n"):
                f.write("\n")
            f.writelines(lessons)
            
    def get_recent_lessons(self, limit=5) -> str:
        """Get the most recent lessons formatted for a prompt."""
        if not os.path.exists(self.filepath):
            return ""
            
        with open(self.filepath, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.startswith("-")]
            
        if not lines:
            return ""
            
        # Get random selection from recent history to avoid staleness
        # taking last 20, picking 'limit' random ones
        candidates = lines[-20:]
        if len(candidates) > limit:
            selected = random.sample(candidates, limit)
        else:
            selected = candidates
            
        return "\n".join(selected)