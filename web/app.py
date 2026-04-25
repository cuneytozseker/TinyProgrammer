"""
Flask Web Application for TinyProgrammer

Simple web UI for monitoring and configuration.
Runs in a background thread alongside the main programmer loop.
"""

import os
import re
import time
import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response

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
        return render_template('dashboard.html', status=status)

    @app.route('/api/status')
    def api_status():
        """JSON API for status (for future use)."""
        if _brain:
            return jsonify(_brain.get_status())
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

    @app.route('/api/reroll-name', methods=['POST'])
    def api_reroll_name():
        """Reroll the device's BBS display name."""
        if not _brain or not getattr(_brain, 'bbs_client', None):
            return jsonify({"error": "BBS not available"}), 400
        result = _brain.bbs_client.reroll_name()
        if "error" in result:
            status = 429 if "Cooldown" in result.get("error", "") else 500
            return jsonify(result), status
        return jsonify(result)

    @app.route('/api/like', methods=['POST'])
    def api_like():
        """Like the current program for future remixing."""
        if not _brain or not _brain.current_program:
            return jsonify({"error": "No program running"}), 400
        prog = _brain.current_program
        if not prog.code:
            return jsonify({"error": "No code to like"}), 400
        _brain.liked_store.add(prog.program_type, prog.code)
        return jsonify({"success": True, "liked_count": _brain.liked_store.count()})

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
        from llm.generator import AVAILABLE_MODELS, DEFAULT_MODEL, SURPRISE_ME, SURPRISE_ME_LOCAL

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

            # Program types live on the /prompt page now; see prompt_editor().

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
        models_for_template[SURPRISE_ME_LOCAL] = "Surprise Me! (Local)"
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
        """Program types & prompt editor — manage built-in and custom types."""
        import config as _config
        from llm.generator import PROGRAM_DESCRIPTIONS as DEFAULT_DESCRIPTIONS
        from programmer.creativity import CATEGORIES

        builtin_slugs = list(DEFAULT_DESCRIPTIONS.keys())
        builtin_set = set(builtin_slugs)
        core_set = set(getattr(_config, 'CORE_PROGRAMS', []))
        # Keep declared order: core first (in CORE_PROGRAMS order), then the rest
        core_slugs = [s for s in _config.CORE_PROGRAMS if s in builtin_set]
        creative_slugs = [s for s in builtin_slugs if s not in core_set]
        category_names = list(CATEGORIES.keys())

        message = None
        message_type = 'success'

        if request.method == 'POST':
            current = config_mgr.get_all()
            custom_types = dict(current.get('CUSTOM_PROGRAM_TYPES') or {})
            current_descriptions = dict(current.get('PROGRAM_DESCRIPTIONS') or {})

            # --- Delete a custom type ---------------------------------------
            delete_slug = request.form.get('delete')
            if delete_slug:
                if delete_slug in custom_types:
                    custom_types.pop(delete_slug, None)
                    current_descriptions.pop(delete_slug, None)
                    # Drop from enabled list too
                    remaining_types = [
                        (t, w) for (t, w) in (current.get('PROGRAM_TYPES') or [])
                        if t != delete_slug
                    ]
                    # Purge liked entries referencing the deleted slug
                    if _brain is not None and getattr(_brain, 'liked_store', None):
                        try:
                            _brain.liked_store.purge_type(delete_slug)
                        except Exception as e:
                            print(f"[PromptEditor] purge_type failed: {e}")
                    config_mgr.save_overrides({
                        'CUSTOM_PROGRAM_TYPES': custom_types,
                        'PROGRAM_DESCRIPTIONS': current_descriptions,
                        'PROGRAM_TYPES': remaining_types,
                    })
                    message = f"Deleted custom type '{delete_slug}'."
                else:
                    message = f"Unknown custom type '{delete_slug}'."
                    message_type = 'error'
            else:
                # --- Regular save ------------------------------------------
                errors = []

                # Gather enable + weight for all types (built-in + existing customs)
                program_types = []
                for key in request.form:
                    if key.startswith('ptype_'):
                        slug = key[len('ptype_'):]
                        try:
                            weight = int(request.form.get(f'pweight_{slug}', 1))
                        except ValueError:
                            weight = 1
                        weight = max(1, min(10, weight))
                        program_types.append((slug, weight))

                # Descriptions (per-type textareas)
                descriptions = {}
                for key in request.form:
                    if key.startswith('desc_'):
                        slug = key[len('desc_'):]
                        desc = request.form[key].strip()
                        if len(desc) > 500:
                            errors.append(f"Description for '{slug}' is over 500 characters.")
                            continue
                        if desc:
                            descriptions[slug] = desc

                # Update custom-type category + core flags from existing rows
                for slug in list(custom_types.keys()):
                    cat = request.form.get(f'custom_cat_{slug}', '').strip() or None
                    if cat and cat not in CATEGORIES:
                        errors.append(f"Invalid category '{cat}' for '{slug}'.")
                        cat = custom_types[slug].get('category')
                    custom_types[slug] = {
                        'description': descriptions.get(slug, custom_types[slug].get('description', '')),
                        'category': cat,
                        'core': f'custom_core_{slug}' in request.form,
                    }

                # --- Add new custom type -----------------------------------
                new_slug = (request.form.get('new_slug') or '').strip().lower()
                new_desc = (request.form.get('new_desc') or '').strip()
                new_cat = (request.form.get('new_cat') or '').strip() or None
                new_core = 'new_core' in request.form

                if new_slug or new_desc:
                    if not new_slug:
                        errors.append("New custom type needs a slug.")
                    elif not _valid_slug(new_slug):
                        errors.append("Slug must be lowercase letters, digits, or underscores (1-40 chars).")
                    elif new_slug in builtin_set:
                        errors.append(f"Slug '{new_slug}' collides with a built-in type.")
                    elif new_slug in custom_types:
                        errors.append(f"Custom type '{new_slug}' already exists.")
                    elif not new_desc:
                        errors.append("New custom type needs a description.")
                    elif len(new_desc) > 500:
                        errors.append("New description is over 500 characters.")
                    elif new_cat and new_cat not in CATEGORIES:
                        errors.append(f"Invalid category '{new_cat}'.")
                    else:
                        custom_types[new_slug] = {
                            'description': new_desc,
                            'category': new_cat,
                            'core': new_core,
                        }
                        descriptions[new_slug] = new_desc
                        # Enabled by default with weight 1
                        if not any(t == new_slug for t, _ in program_types):
                            program_types.append((new_slug, 1))

                # Canvas constraints
                try:
                    canvas_constraints = {
                        'width': int(request.form.get('canvas_width', 416)),
                        'height': int(request.form.get('canvas_height', 218)),
                        'sleep': float(request.form.get('canvas_sleep', 0.1)),
                    }
                except ValueError:
                    errors.append("Canvas constraints must be numeric.")
                    canvas_constraints = current.get('CANVAS_CONSTRAINTS')

                if errors:
                    message = " ".join(errors)
                    message_type = 'error'
                else:
                    updates = {
                        'PROGRAM_TYPES': program_types,
                        'PROGRAM_DESCRIPTIONS': descriptions,
                        'CUSTOM_PROGRAM_TYPES': custom_types,
                        'CANVAS_CONSTRAINTS': canvas_constraints,
                    }
                    config_mgr.save_overrides(updates)
                    message = "Saved! Changes apply on the next program cycle."

        # --- Render ---------------------------------------------------------
        current = config_mgr.get_all()
        enabled_weights = dict(current.get('PROGRAM_TYPES') or [])
        custom_types = current.get('CUSTOM_PROGRAM_TYPES') or {}
        # Merged view: overrides on top of built-in defaults
        descriptions = dict(DEFAULT_DESCRIPTIONS)
        descriptions.update(current.get('PROGRAM_DESCRIPTIONS') or {})

        return render_template('prompt.html',
                             core_slugs=core_slugs,
                             creative_slugs=creative_slugs,
                             enabled_weights=enabled_weights,
                             custom_types=custom_types,
                             descriptions=descriptions,
                             defaults=DEFAULT_DESCRIPTIONS,
                             categories=category_names,
                             config=current,
                             message=message,
                             message_type=message_type)

    return app


_SLUG_RE = re.compile(r'^[a-z0-9_]{1,40}$')


def _valid_slug(slug: str) -> bool:
    return bool(_SLUG_RE.match(slug))


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
