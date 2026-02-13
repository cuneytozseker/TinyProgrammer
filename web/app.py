"""
Flask Web Application for TinyProgrammer

Simple web UI for monitoring and configuration.
Runs in a background thread alongside the main programmer loop.
"""

import os
import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify

from .config_manager import ConfigManager

# Global reference to brain (set by main.py)
_brain = None


def set_brain(brain):
    """Set the brain instance for status access."""
    global _brain
    _brain = brain


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    app.secret_key = 'tinyprogrammer-secret-key'

    # Initialize config manager
    config_mgr = ConfigManager()

    # =========================================================================
    # Routes
    # =========================================================================

    @app.route('/')
    def dashboard():
        """Dashboard - show current status."""
        status = {}
        if _brain:
            status = _brain.get_status()
        return render_template('dashboard.html', status=status)

    @app.route('/api/status')
    def api_status():
        """JSON API for status (for future use)."""
        if _brain:
            return jsonify(_brain.get_status())
        return jsonify({"error": "Brain not initialized"})

    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        """Settings page - view and edit configuration."""
        from llm.generator import AVAILABLE_MODELS, DEFAULT_MODEL

        message = None
        if request.method == 'POST':
            # Collect form data
            updates = {}

            # LLM model selection (OpenRouter)
            selected_model = request.form.get('llm_model', DEFAULT_MODEL)
            updates['LLM_MODEL'] = selected_model

            # If brain is running, update the model immediately
            if _brain and hasattr(_brain, 'llm'):
                _brain.llm.set_model(selected_model)

            updates['LLM_TEMPERATURE'] = float(request.form.get('llm_temperature', 0.7))
            updates['LLM_MAX_TOKENS'] = int(request.form.get('llm_max_tokens', 512))

            # Timing settings
            updates['WATCH_DURATION_MIN'] = int(request.form.get('watch_duration_min', 600))
            updates['WATCH_DURATION_MAX'] = int(request.form.get('watch_duration_max', 600))
            updates['THINK_DURATION_MIN'] = int(request.form.get('think_duration_min', 3))
            updates['THINK_DURATION_MAX'] = int(request.form.get('think_duration_max', 10))
            updates['STATE_TRANSITION_DELAY'] = int(request.form.get('state_transition_delay', 2))

            # Personality settings
            updates['TYPING_SPEED_MIN'] = int(request.form.get('typing_speed_min', 2))
            updates['TYPING_SPEED_MAX'] = int(request.form.get('typing_speed_max', 8))
            updates['TYPO_PROBABILITY'] = float(request.form.get('typo_probability', 0.02))
            updates['PAUSE_PROBABILITY'] = float(request.form.get('pause_probability', 0.05))

            # Program types (checkboxes)
            program_types = []
            for ptype in ['bouncing_ball', 'pattern', 'animation', 'game_of_life',
                          'cellular_automata', 'l_system', 'spiral', 'random_walker',
                          'starfield', 'rain', 'generative_glyphs', 'pong']:
                if request.form.get(f'ptype_{ptype}'):
                    weight = int(request.form.get(f'pweight_{ptype}', 1))
                    program_types.append((ptype, weight))
            if program_types:
                updates['PROGRAM_TYPES'] = program_types

            config_mgr.save_overrides(updates)
            message = "Settings saved! Changes will apply on next program cycle."

        # Load current config
        current = config_mgr.get_all()

        # Get current model from brain if available
        current_model = DEFAULT_MODEL
        if _brain and hasattr(_brain, 'llm'):
            current_model = _brain.llm.get_current_model()

        return render_template('settings.html',
                             config=current,
                             message=message,
                             available_models=AVAILABLE_MODELS,
                             current_model=current_model)

    @app.route('/prompt', methods=['GET', 'POST'])
    def prompt_editor():
        """Prompt editor - customize program descriptions."""
        message = None
        if request.method == 'POST':
            updates = {}

            # Program descriptions
            descriptions = {}
            for ptype in ['bouncing_ball', 'pattern', 'animation', 'game_of_life',
                          'cellular_automata', 'l_system', 'spiral', 'random_walker',
                          'starfield', 'rain', 'generative_glyphs', 'pong']:
                desc = request.form.get(f'desc_{ptype}', '').strip()
                if desc:
                    descriptions[ptype] = desc

            if descriptions:
                updates['PROGRAM_DESCRIPTIONS'] = descriptions

            # Canvas constraints
            canvas_width = request.form.get('canvas_width', '416')
            canvas_height = request.form.get('canvas_height', '218')
            canvas_sleep = request.form.get('canvas_sleep', '0.1')
            updates['CANVAS_CONSTRAINTS'] = {
                'width': int(canvas_width),
                'height': int(canvas_height),
                'sleep': float(canvas_sleep)
            }

            config_mgr.save_overrides(updates)
            message = "Prompts saved! Changes will apply on next program."

        # Load current config
        current = config_mgr.get_all()

        # Get default descriptions from generator
        from llm.generator import PROGRAM_DESCRIPTIONS
        descriptions = current.get('PROGRAM_DESCRIPTIONS', PROGRAM_DESCRIPTIONS)

        return render_template('prompt.html',
                             descriptions=descriptions,
                             defaults=PROGRAM_DESCRIPTIONS,
                             config=current,
                             message=message)

    return app


def start_web_server(brain, host='0.0.0.0', port=5000):
    """Start the web server in a background thread."""
    set_brain(brain)
    app = create_app()

    # Disable Flask's reloader and debug in production
    def run_server():
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    print(f"[Web] Server started at http://{host}:{port}")
    return thread
