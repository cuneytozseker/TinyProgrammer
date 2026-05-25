"""Programmer package exports."""

__all__ = ["Brain", "Personality"]


def __getattr__(name):
    if name == "Brain":
        from .brain import Brain
        return Brain
    if name == "Personality":
        from .personality import Personality
        return Personality
    raise AttributeError(name)
