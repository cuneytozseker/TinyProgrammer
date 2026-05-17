import program_source
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


def test_trims_prose_only_to_compiling_code():
    code, _ = sanitize_generated_code(
        "Here is the code:\nprint('ok')\nThat is all.\n"
    )

    assert code == "print('ok')\n"


def test_broken_code_falls_back_to_cleaned_source():
    code, diagnostics = sanitize_generated_code("python\ndef broken(:\n    pass\n")

    assert code == "def broken(:\n    pass\n"
    assert "no compilable candidate" in diagnostics


def test_match_case_is_preserved():
    raw = "match value:\n    case 1:\n        print('one')\n"

    code, _ = sanitize_generated_code(raw)

    assert code == raw


def test_valid_bare_name_expressions_are_preserved():
    raw = "x = 1\nx\n"

    code, _ = sanitize_generated_code(raw)

    assert code == raw


def test_valid_full_response_does_not_scan_line_slices(monkeypatch):
    def fail_if_called(_text):
        raise AssertionError("line slice scan should not run")

    monkeypatch.setattr(program_source, "_trim_to_compiling", fail_if_called)

    code, _ = program_source.sanitize_generated_code("print('ok')\n")

    assert code == "print('ok')\n"


def test_wrapper_line_detection():
    assert is_generated_wrapper_line("```python")
    assert is_generated_wrapper_line("python3")
    assert is_generated_wrapper_line("<|im_end|>")
    assert not is_generated_wrapper_line("print('ok')")


def test_replay_candidates_sanitize_legacy_archive_sources(tmp_path):
    repo = Repository(str(tmp_path))
    programs_dir = tmp_path / "programs"

    (programs_dir / "legacy.py").write_text(
        "Here is the code:\nprint('ok')\nThat is all.\n",
        encoding="utf-8",
    )
    (programs_dir / "broken.py").write_text(
        "def broken(:\n    pass\n",
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
