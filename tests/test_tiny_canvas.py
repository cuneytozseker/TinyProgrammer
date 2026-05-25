import contextlib
import io
import os
import unittest

from programmer.program_source import CANVAS_FUNCTION_PROTOCOL
from programs.tiny_canvas import (
    CANVAS_FRAME_PACKET_PROTOCOL,
    CANVAS_PROTOCOL_ENV,
    Canvas,
)


@contextlib.contextmanager
def canvas_protocol(value):
    previous = os.environ.get(CANVAS_PROTOCOL_ENV)
    if value is None:
        os.environ.pop(CANVAS_PROTOCOL_ENV, None)
    else:
        os.environ[CANVAS_PROTOCOL_ENV] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(CANVAS_PROTOCOL_ENV, None)
        else:
            os.environ[CANVAS_PROTOCOL_ENV] = previous


class TinyCanvasTests(unittest.TestCase):
    def test_buffered_canvas_collects_commands(self):
        with canvas_protocol(CANVAS_FRAME_PACKET_PROTOCOL):
            canvas = Canvas(10, 10)
            canvas.clear(1, 2, 3)
            canvas.line(0, 1, 2, 3, 4, 5, 6)

            self.assertEqual(
                canvas.consume_commands(),
                [["CLEAR", 1, 2, 3], ["LINE", 0, 1, 2, 3, 4, 5, 6]],
            )
            self.assertEqual(canvas.consume_commands(), [])

    def test_legacy_sleep_flushes_dirty_frame(self):
        with canvas_protocol(None):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                canvas = Canvas(10, 10)
                canvas.clear(1, 2, 3)
                canvas.sleep(0)

        self.assertEqual(stream.getvalue(), 'CMDS:[["CLEAR",1,2,3]]\nCMD:FLIP\n')

    def test_canvas_frame_packet_protocol_matches_runtime_protocol(self):
        self.assertEqual(CANVAS_FRAME_PACKET_PROTOCOL, CANVAS_FUNCTION_PROTOCOL)


if __name__ == "__main__":
    unittest.main()
