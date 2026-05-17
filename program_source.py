"""Generated program source handling."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from types import CodeType


_FENCED_BLOCK_RE = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,})[ \t]*(?P<info>[^\n]*)\n"
    r"(?P<body>.*?)"
    r"\n^[ \t]*(?P=fence)[ \t]*$",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
_FENCE_LINE_RE = re.compile(r"^\s*(?:`{3,}|~{3,})(?:[^\n]*)?$", re.IGNORECASE)
_LANG_TAG_LINE_RE = re.compile(r"^\s*(?:python|py|python3)\s*$", re.IGNORECASE)
_MODEL_END_LINE_RE = re.compile(r"^\s*<\|im_end\|>\s*$")


@dataclass(frozen=True)
class ProgramSource:
    """Raw and executable forms of one generated Python program."""

    raw: str
    code: str
    diagnostics: tuple[str, ...] = ()

    @classmethod
    def empty(cls) -> "ProgramSource":
        """Build an empty source object before generation starts."""
        return cls(raw="", code="", diagnostics=())

    @classmethod
    def from_generated(cls, raw: str) -> "ProgramSource":
        """Keep the original response beside the sanitized program text."""
        code, diagnostics = sanitize_generated_code(raw)
        return cls(raw=raw, code=code, diagnostics=tuple(diagnostics))

    def compile(self, filename: str = "<generated>") -> CodeType:
        """Compile the executable source."""
        return compile(self.code, filename, "exec")


def sanitize_generated_code(raw: str) -> tuple[str, list[str]]:
    """Return executable Python from an LLM response or archived source."""
    text = (raw or "").replace("\r\n", "\n").replace("\r", "\n")
    diagnostics: list[str] = []
    if "<|im_end|>" in text:
        text = text.replace("<|im_end|>", "")
        diagnostics.append("removed model end marker")

    cleaned, clean_diags = _drop_wrapper_lines(text)
    candidates = _fenced_candidates(text)
    candidates.append((cleaned, clean_diags))

    for candidate, diags in candidates:
        code = _finish(candidate)
        if code and _compiles_as_program(code):
            return code, diagnostics + diags

    trimmed = _trim_to_compiling(cleaned)
    if trimmed and _finish(trimmed[0]) != _finish(cleaned):
        code = _finish(trimmed[0])
        if code and _compiles_as_program(code):
            return code, diagnostics + clean_diags + trimmed[1]

    fallback = _finish(cleaned)
    if fallback:
        return fallback, diagnostics + clean_diags + ["no compilable candidate"]
    if text.strip():
        return "", diagnostics + clean_diags + ["no compilable candidate"]
    return "", diagnostics + clean_diags


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
        prefix, prefix_diags = _drop_wrapper_lines(text[:match.start()])
        if _looks_like_setup(prefix):
            candidates.append((_join(prefix, body), prefix_diags + body_diags + [f"{label} with prefix"]))
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


def _trim_to_compiling(text: str) -> tuple[str, list[str]] | None:
    """Find the smallest leading/trailing trim that leaves a program."""
    lines = text.split("\n")
    best = None
    for start in range(len(lines)):
        for end in range(start + 1, len(lines) + 1):
            candidate = "\n".join(lines[start:end])
            if _finish(candidate) == _finish(text):
                continue
            if _compiles_as_program(_finish(candidate)):
                score = (start + len(lines) - end, start, start - end)
                if best is None or score < best[0]:
                    best = (score, start, end, candidate)
    if best is None:
        return None

    _, start, end, candidate = best
    diagnostics = ["selected compilable line slice"]
    if start:
        diagnostics.append("removed leading prose")
    if end < len(lines):
        diagnostics.append("removed trailing prose")
    return candidate, diagnostics


def _compiles_as_program(text: str) -> bool:
    """Return whether text parses as a non-empty Python program."""
    if not text:
        return False
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, TypeError):
        return False
    if not tree.body:
        return False
    return True


def _looks_like_setup(text: str) -> bool:
    """Return whether a prefix looks like reusable setup code."""
    if not _compiles_as_program(_finish(text)):
        return False
    return any(
        line.strip().startswith(("import ", "from ", "def ", "class "))
        or ("=" in line and not line.strip().startswith("#"))
        for line in text.splitlines()
    )


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
