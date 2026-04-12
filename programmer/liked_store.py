"""
Liked Programs Store — saves programs the user liked for future remixing.

Stores full code + metadata in a JSON file so the LLM can generate
variations of programs the user enjoyed.
"""

import json
import os
import random
import time


class LikedStore:

    def __init__(self, path: str = None, max_items: int = 20):
        if path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base, "liked_programs.json")
        self.path = path
        self.max_items = max_items
        self._items = self._load()

    def _load(self) -> list:
        try:
            with open(self.path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self._items, f, indent=2)
        os.replace(tmp, self.path)

    def add(self, program_type: str, code: str):
        """Add a liked program. Bumps oldest if at capacity."""
        self._items.append({
            "type": program_type,
            "code": code,
            "liked_at": time.time(),
            "times_remixed": 0,
        })
        if len(self._items) > self.max_items:
            self._items.pop(0)
        self._save()

    def pick(self) -> dict | None:
        """Pick a random liked program, preferring less-remixed ones."""
        if not self._items:
            return None
        weights = [1.0 / (item["times_remixed"] + 1) for item in self._items]
        chosen = random.choices(self._items, weights=weights, k=1)[0]
        chosen["times_remixed"] += 1
        self._save()
        return chosen

    def count(self) -> int:
        return len(self._items)
