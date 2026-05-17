"""Generated program source handling."""

from __future__ import annotations

import re


_FENCED_BLOCK_RE = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,})[ \t]*(?P<info>[^\n]*)\n"
    r"(?P<body>.*?)"
    r"\n^[ \t]*(?P=fence)[ \t]*$",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
_FENCE_LINE_RE = re.compile(r"^\s*(?:`{3,}|~{3,})(?:[^\n]*)?$", re.IGNORECASE)
_LANG_TAG_LINE_RE = re.compile(r"^\s*(?:python|py|python3)\s*$", re.IGNORECASE)
_MODEL_END_LINE_RE = re.compile(r"^\s*<\|im_end\|>\s*$")
_GENERATED_SETUP_LINES = {
    "import time",
    "import random",
    "import math",
    "from tiny_canvas import Canvas",
    "c = Canvas()",
    "from tiny_plot3d import Plot3D",
    "p = Plot3D(c)",
}


def sanitize_generated_code(raw: str) -> tuple[str, list[str]]:
    """Return executable Python from an LLM response or archived source."""
    text = (raw or "").replace("\r\n", "\n").replace("\r", "\n")
    diagnostics: list[str] = []
    if "<|im_end|>" in text:
        text = text.replace("<|im_end|>", "")
        diagnostics.append("removed model end marker")

    candidates = _fenced_candidates(text)
    if candidates:
        candidate, candidate_diags = candidates[0]
        return _finish(candidate), diagnostics + candidate_diags

    cleaned, clean_diags = _drop_wrapper_lines(text)
    return _finish(cleaned), diagnostics + clean_diags


def is_generated_wrapper_line(line: str) -> bool:
    """Return whether a line is generated response wrapper text."""
    stripped = line.strip()
    return bool(
        _FENCE_LINE_RE.match(stripped)
        or _LANG_TAG_LINE_RE.match(stripped)
        or _MODEL_END_LINE_RE.match(stripped)
    )


def _fenced_candidates(text: str) -> list[tuple[str, list[str]]]:
    """Return complete markdown fence bodies, with Python fences first."""
    matches = list(_FENCED_BLOCK_RE.finditer(text))
    matches.sort(key=lambda m: 0 if _is_python_fence(m.group("info")) else 1)

    candidates = []
    for match in matches:
        label = "selected python fenced code block" if _is_python_fence(match.group("info")) else "selected fenced code block"
        body, body_diags = _drop_wrapper_lines(match.group("body"))
        prefix = _generated_setup_prefix(text[:match.start()])
        if prefix:
            candidates.append((_join(prefix[0], body), prefix[1] + body_diags + [f"{label} with prefix"]))
        candidates.append((body, body_diags + [label]))
    return candidates


def _drop_wrapper_lines(text: str) -> tuple[str, list[str]]:
    """Remove wrapper-only lines while preserving the remaining source text."""
    diagnostics: list[str] = []
    lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if _FENCE_LINE_RE.match(stripped):
            diagnostics.append("removed markdown fence")
        elif _LANG_TAG_LINE_RE.match(stripped):
            diagnostics.append(f"removed language tag: {stripped}")
        elif _MODEL_END_LINE_RE.match(stripped):
            diagnostics.append("removed model end marker")
        else:
            lines.append(line)
    return "\n".join(lines), diagnostics


def _generated_setup_prefix(text: str) -> tuple[str, list[str]] | None:
    """Return known generated setup code if a fence prefix contains only that."""
    prefix, diagnostics = _drop_wrapper_lines(text)
    lines = prefix.split("\n")
    kept = [line for line in lines if line.strip()]
    if not kept:
        return None
    if all(line.strip() in _GENERATED_SETUP_LINES for line in kept):
        return prefix, diagnostics
    return None


def _is_python_fence(info: str) -> bool:
    """Return whether a markdown fence info string names Python."""
    tokens = {token.lstrip(".") for token in re.split(r"[\s{}]+", info.lower().strip()) if token}
    return bool(tokens & {"python", "py", "python3"})


def _join(prefix: str, body: str) -> str:
    """Join two source fragments without introducing extra blank edges."""
    prefix = _trim_blank(prefix)
    body = _trim_blank(body)
    if prefix and body:
        return prefix + "\n" + body
    return prefix or body


def _finish(text: str) -> str:
    """Normalize source edges and keep a final newline for file output."""
    text = _trim_blank(text)
    return text + "\n" if text else ""


def _trim_blank(text: str) -> str:
    """Trim blank lines without changing indentation inside the source."""
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)
