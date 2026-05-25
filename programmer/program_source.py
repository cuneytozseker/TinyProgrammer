"""Source cleaning and validation for generated canvas sketches."""

from __future__ import annotations

import ast
import inspect


CANVAS_FUNCTION_PROTOCOL = "canvas_function_v1"


class ProgramSourceError(ValueError):
    """Raised when generated source violates the sketch contract."""


def clean_generated_source(raw_code: str) -> str:
    """Remove markdown fences and common language-label debris."""
    raw_lines = raw_code.replace("<|im_end|>", "").splitlines()
    if any(line.strip().startswith("```") for line in raw_lines):
        fenced_lines = []
        in_fence = False
        for line in raw_lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_fence:
                    break
                in_fence = True
                continue
            if in_fence and stripped != "python":
                fenced_lines.append(line.rstrip())
        return "\n".join(fenced_lines).strip()

    lines = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped == "python":
            continue
        lines.append(line.rstrip())

    return "\n".join(lines).strip()


def validate_canvas_function_source(source: str) -> None:
    """Validate the LLM-authored module has the required source shape."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ProgramSourceError(
            f"SyntaxError: {exc.msg} at line {exc.lineno}"
        ) from exc

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    draw = functions.get("draw")
    if draw is None:
        raise ProgramSourceError("Missing required draw(c, state, t, dt) function")
    _validate_function_args(draw, "draw", ("c", "state", "t", "dt"))

    setup = functions.get("setup")
    if setup is not None:
        _validate_function_args(setup, "setup", ("c",))


def validate_canvas_runtime_namespace(namespace: dict) -> None:
    """Validate the executed module still exposes callable setup/draw hooks."""
    draw = namespace.get("draw")
    if not callable(draw):
        raise ProgramSourceError("draw must be callable")
    _validate_callable_args(draw, "draw", ("c", "state", "t", "dt"))

    setup = namespace.get("setup")
    if setup is not None:
        if not callable(setup):
            raise ProgramSourceError("setup must be callable")
        _validate_callable_args(setup, "setup", ("c",))


def _validate_function_args(
    node: ast.FunctionDef,
    name: str,
    expected: tuple[str, ...],
) -> None:
    args = node.args
    if (
        args.vararg
        or args.kwarg
        or args.kwonlyargs
        or args.posonlyargs
        or len(args.args) != len(expected)
    ):
        expected_text = ", ".join(expected)
        raise ProgramSourceError(f"{name} must have signature {name}({expected_text})")

    actual = tuple(arg.arg for arg in args.args)
    if actual != expected:
        expected_text = ", ".join(expected)
        raise ProgramSourceError(f"{name} must have signature {name}({expected_text})")


def _validate_callable_args(func, name: str, expected: tuple[str, ...]) -> None:
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError) as exc:
        raise ProgramSourceError(f"{name} must be callable with the documented signature") from exc

    params = tuple(signature.parameters.values())
    valid_kinds = {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    }
    actual = tuple(param.name for param in params)
    if len(params) != len(expected) or actual != expected:
        expected_text = ", ".join(expected)
        raise ProgramSourceError(f"{name} must have signature {name}({expected_text})")
    if any(param.kind not in valid_kinds for param in params):
        expected_text = ", ".join(expected)
        raise ProgramSourceError(f"{name} must have signature {name}({expected_text})")
