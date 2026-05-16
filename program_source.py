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
_CODE_START_RE = re.compile(
    r"^\s*(?:"
    r"#|"
    r"@[A-Za-z_][A-Za-z0-9_]*(?:\.|\(|\s|$)|"
    r"import\s+|"
    r"from\s+|"
    r"class\s+|"
    r"def\s+|"
    r"async\s+def\s+|"
    r"for\s+|"
    r"while\s+|"
    r"if\s+|"
    r"try\s*:|"
    r"with\s+|"
    r"(?:[A-Za-z_][A-Za-z0-9_]*\s*,\s*)+[A-Za-z_][A-Za-z0-9_]*\s*=|"
    r"[A-Za-z_][A-Za-z0-9_]*\s*=|"
    r"[A-Za-z_][A-Za-z0-9_]*\s*\(|"
    r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_]"
    r")"
)


@dataclass(frozen=True)
class ProgramSource:
    """Raw and executable forms of one generated Python program."""

    raw: str
    code: str
    diagnostics: tuple[str, ...] = ()

    @classmethod
    def empty(cls) -> "ProgramSource":
        return cls(raw="", code="", diagnostics=())

    @classmethod
    def from_generated(cls, raw: str) -> "ProgramSource":
        code, diagnostics = sanitize_generated_code(raw)
        return cls(raw=raw, code=code, diagnostics=tuple(diagnostics))

    def ast_tree(self) -> ast.Module:
        """Parse the executable source for future structural review work."""
        return ast.parse(self.code)

    def compile(self, filename: str = "<generated>") -> CodeType:
        """Compile the executable source."""
        return compile(self.code, filename, "exec")


def sanitize_generated_code(raw: str) -> tuple[str, list[str]]:
    """Return executable Python from an LLM response or archived source.

    The sanitizer intentionally handles only wrapper artifacts around code:
    markdown fences, bare language tags, model end markers, and leading prose.
    It avoids rewriting Python syntax so future AST validation sees the
    generated program itself.
    """
    diagnostics: list[str] = []
    code = (raw or "").replace("\r\n", "\n").replace("\r", "\n")
    if "<|im_end|>" in code:
        code = code.replace("<|im_end|>", "")
        diagnostics.append("removed model end marker")

    code = _select_fenced_region(code, diagnostics)

    clean_lines: list[str] = []
    for line in code.split("\n"):
        stripped = line.strip()
        if _FENCE_LINE_RE.match(stripped):
            diagnostics.append("removed markdown fence")
            continue
        if _LANG_TAG_LINE_RE.match(stripped):
            diagnostics.append(f"removed language tag: {stripped}")
            continue
        if _MODEL_END_LINE_RE.match(stripped):
            diagnostics.append("removed model end marker")
            continue
        clean_lines.append(line)

    clean_lines = _drop_leading_prose(clean_lines, diagnostics)

    sanitized = "\n".join(clean_lines).strip()
    if sanitized:
        sanitized += "\n"
    return sanitized, diagnostics


def _select_fenced_region(code: str, diagnostics: list[str]) -> str:
    matches = list(_FENCED_BLOCK_RE.finditer(code))
    if not matches:
        return code

    first = matches[0]
    before = code[:first.start()]
    has_prefix_code = _contains_python_code(before)

    python_matches = [
        match for match in matches
        if _is_python_fence_info(match.group("info"))
    ]
    for match in python_matches:
        if _is_compilable_code_candidate(match.group("body")):
            diagnostics.append("selected python fenced code block")
            return _with_code_prefix(before, match.group("body"), has_prefix_code, diagnostics)

    for match in matches:
        if _is_compilable_code_candidate(match.group("body")):
            diagnostics.append("selected fenced code block")
            return _with_code_prefix(before, match.group("body"), has_prefix_code, diagnostics)

    if python_matches:
        diagnostics.append("selected python fenced code block")
        return _with_code_prefix(before, python_matches[0].group("body"), has_prefix_code, diagnostics)

    diagnostics.append("selected fenced code block")
    return _with_code_prefix(before, first.group("body"), has_prefix_code, diagnostics)


def _with_code_prefix(prefix: str, body: str, include_prefix: bool,
                      diagnostics: list[str]) -> str:
    if not include_prefix:
        return body

    clean_prefix = _clean_code_prefix(prefix)
    if clean_prefix != prefix:
        diagnostics.append("removed prose before fenced code block")
    if not clean_prefix:
        return body

    separator = "" if clean_prefix.endswith("\n") or not body else "\n"
    return clean_prefix + separator + body


def _clean_code_prefix(prefix: str) -> str:
    lines = _drop_leading_prose(prefix.split("\n"), [])
    lines = _drop_trailing_prose(lines)

    for end in range(len(lines), 0, -1):
        candidate = "\n".join(lines[:end]).strip()
        if not candidate:
            continue
        try:
            compile(candidate, "<prefix-candidate>", "exec")
        except (SyntaxError, ValueError):
            continue
        return candidate + "\n"

    candidate = "\n".join(lines).strip()
    if candidate:
        return candidate + "\n"
    return ""


def _drop_trailing_prose(lines: list[str]) -> list[str]:
    trimmed = list(lines)
    while trimmed:
        if _looks_like_python_line(trimmed[-1]):
            break
        trimmed.pop()
    return trimmed


def _looks_like_python_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if line[:1].isspace():
        return True
    if _CODE_START_RE.match(stripped):
        return True
    if stripped in {"else:", "except:", "finally:", "pass", "break", "continue"}:
        return True
    return stripped.startswith((
        "elif ",
        "else:",
        "except ",
        "except:",
        "finally:",
        "return ",
        "raise ",
        "yield ",
        "assert ",
        "del ",
        "global ",
        "nonlocal ",
    ))


def _is_python_fence_info(info: str) -> bool:
    tokens = re.split(r"[\s{}]+", info.lower().strip())
    languages = {token.lstrip(".") for token in tokens if token}
    return bool(languages & {"python", "py", "python3"})


def _is_compilable_code_candidate(text: str) -> bool:
    clean_lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if _FENCE_LINE_RE.match(stripped):
            continue
        if _LANG_TAG_LINE_RE.match(stripped):
            continue
        if _MODEL_END_LINE_RE.match(stripped):
            continue
        clean_lines.append(line)

    clean_lines = _drop_leading_prose(clean_lines, [])
    candidate = "\n".join(clean_lines).strip()
    if not candidate:
        return False

    try:
        compile(candidate, "<fenced-candidate>", "exec")
    except (SyntaxError, ValueError):
        return False
    return True


def _contains_python_code(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _FENCE_LINE_RE.match(stripped) or _LANG_TAG_LINE_RE.match(stripped):
            continue
        if _CODE_START_RE.match(stripped):
            return True
    return False


def _drop_leading_prose(lines: list[str], diagnostics: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if _CODE_START_RE.match(stripped):
            if index:
                diagnostics.append("removed leading prose")
            return lines[index:]

    if any(line.strip() for line in lines):
        diagnostics.append("removed non-code response")
    return []
