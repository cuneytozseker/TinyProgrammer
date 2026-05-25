import unittest

from programmer.canvas_protocol import FramePacketParser, encode_frame_packet


class FramePacketParserTests(unittest.TestCase):
    def test_split_packet_does_not_parse_until_complete(self):
        frame = {
            "protocol": "canvas_function_v1",
            "frame": 1,
            "commands": [["CLEAR", 0, 0, 0], ["PIXEL", 1, 2, 255, 255, 255]],
        }
        packet = encode_frame_packet(frame)
        parser = FramePacketParser()

        self.assertEqual(parser.feed(packet[:5]), [])
        self.assertEqual(parser.feed(packet[5:20]), [])
        self.assertEqual(parser.feed(packet[20:]), [frame])

    def test_noise_before_packet_is_ignored(self):
        frame = {"protocol": "canvas_function_v1", "frame": 2, "commands": []}
        parser = FramePacketParser()

        self.assertEqual(parser.feed(b"log line\n" + encode_frame_packet(frame)), [frame])

    def test_false_prefix_before_packet_resyncs(self):
        frame = {"protocol": "canvas_function_v1", "frame": 3, "commands": []}
        parser = FramePacketParser()

        self.assertEqual(parser.feed(b"log FRAME:"), [])
        self.assertEqual(parser.feed(encode_frame_packet(frame)), [frame])

    def test_malformed_header_between_packets_is_dropped(self):
        first = {"protocol": "canvas_function_v1", "frame": 4, "commands": []}
        second = {"protocol": "canvas_function_v1", "frame": 5, "commands": []}
        parser = FramePacketParser()

        data = (
            encode_frame_packet(first)
            + b"FRAME:not-a-length\n"
            + encode_frame_packet(second)
        )

        self.assertEqual(parser.feed(data), [first, second])

    def test_invalid_json_packet_is_dropped(self):
        frame = {"protocol": "canvas_function_v1", "frame": 6, "commands": []}
        parser = FramePacketParser()

        data = b"FRAME:5\nabcde" + encode_frame_packet(frame)

        self.assertEqual(parser.feed(data), [frame])


if __name__ == "__main__":
    unittest.main()
