"""
Web Interface for TinyProgrammer

Provides a simple Flask-based web UI for:
- Monitoring current state (dashboard)
- Editing configuration (settings)
- Customizing prompts (prompt editor)
"""

from .app import create_app, start_web_server

__all__ = ["create_app", "start_web_server"]
