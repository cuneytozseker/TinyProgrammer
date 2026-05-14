"""Display package exports.

Keep package import lightweight because config imports display.layout during
startup before pygame and framebuffer modules should be initialized.
"""

__all__ = ["Terminal", "FramebufferWriter", "get_writer", "IS_FRAMEBUFFER_AVAILABLE"]


def __getattr__(name):
    if name == "Terminal":
        from .terminal import Terminal

        globals()[name] = Terminal
        return Terminal

    if name in {"FramebufferWriter", "get_writer", "IS_FRAMEBUFFER_AVAILABLE"}:
        from .framebuffer import FramebufferWriter, IS_FRAMEBUFFER_AVAILABLE, get_writer

        exports = {
            "FramebufferWriter": FramebufferWriter,
            "get_writer": get_writer,
            "IS_FRAMEBUFFER_AVAILABLE": IS_FRAMEBUFFER_AVAILABLE,
        }
        globals().update(exports)
        return exports[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
