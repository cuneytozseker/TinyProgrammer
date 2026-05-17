from program_source import is_generated_wrapper_line, sanitize_generated_code


def test_selects_fenced_code_over_prose():
    code, _ = sanitize_generated_code(
        "Here\n```python\nprint('ok')\n```\nThanks\n"
    )

    assert code == "print('ok')\n"


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


def test_wrapper_line_detection():
    assert is_generated_wrapper_line("```python")
    assert is_generated_wrapper_line("python3")
    assert is_generated_wrapper_line("<|im_end|>")
    assert not is_generated_wrapper_line("print('ok')")
