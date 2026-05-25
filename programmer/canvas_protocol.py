"""Frame-packet protocol for buffered canvas sketches."""

from __future__ import annotations

import json


FRAME_PREFIX = b"FRAME:"
MAX_FRAME_BYTES = 4 * 1024 * 1024


class FramePacketParser:
    """Incrementally parse length-prefixed JSON canvas frames."""

    def __init__(self):
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[dict]:
        """Feed bytes and return every complete frame parsed so far."""
        if not data:
            return []

        self._buffer.extend(data)
        frames: list[dict] = []

        while True:
            prefix_index = self._buffer.find(FRAME_PREFIX)
            if prefix_index < 0:
                keep = max(0, len(FRAME_PREFIX) - 1)
                if len(self._buffer) > keep:
                    del self._buffer[:-keep]
                break
            if prefix_index > 0:
                del self._buffer[:prefix_index]

            header_end = self._buffer.find(b"\n", len(FRAME_PREFIX))
            if header_end < 0:
                break

            raw_length = bytes(self._buffer[len(FRAME_PREFIX):header_end])
            if not raw_length.isdigit():
                self._discard_bad_prefix()
                continue

            length = int(raw_length)
            if length < 0 or length > MAX_FRAME_BYTES:
                self._discard_bad_prefix()
                continue

            payload_start = header_end + 1
            payload_end = payload_start + length
            if len(self._buffer) < payload_end:
                break

            payload = bytes(self._buffer[payload_start:payload_end])

            try:
                frame = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._discard_bad_prefix()
                continue

            del self._buffer[:payload_end]
            frames.append(frame)

        return frames

    def _discard_bad_prefix(self) -> None:
        """Discard only the current bad prefix so parsing can resync."""
        del self._buffer[:len(FRAME_PREFIX)]


def encode_frame_packet(frame: dict) -> bytes:
    """Encode one frame as a length-prefixed JSON packet."""
    payload = json.dumps(frame, separators=(",", ":")).encode("utf-8")
    return FRAME_PREFIX + str(len(payload)).encode("ascii") + b"\n" + payload
