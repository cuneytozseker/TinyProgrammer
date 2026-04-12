"""
Flask Web Application for TinyProgrammer

Simple web UI for monitoring and configuration.
Runs in a background thread alongside the main programmer loop.
"""

import os
import time
import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, send_from_directory

from .avatar_expressions import AVATAR_BLINK_PIXELS, AVATAR_EXPRESSIONS
from .config_manager import ConfigManager

# Global reference to brain (set by main.py)
_brain = None
# Global reference to history logger (set by main.py)
_history = None


def set_brain(brain, history=None):
    """Set the brain instance and history logger for status access."""
    global _brain, _history
    _brain = brain
    _history = history


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

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
        return render_template(
            'dashboard.html',
            status=status,
            avatar_expressions=AVATAR_EXPRESSIONS,
            avatar_blink_pixels=AVATAR_BLINK_PIXELS,
        )

    @app.route('/api/status')
    def api_status():
        """JSON API for status with history data."""
        if _brain:
            status = _brain.get_status()
            if _history:
                status["recent_history"] = _history.get_recent(10)
                status["stats"] = _history.get_stats()
                status["moods"] = _history.get_moods(50)
            return jsonify(status)
        return jsonify({"error": "Brain not initialized"})

    @app.route('/api/ollama-models')
    def api_ollama_models():
        """Return detected Ollama models as JSON."""
        from llm.generator import detect_ollama_models
        available, models = detect_ollama_models()
        return jsonify({"available": available, "models": models})

    @app.route('/api/restart', methods=['POST'])
    def api_restart():
        """Restart the program - skip to next cycle."""
        if _brain:
            _brain.request_restart()
            return jsonify({"success": True, "message": "Restart requested"})
        return jsonify({"error": "Brain not initialized"})

    @app.route('/api/screensaver/on', methods=['POST'])
    def api_screensaver_on():
        """Start screensaver manually."""
        if _brain:
            _brain._force_screensaver = True
            return jsonify({"success": True, "screensaver": "on"})
        return jsonify({"error": "Brain not initialized"})

    @app.route('/api/screensaver/off', methods=['POST'])
    def api_screensaver_off():
        """Stop screensaver manually."""
        if _brain:
            _brain._force_screensaver = False
            return jsonify({"success": True, "screensaver": "off"})
        return jsonify({"error": "Brain not initialized"})

    @app.route('/api/screenshot')
    def api_screenshot():
        """Return the current display surface as a PNG download."""
        if not _brain or not hasattr(_brain, 'terminal'):
            return jsonify({"error": "Brain not initialized"}), 503
        try:
            import io
            import pygame
            from datetime import datetime

            surface = _brain.terminal.screen
            if surface is None:
                return jsonify({"error": "No display surface available"}), 503

            buf = io.BytesIO()
            pygame.image.save(surface, buf, "PNG")
            buf.seek(0)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tinyprogrammer_{timestamp}.png"
            return Response(
                buf.getvalue(),
                mimetype="image/png",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/stream')
    def video_stream():
        """MJPEG stream of the live display surface (Docker/desktop only)."""
        import config
        if not config.WEB_STREAM_ENABLED:
            return "Stream not enabled. Set WEB_STREAM_ENABLED=true to activate.", 404

        from display.frame_stream import get_frame

        def generate():
            while True:
                frame = get_frame()
                if frame:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                    )
                time.sleep(0.05)  # ~20fps cap for the stream

        return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        """Settings page - view and edit configuration."""
        from llm.generator import AVAILABLE_MODELS, DEFAULT_MODEL, SURPRISE_ME

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
            updates['WATCH_DURATION_MIN'] = int(request.form.get('watch_duration_min', 120))
            updates['WATCH_DURATION_MAX'] = int(request.form.get('watch_duration_max', 120))
            updates['THINK_DURATION_MIN'] = int(request.form.get('think_duration_min', 3))
            updates['THINK_DURATION_MAX'] = int(request.form.get('think_duration_max', 10))
            updates['STATE_TRANSITION_DELAY'] = int(request.form.get('state_transition_delay', 2))

            # Personality settings
            updates['TYPING_SPEED_MIN'] = int(request.form.get('typing_speed_min', 2))
            updates['TYPING_SPEED_MAX'] = int(request.form.get('typing_speed_max', 8))
            updates['TYPO_PROBABILITY'] = float(request.form.get('typo_probability', 0.02))
            updates['PAUSE_PROBABILITY'] = float(request.form.get('pause_probability', 0.05))

            # Program types (checkboxes) — iterate over all known types from config
            import config as _cfg
            all_types = [t for t, _ in _cfg.PROGRAM_TYPES]
            program_types = []
            for ptype in all_types:
                if request.form.get(f'ptype_{ptype}'):
                    weight = int(request.form.get(f'pweight_{ptype}', 1))
                    program_types.append((ptype, weight))
            if program_types:
                updates['PROGRAM_TYPES'] = program_types

            # Color scheme (display adjustment layer)
            color_scheme = request.form.get('color_scheme', 'none')
            updates['COLOR_SCHEME'] = color_scheme

            # BBS settings
            updates['BBS_ENABLED'] = 'bbs_enabled' in request.form
            updates['BBS_BREAK_CHANCE'] = float(request.form.get('bbs_break_chance', 0.3))
            updates['BBS_BREAK_DURATION_MIN'] = int(request.form.get('bbs_break_duration_min', 120))
            updates['BBS_BREAK_DURATION_MAX'] = int(request.form.get('bbs_break_duration_max', 300))
            updates['BBS_DISPLAY_COLOR'] = request.form.get('bbs_display_color', 'green')
            updates['BBS_DEVICE_NAME'] = request.form.get('bbs_device_name', 'TinyProgrammer')

            # Schedule settings
            updates['SCHEDULE_ENABLED'] = 'schedule_enabled' in request.form
            updates['SCHEDULE_CLOCK_IN'] = int(request.form.get('schedule_clock_in', 9))
            updates['SCHEDULE_CLOCK_OUT'] = int(request.form.get('schedule_clock_out', 23))

            # Apply color scheme immediately to framebuffer
            try:
                from display.framebuffer import set_color_scheme
                set_color_scheme(color_scheme)
            except ImportError:
                pass  # Framebuffer not available (e.g., on dev machine)

            config_mgr.save_overrides(updates)
            message = "Settings saved! Changes will apply on next program cycle."

        # Load current config
        current = config_mgr.get_all()

        # Get current model from brain if available
        current_model = DEFAULT_MODEL
        if _brain and hasattr(_brain, 'llm'):
            current_model = _brain.llm.get_current_model()

        # Build models dict with display names for template
        models_for_template = {}
        models_for_template[SURPRISE_ME] = "Surprise Me!"
        for k, v in AVAILABLE_MODELS.items():
            models_for_template[k] = v[0]  # v is (display_name, short_name)

        # Get available color schemes
        from display.color_adjustment import COLOR_SCHEMES
        color_schemes = list(COLOR_SCHEMES.keys())

        return render_template('settings.html',
                             config=current,
                             message=message,
                             available_models=models_for_template,
                             current_model=current_model,
                             color_schemes=color_schemes)

    @app.route('/prompt', methods=['GET', 'POST'])
    def prompt_editor():
        """Prompt editor - customize program descriptions."""
        message = None
        if request.method == 'POST':
            updates = {}

            # Program descriptions — iterate over all known types from config
            import config as _cfg
            all_types = [t for t, _ in _cfg.PROGRAM_TYPES]
            descriptions = {}
            for ptype in all_types:
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

    # =========================================================================
    # History & Gallery API
    # =========================================================================

    @app.route('/api/history')
    def api_history():
        """Recent history events for the activity timeline."""
        if not _history:
            return jsonify([])
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        return jsonify(_history.get_recent(limit, offset))

    @app.route('/api/history/stats')
    def api_history_stats():
        """Aggregated success/fail stats for the pulse chart."""
        if not _history:
            return jsonify({"total_programs": 0, "success": 0, "failed": 0, "by_type": {}, "pulse": []})
        return jsonify(_history.get_stats())

    @app.route('/api/history/moods')
    def api_history_moods():
        """Recent mood shift events for the mood timeline."""
        if not _history:
            return jsonify([])
        limit = request.args.get('limit', 50, type=int)
        return jsonify(_history.get_moods(limit))

    @app.route('/api/canvas')
    def api_canvas():
        """List saved canvas images with metadata."""
        import config
        canvas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'canvas')
        results = []
        if os.path.isdir(canvas_dir):
            for fname in sorted(os.listdir(canvas_dir)):
                if fname.endswith('.png'):
                    # Look up metadata from history
                    meta = {}
                    if _history:
                        for evt in reversed(_history.get_recent(200)):
                            if evt["type"] == "canvas_capture" and evt["data"].get("filename") == fname:
                                meta = evt["data"]
                                break
                    results.append({
                        "filename": fname,
                        "url": f"/canvas/{fname}",
                        "prog_type": meta.get("prog_type", ""),
                        "program_name": meta.get("program_name", fname.replace(".png", ".py")),
                    })
        return jsonify(results)

    @app.route('/canvas/<path:filename>')
    def serve_canvas(filename):
        """Serve canvas PNG files."""
        canvas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'canvas')
        return send_from_directory(canvas_dir, filename)

    @app.route('/api/program/<name>')
    def api_program_detail(name):
        """Full program details for the detail modal."""
        if not _brain:
            return jsonify({"error": "Brain not initialized"})

        # Read code from archive
        import config
        programs_dir = os.path.join(config.ARCHIVE_PATH, "programs")
        code_path = os.path.join(programs_dir, name)
        code = ""
        if os.path.exists(code_path):
            with open(code_path, 'r') as f:
                code = f.read()

        # Get metadata from archive index
        metadata = {}
        if _brain and hasattr(_brain, 'archive'):
            for p in _brain.archive.index:
                if p.filename == name:
                    metadata = {
                        "program_type": p.program_type,
                        "created_at": p.created_at,
                        "mood": p.mood,
                        "success": p.success,
                        "thought_process": p.thought_process,
                        "error_message": p.error_message,
                        "lines_of_code": p.lines_of_code,
                    }
                    break

        # Get run-time stats from history
        run_stats = {}
        if _history:
            for evt in reversed(_history.get_recent(200)):
                if evt["type"] == "program_result" and evt["data"].get("name") == name:
                    run_stats = evt["data"]
                    break

        # Check for canvas image
        canvas_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'canvas', name.replace('.py', '.png'))
        has_canvas = os.path.exists(canvas_path)

        return jsonify({
            "name": name,
            "code": code,
            "metadata": metadata,
            "run_stats": run_stats,
            "has_canvas": has_canvas,
            "canvas_url": f"/canvas/{name.replace('.py', '.png')}" if has_canvas else None,
        })

    return app


def start_web_server(brain, history=None, host='0.0.0.0', port=5000):
    """Start the web server in a background thread."""
    set_brain(brain, history)
    app = create_app()

    # Disable Flask's reloader and debug in production
    def run_server():
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    print(f"[Web] Server started at http://{host}:{port}")
    return thread
