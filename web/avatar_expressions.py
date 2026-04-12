from collections import OrderedDict

__all__ = [
    "AVATAR_BLINK_PIXELS",
    "AVATAR_EXPRESSIONS",
    "AVATAR_HEAD_PIXELS",
    "MOOD_ORDER",
]


MOOD_ORDER = (
    "hopeful",
    "focused",
    "curious",
    "proud",
    "frustrated",
    "tired",
    "playful",
    "determined",
)


def _pixels(*rows: str) -> list[int]:
    if len(rows) != 8:
        raise ValueError("Avatar expressions must use exactly 8 rows")

    pixels = []
    for row_index, row in enumerate(rows):
        if len(row) != 8:
            raise ValueError("Avatar expression rows must be exactly 8 columns wide")
        for column_index, char in enumerate(row):
            if char == "#":
                pixels.append((row_index * 8) + column_index)
            elif char != ".":
                raise ValueError("Avatar expressions may only use '#' or '.'")

    return sorted(pixels)


AVATAR_HEAD_PIXELS = _pixels(
    "........",
    ".#....#.",
    "..#####.",
    "..#...#.",
    "..#...#.",
    "...##...",
    "........",
    "........",
)

AVATAR_BLINK_PIXELS = _pixels(
    "........",
    "........",
    "..#####.",
    "........",
    "........",
    "........",
    "........",
    "........",
)

AVATAR_EXPRESSIONS = OrderedDict(
    (
        mood,
        _pixels(*rows),
    )
    for mood, rows in (
        (
            "hopeful",
            (
                "........",
                ".#....#.",
                "..#####.",
                "..#...#.",
                "..#...#.",
                "...##...",
                "..#..#..",
                "........",
            ),
        ),
        (
            "focused",
            (
                "........",
                ".#....#.",
                "..#####.",
                "..#...#.",
                "..#...#.",
                "..###...",
                "........",
                "........",
            ),
        ),
        (
            "curious",
            (
                "........",
                ".#....#.",
                "..#####.",
                "..#...#.",
                "..#...#.",
                "...##...",
                "........",
                "........",
            ),
        ),
        (
            "proud",
            (
                "........",
                ".#....#.",
                "..#####.",
                "..#...#.",
                "..#...#.",
                "...###..",
                "........",
                "........",
            ),
        ),
        (
            "frustrated",
            (
                "........",
                ".#....#.",
                "..#####.",
                "..#...#.",
                "..#...#.",
                "...##...",
                "..####..",
                "........",
            ),
        ),
        (
            "tired",
            (
                "........",
                ".#....#.",
                "..#####.",
                "..#...#.",
                "..#...#.",
                "...##...",
                "...##...",
                "........",
            ),
        ),
        (
            "playful",
            (
                "........",
                ".#....#.",
                "..#####.",
                "..#...#.",
                "..#...#.",
                "..####..",
                "..#...#.",
                "........",
            ),
        ),
        (
            "determined",
            (
                "........",
                ".#....#.",
                "..#####.",
                "..#...#.",
                "..#...#.",
                "...##...",
                "..#.#.#.",
                "........",
            ),
        ),
    )
)
