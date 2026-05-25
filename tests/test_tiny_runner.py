import io
import os
import tempfile
import unittest

from programmer.canvas_protocol import FramePacketParser
from programmer.program_source import ProgramSourceError
from programs.tiny_canvas import CANVAS_FRAME_PACKET_PROTOCOL
from programs.tiny_runner import clamp_dt, emit_frame, load_sketch


class TinyRunnerTests(unittest.TestCase):
    def test_clamp_dt(self):
        self.assertEqual(clamp_dt(10.0, 9.0, 0.1), 0.0)
        self.assertAlmostEqual(clamp_dt(10.0, 10.05, 0.1), 0.05)
        self.assertEqual(clamp_dt(10.0, 11.0, 0.1), 0.1)

    def test_emit_frame_writes_parseable_packet(self):
        stream = io.BytesIO()
        frame = {
            "protocol": CANVAS_FRAME_PACKET_PROTOCOL,
            "frame": 3,
            "commands": [["CLEAR", 0, 0, 0]],
        }

        emit_frame(stream, frame)

        self.assertEqual(FramePacketParser().feed(stream.getvalue()), [frame])

    def test_load_sketch_rejects_reassigned_draw(self):
        source = (
            "def draw(c, state, t, dt):\n"
            "    c.clear(0, 0, 0)\n"
            "draw = None\n"
        )

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as temp:
            temp.write(source)
            temp_path = temp.name

        try:
            with self.assertRaisesRegex(ProgramSourceError, "draw must be callable"):
                load_sketch(temp_path)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
