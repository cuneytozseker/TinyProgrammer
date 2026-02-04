# Display module
from .terminal import Terminal
from .framebuffer import FramebufferWriter, get_writer, IS_FRAMEBUFFER_AVAILABLE

__all__ = ['Terminal', 'FramebufferWriter', 'get_writer', 'IS_FRAMEBUFFER_AVAILABLE']
