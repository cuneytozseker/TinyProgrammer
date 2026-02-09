import sys
import time

class Canvas:
    """
    A simple interface for drawing on the Tiny Programmer canvas.
    Outputs commands to stdout that the main process interprets.
    Canvas size is 416x218 (inside the popup window).
    """

    def __init__(self, w=416, h=218):
        self.width = w
        self.height = h
        # Flush immediately so animation is smooth
        sys.stdout.reconfigure(line_buffering=True)
    
    def update(self):
        """Dummy method for compatibility."""
        pass
        
    def move(self, *args):
        """Dummy method for compatibility."""
        pass

    def clear(self, r=0, g=0, b=0):
        """Clear screen with color."""
        print(f"CMD:CLEAR,{r},{g},{b}")

    def pixel(self, x, y, r=255, g=255, b=255):
        """Draw a single pixel."""
        print(f"CMD:PIXEL,{int(x)},{int(y)},{r},{g},{b}")

    def line(self, x1, y1, x2, y2, r=255, g=255, b=255):
        """Draw a line."""
        print(f"CMD:LINE,{int(x1)},{int(y1)},{int(x2)},{int(y2)},{r},{g},{b}")

    def rect(self, x, y, w, h, r=255, g=255, b=255):
        """Draw a rectangle outline."""
        print(f"CMD:RECT,{int(x)},{int(y)},{int(w)},{int(h)},{r},{g},{b}")

    def fill_rect(self, x, y, w, h, r=255, g=255, b=255):
        """Draw a filled rectangle."""
        print(f"CMD:FILLRECT,{int(x)},{int(y)},{int(w)},{int(h)},{r},{g},{b}")

    def circle(self, x, y, radius, r=255, g=255, b=255):
        """Draw a circle outline."""
        print(f"CMD:CIRCLE,{int(x)},{int(y)},{int(radius)},{r},{g},{b}")
    
    def fill_circle(self, x, y, radius, r=255, g=255, b=255):
        """Draw a filled circle."""
        print(f"CMD:FILLCIRCLE,{int(x)},{int(y)},{int(radius)},{r},{g},{b}")

    def show(self):
        """Update the display (flip buffer)."""
        # In this protocol, we assume immediate drawing, but this can be a sync point
        # print("CMD:FLIP") 
        # For now, commands render immediately
        pass
        
    def sleep(self, seconds):
        """Sleep for seconds."""
        time.sleep(seconds)
