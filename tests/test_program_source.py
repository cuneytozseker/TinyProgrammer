from archive.repository import ProgramMetadata, Repository
from program_source import is_generated_wrapper_line, sanitize_generated_code


def _metadata(filename: str, success: bool = True) -> ProgramMetadata:
    return ProgramMetadata(
        id=filename,
        filename=filename,
        program_type="test",
        created_at="2026-01-01T00:00:00",
        mood="quiet",
        success=success,
        lines_of_code=1,
        thought_process="",
    )


def test_selects_fenced_code_over_prose():
    code, _ = sanitize_generated_code(
        "Here\n```python\nprint('ok')\n```\nThanks\n"
    )

    assert code == "print('ok')\n"


def test_keeps_setup_prefix_before_fenced_body():
    raw = (
        "import time\n"
        "from tiny_canvas import Canvas\n"
        "c = Canvas()\n"
        "```python\n"
        "c.clear()\n"
        "```\n"
    )

    code, _ = sanitize_generated_code(raw)

    assert code == (
        "import time\n"
        "from tiny_canvas import Canvas\n"
        "c = Canvas()\n"
        "c.clear()\n"
    )


def test_ignores_non_setup_prefix_before_fenced_body():
    raw = (
        "helper = make_setup()\n"
        "```python\n"
        "print('ok')\n"
        "```\n"
    )

    code, _ = sanitize_generated_code(raw)

    assert code == "print('ok')\n"


def test_preserves_unfenced_prose_for_review_or_fix():
    raw = (
        "Here is the code:\nprint('ok')\nThat is all.\n"
    )

    code, _ = sanitize_generated_code(raw)

    assert code == raw


def test_does_not_rescue_middle_prose():
    raw = "x = 1\nThat is all.\ny = 2\n"

    code, _ = sanitize_generated_code(raw)

    assert code == raw


def test_preserves_edge_assignments_that_look_like_prose_words():
    raw = (
        "this = 1\n"
        "sure = True\n"
        "surely = False\n"
        "here = 3\n"
        "below = 4\n"
    )

    code, _ = sanitize_generated_code(raw)

    assert code == raw


def test_preserves_multiline_python_closing_delimiters():
    raw = (
        "points = [\n"
        "    (0, 0),\n"
        "    (1, 1),\n"
        "]\n"
        "c.line(\n"
        "    0, 0, 10, 10, 255, 255, 255\n"
        ")\n"
    )

    code, _ = sanitize_generated_code(raw)

    assert code == raw


def test_broken_code_returns_cleaned_source():
    code, diagnostics = sanitize_generated_code("python\ndef broken(:\n    pass\n")

    assert code == "def broken(:\n    pass\n"
    assert "removed language tag: python" in diagnostics


def test_removes_model_end_marker():
    code, diagnostics = sanitize_generated_code("python\nprint('ok')\n<|im_end|>\n")

    assert code == "print('ok')\n"
    assert "removed language tag: python" in diagnostics
    assert "removed model end marker" in diagnostics


def test_match_case_is_preserved():
    raw = "match value:\n    case 1:\n        print('one')\n"

    code, _ = sanitize_generated_code(raw)

    assert code == raw


def test_valid_bare_name_expressions_are_preserved():
    raw = "x = 1\nx\n"

    code, _ = sanitize_generated_code(raw)

    assert code == raw


def test_header_prefixed_prose_does_not_become_header_only():
    header = (
        "import time\n"
        "import random\n"
        "import math\n"
        "from tiny_canvas import Canvas\n"
        "\n"
        "c = Canvas()\n"
    )
    raw = header + "Here is the code:\nc.clear(0, 0, 0)\nc.show()\n"

    code, _ = sanitize_generated_code(raw)

    assert code != header
    assert "Here is the code:" in code
    assert "c.clear(0, 0, 0)" in code


def test_wrapper_line_detection():
    assert is_generated_wrapper_line("```python")
    assert is_generated_wrapper_line("python3")
    assert is_generated_wrapper_line("<|im_end|>")
    assert not is_generated_wrapper_line("print('ok')")


def test_replay_candidates_sanitize_wrapped_archive_sources(tmp_path):
    repo = Repository(str(tmp_path))
    programs_dir = tmp_path / "programs"

    (programs_dir / "legacy.py").write_text(
        "```python\nprint('ok')\n```\n",
        encoding="utf-8",
    )
    (programs_dir / "broken.py").write_text(
        (
            "python\n"
            "def main():\n"
            "    grid = [\n"
            "        [0, 1],\n"
            "        [1, 0],\n"
            "    ]\n"
            "\n"
            "    while True:\n"
            "        live_neighbors = sum(1 for r, c in ((0, 1), (1, 0))\n"
            "        print(live_neighbors)\n"
        ),
        encoding="utf-8",
    )
    (programs_dir / "failed.py").write_text(
        "print('not a successful archive entry')\n",
        encoding="utf-8",
    )

    repo.index = [
        _metadata("legacy.py"),
        _metadata("broken.py"),
        _metadata("failed.py", success=False),
    ]

    assert repo.get_replay_candidates() == [repo.index[0]]
