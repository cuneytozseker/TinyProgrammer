"""Reminisce helpers for replaying archived creations."""

import random
from typing import Iterable, List, Optional

from archive.repository import ProgramMetadata


INTRO_TEMPLATES = [
    (
        "// that conversation shook something loose...\n",
        "// remembering a {program_type} I made when I felt {mood}\n",
        "// opening {filename}\n",
    ),
    (
        "// something on the board reminded me...\n",
        "// I want to see my old {program_type} again\n",
    ),
    (
        "// a small memory is glowing in the archive\n",
        "// replaying {filename}\n",
    ),
    (
        "// I think I made something like this once\n",
        "// it was a {program_type}, from a {mood} moment\n",
        "// opening {filename}\n",
    ),
    (
        "// the board left a small echo in me\n",
        "// it sounds like {filename}\n",
    ),
    (
        "// I found an old shape in my memory\n",
        "// a {program_type} from when I felt {mood}\n",
    ),
    (
        "// something familiar is tugging at the canvas\n",
        "// let me remember {filename}\n",
    ),
    (
        "// I want to sit with something I made before\n",
        "// this one was a {program_type}\n",
        "// opening {filename}\n",
    ),
    (
        "// the archive feels warm for a second\n",
        "// replaying a {mood} little {program_type}\n",
    ),
    (
        "// I can almost see an old program blinking\n",
        "// bringing back {filename}\n",
    ),
    (
        "// a little part of me remembers drawing this\n",
        "// {filename} is coming back into view\n",
    ),
    (
        "// the BBS made the archive feel less far away\n",
        "// remembering my old {program_type}\n",
    ),
    (
        "// I kept this one somewhere quiet\n",
        "// it was called {filename}\n",
    ),
    (
        "// there is a familiar rhythm in the screen\n",
        "// I think it belongs to {filename}\n",
    ),
    (
        "// something I made is asking to be seen again\n",
        "// a {program_type}, still here\n",
    ),
    (
        "// I am following an old thread through memory\n",
        "// it leads to {filename}\n",
    ),
    (
        "// this one feels like a note from myself\n",
        "// written in {program_type} shapes\n",
    ),
    (
        "// I remember being {mood} when this came alive\n",
        "// opening {filename}\n",
    ),
    (
        "// the canvas remembers before I do\n",
        "// replaying {filename}\n",
    ),
    (
        "// I found a small old light in the archive\n",
        "// it is a {program_type}\n",
        "// opening {filename}\n",
    ),
]


class Reminiscence:
    """Tracks one REMINISCE sequence and formats intro lines."""

    def __init__(self):
        self._seen = set()
        self.current: Optional[ProgramMetadata] = None

    def clear(self):
        """Reset sequence-local replay state."""
        self._seen = set()
        self.current = None

    def choose(self, candidates: Iterable[ProgramMetadata]) -> Optional[ProgramMetadata]:
        """Pick and mark an unseen candidate from this REMINISCE sequence."""
        unseen = self.unseen(candidates)
        if not unseen:
            return None
        self.current = random.choice(unseen)
        self._seen.add(self.key(self.current))
        return self.current

    def has_unseen(self, candidates: Iterable[ProgramMetadata]) -> bool:
        """Return whether any candidate has not played in this sequence."""
        return bool(self.unseen(candidates))

    def unseen(self, candidates: Iterable[ProgramMetadata]) -> List[ProgramMetadata]:
        """Return candidates not yet replayed in this sequence."""
        return [
            metadata for metadata in candidates
            if self.key(metadata) not in self._seen
        ]

    def key(self, metadata: ProgramMetadata) -> str:
        """Stable key for avoiding repeats in one REMINISCE sequence."""
        return metadata.filename or metadata.id

    def intro_lines(self, metadata: ProgramMetadata) -> List[str]:
        """Return formatted tender-machine intro lines for a candidate."""
        program_type = metadata.program_type.replace("_", " ")
        mood = metadata.mood or "quiet"
        template = random.choice(INTRO_TEMPLATES)
        return [
            line.format(
                filename=metadata.filename,
                program_type=program_type,
                mood=mood,
            )
            for line in template
        ]
