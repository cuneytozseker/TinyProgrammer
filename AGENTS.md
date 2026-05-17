# AGENTS.md

This is the authoritative project guidance for coding agents working in this
repo. Keep it concise and repo-specific. Do not add personal device
credentials, API keys, or one-off troubleshooting history here.

## Project Shape

TinyProgrammer is a long-running Python 3.11+ application that:

- renders a retro IDE UI with Pygame
- generates short Python programs through an LLM
- runs, watches, and archives generated programs
- exposes a Flask dashboard for monitoring and live configuration
- supports Raspberry Pi framebuffer output, desktop Pygame fallback, and
  headless Docker/dashboard operation

## Working Setup

Use the repo root as the working directory.

Typical local setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Typical local run:

```bash
python3 main.py
```

Typical Docker run:

```bash
cp .env.example .env
docker compose up --build
```

Important notes:

- `OPENROUTER_API_KEY` is required unless `LLM_MODEL` is set to an
  `ollama/...` model.
- The local app serves Flask on port `5000`; Docker publishes it on `5001`.
- Avoid `start.sh` during development. It runs `git pull`, `sudo pkill`, and
  `sudo python3 main.py`, which is unsafe for normal feature work.

## Architecture Map

- `main.py`: true entry point. Loads `.env` before importing `config`, then
  initializes `Terminal`, `LLMGenerator`, `Brain`, archive, BBS, and web server.
- `config.py`: default settings for display profiles, LLMs, schedule, BBS,
  reminisce, and web flags.
- `programmer/brain.py`: main state machine
  (`THINK -> WRITE -> REVIEW -> RUN -> WATCH -> ARCHIVE -> REFLECT -> repeat`,
  with `FIX` on failures and optional `BBS_BREAK -> REMINISCE` after reflect).
- `programmer/reminiscence.py`: archive replay selection and intro text for
  optional `REMINISCE` sessions.
- `llm/generator.py`: model registry, OpenRouter/Ollama routing, and prompt
  construction.
- `display/`: Pygame terminal renderer, screensaver, framebuffer writer, and
  stream support.
- `web/app.py`: Flask dashboard and JSON endpoints.
- `web/config_manager.py`: persists dashboard edits and applies them to the
  live `config` module.
- `archive/`: program archive metadata and long-term lessons journal.
- `bbs/`: TinyBBS client and social break support.

## Runtime Data And Generated Files

This repo mixes source files and runtime output. Be careful.

- `programs/tiny_canvas.py` and `programs/tiny_plot3d.py` are source files used
  by generated sketches.
- `programs/index.json` is archive metadata.
- archived generated programs are written to `programs/programs/`.
- transient execution output is written to `programs/temp_execution.py`.
- `lessons.md`, `config_overrides.json`, and `liked_programs.json` are mutable
  runtime files at repo root in non-Docker runs.

Docker changes that layout:

- `entrypoint.sh` creates `/app/runtime/lessons.md`,
  `/app/runtime/config_overrides.json`, and `/app/runtime/liked_programs.json`.
- those files are symlinked back into `/app/` so the Python code still reads
  root-level paths.
- the Docker archive still lives under `/app/programs`.

Practical consequence:

- letting the app run in the main worktree can modify tracked archive files
  under `programs/`.
- prefer short smoke tests, a disposable clone, or a Docker volume reset if you
  do not want archive churn in the repo.

## Codebase Rules

- Preserve `.env` load order in `main.py`. `config.py` reads environment
  variables at import time.
- Dashboard-editable default settings belong in `config.py` and must be
  JSON-serializable for `config_overrides.json`; prompt-editor dynamic values
  may be override-only when consumers read them with `getattr`.
- The dashboard model picker is driven from `llm/generator.py`; add models
  there, not only in templates.
- `programmer/brain.py` duplicates generated-code cleaning across review and
  run paths. Update both when changing sanitation rules.
- Generated programs are intentionally restricted. `_do_review()` rejects
  `pygame`, `turtle`, `tkinter`, and `matplotlib`.

Do:

- use existing patterns and keep edits focused.
- keep Raspberry Pi and framebuffer changes minimal, reproducible, and clearly
  tied to hardware behavior.
- prefer structured parsers/APIs over ad hoc string manipulation when practical.

Do not:

- hand-edit generated/runtime files unless the task explicitly concerns runtime
  state.
- add heavyweight dependencies or broad refactors without clear user intent.
- assume desktop display behavior matches Pi framebuffer behavior.

## Verification

There is no automated test suite in this repo today. Prefer targeted checks:

- syntax/import-sensitive changes:
  `python3 -m py_compile main.py config.py display/framebuffer.py display/terminal.py programmer/brain.py`
- script edits: `bash -n <script>`
- dashboard changes: verify `/`, `/settings`, `/prompt`, and relevant `/api/*`
  endpoints.
- Docker-specific changes: verify `docker compose up --build` and confirm the
  dashboard at `http://localhost:5001`.
- Pi/framebuffer changes: review `display/framebuffer.py` and
  `display/terminal.py` together; validate on hardware when behavior matters.

Avoid long unattended app runs when the change does not require the full LLM
loop, because the application continuously mutates archive state.

## Maintenance

- Update this file when setup commands, runtime file layout, hardware support,
  dashboard endpoints, or verification commands change.
- Remove stale experiment notes instead of preserving investigation history.
- Prefer pointers to README/docs for long explanations; keep `AGENTS.md` as
  project orientation and durable editing guidance.
