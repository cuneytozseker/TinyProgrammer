"""Run canvas_function_v1 sketches in a subprocess."""

from __future__ import annotations

import os
import sys
import time
import traceback


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAMS_DIR = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if PROGRAMS_DIR not in sys.path:
    sys.path.insert(0, PROGRAMS_DIR)

from programmer.canvas_protocol import encode_frame_packet
from programmer.program_source import (
    validate_canvas_function_source,
    validate_canvas_runtime_namespace,
)
from tiny_canvas import CANVAS_FRAME_PACKET_PROTOCOL, CANVAS_PROTOCOL_ENV, Canvas


def clamp_dt(last_time: float, now: float, max_dt: float) -> float:
    """Return a non-negative, clamped delta time."""
    return max(0.0, min(now - last_time, max_dt))


def load_sketch(source_path: str) -> dict:
    """Validate and execute a sketch module, returning its globals."""
    with open(source_path, "r", encoding="utf-8") as source_file:
        source = source_file.read()

    validate_canvas_function_source(source)
    namespace = {
        "__name__": "__tiny_sketch__",
        "__file__": source_path,
    }
    code = compile(source, source_path, "exec")
    exec(code, namespace)
    validate_canvas_runtime_namespace(namespace)
    return namespace


def emit_frame(protocol_stream, frame: dict) -> None:
    """Write one complete frame packet to the protocol stream."""
    packet = encode_frame_packet(frame)
    protocol_stream.write(packet)
    protocol_stream.flush()


def run(source_path: str) -> int:
    """Run a sketch module until the parent process terminates us."""
    protocol_stream = sys.stdout.buffer
    sys.stdout = sys.stderr

    os.environ[CANVAS_PROTOCOL_ENV] = CANVAS_FRAME_PACKET_PROTOCOL
    width = int(os.environ.get("TINY_CANVAS_W", 416))
    height = int(os.environ.get("TINY_CANVAS_H", 218))
    target_fps = max(1.0, float(os.environ.get("TINY_TARGET_FPS", "30")))
    max_dt = max(0.001, float(os.environ.get("TINY_DT_MAX", "0.1")))
    frame_interval = 1.0 / target_fps

    namespace = load_sketch(source_path)
    setup = namespace.get("setup")
    draw = namespace["draw"]

    canvas = Canvas(width, height)
    state = setup(canvas) if setup else {}
    if state is None:
        state = {}

    frame_id = 0
    start_time = time.monotonic()
    last_time = start_time
    next_frame_time = start_time

    while True:
        now = time.monotonic()
        if now < next_frame_time:
            time.sleep(next_frame_time - now)
            now = time.monotonic()

        dt = clamp_dt(last_time, now, max_dt)
        t = now - start_time
        last_time = now

        canvas.begin_frame()
        draw(canvas, state, t, dt)
        commands = canvas.consume_commands()

        frame = {
            "protocol": CANVAS_FRAME_PACKET_PROTOCOL,
            "frame": frame_id,
            "width": canvas.width,
            "height": canvas.height,
            "t": t,
            "dt": dt,
            "commands": commands,
        }
        emit_frame(protocol_stream, frame)

        frame_id += 1
        next_frame_time += frame_interval
        if next_frame_time < time.monotonic() - frame_interval:
            next_frame_time = time.monotonic()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: tiny_runner.py <source.py>", file=sys.stderr)
        return 2
    try:
        return run(argv[1])
    except KeyboardInterrupt:
        return 0
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
