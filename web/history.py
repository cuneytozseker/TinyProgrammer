"""
History Logger

Thread-safe event logger for the TinyProgrammer dashboard.
Records program results, mood shifts, BBS posts, and canvas captures
to a JSON file for the activity timeline and charts.
"""

import json
import threading
import time
from datetime import datetime
from typing import Optional


class HistoryLogger:
    """
    Thread-safe history logger.

    Brain writes events, web reads them. Uses a lock to prevent
    concurrent access to the history JSON file.
    """

    def __init__(self, filepath: str = "history.json", max_events: int = 500):
        self.filepath = filepath
        self.max_events = max_events
        self._lock = threading.Lock()
        self._events = []
        self._load()

    def _load(self):
        """Load existing events from disk."""
        try:
            with open(self.filepath, 'r') as f:
                self._events = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._events = []

    def _save(self):
        """Write events to disk."""
        with open(self.filepath, 'w') as f:
            json.dump(self._events, f, indent=2)

    def _rotate(self):
        """Trim oldest events if over the cap."""
        if len(self._events) > self.max_events:
            self._events = self._events[-(self.max_events - 50):]

    def log(self, event_type: str, data: dict):
        """
        Append an event to history.

        Args:
            event_type: One of 'program_result', 'mood_shift', 'bbs_post', 'canvas_capture'
            data: Event payload (varies by type)
        """
        event = {
            "ts": datetime.now().isoformat(timespec='seconds'),
            "type": event_type,
            "data": data,
        }
        with self._lock:
            self._events.append(event)
            self._rotate()
            self._save()

    def get_recent(self, n: int = 20, offset: int = 0) -> list:
        """Return the last N events (all types), newest last, with offset for pagination."""
        with self._lock:
            # offset skips the N most recent events (for "load more")
            total = len(self._events)
            end = total - offset
            start = max(0, end - n)
            if end <= 0:
                return []
            return self._events[start:end]

    def get_stats(self) -> dict:
        """
        Return aggregated stats for the pulse chart.

        Includes success/fail counts, per-type breakdown, and
        a list of recent program outcomes for charting.
        """
        with self._lock:
            results = [e for e in self._events if e["type"] == "program_result"]

        success = sum(1 for e in results if e["data"].get("success"))
        fail = len(results) - success
        by_type = {}
        for e in results:
            t = e["data"].get("prog_type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1

        # Last 50 program outcomes for the pulse chart
        pulse = []
        for e in results[-50:]:
            pulse.append({
                "ts": e["ts"],
                "success": e["data"].get("success", False),
                "name": e["data"].get("name", ""),
                "run_time": e["data"].get("run_time"),
            })

        return {
            "total_programs": len(results),
            "success": success,
            "failed": fail,
            "by_type": by_type,
            "pulse": pulse,
        }

    def get_moods(self, n: int = 50) -> list:
        """Return the last N mood shift events."""
        with self._lock:
            return [e for e in self._events if e["type"] == "mood_shift"][-n:]
